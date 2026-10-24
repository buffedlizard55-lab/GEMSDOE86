"""Deconfounded 5 km ridge-supported CONCENTRATION axis for GEMSDOE86.

Why this module exists
----------------------
After PR #41 merged ``TRACKB``, ``CONCENTRATION`` remained the only brief-v2 §5
axis with a single ledger row (``b1km-move15`` from PR #37), and forensic review
of ``b1km-move15`` uncovered four concrete issues (``IR-86-CONC-05``):

1. Its ``+0.006 MODEL`` ledger/plan figure was a hard-coded dictionary constant
   in ``scripts/build_axis_variants.py`` rather than a measured SGMC surrogate
   delta;
2. It placed newly emitted dots down to ``2.2361 px`` (224 m) from the mapped
   catalogue, violating brief v2 §4.4 (``>= 3 px`` clearance on newly emitted
   mass unless ``AXIS=PRUNE``) and relaxing R0's ``sqrt(8)`` spacing floor;
3. It moved dots off the parent lineage's lineament evidence surface onto empty
   desert pixels inside 1 km cells (``IR-86-SPACING-02``);
4. It tested only 1 km upward clustering (pushing 1 km occupied block-density CV
   from ``0.6235`` to ``0.7644``, *away* from the ``0.51-0.59`` band occupied by
   top-scoring historical submissions), leaving ``SLOT_PLAN.md``'s 5 km regional
   structural scale and spread-into-CV-band sign flip unbuilt.

What this module builds (deterministic, zero RNG on all candidate arms)
-----------------------------------------------------------------------
* **Faulds 5 km Fault-Interaction Block Prior** on ``50 x 50 px`` (5 km) blocks:
    - ``0.40 * z(cat_tips_junctions_15km)``: 15 km halo density of skeletonized
      mapped-fault terminations (tips) and branch/intersection junctions (Faulds
      & Hinz 2015 structural step-overs, splays, and accommodation zones, avoiding
      raw fault-length quadrangle mapping bias);
    - ``0.30 * z(ridge_tips_junctions_5km)``: 5 km density of terminations and
      junctions on the pinned ancestor ridge union ``H19-5 | H19-4 | H16-1`` (so
      unmapped basins with strong geophysical/topographic fault-interaction
      geometry are scored alongside mapped range fronts);
    - ``0.30 * z(tmi_agc_5km)``: 5 km mean of 10.1 km local-RMS Automatic Gain
      Control (AGC) Sobel horizontal gradient of 150 m upward-continued TMI
      (USGS GeoDAWN DOI 10.5066/P93LGLVQ), eliminating the ~2x Miocene basalt vs
      Paleozoic carbonate magnetization amplitude bias across NW vs E Nevada.
* **Candidate position constraint**: every newly placed dot must lie on a genuine
  pinned ancestor lineament ridge cell (``H19-5 | H19-4 | H16-1``), inside the
  footprint, strictly ``> 3.0 px`` clear of mapped catalogue faults (§4.4), and
  at Euclidean distance ``>= sqrt(8) = 2.8284 px`` from every retained and newly
  placed dot (zero tightening of R0's spacing floor).
* **Three controlled single-axis variants on R0** (all ``count = 37,654`` fixed):
    1. ``b5km-ridge-up8``: relocate 8.0% of R0 (3,012 dots, 15.9983% changed)
       from lowest-prior 5 km blocks onto unused ancestor ridges in the top-35%
       fault-interaction 5 km blocks;
    2. ``b5km-ridge-up4``: relocate 4.0% of R0 (1,506 dots, 7.9991% changed) —
       strict nested half-dose prefix of ``b5km-ridge-up8`` in both sources and
       destinations;
    3. ``b5km-cvband-down4``: exact-dose sign flip (1,506 dots moved, 7.9991%
       changed) shaving redundant dots from the densest ``>= 3``-dot 1 km blocks
       onto unused ancestor ridges in sparse ``1-2``-dot blocks, bringing 1 km
       occupied block-density CV from ``0.6235`` down into ``[0.51, 0.59]``.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

try:
    from gems86 import mass_econ
except ImportError:  # pragma: no cover
    from src.gems86 import mass_econ


def zhang_suen_thin(mask: np.ndarray) -> np.ndarray:
    """Deterministic 2-subiteration Zhang-Suen 1-px morphological skeleton."""
    a = np.pad(np.asarray(mask, dtype=np.uint8), 1, mode="constant")
    while True:
        changed = False
        for step in (0, 1):
            p2 = a[:-2, 1:-1]
            p3 = a[:-2, 2:]
            p4 = a[1:-1, 2:]
            p5 = a[2:, 2:]
            p6 = a[2:, 1:-1]
            p7 = a[2:, :-2]
            p8 = a[1:-1, :-2]
            p9 = a[:-2, :-2]
            b_cnt = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            a_tr = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1))
                + ((p4 == 0) & (p5 == 1))
                + ((p5 == 0) & (p6 == 1))
                + ((p6 == 0) & (p7 == 1))
                + ((p7 == 0) & (p8 == 1))
                + ((p8 == 0) & (p9 == 1))
                + ((p9 == 0) & (p2 == 1))
            )
            if step == 0:
                m1 = p2 * p4 * p6
                m2 = p4 * p6 * p8
            else:
                m1 = p2 * p4 * p8
                m2 = p2 * p6 * p8
            rem = (
                (a[1:-1, 1:-1] == 1)
                & (b_cnt >= 2)
                & (b_cnt <= 6)
                & (a_tr == 1)
                & (m1 == 0)
                & (m2 == 0)
            )
            if np.any(rem):
                a[1:-1, 1:-1][rem] = 0
                changed = True
        if not changed:
            break
    return a[1:-1, 1:-1].astype(bool)


def skeleton_tips_and_junctions(mask: np.ndarray) -> dict[str, np.ndarray]:
    """Identify 1-px skeleton terminations (deg=1) and junctions (deg>=3)."""
    sk = zhang_suen_thin(mask)
    kern = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16)
    deg = ndi.convolve(sk.astype(np.int16), kern, mode="constant", cval=0)
    tips = sk & (deg == 1)
    junctions = sk & (deg >= 3)
    return dict(skeleton=sk, tips=tips, junctions=junctions)


def local_agc_gradient(
    field: np.ndarray,
    footprint: np.ndarray,
    *,
    window_px: int = 101,
    floor: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Sobel horizontal gradient + footprint-masked local-RMS gain control."""
    foot = np.asarray(footprint, dtype=bool)
    arr = np.asarray(field, dtype=np.float64)
    finite = foot & np.isfinite(arr)
    med = float(np.median(arr[finite])) if np.any(finite) else 0.0
    clean = np.where(finite, arr, med)
    gx = ndi.sobel(clean, axis=1, mode="nearest") / 8.0
    gy = ndi.sobel(clean, axis=0, mode="nearest") / 8.0
    interior = ndi.binary_erosion(finite, structure=np.ones((3, 3), dtype=bool))
    grad = np.where(interior, np.hypot(gx, gy), 0.0).astype(np.float32)

    num = ndi.uniform_filter(
        np.where(foot, grad.astype(np.float64) ** 2, 0.0), size=int(window_px), mode="nearest"
    )
    den = np.maximum(
        ndi.uniform_filter(foot.astype(np.float64), size=int(window_px), mode="nearest"), 1e-6
    )
    rms = np.sqrt(np.maximum(num / den, 0.0))
    agc = np.where(foot, grad / (rms + float(floor)), 0.0).astype(np.float32)
    return grad, agc


def _block_mean_padded(arr: np.ndarray, block_px: int) -> np.ndarray:
    """Mean over ``block_px x block_px`` tiles covering the full raster (padded with 0)."""
    h, w = arr.shape
    nb = (h + block_px - 1) // block_px
    mb = (w + block_px - 1) // block_px
    ph, pw = nb * block_px - h, mb * block_px - w
    padded = np.pad(np.asarray(arr, dtype=np.float64), ((0, ph), (0, pw)), mode="constant", constant_values=0.0)
    return padded.reshape(nb, block_px, mb, block_px).mean(axis=(1, 3))


def _block_sum_padded(arr: np.ndarray, block_px: int) -> np.ndarray:
    h, w = arr.shape
    nb = (h + block_px - 1) // block_px
    mb = (w + block_px - 1) // block_px
    ph, pw = nb * block_px - h, mb * block_px - w
    padded = np.pad(np.asarray(arr, dtype=np.float64), ((0, ph), (0, pw)), mode="constant", constant_values=0.0)
    return padded.reshape(nb, block_px, mb, block_px).sum(axis=(1, 3))


def expand_blocks_to_pixels(block_field: np.ndarray, shape: tuple[int, int], block_px: int) -> np.ndarray:
    """Expand a padded block grid back to exact ``shape`` pixel coordinates."""
    h, w = shape
    expanded = np.repeat(np.repeat(np.asarray(block_field, dtype=np.float64), block_px, axis=0), block_px, axis=1)
    return expanded[:h, :w]


def block_density_stats(dots: np.ndarray, footprint: np.ndarray, block_px: int) -> dict[str, Any]:
    """Occupied block-density CV at ``block_px`` scale (10 px = 1 km, 50 px = 5 km)."""
    m = np.asarray(dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    f = np.asarray(footprint, dtype=bool)
    h, w = m.shape
    nb, mb = h // block_px, w // block_px
    d = m[: nb * block_px, : mb * block_px].astype(np.float64).reshape(nb, block_px, mb, block_px).sum(axis=(1, 3))
    fb = f[: nb * block_px, : mb * block_px].astype(np.float64).reshape(nb, block_px, mb, block_px).sum(axis=(1, 3))
    dens = d / np.maximum(fb, 1.0)
    occ = d > 0
    if not np.any(occ):
        return dict(
            block_px=int(block_px),
            occupied_blocks=0,
            total_blocks=int(d.size),
            density_cv_occupied=0.0,
            count_cv_occupied=0.0,
            mean_dots_per_occupied_block=0.0,
        )
    return dict(
        block_px=int(block_px),
        occupied_blocks=int(occ.sum()),
        total_blocks=int(d.size),
        density_cv_occupied=round(float(dens[occ].std() / dens[occ].mean()), 4),
        count_cv_occupied=round(float(d[occ].std() / d[occ].mean()), 4),
        mean_dots_per_occupied_block=round(float(d[occ].mean()), 4),
    )


def faulds_5km_block_prior(
    footprint: np.ndarray,
    catalogue: np.ndarray,
    ridge_union: np.ndarray,
    tmi_up150: np.ndarray,
    *,
    block_px: int = 50,
    min_foot_frac: float = 0.05,
    agc_window_px: int = 101,
    precomputed_ridge_topo: dict[str, np.ndarray] | None = None,
    precomputed_tmi_grad_agc: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict[str, Any]:
    """Compute deconfounded 5 km Faulds structural fault-interaction prior."""
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool) & foot
    rdg = np.asarray(ridge_union, dtype=bool) & foot

    cat_topo = skeleton_tips_and_junctions(cat)
    rdg_topo = precomputed_ridge_topo if precomputed_ridge_topo is not None else skeleton_tips_and_junctions(rdg)
    if precomputed_tmi_grad_agc is not None:
        tmi_grad, tmi_agc = precomputed_tmi_grad_agc
    else:
        tmi_grad, tmi_agc = local_agc_gradient(tmi_up150, foot, window_px=agc_window_px)

    cat_loci = (cat_topo["tips"] | cat_topo["junctions"]).astype(np.float32)
    rdg_loci = (rdg_topo["tips"] | rdg_topo["junctions"]).astype(np.float32)

    cat_halo = ndi.uniform_filter(cat_loci, size=max(3 * block_px, 3), mode="constant")
    rdg_halo = ndi.uniform_filter(rdg_loci, size=max(block_px, 3), mode="constant")

    fp_frac = _block_mean_padded(foot.astype(np.float32), block_px)
    valid_b = fp_frac >= float(min_foot_frac)

    b_cat = _block_sum_padded(cat_halo * foot, block_px) / np.maximum(_block_sum_padded(foot, block_px), 1.0)
    b_rdg = _block_sum_padded(rdg_halo * foot, block_px) / np.maximum(_block_sum_padded(foot, block_px), 1.0)
    b_tmi = _block_sum_padded(tmi_agc * foot, block_px) / np.maximum(_block_sum_padded(foot, block_px), 1.0)

    def _bz(b: np.ndarray) -> np.ndarray:
        vals = b[valid_b]
        if vals.size == 0 or float(vals.std()) < 1e-9:
            return np.where(valid_b, 0.0, -np.inf)
        return np.where(valid_b, (b - float(vals.mean())) / float(vals.std()), -np.inf)

    prior_b = 0.40 * _bz(b_cat) + 0.30 * _bz(b_rdg) + 0.30 * _bz(b_tmi)
    prior_b[~valid_b] = -np.inf
    prior_px = expand_blocks_to_pixels(prior_b, foot.shape, block_px)

    nb, mb = prior_b.shape
    q_b = np.zeros((nb, mb), dtype=np.int8)
    q_b[: nb // 2, mb // 2 :] = 1
    q_b[nb // 2 :, : mb // 2] = 2
    q_b[nb // 2 :, mb // 2 :] = 3
    top35_cut = float(np.quantile(prior_b[valid_b], 0.65)) if np.any(valid_b) else 0.0
    n_top35 = max(int((valid_b & (prior_b >= top35_cut)).sum()), 1)
    quad_summary = {}
    for qi, qn in enumerate(("Q1_NW", "Q2_NE", "Q3_SW", "Q4_SE")):
        m = valid_b & (q_b == qi)
        quad_summary[qn] = dict(
            valid_blocks=int(m.sum()),
            valid_share_pct=round(100.0 * float(m.sum()) / max(int(valid_b.sum()), 1), 2),
            top35_share_pct=round(100.0 * float((m & (prior_b >= top35_cut)).sum()) / n_top35, 2),
            mean_prior=round(float(prior_b[m].mean()), 4) if np.any(m) else 0.0,
        )

    return dict(
        prior_blocks=prior_b.astype(np.float64),
        prior_px=prior_px.astype(np.float64),
        valid_blocks=valid_b,
        tmi_grad=tmi_grad,
        tmi_agc=tmi_agc,
        cat_loci_map=cat_halo.astype(np.float32),
        rdg_loci_map=rdg_halo.astype(np.float32),
        counts=dict(
            cat_tips=int(cat_topo["tips"].sum()),
            cat_junctions=int(cat_topo["junctions"].sum()),
            ridge_tips=int(rdg_topo["tips"].sum()),
            ridge_junctions=int(rdg_topo["junctions"].sum()),
            valid_5km_blocks=int(valid_b.sum()),
        ),
        quadrant_balance=quad_summary,
    )


def _min_pair_distance(mask: np.ndarray) -> float:
    ys, xs = np.nonzero(mask)
    if len(ys) < 2:
        return float("inf")
    pts = np.column_stack([ys, xs]).astype(np.float64)
    d2, _ = cKDTree(pts).query(pts, k=2)
    return float(d2[:, 1].min())


def _relocation_stats(
    parent: np.ndarray,
    child: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    *,
    src_rc: np.ndarray,
    dst_rc: np.ndarray,
) -> dict[str, Any]:
    p = np.asarray(parent, dtype=bool)
    c = np.asarray(child, dtype=bool)
    added = c & ~p
    removed = p & ~c
    n_p = int(p.sum())
    n_c = int(c.sum())
    n_add = int(added.sum())
    n_rem = int(removed.sum())
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
        added_on_ancestor_ridge_fraction=(
            round(float((added & ridge_union).sum()) / n_add, 6) if n_add else 1.0
        ),
        min_pair_distance_parent_px=round(_min_pair_distance(p), 4),
        min_pair_distance_variant_px=round(_min_pair_distance(c), 4),
        displacement_px=dict(
            mean=round(float(disp.mean()), 2) if disp.size else 0.0,
            median=round(float(np.median(disp)), 2) if disp.size else 0.0,
        ),
        cv_1km_parent=block_density_stats(p, footprint, 10),
        cv_1km_variant=block_density_stats(c, footprint, 10),
        cv_5km_parent=block_density_stats(p, footprint, 50),
        cv_5km_variant=block_density_stats(c, footprint, 50),
    )


def relocate_5km_ridge_up(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    prior_blocks: np.ndarray,
    *,
    n_move: int,
    block_px: int = 50,
    dest_block_frac: float = 0.35,
    min_clearance_px: float = 3.0,
    min_spacing_px: float = math.sqrt(8.0) - 1e-6,
    unique_credit_dots: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Relocate ``n_move`` dots from lowest-prior to highest-prior 5 km blocks on ridges.

    Guarantees strict prefix nesting across doses ``n_move``:
      * sources are ordered once by ``(block_prior_asc, unique_credit_asc, row, col)``;
      * destinations are ordered once inside the top ``dest_block_frac`` 5 km blocks
        on ``ridge_union & (edt_cat > min_clearance_px)`` with spacing ``>= min_spacing_px``
        checked against ``parent_dots`` as a whole (which never overlaps the bottom
        donor blocks), so ``src[:k]`` and ``dst[:k]`` are exact prefixes of larger ``k``.
    """
    parent = np.asarray(parent_dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    rdg = np.asarray(ridge_union, dtype=bool) & foot
    edt = np.asarray(edt_cat, dtype=np.float64)
    h, w = parent.shape

    prior_px = expand_blocks_to_pixels(prior_blocks, (h, w), block_px)
    ys, xs = np.nonzero(parent)
    if unique_credit_dots is None:
        u_cred, _ = mass_econ.marginal_credit(parent)
    else:
        u_cred = np.asarray(unique_credit_dots, dtype=np.float64)

    dot_bp = prior_px[ys, xs]
    # Replace -inf (tiny edge slivers if any) with finite floor below minimum valid block
    fin_bp = dot_bp[np.isfinite(dot_bp)]
    bp_floor = (float(fin_bp.min()) - 10.0) if fin_bp.size else -100.0
    dot_bp_clean = np.where(np.isfinite(dot_bp), dot_bp, bp_floor)

    src_order = np.lexsort((xs, ys, u_cred, dot_bp_clean))
    if int(n_move) > len(src_order):
        raise ValueError(f"Requested n_move={n_move} exceeds parent dots {len(src_order)}")
    sel_src_idx = src_order[: int(n_move)]
    src_rc = np.column_stack([ys[sel_src_idx], xs[sel_src_idx]]).astype(np.int32)

    valid_b = np.isfinite(prior_blocks)
    b_order = np.argsort(np.where(valid_b, prior_blocks, -np.inf).ravel(), kind="stable")[::-1]
    n_dest_b = max(1, int(round(float(dest_block_frac) * int(valid_b.sum()))))
    dest_b = np.zeros_like(valid_b)
    dest_b.ravel()[b_order[:n_dest_b]] = True
    dest_px = expand_blocks_to_pixels(dest_b.astype(np.float64), (h, w), block_px) > 0.5

    # Ensure strict spatial disjointness between donor pixels and destination blocks
    donor_mask = np.zeros_like(parent)
    donor_mask[src_rc[:, 0], src_rc[:, 1]] = True
    if np.any(donor_mask & dest_px):
        raise ValueError("Donor blocks overlap destination blocks; reduce dose or dest_block_frac")

    edt_parent = ndi.distance_transform_edt(~parent)
    cand_mask = (
        rdg
        & dest_px
        & ~parent
        & (edt > float(min_clearance_px))
        & (edt_parent >= float(min_spacing_px))
    )
    c_ys, c_xs = np.nonzero(cand_mask)
    c_bp = prior_px[c_ys, c_xs]
    c_gap = edt_parent[c_ys, c_xs]
    # Geometric block-prior ordering: highest-prior block first, then largest kernel gap
    # inside the block (no pixel-scale geophysical snapping!).
    c_order = np.lexsort((c_xs, c_ys, -np.round(c_gap, 4), -np.round(c_bp, 6)))

    occ = parent.copy()
    half = int(math.ceil(float(min_spacing_px)))
    placed: list[tuple[int, int]] = []
    for k in c_order.tolist():
        if len(placed) >= int(n_move):
            break
        r, c = int(c_ys[k]), int(c_xs[k])
        r0, r1 = max(0, r - half), min(h, r + half + 1)
        c0, c1 = max(0, c - half), min(w, c + half + 1)
        win = occ[r0:r1, c0:c1]
        if win.any():
            rr, cc = np.nonzero(win)
            if float(np.hypot(rr + r0 - r, cc + c0 - c).min()) < float(min_spacing_px):
                continue
        occ[r, c] = True
        placed.append((r, c))

    if len(placed) < int(n_move):
        raise ValueError(
            f"Ridge destination capacity {len(placed)} < requested n_move={n_move} "
            f"(dest_block_frac={dest_block_frac})"
        )

    dst_rc = np.asarray(placed, dtype=np.int32)
    out = parent.copy()
    out[src_rc[:, 0], src_rc[:, 1]] = False
    out[dst_rc[:, 0], dst_rc[:, 1]] = True

    stats = _relocation_stats(
        parent, out, foot, edt, rdg, src_rc=src_rc, dst_rc=dst_rc
    )
    stats["dest_5km_blocks"] = int(n_dest_b)
    stats["dest_block_frac"] = float(dest_block_frac)
    return out, src_rc, dst_rc, stats


def relocate_cvband_down(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    *,
    n_move: int = 1506,
    km_block_px: int = 10,
    min_clearance_px: float = 3.0,
    min_spacing_px: float = math.sqrt(8.0) - 1e-6,
    unique_credit_dots: np.ndarray | None = None,
    dest_filter: np.ndarray | None = None,
    dest_prefer: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Sign-flip arm: shave over-concentrated blocks into sparse ridge-bearing blocks.

    Brings 1 km occupied block-density CV from R0's ``0.6235`` down into the
    ``0.51-0.59`` empirical top-scorer band while preserving count, ``> 3.0 px``
    catalogue clearance, ``>= sqrt(8)`` inter-dot spacing, and 100% ancestor-ridge
    placement.

    ``dest_filter`` (optional) restricts the destination candidate pool to a
    pre-computed boolean mask (e.g. the truth-free pediment window); the removal
    loop is untouched, so sources stay identical to the unfiltered arm.
    ``dest_prefer`` (optional) reorders the destination scan so masked cells are
    filled first (dose arms spill over into the rest of the pool only after the
    preferred cells are exhausted). Both default to ``None`` == the historical
    byte-identical behaviour asserted by the unit tests.
    """
    parent = np.asarray(parent_dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    rdg = np.asarray(ridge_union, dtype=bool) & foot
    edt = np.asarray(edt_cat, dtype=np.float64)
    h, w = parent.shape

    nb, mb = h // km_block_px, w // km_block_px
    sub_p = parent[: nb * km_block_px, : mb * km_block_px].astype(np.float64)
    sub_f = foot[: nb * km_block_px, : mb * km_block_px].astype(np.float64)
    c_cur = sub_p.reshape(nb, km_block_px, mb, km_block_px).sum(axis=(1, 3)).copy()
    fb = sub_f.reshape(nb, km_block_px, mb, km_block_px).sum(axis=(1, 3))
    d_cur = c_cur / np.maximum(fb, 1.0)

    ys, xs = np.nonzero(parent)
    if unique_credit_dots is None:
        u_cred, _ = mass_econ.marginal_credit(parent)
    else:
        u_cred = np.asarray(unique_credit_dots, dtype=np.float64)

    # Order dots inside each 1 km block so the lowest-unique-credit dot is popped first
    blk_dots: dict[tuple[int, int], list[tuple[float, int, int]]] = {}
    for idx in range(len(ys)):
        r, c = int(ys[idx]), int(xs[idx])
        bi, bj = r // km_block_px, c // km_block_px
        if bi < nb and bj < mb:
            blk_dots.setdefault((bi, bj), []).append((float(u_cred[idx]), r, c))
    for k in blk_dots:
        # Sort descending so .pop() yields the lowest unique-credit dot (tie-break: row, col)
        blk_dots[k].sort(key=lambda item: (-item[0], -item[1], -item[2]))

    sim = parent.copy()
    removed: list[tuple[int, int]] = []
    while len(removed) < int(n_move):
        elig_hi = c_cur >= 3
        if not np.any(elig_hi):
            raise ValueError(f"Exhausted >=3-dot blocks after {len(removed)} removals")
        flat_idx = int(np.argmax(np.where(elig_hi, d_cur, -1.0)))
        bi, bj = divmod(flat_idx, mb)
        _, r, c = blk_dots[(bi, bj)].pop()
        sim[r, c] = False
        c_cur[bi, bj] -= 1.0
        d_cur[bi, bj] = c_cur[bi, bj] / max(fb[bi, bj], 1.0)
        removed.append((r, c))

    edt_sim = ndi.distance_transform_edt(~sim)
    min_area = max(1, int(0.40 * (km_block_px ** 2)))
    dest_blk = (c_cur >= 1) & (c_cur <= 2) & (fb >= min_area)
    dest_px = np.zeros((h, w), dtype=bool)
    dest_px[: nb * km_block_px, : mb * km_block_px] = np.repeat(
        np.repeat(dest_blk, km_block_px, axis=0), km_block_px, axis=1
    )

    cand_mask = (
        rdg
        & dest_px
        & ~parent  # never re-place a dot on a cell that was just vacated
        & (edt > float(min_clearance_px))
        & (edt_sim >= float(min_spacing_px))
    )
    if dest_filter is not None:
        df = np.asarray(dest_filter, dtype=bool)
        if df.shape != cand_mask.shape:
            raise ValueError("dest_filter must share the grid shape")
        cand_mask &= df
    c_ys, c_xs = np.nonzero(cand_mask)
    c_cnt = np.repeat(np.repeat(c_cur, km_block_px, axis=0), km_block_px, axis=1)[c_ys, c_xs]
    c_gap = edt_sim[c_ys, c_xs]
    if dest_prefer is None:
        c_order = np.lexsort((c_xs, c_ys, -np.round(c_gap, 4), c_cnt))
    else:
        dp = np.asarray(dest_prefer, dtype=bool)
        if dp.shape != cand_mask.shape:
            raise ValueError("dest_prefer must share the grid shape")
        # lexsort: LAST key is primary -> preferred cells are scanned first
        c_order = np.lexsort((c_xs, c_ys, -np.round(c_gap, 4), c_cnt, -dp[c_ys, c_xs].astype(np.int64)))

    half = int(math.ceil(float(min_spacing_px)))
    added: list[tuple[int, int]] = []
    for k in c_order.tolist():
        if len(added) >= int(n_move):
            break
        r, c = int(c_ys[k]), int(c_xs[k])
        bi, bj = r // km_block_px, c // km_block_px
        if c_cur[bi, bj] >= 3:
            continue
        r0, r1 = max(0, r - half), min(h, r + half + 1)
        c0, c1 = max(0, c - half), min(w, c + half + 1)
        win = sim[r0:r1, c0:c1]
        if win.any():
            rr, cc = np.nonzero(win)
            if float(np.hypot(rr + r0 - r, cc + c0 - c).min()) < float(min_spacing_px):
                continue
        sim[r, c] = True
        c_cur[bi, bj] += 1.0
        added.append((r, c))

    if len(added) < int(n_move):
        raise ValueError(f"CV-band dispersal destination capacity {len(added)} < n_move={n_move}")

    src_rc = np.asarray(removed, dtype=np.int32)
    dst_rc = np.asarray(added, dtype=np.int32)
    stats = _relocation_stats(parent, sim, foot, edt, rdg, src_rc=src_rc, dst_rc=dst_rc)
    return sim, src_rc, dst_rc, stats


def relocate_5km_random_control(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    valid_blocks: np.ndarray,
    *,
    n_move: int,
    block_px: int = 50,
    seed: int = 20261023,
    min_clearance_px: float = 3.0,
    min_spacing_px: float = math.sqrt(8.0) - 1e-6,
    unique_credit_dots: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Matched null control (measured, never promoted): random 5 km block prior."""
    rng = np.random.default_rng(int(seed))
    rand_b = np.full(valid_blocks.shape, -np.inf, dtype=np.float64)
    rand_b[valid_blocks] = rng.standard_normal(int(valid_blocks.sum()))
    for dfrac in (0.35, 0.45, 0.55):
        try:
            out, _, _, stats = relocate_5km_ridge_up(
                parent_dots,
                footprint,
                edt_cat,
                ridge_union,
                rand_b,
                n_move=n_move,
                block_px=block_px,
                dest_block_frac=dfrac,
                min_clearance_px=min_clearance_px,
                min_spacing_px=min_spacing_px,
                unique_credit_dots=unique_credit_dots,
            )
            stats["random_seed"] = int(seed)
            return out, stats
        except ValueError:
            continue
    raise ValueError(f"Random 5 km control could not place {n_move} dots on ridge union")
