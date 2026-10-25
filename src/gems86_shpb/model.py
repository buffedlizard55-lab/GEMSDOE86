"""Strict 4-Fold Spatial Leave-One-Quadrant-Out (LOQO) Coupled Kostrov-Bayes &
Blind Conduit Specialists with Exact 6-Ring Bernoulli Survival Dinkelbach-CELF
for Lane H86N-SHPB."""

from __future__ import annotations

from dataclasses import dataclass
import gc
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gems86_ewcs.features import compute_elastic_fields as compute_ewcs_elastic_fields
from gems86_ksad.allocator import elkan_bayes_recalibrate
from gems86_ksad.physics import compute_kostrov_elastic_fields
from gems86_stdp.dinkelbach_celf import (
    DinkelbachCELFAllocation,
    dinkelbach_celf_allocate_dots,
    static_ek_spacing_allocate,
)
from gems86_stdp.model import (
    calibrate_quadrant_sparse_posterior,
    rank01_on_mask,
    split_visible_components,
)

from .features import ABLATION_LOCAL_NAMES, SHPB_ELASTIC_NAMES, SHPB_STATIC_NAMES

ABLATION_ELASTIC_NAMES: tuple[str, ...] = ("iso_tip_halo",)


@dataclass(frozen=True)
class SHPBConfig:
    collar_px: float = 3.0
    blind_neg_buffer_px: float = 8.0
    n_neg_blind: int = 160_000
    n_neg_coupled: int = 190_000
    tau0_logit: float = -4.55
    beta_logit: float = 1.65
    blind_hgb_weight: float = 0.62
    blind_corrob_weight: float = 0.38
    alpha_coupled: float = 0.78
    alpha_blind_base: float = 0.34
    seed: int = 861425


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
    """Precompute the disjoint 8-connected visible-component split (va_full, vb_full)
    and its cross-component Kostrov-Pollard and isotropic tip-halo fields once for a
    given visible fault mask."""
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
    differences across NW/NE/SW/SE are preserved without distortion."""
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


def _pos_exposure_weights(p_idx: np.ndarray, c_exposure: np.ndarray | None) -> np.ndarray:
    if c_exposure is None or p_idx.size == 0:
        return np.ones(p_idx.size, dtype=np.float32)
    c_vals = c_exposure.ravel()[p_idx]
    return np.clip(1.0 / np.sqrt(np.maximum(c_vals, 0.35)), 1.0, 1.69).astype(np.float32)


def sample_loqo_from_precomputed(
    X_static: np.ndarray,
    pre: PrecomputedNestedElastic,
    train_domain: np.ndarray,
    valid: np.ndarray,
    elastic_keys: tuple[str, ...],
    el_a: dict[str, np.ndarray] | None,
    el_b: dict[str, np.ndarray] | None,
    c_exposure: np.ndarray | None,
    *,
    n_neg: int,
    collar_px: float,
    neg_buffer_px: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Sample positive and unlabelled training rows strictly inside ``train_domain``
    using precomputed cross-component elastic fields."""
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
        wp = _pos_exposure_weights(pos_idx, c_exposure)
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
    wp_a = _pos_exposure_weights(pos_a, c_exposure)
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate(
        [np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)]
    )
    wa = np.concatenate([wp_a, np.ones(neg_a.size, dtype=np.float32)])
    Xa = _extract_rows(X_static, idx_a, el_b, elastic_keys)

    pos_b = np.flatnonzero((pre.vb_full & dom & (pre.da > collar_px)).ravel())
    wp_b = _pos_exposure_weights(pos_b, c_exposure)
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
        np.concatenate([wa, wb]),
        eff_r,
    )


def _fit_hgb(
    X: np.ndarray,
    y: np.ndarray,
    w: np.ndarray | None,
    *,
    seed: int,
    max_leaf_nodes: int = 55,
    max_iter: int = 230,
    l2_reg: float = 2.5,
) -> HistGradientBoostingClassifier:
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=0.06,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=95,
        l2_regularization=l2_reg,
        early_stopping=False,
        random_state=seed,
    )
    return clf.fit(X, y, sample_weight=w)


def fuse_cover_aware_shpb(
    p_coupled_cal: np.ndarray,
    p_blind_cal: np.ndarray,
    c_exposure: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_coupled: float = 0.78,
    alpha_blind_base: float = 0.34,
) -> np.ndarray:
    """Cover-aware Noisy-OR fusion of Elkan-Bayes coupled Kostrov-SHPB posterior
    and quadrant-sparse blind SHPB conduit posterior."""
    fp = np.asarray(valid, dtype=bool)
    pc = np.clip(np.asarray(p_coupled_cal, dtype=np.float32), 0.0, 1.0)
    pb = np.clip(np.asarray(p_blind_cal, dtype=np.float32), 0.0, 1.0)
    ce = np.clip(np.asarray(c_exposure, dtype=np.float32), 0.35, 1.0)
    w_blind = float(alpha_blind_base) * (0.65 + 0.70 * (1.0 - ce))
    fused = 1.0 - (1.0 - float(alpha_coupled) * pc) * (1.0 - np.clip(w_blind * pb, 0.0, 0.99))
    return np.where(fp, np.clip(fused, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_shpb_fold_surfaces(
    X_shpb: np.ndarray,
    L_shpb: np.ndarray,
    X_abl: np.ndarray,
    c_exposure: np.ndarray,
    pre: PrecomputedNestedElastic,
    train_domain: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray,
    cfg: SHPBConfig,
    *,
    fold_seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit E1 (coupled SHPB), E2 (blind SHPB conduit), and E3 (local unpulled ablation)
    strictly on ``train_domain`` (quad != fold_i eroded 12 px) and return their full-grid
    probability surfaces for fold evaluation."""
    fp = np.asarray(valid, dtype=bool)

    # 1. Blind SHPB conduit specialist (Arm E2 standalone & blind component of Arm E1)
    X_b, y_b, w_b, _ = sample_loqo_from_precomputed(
        X_shpb,
        pre,
        train_domain,
        fp,
        (),
        None,
        None,
        c_exposure,
        n_neg=cfg.n_neg_blind,
        collar_px=cfg.collar_px,
        neg_buffer_px=cfg.blind_neg_buffer_px,
        seed=fold_seed + 11,
    )
    clf_b = _fit_hgb(X_b, y_b, w_b, seed=fold_seed + 11, max_leaf_nodes=43, max_iter=210, l2_reg=2.8)
    del X_b, y_b, w_b
    raw_blind = _predict_chunked(clf_b, X_shpb, None, (), fp)
    del clf_b
    p_blind_hgb = calibrate_quadrant_sparse_posterior(
        raw_blind, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    del raw_blind
    l_prob = np.clip(0.005 + 0.990 * np.asarray(L_shpb, dtype=np.float32), 1e-4, 0.9999)
    p_corrob_cal = calibrate_quadrant_sparse_posterior(
        l_prob, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    surf_e2_blind = np.where(
        fp,
        np.clip(
            cfg.blind_hgb_weight * p_blind_hgb + cfg.blind_corrob_weight * p_corrob_cal,
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)
    del p_blind_hgb, p_corrob_cal

    # 2. Coupled 30-feature SHPB + 6 anisotropic Kostrov-Pollard ensemble (2 diverse-depth trees)
    X_c, y_c, w_c, r_c = sample_loqo_from_precomputed(
        X_shpb,
        pre,
        train_domain,
        fp,
        SHPB_ELASTIC_NAMES,
        pre.el_ksad_a,
        pre.el_ksad_b,
        c_exposure,
        n_neg=cfg.n_neg_coupled,
        collar_px=cfg.collar_px,
        neg_buffer_px=cfg.collar_px,
        seed=fold_seed + 23,
    )
    clf_c1 = _fit_hgb(X_c, y_c, w_c, seed=fold_seed + 23, max_leaf_nodes=55, max_iter=230, l2_reg=2.5)
    clf_c2 = _fit_hgb(X_c, y_c, w_c, seed=fold_seed + 29, max_leaf_nodes=35, max_iter=250, l2_reg=3.5)
    del X_c, y_c, w_c
    p_c1 = _predict_chunked(clf_c1, X_shpb, pre.el_ksad_full, SHPB_ELASTIC_NAMES, fp)
    p_c2 = _predict_chunked(clf_c2, X_shpb, pre.el_ksad_full, SHPB_ELASTIC_NAMES, fp)
    del clf_c1, clf_c2
    p_coupled_bayes = elkan_bayes_recalibrate(0.55 * p_c1 + 0.45 * p_c2, r_c, valid=fp)
    del p_c1, p_c2
    p_coupled_cal = calibrate_global_sparse_posterior(
        p_coupled_bayes, fp, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    del p_coupled_bayes

    surf_e1_coupled = fuse_cover_aware_shpb(
        p_coupled_cal,
        surf_e2_blind,
        c_exposure,
        fp,
        alpha_coupled=cfg.alpha_coupled,
        alpha_blind_base=cfg.alpha_blind_base,
    )
    del p_coupled_cal

    # 3. Ablation control E3 (8 unpulled pixel-local gradient planes + isotropic tip halo)
    X_a, y_a, _, r_a = sample_loqo_from_precomputed(
        X_abl,
        pre,
        train_domain,
        fp,
        ABLATION_ELASTIC_NAMES,
        pre.el_iso_a,
        pre.el_iso_b,
        None,
        n_neg=cfg.n_neg_coupled,
        collar_px=cfg.collar_px,
        neg_buffer_px=cfg.collar_px,
        seed=fold_seed + 41,
    )
    clf_a = _fit_hgb(X_a, y_a, None, seed=fold_seed + 41, max_leaf_nodes=47, max_iter=210, l2_reg=2.5)
    del X_a, y_a
    raw_abl = _predict_chunked(clf_a, X_abl, pre.el_iso_full, ABLATION_ELASTIC_NAMES, fp)
    del clf_a
    p_abl_bayes = elkan_bayes_recalibrate(raw_abl, r_a, valid=fp)
    del raw_abl
    surf_e3_abl = calibrate_quadrant_sparse_posterior(
        p_abl_bayes, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    del p_abl_bayes
    gc.collect()

    return surf_e1_coupled, surf_e2_blind, surf_e3_abl


def fit_predict_shpb_arms(
    X_shpb: np.ndarray,
    L_shpb: np.ndarray,
    X_abl: np.ndarray,
    c_exposure: np.ndarray,
    pre: PrecomputedNestedElastic,
    train_domain: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray,
    allowed: np.ndarray,
    known_faults: np.ndarray,
    cfg: SHPBConfig,
    *,
    fold_seed: int,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
) -> dict[str, tuple[np.ndarray, DinkelbachCELFAllocation | None]]:
    """Fit and allocate all 3 preregistered arms (E1, E2, E3) for one fold."""
    surf_e1, surf_e2, surf_e3 = fit_predict_shpb_fold_surfaces(
        X_shpb,
        L_shpb,
        X_abl,
        c_exposure,
        pre,
        train_domain,
        valid,
        quad,
        cfg,
        fold_seed=fold_seed,
    )
    dc_e1 = dinkelbach_celf_allocate_dots(
        surf_e1,
        allowed,
        known_faults=known_faults,
        valid=valid,
        budget=budget,
        min_spacing_px=min_spacing_px,
        outer_iterations=2,
        candidate_cap=450_000,
    )
    dc_e2 = dinkelbach_celf_allocate_dots(
        surf_e2,
        allowed,
        known_faults=known_faults,
        valid=valid,
        budget=budget,
        min_spacing_px=min_spacing_px,
        outer_iterations=2,
        candidate_cap=350_000,
    )
    dots_e3 = static_ek_spacing_allocate(
        surf_e3,
        allowed,
        known_faults=known_faults,
        valid=valid,
        budget=budget,
        min_spacing_px=min_spacing_px,
        candidate_cap=450_000,
    )
    return {
        "E1_shpb_coupled_dinkelbach_celf": (dc_e1.dots, dc_e1),
        "E2_shpb_blind_conduit_dinkelbach_celf": (dc_e2.dots, dc_e2),
        "E3_local_unpulled_staticek_ablation": (dots_e3, None),
    }


def fit_predict_shpb_full_submission(
    X_shpb: np.ndarray,
    L_shpb: np.ndarray,
    X_abl: np.ndarray,
    c_exposure: np.ndarray,
    full_catalogue: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray,
    cfg: SHPBConfig,
    *,
    erode_px: int = 12,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
) -> dict[str, dict]:
    """Assemble out-of-quadrant full-footprint surfaces across the 4 eroded LOQO training
    domains and decode final 37,654-dot sets for E1, E2, and E3."""
    fp = np.asarray(valid, dtype=bool)
    cat = np.asarray(full_catalogue, dtype=bool) & fp
    pre_full = build_precomputed_nested_elastic(cat, fp, split_seed=cfg.seed + 503)
    allowed = fp & (pre_full.d_vis > cfg.collar_px)

    raw_blind_oof = np.zeros(fp.shape, dtype=np.float32)
    p_coupled_bayes_oof = np.zeros(fp.shape, dtype=np.float32)
    p_abl_bayes_oof = np.zeros(fp.shape, dtype=np.float32)

    for q in range(4):
        train_dom = ndi.binary_erosion((quad >= 0) & (quad != q), iterations=erode_px) & fp
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        f_seed = cfg.seed + 500 + 37 * q

        # Blind model for quadrant q
        X_b, y_b, w_b, _ = sample_loqo_from_precomputed(
            X_shpb,
            pre_full,
            train_dom,
            fp,
            (),
            None,
            None,
            c_exposure,
            n_neg=cfg.n_neg_blind,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.blind_neg_buffer_px,
            seed=f_seed + 1,
        )
        clf_b = _fit_hgb(X_b, y_b, w_b, seed=f_seed + 1, max_leaf_nodes=43, max_iter=210, l2_reg=2.8)
        del X_b, y_b, w_b
        raw_blind_oof[q_mask] = _predict_chunked(clf_b, X_shpb, None, (), q_mask)[q_mask]
        del clf_b

        # Coupled model for quadrant q
        X_c, y_c, w_c, r_c = sample_loqo_from_precomputed(
            X_shpb,
            pre_full,
            train_dom,
            fp,
            SHPB_ELASTIC_NAMES,
            pre_full.el_ksad_a,
            pre_full.el_ksad_b,
            c_exposure,
            n_neg=cfg.n_neg_coupled,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.collar_px,
            seed=f_seed + 5,
        )
        clf_c1 = _fit_hgb(X_c, y_c, w_c, seed=f_seed + 5, max_leaf_nodes=55, max_iter=230, l2_reg=2.5)
        clf_c2 = _fit_hgb(X_c, y_c, w_c, seed=f_seed + 9, max_leaf_nodes=35, max_iter=250, l2_reg=3.5)
        del X_c, y_c, w_c
        p1 = _predict_chunked(clf_c1, X_shpb, pre_full.el_ksad_full, SHPB_ELASTIC_NAMES, q_mask)
        p2 = _predict_chunked(clf_c2, X_shpb, pre_full.el_ksad_full, SHPB_ELASTIC_NAMES, q_mask)
        del clf_c1, clf_c2
        p_cb = elkan_bayes_recalibrate(0.55 * p1 + 0.45 * p2, r_c, valid=q_mask)
        p_coupled_bayes_oof[q_mask] = p_cb[q_mask]
        del p1, p2, p_cb

        # Ablation model for quadrant q
        X_a, y_a, _, r_a = sample_loqo_from_precomputed(
            X_abl,
            pre_full,
            train_dom,
            fp,
            ABLATION_ELASTIC_NAMES,
            pre_full.el_iso_a,
            pre_full.el_iso_b,
            None,
            n_neg=cfg.n_neg_coupled,
            collar_px=cfg.collar_px,
            neg_buffer_px=cfg.collar_px,
            seed=f_seed + 13,
        )
        clf_a = _fit_hgb(X_a, y_a, None, seed=f_seed + 13, max_leaf_nodes=47, max_iter=210, l2_reg=2.5)
        del X_a, y_a
        pa = _predict_chunked(clf_a, X_abl, pre_full.el_iso_full, ABLATION_ELASTIC_NAMES, q_mask)
        del clf_a
        p_ab = elkan_bayes_recalibrate(pa, r_a, valid=q_mask)
        p_abl_bayes_oof[q_mask] = p_ab[q_mask]
        del pa, p_ab
        gc.collect()

    del pre_full
    gc.collect()

    p_blind_hgb = calibrate_quadrant_sparse_posterior(
        raw_blind_oof, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    l_prob = np.clip(0.005 + 0.990 * np.asarray(L_shpb, dtype=np.float32), 1e-4, 0.9999)
    p_corrob_cal = calibrate_quadrant_sparse_posterior(
        l_prob, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    surf_e2 = np.where(
        fp,
        np.clip(
            cfg.blind_hgb_weight * p_blind_hgb + cfg.blind_corrob_weight * p_corrob_cal,
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)

    p_coupled_cal = calibrate_global_sparse_posterior(
        p_coupled_bayes_oof, fp, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    surf_e1 = fuse_cover_aware_shpb(
        p_coupled_cal,
        surf_e2,
        c_exposure,
        fp,
        alpha_coupled=cfg.alpha_coupled,
        alpha_blind_base=cfg.alpha_blind_base,
    )
    surf_e3 = calibrate_quadrant_sparse_posterior(
        p_abl_bayes_oof, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )

    r_e1 = rank01_on_mask(surf_e1, fp)
    surf_e1_alloc = np.where(
        fp, 0.70 * r_e1 + 0.30 * np.asarray(L_shpb, dtype=np.float32), np.float32(0.0)
    ).astype(np.float32)
    r_e2 = rank01_on_mask(surf_e2, fp)
    surf_e2_alloc = np.where(
        fp, 0.58 * r_e2 + 0.42 * np.asarray(L_shpb, dtype=np.float32), np.float32(0.0)
    ).astype(np.float32)

    dc_e1 = dinkelbach_celf_allocate_dots(
        surf_e1_alloc,
        allowed,
        known_faults=cat,
        valid=fp,
        budget=budget,
        min_spacing_px=min_spacing_px,
        outer_iterations=2,
        candidate_cap=500_000,
    )
    dc_e2 = dinkelbach_celf_allocate_dots(
        surf_e2_alloc,
        allowed,
        known_faults=cat,
        valid=fp,
        budget=budget,
        min_spacing_px=min_spacing_px,
        outer_iterations=2,
        candidate_cap=450_000,
    )
    dots_e3 = static_ek_spacing_allocate(
        surf_e3,
        allowed,
        known_faults=cat,
        valid=fp,
        budget=budget,
        min_spacing_px=min_spacing_px,
        candidate_cap=450_000,
    )

    return {
        "E1_shpb_coupled_dinkelbach_celf": {
            "surface": rank01_on_mask(surf_e1_alloc, fp),
            "posterior": surf_e1,
            "dots": dc_e1.dots,
            "allocation": dc_e1,
        },
        "E2_shpb_blind_conduit_dinkelbach_celf": {
            "surface": rank01_on_mask(surf_e2_alloc, fp),
            "posterior": surf_e2,
            "dots": dc_e2.dots,
            "allocation": dc_e2,
        },
        "E3_local_unpulled_staticek_ablation": {
            "surface": rank01_on_mask(surf_e3, fp),
            "posterior": surf_e3,
            "dots": dots_e3,
            "allocation": None,
        },
    }
