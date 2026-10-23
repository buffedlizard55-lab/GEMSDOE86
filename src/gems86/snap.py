"""Pure geometry for the SNAP axis: reposition dots inside a fixed window.

The AXIS contract
-----------------
A SNAP variant differs from its parent **only** by moving dots.  The number of
dots, their mass (unit per dot), the footprint, and the catalogue exclusion are
carried through unchanged; no dot is created, deleted or re-weighted.  Each dot
may move at most ``radius`` pixels (Euclidean) to the cell inside its window
that carries the strongest potential-field edge response.

Why a *movement* axis can pay at all
------------------------------------
The DTI at ``alpha=0.2`` credits a dot with ``k = max(1 - d/3, 0)`` against the
nearest truth cell, so a dot 1 px off the trace earns 0.667 and a dot 2 px off
earns 0.333.  Moving a dot *towards* truth therefore raises ``T`` and lowers
``FP_w`` twice over: ``dD = alpha*(dT - dk)`` with ``dk`` the change in the
dot's own self-credit, and ``DTI = T/D``.  When the dot is the unique cover of
one truth cell ``dT == dk`` and the denominator is unchanged while the numerator
grows; when the move is only a redundancy reduction ``dT == 0`` the denominator
shrinks.  Both directions are strictly positive.  The symmetric risk is a move
*away* from truth, which is why the falsifier is a measured mean displacement
and not an argument.

Why rank-normalised bands and not raw gradients
-----------------------------------------------
``tmi_hg`` and ``iso_grav_anom_hg`` are horizontal-gradient magnitudes in
different units and with different heavy tails.  Rank-normalising each over the
scored footprint and averaging puts them on one scale without letting a single
high-amplitude body dominate the search.  The transform is monotone per band,
so it cannot invent an edge that is not in the data.

Nothing here reads a truth raster, the network, a portal, or a credential.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

#: The two pinned gradient bands this axis is allowed to use (manifest band
#: descriptions 3 and 18 of ``data/bridge/training_features.tif``).
SNAP_BANDS = ("tmi_hg", "iso_grav_anom_hg")


def rank01(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Rank-normalise ``values`` to ``[0, 1]`` over ``valid``; 0 elsewhere.

    Ties share their mean rank, so a constant band maps to 0.5 and contributes
    nothing to an arg-max search.
    """
    v = np.asarray(values, np.float64)
    m = np.asarray(valid, bool) & np.isfinite(v)
    out = np.zeros(v.shape, np.float64)
    n = int(m.sum())
    if n < 2:
        return out
    vals = v[m]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(n, np.float64)
    ranks[order] = np.arange(n, dtype=np.float64)
    uniq, inv, cnt = np.unique(vals[order], return_inverse=True, return_counts=True)
    if (cnt > 1).any():
        sums = np.bincount(inv, weights=ranks[order])
        means = (sums / cnt).astype(np.float64)
        ranks[order] = means[inv]
    out[m] = ranks / max(n - 1, 1)
    return out


def edge_response(bands: dict[str, np.ndarray], valid: np.ndarray,
                  weights: dict[str, float] | None = None) -> np.ndarray:
    """Weighted mean of the rank-normalised bands; ``weights`` must sum to 1."""
    if not bands:
        raise ValueError("edge_response needs at least one band")
    keys = sorted(bands)
    w = dict(weights or {k: 1.0 / len(keys) for k in keys})
    if set(w) != set(keys):
        raise ValueError("weights must name exactly the supplied bands")
    total = float(sum(w.values()))
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"weights must sum to 1, got {total}")
    out = np.zeros(np.asarray(valid).shape, np.float64)
    for k in keys:
        out += w[k] * rank01(bands[k], valid)
    return out


def window_offsets(radius: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """All integer offsets with ``0 < hypot(dy,dx) <= radius``, row-major."""
    if radius <= 0:
        raise ValueError("radius must be positive")
    r = int(np.ceil(radius))
    dy, dx = [], []
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            d = float(np.hypot(j, i))
            if 0.0 < d <= radius + 1e-12:
                dy.append(j)
                dx.append(i)
    return np.array(dy, np.int64), np.array(dx, np.int64), np.hypot(np.array(dy), np.array(dx))


@dataclass
class SnapResult:
    dots: np.ndarray            # bool, same count as the parent
    displacement: np.ndarray    # float, one entry per *moved* dot
    gain: np.ndarray            # response gain of each moved dot
    src_y: np.ndarray           # parent row of each moved dot
    src_x: np.ndarray
    n_parent: int
    n_snapped: int


def snap_dots(dots: np.ndarray, response: np.ndarray, allowed: np.ndarray,
              radius: float = 2.0, *, min_gain: float = 0.0) -> SnapResult:
    """Move every dot at most ``radius`` px to the best free cell in its window.

    ``allowed`` marks where a dot may land (footprint, off-catalogue, and any
    other exclusion the caller wants to preserve).  A dot's own cell is always
    allowed to keep.  Count is preserved exactly: the search is a single greedy
    pass over dots ordered by their best available gain, so a cell can be taken
    by at most one dot and the vacated cell is released for later dots.  The
    pass is deterministic (stable sort on gain, then row-major index).
    """
    dots = np.asarray(dots, bool)
    response = np.asarray(response, np.float64)
    allowed = np.asarray(allowed, bool) & np.isfinite(response)
    if dots.shape != response.shape or dots.shape != allowed.shape:
        raise ValueError("dots, response and allowed must share a shape")
    if np.any(dots & ~allowed):
        raise ValueError("a parent dot sits outside the landing mask; a SNAP variant "
                         "cannot preserve the parent's exclusions")
    dy, dx, dist = window_offsets(radius)
    pad = int(np.ceil(radius))
    resp_p = np.pad(response, pad, constant_values=-np.inf)
    allow_p = np.pad(allowed, pad, constant_values=False)
    occ = np.pad(dots, pad, constant_values=False)
    ys, xs = np.nonzero(dots)
    ys = ys + pad
    xs = xs + pad
    base = resp_p[ys, xs]

    best_gain = np.full(ys.size, -np.inf, np.float64)
    for j, i in zip(dy, dx):
        cand = resp_p[ys + j, xs + i]
        ok = allow_p[ys + j, xs + i]
        best_gain = np.maximum(best_gain, np.where(ok, cand - base, -np.inf))

    order = np.argsort(-best_gain, kind="stable")
    moved_y, moved_x, moved_d, moved_g = [], [], [], []
    for idx in order:
        gain = best_gain[idx]
        if not np.isfinite(gain) or gain <= min_gain:
            break
        y, x = int(ys[idx]), int(xs[idx])
        best, by, bx = -np.inf, y, x
        for j, i in zip(dy, dx):
            yy, xx = y + j, x + i
            if not allow_p[yy, xx] or occ[yy, xx]:
                continue
            r = resp_p[yy, xx]
            if r > best:
                best, by, bx = r, yy, xx
        if not np.isfinite(best) or best - resp_p[y, x] <= min_gain:
            continue
        occ[y, x] = False
        occ[by, bx] = True
        moved_y.append(y)
        moved_x.append(x)
        moved_d.append(float(np.hypot(by - y, bx - x)))
        moved_g.append(float(best - resp_p[y, x]))

    out = occ[pad:pad + dots.shape[0], pad:pad + dots.shape[1]].copy()
    if int(out.sum()) != int(dots.sum()):
        raise AssertionError(f"snap changed the dot count: {int(out.sum())} != {int(dots.sum())}")
    if np.any(out & ~allowed):
        raise AssertionError("a dot landed outside the allowed mask")
    return SnapResult(dots=out,
                      displacement=np.asarray(moved_d, np.float64),
                      gain=np.asarray(moved_g, np.float64),
                      src_y=np.asarray(moved_y, np.int64),
                      src_x=np.asarray(moved_x, np.int64),
                      n_parent=int(dots.sum()), n_snapped=len(moved_d))


def nearest_neighbour(dots: np.ndarray) -> np.ndarray:
    """Euclidean distance from each dot to its nearest other dot (px)."""
    ys, xs = np.nonzero(np.asarray(dots, bool))
    if ys.size < 2:
        return np.zeros(ys.size, np.float64)
    pts = np.column_stack([ys, xs]).astype(np.float64)
    d, _ = cKDTree(pts).query(pts, k=2)
    return d[:, 1]


def movement_stats(parent: np.ndarray, result: SnapResult, response: np.ndarray,
                   catalogue_distance: np.ndarray) -> dict:
    """Everything the brief asks a SNAP variant to report, plus its confounder.

    Displacements come from :class:`SnapResult`, i.e. from the algorithm that
    produced the moves -- never re-derived by matching the deleted and added
    cells (both sets are unordered, so a rematch would be arbitrary).
    """
    p = np.asarray(parent, bool)
    c = np.asarray(result.dots, bool)
    if p.shape != c.shape:
        raise ValueError("parent and child must share a shape")
    if int(p.sum()) != int(c.sum()):
        raise ValueError("SNAP must preserve the dot count")
    if np.any(c & ~np.isfinite(response)):
        raise ValueError("a dot landed on a non-finite response cell")
    disp = np.asarray(result.displacement, np.float64)
    n = int(p.sum())
    nn_before = nearest_neighbour(p)
    nn_after = nearest_neighbour(c)
    cat_before = np.asarray(catalogue_distance, np.float64)[p]
    cat_after = np.asarray(catalogue_distance, np.float64)[c]
    moved = int(result.n_snapped)
    return {
        "n_parent": n,
        "n_candidate": int(c.sum()),
        "n_snapped": moved,
        "pct_snapped": round(100.0 * moved / float(n), 4),
        "mean_displacement_px_moved": round(float(disp.mean()), 4) if disp.size else 0.0,
        "median_displacement_px_moved": round(float(np.median(disp)), 4) if disp.size else 0.0,
        "max_displacement_px": round(float(disp.max()), 4) if disp.size else 0.0,
        "mean_displacement_px_all_dots": round(float(disp.sum()) / float(n), 4),
        "mean_response_gain_moved": round(float(np.asarray(result.gain).mean()), 6) if moved else 0.0,
        "mean_response_before_dots": round(float(np.asarray(response)[p].mean()), 6),
        "mean_response_after_dots": round(float(np.asarray(response)[c].mean()), 6),
        "nn_distance_before_mean_px": round(float(nn_before.mean()), 4),
        "nn_distance_after_mean_px": round(float(nn_after.mean()), 4),
        "nn_distance_before_median_px": round(float(np.median(nn_before)), 4),
        "nn_distance_after_median_px": round(float(np.median(nn_after)), 4),
        "nn_lt_2px_before": int((nn_before < 2.0).sum()),
        "nn_lt_2px_after": int((nn_after < 2.0).sum()),
        "catalogue_distance_before_mean_px": round(float(cat_before.mean()), 4),
        "catalogue_distance_after_mean_px": round(float(cat_after.mean()), 4),
        "catalogue_distance_before_min_px": round(float(cat_before.min()), 4),
        "catalogue_distance_after_min_px": round(float(cat_after.min()), 4),
        "dots_moved_closer_to_catalogue": int((cat_after < cat_before).sum()),
        "dots_moved_farther_from_catalogue": int((cat_after > cat_before).sum()),
        "dots_on_catalogue": int((c & (np.asarray(catalogue_distance) == 0.0)).sum()),
    }


def move_diff(parent: np.ndarray, child: np.ndarray, catalogue_distance: np.ndarray) -> dict:
    """Parent-difference statistics for a *movement* axis.

    ``gems86.prune.diff_stats`` refuses any variant that adds a dot -- correct
    for PRUNE, wrong here: a SNAP move necessarily adds a cell and deletes one.
    The same keys are returned so the ledger's columns mean the same thing.
    """
    p = np.asarray(parent, bool)
    c = np.asarray(child, bool)
    d = np.asarray(catalogue_distance, np.float64)
    if p.shape != c.shape:
        raise ValueError("parent and child must share a shape")
    n_parent = int(p.sum())
    n_child = int(c.sum())
    if n_parent != n_child:
        raise ValueError("SNAP must preserve the dot count")
    removed = p & ~c
    added = c & ~p
    if int(removed.sum()) != int(added.sum()):
        raise ValueError("SNAP is not a bijection")
    changed = int(removed.sum() + added.sum())
    return {
        "n_parent": n_parent,
        "n_candidate": n_child,
        "retained": int((p & c).sum()),
        "removed": int(removed.sum()),
        "added": int(added.sum()),
        "pct_of_parent_changed": round(100.0 * changed / n_parent, 4),
        "pct_changed": round(100.0 * changed / n_parent, 4),
        "pct_removed": round(100.0 * int(removed.sum()) / n_parent, 4),
        "pct_added": round(100.0 * int(added.sum()) / n_parent, 4),
        "kept_fraction": round(float((p & c).sum()) / n_parent, 6),
        "kept_distance_min_px": round(float(d[c].min()), 4),
        "count_exact": True,
        "axis_note": "positions changed only; no dot created, deleted or re-weighted",
    }
