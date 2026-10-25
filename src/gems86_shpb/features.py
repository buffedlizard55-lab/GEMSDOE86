"""Translation-invariant multi-physics feature builder for Lane H86N-SHPB.

Combines:
  1. Steerable Odd-Step vs Even-Dike Quadrature Phase-Asymmetry on vector gravity
     (Bands 11, 13, 18) and RTP/TMI_up150 (Band 2 + ext Band 4), bilinearly pulled
     back up-dip from hanging-wall depth Z_b along (-grad Z_b) by (Z_b/100)*cot(60 deg).
  2. Multi-altitude 2-D FFT Salem-Fairhead (2007) tilt-angle zero-contour sharpness
     and lateral dip-migration (z0=100 m vs z1=400 m).
  3. Oriented 2-D structure-tensor anisotropy of earthquake density/inverse-distance
     (Bands 10, 16) projected onto Kostrov normal-dilation and Riedel shear strain
     rates (Bands 4, 7, 8), plus aseismic creep deficit.
  4. Up-hydraulic-head advected DOE GDR #1391 silica/cation geothermometer
     disequilibrium + 2-m temperature probe thermal walls + paleo-sinter vents
     (strictly banning dist_known_fault_px).
  5. GeoDAWN survey-block seam-vetoed K/eTh and U/eTh steps + 10 m DEM quantile-debiased
     1 m 3DEP LiDAR scarps and fluvial chi knickzones.
"""

from __future__ import annotations

import gc
from pathlib import Path
import sys

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
for _p in (ROOT_DIR, SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems86_ksad.physics import (
    ELASTIC_FEATURE_NAMES as KSAD_ELASTIC_NAMES,
    compute_exposure_propensity,
    compute_kostrov_elastic_fields,
    kostrov_azimuthal_tendencies,
    spin2_from_row_col_grad,
)
from gems86_stdp.features import (
    ABLATION_LOCAL_NAMES as STDP_ABLATION_NAMES,
    STDP_STATIC_NAMES,
    _masked_gaussian,
    _rank01,
    _read_ext,
    _read_native,
    _robust_pos_z,
    build_stdp_static_stack,
    updip_hangingwall_pullback,
    verify_stdp_input_contract,
)

SHPB_STATIC_NAMES: tuple[str, ...] = (
    "odd_step_even_dike_grav_updip",
    "odd_step_even_dike_rtp_updip",
    "salem_rtp_tilt_zero_z100",
    "salem_grav_tilt_zero_z100",
    "salem_rtp_dip_migration",
    "salem_grav_dip_migration",
    "updip_pullback_monogenic",
    "updip_pullback_cond_neck",
    "intrabasin_keystone_hinge",
    "tmi_up150_wavenumber_si",
    "hydro_magnetite_destruction",
    "kostrov_dilation_tendency",
    "kostrov_riedel_slip_tendency",
    "eq_lineation_transtens_align",
    "aseismic_creep_deficit",
    "uphead_geotherm_diseq",
    "probe2m_uphead_thermal_wall",
    "paleo_sinter_vent_corridor",
    "rad_kth_alteration_seamfree",
    "rad_uth_redox_seamfree",
    "geotherm_conjugate_intersect",
    "lidar1m_scarp_swath_debiased",
    "topo10_piedmont_curv_break",
    "chi10_drainage_knick_step",
)

SHPB_ELASTIC_NAMES: tuple[str, ...] = tuple(KSAD_ELASTIC_NAMES)
ABLATION_LOCAL_NAMES: tuple[str, ...] = tuple(STDP_ABLATION_NAMES)


def verify_shpb_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify native band physics contract and SHA-256 external pins."""
    return verify_stdp_input_contract(ext_dir)


def steerable_odd_step_minus_even_dike(
    field: np.ndarray,
    valid: np.ndarray,
    *,
    gx_override: np.ndarray | None = None,
    gy_override: np.ndarray | None = None,
    sigmas: tuple[float, ...] = (1.6, 3.4),
) -> tuple[np.ndarray, np.ndarray]:
    """Compute multi-scale steerable odd-step vs even-dike quadrature phase-asymmetry.

    Along the local fault-normal unit vector n = (gx, gy) / (||g|| + eps), the first
    directional derivative is O_sigma = ||g_sigma||_2 (odd-symmetric, peaking at step
    inflection points), whereas the scale-normalized directional second derivative is
    E_sigma = sigma * |n^T H_sigma(field) n| (even-symmetric, peaking at volcanic dike
    and paleochannel ridge/trough crests where O_sigma -> 0).

    Returns:
      - ``asymmetry_pure``: contrast-invariant ratio (O - E) / (O + E + eps) in [-1, 1],
        strictly invariant to multiplying ``field`` (and overrides) by any c > 0.
      - ``step_score``: rectified odd-step dominance weighted by normalized gradient
        amplitude so homogeneous flat regions evaluate near zero.
    """
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    f_clean = np.where(v, f - _masked_gaussian(f, v, sigma=28.0), np.float32(0.0))

    asym_acc = np.zeros(f.shape, dtype=np.float32)
    score_acc = np.zeros(f.shape, dtype=np.float32)
    w_tot = 0.0

    for idx, sig in enumerate(sigmas):
        w = 0.60 if idx == 0 else 0.40
        sm = _masked_gaussian(f_clean, v, sigma=float(sig))
        if gx_override is not None and gy_override is not None:
            gx = _masked_gaussian(np.asarray(gx_override, dtype=np.float32), v, sigma=max(float(sig) - 0.5, 0.8))
            gy = _masked_gaussian(np.asarray(gy_override, dtype=np.float32), v, sigma=max(float(sig) - 0.5, 0.8))
        else:
            gx = ndi.gaussian_filter(sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
            gy = ndi.gaussian_filter(sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)

        g_mag = np.hypot(gx, gy).astype(np.float32)
        eps_g = float(max(np.percentile(g_mag[v], 15) * 1e-4, 1e-12)) if v.any() else 1e-12
        nx = gx / (g_mag + eps_g)
        ny = gy / (g_mag + eps_g)

        hxx = ndi.gaussian_filter(gx, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
        hyy = ndi.gaussian_filter(gy, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
        hxy = 0.5 * (
            ndi.gaussian_filter(gx, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
            + ndi.gaussian_filter(gy, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
        )
        # Scale-normalized directional second derivative along local normal n = (nx, ny)
        d2_nn = np.abs(nx * nx * hxx + 2.0 * nx * ny * hxy + ny * ny * hyy) * float(sig)
        del gx, gy, nx, ny, hxx, hyy, hxy

        asym_s = (g_mag - d2_nn) / (g_mag + d2_nn + eps_g)
        asym_acc += float(w) * np.where(v, asym_s, np.float32(0.0))

        g_p75 = float(max(np.percentile(g_mag[v], 75), 1e-6)) if v.any() else 1.0
        amp_gate = np.tanh(g_mag / g_p75).astype(np.float32)
        step_s = np.maximum(asym_s, np.float32(-0.15)) * amp_gate
        score_acc += float(w) * np.where(v, step_s, np.float32(0.0))
        w_tot += float(w)
        del g_mag, d2_nn, asym_s, amp_gate, step_s

    inv_w = np.float32(1.0 / max(w_tot, 1e-6))
    return (asym_acc * inv_w).astype(np.float32), (score_acc * inv_w).astype(np.float32)


def seismic_geodetic_lineation_alignment(
    b10_deq: np.ndarray,
    b16_ieq: np.ndarray,
    b7_shear: np.ndarray,
    b8_dilate: np.ndarray,
    b4_inv2: np.ndarray,
    valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute oriented 2-D structure-tensor anisotropy of earthquake lineations
    projected onto Great Basin Kostrov normal-dilation and Riedel shear strain rates.

    Returns:
      - ``anisotropy_alignment``: pure directional coherence * Kostrov azimuth factor in [0, 1].
      - ``coupled_score``: standardized seismic-geodetic transtensional conduit score.
    """
    v = np.asarray(valid, dtype=bool)
    deq_log = np.log1p(np.maximum(np.asarray(b10_deq, dtype=np.float32), 0.0))
    ieq_pos = np.maximum(np.asarray(b16_ieq, dtype=np.float32), 0.0)

    # High-pass seismic lineation potential
    deq_hp = deq_log - _masked_gaussian(deq_log, v, sigma=22.0)
    ieq_hp = ieq_pos - _masked_gaussian(ieq_pos, v, sigma=22.0)
    eq_field = 0.55 * _robust_pos_z(deq_hp, v) + 0.45 * _robust_pos_z(ieq_hp, v)
    del deq_log, ieq_pos, deq_hp, ieq_hp

    sm = _masked_gaussian(eq_field, v, sigma=1.4)
    dr_south = ndi.gaussian_filter(sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
    dc_east = ndi.gaussian_filter(sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)

    j_cc = ndi.gaussian_filter(dc_east * dc_east, sigma=2.8, mode="nearest").astype(np.float32)
    j_rr = ndi.gaussian_filter(dr_south * dr_south, sigma=2.8, mode="nearest").astype(np.float32)
    j_rc = ndi.gaussian_filter(2.0 * dr_south * dc_east, sigma=2.8, mode="nearest").astype(np.float32)
    trace = j_cc + j_rr + 1e-8
    diff = np.hypot(j_cc - j_rr, j_rc).astype(np.float32)
    coherence = np.clip(diff / trace, 0.0, 1.0).astype(np.float32)
    c2_eq = ((j_cc - j_rr) / (diff + 1e-8)).astype(np.float32)
    s2_eq = (j_rc / (diff + 1e-8)).astype(np.float32)
    del sm, dr_south, dc_east, j_cc, j_rr, j_rc, trace, diff

    # Project seismic lineation strike onto Great Basin N22E normal dilation & Riedel shear
    unit_ones = np.ones(v.shape, dtype=np.float32)
    k_dil_unit, k_sh_unit = kostrov_azimuthal_tendencies(c2_eq, s2_eq, unit_ones, unit_ones)
    az_align = np.where(v, coherence * (0.62 * k_dil_unit + 0.38 * k_sh_unit), np.float32(0.0)).astype(
        np.float32
    )
    del unit_ones, k_dil_unit, k_sh_unit, c2_eq, s2_eq

    dil_pos = np.maximum(np.asarray(b8_dilate, dtype=np.float32), 0.0)
    sh_pos = np.maximum(np.asarray(b7_shear, dtype=np.float32), 0.0)
    inv_pos = np.maximum(np.asarray(b4_inv2, dtype=np.float32), 0.0)
    strain_z = (
        0.45 * _robust_pos_z(dil_pos, v)
        + 0.35 * _robust_pos_z(sh_pos, v)
        + 0.20 * _robust_pos_z(inv_pos, v)
    )
    coupled = _robust_pos_z(az_align * np.maximum(eq_field, 0.0) * (1.0 + 0.35 * np.maximum(strain_z, 0.0)), v)
    return az_align, coupled


def build_shpb_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_shpb_path: Path,
    out_ablation_path: Path,
    stdp_cache_dir: Path | None = None,
    footprint: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Build or assemble the 24-plane H86N-SHPB static stack, corroboration prior,
    8-plane ablation control stack, and alluvial exposure propensity."""
    qc_contract = verify_shpb_input_contract(ext_dir)

    with rasterio.open(feature_tif) as ds:
        H, W = ds.height, ds.width
        b2_raw = ds.read(2).astype(np.float32)
        valid = (
            np.asarray(footprint, dtype=bool)
            if footprint is not None
            else (np.isfinite(b2_raw) & (b2_raw > -1e18))
        )
        del b2_raw

        # Build or load the verified H86K-STDP base stack to reuse shared planes cleanly
        s_dir = stdp_cache_dir if stdp_cache_dir is not None else out_shpb_path.parent / "stdp_base"
        s_dir.mkdir(parents=True, exist_ok=True)
        stdp_mm_path = s_dir / "h86k_X_stdp.npy"
        stdp_l_path = s_dir / "h86k_L_stdp.npy"
        if stdp_mm_path.is_file() and out_ablation_path.is_file() and stdp_l_path.is_file():
            X_stdp = np.load(stdp_mm_path, mmap_mode="r")
            X_abl = np.load(out_ablation_path, mmap_mode="r")
            L_stdp = np.load(stdp_l_path)
            qc_receipt_path = s_dir / "h86k_qc_receipt.json"
            if qc_receipt_path.is_file():
                import json
                qc_base = json.loads(qc_receipt_path.read_text(encoding="utf-8"))
            else:
                qc_base = qc_contract
        else:
            X_stdp, L_stdp, X_abl, _, qc_base = build_stdp_static_stack(
                feature_tif,
                ext_dir,
                out_stdp_path=stdp_mm_path,
                out_ablation_path=out_ablation_path,
                footprint=valid,
            )
            np.save(stdp_l_path, L_stdp)

        # Read native bands required for the 5 new H86N-SHPB physical operators
        b2_rtp = _read_native(ds, 2, valid)
        b4_inv2 = _read_native(ds, 4, valid)
        b7_shear = _read_native(ds, 7, valid)
        b8_dilate = _read_native(ds, 8, valid)
        b10_deq = _read_native(ds, 10, valid)
        b11_g_south = _read_native(ds, 11, valid)
        b13_grav = _read_native(ds, 13, valid)
        b15_zbase = np.maximum(_read_native(ds, 15, valid), np.float32(0.0))
        b16_ieq = _read_native(ds, 16, valid)
        b18_g_east = _read_native(ds, 18, valid)

    tmi_up150 = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid)

    # 1. Steerable odd-step vs even-dike phase-asymmetry on vector gravity (pulled back up-dip)
    _, grav_odd_step = steerable_odd_step_minus_even_dike(
        b13_grav,
        valid,
        gx_override=b18_g_east,
        gy_override=b11_g_south,
        sigmas=(1.6, 3.4),
    )
    grav_odd_updip_raw, _ = updip_hangingwall_pullback(
        _robust_pos_z(grav_odd_step, valid),
        b15_zbase,
        valid,
        dip_deg=60.0,
        max_shift_px=8.0,
        pulled_weight=0.68,
    )
    p0_grav_odd_updip = _robust_pos_z(grav_odd_updip_raw, valid)
    del grav_odd_step, grav_odd_updip_raw

    # 2. Steerable odd-step vs even-dike phase-asymmetry on RTP + TMI_up150 (pulled back up-dip)
    _, rtp_odd_step = steerable_odd_step_minus_even_dike(b2_rtp, valid, sigmas=(1.6, 3.4))
    _, up150_odd_step = steerable_odd_step_minus_even_dike(tmi_up150, valid, sigmas=(2.0, 4.0))
    mag_odd_comb = 0.62 * _robust_pos_z(rtp_odd_step, valid) + 0.38 * _robust_pos_z(up150_odd_step, valid)
    mag_odd_updip_raw, _ = updip_hangingwall_pullback(
        mag_odd_comb,
        b15_zbase,
        valid,
        dip_deg=60.0,
        max_shift_px=8.0,
        pulled_weight=0.68,
    )
    p1_rtp_odd_updip = _robust_pos_z(mag_odd_updip_raw, valid)
    del rtp_odd_step, up150_odd_step, mag_odd_comb, mag_odd_updip_raw, tmi_up150

    # 3. Coherent multi-physics spin-2 strike director & Kostrov azimuthal tendencies
    rtp_sm = _masked_gaussian(b2_rtp, valid, sigma=1.6)
    dr_rtp = ndi.gaussian_filter(rtp_sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
    dc_rtp = ndi.gaussian_filter(rtp_sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
    zb_sm = _masked_gaussian(b15_zbase, valid, sigma=2.2)
    dr_zb = ndi.gaussian_filter(zb_sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
    dc_zb = ndi.gaussian_filter(zb_sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
    del rtp_sm, zb_sm, b2_rtp, b13_grav, b15_zbase

    c2_g, s2_g, _ = spin2_from_row_col_grad(b11_g_south, b18_g_east, smooth_sigma=2.5)
    c2_m, s2_m, _ = spin2_from_row_col_grad(dr_rtp, dc_rtp, smooth_sigma=2.5)
    c2_b, s2_b, _ = spin2_from_row_col_grad(dr_zb, dc_zb, smooth_sigma=3.0)
    del b11_g_south, b18_g_east, dr_rtp, dc_rtp, dr_zb, dc_zb

    u_bar = 0.42 * c2_g + 0.33 * c2_m + 0.25 * c2_b
    v_bar = 0.42 * s2_g + 0.33 * s2_m + 0.25 * s2_b
    uv_norm = np.hypot(u_bar, v_bar) + 1e-8
    c2_phys = (u_bar / uv_norm).astype(np.float32)
    s2_phys = (v_bar / uv_norm).astype(np.float32)
    del c2_g, s2_g, c2_m, s2_m, c2_b, s2_b, u_bar, v_bar, uv_norm

    dil_hp = np.maximum(b8_dilate - _masked_gaussian(b8_dilate, valid, sigma=24.0), 0.0)
    sh_hp = np.maximum(b7_shear - _masked_gaussian(b7_shear, valid, sigma=24.0), 0.0)
    k_dil_raw, k_riedel_raw = kostrov_azimuthal_tendencies(
        c2_phys,
        s2_phys,
        _robust_pos_z(dil_hp, valid),
        _robust_pos_z(sh_hp, valid),
    )
    p11_kostrov_dil = _robust_pos_z(k_dil_raw, valid)
    p12_kostrov_riedel = _robust_pos_z(k_riedel_raw, valid)
    del c2_phys, s2_phys, dil_hp, sh_hp, k_dil_raw, k_riedel_raw

    # 4. Seismic-geodetic transtensional lineation alignment
    _, p13_eq_lineation = seismic_geodetic_lineation_alignment(
        b10_deq, b16_ieq, b7_shear, b8_dilate, b4_inv2, valid
    )
    del b10_deq, b16_ieq, b7_shear, b8_dilate, b4_inv2
    gc.collect()

    # Assemble the 24-plane float16 memmap
    out_shpb_path.parent.mkdir(parents=True, exist_ok=True)
    mm_shpb = open_memmap(
        out_shpb_path, mode="w+", dtype=np.float16, shape=(len(SHPB_STATIC_NAMES), H, W)
    )

    stdp_idx = {name: i for i, name in enumerate(STDP_STATIC_NAMES)}
    new_planes = {
        "odd_step_even_dike_grav_updip": p0_grav_odd_updip,
        "odd_step_even_dike_rtp_updip": p1_rtp_odd_updip,
        "kostrov_dilation_tendency": p11_kostrov_dil,
        "kostrov_riedel_slip_tendency": p12_kostrov_riedel,
        "eq_lineation_transtens_align": p13_eq_lineation,
    }

    for j, name in enumerate(SHPB_STATIC_NAMES):
        if name in new_planes:
            arr = new_planes[name]
        else:
            arr = X_stdp[stdp_idx[name]].astype(np.float32)
        mm_shpb[j] = np.clip(arr, -16.0, 16.0).astype(np.float16)

    mm_shpb.flush()

    # Enhanced blind corroboration prior incorporating steerable odd-step & seismic lineation
    l_odd = 0.50 * _rank01(p0_grav_odd_updip, valid) + 0.50 * _rank01(p1_rtp_odd_updip, valid)
    l_eq = _rank01(p13_eq_lineation, valid)
    L_shpb = _rank01(0.74 * L_stdp + 0.18 * l_odd + 0.08 * l_eq, valid)
    del new_planes, p0_grav_odd_updip, p1_rtp_odd_updip, p11_kostrov_dil, p12_kostrov_riedel, p13_eq_lineation
    gc.collect()

    c_exposure = compute_exposure_propensity(ext_dir, valid)

    qc_out = {
        **qc_base,
        "shpb_static_features": list(SHPB_STATIC_NAMES),
        "shpb_elastic_features": list(SHPB_ELASTIC_NAMES),
        "ablation_control_features": list(ABLATION_LOCAL_NAMES),
    }
    return mm_shpb, L_shpb, X_abl, c_exposure, qc_out
