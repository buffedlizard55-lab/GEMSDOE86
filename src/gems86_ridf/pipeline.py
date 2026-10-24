"""H86E-RIDF: model, metric-aware emission and holdout helpers.

Shared tools are reused unchanged: ``gems57.holdout.buffered_component_draw``
(split), ``gems57.evaluate_holdout`` (exact pooled DTI + paired spatial
bootstrap) and ``gems57.submission_writer`` (fail-closed GeoTIFF/ZIP writer).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

from gems57 import evaluate_holdout as E

SPACING_PX = 2.8          # disc-thinning radius proven by the D2.8 lineage
COLLAR_PX = 2.0           # visible-catalogue collar (H33 rule, visible faults only)
R0_DCAT_BINS = (2.0, 4.0, 8.0, 16.0, 32.0, 64.0, np.inf)
# Fraction of the 37,654 R0 dots per d_cat bin, MEASURED in this session from the
# pinned GEMSDOE32 h33-h33-2-b2 raster (sha256 c55bafc4...): [2,4) 8.9 %, [4,8) 15.0 %,
# [8,16) 19.5 %, [16,32) 22.6 %, [32,64) 22.1 %, >=64 12.0 %.  Used as a *profile*
# target only; no R0 dot location is used.
R0_DCAT_PROFILE = (0.089, 0.150, 0.195, 0.226, 0.221, 0.120)


def sample_training(feats, labels, allowed, n_neg=300_000, seed=0, neg_gap_px=1):
    """Positives: labelled pixels in ``allowed``; negatives: random allowed pixels
    farther than ``neg_gap_px`` from any label (unlabelled = negative, PU-style)."""
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero((labels & allowed).ravel())
    far = ndi.distance_transform_edt(~labels) > neg_gap_px
    negpool = np.flatnonzero((far & allowed).ravel())
    neg = rng.choice(negpool, size=min(n_neg, negpool.size), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(pos.size, np.int8), np.zeros(neg.size, np.int8)])
    X = np.stack([feats[k].ravel()[idx].astype(np.float32) for k in range(feats.shape[0])], 1)
    return X, y


def fit(X, y, seed=0):
    model = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08,
                                           max_leaf_nodes=63, l2_regularization=1.0,
                                           min_samples_leaf=80, random_state=seed)
    return model.fit(X, y)


def predict(model, feats, mask, chunk_rows=256):
    out = np.zeros(mask.shape, np.float32)
    h = mask.shape[0]
    for r0 in range(0, h, chunk_rows):
        m = mask[r0:r0 + chunk_rows]
        if not m.any():
            continue
        X = np.stack([feats[k, r0:r0 + chunk_rows][m].astype(np.float32)
                      for k in range(feats.shape[0])], 1)
        block = out[r0:r0 + chunk_rows]
        block[m] = model.predict_proba(X)[:, 1]
    return out


def disc_thin(score, allowed, budget, spacing=SPACING_PX):
    """Greedy descending-score disc thinning (no two dots closer than ``spacing``)."""
    r = int(np.ceil(spacing))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = (yy * yy + xx * xx) < spacing * spacing
    h, w = score.shape
    blocked = np.zeros((h + 2 * r, w + 2 * r), bool)
    flat = np.flatnonzero(allowed.ravel())
    order = flat[np.argsort(-score.ravel()[flat], kind="stable")]
    dots = np.zeros(score.shape, bool)
    n = 0
    for f in order:
        y, x = divmod(int(f), w)
        if blocked[y + r, x + r]:
            continue
        dots[y, x] = True
        blocked[y:y + 2 * r + 1, x:x + 2 * r + 1] |= disc
        n += 1
        if n >= budget:
            break
    return dots


def stratified_thin(score, allowed, budget, dcat, profile=R0_DCAT_PROFILE,
                    bins=R0_DCAT_BINS, spacing=SPACING_PX):
    """Disc thinning with per-distance-band quotas (the distal profile target)."""
    out = np.zeros(score.shape, bool)
    for lo, hi, frac in zip(bins[:-1], bins[1:], profile):
        band = allowed & (dcat > lo) & (dcat <= hi) if lo > 0 else allowed & (dcat <= hi)
        out |= disc_thin(score, band, int(round(budget * frac)), spacing)
    return out


def crop_fold(fold, footprint, pad=6):
    region = fold["region"]
    rows = np.flatnonzero(region.any(1))
    cols = np.flatnonzero(region.any(0))
    sl = (slice(max(rows[0] - pad, 0), rows[-1] + pad + 1),
          slice(max(cols[0] - pad, 0), cols[-1] + pad + 1))
    sub = {k: fold[k][sl] for k in ("region", "truth", "masked_known", "visible")}
    return sl, sub, footprint[sl]


def holdout_terms(dots, folds, footprint):
    """Pooled per-20-km-block metric terms (shared evaluator, cropped folds)."""
    terms, per_fold = None, []
    for fold in folds:
        sl, sub, fp = crop_fold(fold, footprint)
        res, t = E.evaluate(dots[sl].astype(np.float32), sub, fp,
                            origin=(sl[0].start, sl[1].start), global_shape=dots.shape)
        per_fold.append(dict(fold=fold["name"], dti=res["dti"], n_truth=res["n_truth"],
                             emitted=res["emitted"]))
        terms = t if terms is None else terms + t
    return terms, per_fold


def single_feature_auc(feat, truth, negatives, rng, n=200_000):
    """Rank AUC of one feature alone (max of both orientations)."""
    from sklearn.metrics import roc_auc_score
    p = np.flatnonzero(truth.ravel())
    q = np.flatnonzero(negatives.ravel())
    q = rng.choice(q, size=min(n, q.size), replace=False)
    v = np.concatenate([feat.ravel()[p], feat.ravel()[q]]).astype(np.float32)
    y = np.concatenate([np.ones(p.size), np.zeros(q.size)])
    a = roc_auc_score(y, v)
    return float(max(a, 1 - a))
