"""Strict 4-fold Leave-One-Quadrant-Out (LOQO) Specialists, Elkan (2001) Bayes
Subsampling Recalibration, and 8-Azimuth Axial Geodesic Strand Coherence for
Lane H86M-BMGS.

Directly fixes three structural failure modes diagnosed across the 92-repo fleet:
  1. High-floor quantile calibration dilution (H86K-STDP mapped median background
     pixels to p ~= 0.0105, inflating background kernel credit): replaced by exact
     Elkan (2001) case-control Bayes odds recalibration with mild zero-label
     quadrant median stabilization so background desert stays at true sparse
     p ~= 0.0007-0.0015 while sharp fault crests reach 0.40-0.75.
  2. Near-catalogue PU halo crowding (GEMSDOE91 S17-LFTG = 0.1823 placed 68.5% of
     dots < 1 km from existing_faults.tif): P_blind is trained 100% without elastic
     catalogue features and without raw 100 m DEM (Bands 12/19), then sharpened along
     local GSST geophysical fault strike theta_hat.
  3. Probability-space 8-azimuth axial geodesic strand coherence boosts collinear
     600 m fault strands over isolated 1-pixel noise speckles without multiplicatively
     penalizing curved 1-pixel fault traces.
"""

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

from gems86_ewcs.features import compute_elastic_fields


@dataclass(frozen=True)
class BMGSConfig:
    collar_px: float = 3.0
    blind_neg_buffer_px: float = 8.0
    domain_erode_px: int = 12
    n_neg_blind: int = 180_000
    n_neg_kin: int = 200_000
    max_iter: int = 210
    learning_rate: float = 0.055
    max_leaf_nodes: int = 51
    min_samples_leaf: int = 95
    l2_regularization: float = 2.5
    blind_hgb_weight: float = 0.90
    blind_corrob_weight: float = 0.10
    strand_along_weight: float = 0.24
    strand_contrast_weight: float = 0.14
    alpha_blind: float = 0.46
    alpha_kin: float = 0.78
    seed: int = 861325


def quadrant_grid(shape: tuple[int, int]) -> np.ndarray:
    """Return int8 quadrant IDs {0: NW, 1: NE, 2: SW, 3: SE} matching gems57 folds."""
    h, w = shape
    yy, xx = np.indices((h, w), sparse=True)
    return ((yy >= h // 2).astype(np.int8) * 2 + (xx >= w // 2).astype(np.int8)).astype(
        np.int8
    )


def elkan_quadrant_aligned_posterior(
    raw_prob: np.ndarray,
    neg_subsample_ratio: float,
    valid: np.ndarray,
    quad: np.ndarray | None = None,
    *,
    quad_align_strength: float = 0.15,
) -> np.ndarray:
    """Apply Elkan (2001) case-control Bayes subsampling odds correction with
    gentle zero-label quadrant-median stabilization.

    Given negative subsampling factor ``r = N_neg_pool / N_neg_sampled >= 1``,
    Bayes' theorem gives ``p_bayes = p_raw / (p_raw + r * (1 - p_raw))``
    (equivalently ``ell_bayes = logit(p_raw) - log(r)``).
    """
    fp = np.asarray(valid, dtype=bool)
    out = np.zeros(fp.shape, dtype=np.float32)
    if not fp.any():
        return out

    r = max(float(neg_subsample_ratio), 1.0)
    p = np.clip(np.asarray(raw_prob, dtype=np.float32), 1e-6, 1.0 - 1e-6)
    ell = np.log(p / (1.0 - p)) - np.float32(np.log(r))

    if quad_align_strength > 0.0:
        q_grid = quadrant_grid(fp.shape) if quad is None else np.asarray(quad, dtype=np.int8)
        global_med = float(np.median(ell[fp]))
        for q in range(4):
            qm = fp & (q_grid == q)
            if not qm.any():
                continue
            q_med = float(np.median(ell[qm]))
            ell_q = np.clip(
                ell[qm] - float(quad_align_strength) * (q_med - global_med), -14.0, 10.0
            )
            out[qm] = (1.0 / (1.0 + np.exp(-ell_q))).astype(np.float32)
    else:
        ell_c = np.clip(ell[fp], -14.0, 10.0)
        out[fp] = (1.0 / (1.0 + np.exp(-ell_c))).astype(np.float32)
    return out


def _sparse_strand_offsets(
    theta_rad: float,
    *,
    radius: int = 3,
    sigma_along: float = 2.4,
    sigma_across: float = 0.65,
) -> list[tuple[int, int, float]]:
    """Build sparse normalized 7x7 directional strand offsets along strike theta_rad
    (excluding center (0,0) so strand support reflects genuine neighbouring continuity)."""
    ct = float(np.cos(theta_rad))  # col (east) unit component
    st = float(np.sin(theta_rad))  # row (south) unit component
    entries: list[tuple[int, int, float]] = []
    w_sum = 0.0
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            s_along = dc * ct + dr * st
            s_across = -dc * st + dr * ct
            w = float(
                np.exp(
                    -0.5 * (s_along / sigma_along) ** 2
                    - 0.5 * (s_across / sigma_across) ** 2
                )
            )
            if w >= 0.05:
                entries.append((dr, dc, w))
                w_sum += w
    if w_sum <= 0.0:
        return [(0, 1, 0.5), (0, -1, 0.5)]
    return [(dr, dc, w / w_sum) for dr, dc, w in entries]


def _convolve_sparse_offsets(arr: np.ndarray, offsets: list[tuple[int, int, float]]) -> np.ndarray:
    h, w = arr.shape
    acc = np.zeros((h, w), dtype=np.float32)
    w_norm = np.zeros((h, w), dtype=np.float32)
    for dr, dc, wt in offsets:
        dst_r0, dst_r1 = max(0, -dr), min(h, h - dr)
        dst_c0, dst_c1 = max(0, -dc), min(w, w - dc)
        src_r0, src_r1 = dst_r0 + dr, dst_r1 + dr
        src_c0, src_c1 = dst_c0 + dc, dst_c1 + dc
        w32 = np.float32(wt)
        acc[dst_r0:dst_r1, dst_c0:dst_c1] += w32 * arr[src_r0:src_r1, src_c0:src_c1]
        w_norm[dst_r0:dst_r1, dst_c0:dst_c1] += w32
    return acc / np.maximum(w_norm, np.float32(1e-6))


def axial_geodesic_strand_sharpen(
    prob_bayes: np.ndarray,
    theta_strike: np.ndarray,
    valid: np.ndarray,
    *,
    along_weight: float = 0.24,
    contrast_weight: float = 0.14,
    n_azimuths: int = 8,
) -> np.ndarray:
    """Sharpen sparse fault posteriors along local GSST geophysical strike theta_strike
    in probability space (additive strand reinforcement).

    Unlike log-odds geometric averaging (which multiplicatively zeroes curved 1-px
    faults whenever any stencil point hits background desert), probability-space
    directional integration preserves 1-px curved fault crests while boosting
    collinear strands over isolated 1-pixel noise speckles.
    """
    fp = np.asarray(valid, dtype=bool)
    if not fp.any():
        return np.zeros(fp.shape, dtype=np.float32)

    p = np.where(fp, np.clip(np.asarray(prob_bayes, dtype=np.float32), 0.0, 1.0), np.float32(0.0))

    th = np.mod(np.asarray(theta_strike, dtype=np.float32), np.float32(np.pi))
    bin_f = th * np.float32(n_azimuths / np.pi)
    k0 = np.floor(bin_f).astype(np.int32) % n_azimuths
    frac = (bin_f - np.floor(bin_f)).astype(np.float32)

    along_interp = np.zeros(fp.shape, dtype=np.float32)
    orth_interp = np.zeros(fp.shape, dtype=np.float32)

    dir_responses: list[np.ndarray] = []
    for k in range(n_azimuths):
        th_k = float(k * np.pi / n_azimuths)
        offs = _sparse_strand_offsets(th_k)
        dir_responses.append(_convolve_sparse_offsets(p, offs))

    half_az = n_azimuths // 2
    for k in range(n_azimuths):
        k_next = (k + 1) % n_azimuths
        m0 = k0 == k
        if not np.any(m0):
            continue
        f_m = frac[m0]
        along_interp[m0] = (1.0 - f_m) * dir_responses[k][m0] + f_m * dir_responses[k_next][m0]
        ko = (k + half_az) % n_azimuths
        ko_next = (k_next + half_az) % n_azimuths
        orth_interp[m0] = (1.0 - f_m) * dir_responses[ko][m0] + f_m * dir_responses[ko_next][m0]
    del dir_responses

    w_a = float(along_weight)
    w_c = float(contrast_weight)
    strand_excess = np.maximum(along_interp - orth_interp, 0.0)
    p_sharp = (1.0 - w_a) * p + w_a * along_interp + w_c * strand_excess
    return np.where(fp, np.clip(p_sharp, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def split_visible_components(
    vis_cat: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Balanced disjoint split of 8-connected components for cross-component PU."""
    comp, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=int))
    if n_comp < 2:
        half = vis_cat.shape[0] // 2
        va = vis_cat.copy()
        vb = vis_cat.copy()
        va[half:, :] = False
        vb[:half, :] = False
        return va, vb
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    set_a = np.zeros(n_comp + 1, dtype=bool)
    set_a[perm[::2]] = True
    va = set_a[comp]
    vb = (~set_a)[comp] & (comp > 0)
    return va, vb


def _make_hgb(
    cfg: BMGSConfig, seed: int, *, max_leaf_nodes: int | None = None
) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=cfg.max_iter,
        learning_rate=cfg.learning_rate,
        max_leaf_nodes=cfg.max_leaf_nodes if max_leaf_nodes is None else max_leaf_nodes,
        min_samples_leaf=cfg.min_samples_leaf,
        l2_regularization=cfg.l2_regularization,
        early_stopping=False,
        random_state=seed,
    )


def _eroded_train_quadrant_masks(quad: np.ndarray, valid: np.ndarray, erode_px: int) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    for q in range(4):
        raw_tr = (quad >= 0) & (quad != q)
        if erode_px > 0:
            er = ndi.binary_erosion(raw_tr, iterations=erode_px) & valid
            if not er.any():
                er = raw_tr & valid
        else:
            er = raw_tr & valid
        out.append(er)
    return out


def _extract_rows(
    X_static: np.ndarray,
    flat_idx: np.ndarray,
    elastic_planes: dict[str, np.ndarray] | None = None,
    elastic_keys: tuple[str, ...] = (),
) -> np.ndarray:
    n_s, _, w = X_static.shape
    ys, xs = np.divmod(flat_idx, w)
    n_e = len(elastic_keys) if elastic_planes is not None else 0
    out = np.empty((flat_idx.size, n_s + n_e), dtype=np.float32)
    out[:, :n_s] = X_static[:, ys, xs].T.astype(np.float32)
    if n_e and elastic_planes is not None:
        for j, k in enumerate(elastic_keys):
            out[:, n_s + j] = elastic_planes[k][ys, xs].astype(np.float32)
    return out


def _predict_chunked_pair(
    clfs: list[HistGradientBoostingClassifier],
    weights: tuple[float, ...],
    X_static: np.ndarray,
    elastic_planes: dict[str, np.ndarray] | None,
    elastic_keys: tuple[str, ...],
    pred_mask: np.ndarray,
    chunk_rows: int = 384,
) -> np.ndarray:
    n_s, h, w = X_static.shape
    n_e = len(elastic_keys) if elastic_planes is not None else 0
    out = np.zeros((h, w), dtype=np.float32)
    for r0 in range(0, h, chunk_rows):
        r1 = min(h, r0 + chunk_rows)
        m = pred_mask[r0:r1]
        n_m = int(m.sum())
        if n_m == 0:
            continue
        X_chunk = np.empty((n_m, n_s + n_e), dtype=np.float32)
        X_chunk[:, :n_s] = np.moveaxis(X_static[:, r0:r1, :], 0, -1)[m].astype(np.float32)
        if n_e and elastic_planes is not None:
            for j, k in enumerate(elastic_keys):
                X_chunk[:, n_s + j] = elastic_planes[k][r0:r1][m].astype(np.float32)
        acc = np.zeros(n_m, dtype=np.float32)
        for clf, wt in zip(clfs, weights):
            acc += np.float32(wt) * clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
        blk = out[r0:r1]
        blk[m] = acc
    return out


def fit_predict_loqo_blind_bmgs(
    X_static: np.ndarray,
    theta_strike: np.ndarray,
    L_corrob: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: BMGSConfig,
) -> np.ndarray:
    """Strict 4-fold Leave-One-Quadrant-Out (12-px eroded boundary) cover-blind
    specialist + Elkan Bayes recalibration + probability-space axial strand sharpening."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)
    train_domains = _eroded_train_quadrant_masks(quad, fp, cfg.domain_erode_px)

    d_vis = ndi.distance_transform_edt(~vis)
    neg_mask = fp & (d_vis > cfg.blind_neg_buffer_px)
    del d_vis

    rng = np.random.default_rng(cfg.seed)
    pos_idx = np.flatnonzero(vis.ravel())
    neg_pool = np.flatnonzero(neg_mask.ravel())
    n_neg_sample = min(cfg.n_neg_blind, neg_pool.size)
    neg_idx = rng.choice(neg_pool, size=n_neg_sample, replace=False)
    neg_sub_ratio = float(neg_pool.size) / max(float(n_neg_sample), 1.0)
    del neg_pool

    all_idx = np.concatenate([pos_idx, neg_idx])
    y_all = np.concatenate(
        [np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)]
    )
    X_all = _extract_rows(X_static, all_idx)

    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        tr = train_domains[q].ravel()[all_idx]
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf1 = _make_hgb(cfg, cfg.seed + 10 + q, max_leaf_nodes=47)
        clf1.fit(X_all[tr], y_all[tr])
        raw_loqo[q_mask] = _predict_chunked_pair(
            [clf1], (1.0,), X_static, None, (), q_mask
        )[q_mask]

    p_hgb = elkan_quadrant_aligned_posterior(
        raw_loqo, neg_sub_ratio, fp, quad, quad_align_strength=0.15
    )

    l_rank = np.clip(np.asarray(L_corrob, dtype=np.float32), 0.0, 1.0)
    p_corrob = np.where(fp, 0.0007 * np.exp(5.5 * (l_rank**2)), np.float32(0.0)).astype(
        np.float32
    )
    p_corrob = np.clip(p_corrob, 0.0, 0.35)

    p_mix = cfg.blind_hgb_weight * p_hgb + cfg.blind_corrob_weight * p_corrob
    p_strand = axial_geodesic_strand_sharpen(
        p_mix,
        theta_strike,
        fp,
        along_weight=cfg.strand_along_weight,
        contrast_weight=cfg.strand_contrast_weight,
    )
    return np.where(fp, np.clip(p_strand, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_loqo_kinematic_bmgs(
    X_static: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: BMGSConfig,
    elastic_keys: tuple[str, ...],
    *,
    precomputed_elastic: dict[str, np.ndarray] | None = None,
    two_seed_ensemble: bool = True,
) -> np.ndarray:
    """Strict 4-fold LOQO (12-px eroded boundary) + nested cross-component fracture
    specialist calibrated via Elkan (2001) Bayes subsampling odds."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)
    train_domains = _eroded_train_quadrant_masks(quad, fp, cfg.domain_erode_px)

    rng = np.random.default_rng(cfg.seed + 77)
    d_vis = ndi.distance_transform_edt(~vis)
    neg_pool = np.flatnonzero((fp & (d_vis > cfg.collar_px)).ravel())
    n_neg_total = neg_pool.size
    del d_vis
    rng.shuffle(neg_pool)
    half_neg = min(cfg.n_neg_kin // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg : 2 * half_neg]
    neg_sub_ratio = float(n_neg_total) / max(float(2 * half_neg), 1.0)
    del neg_pool

    va, vb = split_visible_components(vis, seed=cfg.seed + 3)

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & fp & (db > cfg.collar_px)).ravel())
    del db
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate(
        [np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)]
    )
    el_b = compute_elastic_fields(vb, fp)
    Xa = _extract_rows(X_static, idx_a, el_b, elastic_keys)
    del el_b, pos_a, neg_a
    gc.collect()

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & fp & (da > cfg.collar_px)).ravel())
    del da, vb
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate(
        [np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)]
    )
    el_a = compute_elastic_fields(va, fp)
    del va
    Xb = _extract_rows(X_static, idx_b, el_a, elastic_keys)
    del el_a, pos_b, neg_b
    gc.collect()

    all_idx = np.concatenate([idx_a, idx_b])
    X_all = np.vstack([Xa, Xb])
    y_all = np.concatenate([ya, yb])
    del idx_a, idx_b, Xa, Xb, ya, yb

    el_full = (
        precomputed_elastic
        if precomputed_elastic is not None
        else compute_elastic_fields(vis, fp)
    )

    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        tr = train_domains[q].ravel()[all_idx]
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf1 = _make_hgb(cfg, cfg.seed + 100 + q, max_leaf_nodes=55)
        clf1.fit(X_all[tr], y_all[tr])
        if two_seed_ensemble:
            clf2 = _make_hgb(cfg, cfg.seed + 200 + q, max_leaf_nodes=35)
            clf2.fit(X_all[tr], y_all[tr])
            raw_loqo[q_mask] = _predict_chunked_pair(
                [clf1, clf2], (0.55, 0.45), X_static, el_full, elastic_keys, q_mask
            )[q_mask]
        else:
            raw_loqo[q_mask] = _predict_chunked_pair(
                [clf1], (1.0,), X_static, el_full, elastic_keys, q_mask
            )[q_mask]

    return elkan_quadrant_aligned_posterior(
        raw_loqo, neg_sub_ratio, fp, quad, quad_align_strength=0.0
    )


def fuse_bmgs_noisy_or(
    p_blind_strand: np.ndarray,
    p_kin: np.ndarray,
    theta_strike: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_blind: float = 0.46,
    alpha_kin: float = 0.78,
) -> np.ndarray:
    """Far-field-preserving Noisy-OR + max-lift fusion followed by mild axial strand coherence."""
    fp = np.asarray(valid, dtype=bool)
    pb = np.clip(np.asarray(p_blind_strand, dtype=np.float32), 0.0, 1.0)
    pk = np.clip(np.asarray(p_kin, dtype=np.float32), 0.0, 1.0)
    noisy_or = 1.0 - (1.0 - float(alpha_blind) * pb) * (1.0 - float(alpha_kin) * pk)
    fused = 0.75 * noisy_or + 0.25 * np.maximum(pk, 0.85 * pb)
    fused_strand = axial_geodesic_strand_sharpen(
        fused, theta_strike, fp, along_weight=0.14, contrast_weight=0.08
    )
    return np.where(fp, np.clip(fused_strand, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_bmgs_arms_fold(
    X_bmgs: np.ndarray,
    theta_strike: np.ndarray,
    L_bmgs: np.ndarray,
    X_abl: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: BMGSConfig,
    elastic_keys: tuple[str, ...],
    *,
    precomputed_elastic: dict[str, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit and predict strict 4-quadrant eroded-LOQO surfaces (E1, E2_blind, E3_ablation)."""
    p_blind = fit_predict_loqo_blind_bmgs(
        X_bmgs, theta_strike, L_bmgs, vis_cat, valid, cfg
    )
    p_kin = fit_predict_loqo_kinematic_bmgs(
        X_bmgs,
        vis_cat,
        valid,
        cfg,
        elastic_keys,
        precomputed_elastic=precomputed_elastic,
        two_seed_ensemble=True,
    )
    surf_e1 = fuse_bmgs_noisy_or(
        p_blind,
        p_kin,
        theta_strike,
        valid,
        alpha_blind=cfg.alpha_blind,
        alpha_kin=cfg.alpha_kin,
    )
    surf_e3 = fit_predict_loqo_kinematic_bmgs(
        X_abl,
        vis_cat,
        valid,
        cfg,
        ("iso_tip_halo",),
        precomputed_elastic=precomputed_elastic,
        two_seed_ensemble=False,
    )
    return surf_e1, p_blind, surf_e3


def fit_predict_bmgs_full_surface(
    X_bmgs: np.ndarray,
    theta_strike: np.ndarray,
    L_bmgs: np.ndarray,
    X_abl: np.ndarray,
    full_catalogue: np.ndarray,
    valid: np.ndarray,
    cfg: BMGSConfig,
    elastic_keys: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit full-footprint LOQO surfaces (E1, E2_blind, E3_ablation) on full catalogue."""
    el_full = compute_elastic_fields(full_catalogue & valid, valid)
    return fit_predict_bmgs_arms_fold(
        X_bmgs,
        theta_strike,
        L_bmgs,
        X_abl,
        full_catalogue,
        valid,
        cfg,
        elastic_keys,
        precomputed_elastic=el_full,
    )
