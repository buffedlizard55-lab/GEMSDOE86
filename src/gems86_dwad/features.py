"""Translation-invariant 24-plane static feature stack builder for Lane H86S-DWAD."""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi

from src.gems86.io import BANDS
from src.gems86_bfra.operators import (
    broken_plate_flexural_shear_and_rollover,
    regolith_and_metasomatic_unmixing,
    tmi_vs_rtp_remanence_dislocation,
)
from src.gems86_slcq.operators import (
    adaptive_vector_updip_pullback,
    salem_adaptive_dip_and_sharpness,
)
from src.gems86_stdp.features import (
    BANNED_CSV_COLUMNS,
    _gdr_geothermal_planes,
    _geodawn_seam_keep_mask,
    _rank01,
    _read_ext,
    _read_native,
    _robust_pos_z,
    verify_stdp_input_contract,
)
from src.gems86_tcwb.operators import downslope_tc_wash_asymmetry
from .operators import (
    compute_survey_observability,
    downslope_canyon_knickzone_backprojection,
    mohr_coulomb_conjugate_slip_tendency,
    sub_claycap_geothermal_feeder_disjunction,
)

DWAD_STATIC_NAMES: tuple[str, ...] = (
    # Group A: Survey-observability / exposure geometry
    "obs_shallow_basement_exposure",
    "obs_topographic_relief_exposure",
    "obs_lidar1m_swath_coverage",
    # Group B: Downslope canyon-mouth fluvial knickzone back-projection (KNDS)
    "knds_canyon_ksn_excess",
    "knds_downslope_advected_800m",
    "knds_downslope_advected_1500m",
    "knds_piedmont_apex_basement_gate",
    "knds_cross_canyon_strike_coherence",
    # Group C: Sub-clay-cap hydrothermal feeder-margin & GDR vent disjunction
    "geo_claycap_lateral_margin",
    "geo_subcap_basement_feeder_conj",
    "geo_uphead_sinter_probe_wall",
    "geo_blind_vent_alignment_ridge",
    # Group D: Broken-plate subsurface, up-dip Salem, remanence, regolith & Mohr-Coulomb
    "sub_basement_flexural_shear",
    "sub_listric_hangingwall_rollover",
    "sub_updip_salem_grav_contact",
    "sub_updip_salem_rtp_contact",
    "sub_remanence_phase_dislocation",
    "sub_garland_poisson_admittance_jump",
    "rad_piedmont_provenance_unmix",
    "rad_hydro_k_over_th_metasom",
    "rad_tc_downslope_wash_step",
    "topo_debiased_lidar_dem10_scarp",
    "coulomb_critical_slip_tendency",
    "coulomb_transtens_dilatancy_swarm",
)

DWAD_ABLATION_NAMES: tuple[str, ...] = (
    "abl_local_chi_ksn_raw",
    "abl_local_cond_surf_raw",
    "abl_local_grav_slope_b5",
    "abl_local_tmi_hg_b3",
    "abl_local_det_elev_slope_b19",
    "abl_local_tc_b6",
)

DWAD_CONT_NAMES: tuple[str, ...] = (
    "dwad_cont_strike_bridge_1p8km",
    "dwad_cont_conjugate_stepover",
    "dwad_cont_tip_dilation_cone",
    "dwad_cont_far_basin_corridor",
)


def verify_dwad_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify all 19 native competition bands against ``src/gems86/io.py`` and external SHA-256 pins."""
    qc = verify_stdp_input_contract(ext_dir)
    qc["verified_native_bands"] = {str(k): v for k, v in sorted(BANDS.items())}
    return qc


def build_dwad_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_dwad_path: Path | None = None,
    out_ablation_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> dict[str, object]:
    """Build all 24 DWAD static planes, 6 point-local ablation planes, survey
    observability O(x), Band 8 dilatation, and multi-physics blind prior L_dwad."""
    with rasterio.open(feature_tif) as ds:
        if ds.count != 19:
            raise RuntimeError(f"Expected 19 native bands, got {ds.count}")
        H, W = ds.height, ds.width
        if footprint is None:
            b12_probe = ds.read(12)
            nodata = ds.nodata
            valid = np.isfinite(b12_probe)
            if nodata is not None and np.isfinite(nodata):
                valid &= b12_probe > float(nodata) * 0.5
            del b12_probe
        else:
            valid = np.asarray(footprint, dtype=bool)

        n_dwad = len(DWAD_STATIC_NAMES)
        n_abl = len(DWAD_ABLATION_NAMES)
        if out_dwad_path is not None:
            out_dwad_path.parent.mkdir(parents=True, exist_ok=True)
            X_dwad = open_memmap(out_dwad_path, mode="w+", dtype=np.float16, shape=(n_dwad, H, W))
        else:
            X_dwad = np.zeros((n_dwad, H, W), dtype=np.float16)
        if out_ablation_path is not None:
            out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
            X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, H, W))
        else:
            X_abl = np.zeros((n_abl, H, W), dtype=np.float16)

        def _put_dwad(name: str, arr: np.ndarray) -> None:
            idx = DWAD_STATIC_NAMES.index(name)
            z = _robust_pos_z(arr, valid)
            X_dwad[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

        def _put_abl(name: str, arr: np.ndarray) -> None:
            idx = DWAD_ABLATION_NAMES.index(name)
            z = _robust_pos_z(arr, valid)
            X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

        seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)

        # Read external 3DEP layers
        ksn_max = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 3, valid)
        log10_area = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 4, valid)
        zmean_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
        topo_relief = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 5, valid)
        topo_curv = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 6, valid)
        topo_line = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 8, valid)
        lid_step = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 3, valid)
        lid_coh = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 10, valid)
        lid_valid = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 12, valid)

        lahontan_band = np.exp(-(((zmean_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
            -(((zmean_m - 1205.0) / 15.0) ** 2)
        )
        lahontan_band = np.where(valid & (zmean_m > 900.0), lahontan_band, 0.0).astype(np.float32)

        zb_m = _read_native(ds, 15, valid)
        b19_slope = _read_native(ds, 19, valid)
        b12_det = _read_native(ds, 12, valid)

        # Group A: Survey-observability O(x)
        observability, obs_bed, obs_rel, obs_lid = compute_survey_observability(
            zb_m, b19_slope, topo_relief, lid_valid, valid, floor=0.15
        )
        _put_dwad("obs_shallow_basement_exposure", obs_bed)
        _put_dwad("obs_topographic_relief_exposure", obs_rel)
        _put_dwad("obs_lidar1m_swath_coverage", obs_lid)
        del obs_bed, obs_rel, obs_lid, topo_relief

        # Group B: Downslope canyon-mouth fluvial knickzone back-projection (KNDS)
        ksn_ex, adv_800, adv_1500, apex_gate, strike_coh = downslope_canyon_knickzone_backprojection(
            ksn_max, log10_area, zmean_m, zb_m, valid, steps_px=(8.0, 15.0)
        )
        _put_dwad("knds_canyon_ksn_excess", ksn_ex)
        _put_dwad("knds_downslope_advected_800m", adv_800)
        _put_dwad("knds_downslope_advected_1500m", adv_1500)
        _put_dwad("knds_piedmont_apex_basement_gate", apex_gate)
        _put_dwad("knds_cross_canyon_strike_coherence", strike_coh)
        _put_abl("abl_local_chi_ksn_raw", np.maximum(ksn_max, 0.0))
        _put_abl("abl_local_det_elev_slope_b19", np.maximum(b19_slope, 0.0))
        knds_prior = (0.52 * _rank01(apex_gate, valid) + 0.48 * _rank01(strike_coh, valid)).astype(
            np.float32
        )
        del ksn_max, log10_area, ksn_ex, adv_800, adv_1500, apex_gate, strike_coh

        # Debiased 1m LiDAR + 10m DEM scarp profile curvature (Lahontan shoreline suppressed)
        dem10_scarp = 0.55 * _rank01(topo_curv, valid) + 0.45 * _rank01(topo_line, valid)
        lid_mask = valid & (lid_valid > 0.5)
        lid_scarp = np.zeros((H, W), dtype=np.float32)
        if lid_mask.any():
            lid_scarp[lid_mask] = (
                0.55 * _rank01(lid_step, lid_mask)[lid_mask]
                + 0.45 * _rank01(lid_coh, lid_mask)[lid_mask]
            )
        scarp_fused = np.where(lid_mask, 0.58 * lid_scarp + 0.42 * dem10_scarp, dem10_scarp)
        scarp_debiased = (scarp_fused * (1.0 - 0.55 * np.clip(lahontan_band, 0.0, 1.0))).astype(
            np.float32
        )
        _put_dwad("topo_debiased_lidar_dem10_scarp", scarp_debiased)
        scarp_prior = _rank01(scarp_debiased, valid)
        del topo_curv, topo_line, lid_step, lid_coh, lid_valid, lid_mask, lid_scarp, scarp_fused, scarp_debiased

        # Group C: GDR #1391 + Sub-Clay-Cap Hydrothermal Feeder Disjunction
        accessed_columns: dict[str, tuple[str, ...]] = {}
        uphead_diseq, probe_wall, sinter_corridor, _ = _gdr_geothermal_planes(
            ext_dir, valid, zmean_m, accessed_columns
        )
        assert not any(set(cols) & BANNED_CSV_COLUMNS for cols in accessed_columns.values())
        del zmean_m

        b17_cond = _read_native(ds, 17, valid)
        b2_rtp = _read_native(ds, 2, valid)
        b5_gslope = _read_native(ds, 5, valid)
        b3_tmi_hg = _read_native(ds, 3, valid)
        _put_abl("abl_local_cond_surf_raw", np.maximum(b17_cond, 0.0))
        _put_abl("abl_local_grav_slope_b5", np.maximum(b5_gslope, 0.0))
        _put_abl("abl_local_tmi_hg_b3", np.maximum(b3_tmi_hg, 0.0))

        clay_margin, subcap_conj, th_wall, vent_ridge = sub_claycap_geothermal_feeder_disjunction(
            b17_cond, b2_rtp, b5_gslope, uphead_diseq, probe_wall, sinter_corridor, valid, seam_keep
        )
        _put_dwad("geo_claycap_lateral_margin", clay_margin)
        _put_dwad("geo_subcap_basement_feeder_conj", subcap_conj)
        _put_dwad("geo_uphead_sinter_probe_wall", th_wall)
        _put_dwad("geo_blind_vent_alignment_ridge", vent_ridge)
        geo_prior = (
            0.40 * _rank01(subcap_conj, valid)
            + 0.35 * _rank01(vent_ridge, valid)
            + 0.25 * _rank01(th_wall, valid)
        ).astype(np.float32)
        del uphead_diseq, probe_wall, sinter_corridor, clay_margin, subcap_conj, th_wall, vent_ridge

        # Group D: Subsurface broken-plate + up-dip Salem + remanence + regolith + Mohr-Coulomb
        b13_grav = _read_native(ds, 13, valid)
        b11_gvg = _read_native(ds, 11, valid)
        b18_ghg = _read_native(ds, 18, valid)
        b9_tvg = _read_native(ds, 9, valid)
        b1_mag = _read_native(ds, 1, valid)
        b14_tmi = _read_native(ds, 14, valid)

        g_sh, _, g_cr, g_cc = salem_adaptive_dip_and_sharpness(
            b13_grav, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        m_sh, _, m_cr, m_cc = salem_adaptive_dip_and_sharpness(
            b2_rtp, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        cot_r = (0.64 * g_cr + 0.36 * m_cr * seam_keep).astype(np.float32)
        cot_c = (0.64 * g_cc + 0.36 * m_cc * seam_keep).astype(np.float32)
        del g_cr, g_cc, m_cr, m_cc

        salem_grav = adaptive_vector_updip_pullback(g_sh, zb_m, cot_r, cot_c, valid)
        salem_rtp = adaptive_vector_updip_pullback(m_sh * seam_keep, zb_m, cot_r, cot_c, valid)
        _put_dwad("sub_updip_salem_grav_contact", salem_grav)
        _put_dwad("sub_updip_salem_rtp_contact", salem_rtp)
        del g_sh, m_sh, b13_grav

        d3_shear, rollover_raw, nr_basin, nc_basin = broken_plate_flexural_shear_and_rollover(
            zb_m, b11_gvg, b18_ghg, valid, sigmas_px=(3.0, 5.0)
        )
        d3_pull = adaptive_vector_updip_pullback(d3_shear, zb_m, cot_r, cot_c, valid)
        roll_pull = adaptive_vector_updip_pullback(rollover_raw, zb_m, cot_r, cot_c, valid)
        _put_dwad("sub_basement_flexural_shear", d3_pull)
        _put_dwad("sub_listric_hangingwall_rollover", roll_pull)
        del d3_shear, rollover_raw

        rem_raw = tmi_vs_rtp_remanence_dislocation(
            b14_tmi, b2_rtp, b1_mag, nr_basin, nc_basin, valid, seam_keep=seam_keep
        )
        rem_pull = adaptive_vector_updip_pullback(rem_raw, zb_m, cot_r, cot_c, valid)
        _put_dwad("sub_remanence_phase_dislocation", rem_pull)
        del b1_mag, b14_tmi, nr_basin, nc_basin, rem_raw, rem_pull, cot_r, cot_c

        # Garland cross-gradient Poisson admittance jump (Band 9 tmi_vg vs Band 5 grav_slope)
        t9_grad = np.hypot(
            ndi.gaussian_filter(b9_tvg, sigma=2.0, order=(1, 0), mode="nearest"),
            ndi.gaussian_filter(b9_tvg, sigma=2.0, order=(0, 1), mode="nearest"),
        )
        garland_jump = np.abs(_rank01(b5_gslope, valid) - _rank01(t9_grad * seam_keep, valid)) * (
            0.55 * _rank01(b5_gslope, valid) + 0.45 * _rank01(b3_tmi_hg * seam_keep, valid)
        )
        _put_dwad("sub_garland_poisson_admittance_jump", garland_jump)
        sub_prior = (
            0.40 * _rank01(salem_grav, valid)
            + 0.30 * _rank01(d3_pull, valid)
            + 0.30 * _rank01(salem_rtp, valid)
        ).astype(np.float32)
        del b9_tvg, b5_gslope, b3_tmi_hg, t9_grad, garland_jump, salem_grav, salem_rtp, d3_pull, roll_pull, zb_m

        # Regolith provenance unmixing + hydrothermal K/Th + downslope TC wash step
        b6_tc = _read_native(ds, 6, valid)
        _put_abl("abl_local_tc_b6", np.maximum(b6_tc, 0.0))
        rad_k = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid) + 1.0
        rad_th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid) + 1.0
        rad_u = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid) + 1.0
        reg_jump, hydro_meta = regolith_and_metasomatic_unmixing(
            b6_tc,
            rad_k,
            rad_th,
            rad_u,
            b12_det,
            b19_slope,
            b17_cond,
            valid,
            seam_keep=seam_keep,
            lahontan_band=lahontan_band,
            standoff_px=4.0,
        )
        _put_dwad("rad_piedmont_provenance_unmix", reg_jump)
        _put_dwad("rad_hydro_k_over_th_metasom", hydro_meta)
        tc_wash, _ = downslope_tc_wash_asymmetry(
            b6_tc,
            b12_det,
            valid,
            seam_keep=seam_keep,
            lahontan_band=lahontan_band,
            standoff_px=4.0,
        )
        _put_dwad("rad_tc_downslope_wash_step", tc_wash)
        del b6_tc, rad_k, rad_th, rad_u, b12_det, b19_slope, b17_cond, reg_jump, hydro_meta, tc_wash, lahontan_band, seam_keep

        # Mohr-Coulomb conjugate slip tendency + transtensional dilatancy swarm
        b4_2nd = _read_native(ds, 4, valid)
        b7_sh = _read_native(ds, 7, valid)
        b8_dil = _read_native(ds, 8, valid)
        b10_deq = _read_native(ds, 10, valid)
        b16_ieq = _read_native(ds, 16, valid)
        coul_ts, dil_swarm = mohr_coulomb_conjugate_slip_tendency(
            b4_2nd, b7_sh, b8_dil, b11_gvg, b18_ghg, b2_rtp, b10_deq, b16_ieq, valid
        )
        _put_dwad("coulomb_critical_slip_tendency", coul_ts)
        _put_dwad("coulomb_transtens_dilatancy_swarm", dil_swarm)
        coul_prior = _rank01(coul_ts, valid)
        del b4_2nd, b7_sh, b10_deq, b16_ieq, b11_gvg, b18_ghg, b2_rtp, coul_ts, dil_swarm

    # Corroborated multi-domain zero-catalogue prior (requires >=2 physical families agreeing)
    fams = np.stack([sub_prior, knds_prior, geo_prior, scarp_prior, coul_prior], axis=0)
    fams.sort(axis=0)
    # Geometric blend of top-1, top-2, and top-3 physical families suppresses single-sensor mimics
    L_dwad = np.where(
        valid,
        0.44 * fams[-2] + 0.34 * fams[-3] + 0.22 * fams[-1],
        np.float32(0.0),
    ).astype(np.float32)
    del fams, sub_prior, knds_prior, geo_prior, scarp_prior, coul_prior
    if hasattr(X_dwad, "flush"):
        X_dwad.flush()
    if hasattr(X_abl, "flush"):
        X_abl.flush()
    gc.collect()
    return {
        "X_dwad": X_dwad,
        "X_abl": X_abl,
        "observability": observability,
        "dilaterate_b8": b8_dil,
        "L_dwad": L_dwad,
        "valid": valid,
        "accessed_columns": accessed_columns,
    }
