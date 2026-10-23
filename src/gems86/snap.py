"""Pure geometry for the SNAP axis: local relocation of a dot field to an edge crest.

The contract is deliberately narrow: a SNAP variant *moves* dots of its parent
by at most a stated Euclidean radius to the strongest edge response inside that
window. It never adds or deletes a dot (count is preserved exactly), never
re-weights a dot, and never places a dot on a cell its caller marks ineligible
(the R0 caller requires: inside the footprint, off the mapped catalogue,
Euclidean catalogue distance > 2 px -- the parent's own exclusion -- and a
valid edge value).

Determinism / collision rule
-----------------------------
Independent per-dot argmax choices can collide (two dots wanting one cell).
Collisions are resolved by a gain-ordered greedy placement:

* every dot's *ideal* gain (best eligible window cell minus its origin) is
  computed first, ignoring occupancy;
* dots are placed in decreasing ideal-gain order, ties by ascending origin
  flat index (row-major);
* while a dot is unplaced its origin cell stays *reserved*, so an already
  placed dot can never steal it -- which guarantees every dot can always fall
  back to staying put, hence the count is preserved exactly;
* at its turn a dot takes the best still-free eligible cell in its window
  (ties: higher edge, then smaller displacement, then lower destination flat
  index), but only if the realised gain clears ``min_gain`` (and is strictly
  positive); otherwise it stays.

A dot whose origin has no valid edge value cannot be evaluated and stays.
"""
from __future__ import annotations

import numpy as np


def window_offsets(radius: float) -> tuple[tuple[int, int, float], ...]:
    """Lattice offsets (dy, dx, Euclidean distance) with distance <= radius."""
    if radius < 0:
        raise ValueError("radius must be non-negative")
    lim = int(np.ceil(radius))
    out = []
    for dy in range(-lim, lim + 1):
        for dx in range(-lim, lim + 1):
            d = float(np.hypot(dy, dx))
            if d <= radius + 1e-9:
                out.append((dy, dx, d))
    return tuple(out)


def percentile_ranks(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Percentile rank in [0, 1] over ``valid`` cells; NaN elsewhere.

    Row-major extraction with a stable sort, so equal values receive
    consecutive ranks in row-major order -- fully deterministic.
    """
    values = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    if values.shape != valid.shape:
        raise ValueError("values and valid must share a shape")
    out = np.full(values.shape, np.nan, dtype=np.float32)
    v = values[valid]
    if v.size == 0:
        return out
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, v.size, dtype=np.float32)
    out[valid] = ranks
    return out


def _best_in_window(edge, eligible, blocked, y, x, offsets):
    """Best (edge, -dist, -flat, ny, nx, dist) candidate for one dot, or None."""
    height, width = edge.shape
    best = None
    for dy, dx, dist in offsets:
        ny, nx = y + dy, x + dx
        if not (0 <= ny < height and 0 <= nx < width):
            continue
        if blocked is not None and blocked[ny, nx]:
            continue
        if not eligible[ny, nx]:
            continue
        e = float(edge[ny, nx])
        if not np.isfinite(e):
            continue
        key = (e, -dist, -(ny * width + nx))
        if best is None or key > best[0]:
            best = (key, ny, nx, dist, e)
    return best


def snap_dots(dots: np.ndarray, edge: np.ndarray, eligible: np.ndarray,
              radius: float, min_gain: float = 0.0) -> tuple[np.ndarray, dict]:
    """Snap every dot to the strongest eligible edge cell within ``radius`` px.

    ``eligible`` must already encode every destination rule except occupancy
    (footprint, catalogue exclusion, valid edge, ...). An origin cell is
    always allowed as the "stay" fallback even when it is not itself
    eligible (e.g. its edge value is missing), so the parent is never
    worsened by construction and the count is exact.
    """
    dots = np.asarray(dots, dtype=bool)
    edge = np.asarray(edge, dtype=np.float64)
    eligible = np.asarray(eligible, dtype=bool)
    if not (dots.shape == edge.shape == eligible.shape):
        raise ValueError("dots, edge and eligible must share a shape")
    if min_gain < 0:
        raise ValueError("min_gain must be non-negative")
    offsets = window_offsets(radius)
    coords = np.argwhere(dots)                      # row-major
    n = int(coords.shape[0])
    width = dots.shape[1]
    flat = coords[:, 0] * width + coords[:, 1]

    # Ideal (occupancy-free) gain per dot -> placement order.
    ideal_gain = np.full(n, -np.inf)
    origin_edge = np.full(n, np.nan)
    for i, (y, x) in enumerate(coords):
        e0 = float(edge[y, x])
        origin_edge[i] = e0
        if not np.isfinite(e0):
            continue
        best = _best_in_window(edge, eligible, None, int(y), int(x), offsets)
        if best is not None:
            ideal_gain[i] = best[4] - e0
    order = sorted(range(n), key=lambda i: (-ideal_gain[i], int(flat[i])))

    reserved = dots.copy()         # origins of not-yet-placed dots
    final = np.zeros_like(dots)    # cells already taken by placed dots
    dest = coords.copy()
    realised_gain = np.zeros(n)
    displacement = np.zeros(n)
    for i in order:
        y, x = int(coords[i, 0]), int(coords[i, 1])
        reserved[y, x] = False     # release own origin; it stays available
        e0 = origin_edge[i]
        if np.isfinite(e0):
            blocked = reserved | final
            blocked[y, x] = True   # origin handled as the stay fallback below
            best = _best_in_window(edge, eligible, blocked, y, x, offsets)
            if best is not None:
                _, ny, nx, dist, e = best
                gain = e - e0
                if gain > 0.0 and gain >= min_gain - 1e-12:
                    dest[i] = (ny, nx)
                    realised_gain[i] = gain
                    displacement[i] = dist
        final[dest[i, 0], dest[i, 1]] = True

    moved = displacement > 0
    if int(final.sum()) != n:
        raise AssertionError("SNAP must preserve the dot count exactly")
    stats = {
        "n_dots": n,
        "n_moved": int(moved.sum()),
        "n_stayed": int((~moved).sum()),
        "mean_displacement_px": float(displacement.mean()) if n else 0.0,
        "mean_displacement_moved_px": float(displacement[moved].mean()) if moved.any() else 0.0,
        "max_displacement_px": float(displacement.max()) if n else 0.0,
        "mean_realised_gain": float(realised_gain.mean()) if n else 0.0,
        "mean_realised_gain_moved": float(realised_gain[moved].mean()) if moved.any() else 0.0,
        "n_origin_edge_invalid": int((~np.isfinite(origin_edge)).sum()),
        "radius_px": float(radius),
        "min_gain": float(min_gain),
        "displacement_px": displacement,
        "realised_gain": realised_gain,
    }
    return final, stats


def snap_diff_stats(parent: np.ndarray, candidate: np.ndarray) -> dict:
    """Parent-difference statistics for a same-count relocation."""
    p = np.asarray(parent, dtype=bool)
    c = np.asarray(candidate, dtype=bool)
    if p.shape != c.shape:
        raise ValueError("parent and candidate must share a shape")
    n0, n1 = int(p.sum()), int(c.sum())
    removed = int((p & ~c).sum())
    added = int((c & ~p).sum())
    return {
        "n_parent": n0,
        "n_candidate": n1,
        "retained": int((p & c).sum()),
        "removed": removed,
        "added": added,
        # house/ledger convention: changed grid cells over the parent dot count
        "pct_of_parent_changed": round(100.0 * (removed + added) / n0, 4) if n0 else 0.0,
        "pct_dots_moved": round(100.0 * removed / n0, 4) if n0 else 0.0,
        "kept_fraction": round(float((p & c).sum()) / n0, 6) if n0 else 0.0,
    }
