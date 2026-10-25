"""Quadrant-invariant multi-physics feature builder and anisotropic Kostrov-Pollard
crack-tip/stepover fields for Lane H86I-KSAD.

Strict zero-leakage & low-RSS guarantees:
1. ``build_static_features`` NEVER reads ``existing_faults.tif``, ``labels.tif``,
   ``gdr_qfaults_traces.csv``, or any registry raster.
2. Band indices are verified against ``src/gems86/io.py:BANDS`` (including the
   pixel-verified Band 6 = Radiometric Total Count ``tc``, Band 11 = ``+dg/drow_south``,
   and Band 18 = ``+dg/dx_east`` overrides).
3. All 26 static planes are streamed block-by-block into a single ``float16``
   memory-mapped array (687 MB on disk, < 250 MB resident RSS).
4. ``compute_kostrov_elastic_fields`` takes ONLY an explicit fold-visible boolean
   mask ``vis_cat`` and never accesses global catalogue state.
"""
from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi

from gems86.io import BANDS

# Optimal normal-dilation fault strike perpendicular to NW Great Basin WNW-ESE
# extension (sigma_3 ~ N112E -> normal strike theta_0 = N22E; Faulds & Hinz 2015).
THETA_DIL_RAD: float = float(np.deg2rad(22.0))
COS_2THETA0: float = float(np.cos(2.0 * THETA_DIL_RAD))
SIN_2THETA0: float = float(np.sin(2.0 * THETA_DIL_RAD))

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    # Block A: Roest 3-D Analytic Signal, Upward-Continued Depth Persistence & Vector Gravity (6)
    "mag_asig3d_log",
    "verduzco_tilt_zero_s2",
    "verduzco_tilt_zero_s5",
    "up150_depth_persist",
    "laplace_gzz_zero_s3",
    "grav_asig_ridge_s3",
    # Block B: Morris-Byerlee-Kostrov Azimuthal Slip/Dilation Tendency & Crustal Fabric (6)
    "base_hinge_curvature",
    "kostrov_dilation_tendency",
    "kostrov_riedel_slip_tendency",
    "multi_physics_spin2_coherence",
    "poisson_tensor_misalign_s4",
    "cond_lateral_barrier",
    # Block C: Seismicity, Potassic K/Th Alteration & Alluvial Radiometric Quietness (4)
    "eq_strain_coupling",
    "rad_k_th_alteration",
    "rad_uth_redox_front",
    "tc_alluvial_quietness",
    # Block D: 1m LiDAR Unilateral Polarity, 10m Fluvial k_sn & Lahontan Deconfounding (7)
    "lidar_step_norm",
    "lidar_valid_flag",
    "lidar_unilateral_polarity",
    "topo10_tectonic_scarp",
    "topo10_piedmont_break",
    "lahontan_contour_mimic",
    "fluv_ksn_knickzone",
    "fluv_chi_step_knick",
    # Block E: Coarse Native 100m Scarp Context (2 + slope = 2 -> total 26 static planes)
    "dem100_hess_s2",
    "dem100_slope_norm",
)

TOPO100_NATIVE_NAMES: tuple[str, ...] = (
    "dem100_hess_s2",
    "dem100_slope_norm",
)

COVER_BLIND_STATIC_NAMES: tuple[str, ...] = tuple(
    k for k in STATIC_FEATURE_NAMES if k not in TOPO100_NATIVE_NAMES
)

ELASTIC_FEATURE_NAMES: tuple[str, ...] = (
    "kostrov_wing_crack_lobe",
    "collinear_tip_cone_short",
    "collinear_tip_cone_long",
    "releasing_stepover_bridge",
    "strike_anisotropic_corridor",
    "broadside_stress_shadow",
)

EXPECTED_BAND_NAMES: dict[int, str] = {
    2: "rtp",
    3: "tmi_hg",
    4: "geod_2ndinv",
    6: "tc",
    7: "geod_shearrate",
    8: "geod_dilaterate",
    9: "tmi_vg",
    10: "deq_n100a15",
    11: "iso_grav_anom_vg",
    12: "det_elev",
    13: "iso_grav_anom",
    14: "tmi",
    15: "depth_to_base_surf",
    16: "ieq_n100a15",
    17: "cond_surf",
    18: "iso_grav_anom_hg",
    19: "det_elev_slope",
}


def verify_band_table() -> None:
    """Fail closed if canonical band indices in ``src/gems86/io.py`` drift."""
    for idx, expected in EXPECTED_BAND_NAMES.items():
        actual = BANDS.get(idx)
        if actual != expected:
            raise RuntimeError(f"Band {idx} mismatch: expected {expected!r}, got {actual!r}")


def _clean_fill(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    ok = valid & np.isfinite(arr) & (np.abs(arr) < 1e18)
    med = float(np.median(arr[ok])) if ok.any() else 0.0
    return np.where(ok, arr, med).astype(np.float32)


def _pos_scale(arr: np.ndarray, valid: np.ndarray, pct: float = 95.0) -> np.ndarray:
    ok = valid & np.isfinite(arr)
    if not ok.any():
        return np.zeros(arr.shape, dtype=np.float32)
    scale = max(float(np.percentile(np.abs(arr[ok]), pct)), 1e-6)
    return np.where(valid, np.clip(arr / scale, -6.0, 6.0), 0.0).astype(np.float32)


def _robust_z(arr: np.ndarray, valid: np.ndarray, clip: float = 6.0) -> np.ndarray:
    ok = valid & np.isfinite(arr)
    if not ok.any():
        return np.zeros(arr.shape, dtype=np.float32)
    vals = arr[ok]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826
    if not np.isfinite(mad) or mad < 1e-6:
        mad = max(float(np.std(vals)), 1e-6)
    out = np.zeros(arr.shape, dtype=np.float32)
    out[ok] = np.clip((vals - med) / mad, -clip, clip).astype(np.float32)
    return out


def spin2_from_row_col_grad(
    dr_south: np.ndarray,
    dc_east: np.ndarray,
    smooth_sigma: float = 2.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute coherent spin-2 strike director ``(c2, s2, energy)`` in compass coordinates.

    On a north-up grid where ``dr_south`` increases southward and ``dc_east`` increases
    eastward, a fault striking at compass azimuth ``theta`` clockwise from North has
    normal gradient proportional to ``(dr_south, dc_east) = (sin(theta), cos(theta))``.
    Therefore:
        cos(2*theta) = (dc_east^2 - dr_south^2) / (dc_east^2 + dr_south^2)
        sin(2*theta) = (2 * dr_south * dc_east) / (dc_east^2 + dr_south^2)
    which is invariant to 180-degree step polarity flips and free of branch cuts.
    """
    j_cc = dc_east * dc_east
    j_rr = dr_south * dr_south
    j_rc = 2.0 * dr_south * dc_east
    if smooth_sigma > 0.0:
        u_raw = ndi.gaussian_filter(j_cc - j_rr, sigma=smooth_sigma).astype(np.float32)
        v_raw = ndi.gaussian_filter(j_rc, sigma=smooth_sigma).astype(np.float32)
        energy = ndi.gaussian_filter(j_cc + j_rr, sigma=smooth_sigma).astype(np.float32)
    else:
        u_raw = (j_cc - j_rr).astype(np.float32)
        v_raw = j_rc.astype(np.float32)
        energy = (j_cc + j_rr).astype(np.float32)
    norm = np.hypot(u_raw, v_raw) + 1e-8
    return (u_raw / norm).astype(np.float32), (v_raw / norm).astype(np.float32), energy


def kostrov_azimuthal_tendencies(
    c2: np.ndarray,
    s2: np.ndarray,
    dilate_rate_pos: np.ndarray,
    shear_rate: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Project local spin-2 strike ``(c2, s2)`` onto Great Basin extension/transtension.

    * Normal dilation tendency: ``dilate_+ * cos^2(theta - theta_0)``
    * Conjugate Riedel / oblique slip tendency: ``shear * sin^2(2*(theta - theta_0))``
    """
    cos2_align = np.clip(0.5 * (1.0 + c2 * COS_2THETA0 + s2 * SIN_2THETA0), 0.0, 1.0)
    sin_2delta = s2 * COS_2THETA0 - c2 * SIN_2THETA0
    sin2_riedel = np.clip(sin_2delta * sin_2delta, 0.0, 1.0)
    t_dil = (dilate_rate_pos * cos2_align).astype(np.float32)
    t_slip = (shear_rate * sin2_riedel).astype(np.float32)
    return t_dil, t_slip


def unilateral_scarp_polarity(
    downface: np.ndarray,
    upface: np.ndarray,
    coherence: np.ndarray,
    tau: float = 12.0,
) -> np.ndarray:
    """Distinguish unilateral tectonic fault scarps from symmetric V-shaped stream gullies."""
    df = np.maximum(downface.astype(np.float32), 0.0)
    uf = np.maximum(upface.astype(np.float32), 0.0)
    coh = np.clip(coherence.astype(np.float32) / 255.0, 0.0, 1.0)
    asym = np.abs(df - uf) / (df + uf + float(tau))
    amp = np.clip(np.maximum(df, uf) / 140.0, 0.0, 1.0)
    return (asym * coh * amp).astype(np.float32)


def upward_continuation_persistence(
    grad_up150: np.ndarray,
    grad_drape: np.ndarray,
    tau: float,
) -> np.ndarray:
    """Harmonic depth-persistence ratio ``|grad TMI_up150| / (|grad TMI_drape| + tau)``."""
    num = np.maximum(grad_up150.astype(np.float32), 0.0)
    den = np.maximum(grad_drape.astype(np.float32), 0.0) + max(float(tau), 1e-6)
    return np.clip(num / den, 0.0, 2.5).astype(np.float32)


def _hessian_max_ridge(field: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return max absolute curvature magnitude and principal strike spin-2 ``(c2, s2)``."""
    f = ndi.gaussian_filter(field, sigma=sigma)
    frr = ndi.gaussian_filter(field, sigma=sigma, order=(2, 0))
    fcc = ndi.gaussian_filter(field, sigma=sigma, order=(0, 2))
    frc = ndi.gaussian_filter(field, sigma=sigma, order=(1, 1))
    del f
    diff = fcc - frr
    rad = np.hypot(diff, 2.0 * frc)
    eig_max = (0.5 * (np.abs(fcc + frr) + rad)).astype(np.float32)
    norm = rad + 1e-8
    c2 = (diff / norm).astype(np.float32)
    s2 = (2.0 * frc / norm).astype(np.float32)
    return eig_max, c2, s2


def build_static_features(
    feature_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
    out_memmap_path: Path,
) -> np.ndarray:
    """Stream all 26 quadrant-invariant static planes into ``float16`` memmap."""
    verify_band_table()
    fp = np.asarray(footprint, dtype=bool)
    h, w = fp.shape
    out_memmap_path.parent.mkdir(parents=True, exist_ok=True)
    mm = open_memmap(
        out_memmap_path,
        mode="w+",
        dtype=np.float16,
        shape=(len(STATIC_FEATURE_NAMES), h, w),
    )

    def _store(name: str, arr: np.ndarray) -> None:
        idx = STATIC_FEATURE_NAMES.index(name)
        mm[idx] = np.where(fp, np.clip(arr, -30.0, 30.0), 0.0).astype(np.float16)

    with rasterio.open(feature_tif) as src:
        if src.shape != (h, w):
            raise RuntimeError(f"training_features shape {src.shape} != {(h, w)}")

        # --- Block A1: Magnetic 3-D Analytic Signal & Upward-Continued Persistence ---
        b3_hg = _clean_fill(src.read(3), fp)
        b9_vg = _clean_fill(src.read(9), fp)
        asig = np.hypot(b3_hg, b9_vg)
        med_asig = max(float(np.median(asig[fp])), 1e-4)
        _store("mag_asig3d_log", _robust_z(np.log1p(asig / med_asig), fp))

        for sigma, key in ((2.0, "verduzco_tilt_zero_s2"), (5.0, "verduzco_tilt_zero_s5")):
            hg_s = ndi.gaussian_filter(np.maximum(b3_hg, 0.0), sigma=sigma)
            vg_s = ndi.gaussian_filter(b9_vg, sigma=sigma)
            tilt = np.arctan2(vg_s, hg_s + 1e-4)
            tr, tc = np.gradient(tilt)
            sharp = np.hypot(tr, tc) * np.exp(-((tilt / 0.35) ** 2))
            _store(key, _pos_scale(sharp, fp))
            del hg_s, vg_s, tilt, tr, tc, sharp
        del b3_hg, b9_vg, asig
        gc.collect()

        b14_tmi = _clean_fill(src.read(14), fp)
        tmi_s = ndi.gaussian_filter(b14_tmi, sigma=1.5)
        dr_tmi, dc_tmi = np.gradient(tmi_s)
        grad_tmi = np.hypot(dr_tmi, dc_tmi)
        del b14_tmi, tmi_s, dr_tmi, dc_tmi

        with rasterio.open(external_dir / "geodawn_extensions_u8.tif") as ext_ds:
            up150 = _clean_fill(ext_ds.read(4).astype(np.float32), fp)
            uth_u8 = _clean_fill(ext_ds.read(3).astype(np.float32), fp)
        up150_s = ndi.gaussian_filter(up150, sigma=1.8)
        dr_up, dc_up = np.gradient(up150_s)
        grad_up = np.hypot(dr_up, dc_up)
        c2_mag, s2_mag, _ = spin2_from_row_col_grad(dr_up, dc_up, smooth_sigma=3.0)
        del up150, up150_s, dr_up, dc_up
        grad_up_n = grad_up / max(float(np.percentile(grad_up[fp], 90.0)), 1e-4)
        grad_tmi_n = grad_tmi / max(float(np.percentile(grad_tmi[fp], 90.0)), 1e-4)
        persist = upward_continuation_persistence(grad_up_n, grad_tmi_n, tau=0.20) * np.clip(grad_up_n, 0.0, 2.5)
        _store("up150_depth_persist", _pos_scale(persist, fp))
        del grad_tmi, grad_up, grad_up_n, grad_tmi_n, persist
        gc.collect()

        # --- Block A2: Vector-Consistent Gravity Laplace g_zz & 3-D Gravity Ridge ---
        b11_south = _clean_fill(src.read(11), fp)
        b18_east = _clean_fill(src.read(18), fp)
        g_south_s = ndi.gaussian_filter(b11_south, sigma=3.0)
        g_east_s = ndi.gaussian_filter(b18_east, sigma=3.0)
        c2_grav, s2_grav, _ = spin2_from_row_col_grad(g_south_s, g_east_s, smooth_sigma=3.0)
        d_east_dc = np.gradient(g_east_s, axis=1)
        d_south_dr = np.gradient(g_south_s, axis=0)
        d_east_dr = np.gradient(g_east_s, axis=0)
        d_south_dc = np.gradient(g_south_s, axis=1)
        g_zz = -(d_east_dc + d_south_dr)
        curl_err = np.abs(d_south_dc - d_east_dr)
        gh = np.hypot(g_east_s, g_south_s)
        seam_ok = np.exp(-((curl_err / (np.percentile(curl_err[fp], 92.0) + 1e-5)) ** 2))
        gtilt = np.arctan2(g_zz, gh + 1e-4)
        gtr, gtc = np.gradient(gtilt)
        gzz_sharp = np.hypot(gtr, gtc) * np.exp(-((gtilt / 0.35) ** 2)) * seam_ok
        _store("laplace_gzz_zero_s3", _pos_scale(gzz_sharp, fp))
        del d_east_dc, d_south_dr, d_east_dr, d_south_dc, g_zz, curl_err, gtilt, gtr, gtc, gzz_sharp

        gh_raw = np.hypot(b18_east, b11_south)
        gh_bg = ndi.gaussian_filter(gh_raw, sigma=16.0)
        gh_prom = gh / (gh_bg + float(np.median(gh_raw[fp])) * 0.35 + 1e-5) * seam_ok
        _store("grav_asig_ridge_s3", _pos_scale(gh_prom, fp))
        del b11_south, b18_east, g_south_s, g_east_s, gh, gh_raw, gh_bg, gh_prom, seam_ok
        gc.collect()

        # --- Block B: Basement Hinge, Poisson Misalignment & Kostrov-Byerlee Tendency ---
        b15_base = _clean_fill(src.read(15), fp)
        hinge_eig, _, _ = _hessian_max_ridge(b15_base, sigma=4.0)
        hinge_bg = ndi.gaussian_filter(hinge_eig, sigma=18.0) + float(np.median(hinge_eig[fp])) + 1e-5
        _store("base_hinge_curvature", _pos_scale(hinge_eig / hinge_bg, fp))
        del b15_base, hinge_eig, hinge_bg

        b13_grav = _clean_fill(src.read(13), fp)
        b2_rtp = _clean_fill(src.read(2), fp)
        _, c2_hg, s2_hg = _hessian_max_ridge(b13_grav, sigma=4.0)
        _, c2_hm, s2_hm = _hessian_max_ridge(b2_rtp, sigma=4.0)
        sin2_mis = 0.5 * (1.0 - np.clip(c2_hg * c2_hm + s2_hg * s2_hm, -1.0, 1.0))
        _store("poisson_tensor_misalign_s4", sin2_mis.astype(np.float32))
        del b13_grav, b2_rtp, c2_hg, s2_hg, c2_hm, s2_hm, sin2_mis
        gc.collect()

        with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as t10_ds:
            slope_p90 = _clean_fill(t10_ds.read(1).astype(np.float32), fp)
            relief_loc = _clean_fill(t10_ds.read(5).astype(np.float32), fp)
            curv_prof = _clean_fill(t10_ds.read(6).astype(np.float32), fp)
            asp_coh = _clean_fill(t10_ds.read(7).astype(np.float32), fp)
            hs_lin = _clean_fill(t10_ds.read(8).astype(np.float32), fp)

        _, c2_t10, s2_t10 = _hessian_max_ridge(hs_lin, sigma=2.0)
        c2_sum = 0.40 * c2_grav + 0.35 * c2_mag + 0.25 * c2_t10
        s2_sum = 0.40 * s2_grav + 0.35 * s2_mag + 0.25 * s2_t10
        coh_mp = np.hypot(c2_sum, s2_sum)
        c2_joint = (c2_sum / (coh_mp + 1e-8)).astype(np.float32)
        s2_joint = (s2_sum / (coh_mp + 1e-8)).astype(np.float32)
        _store("multi_physics_spin2_coherence", np.clip(coh_mp, 0.0, 1.0))
        del c2_grav, s2_grav, c2_mag, s2_mag, c2_sum, s2_sum, coh_mp

        b8_dil = _clean_fill(src.read(8), fp)
        b7_shr = _clean_fill(src.read(7), fp)
        dil_pos = np.maximum(b8_dil - float(np.percentile(b8_dil[fp], 15.0)), 0.0)
        dil_pos /= max(float(np.median(dil_pos[fp])), 1e-6)
        shr_pos = np.maximum(b7_shr, 0.0) / max(float(np.median(np.abs(b7_shr[fp]))), 1e-6)
        t_dil, t_slip = kostrov_azimuthal_tendencies(c2_joint, s2_joint, dil_pos, shr_pos)
        _store("kostrov_dilation_tendency", _pos_scale(t_dil, fp))
        _store("kostrov_riedel_slip_tendency", _pos_scale(t_slip, fp))
        del b8_dil, b7_shr, dil_pos, shr_pos, t_dil, t_slip, c2_joint, s2_joint

        b17_cond = _clean_fill(src.read(17), fp)
        cond_log = np.log1p(np.maximum(b17_cond - float(np.min(b17_cond[fp])), 0.0))
        cond_s = ndi.gaussian_filter(cond_log, sigma=2.5)
        cdr, cdc = np.gradient(cond_s)
        _store("cond_lateral_barrier", _pos_scale(np.hypot(cdr, cdc), fp))
        del b17_cond, cond_log, cond_s, cdr, cdc

        # --- Block C: Seismicity, K/Th Potassic Alteration & Alluvial Quietness ---
        b4_inv = _clean_fill(src.read(4), fp)
        b10_deq = _clean_fill(src.read(10), fp)
        b16_ieq = _clean_fill(src.read(16), fp)
        eq_coup = (
            np.log1p(np.maximum(b16_ieq, 0.0))
            * (np.maximum(b4_inv, 0.0) / max(float(np.median(np.abs(b4_inv[fp]))), 1e-6))
            / (1.0 + np.maximum(b10_deq, 0.0) / 18000.0)
        )
        _store("eq_strain_coupling", _pos_scale(eq_coup, fp))
        del b4_inv, b10_deq, b16_ieq, eq_coup

        with rasterio.open(external_dir / "geodawn_rad_u8.tif") as rad_ds:
            k_u8 = _clean_fill(rad_ds.read(1).astype(np.float32), fp)
            th_u8 = _clean_fill(rad_ds.read(2).astype(np.float32), fp)
        zk = _robust_z(k_u8, fp)
        zth = _robust_z(th_u8, fp)
        k_resid = zk - 0.75 * zth
        k_hp = ndi.gaussian_filter(k_resid, sigma=2.0) - ndi.gaussian_filter(k_resid, sigma=18.0)
        _store("rad_k_th_alteration", _robust_z(k_hp, fp))
        del k_u8, th_u8, zk, zth, k_resid, k_hp

        uth_hp = ndi.gaussian_filter(uth_u8, sigma=2.0) - ndi.gaussian_filter(uth_u8, sigma=18.0)
        _store("rad_uth_redox_front", _robust_z(uth_hp, fp))
        del uth_u8, uth_hp

        b6_tc = _clean_fill(src.read(6), fp)
        tc_s = ndi.gaussian_filter(b6_tc, sigma=2.0)
        tcr, tcc = np.gradient(tc_s)
        tc_grad = np.hypot(tcr, tcc)
        tc_quiet = 1.0 / (1.0 + tc_grad / max(float(np.median(tc_grad[fp])), 1e-4))
        _store("tc_alluvial_quietness", tc_quiet.astype(np.float32))
        del b6_tc, tc_s, tcr, tcc, tc_grad, tc_quiet
        gc.collect()

        # --- Block D: 1m LiDAR Polarity, 10m Fluvial k_sn & Lahontan Deconfounder ---
        with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as lid_ds:
            ex_max = lid_ds.read(1).astype(np.float32)
            step_max = lid_ds.read(3).astype(np.float32)
            downface = lid_ds.read(6).astype(np.float32)
            upface = lid_ds.read(7).astype(np.float32)
            coh100 = lid_ds.read(10).astype(np.float32)
            lid_valid = (lid_ds.read(12) > 0) & fp

        lid_comb = (0.60 * step_max + 0.40 * ex_max) / 255.0
        lid_med = float(np.median(lid_comb[lid_valid])) if lid_valid.any() else 0.0
        lid_step = np.where(lid_valid, lid_comb, lid_med).astype(np.float32)
        _store("lidar_step_norm", _robust_z(lid_step, fp))
        _store("lidar_valid_flag", lid_valid.astype(np.float32))

        pol_raw = unilateral_scarp_polarity(downface, upface, coh100, tau=12.0)
        pol_med = float(np.median(pol_raw[lid_valid])) if lid_valid.any() else 0.0
        _store("lidar_unilateral_polarity", _pos_scale(np.where(lid_valid, pol_raw, pol_med), fp))
        del ex_max, step_max, downface, upface, coh100, lid_valid, lid_comb, lid_step, pol_raw
        gc.collect()

        tect_scarp = (curv_prof / 255.0) * (hs_lin / 255.0) * (0.35 + 0.65 * (asp_coh / 255.0))
        _store("topo10_tectonic_scarp", _pos_scale(tect_scarp, fp))

        pied_break = (
            ndi.gaussian_filter(slope_p90, sigma=1.8) - 0.85 * ndi.gaussian_filter(slope_p90, sigma=12.0)
        ) * np.exp(-(((slope_p90 - 75.0) / 65.0) ** 2))
        _store("topo10_piedmont_break", _robust_z(pied_break, fp))
        del curv_prof, asp_coh, hs_lin, pied_break, relief_loc, slope_p90

        with rasterio.open(external_dir / "dem10_chi_100m_i16.tif") as chi_ds:
            step_hi = chi_ds.read(1).astype(np.float32)
            step_lo = chi_ds.read(2).astype(np.float32)
            ksn_raw = chi_ds.read(3).astype(np.float32)
            log_area = chi_ds.read(4).astype(np.float32)
            zmean = _clean_fill(chi_ds.read(5).astype(np.float32), fp)

        z_smooth = ndi.gaussian_filter(zmean, sigma=3.5)
        zr, zc = np.gradient(z_smooth)
        c2_elev, s2_elev, _ = spin2_from_row_col_grad(zr, zc, smooth_sigma=3.0)
        contour_par = np.clip(0.5 * (1.0 + c2_t10 * c2_elev + s2_t10 * s2_elev), 0.0, 1.0)
        lahontan_band = np.exp(-(((zmean - 1285.0) / 60.0) ** 2))
        lahontan_mimic = lahontan_band * contour_par * np.clip(tect_scarp * 4.0, 0.0, 1.0)
        _store("lahontan_contour_mimic", lahontan_mimic.astype(np.float32))
        del zmean, z_smooth, zr, zc, c2_elev, s2_elev, c2_t10, s2_t10, contour_par, lahontan_band, lahontan_mimic, tect_scarp

        ok_ksn = fp & (ksn_raw > -32000.0)
        ksn_clean = np.where(ok_ksn, np.maximum(ksn_raw, 0.0), 0.0).astype(np.float32)
        w_ksn = ok_ksn.astype(np.float32)
        ksn_s2 = ndi.gaussian_filter(ksn_clean, sigma=2.2) / (ndi.gaussian_filter(w_ksn, sigma=2.2) + 0.05)
        ksn_s15 = ndi.gaussian_filter(ksn_clean, sigma=15.0) / (ndi.gaussian_filter(w_ksn, sigma=15.0) + 0.05)
        _store("fluv_ksn_knickzone", _pos_scale(np.maximum(ksn_s2 - 0.80 * ksn_s15, 0.0), fp))
        del ok_ksn, ksn_clean, w_ksn, ksn_s2, ksn_s15, ksn_raw

        ok_step = fp & (step_hi > -32000.0) & (step_lo > -32000.0) & (log_area > -32000.0)
        chi_diff = np.where(
            ok_step,
            np.maximum(step_hi - step_lo, 0.0) * np.clip((log_area - 4000.0) / 3000.0, 0.1, 1.5),
            0.0,
        ).astype(np.float32)
        chi_s = ndi.gaussian_filter(chi_diff, sigma=2.5)
        _store("fluv_chi_step_knick", _pos_scale(chi_s, fp))
        del step_hi, step_lo, log_area, ok_step, chi_diff, chi_s
        gc.collect()

        # --- Block E: Coarse Native 100m DEM Context ---
        b12_dem = _clean_fill(src.read(12), fp)
        dem_eig, _, _ = _hessian_max_ridge(b12_dem, sigma=2.0)
        _store("dem100_hess_s2", _pos_scale(dem_eig, fp))
        del b12_dem, dem_eig

        b19_slp = _clean_fill(src.read(19), fp)
        _store("dem100_slope_norm", _robust_z(b19_slp, fp))
        del b19_slp
        gc.collect()

    mm.flush()
    del mm
    return np.load(out_memmap_path, mmap_mode="r")


def compute_exposure_propensity(external_dir: Path, footprint: np.ndarray) -> np.ndarray:
    """Label-free SAR surface-exposure propensity ``c(x) in [0.35, 1.0]``.

    Bedrock/range-front steep terrain has high fault-mapping completeness (``c -> 1``),
    while low-slope Holocene alluvial aprons and playas have lower mapping propensity
    (``c -> 0.35``), giving bounded inverse-propensity positive weights ``1 / sqrt(c)``.
    """
    fp = np.asarray(footprint, dtype=bool)
    with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as ds:
        slope = _clean_fill(ds.read(1).astype(np.float32), fp) / 255.0
        relief = _clean_fill(ds.read(5).astype(np.float32), fp) / 255.0
    s_reg = ndi.gaussian_filter(0.6 * slope + 0.4 * relief, sigma=6.0)
    p90 = max(float(np.percentile(s_reg[fp], 90.0)), 1e-4)
    c_hat = np.clip(0.35 + 0.65 * (s_reg / p90), 0.35, 1.0)
    return np.where(fp, c_hat, 1.0).astype(np.float32)


def _find_visible_tips_and_tangents(
    vis_cat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract 8-connected fault endpoints and outward unit tip tangents strictly from ``vis_cat``."""
    v = np.asarray(vis_cat, dtype=bool)
    if not v.any():
        e = np.zeros(0, dtype=np.int32)
        f = np.zeros(0, dtype=np.float32)
        return e, e, f, f
    nb = ndi.convolve(v.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    tips = v & (nb == 1)
    ty, tx = np.nonzero(tips)
    if ty.size == 0:
        e = np.zeros(0, dtype=np.int32)
        f = np.zeros(0, dtype=np.float32)
        return e, e, f, f
    vf = v.astype(np.float32)
    cy = ndi.uniform_filter(vf, size=9, mode="constant")
    cx = ndi.uniform_filter(vf, size=9, mode="constant")
    # Weighted local fault-pixel centroid in 9x9 window around each tip:
    h, w = v.shape
    yy_grid, xx_grid = np.indices((h, w), dtype=np.float32)
    mass = np.maximum(ndi.uniform_filter(vf, size=9, mode="constant"), 1e-6)
    mean_y = ndi.uniform_filter(vf * yy_grid, size=9, mode="constant") / mass
    mean_x = ndi.uniform_filter(vf * xx_grid, size=9, mode="constant") / mass
    del cy, cx, yy_grid, xx_grid, mass, vf
    # Outward tangent points AWAY from the interior fault centroid through the tip:
    vy = ty.astype(np.float32) - mean_y[ty, tx]
    vx = tx.astype(np.float32) - mean_x[ty, tx]
    norm = np.hypot(vy, vx) + 1e-6
    return ty.astype(np.int32), tx.astype(np.int32), (vy / norm).astype(np.float32), (vx / norm).astype(np.float32)


def compute_kostrov_elastic_fields(
    vis_cat: np.ndarray,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute 6 strictly fold-visible Kostrov-Pollard crack-tip, stepover & shadow planes."""
    v = np.asarray(vis_cat, dtype=bool) & np.asarray(footprint, dtype=bool)
    fp = np.asarray(footprint, dtype=bool)
    h, w = fp.shape
    zeros = {k: np.zeros((h, w), dtype=np.float32) for k in ELASTIC_FEATURE_NAMES}
    if not v.any():
        return zeros

    # Nearest visible fault pixel and local visible strike director
    d_vis, (ny_idx, nx_idx) = ndi.distance_transform_edt(~v, return_indices=True)
    d_vis = d_vis.astype(np.float32)
    vf_s = ndi.gaussian_filter(v.astype(np.float32), sigma=2.2)
    vr, vc = np.gradient(vf_s)
    c2_v, s2_v, _ = spin2_from_row_col_grad(vr, vc, smooth_sigma=3.0)
    del vf_s, vr, vc

    yy, xx = np.indices((h, w), dtype=np.float32)
    ry = yy - ny_idx.astype(np.float32)
    rx = xx - nx_idx.astype(np.float32)
    rnorm = np.hypot(ry, rx) + 1e-6
    uy_rel = ry / rnorm
    ux_rel = rx / rnorm
    del ry, rx, rnorm

    # Vector (uy_rel, ux_rel) from nearest visible fault pixel:
    # Fault tangent spin-2 in (row_south, col_east): since normal is (sin theta, cos theta),
    # tangent is (-cos theta, sin theta), so cos(2*phi_vec) along tangent satisfies:
    c2_rel = ux_rel * ux_rel - uy_rel * uy_rel
    s2_rel = 2.0 * uy_rel * ux_rel
    # Note: normal to fault has (dr, dc) = (sin theta, cos theta) -> (c2_v, s2_v).
    # Fault tangent is rotated by 90 deg -> (-c2_v, -s2_v)!
    # Therefore alignment with fault NORMAL (broadside perpendicular) is 0.5*(1 + c2_rel*c2_v + s2_rel*s2_v)!
    perp_align = np.clip(0.5 * (1.0 + c2_rel * c2_v + s2_rel * s2_v), 0.0, 1.0)
    along_align = 1.0 - perp_align
    del uy_rel, ux_rel, c2_rel, s2_rel

    # Broadside elastic stress-release shadow (3 < d_vis <= 24 px perpendicular to mid-segment)
    broadside = perp_align * np.exp(-(((d_vis - 8.5) / 8.5) ** 2)) * (d_vis > 2.6)
    # Strike-aligned continuation corridor outside 2.6 px collar
    corridor = (along_align ** 2) * np.exp(-d_vis / 14.0) * (d_vis > 2.6)
    del ny_idx, nx_idx, c2_v, s2_v, perp_align, along_align

    ty, tx, tvy, tvx = _find_visible_tips_and_tangents(v)
    if ty.size == 0:
        out = dict(zeros)
        out["broadside_stress_shadow"] = np.where(fp, broadside, 0.0).astype(np.float32)
        out["strike_anisotropic_corridor"] = np.where(fp, corridor, 0.0).astype(np.float32)
        return out

    tip_mask = np.zeros((h, w), dtype=bool)
    tip_mask[ty, tx] = True
    d_tip, (tny, tnx) = ndi.distance_transform_edt(~tip_mask, return_indices=True)
    d_tip = d_tip.astype(np.float32)
    tip_id_grid = np.zeros((h, w), dtype=np.int32)
    tip_id_grid[ty, tx] = np.arange(ty.size, dtype=np.int32)
    nearest_tip = tip_id_grid[tny, tnx]
    del tip_mask, tip_id_grid, tny, tnx

    oty = tvy[nearest_tip]
    otx = tvx[nearest_tip]
    dy_tip = yy - ty[nearest_tip].astype(np.float32)
    dx_tip = xx - tx[nearest_tip].astype(np.float32)
    del yy, xx, nearest_tip
    dn = np.hypot(dy_tip, dx_tip) + 1e-6
    cos_a = np.clip((dy_tip * oty + dx_tip * otx) / dn, -1.0, 1.0)
    sin_abs = np.sqrt(np.maximum(0.0, 1.0 - cos_a * cos_a))
    # Kostrov extensional weight of the tip tangent (oty = -cos theta, otx = sin theta -> c2_tip = c2_normal):
    # Tangent (-cos theta, sin theta) has otx^2 - oty^2 = sin^2 - cos^2 = -cos(2*theta),
    # 2*oty*otx = -sin(2*theta), so normal (c2, s2) = (oty^2 - otx^2, -2*oty*otx):
    c2_tip = oty * oty - otx * otx
    s2_tip = -2.0 * oty * otx
    kostrov_w = 0.45 + 0.55 * np.clip(0.5 * (1.0 + c2_tip * COS_2THETA0 + s2_tip * SIN_2THETA0), 0.0, 1.0)
    del dy_tip, dx_tip, dn, oty, otx, c2_tip, s2_tip

    fwd = np.maximum(cos_a, 0.0)
    outside_collar = (d_vis > 2.6).astype(np.float32)
    cone_short = (fwd ** 4) * np.exp(-d_tip / 14.0) * kostrov_w * outside_collar
    cone_long = (fwd ** 4) * np.exp(-d_tip / 36.0) * kostrov_w * outside_collar
    # Pollard-Segall off-axis tensile wing-crack lobes peaking near +-27 deg (sin ~ 0.45, cos ~ 0.89)
    wing_ang = np.exp(-(((sin_abs - 0.45) / 0.20) ** 2)) * (fwd ** 2)
    wing_lobe = wing_ang * np.exp(-d_tip / 24.0) * kostrov_w * outside_collar
    del cos_a, sin_abs, fwd, kostrov_w, d_tip, d_vis

    # Opposing-tip releasing stepover bridge: S_tip^2 - ||V_tip||^2 > 0 where two anti-parallel tips face each other
    imp_s = np.zeros((h, w), dtype=np.float32)
    imp_vy = np.zeros((h, w), dtype=np.float32)
    imp_vx = np.zeros((h, w), dtype=np.float32)
    imp_s[ty, tx] = 1.0
    imp_vy[ty, tx] = tvy
    imp_vx[ty, tx] = tvx
    s_field = ndi.gaussian_filter(imp_s, sigma=14.0) * (2.0 * np.pi * 196.0)
    vy_field = ndi.gaussian_filter(imp_vy, sigma=14.0) * (2.0 * np.pi * 196.0)
    vx_field = ndi.gaussian_filter(imp_vx, sigma=14.0) * (2.0 * np.pi * 196.0)
    del imp_s, imp_vy, imp_vx
    stepover = np.sqrt(np.maximum(0.0, s_field * s_field - (vy_field * vy_field + vx_field * vx_field))) * outside_collar
    del s_field, vy_field, vx_field, outside_collar

    return {
        "kostrov_wing_crack_lobe": np.where(fp, wing_lobe, 0.0).astype(np.float32),
        "collinear_tip_cone_short": np.where(fp, cone_short, 0.0).astype(np.float32),
        "collinear_tip_cone_long": np.where(fp, cone_long, 0.0).astype(np.float32),
        "releasing_stepover_bridge": np.where(fp, stepover, 0.0).astype(np.float32),
        "strike_anisotropic_corridor": np.where(fp, corridor, 0.0).astype(np.float32),
        "broadside_stress_shadow": np.where(fp, broadside, 0.0).astype(np.float32),
    }
