"""H86S-DWPU feature stack + completeness + HGB training (frozen preregistration).

11 catalogue-free native-band planes. The catalogue enters ONLY as training
labels (visible-only inside holdout) and the emission collar. Completeness
c(x) is built from Bands 15/19 percentile ranks; it weights NEGATIVE samples
only (E1/E3), never positives, and is not itself a model feature in E3.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

SENTINEL = -3.4028234663852886e38
FEATURE_NAMES = (
    "dwpu_rtp_b2", "dwpu_tmi_hg_b3_abs", "dwpu_grav_slope_b5", "dwpu_tc_b6",
    "dwpu_grav_south_b11", "dwpu_grav_b13", "dwpu_basement_b15",
    "dwpu_grav_east_b18", "dwpu_slope_b19", "dwpu_rtp_gradmag",
    "dwpu_basement_gradmag",
)
COVER_FEATURES = ("dwpu_basement_b15", "dwpu_slope_b19")  # excluded in E3
SEED = 20261027


def clean(band: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(band, dtype=np.float32)
    ok = fp & np.isfinite(a) & (a > SENTINEL * 0.5)
    return np.where(ok, a, 0.0).astype(np.float32), ok


def rank01(values: np.ndarray, ok: np.ndarray) -> np.ndarray:
    out = np.zeros(values.shape, np.float32)
    v = values[ok].astype(np.float64)
    if v.size == 0:
        return out
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, np.float64)
    ranks[order] = np.arange(v.size)
    out[ok] = (ranks / max(v.size - 1, 1)).astype(np.float32)
    return out


def _gradmag(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a)
    return np.hypot(gx, gy).astype(np.float32)


def build_stack(read_band, fp: np.ndarray) -> dict[str, np.ndarray]:
    """read_band(index) -> array. Returns the 11 frozen planes (float32)."""
    planes: dict[str, np.ndarray] = {}
    raw: dict[int, np.ndarray] = {}
    oks: dict[int, np.ndarray] = {}
    for idx in (2, 3, 5, 6, 11, 13, 15, 18, 19):
        raw[idx], oks[idx] = clean(read_band(idx), fp)
    planes["dwpu_rtp_b2"] = raw[2]
    planes["dwpu_tmi_hg_b3_abs"] = np.abs(raw[3]).astype(np.float32)
    planes["dwpu_grav_slope_b5"] = raw[5]
    planes["dwpu_tc_b6"] = raw[6]
    planes["dwpu_grav_south_b11"] = raw[11]
    planes["dwpu_grav_b13"] = raw[13]
    planes["dwpu_basement_b15"] = raw[15]
    planes["dwpu_grav_east_b18"] = raw[18]
    planes["dwpu_slope_b19"] = raw[19]
    sm = ndi.gaussian_filter(raw[2], 1.5, mode="nearest")
    planes["dwpu_rtp_gradmag"] = _gradmag(sm)
    del sm
    sm = ndi.gaussian_filter(raw[15], 1.5, mode="nearest")
    planes["dwpu_basement_gradmag"] = _gradmag(sm)
    del sm
    return planes


def completeness(planes: dict[str, np.ndarray], fp: np.ndarray) -> np.ndarray:
    """c in [0,1]: shallow basement + steep slope = mapping-complete."""
    depth_rank = rank01(planes["dwpu_basement_b15"], fp)
    slope_rank = rank01(planes["dwpu_slope_b19"], fp)
    c = 0.6 * (1.0 - depth_rank) + 0.4 * slope_rank
    return np.clip(c, 0.0, 1.0).astype(np.float32)


def stack_matrix(planes: dict[str, np.ndarray], names, fp: np.ndarray) -> np.ndarray:
    """(n_fp_pixels, n_features) float32 matrix in footprint flat order."""
    cols = [planes[n].ravel()[fp.ravel()].astype(np.float32) for n in names]
    return np.column_stack(cols).astype(np.float32)


def train_predict(planes, names, labels: np.ndarray, fp: np.ndarray,
                  comp: np.ndarray, weighted: bool,
                  n_neg: int = 250_000) -> np.ndarray:
    """Train HGB on sampled pixels, predict probability on the full footprint.

    labels: bool positive mask (visible-only for holdout, full for final).
    Negative pool excludes a 3-px dilation of labels. Robust standardization
    (median/IQR) is estimated on the training sample only.
    """
    rng = np.random.default_rng(SEED)
    pos_idx = np.flatnonzero((labels & fp).ravel())
    dilated = ndi.binary_dilation(labels, iterations=3)
    neg_pool = np.flatnonzero((fp & ~dilated).ravel())
    neg_idx = rng.choice(neg_pool, size=min(n_neg, neg_pool.size), replace=False)
    fp_flat = np.flatnonzero(fp.ravel())
    fp_pos = {int(v): i for i, v in enumerate(fp_flat.tolist())}
    # Map grid-flat index -> row in footprint matrix without a giant dict:
    # footprint rows are sorted flat indices, so searchsorted is exact.
    def rows_of(grid_flat):
        r = np.searchsorted(fp_flat, grid_flat)
        assert np.array_equal(fp_flat[r], grid_flat)
        return r
    Xfull = stack_matrix(planes, names, fp)
    X = np.vstack([Xfull[rows_of(pos_idx)], Xfull[rows_of(neg_idx)]]).astype(np.float32)
    y = np.r_[np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)]
    if weighted:
        w_pos = np.ones(pos_idx.size, np.float64)
        w_neg = 0.05 + 0.95 * comp.ravel()[neg_idx].astype(np.float64)
        w = np.r_[w_pos, w_neg]
    else:
        w = np.ones(y.size, np.float64)
    med = np.median(X, axis=0)
    q25, q75 = np.percentile(X, [25, 75], axis=0)
    iqr = np.where((q75 - q25) > 0, q75 - q25, 1.0)
    Xs = ((X - med) / iqr).astype(np.float32)
    clf = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.06, max_leaf_nodes=31,
        min_samples_leaf=50, l2_regularization=0.1, random_state=SEED)
    clf.fit(Xs, y, sample_weight=w)
    surf = np.zeros(fp.shape, np.float32)
    proba = np.empty(Xfull.shape[0], np.float32)
    for s in range(0, Xfull.shape[0], 500_000):
        chunk = ((Xfull[s:s + 500_000] - med) / iqr).astype(np.float32)
        proba[s:s + 500_000] = clf.predict_proba(chunk)[:, 1].astype(np.float32)
    surf.ravel()[fp_flat] = proba
    return surf
