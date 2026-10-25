"""Spatial Leave-One-Quadrant-Out (LOQO) Dual-Regime Positive-Unlabelled specialists
(blind monogenic-geothermal specialist + fold-visible elastic fracture-mechanics
specialist) and Noisy-OR structural fusion for lane H86J-MCSP."""

from __future__ import annotations

import gc
from dataclasses import dataclass
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
class MCSPConfig:
    collar_px: float = 3.0
    blind_neg_buffer_px: float = 8.0
    n_neg_blind: int = 160_000
    n_neg_kin: int = 200_000
    max_iter: int = 200
    learning_rate: float = 0.065
    max_leaf_nodes: int = 47
    min_samples_leaf: int = 110
    l2_regularization: float = 2.5
    blind_hgb_blend: float = 0.55
    blind_corrob_blend: float = 0.45
    alpha_blind: float = 0.50
    alpha_kin: float = 0.65
    seed: int = 861025


def quadrant_grid(shape: tuple[int, int]) -> np.ndarray:
    """Return int8 grid in {0: NW, 1: NE, 2: SW, 3: SE} matching gems57 spatial folds."""
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


def split_visible_components(
    vis_cat: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Balanced disjoint split of 8-connected components for nested cross-component PU."""
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


def _prior_align_prob(
    prob: np.ndarray, mask: np.ndarray, pi_fold: float, pi_global: float
) -> np.ndarray:
    """Align out-of-quadrant logistic posterior to global positive prior (Elkan 2001)
    without forcing artificial equal dot quotas across quadrants."""
    p = np.clip(prob[mask].astype(np.float64), 1e-6, 1.0 - 1e-6)
    pf = float(np.clip(pi_fold, 1e-6, 1.0 - 1e-6))
    pg = float(np.clip(pi_global, 1e-6, 1.0 - 1e-6))
    odds = (p / (1.0 - p)) * ((1.0 - pf) / pf) * (pg / (1.0 - pg))
    out = np.zeros(prob.shape, dtype=np.float32)
    out[mask] = (odds / (1.0 + odds)).astype(np.float32)
    return out


def _make_hgb(cfg: MCSPConfig, seed: int) -> HistGradientBoostingClassifier:
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
    """Fast vectorized gathering from (C, H, W) memmap without full-raster ravel copies."""
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


def fit_predict_loqo_blind(
    X_static: np.ndarray,
    L_corrob: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: MCSPConfig,
    *,
    exclude_train_mask: np.ndarray | None = None,
    pred_mask: np.ndarray | None = None,
    target_quad_id: int | None = None,
) -> np.ndarray:
    """Out-of-quadrant spatial cross-fitted blind monogenic-geothermal specialist."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)
    d_vis = ndi.distance_transform_edt(~vis)

    excl = (
        np.zeros(fp.shape, dtype=bool)
        if exclude_train_mask is None
        else np.asarray(exclude_train_mask, dtype=bool)
    )
    pos_mask = vis & ~excl
    neg_mask = fp & ~excl & (d_vis > cfg.blind_neg_buffer_px)
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

    if target_quad_id is not None:
        tr = q_all != int(target_quad_id)
        clf = _make_hgb(cfg, cfg.seed + 10 + int(target_quad_id))
        clf.fit(X_all[tr], y_all[tr])
        pm = fp if pred_mask is None else (np.asarray(pred_mask, dtype=bool) & fp)
        raw_p = _predict_chunked(clf, X_static, None, (), pm)
        p_cal = rank01_on_mask(raw_p, pm)
        l_cal = rank01_on_mask(L_corrob, pm)
        out = cfg.blind_hgb_blend * p_cal + cfg.blind_corrob_blend * l_cal
        return np.where(pm, np.clip(out, 0.0, 1.0), np.float32(0.0)).astype(np.float32)

    # Full-footprint 4-fold Leave-One-Quadrant-Out prediction (prior-aligned across footprint)
    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    pi_glob = float(y_all.mean())
    for q in range(4):
        tr = q_all != q
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf = _make_hgb(cfg, cfg.seed + 10 + q)
        clf.fit(X_all[tr], y_all[tr])
        raw_q = _predict_chunked(clf, X_static, None, (), q_mask)
        raw_loqo[q_mask] = _prior_align_prob(
            raw_q, q_mask, float(y_all[tr].mean()), pi_glob
        )[q_mask]

    p_loqo = rank01_on_mask(raw_loqo, fp)
    l_cal = rank01_on_mask(L_corrob, fp)
    out = cfg.blind_hgb_blend * p_loqo + cfg.blind_corrob_blend * l_cal
    return np.where(fp, np.clip(out, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_loqo_kinematic(
    X_static: np.ndarray,
    vis_cat: np.ndarray,
    valid: np.ndarray,
    cfg: MCSPConfig,
    elastic_keys: tuple[str, ...],
    *,
    exclude_train_mask: np.ndarray | None = None,
    pred_mask: np.ndarray | None = None,
    target_quad_id: int | None = None,
    precomputed_elastic: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Out-of-quadrant spatial cross-fitted + nested cross-component fracture specialist."""
    fp = np.asarray(valid, dtype=bool)
    vis = np.asarray(vis_cat, dtype=bool) & fp
    quad = quadrant_grid(fp.shape)
    excl = (
        np.zeros(fp.shape, dtype=bool)
        if exclude_train_mask is None
        else np.asarray(exclude_train_mask, dtype=bool)
    )

    rng = np.random.default_rng(cfg.seed + 77)
    d_vis = ndi.distance_transform_edt(~vis)
    neg_pool = np.flatnonzero((fp & ~excl & (d_vis > cfg.collar_px)).ravel())
    del d_vis
    rng.shuffle(neg_pool)
    half_neg = min(cfg.n_neg_kin // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    va, vb = split_visible_components(vis, seed=cfg.seed + 3)

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & fp & ~excl & (db > cfg.collar_px)).ravel())
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
    pos_b = np.flatnonzero((vb & fp & ~excl & (da > cfg.collar_px)).ravel())
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

    if target_quad_id is not None:
        tr = q_all != int(target_quad_id)
        clf = _make_hgb(cfg, cfg.seed + 100 + int(target_quad_id))
        clf.fit(X_all[tr], y_all[tr])
        pm = fp if pred_mask is None else (np.asarray(pred_mask, dtype=bool) & fp)
        raw_p = _predict_chunked(clf, X_static, el_full, elastic_keys, pm)
        return rank01_on_mask(raw_p, pm)

    raw_loqo = np.zeros(fp.shape, dtype=np.float32)
    pi_glob = float(y_all.mean())
    for q in range(4):
        tr = q_all != q
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue
        clf = _make_hgb(cfg, cfg.seed + 100 + q)
        clf.fit(X_all[tr], y_all[tr])
        raw_q = _predict_chunked(clf, X_static, el_full, elastic_keys, q_mask)
        raw_loqo[q_mask] = _prior_align_prob(
            raw_q, q_mask, float(y_all[tr].mean()), pi_glob
        )[q_mask]
    return rank01_on_mask(raw_loqo, fp)


def fuse_dual_noisy_or(
    p_blind: np.ndarray,
    p_kin: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_blind: float = 0.50,
    alpha_kin: float = 0.65,
) -> np.ndarray:
    """Noisy-OR structural probability S = 1 - (1 - a_B P_blind)(1 - a_K P_kin)."""
    fp = np.asarray(valid, dtype=bool)
    pb = np.clip(np.asarray(p_blind, dtype=np.float32), 0.0, 1.0)
    pk = np.clip(np.asarray(p_kin, dtype=np.float32), 0.0, 1.0)
    fused = 1.0 - (1.0 - float(alpha_blind) * pb) * (1.0 - float(alpha_kin) * pk)
    return np.where(fp, np.clip(fused, 0.0, 1.0), np.float32(0.0)).astype(np.float32)
