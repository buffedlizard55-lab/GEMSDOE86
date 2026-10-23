"""Pure geometry for the SPACING axis: relocate the metric's *redundant* mass under three
different spacing laws, at a fixed dot count.

Why this axis (and nothing else) is here
----------------------------------------
Every step of this lineage's climb was an edit of the same physical quantity: how much of a
dot's unit mass is *already* claimed by a neighbour.  The official score is a max over the
triangular kernel of radius ``R = 3 px = 300 m`` (``vendor/gems57/metric.py``:
``TP_w = sum_g max_x p(x) k(d(x,g))``, ``FP_w = sum_x p(x) [1 - max_g k]``), so two dots closer
than ``R`` cannot both earn credit for the truth pixel between them, while each still pays its
full false-positive term.  ``d1.5 -> d2.8`` thinning bought +0.0123 live (0.2477 -> 0.2600, both
CLAIM, not receipts) and SNAP's measured damage was a spacing effect (dots closer than 2 px:
0 -> 3,448).  Mass, collar, relief and block concentration have all been swept on this parent;
the *arrangement law* at the kernel scale has not.

What this module is allowed to know
-----------------------------------
Nothing but the parent's own dot mask, the pinned footprint and the pinned catalogue.  No band,
no label and no probability field enters a placement: a candidate cell is chosen by (a) the
distance to the nearest retained dot and (b) the arm's geometric law.  That is deliberate.  The
moment a placement uses a geophysical response it becomes SNAP, which three sessions have
measured as negative, and the edit stops being attributable to spacing.

The four arms differ **only** in which cells inside the local window are admissible:

``pdisk``    every eligible cell            -> isotropic hard-core (blue noise / Poisson-disk)
``lattice``  hexagonal covering nodes only   -> maximally even, ordered placement
``strike``   cells on the local dot ridge    -> keep the trace and extend it
``random``   a uniform draw from the window  -> null control: the cost of moving at all

Which dots move is shared by all four arms: every dot whose exclusive disc credit is at or below a
stated threshold (:func:`exclusive_credit`), i.e. the mass the metric's own max-operator has
already written off.  The dose is therefore a statement about redundancy, not a percentage.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

#: Official kernel radius in pixels (300 m on the 100 m grid).
R_PX = 3.0
#: The thinnest hexagonal *covering* of the plane by discs of radius R has node spacing
#: ``sqrt(3) * R``: every cell of the plane is then within R of a node, and no denser ordered
#: arrangement covers more area per dot.
HEX_SPACING_PX = float(np.sqrt(3.0) * R_PX)          # 5.1961524227...
#: R0's own nearest-neighbour floor, inherited from the d2.8 thinning that produced it.
PARENT_FLOOR_PX = float(np.sqrt(8.0))                 # 2.8284271247...
EPS = 1e-9

LAWS = ("pdisk", "lattice", "strike", "random")


# --------------------------------------------------------------------------- mechanism measures
def disc_offsets(radius: float = R_PX) -> np.ndarray:
    """Integer offsets with non-zero triangular-kernel weight (``d <= radius``)."""
    r = int(np.floor(radius + EPS))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    keep = np.hypot(dy, dx) <= radius + EPS
    return np.stack([dy[keep], dx[keep]], axis=1).astype(np.int64)


def disc_cover(dots: np.ndarray, radius: float = R_PX) -> np.ndarray:
    """Boolean union of every dot's kernel disc (``distance to the nearest dot <= radius``)."""
    return ndi.distance_transform_edt(~np.asarray(dots, bool)) <= radius + EPS


def exclusive_credit(dots: np.ndarray, radius: float = R_PX) -> tuple[np.ndarray, dict]:
    """Cells each dot owns exclusively, i.e. that no other dot reaches first.

    Every grid cell is assigned to its nearest dot (a Voronoi partition on the pixel lattice), and
    only cells within ``radius`` of their owner count.  Under a max kernel that exclusive set is
    precisely the part of a dot's credit a neighbour cannot take away, so a small value means
    *redundant mass* rather than a wrong location.

    ``redundancy_fraction`` is the share of the nominal disc area (``n_dots`` full discs) that
    is lost because another dot reaches those cells first: it is the metric's max-operator
    written as a single number, and it is what this whole axis exists to reduce.

    Returns ``(per_dot_counts, stats)``.
    """
    dots = np.asarray(dots, bool)
    if not dots.any():
        raise ValueError("empty dot field")
    h, w = dots.shape
    dist, (ri, ci) = ndi.distance_transform_edt(~dots, return_indices=True)
    owner = np.int64(w) * ri + ci
    inside = dist <= radius + EPS
    counts = np.bincount(owner[inside].ravel(), minlength=h * w)
    flat = np.int64(w) * dots.nonzero()[0] + dots.nonzero()[1]
    per_dot = counts[flat].astype(np.int64)
    stats = {
        "exclusive_cells_mean": round(float(per_dot.mean()), 4),
        "exclusive_cells_median": float(np.median(per_dot)),
        "exclusive_cells_min": int(per_dot.min()),
        "exclusive_cells_max": int(per_dot.max()),
        "disc_cells_max_possible": int(len(disc_offsets(radius))),
        "union_disc_cells": int(inside.sum()),
        "redundancy_fraction": round(1.0 - float(per_dot.sum())
                                    / float(len(per_dot) * len(disc_offsets(radius))), 6),
        "exclusive_cells_total": int(per_dot.sum()),
    }
    return per_dot, stats


def congestion(dots: np.ndarray, radius: float = R_PX) -> np.ndarray:
    """Number of parent dots inside each dot's kernel disc, the dot itself excluded.

    Used only to order the moves (most congested first).  Ordering by a *count* keeps the
    sequence geography-blind; ordering by row-major index alone is what made the MASS session's
    dropped 10 % "100 % southern-half dots" (IR-86-MASS-01), so the failure mode is designed out
    here and then measured, not assumed away.
    """
    dots = np.asarray(dots, bool)
    pts = np.argwhere(dots).astype(np.float64)
    if len(pts) < 2:
        return np.zeros(len(pts), np.int32)
    tree = cKDTree(pts)
    return np.asarray([len(tree.query_ball_point(pt, r=radius + EPS)) - 1 for pt in pts], np.int32)


def select_redundant(dots: np.ndarray, credit_max: int,
                     radius: float = R_PX) -> tuple[np.ndarray, np.ndarray, dict]:
    """Every parent dot whose exclusive disc credit is ``<= credit_max``, in the order they move.

    The dose is a *threshold on the mechanism variable*, not a count, because the credit
    distribution is quantised: a count-based cut lands inside a tie class (credit 17: 3,411 dots
    on R0) and the tie-break would then silently decide which dots move.  A threshold needs no
    tie-break, so no pixel-scan order can select the dose.

    Move order inside a credit class is most-congested-first, then row-major.  Returns
    ``(selection_mask, flat_indices_in_move_order, info)``; everything is reproducible from the
    parent mask alone with no RNG.
    """
    dots = np.asarray(dots, bool)
    per_dot, st = exclusive_credit(dots, radius)
    rows, cols = dots.nonzero()
    flat = np.int64(dots.shape[1]) * rows + cols
    cong = congestion(dots, radius)
    keep = per_dot <= int(credit_max)
    idx = np.flatnonzero(keep)
    order = np.lexsort((flat[idx], -cong[idx], per_dot[idx]))   # credit asc, then congestion desc
    chosen = idx[order]
    sel = np.zeros(dots.shape, bool)
    sel[rows[chosen], cols[chosen]] = True
    info = {
        "credit_threshold": int(credit_max),
        "kernel_disc_cells": int(len(disc_offsets(radius))),
        "n_selected": int(sel.sum()),
        "pct_of_parent_selected": round(100.0 * int(sel.sum()) / max(int(dots.sum()), 1), 4),
        "credit_selected_mean": round(float(per_dot[chosen].mean()), 4) if chosen.size else None,
        "credit_selected_max": int(per_dot[chosen].max()) if chosen.size else None,
        "credit_kept_min": int(per_dot[~keep].min()) if (~keep).any() else None,
        "dots_at_threshold": int((per_dot == int(credit_max)).sum()),
        "parent_redundancy_fraction": st["redundancy_fraction"],
        "selection_rule": (f"every parent dot owning <= {int(credit_max)} of the "
                           f"{len(disc_offsets(radius))} cells of its radius-{radius:g} px kernel "
                           "disc, i.e. mass the max-operator has already written off; move order "
                           "is credit ascending, then congestion descending, then row-major"),
    }
    return sel, flat[chosen], info



def ridge_axes(dots: np.ndarray, k: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """Local strike direction ``(dy, dx)`` and line-likeness (coherence) for every dot.

    PCA of the ``k`` nearest other dots.  For a thinned lineament field the neighbourhood cloud is
    elongated along the trace, so the leading eigenvector is the local strike and
    ``coherence = (l1 - l2) / (l1 + l2)`` says how line-like the neighbourhood is.  The parent's
    own geometry is the only input, which is what keeps this axis out of SNAP's territory.

    Point order is ``dots.nonzero()`` (row-major).
    """
    pts = np.argwhere(np.asarray(dots, bool)).astype(np.float64)
    n = len(pts)
    vec = np.zeros((n, 2), np.float64)
    coh = np.zeros(n, np.float64)
    if n < 4:
        return vec, coh
    tree = cKDTree(pts)
    dist, idx = tree.query(pts, k=min(k + 1, n))
    for i in range(n):
        live = (dist[i] > 0) & np.isfinite(dist[i])
        if live.sum() < 3:
            continue
        nb = pts[idx[i][live]] - pts[i]
        cov = np.cov(nb.T)
        ev, evec = np.linalg.eigh(cov)
        o = np.argsort(ev)[::-1]
        ev, evec = ev[o], evec[:, o]
        # columns of evec are eigenvectors in (row=y, col=x) space
        vec[i] = (evec[0, 0], evec[1, 0])
        l1, l2 = float(max(ev[0], 0.0)), float(max(ev[1], 0.0))
        coh[i] = (l1 - l2) / (l1 + l2 + 1e-12)
    return vec, coh


def hex_lattice(shape: tuple[int, int], spacing: float | None = None) -> dict:
    """Node raster of a hexagonal lattice, at the sparsest spacing that still *covers*.

    The ideal covering statement is ``a = sqrt(3) * R`` (every cell of the plane within ``R`` of a
    node), but nodes must land on grid cells, and rounding moves them by up to ~0.7 px, which
    breaks a lattice sitting exactly on the theoretical limit.  So the spacing is searched downward
    from the nominal value until the *measured* interior covering radius is within ``R`` plus half a
    pixel, and the measurement is reported next to the theory instead of being assumed.

    Covering is measured on the interior (one spacing in from every edge), because a lattice
    cannot cover cells outside its own extent; the edge value is reported separately.
    """
    h, w = shape
    margin = int(np.ceil(R_PX * np.sqrt(3.0))) + 2
    nominal = HEX_SPACING_PX
    ladder = ([nominal] if spacing is None else []) + ([nominal - 0.1 * i for i in range(1, 16)]
                                                       if spacing is None else [])
    if spacing is not None:
        ladder = [float(spacing)]
    chosen = None
    for cand in ladder:
        mask = _hex_mask(h, w, cand)
        far = ndi.distance_transform_edt(~mask)
        interior = far[margin:h - margin, margin:w - margin]
        if interior.size and float(interior.max()) <= R_PX + 0.5:
            chosen = (cand, mask, float(interior.max()), float(far.max()))
            break
    if chosen is None:                                   # pragma: no cover - defensive
        cand = ladder[-1]
        mask = _hex_mask(h, w, cand)
        far = ndi.distance_transform_edt(~mask)
        chosen = (cand, mask, float(far.max()), float(far.max()))
    cand, mask, interior_max, full_max = chosen
    node_pts = np.argwhere(mask).astype(np.float64)
    nn = np.inf
    if len(node_pts) > 1:
        nn = float(cKDTree(node_pts).query(node_pts, k=2)[0][:, 1].min())
    return {"mask": mask,
            "nominal_covering_spacing_px": round(nominal, 6),
            "spacing_px": round(float(cand), 6),
            "nodes": int(mask.sum()),
            "interior_max_cell_to_node_px": round(interior_max, 4),
            "max_cell_to_node_px": round(full_max, 4),
            "covers_at_radius": bool(interior_max <= R_PX + 0.5),
            "min_node_separation_px": round(nn, 4) if np.isfinite(nn) else None}


def _hex_mask(h: int, w: int, spacing: float) -> np.ndarray:
    """Rasterise a hexagonal lattice of the given node spacing onto an ``h x w`` grid."""
    mask = np.zeros((h, w), bool)
    row_step = spacing * np.sqrt(3.0) / 2.0
    j = 0
    while j * row_step <= h:
        y = j * row_step
        x = 0.5 * spacing if (j % 2) else 0.0
        while x <= w:
            ri, ci = int(round(y)), int(round(x))
            if 0 <= ri < h and 0 <= ci < w:
                mask[ri, ci] = True
            x += spacing
        j += 1
    return mask


# --------------------------------------------------------------------------- placement
def _window(shape: tuple[int, int], r: int, c: int, radius: int):
    r0, r1 = max(0, r - radius), min(shape[0], r + radius + 1)
    c0, c1 = max(0, c - radius), min(shape[1], c + radius + 1)
    yy, xx = np.mgrid[r0:r1, c0:c1]
    return yy.ravel(), xx.ravel()


def _floor_ok(taken: np.ndarray, r: int, c: int, floor_px: float) -> bool:
    """True when no already-placed dot sits closer than ``floor_px`` to ``(r, c)``."""
    rad = int(np.ceil(floor_px)) + 1
    r0, r1 = max(0, r - rad), min(taken.shape[0], r + rad + 1)
    c0, c1 = max(0, c - rad), min(taken.shape[1], c + rad + 1)
    win = taken[r0:r1, c0:c1]
    if not win.any():
        return True
    yy, xx = np.nonzero(win)
    return bool(np.hypot(yy + r0 - r, xx + c0 - c).min() >= floor_px - EPS)


def _admissible(law: str, yy: np.ndarray, xx: np.ndarray, r: int, c: int, radius: int,
                vec: np.ndarray, nodes: np.ndarray, across_tol: float,
                min_along: float) -> np.ndarray:
    """The law's own shape, evaluated on the window cells (boolean, same length as ``yy``)."""
    dy = yy - r
    dx = xx - c
    inside = np.hypot(dy, dx) <= radius + EPS
    if law in ("pdisk", "random"):
        return inside
    if law == "lattice":
        return inside & nodes[yy, xx]
    if law == "strike":
        along = dx * vec[1] + dy * vec[0]
        across = np.abs(dx * vec[0] - dy * vec[1])      # |cross product| = perpendicular offset
        return inside & (across <= across_tol + EPS) & (np.abs(along) >= min_along - EPS)
    raise ValueError(f"unknown spacing law {law!r}; expected one of {LAWS}")


def relocate(parent: np.ndarray, ctx: dict, law: str, credit_max: int = 16, *,
             window_px: int = 8, floor_px: float = R_PX, clearance_px: float = R_PX,
             across_tol_px: float = 1.0, min_along_px: float = 2.0,
             coherence_min: float = 0.30, seed: int = 0, neighbour_k: int = 10) -> tuple[np.ndarray, dict]:
    """Relocate every dot owning ``<= credit_max`` exclusive disc cells, count fixed.

    Moves are taken in redundancy order (most redundant, then most congested, first).  The
    objective is shared and purely geometric -- the largest distance to the nearest *retained* dot
    inside the window ("fill the biggest local kernel gap") -- so the only thing that differs
    between arms is the admissible *shape*.  A dot with no admissible cell in the window gets one
    widened attempt at ``2 * window_px`` (counted in ``placed_outside_window``); a dot with none
    there keeps its parent cell and is counted in ``moved_unplaced``, so a shortfall can never
    masquerade as a mass change.  The count is therefore fixed by construction, not repaired.
    """
    if law not in LAWS:
        raise ValueError(f"unknown spacing law {law!r}; expected one of {LAWS}")
    foot = np.asarray(ctx["footprint"], bool)
    cat = np.asarray(ctx["catalogue"], bool)
    dots = np.asarray(parent, bool) & foot
    if floor_px < PARENT_FLOOR_PX - EPS:
        raise ValueError("a SPACING arm may not tighten the parent's own spacing floor "
                         f"({PARENT_FLOOR_PX:.4f} px); requested {floor_px}")
    edt_cat = ndi.distance_transform_edt(~cat)
    # Brief 4.4 ("zero mass on catalogue pixels, >= 3 px off them") is applied to NEWLY emitted
    # mass only: R0 itself has 2,171 dots between 2 and 3 px, so the rule is unsatisfiable
    # jointly with the parent's geometry (IR-86-RELIEF-02, IR-86-SNAP-08).
    eligible = foot & ~cat & (edt_cat > clearance_px + EPS)

    sel, chosen_flat, sel_info = select_redundant(dots, credit_max)
    retained = dots & ~sel
    gap = ndi.distance_transform_edt(~retained).astype(np.float64)   # shared ranking field

    sel_pts = np.stack(np.unravel_index(chosen_flat, dots.shape), -1)  # (n_selected, 2)
    vec_all, coh_all = ridge_axes(dots, k=neighbour_k)
    pos_of = {int(np.int64(dots.shape[1]) * p[0] + p[1]): i for i, p in enumerate(
        np.argwhere(dots).tolist())}
    lat = hex_lattice(dots.shape)
    nodes = lat["mask"]
    rng = np.random.default_rng(int(seed))

    # ``occ`` is the set of cells that are *already* a dot as the moves proceed: every parent dot
    # that has not yet been processed still occupies its cell, so a destination can neither land on
    # a dot that is about to stay put nor break the spacing floor against one.  A source is freed
    # the moment it is processed and re-filled if the dot cannot be placed, which makes the count
    # fixed by construction rather than by a later repair.
    occ = dots.copy()
    moves: list[tuple[int, int, int, int]] = []
    unplaced = widened = fallback_isotropic = blocked_no_cell = reused_sources = 0
    for r, c in sel_pts.tolist():
        occ[r, c] = False                       # vacate the source before searching
        i = pos_of[int(np.int64(dots.shape[1]) * r + c)]
        vec, coh = vec_all[i], coh_all[i]
        used_law = law
        if law == "strike" and coh < coherence_min:
            used_law = "pdisk"                  # not a line: along-strike is undefined here
            fallback_isotropic += 1
        placed_here = False
        for radius, is_wide in ((int(window_px), False), (2 * int(window_px), True)):
            yy, xx = _window(dots.shape, r, c, radius)
            shape_ok = _admissible(used_law, yy, xx, r, c, radius, vec, nodes,
                                   across_tol_px, min_along_px)
            ok = shape_ok & eligible[yy, xx] & ~occ[yy, xx]
            if not ok.any():
                if not is_wide:
                    blocked_no_cell += 1
                continue
            choice = None
            if law == "random":
                idxs = [t for t in np.flatnonzero(ok)
                        if _floor_ok(occ, int(yy[t]), int(xx[t]), floor_px)]
                if idxs:
                    choice = int(idxs[int(rng.integers(len(idxs)))])
            else:
                score = np.where(ok, gap[yy, xx], -np.inf)
                for t in np.lexsort((xx, yy, -score)):
                    if not ok[t]:
                        continue
                    if _floor_ok(occ, int(yy[t]), int(xx[t]), floor_px):
                        choice = int(t)
                        break
            if choice is None:
                continue
            nr, nc = int(yy[choice]), int(xx[choice])
            occ[nr, nc] = True
            moves.append((r, c, nr, nc))
            if sel[nr, nc]:
                reused_sources += 1        # the cell another dot vacated earlier in the sequence
            if is_wide:
                widened += 1
            placed_here = True
            break
        if not placed_here:
            occ[r, c] = True                    # the dot keeps its parent cell; count preserved
            unplaced += 1

    out = occ
    disp = (np.hypot(np.array([m[2] - m[0] for m in moves], float),
                     np.array([m[3] - m[1] for m in moves], float)) if moves
            else np.zeros(0, float))
    dest = np.array([[m[2], m[3]] for m in moves], np.int64) if moves else np.zeros((0, 2), np.int64)
    stats = _stats(law, dots, out, sel, sel_info, len(moves), unplaced, widened,
                   fallback_isotropic, blocked_no_cell, disp, dest, edt_cat, gap, foot, cat,
                   floor_px, clearance_px, int(window_px), across_tol_px, min_along_px,
                   coherence_min, lat, reused_sources)
    return out, stats


def _stats(law, dots, out, sel, sel_info, placed, unplaced, widened, fb, blocked, disp, dest,
           edt_cat, gap, foot, cat, floor_px, clearance_px, window_px, across_tol, min_along,
           coherence_min, lat, reused=0) -> dict:
    def nn(mask):
        p = np.argwhere(mask)
        if len(p) < 2:
            return {}
        d = cKDTree(p).query(p, k=2)[0][:, 1]
        return {"nn_mean_px": round(float(d.mean()), 4), "nn_median_px": float(np.median(d)),
                "nn_min_px": round(float(d.min()), 4),
                "dots_below_2px": int((d < 2.0 - EPS).sum()),
                "dots_below_kernel_radius": int((d < R_PX - EPS).sum()),
                "fraction_below_parent_floor": round(float((d < PARENT_FLOOR_PX - EPS).mean()), 6)}

    cover_parent = disc_cover(dots)
    cover_variant = disc_cover(out)
    _cpar, spar = exclusive_credit(dots)
    _cvar, svar = exclusive_credit(out)
    eligible = foot & ~cat & (edt_cat > clearance_px + EPS)
    return {
        "axis": "SPACING", "law": law,
        "n_dots_parent": int(dots.sum()), "n_dots_variant": int(out.sum()),
        "count_fixed": bool(int(dots.sum()) == int(out.sum())),
        "moved_target": sel_info["n_selected"], "moved_placed": placed,
        "moved_unplaced": unplaced, "placed_outside_window": widened,
        "empty_window_before_widening": blocked,
        "destinations_on_vacated_source_cells": int(reused),
        "strike_fallback_isotropic": fb, "strike_coherence_min": coherence_min,
        "pct_relocated_of_parent": round(100.0 * placed / max(int(dots.sum()), 1), 4),
        "dots_changed": int((out != dots).sum()),
        "pct_changed": round(100.0 * int((out != dots).sum()) / max(int(dots.sum()), 1), 4),
        "mean_displacement_px": round(float(disp.mean()), 4) if placed else 0.0,
        "median_displacement_px": round(float(np.median(disp)), 4) if placed else 0.0,
        "max_displacement_px": round(float(disp.max()), 4) if placed else 0.0,
        "window_px": window_px, "floor_px": floor_px, "clearance_px": clearance_px,
        "across_trace_tol_px": across_tol, "min_along_trace_px": min_along,
        "parent_nn": nn(dots), "variant_nn": nn(out),
        "exclusive_parent": spar, "exclusive_variant": svar,
        "union_cover_parent_cells": int(cover_parent.sum()),
        "union_cover_variant_cells": int(cover_variant.sum()),
        "union_cover_gain_cells": int(cover_variant.sum() - cover_parent.sum()),
        "union_cover_gain_offcatalogue_px": int(
            (cover_variant & ~cat & foot).sum() - (cover_parent & ~cat & foot).sum()),
        "eligible_covered_parent": int(cover_parent[eligible].sum()),
        "eligible_covered_variant": int(cover_variant[eligible].sum()),
        "destination_gap_px_mean": round(float(gap[dest[:, 0], dest[:, 1]].mean()), 4) if placed else None,
        "cat_edt_min_parent": round(float(edt_cat[dots].min()), 4),
        "cat_edt_min_variant": round(float(edt_cat[out].min()), 4),
        "cat_edt_mean_parent": round(float(edt_cat[dots].mean()), 4),
        "cat_edt_mean_variant": round(float(edt_cat[out].mean()), 4),
        "dots_within_300m_of_catalogue_parent": int((edt_cat[dots] <= 3.0 + EPS).sum()),
        "dots_within_300m_of_catalogue_variant": int((edt_cat[out] <= 3.0 + EPS).sum()),
        "lattice": {k: v for k, v in lat.items() if k != "mask"},
        "selection": sel_info,
        "placement_rule": {
            "pdisk": "largest gap to the nearest retained dot inside an 8 px window, any "
                     "direction (isotropic hard-core, blue-noise / Poisson-disk form)",
            "lattice": "same objective and window, restricted to the nodes of a hexagonal "
                       f"lattice with spacing {HEX_SPACING_PX:.4f} px = sqrt(3)*R, the thinnest "
                       "covering of the plane by radius-R discs",
            "strike": "same objective and window, restricted to cells within 1 px across the "
                      "local dot ridge and >= 2 px along it: extend the trace instead of "
                      "leaving it; falls back to isotropic where the neighbourhood is not "
                      "line-like (coherence < 0.30)",
            "random": "uniform draw from the eligible cells of the window (null control: the "
                      "cost of moving at all, with no spacing law)",
        }[law],
        "eligibility": (f"eligible = footprint & ~catalogue & distance-to-catalogue > "
                        f"{clearance_px:g} px, applied to newly emitted mass only; inherited dots "
                        "keep the parent's own >2 px geometry (brief 4.4 vs R0, IR-86-RELIEF-02)"),
    }


def parent_diff(parent: np.ndarray, variant: np.ndarray, footprint: np.ndarray) -> dict:
    """Parent-difference statistics every ledger row must carry (brief 6)."""
    p = np.asarray(parent, bool) & footprint
    v = np.asarray(variant, bool) & footprint
    both = int((p & v).sum())
    union = int((p | v).sum())
    return {"parent_dots": int(p.sum()), "variant_dots": int(v.sum()),
            "shared_dots": both, "dropped": int((p & ~v).sum()), "added": int((v & ~p).sum()),
            "dots_changed": int((p != v).sum()),
            "pct_changed_of_parent": round(100.0 * int((p != v).sum()) / max(int(p.sum()), 1), 4),
            "pct_relocated": round(100.0 * int((p & ~v).sum()) / max(int(p.sum()), 1), 4),
            "jaccard": round(both / union, 6) if union else None,
            "count_delta": int(v.sum() - p.sum())}
