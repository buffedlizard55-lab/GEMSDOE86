"""Pure geometry for the TRACKB axis: strike-consistent traces from R0's dots.

Phase 2 of the GEMS Prize (problem page, brief sec.2) rescores against labels
that experts expand *after reviewing submitted faults*.  A dot field cannot be
reviewed; a trace can.  TRACKB therefore converts the parent's dots into
strike-consistent polylines of at least 1 km, with one evidence paragraph per
trace, as GeoJSON plus a raster rendering.  It is **not** a weekly-slot
candidate unless the human decides otherwise (brief sec.5).

What this module is allowed to know
-----------------------------------
Nothing but the parent's own dot mask, the footprint and the catalogue
distance field.  No band, no label, no probability field enters a placement:
that keeps the axis attributable to *geometry* alone (the same discipline the
SPACING session applied), and it means "R0's top-ranked dots" (brief sec.5)
cannot mean the MASS session's FIFO-BFS traversal order -- that order is a
geographic walk, not a quality ranking (IR-86-MASS-01).  Here a dot's rank is
its *chain support*: whether it lies on a strike-consistent chain of at least
1 km, and how long / straight that chain is.  Dots on no such chain are, for
Phase-2 purposes, unranked, and are reported as such rather than hidden.

Chain rule (the only free parameter is the turning-angle ceiling)
-----------------------------------------------------------------
Greedy two-sided path growth on the dot graph:

* vertices are R0 dots; a step joins dots at most ``MAX_STEP_PX`` apart
  (R0's thinning floor is 2.828 px, so 4.5 px admits the floor diagonal and
  one missing dot, but not a jump across a step-over);
* at each tip the next dot is the unused neighbour minimising the turning
  angle against the incoming direction, admitted only if that angle is at
  most ``max_turn_deg`` -- the variant's single value;
* seeds are tried in descending local-neighbour count (geography-blind: a
  count, never a row/column index; IR-86-MASS-01 designed out);
* a chain is kept iff it has at least ``MIN_DOTS`` dots and a polyline length
  of at least ``MIN_LENGTH_PX`` = 10 px = 1 km (brief sec.5); its dots are
  then consumed.  Shorter chains release their dots.

The three variants differ **only** in ``max_turn_deg`` (20 / 30 / 40).  Step,
length floor, seed order, exclusions and raster rule are shared, so any
difference between arms is the coherence threshold and nothing else.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

MAX_STEP_PX = 4.5
MIN_LENGTH_PX = 10.0          # 1 km on the 100 m grid (brief sec.5: traces >= 1 km)
MIN_DOTS = 4
#: new (non-dot) raster mass must clear the catalogue by this much (brief 4.4);
#: inherited member dots keep R0's own >= 2.236 px geometry (IR-86-RELIEF-02).
NEW_MASS_CLEARANCE_PX = 3.0
EPS = 1e-9


def dot_points(mask: np.ndarray) -> np.ndarray:
    """(row, col) float points of a boolean dot mask, row-major (deterministic)."""
    return np.argwhere(np.asarray(mask, bool)).astype(np.float64)


def _grow(points: np.ndarray, tree: cKDTree, chain: list[int], used: np.ndarray,
          max_step: float, max_turn_deg: float, forward: bool) -> list[int]:
    """Extend ``chain`` at one end; ``forward`` appends, otherwise prepends."""
    chain = list(chain)
    while len(chain) >= 1:
        tip = chain[-1] if forward else chain[0]
        if len(chain) >= 2:
            prev = chain[-2] if forward else chain[1]
            direction = points[tip] - points[prev]
            n = float(np.linalg.norm(direction))
            if n < EPS:
                break
            direction = direction / n
        else:
            direction = None
        best, best_key = None, None
        for j in tree.query_ball_point(points[tip], max_step):
            j = int(j)
            if j == tip or used[j] or j in chain:
                continue
            step = points[j] - points[tip]
            dist = float(np.linalg.norm(step))
            if dist < EPS or dist > max_step + EPS:
                continue
            if direction is None:
                ang = 0.0
            else:
                ang = float(np.degrees(np.arccos(
                    np.clip(step @ direction / dist, -1.0, 1.0))))
                if ang > max_turn_deg + EPS:
                    continue
            key = (ang, dist, j)          # deterministic tie-break
            if best_key is None or key < best_key:
                best, best_key = j, key
        if best is None:
            break
        if forward:
            chain.append(best)
        else:
            chain.insert(0, best)
    return chain


def extract_traces(mask: np.ndarray, max_turn_deg: float,
                   max_step: float = MAX_STEP_PX,
                   min_length_px: float = MIN_LENGTH_PX,
                   min_dots: int = MIN_DOTS) -> tuple[list[dict], dict]:
    """Strike-consistent chains of ``mask`` at one turning-angle ceiling.

    Returns ``(traces, stats)``; each trace is a dict of measured geometry
    only (no band, label or field is read anywhere in this module).
    """
    points = dot_points(mask)
    if len(points) == 0:
        raise ValueError("empty dot field")
    tree = cKDTree(points)
    nbr_counts = np.array([len(tree.query_ball_point(p, max_step)) - 1
                           for p in points], dtype=np.int64)
    # geography-blind seed order: most-supported first, index breaks ties
    order = sorted(range(len(points)), key=lambda i: (-int(nbr_counts[i]), i))
    used = np.zeros(len(points), bool)
    traces: list[dict] = []
    attempted = 0
    for seed in order:
        if used[seed]:
            continue
        attempted += 1
        chain = _grow(points, tree, [seed], used, max_step, max_turn_deg, True)
        chain = _grow(points, tree, chain, used, max_step, max_turn_deg, False)
        stats = trace_stats(points[chain]) if len(chain) >= 2 else None
        if stats and len(chain) >= min_dots and stats["length_px"] >= min_length_px - EPS:
            used[chain] = True
            traces.append({"dot_indices": [int(i) for i in chain], **stats})
        # a failed seed stays unused: a later, straighter seed may claim its dots
    traces.sort(key=lambda t: (-t["length_px"], t["dot_indices"][0]))
    for k, t in enumerate(traces, 1):
        t["trace_id"] = f"T{k:04d}"
    n_traced = int(sum(len(t["dot_indices"]) for t in traces))
    stats = {
        "max_turn_deg": float(max_turn_deg), "max_step_px": float(max_step),
        "min_length_px": float(min_length_px), "min_dots": int(min_dots),
        "n_parent_dots": int(len(points)), "seeds_attempted": int(attempted),
        "n_traces": len(traces), "n_traced_dots": n_traced,
        "pct_parent_dots_traced": round(100.0 * n_traced / len(points), 4),
        "total_length_km": round(float(sum(t["length_px"] for t in traces)) / 10.0, 3),
        "median_length_km": round(float(np.median([t["length_px"] for t in traces])) / 10.0, 3)
        if traces else 0.0,
        "max_length_km": round(float(max(t["length_px"] for t in traces)) / 10.0, 3) if traces else 0.0,
    }
    return traces, stats


def trace_stats(pts: np.ndarray) -> dict:
    """Measured geometry of one polyline given as (row, col) points."""
    pts = np.asarray(pts, dtype=np.float64)
    steps = np.diff(pts, axis=0)
    seg = np.linalg.norm(steps, axis=1)
    length = float(seg.sum())
    extent = float(np.linalg.norm(pts[-1] - pts[0])) if len(pts) else 0.0
    turns = []
    for a, b in zip(steps[:-1], steps[1:]):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na > EPS and nb > EPS:
            turns.append(float(np.degrees(np.arccos(np.clip(a @ b / (na * nb), -1, 1)))))
    # strike: azimuth (deg clockwise from north = -row) of the PCA major axis
    centred = pts - pts.mean(axis=0)
    cov = centred.T @ centred
    vec = np.linalg.eigvalsh(cov)
    w, v = np.linalg.eigh(cov)
    major = v[:, int(np.argmax(w))]
    azimuth = float(np.degrees(np.arctan2(major[1], -major[0])) % 180.0)
    resid = centred - np.outer(centred @ major, major)
    rms = float(np.sqrt(np.mean(np.sum(resid ** 2, axis=1)))) if len(pts) else 0.0
    return {
        "length_px": round(length, 4), "extent_px": round(extent, 4),
        "sinuosity": round(length / extent, 4) if extent > EPS else None,
        "n_dots": int(len(pts)),
        "strike_azimuth_deg": round(azimuth, 2),
        "mean_turn_deg": round(float(np.mean(turns)), 3) if turns else 0.0,
        "max_turn_deg_measured": round(float(np.max(turns)), 3) if turns else 0.0,
        "rms_residual_px": round(rms, 4),
        "mean_step_px": round(float(seg.mean()), 4) if len(seg) else 0.0,
        "max_step_px_measured": round(float(seg.max()), 4) if len(seg) else 0.0,
        "eig_ratio": round(float(vec[-1] / vec[-2]), 3) if len(vec) > 1 and vec[-2] > EPS else None,
    }


def rasterize(traces: list[dict], points: np.ndarray, shape: tuple[int, int],
              catalogue_edt: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, dict]:
    """Render traces to a unit-mass pixel mask under the brief-4.4 rule.

    Member dots are inherited R0 mass (R0's own >= 2.236 px catalogue geometry);
    every *new* pixel a segment creates must sit > ``NEW_MASS_CLEARANCE_PX``
    from the catalogue and inside the footprint, or it is dropped and counted.
    The GeoJSON polyline is the Phase-2 object; this raster is its rendering,
    so a dropped pixel is a rendering gap, never a moved trace.
    """
    out = np.zeros(shape, bool)
    member = np.zeros(shape, bool)
    dropped = 0
    kept_new = 0
    for t in traces:
        pts = points[t["dot_indices"]]
        for r, c in pts:
            member[int(r), int(c)] = True
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(2, int(np.ceil(np.linalg.norm(b - a) / 0.25)) + 1)
            for r, c in np.linspace(a, b, n):
                ri, ci = int(round(r)), int(round(c))
                if not (0 <= ri < shape[0] and 0 <= ci < shape[1]):
                    continue
                if member[ri, ci] or out[ri, ci]:
                    continue
                if footprint[ri, ci] and catalogue_edt[ri, ci] > NEW_MASS_CLEARANCE_PX + EPS:
                    out[ri, ci] = True
                    kept_new += 1
                else:
                    dropped += 1
    out |= member & footprint
    return out, {"member_dot_px": int((member & footprint).sum()),
                 "new_segment_px_kept": int(kept_new),
                 "new_segment_px_dropped_clearance": int(dropped)}


def evidence_paragraph(trace: dict, cat_dist_px: dict) -> str:
    """One geologist-facing paragraph per trace, from measured numbers only."""
    return (
        f"{trace['trace_id']}: {trace['n_dots']} of R0's dots form a "
        f"{trace['length_px'] / 10.0:.2f} km polyline (end-to-end "
        f"{trace['extent_px'] / 10.0:.2f} km, sinuosity {trace['sinuosity']}) at a PCA strike of "
        f"{trace['strike_azimuth_deg']:.0f} deg (mod 180), with mean turning angle "
        f"{trace['mean_turn_deg']:.1f} deg (max {trace['max_turn_deg_measured']:.1f} deg), RMS "
        f"residual {trace['rms_residual_px']:.2f} px from the fitted strike line, and mean dot "
        f"spacing {trace['mean_step_px']:.2f} px. Its nearest approach to a mapped catalogue "
        f"fault is {cat_dist_px['min']:.2f} px (median {cat_dist_px['median']:.2f} px), so it is "
        f"not a re-tracing of a known fault. Read as a candidate blind or unmapped fault strand "
        f"whose dots the parent field already placed independently of this chaining; the "
        f"non-fault process that could mimic it is a chance alignment of field maxima (or a "
        f"cultural/drainage lineament) at the 2.8-4.5 px dot spacing, which is why the turning-"
        f"angle ceiling and the 1 km floor, not the eye, decide membership. Falsifier: an expert "
        f"reviewer rejects the lineament, or a stricter ceiling dissolves it."
    )
