"""H86G-EDTI posterior model + E[k]-ranked spacing-greedy emission.

Emission reuses the vendor decision variable ``E[k] = p (x) triangular kernel``
(``gems57.emit.expected_credit``) but replaces the 3 px *tile* decimation with a
true spacing-greedy: candidates are visited in decreasing E[k]; a candidate is
kept only if no kept dot lies within ``min_spacing_px`` (default 2.8 px = the
D2.8 geometry the owner-reported 0.26-0.2778 fleet converged on).  The kept
sequence is nested, so every budget prefix is available from one pass.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

HGB_PARAMS = dict(
    loss="log_loss", max_iter=250, learning_rate=0.07, max_leaf_nodes=63,
    min_samples_leaf=50, l2_regularization=1.0, early_stopping=False,
    random_state=861025,
)


def sample_training(stack, footprint, visible, *, n_neg=480_000, collar_px=3.0,
                    seed=861025):
    """PU-honest sampling: positives = visible catalogue; negatives = footprint
    background beyond the collar (withheld faults, if any, stay unlabelled in
    the background exactly as in the real task -- never used as labels)."""
    rng = np.random.default_rng(seed)
    dvis = ndi.distance_transform_edt(~visible)
    pos_yx = np.argwhere(visible & footprint)
    neg_mask = footprint & (dvis > collar_px)
    neg_yx_all = np.argwhere(neg_mask)
    neg_yx = neg_yx_all[rng.choice(len(neg_yx_all),
                                    size=min(n_neg, len(neg_yx_all)),
                                    replace=False)]
    yx = np.vstack([pos_yx, neg_yx])
    y = np.r_[np.ones(len(pos_yx), np.int8), np.zeros(len(neg_yx), np.int8)]
    X = np.empty((len(yx), stack.shape[0]), np.float32)
    for i in range(stack.shape[0]):
        X[:, i] = stack[i][yx[:, 0], yx[:, 1]]
    w = np.where(y == 1, len(neg_yx) / max(len(pos_yx), 1), 1.0).astype(np.float64)
    return X, y, w, int(len(pos_yx)), int(len(neg_yx))


def fit_posterior(stack, footprint, visible, **kw):
    X, y, w, n_pos, n_neg = sample_training(stack, footprint, visible, **kw)
    clf = HistGradientBoostingClassifier(**HGB_PARAMS)
    clf.fit(X, y, sample_weight=w)
    return clf, {"n_pos": n_pos, "n_neg": n_neg}


def predict_full(clf, stack, footprint, *, block_rows=200) -> np.ndarray:
    """Posterior over footprint pixels; exactly 0 outside the footprint."""
    H, W = footprint.shape
    p = np.zeros((H, W), np.float32)
    F = stack.shape[0]
    for r0 in range(0, H, block_rows):
        r1 = min(H, r0 + block_rows)
        block_fp = footprint[r0:r1]
        if not block_fp.any():
            continue
        Xb = np.empty((int(block_fp.sum()), F), np.float32)
        for i in range(F):
            Xb[:, i] = np.asarray(stack[i][r0:r1])[block_fp]
        p[r0:r1][block_fp] = clf.predict_proba(Xb)[:, 1].astype(np.float32)
    return p


def spacing_greedy_ranking(ek: np.ndarray, allowed: np.ndarray, *,
                           min_spacing_px: float = 2.8,
                           candidate_cap: int = 900_000) -> np.ndarray:
    """Nested dot ranking: ``ranked[y, x] = 1..n`` in acceptance order, 0 else.

    Candidates sorted by decreasing ``ek``; grid-hash (3 px cells) enforces the
    minimum spacing against already-accepted dots only.
    """
    cand = np.asarray(allowed, bool) & (ek > 0)
    ys, xs = np.nonzero(cand)
    if ys.size == 0:
        return np.zeros(ek.shape, np.int32)
    order = np.argsort(-ek[ys, xs], kind="stable")[:candidate_cap]
    ys, xs = ys[order], xs[order]
    ranked = np.zeros(ek.shape, np.int32)
    cell = 3
    buckets: dict[tuple[int, int], list[tuple[int, int]]] = {}
    r2 = float(min_spacing_px) ** 2
    n = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        cy, cx = y // cell, x // cell
        ok = True
        for by in (cy - 1, cy, cy + 1):
            for bx in (cx - 1, cx, cx + 1):
                for (py, px) in buckets.get((by, bx), ()):
                    if (py - y) ** 2 + (px - x) ** 2 < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            n += 1
            ranked[y, x] = n
            buckets.setdefault((cy, cx), []).append((y, x))
    return ranked


def prefix(ranked: np.ndarray, budget: int) -> np.ndarray:
    return (ranked > 0) & (ranked <= int(budget))
