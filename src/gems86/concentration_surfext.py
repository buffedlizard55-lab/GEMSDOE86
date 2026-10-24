"""Surface-extension CONCENTRATION arm on the pinned R0 parent (session 2026-10-23).

Why this module exists
----------------------
Every merged ``CONCENTRATION`` arm relocates dots *within* the occupied evidence
surface.  A pre-build capacity audit of R0 (this session) shows that surface is
full: the parent is ``H19-5`` dotted at 2.8 px, all 37,654 dots sit on
``H19-5``, and only **90** cells of ``H19-5`` remain legal under the parent's own
``>= sqrt(8) = 2.8284 px`` spacing floor and the brief's ``> 3.0 px`` catalogue
clearance.  That is why every within-surface rearrangement reads ``|dDTI| <=
0.004``: there is nowhere to put the mass.

The parent lineage's blind spot is measurable.  The pinned ancestor evidence
surfaces are three scored submissions of nearly equal owner-reported quality
(``H19-5`` 0.1922, ``H19-4`` 0.1894, ``H16-1`` 0.1855, all CLAIM).  Their union
covers 157,085 footprint pixels; ``H19-4 | H16-1`` minus ``H19-5`` is 35,954 px
that the parent **never uses** (0 of its dots lie there), and 8,671 of those
cells are legal under both constraints above (6,456 dots placeable greedily).

The arms built here therefore extend the *same* dotted-lineament construction
onto the unoccupied part of the ancestor union, moving mass out of the dots
whose kernel credit is most redundant under the metric's max operator.

Metric mechanism (why the source rule matters)
----------------------------------------------
With binary unit-mass dots the official DTI is

    DTI = T / (alpha*T + alpha*(n - M) + beta*|G|),   alpha = 0.2, beta = 0.8

where ``T = sum_g max_x p(x) k(d(x,g))`` **saturates at one per truth cell** and
``M = sum_x max_g k(d(x,g))`` saturates per dot.  A dot whose truth
neighbourhood is already covered by a neighbour adds ``dT = 0`` but still costs
``alpha*(1 - k)`` in the denominator, so redundant mass is a strict drag.  The
source rule pops the lowest-unique-kernel-credit dot from the densest occupied
1 km block, exactly as the merged ``b5km-cvband-down4`` arm does
(:func:`gems86.concentration_5km.relocate_cvband_down`); this module only
changes where the mass goes.

Determinism
-----------
The treatment arms are RNG-free.  The matched null control uses one fixed seed
and is never promoted to a slot candidate.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from gems86 import mass_econ

KM_BLOCK_PX = 10
MIN_CLEARANCE_PX = 3.0
MIN_SPACING_PX = math.sqrt(8.0) - 1e-6
MAX_DOTS_PER_DEST_BLOCK = 4


def _min_pair_distance(mask: np.ndarray) -> float:
    """Smallest Euclidean distance between any two positive cells (brute force, small n)."""
    from scipy.spatial import cKDTree

    ys, xs = np.nonzero(mask)
    if len(ys) < 2:
        return float("inf")
    return float(cKDTree(np.column_stack([ys, xs])).query(np.column_stack([ys, xs]), k=2)[0][:, 1].min())


def redundant_source_order(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    *,
    km_block_px: int = KM_BLOCK_PX,
    unique_credit_dots: np.ndarray | None = None,
    n_max: int | None = None,
) -> np.ndarray:
    """Full dose-independent removal order used by the merged cvband arm.

    Repeats: among 1 km blocks holding ``>= 3`` dots, take the densest, and pop
    its lowest unique-kernel-credit dot (ties: higher row, then higher column,
    matching the merged arm).  Because each step depends only on the state the
    previous steps produced, the sequence for ``n_move = k`` is the exact prefix
    of the sequence for any larger ``k`` -- the nesting invariant the ledger
    requires of a dose ladder.
    """
    parent = np.asarray(parent_dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    h, w = parent.shape
    nb, mb = h // km_block_px, w // km_block_px
    sub_p = parent[: nb * km_block_px, : mb * km_block_px].astype(np.float64)
    sub_f = np.asarray(footprint, dtype=bool)[: nb * km_block_px, : mb * km_block_px].astype(np.float64)
    c_cur = sub_p.reshape(nb, km_block_px, mb, km_block_px).sum(axis=(1, 3)).copy()
    fb = sub_f.reshape(nb, km_block_px, mb, km_block_px).sum(axis=(1, 3))
    d_cur = c_cur / np.maximum(fb, 1.0)

    ys, xs = np.nonzero(parent)
    if unique_credit_dots is None:
        u_cred, _ = mass_econ.marginal_credit(parent)
    else:
        u_cred = np.asarray(unique_credit_dots, dtype=np.float64)

    blk_dots: dict[tuple[int, int], list[tuple[float, int, int]]] = {}
    for idx in range(len(ys)):
        r, c = int(ys[idx]), int(xs[idx])
        bi, bj = r // km_block_px, c // km_block_px
        if bi < nb and bj < mb:
            blk_dots.setdefault((bi, bj), []).append((float(u_cred[idx]), r, c))
    for key in blk_dots:
        blk_dots[key].sort(key=lambda item: (-item[0], -item[1], -item[2]))

    limit = int(n_max) if n_max is not None else int(parent.sum())
    out: list[tuple[int, int]] = []
    while len(out) < limit:
        elig = c_cur >= 3
        if not np.any(elig):
            break
        bi, bj = divmod(int(np.argmax(np.where(elig, d_cur, -1.0))), mb)
        _, r, c = blk_dots[(bi, bj)].pop()
        c_cur[bi, bj] -= 1.0
        d_cur[bi, bj] = c_cur[bi, bj] / max(fb[bi, bj], 1.0)
        out.append((r, c))
    return np.asarray(out, dtype=np.int32)


def _placement_scan(
    parent: np.ndarray,
    dest_mask: np.ndarray,
    edt_cat: np.ndarray,
    *,
    n_move: int,
    order_seed: int | None = None,
    km_block_px: int = KM_BLOCK_PX,
    min_clearance_px: float = MIN_CLEARANCE_PX,
    min_spacing_px: float = MIN_SPACING_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Greedy placement of ``n_move`` dots inside ``dest_mask``.

    Deterministic order: sparsest occupied 1 km block first, then the largest
    distance to the nearest retained dot, then row/column.  ``order_seed``
    switches to a uniform random order (the matched null control).
    """
    h, w = parent.shape
    nb, mb = h // km_block_px, w // km_block_px
    counts = parent[: nb * km_block_px, : mb * km_block_px].astype(np.float64).reshape(
        nb, km_block_px, mb, km_block_px
    ).sum(axis=(1, 3))
    block_count_px = np.repeat(np.repeat(counts, km_block_px, axis=0), km_block_px, axis=1)

    edt_parent = ndi.distance_transform_edt(~parent)
    cand = np.asarray(dest_mask, dtype=bool) & ~parent & (edt_cat > float(min_clearance_px)) & (
        edt_parent >= float(min_spacing_px)
    )
    c_ys, c_xs = np.nonzero(cand)
    if len(c_ys) == 0:
        raise ValueError("surface-extension: no legal destination cells")
    c_cnt = block_count_px[c_ys, c_xs]
    c_gap = edt_parent[c_ys, c_xs]
    if order_seed is None:
        order = np.lexsort((c_xs, c_ys, -np.round(c_gap, 4), c_cnt))
    else:
        order = np.random.default_rng(int(order_seed)).permutation(len(c_ys))

    occ = parent.copy()
    added: list[tuple[int, int]] = []
    block_now = counts.copy()
    half = int(math.ceil(float(min_spacing_px)))
    for k in order.tolist():
        if len(added) >= int(n_move):
            break
        r, c = int(c_ys[k]), int(c_xs[k])
        bi, bj = r // km_block_px, c // km_block_px
        if bi < nb and bj < mb and block_now[bi, bj] >= MAX_DOTS_PER_DEST_BLOCK:
            continue
        r0, r1 = max(0, r - half), min(h, r + half + 1)
        c0, c1 = max(0, c - half), min(w, c + half + 1)
        win = occ[r0:r1, c0:c1]
        if win.any():
            rr, cc = np.nonzero(win)
            if float(np.hypot(rr + r0 - r, cc + c0 - c).min()) < float(min_spacing_px):
                continue
        occ[r, c] = True
        if bi < nb and bj < mb:
            block_now[bi, bj] += 1.0
        added.append((r, c))
    if len(added) < int(n_move):
        raise ValueError(
            f"surface-extension destination capacity {len(added)} < n_move={n_move}"
        )
    return np.asarray(added, dtype=np.int32), dict(
        n_candidate_cells=int(len(c_ys)),
        n_placed=int(len(added)),
        order="deterministic_sparse_block_gap" if order_seed is None else f"uniform_random_seed{int(order_seed)}",
    )


def relocate_surface_extension(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    dest_surface: np.ndarray,
    *,
    n_move: int,
    km_block_px: int = KM_BLOCK_PX,
    min_clearance_px: float = MIN_CLEARANCE_PX,
    min_spacing_px: float = MIN_SPACING_PX,
    unique_credit_dots: np.ndarray | None = None,
    order_seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Move ``n_move`` redundant dots onto ``dest_surface``; count fixed."""
    parent = np.asarray(parent_dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    src_all = redundant_source_order(
        parent, footprint, km_block_px=km_block_px,
        unique_credit_dots=unique_credit_dots, n_max=int(n_move),
    )
    if len(src_all) < int(n_move):
        raise ValueError(f"only {len(src_all)} redundant-source dots available for n_move={n_move}")
    src_rc = src_all[: int(n_move)]

    sim = parent.copy()
    sim[src_rc[:, 0], src_rc[:, 1]] = False
    if np.any(sim & np.asarray(dest_surface, bool)):
        raise ValueError("destination surface still holds a retained dot; destinations are not free")
    dst_rc, place = _placement_scan(
        sim, np.asarray(dest_surface, dtype=bool), edt_cat,
        n_move=int(n_move), order_seed=order_seed, km_block_px=km_block_px,
        min_clearance_px=min_clearance_px, min_spacing_px=min_spacing_px,
    )
    out = sim.copy()
    out[dst_rc[:, 0], dst_rc[:, 1]] = True
    if int(out.sum()) != int(parent.sum()):
        raise ValueError("surface-extension changed the dot count")
    stats = relocation_stats(parent, out, footprint, edt_cat, dest_surface,
                            src_rc=src_rc, dst_rc=dst_rc)
    stats["placement"] = place
    return out, src_rc, dst_rc, stats


def relocation_stats(
    parent: np.ndarray,
    child: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    dest_surface: np.ndarray,
    *,
    src_rc: np.ndarray,
    dst_rc: np.ndarray,
) -> dict[str, Any]:
    """Parent-diff statistics required by brief section 6."""
    p = np.asarray(parent, dtype=bool)
    c = np.asarray(child, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    added = c & ~p
    removed = p & ~c
    n_p, n_c = int(p.sum()), int(c.sum())
    n_add, n_rem = int(added.sum()), int(removed.sum())
    disp = np.hypot(dst_rc[:, 0] - src_rc[:, 0], dst_rc[:, 1] - src_rc[:, 1]) if len(src_rc) else np.zeros(0)
    return dict(
        n_parent=n_p,
        n_dots=n_c,
        count_fixed=(n_c == n_p),
        n_removed=n_rem,
        n_added=n_add,
        n_symmetric_diff=n_rem + n_add,
        pct_moved_of_parent=round(100.0 * n_rem / max(n_p, 1), 4),
        pct_changed=round(100.0 * (n_rem + n_add) / max(n_p, 1), 4),
        min_added_cat_clearance_px=(round(float(edt_cat[added].min()), 4) if n_add else None),
        median_added_cat_clearance_px=(round(float(np.median(edt_cat[added])), 4) if n_add else None),
        added_on_destination_surface_fraction=(
            round(float((added & np.asarray(dest_surface, bool)).sum()) / n_add, 6) if n_add else 1.0
        ),
        added_inside_footprint_fraction=round(float((added & foot).sum()) / max(n_add, 1), 6),
        min_pair_distance_parent_px=round(_min_pair_distance(p), 4),
        min_pair_distance_variant_px=round(_min_pair_distance(c), 4),
        displacement_px=dict(
            mean=round(float(disp.mean()), 2) if disp.size else 0.0,
            median=round(float(np.median(disp)), 2) if disp.size else 0.0,
        ),
    )
