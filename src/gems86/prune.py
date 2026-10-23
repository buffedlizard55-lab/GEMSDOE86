"""Pure geometry for the PRUNE axis: catalogue-distance pruning of a dot field.

Everything here is deterministic, reads no truth file, and is unit-tested in
``tests/test_prune_ladder.py``. The AXIS contract is narrow on purpose: a
PRUNE variant differs from its parent only by *deleting* dots whose Euclidean
distance to a mapped-fault pixel is at or below a stated threshold. No dot is
added, moved, or re-weighted.

Why Euclidean pixels and not metres: the scored grid is 100 m, the metric
kernel is 300 m = 3 px, and the organizer's own description of the collar is
"within 2 px of the catalogue". Distances between dot centres are therefore
drawn from the discrete set {1, sqrt2, 2, sqrt5, sqrt8, 3, ...}; a threshold
between two of those values is the same experiment. ``SHELLS_*`` below names
the shells explicitly so nobody has to guess which dots a threshold removes.
"""

from __future__ import annotations

import hashlib

import numpy as np
from scipy.ndimage import distance_transform_edt

# Squared distances of the 8-connected pixel neighbourhood, ascending.
SHELLS = {
    "d1": 1.0,                    # orthogonal neighbour
    "d_sqrt2": float(np.sqrt(2)),  # diagonal neighbour   ~1.4142
    "d2": 2.0,                    # two orthogonal steps
    "d_sqrt5": float(np.sqrt(5)),  # knight move          ~2.2361
    "d_sqrt8": float(np.sqrt(8)),  # two diagonal steps   ~2.8284
    "d3": 3.0,                    # three orthogonal steps = the metric radius
}

#: Named ladder rungs. ``r0`` is the incumbent (already built elsewhere); the
#: other three are this session's experiments. ``upper`` is the inclusive
#: distance bound, so ``r225`` means "delete dots at d <= sqrt5".
RUNGS = {
    "r150": {"upper": 1.5, "shells": ["d1", "d_sqrt2"]},
    "r225": {"upper": float(np.sqrt(5)) + 1e-9, "shells": ["d1", "d_sqrt2", "d2", "d_sqrt5"]},
    "r283": {"upper": float(np.sqrt(8)) + 1e-9, "shells": ["d1", "d_sqrt2", "d2", "d_sqrt5", "d_sqrt8"]},
    "r300": {"upper": 3.0 + 1e-9, "shells": ["d1", "d_sqrt2", "d2", "d_sqrt5", "d_sqrt8", "d3"]},
}


def catalogue_distance(catalogue: np.ndarray) -> np.ndarray:
    """Euclidean distance, in pixels, from every cell to the nearest catalogue cell.

    The catalogue pixel itself is 0. A cell with no catalogue anywhere in the
    raster gets a large finite value from the exact EDT, never ``inf``.
    """
    cat = np.asarray(catalogue, dtype=bool)
    if not cat.any():
        raise ValueError("catalogue is empty; distances are undefined")
    return distance_transform_edt(~cat)


def prune_mask(dots: np.ndarray, distance: np.ndarray, upper: float) -> np.ndarray:
    """Dots that survive ``d > upper``; i.e. delete everything at or inside the collar."""
    dots = np.asarray(dots, dtype=bool)
    if dots.shape != np.asarray(distance).shape:
        raise ValueError("dots and distance must share a shape")
    if upper < 0:
        raise ValueError("upper must be non-negative")
    return dots & (distance > float(upper))


def removed_counts(dots: np.ndarray, distance: np.ndarray) -> dict:
    """How many dots sit in each named shell (for the ledger's dose-response table)."""
    dots = np.asarray(dots, dtype=bool)
    d = np.asarray(distance)
    vals = d[dots]
    out = {}
    for name, radius in SHELLS.items():
        out[name] = int(np.isclose(vals, radius, atol=1e-6).sum())
    return out


def mass_matched_control(dots: np.ndarray, distance: np.ndarray, n_drop: int,
                         *, keep_above: float, seed: int) -> np.ndarray:
    """Delete ``n_drop`` dots at random from dots strictly outside ``keep_above``.

    This is the confound control for a PRUNE variant: it removes the same
    *number* of dots but none of them is near the catalogue, so a live change
    common to the variant and this control is a mass effect, not a collar
    effect. Raises rather than silently shrinking the sample.
    """
    dots = np.asarray(dots, dtype=bool)
    d = np.asarray(distance)
    pool = np.flatnonzero((dots & (d > float(keep_above))).ravel())
    if n_drop > pool.size:
        raise ValueError(f"cannot drop {n_drop} from a pool of {pool.size} far dots")
    rng = np.random.default_rng(int(seed))
    drop = rng.choice(pool, size=int(n_drop), replace=False)
    out = dots.ravel().copy()
    out[drop] = False
    return out.reshape(dots.shape)


def dot_digest(dots: np.ndarray) -> str:
    """Stable identity of a dot *set*: sha256 over sorted flat indices (uint32, LE).

    File bytes depend on the GeoTIFF encoder; the dot set does not. Both are
    recorded in the ledger, but only this digest can be reproduced byte-for-byte
    across GDAL builds (see IRREGULARITIES.md, parent-byte issue).
    """
    idx = np.flatnonzero(np.asarray(dots, dtype=bool).ravel()).astype("<u4")
    return hashlib.sha256(idx.tobytes()).hexdigest()


def diff_stats(parent: np.ndarray, child: np.ndarray, distance: np.ndarray) -> dict:
    """Parent-difference statistics for one variant (the gates ask for these)."""
    p = np.asarray(parent, dtype=bool)
    c = np.asarray(child, dtype=bool)
    d = np.asarray(distance)
    n_parent = int(p.sum())
    n_child = int(c.sum())
    removed = p & ~c
    added = c & ~p
    if added.any():
        raise ValueError("PRUNE variants may only delete dots")
    rd = d[removed]
    kept_d = d[c]
    return {
        "n_parent": n_parent,
        "n_child": n_child,
        "n_removed": int(removed.sum()),
        "n_added": 0,
        "pct_changed": round(100.0 * int(removed.sum()) / n_parent, 4) if n_parent else 0.0,
        "removed_distance_median_px": float(np.median(rd)) if rd.size else None,
        "removed_distance_max_px": float(rd.max()) if rd.size else None,
        "kept_distance_min_px": float(kept_d.min()) if kept_d.size else None,
        "kept_distance_median_px": float(np.median(kept_d)) if kept_d.size else None,
    }
