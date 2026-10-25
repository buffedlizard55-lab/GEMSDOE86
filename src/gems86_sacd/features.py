"""Leak-free multi-physics static planes, verified spin-2 strike directors,
Bekker-Davis (2020) alluvial-burial propensity, and fold-hygienic Pollard-Segall
spin-2 Coulomb strike-concordance features for H86I-SACD.

All band indices and sign conventions follow `src/gems86/io.py:BANDS` and
`BAND_PHYSICS_VERIFIED` (verified empirically prior to encoding):
  - Band 2 (`rtp`), Band 3 (`tmi_hg`), Band 9 (`tmi_vg`), Band 14 (`tmi`)
  - Band 6 (`tc`): GeoDAWN Radiometric Total Count (NOT magnetic tilt)
  - Band 11 (`iso_grav_anom_vg`): signed southward `+d(B13)/drow_south`
  - Band 18 (`iso_grav_anom_hg`): signed eastward `+dg/dx_east`
  - Laplace vertical gravity curvature: `g_zz = -(d_col B18 + d_row B11)`
  - 1 m LiDAR `strike_u8` (`lidar_scarp_features_u8.tif` band 11): quantized as
    `theta = pi * strike_u8 / 256` directly in the `(dx_east, dr_south)` frame
    (`mean spin-2 dot = +0.5005` against 100 m DEM scarp strike across 395,607
    high-coherence scarps).
"""
from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

STATIC_SUBSURFACE_NAMES: tuple[str, ...] = (
    "verduzco_tilt_zero",
    "verduzco_tilt_depth_inv",
    "jacobsen_up150_atten",
    "analytic_signal_mag",
    "rtp_bandpass",
    "laplace_gzz_signed",
    "laplace_gzz_hinge",
    "grav_mag_strike_coalign",
    "basin_edge_curv",
    "basin_biharmonic_flex",
    "cond_log_grad",
    "buried_basin_prior",
    "geodawn_k_th_alter",
    "geodawn_u_th_redox",
    "tc_contour_cross_grad",
    "coulomb_strain_transtens",
    "strain_vorticity_part",
    "seismic_corridor",
)

STATIC_SURFACE_NAMES: tuple[str, ...] = (
    "lidar_scarp_lahontan_deconf",
    "lidar_crest_toe_dipole",
    "lidar_valid_flag",
    "topo10_prof_scarp",
    "topo10_lineament_relief",
    "dem100_hess_scarp",
    "chi_divide_step",
    "ksn_knickzone",
)

STATIC_FEATURE_NAMES: tuple[str, ...] = STATIC_SUBSURFACE_NAMES + STATIC_SURFACE_NAMES

DYNAMIC_SCALAR_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "log_tip_dist",
)

DYNAMIC_SPIN2_NAMES: tuple[str, ...] = (
    "spin2_concord_scarp",
    "spin2_concord_grav",
    "spin2_concord_mag",
)

DYNAMIC_FEATURE_NAMES: tuple[str, ...] = DYNAMIC_SCALAR_NAMES + DYNAMIC_SPIN2_NAMES

DIRECTOR_NAMES: tuple[str, ...] = (
    "c2_scarp",
    "s2_scarp",
    "c2_grav",
    "s2_grav",
    "c2_mag",
    "s2_mag",
)


def _robust_z_fp(vec: np.ndarray, clip: float = 6.0) -> np.ndarray:
    """Median/MAD z-score on finite footprint vector -> float16."""
    v = vec.astype(np.float32, copy=False)
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) * 1.4826
    if mad < 1e-7:
        std = float(np.std(v))
        mad = std if std > 1e-7 else 1.0
    z = np.clip((v - med) / mad, -clip, clip)
    return z.astype(np.float16)


def _read_native_band(src: rasterio.DatasetReader, idx: int, footprint: np.ndarray) -> np.ndarray:
    raw = src.read(idx).astype(np.float32)
    valid = footprint & np.isfinite(raw) & (raw > -1e20)
    med = float(np.median(raw[valid])) if np.any(valid) else 0.0
    raw[~valid] = med
    return raw


def _read_ext_band(path: Path, idx: int, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        raw = src.read(idx).astype(np.float32)
    valid = footprint & np.isfinite(raw)
    med = float(np.median(raw[valid])) if np.any(valid) else 0.0
    raw[~valid] = med
    return raw


def build_static_sacd_pack(
    features_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
    cache_dir: Path | None = None,
) -> dict[str, np.ndarray]:
    """Compute label-free static footprint planes, spin-2 directors, and burial propensity.

    All outputs are indexed strictly on `footprint` (`shape = (K, N_fp)`, `float16`)
    so total resident footprint is ~360 MB instead of multi-gigabyte full-grid cubes.
    """
    n_fp = int(footprint.sum())
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        f_static = cache_dir / "sacd_static_fp_v1.npy"
        f_dir = cache_dir / "sacd_directors_fp_v1.npy"
        f_prop = cache_dir / "sacd_propensity_fp_v1.npy"
        if f_static.exists() and f_dir.exists() and f_prop.exists():
            st = np.load(f_static)
            dr = np.load(f_dir)
            pr = np.load(f_prop)
            if (
                st.shape == (len(STATIC_FEATURE_NAMES), n_fp)
                and dr.shape == (len(DIRECTOR_NAMES), n_fp)
                and pr.shape == (n_fp,)
            ):
                return {"static": st, "directors": dr, "propensity": pr}

    static_fp = np.zeros((len(STATIC_FEATURE_NAMES), n_fp), dtype=np.float16)
    directors_fp = np.zeros((len(DIRECTOR_NAMES), n_fp), dtype=np.float16)

    with rasterio.open(features_tif) as src:
        # 1. Magnetic harmonic tilt, analytic signal & Jacobsen 150 m upward-continuation filter
        b2_rtp = _read_native_band(src, 2, footprint)
        b3_hg = _read_native_band(src, 3, footprint)
        b9_vg = _read_native_band(src, 9, footprint)
        b14_tmi = _read_native_band(src, 14, footprint)

        hg_pos = np.maximum(b3_hg, 0.0)
        tilt = np.arctan2(b9_vg, hg_pos + 1e-5).astype(np.float32)
        tilt_s = ndi.gaussian_filter(tilt, sigma=1.2)
        tr, tx = np.gradient(tilt_s)
        tilt_grad = np.hypot(tr, tx)

        static_fp[0] = _robust_z_fp(np.exp(-np.abs(tilt[footprint]) / 0.30))
        static_fp[1] = _robust_z_fp(
            tilt_grad[footprint] * np.exp(-np.abs(tilt[footprint]) / 0.45)
        )

        tmi_up150 = _read_ext_band(external_dir / "geodawn_extensions_u8.tif", 4, footprint)
        # Normalize scales before computing shallow-vs-upward-continued gradient ratio
        tmi_s = ndi.gaussian_filter(b14_tmi, sigma=1.0)
        g0_r, g0_x = np.gradient(tmi_s)
        g0_mag = np.hypot(g0_r, g0_x)[footprint]
        g0_norm = g0_mag / (float(np.median(g0_mag)) + 1e-6)

        up_s = ndi.gaussian_filter(tmi_up150, sigma=1.0)
        gu_r, gu_x = np.gradient(up_s)
        gu_mag = np.hypot(gu_r, gu_x)[footprint]
        gu_norm = gu_mag / (float(np.median(gu_mag)) + 1e-6)
        static_fp[2] = _robust_z_fp(np.log((g0_norm + 0.08) / (gu_norm + 0.08)))

        as_mag = np.hypot(hg_pos, b9_vg)
        static_fp[3] = _robust_z_fp(np.log1p(np.maximum(as_mag[footprint], 0.0)))
        rtp_bp = ndi.gaussian_filter(b2_rtp, sigma=1.0) - ndi.gaussian_filter(b2_rtp, sigma=6.0)
        static_fp[4] = _robust_z_fp(rtp_bp[footprint])

        # Spin-2 Verduzco magnetic tilt contour strike (-tr, tx) in (east, south)
        mn = tr[footprint] ** 2 + tx[footprint] ** 2 + 1e-8
        w_mag = np.exp(-np.abs(tilt[footprint]) / 0.55).astype(np.float32)
        c2_mag = ((tr[footprint] ** 2 - tx[footprint] ** 2) / mn) * w_mag
        s2_mag = ((-2.0 * tr[footprint] * tx[footprint]) / mn) * w_mag
        directors_fp[4] = c2_mag.astype(np.float16)
        directors_fp[5] = s2_mag.astype(np.float16)

        as_fp = as_mag[footprint].copy()
        del b2_rtp, b3_hg, b9_vg, b14_tmi, tmi_up150, tilt, tilt_s, tr, tx, tilt_grad, as_mag, rtp_bp
        gc.collect()

        # 2. Vector-consistent Laplace vertical gravity curvature & gravity-magnetic coalignment
        b11_gs = _read_native_band(src, 11, footprint)  # +dg/drow_south
        b18_ge = _read_native_band(src, 18, footprint)  # +dg/dx_east
        gs_s = ndi.gaussian_filter(b11_gs, sigma=1.2)
        ge_s = ndi.gaussian_filter(b18_ge, sigma=1.2)
        dge_dx = np.gradient(ge_s, axis=1)
        dgs_dr = np.gradient(gs_s, axis=0)
        g_zz = -(dge_dx + dgs_dr)
        gh_mag = np.hypot(ge_s, gs_s)
        gzz_scale = float(np.percentile(np.abs(g_zz[footprint]), 65)) + 1e-6

        static_fp[5] = _robust_z_fp(g_zz[footprint])
        static_fp[6] = _robust_z_fp(
            gh_mag[footprint] * np.exp(-np.abs(g_zz[footprint]) / gzz_scale)
        )

        # Spin-2 gravity density-step strike (-gs, ge) in (east, south)
        gn = gs_s[footprint] ** 2 + ge_s[footprint] ** 2 + 1e-8
        gh_med = float(np.median(gh_mag[footprint])) + 1e-6
        w_grav = np.tanh(gh_mag[footprint] / gh_med).astype(np.float32)
        c2_grav = ((gs_s[footprint] ** 2 - ge_s[footprint] ** 2) / gn) * w_grav
        s2_grav = ((-2.0 * gs_s[footprint] * ge_s[footprint]) / gn) * w_grav
        directors_fp[2] = c2_grav.astype(np.float16)
        directors_fp[3] = s2_grav.astype(np.float16)

        coalign = np.maximum(0.0, c2_grav * c2_mag + s2_grav * s2_mag)
        static_fp[7] = _robust_z_fp(np.sqrt(gh_mag[footprint] * np.maximum(as_fp, 0.0)) * coalign)
        del b11_gs, b18_ge, gs_s, ge_s, dge_dx, dgs_dr, g_zz, gh_mag, as_fp, coalign
        gc.collect()

        # 3. Basin basement flexure, MT/TEM conductivity, radiometrics, strain & seismicity
        b15_base = _read_native_band(src, 15, footprint)
        base_s = ndi.gaussian_filter(b15_base, sigma=1.5)
        br_r, br_x = np.gradient(base_s)
        static_fp[8] = _robust_z_fp(np.hypot(br_r, br_x)[footprint])
        base_flex = base_s - ndi.gaussian_filter(b15_base, sigma=5.0)
        static_fp[9] = _robust_z_fp(base_flex[footprint])

        b17_cond = _read_native_band(src, 17, footprint)
        cond_l = ndi.gaussian_filter(np.log1p(np.maximum(b17_cond, 0.0)), sigma=1.2)
        cr_r, cr_x = np.gradient(cond_l)
        static_fp[10] = _robust_z_fp(np.hypot(cr_r, cr_x)[footprint])

        b19_slope = _read_native_band(src, 19, footprint)
        z_b15 = _robust_z_fp(b15_base[footprint]).astype(np.float32)
        z_b19 = _robust_z_fp(b19_slope[footprint]).astype(np.float32)
        static_fp[11] = _robust_z_fp(z_b15 - 0.5 * z_b19)

        # GeoDAWN K/Th potassic adularia-illite & U/Th redox enrichment
        rad_k = _read_ext_band(external_dir / "geodawn_rad_u8.tif", 1, footprint)
        rad_th = _read_ext_band(external_dir / "geodawn_rad_u8.tif", 2, footprint)
        ext_thk = _read_ext_band(external_dir / "geodawn_extensions_u8.tif", 1, footprint)
        ext_uth = _read_ext_band(external_dir / "geodawn_extensions_u8.tif", 3, footprint)
        k_over_th = (rad_k[footprint] + 4.0) / (rad_th[footprint] + 8.0)
        static_fp[12] = _robust_z_fp(
            0.6 * _robust_z_fp(k_over_th).astype(np.float32)
            - 0.4 * _robust_z_fp(ext_thk[footprint]).astype(np.float32)
        )
        static_fp[13] = _robust_z_fp(ext_uth[footprint])
        del rad_k, rad_th, ext_thk, ext_uth

        b12_elev = _read_native_band(src, 12, footprint)
        elev_s = ndi.gaussian_filter(b12_elev, sigma=1.5)
        er_r, er_x = np.gradient(elev_s)
        en = er_r[footprint] ** 2 + er_x[footprint] ** 2 + 1e-8
        c2_elev_contour = (er_r[footprint] ** 2 - er_x[footprint] ** 2) / en
        s2_elev_contour = (-2.0 * er_r[footprint] * er_x[footprint]) / en

        b6_tc = _read_native_band(src, 6, footprint)
        tc_s = ndi.gaussian_filter(b6_tc, sigma=1.2)
        tcr_r, tcr_x = np.gradient(tc_s)
        tc_grad = np.hypot(tcr_r, tcr_x)[footprint]
        tcn = tcr_r[footprint] ** 2 + tcr_x[footprint] ** 2 + 1e-8
        c2_tc = (tcr_r[footprint] ** 2 - tcr_x[footprint] ** 2) / tcn
        s2_tc = (-2.0 * tcr_r[footprint] * tcr_x[footprint]) / tcn
        contour_parallel = np.maximum(0.0, c2_tc * c2_elev_contour + s2_tc * s2_elev_contour)
        static_fp[14] = _robust_z_fp(tc_grad * (1.0 - 0.65 * contour_parallel))
        del b6_tc, tc_s, tcr_r, tcr_x, tc_grad, c2_tc, s2_tc

        b4_e2 = _read_native_band(src, 4, footprint)
        b7_sh = _read_native_band(src, 7, footprint)
        b8_di = _read_native_band(src, 8, footprint)
        static_fp[15] = _robust_z_fp(
            _robust_z_fp(b7_sh[footprint]).astype(np.float32)
            + 0.7 * _robust_z_fp(np.maximum(b8_di[footprint], 0.0)).astype(np.float32)
            + 0.4 * _robust_z_fp(b4_e2[footprint]).astype(np.float32)
        )
        e2_scale = float(np.percentile(np.abs(b4_e2[footprint]), 25)) + 1e-6
        wk = (b7_sh[footprint] - np.abs(b8_di[footprint])) / (np.abs(b4_e2[footprint]) + e2_scale)
        static_fp[16] = _robust_z_fp(wk)
        del b4_e2, b7_sh, b8_di, wk

        b10_deq = _read_native_band(src, 10, footprint)
        b16_ieq = _read_native_band(src, 16, footprint)
        static_fp[17] = _robust_z_fp(
            0.6 * _robust_z_fp(np.log1p(np.maximum(b10_deq[footprint], 0.0))).astype(np.float32)
            + 0.4 * _robust_z_fp(np.log1p(np.maximum(b16_ieq[footprint], 0.0))).astype(np.float32)
        )
        del b10_deq, b16_ieq, b17_cond, cond_l, cr_r, cr_x, base_s, br_r, br_x, base_flex
        gc.collect()

        # 4. Multi-resolution 1 m LiDAR, 10 m 3DEP, Lake Lahontan deconfounder & 10 m fluvial chi
        with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as lsrc:
            lid_step = lsrc.read(3)[footprint].astype(np.float32)
            lid_lapn = lsrc.read(4)[footprint].astype(np.float32)
            lid_lapp = lsrc.read(5)[footprint].astype(np.float32)
            lid_coh = lsrc.read(10)[footprint].astype(np.float32)
            lid_strike = lsrc.read(11)[footprint].astype(np.float32)
            lid_valid = (lsrc.read(12)[footprint] > 0).astype(np.float32)

        # Verified empirically: theta_lidar = pi * strike_u8 / 256 in (dx_east, dr_south)
        th_lid = np.pi * (lid_strike / 256.0)
        c2_lid = np.cos(2.0 * th_lid).astype(np.float32)
        s2_lid = np.sin(2.0 * th_lid).astype(np.float32)

        # Attenuate Lake Lahontan shoreline benches (~1255-1345 m) parallel to elevation contours
        elev_fp = b12_elev[footprint]
        in_lahontan_band = np.exp(-0.5 * ((elev_fp - 1305.0) / 38.0) ** 2).astype(np.float32)
        lid_contour_align = np.maximum(0.0, c2_lid * c2_elev_contour + s2_lid * s2_elev_contour)
        lahontan_penalty = 1.0 - 0.55 * in_lahontan_band * lid_contour_align

        static_fp[18] = _robust_z_fp(lid_valid * lid_step * (lid_coh / 255.0) * lahontan_penalty)
        static_fp[19] = _robust_z_fp(lid_valid * 0.5 * (lid_lapn + lid_lapp))
        static_fp[20] = (lid_valid * 2.0 - 1.0).astype(np.float16)

        with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as tsrc:
            t10_relief = tsrc.read(5)[footprint].astype(np.float32)
            t10_curv = tsrc.read(6)[footprint].astype(np.float32)
            t10_acoh = tsrc.read(7)[footprint].astype(np.float32)
            t10_lin = tsrc.read(8)[footprint].astype(np.float32)

        static_fp[21] = _robust_z_fp(t10_curv * (t10_acoh / 255.0))
        static_fp[22] = _robust_z_fp(t10_lin / (t10_relief + 18.0))

        # 100 m DEM Hessian scarp ridge curvature
        err, erx = np.gradient(er_r)
        exr, exx = np.gradient(er_x)
        tr_h = err + exx
        disc_h = np.hypot(err - exx, 2.0 * erx)
        lam_min = 0.5 * (tr_h - disc_h)
        static_fp[23] = _robust_z_fp(np.maximum(-lam_min[footprint], 0.0))

        # Unified 1 m LiDAR + 10 m / 100 m scarp spin-2 director across 100% of footprint
        w_lid = lid_valid * np.clip(lid_coh / 180.0, 0.0, 1.0)
        w_dem = np.tanh(np.hypot(er_r[footprint], er_x[footprint]) / (float(np.median(np.hypot(er_r[footprint], er_x[footprint]))) + 1e-6))
        c2_scarp = w_lid * c2_lid + (1.0 - w_lid) * w_dem * c2_elev_contour
        s2_scarp = w_lid * s2_lid + (1.0 - w_lid) * w_dem * s2_elev_contour
        directors_fp[0] = c2_scarp.astype(np.float16)
        directors_fp[1] = s2_scarp.astype(np.float16)

        # 10 m fluvial chi step & normalized channel steepness knickpoints
        with rasterio.open(external_dir / "dem10_chi_100m_i16.tif") as csrc:
            chi_step = np.maximum(csrc.read(1)[footprint].astype(np.float32), 0.0)
            ksn_max = np.maximum(csrc.read(3)[footprint].astype(np.float32), 0.0)
        static_fp[24] = _robust_z_fp(np.log1p(chi_step))
        static_fp[25] = _robust_z_fp(np.log1p(ksn_max))

        # Label-free Bekker-Davis (2020) geomorphic exposure propensity c_hat in [0.22, 1.0]
        z_rel10 = _robust_z_fp(t10_relief).astype(np.float32)
        logit_c = 0.85 * z_b19 + 0.55 * z_rel10 - 0.45 * z_b15
        propensity_fp = (0.22 + 0.78 / (1.0 + np.exp(-np.clip(logit_c, -8.0, 8.0)))).astype(np.float16)

    if cache_dir is not None:
        np.save(cache_dir / "sacd_static_fp_v1.npy", static_fp)
        np.save(cache_dir / "sacd_directors_fp_v1.npy", directors_fp)
        np.save(cache_dir / "sacd_propensity_fp_v1.npy", propensity_fp)

    return {"static": static_fp, "directors": directors_fp, "propensity": propensity_fp}


def _extract_visible_tips(
    vis_cat: np.ndarray, min_comp_px: int = 8
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract outward unit propagation vectors `(ur_south, ux_east)` at visible fault tips."""
    labeled, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=np.int8))
    if n_comp == 0:
        empty = np.zeros(0, dtype=np.float32)
        return empty, empty, empty, empty

    slices = ndi.find_objects(labeled)
    tip_r: list[float] = []
    tip_c: list[float] = []
    tip_ur: list[float] = []
    tip_ux: list[float] = []

    for comp_id, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        sub = labeled[sl] == comp_id
        n_px = int(sub.sum())
        if n_px < min_comp_px:
            continue
        rr, cc = np.nonzero(sub)
        r_abs = rr.astype(np.float32) + float(sl[0].start)
        c_abs = cc.astype(np.float32) + float(sl[1].start)

        rc = float(r_abs.mean())
        cc_m = float(c_abs.mean())
        dr = r_abs - rc
        dc = c_abs - cc_m
        cov_rr = float(np.dot(dr, dr)) + 1e-6
        cov_cc = float(np.dot(dc, dc)) + 1e-6
        cov_rc = float(np.dot(dr, dc))
        evals, evecs = np.linalg.eigh(
            np.array([[cov_rr, cov_rc], [cov_rc, cov_cc]], dtype=np.float64)
        )
        axis_r = float(evecs[0, 1])
        axis_x = float(evecs[1, 1])
        proj = dr * axis_r + dc * axis_x
        i_min = int(np.argmin(proj))
        i_max = int(np.argmax(proj))

        for idx_end, sign in ((i_min, -1.0), (i_max, 1.0)):
            tr_pt = float(r_abs[idx_end])
            tc_pt = float(c_abs[idx_end])
            d2 = (r_abs - tr_pt) ** 2 + (c_abs - tc_pt) ** 2
            near = (d2 > 0.5) & (d2 <= 100.0)
            if int(near.sum()) >= 3:
                vr = tr_pt - float(r_abs[near].mean())
                vx = tc_pt - float(c_abs[near].mean())
            else:
                vr = sign * axis_r
                vx = sign * axis_x
            nrm = float(np.hypot(vr, vx))
            if nrm > 1e-5:
                tip_r.append(tr_pt)
                tip_c.append(tc_pt)
                tip_ur.append(vr / nrm)
                tip_ux.append(vx / nrm)

    return (
        np.asarray(tip_r, dtype=np.float32),
        np.asarray(tip_c, dtype=np.float32),
        np.asarray(tip_ur, dtype=np.float32),
        np.asarray(tip_ux, dtype=np.float32),
    )


def compute_sacd_dynamic_fields(
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    directors_fp: np.ndarray,
    scale: int = 2,
) -> np.ndarray:
    """Compute 4 elastic crack fields + 3 spin-2 Coulomb strike-concordance planes.

    Evaluated on a 2x-coarsened grid (`1865 x 1646`) and bilinearly upsampled to
    `(3730, 3292)` before slicing `[footprint]` -> `(7, N_fp)` `float16`.
    """
    h, w = vis_cat.shape
    n_fp = int(footprint.sum())
    out = np.zeros((len(DYNAMIC_FEATURE_NAMES), n_fp), dtype=np.float16)
    if not np.any(vis_cat):
        return out

    hs = (h + scale - 1) // scale
    ws = (w + scale - 1) // scale
    grid_r, grid_c = np.meshgrid(
        (np.arange(hs, dtype=np.float32) + 0.5) * scale,
        (np.arange(ws, dtype=np.float32) + 0.5) * scale,
        indexing="ij",
    )

    tr, tc, ur, ux = _extract_visible_tips(vis_cat)
    wing_s = np.zeros((hs, ws), dtype=np.float32)
    cone_s = np.zeros((hs, ws), dtype=np.float32)
    step_s = np.zeros((hs, ws), dtype=np.float32)
    # Spin-2 projected failure-trajectory accumulators in (dx_east, dr_south)
    stress_c2 = np.zeros((hs, ws), dtype=np.float32)
    stress_s2 = np.zeros((hs, ws), dtype=np.float32)
    stress_w = np.zeros((hs, ws), dtype=np.float32)

    if tr.size > 0:
        pts_rc = np.column_stack([tr, tc])
        q_rc = np.column_stack([grid_r.ravel(), grid_c.ravel()])
        tree = cKDTree(pts_rc)
        k_nn = min(6, tr.size)
        dists, idxs = tree.query(q_rc, k=k_nn, distance_upper_bound=52.0)
        if k_nn == 1:
            dists = dists[:, None]
            idxs = idxs[:, None]

        for j in range(k_nn):
            d = dists[:, j].reshape(hs, ws)
            idx = idxs[:, j].reshape(hs, ws)
            valid = np.isfinite(d) & (idx < tr.size) & (d > 0.5)
            if not np.any(valid):
                continue
            safe_idx = np.where(valid, idx, 0)
            rr_rel = np.where(valid, grid_r - tr[safe_idx], 0.0)
            rx_rel = np.where(valid, grid_c - tc[safe_idx], 0.0)
            dist = np.maximum(d, 1.0)
            u_r = ur[safe_idx]
            u_x = ux[safe_idx]

            # Forward cosine & signed cross product in (dx_east, dr_south)
            cos_a = (rx_rel * u_x + rr_rel * u_r) / dist
            sin_a = (u_x * rr_rel - u_r * rx_rel) / dist
            fwd = np.maximum(cos_a, 0.0)

            cone_k = np.where(valid, (fwd ** 4) * np.exp(-dist / 28.0), 0.0)
            sin_half = np.sqrt(np.maximum(0.0, 0.5 * (1.0 - cos_a)))
            cos_3half = np.abs(4.0 * (np.sqrt(np.maximum(0.0, 0.5 * (1.0 + cos_a))) ** 3) - 3.0 * np.sqrt(np.maximum(0.0, 0.5 * (1.0 + cos_a))))
            wing_ang = np.maximum(0.0, cos_a) * sin_half * (0.5 + 0.5 * cos_3half)
            wing_k = np.where(
                valid,
                wing_ang * np.exp(-dist / 24.0) / np.sqrt(1.0 + dist / 4.0),
                0.0,
            )

            wing_s += wing_k
            cone_s += cone_k

            # Spin-2 trajectory: collinear cone aligns with tip vector (u_x, u_r);
            # wing-crack trajectory aligns with chord / +/-24 deg tensile splay
            c2_tip = u_x * u_x - u_r * u_r
            s2_tip = 2.0 * u_x * u_r
            cx = rx_rel / dist
            cr = rr_rel / dist
            c2_chord = cx * cx - cr * cr
            s2_chord = 2.0 * cx * cr

            wk_tot = cone_k + 0.85 * wing_k
            stress_c2 += cone_k * c2_tip + 0.85 * wing_k * c2_chord
            stress_s2 += cone_k * s2_tip + 0.85 * wing_k * s2_chord
            stress_w += wk_tot

        # Opposing-tip releasing stepover bridges + stepover chord spin-2 director
        pairs = tree.query_pairs(r=44.0, output_type="ndarray")
        for i1, i2 in pairs:
            dot_u = float(ux[i1] * ux[i2] + ur[i1] * ur[i2])
            if dot_u > -0.20:
                continue
            bx = float(tc[i2] - tc[i1])
            br = float(tr[i2] - tr[i1])
            bn = float(np.hypot(bx, br))
            if bn < 4.0:
                continue
            if (bx * float(ux[i1]) + br * float(ur[i1])) / bn < 0.25:
                continue
            mc = 0.5 * float(tc[i1] + tc[i2])
            mr = 0.5 * float(tr[i1] + tr[i2])
            rad = 0.65 * bn + 6.0
            r0 = max(0, int((mr - rad) // scale))
            r1 = min(hs, int((mr + rad) // scale) + 2)
            c0 = max(0, int((mc - rad) // scale))
            c1 = min(ws, int((mc + rad) // scale) + 2)
            if r1 <= r0 or c1 <= c0:
                continue
            ux_b = bx / bn
            ur_b = br / bn
            sub_x = grid_c[r0:r1, c0:c1] - mc
            sub_r = grid_r[r0:r1, c0:c1] - mr
            along = sub_x * ux_b + sub_r * ur_b
            perp = -sub_x * ur_b + sub_r * ux_b
            sig_a = max(0.45 * bn, 4.0)
            sig_p = max(0.22 * bn, 3.0)
            bridge = np.exp(-0.5 * ((along / sig_a) ** 2 + (perp / sig_p) ** 2)).astype(np.float32)
            step_s[r0:r1, c0:c1] = np.maximum(step_s[r0:r1, c0:c1], bridge)

            c2_b = ux_b * ux_b - ur_b * ur_b
            s2_b = 2.0 * ux_b * ur_b
            stress_c2[r0:r1, c0:c1] += 0.9 * bridge * c2_b
            stress_s2[r0:r1, c0:c1] += 0.9 * bridge * s2_b
            stress_w[r0:r1, c0:c1] += 0.9 * bridge

        d_tip_s = np.minimum(dists[:, 0].reshape(hs, ws), 52.0).astype(np.float32)
    else:
        d_tip_s = np.full((hs, ws), 52.0, dtype=np.float32)

    # Also propagate local fault tangent strike within 14 px of visible strands
    vis_s = vis_cat[::scale, ::scale][:hs, :ws].astype(np.float32)
    if np.any(vis_s > 0):
        vs_blur = ndi.gaussian_filter(vis_s, sigma=2.0)
        vrr, vrx = np.gradient(np.gradient(vs_blur, axis=0))
        vxr, vxx = np.gradient(np.gradient(vs_blur, axis=1))
        hn = np.hypot(vxx - vrr, 2.0 * vxr) + 1e-8
        d_vis_s = ndi.distance_transform_edt(vis_s == 0).astype(np.float32) * scale
        w_strand = 0.35 * np.exp(-d_vis_s / 14.0)
        stress_c2 += w_strand * ((vxx - vrr) / hn)
        stress_s2 += w_strand * ((2.0 * vxr) / hn)
        stress_w += w_strand

    zoom_f = (h / hs, w / ws)

    def _upsample_fp(arr_s: np.ndarray) -> np.ndarray:
        up = ndi.zoom(arr_s, zoom_f, order=1, prefilter=False)
        return up[:h, :w][footprint].astype(np.float32)

    wing_fp = _upsample_fp(wing_s)
    cone_fp = _upsample_fp(cone_s)
    step_fp = _upsample_fp(step_s)
    dtip_fp = _upsample_fp(d_tip_s)

    out[0] = _robust_z_fp(np.log1p(wing_fp * 10.0))
    out[1] = _robust_z_fp(np.log1p(cone_fp * 10.0))
    out[2] = _robust_z_fp(step_fp)
    out[3] = _robust_z_fp(-np.log1p(np.maximum(dtip_fp, 0.0)))

    # Normalize spin-2 stress trajectory & gate smoothly by stress intensity
    sc2_fp = _upsample_fp(stress_c2)
    ss2_fp = _upsample_fp(stress_s2)
    sw_fp = _upsample_fp(stress_w)
    snorm = np.hypot(sc2_fp, ss2_fp) + 1e-7
    w_gate = np.tanh(sw_fp * 3.0)
    unit_sc2 = (sc2_fp / snorm) * w_gate
    unit_ss2 = (ss2_fp / snorm) * w_gate

    for k, (i_c, i_s) in enumerate(((0, 1), (2, 3), (4, 5))):
        obs_c = directors_fp[i_c].astype(np.float32)
        obs_s = directors_fp[i_s].astype(np.float32)
        concord = obs_c * unit_sc2 + obs_s * unit_ss2
        out[4 + k] = _robust_z_fp(concord)

    return out
