"""Strict 4-fold Spatial Leave-One-Quadrant-Out (LOQO) Dual-Regime Specialists
with Quadrant-Tail Sparse Posterior Calibration for Lane H86M-PFTE."""

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
class PFTEConfig:
    collar_px: float = 3.0
    blind_neg_buffer_px: float = 8.0
    n_neg_blind: int = 165_000
    n_neg_kin: int = 200_000
    max_iter: int = 220
    learning_rate: float = 0.055
    max_leaf_nodes: int = 51
    min_samples_leaf: int = 105
    l2_regularization: float = 2.8
    tau0_logit: float = -4.65
    beta_logit: float = 1.72
    blind_hgb_weight: float = 0.64
    blind_corrob_weight: float = 0.36
    alpha_blind: float = 0.56
    alpha_kin: float = 0.68
    seed: int = 861225


def quadrant_grid(shape: tuple[int, int]) -> np.ndarray:
    """Return int8 quadrant IDs {0: NW, 1: NE, 2: SW, 3: SE} matching gems57 folds."""
    h, w = shape
    yy, xx = np.indices((h, w), sparse=True)
    return ((yy >= h // 2).astype(np.int8) * 2 + (xx >= w // 2).astype(np.int8)).astype(
        np.int8
    )


def rank01_on_mask(surface: np.ndarray, mask: np.ndarray) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    out = np.zeros(surface.shape, dtype=np.float32)
    vals = np.asarray(surface[m], dtype=np.float64)
    if vals.size == 0:
        return out
    vals = np.nan_to_num(vals, nan=0.0, posinf=1.0, neginf=0.0)
    if np.ptp(vals) == 0.0:
        out[m] = np.float32(0.5)
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(1e-6, 1.0, vals.size, dtype=np.float32)
    out[m] = ranks
    return out


def calibrate_quadrant_sparse_posterior(
    raw_prob: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray | None = None,
    *,
    tau0: float = -4.65,
    beta: float = 1.72,
) -> np.ndarray:
    """Map raw out-of-quadrant probabilities into a quadrant-invariant sparse fault
    posterior in (0, 1) using ONLY unlabelled score quantiles within each quadrant."""
    fp = np.asarray(valid, dtype=bool)
    q_grid = quadrant_grid(fp.shape) if quad is None else np.asarray(quad, dtype=np.int8)
    out = np.zeros(fp.shape, dtype=np.float32)

    for q in range(4):
        qm = fp & (q_grid == q)
        if not qm.any():
            continue
        p = np.clip(raw_prob[qm].astype(np.float64), 1e-6, 1.0 - 1e-6)
        ell = np.log(p / (1.0 - p))
        med = float(np.median(ell))
        p90 = float(np.percentile(ell, 90.0))
        scale = max(p90 - med, 1e-4)
        z = np.clip((ell - med) / scale, -6.0, 8.5)
        logits = float(tau0) + float(beta) * z
        out[qm] = (1.0 / (1.0 + np.exp(-logits))).astype(np.float32)
    return out


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


def _make_hgb(cfg: PFTEConfig, seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=cfg.max_iter,
        learning_rate=cfg.learning_rate,
        max_leaf_nodes=cfg.max_leaf_nodes,
        min_samples_leaf=cfg.min_samples_leaf,
        l2_regularization=cfg.l2_regularization,
        random_state=seed,
    )


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


def fit_predict_loqo_blind_pfte(
    X_static: np.ndarray,
    L_corrob: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: PFTEConfig,
) -> np.ndarray:
    """Strict 4-fold Leave-One-Quadrant-Out blind PFTE physical/geothermal specialist."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)
    d_vis = ndi.distance_transform_edt(~vis)

    pos_mask = vis
    neg_mask = fp & (d_vis > cfg.blind_neg_buffer_px)
    del d_vis

    rng = np.random.default_rng(cfg.seed)
    pos_idx = np.flatnonzero(pos_mask.ravel())
    neg_pool = np.flatnonzero(neg_mask.ravel())
    neg_idx = rng.choice(
        neg_pool, size=min(cfg.n_neg_blind, neg_pool.size), replace=False
    )
    all_idx = np.concatenate([pos_idx, neg_idx])
    y_all = np.concatenate(
        [np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)]
    )
    q_all = quad.ravel()[all_idx]
    X_all = _extract_rows(X_static, all_idx)

    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        tr = q_all != q
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf = _make_hgb(cfg, cfg.seed + 10 + q)
        clf.fit(X_all[tr], y_all[tr])
        raw_loqo[q_mask] = _predict_chunked(clf, X_static, None, (), q_mask)[q_mask]

    p_hgb_cal = calibrate_quadrant_sparse_posterior(
        raw_loqo, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    l_prob = np.clip(0.005 + 0.990 * np.asarray(L_corrob, dtype=np.float32), 1e-4, 0.9999)
    p_corrob_cal = calibrate_quadrant_sparse_posterior(
        l_prob, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    fused_blind = cfg.blind_hgb_weight * p_hgb_cal + cfg.blind_corrob_weight * p_corrob_cal
    return np.where(fp, np.clip(fused_blind, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_loqo_kinematic_pfte(
    X_static: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: PFTEConfig,
    elastic_keys: tuple[str, ...],
    *,
    precomputed_elastic: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Strict 4-fold Leave-One-Quadrant-Out + nested cross-component fracture specialist."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)

    rng = np.random.default_rng(cfg.seed + 77)
    d_vis = ndi.distance_transform_edt(~vis)
    neg_pool = np.flatnonzero((fp & (d_vis > cfg.collar_px)).ravel())
    del d_vis
    rng.shuffle(neg_pool)
    half_neg = min(cfg.n_neg_kin // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    va, vb = split_visible_components(vis, seed=cfg.seed + 3)

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & fp & (db > cfg.collar_px)).ravel())
    del db
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate(
        [np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)]
    )
    qa = quad.ravel()[idx_a]
    el_b = compute_elastic_fields(vb, fp)
    Xa = _extract_rows(X_static, idx_a, el_b, elastic_keys)
    del el_b, pos_a, neg_a, idx_a
    gc.collect()

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & fp & (da > cfg.collar_px)).ravel())
    del da, vb
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate(
        [np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)]
    )
    qb = quad.ravel()[idx_b]
    el_a = compute_elastic_fields(va, fp)
    del va
    Xb = _extract_rows(X_static, idx_b, el_a, elastic_keys)
    del el_a, pos_b, neg_b, idx_b
    gc.collect()

    X_all = np.vstack([Xa, Xb])
    y_all = np.concatenate([ya, yb])
    q_all = np.concatenate([qa, qb])
    del Xa, Xb, ya, yb, qa, qb

    el_full = (
        precomputed_elastic
        if precomputed_elastic is not None
        else compute_elastic_fields(vis, fp)
    )

    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        tr = q_all != q
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf = _make_hgb(cfg, cfg.seed + 100 + q)
        clf.fit(X_all[tr], y_all[tr])
        raw_loqo[q_mask] = _predict_chunked(clf, X_static, el_full, elastic_keys, q_mask)[q_mask]

    return calibrate_quadrant_sparse_posterior(
        raw_loqo, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )


def fuse_calibrated_noisy_or(
    p_blind: np.ndarray,
    p_kin: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_blind: float = 0.56,
    alpha_kin: float = 0.68,
) -> np.ndarray:
    """Noisy-OR probability fusion S = 1 - (1 - a_B P_blind)(1 - a_K P_kin)."""
    fp = np.asarray(valid, dtype=bool)
    pb = np.clip(np.asarray(p_blind, dtype=np.float32), 0.0, 1.0)
    pk = np.clip(np.asarray(p_kin, dtype=np.float32), 0.0, 1.0)
    fused = 1.0 - (1.0 - float(alpha_blind) * pb) * (1.0 - float(alpha_kin) * pk)
    return np.where(fp, np.clip(fused, 0.0, 1.0), np.float32(0.0)).astype(np.float32)
