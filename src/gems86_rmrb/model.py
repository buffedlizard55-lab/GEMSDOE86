"""Fold-proper positive/unlabelled learner and deterministic sparse emitter."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

SEED = 86022


def _matrix(features, indices, columns):
    """Gather (pixel, channel) rows from a channel-major memmap."""
    return np.asarray(features[np.asarray(columns, int)][:, np.asarray(indices, np.int64)].T,
                      dtype=np.float32)


def leakage_canaries(features, names, folds, footprint, *, seed=SEED):
    """Test every feature alone; symmetric AUC >0.90 is a stop condition."""
    rows = []
    for col, name in enumerate(names):
        yes, no = [], []
        rng = np.random.default_rng(seed + col)
        for fold in folds:
            region = np.asarray(fold["region"], bool) & footprint
            positives = np.flatnonzero(fold["truth"] & region)
            negatives = region & ~fold["masked_known"] & ~fold["truth"]
            negatives &= ~binary_dilation(fold["truth"], iterations=3)
            candidates = np.flatnonzero(negatives)
            n = min(len(positives), len(candidates), 2500)
            if n == 0:
                raise ValueError("empty positive or negative canary sample")
            yes.append(np.asarray(features[col, rng.choice(positives, n, replace=False)]))
            no.append(np.asarray(features[col, rng.choice(candidates, n, replace=False)]))
        positive, negative = np.concatenate(yes), np.concatenate(no)
        score = np.r_[positive, negative]
        auc = float(roc_auc_score(
            np.r_[np.ones(positive.size), np.zeros(negative.size)], score
        ))
        rows.append({
            "feature": name,
            "evidence_class": "HOLDOUT-FEATURE-CANARY",
            "auc": auc,
            "symmetric_auc": max(auc, 1.0 - auc),
            "withheld_sample": int(positive.size),
            "negative_sample": int(negative.size),
            "passed": max(auc, 1.0 - auc) <= 0.90,
        })
    return rows


def fit(features, footprint, visible, training_domain, columns, *, seed=SEED):
    """Fit only on visible faults outside the held quadrant.

    Unlabelled samples are kept at least three pixels from visible faults. Hidden
    truth is never passed to this function and no catalogue geometry is a model
    channel.
    """
    valid = np.asarray(footprint, bool) & np.asarray(training_domain, bool)
    visible = np.asarray(visible, bool)
    positives = np.flatnonzero(valid & visible)
    exclusion = binary_dilation(visible, iterations=3)
    unlabelled = np.flatnonzero(valid & ~exclusion)
    if not len(positives) or not len(unlabelled):
        raise ValueError("empty fold-proper training class")
    rng = np.random.default_rng(seed)
    pos = rng.choice(positives, min(20_000, len(positives)), replace=False)
    neg = rng.choice(unlabelled, min(60_000, len(unlabelled)), replace=False)
    index = np.r_[pos, neg]
    labels = np.r_[np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)]
    estimator = HistGradientBoostingClassifier(
        max_iter=70,
        learning_rate=0.065,
        max_leaf_nodes=19,
        max_bins=128,
        min_samples_leaf=35,
        l2_regularization=1.5,
        random_state=seed,
    )
    estimator.fit(_matrix(features, index, columns), labels)
    return estimator, {
        "columns": list(columns),
        "n_visible_training": int(len(positives)),
        "n_positive_sample": int(len(pos)),
        "n_unlabelled_sample": int(len(neg)),
        "positive_unlabelled_assumption": True,
        "hidden_truth_used": False,
    }


def probability(estimator, features, indices, columns, chunk=120_000):
    indices = np.asarray(indices, np.int64)
    result = np.empty(len(indices), np.float32)
    for start in range(0, len(indices), chunk):
        part = indices[start:start + chunk]
        result[start:start + len(part)] = estimator.predict_proba(
            _matrix(features, part, columns)
        )[:, 1]
    if not np.isfinite(result).all() or (result < 0).any() or (result > 1).any():
        raise ValueError("model generated invalid probabilities")
    return result


def catalogue_collar_allowed(footprint, visible, radius_px=2):
    """Label-derived placement mask; caller must pass fold-visible catalogue only."""
    footprint = np.asarray(footprint, bool)
    visible = np.asarray(visible, bool)
    if footprint.shape != visible.shape:
        raise ValueError("placement masks do not match")
    if not visible.any():
        return footprint.copy()
    distance = distance_transform_edt(~visible)
    return footprint & (distance > float(radius_px))


def spaced_dots(probability_surface, eligible, budget, radius=2, *, tie=None):
    """Greedy fixed-budget non-maximum placement with deterministic tie breaks."""
    probability_surface = np.asarray(probability_surface, np.float32)
    eligible = np.asarray(eligible, bool)
    if probability_surface.ndim != 2 or eligible.shape != probability_surface.shape:
        raise ValueError("surface/eligibility shape mismatch")
    if budget < 1 or radius < 0:
        raise ValueError("invalid budget or spacing radius")
    if not np.isfinite(probability_surface).all() or (probability_surface < 0).any() or (probability_surface > 1).any():
        raise ValueError("probability surface outside [0,1]")
    candidates = np.flatnonzero(eligible.ravel() & (probability_surface.ravel() > 0))
    if not len(candidates):
        raise ValueError("no eligible positive predictions")
    tie_values = (np.zeros(probability_surface.size, np.float32) if tie is None
                  else np.asarray(tie, np.float32).ravel())
    if tie_values.shape != (probability_surface.size,) or not np.isfinite(tie_values[candidates]).all():
        raise ValueError("invalid tie-break surface")
    poolsize = min(len(candidates), max(20_000, budget * 30))
    ranking = probability_surface.ravel()[candidates].astype(np.float64)
    ranking += 1e-8 * tie_values[candidates]
    if poolsize < len(candidates):
        keep = np.argpartition(ranking, -poolsize)[-poolsize:]
        candidates, ranking = candidates[keep], ranking[keep]
    order = np.lexsort((candidates, -tie_values[candidates], -ranking))
    ordered = candidates[order]

    output = np.zeros(probability_surface.shape, bool)
    blocked = np.zeros(probability_surface.shape, bool)
    h, w = output.shape
    offsets = [(dy, dx) for dy in range(-radius, radius + 1)
               for dx in range(-radius, radius + 1)
               if dy * dy + dx * dx <= radius * radius]
    emitted = 0
    for flat in ordered:
        row, col = divmod(int(flat), w)
        if blocked[row, col]:
            continue
        output[row, col] = True
        emitted += 1
        for dy, dx in offsets:
            yy, xx = row + dy, col + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
        if emitted == budget:
            break
    if emitted != budget:
        raise ValueError(f"emission exhausted at {emitted}, required {budget}")
    return output, {
        "requested": int(budget),
        "emitted": int(emitted),
        "separation_radius_px": int(radius),
        "ranked_pool": int(poolsize),
        "positive_candidates": int(len(candidates)),
    }
