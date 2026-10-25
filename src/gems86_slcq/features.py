"""Static translation-invariant multi-physics feature builder for Lane H86M-SLCQ.

Reuses SHA-256-verified competition & USGS/GeoDAWN/GDR-1391 helpers from
``src.gems86_stdp.features`` without duplicating raw binary readers, while
replacing constant-dip (60 deg) pullback and isotropic monogenic amplitude with:
  - Dip-adaptive 2-D Salem tilt-contact migration pullback ``(cot_r, cot_c)``,
  - Steerable 8-azimuth log-Cauchy odd-step minus even-dike quadrature symmetry,
  - Garland (1951) Poisson magnetization-to-density admittance step,
  -Verified Laplace vertical gravity gradient ``-div(B18, B11)`` step, and
  - Precomputed Cordell-Bouguer basis ``psi_bmr`` (from Band 15 only) for strict
    out-of-quadrant BMR residual fitting inside each LOQO fold.
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi

from src.gems86_stdp.features import (
    ABLATION_LOCAL_NAMES,
    NODATA,
    _geodawn_seam_keep_mask,
    _gdr_geothermal_planes,
    _hessian_ridge_and_eccentricity,
    _masked_gaussian,
    _masked_gradients,
    _rank01,
    _read_ext,
    _read_native,
    _robust_pos_z,
    _structure_tensor_intersection,
    verify_stdp_input_contract,
)
from .operators import (
    adaptive_vector_updip_pullback,
    build_bmr_basis,
    garland_poisson_admittance_jump,
    salem_adaptive_dip_and_sharpness,
    steerable_log_cauchy_step_vs_dike,
)

SLCQ_STATIC_NAMES: tuple[str, ...] = (
    "salem_grav_sharp_z150",
    "salem_grav_cot_dip",
    "salem_rtp_sharp_z150",
    "salem_rtp_cot_dip",
    "pullback_grav_lc_step_400m",
    "pullback_grav_lc_step_1000m",
    "grav_lc_pc_nodike",
    "pullback_rtp_lc_step_500m",
    "rtp_lc_pc_nodike",
    "pullback_garland_poisson_jump",
    "pullback_grav_laplace_gzz_step",
    "pullback_cond_gouge_neck",
    "intrabasin_keystone_hinge",
    "tmi_up150_wavenumber_si",
    "hydro_magnetite_destruction",
    "transtens_strain_rate_hp",
    "aseismic_creep_deficit",
    "microseismic_swarm_hp",
    "uphead_geotherm_diseq",
    "probe2m_uphead_thermal_wall",
    "paleo_sinter_vent_corridor",
    "rad_kth_uth_alteration_seamfree",
    "lidar1m_scarp_swath_debiased",
    "lidar1m_curv_dipole_debiased",
    "topo10_piedmont_curv_break",
    "chi10_drainage_knick_step",
)

BLIND_CONDUIT_NAMES: tuple[str, ...] = SLCQ_STATIC_NAMES

BMR_FOLD_NAMES: tuple[str, ...] = (
    "bmr_grad_adaptive_pullback",
    "bmr_lc_step_nodike",
)

ELASTIC_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
)


def _verified_laplace_gzz_step(
    b18_east: np.ndarray,
    b11_south: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Horizontal gradient magnitude of Laplace vertical gravity derivative
    G_zz = -div_physical(g_h) = -(d(B18)/dx_east - d(B11)/drow_south).

    Per ``docs/evidence/band-physics-verification-20261024.json``:
      Band 18 = +dg/dx_east, Band 11 = +dg/drow_south = -dg/dy_north, so physical
      horizontal divergence is d(B18)/dx_east + d(-B11)/dy_north = d(B18)/dc + d(B11)/dr!
      Smoothing at sigma=4.5 px achieves r > 0.88 against FFT -Laplacian(B13).
    """
    v = np.asarray(valid, dtype=bool)
    b18_s = _masked_gaussian(b18_east, v, sigma=4.5)
    b11_s = _masked_gaussian(b11_south, v, sigma=4.5)
    db18_dc = ndi.gaussian_filter(b18_s, sigma=1.0, order=(0, 1), mode="nearest")
    db11_dr = ndi.gaussian_filter(b11_s, sigma=1.0, order=(1, 0), mode="nearest")
    gzz = -(db18_dc + db11_dr).astype(np.float32)
    gr = ndi.gaussian_filter(gzz, sigma=1.2, order=(1, 0), mode="nearest")
    gc_ = ndi.gaussian_filter(gzz, sigma=1.2, order=(0, 1), mode="nearest")
    return np.where(v, np.hypot(gr, gc_), np.float32(0.0)).astype(np.float32)


def build_slcq_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_slcq_path: Path | None = None,
    out_ablation_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> dict[str, object]:
    """Stream all 26 H86M-SLCQ static planes + 8 pixel-local ablation planes +
    L_slcq corroboration + alluvial_cover_propensity + fold-safe BMR inputs."""
    qc = verify_stdp_input_contract(ext_dir)
    accessed_cols: dict[str, tuple[str, ...]] = {}

    with rasterio.open(feature_tif) as ds:
        H, W = ds.height, ds.width
        b2_probe = ds.read(2).astype(np.float32)
        feat_valid = np.isfinite(b2_probe) & (b2_probe > NODATA * 0.5)
        del b2_probe

    valid = feat_valid if footprint is None else (feat_valid & np.asarray(footprint, dtype=bool))
    n_slcq = len(SLCQ_STATIC_NAMES)
    n_abl = len(ABLATION_LOCAL_NAMES)

    if out_slcq_path is not None:
        out_slcq_path.parent.mkdir(parents=True, exist_ok=True)
        X_slcq = open_memmap(out_slcq_path, mode="w+", dtype=np.float16, shape=(n_slcq, H, W))
    else:
        X_slcq = np.zeros((n_slcq, H, W), dtype=np.float16)

    if out_ablation_path is not None:
        out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
        X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, H, W))
    else:
        X_abl = np.zeros((n_abl, H, W), dtype=np.float16)

    def _put_slcq(name: str, arr: np.ndarray) -> None:
        idx = SLCQ_STATIC_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_slcq[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    def _put_abl(name: str, arr: np.ndarray) -> None:
        idx = ABLATION_LOCAL_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)

    fam_slcq = np.zeros((H, W), dtype=np.float32)
    fam_geotherm = np.zeros((H, W), dtype=np.float32)
    fam_scarp = np.zeros((H, W), dtype=np.float32)
    fam_tect = np.zeros((H, W), dtype=np.float32)

    with rasterio.open(feature_tif) as ds:
        # 1. Basement depth Z_b + Dip-Adaptive Salem Tilt Migration on Gravity & RTP
        zb_m = _read_native(ds, 15, valid)
        z_gx, z_gy = _masked_gradients(zb_m, valid, sigma=3.0)
        _put_abl("local_depth_gradmag_s3", np.hypot(z_gx, z_gy))
        del z_gx, z_gy

        b13 = _read_native(ds, 13, valid)
        b5 = _read_native(ds, 5, valid)
        _put_abl("local_grav_slope_b5", b5)

        g_sharp, g_cot, g_cr, g_cc = salem_adaptive_dip_and_sharpness(
            b13, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        _put_slcq("salem_grav_sharp_z150", g_sharp)
        _put_slcq("salem_grav_cot_dip", g_cot)

        b2 = _read_native(ds, 2, valid)
        rtp_gx, rtp_gy = _masked_gradients(b2, valid, sigma=2.0)
        _put_abl("local_rtp_gradmag_s2", np.hypot(rtp_gx, rtp_gy))
        del rtp_gx, rtp_gy

        m_sharp, m_cot, m_cr, m_cc = salem_adaptive_dip_and_sharpness(
            b2, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        m_sharp = (m_sharp * seam_keep).astype(np.float32)
        m_cot = (m_cot * seam_keep).astype(np.float32)
        _put_slcq("salem_rtp_sharp_z150", m_sharp)
        _put_slcq("salem_rtp_cot_dip", m_cot)
        del m_cot

        # Joint 2-D Salem dip-cotangent vector (gravity-led, magnetic-corroborated away from seams)
        cot_r = (0.62 * g_cr + 0.38 * m_cr * seam_keep).astype(np.float32)
        cot_c = (0.62 * g_cc + 0.38 * m_cc * seam_keep).astype(np.float32)
        del g_cr, g_cc, m_cr, m_cc, g_cot

        # 2. Steerable 8-Azimuth Log-Cauchy Odd-Step Minus Even-Dike Symmetry & Garland Poisson
        g_lc400, g_pc400, _ = steerable_log_cauchy_step_vs_dike(
            b13, valid, wavelength_m=400.0, n_orient=8, dike_veto_gamma=1.05
        )
        g_lc1000, g_pc1000, _ = steerable_log_cauchy_step_vs_dike(
            b13, valid, wavelength_m=1000.0, n_orient=8, dike_veto_gamma=1.05
        )
        pull_g400 = adaptive_vector_updip_pullback(g_lc400, zb_m, cot_r, cot_c, valid)
        pull_g1000 = adaptive_vector_updip_pullback(g_lc1000, zb_m, cot_r, cot_c, valid)
        grav_pc = (0.55 * g_pc400 + 0.45 * g_pc1000).astype(np.float32)
        _put_slcq("pullback_grav_lc_step_400m", pull_g400)
        _put_slcq("pullback_grav_lc_step_1000m", pull_g1000)
        _put_slcq("grav_lc_pc_nodike", grav_pc)
        del g_lc400, g_lc1000, g_pc400, g_pc1000

        m_lc500, m_pc500, _ = steerable_log_cauchy_step_vs_dike(
            b2, valid, wavelength_m=500.0, n_orient=8, dike_veto_gamma=1.05
        )
        m_lc500 = (m_lc500 * seam_keep).astype(np.float32)
        m_pc500 = (m_pc500 * seam_keep).astype(np.float32)
        pull_m500 = adaptive_vector_updip_pullback(m_lc500, zb_m, cot_r, cot_c, valid)
        _put_slcq("pullback_rtp_lc_step_500m", pull_m500)
        _put_slcq("rtp_lc_pc_nodike", m_pc500)
        del m_lc500

        garland_raw = garland_poisson_admittance_jump(b2, b5, valid, seam_keep=seam_keep)
        pull_garland = adaptive_vector_updip_pullback(garland_raw, zb_m, cot_r, cot_c, valid)
        _put_slcq("pullback_garland_poisson_jump", pull_garland)
        del garland_raw, b5

        rtp_trough = np.maximum(_masked_gaussian(b2, valid, 9.0) - _masked_gaussian(b2, valid, 2.0), 0.0)
        del b2
        gc.collect()

        # Verified Laplace vertical gravity derivative step (Bands 18 & 11)
        b18 = _read_native(ds, 18, valid)
        b11 = _read_native(ds, 11, valid)
        gzz_step = _verified_laplace_gzz_step(b18, b11, valid)
        del b18, b11
        pull_gzz = adaptive_vector_updip_pullback(gzz_step, zb_m, cot_r, cot_c, valid)
        _put_slcq("pullback_grav_laplace_gzz_step", pull_gzz)
        del gzz_step

        # Hanging-wall rollover keystone curvature along local Salem dip vector
        zb_sm = _masked_gaussian(zb_m, valid, sigma=3.5)
        cmag = np.hypot(cot_r, cot_c)
        ur = np.where(cmag > 1e-4, cot_r / np.maximum(cmag, 1e-4), np.float32(0.0))
        uc = np.where(cmag > 1e-4, cot_c / np.maximum(cmag, 1e-4), np.float32(0.0))
        z_rr = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(2, 0), mode="nearest")
        z_cc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(0, 2), mode="nearest")
        z_rc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(1, 1), mode="nearest")
        d2z_du2 = ur * ur * z_rr + 2.0 * ur * uc * z_rc + uc * uc * z_cc
        keystone = np.where(
            valid,
            np.maximum(-d2z_du2, 0.0) * (0.35 + 0.65 * grav_pc),
            np.float32(0.0),
        ).astype(np.float32)
        del zb_sm, cmag, ur, uc, z_rr, z_cc, z_rc, d2z_du2
        _put_slcq("intrabasin_keystone_hinge", keystone)

        pull_gsharp = adaptive_vector_updip_pullback(g_sharp, zb_m, cot_r, cot_c, valid)
        hydro_demag = (
            _rank01(rtp_trough, valid)
            * (0.55 * grav_pc + 0.45 * _rank01(pull_g400, valid))
            * seam_keep
        ).astype(np.float32)
        _put_slcq("hydro_magnetite_destruction", hydro_demag)
        del rtp_trough, g_sharp, m_sharp

        fam_slcq += (
            0.24 * _rank01(pull_g400, valid)
            + 0.18 * _rank01(pull_g1000, valid)
            + 0.16 * _rank01(pull_m500, valid)
            + 0.14 * _rank01(pull_garland, valid)
            + 0.14 * _rank01(pull_gzz, valid)
            + 0.14 * _rank01(keystone, valid)
        )
        del pull_g1000, pull_m500, pull_garland, pull_gzz, keystone, m_pc500

        # 3. Upward-continuation TMI wavenumber SI + Conductive fault-gouge up-dip pullback
        b3 = _read_native(ds, 3, valid)
        b9 = _read_native(ds, 9, valid)
        h_tmi0 = np.hypot(b3, b9)
        del b3, b9
        tmi150 = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid)
        ux, uy = _masked_gradients(tmi150, valid, sigma=1.8)
        del tmi150
        h_tmi150 = np.hypot(ux, uy)
        del ux, uy
        r0 = _rank01(h_tmi0, valid)
        r150 = _rank01(h_tmi150, valid)
        del h_tmi0, h_tmi150
        wavenumber_si = (
            np.sqrt(r0 * r150 + 1e-8) * (1.0 - np.abs(r0 - r150)) * seam_keep
        ).astype(np.float32)
        del r0, r150
        _put_slcq("tmi_up150_wavenumber_si", wavenumber_si)
        fam_slcq += 0.12 * _rank01(wavenumber_si, valid)
        del wavenumber_si

        b17 = _read_native(ds, 17, valid)
        cond_log = np.log1p(np.maximum(b17 - float(np.min(b17[valid])), 0.0))
        del b17
        cond_ridge, cond_ecc = _hessian_ridge_and_eccentricity(cond_log, valid, sigma=2.4)
        del cond_log
        cond_neck_raw = (cond_ridge * (cond_ecc**2)).astype(np.float32)
        del cond_ridge, cond_ecc
        pull_cond = adaptive_vector_updip_pullback(cond_neck_raw, zb_m, cot_r, cot_c, valid)
        del cond_neck_raw
        _put_slcq("pullback_cond_gouge_neck", pull_cond)
        fam_geotherm += 0.22 * _rank01(pull_cond, valid) + 0.16 * _rank01(hydro_demag, valid)
        del pull_cond, hydro_demag
        gc.collect()

        # 4. Aseismic Transtensional Strain-Energy Deficit & Microseismic Swarms
        b4 = _read_native(ds, 4, valid)
        b7 = _read_native(ds, 7, valid)
        b8 = _read_native(ds, 8, valid)
        inv_hp = b4 - _masked_gaussian(b4, valid, 24.0)
        _put_abl("local_strain_2ndinv_hp", inv_hp)
        dil_hp = np.maximum(b8 - _masked_gaussian(b8, valid, 24.0), 0.0)
        shr_hp = np.maximum(b7 - _masked_gaussian(b7, valid, 24.0), 0.0)
        del b4, b7, b8
        transtens = (np.sqrt(shr_hp * dil_hp + 1e-12) + 0.35 * np.maximum(inv_hp, 0.0)).astype(
            np.float32
        )
        del inv_hp, dil_hp, shr_hp
        _put_slcq("transtens_strain_rate_hp", transtens)

        b10 = _read_native(ds, 10, valid)
        b16 = _read_native(ds, 16, valid)
        eq_prox = np.exp(-np.maximum(b10, 0.0) / float(np.median(b10[valid]) + 1e-6))
        eq_hp = eq_prox - _masked_gaussian(eq_prox, valid, 24.0)
        ieq_hp = b16 - _masked_gaussian(b16, valid, 24.0)
        del b10, b16, eq_prox
        swarm_hp = (_rank01(eq_hp, valid) + 0.5 * _rank01(ieq_hp, valid)).astype(np.float32)
        _put_slcq("microseismic_swarm_hp", swarm_hp)

        z_str = _robust_pos_z(transtens, valid)
        z_ieq = _robust_pos_z(ieq_hp, valid)
        creep_def = np.where(
            valid, np.maximum(z_str - 0.65 * np.maximum(z_ieq, 0.0), 0.0), np.float32(0.0)
        ).astype(np.float32)
        del eq_hp, ieq_hp, z_str, z_ieq
        _put_slcq("aseismic_creep_deficit", creep_def)
        fam_tect += (
            0.28 * _rank01(transtens, valid)
            + 0.22 * _rank01(creep_def, valid)
            + 0.14 * _rank01(swarm_hp, valid)
        )
        del transtens, creep_def, swarm_hp

        b6_tc = _read_native(ds, 6, valid)
        tc_hp = np.abs(b6_tc - _masked_gaussian(b6_tc, valid, 8.0))
        del b6_tc

        b19 = _read_native(ds, 19, valid)
        _put_abl("local_elev_slope_b19", b19)
        b12 = _read_native(ds, 12, valid)
        elev_ridge, _ = _hessian_ridge_and_eccentricity(b12, valid, sigma=2.0)
        del b12
        slope_rel = b19 / (
            _masked_gaussian(b19, valid, 12.0) + float(np.percentile(b19[valid], 25) + 1e-4)
        )
        slope_smoothness = 1.0 - _rank01(_masked_gaussian(b19, valid, 3.0), valid)
        del b19
        gc.collect()

    # 5. External DOE GDR #1391 Up-Head Geothermal Conduits + Seam-Free GeoDAWN Radiometrics
    z_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)

    uphead_diseq, probe_wall, sinter_corr, iso_geoth = _gdr_geothermal_planes(
        ext_dir, valid, z_m, accessed_cols
    )
    del z_m
    _put_abl("local_geotherm_iso_blur", iso_geoth)
    del iso_geoth

    struct_gate = (
        0.30 + 0.70 * (0.55 * _rank01(pull_g400, valid) + 0.45 * _rank01(pull_gsharp, valid))
    ).astype(np.float32)
    uphead_diseq_g = (uphead_diseq * struct_gate).astype(np.float32)
    probe_wall_g = (probe_wall * struct_gate).astype(np.float32)
    sinter_corr_g = (sinter_corr * struct_gate).astype(np.float32)
    del uphead_diseq, probe_wall, sinter_corr, struct_gate
    _put_slcq("uphead_geotherm_diseq", uphead_diseq_g)
    _put_slcq("probe2m_uphead_thermal_wall", probe_wall_g)
    _put_slcq("paleo_sinter_vent_corridor", sinter_corr_g)
    fam_geotherm += (
        0.22 * _rank01(uphead_diseq_g, valid)
        + 0.18 * _rank01(probe_wall_g, valid)
        + 0.14 * _rank01(sinter_corr_g, valid)
    )
    del uphead_diseq_g, probe_wall_g, sinter_corr_g

    rad_K = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid)
    rad_Th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid)
    ext_ThK = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 1, valid)
    kth_ratio = (rad_K + 1.0) / (rad_Th + 8.0) - 0.35 * (ext_ThK / 255.0)
    del rad_K, ext_ThK
    kth_gx, kth_gy = _masked_gradients(kth_ratio, valid, sigma=1.8)
    del kth_ratio
    rad_kth = np.hypot(kth_gx, kth_gy) * seam_keep * (1.0 - 0.55 * lahontan_band)
    del kth_gx, kth_gy

    rad_U = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid)
    ext_UTh = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 3, valid)
    uth_field = 0.6 * (ext_UTh / 255.0) + 0.4 * ((rad_U + 1.0) / (rad_Th + 8.0))
    del rad_U, rad_Th, ext_UTh
    uth_gx, uth_gy = _masked_gradients(uth_field, valid, sigma=1.8)
    del uth_field
    rad_uth = np.hypot(uth_gx, uth_gy) * seam_keep * (1.0 - 0.40 * lahontan_band)
    del uth_gx, uth_gy
    rad_joint = (
        0.48 * _rank01(rad_kth, valid)
        + 0.34 * _rank01(rad_uth, valid)
        + 0.18 * _rank01(tc_hp * seam_keep, valid)
    ).astype(np.float32)
    del rad_kth, rad_uth, tc_hp, seam_keep
    _put_slcq("rad_kth_uth_alteration_seamfree", rad_joint)
    fam_geotherm += 0.22 * rad_joint
    del rad_joint
    gc.collect()

    # 6. Swath-Debiased 3DEP 1 m LiDAR + 10 m DEM Piedmont Curvature + Fluvial Chi Knickzones
    topo_asp = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid)
    lahontan_mimic = np.where(
        valid,
        np.clip(
            lahontan_band
            * (topo_asp / 255.0)
            * (1.0 - np.clip(_rank01(pull_g400, valid), 0.0, 1.0)),
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)
    del lahontan_band

    topo_curv = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 6, valid)
    topo_hs = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 8, valid)
    topo10_pied = (
        (
            0.40 * (topo_hs / 255.0)
            + 0.35 * (topo_curv / 255.0)
            + 0.25 * (0.6 * np.clip(slope_rel / 3.0, 0.0, 1.5) + 0.4 * _rank01(elev_ridge, valid))
        )
        * (0.4 + 0.6 * (topo_asp / 255.0))
        * (1.0 - 0.55 * lahontan_mimic)
    ).astype(np.float32)
    del topo_curv, topo_hs, topo_asp, slope_rel, elev_ridge
    _put_slcq("topo10_piedmont_curv_break", topo10_pied)
    fam_scarp += 0.34 * _rank01(topo10_pied, valid)

    topo_slope_10m = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_abl("local_topo10_slope_p90", topo_slope_10m)

    # Translation-invariant alluvial cover propensity c_cover in [0, 1] (zero raw elevation!)
    topo10_smooth = 1.0 - _rank01(_masked_gaussian(topo_slope_10m, valid, 2.5), valid)
    basin_presence = np.tanh(np.maximum(zb_m, 0.0) / 250.0).astype(np.float32)
    cover_propensity = np.where(
        valid,
        np.clip(0.45 * topo10_smooth + 0.30 * slope_smoothness + 0.25 * basin_presence, 0.0, 1.0),
        np.float32(0.0),
    ).astype(np.float32)
    del topo10_smooth, slope_smoothness, basin_presence

    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as lds:
        li_has = valid & (lds.read(12) > 0)
    li_miss = valid & ~li_has

    def _put_lidar_swath_debiased(
        target_mm: np.ndarray, idx: int, arr_obs: np.ndarray, fb_10m: np.ndarray
    ) -> np.ndarray:
        z_obs = _robust_pos_z(arr_obs, li_has)
        z_fb = _robust_pos_z(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(z_obs)
        merged_z = np.zeros(valid.shape, dtype=np.float32)
        merged_z[li_has] = z_obs[li_has]
        merged_z[li_miss] = z_fb[li_miss]
        target_mm[idx] = np.clip(merged_z, -32.0, 32.0).astype(np.float16)

        r_obs = _rank01(arr_obs, li_has)
        r_fb = _rank01(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(r_obs)
        merged_r = np.zeros(valid.shape, dtype=np.float32)
        merged_r[li_has] = r_obs[li_has]
        merged_r[li_miss] = r_fb[li_miss]
        return merged_r

    li_step = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 3, valid)
    _put_lidar_swath_debiased(
        X_abl,
        ABLATION_LOCAL_NAMES.index("local_lidar_step_debiased"),
        li_step / 255.0,
        topo_slope_10m,
    )
    del topo_slope_10m

    li_cross = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 8, valid)
    li_coh = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 10, valid)
    li_scarp = (
        (li_step / 255.0)
        * (0.5 + 0.5 * (li_cross / 255.0))
        * (0.35 + 0.65 * (li_coh / 255.0))
        * (1.0 - 0.65 * lahontan_mimic)
    ).astype(np.float32)
    del li_step, li_cross
    li_scarp_r = _put_lidar_swath_debiased(
        X_slcq, SLCQ_STATIC_NAMES.index("lidar1m_scarp_swath_debiased"), li_scarp, topo10_pied
    )
    fam_scarp += 0.42 * li_scarp_r

    li_dn = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 6, valid)
    li_up = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 7, valid)
    li_ln = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 4, valid)
    li_lp = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 5, valid)
    li_dip = (
        (np.maximum(li_dn, li_up) / 255.0)
        * np.sqrt((li_ln / 255.0) * (li_lp / 255.0) + 1e-6)
        * (0.4 + 0.6 * (li_coh / 255.0))
    ).astype(np.float32)
    del li_dn, li_up, li_ln, li_lp, li_coh
    li_dip_r = _put_lidar_swath_debiased(
        X_slcq, SLCQ_STATIC_NAMES.index("lidar1m_curv_dipole_debiased"), li_dip, topo10_pied
    )
    fam_scarp += 0.24 * li_dip_r
    del li_scarp, li_dip, li_dip_r, li_has, li_miss

    # Faulds-Hinz structural intersection invariant on dip-pulled dike-vetoed traces
    comp_trace = (
        0.40 * _rank01(pull_g400, valid)
        + 0.24 * grav_pc
        + 0.22 * li_scarp_r
        + 0.14 * _rank01(topo10_pied, valid)
    ).astype(np.float32)
    del pull_g400, pull_gsharp, grav_pc, li_scarp_r, topo10_pied
    conj_inter = _structure_tensor_intersection(comp_trace, valid, sigma_grad=1.2, sigma_int=4.0)
    del comp_trace
    fam_geotherm += 0.18 * _rank01(conj_inter, valid)
    del conj_inter

    chi_step = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 1, valid)
    chi_ksn = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 3, valid)
    chi_area = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 4, valid)
    area_norm = np.clip((chi_area / 1000.0 - 4.0) / 3.0, 0.2, 1.5)
    del chi_area
    chi_knick = (
        0.6 * _rank01(np.maximum(chi_step, 0.0) / area_norm, valid)
        + 0.4 * _rank01(np.maximum(chi_ksn, 0.0), valid)
    ).astype(np.float32)
    del chi_step, chi_ksn, area_norm
    _put_slcq("chi10_drainage_knick_step", chi_knick)
    fam_tect += 0.36 * _rank01(chi_knick, valid)
    del chi_knick

    L_raw = (
        0.38 * fam_slcq
        + 0.24 * fam_geotherm
        + 0.24 * fam_scarp
        + 0.14 * fam_tect
        - 0.18 * lahontan_mimic
    )
    del fam_slcq, fam_geotherm, fam_scarp, fam_tect, lahontan_mimic
    L_slcq = _rank01(L_raw, valid)
    del L_raw

    psi_bmr = build_bmr_basis(zb_m, valid)
    gc.collect()

    if out_slcq_path is not None:
        X_slcq.flush()
        del X_slcq
        X_slcq = np.load(out_slcq_path, mmap_mode="r")
    if out_ablation_path is not None:
        X_abl.flush()
        del X_abl
        X_abl = np.load(out_ablation_path, mmap_mode="r")

    qc["accessed_csv_columns"] = {k: list(v) for k, v in accessed_cols.items()}
    return {
        "X_slcq": X_slcq,
        "X_abl": X_abl,
        "L_slcq": L_slcq,
        "cover_propensity": cover_propensity,
        "b13_grav": b13,
        "b15_zb": zb_m,
        "cot_r": cot_r,
        "cot_c": cot_c,
        "psi_bmr": psi_bmr,
        "valid": valid,
        "qc": qc,
    }
