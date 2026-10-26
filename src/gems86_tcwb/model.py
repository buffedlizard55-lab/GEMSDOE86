"""Strict 4-Fold Spatial Eroded Leave-One-Quadrant-Out (LOQO) Coupled & Blind
Piedmont/Basement/Clay-Cap Specialists with Radial-Cover Elkan-Bayes Fusion and
Exact 6-Ring Bernoulli Survival Dinkelbach-CELF for Lane H86P-TCWB."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

from src.gems86_ewcs.features import compute_elastic_fields as compute_ewcs_elastic_fields
from src.gems86_ksad.allocator import elkan_bayes_recalibrate
from src.gems86_ksad.physics import compute_kostrov_elastic_fields
from src.gems86_stdp.model import (
    calibrate_quadrant_sparse_posterior,
    rank01_on_mask,
    split_visible_components,
)
from .features import ABLATION_LOCAL_NAMES, TCWB_ELASTIC_NAMES, TCWB_STATIC_NAMES

ABLATION_ELASTIC_NAMES: tuple[str, ...] = ("iso_tip_halo",)


@dataclass(frozen=True)
class TCWBConfig:
    collar_px: float = 3.0
    coupled_neg_buffer_px: float = 4.5
    blind_neg_buffer_px: float = 8.0
    erode_train_px: int = 12
    n_neg_blind: int = 160_000
    n_neg_coupled: int = 195_000
    tau0_logit: float = -4.55
    beta_logit: float = 1.65
    blind_hgb_weight: float = 0.62
    blind_corrob_weight: float = 0.38
    alpha_coupled: float = 0.77
    alpha_blind_base: float = 0.36
    seed: int = 861626


@dataclass
class PrecomputedNestedElastic:
    vis_full: np.ndarray
    d_vis: np.ndarray
    va_full: np.ndarray
    vb_full: np.ndarray
    da: np.ndarray
    db: np.ndarray
    el_ksad_a: dict[str, np.ndarray]
    el_ksad_b: dict[str, np.ndarray]
    el_ksad_full: dict[str, np.ndarray]
    el_iso_a: dict[str, np.ndarray]
    el_iso_b: dict[str, np.ndarray]
    el_iso_full: dict[str, np.ndarray]


def build_precomputed_nested_elastic(
    vis_cat: np.ndarray, valid: np.ndarray, *, split_seed: int
) -> PrecomputedNestedElastic:
    """Precompute disjoint 8-connected visible-component splits (va_full, vb_full)
    and their cross-component Kostrov-Pollard and isotropic tip-halo fields strictly
    from ``vis_cat``."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    va, vb = split_visible_components(vis, seed=split_seed)
    da = ndi.distance_transform_edt(~va).astype(np.float32)
    db = ndi.distance_transform_edt(~vb).astype(np.float32)

    el_ksad_a = compute_kostrov_elastic_fields(va, fp)
    el_ksad_b = compute_kostrov_elastic_fields(vb, fp)
    el_ksad_full = compute_kostrov_elastic_fields(vis, fp)

    ew_a = compute_ewcs_elastic_fields(va, fp)
    ew_b = compute_ewcs_elastic_fields(vb, fp)
    ew_full = compute_ewcs_elastic_fields(vis, fp)
    el_iso_a = {"iso_tip_halo": ew_a["iso_tip_halo"]}
    el_iso_b = {"iso_tip_halo": ew_b["iso_tip_halo"]}
    el_iso_full = {"iso_tip_halo": ew_full["iso_tip_halo"]}
    del ew_a, ew_b, ew_full
    gc.collect()

    return PrecomputedNestedElastic(
        vis_full=vis,
        d_vis=d_vis,
        va_full=va,
        vb_full=vb,
        da=da,
        db=db,
        el_ksad_a=el_ksad_a,
        el_ksad_b=el_ksad_b,
        el_ksad_full=el_ksad_full,
        el_iso_a=el_iso_a,
        el_iso_b=el_iso_b,
        el_iso_full=el_iso_full,
    )


def calibrate_global_sparse_posterior(
    prob: np.ndarray,
    valid: np.ndarray,
    *,
    tau0: float = -4.55,
    beta: float = 1.65,
) -> np.ndarray:
    """Map Elkan-Bayes recalibrated probabilities into a sparse fault posterior in (0, 1)
    using footprint-wide median and P90 log-odds so natural fold-to-fold fault-density
    differences across NW/NE/SW/SE are preserved."""
    fp = np.asarray(valid, dtype=bool)
    out = np.zeros(fp.shape, dtype=np.float32)
    if not fp.any():
        return out
    p = np.clip(prob[fp].astype(np.float64), 1e-6, 1.0 - 1e-6)
    ell = np.log(p / (1.0 - p))
    med = float(np.median(ell))
    p90 = float(np.percentile(ell, 90.0))
    scale = max(p90 - med, 1e-4)
    z = np.clip((ell - med) / scale, -6.0, 8.0)
    logits = float(tau0) + float(beta) * z
    out[fp] = (1.0 / (1.0 + np.exp(-logits))).astype(np.float32)
    return out


def _extract_rows(
    X_static: np.ndarray,
    flat_idx: np.ndarray,
    elastic_planes: dict[str, np.ndarray] | None = None,
    elastic_keys: tuple[str, ...] = (),
) -> np.ndarray:
    n_s, _, W = X_static.shape
    ys, xs = np.divmod(flat_idx, W)
    n_e = len(elastic_keys) if elastic_planes is not None else 0
    out = np.empty((flat_idx.size, n_s + n_e), dtype=np.float32)
    out[:, :n_s] = X_static[:, ys, xs].T.astype(np.float32)
    if n_e and elastic_planes is not None:
        for j, k in enumerate(elastic_keys):
            out[:, n_s + j] = elastic_planes[k][ys, xs].astype(np.float32)
    return out


def _predict_chunked(
    clf: HistGradientBoostingClassifier,
    X_static: np.ndarray,
    elastic_planes: dict[str, np.ndarray] | None,
    elastic_keys: tuple[str, ...],
    pred_mask: np.ndarray,
    chunk_rows: int = 256,
) -> np.ndarray:
    n_s, H, W = X_static.shape
    n_e = len(elastic_keys) if elastic_planes is not None else 0
    out = np.zeros((H, W), dtype=np.float32)
    for r0 in range(0, H, chunk_rows):
        r1 = min(H, r0 + chunk_rows)
        m = pred_mask[r0:r1]
        n_m = int(m.sum())
        if n_m == 0:
            continue
        X_chunk = np.empty((n_m, n_s + n_e), dtype=np.float32)
        X_chunk[:, :n_s] = np.moveaxis(X_static[:, r0:r1, :], 0, -1)[m].astype(np.float32)
        if n_e and elastic_planes is not None:
            for j, k in enumerate(elastic_keys):
                X_chunk[:, n_s + j] = elastic_planes[k][r0:r1][m].astype(np.float32)
        blk = out[r0:r1]
        blk[m] = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
    return out


def _pos_cover_weights(p_idx: np.ndarray, cover_propensity: np.ndarray | None) -> np.ndarray:
    """Up-weight mapped faults preserved inside alluvial/basin cover so the PU learner
    counteracts subaerial bedrock mapping bias."""
    if cover_propensity is None or p_idx.size == 0:
        return np.ones(p_idx.size, dtype=np.float32)
    c_vals = np.clip(cover_propensity.ravel()[p_idx], 0.0, 1.0)
    exposure = np.clip(1.0 - 0.65 * c_vals, 0.35, 1.0)
    return np.clip(1.0 / np.sqrt(exposure), 1.0, 1.69).astype(np.float32)


def sample_loqo_tcwb(
    X_static: np.ndarray,
    pre: PrecomputedNestedElastic,
    train_domain: np.ndarray,
    valid: np.ndarray,
    elastic_keys: tuple[str, ...],
    el_a: dict[str, np.ndarray] | None,
    el_b: dict[str, np.ndarray] | None,
    cover_propensity: np.ndarray | None,
    *,
    n_neg: int,
    collar_px: float,
    neg_buffer_px: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Sample positive and unlabelled training rows strictly inside ``train_domain``."""
    rng = np.random.default_rng(seed)
    fp = np.asarray(valid, dtype=bool)
    dom = np.asarray(train_domain, dtype=bool) & fp
    neg_pool = np.flatnonzero((dom & (pre.d_vis > max(collar_px, neg_buffer_px))).ravel())

    if not elastic_keys:
        pos_idx = np.flatnonzero((pre.vis_full & dom).ravel())
        take_neg = rng.choice(neg_pool, size=min(n_neg, neg_pool.size), replace=False)
        idx = np.concatenate([pos_idx, take_neg])
        y = np.concatenate(
            [np.ones(pos_idx.size, dtype=np.int8), np.zeros(take_neg.size, dtype=np.int8)]
        )
        wp = _pos_cover_weights(pos_idx, cover_propensity)
        w = np.concatenate([wp, np.ones(take_neg.size, dtype=np.float32)])
        X = _extract_rows(X_static, idx)
        mean_wp = float(wp.mean()) if wp.size else 1.0
        eff_r = (float(neg_pool.size) / float(max(take_neg.size, 1))) / max(mean_wp, 1e-6)
        return X, y, w, eff_r

    tot_neg_dom = int(neg_pool.size)
    rng.shuffle(neg_pool)
    half_neg = min(n_neg // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    pos_a = np.flatnonzero((pre.va_full & dom & (pre.db > collar_px)).ravel())
    wp_a = _pos_cover_weights(pos_a, cover_propensity)
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate(
        [np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)]
    )
    wa = np.concatenate([wp_a, np.ones(neg_a.size, dtype=np.int8)])
    Xa = _extract_rows(X_static, idx_a, el_b, elastic_keys)

    pos_b = np.flatnonzero((pre.vb_full & dom & (pre.da > collar_px)).ravel())
    wp_b = _pos_cover_weights(pos_b, cover_propensity)
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate(
        [np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)]
    )
    wb = np.concatenate([wp_b, np.ones(neg_b.size, dtype=np.float32)])
    Xb = _extract_rows(X_static, idx_b, el_a, elastic_keys)

    samp_neg = int(neg_a.size + neg_b.size)
    all_wp = np.concatenate([wp_a, wp_b])
    mean_wp = float(all_wp.mean()) if all_wp.size else 1.0
    eff_r = (float(tot_neg_dom) / float(max(samp_neg, 1))) / max(mean_wp, 1e-6)
    return (
        np.vstack([Xa, Xb]),
        np.concatenate([ya, yb]),
        np.concatenate([wa.astype(np.float32), wb.astype(np.float32)]),
        eff_r,
    )


def _fit_hgb_pair(
    X: np.ndarray,
    y: np.ndarray,
    w: np.ndarray | None,
    *,
    seed: int,
) -> tuple[HistGradientBoostingClassifier, HistGradientBoostingClassifier]:
    c1 = HistGradientBoostingClassifier(
        max_iter=230,
        learning_rate=0.06,
        max_leaf_nodes=55,
        min_samples_leaf=95,
        l2_regularization=2.5,
        early_stopping=False,
        random_state=seed,
    ).fit(X, y, sample_weight=w)
    c2 = HistGradientBoostingClassifier(
        max_iter=190,
        learning_rate=0.065,
        max_leaf_nodes=39,
        min_samples_leaf=120,
        l2_regularization=3.5,
        early_stopping=False,
        random_state=seed + 97,
    ).fit(X, y, sample_weight=w)
    return c1, c2


def fuse_radial_cover_tcwb(
    p_coupled_cal: np.ndarray,
    p_blind_cal: np.ndarray,
    cover_propensity: np.ndarray,
    d_vis: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_coupled: float = 0.77,
    alpha_blind_base: float = 0.36,
) -> np.ndarray:
    """Two-regime radial-and-cover-aware Noisy-OR fusion.

    Strictly uses ``d_vis`` from fold-visible faults during holdout (and full
    catalogue at final emission), gently damping blind background inside the
    3-8 px near-catalogue collar while amplifying blind piedmont/basement/clay-cap
    discovery under alluvial cover and beyond 1 km.
    """
    fp = np.asarray(valid, dtype=bool)
    cov = np.clip(np.asarray(cover_propensity, dtype=np.float32), 0.0, 1.0)
    dv = np.asarray(d_vis, dtype=np.float32)
    radial_boost = 0.85 + 0.30 * np.tanh(np.maximum(dv - 8.0, 0.0) / 10.0)
    w_blind = float(alpha_blind_base) * (0.68 + 0.64 * cov) * radial_boost
    s = 1.0 - (1.0 - float(alpha_coupled) * p_coupled_cal) * (
        1.0 - np.clip(w_blind * p_blind_cal, 0.0, 0.98)
    )
    return np.where(fp, s, np.float32(0.0)).astype(np.float32)


def _eroded_out_of_fold_domain(
    eval_region: np.ndarray, valid: np.ndarray, erode_px: int
) -> np.ndarray:
    """Return pixels outside ``eval_region`` at Euclidean distance > ``erode_px``
    from ``eval_region`` so no spatial filter or 3-px kernel straddles the fold seam."""
    reg = np.asarray(eval_region, dtype=bool)
    if erode_px <= 0:
        return (~reg) & np.asarray(valid, dtype=bool)
    dist_to_eval = ndi.distance_transform_edt(~reg)
    return (dist_to_eval > float(erode_px)) & np.asarray(valid, dtype=bool)


def fit_predict_loqo_tcwb_surfaces(
    X_tcwb: np.ndarray,
    X_abl: np.ndarray,
    L_tcwb: np.ndarray,
    cover_propensity: np.ndarray,
    regions: list[tuple[str, np.ndarray, np.ndarray]],
    valid: np.ndarray,
    cfg: TCWBConfig = TCWBConfig(),
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
    for q_idx, (_, _, vis_mask) in enumerate(regions):
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        if vh not in pre_cache:
            pre_cache[vh] = build_precomputed_nested_elastic(
                vis_mask, fp, split_seed=cfg.seed + 17 * (len(pre_cache) + 1)
            )

    for q_idx, (q_name, eval_mask, vis_mask) in enumerate(regions):
        ev = np.asarray(eval_mask, dtype=bool) & fp
        quad_ids[ev] = q_idx
        train_dom = _eroded_out_of_fold_domain(eval_mask, fp, cfg.erode_train_px)
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        pre = pre_cache[vh]
        d_vis_eval[ev] = pre.d_vis[ev]

        # 1. Coupled TCWB + 6 Kostrov-Pollard planes (4.5 px stress-shadow negative buffer)
        Xc, yc, wc, eff_rc = sample_loqo_tcwb(
            X_tcwb,
            pre,
            train_dom,
            fp,
            TCWB_ELASTIC_NAMES,
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
        pr1 = _predict_chunked(c1, X_tcwb, pre.el_ksad_full, TCWB_ELASTIC_NAMES, ev)
        pr2 = _predict_chunked(c2, X_tcwb, pre.el_ksad_full, TCWB_ELASTIC_NAMES, ev)
        pr_avg = 0.55 * pr1 + 0.45 * pr2
        p_coupled_raw[ev] = elkan_bayes_recalibrate(pr_avg[ev], eff_rc).astype(np.float32)
        del c1, c2, pr1, pr2, pr_avg

        # 2. Pure zero-catalogue-feature blind TCWB specialist (8.0 px negative buffer)
        Xb, yb, wb, eff_rb = sample_loqo_tcwb(
            X_tcwb,
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
        pb1 = _predict_chunked(b1, X_tcwb, None, (), ev)
        pb2 = _predict_chunked(b2, X_tcwb, None, (), ev)
        pb_avg = 0.55 * pb1 + 0.45 * pb2
        p_blind_raw[ev] = elkan_bayes_recalibrate(pb_avg[ev], eff_rb).astype(np.float32)
        del b1, b2, pb1, pb2, pb_avg

        # 3. Pixel-local unpulled ablation control (8 local planes + isotropic tip halo, uncalibrated)
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

    corrob_rank = np.power(np.clip(rank01_on_mask(L_tcwb, eval_union), 0.0, 1.0), 1.25)
    blind_blend = (
        cfg.blind_hgb_weight * rank01_on_mask(p_blind_raw, eval_union)
        + cfg.blind_corrob_weight * corrob_rank
    ).astype(np.float32)
    p_blind_cal = calibrate_quadrant_sparse_posterior(
        blind_blend,
        quad_ids,
        eval_union,
        tau0=cfg.tau0_logit - 0.15,
        beta=cfg.beta_logit,
    )

    s_e1 = fuse_radial_cover_tcwb(
        p_coupled_cal,
        p_blind_cal,
        cover_propensity,
        d_vis_eval,
        eval_union,
        alpha_coupled=cfg.alpha_coupled,
        alpha_blind_base=cfg.alpha_blind_base,
    )
    p_abl_cal = calibrate_global_sparse_posterior(
        p_abl_raw, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    return {
        "S_e1_coupled": s_e1,
        "S_e2_blind": p_blind_cal,
        "S_e3_ablation": p_abl_cal,
        "p_coupled_cal": p_coupled_cal,
    }
