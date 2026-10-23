"""H86-2 Counterfactual Component-Withheld SAR-PU 3-Family Heterogeneous LOQO Ensemble
(`LightGBM` + `HistGradientBoosting` + `Neural MLP`) & 8-Stratum Seam-Free Calibration.

Enforces strict spatial separation (`35 px = 3.5 km` > max 33 px kernel radius)
around each held-out quadrant so zero feature or label information ever crosses
a quadrant fold boundary.
"""
from __future__ import annotations

import gc
from typing import Dict, List, Tuple

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover - optional in lightweight CI unit tests
    lgb = None  # type: ignore[assignment]
import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import STATIC_60_NAMES
from .wingcrack_network import WINGCRACK_12_NAMES, compute_wingcrack12_fp

ALL_72_NAMES: List[str] = STATIC_60_NAMES + WINGCRACK_12_NAMES
LIDAR_VALID_COL = STATIC_60_NAMES.index("scarp_lid1m_valid_mask")


def _logit(p: np.ndarray) -> np.ndarray:
    pc = np.clip(p.astype(np.float32, copy=False), 1e-6, 1.0 - 1e-6)
    return np.log(pc / (1.0 - pc)).astype(np.float32)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    zc = np.clip(z.astype(np.float32, copy=False), -20.0, 20.0)
    return (1.0 / (1.0 + np.exp(-zc))).astype(np.float32)


def calibrate_8strata_bayes_prior(
    raw_prob_fp: np.ndarray,
    quad_fp: np.ndarray,
    lid_valid_fp: np.ndarray,
    allowed_fp: np.ndarray,
    pi_target: float = 0.0086,
    temperature: float = 0.94,
) -> np.ndarray:
    """Calibrate posterior probabilities across 8 `(Quadrant x 1m-LiDAR-Seam)` strata.

    Because USGS 3DEP 1 m LiDAR coverage (`75.4%`) is an administrative survey
    boundary rather than a tectonic boundary, equalizing the off-catalogue
    discovery prior `pi_target` across `(q, lid)` removes sensor-seam bias and
    prevents Northern Nevada (`NW+NE`) or non-LiDAR basin starvation.
    """
    z = _logit(raw_prob_fp) * np.float32(temperature)
    out = np.zeros_like(z, dtype=np.float32)

    for q in range(4):
        for lid in (0, 1):
            mask = allowed_fp & (quad_fp == q) & ((lid_valid_fp > 0.5) == bool(lid))
            if int(mask.sum()) < 200:
                mask = allowed_fp & (quad_fp == q)
            if not mask.any():
                continue
            zm = z[mask]
            # Subsample for fast exact root-finding of shift `delta` s.t. mean(sigmoid(zm + delta)) == pi_target
            sub = zm[:: max(1, zm.size // 80_000)]
            lo, hi = -16.0, 8.0
            for _ in range(28):
                mid = 0.5 * (lo + hi)
                if float(_sigmoid(sub + np.float32(mid)).mean()) < pi_target:
                    lo = mid
                else:
                    hi = mid
            delta = np.float32(0.5 * (lo + hi))
            target_idx = allowed_fp & (quad_fp == q) & ((lid_valid_fp > 0.5) == bool(lid))
            out[target_idx] = _sigmoid(z[target_idx] + delta)
    return out


def build_counterfactual_splits(
    catalogue_grid: np.ndarray,
    fp: np.ndarray,
    seed: int = 8601,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Partition connected fault components 50/50 into two complementary counterfactual splits.

    Returns `[(sub_vis_A, sub_hid_A), (sub_vis_B, sub_hid_B)]`.
    In each split, `sub_hid` are genuinely withheld whole fault components whose
    off-sub-catalogue pixels (`d(x, sub_vis) > 3.0 px`) mimic unmapped test faults.
    """
    comp, n_comp = ndi.label(catalogue_grid & fp, structure=np.ones((3, 3), dtype=bool))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    half = len(perm) // 2
    set_a = np.isin(comp, perm[:half]) & fp
    set_b = (catalogue_grid & fp) & (~set_a)
    return [(set_a, set_b), (set_b, set_a)]


def _fit_3family_models(X_tr: np.ndarray, y_tr: np.ndarray, seed: int) -> Tuple[object, object, object]:
    m_lgb = lgb.LGBMClassifier(
        n_estimators=260,
        learning_rate=0.045,
        num_leaves=47,
        min_child_samples=80,
        subsample=0.80,
        subsample_freq=1,
        colsample_bytree=0.75,
        reg_alpha=1.0,
        reg_lambda=3.0,
        random_state=seed,
        n_jobs=2,
        verbose=-1,
    )
    m_lgb.fit(X_tr, y_tr)

    m_hgb = HistGradientBoostingClassifier(
        max_iter=220,
        learning_rate=0.05,
        max_leaf_nodes=39,
        min_samples_leaf=90,
        l2_regularization=2.5,
        random_state=seed + 17,
    )
    m_hgb.fit(X_tr, y_tr)

    m_mlp = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            alpha=1.5e-2,
            batch_size=2048,
            learning_rate_init=2.0e-3,
            max_iter=20,
            tol=1e-3,
            early_stopping=True,
            n_iter_no_change=3,
            random_state=seed + 31,
        ),
    )
    m_mlp.fit(X_tr, y_tr)
    return m_lgb, m_hgb, m_mlp


def _predict_3family_chunked(
    models: Tuple[object, object, object],
    static_mm: np.ndarray,
    wc12_fp: np.ndarray | None,
    idx_fp: np.ndarray,
) -> np.ndarray:
    """Predict blended probabilities on `idx_fp` in 350k-row chunks (<140 MB RAM)."""
    m_lgb, m_hgb, m_mlp = models
    n = idx_fp.size
    preds = np.empty(n, dtype=np.float32)
    n_s = static_mm.shape[1]
    n_tot = n_s + (12 if wc12_fp is not None else 0)
    chunk = 350_000

    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        rows = idx_fp[s:e]
        X_c = np.empty((e - s, n_tot), dtype=np.float32)
        X_c[:, :n_s] = static_mm[rows].astype(np.float32)
        if wc12_fp is not None:
            X_c[:, n_s:] = wc12_fp[rows]
        p1 = m_lgb.predict_proba(X_c)[:, 1]
        p2 = m_hgb.predict_proba(X_c)[:, 1]
        p3 = m_mlp.predict_proba(X_c)[:, 1]
        z_blend = 0.48 * _logit(p1) + 0.34 * _logit(p2) + 0.18 * _logit(p3)
        preds[s:e] = _sigmoid(z_blend)
        del X_c
    return preds


def fit_physical_only_loqo(
    static_mm: np.ndarray,
    fp: np.ndarray,
    catalogue_grid: np.ndarray,
    quad_grid: np.ndarray,
    neg_ratio: int = 6,
    seed: int = 8610,
) -> Dict[int, Tuple[object, object, object]]:
    """EXP-86-1: Fit 3-family LOQO models using ONLY the 60 label-free H86-1/H86-4 channels.

    Even for physical-only training, training rows inside quadrant `q` AND within
    `35 px` (`3.5 km`) of quadrant `q` are excluded when fitting fold `q`!
    """
    cat_fp = catalogue_grid[fp]
    # Exclude 1..3 px halo of catalogue from unlabeled negatives (PU safe zone)
    d_cat_fp = ndi.distance_transform_edt(~catalogue_grid)[fp].astype(np.float32)

    models_by_quad: Dict[int, Tuple[object, object, object]] = {}
    rng = np.random.default_rng(seed)

    scarp_or_mimic = (
        (static_mm[:, 40] > 1.0) | (static_mm[:, 48] > 1.0) | (static_mm[:, 54] > 1.0) | (static_mm[:, 57] > 1.0)
    )
    for q in range(4):
        q_dilated = ndi.binary_dilation(quad_grid == q, iterations=35)
        train_elig_fp = (~q_dilated)[fp]

        pos_idx = np.flatnonzero(train_elig_fp & cat_fp)
        neg_pool = np.flatnonzero(train_elig_fp & (d_cat_fp > 3.5))
        n_unif = min(neg_pool.size, int(pos_idx.size * neg_ratio * 0.75))
        neg_unif = rng.choice(neg_pool, size=n_unif, replace=False)
        hard_pool = np.flatnonzero(train_elig_fp & (d_cat_fp > 3.5) & scarp_or_mimic)
        n_hard = min(hard_pool.size, int(pos_idx.size * neg_ratio * 0.25))
        neg_hard = rng.choice(hard_pool, size=n_hard, replace=False) if n_hard > 0 else np.empty(0, dtype=np.int64)
        neg_idx = np.unique(np.concatenate([neg_unif, neg_hard]))

        sel = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(pos_idx.size, dtype=np.int32), np.zeros(neg_idx.size, dtype=np.int32)])
        order = rng.permutation(sel.size)
        sel = sel[order]
        y_tr = y_tr[order]

        X_tr = static_mm[sel].astype(np.float32)
        models_by_quad[q] = _fit_3family_models(X_tr, y_tr, seed=seed + 100 * q)
        del X_tr, sel, y_tr
        gc.collect()
    return models_by_quad


def fit_counterfactual_wingcrack_loqo(
    static_mm: np.ndarray,
    fp: np.ndarray,
    catalogue_grid: np.ndarray,
    quad_grid: np.ndarray,
    neg_ratio: int = 6,
    seed: int = 8620,
) -> Tuple[Dict[int, Tuple[object, object, object]], Dict[str, float]]:
    """EXP-86-2: Fit 3-family SAR-PU LOQO ensemble on 72 channels (`60` physical + `12` wingcrack)
    using dual 50/50 component-withheld counterfactual splits strictly at `d_sub_vis > 3.0 px`
    and `> 35 px` outside each held-out quadrant `q`.
    """
    splits = build_counterfactual_splits(catalogue_grid, fp, seed=seed)
    rng = np.random.default_rng(seed)

    # Extract compact training samples per counterfactual split so we don't hold 2 full 250MB matrices
    split_samples = []
    for s_idx, (sub_vis, sub_hid) in enumerate(splits):
        wc12_fp, d_vis_fp = compute_wingcrack12_fp(sub_vis, fp, static_mm)
        hid_fp = sub_hid[fp]
        off_collar = d_vis_fp > 3.0

        pos_idx = np.flatnonzero(off_collar & hid_fp)
        # Stratified unlabeled background: 75% uniform off-collar + 25% hard high-scarp/mimic negatives
        neg_all = np.flatnonzero(off_collar & (~hid_fp) & (~sub_vis[fp]))
        n_unif = min(neg_all.size, int(pos_idx.size * neg_ratio * 0.75))
        neg_unif = rng.choice(neg_all, size=n_unif, replace=False)

        # Hard negatives where raw scarp or paleoshoreline/road mimic is elevated (> 1.0 z)
        scarp_or_mimic = (
            (static_mm[:, 40] > 1.0) | (static_mm[:, 48] > 1.0) | (static_mm[:, 54] > 1.0) | (static_mm[:, 57] > 1.0)
        )
        hard_pool = np.flatnonzero(off_collar & (~hid_fp) & (~sub_vis[fp]) & scarp_or_mimic)
        n_hard = min(hard_pool.size, int(pos_idx.size * neg_ratio * 0.25))
        neg_hard = rng.choice(hard_pool, size=n_hard, replace=False) if n_hard > 0 else np.empty(0, dtype=np.int64)

        neg_idx = np.unique(np.concatenate([neg_unif, neg_hard]))
        rows = np.concatenate([pos_idx, neg_idx])
        labels = np.concatenate([np.ones(pos_idx.size, dtype=np.int32), np.zeros(neg_idx.size, dtype=np.int32)])

        X_part = np.empty((rows.size, 72), dtype=np.float32)
        X_part[:, :60] = static_mm[rows].astype(np.float32)
        X_part[:, 60:] = wc12_fp[rows]
        split_samples.append((rows, X_part, labels))
        del wc12_fp, d_vis_fp
        gc.collect()

    models_by_quad: Dict[int, Tuple[object, object, object]] = {}
    imp_acc = np.zeros(72, dtype=np.float64)

    for q in range(4):
        # 35 px (3.5 km) erosion exceeds max 33 px kernel radius -> zero cross-quadrant feature bleed!
        q_dilated_fp = ndi.binary_dilation(quad_grid == q, iterations=35)[fp]
        X_list, y_list = [], []
        for rows, X_part, labels in split_samples:
            keep = ~q_dilated_fp[rows]
            X_list.append(X_part[keep])
            y_list.append(labels[keep])
        X_tr = np.vstack(X_list)
        y_tr = np.concatenate(y_list)
        perm = rng.permutation(y_tr.size)
        X_tr = X_tr[perm]
        y_tr = y_tr[perm]

        models = _fit_3family_models(X_tr, y_tr, seed=seed + 200 * q)
        models_by_quad[q] = models
        imp_acc += models[0].booster_.feature_importance(importance_type="gain")
        del X_tr, y_tr
        gc.collect()

    del split_samples
    gc.collect()
    imp_norm = imp_acc / max(float(imp_acc.sum()), 1e-9)
    gain_dict = {ALL_72_NAMES[i]: round(float(imp_norm[i]), 6) for i in range(72)}
    return models_by_quad, gain_dict


def predict_fold_surface(
    models: Tuple[object, object, object],
    static_mm: np.ndarray,
    fp: np.ndarray,
    vis_mask: np.ndarray,
    quad_grid: np.ndarray,
    fold_idx: int | None = None,
    use_wingcrack: bool = True,
    pi_target: float = 0.0086,
    temperature: float = 0.94,
) -> np.ndarray:
    """Predict calibrated probability grid (`float32`, `3730 x 3292`) for one fold or full LOQO."""
    wc12_fp = None
    if use_wingcrack:
        wc12_fp, _ = compute_wingcrack12_fp(vis_mask, fp, static_mm)

    n_fp = int(fp.sum())
    quad_fp = quad_grid[fp]
    lid_fp = static_mm[:, LIDAR_VALID_COL].astype(np.float32)
    allowed_fp = ~vis_mask[fp]

    raw_fp = np.zeros(n_fp, dtype=np.float32)
    if fold_idx is not None:
        idx = np.flatnonzero((quad_fp == fold_idx) & allowed_fp)
        raw_fp[idx] = _predict_3family_chunked(models, static_mm, wc12_fp, idx)
    else:
        raise ValueError("Use predict_full_loqo_surface for full-grid LOQO prediction")

    cal_fp = calibrate_8strata_bayes_prior(
        raw_fp, quad_fp, lid_fp, allowed_fp & (quad_fp == fold_idx), pi_target=pi_target, temperature=temperature
    )
    out = np.zeros(fp.shape, dtype=np.float32)
    out[fp] = cal_fp
    out[vis_mask] = 0.0
    del wc12_fp
    gc.collect()
    return out


def predict_full_loqo_surface(
    models_by_quad: Dict[int, Tuple[object, object, object]],
    static_mm: np.ndarray,
    fp: np.ndarray,
    catalogue_grid: np.ndarray,
    quad_grid: np.ndarray,
    use_wingcrack: bool = True,
    pi_target: float = 0.0086,
    temperature: float = 0.94,
) -> np.ndarray:
    """Predict seamless 4-quadrant out-of-fold production posterior surface on `fp & ~catalogue`."""
    wc12_fp = None
    if use_wingcrack:
        wc12_fp, _ = compute_wingcrack12_fp(catalogue_grid, fp, static_mm)

    n_fp = int(fp.sum())
    quad_fp = quad_grid[fp]
    lid_fp = static_mm[:, LIDAR_VALID_COL].astype(np.float32)
    allowed_fp = ~catalogue_grid[fp]

    raw_fp = np.zeros(n_fp, dtype=np.float32)
    for q in range(4):
        idx = np.flatnonzero((quad_fp == q) & allowed_fp)
        raw_fp[idx] = _predict_3family_chunked(models_by_quad[q], static_mm, wc12_fp, idx)

    cal_fp = calibrate_8strata_bayes_prior(
        raw_fp, quad_fp, lid_fp, allowed_fp, pi_target=pi_target, temperature=temperature
    )
    out = np.zeros(fp.shape, dtype=np.float32)
    out[fp] = cal_fp
    out[catalogue_grid] = 0.0
    del wc12_fp
    gc.collect()
    return out
