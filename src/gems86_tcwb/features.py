"""Translation-invariant static feature stack builder for Lane H86P-TCWB.

Builds all 26 preregistered static planes + 8 pixel-local ablation planes +
``L_tcwb`` multi-physics corroboration prior + ``cover_propensity``, enforcing:
  1. Verified band physics (``src/gems86/io.py`` ``BAND_PHYSICS_VERIFIED``),
  2. SHA-256 verification of all external USGS GeoDAWN / 3DEP / DOE GDR #1391 pins,
  3. Zero reads of ``dist_known_fault_px`` or ``derived_sgmc_faults_100m_u8.tif``,
  4. Strict translation invariance (zero raw coordinates or regional base levels).
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi

from src.gems86_ksad.physics import (
    ELASTIC_FEATURE_NAMES as KSAD_ELASTIC_NAMES,
    kostrov_azimuthal_tendencies,
    spin2_from_row_col_grad,
)
from src.gems86_slcq.features import _verified_laplace_gzz_step
from src.gems86_slcq.operators import (
    adaptive_vector_updip_pullback,
    garland_poisson_admittance_jump,
    salem_adaptive_dip_and_sharpness,
    steerable_log_cauchy_step_vs_dike,
)
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
    verify_stdp_input_contract,
)
from .operators import (
    aitchison_clr_radiometric_jacobian,
    claycap_lateral_fault_seal_termination,
    downslope_tc_wash_asymmetry,
    gravity_signed_basement_hinge_kink,
    seismicity_conditioned_dilatancy_gate,
)

TCWB_STATIC_NAMES: tuple[str, ...] = (
    "tc_downslope_wash_asym",
    "tc_crossbreak_contrast",
    "basement_hinge_signed_kink",
    "basement_hinge_updip_pullback",
    "claycap_fault_seal_term",
    "seismo_dilatancy_conduit_gate",
    "aitchison_clr_rad_juxtaposition",
    "salem_grav_sharp_z150",
    "salem_rtp_sharp_z150",
    "salem_grav_dip_migration",
    "salem_rtp_dip_migration",
    "pullback_grav_odd_step_nodike",
    "pullback_rtp_odd_step_nodike",
    "pullback_garland_poisson_jump",
    "pullback_laplace_gzz_step",
    "tmi_up150_wavenumber_si",
    "hydro_magnetite_destruction",
    "kostrov_dilation_tendency",
    "kostrov_riedel_slip_tendency",
    "aseismic_creep_deficit",
    "uphead_geotherm_diseq",
    "probe2m_uphead_thermal_wall",
    "paleo_sinter_vent_corridor",
    "lidar1m_scarp_swath_debiased",
    "topo10_piedmont_curv_break",
    "chi10_drainage_knick_step",
)

TCWB_ELASTIC_NAMES: tuple[str, ...] = tuple(KSAD_ELASTIC_NAMES)


def verify_tcwb_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify native band physics contract and SHA-256 external pins."""
    return verify_stdp_input_contract(ext_dir)


def build_tcwb_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_tcwb_path: Path | None = None,
    out_ablation_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> dict[str, object]:
    """Stream all 26 H86P-TCWB static planes + 8 pixel-local ablation planes +
    ``L_tcwb`` physics corroboration + ``cover_propensity``."""
    qc = verify_tcwb_input_contract(ext_dir)
    accessed_cols: dict[str, tuple[str, ...]] = {}

    with rasterio.open(feature_tif) as ds:
        H, W = ds.height, ds.width
        b2_probe = ds.read(2).astype(np.float32)
        feat_valid = np.isfinite(b2_probe) & (b2_probe > NODATA * 0.5)
        del b2_probe

    valid = feat_valid if footprint is None else (feat_valid & np.asarray(footprint, dtype=bool))
    n_tcwb = len(TCWB_STATIC_NAMES)
    n_abl = len(ABLATION_LOCAL_NAMES)

    if out_tcwb_path is not None:
        out_tcwb_path.parent.mkdir(parents=True, exist_ok=True)
        X_tcwb = open_memmap(out_tcwb_path, mode="w+", dtype=np.float16, shape=(n_tcwb, H, W))
    else:
        X_tcwb = np.zeros((n_tcwb, H, W), dtype=np.float16)

    if out_ablation_path is not None:
        out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
        X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, H, W))
    else:
        X_abl = np.zeros((n_abl, H, W), dtype=np.float16)

    def _put_tcwb(name: str, arr: np.ndarray) -> None:
        idx = TCWB_STATIC_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_tcwb[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    def _put_abl(name: str, arr: np.ndarray) -> None:
        idx = ABLATION_LOCAL_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)
    z_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)

    fam_basement = np.zeros((H, W), dtype=np.float32)
    fam_piedmont_rad = np.zeros((H, W), dtype=np.float32)
    fam_geotherm_seal = np.zeros((H, W), dtype=np.float32)
    fam_tectonic = np.zeros((H, W), dtype=np.float32)

    with rasterio.open(feature_tif) as ds:
        # 1. Basement depth Z_b + Gravity-Signed Hinge Kink + Dip-Adaptive Salem Migration
        zb_m = _read_native(ds, 15, valid)
        z_gx, z_gy = _masked_gradients(zb_m, valid, sigma=3.0)
        _put_abl("local_depth_gradmag_s3", np.hypot(z_gx, z_gy))
        del z_gx, z_gy

        b13 = _read_native(ds, 13, valid)
        b5 = _read_native(ds, 5, valid)
        _put_abl("local_grav_slope_b5", b5)
        b18 = _read_native(ds, 18, valid)
        b11 = _read_native(ds, 11, valid)

        g_sharp, g_cot, g_cr, g_cc = salem_adaptive_dip_and_sharpness(
            b13, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        _put_tcwb("salem_grav_sharp_z150", g_sharp)
        _put_tcwb("salem_grav_dip_migration", g_cot)

        b2 = _read_native(ds, 2, valid)
        rtp_gx, rtp_gy = _masked_gradients(b2, valid, sigma=2.0)
        _put_abl("local_rtp_gradmag_s2", np.hypot(rtp_gx, rtp_gy))
        del rtp_gx, rtp_gy

        m_sharp, m_cot, m_cr, m_cc = salem_adaptive_dip_and_sharpness(
            b2, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        m_sharp = (m_sharp * seam_keep).astype(np.float32)
        m_cot = (m_cot * seam_keep).astype(np.float32)
        _put_tcwb("salem_rtp_sharp_z150", m_sharp)
        _put_tcwb("salem_rtp_dip_migration", m_cot)
        del m_cot

        cot_r = (0.64 * g_cr + 0.36 * m_cr * seam_keep).astype(np.float32)
        cot_c = (0.64 * g_cc + 0.36 * m_cc * seam_keep).astype(np.float32)
        del g_cr, g_cc, m_cr, m_cc, g_cot

        # Vector-gravity-signed basement hinge kink + up-dip pullback
        hinge_kink, nr_basin, nc_basin = gravity_signed_basement_hinge_kink(
            zb_m, b11, b18, valid, sigmas_px=(2.2, 4.0)
        )
        hinge_pull = adaptive_vector_updip_pullback(hinge_kink, zb_m, cot_r, cot_c, valid)
        _put_tcwb("basement_hinge_signed_kink", hinge_kink)
        _put_tcwb("basement_hinge_updip_pullback", hinge_pull)

        # Spin-2 structural strike director from vector gravity + basement gradient
        c2_str, s2_str, _ = spin2_from_row_col_grad(
            0.65 * b11 + 0.35 * nr_basin,
            0.65 * b18 + 0.35 * nc_basin,
            smooth_sigma=2.5,
        )

        # Steerable 8-azimuth log-Cauchy odd-step minus even-dike + Garland + Laplace G_zz
        g_lc400, g_pc400, _ = steerable_log_cauchy_step_vs_dike(
            b13, valid, wavelength_m=450.0, n_orient=8, dike_veto_gamma=1.08
        )
        g_lc950, g_pc950, _ = steerable_log_cauchy_step_vs_dike(
            b13, valid, wavelength_m=950.0, n_orient=8, dike_veto_gamma=1.08
        )
        pull_g_step = adaptive_vector_updip_pullback(
            (0.58 * g_lc400 + 0.42 * g_lc950).astype(np.float32), zb_m, cot_r, cot_c, valid
        )
        grav_pc = (0.55 * g_pc400 + 0.45 * g_pc950).astype(np.float32)
        _put_tcwb("pullback_grav_odd_step_nodike", pull_g_step)
        del g_lc400, g_lc950, g_pc400, g_pc950, b13

        m_lc500, _, _ = steerable_log_cauchy_step_vs_dike(
            b2, valid, wavelength_m=500.0, n_orient=8, dike_veto_gamma=1.08
        )
        pull_m_step = adaptive_vector_updip_pullback(
            (m_lc500 * seam_keep).astype(np.float32), zb_m, cot_r, cot_c, valid
        )
        _put_tcwb("pullback_rtp_odd_step_nodike", pull_m_step)
        del m_lc500

        garland_raw = garland_poisson_admittance_jump(b2, b5, valid, seam_keep=seam_keep)
        pull_garland = adaptive_vector_updip_pullback(garland_raw, zb_m, cot_r, cot_c, valid)
        _put_tcwb("pullback_garland_poisson_jump", pull_garland)
        del garland_raw, b5

        gzz_step = _verified_laplace_gzz_step(b18, b11, valid)
        del b18, b11
        pull_gzz = adaptive_vector_updip_pullback(gzz_step, zb_m, cot_r, cot_c, valid)
        _put_tcwb("pullback_laplace_gzz_step", pull_gzz)
        del gzz_step

        rtp_trough = np.maximum(
            _masked_gaussian(b2, valid, 9.0) - _masked_gaussian(b2, valid, 2.0), 0.0
        )
        del b2
        hydro_demag = (
            _rank01(rtp_trough, valid)
            * (0.55 * grav_pc + 0.45 * _rank01(pull_g_step, valid))
            * seam_keep
        ).astype(np.float32)
        _put_tcwb("hydro_magnetite_destruction", hydro_demag)

        # 2. One-Sided Hydrothermal Smectite Clay-Cap Lateral Fault-Seal Termination (Band 17)
        b17 = _read_native(ds, 17, valid)
        clay_raw = claycap_lateral_fault_seal_termination(
            b17, nr_basin, nc_basin, rtp_trough, valid, seam_keep=seam_keep
        )
        del b17, rtp_trough, nr_basin, nc_basin
        clay_pull = adaptive_vector_updip_pullback(clay_raw, zb_m, cot_r, cot_c, valid)
        del clay_raw
        _put_tcwb("claycap_fault_seal_term", clay_pull)

        fam_basement += (
            0.26 * _rank01(hinge_pull, valid)
            + 0.16 * _rank01(hinge_kink, valid)
            + 0.24 * _rank01(pull_g_step, valid)
            + 0.14 * _rank01(pull_m_step, valid)
            + 0.10 * _rank01(pull_garland, valid)
            + 0.10 * _rank01(pull_gzz, valid)
        )
        fam_geotherm_seal += 0.34 * _rank01(clay_pull, valid) + 0.18 * _rank01(hydro_demag, valid)
        del hinge_kink, hinge_pull, pull_m_step, pull_garland, pull_gzz, hydro_demag, clay_pull, m_sharp

        # 3. TMI upward-continued wavenumber structural index
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
        _put_tcwb("tmi_up150_wavenumber_si", wavenumber_si)
        del wavenumber_si

        # 4. Seismicity-Conditioned Dilatancy Gate + Azimuthal Kostrov/Riedel + Creep Deficit
        b4 = _read_native(ds, 4, valid)
        b7 = _read_native(ds, 7, valid)
        b8 = _read_native(ds, 8, valid)
        inv_hp = b4 - _masked_gaussian(b4, valid, 24.0)
        _put_abl("local_strain_2ndinv_hp", inv_hp)
        dil_pos = np.maximum(b8 - _masked_gaussian(b8, valid, 24.0), 0.0)
        shr_pos = np.maximum(b7 - _masked_gaussian(b7, valid, 24.0), 0.0)

        k_dil, k_riedel = kostrov_azimuthal_tendencies(c2_str, s2_str, dil_pos, shr_pos)
        del c2_str, s2_str
        _put_tcwb("kostrov_dilation_tendency", k_dil)
        _put_tcwb("kostrov_riedel_slip_tendency", k_riedel)

        b10 = _read_native(ds, 10, valid)
        b16 = _read_native(ds, 16, valid)
        seis_dil = seismicity_conditioned_dilatancy_gate(b7, b8, b10, b16, valid)
        _put_tcwb("seismo_dilatancy_conduit_gate", seis_dil)

        transtens = (np.sqrt(shr_pos * dil_pos + 1e-12) + 0.35 * np.maximum(inv_hp, 0.0)).astype(
            np.float32
        )
        ieq_hp = b16 - _masked_gaussian(b16, valid, 24.0)
        z_str = _robust_pos_z(transtens, valid)
        z_ieq = _robust_pos_z(ieq_hp, valid)
        creep_def = np.where(
            valid, np.maximum(z_str - 0.65 * np.maximum(z_ieq, 0.0), 0.0), np.float32(0.0)
        ).astype(np.float32)
        del b4, b7, b8, b10, b16, inv_hp, dil_pos, shr_pos, transtens, ieq_hp, z_str, z_ieq
        _put_tcwb("aseismic_creep_deficit", creep_def)
        fam_tectonic += (
            0.34 * _rank01(seis_dil, valid)
            + 0.24 * _rank01(k_dil, valid)
            + 0.22 * _rank01(k_riedel, valid)
            + 0.20 * _rank01(creep_def, valid)
        )
        del seis_dil, k_dil, k_riedel, creep_def

        # 5. Downslope Total-Count (Band 6 tc) Wash-Blanket Asymmetry & Aitchison CLR
        b6_tc = _read_native(ds, 6, valid)
        b12 = _read_native(ds, 12, valid)
        b19 = _read_native(ds, 19, valid)
        _put_abl("local_elev_slope_b19", b19)

        tc_asym, tc_contrast = downslope_tc_wash_asymmetry(
            b6_tc,
            b12,
            valid,
            seam_keep=seam_keep,
            lahontan_band=lahontan_band,
            standoff_px=4.5,
            director_sigma_px=5.0,
        )
        _put_tcwb("tc_downslope_wash_asym", tc_asym)
        _put_tcwb("tc_crossbreak_contrast", tc_contrast)

        elev_ridge, _ = _hessian_ridge_and_eccentricity(b12, valid, sigma=2.0)
        del b12
        slope_rel = b19 / (
            _masked_gaussian(b19, valid, 12.0) + float(np.percentile(b19[valid], 25) + 1e-4)
        )
        slope_smoothness = 1.0 - _rank01(_masked_gaussian(b19, valid, 3.0), valid)
        del b19
        gc.collect()

    rad_K = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid) + 1.0
    rad_Th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid) + 1.0
    rad_U = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid) + 1.0
    clr_jac = aitchison_clr_radiometric_jacobian(
        b6_tc,
        rad_K,
        rad_Th,
        rad_U,
        valid,
        seam_keep=seam_keep,
        lahontan_band=lahontan_band,
        sigma_px=1.8,
    )
    del b6_tc, rad_K, rad_Th, rad_U
    _put_tcwb("aitchison_clr_rad_juxtaposition", clr_jac)
    fam_piedmont_rad += (
        0.38 * _rank01(tc_asym, valid)
        + 0.24 * _rank01(tc_contrast, valid)
        + 0.22 * _rank01(clr_jac, valid)
    )
    del tc_asym, tc_contrast, clr_jac

    # 6. External DOE GDR #1391 Up-Head Geothermal Conduits
    uphead_diseq, probe_wall, sinter_corr, iso_geoth = _gdr_geothermal_planes(
        ext_dir, valid, z_m, accessed_cols
    )
    del z_m
    _put_abl("local_geotherm_iso_blur", iso_geoth)
    del iso_geoth

    struct_gate = (
        0.30 + 0.70 * (0.55 * _rank01(pull_g_step, valid) + 0.45 * _rank01(g_sharp, valid))
    ).astype(np.float32)
    uphead_diseq_g = (uphead_diseq * struct_gate).astype(np.float32)
    probe_wall_g = (probe_wall * struct_gate).astype(np.float32)
    sinter_corr_g = (sinter_corr * struct_gate).astype(np.float32)
    del uphead_diseq, probe_wall, sinter_corr, struct_gate, g_sharp
    _put_tcwb("uphead_geotherm_diseq", uphead_diseq_g)
    _put_tcwb("probe2m_uphead_thermal_wall", probe_wall_g)
    _put_tcwb("paleo_sinter_vent_corridor", sinter_corr_g)
    fam_geotherm_seal += (
        0.20 * _rank01(uphead_diseq_g, valid)
        + 0.16 * _rank01(probe_wall_g, valid)
        + 0.12 * _rank01(sinter_corr_g, valid)
    )
    del uphead_diseq_g, probe_wall_g, sinter_corr_g

    # 7. Swath-Debiased 3DEP 1 m LiDAR + 10 m DEM Piedmont Curvature + Fluvial Chi Knickzones
    topo_asp = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid)
    lahontan_mimic = np.where(
        valid,
        np.clip(
            lahontan_band
            * (topo_asp / 255.0)
            * (1.0 - np.clip(_rank01(pull_g_step, valid), 0.0, 1.0)),
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)
    del lahontan_band, pull_g_step, grav_pc

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
    _put_tcwb("topo10_piedmont_curv_break", topo10_pied)

    topo_slope_10m = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_abl("local_topo10_slope_p90", topo_slope_10m)

    topo10_smooth = 1.0 - _rank01(_masked_gaussian(topo_slope_10m, valid, 2.5), valid)
    basin_presence = np.tanh(np.maximum(zb_m, 0.0) / 250.0).astype(np.float32)
    cover_propensity = np.where(
        valid,
        np.clip(0.45 * topo10_smooth + 0.30 * slope_smoothness + 0.25 * basin_presence, 0.0, 1.0),
        np.float32(0.0),
    ).astype(np.float32)
    del topo10_smooth, slope_smoothness, basin_presence, zb_m, cot_r, cot_c

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
    del li_step, li_cross, li_coh
    li_scarp_r = _put_lidar_swath_debiased(
        X_tcwb, TCWB_STATIC_NAMES.index("lidar1m_scarp_swath_debiased"), li_scarp, topo10_pied
    )
    fam_piedmont_rad += 0.16 * (0.60 * li_scarp_r + 0.40 * _rank01(topo10_pied, valid))
    del li_scarp, li_scarp_r, topo10_pied, li_has, li_miss

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
    _put_tcwb("chi10_drainage_knick_step", chi_knick)
    fam_tectonic += 0.20 * _rank01(chi_knick, valid)
    del chi_knick

    L_raw = (
        0.34 * fam_basement
        + 0.26 * fam_piedmont_rad
        + 0.24 * fam_geotherm_seal
        + 0.16 * fam_tectonic
        - 0.18 * lahontan_mimic
    )
    del fam_basement, fam_piedmont_rad, fam_geotherm_seal, fam_tectonic, lahontan_mimic
    L_tcwb = _rank01(L_raw, valid)
    del L_raw
    gc.collect()

    if out_tcwb_path is not None:
        X_tcwb.flush()
        del X_tcwb
        X_tcwb = np.load(out_tcwb_path, mmap_mode="r")
    if out_ablation_path is not None:
        X_abl.flush()
        del X_abl
        X_abl = np.load(out_ablation_path, mmap_mode="r")

    qc["accessed_csv_columns"] = {k: list(v) for k, v in accessed_cols.items()}
    return {
        "X_tcwb": X_tcwb,
        "X_abl": X_abl,
        "L_tcwb": L_tcwb,
        "cover_propensity": cover_propensity,
        "valid": valid,
        "qc": qc,
    }
