"""Strict 4-Fold Spatial Eroded Leave-One-Quadrant-Out (LOQO) Coupled & Blind
Subsurface/Piedmont/Remanence Specialists with Quadrant-Repaired Sparse Posterior
Calibration, Two-Regime Radial Fusion, and 1-D Strand-Sharp Survival for Lane H86Q-BFRA."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from src.gems86_ksad.allocator import elkan_bayes_recalibrate
from src.gems86_stdp.model import (
    calibrate_quadrant_sparse_posterior,
    rank01_on_mask,
)
from src.gems86_tcwb.model import (
    ABLATION_ELASTIC_NAMES,
    PrecomputedNestedElastic,
    _eroded_out_of_fold_domain,
    _fit_hgb_pair,
    _predict_chunked,
    build_precomputed_nested_elastic,
    calibrate_global_sparse_posterior,
    sample_loqo_tcwb,
)
from .features import BFRA_ELASTIC_NAMES
from .operators import strand_tangent_sharpen_posterior


@dataclass(frozen=True)
class BFRAConfig:
    collar_px: float = 3.0
    coupled_neg_buffer_px: float = 4.5
    blind_neg_buffer_px: float = 8.0
    erode_train_px: int = 12
    n_neg_blind: int = 165_000
    n_neg_coupled: int = 200_000
    tau0_logit: float = -4.55
    beta_logit: float = 1.65
    blind_hgb_weight: float = 0.64
    blind_corrob_weight: float = 0.36
    alpha_coupled: float = 0.74
    alpha_blind_base: float = 0.43
    crest_gain: float = 0.14
    flank_trim: float = 0.12
    seed: int = 861726


def rank01_per_quadrant(
    surface: np.ndarray, valid: np.ndarray, quad_ids: np.ndarray
) -> np.ndarray:
    """Rank-normalize ``surface`` within each spatial quadrant ``q in {0, 1, 2, 3}``
    so regional baseline differences between Walker Lane (SW) and northern Nevada
    (NW/NE) never starve northern quadrants."""
    fp = np.asarray(valid, dtype=bool)
    q_grid = np.asarray(quad_ids, dtype=np.int8)
    out = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        qm = fp & (q_grid == q)
        if qm.any():
            out[qm] = rank01_on_mask(surface, qm)[qm]
    return out


def fuse_tworegime_radial_bfra(
    p_coupled_cal: np.ndarray,
    p_blind_cal: np.ndarray,
    cover_propensity: np.ndarray,
    d_vis: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_coupled: float = 0.74,
    alpha_blind_base: float = 0.43,
) -> np.ndarray:
    """Two-regime radial-and-cover-aware Noisy-OR fusion.

    Preserves high-precision Kostrov-Pollard + BFRA stepover recovery inside the
    3-8.5 px near-catalogue relay zone while ramping blind subsurface/piedmont/remanence
    discovery across > 1 km basin interiors (matching the empirical r = +0.994
    Focus-9 radial leaderboard law).
    """
    fp = np.asarray(valid, dtype=bool)
    cov = np.clip(np.asarray(cover_propensity, dtype=np.float32), 0.0, 1.0)
    dv = np.asarray(d_vis, dtype=np.float32)
    radial_boost = 0.76 + 0.52 * np.tanh(np.maximum(dv - 8.5, 0.0) / 9.0)
    w_blind = float(alpha_blind_base) * (0.68 + 0.64 * cov) * radial_boost
    s = 1.0 - (1.0 - float(alpha_coupled) * p_coupled_cal) * (
        1.0 - np.clip(w_blind * p_blind_cal, 0.0, 0.98)
    )
    return np.where(fp, s, np.float32(0.0)).astype(np.float32)


def fit_predict_loqo_bfra_surfaces(
    X_bfra: np.ndarray,
    X_abl: np.ndarray,
    L_bfra: np.ndarray,
    cover_propensity: np.ndarray,
    regions: list[tuple[str, np.ndarray, np.ndarray]],
    valid: np.ndarray,
    cfg: BFRAConfig = BFRAConfig(),
) -> dict[str, np.ndarray]:
    """Fit strict spatial eroded-LOQO models across ``regions = [(name, eval_mask, vis_mask), ...]``
    and return out-of-fold surfaces for ``E1`` (coupled+blind), ``E2`` (pure blind), and ``E3`` (ablation)."""
    fp = np.asarray(valid, dtype=bool)
    H, W = fp.shape

    p_coupled_raw = np.zeros((H, W), dtype=np.float32)
    p_blind_raw = np.zeros((H, W), dtype=np.float32)
    p_abl_raw = np.zeros((H, W), dtype=np.float32)
    d_vis_eval = np.zeros((H, W), dtype=np.float32)
    quad_ids = np.full((H, W), -1, dtype=np.int8)

    pre_cache: dict[str, PrecomputedNestedElastic] = {}
    for _, _, vis_mask in regions:
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        if vh not in pre_cache:
            pre_cache[vh] = build_precomputed_nested_elastic(
                vis_mask, fp, split_seed=cfg.seed + 19 * (len(pre_cache) + 1)
            )

    for q_idx, (_, eval_mask, vis_mask) in enumerate(regions):
        ev = np.asarray(eval_mask, dtype=bool) & fp
        quad_ids[ev] = q_idx
        train_dom = _eroded_out_of_fold_domain(eval_mask, fp, cfg.erode_train_px)
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        pre = pre_cache[vh]
        d_vis_eval[ev] = pre.d_vis[ev]

        # 1. Coupled 32-plane BFRA + 6 Kostrov-Pollard planes (4.5 px stress-shadow negative buffer)
        Xc, yc, wc, eff_rc = sample_loqo_tcwb(
            X_bfra,
            pre,
            train_dom,
            fp,
            BFRA_ELASTIC_NAMES,
            pre.el_ksad_a,
            pre.el_ksad_b,
            cover_propensity,
            n_neg=cfg.n_neg_coupled,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.coupled_neg_buffer_px,
            seed=cfg.seed + 101 * (q_idx + 1),
        )
        c1, c2 = _fit_hgb_pair(Xc, yc, wc, seed=cfg.seed + 211 * (q_idx + 1))
        del Xc, yc, wc
        pr1 = _predict_chunked(c1, X_bfra, pre.el_ksad_full, BFRA_ELASTIC_NAMES, ev)
        pr2 = _predict_chunked(c2, X_bfra, pre.el_ksad_full, BFRA_ELASTIC_NAMES, ev)
        pr_avg = 0.55 * pr1 + 0.45 * pr2
        p_coupled_raw[ev] = elkan_bayes_recalibrate(pr_avg[ev], eff_rc).astype(np.float32)
        del c1, c2, pr1, pr2, pr_avg

        # 2. Pure zero-catalogue-feature blind 32-plane BFRA specialist (8.0 px negative buffer)
        Xb, yb, wb, eff_rb = sample_loqo_tcwb(
            X_bfra,
            pre,
            train_dom,
            fp,
            (),
            None,
            None,
            cover_propensity,
            n_neg=cfg.n_neg_blind,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.blind_neg_buffer_px,
            seed=cfg.seed + 307 * (q_idx + 1),
        )
        b1, b2 = _fit_hgb_pair(Xb, yb, wb, seed=cfg.seed + 401 * (q_idx + 1))
        del Xb, yb, wb
        pb1 = _predict_chunked(b1, X_bfra, None, (), ev)
        pb2 = _predict_chunked(b2, X_bfra, None, (), ev)
        pb_avg = 0.55 * pb1 + 0.45 * pb2
        p_blind_raw[ev] = elkan_bayes_recalibrate(pb_avg[ev], eff_rb).astype(np.float32)
        del b1, b2, pb1, pb2, pb_avg

        # 3. Pixel-local unpulled ablation control (8 local planes + isotropic tip halo)
        Xa, ya, _, _ = sample_loqo_tcwb(
            X_abl,
            pre,
            train_dom,
            fp,
            ABLATION_ELASTIC_NAMES,
            pre.el_iso_a,
            pre.el_iso_b,
            None,
            n_neg=cfg.n_neg_blind,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.blind_neg_buffer_px,
            seed=cfg.seed + 503 * (q_idx + 1),
        )
        ca = HistGradientBoostingClassifier(
            max_iter=170,
            learning_rate=0.06,
            max_leaf_nodes=35,
            min_samples_leaf=110,
            l2_regularization=3.0,
            early_stopping=False,
            random_state=cfg.seed + 601 * (q_idx + 1),
        ).fit(Xa, ya)
        del Xa, ya
        p_abl_raw[ev] = _predict_chunked(
            ca, X_abl, pre.el_iso_full, ABLATION_ELASTIC_NAMES, ev
        )[ev]
        del ca
        gc.collect()

    del pre_cache
    gc.collect()

    eval_union = (quad_ids >= 0) & fp
    p_coupled_cal = calibrate_global_sparse_posterior(
        p_coupled_raw, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )

    # Quadrant-repaired calibration (repairs IR-86Q-TCWB-SWAPPED-ARGS-20261026)
    corrob_q = np.power(
        np.clip(rank01_per_quadrant(L_bfra, eval_union, quad_ids), 0.0, 1.0), 1.25
    )
    blind_blend = (
        cfg.blind_hgb_weight * rank01_per_quadrant(p_blind_raw, eval_union, quad_ids)
        + cfg.blind_corrob_weight * corrob_q
    ).astype(np.float32)
    p_blind_cal = calibrate_quadrant_sparse_posterior(
        blind_blend,
        eval_union,
        quad_ids,
        tau0=cfg.tau0_logit - 0.12,
        beta=cfg.beta_logit,
    )

    s_e2_sharp = strand_tangent_sharpen_posterior(
        p_blind_cal,
        eval_union,
        crest_gain=cfg.crest_gain,
        flank_trim=cfg.flank_trim,
    )
    s_e1_raw = fuse_tworegime_radial_bfra(
        p_coupled_cal,
        s_e2_sharp,
        cover_propensity,
        d_vis_eval,
        eval_union,
        alpha_coupled=cfg.alpha_coupled,
        alpha_blind_base=cfg.alpha_blind_base,
    )
    s_e1_sharp = strand_tangent_sharpen_posterior(
        s_e1_raw,
        eval_union,
        crest_gain=cfg.crest_gain,
        flank_trim=cfg.flank_trim,
    )
    p_abl_cal = calibrate_global_sparse_posterior(
        p_abl_raw, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    return {
        "S_e1_coupled": s_e1_sharp,
        "S_e2_blind": s_e2_sharp,
        "S_e3_ablation": p_abl_cal,
        "p_coupled_cal": p_coupled_cal,
    }
