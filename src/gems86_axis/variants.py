"""The three AXIS builders: PRUNE, CONCENTRATION, SNAP.

Every builder takes the parent dot mask and returns ``(new_mask, stats)`` where ``stats``
carries the parent-diff numbers the ledger and the run card need.  Each one is a single
declared axis:

PRUNE           remove dots whose catalogue distance is <= ``radius_px``; refill to hold
                the count from the parent's own support surface, largest gaps first.
CONCENTRATION   move a fixed fraction of dots out of the lowest-prior 1 km blocks into the
                highest-prior ones, count and exclusions unchanged.
SNAP            move each dot at most ``max_shift_px`` to the strongest edge/scarp response
                in its window, count and exclusions unchanged.

Nothing here reads a label raster, and no builder is allowed to place a dot on a catalogue
pixel or inside the parent's catalogue clearance floor.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

BLOCK_PX = 10  # 1 km at the competition's 100 m grid


def _cat_edt(catalogue: np.ndarray) -> np.ndarray:
    """Euclidean distance, in pixels, from every cell to the nearest catalogue pixel."""
    return ndimage.distance_transform_edt(~catalogue).astype(np.float32)


def _dot_edt(dots: np.ndarray) -> np.ndarray:
    return ndimage.distance_transform_edt(~dots).astype(np.float32)


def _eligible(footprint, catalogue, edt_cat, clearance_px) -> np.ndarray:
    """Parent exclusions: inside the footprint, off-catalogue, outside the clearance floor."""
    return footprint & ~catalogue & (edt_cat > clearance_px)


def _ranked_candidates(eligible: np.ndarray, score: np.ndarray, occupied: np.ndarray,
                       min_spacing_px: float) -> list[tuple[int, int]]:
    """Eligible, unoccupied pixels that respect ``min_spacing_px`` from ``occupied``.

    Returned in descending ``score`` order, ties broken by (row, col) so the result is
    reproducible with no RNG.
    """
    dist_to_occupied = _dot_edt(occupied) if occupied.any() else np.full(eligible.shape, np.inf, np.float32)
    cand = eligible & ~occupied & (dist_to_occupied >= min_spacing_px)
    if not cand.any():
        return []
    rows, cols = np.nonzero(cand)
    key = score[rows, cols]
    order = np.lexsort((cols, rows, -key))
    return [(int(rows[i]), int(cols[i])) for i in order]


def prune(parent: np.ndarray, ctx: dict, radius_px: float, support: np.ndarray,
          clearance_px: float, min_spacing_px: float) -> tuple[np.ndarray, dict]:
    """PRUNE axis: widen the catalogue collar from the parent's rule to ``radius_px``."""
    foot, cat = ctx["footprint"], ctx["catalogue"]
    dots = parent & foot
    edt = _cat_edt(cat)
    removed = dots & (edt <= radius_px)
    n_removed = int(removed.sum())
    kept = dots & ~removed

    eligible = _eligible(foot, cat, edt, max(clearance_px, radius_px))
    pool = _ranked_candidates(eligible & support, _dot_edt(kept), kept, 0.0)
    # Two passes.  Pass 1 keeps the parent's own d=2.8 thinning.  The parent's support
    # mask is saturated at that spacing (only 611 free cells region-wide), so pass 2
    # relaxes to the parent's catalogue-clearance floor only as far as holding the count
    # requires, and the relaxation is reported as a spacing side-effect of this axis.
    taken = kept.copy()
    refill: list[tuple[int, int]] = []
    n_at_parent_spacing = 0
    for spacing in (min_spacing_px, clearance_px + 1e-9):
        for rc in pool:
            if len(refill) >= n_removed:
                break
            r, c = rc
            if taken[r, c]:
                continue
            r0, r1 = max(0, r - 3), min(taken.shape[0], r + 4)
            c0, c1 = max(0, c - 3), min(taken.shape[1], c + 4)
            win = taken[r0:r1, c0:c1]
            if win.any():
                rr, cc = np.nonzero(win)
                if np.hypot(rr + r0 - r, cc + c0 - c).min() < spacing:
                    continue
            refill.append(rc)
            taken[r, c] = True
            if spacing == min_spacing_px:
                n_at_parent_spacing += 1
        if len(refill) >= n_removed:
            break
    out = taken
    changed = int((out != dots).sum())
    stats = {
        "axis": "PRUNE", "value": f"collar{radius_px:g}px",
        "radius_px": radius_px,
        "removed_dots": n_removed, "refilled_dots": len(refill),
        "refilled_at_parent_spacing": n_at_parent_spacing,
        "refilled_at_relaxed_spacing": len(refill) - n_at_parent_spacing,
        "refill_shortfall": n_removed - len(refill),
        "n_dots_parent": int(dots.sum()), "n_dots_variant": int(out.sum()),
        "dots_changed": changed, "pct_changed": round(100.0 * changed / max(int(dots.sum()), 1), 3),
        "refill_pool": ("parent H19-5 support mask, eligible cells ranked by distance to the "
                        "nearest retained dot (largest kernel gaps first); pass 1 keeps the "
                        "parent's 2.83 px thinning, pass 2 relaxes to the parent's 2 px "
                        "clearance floor only as far as holding the count requires"),
        "cat_edt_mean_parent": round(float(edt[dots].mean()), 4),
        "cat_edt_mean_variant": round(float(edt[out].mean()), 4),
        "min_cat_edt_variant": round(float(edt[out].min()), 4),
    }
    return out, stats


def block_prior(ctx: dict, bands: dict, catalogue: np.ndarray, block_px: int = BLOCK_PX) -> dict:
    """Km-block prior on where *unmapped* fault pixels are most likely.

    Two terms, equal weight, both z-scored over occupied-area blocks:
      * fault-interaction density - catalogue fault pixels in the block and its 8 neighbours
        (the Faulds step-over/intersection/termination result used only as a prior, per
        brief section 2);
      * magnetic edge response - mean Sobel-gradient magnitude of upward-continued TMI.
    """
    foot = ctx["footprint"]
    h, w = foot.shape
    nb, mb = h // block_px, w // block_px
    catf = (catalogue & foot).astype(np.float32)
    catf = ndimage.uniform_filter(catf, size=3 * block_px, mode="constant")
    tmi_grad = bands["tmi_grad"]
    tmi_grad = np.nan_to_num(tmi_grad, nan=0.0)

    def blk(a: np.ndarray) -> np.ndarray:
        return a[: nb * block_px, : mb * block_px].reshape(nb, block_px, mb, block_px).mean(axis=(1, 3))

    fpb = blk(foot.astype(np.float32))
    from .bands import zscore
    prior = zscore(blk(catf)) + zscore(blk(tmi_grad))
    prior[fpb <= 0] = -np.inf
    return {"prior": prior.astype(np.float32), "footprint_blocks": fpb,
            "cat_block": blk(catf), "tmi_block": blk(tmi_grad),
            "block_px": block_px, "shape": (nb, mb)}


def block_to_pixels(block_field: np.ndarray, shape: tuple[int, int],
                    block_px: int = BLOCK_PX) -> np.ndarray:
    """Expand a per-block field to pixel resolution; cells past the last block get -inf."""
    h, w = shape
    nb, mb = block_field.shape
    out = np.full((h, w), -np.inf, dtype=np.float64)
    rows = min(nb * block_px, h)
    cols = min(mb * block_px, w)
    expanded = np.repeat(np.repeat(np.asarray(block_field, dtype=np.float64), block_px, axis=0),
                         block_px, axis=1)
    out[:rows, :cols] = expanded[:rows, :cols]
    return out


def block_density(mask: np.ndarray, footprint: np.ndarray, block_px: int = BLOCK_PX) -> dict:
    """Dot density per km block plus the CV the brief asks for (0.51-0.59 on the best files)."""
    h, w = mask.shape
    nb, mb = h // block_px, w // block_px
    m = (mask & footprint)[: nb * block_px, : mb * block_px].astype(np.float64)
    f = footprint[: nb * block_px, : mb * block_px].astype(np.float64)
    d = m.reshape(nb, block_px, mb, block_px).sum(axis=(1, 3))
    fb = f.reshape(nb, block_px, mb, block_px).sum(axis=(1, 3))
    dens = d / np.maximum(fb, 1.0)
    occ = d > 0
    return {"occupied_blocks": int(occ.sum()), "total_blocks": int(d.size),
            "density_cv_occupied": round(float(dens[occ].std() / dens[occ].mean()), 4),
            "count_cv_occupied": round(float(d[occ].std() / d[occ].mean()), 4),
            "mean_dots_per_occupied_block": round(float(d[occ].mean()), 4),
            "counts": d}


def concentration(parent: np.ndarray, ctx: dict, bands: dict, prior: np.ndarray,
                  move_fraction: float, clearance_px: float, min_spacing_px: float,
                  block_px: int = BLOCK_PX,
                  dest_block_frac: float = 0.20) -> tuple[np.ndarray, dict]:
    """CONCENTRATION axis: relocate ``move_fraction`` of dots from low- to high-prior blocks.

    ``dest_block_frac`` is the share of footprint-bearing blocks that count as
    "highest-prior" destinations.  Placement inside a destination block is purely
    geometric (largest remaining kernel gap first) so this axis cannot smuggle in the
    pixel-scale edge snapping that SNAP measures.
    """
    foot, cat = ctx["footprint"], ctx["catalogue"]
    dots = parent & foot
    edt = _cat_edt(cat)
    n_move = int(round(move_fraction * int(dots.sum())))

    h, w = foot.shape
    nb, mb = prior.shape
    prior_px = block_to_pixels(prior, (h, w), block_px)

    dot_rows, dot_cols = np.nonzero(dots)
    dot_prior = prior_px[dot_rows, dot_cols]

    order = np.argsort(dot_prior, kind="stable")  # ascending prior -> lowest first
    drop_idx = order[:n_move]
    drop = np.zeros_like(dots)
    drop[dot_rows[drop_idx], dot_cols[drop_idx]] = True
    kept = dots & ~drop

    # Destinations.  This axis moves mass between km blocks and must not also move it onto
    # geophysical edges (that is SNAP), so the ranking is purely geometric: highest-prior
    # block first, and inside a block the largest remaining kernel gap first - the same
    # gap rule PRUNE's refill uses.  No pixel-scale response term enters here.
    eligible = _eligible(foot, cat, edt, clearance_px)
    # destination blocks = the highest-prior fifth of the blocks that have any footprint
    finite = np.isfinite(prior)
    order = np.argsort(np.where(finite, prior, -np.inf).ravel(), kind="stable")[::-1]
    n_dest = max(1, int(round(dest_block_frac * int(finite.sum()))))
    dest_blocks = np.zeros(prior.shape, dtype=bool)
    dest_blocks.ravel()[order[:n_dest]] = True
    dest_px = block_to_pixels(dest_blocks.astype(np.float64), (h, w), block_px) > 0.5

    score = prior_px + 0.1 * _dot_edt(kept).astype(np.float64)
    score[~np.isfinite(score)] = -np.inf
    score[~(eligible & dest_px)] = -np.inf
    cand = _ranked_candidates(eligible & dest_px, score, kept, clearance_px + 1e-9)

    taken = kept.copy()
    placed: list[tuple[int, int]] = []
    half = int(np.ceil(min_spacing_px))
    n_at_parent_spacing = 0
    for spacing in (min_spacing_px, clearance_px + 1e-9):
        for rc in cand:
            if len(placed) >= n_move:
                break
            r, c = rc
            if taken[r, c]:
                continue
            r0, r1 = max(0, r - half), min(h, r + half + 1)
            c0, c1 = max(0, c - half), min(w, c + half + 1)
            win = taken[r0:r1, c0:c1]
            if win.any():
                rr, cc = np.nonzero(win)
                if np.hypot(rr + r0 - r, cc + c0 - c).min() < spacing:
                    continue
            placed.append(rc)
            taken[r, c] = True
            if spacing == min_spacing_px:
                n_at_parent_spacing += 1
        if len(placed) >= n_move:
            break
    out = taken
    changed = int((out != dots).sum())
    stats = {
        "axis": "CONCENTRATION", "value": f"b{block_px // 10}km-move{int(round(100*move_fraction))}",
        "block_size": f"{block_px * 100} m ({block_px}x{block_px} px)",
        "move_fraction_target": move_fraction, "moved_target": n_move,
        "moved_placed": len(placed), "moved_shortfall": n_move - len(placed),
        "placed_at_parent_spacing": n_at_parent_spacing,
        "placed_at_relaxed_spacing": len(placed) - n_at_parent_spacing,
        "dest_block_frac": dest_block_frac, "dest_blocks": int(n_dest),
        "placement_rule": "geometric only: highest-prior destination block, then the largest "
                          "remaining kernel gap; no pixel-scale response term",
        "source_rule": "lowest-prior km blocks first, all dots in a block before the next",
        "n_dots_parent": int(dots.sum()), "n_dots_variant": int(out.sum()),
        "dots_changed": changed, "pct_changed": round(100.0 * changed / max(int(dots.sum()), 1), 3),
        "prior_terms": ["catalogue fault-interaction density (3x3 km mean, z-scored)",
                        "mean Sobel gradient of TMI upward-continued to 150 m (z-scored)"],
        "block_density_parent": {k: v for k, v in block_density(dots, foot, block_px).items() if k != "counts"},
        "block_density_variant": {k: v for k, v in block_density(out, foot, block_px).items() if k != "counts"},
        "min_cat_edt_variant": round(float(edt[out].min()), 4),
    }
    return out, stats


def snap(parent: np.ndarray, ctx: dict, response: np.ndarray, max_shift_px: int,
         clearance_px: float) -> tuple[np.ndarray, dict]:
    """SNAP axis: relocate each dot to the strongest response within ``max_shift_px``."""
    foot, cat = ctx["footprint"], ctx["catalogue"]
    dots = parent & foot
    edt = _cat_edt(cat)
    h, w = dots.shape
    resp = np.nan_to_num(response, nan=-np.inf).astype(np.float64)
    # a true "<= 2 px" move is a Euclidean disk, so the 2.83 px corners are excluded
    offs = [(dy, dx) for dy in range(-max_shift_px, max_shift_px + 1)
            for dx in range(-max_shift_px, max_shift_px + 1)
            if float(np.hypot(dy, dx)) <= max_shift_px + 1e-9]

    rows, cols = np.nonzero(dots)
    disp = []
    blocked_cat = 0
    blocked_occupied = 0
    out = np.zeros_like(dots)
    order = np.lexsort((cols, rows, -resp[rows, cols]))
    for i in order:
        r, c = int(rows[i]), int(cols[i])
        best_rc = (r, c)
        best_val = -np.inf
        ok = foot & ~cat & (edt > clearance_px)
        for dy, dx in offs:
            tr, tc = r + dy, c + dx
            if not (0 <= tr < h and 0 <= tc < w) or not ok[tr, tc]:
                continue
            v = resp[tr, tc]
            if v > best_val:
                best_val, best_rc = v, (tr, tc)
        tr, tc = best_rc
        if out[tr, tc]:
            blocked_occupied += 1
            tr, tc = r, c
        if cat[tr, tc] or edt[tr, tc] <= clearance_px:
            blocked_cat += 1
            tr, tc = r, c
        out[tr, tc] = True
        disp.append(float(np.hypot(tr - r, tc - c)))
    disp = np.asarray(disp)
    changed = int((out != dots).sum())
    stats = {
        "axis": "SNAP", "value": f"{max_shift_px}px",
        "max_shift_px": max_shift_px,
        "mean_displacement_px": round(float(disp.mean()), 4),
        "median_displacement_px": round(float(np.median(disp)), 4),
        "max_displacement_px": round(float(disp.max()), 4),
        "dots_moved": int((disp > 0).sum()),
        "dots_blocked_by_occupancy": blocked_occupied,
        "dots_blocked_by_clearance": blocked_cat,
        "n_dots_parent": int(dots.sum()), "n_dots_variant": int(out.sum()),
        "dots_changed": changed, "pct_changed": round(100.0 * changed / max(int(dots.sum()), 1), 3),
        "cat_edt_mean_parent": round(float(edt[dots].mean()), 4),
        "cat_edt_mean_variant": round(float(edt[out].mean()), 4),
        "min_cat_edt_variant": round(float(edt[out].min()), 4),
        "response": "Sobel gradient magnitude of TMI upward-continued to 150 m + z-scored DEM "
                    "scarp composite (|profile curvature|, max slope, hillshade lineament)",
    }
    return out, stats


def parent_diff(parent: np.ndarray, variant: np.ndarray, footprint: np.ndarray) -> dict:
    """The parent-diff statistics every ledger row must carry."""
    p, v = parent & footprint, variant & footprint
    both = int((p & v).sum())
    only_p = int((p & ~v).sum())
    only_v = int((v & ~p).sum())
    union = int((p | v).sum())
    return {"parent_dots": int(p.sum()), "variant_dots": int(v.sum()),
            "shared_dots": both, "dropped": only_p, "added": only_v,
            "dots_changed": only_p + only_v,
            "pct_changed_of_parent": round(100.0 * (only_p + only_v) / max(int(p.sum()), 1), 3),
            "jaccard": round(both / union, 6) if union else None,
            "count_delta": int(v.sum() - p.sum())}
