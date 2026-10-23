"""Pure geometry for the RELIEF axis: count-fixed relocation of dot mass between
relief regimes read off the pinned detrended-elevation bands.

Everything here is deterministic, reads no truth file, and is unit-tested in
``tests/test_relief_axis.py``. The AXIS contract is narrow on purpose. A RELIEF
variant differs from its parent only by *moving* a stated number of dots from one
relief regime into another:

* the dot **count** is fixed (unit mass per dot, so total mass is fixed too --
  this is therefore not a MASS test and cannot be read as one);
* no dot is created on or removed near the catalogue for its own sake -- that
  would be the PRUNE axis (already spent: IR-86-PRUNE-08);
* every **newly occupied** cell is at least ``min_catalogue_px`` (default 3.0)
  from a mapped-fault cell, which is the hard constraint in brief v2 §4.4;
* every newly occupied cell also keeps the parent's own minimum dot spacing
  (``min_dot_px``, default 2.8 px), so the variant cannot smuggle in a
  spacing/clustering effect (the confound that IR-86-LADDER-01 recorded for
  PR #28's refill design).

Selection and placement are **content-blind**: sources are the ``k`` parent dots
of the source regime that are closest to an eligible destination cell, and each
one is placed on the nearest still-free eligible cell. No geological score, no
ranking and no external dataset enters the raster -- the file is a pure geometric
edit of the parent, so a live result attributes to relief-regime membership alone.
(The independent USGS SGMC raster is used only in the *prediction* written in the
run card, never in the builder.)

Why these three regimes: brief v2 §5 names "basin / piedmont / range-front
terciles (relief from the detrended-elevation bands)". ``det_elev`` (band 12) is
topography with the regional trend removed and ``det_elev_slope`` (band 19) is its
gradient, so the sum of their standardised, km-smoothed values is a dimensionless
"how far up and how dissected" index. Terciles of that index give basin / middle /
high. The high class is then split by proximity to a basin cell, because a
*range front* is defined as the basin-margin scarp: high-index cells more than
``front_proximity_px`` away from any basin cell are range interior and are
excluded from both source and destination sets. Without that gate a "front"
experiment would silently be a "move mass into the mountains" experiment.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

#: Regime codes written by :func:`regime_map`. ``0`` means "not in any class"
#: (outside the footprint, or high-index range interior).
REGIMES = {
    0: "unassigned",
    1: "piedmont",
    2: "range-front",
    3: "basin",
    4: "range-interior",
}

#: Defaults fixed by the pinned grid (100 m px) and by the parent's own geometry.
SMOOTH_WINDOW_PX = 31          # 3.1 km box: regional position, not pixel noise
LOWER_QUANTILE = 1.0 / 3.0
UPPER_QUANTILE = 2.0 / 3.0
FRONT_PROXIMITY_PX = 50        # 5 km: a front must touch a basin
MIN_CATALOGUE_PX = 3.0         # brief v2 §4.4 for newly emitted mass
MIN_DOT_PX = 2.8               # R0's own minimum dot spacing (measured, see run card)
QUERY_WIDTH = 24               # candidates examined per source dot before widening


def _masked_mean(block: np.ndarray, footprint: np.ndarray, window_px: int) -> np.ndarray:
    """Box mean of ``block`` over ``footprint`` only (no zero-padding leak)."""
    if window_px < 1:
        raise ValueError("smoothing window must be >= 1 px")
    inside = np.where(footprint, block, 0.0)
    num = ndi.uniform_filter(inside, size=window_px, mode="constant", cval=0.0)
    den = ndi.uniform_filter(footprint.astype(np.float32), size=window_px,
                             mode="constant", cval=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(den > 0.15, num / np.maximum(den, 1e-6), 0.0)
    return out.astype(np.float64)


def _standardise(x: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    vals = x[footprint]
    sd = float(vals.std())
    if not np.isfinite(sd) or sd <= 0:
        raise ValueError("degenerate band: standard deviation is zero on the footprint")
    return (x - float(vals.mean())) / sd


def relief_index(det_elev: np.ndarray, det_elev_slope: np.ndarray, footprint: np.ndarray,
                 *, window_px: int = SMOOTH_WINDOW_PX) -> np.ndarray:
    """Dimensionless "up and dissected" index = z(smooth det_elev) + z(smooth |slope|).

    Mean zero over the footprint; the scale is arbitrary (it is only cut at its
    own terciles), so the index is standardised once for readability.
    """
    foot = np.asarray(footprint, bool)
    up = _masked_mean(np.asarray(det_elev, np.float64), foot, int(window_px))
    rough = _masked_mean(np.abs(np.asarray(det_elev_slope, np.float64)), foot, int(window_px))
    return _standardise(up, foot) + _standardise(rough, foot)


def regime_map(index: np.ndarray, footprint: np.ndarray, *,
               lower: float = LOWER_QUANTILE, upper: float = UPPER_QUANTILE,
               front_proximity_px: int = FRONT_PROXIMITY_PX,
               smooth_window_px: int = SMOOTH_WINDOW_PX) -> tuple[np.ndarray, dict]:
    """Terciles of ``index`` -> basin / piedmont / high; the high class split by basin proximity.

    Returns ``(labels, cuts)`` where ``labels`` is a uint8 array using
    :data:`REGIMES` and ``cuts`` records the quantile values that define it.
    """
    foot = np.asarray(footprint, bool)
    idx = np.asarray(index, np.float64)
    if idx.shape != foot.shape:
        raise ValueError("index and footprint must share a shape")
    if not foot.any():
        raise ValueError("empty footprint")
    q_low, q_high = (float(v) for v in np.quantile(idx[foot], [lower, upper]))
    basin = foot & (idx <= q_low)
    hi = foot & (idx > q_high)
    if not basin.any():
        raise ValueError("lower quantile selected nothing")
    dist_basin = ndi.distance_transform_edt(~basin)
    front = hi & (dist_basin <= front_proximity_px)
    interior = hi & ~front
    pied = foot & (idx > q_low) & (idx <= q_high)
    lab = np.zeros(foot.shape, np.uint8)
    lab[pied] = 1
    lab[front] = 2
    lab[basin] = 3
    lab[interior] = 4
    cuts = dict(quantile_lower=q_low, quantile_upper=q_high,
                front_proximity_px=int(front_proximity_px),
                smooth_window_px=int(smooth_window_px),
                area_px={REGIMES[c]: int((lab == c).sum()) for c in (1, 2, 3, 4)})
    return lab, cuts


def eligible_cells(dots: np.ndarray, catalogue: np.ndarray, footprint: np.ndarray, *,
                   min_catalogue_px: float = MIN_CATALOGUE_PX,
                   min_dot_px: float = MIN_DOT_PX) -> np.ndarray:
    """Cells a RELIEF variant may newly occupy.

    Outside these constraints nothing is emitted: no mass on the catalogue, at
    least ``min_catalogue_px`` from it (the parent's own dots that already sit at
    2.236-3 px are left untouched -- editing them is the PRUNE axis), at least
    ``min_dot_px`` from every parent dot, and never on an existing dot.
    """
    dots = np.asarray(dots, bool)
    cat = np.asarray(catalogue, bool)
    foot = np.asarray(footprint, bool)
    d_cat = ndi.distance_transform_edt(~cat)
    d_dot = ndi.distance_transform_edt(~dots)
    return (foot & ~dots & (d_cat > float(min_catalogue_px))
            & (d_dot > float(min_dot_px)))


def nearest_free(tree: cKDTree, coords: np.ndarray, point: np.ndarray,
                 taken: np.ndarray) -> int:
    """Index into ``tree.data`` of the closest not-yet-taken cell to ``point``.

    Widens the query window geometrically instead of scanning the whole target
    set; raises if the target set is exhausted.
    """
    width = QUERY_WIDTH
    while True:
        k = min(width, len(tree.data))
        _d, j = tree.query(point[None, :], k=k)
        j = np.atleast_1d(j).astype(np.int64)
        free = j[~taken[j]]
        if free.size:
            return int(free[0])
        if k == len(tree.data):
            raise RuntimeError("no free destination cell left")
        width *= 4


def plan_moves(dots: np.ndarray, labels: np.ndarray, eligible: np.ndarray, *,
               source: int, destination: int, n_move: int,
               select: str = "deepest", min_dot_px: float = MIN_DOT_PX) -> tuple[np.ndarray, np.ndarray, dict]:
    """Choose ``n_move`` source-regime dots and pair each with a legal destination cell.

    Returns ``(source_flat, destination_flat, stats)``. In both modes the source
    order is fixed and independent of ``n_move``, so a smaller dose is always a
    strict prefix of a larger one -- a dose-response ladder built here is nested
    by construction, which is what makes two rungs comparable.

    ``select="deepest"`` (the shipped rule) takes the dots sitting farthest inside
    the source regime, measured by their distance to that regime's own boundary,
    so a moved dot really changes terrain setting -- a basin-floor dot becomes a
    front dot. ``select="nearest-boundary"`` takes the dots closest to a legal
    destination instead; measured on the real grid that moves every dot only
    3-4 px (300-400 m), i.e. it flips a class label without changing anything a
    geologist would call the dot's setting, so it is kept only as the control.
    """
    dots = np.asarray(dots, bool)
    lab = np.asarray(labels)
    elig = np.asarray(eligible, bool)
    if not 1 <= n_move:
        raise ValueError("n_move must be >= 1")
    if select not in ("deepest", "nearest-boundary"):
        raise ValueError(f"unknown selection rule {select!r}")
    src_sel = dots & (lab == int(source))
    dst_sel = elig & (lab == int(destination))
    n_src, n_dst = int(src_sel.sum()), int(dst_sel.sum())
    if n_move > min(n_src, n_dst):
        raise ValueError(f"cannot move {n_move}: {n_src} source dots, {n_dst} free destinations")
    src_flat = np.flatnonzero(src_sel.ravel())
    dst_flat = np.flatnonzero(dst_sel.ravel())
    shape = dots.shape

    def _rc(flat: np.ndarray) -> np.ndarray:
        return np.column_stack(np.divmod(flat, shape[1])).astype(np.float64)

    src_rc = _rc(src_flat)
    dst_rc = _rc(dst_flat)
    tree = cKDTree(dst_rc)
    d1, _j1 = tree.query(src_rc, k=1)
    depth = ndi.distance_transform_edt(lab == int(source)).ravel()[src_flat]
    key = -np.round(depth, 9) if select == "deepest" else np.round(d1, 9)
    order = np.lexsort((src_flat, key))[:int(n_move)]
    picked_src = src_flat[order]
    picked_d = d1[order]
    picked_depth = depth[order]
    # Accept destinations one at a time, and each time block every remaining
    # candidate inside the parent's own spacing disc. Without this, two dots that
    # started 2.83 px apart can be placed 1 px apart: they were legal against the
    # *parent* set, but not against each other, and the variant would then change
    # clustering as well as relief regime -- the confound IR-86-LADDER-01 records
    # for PR #28's refill. Blocking keeps min(nn) >= min_dot_px for the child, so
    # a RELIEF variant's only systematic difference from its parent is which
    # regime the mass sits in.
    shape = dots.shape
    slot = np.full(shape[0] * shape[1], -1, np.int32)
    slot[dst_flat] = np.arange(n_dst, dtype=np.int32)
    rr, cc = np.divmod(dst_flat, shape[1])
    reach = int(np.ceil(min_dot_px))
    off = [(dy, dx) for dy in range(-reach, reach + 1) for dx in range(-reach, reach + 1)
           if np.hypot(dy, dx) <= min_dot_px + 1e-9]
    off = np.array(off, np.int64)
    taken = np.zeros(n_dst, bool)
    out_dst = np.empty(len(order), np.int64)
    out_d = np.empty(len(order), np.float64)
    for i, si in enumerate(order):
        free = nearest_free(tree, dst_rc, src_rc[si], taken)
        taken[free] = True
        out_dst[i] = dst_flat[free]
        out_d[i] = float(np.hypot(*(dst_rc[free] - src_rc[si])))
        y, x = dst_rc[free].astype(np.int64)
        oy = y + off[:, 0]
        ox = x + off[:, 1]
        ok = (oy >= 0) & (oy < shape[0]) & (ox >= 0) & (ox < shape[1])
        neigh = slot[oy[ok] * shape[1] + ox[ok]]
        taken[neigh[neigh >= 0]] = True
    disp = out_d
    stats = dict(
        source=REGIMES[int(source)], destination=REGIMES[int(destination)],
        n_move=int(len(order)), n_source_available=n_src, n_destination_free=n_dst,
        selection=select,
        dose_order=("descending distance of the source dot to its own regime boundary"
                    if select == "deepest" else
                    "ascending nearest-destination distance") + ", ties by flat index",
        source_boundary_depth_px=dict(median=round(float(np.median(picked_depth)), 4),
                                      min=round(float(picked_depth.min()), 4)),
        source_regime_area_px=int((lab == int(source)).sum()),
        displacement_px=dict(mean=round(float(disp.mean()), 4),
                             median=round(float(np.median(disp)), 4),
                             p90=round(float(np.percentile(disp, 90)), 4),
                             max=round(float(disp.max()), 4)),
        source_shift_px_median=round(float(np.median(picked_d)), 4),
    )
    return picked_src.astype(np.int64), out_dst.astype(np.int64), stats


def apply_moves(dots: np.ndarray, src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Move ``src`` dots to ``dst`` cells; the count is asserted, not assumed."""
    dots = np.asarray(dots, bool)
    out = dots.ravel().copy()
    src = np.asarray(src, np.int64)
    dst = np.asarray(dst, np.int64)
    if src.size != dst.size:
        raise ValueError("src/dst must be the same length")
    if not out[src].all():
        raise ValueError("a source cell is not occupied")
    if out[dst].any():
        raise ValueError("a destination cell is already occupied")
    if np.intersect1d(src, dst).size:
        raise ValueError("a cell is both source and destination")
    out[src] = False
    out[dst] = True
    return out.reshape(dots.shape)


def nn_distances(dots: np.ndarray) -> np.ndarray:
    """Nearest-neighbour distance in px for every dot (0.0 for an isolated single dot)."""
    flat = np.flatnonzero(np.asarray(dots, bool).ravel())
    if flat.size < 2:
        return np.zeros(flat.size)
    rc = np.column_stack(np.divmod(flat, np.asarray(dots).shape[1])).astype(np.float64)
    d, _ = cKDTree(rc).query(rc, k=2)
    return np.asarray(d[:, 1], np.float64)


def relief_diff(dots: np.ndarray, new: np.ndarray, labels: np.ndarray,
                catalogue: np.ndarray, *, n_move: int) -> dict:
    """Parent-difference statistics for one RELIEF variant (brief §6 MUST record these)."""
    p = np.asarray(dots, bool)
    c = np.asarray(new, bool)
    lab = np.asarray(labels)
    removed = p & ~c
    added = c & ~p
    d_cat = ndi.distance_transform_edt(~np.asarray(catalogue, bool))
    shares = lambda arr: {REGIMES[i]: round(100.0 * int((arr & (lab == i)).sum()) / max(arr.sum(), 1), 4)
                           for i in (1, 2, 3, 4)}
    n_parent = int(p.sum())
    nn_p, nn_c = nn_distances(p), nn_distances(c)
    return dict(
        n_parent=n_parent, n_child=int(c.sum()), count_fixed=bool(p.sum() == c.sum()),
        n_removed=int(removed.sum()), n_added=int(added.sum()),
        pct_changed=round(100.0 * int(removed.sum()) / n_parent, 4) if n_parent else 0.0,
        expected_pct_changed=round(100.0 * int(n_move) / n_parent, 4) if n_parent else 0.0,
        regime_share_parent_pct=shares(p), regime_share_child_pct=shares(c),
        removed_from_regime={REGIMES[i]: int((removed & (lab == i)).sum()) for i in (1, 2, 3, 4)},
        added_in_regime={REGIMES[i]: int((added & (lab == i)).sum()) for i in (1, 2, 3, 4)},
        min_catalogue_px_child=round(float(d_cat[c].min()), 6),
        dots_in_2_3px_of_catalogue=dict(parent=int(((d_cat[p] > 2.0) & (d_cat[p] <= 3.0)).sum()),
                                        child=int(((d_cat[c] > 2.0) & (d_cat[c] <= 3.0)).sum())),
        nn_dist_px=dict(parent=dict(mean=round(float(nn_p.mean()), 4), min=round(float(nn_p.min()), 4)),
                        child=dict(mean=round(float(nn_c.mean()), 4), min=round(float(nn_c.min()), 4))),
    )
