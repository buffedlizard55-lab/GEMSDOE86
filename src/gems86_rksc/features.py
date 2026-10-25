"""Catalogue-blind feature operators for Lane H86I-RKSC.

Physical mechanism:
1. Asymmetric Piedmont Scarp Profile-Curvature Dipole (`training_features.tif`
   `Band 12 det_elev`, `Band 19 det_elev_slope`, plus `topo_10m_derived_100m_u8.tif`
   `Band 6 curv_prof_absmax` and `Band 9 dem_mean`):
   Late-Quaternary range-front and intrabasin normal faults cutting coalescing
   alluvial fans produce a slope-normal profile-curvature inflection
   `kappa_prof = -div(grad(z_det) / ||grad(z_det)||)` reinforced by 10m 3DEP
   profile curvature within the piedmont slope window (`Band 19`), deconfounded
   against Pleistocene Lake Lahontan contour-parallel strandlines (`Band 9 dem_mean`).
2. GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step (`training_features.tif`
   `Band 6 tc` [pixel-verified GeoDAWN Total Count TC] and `geodawn_rad_u8.tif`
   `Band 1 K`, `Band 2 Th`, `Band 3 U`, `Band 4 TC`):
   Thorium (`Th`) is geochemically immobile during hydrothermal alteration, whereas
   potassium (`K`) is enriched by adularia/illite K-metasomatism along fault conduits
   and steps sharply across juxtaposed footwall/hanging-wall fan provenance boundaries.
   We compute the immobile-normalized potassium index `R_K_Th = z(K) - 0.85 * z(Th)`
   and project its spatial gradient (together with `Band 6 tc` gradient) onto the
   local scarp-hinge spin-2 director.
3. Seismic-Geodetic-Argillic Conduit Favorability (`training_features.tif`
   `Band 4 geod_2ndinv`, `Band 7 geod_shearrate`, `Band 8 geod_dilaterate`,
   `Band 10 deq_n100a15`, `Band 16 ieq_n100a15`, `Band 17 cond_surf`):
   Permeable geothermal fault segments channel microseismic swarm activity (`B10`, `B16`),
   shallow smectite clay alteration gradients (`B17`), and transtensional strain
   release (`B4`, `B7`, `B8`).

Zero-leakage guarantee:
This module never reads any fault-catalogue layer or distance transform.
"""
from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems86.io import BANDS

NODATA_FLOOR = -1.0e37

REQUIRED_BANDS: dict[int, str] = {
    4: "geod_2ndinv",
    6: "tc",
    7: "geod_shearrate",
    8: "geod_dilaterate",
    10: "deq_n100a15",
    12: "det_elev",
    16: "ieq_n100a15",
    17: "cond_surf",
    19: "det_elev_slope",
}

FEATURE_NAMES: tuple[str, ...] = (
    "scarp_curvature_deconf",
    "scarp_tensor_anisotropy",
    "rad_kth_metasomatism_index",
    "rad_kth_step_concordant",
    "rad_depleted_lahontan_control",
    "seismic_upflow_gradient",
    "seismic_strain_conductance_gate",
)

ARM_NAMES: tuple[str, ...] = (
    "E1_rksc_full",
    "E2_rksc_rad_scarp_only",
    "E3_rksc_lahontan_uncorrected_control",
)


def verify_band_contract() -> None:
    """Verify every band index in REQUIRED_BANDS matches src/gems86/io.py::BANDS."""
    for idx, expected_name in REQUIRED_BANDS.items():
        actual = BANDS.get(idx)
        if actual != expected_name:
            raise ValueError(f"Band {idx} mismatch: expected {expected_name!r}, got {actual!r}")


def _clean_band(arr: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    fp = np.asarray(footprint, dtype=bool)
    raw = np.asarray(arr, dtype=np.float32)
    valid = fp & np.isfinite(raw) & (raw > NODATA_FLOOR) & (np.abs(raw) < 1e20)
    med = float(np.median(raw[valid])) if np.any(valid) else 0.0
    centered = np.where(valid, raw - np.float32(med), np.float32(0.0)).astype(np.float32)
    return centered, valid


def _masked_gaussian(
    arr: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    order: tuple[int, int] = (0, 0),
) -> np.ndarray:
    w = ndi.gaussian_filter(valid.astype(np.float32), sigma=float(sigma), mode="constant", cval=0.0)
    num = ndi.gaussian_filter(
        arr.astype(np.float32), sigma=float(sigma), order=order, mode="constant", cval=0.0
    )
    out = np.zeros_like(num, dtype=np.float32)
    ok = valid & (w > 0.25)
    out[ok] = num[ok] / np.maximum(w[ok], np.float32(1e-6))
    return out


def _robust_z(arr: np.ndarray, valid: np.ndarray, clip: float = 6.0) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    ok = valid & np.isfinite(arr)
    if not np.any(ok):
        return out
    vals = arr[ok]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826
    if not np.isfinite(mad) or mad < 1e-6:
        mad = float(np.std(vals))
    if not np.isfinite(mad) or mad < 1e-6:
        return out
    z = np.clip((vals - np.float32(med)) / np.float32(mad), -clip, clip)
    out[ok] = z.astype(np.float32)
    return out


def _sigmoid(x: np.ndarray) -> np.ndarray:
    xc = np.clip(x.astype(np.float32, copy=False), np.float32(-12.0), np.float32(12.0))
    return (np.float32(1.0) / (np.float32(1.0) + np.exp(-xc))).astype(np.float32)


def _unit01(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    fp = np.asarray(footprint, dtype=bool)
    out = np.zeros(arr.shape, dtype=np.float32)
    ok = fp & np.isfinite(arr)
    if not np.any(ok):
        return out
    vals = arr[ok]
    lo = float(np.percentile(vals, 1.0))
    hi = float(np.percentile(vals, 99.5))
    if not np.isfinite(hi - lo) or (hi - lo) < 1e-8:
        lo = float(np.min(vals))
        hi = float(np.max(vals))
    if not np.isfinite(hi - lo) or (hi - lo) < 1e-8:
        return out
    out[ok] = np.clip((vals - np.float32(lo)) / np.float32(hi - lo), 0.0, 1.0).astype(np.float32)
    return out


def _spin2_director(
    gy: np.ndarray,
    gx: np.ndarray,
    valid: np.ndarray,
    tensor_sigma: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return spin-2 orientation `(cos2, sin2, coh)` of gradient field `(gy, gx)`."""
    jxx = _masked_gaussian(gx * gx, valid, sigma=tensor_sigma)
    jyy = _masked_gaussian(gy * gy, valid, sigma=tensor_sigma)
    jxy = _masked_gaussian(gx * gy, valid, sigma=tensor_sigma)
    tr = np.maximum(jxx + jyy, np.float32(1e-12))
    dx = jxx - jyy
    dy = np.float32(2.0) * jxy
    mag = np.hypot(dx, dy).astype(np.float32)
    coh = np.where(valid, np.clip(mag / tr, 0.0, 1.0), np.float32(0.0)).astype(np.float32)
    denom = np.maximum(mag, np.float32(1e-12))
    cos2 = np.where(valid, dx / denom, np.float32(0.0)).astype(np.float32)
    sin2 = np.where(valid, dy / denom, np.float32(0.0)).astype(np.float32)
    return cos2, sin2, coh


def compute_rksc_arrays(
    *,
    b4_geod_2ndinv: np.ndarray,
    b6_rad_tc: np.ndarray,
    b7_geod_shearrate: np.ndarray,
    b8_geod_dilaterate: np.ndarray,
    b10_deq: np.ndarray,
    b12_det_elev: np.ndarray,
    b16_ieq: np.ndarray,
    b17_cond_surf: np.ndarray,
    b19_det_elev_slope: np.ndarray,
    rad_k_u8: np.ndarray,
    rad_th_u8: np.ndarray,
    rad_u_u8: np.ndarray,
    topo10_curv_u8: np.ndarray,
    topo10_dem_u8: np.ndarray,
    footprint: np.ndarray,
    sigma_scarp_px: float = 3.0,
    sigma_rad_px: float = 2.5,
    sigma_tensor_px: float = 5.0,
) -> dict[str, np.ndarray]:
    """Compute all 7 bounded `[0, 1]` catalogue-blind feature planes for H86I-RKSC."""
    verify_band_contract()
    fp = np.asarray(footprint, dtype=bool)
    core = ndi.binary_erosion(fp, iterations=3)
    if not np.any(core):
        core = fp.copy()

    # Block 1: Piedmont Scarp Profile-Curvature Dipole & Spin-2 Director (Bands 12, 19 + 10m 3DEP)
    c12, v12 = _clean_band(b12_det_elev, fp)
    c19, v19 = _clean_band(b19_det_elev_slope, fp)
    ccurv, vcurv = _clean_band(topo10_curv_u8, fp)
    cdem, vdem = _clean_band(topo10_dem_u8, fp)
    valid_topo = core & v12 & v19 & vcurv & vdem
    if not np.any(valid_topo):
        valid_topo = fp & v12

    z_det_s = _masked_gaussian(c12, v12, sigma=sigma_scarp_px)
    gy_z = _masked_gaussian(z_det_s, v12, sigma=1.5, order=(1, 0))
    gx_z = _masked_gaussian(z_det_s, v12, sigma=1.5, order=(0, 1))
    grad_z_mag = np.hypot(gx_z, gy_z).astype(np.float32)
    scale_g = float(np.percentile(grad_z_mag[valid_topo], 50.0)) if np.any(valid_topo) else 1.0
    denom_g = np.maximum(grad_z_mag, np.float32(max(0.15 * scale_g, 1e-4)))
    ny_z = np.where(v12, gy_z / denom_g, np.float32(0.0)).astype(np.float32)
    nx_z = np.where(v12, gx_z / denom_g, np.float32(0.0)).astype(np.float32)

    dnx_dx = _masked_gaussian(nx_z, v12, sigma=1.5, order=(0, 1))
    dny_dy = _masked_gaussian(ny_z, v12, sigma=1.5, order=(1, 0))
    kappa_prof = -(dnx_dx + dny_dy)
    del nx_z, ny_z, dnx_dx, dny_dy, z_det_s

    z_kappa = np.abs(_robust_z(kappa_prof, valid_topo)).astype(np.float32)
    del kappa_prof
    z_curv10 = _sigmoid(_robust_z(_masked_gaussian(ccurv, vcurv, sigma=1.8), valid_topo))
    del ccurv, vcurv
    z_grad_det = _robust_z(grad_z_mag, valid_topo)
    del grad_z_mag

    z_slope19 = _robust_z(c19, valid_topo)
    z_abs_det12 = _robust_z(np.abs(c12), valid_topo)
    del c12, c19, v19
    piedmont_window = (
        np.exp(np.float32(-0.5) * ((z_slope19 - np.float32(0.55)) / np.float32(1.35)) ** 2)
        * np.exp(np.float32(-0.5) * ((z_abs_det12 - np.float32(0.25)) / np.float32(1.75)) ** 2)
    ).astype(np.float32)
    del z_abs_det12

    scarp_cos2, scarp_sin2, scarp_coh = _spin2_director(
        gy_z, gx_z, valid_topo, tensor_sigma=sigma_tensor_px
    )
    del gy_z, gx_z

    raw_dem_u8 = np.where(vdem, np.asarray(topo10_dem_u8, dtype=np.float32), np.float32(0.0))
    elev_s = _masked_gaussian(cdem, vdem, sigma=sigma_scarp_px)
    del cdem
    gy_e = _masked_gaussian(elev_s, vdem, sigma=1.5, order=(1, 0))
    gx_e = _masked_gaussian(elev_s, vdem, sigma=1.5, order=(0, 1))
    del elev_s
    elev_cos2, elev_sin2, _ = _spin2_director(
        gy_e, gx_e, valid_topo, tensor_sigma=sigma_tensor_px
    )
    del gy_e, gx_e, vdem
    contour_align = np.clip(
        np.float32(0.5) * (np.float32(1.0) + scarp_cos2 * elev_cos2 + scarp_sin2 * elev_sin2),
        0.0,
        1.0,
    ).astype(np.float32)
    del elev_cos2, elev_sin2

    lahontan_elev_weight = np.exp(
        np.float32(-0.5) * ((raw_dem_u8 - np.float32(58.0)) / np.float32(22.0)) ** 2
    ).astype(np.float32)
    del raw_dem_u8
    lahontan_mimic = np.where(
        valid_topo,
        lahontan_elev_weight * contour_align * _sigmoid(np.float32(-0.6) * z_slope19),
        np.float32(0.0),
    ).astype(np.float32)
    del lahontan_elev_weight, contour_align, z_slope19

    raw_scarp_deconf = (
        (np.float32(0.65) * z_kappa + np.float32(0.35) * z_curv10)
        * (np.float32(0.45) + np.float32(0.55) * _sigmoid(z_grad_det))
        * (np.float32(0.35) + np.float32(0.65) * piedmont_window)
        * (np.float32(1.0) - np.float32(0.60) * lahontan_mimic)
    ).astype(np.float32)
    scarp_curvature_deconf = _unit01(np.where(valid_topo, raw_scarp_deconf, np.float32(0.0)), fp)
    scarp_tensor_anisotropy = _unit01(
        np.where(
            valid_topo,
            scarp_coh * (np.float32(0.4) + np.float32(0.6) * _sigmoid(z_grad_det)),
            np.float32(0.0),
        ),
        fp,
    )
    del raw_scarp_deconf, z_curv10, z_grad_det, piedmont_window, scarp_coh

    # Block 2: GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step
    c6, v6 = _clean_band(b6_rad_tc, fp)
    ck, vk = _clean_band(rad_k_u8, fp)
    cth, vth = _clean_band(rad_th_u8, fp)
    cu, vu = _clean_band(rad_u_u8, fp)
    valid_rad = valid_topo & v6 & vk & vth & vu
    if not np.any(valid_rad):
        valid_rad = valid_topo

    k_smooth = _masked_gaussian(ck, vk, sigma=sigma_rad_px)
    th_smooth = _masked_gaussian(cth, vth, sigma=sigma_rad_px)
    u_smooth = _masked_gaussian(cu, vu, sigma=sigma_rad_px)
    tc_smooth = _masked_gaussian(c6, v6, sigma=sigma_rad_px)
    del ck, vk, cth, vth, cu, vu, c6, v6

    z_k = _robust_z(k_smooth, valid_rad)
    z_th = _robust_z(th_smooth, valid_rad)
    z_u = _robust_z(u_smooth, valid_rad)
    z_tc = _robust_z(tc_smooth, valid_rad)
    del k_smooth, th_smooth, u_smooth, tc_smooth

    r_k_th = (z_k - np.float32(0.85) * z_th + np.float32(0.20) * (z_u - z_th)).astype(np.float32)
    del z_k, z_th, z_u
    rad_kth_metasomatism_index = _unit01(
        np.where(valid_rad, _sigmoid(np.float32(0.9) * r_k_th + np.float32(0.25) * z_tc), np.float32(0.0)),
        fp,
    )

    gy_rk = _masked_gaussian(r_k_th, valid_rad, sigma=1.8, order=(1, 0))
    gx_rk = _masked_gaussian(r_k_th, valid_rad, sigma=1.8, order=(0, 1))
    grad_rk_mag = np.hypot(gx_rk, gy_rk).astype(np.float32)

    gy_tc = _masked_gaussian(z_tc, valid_rad, sigma=1.8, order=(1, 0))
    gx_tc = _masked_gaussian(z_tc, valid_rad, sigma=1.8, order=(0, 1))
    grad_tc_mag = np.hypot(gx_tc, gy_tc).astype(np.float32)
    del z_tc

    rad_cos2, rad_sin2, rad_coh = _spin2_director(
        gy_rk + np.float32(0.6) * gy_tc,
        gx_rk + np.float32(0.6) * gx_tc,
        valid_rad,
        tensor_sigma=sigma_tensor_px,
    )
    del gy_rk, gx_rk, gy_tc, gx_tc

    rad_scarp_concord = np.clip(
        np.float32(0.5) * (np.float32(1.0) + scarp_cos2 * rad_cos2 + scarp_sin2 * rad_sin2),
        0.0,
        1.0,
    ).astype(np.float32)
    del scarp_cos2, scarp_sin2, rad_cos2, rad_sin2

    z_grad_rk = _robust_z(grad_rk_mag, valid_rad)
    z_grad_tc = _robust_z(grad_tc_mag, valid_rad)
    del grad_rk_mag, grad_tc_mag

    raw_rad_step = (
        _sigmoid(np.float32(0.85) * z_grad_rk + np.float32(0.45) * z_grad_tc)
        * (np.float32(0.35) + np.float32(0.65) * rad_scarp_concord)
        * (np.float32(0.40) + np.float32(0.60) * rad_coh)
        * (np.float32(0.35) + np.float32(0.65) * _sigmoid(np.float32(0.8) * r_k_th))
    ).astype(np.float32)
    rad_kth_step_concordant = _unit01(np.where(valid_rad, raw_rad_step, np.float32(0.0)), fp)
    del raw_rad_step, z_grad_rk, z_grad_tc, rad_coh

    raw_control = (
        z_kappa
        * (np.float32(1.0) + np.float32(0.65) * lahontan_mimic)
        * _sigmoid(np.float32(-0.85) * r_k_th)
        * (np.float32(1.0) - np.float32(0.50) * rad_scarp_concord)
    ).astype(np.float32)
    rad_depleted_lahontan_control = _unit01(np.where(valid_rad, raw_control, np.float32(0.0)), fp)
    del raw_control, z_kappa, lahontan_mimic, r_k_th, rad_scarp_concord

    # Block 3: Microseismic Swarm Proximity & Intensity Gradient (Bands 10, 16)
    c10, v10 = _clean_band(b10_deq, fp)
    c16, v16 = _clean_band(b16_ieq, fp)
    valid_seis = valid_topo & v10 & v16
    if not np.any(valid_seis):
        valid_seis = valid_topo
    deq_s = _masked_gaussian(c10, v10, sigma=3.5)
    ieq_s = _masked_gaussian(c16, v16, sigma=3.5)
    del c10, v10, c16
    z_prox_eq = -_robust_z(deq_s, valid_seis)
    del deq_s
    z_ieq = _robust_z(ieq_s, valid_seis)
    grad_ieq = np.hypot(
        _masked_gaussian(ieq_s, v16, sigma=2.5, order=(0, 1)),
        _masked_gaussian(ieq_s, v16, sigma=2.5, order=(1, 0)),
    ).astype(np.float32)
    del ieq_s, v16
    z_gieq = _robust_z(grad_ieq, valid_seis)
    del grad_ieq
    raw_seismic_upflow = _sigmoid(
        np.float32(0.50) * z_ieq + np.float32(0.45) * z_prox_eq + np.float32(0.40) * z_gieq
    )
    seismic_upflow_gradient = _unit01(
        np.where(valid_seis, raw_seismic_upflow, np.float32(0.0)), fp
    )
    del raw_seismic_upflow, z_ieq, z_prox_eq, z_gieq

    # Block 4: Geodetic Transtension + Shallow Argillic Conductance Gate (Bands 4, 7, 8, 17)
    c4, v4 = _clean_band(b4_geod_2ndinv, fp)
    c7, v7 = _clean_band(b7_geod_shearrate, fp)
    c8, v8 = _clean_band(b8_geod_dilaterate, fp)
    c17, v17 = _clean_band(b17_cond_surf, fp)
    valid_strain = valid_topo & v4 & v7 & v8 & v17
    if not np.any(valid_strain):
        valid_strain = valid_topo

    inv2_s = _masked_gaussian(c4, v4, sigma=3.5)
    sh_s = _masked_gaussian(c7, v7, sigma=3.5)
    dl_s = _masked_gaussian(c8, v8, sigma=3.5)
    cd_s = _masked_gaussian(c17, v17, sigma=3.0)
    del c4, v4, c7, v7, c8, v8, c17

    z_inv2 = _robust_z(inv2_s, valid_strain)
    z_sh = _robust_z(sh_s, valid_strain)
    z_dl = _robust_z(dl_s, valid_strain)
    z_cd = _robust_z(cd_s, valid_strain)
    del inv2_s, sh_s, dl_s
    grad_cd = np.hypot(
        _masked_gaussian(cd_s, v17, sigma=2.0, order=(0, 1)),
        _masked_gaussian(cd_s, v17, sigma=2.0, order=(1, 0)),
    ).astype(np.float32)
    del cd_s, v17
    z_gcd = _robust_z(grad_cd, valid_strain)
    del grad_cd
    cond_clay_gate = (
        np.exp(np.float32(-0.5) * ((z_cd - np.float32(0.25)) / np.float32(1.65)) ** 2)
        * _sigmoid(np.float32(0.75) * z_gcd)
    ).astype(np.float32)
    raw_seis_strain = (
        _sigmoid(np.float32(0.45) * z_inv2 + np.float32(0.45) * z_sh + np.float32(0.45) * z_dl)
        * (np.float32(0.45) + np.float32(0.55) * cond_clay_gate)
    ).astype(np.float32)
    seismic_strain_conductance_gate = _unit01(
        np.where(valid_strain, raw_seis_strain, np.float32(0.0)), fp
    )
    del z_inv2, z_sh, z_dl, z_cd, z_gcd, cond_clay_gate, raw_seis_strain

    return {
        "scarp_curvature_deconf": scarp_curvature_deconf,
        "scarp_tensor_anisotropy": scarp_tensor_anisotropy,
        "rad_kth_metasomatism_index": rad_kth_metasomatism_index,
        "rad_kth_step_concordant": rad_kth_step_concordant,
        "rad_depleted_lahontan_control": rad_depleted_lahontan_control,
        "seismic_upflow_gradient": seismic_upflow_gradient,
        "seismic_strain_conductance_gate": seismic_strain_conductance_gate,
    }


def compose_rksc_arms(
    planes: dict[str, np.ndarray],
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compose the 3 preregistered H86I-RKSC experimental surfaces in `[0, 1]`."""
    fp = np.asarray(footprint, dtype=bool)
    scarp = planes["scarp_curvature_deconf"]
    aniso = planes["scarp_tensor_anisotropy"]
    rad_idx = planes["rad_kth_metasomatism_index"]
    rad_step = planes["rad_kth_step_concordant"]
    ctrl = planes["rad_depleted_lahontan_control"]
    upflow = planes["seismic_upflow_gradient"]
    strain = planes["seismic_strain_conductance_gate"]

    e1_raw = (
        (np.float32(0.52) * scarp + np.float32(0.48) * rad_step)
        * (np.float32(0.40) + np.float32(0.60) * aniso)
        * (np.float32(0.45) + np.float32(0.55) * rad_idx)
        * (np.float32(0.45) + np.float32(0.30) * upflow + np.float32(0.25) * strain)
    ).astype(np.float32)
    e1 = _unit01(e1_raw, fp)

    e2_raw = (
        (np.float32(0.52) * scarp + np.float32(0.48) * rad_step)
        * (np.float32(0.40) + np.float32(0.60) * aniso)
        * (np.float32(0.45) + np.float32(0.55) * rad_idx)
    ).astype(np.float32)
    e2 = _unit01(e2_raw, fp)

    e3_raw = (
        ctrl
        * (np.float32(1.0) - np.float32(0.35) * upflow)
        * (np.float32(1.0) - np.float32(0.35) * strain)
    ).astype(np.float32)
    e3 = _unit01(e3_raw, fp)

    return {
        "E1_rksc_full": e1,
        "E2_rksc_rad_scarp_only": e2,
        "E3_rksc_lahontan_uncorrected_control": e3,
    }


def compute_rksc_from_tif(
    tif_path: Path,
    geodawn_path: Path,
    topo10_path: Path,
    footprint: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Read required bands from `training_features.tif`, `geodawn_rad_u8.tif`, and `topo_10m_derived_100m_u8.tif`."""
    verify_band_contract()
    with rasterio.open(tif_path) as src:
        b4 = src.read(4)
        b6 = src.read(6)
        b7 = src.read(7)
        b8 = src.read(8)
        b10 = src.read(10)
        b12 = src.read(12)
        b16 = src.read(16)
        b17 = src.read(17)
        b19 = src.read(19)
    with rasterio.open(geodawn_path) as src_g:
        rad_k = src_g.read(1)
        rad_th = src_g.read(2)
        rad_u = src_g.read(3)
    with rasterio.open(topo10_path) as src_t:
        topo_curv = src_t.read(6)
        topo_dem = src_t.read(9)

    planes = compute_rksc_arrays(
        b4_geod_2ndinv=b4,
        b6_rad_tc=b6,
        b7_geod_shearrate=b7,
        b8_geod_dilaterate=b8,
        b10_deq=b10,
        b12_det_elev=b12,
        b16_ieq=b16,
        b17_cond_surf=b17,
        b19_det_elev_slope=b19,
        rad_k_u8=rad_k,
        rad_th_u8=rad_th,
        rad_u_u8=rad_u,
        topo10_curv_u8=topo_curv,
        topo10_dem_u8=topo_dem,
        footprint=footprint,
    )
    del b4, b6, b7, b8, b10, b12, b16, b17, b19, rad_k, rad_th, rad_u, topo_curv, topo_dem
    gc.collect()
    arms = compose_rksc_arms(planes, footprint)
    return planes, arms
