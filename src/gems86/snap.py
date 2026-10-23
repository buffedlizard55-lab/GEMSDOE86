"""Pure geometry for the SNAP axis: relocate dots onto a physical edge response.

The AXIS contract is narrow on purpose. A SNAP variant differs from its parent
**only** by moving existing dots, each by at most ``radius`` pixels, onto the
strongest value of one declared response surface inside its own window:

* the dot count is preserved exactly (nothing added, nothing deleted);
* a dot never lands on a cell that is outside the footprint, closer than
  ``min_catalogue_px`` to a mapped-fault cell, or already occupied by another
  dot;
* a dot moves only if the target cell scores **strictly** higher on the
  response than the dot's own cell, so the move is never gratuitous;
* ties are broken by a documented total order (higher response, then smaller
  displacement, then row-major cell index), never by a random seed, so the whole
  transformation is reproducible from the declared inputs.

Nothing here reads a truth file, a holdout label, or the leaderboard. The only
inputs are the parent dot field, the pinned feature stack, and the pinned
catalogue used as an exclusion mask.

Why the exclusion radius is 3 px and not the parent's own 2.236 px
-----------------------------------------------------------------
R0 already keeps every dot more than 2 px from the catalogue (its minimum is
sqrt(5) = 2.2361 px, a knight move). Those inherited dots are allowed to *stay*
where they are, but no dot is ever *moved* to a cell inside 3 px of the
catalogue: the organizer says known-fault pixels are masked and score nothing,
so mass pulled into the collar would pay zero at best and, per PRUNE, cost
coverage. The variant therefore never creates a new collar violation; it
inherits the parent's.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

#: Candidate displacements, in pixels, up to the brief's 2 px SNAP window.
SNAP_RADIUS = 2.0
#: A dot may not be *moved* to a cell at or inside this catalogue distance.
MIN_CATALOGUE_PX = 3.0


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dot_digest(dots: np.ndarray) -> str:
    """Stable identity of a dot *set*: sha256 over sorted flat indices (uint32 LE)."""
    return hashlib.sha256(np.flatnonzero(np.asarray(dots, bool)).astype("<u4").tobytes()).hexdigest()


def window_offsets(radius: float = SNAP_RADIUS) -> list[tuple[int, int, float]]:
    """Every integer displacement ``(dy, dx, distance)`` with ``0 < d <= radius``.

    Sorted by (distance, dy, dx) so the tie-break used by
    :func:`snap_dots` is explicit and stable across machines.
    """
    r = int(np.floor(radius + 1e-9))
    out = [(dy, dx, float(np.hypot(dy, dx)))
           for dy in range(-r, r + 1) for dx in range(-r, r + 1)
           if (dy, dx) != (0, 0)]
    out = [t for t in out if t[2] <= radius + 1e-9]
    out.sort(key=lambda t: (t[2], t[0], t[1]))
    return out


@dataclass(frozen=True)
class SnapResult:
    """One snapped dot field plus everything a reviewer needs to audit it."""

    dots: np.ndarray                 # bool, the new dot field (same count as the parent)
    moved: np.ndarray                # bool over parent dots, in row-major order
    from_yx: np.ndarray              # (n_moved, 2) int32 origin cells
    to_yx: np.ndarray                # (n_moved, 2) int32 destination cells
    displacement_px: np.ndarray      # (n_moved,) float64
    blocked_by_collar: int           # dots whose best in-window cell is inside the 3 px collar
    blocked_by_occupancy: int        # dots that had a gain but lost every candidate to a taken cell

    @property
    def n_dots(self) -> int:
        return int(self.dots.sum())

    @property
    def n_moved(self) -> int:
        return int(self.moved.sum())

    def stats(self) -> dict:
        d = self.displacement_px
        hist = {}
        if d.size:
            vals, counts = np.unique(np.round(d, 4), return_counts=True)
            hist = {f"{float(v):.4f}": int(c) for v, c in zip(vals, counts)}
        return {
            "n_dots": self.n_dots,
            "n_moved": self.n_moved,
            "fraction_moved": round(float(self.n_moved) / max(self.n_dots, 1), 6),
            "mean_displacement_px": round(float(d.mean()), 4) if d.size else 0.0,
            "median_displacement_px": round(float(np.median(d)), 4) if d.size else 0.0,
            "max_displacement_px": round(float(d.max()), 4) if d.size else 0.0,
            "displacement_histogram": hist,
            "blocked_by_collar": self.blocked_by_collar,
            "blocked_by_occupancy": self.blocked_by_occupancy,
        }


def snap_dots(dots: np.ndarray, response: np.ndarray, footprint: np.ndarray,
              distance: np.ndarray, *, radius: float = SNAP_RADIUS,
              min_catalogue_px: float = MIN_CATALOGUE_PX,
              min_gain: float = 0.0, min_response: float = -np.inf) -> SnapResult:
    """Move each dot onto the strongest response cell within ``radius`` pixels.

    Greedy, deterministic and conflict-free by construction:

    1. every dot's unconstrained best cell is computed (highest response, then
       smallest displacement, then row-major index);
    2. dots are served in descending order of their response gain, ties broken
       by row-major position, so the dot with the most to gain never loses its
       target to a dot with less;
    3. a served dot takes its best still-free candidate, or stays put.

    A cell counts as free when no dot has kept it and no already-served dot has
    moved into it. Cells belonging to not-yet-served dots are *not* free, which
    keeps the result a matching rather than a pile-up.

    ``min_gain`` is the selectivity gate: a dot moves only if the target beats
    its own cell by more than ``min_gain`` in response units. With ``min_gain``
    at zero and a smooth response, nearly every dot climbs to the edge of its
    window (measured: 97-99 % moved, mean 1.8 px), which is a relocation of the
    whole field rather than a correction of individual dots. A positive gate
    keeps the edit local and attributable.

    ``min_response`` is the crest gate: only cells at or above it are eligible
    targets. It is applied to the *target* only, so a dot sitting below the
    crest can still climb onto one; its own cell keeps its true response, which
    is what the gain is measured against.
    """
    dots = np.asarray(dots, bool)
    footprint = np.asarray(footprint, bool)
    response = np.asarray(response, np.float32)
    distance = np.asarray(distance, np.float32)
    if dots.shape != response.shape or dots.shape != footprint.shape:
        raise ValueError("dots, response and footprint must share one grid")
    if dots.shape != distance.shape:
        raise ValueError("distance must share the dot grid")
    if np.any(dots & ~footprint):
        raise ValueError("parent emits dots outside the footprint")

    h, w = dots.shape
    ys, xs = np.nonzero(dots)                       # row-major order
    n = ys.size
    cur = np.where(np.isfinite(response[ys, xs]), response[ys, xs], -np.inf).astype(np.float32)

    pad = int(np.ceil(radius))
    resp_p = np.pad(response, pad, constant_values=np.float32(-np.inf))
    fp_p = np.pad(footprint, pad, constant_values=False)
    dist_p = np.pad(distance, pad, constant_values=np.float32(0.0))

    offsets = window_offsets(radius)
    best_val = np.full(n, -np.inf, np.float32)      # best cell that obeys the collar rule
    best_any = np.full(n, -np.inf, np.float32)      # best footprinted cell, collar ignored
    for dy, dx, _dist in offsets:
        yy, xx = ys + pad + dy, xs + pad + dx
        v = resp_p[yy, xx]
        in_fp = fp_p[yy, xx]
        collared = dist_p[yy, xx] < min_catalogue_px
        best_any = np.maximum(best_any, np.where(in_fp, v, -np.inf))
        best_val = np.maximum(best_val, np.where(in_fp & ~collared & (v >= min_response),
                                                 v, -np.inf))

    blocked_collar = int(np.count_nonzero(np.isfinite(best_any) & (best_any > cur) & ~(best_val > cur)))
    gain = best_val - cur
    wants = np.flatnonzero(np.isfinite(gain) & (gain > max(min_gain, 0.0)))
    # serve the largest gain first; ties by row-major dot index (ys, xs are sorted)
    order = wants[np.lexsort((wants, -gain[wants]))]

    occ = dots.copy()
    new_dots = dots.copy()
    moved = np.zeros(n, bool)
    dest_cells: list[tuple[int, int]] = []
    served_idx: list[int] = []
    occupancy_blocked = 0
    for i in order:
        y0, x0 = int(ys[i]), int(xs[i])
        cands = []
        for dy, dx, dist in offsets:
            yy, xx = y0 + dy, x0 + dx
            if not (0 <= yy < h and 0 <= xx < w):
                continue
            if not footprint[yy, xx] or distance[yy, xx] < min_catalogue_px:
                continue
            v = response[yy, xx]
            if not np.isfinite(v) or v < min_response:
                continue
            if (v - cur[i]) <= max(min_gain, 0.0):
                continue
            cands.append((-float(v), dist, yy, xx))
        cands.sort()
        served = False
        for _negv, _dist, yy, xx in cands:
            if occ[yy, xx]:
                continue
            occ[y0, x0] = False
            occ[yy, xx] = True
            new_dots[y0, x0] = False
            new_dots[yy, xx] = True
            moved[i] = True
            served = True
            served_idx.append(int(i))
            dest_cells.append((yy, xx))
            break
        if not served:
            occupancy_blocked += 1

    idx = np.asarray(served_idx, np.int64)
    from_yx = np.column_stack([ys[idx], xs[idx]]).astype(np.int32) if idx.size else np.zeros((0, 2), np.int32)
    to_yx = np.asarray(dest_cells, np.int32).reshape(-1, 2)
    disp = np.hypot((to_yx[:, 0] - from_yx[:, 0]).astype(float),
                    (to_yx[:, 1] - from_yx[:, 1]).astype(float)) if idx.size else np.zeros(0)
    return SnapResult(dots=new_dots, moved=moved, from_yx=from_yx, to_yx=to_yx,
                      displacement_px=disp,
                      blocked_by_collar=blocked_collar,
                      blocked_by_occupancy=occupancy_blocked)


# ------------------------------------------------------------------ diagnostics
def nearest_neighbour_px(dots: np.ndarray) -> dict:
    """Mean / median / max nearest-neighbour distance among dot centres, in px."""
    from scipy.spatial import cKDTree

    pts = np.column_stack(np.nonzero(dots)).astype(float)
    if pts.shape[0] < 2:
        return {"n": int(pts.shape[0])}
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    return {"n": int(pts.shape[0]), "mean": round(float(nn.mean()), 4),
            "median": round(float(np.median(nn)), 4), "min": round(float(nn.min()), 4)}


def block_density_cv(dots: np.ndarray, footprint: np.ndarray, block_px: int = 50) -> float:
    """Coefficient of variation of dot density across ``block_px`` blocks (5 km at 100 m).

    Only blocks that are at least 25 % inside the footprint are counted, so the
    number is not dominated by empty corner blocks outside the study area.
    """
    dots = np.asarray(dots, bool)
    fp = np.asarray(footprint, bool)
    h, w = dots.shape
    dens = []
    for y in range(0, h - block_px + 1, block_px):
        for x in range(0, w - block_px + 1, block_px):
            nb = int(fp[y:y + block_px, x:x + block_px].sum())
            if nb < 0.25 * block_px * block_px:
                continue
            dens.append(float(dots[y:y + block_px, x:x + block_px].sum()) / nb)
    a = np.asarray(dens, float)
    return round(float(a.std() / a.mean()), 4) if a.size and a.mean() > 0 else 0.0
