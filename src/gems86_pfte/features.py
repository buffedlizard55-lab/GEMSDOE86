"""First-principles geophysical & hydrogeological feature operators for Lane H86M-PFTE:
  1. 3-D Cordell-Parker spectral exponential-compaction basin gravity stripping
     (Cordell 1973; Parker 1973) honoring BAND_PHYSICS_VERIFIED (+B18 East, +B11 South).
  2. Symmetric 2x2 horizontal Marussi gravity curvature tensor eigensystem
     (Pedersen & Rasmussen 1990; Beiki 2010), hyperbolic fault-contact saddle
     sqrt(max(0, -lambda_1 * lambda_2)), spin-2 strike director (cos 2*theta, sin 2*theta),
     and conservative potential-field curl gridding-seam suppressor |d_r g_x - d_x g_r|.
  3. Baranov (1957) 2-D FFT pseudogravity vector non-collinearity & hydrothermal
     titanomagnetite-destruction conduit decoupling.
  4. Spin-2 strike-projected Peclet across-vs-along-strike thermal/geochemical barrier
     sharpness on DOE GDR #1391 2-m temperature probes & Fournier silica/cation
     disequilibrium (dist_known_fault_px strictly banned and audited).
  5. Up-dip hanging-wall pullback onto near-surface fault emergence, Kostrov geodetic
     transtensional obliquity, Band 6 Radiometric Total Count + GeoDAWN K/eTh/eU
     metasomatism, and 10 m DEM quantile-debiased 3DEP 1 m LiDAR & fluvial chi breaks.
"""

from __future__ import annotations

import csv
import gc
import hashlib
from pathlib import Path
import struct
import sys
import zipfile

import numpy as np
from numpy.fft import fftfreq, irfft2, rfft2, rfftfreq
from numpy.lib.format import open_memmap
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gems86.io import BANDS, BAND_PHYSICS_VERIFIED, NODATA
from scripts.restore_data import EXTERNAL_PINS

GDR_AND_AUDIT_PINS: dict[str, str] = {
    "acquisition_block_id_100m.tif": "2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a",
    "gdr_wellspring_in_footprint.csv": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
    "gdr_volcanic_vents_in_footprint.csv": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
    "2m_temperature_probe_INGENIOUS_regional_data.zip": "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3",
    "paleo_geothermal_regional.zip": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
}

BANNED_CSV_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})

EXPECTED_NATIVE_BANDS: dict[int, str] = {
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

PFTE_STATIC_NAMES: tuple[str, ...] = (
    "parker3d_marussi_diff_curv",
    "parker3d_hyperbolic_contact_saddle",
    "parker3d_beiki_curv_tilt_sharp",
    "parker3d_laplace_gzz_step",
    "updip_pullback_marussi_curv",
    "updip_pullback_contact_saddle",
    "baranov_pseudograv_cross_decouple",
    "baranov_hydro_demag_conduit",
    "updip_pullback_rtp_beiki_sharp",
    "tmi_up150_depth_persistence",
    "mt_cond_across_strike_gouge",
    "kostrov_transtens_obliquity_hp",
    "aseismic_strain_creep_deficit",
    "hypocenter_ramp_swarm_hp",
    "peclet_across_strike_geotherm_diseq",
    "peclet_across_strike_probe2m_wall",
    "paleo_sinter_travertine_corridor",
    "rad_tc_kth_metasomatic_step",
    "rad_uth_redox_front_seamfree",
    "marussi_conjugate_fault_intersect",
    "lidar1m_scarp_swath_debiased",
    "lidar1m_dipole_swath_debiased",
    "topo10_piedmont_break_lahontan_clean",
    "chi10_cross_watershed_knick",
)

PFTE_ABLATION_NAMES: tuple[str, ...] = (
    "unstripped_grav_slope_b5",
    "unstripped_rtp_gradmag_s2",
    "unstripped_depth_gradmag_s3",
    "unstripped_elev_slope_b19",
    "unstripped_lidar_step_debiased",
    "unstripped_topo10_slope_p90",
    "unstripped_strain_2ndinv_hp",
    "isotropic_geotherm_blur",
)

FOLD_ELASTIC_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
)


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pfte_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify native band contract, BAND_PHYSICS_VERIFIED overrides, and SHA-256 external pins."""
    for idx, expected in EXPECTED_NATIVE_BANDS.items():
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
        all_pins = {**EXTERNAL_PINS, **GDR_AND_AUDIT_PINS}
        for fname, expected_sha in all_pins.items():
            p = ext_root / fname
            if not p.is_file():
                raise FileNotFoundError(f"Missing pinned external input: {p}")
            got = _sha256_path(p)
            if got != expected_sha:
                raise RuntimeError(
                    f"SHA-256 mismatch for {fname}: got {got}, expected {expected_sha}"
                )
            ext_verified[fname] = got

    return {
        "verified_native_bands": {str(k): v for k, v in EXPECTED_NATIVE_BANDS.items()},
        "verified_overrides": {str(k): BAND_PHYSICS_VERIFIED[k] for k in (5, 6, 11, 18)},
        "verified_external_sha256": ext_verified,
        "banned_csv_columns": sorted(BANNED_CSV_COLUMNS),
    }


def _masked_gaussian(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    v = valid.astype(np.float32)
    num = ndi.gaussian_filter(
        np.where(valid, arr, 0.0).astype(np.float32), sigma=sigma, mode="nearest"
    )
    den = ndi.gaussian_filter(v, sigma=sigma, mode="nearest")
    return np.where(valid & (den > 1e-5), num / np.maximum(den, 1e-5), 0.0).astype(np.float32)


def _masked_gradients(
    arr: np.ndarray, valid: np.ndarray, sigma: float = 1.5
) -> tuple[np.ndarray, np.ndarray]:
    """Return (gx_east, gr_south) on right-handed image plane (col_east, row_south)."""
    sm = _masked_gaussian(arr, valid, sigma)
    gr = ndi.gaussian_filter(sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
    gx = ndi.gaussian_filter(sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
    gr[~valid] = 0.0
    gx[~valid] = 0.0
    return gx, gr


def _robust_pos_z(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    vals = arr[mask]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    q75, q25 = np.percentile(vals, [75.0, 25.0])
    scale = float(max((q75 - q25) * 0.7413, np.std(vals) * 0.5, 1e-6))
    z = (arr.astype(np.float32) - med) / scale
    return np.where(mask, np.clip(z, -8.0, 12.0), np.float32(0.0))


def _rank01(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    vals = np.nan_to_num(arr[mask], nan=0.0, posinf=0.0, neginf=0.0)
    if vals.size == 0 or np.ptp(vals) == 0.0:
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[mask] = ranks
    return out


def _read_native(ds: rasterio.DatasetReader, idx: int, valid: np.ndarray) -> np.ndarray:
    a = ds.read(idx).astype(np.float32)
    bad = ~np.isfinite(a) | (a <= NODATA * 0.5) | ~valid
    if bad.any():
        med = float(np.median(a[~bad])) if (~bad).any() else 0.0
        a[bad] = med
    return a


def _read_ext(ext_dir: Path, fname: str, idx: int, valid: np.ndarray) -> np.ndarray:
    with rasterio.open(ext_dir / fname) as ds:
        a = ds.read(idx).astype(np.float32)
    a[~np.isfinite(a) | ~valid] = 0.0
    return a


def cordell_parker_3d_basin_strip(
    b13_grav: np.ndarray,
    b18_gx_east: np.ndarray,
    b11_gr_south: np.ndarray,
    depth_to_basement_m: np.ndarray,
    valid: np.ndarray,
    *,
    cell_m: float = 100.0,
    z_char_m: float = 1500.0,
    shell_edges_m: tuple[float, ...] = (0.0, 300.0, 700.0, 1200.0, 1800.0, 2600.0, 4000.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Strip 3-D wavenumber-attenuated exponential-compaction sedimentary basin bowls
    (Cordell 1973; Parker 1973) from observed gravity potential & directional gradients.

    Because Cenozoic valley fill has negative density contrast (Delta_rho < 0) relative to
    pre-Cenozoic basement, the synthetic potential Phi_Parker <= 0 decreases with Z_b > 0
    and aligns positively with (b13_grav, +b18_gx_east, +b11_gr_south). Smooth unsupervised
    local vector coupling gamma >= 0 absorbs regional lithologic density-contrast variation
    without touching sharp intrabasin fault steps.
    """
    gz = np.asarray(b13_grav, dtype=np.float32)
    gx_obs = np.asarray(b18_gx_east, dtype=np.float32)
    gr_obs = np.asarray(b11_gr_south, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0)
    v = np.asarray(valid, dtype=bool)
    H, W = gz.shape

    taper = ndi.gaussian_filter(v.astype(np.float32), sigma=4.0, mode="constant")
    kr_f = fftfreq(H, d=cell_m).astype(np.float32)[:, None]
    kx_f = rfftfreq(W, d=cell_m).astype(np.float32)[None, :]
    k_mag = np.sqrt(kx_f * kx_f + kr_f * kr_f)
    k_nyq = float(0.5 / cell_m)
    anti_ring = np.exp(-((k_mag / (0.72 * k_nyq)) ** 4)).astype(np.float32)

    spec_sum = np.zeros((H, W // 2 + 1), dtype=np.complex64)
    # Smooth Z_b slightly before forward basin bowl synthesis so sharp basement fault steps
    # remain in the stripped residual rather than being subtracted out!
    zb_bowl = _masked_gaussian(zb, v, sigma=6.5)

    for m in range(len(shell_edges_m) - 1):
        z0 = float(shell_edges_m[m])
        z1 = float(shell_edges_m[m + 1])
        z_mid = 0.5 * (z0 + z1)
        dh = np.clip(zb_bowl - z0, 0.0, z1 - z0)
        dh_hp = (dh - _masked_gaussian(dh, v, sigma=48.0)) * taper
        w_comp = float(np.exp(-z_mid / float(z_char_m)))
        prop = (w_comp * np.exp(-2.0 * np.pi * z_mid * k_mag) * anti_ring).astype(np.float32)
        # Negative sign: thicker low-density basin produces negative gravity anomaly
        spec_sum -= rfft2(dh_hp, s=(H, W)).astype(np.complex64) * prop
    del zb_bowl, taper, anti_ring, k_mag

    phi_parker = irfft2(spec_sum, s=(H, W)).astype(np.float32)
    gx_parker = irfft2(
        spec_sum * (1j * 2.0 * np.pi * kx_f).astype(np.complex64), s=(H, W)
    ).astype(np.float32)
    gr_parker = irfft2(
        spec_sum * (1j * 2.0 * np.pi * kr_f).astype(np.complex64), s=(H, W)
    ).astype(np.float32)
    del spec_sum, kx_f, kr_f

    # Fit smooth regional coupling scalar gamma_vec >= 0 in gradient vector space
    dot_gp = _masked_gaussian(gx_obs * gx_parker + gr_obs * gr_parker, v, sigma=20.0)
    norm_pp = _masked_gaussian(gx_parker * gx_parker + gr_parker * gr_parker, v, sigma=20.0)
    eps_p = float(np.percentile(norm_pp[v], 25) * 0.1 + 1e-12) if v.any() else 1e-12
    gamma_vec = np.clip(dot_gp / (norm_pp + eps_p), 0.0, 1e6).astype(np.float32)

    gz_hp = gz - _masked_gaussian(gz, v, sigma=48.0)
    dot_zp = _masked_gaussian(gz_hp * phi_parker, v, sigma=20.0)
    norm_zz = _masked_gaussian(phi_parker * phi_parker, v, sigma=20.0)
    eps_z = float(np.percentile(norm_zz[v], 25) * 0.1 + 1e-12) if v.any() else 1e-12
    gamma_pot = np.clip(dot_zp / (norm_zz + eps_z), 0.0, 1e6).astype(np.float32)

    dg_z = np.where(v, gz_hp - 0.75 * gamma_pot * phi_parker, np.float32(0.0)).astype(np.float32)
    dg_x = np.where(v, gx_obs - 0.75 * gamma_vec * gx_parker, np.float32(0.0)).astype(np.float32)
    dg_r = np.where(v, gr_obs - 0.75 * gamma_vec * gr_parker, np.float32(0.0)).astype(np.float32)
    return dg_z, dg_x, dg_r


def marussi_curvature_eigensystem(
    dg_x: np.ndarray,
    dg_r: np.ndarray,
    valid: np.ndarray,
    *,
    sigma_deriv: float = 1.3,
) -> dict[str, np.ndarray]:
    """Compute symmetric 2x2 horizontal Marussi gravity curvature invariants,
    conservative curl gridding-seam suppressor, Beiki (2010) curvature-tilt sharpness,
    and headless spin-2 fault-strike director (c2_strike, s2_strike).

    Coordinate convention: x = East (+col), r = South (+row).
    """
    gx = np.where(valid, np.asarray(dg_x, dtype=np.float32), np.float32(0.0))
    gr = np.where(valid, np.asarray(dg_r, dtype=np.float32), np.float32(0.0))
    v = np.asarray(valid, dtype=bool)

    gxx = ndi.gaussian_filter(gx, sigma=sigma_deriv, order=(0, 1), mode="nearest").astype(
        np.float32
    )
    grr = ndi.gaussian_filter(gr, sigma=sigma_deriv, order=(1, 0), mode="nearest").astype(
        np.float32
    )
    gxr = ndi.gaussian_filter(gx, sigma=sigma_deriv, order=(1, 0), mode="nearest").astype(
        np.float32
    )
    grx = ndi.gaussian_filter(gr, sigma=sigma_deriv, order=(0, 1), mode="nearest").astype(
        np.float32
    )

    # Conservative potential-field curl |d_r g_x - d_x g_r| flags gridding/stitch seams
    frob = np.sqrt(gxx * gxx + grr * grr + 0.5 * (gxr * gxr + grx * grx))
    eps_f = float(np.percentile(frob[v], 15) * 0.1 + 1e-9) if v.any() else 1e-9
    curl_ratio = np.abs(gxr - grx) / (frob + eps_f)
    curl_clean = np.where(v, np.clip(1.0 - 0.65 * curl_ratio, 0.25, 1.0), np.float32(0.0)).astype(
        np.float32
    )

    gsym = 0.5 * (gxr + grx)
    tr = gxx + grr  # Laplace: g_zz = -(g_xx + g_rr) = -tr
    gzz = -tr
    diff_curv = np.hypot(gxx - grr, 2.0 * gsym).astype(np.float32)  # lambda_1 - lambda_2 >= 0
    det_t = gxx * grr - gsym * gsym  # lambda_1 * lambda_2

    # Hyperbolic fault-contact saddle: > 0 along elongated step/hinge saddles, == 0 on circular plugs (det > 0)
    contact_saddle = (np.sqrt(np.maximum(-det_t, 0.0)) * curl_clean).astype(np.float32)
    diff_curv_clean = (diff_curv * curl_clean).astype(np.float32)

    # Beiki (2010) curvature-tilt angle & zero-contour sharpness
    gh = np.hypot(gx, gr)
    scale_h = float(np.median(diff_curv[v]) / max(float(np.median(gh[v])), 1e-6)) if v.any() else 0.4
    denom_beiki = np.sqrt(diff_curv * diff_curv + (scale_h * gh) ** 2 + eps_f * eps_f)
    theta_beiki = np.arctan2(gzz, denom_beiki).astype(np.float32)
    tb_x = ndi.gaussian_filter(theta_beiki, sigma=1.1, order=(0, 1), mode="nearest")
    tb_r = ndi.gaussian_filter(theta_beiki, sigma=1.1, order=(1, 0), mode="nearest")
    sech2 = (1.0 / np.cosh(np.clip(theta_beiki / 0.38, -8.0, 8.0))) ** 2
    beiki_sharp = np.where(v, np.hypot(tb_x, tb_r) * sech2 * curl_clean, np.float32(0.0)).astype(
        np.float32
    )

    # Spin-2 fault-strike director: normal direction combines gradient vector (gx, gr) and principal curvature
    # For gradient (gx, gr), normal double-angle is (gx^2 - gr^2, 2*gx*gr)/gh^2, so strike (theta_n + pi/2)
    # negates the spin-2 vector: c2_strike = (gr^2 - gx^2)/(gh^2 + eps), s2_strike = -2*gx*gr/(gh^2 + eps).
    gh2 = gx * gx + gr * gr
    eps_g2 = float(np.percentile(gh2[v], 15) * 0.05 + 1e-12) if v.any() else 1e-12
    c2_grad = (gr * gr - gx * gx) / (gh2 + eps_g2)
    s2_grad = (-2.0 * gx * gr) / (gh2 + eps_g2)

    # Principal eigenvector of T has double-angle ((gxx - grr)/diff, 2*gsym/diff); fault strike perpendicular:
    eps_d = float(np.percentile(diff_curv[v], 15) * 0.05 + 1e-12) if v.any() else 1e-12
    c2_curv = -(gxx - grr) / (diff_curv + eps_d)
    s2_curv = -(2.0 * gsym) / (diff_curv + eps_d)

    c2_raw = _masked_gaussian(0.60 * c2_grad + 0.40 * c2_curv, v, sigma=2.2)
    s2_raw = _masked_gaussian(0.60 * s2_grad + 0.40 * s2_curv, v, sigma=2.2)
    n2 = np.hypot(c2_raw, s2_raw) + np.float32(1e-6)
    c2_strike = np.where(v, c2_raw / n2, np.float32(1.0)).astype(np.float32)
    s2_strike = np.where(v, s2_raw / n2, np.float32(0.0)).astype(np.float32)

    laplace_gzz_step = np.where(v, np.abs(gzz) * curl_clean, np.float32(0.0)).astype(np.float32)

    return {
        "diff_curv": np.where(v, diff_curv_clean, np.float32(0.0)),
        "contact_saddle": np.where(v, contact_saddle, np.float32(0.0)),
        "beiki_sharp": beiki_sharp,
        "laplace_gzz_step": laplace_gzz_step,
        "curl_clean": curl_clean,
        "c2_strike": c2_strike,
        "s2_strike": s2_strike,
    }


def baranov_pseudogravity_decoupling(
    b2_rtp: np.ndarray,
    dg_x: np.ndarray,
    dg_r: np.ndarray,
    valid: np.ndarray,
    seam_keep: np.ndarray | None = None,
    *,
    cell_m: float = 100.0,
    z_reg_m: float = 120.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Baranov (1957) 2-D FFT pseudogravity vector non-collinearity,
    hydrothermal magnetite-destruction conduit excess, and RTP Beiki sharpness."""
    rtp = np.asarray(b2_rtp, dtype=np.float32)
    gx = np.asarray(dg_x, dtype=np.float32)
    gr = np.asarray(dg_r, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    sk = np.ones_like(rtp) if seam_keep is None else np.asarray(seam_keep, dtype=np.float32)
    H, W = rtp.shape

    rtp_hp = rtp - _masked_gaussian(rtp, v, sigma=36.0)
    taper = ndi.gaussian_filter(v.astype(np.float32), sigma=4.0, mode="constant")
    spec_m = rfft2(np.where(v, rtp_hp, 0.0) * taper, s=(H, W))
    del rtp_hp, taper

    kr_f = fftfreq(H, d=cell_m).astype(np.float32)[:, None]
    kx_f = rfftfreq(W, d=cell_m).astype(np.float32)[None, :]
    k_mag = np.sqrt(kx_f * kx_f + kr_f * kr_f)
    k0 = float(1.0 / 25000.0)
    k_nyq = float(0.5 / cell_m)
    reg = (
        np.exp(-2.0 * np.pi * float(z_reg_m) * k_mag)
        * np.exp(-((k_mag / (0.75 * k_nyq)) ** 4))
        / np.sqrt(k_mag * k_mag + k0 * k0)
    ).astype(np.float32)

    px = irfft2(spec_m * (1j * kx_f * reg).astype(np.complex64), s=(H, W)).astype(np.float32)
    pr = irfft2(spec_m * (1j * kr_f * reg).astype(np.complex64), s=(H, W)).astype(np.float32)
    del spec_m, kx_f, kr_f, k_mag, reg

    gn = np.hypot(gx, gr)
    pn = np.hypot(px, pr)
    eps_g = float(np.percentile(gn[v], 15) * 0.1 + 1e-9) if v.any() else 1e-9
    eps_p = float(np.percentile(pn[v], 15) * 0.1 + 1e-9) if v.any() else 1e-9

    sin_ang = np.abs(gx * pr - gr * px) / ((gn + eps_g) * (pn + eps_p))
    rg = _rank01(gn, v)
    rp = _rank01(pn, v)
    cross_decouple = np.where(
        v, sin_ang * np.sqrt(rg * rp + 1e-8) * sk, np.float32(0.0)
    ).astype(np.float32)

    # Hydrothermal demagnetization along density steps: strong gravity step + weak pseudogravity + RTP trough
    rtp_trough = np.maximum(_masked_gaussian(rtp, v, 9.0) - _masked_gaussian(rtp, v, 2.0), 0.0)
    hydro_demag = np.where(
        v,
        rg * np.maximum(rg - 0.70 * rp, 0.0) * (0.35 + 0.65 * _rank01(rtp_trough, v)) * sk,
        np.float32(0.0),
    ).astype(np.float32)

    rtp_marussi = marussi_curvature_eigensystem(px, pr, v, sigma_deriv=1.2)
    rtp_beiki = (rtp_marussi["beiki_sharp"] * sk).astype(np.float32)
    return cross_decouple, hydro_demag, rtp_beiki


def peclet_across_strike_barrier(
    field: np.ndarray,
    c2_strike: np.ndarray,
    s2_strike: np.ndarray,
    valid: np.ndarray,
    *,
    sigma_grad: float = 2.5,
) -> np.ndarray:
    """Project gradient of ``field`` onto headless spin-2 fault frame (c2_strike, s2_strike)
    to isolate sharp across-strike thermal/geochemical/clay-gouge barriers while penalizing
    circular or isotropic plumes.

    Exact branch-cut-free spin-2 identities for v = (vx, vr):
      |v . e_strike|^2 = 0.5*(vx^2 + vr^2) + 0.5*(vx^2 - vr^2)*c2 + vx*vr*s2
      |v . e_perp|^2   = 0.5*(vx^2 + vr^2) - 0.5*(vx^2 - vr^2)*c2 - vx*vr*s2
    """
    f = np.asarray(field, dtype=np.float32)
    c2 = np.asarray(c2_strike, dtype=np.float32)
    s2 = np.asarray(s2_strike, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)

    vx, vr = _masked_gradients(f, v, sigma=sigma_grad)
    v2 = vx * vx + vr * vr
    aniso = 0.5 * (vx * vx - vr * vr) * c2 + vx * vr * s2
    g_perp = np.sqrt(np.maximum(0.5 * v2 - aniso, 0.0))
    g_par = np.sqrt(np.maximum(0.5 * v2 + aniso, 0.0))
    eps = float(np.percentile(np.sqrt(v2[v]), 20) * 0.15 + 1e-9) if v.any() else 1e-9
    peclet_aniso = g_perp / (g_perp + g_par + eps)
    return np.where(v, g_perp * peclet_aniso, np.float32(0.0)).astype(np.float32)


def updip_hangingwall_pullback(
    deep_plane: np.ndarray,
    depth_to_basement_m: np.ndarray,
    valid: np.ndarray,
    *,
    dip_deg: float = 60.0,
    max_shift_px: float = 8.0,
    cell_m: float = 100.0,
    pulled_weight: float = 0.65,
) -> tuple[np.ndarray, np.ndarray]:
    """Map buried hanging-wall step anomalies up-dip along -grad(Z_b) onto surface emergence."""
    plane = np.asarray(deep_plane, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0)
    v = np.asarray(valid, dtype=bool)
    H, W = plane.shape

    zb_sm = _masked_gaussian(zb, v, sigma=3.5)
    gz_r = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(1, 0), mode="nearest")
    gz_c = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(0, 1), mode="nearest")
    gnorm = np.hypot(gz_r, gz_c) + np.float32(5.0)
    ur = (gz_r / gnorm).astype(np.float32)
    uc = (gz_c / gnorm).astype(np.float32)

    rr, cc = np.indices((H, W), dtype=np.float32)
    zb_ahead = ndi.map_coordinates(
        zb_sm,
        [np.clip(rr + 3.0 * ur, 0.0, H - 1.0), np.clip(cc + 3.0 * uc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    )
    cot_dip = float(1.0 / np.tan(np.deg2rad(dip_deg)))
    ds = np.clip((zb_ahead / float(cell_m)) * cot_dip, 0.0, float(max_shift_px)).astype(
        np.float32
    )
    pulled = ndi.map_coordinates(
        plane,
        [np.clip(rr + ds * ur, 0.0, H - 1.0), np.clip(cc + ds * uc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    ).astype(np.float32)
    combined = np.where(
        v, float(pulled_weight) * pulled + (1.0 - float(pulled_weight)) * plane, np.float32(0.0)
    ).astype(np.float32)

    z_rr = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(2, 0), mode="nearest")
    z_cc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(0, 2), mode="nearest")
    z_rc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(1, 1), mode="nearest")
    d2z_du2 = ur * ur * z_rr + 2.0 * ur * uc * z_rc + uc * uc * z_cc
    basin_gate = np.exp(-(((zb_sm - 850.0) / 750.0) ** 2)) * (zb_sm > 80.0).astype(np.float32)
    keystone = np.where(v, np.maximum(-d2z_du2, 0.0) * basin_gate, np.float32(0.0)).astype(
        np.float32
    )
    return combined, keystone


def _hessian_ridge_and_eccentricity(
    field: np.ndarray, valid: np.ndarray, sigma: float = 2.2
) -> tuple[np.ndarray, np.ndarray]:
    sm = _masked_gaussian(field, valid, sigma)
    frr = ndi.gaussian_filter(sm, sigma=1.0, order=(2, 0), mode="nearest")
    fcc = ndi.gaussian_filter(sm, sigma=1.0, order=(0, 2), mode="nearest")
    frc = ndi.gaussian_filter(sm, sigma=1.0, order=(1, 1), mode="nearest")
    tr = frr + fcc
    df = np.hypot(frr - fcc, 2.0 * frc)
    lam_min = 0.5 * (tr - df)
    lam_max = 0.5 * (tr + df)
    ridge = np.where(valid, np.maximum(-lam_min, 0.0), np.float32(0.0)).astype(np.float32)
    ecc = np.where(
        valid,
        df / (np.abs(lam_min) + np.abs(lam_max) + 1e-6),
        np.float32(0.0),
    ).astype(np.float32)
    return ridge, np.clip(ecc, 0.0, 1.0)


def _structure_tensor_intersection(
    trace_field: np.ndarray,
    valid: np.ndarray,
    *,
    sigma_grad: float = 1.2,
    sigma_int: float = 4.0,
) -> np.ndarray:
    gx, gr = _masked_gradients(trace_field, valid, sigma=sigma_grad)
    jxx = _masked_gaussian(gx * gx, valid, sigma_int)
    jrr = _masked_gaussian(gr * gr, valid, sigma_int)
    jxr = _masked_gaussian(gx * gr, valid, sigma_int)
    det_j = np.maximum(jxx * jrr - jxr * jxr, 0.0)
    tr_j = jxx + jrr + 1e-9
    return np.where(valid, np.sqrt(det_j) * (det_j / (tr_j * tr_j)), np.float32(0.0)).astype(
        np.float32
    )


def _geodawn_seam_keep_mask(ext_dir: Path, valid: np.ndarray) -> np.ndarray:
    blk = _read_ext(ext_dir, "acquisition_block_id_100m.tif", 1, valid)
    b_max = ndi.maximum_filter(blk, size=3, mode="nearest")
    b_min = ndi.minimum_filter(blk, size=3, mode="nearest")
    seam = valid & (b_max != b_min) & (b_min > 0)
    seam_halo = ndi.gaussian_filter(
        ndi.binary_dilation(seam, iterations=2).astype(np.float32), sigma=1.2, mode="nearest"
    )
    seam_halo = np.clip(seam_halo / max(float(seam_halo.max()), 1e-6), 0.0, 1.0)
    return np.where(valid, 1.0 - 0.82 * seam_halo, np.float32(0.0)).astype(np.float32)


def _gdr_peclet_geothermal_planes(
    ext_dir: Path,
    valid: np.ndarray,
    dem_mean: np.ndarray,
    c2_strike: np.ndarray,
    s2_strike: np.ndarray,
    accessed_columns: dict[str, tuple[str, ...]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build strike-projected Peclet thermal/geochemical barrier planes from DOE GDR #1391
    without ever reading ``dist_known_fault_px``."""
    shape = valid.shape

    dem_sm = _masked_gaussian(dem_mean, valid, sigma=6.0)
    gr = ndi.gaussian_filter(dem_sm, sigma=2.5, order=(1, 0), mode="nearest")
    gc_ = ndi.gaussian_filter(dem_sm, sigma=2.5, order=(0, 1), mode="nearest")
    gn = np.hypot(gr, gc_) + np.float32(1.5)
    ur_up = (gr / gn).astype(np.float32)
    uc_up = (gc_ / gn).astype(np.float32)
    del dem_sm, gr, gc_, gn

    # 1. Fournier silica/cation geothermometer disequilibrium (strictly excluding dist_known_fault_px)
    ws_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c")
    assert not (set(ws_cols) & BANNED_CSV_COLUMNS)
    accessed_columns["gdr_wellspring_in_footprint.csv"] = ws_cols

    imp_up = np.zeros(shape, dtype=np.float32)
    imp_iso = np.zeros(shape, dtype=np.float32)
    with (ext_dir / "gdr_wellspring_in_footprint.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or not set(ws_cols).issubset(reader.fieldnames):
            raise RuntimeError("Unexpected header in gdr_wellspring_in_footprint.csv")
        for row in reader:
            try:
                r = int(row["row"])
                c = int(row["col"])
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]) or not valid[r, c]:
                continue
            t_meas = float(row["temp_c"]) if row.get("temp_c") else 0.0
            t_qtz = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") else 0.0
            t_ch = float(row["geothermchalc_c"]) if row.get("geothermchalc_c") else 0.0
            t_cat = float(row["geothermcat_c"]) if row.get("geothermcat_c") else 0.0
            t_res = max(t_qtz, t_ch, min(t_cat, 260.0))
            diseq = max(t_res - max(t_meas, 14.0), 0.0) / 85.0
            direct = max(t_meas - 20.0, 0.0) / 45.0
            score = float(min(0.68 * diseq + 0.32 * max(t_res - 75.0, 0.0) / 95.0 + 0.28 * direct, 5.0))
            if score <= 0.02:
                continue
            if score > imp_iso[r, c]:
                imp_iso[r, c] = score
            ru = int(np.clip(round(r + 3.5 * float(ur_up[r, c])), 0, shape[0] - 1))
            cu = int(np.clip(round(c + 3.5 * float(uc_up[r, c])), 0, shape[1] - 1))
            if score > imp_up[ru, cu]:
                imp_up[ru, cu] = score

    diseq_plume = (
        0.65 * ndi.gaussian_filter(imp_up, sigma=4.5, mode="constant")
        + 0.35 * ndi.gaussian_filter(imp_up, sigma=12.0, mode="constant")
    ).astype(np.float32)
    iso_geoth = ndi.gaussian_filter(imp_iso, sigma=10.0, mode="constant").astype(np.float32)
    diseq_plume[~valid] = 0.0
    iso_geoth[~valid] = 0.0
    del imp_up, imp_iso

    diseq_bar = peclet_across_strike_barrier(diseq_plume, c2_strike, s2_strike, valid, sigma_grad=2.2)
    peclet_diseq = np.where(
        valid,
        0.58 * _rank01(diseq_bar, valid) + 0.42 * _rank01(diseq_plume, valid),
        np.float32(0.0),
    ).astype(np.float32)
    del diseq_plume, diseq_bar

    # 2. DOE GDR #1391 2-m temperature probes (3,800 probes) across-strike Peclet barrier
    with zipfile.ZipFile(ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip") as zf:
        dbf = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
        shp = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp"
        )
    nrec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while dbf[pos] != 0x0D:
        fields.append((dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii"), dbf[pos + 16]))
        pos += 32
    accessed_columns["2m_temperature_probe_n83geo.dbf"] = ("F2mDAB",)

    lons: list[float] = []
    lats: list[float] = []
    dabs: list[float] = []
    shp_pos = 100
    for i in range(nrec):
        _, content_len = struct.unpack(">II", shp[shp_pos : shp_pos + 8])
        x, y = struct.unpack("<dd", shp[shp_pos + 12 : shp_pos + 28])
        shp_pos += 8 + content_len * 2
        row_bytes = dbf[hdr_len + i * rec_len + 1 : hdr_len + (i + 1) * rec_len]
        off = 0
        f2m_val = 0.0
        for fn, fl in fields:
            if fn == "F2mDAB":
                txt = row_bytes[off : off + fl].decode("utf-8", errors="replace").strip()
                f2m_val = float(txt) if txt else 0.0
            off += fl
        lons.append(x)
        lats.append(y)
        dabs.append(f2m_val)
    del dbf, shp

    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])

    p_anom = np.zeros(shape, dtype=np.float32)
    p_cnt = np.zeros(shape, dtype=np.float32)
    dab_pos = np.clip(np.nan_to_num(np.asarray(dabs, dtype=np.float32), nan=0.0), 0.0, 15.0)
    r_ib = rows[inb]
    c_ib = cols[inb]
    r_sh = np.clip(np.rint(r_ib + 2.5 * ur_up[r_ib, c_ib]).astype(np.int32), 0, shape[0] - 1)
    c_sh = np.clip(np.rint(c_ib + 2.5 * uc_up[r_ib, c_ib]).astype(np.int32), 0, shape[1] - 1)
    np.maximum.at(p_anom, (r_sh, c_sh), dab_pos[inb])
    np.add.at(p_cnt, (r_sh, c_sh), 1.0)
    del ur_up, uc_up

    num = ndi.gaussian_filter(p_anom, sigma=8.0, mode="constant")
    den = ndi.gaussian_filter((p_cnt > 0).astype(np.float32), sigma=8.0, mode="constant")
    plume = (num / (den + 0.01)).astype(np.float32)
    del p_anom, p_cnt, num, den
    p_bar = peclet_across_strike_barrier(plume, c2_strike, s2_strike, valid, sigma_grad=2.6)
    peclet_probe = np.where(
        valid, 0.62 * _rank01(p_bar, valid) + 0.38 * _rank01(plume, valid), np.float32(0.0)
    ).astype(np.float32)
    del plume, p_bar

    # 3. Paleo-geothermal sinter/travertine/tufa (726 sites) + Quaternary volcanic vents
    with zipfile.ZipFile(ext_dir / "paleo_geothermal_regional.zip") as zf:
        lines = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    accessed_columns["Paleo_geothermal_final.csv"] = ("Long_deg_NAD83", "Lat_deg_NAD83")
    slons: list[float] = []
    slats: list[float] = []
    for row in csv.DictReader(lines):
        try:
            slons.append(float(row["Long_deg_NAD83"]))
            slats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    sxs, sys_ = warp_transform("EPSG:4269", "EPSG:32611", lons=slons, lats=slats) if False else warp_transform("EPSG:4269", "EPSG:32611", slons, slats)
    scols = np.floor((np.asarray(sxs) - 243350.0) / 100.0).astype(np.int32)
    srows = np.floor((4508550.0 - np.asarray(sys_)) / 100.0).astype(np.int32)
    sinb = (srows >= 0) & (srows < shape[0]) & (scols >= 0) & (scols < shape[1])
    sinter_src = np.zeros(shape, dtype=bool)
    sinter_src[srows[sinb], scols[sinb]] = True

    vv_cols = ("row", "col")
    assert not (set(vv_cols) & BANNED_CSV_COLUMNS)
    accessed_columns["gdr_volcanic_vents_in_footprint.csv"] = vv_cols
    with (ext_dir / "gdr_volcanic_vents_in_footprint.csv").open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                vr = int(row["row"])
                vc = int(row["col"])
            except (KeyError, ValueError):
                continue
            if 0 <= vr < shape[0] and 0 <= vc < shape[1]:
                sinter_src[vr, vc] = True

    d_vent = ndi.distance_transform_edt(~sinter_src).astype(np.float32)
    sinter_corridor = np.where(
        valid,
        0.68 * np.exp(-d_vent / 6.0) + 0.32 * np.exp(-d_vent / 18.0),
        np.float32(0.0),
    ).astype(np.float32)
    del sinter_src, d_vent
    return peclet_diseq, peclet_probe, sinter_corridor, iso_geoth


def build_pfte_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_pfte_path: Path | None = None,
    out_ablation_path: Path | None = None,
    out_strike_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Stream all 24 H86M-PFTE planes + L_pfte corroboration + 8 ablation planes +
    spin-2 strike director (2, H, W) into float16 disk-backed memmaps (< 850 MiB RSS)."""
    qc = verify_pfte_input_contract(ext_dir)
    accessed_cols: dict[str, tuple[str, ...]] = {}

    with rasterio.open(feature_tif) as ds:
        H, W = ds.height, ds.width
        b2_probe = ds.read(2).astype(np.float32)
        feat_valid = np.isfinite(b2_probe) & (b2_probe > NODATA * 0.5)
        del b2_probe

    valid = feat_valid if footprint is None else (feat_valid & np.asarray(footprint, dtype=bool))
    n_pfte = len(PFTE_STATIC_NAMES)
    n_abl = len(PFTE_ABLATION_NAMES)

    if out_pfte_path is not None:
        out_pfte_path.parent.mkdir(parents=True, exist_ok=True)
        X_pfte = open_memmap(out_pfte_path, mode="w+", dtype=np.float16, shape=(n_pfte, H, W))
    else:
        X_pfte = np.zeros((n_pfte, H, W), dtype=np.float16)

    if out_ablation_path is not None:
        out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
        X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, H, W))
    else:
        X_abl = np.zeros((n_abl, H, W), dtype=np.float16)

    if out_strike_path is not None:
        out_strike_path.parent.mkdir(parents=True, exist_ok=True)
        strike_cs2 = open_memmap(out_strike_path, mode="w+", dtype=np.float16, shape=(2, H, W))
    else:
        strike_cs2 = np.zeros((2, H, W), dtype=np.float16)

    def _put_pfte(name: str, arr: np.ndarray) -> None:
        idx = PFTE_STATIC_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_pfte[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    def _put_abl(name: str, arr: np.ndarray) -> None:
        idx = PFTE_ABLATION_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)

    fam_marussi = np.zeros((H, W), dtype=np.float32)
    fam_geotherm = np.zeros((H, W), dtype=np.float32)
    fam_scarp = np.zeros((H, W), dtype=np.float32)
    fam_tect = np.zeros((H, W), dtype=np.float32)

    with rasterio.open(feature_tif) as ds:
        # 1. Cordell-Parker 3-D Spectral Basin Stripping + Marussi Curvature Eigensystem
        zb_m = _read_native(ds, 15, valid)
        z_gx, z_gr = _masked_gradients(zb_m, valid, sigma=3.0)
        _put_abl("unstripped_depth_gradmag_s3", np.hypot(z_gx, z_gr))
        del z_gx, z_gr

        b13 = _read_native(ds, 13, valid)
        b18 = _read_native(ds, 18, valid)  # +d(B13)/dx_east
        b11 = _read_native(ds, 11, valid)  # +d(B13)/drow_south
        b5 = _read_native(ds, 5, valid)
        _put_abl("unstripped_grav_slope_b5", b5)
        del b5

        _, dg_x, dg_r = cordell_parker_3d_basin_strip(b13, b18, b11, zb_m, valid)
        del b13, b18, b11
        gc.collect()

        mar = marussi_curvature_eigensystem(dg_x, dg_r, valid, sigma_deriv=1.3)
        diff_curv = mar["diff_curv"]
        contact_saddle = mar["contact_saddle"]
        beiki_sharp = mar["beiki_sharp"]
        lap_gzz = mar["laplace_gzz_step"]
        c2_grav = mar["c2_strike"]
        s2_grav = mar["s2_strike"]
        del mar

        _put_pfte("parker3d_marussi_diff_curv", diff_curv)
        _put_pfte("parker3d_hyperbolic_contact_saddle", contact_saddle)
        _put_pfte("parker3d_beiki_curv_tilt_sharp", beiki_sharp)
        _put_pfte("parker3d_laplace_gzz_step", lap_gzz)

        pull_curv, keystone_raw = updip_hangingwall_pullback(diff_curv, zb_m, valid)
        _put_pfte("updip_pullback_marussi_curv", pull_curv)
        pull_saddle_raw, _ = updip_hangingwall_pullback(contact_saddle, zb_m, valid)
        pull_saddle = (0.72 * pull_saddle_raw + 0.28 * keystone_raw).astype(np.float32)
        _put_pfte("updip_pullback_contact_saddle", pull_saddle)
        del diff_curv, contact_saddle, beiki_sharp, lap_gzz, pull_saddle_raw, keystone_raw
        gc.collect()

        # 2. Baranov (1957) FFT Pseudogravity Decoupling & Hydrothermal Demagnetization
        b2 = _read_native(ds, 2, valid)
        rtp_gx, rtp_gr = _masked_gradients(b2, valid, sigma=2.0)
        _put_abl("unstripped_rtp_gradmag_s2", np.hypot(rtp_gx, rtp_gr))
        del rtp_gx, rtp_gr

        cross_dec, hydro_demag, rtp_beiki = baranov_pseudogravity_decoupling(
            b2, dg_x, dg_r, valid, seam_keep
        )
        del b2, dg_x, dg_r
        _put_pfte("baranov_pseudograv_cross_decouple", cross_dec)
        _put_pfte("baranov_hydro_demag_conduit", hydro_demag)
        pull_rtp_beiki, _ = updip_hangingwall_pullback(rtp_beiki, zb_m, valid)
        _put_pfte("updip_pullback_rtp_beiki_sharp", pull_rtp_beiki)
        del rtp_beiki

        fam_marussi += (
            0.30 * _rank01(pull_curv, valid)
            + 0.28 * _rank01(pull_saddle, valid)
            + 0.22 * _rank01(pull_rtp_beiki, valid)
            + 0.20 * _rank01(cross_dec, valid)
        )
        del cross_dec, pull_rtp_beiki
        gc.collect()

        # 3. TMI Upward-Continued Persistence + Across-Strike MT Clay-Gouge Barrier
        b3 = _read_native(ds, 3, valid)
        b9 = _read_native(ds, 9, valid)
        h_tmi0 = np.hypot(b3, b9)
        del b3, b9
        tmi150 = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid)
        ux, ur = _masked_gradients(tmi150, valid, sigma=1.8)
        del tmi150
        h_tmi150 = np.hypot(ux, ur)
        del ux, ur
        r0 = _rank01(h_tmi0, valid)
        r150 = _rank01(h_tmi150, valid)
        del h_tmi0, h_tmi150
        tmi_persist = (np.sqrt(r0 * r150 + 1e-8) * (1.0 - 0.85 * np.abs(r0 - r150)) * seam_keep).astype(
            np.float32
        )
        del r0, r150
        _put_pfte("tmi_up150_depth_persistence", tmi_persist)
        fam_marussi += 0.14 * _rank01(tmi_persist, valid)
        del tmi_persist

        b17 = _read_native(ds, 17, valid)
        cond_log = np.log1p(np.maximum(b17 - float(np.min(b17[valid])), 0.0))
        del b17
        cond_ridge, cond_ecc = _hessian_ridge_and_eccentricity(cond_log, valid, sigma=2.4)
        cond_bar = peclet_across_strike_barrier(cond_log, c2_grav, s2_grav, valid, sigma_grad=2.2)
        del cond_log
        cond_gouge_raw = (
            0.55 * _rank01(cond_ridge * (cond_ecc**2), valid) + 0.45 * _rank01(cond_bar, valid)
        ).astype(np.float32)
        del cond_ridge, cond_ecc, cond_bar
        pull_cond, _ = updip_hangingwall_pullback(cond_gouge_raw, zb_m, valid)
        del cond_gouge_raw, zb_m
        _put_pfte("mt_cond_across_strike_gouge", pull_cond)
        fam_geotherm += 0.22 * _rank01(pull_cond, valid) + 0.18 * _rank01(hydro_demag, valid)
        del pull_cond, hydro_demag
        gc.collect()

        # 4. Kostrov Transtensional Obliquity, Creep Deficit & Hypocenter-Depth Ramps
        b4 = _read_native(ds, 4, valid)
        b7 = _read_native(ds, 7, valid)
        b8 = _read_native(ds, 8, valid)
        inv_hp = b4 - _masked_gaussian(b4, valid, 24.0)
        _put_abl("unstripped_strain_2ndinv_hp", inv_hp)
        dil_hp = np.maximum(b8 - _masked_gaussian(b8, valid, 24.0), 0.0)
        shr_hp = np.maximum(b7 - _masked_gaussian(b7, valid, 24.0), 0.0)
        del b4, b7, b8
        obliq = dil_hp / (np.hypot(shr_hp, dil_hp) + float(np.percentile(shr_hp[valid] + 1e-9, 25) * 0.2 + 1e-9))
        kostrov_transtens = (
            np.sqrt(shr_hp * dil_hp + 1e-12) * (0.45 + 0.55 * obliq) + 0.25 * np.maximum(inv_hp, 0.0)
        ).astype(np.float32)
        del inv_hp, dil_hp, shr_hp, obliq
        _put_pfte("kostrov_transtens_obliquity_hp", kostrov_transtens)

        b10 = _read_native(ds, 10, valid)
        b16 = _read_native(ds, 16, valid)
        b10_gx, b10_gr = _masked_gradients(b10, valid, sigma=2.5)
        b10_ramp = np.hypot(b10_gx, b10_gr)
        del b10_gx, b10_gr
        eq_prox = np.exp(-np.maximum(b10, 0.0) / float(np.median(b10[valid]) + 1e-6))
        ieq_hp = b16 - _masked_gaussian(b16, valid, 24.0)
        del b10, b16
        hypo_swarm = (
            0.45 * _rank01(b10_ramp * eq_prox, valid)
            + 0.35 * _rank01(eq_prox - _masked_gaussian(eq_prox, valid, 24.0), valid)
            + 0.20 * _rank01(ieq_hp, valid)
        ).astype(np.float32)
        del b10_ramp, eq_prox
        _put_pfte("hypocenter_ramp_swarm_hp", hypo_swarm)

        z_str = _robust_pos_z(kostrov_transtens, valid)
        z_ieq = _robust_pos_z(ieq_hp, valid)
        creep_def = np.where(
            valid, np.maximum(z_str - 0.65 * np.maximum(z_ieq, 0.0), 0.0), np.float32(0.0)
        ).astype(np.float32)
        del ieq_hp, z_str, z_ieq
        _put_pfte("aseismic_strain_creep_deficit", creep_def)
        fam_tect += (
            0.28 * _rank01(kostrov_transtens, valid)
            + 0.22 * _rank01(creep_def, valid)
            + 0.16 * _rank01(hypo_swarm, valid)
        )
        del kostrov_transtens, creep_def, hypo_swarm

        # Band 6 VERIFIED as GeoDAWN Airborne Radiometric Total Count (NEVER magnetic tilt)
        b6_tc = _read_native(ds, 6, valid)
        b19 = _read_native(ds, 19, valid)
        _put_abl("unstripped_elev_slope_b19", b19)
        b12 = _read_native(ds, 12, valid)
        elev_ridge, _ = _hessian_ridge_and_eccentricity(b12, valid, sigma=2.0)
        del b12
        slope_rel = b19 / (
            _masked_gaussian(b19, valid, 12.0) + float(np.percentile(b19[valid], 25) + 1e-4)
        )
        del b19
        gc.collect()

    # 5. Swath-Debiased 3DEP LiDAR + Multi-Sensor Spin-2 Fault Strike Director
    z_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)

    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as lds:
        li_has = valid & (lds.read(12) > 0)
        li_strike_u8 = lds.read(11).astype(np.float32)
        li_coh_u8 = lds.read(10).astype(np.float32)
    li_miss = valid & ~li_has

    # Blend Marussi gravity strike with coherent 1 m LiDAR scarp strike where LiDAR is present
    # LiDAR Band 11 encodes orientation in [0, pi) over [0..255]
    th_li = (li_strike_u8 / 255.0) * np.pi
    w_li = np.where(li_has, 0.45 * (li_coh_u8 / 255.0), np.float32(0.0)).astype(np.float32)
    c2_joint = (1.0 - w_li) * c2_grav + w_li * np.cos(2.0 * th_li).astype(np.float32)
    s2_joint = (1.0 - w_li) * s2_grav + w_li * np.sin(2.0 * th_li).astype(np.float32)
    nj = np.hypot(c2_joint, s2_joint) + np.float32(1e-6)
    c2_strike = np.where(valid, c2_joint / nj, np.float32(1.0)).astype(np.float32)
    s2_strike = np.where(valid, s2_joint / nj, np.float32(0.0)).astype(np.float32)
    del li_strike_u8, th_li, w_li, c2_joint, s2_joint, nj, c2_grav, s2_grav

    strike_cs2[0] = c2_strike.astype(np.float16)
    strike_cs2[1] = s2_strike.astype(np.float16)

    # 6. DOE GDR #1391 Strike-Guided Peclet Thermal/Geochemical Barriers & Radiometrics
    pec_diseq, pec_probe, sinter_corr, iso_geoth = _gdr_peclet_geothermal_planes(
        ext_dir, valid, z_m, c2_strike, s2_strike, accessed_cols
    )
    del z_m
    _put_abl("isotropic_geotherm_blur", iso_geoth)
    del iso_geoth

    struct_gate = (
        0.28 + 0.72 * (0.52 * _rank01(pull_curv, valid) + 0.48 * _rank01(pull_saddle, valid))
    ).astype(np.float32)
    pec_diseq_g = (pec_diseq * struct_gate).astype(np.float32)
    pec_probe_g = (pec_probe * struct_gate).astype(np.float32)
    sinter_corr_g = (sinter_corr * struct_gate).astype(np.float32)
    del pec_diseq, pec_probe, sinter_corr, struct_gate
    _put_pfte("peclet_across_strike_geotherm_diseq", pec_diseq_g)
    _put_pfte("peclet_across_strike_probe2m_wall", pec_probe_g)
    _put_pfte("paleo_sinter_travertine_corridor", sinter_corr_g)
    fam_geotherm += (
        0.18 * _rank01(pec_diseq_g, valid)
        + 0.16 * _rank01(pec_probe_g, valid)
        + 0.12 * _rank01(sinter_corr_g, valid)
    )
    del pec_diseq_g, pec_probe_g, sinter_corr_g

    # Potassium metasomatism using BOTH GeoDAWN K/eTh and native Band 6 TC (verified Total Count!)
    rad_K = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid)
    rad_Th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid)
    ext_ThK = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 1, valid)
    k_meta = (
        0.65 * ((rad_K + 1.0) / (rad_Th + 8.0))
        + 0.35 * ((rad_K + 1.0) / (np.maximum(b6_tc, 1.0) + 4.0))
        - 0.30 * (ext_ThK / 255.0)
    ).astype(np.float32)
    del rad_K, ext_ThK, b6_tc
    k_bar = peclet_across_strike_barrier(k_meta, c2_strike, s2_strike, valid, sigma_grad=1.8)
    del k_meta
    rad_kth = (k_bar * seam_keep * (1.0 - 0.55 * lahontan_band)).astype(np.float32)
    del k_bar
    _put_pfte("rad_tc_kth_metasomatic_step", rad_kth)

    rad_U = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid)
    ext_UTh = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 3, valid)
    uth_field = 0.6 * (ext_UTh / 255.0) + 0.4 * ((rad_U + 1.0) / (rad_Th + 8.0))
    del rad_U, rad_Th, ext_UTh
    uth_bar = peclet_across_strike_barrier(uth_field, c2_strike, s2_strike, valid, sigma_grad=1.8)
    del uth_field, c2_strike, s2_strike
    rad_uth = (uth_bar * seam_keep * (1.0 - 0.40 * lahontan_band)).astype(np.float32)
    del uth_bar, seam_keep
    _put_pfte("rad_uth_redox_front_seamfree", rad_uth)
    fam_geotherm += 0.14 * _rank01(rad_kth, valid)
    del rad_kth, rad_uth
    gc.collect()

    # 7. Piedmont Curvature, Swath-Debiased 3DEP 1 m LiDAR & Fluvial Chi
    topo_asp = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid)
    lahontan_mimic = np.where(
        valid,
        np.clip(
            lahontan_band
            * (topo_asp / 255.0)
            * (1.0 - np.clip(_rank01(pull_curv, valid), 0.0, 1.0)),
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
    _put_pfte("topo10_piedmont_break_lahontan_clean", topo10_pied)
    fam_scarp += 0.34 * _rank01(topo10_pied, valid)

    topo_slope_10m = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_abl("unstripped_topo10_slope_p90", topo_slope_10m)

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
        X_abl, PFTE_ABLATION_NAMES.index("unstripped_lidar_step_debiased"), li_step / 255.0, topo_slope_10m
    )
    del topo_slope_10m

    li_cross = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 8, valid)
    li_scarp = (
        (li_step / 255.0)
        * (0.5 + 0.5 * (li_cross / 255.0))
        * (0.35 + 0.65 * (li_coh_u8 / 255.0))
        * (1.0 - 0.65 * lahontan_mimic)
    ).astype(np.float32)
    del li_step, li_cross
    li_scarp_r = _put_lidar_swath_debiased(
        X_pfte, PFTE_STATIC_NAMES.index("lidar1m_scarp_swath_debiased"), li_scarp, topo10_pied
    )
    fam_scarp += 0.42 * li_scarp_r

    li_dn = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 6, valid)
    li_up = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 7, valid)
    li_ln = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 4, valid)
    li_lp = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 5, valid)
    li_dip = (
        (np.maximum(li_dn, li_up) / 255.0)
        * np.sqrt((li_ln / 255.0) * (li_lp / 255.0) + 1e-6)
        * (0.4 + 0.6 * (li_coh_u8 / 255.0))
    ).astype(np.float32)
    del li_dn, li_up, li_ln, li_lp, li_coh_u8
    li_dip_r = _put_lidar_swath_debiased(
        X_pfte, PFTE_STATIC_NAMES.index("lidar1m_dipole_swath_debiased"), li_dip, topo10_pied
    )
    fam_scarp += 0.24 * li_dip_r
    del li_scarp, li_dip, li_dip_r, li_has, li_miss

    comp_trace = (
        0.36 * _rank01(pull_curv, valid)
        + 0.28 * _rank01(pull_saddle, valid)
        + 0.22 * li_scarp_r
        + 0.14 * _rank01(topo10_pied, valid)
    ).astype(np.float32)
    del pull_curv, pull_saddle, li_scarp_r, topo10_pied
    conj_inter = _structure_tensor_intersection(comp_trace, valid, sigma_grad=1.2, sigma_int=4.0)
    del comp_trace
    _put_pfte("marussi_conjugate_fault_intersect", conj_inter)
    fam_geotherm += 0.24 * _rank01(conj_inter, valid)
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
    _put_pfte("chi10_cross_watershed_knick", chi_knick)
    fam_tect += 0.34 * _rank01(chi_knick, valid)
    del chi_knick

    L_raw = (
        0.38 * fam_marussi
        + 0.22 * fam_geotherm
        + 0.26 * fam_scarp
        + 0.14 * fam_tect
        - 0.18 * lahontan_mimic
    )
    del fam_marussi, fam_geotherm, fam_scarp, fam_tect, lahontan_mimic
    L_pfte = _rank01(L_raw, valid)
    del L_raw
    gc.collect()

    if out_pfte_path is not None:
        X_pfte.flush()
        del X_pfte
        X_pfte = np.load(out_pfte_path, mmap_mode="r")
    if out_ablation_path is not None:
        X_abl.flush()
        del X_abl
        X_abl = np.load(out_ablation_path, mmap_mode="r")
    if out_strike_path is not None:
        strike_cs2.flush()
        del strike_cs2
        strike_cs2 = np.load(out_strike_path, mmap_mode="r")

    qc["accessed_csv_columns"] = {k: list(v) for k, v in accessed_cols.items()}
    return X_pfte, L_pfte, X_abl, strike_cs2, valid, qc
