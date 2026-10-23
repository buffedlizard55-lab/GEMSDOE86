"""TRACKB: strike-coherent traces extracted from a dot field, and a count-fixed
trace-consistent variant of that field.

Why this module exists
----------------------
TRACKB is the one AXIS in brief v2 §5 that the repository had never built. Its
brief definition is "strike-consistent traces >= 1 km built from R0's top-ranked
dots, as GeoJSON + raster, with one evidence paragraph per trace for a geologist".

The lineage ranking caveat (IR-86-TRACKB-01)
--------------------------------------------
R0's only recoverable "ranking" is the FIFO-BFS *visitation* order of the
`gems27.thinning` recipe. That order is a geographic traversal of the H19-5
field, not a geological probability: the MASS session already showed that its
first and last deciles are pure north-strip and south-half geography
(IR-86-MASS-01). The restored H19-5 mirror is binary (every positive cell is
exactly 1.0), so it carries no per-dot score either. This module therefore
substitutes the only ranking the parent actually contains -- *trace support*,
i.e. how much of its mass already lies on a coherent strike line -- and says so
on the mechanism card instead of pretending a provenance ranking exists.

What is computed
----------------
1. :func:`trace_runs` -- a deterministic Hough-style lineament detector. For
   each of 18 strike bins (10 deg steps) every dot is projected onto the along
   strike (t) and across strike (n) axes of that bin; dots are bucketed by
   ``floor(n / 1.5)`` so a trace may wander +/-0.75 px across strike, chained
   with a maximum along-strike gap, and split into runs. A run's length is its
   along-strike extent in pixels (1 px = 100 m).
2. :func:`trace_table` -- near-duplicate runs (the same physical line seen in
   two adjacent strike bins) are suppressed by a dot-overlap rule, and runs
   shorter than ``min_len_px`` are dropped. This is the trace set that is
   exported as GeoJSON.
3. :func:`plan_extension` -- the count-fixed edit. Dots are ranked by trace
   support; the lowest-support dots are removed and the same number are
   appended to the ends of the strongest traces, walking along strike inside a
   +/-20 deg cone. Every new cell must be off the catalogue, > 3 px from it and
   >= the parent's 2.828 px dot separation from every retained dot.

Nothing here reads a truth raster, contacts a network, or writes a file.
"""

from __future__ import annotations

import numpy as np

#: Strike bins in degrees from +x axis (east), counter-clockwise in (x, y) with
#: y pointing *down* the raster rows. Utilities in this repo report strike as a
#: 0-180 azimuth instead; :func:`strike_azimuth` does the conversion.
ORIENTATIONS_DEG: np.ndarray = np.arange(0.0, 180.0, 10.0)

#: Half-width of the corridor used by the detector, in pixels. Bucket width is
#: 1.5 px, so a run may wander +/-0.75 px across strike and still be one line.
CORRIDOR_PX: float = 1.5

#: Maximum along-strike gap between consecutive dots of one run. The parent was
#: thinned at d2.8, so neighbours on a strand sit 2.83 px apart; a slightly
#: larger allowance lets one missed cell be bridged, no more.
MAX_GAP_PX: float = 3.2

#: The parent's own dot separation (thinning distance sqrt(8)).
MIN_SEP_PX: float = float(np.sqrt(8.0))

#: The brief's catalogue collar for newly emitted mass (brief §4.4).
CLEARANCE_PX: float = 3.0

#: Cone half-angle tried when extending a trace end, degrees.
CONE_DEG: tuple[float, ...] = (0.0, 5.0, -5.0, 10.0, -10.0, 15.0, -15.0, 20.0, -20.0)


def strike_azimuth(theta_deg: float) -> float:
    """Convert a detector angle (from +x/east, y down) to a 0-180 azimuth.

    The competition grid is a north-up projected raster, so +x is east and +y is
    *south*. Rotating a vector measured clockwise from east into a compass
    azimuth therefore means ``az = (90 - theta) mod 180``.
    """
    return float((90.0 - float(theta_deg)) % 180.0)


def _occupied_offsets(min_sep: float = MIN_SEP_PX) -> np.ndarray:
    """Lattice offsets strictly closer than ``min_sep`` to the origin."""
    r = int(np.ceil(min_sep))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    inside = (dy * dy + dx * dx) < (min_sep * min_sep) - 1e-9
    return np.column_stack([dy[inside], dx[inside]])


OCCUPIED_OFFSETS = _occupied_offsets()


def trace_runs(dots: np.ndarray, orientations: np.ndarray = ORIENTATIONS_DEG,
               corridor_px: float = CORRIDOR_PX, max_gap_px: float = MAX_GAP_PX,
               min_dots: int = 3) -> list[dict]:
    """All maximal collinear runs of at least ``min_dots`` dots, per strike bin.

    Deterministic: the ordering of dots inside a run is an ``lexsort`` on
    (along strike, bucket) with the flat cell index as the final tie break.
    """
    dots = np.asarray(dots, bool)
    rows, cols = np.nonzero(dots)
    if rows.size < min_dots:
        return []
    x = cols.astype(np.float64)
    y = rows.astype(np.float64)
    flat = rows.astype(np.int64) * dots.shape[1] + cols
    half = float(corridor_px) / 2.0
    runs: list[dict] = []
    for theta_index, theta in enumerate(np.asarray(orientations, float)):
        rad = np.deg2rad(theta)
        ux, uy = np.cos(rad), np.sin(rad)
        t = x * ux + y * uy
        n = -x * uy + y * ux
        bucket = np.floor(n / half).astype(np.int64)
        order = np.lexsort((flat, t, bucket))
        b_sorted = bucket[order]
        t_sorted = t[order]
        i_sorted = flat[order]   # order indexes the dot list; map it back to flat cells
        starts = np.r_[0, np.flatnonzero(np.diff(b_sorted) != 0) + 1]
        ends = np.r_[starts[1:], b_sorted.size]
        for s, e in zip(starts.tolist(), ends.tolist()):
            ts = t_sorted[s:e]
            ids = i_sorted[s:e]
            if ts.size < min_dots:
                continue
            breaks = np.flatnonzero(np.diff(ts) > max_gap_px)
            seg_starts = np.r_[0, breaks + 1]
            seg_ends = np.r_[breaks + 1, ts.size]
            for ss, ee in zip(seg_starts.tolist(), seg_ends.tolist()):
                if ee - ss < min_dots:
                    continue
                seg_t = ts[ss:ee]
                runs.append({
                    "theta_index": int(theta_index),
                    "theta_deg": float(theta),
                    "bucket": int(b_sorted[s]),
                    "length_px": float(seg_t[-1] - seg_t[0] + 1.0),
                    "dot_flat": ids[ss:ee].astype(np.int64),
                    "t": seg_t,
                    "t0": float(seg_t[0]),
                    "t1": float(seg_t[-1]),
                    "n_center": float((b_sorted[s] + 0.5) * half),
                })
    return runs


def dot_support(dots: np.ndarray, runs: list[dict]) -> np.ndarray:
    """Longest run length (px) containing each dot; 0 for a dot on no run."""
    support = np.zeros(np.asarray(dots).shape, np.float64)
    width = np.asarray(dots).shape[1]
    for run in runs:
        rows = run["dot_flat"] // width
        cols = run["dot_flat"] % width
        support[rows, cols] = np.maximum(support[rows, cols], run["length_px"])
    return support


def trace_table(dots: np.ndarray, runs: list[dict], min_len_px: float,
                overlap_frac: float = 0.5) -> list[dict]:
    """Non-redundant traces at or above ``min_len_px``, strongest first.

    A run is rejected when more than ``overlap_frac`` of its dots are already in
    an accepted trace: that is the same physical line seen in an adjacent strike
    bin, not a second structure.
    """
    shape = np.asarray(dots).shape
    width = shape[1]
    candidates = sorted((r for r in runs if r["length_px"] >= float(min_len_px)),
                        key=lambda r: (-r["length_px"], r["theta_index"], r["bucket"],
                                       int(r["dot_flat"][0])))
    claimed = np.zeros(shape, bool)
    accepted: list[dict] = []
    for run in candidates:
        rows = run["dot_flat"] // width
        cols = run["dot_flat"] % width
        shared = float(claimed[rows, cols].mean())
        if shared > overlap_frac:
            continue
        claimed[rows, cols] = True
        accepted.append(dict(run, n_dots=int(run["dot_flat"].size),
                             n_new_dots=int((~claimed[rows, cols]).sum() * 0 + run["dot_flat"].size),
                             overlap_with_stronger=round(shared, 4),
                             theta_index=len(accepted),
                             rank=len(accepted)))
    # n_new_dots is reported after claiming, i.e. how many cells of this trace were
    # not already covered by a stronger one.
    for i, tr in enumerate(accepted):
        rows = tr["dot_flat"] // width
        cols = tr["dot_flat"] % width
        earlier = np.zeros(shape, bool)
        for prev in accepted[:i]:
            earlier[prev["dot_flat"] // width, prev["dot_flat"] % width] = True
        tr["n_new_dots"] = int((~earlier[rows, cols]).sum())
    return accepted


def trace_length_summary(lengths_px: np.ndarray) -> dict:
    lengths_px = np.asarray(lengths_px, float)
    if lengths_px.size == 0:
        return {"n": 0, "max_px": 0.0, "median_px": 0.0, "total_px": 0.0}
    return {"n": int(lengths_px.size), "max_px": round(float(lengths_px.max()), 2),
            "median_px": round(float(np.median(lengths_px)), 2),
            "total_px": round(float(lengths_px.sum()), 2)}


def select_donors(dots: np.ndarray, support: np.ndarray, n_remove: int) -> np.ndarray:
    """Boolean mask of the ``n_remove`` least trace-supported *dots*.

    ``support`` is a full-raster array and is zero on non-dot cells, so the dot
    mask must be supplied: an earlier revision used ``support >= 0``, which is
    true for every cell of the raster, and silently donated empty cells. Caught
    by the fixed-count gate, not by the tests (IR-86-TRACKB-02).
    """
    dots = np.asarray(dots, bool)
    support = np.asarray(support, float)
    if support.shape != dots.shape:
        raise ValueError("support and dots must share a shape")
    if int(n_remove) > int(dots.sum()):
        raise ValueError("cannot donate more dots than the parent has")
    candidates = np.argwhere(dots)  # dots only
    values = support[tuple(candidates.T)]
    keys = np.lexsort((candidates[:, 1], candidates[:, 0], values))
    chosen = candidates[keys[:int(n_remove)]]
    mask = np.zeros(support.shape, bool)
    mask[chosen[:, 0], chosen[:, 1]] = True
    return mask


def _ends(trace: dict, width: int) -> list[tuple[float, float, float, float]]:
    """(row, col, dir_row, dir_col) for both ends of a trace, pointing outwards."""
    flat = trace["dot_flat"]
    rows = (flat // width).astype(float)
    cols = (flat % width).astype(float)
    t = np.asarray(trace["t"], float)
    order = np.argsort(t)
    rad = np.deg2rad(trace["theta_deg"])
    uy, ux = np.sin(rad), np.cos(rad)          # (row, col)
    first = (rows[order[0]], cols[order[0]])
    last = (rows[order[-1]], cols[order[-1]])
    return [(first[0], first[1], -uy, -ux), (last[0], last[1], uy, ux)]


def plan_extension(kept: np.ndarray, traces: list[dict], footprint: np.ndarray,
                   distance_to_catalogue: np.ndarray, n_add: int,
                   *, min_sep_px: float = MIN_SEP_PX, clearance_px: float = CLEARANCE_PX,
                   max_steps: int = 24, cone_deg: tuple[float, ...] = CONE_DEG,
                   step_px: float | None = None) -> tuple[np.ndarray, dict]:
    """Walk each trace end along strike and emit up to ``n_add`` new unit dots.

    Returns ``(added_mask, stats)``. Deterministic: traces are visited strongest
    first, the two ends in (t_min, t_max) order, and the cone is scanned in the
    declared order of ``cone_deg``.
    """
    kept = np.asarray(kept, bool)
    height, width = kept.shape
    # One step must clear the parent's own dot separation, otherwise every
    # candidate cell is inside the occupied halo of the dot it leaves.
    step = float(min_sep_px + 0.1) if step_px is None else float(step_px)
    if step <= min_sep_px:
        raise ValueError("step_px must exceed the dot separation")
    occupied = kept.copy()
    added = np.zeros_like(occupied)
    offs = OCCUPIED_OFFSETS
    struck_by: dict[int, int] = {}
    visited_traces = 0
    short = 0
    for trace in traces:
        if int(added.sum()) >= n_add:
            break
        visited_traces += 1
        for (r0, c0, dy, dx) in _ends(trace, width):
            pos_r, pos_c = float(r0), float(c0)
            dir_r, dir_c = float(dy), float(dx)
            for _ in range(int(max_steps)):
                if int(added.sum()) >= n_add:
                    break
                placed = False
                for delta in cone_deg:
                    a = np.deg2rad(delta)
                    nr = dir_r * np.cos(a) - dir_c * np.sin(a)
                    nc = dir_r * np.sin(a) + dir_c * np.cos(a)
                    rr, cc = pos_r + step * nr, pos_c + step * nc
                    r, c = int(round(rr)), int(round(cc))
                    if not (0 <= r < height and 0 <= c < width):
                        continue
                    if not footprint[r, c] or distance_to_catalogue[r, c] <= clearance_px:
                        continue
                    if occupied[r, c]:
                        continue
                    blocked = any(
                        0 <= r + orow < height and 0 <= c + ocol < width
                        and occupied[r + orow, c + ocol]
                        for orow, ocol in offs)
                    if blocked:
                        continue
                    added[r, c] = True
                    occupied[r, c] = True
                    pos_r, pos_c = rr, cc
                    dir_r, dir_c = nr, nc
                    struck_by[trace["rank"]] = struck_by.get(trace["rank"], 0) + 1
                    placed = True
                    break
                if not placed:
                    break
    if int(added.sum()) < n_add:
        short = int(n_add - int(added.sum()))
    stats = {
        "requested_added": int(n_add),
        "added": int(added.sum()),
        "shortfall": short,
        "traces_visited": visited_traces,
        "dots_placed_per_trace": {str(k): v for k, v in sorted(struck_by.items())},
        "cone_deg": list(cone_deg),
        "step_px": round(step, 3),
        "min_sep_px": float(min_sep_px),
        "clearance_px": float(clearance_px),
    }
    return added, stats


def apply_swap(dots: np.ndarray, remove: np.ndarray, add: np.ndarray) -> np.ndarray:
    """The count-fixed edit: delete ``remove`` and emit ``add`` (must not overlap)."""
    dots = np.asarray(dots, bool)
    remove = np.asarray(remove, bool)
    add = np.asarray(add, bool)
    if np.any(remove & add):
        raise ValueError("a cell cannot be both donated and refilled")
    out = (dots & ~remove) | add
    if int(out.sum()) != int(dots.sum()):
        raise ValueError(f"count not fixed: {int(dots.sum())} -> {int(out.sum())}")
    return out


def diff_stats(parent: np.ndarray, child: np.ndarray) -> dict:
    """Parent-diff statistics required by brief v2 §6."""
    parent = np.asarray(parent, bool)
    child = np.asarray(child, bool)
    removed = int((parent & ~child).sum())
    added = int((child & ~parent).sum())
    n = int(parent.sum())
    return {
        "parent_dots": n,
        "candidate_dots": int(child.sum()),
        "removed": removed,
        "added": added,
        "retained": int((parent & child).sum()),
        "changed": removed + added,
        "pct_changed": round(100.0 * (removed + added) / n, 4),
        "pct_removed": round(100.0 * removed / n, 4),
        "pct_added": round(100.0 * added / n, 4),
        "count_fixed": int(child.sum()) == n,
    }


def broken_traces(before: list[dict], after: np.ndarray) -> dict:
    """How many exported traces lost at least one dot to the donor cut."""
    after = np.asarray(after, bool)
    width = after.shape[1]
    lost = [int((~after[tr["dot_flat"] // width, tr["dot_flat"] % width]).sum()) for tr in before]
    return {"n_traces": len(before),
            "n_traces_with_lost_dots": int(sum(1 for x in lost if x > 0)),
            "dots_lost_from_traces": int(sum(lost)),
            "max_lost_from_one_trace": int(max(lost)) if lost else 0}


def traces_to_geojson(traces: list[dict], n_added_by_trace: dict[int, int],
                      transform, crs_wkt: str, catalogue_distance: np.ndarray) -> dict:
    """GeoJSON FeatureCollection of the trace set, one LineString per trace."""
    features = []
    for tr in traces:
        flat = np.asarray(tr["dot_flat"], np.int64)
        order = np.argsort(np.asarray(tr["t"], float))
        flat = flat[order]
        rows = (flat // catalogue_distance.shape[1]).astype(float)
        cols = (flat % catalogue_distance.shape[1]).astype(float)
        coords = []
        for r, c in zip(rows.tolist(), cols.tolist()):
            x, y = transform @ (c + 0.5, r + 0.5)
            coords.append([round(float(x), 1), round(float(y), 1)])
        d = catalogue_distance[flat // catalogue_distance.shape[1],
                               flat % catalogue_distance.shape[1]]
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "trace_id": f"TRK-{tr['rank']:03d}",
                "length_km": round(float(tr["length_px"]) / 10.0, 2),
                "strike_azimuth_deg": round(strike_azimuth(tr["theta_deg"]), 1),
                "n_dots": int(tr["n_dots"]),
                "n_dots_shared_with_stronger_trace": int(tr["n_dots"]) - int(tr["n_new_dots"]),
                "dots_added_by_this_edit": int(n_added_by_trace.get(tr["rank"], 0)),
                "median_catalogue_distance_px": round(float(np.median(d)), 2),
                "min_catalogue_distance_px": round(float(d.min()), 2),
                "evidence_paragraph": trace_paragraph(tr, catalogue_distance, n_added_by_trace),
            },
        })
    return {"type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32611"}},
            "note": ("Trace set extracted from R0 (GEMSDOE32 h33-h33-2-b2) dot geometry only. "
                     "No new physical field was used; strike bins are 10 degrees, the corridor is "
                     "+/-0.75 px, and the minimum length is set by the variant. Candidate "
                     "predictions, not mapped faults."),
            "features": features}


def trace_paragraph(trace: dict, catalogue_distance: np.ndarray,
                    n_added_by_trace: dict[int, int]) -> str:
    """One plain-language evidence paragraph, deterministic from the geometry.

    Deliberately conservative: it states what the geometry is, where it is, how
    far it is from the mapped catalogue, and what would falsify it. A structural
    geologist is the intended reader, so no probability language is used.
    """
    rows = (trace["dot_flat"] // catalogue_distance.shape[1])
    cols = (trace["dot_flat"] % catalogue_distance.shape[1])
    d = catalogue_distance[rows, cols]
    n_shared = int(trace["n_dots"]) - int(trace["n_new_dots"])
    added = int(n_added_by_trace.get(trace["rank"], 0))
    az = strike_azimuth(trace["theta_deg"])
    return (
        f"TRK-{trace['rank']:03d}: a {trace['length_px'] / 10.0:.1f} km strike line at "
        f"{az:.0f} deg azimuth carried by {int(trace['n_dots'])} unit dots, of which "
        f"{added} were emitted by this edit as along-strike continuation. The line stays a "
        f"median {float(np.median(d)):.1f} px ({float(np.median(d)) * 100:.0f} m) and at least "
        f"{float(d.min()):.1f} px from the mapped catalogue, so it is not a redrawing of a known "
        f"trace; {n_shared} of its dots are shared with a stronger line in an adjacent strike "
        f"bin, which is the usual signature of one strand at a bin boundary. Falsifier: an "
        f"independent lineament map (lidar shading or field mapping) that shows nothing along "
        f"this azimuth within 300 m of the line."
    )
