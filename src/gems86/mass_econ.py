"""MASS axis, kernel-budget session: rank mass by the metric's own economics, not by geography.

Why this module exists
----------------------
Brief v2 §5 defines MASS as "drop the lowest-ranked 10 % / add the next-ranked 10 %, by the
parent's own ranking".  That was built in an earlier session and *both* arms lost
(``massminus10`` −0.003, ``massplus10`` −0.006, MODEL).  The post-mortem (IR-86-MASS-01) is that
the recorded ranking is the FIFO-BFS *traversal* of the thinning recipe: the dropped 10 % was
100 % southern-half dots and the added 10 % was 98.6 % cells already inside a neighbour's kernel
disc.  A traversal ranks geography; it cannot rank mass.

This module supplies the ranking the brief actually asks for in §2 ("rank dots by exact marginal
gain from the metric code, not the shortcut"):

``marginal_credit``
    For a binary dot field and the official max-kernel,
    ``T = sum_g max_x k(d(x,g))``.  Dot ``x``'s unique credit at cell ``g`` is
    ``max(0, k(d(x,g)) - max_{y != x} k(d(y,g)))`` and ``u_x = sum_g (...)`` is *exactly* the
    amount ``T`` would fall if ``x`` were removed and every cell of its disc were truth.  It needs
    no label, no band and no surrogate: it is a property of the parent's own geometry.

    Note the marginals are **not** a partition of ``T``: the max operator makes them sum to
    ``sum_g (best - second)``, which is smaller than ``sum_g best`` whenever two dots share a cell.
    That is the point -- the shortfall *is* the credit the max operator has already written off --
    so ``u_x`` is a removal price and never a share of the numerator.

``exact_terms``
    The metric's own three quantities ``T``, ``M`` and ``DTI`` for any binary field against any
    truth raster, used only as the report-only MODEL instrument (SGMC inventory, off-catalogue).

``add_extension`` / ``add_random``
    The mirror experiment.  New mass is only useful if it is *not* redundant (a dot inside a
    neighbour's disc adds little to ``T`` while paying its full ``1 - k`` false-positive charge),
    so both arms admit only cells at least one kernel radius (3 px) from every existing dot, and
    differ solely in how they are chosen: along the local trace (``extend``) or uniformly at
    random inside the same window (``random`` = null control).

``mass_bar``
    The two-sided test from ``vendor/gems57/metric.py`` written as the two thresholds this axis
    turns on: a dot pays iff ``dT > alpha * DTI * (dT + 1 - k)``, so at ``DTI = 0.2778`` any
    non-redundant dot within 2.83 px of truth pays, and a *removal* pays only if the removed
    dot's unique truth credit is below ``alpha * DTI / (1 - alpha * DTI)`` times its own
    false-positive charge -- ``0.0589 * f`` at the incumbent's claimed score.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from gems86 import spacing as SP

#: Official kernel radius (300 m on the 100 m grid).
R_PX = SP.R_PX
#: alpha and beta of the official DTI (vendor/gems57/metric.py).
ALPHA = 0.2
BETA = 0.8
EPS = 1e-9

ARMS = ("minus10pct-marginal", "plus10pct-extend", "plus10pct-extend-rand")


# ------------------------------------------------------------------ numerator decomposition
def _kernel_offsets(radius: float = R_PX) -> tuple[np.ndarray, np.ndarray]:
    """Integer offsets with non-zero triangular weight and their kernel values (29 for R = 3)."""
    r = int(np.floor(radius + EPS))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.hypot(dy, dx)
    keep = d <= radius + EPS            # the dot's own cell counts: k(0) = 1
    return np.stack([dy[keep], dx[keep]], axis=1).astype(np.int64), np.maximum(1.0 - d[keep] / radius, 0.0)


def marginal_credit(dots: np.ndarray, radius: float = R_PX) -> tuple[np.ndarray, dict]:
    """Per-dot unique kernel credit ``u_x`` (point order = ``dots.nonzero()``), plus stats.

    Exact attribution of ``T``: at every grid cell the best dot gets its full kernel value, the
    second-best dot gets ``value - best``, and every other dot gets nothing.  Summing per dot
    therefore reproduces ``sum_cells max_x k`` exactly, which is the invariant the unit test
    checks.  A dot whose disc is shared with close neighbours has a small ``u``; an isolated dot
    has ``u = 9.3803`` (the weight sum of a 29-cell radius-3 disc).
    """
    dots = np.asarray(dots, bool)
    if not dots.any():
        raise ValueError("empty dot field")
    rows, cols = dots.nonzero()
    n = rows.size
    h, w = dots.shape
    offsets, values = _kernel_offsets(radius)
    idx = np.arange(n, dtype=np.int32)
    best = np.zeros((h, w), np.float32)
    second = np.zeros((h, w), np.float32)
    argbest = np.full((h, w), -1, dtype=np.int32)
    for (dy, dx), v in zip(offsets, values):
        tr, tc = rows + dy, cols + dx
        ok = (tr >= 0) & (tr < h) & (tc >= 0) & (tc < w)
        tr, tc, i2 = tr[ok], tc[ok], idx[ok]
        if tr.size == 0:
            continue
        b = best[tr, tc]
        s = second[tr, tc]
        better = v > b
        # v == b happens only for two different dots at the same distance from the cell: then the
        # second-best value is also v, which is what the max operator charges.
        # new second = old best when v beats it, else max(old second, v)
        s = np.where(better, b, np.maximum(s, v))
        second[tr, tc] = s
        argbest[tr, tc] = np.where(better, i2, argbest[tr, tc])
        best[tr, tc] = np.where(better, v, b)

    u = np.zeros(n, np.float64)
    for (dy, dx), v in zip(offsets, values):
        tr, tc = rows + dy, cols + dx
        ok = (tr >= 0) & (tr < h) & (tc >= 0) & (tc < w)
        tr, tc, i2 = tr[ok], tc[ok], idx[ok]
        if tr.size == 0:
            continue
        b, s, a = best[tr, tc], second[tr, tc], argbest[tr, tc]
        other = np.where(a == i2, s, b)
        u[i2] += np.clip(v - other, 0.0, None)

    disc_sum = float(values.sum())
    st = {
        "disc_cells": int(offsets.shape[0]),
        "disc_kernel_sum": round(disc_sum, 6),
        "marginal_credit_mean": round(float(u.mean()), 6),
        "marginal_credit_min": round(float(u.min()), 6),
        "marginal_credit_median": round(float(np.median(u)), 6),
        "marginal_credit_max": round(float(u.max()), 6),
        "overlap_writeoff_fraction": round(1.0 - float(u.sum()) / (n * disc_sum), 6),
        "n_dots": int(n),
    }
    return u, st


def select_lowest_marginal(dots: np.ndarray, n_drop: int, radius: float = R_PX) -> tuple[np.ndarray, dict]:
    """The ``n_drop`` dots with the smallest unique credit, as a boolean mask.

    Tie-break (a real tie class exists -- credit values are quantised by the integer offset
    lattice): credit ascending, then *most congested first* (nearest-neighbour distance
    ascending), then row-major.  The last key alone would reintroduce the traversal order that
    confounded the earlier MASS session, so it is only the third key.
    """
    dots = np.asarray(dots, bool)
    rows, cols = dots.nonzero()
    n = rows.size
    if not 0 < n_drop <= n:
        raise ValueError(f"n_drop={n_drop} outside 1..{n}")
    u, st = marginal_credit(dots, radius)
    pts = np.column_stack([rows, cols]).astype(np.float64)
    nn = np.zeros(n)
    if n > 1:
        nn = cKDTree(pts).query(pts, k=2)[0][:, 1]
    flat = np.int64(dots.shape[1]) * rows + cols
    order = np.lexsort((flat, nn, u))
    chosen = order[:n_drop]
    sel = np.zeros(dots.shape, bool)
    sel[rows[chosen], cols[chosen]] = True
    boundary = int((u == u[chosen[-1]]).sum())
    parent_stats = dict(st)
    st.update({
        "selection_rule": ("unique kernel credit ascending, then nearest-neighbour distance "
                           "ascending, then row-major"),
        "n_drop": int(sel.sum()),
        "dropped_credit_mean": round(float(u[chosen].mean()), 6),
        "kept_credit_min": round(float(u[order[n_drop:]].min()), 6) if n_drop < n else None,
        "tie_class_at_cut": boundary,
        "tie_class_split_by_tiebreak": bool(boundary > int((u[chosen] == u[chosen[-1]]).sum())),
        "parent_u_stats": parent_stats,
    })
    return sel, st


# ------------------------------------------------------------------ the metric's three terms
def exact_terms(mask: np.ndarray, truth: np.ndarray, radius: float = R_PX) -> dict:
    """``T``, ``M``, ``n`` and DTI of a binary field against a truth raster.

    Same quantities as ``vendor/gems57/metric.py``: ``T = sum_g max_x k``, ``M = sum_x max_g k``,
    ``DTI = T / (T + alpha*(n - M) + beta*(|G| - T))``.
    """
    mask = np.asarray(mask, bool)
    truth = np.asarray(truth, bool)
    h, w = mask.shape
    offsets, values = _kernel_offsets(radius)
    gr, gc = truth.nonzero()
    t = 0.0
    if gr.size:
        best = np.zeros(gr.size, np.float32)
        for (dy, dx), v in zip(offsets, values):
            tr, tc = gr + dy, gc + dx
            ok = (tr >= 0) & (tr < h) & (tc >= 0) & (tc < w)
            if not ok.any():
                continue
            hit = np.zeros(gr.size, bool)
            hit[ok] = mask[tr[ok], tc[ok]]
            best = np.maximum(best, np.where(hit, v, 0.0))
        t = float(best.sum())
    mr, mc = mask.nonzero()
    m = 0.0
    if mr.size:
        for (dy, dx), v in zip(offsets, values):
            tr, tc = mr + dy, mc + dx
            ok = (tr >= 0) & (tr < h) & (tc >= 0) & (tc < w)
            if not ok.any():
                continue
            hit = np.zeros(mr.size, bool)
            hit[ok] = truth[tr[ok], tc[ok]]
            m += float(np.where(hit, v, 0.0).sum())
    n = float(mask.sum())
    g = float(truth.sum())
    den = t + ALPHA * (n - m) + BETA * (g - t)
    return {"T": round(t, 4), "M": round(m, 4), "n": n, "G": g,
            "denominator": round(den, 4), "dti": round(t / den, 8) if den > 0 else 0.0}


def mass_bar(dti: float) -> dict:
    """The two thresholds this axis turns on, in the units the metric uses."""
    a_dti = ALPHA * dti
    return {
        "dti_reference": dti,
        "alpha_dti": round(a_dti, 6),
        "add_bar_nonredundant_dot": {
            "rule": "a non-redundant dot (dT == k) pays iff k > alpha*DTI with k = 1 - d/R, i.e. "
                    "iff it is within R*(1 - alpha*DTI) of a truth pixel",
            "max_distance_px": round(R_PX * (1.0 - a_dti), 4),
            "note": "2.83 px at the incumbent's claimed 0.2778, which is why the parent's 2.8 px "
                    "thinning sits exactly at the metric's own marginal bar",
        },
        "remove_bar": {
            "rule": "removing a dot pays iff its unique truth credit u < alpha*DTI*(u + f) with "
                    "f = 1 - k its own false-positive charge, i.e. u < [alpha*DTI/(1 - alpha*DTI)]*f",
            "coefficient_on_fp_charge": round(a_dti / (1.0 - a_dti), 6),
            "note": "with f in [0,1] a removal can only pay for dots whose unique truth credit is "
                    "under ~0.06 kernel units; measured parent credits are all >= 1.49",
        },
    }


# ------------------------------------------------------------------ the mirror experiment
def _eligible(ctx: dict, dots: np.ndarray, clearance_px: float, lo: float, hi: float) -> np.ndarray:
    foot = np.asarray(ctx["footprint"], bool)
    cat = np.asarray(ctx["catalogue"], bool)
    cat_edt = ndi.distance_transform_edt(~cat)
    dot_edt = ndi.distance_transform_edt(~np.asarray(dots, bool))
    return foot & ~cat & (cat_edt > clearance_px) & (dot_edt >= lo - EPS) & (dot_edt <= hi + EPS)


def _spaced_pick(score: np.ndarray, cand: np.ndarray, n_pick: int, floor_px: float,
                 order: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Greedily take ``n_pick`` candidate cells in ``order`` while holding ``floor_px``."""
    h, w = cand.shape
    rows, cols = np.nonzero(cand)
    if order is None:
        flat = np.int64(w) * rows + cols
        order = np.lexsort((flat, -score[rows, cols]))
    taken = np.zeros((h, w), bool)
    picked = np.zeros((h, w), bool)
    blocked = 0
    floor_mask = None
    rad = int(np.ceil(floor_px)) + 1
    for i in order:
        if picked.sum() >= n_pick:
            break
        r, c = rows[i], cols[i]
        r0, r1 = max(0, r - rad), min(h, r + rad + 1)
        c0, c1 = max(0, c - rad), min(w, c + rad + 1)
        win = picked[r0:r1, c0:c1]
        if win.any():
            yy, xx = np.nonzero(win)
            if np.hypot(yy + r0 - r, xx + c0 - c).min() < floor_px - EPS:
                blocked += 1
                continue
        picked[r, c] = True
    del taken, floor_mask
    return picked, {"n_picked": int(picked.sum()), "n_requested": int(n_pick),
                    "shortfall": int(n_pick) - int(picked.sum()), "rejected_by_spacing_floor": blocked}


def _dot_strike(dots: np.ndarray, k: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """Local strike unit vectors and coherence at every dot (packet order = row-major)."""
    return SP.ridge_axes(dots, k=k)


def add_extension(ctx: dict, parent: np.ndarray, n_add: int, *, clearance_px: float = R_PX,
                  lo: float = R_PX, hi: float = 2.0 * R_PX, across_tol_px: float = 1.5,
                  coherence_min: float = 0.30, floor_px: float = R_PX) -> tuple[np.ndarray, dict]:
    """Add ``n_add`` dots along the local trace, every one >= one kernel radius from existing mass."""
    dots = np.asarray(parent, bool) & np.asarray(ctx["footprint"], bool)
    cand = _eligible(ctx, dots, clearance_px, lo, hi)
    rows, cols = dots.nonzero()
    vec, coh = _dot_strike(dots)
    tree = cKDTree(np.column_stack([rows, cols]).astype(np.float64))
    cr, cc = np.nonzero(cand)
    if cr.size == 0:
        raise ValueError("no eligible candidate cells")
    dist, near = tree.query(np.column_stack([cr, cc]).astype(np.float64), k=1)
    dy = cr - rows[near]
    dx = cc - cols[near]
    strike = vec[near]                                    # (dy, dx) unit vector
    along = dy * strike[:, 0] + dx * strike[:, 1]
    across = np.abs(dy * strike[:, 1] - dx * strike[:, 0])
    coherent = coh[near] >= coherence_min
    ok = coherent & (across <= across_tol_px + EPS) & (np.abs(along) >= floor_px - EPS)
    score = np.zeros(cand.shape, np.float64)
    score[cr, cc] = np.where(ok, coh[near] * (1.0 - across / (across_tol_px + EPS))
                             * (1.0 - np.abs(dist - floor_px) / (2.0 * R_PX)), 0.0)
    admit = np.zeros(cand.shape, bool)
    admit[cr, cc] = ok
    picked, st = _spaced_pick(score, admit, n_add, floor_px)
    st.update({"law": "extend", "candidate_cells": int(cand.sum()), "admissible_cells": int(admit.sum()),
               "coherent_candidates": int((coherent & ok).sum()) if cr.size else 0,
               "across_tol_px": across_tol_px, "coherence_min": coherence_min,
               "window_px": [lo, hi], "clearance_px": clearance_px,
               "rule": "cells 3-6 px from the nearest dot, within 1.5 px of that dot's local "
                       "strike (PCA of its 10 nearest dots, coherence >= 0.30), ranked by "
                       "coherence x across-strike fit x distance-to-one-kernel-radius, with a "
                       "3 px spacing floor among the new dots"})
    return picked, st


def add_random(ctx: dict, parent: np.ndarray, n_add: int, *, clearance_px: float = R_PX,
               lo: float = R_PX, hi: float = 2.0 * R_PX, floor_px: float = R_PX,
               seed: int = 20261023) -> tuple[np.ndarray, dict]:
    """Null control: the same admissible window, uniformly sampled, same spacing floor."""
    dots = np.asarray(parent, bool) & np.asarray(ctx["footprint"], bool)
    cand = _eligible(ctx, dots, clearance_px, lo, hi)
    rng = np.random.default_rng(seed)
    score = rng.random(cand.shape)
    picked, st = _spaced_pick(score, cand, n_add, floor_px)
    st.update({"law": "random", "candidate_cells": int(cand.sum()), "window_px": [lo, hi],
               "clearance_px": clearance_px, "seed": int(seed),
               "rule": "uniformly drawn cells from the same admissible window with the same 3 px "
                       "spacing floor; the control the extend arm is read against"})
    return picked, st
