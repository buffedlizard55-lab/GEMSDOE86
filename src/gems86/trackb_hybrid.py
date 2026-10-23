"""TRACKB (Phase 2) axis: strike-consistent >= 1 km fault traces from R0's dots + 3 controlled R0 variants.

Scientific scope (brief v2 sections 2, 4, 5, 6)
-----------------------------------------------
Phase 1 ($50k) scores private chunks under the distance-weighted Tversky index (DTI, alpha=0.2,
beta=0.8, triangular kernel R=300 m = 3 px).  Phase 2 ($250k) rescores the *same* single blind
final GeoTIFF after structural-geology experts review submitted faults and expand the reference
label set.

This module implements ``AXIS = TRACKB`` as a purely label-free, reproducible geometric + USGS
multi-physics trace extraction on R0 (``h33-h33-2-b2``, 37,654 unit-mass dots):

1. **Strike-consistent polyline inventory (>= 1.0 km)** built strictly from R0's dots (> 3.0 px
   clear of mapped USGS/INGENIOUS catalogue traces) along R0's pinned ``H19-5`` ridge network,
   ranked by a susceptibility-invariant multi-physics fault-evidence composite (5 km AGC-normalised
   GeoDAWN ``TMI_up150`` horizontal gradient + USGS 3DEP 10 m scarp composite) plus log trace
   length.  Exported as RFC 7946 GeoJSON (``CRS84`` lon/lat + native ``EPSG:32611`` UTM metadata)
   with one quantitative structural-geologist evidence paragraph per trace.
2. **Three controlled variants of R0** (all strictly changing 1-50 % of R0's dots, zero mass on
   catalogue pixels, every newly emitted pixel > 3.0 px off catalogue):
   * ``cull1dot``      delete isolated 1-dot singletons (no R0 neighbour within 550 m), keeping all
                       multi-dot chains and >= 1 km traces untouched (selection needs zero tie-break).
   * ``bridge1km``     count-fixed (37,654) kernel-spaced (>= 2.8284 px) reallocation from those
                       isolated singletons into internal > 300 m kernel blind-spot midpoints and
                       collinear 320 m tip extensions of R0's >= 1 km strike-consistent traces.
   * ``rendertop120``  count-fixed (37,654) continuous 100 m 8-connected Bresenham polyline
                       rasterisation of the top-120 GeoJSON traces, funded 1-for-1 by removing the
                       weakest isolated singletons — testing Phase 2 continuous trace identity
                       against the Phase 1 DTI sub-kernel overlap tax.

Nothing here reads competition test labels or USGS SGMC faults during extraction or placement.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage as ndi
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

CELL_M = 100.0
KERNEL_R_PX = 3.0
PARENT_MIN_SPACING_PX = float(np.sqrt(8.0))  # 2.8284271247461903 px (R0's d=2.8 thinning floor)
NEW_MASS_CLEARANCE_PX = 3.0                  # brief section 4.4: >= 3 px off catalogue
SINGLETON_LINK_PX = 5.5                      # 550 m: < 2 kernel radii; singletons cannot form chains


def bresenham_line(r0: int, c0: int, r1: int, c1: int) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic 8-connected integer pixel segment from ``(r0, c0)`` to ``(r1, c1)``."""
    r0_i, c0_i, r1_i, c1_i = int(r0), int(c0), int(r1), int(c1)
    n = max(abs(r1_i - r0_i), abs(c1_i - c0_i))
    if n == 0:
        return np.array([r0_i], dtype=np.int32), np.array([c0_i], dtype=np.int32)
    rs = np.rint(np.linspace(r0_i, r1_i, n + 1)).astype(np.int32)
    cs = np.rint(np.linspace(c0_i, c1_i, n + 1)).astype(np.int32)
    rs[0], cs[0] = r0_i, c0_i
    rs[-1], cs[-1] = r1_i, c1_i
    return rs, cs


def dti_algebra_terms(pred: np.ndarray, truth: np.ndarray,
                      valid: np.ndarray | None = None,
                      known: np.ndarray | None = None) -> dict[str, float]:
    """Compute exact DTI algebra terms (brief section 2) and verify identity against ``gems57.metric``.

    ``DTI = T / (0.2*T + 0.2*(S - M) + 0.8*|G| + eps)``, where:
      * ``T`` = sum over scored truth pixels ``g`` of ``max_x p(x) * k(d(x, g))``
      * ``S`` = sum over scored non-known pixels ``x`` of ``p(x)``
      * ``M`` = sum over scored non-known pixels ``x`` of ``p(x) * max_g k(d(x, g))``
      * ``|G|`` = count of scored truth pixels
    """
    from gems57 import metric  # vendored immutable shared metric

    p = np.asarray(pred, dtype=np.float32)
    t = np.asarray(truth, dtype=bool)
    res = metric.dti_exact(p, t, valid=valid, known=known)
    T = float(res["tp"])
    F = float(res["fp"])
    G = float(res["n_truth"])
    mask = np.ones(p.shape, dtype=bool) if valid is None else np.asarray(valid, dtype=bool).copy()
    if known is not None:
        mask = mask & ~np.asarray(known, dtype=bool)
    S = float(np.nan_to_num(p[mask], nan=0.0).sum())
    M = S - F
    denom = 0.2 * T + 0.2 * (S - M) + 0.8 * G + float(metric.EPS)
    closed = T / denom if G > 0 else 0.0
    return {
        "T": T,
        "S": S,
        "M": M,
        "F": F,
        "G": G,
        "dti_closed": float(closed),
        "dti_metric": float(res["dti"]),
    }


def exact_marginal_dti_gain(base_pred: np.ndarray, truth: np.ndarray,
                            add_rc: tuple[int, int],
                            valid: np.ndarray | None = None,
                            known: np.ndarray | None = None) -> dict[str, float]:
    """Exact marginal DTI change of adding one unit-mass dot at ``add_rc`` (brief section 2)."""
    before = dti_algebra_terms(base_pred, truth, valid=valid, known=known)
    cand = np.asarray(base_pred, dtype=np.float32).copy()
    cand[int(add_rc[0]), int(add_rc[1])] = 1.0
    after = dti_algebra_terms(cand, truth, valid=valid, known=known)
    return {
        "dti_before": before["dti_metric"],
        "dti_after": after["dti_metric"],
        "delta_dti": after["dti_metric"] - before["dti_metric"],
        "delta_T": after["T"] - before["T"],
        "delta_M": after["M"] - before["M"],
        "isolated_bar": 0.2 * before["dti_metric"],
    }


def isolated_singletons(dots: np.ndarray, footprint: np.ndarray,
                        link_radius_px: float = SINGLETON_LINK_PX) -> tuple[np.ndarray, dict[str, Any]]:
    """Identify R0 dots with zero neighbours inside ``link_radius_px`` (no tie-break needed)."""
    d = np.asarray(dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    pts = np.argwhere(d)
    if len(pts) == 0:
        return np.zeros_like(d), {"n_dots": 0, "n_singletons": 0, "n_pairs": 0, "n_components": 0}
    tree = cKDTree(pts)
    adj = tree.sparse_distance_matrix(tree, max_distance=float(link_radius_px), output_type="coo_matrix")
    n_comp, labels = connected_components(adj, directed=False)
    sizes = np.bincount(labels)[labels]
    sing_pts = pts[sizes == 1]
    sing_mask = np.zeros_like(d)
    if len(sing_pts):
        sing_mask[sing_pts[:, 0], sing_pts[:, 1]] = True
    return sing_mask, {
        "link_radius_px": float(link_radius_px),
        "link_radius_m": float(link_radius_px * CELL_M),
        "n_dots": int(len(pts)),
        "n_components": int(n_comp),
        "n_singletons": int((sizes == 1).sum()),
        "n_pair_dots": int((sizes == 2).sum()),
        "n_small_3to5_dots": int(((sizes >= 3) & (sizes <= 5)).sum()),
        "n_chain_gt5_dots": int((sizes > 5).sum()),
        "pct_singletons": round(100.0 * float((sizes == 1).sum()) / len(pts), 4),
    }


def build_evidence_surface(tmi_up150: np.ndarray, scarp_bands: dict[str, np.ndarray],
                           footprint: np.ndarray, agc_window_px: int = 50) -> dict[str, np.ndarray]:
    """Susceptibility-invariant multi-physics fault-edge evidence (USGS GeoDAWN + 3DEP 10 m).

    Raw ``|grad(TMI)|`` overweights high-susceptibility Miocene-Pliocene flood basalts in NW
    Nevada relative to Mesozoic metasediments and Tertiary tuffs elsewhere in the Great Basin.
    Normalising ``|grad(TMI_up150)|`` by its 5 km local RMS (automatic gain control) removes
    regional susceptibility contrast while preserving local fault-contact edges.
    """
    foot = np.asarray(footprint, dtype=bool)
    a = np.nan_to_num(np.asarray(tmi_up150, dtype=np.float32), nan=0.0)
    gy = ndi.sobel(a, axis=0) / 8.0
    gx = ndi.sobel(a, axis=1) / 8.0
    raw_grad = np.hypot(gy, gx).astype(np.float32)
    local_rms = np.sqrt(ndi.uniform_filter(raw_grad ** 2, size=int(agc_window_px), mode="nearest") + 1e-3)
    tmi_agc = (raw_grad / local_rms).astype(np.float32)

    def _z(arr: np.ndarray) -> np.ndarray:
        vals = arr[foot & np.isfinite(arr)]
        if vals.size == 0:
            return np.zeros(arr.shape, dtype=np.float32)
        mu = float(vals.mean())
        sd = float(vals.std())
        if sd <= 0 or not np.isfinite(sd):
            return np.zeros(arr.shape, dtype=np.float32)
        out = (np.nan_to_num(arr, nan=mu) - mu) / sd
        return out.astype(np.float32)

    z_tmi_agc = _z(tmi_agc)
    scarp_keys = ("curv_prof_absmax", "slope_max", "hs_lineament")
    z_scarp = np.mean([_z(np.asarray(scarp_bands[k], dtype=np.float32)) for k in scarp_keys], axis=0).astype(np.float32)
    composite = (0.50 * z_tmi_agc + 0.50 * z_scarp).astype(np.float32)
    return {
        "composite": composite,
        "tmi_raw_grad": raw_grad,
        "tmi_agc_grad": tmi_agc,
        "z_tmi_agc": z_tmi_agc,
        "z_scarp": z_scarp,
    }


def _strike_azimuth_deg(vertices_rc: np.ndarray) -> float:
    """Geological strike azimuth in degrees East of North ``[0, 180)`` from ordered trace vertices."""
    dr = float(vertices_rc[-1, 0] - vertices_rc[0, 0])
    dc = float(vertices_rc[-1, 1] - vertices_rc[0, 1])
    dx_east = dc
    dy_north = -dr
    az = float(np.degrees(np.arctan2(dx_east, dy_north))) % 180.0
    return round(az, 2)


def strike_domain_label(strike_deg: float) -> str:
    """Classify a trace's strike into its Great Basin / Walker Lane structural trend."""
    s = float(strike_deg) % 180.0
    if 10.0 <= s < 45.0:
        return f"N{s:04.1f}E (NNE Basin-and-Range extensional normal-fault trend)"
    if 45.0 <= s < 80.0:
        return f"N{s:04.1f}E (ENE Humboldt / Midas structural-zone trend)"
    if 80.0 <= s <= 105.0:
        return f"N{s:04.1f}E (E-W transfer / accommodation-zone trend)"
    if 105.0 < s <= 145.0:
        w = 180.0 - s
        return f"N{w:04.1f}W (WNW-NW Walker Lane dextral-oblique / transfer trend)"
    if s > 145.0:
        w = 180.0 - s
        return f"N{w:04.1f}W (NNW range-front / intrabasin normal-fault trend)"
    return f"N{s:04.1f}E (N-S Basin-and-Range range-front normal-fault trend)"


def extract_strike_traces(
    dots: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    support_mask: np.ndarray | None = None,
    evidence_field: np.ndarray | None = None,
    min_length_px: float = 10.0,
    max_step_px: float = 7.5,
    max_step_turn_deg: float = 36.0,
    max_axis_dev_deg: float = 22.0,
    min_straightness: float = 0.90,
    max_rms_cross_px: float = 2.0,
    clearance_px: float = NEW_MASS_CLEARANCE_PX,
    min_support_frac: float = 0.75,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract non-branching, strike-consistent >= 1 km polylines built from R0's dots.

    Every vertex is an existing dot in ``dots``, and every pixel along every Bresenham segment
    between consecutive vertices lies inside ``footprint``, off ``catalogue``, at Euclidean
    distance ``> clearance_px`` from ``catalogue``, and (when ``support_mask`` is supplied) has
    at least ``min_support_frac`` of its segment pixels inside the 1-px dilated parent support
    corridor so links never jump across unrelated parallel ridges.
    """
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    dmask = np.asarray(dots, dtype=bool) & foot
    edt_cat = ndi.distance_transform_edt(~cat) if cat.any() else np.full(foot.shape, np.inf, dtype=np.float64)

    if support_mask is not None:
        sup = np.asarray(support_mask, dtype=bool)
        sup_buf1 = ndi.binary_dilation(sup, iterations=1)
    else:
        sup = dmask
        sup_buf1 = np.ones(foot.shape, dtype=bool)

    ev = (np.zeros(foot.shape, dtype=np.float32) if evidence_field is None
          else np.nan_to_num(np.asarray(evidence_field, dtype=np.float32), nan=0.0))

    elig = dmask & ~cat & (edt_cat > float(clearance_px))
    pts = np.argwhere(elig)
    if len(pts) < 2:
        return [], {"n_eligible_dots": int(len(pts)), "n_traces": 0, "n_dots_in_traces": 0}

    ev_pts = ev[pts[:, 0], pts[:, 1]].astype(np.float64)
    tree = cKDTree(pts)
    pairs = sorted(tree.query_pairs(float(max_step_px)))
    nbrs: list[list[tuple[int, float, float, float, float]]] = [[] for _ in range(len(pts))]

    for i, j in pairs:
        ri, ci = int(pts[i, 0]), int(pts[i, 1])
        rj, cj = int(pts[j, 0]), int(pts[j, 1])
        dist = float(np.hypot(rj - ri, cj - ci))
        if dist < 2.0 - 1e-9:
            continue
        rs, cs = bresenham_line(ri, ci, rj, cj)
        if not (foot[rs, cs].all() and not cat[rs, cs].any() and (edt_cat[rs, cs] > float(clearance_px)).all()):
            continue
        if support_mask is not None and float(sup_buf1[rs, cs].mean()) < float(min_support_frac):
            continue
        hf = float(sup[rs, cs].mean())
        nbrs[i].append((j, (rj - ri) / dist, (cj - ci) / dist, dist, hf))
        nbrs[j].append((i, (ri - rj) / dist, (ci - cj) / dist, dist, hf))

    cos_step = float(np.cos(np.deg2rad(max_step_turn_deg)))
    cos_axis = float(np.cos(np.deg2rad(max_axis_dev_deg)))

    def _grow_chain(seed: int, j0: int, ur0: float, uc0: float, used: np.ndarray) -> list[int]:
        chain = [int(seed), int(j0)]
        for forward in (True, False):
            while True:
                cur = chain[-1] if forward else chain[0]
                ref_idx = chain[max(0, len(chain) - 4)] if forward else chain[min(len(chain) - 1, 3)]
                vr = float(pts[cur, 0] - pts[ref_idx, 0])
                vc = float(pts[cur, 1] - pts[ref_idx, 1])
                vn = float(np.hypot(vr, vc))
                ax_r, ax_c = (vr / vn, vc / vn) if vn > 0 else ((ur0, uc0) if forward else (-ur0, -uc0))

                prev_idx = chain[-2] if forward else chain[1]
                sr = float(pts[cur, 0] - pts[prev_idx, 0])
                sc = float(pts[cur, 1] - pts[prev_idx, 1])
                sn = float(np.hypot(sr, sc))
                sr, sc = sr / sn, sc / sn

                best_nxt: int | None = None
                best_key: tuple[float, int, int] | None = None
                for nxt, ur, uc, dist, hf in nbrs[cur]:
                    if used[nxt] or nxt in chain:
                        continue
                    if sr * ur + sc * uc < cos_step:
                        continue
                    c_ax = ax_r * ur + ax_c * uc
                    if c_ax < cos_axis:
                        continue
                    val = round(1.8 * c_ax + 0.5 * hf + 0.25 * float(ev_pts[nxt]) - 0.08 * dist, 9)
                    key = (val, -int(pts[nxt, 0]), -int(pts[nxt, 1]))
                    if best_key is None or key > best_key:
                        best_key = key
                        best_nxt = int(nxt)
                if best_nxt is None:
                    break
                if forward:
                    chain.append(best_nxt)
                else:
                    chain.insert(0, best_nxt)
        return chain

    used = np.zeros(len(pts), dtype=bool)
    seed_order = np.lexsort((pts[:, 1], pts[:, 0], -ev_pts))
    raw_traces: list[dict[str, Any]] = []

    for seed in seed_order:
        s_i = int(seed)
        if used[s_i] or not nbrs[s_i]:
            continue
        best_chain: list[int] | None = None
        best_chord = -1.0
        for j, ur, uc, _d, _hf in nbrs[s_i]:
            if used[j]:
                continue
            ch = _grow_chain(s_i, j, ur, uc, used)
            cpts = pts[ch].astype(np.float64)
            chord = float(np.hypot(cpts[-1, 0] - cpts[0, 0], cpts[-1, 1] - cpts[0, 1]))
            if chord > best_chord:
                best_chord = chord
                best_chain = ch
        if best_chain is None or best_chord < float(min_length_px):
            continue

        cpts = pts[best_chain].astype(np.float64)
        seg_d = np.hypot(np.diff(cpts[:, 0]), np.diff(cpts[:, 1]))
        arc_px = float(seg_d.sum())
        chord_px = float(np.hypot(cpts[-1, 0] - cpts[0, 0], cpts[-1, 1] - cpts[0, 1]))
        straightness = chord_px / max(arc_px, 1e-9)
        pc = cpts - cpts.mean(axis=0)
        eigvals = np.linalg.eigvalsh(pc.T @ pc / max(len(cpts) - 1, 1))
        rms_cross_px = float(np.sqrt(max(float(eigvals[0]), 0.0)))

        if (chord_px < float(min_length_px) or arc_px < float(min_length_px)
                or straightness < float(min_straightness)
                or rms_cross_px > float(max_rms_cross_px)):
            continue

        used[best_chain] = True
        # Canonical endpoint orientation: northernmost endpoint first (smaller row, then smaller col)
        v_rc = pts[best_chain].astype(np.int32)
        if (int(v_rc[-1, 0]), int(v_rc[-1, 1])) < (int(v_rc[0, 0]), int(v_rc[0, 1])):
            v_rc = v_rc[::-1].copy()

        pix_list: list[tuple[int, int]] = []
        seen_px: set[tuple[int, int]] = set()
        for a, b in zip(v_rc[:-1], v_rc[1:]):
            rs, cs = bresenham_line(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
            for r_p, c_p in zip(rs.tolist(), cs.tolist()):
                rc_t = (int(r_p), int(c_p))
                if rc_t not in seen_px:
                    seen_px.add(rc_t)
                    pix_list.append(rc_t)
        pix_rc = np.asarray(pix_list, dtype=np.int32)
        mean_ev = float(ev[v_rc[:, 0], v_rc[:, 1]].mean())
        score = mean_ev + 0.45 * float(np.log(arc_px / max(float(min_length_px), 1.0)))
        strike_deg = _strike_azimuth_deg(v_rc)

        raw_traces.append({
            "vertices_rc": v_rc,
            "pixels_rc": pix_rc,
            "n_r0_dots": int(len(v_rc)),
            "n_raster_pixels": int(len(pix_rc)),
            "arc_length_px": round(arc_px, 4),
            "arc_length_km": round(arc_px * CELL_M / 1000.0, 4),
            "chord_length_px": round(chord_px, 4),
            "chord_length_km": round(chord_px * CELL_M / 1000.0, 4),
            "straightness": round(straightness, 4),
            "rms_cross_m": round(rms_cross_px * CELL_M, 2),
            "strike_deg_e_of_n": strike_deg,
            "strike_label": strike_domain_label(strike_deg),
            "mean_dot_evidence": round(mean_ev, 6),
            "score": round(score, 6),
            "h19_corridor_pct": round(100.0 * float(sup[pix_rc[:, 0], pix_rc[:, 1]].mean()), 2),
            "min_cat_edt_px": round(float(edt_cat[pix_rc[:, 0], pix_rc[:, 1]].min()), 4),
        })

    raw_traces.sort(key=lambda t: (
        -t["score"],
        -t["arc_length_px"],
        int(t["vertices_rc"][0, 0]),
        int(t["vertices_rc"][0, 1]),
    ))
    for idx, tr in enumerate(raw_traces, start=1):
        tr["rank"] = idx
        tr["trace_id"] = f"TB-{idx:04d}"

    stats = {
        "n_eligible_dots": int(len(pts)),
        "n_traces": int(len(raw_traces)),
        "n_dots_in_traces": int(sum(t["n_r0_dots"] for t in raw_traces)),
        "min_length_km": round(min((t["arc_length_km"] for t in raw_traces), default=0.0), 4),
        "mean_length_km": round(float(np.mean([t["arc_length_km"] for t in raw_traces])) if raw_traces else 0.0, 4),
        "max_length_km": round(max((t["arc_length_km"] for t in raw_traces), default=0.0), 4),
        "min_cat_edt_px_all_traces": round(min((t["min_cat_edt_px"] for t in raw_traces), default=0.0), 4),
    }
    return raw_traces, stats


def _nn_min_and_mean(mask: np.ndarray) -> tuple[float, float, int]:
    pts = np.argwhere(mask)
    if len(pts) < 2:
        return (float("inf"), float("inf"), 0)
    d = cKDTree(pts).query(pts, k=2)[0][:, 1]
    return (float(d.min()), float(d.mean()), int((d < KERNEL_R_PX - 1e-9).sum()))


def build_cull_singletons(
    parent: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    link_radius_px: float = SINGLETON_LINK_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Variant 1 (``cull1dot``): delete unlinked 1-dot singletons, keep every chain & >= 1 km trace."""
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    p = np.asarray(parent, dtype=bool) & foot
    sing, sing_stats = isolated_singletons(p, foot, link_radius_px=link_radius_px)
    out = p & ~sing
    edt_cat = ndi.distance_transform_edt(~cat) if cat.any() else np.full(foot.shape, np.inf)
    p_min, p_mean, p_subk = _nn_min_and_mean(p)
    v_min, v_mean, v_subk = _nn_min_and_mean(out)
    removed = int((p & ~out).sum())
    return out, {
        "axis": "TRACKB",
        "value": "cull1dot",
        "rule": (f"Delete every isolated 1-dot singleton in R0 (zero R0 neighbours within "
                 f"{link_radius_px * CELL_M:.0f} m = {link_radius_px} px); all multi-dot chains "
                 f"and all >= 1 km strike-consistent traces remain 100 % intact; no tie-break."),
        "singleton_stats": sing_stats,
        "n_dots_parent": int(p.sum()),
        "n_dots_variant": int(out.sum()),
        "removed": removed,
        "added": 0,
        "dots_changed": removed,
        "pct_changed": round(100.0 * removed / max(int(p.sum()), 1), 4),
        "nn_min_px_before_after": [round(p_min, 4), round(v_min, 4)],
        "nn_mean_px_before_after": [round(p_mean, 4), round(v_mean, 4)],
        "sub_kernel_dots_before_after": [p_subk, v_subk],
        "min_cat_edt_variant_px": round(float(edt_cat[out].min()), 4) if out.any() else None,
    }


def _trace_bridge_and_tip_candidates(
    traces: list[dict[str, Any]],
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    support_mask: np.ndarray | None,
    evidence: np.ndarray,
    min_spacing_px: float = PARENT_MIN_SPACING_PX,
    clearance_px: float = NEW_MASS_CLEARANCE_PX,
) -> list[tuple[float, int, int, str]]:
    """Deterministic priority list of internal >300 m gap-bridges then collinear tip steps."""
    h, w = footprint.shape
    sup_buf = (ndi.binary_dilation(np.asarray(support_mask, dtype=bool), iterations=1)
               if support_mask is not None else np.ones((h, w), dtype=bool))
    mid_cands: list[tuple[float, int, int, str]] = []
    tip_cands: list[tuple[float, int, int, str]] = []

    for tr in traces:
        sc = float(tr["score"])
        v_rc = tr["vertices_rc"]
        # 1. Internal gaps large enough (>= 2 * min_spacing_px) to fit a kernel-spaced bridge dot
        for a, b in zip(v_rc[:-1], v_rc[1:]):
            seg_len = float(np.hypot(b[0] - a[0], b[1] - a[1]))
            if seg_len < 2.0 * min_spacing_px - 0.15:
                continue
            rs, cs = bresenham_line(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
            mid_idx = len(rs) // 2
            for idx in (mid_idx, max(0, mid_idx - 1), min(len(rs) - 1, mid_idx + 1)):
                mr, mc = int(rs[idx]), int(cs[idx])
                if 0 <= mr < h and 0 <= mc < w and footprint[mr, mc] and edt_cat[mr, mc] > clearance_px:
                    prio = 100.0 + sc + 0.25 * float(evidence[mr, mc]) + 0.5 * float(sup_buf[mr, mc])
                    mid_cands.append((prio, mr, mc, "internal_bridge"))

        # 2. Collinear tip extensions (1 or 2 kernel steps along terminal strike vector)
        n_v = len(v_rc)
        ends = (
            (v_rc[-1], v_rc[max(0, n_v - 4)]),
            (v_rc[0], v_rc[min(n_v - 1, 3)]),
        )
        for end_pt, ref_pt in ends:
            vr = float(end_pt[0] - ref_pt[0])
            vc = float(end_pt[1] - ref_pt[1])
            vn = float(np.hypot(vr, vc))
            if vn <= 0:
                continue
            ur, uc = vr / vn, vc / vn
            for step in (3.2, 6.4):
                for lat in (0.0, -1.0, 1.0):
                    tr_r = int(round(float(end_pt[0]) + step * ur - lat * uc))
                    tr_c = int(round(float(end_pt[1]) + step * uc + lat * ur))
                    if (0 <= tr_r < h and 0 <= tr_c < w
                            and footprint[tr_r, tr_c]
                            and edt_cat[tr_r, tr_c] > clearance_px):
                        prio = (sc - 0.12 * step - 0.15 * abs(lat)
                                + 0.25 * float(evidence[tr_r, tr_c])
                                + 0.60 * float(sup_buf[tr_r, tr_c]))
                        tip_cands.append((prio, tr_r, tr_c, "tip_extension"))

    all_cands = mid_cands + tip_cands
    all_cands.sort(key=lambda item: (-round(item[0], 8), item[1], item[2]))
    deduped: list[tuple[float, int, int, str]] = []
    seen: set[tuple[int, int]] = set()
    for prio, r, c, kind in all_cands:
        if (r, c) not in seen:
            seen.add((r, c))
            deduped.append((prio, r, c, kind))
    return deduped


def _has_close_neighbour(occ: np.ndarray, r: int, c: int, min_dist: float) -> bool:
    rad = int(np.ceil(min_dist))
    r0, r1 = max(0, r - rad), min(occ.shape[0], r + rad + 1)
    c0, c1 = max(0, c - rad), min(occ.shape[1], c + rad + 1)
    win = occ[r0:r1, c0:c1]
    if not win.any():
        return False
    rr, cc = np.nonzero(win)
    return bool(np.hypot(rr + r0 - r, cc + c0 - c).min() < min_dist - 1e-9)


def build_bridge_traces(
    parent: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    traces: list[dict[str, Any]],
    evidence_field: np.ndarray,
    support_mask: np.ndarray | None = None,
    link_radius_px: float = SINGLETON_LINK_PX,
    min_spacing_px: float = PARENT_MIN_SPACING_PX,
    clearance_px: float = NEW_MASS_CLEARANCE_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Variant 2 (``bridge1km``): count-fixed reallocation of singletons onto >= 1 km traces.

    Preserves total count ``== parent.sum()`` by construction (vacate one singleton, place one
    trace-bridge or collinear tip dot at spacing ``>= min_spacing_px`` and ``edt_cat > clearance_px``;
    if no legal trace slot remains, restore the singleton).
    """
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    p = np.asarray(parent, dtype=bool) & foot
    ev = np.nan_to_num(np.asarray(evidence_field, dtype=np.float32), nan=0.0)
    edt_cat = ndi.distance_transform_edt(~cat) if cat.any() else np.full(foot.shape, np.inf)

    sing_mask, sing_stats = isolated_singletons(p, foot, link_radius_px=link_radius_px)
    s_pts = np.argwhere(sing_mask)
    s_ev = ev[s_pts[:, 0], s_pts[:, 1]]
    s_order = np.lexsort((s_pts[:, 1], s_pts[:, 0], s_ev))  # weakest-evidence singleton first

    cands = _trace_bridge_and_tip_candidates(
        traces, foot, edt_cat, support_mask, ev,
        min_spacing_px=min_spacing_px, clearance_px=clearance_px,
    )

    occ = p.copy()
    cand_cursor = 0
    n_bridge = 0
    n_tip = 0
    n_restored = 0
    displacements: list[float] = []

    for idx in s_order:
        sr, sc = int(s_pts[idx, 0]), int(s_pts[idx, 1])
        occ[sr, sc] = False
        placed = False
        while cand_cursor < len(cands):
            _prio, tr, tc, kind = cands[cand_cursor]
            cand_cursor += 1
            if occ[tr, tc]:
                continue
            if not foot[tr, tc] or cat[tr, tc] or edt_cat[tr, tc] <= clearance_px:
                continue
            if _has_close_neighbour(occ, tr, tc, min_spacing_px):
                continue
            occ[tr, tc] = True
            placed = True
            if kind == "internal_bridge":
                n_bridge += 1
            else:
                n_tip += 1
            displacements.append(float(np.hypot(tr - sr, tc - sc)))
            break
        if not placed:
            occ[sr, sc] = True
            n_restored += 1

    removed = int((p & ~occ).sum())
    added = int((occ & ~p).sum())
    changed = removed + added
    p_min, p_mean, p_subk = _nn_min_and_mean(p)
    v_min, v_mean, v_subk = _nn_min_and_mean(occ)
    new_cells = occ & ~p
    sup_pct = (round(100.0 * float(np.asarray(support_mask, dtype=bool)[new_cells].mean()), 2)
               if support_mask is not None and new_cells.any() else None)

    return occ, {
        "axis": "TRACKB",
        "value": "bridge1km",
        "rule": (f"Count-fixed reallocation of R0's isolated 1-dot singletons into internal "
                 f">300 m kernel blind-spot midpoints first, then collinear 320 m/640 m tip "
                 f"extensions of R0's >= 1 km strike-consistent traces; spacing >= "
                 f"{min_spacing_px:.4f} px and catalogue clearance > {clearance_px:.1f} px held."),
        "singleton_stats": sing_stats,
        "n_dots_parent": int(p.sum()),
        "n_dots_variant": int(occ.sum()),
        "removed": removed,
        "added": added,
        "placed_internal_bridges": n_bridge,
        "placed_tip_extensions": n_tip,
        "singletons_restored_unplaced": n_restored,
        "dots_changed": changed,
        "pct_changed": round(100.0 * changed / max(int(p.sum()), 1), 4),
        "mean_relocation_km": round(float(np.mean(displacements)) * CELL_M / 1000.0, 3) if displacements else 0.0,
        "nn_min_px_before_after": [round(p_min, 4), round(v_min, 4)],
        "nn_mean_px_before_after": [round(p_mean, 4), round(v_mean, 4)],
        "sub_kernel_dots_before_after": [p_subk, v_subk],
        "new_mass_on_h19_support_pct": sup_pct,
        "min_cat_edt_new_mass_px": round(float(edt_cat[new_cells].min()), 4) if new_cells.any() else None,
        "min_cat_edt_variant_px": round(float(edt_cat[occ].min()), 4) if occ.any() else None,
    }


def build_render_top_traces(
    parent: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    traces: list[dict[str, Any]],
    evidence_field: np.ndarray,
    top_k: int = 120,
    link_radius_px: float = SINGLETON_LINK_PX,
    clearance_px: float = NEW_MASS_CLEARANCE_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Variant 3 (``rendertop120``): render top-K GeoJSON >=1 km traces as continuous 100 m lines.

    Every Bresenham pixel along the top-K traces (all verified > 3.0 px off catalogue) is emitted,
    and the added connector pixel count is funded 1-for-1 by deleting the weakest-evidence isolated
    non-trace speckles so total emitted mass stays fixed at ``parent.sum()``.
    """
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    p = np.asarray(parent, dtype=bool) & foot
    ev = np.nan_to_num(np.asarray(evidence_field, dtype=np.float32), nan=0.0)
    edt_cat = ndi.distance_transform_edt(~cat) if cat.any() else np.full(foot.shape, np.inf)

    selected_traces = traces[: int(top_k)]
    line_mask = np.zeros_like(p)
    ordered_connectors: list[tuple[int, int]] = []
    seen_conn: set[tuple[int, int]] = set()
    for tr in selected_traces:
        px = tr["pixels_rc"]
        for r, c in px:
            rr, cc = int(r), int(c)
            if foot[rr, cc] and not cat[rr, cc] and edt_cat[rr, cc] > clearance_px:
                line_mask[rr, cc] = True
                if not p[rr, cc] and (rr, cc) not in seen_conn:
                    seen_conn.add((rr, cc))
                    ordered_connectors.append((rr, cc))

    # Removable pool: isolated singletons first, then <=2-dot speckles outside the rendered traces
    sing_mask, sing_stats = isolated_singletons(p, foot, link_radius_px=link_radius_px)
    pts_all = np.argwhere(p)
    if len(pts_all):
        adj = cKDTree(pts_all).sparse_distance_matrix(cKDTree(pts_all), max_distance=float(link_radius_px),
                                                      output_type="coo_matrix")
        _, comp = connected_components(adj, directed=False)
        csz = np.bincount(comp)[comp]
        pair_mask = np.zeros_like(p)
        pair_pts = pts_all[csz == 2]
        if len(pair_pts):
            pair_mask[pair_pts[:, 0], pair_pts[:, 1]] = True
    else:
        pair_mask = np.zeros_like(p)

    pool_sing = np.argwhere(sing_mask & ~line_mask)
    order_s = np.lexsort((pool_sing[:, 1], pool_sing[:, 0], ev[pool_sing[:, 0], pool_sing[:, 1]])) if len(pool_sing) else np.array([], dtype=int)
    pool_pair = np.argwhere(pair_mask & ~line_mask)
    order_p = np.lexsort((pool_pair[:, 1], pool_pair[:, 0], ev[pool_pair[:, 0], pool_pair[:, 1]])) if len(pool_pair) else np.array([], dtype=int)

    removable = [tuple(map(int, pool_sing[i])) for i in order_s] + [tuple(map(int, pool_pair[i])) for i in order_p]
    n_swap = min(len(ordered_connectors), len(removable))

    out = p.copy()
    for rr, cc in removable[:n_swap]:
        out[rr, cc] = False
    for rr, cc in ordered_connectors[:n_swap]:
        out[rr, cc] = True

    removed = int((p & ~out).sum())
    added = int((out & ~p).sum())
    changed = removed + added
    p_min, p_mean, p_subk = _nn_min_and_mean(p)
    v_min, v_mean, v_subk = _nn_min_and_mean(out)
    new_cells = out & ~p
    fully_rendered = sum(
        1 for tr in selected_traces
        if bool(out[tr["pixels_rc"][:, 0], tr["pixels_rc"][:, 1]].all())
    )

    return out, {
        "axis": "TRACKB",
        "value": f"rendertop{int(top_k)}",
        "rule": (f"Rasterise the top-{int(top_k)} GeoJSON >= 1 km strike-consistent traces as "
                 f"unbroken 8-connected 100 m polylines (every pixel > {clearance_px:.1f} px off "
                 f"catalogue), compensated 1-for-1 by removing weakest isolated speckles so total "
                 f"count stays fixed at {int(p.sum())}."),
        "top_k_requested": int(top_k),
        "traces_selected": len(selected_traces),
        "traces_fully_connected_in_raster": int(fully_rendered),
        "trace_r0_vertex_dots": int(sum(t["n_r0_dots"] for t in selected_traces)),
        "trace_total_line_pixels": int(line_mask.sum()),
        "singleton_stats": sing_stats,
        "n_dots_parent": int(p.sum()),
        "n_dots_variant": int(out.sum()),
        "removed": removed,
        "added": added,
        "dots_changed": changed,
        "pct_changed": round(100.0 * changed / max(int(p.sum()), 1), 4),
        "nn_min_px_before_after": [round(p_min, 4), round(v_min, 4)],
        "nn_mean_px_before_after": [round(p_mean, 4), round(v_mean, 4)],
        "sub_kernel_dots_before_after": [p_subk, v_subk],
        "min_cat_edt_new_mass_px": round(float(edt_cat[new_cells].min()), 4) if new_cells.any() else None,
        "min_cat_edt_variant_px": round(float(edt_cat[out].min()), 4) if out.any() else None,
    }


def build_random_singleton_control(
    parent: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    evidence_field: np.ndarray,
    n_relocate: int,
    link_radius_px: float = SINGLETON_LINK_PX,
    min_spacing_px: float = PARENT_MIN_SPACING_PX,
    clearance_px: float = NEW_MASS_CLEARANCE_PX,
    seed: int = 20261023,
) -> tuple[np.ndarray, dict[str, Any]]:
    """In-memory null control: relocate the same ``n_relocate`` singletons to random eligible cells."""
    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    p = np.asarray(parent, dtype=bool) & foot
    ev = np.nan_to_num(np.asarray(evidence_field, dtype=np.float32), nan=0.0)
    edt_cat = ndi.distance_transform_edt(~cat) if cat.any() else np.full(foot.shape, np.inf)

    sing_mask, _ = isolated_singletons(p, foot, link_radius_px=link_radius_px)
    s_pts = np.argwhere(sing_mask)
    s_order = np.lexsort((s_pts[:, 1], s_pts[:, 0], ev[s_pts[:, 0], s_pts[:, 1]]))
    chosen = s_pts[s_order[: int(n_relocate)]]

    occ = p.copy()
    for sr, sc in chosen:
        occ[int(sr), int(sc)] = False

    elig = foot & ~cat & (edt_cat > clearance_px) & ~occ
    elig_pts = np.argwhere(elig)
    rng = np.random.default_rng(int(seed))
    perm = rng.permutation(len(elig_pts))
    placed = 0
    cursor = 0
    for sr, sc in chosen:
        ok = False
        while cursor < len(perm):
            er, ec = int(elig_pts[perm[cursor], 0]), int(elig_pts[perm[cursor], 1])
            cursor += 1
            if occ[er, ec] or _has_close_neighbour(occ, er, ec, min_spacing_px):
                continue
            occ[er, ec] = True
            placed += 1
            ok = True
            break
        if not ok:
            occ[int(sr), int(sc)] = True
    return occ, {"n_dots": int(occ.sum()), "relocated": placed}


def _percentile_lookup(field: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Return sorted finite in-footprint sample values for fast exact percentile reporting."""
    v = np.asarray(field, dtype=np.float64)[valid & np.isfinite(field)]
    if v.size == 0:
        return np.array([0.0], dtype=np.float64)
    if v.size > 250_000:
        step = max(1, v.size // 250_000)
        v = v[::step]
    return np.sort(v)


def _pct_of(val: float, sorted_ref: np.ndarray) -> float:
    if not np.isfinite(val) or sorted_ref.size == 0:
        return 50.0
    idx = int(np.searchsorted(sorted_ref, val, side="right"))
    return round(100.0 * idx / sorted_ref.size, 1)


def _cardinal_normal_label(nr_row: float, nc_col: float) -> str:
    dx_e = float(nc_col)
    dy_n = float(-nr_row)
    ang = float(np.degrees(np.arctan2(dx_e, dy_n))) % 360.0
    dirs = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    return dirs[int(round(ang / 22.5)) % 16]


def annotate_traces_for_geologist(
    traces: list[dict[str, Any]],
    transform: Any,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    ev_pack: dict[str, np.ndarray],
    scarp_bands: dict[str, np.ndarray],
    zmean_m: np.ndarray,
    ksn_m09: np.ndarray,
    rad_k_u8: np.ndarray,
    thk_u8: np.ndarray,
    road_dist_m: np.ndarray,
    rendered_variant_id: str,
) -> dict[str, Any]:
    """Build RFC 7946 GeoJSON FeatureCollection + 1 structural-geologist paragraph per trace."""
    from rasterio.warp import transform as warp_transform

    foot = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    edt_cat_m = ndi.distance_transform_edt(~cat) * CELL_M
    h, w = foot.shape

    ref_tmi_agc = _percentile_lookup(ev_pack["tmi_agc_grad"], foot)
    ref_tmi_raw = _percentile_lookup(ev_pack["tmi_raw_grad"], foot)
    ref_scarp = _percentile_lookup(ev_pack["z_scarp"], foot)
    ref_ksn = _percentile_lookup(ksn_m09, foot & np.isfinite(ksn_m09) & (ksn_m09 > 0))

    features: list[dict[str, Any]] = []
    for tr in traces:
        v_rc = tr["vertices_rc"]
        px_rc = tr["pixels_rc"]
        rows_f = v_rc[:, 0].astype(np.float64) + 0.5
        cols_f = v_rc[:, 1].astype(np.float64) + 0.5
        xs_utm = float(transform.c) + cols_f * float(transform.a)
        ys_utm = float(transform.f) + rows_f * float(transform.e)
        lons, lats = warp_transform("EPSG:32611", "EPSG:4326", xs_utm.tolist(), ys_utm.tolist())
        coords_lonlat = [[round(float(lon), 6), round(float(lat), 6)] for lon, lat in zip(lons, lats)]

        mr, mc = float(px_rc[:, 0].mean()), float(px_rc[:, 1].mean())
        quad = ("NW" if mr < h / 2 and mc < w / 2 else
                "NE" if mr < h / 2 else
                "SW" if mc < w / 2 else "SE")

        # Unit tangent and cross-strike normal (+/- 5 px = +/- 500 m flank sampling)
        vr = float(v_rc[-1, 0] - v_rc[0, 0])
        vc = float(v_rc[-1, 1] - v_rc[0, 1])
        vn = max(float(np.hypot(vr, vc)), 1e-9)
        nr, nc = -vc / vn, vr / vn  # perpendicular normal vector in (row, col)

        pos_r = np.clip(np.rint(px_rc[:, 0] + 5.0 * nr).astype(int), 0, h - 1)
        pos_c = np.clip(np.rint(px_rc[:, 1] + 5.0 * nc).astype(int), 0, w - 1)
        neg_r = np.clip(np.rint(px_rc[:, 0] - 5.0 * nr).astype(int), 0, h - 1)
        neg_c = np.clip(np.rint(px_rc[:, 1] - 5.0 * nc).astype(int), 0, w - 1)

        z_trace = zmean_m[px_rc[:, 0], px_rc[:, 1]]
        elev_m = float(np.nanmean(z_trace)) if np.isfinite(z_trace).any() else float("nan")
        z_pos = zmean_m[pos_r, pos_c]
        z_neg = zmean_m[neg_r, neg_c]
        if not (np.isfinite(z_pos).any() and np.isfinite(z_neg).any()):
            # Footprint-edge trace: fall back to +/-200 m cross-strike flank step
            p2_r = np.clip(np.rint(px_rc[:, 0] + 2.0 * nr).astype(int), 0, h - 1)
            p2_c = np.clip(np.rint(px_rc[:, 1] + 2.0 * nc).astype(int), 0, w - 1)
            n2_r = np.clip(np.rint(px_rc[:, 0] - 2.0 * nr).astype(int), 0, h - 1)
            n2_c = np.clip(np.rint(px_rc[:, 1] - 2.0 * nc).astype(int), 0, w - 1)
            z_pos = zmean_m[p2_r, p2_c]
            z_neg = zmean_m[n2_r, n2_c]
        if np.isfinite(z_pos).any() and np.isfinite(z_neg).any():
            dz = float(np.nanmean(z_pos) - np.nanmean(z_neg))
            down_dir = _cardinal_normal_label(nr, nc) if dz < 0 else _cardinal_normal_label(-nr, -nc)
            throw_m = round(abs(dz), 1)
        else:
            down_dir = "survey-margin"
            throw_m = 0.0

        k_pos = rad_k_u8[pos_r, pos_c].astype(np.float64)
        k_neg = rad_k_u8[neg_r, neg_c].astype(np.float64)
        k_valid = (k_pos > 0) & (k_neg > 0)
        rad_k_step = round(float(np.abs(k_pos[k_valid] - k_neg[k_valid]).mean()), 1) if k_valid.any() else 0.0

        thk_vals = thk_u8[px_rc[:, 0], px_rc[:, 1]]
        thk_med = round(float(np.median(thk_vals[thk_vals > 0])), 1) if (thk_vals > 0).any() else 0.0

        tmi_agc_val = float(ev_pack["tmi_agc_grad"][px_rc[:, 0], pix_c := px_rc[:, 1]].mean())
        tmi_raw_val = float(ev_pack["tmi_raw_grad"][px_rc[:, 0], pix_c].mean())
        scarp_val = float(ev_pack["z_scarp"][px_rc[:, 0], pix_c].mean())
        tmi_agc_pct = _pct_of(tmi_agc_val, ref_tmi_agc)
        tmi_raw_pct = _pct_of(tmi_raw_val, ref_tmi_raw)
        scarp_pct = _pct_of(scarp_val, ref_scarp)

        slope_vals = scarp_bands["slope_max"][px_rc[:, 0], pix_c]
        slope_deg = round(float(np.nanmean(slope_vals)), 1) if np.isfinite(slope_vals).any() else 0.0

        ksn_vals = ksn_m09[px_rc[:, 0], pix_c]
        ksn_fin = ksn_vals[np.isfinite(ksn_vals) & (ksn_vals > 0)]
        ksn_pct = _pct_of(float(ksn_fin.mean()), ref_ksn) if ksn_fin.size else 50.0

        cat_min_m = round(float(edt_cat_m[px_rc[:, 0], pix_c].min()), 0)
        cat_med_km = round(float(np.median(edt_cat_m[px_rc[:, 0], pix_c])) / 1000.0, 2)

        rd_vals = road_dist_m[px_rc[:, 0], pix_c]
        rd_min_m = round(float(np.nanmin(rd_vals)), 0) if np.isfinite(rd_vals).any() else 9999.0
        rd_med_m = round(float(np.nanmedian(rd_vals)), 0) if np.isfinite(rd_vals).any() else 9999.0

        # Non-fault mimic triage tailored to this trace's measured setting
        mimics: list[str] = []
        if rd_med_m < 200.0:
            mimics.append(f"strike-parallel road/rail grade alignment (median TIGER road distance {rd_med_m:.0f} m)")
        if tmi_raw_pct >= 90.0 and slope_deg < 8.0:
            mimics.append("buried volcanic flow margin or mafic feeder dike in low-relief cover")
        if np.isfinite(elev_m) and elev_m < 1360.0 and slope_deg < 12.0:
            mimics.append("Pleistocene Lake Lahontan wave-cut shoreline or beach ridge (<1,360 m pluvial highstand)")
        if slope_deg >= 18.0 and tmi_agc_pct < 65.0:
            mimics.append("resistant ash-flow tuff hogback or non-tectonic erosional canyon wall")
        if not mimics:
            mimics.append("dip-panel lithologic contact or inactive Tertiary basement step beveled by pedimentation")
        mimic_summary = "; ".join(mimics)

        setting = ("basin-floor / playa-margin" if np.isfinite(elev_m) and elev_m < 1350.0 else
                   "piedmont / bajada-range-front transition" if np.isfinite(elev_m) and elev_m < 1750.0 else
                   "upland range-block / horst flank")

        paragraph = (
            f"Trace {tr['trace_id']} (rank {tr['rank']}/{len(traces)}, {quad} quadrant, centroid "
            f"{coords_lonlat[len(coords_lonlat)//2][1]:.4f}N {abs(coords_lonlat[len(coords_lonlat)//2][0]):.4f}W / "
            f"UTM 11N {int(round(xs_utm.mean()))}E {int(round(ys_utm.mean()))}N) is a "
            f"{tr['arc_length_km']:.2f} km strike-consistent candidate fault trace "
            f"(chord {tr['chord_length_km']:.2f} km, straightness {tr['straightness']:.3f}, "
            f"cross-strike RMS {tr['rms_cross_m']:.0f} m) oriented {tr['strike_label']}, linking "
            f"{tr['n_r0_dots']} parent R0 dots across {tr['n_raster_pixels']} connected 100 m cells "
            f"({tr['h19_corridor_pct']:.0f}% on the pinned H19-5 multiline ridge corridor). "
            f"In a {setting} setting at {elev_m:.0f} m mean elevation, cross-strike 3DEP "
            f"topography indicates an apparent {down_dir}-down relief step of {throw_m:.1f} m "
            f"(mean maximum scarp slope {slope_deg:.1f} deg, 3DEP scarp composite {scarp_pct:.1f}th "
            f"footprint percentile; drainage steepness ksn {ksn_pct:.1f}th percentile), paired with "
            f"a {tmi_agc_pct:.1f}th-percentile susceptibility-normalised GeoDAWN TMI_up150 contact "
            f"gradient (raw gradient {tmi_raw_pct:.1f}th percentile; cross-strike gamma-ray K rank "
            f"contrast {rad_k_step:.1f}, median Th/K rank {thk_med:.0f}). "
            f"The entire polyline clears mapped USGS/INGENIOUS faults by at least {cat_min_m:.0f} m "
            f"(median fault distance {cat_med_km:.2f} km; median TIGER road distance {rd_med_m:.0f} m, "
            f"min crossing {rd_min_m:.0f} m); a reviewing geologist should verify displacement "
            f"continuity on 1 m lidar/orthoimagery against the primary non-fault mimic risk: {mimic_summary}."
        )

        features.append({
            "type": "Feature",
            "id": tr["trace_id"],
            "geometry": {
                "type": "LineString",
                "coordinates": coords_lonlat,
            },
            "properties": {
                "trace_id": tr["trace_id"],
                "rank": tr["rank"],
                "parent": "h33-h33-2-b2",
                "quadrant": quad,
                "crs_native": "EPSG:32611",
                "utm_start_m": [round(float(xs_utm[0]), 1), round(float(ys_utm[0]), 1)],
                "utm_end_m": [round(float(xs_utm[-1]), 1), round(float(ys_utm[-1]), 1)],
                "arc_length_km": tr["arc_length_km"],
                "chord_length_km": tr["chord_length_km"],
                "straightness": tr["straightness"],
                "rms_cross_m": tr["rms_cross_m"],
                "strike_deg_e_of_n": tr["strike_deg_e_of_n"],
                "strike_label": tr["strike_label"],
                "n_r0_dots": tr["n_r0_dots"],
                "n_raster_pixels": tr["n_raster_pixels"],
                "h19_corridor_pct": tr["h19_corridor_pct"],
                "score": tr["score"],
                "tmi_agc_gradient_pct": tmi_agc_pct,
                "tmi_raw_gradient_pct": tmi_raw_pct,
                "dem10_scarp_pct": scarp_pct,
                "dem10_slope_max_deg": slope_deg,
                "fluvial_ksn_pct": ksn_pct,
                "mean_elevation_m": round(elev_m, 1) if np.isfinite(elev_m) else None,
                "apparent_downthrown_flank": down_dir,
                "cross_strike_relief_step_m": throw_m,
                "cross_strike_rad_k_rank_diff": rad_k_step,
                "min_catalogue_clearance_m": cat_min_m,
                "median_catalogue_distance_km": cat_med_km,
                "nearest_tiger_road_m": rd_min_m,
                "median_tiger_road_m": rd_med_m,
                "primary_mimic_risk": mimic_summary,
                "rendered_in_variant": rendered_variant_id,
                "evidence_paragraph": paragraph,
            },
        })

    return {
        "type": "FeatureCollection",
        "name": "gems86_r0_trackb_strike_traces_ge1km",
        "metadata": {
            "parent": "h33-h33-2-b2",
            "parent_sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
            "axis": "TRACKB",
            "phase": "Phase 2 geologist trace review (not a weekly-slot candidate unless human decides)",
            "crs_coordinates": "OGC:CRS84 (WGS84 longitude, latitude in degrees per RFC 7946)",
            "crs_native_grid": "EPSG:32611 (100 m GeoDAWN competition grid)",
            "n_traces": len(features),
            "min_trace_length_km": min((f["properties"]["arc_length_km"] for f in features), default=0.0),
            "max_trace_length_km": max((f["properties"]["arc_length_km"] for f in features), default=0.0),
            "min_catalogue_clearance_m": min((f["properties"]["min_catalogue_clearance_m"] for f in features), default=0.0),
            "external_sources": [
                {"name": "USGS GeoDAWN airborne magnetic and radiometric survey",
                 "url": "https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7",
                 "doi": "10.5066/P93LGLVQ", "license": "USGS public domain (CC0)"},
                {"name": "USGS 3D Elevation Program (3DEP) 10 m DEM derivatives",
                 "url": "https://www.usgs.gov/3d-elevation-program",
                 "license": "USGS public domain"},
                {"name": "US Census TIGER/Line road distance (mimic audit only)",
                 "url": "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html",
                 "license": "US Government public domain"},
            ],
        },
        "features": features,
    }
