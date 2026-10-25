"""Memory-bounded (< 900 MiB peak RSS) translation-invariant monogenic cross-spectral
phase congruency, upward-continuation attenuation, geothermal structural-intersection
permeability, and 3DEP scarp planes for lane H86J-MCSP.

Streams one band at a time into float16 disk-backed memmaps so peak memory stays
well within 3.8 GiB containers while exposing zero raw regional background levels.
"""

from __future__ import annotations

import gc
import hashlib
from pathlib import Path
import sys

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy.fft import fftfreq, irfft2, rfft2, rfftfreq
from scipy.ndimage import gaussian_filter

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
for _p in (ROOT_DIR, SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems86.io import BANDS, BAND_PHYSICS_VERIFIED, NODATA
from scripts.restore_data import EXTERNAL_PINS

EXPECTED_BANDS: dict[int, str] = {
    2: "rtp",
    3: "tmi_hg",
    4: "geod_2ndinv",
    5: "iso_grav_anom_slope",
    6: "tc",
    7: "geod_shearrate",
    8: "geod_dilaterate",
    9: "tmi_vg",
    10: "deq_n100a15",
    11: "iso_grav_anom_vg",
    12: "det_elev",
    13: "iso_grav_anom",
    15: "depth_to_base_surf",
    16: "ieq_n100a15",
    17: "cond_surf",
    18: "iso_grav_anom_hg",
    19: "det_elev_slope",
}

MCSP_STATIC_NAMES: tuple[str, ...] = (
    "mpc_rtp_step",
    "mpc_grav_step",
    "mpc_depth_step",
    "tmi_up150_attenuation",
    "verduzco_tilt_contact_s2",
    "laplace_gzz_dipole_s3",
    "cross_phase_coherence",
    "cross_admittance_break",
    "hydro_demag_trough",
    "cond_eccentric_neck",
    "rad_kth_metasom_step",
    "rad_uth_redox_step",
    "tc_alluvial_quietness",
    "transtens_strain_anom",
    "seismic_conduit_anom",
    "geotherm_intersection_det",
    "lidar_scarp_step_deconf",
    "lidar_face_curv_dipole",
    "topo10_curv_lineament",
    "piedmont_slope_break",
    "chi_knickzone_step",
    "lahontan_mimic_veto",
)

ABLATION_AMP_NAMES: tuple[str, ...] = (
    "amp_rtp_gradmag_s2",
    "amp_grav_slope_b5",
    "amp_depth_gradmag_s3",
    "amp_elev_slope_b19",
    "amp_lidar_step_raw",
    "amp_topo10_slope_p90",
    "amp_strain_2ndinv_anom",
    "amp_tc_gradmag_s2",
)

FOLD_ELASTIC_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
)


def verify_band_physics_contract(ext_dir: Path | None = None) -> dict:
    """Fail-closed check against src/gems86/io.py and SHA-256 external pins."""
    for idx, expected in EXPECTED_BANDS.items():
        actual = BANDS.get(idx)
        if actual != expected:
            raise RuntimeError(
                f"Band contract mismatch at Band {idx}: expected {expected!r}, got {actual!r}"
            )
    for req_override in (5, 6, 11, 18):
        if req_override not in BAND_PHYSICS_VERIFIED:
            raise RuntimeError(f"Missing verified physics override for Band {req_override}")

    ext_verified: dict[str, str] = {}
    if ext_dir is not None:
        ext_root = Path(ext_dir)
        for name, expected_sha in EXTERNAL_PINS.items():
            p = ext_root / name
            if not p.is_file():
                raise FileNotFoundError(f"Missing pinned external raster: {p}")
            h = hashlib.sha256()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            got = h.hexdigest()
            if got != expected_sha:
                raise RuntimeError(
                    f"SHA-256 mismatch on {p.name}: expected {expected_sha}, got {got}"
                )
            ext_verified[name] = got
    return {
        "verified_native_bands": {str(k): v for k, v in EXPECTED_BANDS.items()},
        "verified_overrides": {
            str(k): BAND_PHYSICS_VERIFIED[k] for k in (5, 6, 11, 18)
        },
        "verified_external_sha256": ext_verified,
    }


def _masked_gaussian(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    w = valid.astype(np.float32)
    x = np.where(valid, np.asarray(arr, dtype=np.float32), np.float32(0.0))
    if sigma <= 0.0:
        return x
    num = gaussian_filter(x * w, sigma=float(sigma), mode="nearest")
    den = np.maximum(gaussian_filter(w, sigma=float(sigma), mode="nearest"), 1e-6)
    return (num / den).astype(np.float32)


def _masked_gradients(
    arr: np.ndarray, valid: np.ndarray, sigma: float = 1.5
) -> tuple[np.ndarray, np.ndarray]:
    """Return (df/dx_east, df/drow_south) inside valid with smooth rim extension."""
    sm = _masked_gaussian(arr, valid, sigma) if sigma > 0.0 else np.where(valid, arr, 0.0)
    fill = _masked_gaussian(sm, valid, max(4.0, sigma * 2.0))
    u = np.where(valid, sm, fill).astype(np.float32)
    del sm, fill
    drow, dx = np.gradient(u)
    del u
    z = np.float32(0.0)
    return (
        np.where(valid, dx, z).astype(np.float32),
        np.where(valid, drow, z).astype(np.float32),
    )


def _hessian_ridge_and_eccentricity(
    arr: np.ndarray, valid: np.ndarray, sigma: float
) -> tuple[np.ndarray, np.ndarray]:
    gx, gy = _masked_gradients(arr, valid, sigma=sigma)
    hxx, hxy = _masked_gradients(gx, valid, sigma=max(1.0, 0.5 * sigma))
    del gx
    hyx, hyy = _masked_gradients(gy, valid, sigma=max(1.0, 0.5 * sigma))
    del gy
    hxy_s = 0.5 * (hxy + hyx)
    del hxy, hyx
    tr = hxx + hyy
    rad = np.sqrt(np.maximum(0.25 * (hxx - hyy) ** 2 + hxy_s * hxy_s, 0.0))
    del hxx, hyy, hxy_s
    lam1 = 0.5 * tr - rad
    lam2 = 0.5 * tr + rad
    del tr, rad
    a1 = np.abs(lam1)
    a2 = np.abs(lam2)
    hi = np.maximum(a1, a2)
    lo = np.minimum(a1, a2)
    ecc = (hi - lo) / (hi + lo + 1e-6)
    ridge = np.maximum(-lam1, 0.0)
    z = np.float32(0.0)
    return (
        np.where(valid, ridge, z).astype(np.float32),
        np.where(valid, ecc, z).astype(np.float32),
    )


def _rank01(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    m = np.asarray(valid, dtype=bool)
    vals = np.asarray(arr, dtype=np.float32)[m]
    if vals.size <= 1:
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[m] = ranks
    return out


def _robust_pos_z(arr: np.ndarray, valid: np.ndarray, clip: float = 8.0) -> np.ndarray:
    vals = np.asarray(arr, dtype=np.float32)[valid]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75) - np.percentile(vals, 25))
    scale = max(iqr / 1.349, float(np.std(vals)), 1e-6)
    z = np.clip((arr.astype(np.float32) - med) / scale, -clip, clip)
    return np.where(valid, z, np.float32(0.0)).astype(np.float32)


def riesz_monogenic_phase_congruency(
    arr: np.ndarray,
    valid: np.ndarray,
    *,
    scales: tuple[float, ...] = (1.5, 3.0, 6.0),
    bandwidth_ratio: float = 2.0,
    even_penalty: float = 0.65,
    noise_k: float = 1.75,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """2-D Riesz-transform monogenic step-edge phase congruency (Felsberg & Sommer 2001)."""
    H, W = arr.shape
    base = _masked_gaussian(arr, valid, 0.8)
    rim1 = _masked_gaussian(base, valid, 8.0)
    u = np.where(valid, base, rim1)
    del rim1
    rim2 = gaussian_filter(u, sigma=14.0, mode="nearest")
    u = np.where(valid, base, rim2).astype(np.float32)
    del base, rim2

    ky = fftfreq(H).astype(np.float32)[:, None]
    kx = rfftfreq(W).astype(np.float32)[None, :]
    knorm = np.sqrt(kx * kx + ky * ky).astype(np.float32)
    inv_k = np.where(knorm > 0.0, 1.0 / np.maximum(knorm, 1e-12), 0.0).astype(np.float32)
    rx_mult = (-1j * kx * inv_k).astype(np.complex64)
    ry_mult = (-1j * ky * inv_k).astype(np.complex64)
    del kx, ky, knorm, inv_k

    sum_qx = np.zeros((H, W), dtype=np.float32)
    sum_qy = np.zeros((H, W), dtype=np.float32)
    sum_abs_e = np.zeros((H, W), dtype=np.float32)
    sum_amp = np.zeros((H, W), dtype=np.float32)
    noise_floor = 0.0

    for idx, sig in enumerate(scales):
        g_lo = gaussian_filter(u, sigma=float(sig), mode="nearest")
        g_hi = gaussian_filter(u, sigma=float(sig * bandwidth_ratio), mode="nearest")
        even_m = (g_lo - g_hi).astype(np.float32)
        del g_lo, g_hi
        F_e = rfft2(even_m)
        qx_m = irfft2(F_e * rx_mult, s=(H, W)).astype(np.float32)
        qy_m = irfft2(F_e * ry_mult, s=(H, W)).astype(np.float32)
        del F_e
        odd_m = np.hypot(qx_m, qy_m)
        amp_m = np.sqrt(even_m * even_m + odd_m * odd_m + 1e-12, dtype=np.float32)

        if idx == 0:
            med0 = float(np.median(amp_m[valid])) if np.any(valid) else 0.0
            tau0 = med0 / max(float(np.sqrt(np.log(4.0))), 1e-6)
            noise_floor = float(noise_k * tau0 * (1.0 - 0.5 ** len(scales)) / 0.5)

        sum_qx += qx_m
        sum_qy += qy_m
        sum_abs_e += np.abs(even_m)
        sum_amp += amp_m
        del even_m, qx_m, qy_m, odd_m, amp_m

    del u, rx_mult, ry_mult
    odd_vec = np.hypot(sum_qx, sum_qy)
    eps0 = float(np.percentile(sum_amp[valid], 5) * 0.05 + 1e-6) if np.any(valid) else 1e-6
    pc = np.clip(
        (odd_vec - float(even_penalty) * sum_abs_e - noise_floor) / (sum_amp + eps0),
        0.0,
        1.0,
    ).astype(np.float32)
    vec_norm = np.maximum(odd_vec, 1e-6)
    ux = np.where(valid, sum_qx / vec_norm, np.float32(0.0)).astype(np.float32)
    uy = np.where(valid, sum_qy / vec_norm, np.float32(0.0)).astype(np.float32)
    pc = np.where(valid, pc, np.float32(0.0)).astype(np.float32)
    return pc, ux, uy


def _structure_tensor_intersection(
    ridge: np.ndarray, valid: np.ndarray, sigma_grad: float = 1.2, sigma_int: float = 4.0
) -> np.ndarray:
    gx, gy = _masked_gradients(ridge, valid, sigma=sigma_grad)
    jxx = _masked_gaussian(gx * gx, valid, sigma_int)
    jxy = _masked_gaussian(gx * gy, valid, sigma_int)
    jyy = _masked_gaussian(gy * gy, valid, sigma_int)
    del gx, gy
    det_j = np.maximum(jxx * jyy - jxy * jxy, 0.0)
    tr_j = jxx + jyy
    del jxx, jxy, jyy
    eps = float(np.percentile(tr_j[valid], 50) * 0.1 + 1e-8) if np.any(valid) else 1e-8
    inter = det_j / (tr_j + eps)
    return np.where(valid, inter, np.float32(0.0)).astype(np.float32)


def _read_one_native(ds: rasterio.DatasetReader, idx: int, valid: np.ndarray) -> np.ndarray:
    arr = ds.read(idx).astype(np.float32)
    arr[~valid | ~np.isfinite(arr) | (np.abs(arr) >= 1e30)] = 0.0
    return arr


def _read_one_ext(ext_dir: Path, fname: str, band_idx: int, valid: np.ndarray) -> np.ndarray:
    with rasterio.open(ext_dir / fname) as ds:
        arr = ds.read(band_idx).astype(np.float32)
    arr[~valid | ~np.isfinite(arr)] = 0.0
    return arr


def build_mcsp_static_stack(
    features_tif: Path,
    ext_dir: Path,
    *,
    out_mcsp_path: Path | None = None,
    out_amp_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Stream-compute MCSP (22, H, W) and AMP (8, H, W) into float16 memmaps (< 850 MiB RSS)."""
    qc = verify_band_physics_contract(ext_dir)
    with rasterio.open(features_tif) as ds:
        b1 = ds.read(1)
        valid = np.isfinite(b1) & (b1 > NODATA * 0.5) & (np.abs(b1) < 1e30)
        del b1
        if footprint is not None:
            valid = valid & np.asarray(footprint, dtype=bool)
        H, W = valid.shape

        if out_mcsp_path is not None:
            out_mcsp_path.parent.mkdir(parents=True, exist_ok=True)
            X_mcsp = open_memmap(
                out_mcsp_path, mode="w+", dtype=np.float16, shape=(len(MCSP_STATIC_NAMES), H, W)
            )
        else:
            X_mcsp = np.empty((len(MCSP_STATIC_NAMES), H, W), dtype=np.float16)

        if out_amp_path is not None:
            out_amp_path.parent.mkdir(parents=True, exist_ok=True)
            X_amp = open_memmap(
                out_amp_path, mode="w+", dtype=np.float16, shape=(len(ABLATION_AMP_NAMES), H, W)
            )
        else:
            X_amp = np.empty((len(ABLATION_AMP_NAMES), H, W), dtype=np.float16)

        def _put_mcsp(name: str, arr: np.ndarray, raw_unit: bool = False) -> None:
            i = MCSP_STATIC_NAMES.index(name)
            clean = np.where(valid & np.isfinite(arr), arr, np.float32(0.0)).astype(np.float32)
            vals = clean if raw_unit else _robust_pos_z(clean, valid)
            X_mcsp[i] = np.clip(vals, -32.0, 32.0).astype(np.float16)

        def _put_amp(name: str, arr: np.ndarray) -> None:
            i = ABLATION_AMP_NAMES.index(name)
            clean = np.where(valid & np.isfinite(arr), arr, np.float32(0.0)).astype(np.float32)
            X_amp[i] = np.clip(_robust_pos_z(clean, valid), -32.0, 32.0).astype(np.float16)

        fam_pot = np.zeros((H, W), dtype=np.float32)
        fam_geo = np.zeros((H, W), dtype=np.float32)
        fam_scarp = np.zeros((H, W), dtype=np.float32)
        fam_tect = np.zeros((H, W), dtype=np.float32)

        # 1. RTP & TMI_up150 & Gravity monogenic phase + cross-phase + hydro demag
        b2 = _read_one_native(ds, 2, valid)
        mpc_rtp, rtp_ux, rtp_uy = riesz_monogenic_phase_congruency(b2, valid, scales=(1.5, 3.0, 6.0))
        _put_mcsp("mpc_rtp_step", mpc_rtp, raw_unit=True)
        fam_pot += 0.22 * _rank01(mpc_rtp, valid)

        rtp_gx, rtp_gy = _masked_gradients(b2, valid, sigma=1.5)
        rtp_gmag = np.hypot(rtp_gx, rtp_gy)
        del rtp_gx, rtp_gy
        _put_amp("amp_rtp_gradmag_s2", rtp_gmag)

        tmi_up = _read_one_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid)
        up_gx, up_gy = _masked_gradients(tmi_up, valid, sigma=1.5)
        del tmi_up
        tmi_up150_atten = np.maximum(
            _rank01(rtp_gmag, valid) - 0.75 * _rank01(np.hypot(up_gx, up_gy), valid), 0.0
        ).astype(np.float32)
        del up_gx, up_gy, rtp_gmag
        _put_mcsp("tmi_up150_attenuation", tmi_up150_atten)
        fam_pot += 0.14 * _rank01(tmi_up150_atten, valid)
        del tmi_up150_atten

        demag_trough = np.maximum(_masked_gaussian(b2, valid, 6.0) - _masked_gaussian(b2, valid, 2.0), 0.0)
        del b2

        b13 = _read_one_native(ds, 13, valid)
        mpc_grav, grav_ux, grav_uy = riesz_monogenic_phase_congruency(b13, valid, scales=(1.5, 3.0, 6.0))
        del b13
        _put_mcsp("mpc_grav_step", mpc_grav, raw_unit=True)
        fam_pot += 0.24 * _rank01(mpc_grav, valid)

        cos_dpsi = np.abs(rtp_ux * grav_ux + rtp_uy * grav_uy)
        sin_dpsi = np.abs(rtp_ux * grav_uy - rtp_uy * grav_ux)
        del rtp_ux, rtp_uy, grav_ux, grav_uy
        joint_pc = np.sqrt(mpc_rtp * mpc_grav + 1e-12)
        _put_mcsp("cross_phase_coherence", (cos_dpsi**2) * joint_pc)
        _put_mcsp("cross_admittance_break", sin_dpsi * mpc_grav)
        del cos_dpsi, sin_dpsi, joint_pc

        hydro_demag = (_rank01(demag_trough, valid) * mpc_grav).astype(np.float32)
        del demag_trough
        _put_mcsp("hydro_demag_trough", hydro_demag)
        fam_geo += 0.24 * _rank01(hydro_demag, valid)
        del hydro_demag
        gc.collect()

        # 2. Depth to basement monogenic phase & gradient
        b15 = _read_one_native(ds, 15, valid)
        mpc_depth, _, _ = riesz_monogenic_phase_congruency(
            np.log1p(np.maximum(b15, 0.0)), valid, scales=(2.0, 4.0, 8.0)
        )
        _put_mcsp("mpc_depth_step", mpc_depth, raw_unit=True)
        fam_pot += 0.16 * _rank01(mpc_depth, valid)
        del mpc_depth
        d_gx, d_gy = _masked_gradients(b15, valid, sigma=3.0)
        del b15
        _put_amp("amp_depth_gradmag_s3", np.hypot(d_gx, d_gy))
        del d_gx, d_gy
        gc.collect()

        # 3. Verduzco tilt-depth contact (Bands 3, 9) & Laplace g_zz dipole (Bands 5, 11, 18)
        b3 = _read_one_native(ds, 3, valid)
        b9 = _read_one_native(ds, 9, valid)
        h_mag = np.maximum(_masked_gaussian(np.abs(b3), valid, 1.5), 0.0)
        v_mag = _masked_gaussian(b9, valid, 1.5)
        del b3, b9
        theta_mag = np.arctan2(v_mag, h_mag + float(np.percentile(h_mag[valid], 15) + 1e-6))
        del h_mag, v_mag
        tmx, tmy = _masked_gradients(theta_mag, valid, sigma=1.5)
        verduzco = (np.hypot(tmx, tmy) * np.exp(-((theta_mag / 0.35) ** 2))).astype(np.float32)
        del theta_mag, tmx, tmy
        _put_mcsp("verduzco_tilt_contact_s2", verduzco)
        fam_pot += 0.12 * _rank01(verduzco, valid)
        del verduzco

        _put_amp("amp_grav_slope_b5", _read_one_native(ds, 5, valid))
        b18 = _read_one_native(ds, 18, valid)
        b11 = _read_one_native(ds, 11, valid)
        gx_g = _masked_gaussian(b18, valid, 2.0)
        gy_g = _masked_gaussian(b11, valid, 2.0)
        del b18, b11
        dgx_dx, dgx_dy = _masked_gradients(gx_g, valid, sigma=1.5)
        dgy_dx, dgy_dy = _masked_gradients(gy_g, valid, sigma=1.5)
        g_zz = -(dgx_dx + dgy_dy)
        curl_g = np.abs(dgy_dx - dgx_dy)
        curl_veto = np.clip(1.0 - curl_g / (np.hypot(dgx_dx, dgy_dy) + curl_g + 1e-6), 0.0, 1.0)
        del dgx_dx, dgx_dy, dgy_dx, dgy_dy, curl_g
        h_grav = np.hypot(gx_g, gy_g)
        del gx_g, gy_g
        theta_g = np.arctan2(g_zz, h_grav + float(np.percentile(h_grav[valid], 15) + 1e-6))
        del g_zz, h_grav
        tgx, tgy = _masked_gradients(theta_g, valid, sigma=1.8)
        laplace_gzz = (np.hypot(tgx, tgy) * np.exp(-((theta_g / 0.35) ** 2)) * curl_veto).astype(np.float32)
        del theta_g, tgx, tgy, curl_veto
        _put_mcsp("laplace_gzz_dipole_s3", laplace_gzz)
        fam_pot += 0.12 * _rank01(laplace_gzz, valid)
        del laplace_gzz
        gc.collect()

        # 4. Conductivity eccentricity neck, TC quietness, Strain, Seismicity
        b19 = _read_one_native(ds, 19, valid)
        _put_amp("amp_elev_slope_b19", b19)
        b17 = _read_one_native(ds, 17, valid)
        cond_log = np.log1p(np.maximum(b17 - float(np.min(b17[valid])), 0.0))
        del b17
        cond_ridge, cond_ecc = _hessian_ridge_and_eccentricity(cond_log, valid, sigma=2.5)
        del cond_log
        cond_neck = (
            cond_ridge * (cond_ecc**2) * np.tanh(_rank01(b19, valid) * 1.5 + mpc_grav * 2.0)
        ).astype(np.float32)
        del cond_ridge, cond_ecc
        _put_mcsp("cond_eccentric_neck", cond_neck)
        fam_geo += 0.22 * _rank01(cond_neck, valid)
        del cond_neck

        b6 = _read_one_native(ds, 6, valid)
        _put_mcsp("tc_alluvial_quietness", _masked_gaussian(b6, valid, 12.0) - b6)
        tc_gx, tc_gy = _masked_gradients(b6, valid, sigma=2.0)
        del b6
        _put_amp("amp_tc_gradmag_s2", np.hypot(tc_gx, tc_gy))
        del tc_gx, tc_gy

        b4 = _read_one_native(ds, 4, valid)
        b7 = _read_one_native(ds, 7, valid)
        b8 = _read_one_native(ds, 8, valid)
        # Strict 1.0x mesoscale high-pass residual so regional Walker Lane vs NE background cancels
        inv_hp = b4 - _masked_gaussian(b4, valid, 24.0)
        _put_amp("amp_strain_2ndinv_anom", inv_hp)
        dil_hp = np.maximum(b8 - _masked_gaussian(b8, valid, 24.0), 0.0)
        shr_hp = np.maximum(b7 - _masked_gaussian(b7, valid, 24.0), 0.0)
        del b4, b7, b8
        transtens = (np.sqrt(shr_hp * dil_hp + 1e-12) + 0.35 * np.maximum(inv_hp, 0.0)).astype(
            np.float32
        )
        del inv_hp, dil_hp, shr_hp
        _put_mcsp("transtens_strain_anom", transtens)
        fam_tect += 0.40 * _rank01(transtens, valid)
        del transtens

        b10 = _read_one_native(ds, 10, valid)
        b16 = _read_one_native(ds, 16, valid)
        eq_prox = np.exp(-np.maximum(b10, 0.0) / float(np.median(b10[valid]) + 1e-6))
        eq_hp = eq_prox - _masked_gaussian(eq_prox, valid, 24.0)
        ieq_hp = b16 - _masked_gaussian(b16, valid, 24.0)
        del b10, b16, eq_prox
        _put_mcsp("seismic_conduit_anom", _rank01(eq_hp, valid) + 0.5 * _rank01(ieq_hp, valid))
        del eq_hp, ieq_hp

        b12 = _read_one_native(ds, 12, valid)
        slope_bg = _masked_gaussian(b19, valid, 12.0) + float(np.percentile(b19[valid], 25) + 1e-4)
        elev_ridge, _ = _hessian_ridge_and_eccentricity(b12, valid, sigma=2.0)
        del b12
        piedmont_break = (0.6 * (b19 / slope_bg) + 0.4 * _rank01(elev_ridge, valid)).astype(np.float32)
        del b19, slope_bg, elev_ridge
        _put_mcsp("piedmont_slope_break", piedmont_break)
        fam_scarp += 0.22 * _rank01(piedmont_break, valid)
        del piedmont_break
        gc.collect()

    # 5. External GeoDAWN K/Th/U, 3DEP LiDAR, 10 m DEM & Chi-knickzones
    z_m = _read_one_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)
    del z_m

    rad_K = _read_one_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid)
    rad_Th = _read_one_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid)
    ext_ThK = _read_one_ext(ext_dir, "geodawn_extensions_u8.tif", 1, valid)
    kth_ratio = (rad_K + 1.0) / (rad_Th + 8.0) - 0.35 * (ext_ThK / 255.0)
    del rad_K, ext_ThK
    kth_gx, kth_gy = _masked_gradients(kth_ratio, valid, sigma=1.8)
    del kth_ratio
    rad_kth_step = (np.hypot(kth_gx, kth_gy) * (1.0 - 0.5 * lahontan_band)).astype(np.float32)
    del kth_gx, kth_gy
    _put_mcsp("rad_kth_metasom_step", rad_kth_step)
    fam_geo += 0.20 * _rank01(rad_kth_step, valid)
    del rad_kth_step

    rad_U = _read_one_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid)
    ext_UTh = _read_one_ext(ext_dir, "geodawn_extensions_u8.tif", 3, valid)
    uth_field = 0.6 * (ext_UTh / 255.0) + 0.4 * ((rad_U + 1.0) / (rad_Th + 8.0))
    del rad_U, rad_Th, ext_UTh
    uth_gx, uth_gy = _masked_gradients(uth_field, valid, sigma=1.8)
    del uth_field
    _put_mcsp("rad_uth_redox_step", np.hypot(uth_gx, uth_gy))
    del uth_gx, uth_gy

    topo_asp = _read_one_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid)
    lahontan_mimic = np.where(
        valid,
        np.clip(
            lahontan_band * (topo_asp / 255.0) * (1.0 - np.clip(mpc_grav * 2.0, 0.0, 1.0)),
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)
    del lahontan_band
    _put_mcsp("lahontan_mimic_veto", lahontan_mimic, raw_unit=True)

    topo_curv = _read_one_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 6, valid)
    topo_hs = _read_one_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 8, valid)
    topo10_curv_lin = (
        (0.55 * (topo_hs / 255.0) + 0.45 * (topo_curv / 255.0))
        * (0.4 + 0.6 * (topo_asp / 255.0))
        * (1.0 - 0.55 * lahontan_mimic)
    ).astype(np.float32)
    del topo_curv, topo_hs, topo_asp
    _put_mcsp("topo10_curv_lineament", topo10_curv_lin)
    fam_scarp += 0.24 * _rank01(topo10_curv_lin, valid)

    # Note: 3DEP 1 m LiDAR covers 95.1% of SW but only 52.6% of NE, while mapped
    # catalogue density is 16.74 per-mille in SW vs 9.21 per-mille in NE (despite NE
    # having 22.49 per-mille off-catalogue SGMC faults). Both zero-fill and NaN-routing
    # let trees exploit the human LiDAR survey boundary as a proxy for mapping effort.
    # Quantile/z-score matching missing LiDAR pixels with 10 m USGS DEM scarp curvature
    # makes the scarp plane distribution invariant to 1 m swath availability.
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as _lds:
        li_has_swath = valid & (_lds.read(12) > 0)
    li_miss_swath = valid & ~li_has_swath

    def _put_lidar_debiased(
        target_mm: np.ndarray, idx: int, arr: np.ndarray, fallback_10m: np.ndarray
    ) -> np.ndarray:
        z_obs = _robust_pos_z(arr, li_has_swath)
        z_fb = _robust_pos_z(fallback_10m, li_miss_swath) if np.any(li_miss_swath) else np.zeros_like(z_obs)
        merged_z = np.zeros(valid.shape, dtype=np.float32)
        merged_z[li_has_swath] = z_obs[li_has_swath]
        merged_z[li_miss_swath] = z_fb[li_miss_swath]
        target_mm[idx] = np.clip(merged_z, -32.0, 32.0).astype(np.float16)

        r_obs = _rank01(arr, li_has_swath)
        r_fb = _rank01(fallback_10m, li_miss_swath) if np.any(li_miss_swath) else np.zeros_like(r_obs)
        merged_r = np.zeros(valid.shape, dtype=np.float32)
        merged_r[li_has_swath] = r_obs[li_has_swath]
        merged_r[li_miss_swath] = r_fb[li_miss_swath]
        return merged_r

    topo_slope_10m = _read_one_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_amp("amp_topo10_slope_p90", topo_slope_10m)

    li_step = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 3, valid)
    _put_lidar_debiased(
        X_amp, ABLATION_AMP_NAMES.index("amp_lidar_step_raw"), li_step / 255.0, topo_slope_10m
    )
    del topo_slope_10m
    li_cross = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 8, valid)
    li_coh = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 10, valid)
    lidar_scarp_deconf = (
        (li_step / 255.0)
        * (0.5 + 0.5 * (li_cross / 255.0))
        * (0.35 + 0.65 * (li_coh / 255.0))
        * (1.0 - 0.65 * lahontan_mimic)
    ).astype(np.float32)
    del li_step, li_cross
    lidar_scarp_rank = _put_lidar_debiased(
        X_mcsp,
        MCSP_STATIC_NAMES.index("lidar_scarp_step_deconf"),
        lidar_scarp_deconf,
        topo10_curv_lin,
    )
    fam_scarp += 0.34 * lidar_scarp_rank

    li_dn = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 6, valid)
    li_up = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 7, valid)
    li_ln = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 4, valid)
    li_lp = _read_one_ext(ext_dir, "lidar_scarp_features_u8.tif", 5, valid)
    lidar_dipole = (
        (np.maximum(li_dn, li_up) / 255.0)
        * np.sqrt((li_ln / 255.0) * (li_lp / 255.0) + 1e-6)
        * (0.4 + 0.6 * (li_coh / 255.0))
    ).astype(np.float32)
    del li_dn, li_up, li_ln, li_lp, li_coh
    lidar_dip_rank = _put_lidar_debiased(
        X_mcsp,
        MCSP_STATIC_NAMES.index("lidar_face_curv_dipole"),
        lidar_dipole,
        topo10_curv_lin,
    )
    fam_scarp += 0.20 * lidar_dip_rank
    del lidar_dipole, lidar_dip_rank, li_has_swath, li_miss_swath

    # Structure-tensor fault-intersection detector (Faulds & Hinz 2015)
    comp_ridge = (
        0.35 * mpc_grav
        + 0.25 * mpc_rtp
        + 0.25 * lidar_scarp_rank
        + 0.15 * _rank01(topo10_curv_lin, valid)
    )
    del mpc_grav, mpc_rtp, lidar_scarp_deconf, lidar_scarp_rank, topo10_curv_lin
    geotherm_inter = _structure_tensor_intersection(
        comp_ridge, valid, sigma_grad=1.2, sigma_int=4.0
    )
    del comp_ridge
    _put_mcsp("geotherm_intersection_det", geotherm_inter)
    fam_geo += 0.34 * _rank01(geotherm_inter, valid)
    del geotherm_inter

    chi_step = _read_one_ext(ext_dir, "dem10_chi_100m_i16.tif", 1, valid)
    chi_ksn = _read_one_ext(ext_dir, "dem10_chi_100m_i16.tif", 3, valid)
    chi_area = _read_one_ext(ext_dir, "dem10_chi_100m_i16.tif", 4, valid)
    area_norm = np.clip((chi_area / 1000.0 - 4.0) / 3.0, 0.2, 1.5)
    del chi_area
    chi_knick = (
        0.6 * _rank01(np.maximum(chi_step, 0.0) / area_norm, valid)
        + 0.4 * _rank01(np.maximum(chi_ksn, 0.0), valid)
    ).astype(np.float32)
    del chi_step, chi_ksn, area_norm
    _put_mcsp("chi_knickzone_step", chi_knick)
    fam_tect += 0.60 * _rank01(chi_knick, valid)
    del chi_knick

    L_raw = (
        0.38 * fam_pot
        + 0.20 * fam_geo
        + 0.28 * fam_scarp
        + 0.14 * fam_tect
        - 0.18 * lahontan_mimic
    )
    del fam_pot, fam_geo, fam_scarp, fam_tect, lahontan_mimic
    L_mcsp = _rank01(L_raw, valid)
    del L_raw
    gc.collect()

    if out_mcsp_path is not None:
        X_mcsp.flush()
        del X_mcsp
        X_mcsp = np.load(out_mcsp_path, mmap_mode="r")
    if out_amp_path is not None:
        X_amp.flush()
        del X_amp
        X_amp = np.load(out_amp_path, mmap_mode="r")

    return X_mcsp, L_mcsp, X_amp, valid, qc
