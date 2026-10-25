"""Riedel-Listric Multi-Scale (RLMS) static & fold-visible feature planes.

Physical & coordinate conventions verified pixel-by-pixel against
``src/gems86/io.py`` and SHA-256-pinned USGS 3DEP / GeoDAWN external rasters:
- Band 6 (``tc``) is GeoDAWN Radiometric Total Count; true analytical magnetic
  tilt is ``atan2(Band 9 mag_vzz, sqrt(Band 3 mag_hzz^2 + h0^2))``.
- ``(+Band 18 grav_ew_hzz, -Band 11 grav_ns_hzz)`` is Cartesian ``(dg/dx_E, dg/dy_N)``;
  source-free Laplace vertical curvature is ``g_zz = -(d_col B18 + d_row B11)`` and
  curl defect is ``d_row B18 - d_col B11``.
- Gauge-invariant 2D gradient structure tensor ``J = G_tau(grad u grad u^T)``
  yields branch-cut-free spin-2 strike director ``(c2, s2) = (cos 2psi, sin 2psi)``
  in image ``(dx_col, dy_row)`` coordinates matching ``lidar_scarp_features_u8``
  Band 11 ``(strike / 256) * pi`` across steps, crests, and troughs alike.
- Hanging-wall down-dip unit vector ``n_HW`` points down-basin along smoothed
  ``+grad(Band 15 depth_to_base_surf) - grad(Band 13 cba)``, projecting 500 m
  and 1,100 m deep hanging-wall gravity/MT anomalies up-dip onto the emergent
  sub-alluvial footwall trace.
"""
from __future__ import annotations

import gc
import hashlib
from pathlib import Path

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from scipy import ndimage as ndi

from gems86.io import read_band

NATIVE_STATIC_NAMES: tuple[str, ...] = (
    # Harmonic potential-field & Cordell compaction-stripped horst core
    "tilt_miller",
    "verduzco_tilt_contact",
    "mag_trough_alter",
    "gzz_laplace_zero",
    "grav_hgrad_s2",
    "cordell_horst_grad",
    "base_hinge_curv",
    # Listric hanging-wall -> footwall up-dip spatial projections
    "listric_updip_grav_l5",
    "listric_updip_grav_l11",
    "listric_updip_cond_l8",
    "listric_throw_asymmetry",
    # Spin-2 nematic multi-physics director coherence & E-W flight-line veto
    "nematic_grav_mag_coh",
    "ew_flightline_veto",
    "nematic_sub_c2",
    "nematic_sub_s2",
    # Crustal fluids, principal geodetic strain, microseismicity & native DEM
    "cond_smectite_s2",
    "remanence_rtp_tmi_contrast",
    "tc_decouple_quiet",
    "strain_eig_ext1",
    "strain_transtens_regime",
    "eq_prox_exp",
    "dem_hess_scarp_s2",
    "dem_hess_scarp_s5",
    "piedmont_relief_ratio",
    "slope_local",
)

EXTERNAL_STATIC_NAMES: tuple[str, ...] = (
    # SHA-pinned USGS 3DEP 1m LiDAR (NaN-routed on uncovered tiles + Lahontan veto)
    "lidar_scarp_step_clean",
    "lidar_scarp_relief_asym",
    "lidar_nematic_sub_align",
    # SHA-pinned USGS 3DEP 10m seamless DEM & fluvial chi disequilibrium
    "topo10_microscarp_excess",
    "topo10_lineament_coh",
    "chi10_knickpoint_halo",
    "chi10_ksn_diseq",
    # SHA-pinned USGS GeoDAWN ternary K/eTh hydrothermal metasomatism
    "geodawn_k_th_metasom",
)

ALL_STATIC_NAMES: tuple[str, ...] = NATIVE_STATIC_NAMES + EXTERNAL_STATIC_NAMES

# Unprojected scalar baseline subset for Ablation Arm E3
E3_SCALAR_SUBSET: tuple[str, ...] = (
    "grav_hgrad_s2",
    "base_hinge_curv",
    "cond_smectite_s2",
    "remanence_rtp_tmi_contrast",
    "tc_decouple_quiet",
    "strain_transtens_regime",
    "eq_prox_exp",
    "dem_hess_scarp_s2",
    "dem_hess_scarp_s5",
    "piedmont_relief_ratio",
    "slope_local",
)

CONTINUATION_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
    "riedel_nematic_align",
    "conjugate_relay_obliquity",
)

EXTERNAL_PINS: dict[str, tuple[str, str]] = {
    "lidar_scarp": (
        "lidar_scarp_features_u8.tif",
        "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
    ),
    "topo_10m": (
        "topo_10m_derived_100m_u8.tif",
        "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
    ),
    "dem10_chi": (
        "dem10_chi_100m_i16.tif",
        "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
    ),
    "geodawn_rad": (
        "geodawn_rad_u8.tif",
        "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    ),
    "geodawn_ext": (
        "geodawn_extensions_u8.tif",
        "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    ),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_external_rasters(ext_dir: Path) -> dict[str, str]:
    verified: dict[str, str] = {}
    for key, (fname, expected) in EXTERNAL_PINS.items():
        p = ext_dir / fname
        if not p.is_file():
            raise FileNotFoundError(f"missing pinned external USGS raster {key}: {p}")
        actual = _sha256(p)
        if actual != expected:
            raise ValueError(f"external SHA-256 mismatch for {key}: {actual} != {expected}")
        verified[key] = actual
    return verified


def _fill_outside(arr: np.ndarray, fp: np.ndarray, nearest_idx: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    valid = fp & np.isfinite(arr) & (np.abs(arr) < 1e20)
    out = np.asarray(arr, dtype=np.float32).copy()
    if not valid.any():
        return np.zeros_like(out)
    if (~valid).any():
        if np.array_equal(valid, fp):
            out[~valid] = out[nearest_idx[0][~valid], nearest_idx[1][~valid]]
        else:
            _, idx = ndi.distance_transform_edt(~valid, return_indices=True)
            out[~valid] = out[idx[0][~valid], idx[1][~valid]]
    return out


def _robust_std(arr: np.ndarray, fp: np.ndarray, valid_mask: np.ndarray | None = None) -> np.ndarray:
    m = fp if valid_mask is None else (fp & valid_mask)
    vals = arr[m]
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75) - np.percentile(vals, 25))
    scale = iqr if iqr > 1e-6 else float(np.std(vals))
    if scale <= 1e-8:
        scale = 1.0
    out = np.clip((arr.astype(np.float32) - med) / scale, -12.0, 12.0)
    out[~fp] = 0.0
    if valid_mask is not None:
        out[fp & (~valid_mask)] = np.nan
    return out


def _hessian_ridge_abs(arr: np.ndarray, sigma: float) -> np.ndarray:
    hyy = ndi.gaussian_filter(arr, sigma, order=(2, 0))
    hxx = ndi.gaussian_filter(arr, sigma, order=(0, 2))
    hyx = ndi.gaussian_filter(arr, sigma, order=(1, 1))
    tr = 0.5 * (hxx + hyy)
    rad = np.hypot(0.5 * (hxx - hyy), hyx)
    return (np.maximum(np.abs(tr + rad), np.abs(tr - rad)) * (sigma ** 2)).astype(np.float32)


def _structure_nematic(
    arr: np.ndarray, fp: np.ndarray, grad_sigma: float = 1.5, tensor_sigma: float = 3.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gauge-invariant spin-2 strike director ``(c2, s2, weight)`` in image ``(dx, dy)``."""
    gx = ndi.gaussian_filter(arr, grad_sigma, order=(0, 1))
    gy = ndi.gaussian_filter(arr, grad_sigma, order=(1, 0))
    jxx = ndi.gaussian_filter(gx * gx, tensor_sigma)
    jyy = ndi.gaussian_filter(gy * gy, tensor_sigma)
    jxy = ndi.gaussian_filter(gx * gy, tensor_sigma)
    del gx, gy
    tr = jxx + jyy + 1e-10
    diff = jyy - jxx
    off = -2.0 * jxy
    del jxx, jyy, jxy
    aniso = np.hypot(diff, off)
    c2 = (diff / (aniso + 1e-10)).astype(np.float32)
    s2 = (off / (aniso + 1e-10)).astype(np.float32)
    coh = (aniso / tr).astype(np.float32)
    amp = np.sqrt(tr).astype(np.float32)
    med = float(np.median(amp[fp])) + 1e-6 if fp.any() else 1.0
    wt = (coh * np.tanh(amp / (1.5 * med))).astype(np.float32)
    return c2, s2, wt


def _sample_hw_offset(
    plane: np.ndarray, ny: np.ndarray, nx: np.ndarray, offset_px: float
) -> np.ndarray:
    h, w = plane.shape
    yy, xx = np.indices((h, w), dtype=np.float32)
    coords = np.array([yy + offset_px * ny, xx + offset_px * nx], dtype=np.float32)
    del yy, xx
    return ndi.map_coordinates(plane, coords, order=1, mode="nearest").astype(np.float32)


def build_rlms_static_features(
    features_tif: Path,
    ext_dir: Path,
    footprint: np.ndarray,
    out_memmap_path: Path,
) -> np.ndarray:
    """Build all 33 static float16 planes onto disk memmap (<700 MB peak RSS)."""
    fp = np.asarray(footprint, dtype=bool)
    verify_external_rasters(ext_dir)
    _, nearest_idx = ndi.distance_transform_edt(~fp, return_indices=True)

    out_memmap_path.parent.mkdir(parents=True, exist_ok=True)
    mm = open_memmap(
        out_memmap_path,
        mode="w+",
        dtype=np.float16,
        shape=(len(ALL_STATIC_NAMES), fp.shape[0], fp.shape[1]),
    )

    def load_native(name: str) -> np.ndarray:
        raw = read_band(features_tif, name)
        return _fill_outside(raw, fp, nearest_idx)

    def store(name: str, plane: np.ndarray, valid_mask: np.ndarray | None = None) -> None:
        idx = ALL_STATIC_NAMES.index(name)
        mm[idx] = _robust_std(plane, fp, valid_mask=valid_mask).astype(np.float16)

    def store_raw_f16(name: str, plane: np.ndarray) -> None:
        idx = ALL_STATIC_NAMES.index(name)
        clean = np.where(fp, plane, 0.0).astype(np.float16)
        mm[idx] = clean

    # 1. Magnetic analytical tilt & hydrothermal magnetite-destruction trough (Bands 2, 3, 9)
    b3 = np.maximum(load_native("tmi_hg"), 0.0)
    b9 = load_native("tmi_vg")
    h20 = max(float(np.percentile(b3[fp], 20)), 1e-4)
    tilt = np.arctan2(b9, np.sqrt(b3 * b3 + h20 * h20)).astype(np.float32)
    del b3, b9
    store("tilt_miller", tilt)
    t_s = ndi.gaussian_filter(tilt, 1.5)
    tg = np.hypot(
        ndi.gaussian_filter(t_s, 1.0, order=(0, 1)),
        ndi.gaussian_filter(t_s, 1.0, order=(1, 0)),
    )
    store("verduzco_tilt_contact", tg * np.exp(-((t_s / 0.35) ** 2)))
    del t_s, tg

    c2_m, s2_m, w_m = _structure_nematic(tilt, fp, grad_sigma=1.5, tensor_sigma=3.5)
    del tilt

    rtp = load_native("rtp")
    rtp_loc = rtp - ndi.gaussian_filter(rtp, 14.0)
    hyy = ndi.gaussian_filter(rtp, 2.5, order=(2, 0))
    hxx = ndi.gaussian_filter(rtp, 2.5, order=(0, 2))
    hyx = ndi.gaussian_filter(rtp, 2.5, order=(1, 1))
    eig_pos = np.maximum(0.5 * (hxx + hyy) + np.hypot(0.5 * (hxx - hyy), hyx), 0.0)
    store("mag_trough_alter", eig_pos * (1.0 / (1.0 + np.exp(rtp_loc / (np.std(rtp_loc[fp]) + 1e-5)))))
    del rtp, rtp_loc, hyy, hxx, hyx, eig_pos
    gc.collect()

    # 2. Laplace vertical gravity curvature g_zz & Cordell compaction-stripped horst step (Bands 5, 11, 13, 15, 18)
    b18 = load_native("iso_grav_anom_hg")
    b11 = load_native("iso_grav_anom_vg")
    g_hgrad = np.hypot(b18, b11)
    store("grav_hgrad_s2", ndi.gaussian_filter(g_hgrad, 1.5))

    d_col_18 = ndi.gaussian_filter(b18, 1.5, order=(0, 1))
    d_row_11 = ndi.gaussian_filter(b11, 1.5, order=(1, 0))
    g_zz = -(d_col_18 + d_row_11)
    curl_def = np.abs(
        ndi.gaussian_filter(b18, 1.5, order=(1, 0))
        - ndi.gaussian_filter(b11, 1.5, order=(0, 1))
    )
    del b18, b11, d_col_18, d_row_11
    curl_med = max(float(np.median(curl_def[fp])), 1e-6)
    seam_damp = 1.0 / (1.0 + (curl_def / (3.0 * curl_med)) ** 2)
    del curl_def
    gzz_s = ndi.gaussian_filter(g_zz, 1.5)
    gzz_grad = np.hypot(
        ndi.gaussian_filter(gzz_s, 1.0, order=(0, 1)),
        ndi.gaussian_filter(gzz_s, 1.0, order=(1, 0)),
    )
    gzz_std = max(float(np.percentile(np.abs(gzz_s[fp]), 75)), 1e-6)
    gzz_zero = gzz_grad * np.exp(-((gzz_s / (0.45 * gzz_std)) ** 2)) * seam_damp
    store("gzz_laplace_zero", gzz_zero)
    c2_g, s2_g, w_g = _structure_nematic(g_zz, fp, grad_sigma=1.5, tensor_sigma=3.5)
    del g_zz, gzz_s, gzz_grad, seam_damp
    gc.collect()

    zb = np.maximum(load_native("depth_to_base_surf"), 0.0)
    cba = load_native("iso_grav_anom")
    store("base_hinge_curv", _hessian_ridge_abs(zb, sigma=4.0))

    # Cordell exponential basin-compaction curve fit on footprint: cba ~ a0 + a1*(1 - exp(-zb/z0))
    z0 = 1200.0 if float(np.percentile(zb[fp], 90)) > 100.0 else max(float(np.median(zb[fp])), 1.0)
    basis = 1.0 - np.exp(-zb / z0)
    b_fp = basis[fp].astype(np.float64)
    c_fp = cba[fp].astype(np.float64)
    b_mean, c_mean = float(b_fp.mean()), float(c_fp.mean())
    slope_c = float(np.dot(b_fp - b_mean, c_fp - c_mean) / (np.dot(b_fp - b_mean, b_fp - b_mean) + 1e-9))
    cba_comp_res = cba - (c_mean + slope_c * (basis - b_mean)).astype(np.float32)
    del basis, b_fp, c_fp
    cordell_grad = np.hypot(
        ndi.gaussian_filter(cba_comp_res, 2.0, order=(0, 1)),
        ndi.gaussian_filter(cba_comp_res, 2.0, order=(1, 0)),
    )
    store("cordell_horst_grad", cordell_grad)
    del cba_comp_res, cordell_grad

    # 3. Listric hanging-wall -> footwall up-dip projections along +n_HW
    basin_pot = _robust_std(ndi.gaussian_filter(zb, 8.0), fp) - _robust_std(
        ndi.gaussian_filter(cba, 8.0), fp
    )
    del cba
    hw_x = ndi.gaussian_filter(basin_pot, 2.0, order=(0, 1))
    hw_y = ndi.gaussian_filter(basin_pot, 2.0, order=(1, 0))
    hw_mag = np.hypot(hw_x, hw_y)
    nx_hw = (hw_x / (hw_mag + 1e-6)).astype(np.float32)
    ny_hw = (hw_y / (hw_mag + 1e-6)).astype(np.float32)
    margin_gate = np.tanh(hw_mag / (float(np.median(hw_mag[fp])) + 1e-5)).astype(np.float32)
    del basin_pot, hw_x, hw_y, hw_mag

    deep_grav_comp = _robust_std(g_hgrad, fp) + 0.7 * _robust_std(gzz_zero, fp)
    del g_hgrad, gzz_zero
    store("listric_updip_grav_l5", _sample_hw_offset(deep_grav_comp, ny_hw, nx_hw, 5.0) * margin_gate)
    store("listric_updip_grav_l11", _sample_hw_offset(deep_grav_comp, ny_hw, nx_hw, 11.0) * margin_gate)
    del deep_grav_comp

    cond = load_native("cond_surf")
    cond_s2 = ndi.gaussian_filter(cond, 2.0)
    store("cond_smectite_s2", cond_s2)
    store("listric_updip_cond_l8", _sample_hw_offset(cond_s2, ny_hw, nx_hw, 8.0) * margin_gate)
    del cond, cond_s2

    zb_hw = _sample_hw_offset(zb, ny_hw, nx_hw, 6.0)
    zb_fw = _sample_hw_offset(zb, ny_hw, nx_hw, -6.0)
    store("listric_throw_asymmetry", (zb_hw - zb_fw) * margin_gate)
    del zb_hw, zb_fw, nx_hw, ny_hw, margin_gate

    c2_b, s2_b, w_b = _structure_nematic(zb, fp, grad_sigma=2.5, tensor_sigma=5.0)
    del zb
    gc.collect()

    # 4. Spin-2 nematic multi-physics coherence & GeoDAWN E-W flight-line veto
    gm_dot = c2_g * c2_m + s2_g * s2_m
    store("nematic_grav_mag_coh", w_g * w_m * gm_dot)
    # E-W flight line corresponds to psi ~ 0 => c2_m = cos(2*0) ~ +1 without gravity corroboration
    store("ew_flightline_veto", w_m * np.maximum(c2_m, 0.0) * (1.0 - np.maximum(gm_dot, 0.0)))
    del gm_dot

    sub_cx = 0.45 * w_g * c2_g + 0.35 * w_m * c2_m + 0.20 * w_b * c2_b
    sub_sy = 0.45 * w_g * s2_g + 0.35 * w_m * s2_m + 0.20 * w_b * s2_b
    del c2_g, s2_g, w_g, c2_m, s2_m, w_m, c2_b, s2_b, w_b
    sub_cx = ndi.gaussian_filter(sub_cx, 2.0)
    sub_sy = ndi.gaussian_filter(sub_sy, 2.0)
    sub_norm = np.hypot(sub_cx, sub_sy) + 1e-6
    sub_med = float(np.median(sub_norm[fp])) + 1e-6
    sub_w = np.tanh(sub_norm / (1.5 * sub_med)).astype(np.float32)
    sub_c2 = ((sub_cx / sub_norm) * sub_w).astype(np.float32)
    sub_s2 = ((sub_sy / sub_norm) * sub_w).astype(np.float32)
    del sub_cx, sub_sy, sub_norm, sub_w
    store_raw_f16("nematic_sub_c2", sub_c2)
    store_raw_f16("nematic_sub_s2", sub_s2)
    gc.collect()

    # 5. Remanent RTP-TMI contrast, Radiometric TC, Geodetic Eigenvalues, Seismicity & Native DEM
    rtp2 = load_native("rtp")
    tmi_raw = load_native("tmi")
    rem_diff = _robust_std(rtp2, fp) - _robust_std(tmi_raw, fp)
    rem_grad = np.hypot(
        ndi.gaussian_filter(rem_diff, 2.0, order=(0, 1)),
        ndi.gaussian_filter(rem_diff, 2.0, order=(1, 0)),
    )
    store("remanence_rtp_tmi_contrast", rem_grad)
    del rtp2, tmi_raw, rem_diff, rem_grad

    tc = load_native("tc")
    tc_gm = np.hypot(
        ndi.gaussian_filter(tc, 2.0, order=(0, 1)),
        ndi.gaussian_filter(tc, 2.0, order=(1, 0)),
    )
    del tc
    tc_med = max(float(np.median(tc_gm[fp])), 1e-6)
    store("tc_decouple_quiet", 1.0 / (1.0 + tc_gm / tc_med))
    del tc_gm

    dilat = load_native("geod_dilaterate")
    shear = load_native("geod_shearrate")
    inv2 = load_native("geod_2ndinv")
    eig1 = 0.5 * dilat + np.maximum(shear, 0.0)
    store("strain_eig_ext1", eig1)
    eig1_pos = np.maximum(eig1 - float(np.median(eig1[fp])), 0.0)
    store("strain_transtens_regime", np.sqrt(np.maximum(shear, 0.0) * eig1_pos + 1e-12) + 0.25 * inv2)
    del dilat, shear, inv2, eig1, eig1_pos

    eq_d = np.maximum(load_native("deq_n100a15"), 0.0)
    ieq = load_native("ieq_n100a15")
    eq_scale = max(float(np.median(eq_d[fp])), 1.0)
    store("eq_prox_exp", 0.5 * np.exp(-eq_d / (0.5 * eq_scale)) + 0.5 * np.tanh(np.maximum(ieq, 0.0)))
    del eq_d, ieq

    elev = load_native("det_elev")
    store("dem_hess_scarp_s2", _hessian_ridge_abs(elev, sigma=2.0))
    store("dem_hess_scarp_s5", _hessian_ridge_abs(elev, sigma=5.0))
    rel_short = ndi.maximum_filter(elev, size=5) - ndi.minimum_filter(elev, size=5)
    rel_long = ndi.maximum_filter(elev, size=25) - ndi.minimum_filter(elev, size=25)
    store("piedmont_relief_ratio", rel_short / (rel_long + 5.0))
    c2_dem_reg, s2_dem_reg, _ = _structure_nematic(elev, fp, grad_sigma=6.0, tensor_sigma=8.0)
    del elev, rel_short, rel_long

    slope_nat = read_band(features_tif, "det_elev_slope")
    slope_clean = np.where(fp & np.isfinite(slope_nat) & (np.abs(slope_nat) < 1e20), slope_nat, 0.0).astype(
        np.float32
    )
    del slope_nat
    store("slope_local", slope_clean)
    gc.collect()

    # 6. Official SHA-pinned USGS 3DEP 10m DEM & fluvial chi planes (100% footprint coverage)
    with rasterio.open(ext_dir / "dem10_chi_100m_i16.tif") as ds_chi:
        chi_step = ds_chi.read(1).astype(np.float32)
        ksn_raw = ds_chi.read(3).astype(np.float32)
        zmean_m = ds_chi.read(5).astype(np.float32)

    chan_step_ok = fp & (chi_step > -32000.0)
    w_step = ndi.gaussian_filter(chan_step_ok.astype(np.float32), 4.0)
    num_step = ndi.gaussian_filter(np.where(chan_step_ok, np.maximum(chi_step, 0.0), 0.0), 4.0)
    store("chi10_knickpoint_halo", num_step / (w_step + 0.02))
    del chi_step, chan_step_ok, w_step, num_step

    chan_ksn_ok = fp & (ksn_raw > -32000.0)
    w_ksn = ndi.gaussian_filter(chan_ksn_ok.astype(np.float32), 5.0)
    num_ksn = ndi.gaussian_filter(np.where(chan_ksn_ok, np.maximum(ksn_raw, 0.0), 0.0), 5.0)
    store("chi10_ksn_diseq", num_ksn / (w_ksn + 0.02))
    del ksn_raw, chan_ksn_ok, w_ksn, num_ksn

    with rasterio.open(ext_dir / "topo_10m_derived_100m_u8.tif") as ds_t10:
        s10_p90 = ds_t10.read(1).astype(np.float32)
        curv10 = ds_t10.read(6).astype(np.float32)
        asp_coh = ds_t10.read(7).astype(np.float32)
        hs_lin = ds_t10.read(8).astype(np.float32)

    micro_excess = _robust_std(curv10, fp) + 0.6 * np.maximum(
        _robust_std(s10_p90, fp) - _robust_std(slope_clean, fp), 0.0
    )
    store("topo10_microscarp_excess", micro_excess)
    store("topo10_lineament_coh", hs_lin * (asp_coh / 255.0))
    del s10_p90, curv10, asp_coh, hs_lin, micro_excess, slope_clean
    gc.collect()

    # 7. Official SHA-pinned USGS 3DEP 1m LiDAR scarp planes (NaN-routed on uncovered tiles)
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_ex = ds_lid.read(1).astype(np.float32)
        lid_step = ds_lid.read(3).astype(np.float32)
        lid_down = ds_lid.read(6).astype(np.float32)
        lid_up = ds_lid.read(7).astype(np.float32)
        lid_cross = ds_lid.read(8).astype(np.float32)
        lid_coh = ds_lid.read(10).astype(np.float32)
        lid_strike = ds_lid.read(11).astype(np.float32)
        lid_valid = ds_lid.read(12) > 0

    psi_lid = (lid_strike / 256.0) * np.pi
    c2_lid = np.cos(2.0 * psi_lid).astype(np.float32)
    s2_lid = np.sin(2.0 * psi_lid).astype(np.float32)
    del lid_strike, psi_lid

    # Pluvial Lake Lahontan (~1,285-1,355 m) & Bonneville (~1,445-1,560 m) iso-contour shoreline veto
    lahontan_band = np.exp(-(((zmean_m - 1332.0) / 32.0) ** 2)) + 0.6 * np.exp(
        -(((zmean_m - 1500.0) / 45.0) ** 2)
    )
    iso_contour_align = np.maximum(c2_lid * c2_dem_reg + s2_lid * s2_dem_reg, 0.0)
    sub_quiet = 1.0 - np.clip(np.hypot(sub_c2, sub_s2), 0.0, 1.0)
    shoreline_damp = 1.0 - 0.55 * np.clip(lahontan_band * iso_contour_align * sub_quiet, 0.0, 1.0)
    del zmean_m, c2_dem_reg, s2_dem_reg, lahontan_band, iso_contour_align, sub_quiet

    step_prom = (0.65 * lid_step + 0.35 * lid_ex) * (0.4 + 0.6 * (lid_coh / 255.0)) * shoreline_damp
    store("lidar_scarp_step_clean", step_prom, valid_mask=lid_valid)
    face_asym = (np.abs(lid_down - lid_up) + 0.6 * lid_cross) * shoreline_damp
    store("lidar_scarp_relief_asym", face_asym, valid_mask=lid_valid)
    lid_sub_align = (c2_lid * sub_c2 + s2_lid * sub_s2) * (lid_coh / 255.0)
    store("lidar_nematic_sub_align", lid_sub_align, valid_mask=lid_valid)
    del (
        lid_ex,
        lid_step,
        lid_down,
        lid_up,
        lid_cross,
        lid_coh,
        c2_lid,
        s2_lid,
        shoreline_damp,
        step_prom,
        face_asym,
        lid_sub_align,
        lid_valid,
        sub_c2,
        sub_s2,
    )
    gc.collect()

    # 8. Official SHA-pinned USGS GeoDAWN ternary radiometrics (K/eTh hydrothermal metasomatism)
    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as ds_rad:
        rad_k = ds_rad.read(1).astype(np.float32)
        rad_th = ds_rad.read(2).astype(np.float32)
    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as ds_ext:
        ext_thk = ds_ext.read(1).astype(np.float32)
        ext_uth = ds_ext.read(3).astype(np.float32)

    k_th_enrich = ndi.gaussian_filter(rad_k - rad_th, 2.0) - 0.5 * ndi.gaussian_filter(ext_thk, 2.0)
    uth_anom = np.abs(ext_uth - ndi.gaussian_filter(ext_uth, 12.0))
    store("geodawn_k_th_metasom", _robust_std(k_th_enrich, fp) + 0.35 * _robust_std(uth_anom, fp))
    del rad_k, rad_th, ext_thk, ext_uth, k_th_enrich, uth_anom
    gc.collect()

    mm.flush()
    del mm
    return np.load(out_memmap_path, mmap_mode="r")


def compute_continuation_fields(
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    sub_c2: np.ndarray,
    sub_s2: np.ndarray,
    *,
    include_iso_control: bool = False,
) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible Pollard-Segall & Riedel spin-2 continuation planes."""
    fp = np.asarray(footprint, dtype=bool)
    v = (np.asarray(vis_cat, dtype=bool) & fp).astype(np.float32)
    h, w = fp.shape
    if v.sum() == 0:
        zeros = np.zeros((h, w), dtype=np.float16)
        res = {k: zeros.copy() for k in CONTINUATION_NAMES}
        if include_iso_control:
            res["iso_tip_halo"] = zeros.copy()
        return res

    yy, xx = np.indices((h, w), dtype=np.float32)
    sigma_tip = 6.0
    mass = ndi.gaussian_filter(v, sigma_tip) + 1e-8
    mx = ndi.gaussian_filter(v * xx, sigma_tip) / mass - xx
    my = ndi.gaussian_filter(v * yy, sigma_tip) / mass - yy
    asym = np.hypot(mx, my)

    ux_prop = np.where(asym > 1e-4, -mx / (asym + 1e-6), 0.0).astype(np.float32)
    uy_prop = np.where(asym > 1e-4, -my / (asym + 1e-6), 0.0).astype(np.float32)
    tip_ness = np.clip((asym - 1.6) / 2.6, 0.0, 1.0) * (v > 0.5)
    tip_mask = (v > 0.5) & (asym >= 2.2)
    if not tip_mask.any():
        tip_mask = v > 0.5

    # Local mapped fault tangent & spin-2 director (cos 2psi_vis, sin 2psi_vis)
    mass_s2 = ndi.gaussian_filter(v, 2.5)
    ny = ndi.gaussian_filter(mass_s2, 1.0, order=(1, 0))
    nx = ndi.gaussian_filter(mass_s2, 1.0, order=(0, 1))
    nnorm = np.hypot(nx, ny) + 1e-6
    tx_tan = (-ny / nnorm).astype(np.float32)
    ty_tan = (nx / nnorm).astype(np.float32)
    del mass_s2, nx, ny, nnorm

    vis_c2_on = (tx_tan * tx_tan - ty_tan * ty_tan) * v
    vis_s2_on = (2.0 * tx_tan * ty_tan) * v

    r_tip_f64, (ty_i, tx_i) = ndi.distance_transform_edt(~tip_mask, return_indices=True)
    r_tip = r_tip_f64.astype(np.float32)
    del r_tip_f64, tip_mask
    dx_t = xx - tx_i.astype(np.float32)
    dy_t = yy - ty_i.astype(np.float32)
    ux_near = ux_prop[ty_i, tx_i]
    uy_near = uy_prop[ty_i, tx_i]
    del ty_i, tx_i
    cos_a = np.clip((dx_t * ux_near + dy_t * uy_near) / (r_tip + 1e-5), -1.0, 1.0)
    del dx_t, dy_t, ux_near, uy_near
    forward = np.maximum(cos_a, 0.0)
    alpha_abs = np.arccos(np.clip(cos_a, -1.0, 1.0))
    del cos_a

    # 1. Pollard-Segall off-axis wing-crack lobes (~27 deg)
    wing_ang = (forward ** 1.2) * np.exp(-(((alpha_abs - 0.47) / 0.30) ** 2))
    del alpha_abs
    wing_crack_lobe = _robust_std(
        np.exp(-r_tip / 28.0) * wing_ang * (r_tip > 2.0), fp
    ).astype(np.float16)
    del wing_ang

    # 2. Dual-scale collinear valley continuation cone (short 3 km + cross-basin 6.5 km)
    col_cone = (
        0.70 * np.exp(-r_tip / 30.0) * (forward ** 3.0)
        + 0.30 * np.exp(-r_tip / 65.0) * (forward ** 4.0)
    ) * (r_tip > 2.0)
    collinear_tip_cone = _robust_std(col_cone, fp).astype(np.float16)
    del col_cone, forward

    iso_tip_halo = None
    if include_iso_control:
        iso_tip_halo = _robust_std(np.exp(-r_tip / 30.0) * (r_tip > 2.0), fp).astype(np.float16)
    del r_tip

    # 3. Dual-scale opposing-tip releasing-stepover bridge (sigma=16 px & 30 px)
    tip_wt = tip_ness.astype(np.float32)
    sc16 = ndi.gaussian_filter(tip_wt, 16.0)
    vx16 = ndi.gaussian_filter(tip_wt * ux_prop, 16.0)
    vy16 = ndi.gaussian_filter(tip_wt * uy_prop, 16.0)
    opp16 = np.sqrt(np.maximum(sc16 * sc16 - (vx16 * vx16 + vy16 * vy16), 0.0))
    del sc16, vx16, vy16

    sc30 = ndi.gaussian_filter(tip_wt, 30.0)
    vx30 = ndi.gaussian_filter(tip_wt * ux_prop, 30.0)
    vy30 = ndi.gaussian_filter(tip_wt * uy_prop, 30.0)
    opp30 = np.sqrt(np.maximum(sc30 * sc30 - (vx30 * vx30 + vy30 * vy30), 0.0))
    del sc30, vx30, vy30, tip_wt, ux_prop, uy_prop, mx, my, asym
    stepover_bridge = _robust_std(0.65 * opp16 + 0.35 * opp30, fp).astype(np.float16)
    del opp16, opp30

    # 4. Broadside stress-release shadow & nearest-fault spin-2 kinematic strike alignment
    d_vis_f64, (vy_i, vx_i) = ndi.distance_transform_edt(~(v > 0.5), return_indices=True)
    d_vis = d_vis_f64.astype(np.float32)
    del d_vis_f64
    dx_v = xx - vx_i.astype(np.float32)
    dy_v = yy - vy_i.astype(np.float32)
    del xx, yy
    interior_wt = 1.0 - tip_ness[vy_i, vx_i]
    del tip_ness
    along_tan = np.abs(dx_v * tx_tan[vy_i, vx_i] + dy_v * ty_tan[vy_i, vx_i]) / (d_vis + 1e-5)
    del dx_v, dy_v, tx_tan, ty_tan
    broadside_orient = np.clip(1.0 - (along_tan / 0.40) ** 2, 0.0, 1.0)
    del along_tan
    radial_band = np.exp(-(((d_vis - 9.0) / 7.5) ** 2)) * (d_vis > 3.0)
    broadside_stress_shadow = _robust_std(
        interior_wt * broadside_orient * radial_band, fp
    ).astype(np.float16)
    del interior_wt, broadside_orient, radial_band

    # Outward-diffused fold-visible spin-2 fault strike field vs subsurface director
    w_vis_diff = ndi.gaussian_filter(v, 22.0) + 1e-6
    c2_vis_diff = ndi.gaussian_filter(vis_c2_on, 22.0) / w_vis_diff
    s2_vis_diff = ndi.gaussian_filter(vis_s2_on, 22.0) / w_vis_diff
    del v, vis_c2_on, vis_s2_on, w_vis_diff, vy_i, vx_i
    vn = np.hypot(c2_vis_diff, s2_vis_diff) + 1e-6
    c2_vis_u = c2_vis_diff / vn
    s2_vis_u = s2_vis_diff / vn
    del c2_vis_diff, s2_vis_diff, vn

    sc2 = np.asarray(sub_c2, dtype=np.float32)
    ss2 = np.asarray(sub_s2, dtype=np.float32)
    decay = np.exp(-d_vis / 55.0) * (d_vis > 2.0)
    del d_vis

    # 5. Parallel kinematic strike alignment cos(2*(psi_sub - psi_vis)) * |sub|
    cos_2dpsi = (sc2 * c2_vis_u + ss2 * s2_vis_u) * decay
    riedel_nematic_align = _robust_std(cos_2dpsi, fp).astype(np.float16)
    del cos_2dpsi

    # 6. Riedel / relay-breach conjugate obliquity |sin(2*(psi_sub - psi_vis))| * |sub|
    sin_2dpsi = np.abs(ss2 * c2_vis_u - sc2 * s2_vis_u) * decay
    conjugate_relay_obliquity = _robust_std(sin_2dpsi, fp).astype(np.float16)
    del sin_2dpsi, sc2, ss2, c2_vis_u, s2_vis_u, decay

    out = {
        "wing_crack_lobe": wing_crack_lobe,
        "collinear_tip_cone": collinear_tip_cone,
        "stepover_bridge": stepover_bridge,
        "broadside_stress_shadow": broadside_stress_shadow,
        "riedel_nematic_align": riedel_nematic_align,
        "conjugate_relay_obliquity": conjugate_relay_obliquity,
    }
    if include_iso_control and iso_tip_halo is not None:
        out["iso_tip_halo"] = iso_tip_halo
    return out
