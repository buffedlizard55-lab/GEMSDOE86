"""Feature engineering, spin-2 strike directors, filament sharpening, and
strike-concordant kinematic fields for Lane H86C-KSLB.

Strict zero-leakage guarantees (AST-audited in `tests/test_h86c_kslb.py`):
- `build_physical_planes` NEVER reads `existing_faults.tif`, `labels.tif`,
  `gdr_qfaults_traces.csv`, or `derived_sgmc_faults_100m_u8.tif`.
- `dist_known_fault_px` in GDR-1391 CSVs is explicitly forbidden and never read.
- All 48 float32 planes and auxiliary label-free spin-2 director / multi-family
  consensus maps are persisted under `.cache/gems86_data/cache/h86c_planes/` and
  memory-mapped one plane at a time so peak RSS stays well below 1.6 GiB.
"""
from __future__ import annotations

import csv
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.signal import oaconvolve
from sklearn.linear_model import HuberRegressor

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57.faultzone import _fragment_stats
from gems57.network import local_strike
from gems57.relay_bend_anatomy import host_bend_fields, two_host_frame

DEFAULT_DATA_DIR = ROOT / ".cache" / "gems86_data"

PHYS_FEATURES: tuple[str, ...] = (
    # Block 1: Seamless 10m 3DEP Geomorphology, 1m LiDAR & Lahontan Shoreline Deconfounding (14)
    "topo10_curv_prof_z",
    "topo10_hs_lineament_z",
    "topo10_aspect_coh_z",
    "topo10_piedmont_scarp",
    "topo10_scarp_chain",
    "lahontan_zone_weight",
    "lahontan_shoreline_mimic",
    "tectonic_scarp_deconf",
    "tectonic_scarp_chain",
    "lidar_valid",
    "lidar_step_z",
    "lidar_face_asym",
    "dem_piedmont_hinge",
    "dem_valley_chain",
    # Block 2: 10m Fluvial ksn Knickzones, Chi Steps & Rad-Topo Discordance (8)
    "fluv_ksn_knick_s2",
    "fluv_ksn_chain_s5",
    "fluv_chi_step_s3",
    "fluv_scarp_knick_couple",
    "zmean_elev_z",
    "topo10_slope_p90_z",
    "rad_topo_discord_K",
    "rad_topo_discord_UTh",
    # Block 3: Blakely-Miller Tilt Zero-Crossings, Contact-Offsets & Basement Hinge Flexure (14)
    "mag_blakely_zerocross",
    "grav_blakely_zerocross",
    "blakely_joint_zerocross",
    "mag_rtp_grad_s1",
    "mag_rtp_ridge_s1",
    "mag_rtp_ridge_s3",
    "mag_tc_z",
    "mag_up150_atten_grad",
    "mag_turn_disruption",
    "grav_hg_z",
    "contact_offset_grav_mag",
    "grav_mag_concord",
    "base_depth_z",
    "base_hinge_flexure",
    # Block 4: GDR-1391 Geothermometer Disequilibrium, Conductivity & Seismicity-Strain Fabric (12)
    "gt_diseq_s8",
    "gt_diseq_s22",
    "gt_kinlag_s15",
    "gt_thermal_s12",
    "cond_surf_z",
    "cond_surf_grad",
    "gt_conduit_couple",
    "strain_2ndinv_z",
    "strain_dilat_z",
    "strain_transtension",
    "seis_density_z",
    "seis_strain_fabric",
)

FORBIDDEN_CSV_COLUMNS = frozenset({"dist_known_fault_px"})


def plane_dir_for(data_dir: Path | None = None) -> Path:
    d = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    return d / "cache" / "h86c_planes"


def aux_dir_for(data_dir: Path | None = None) -> Path:
    d = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    return d / "cache" / "h86c_aux"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_band(a: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = valid & np.isfinite(a) & (np.abs(a) < 1e18)
    med = float(np.median(a[ok])) if ok.any() else 0.0
    out = np.where(ok, a, med).astype(np.float32)
    return out, ok


def _robust_z(a: np.ndarray, valid: np.ndarray, clip: float = 8.0) -> np.ndarray:
    out = np.zeros(a.shape, dtype=np.float32)
    ok = valid & np.isfinite(a)
    if not ok.any():
        return out
    vals = a[ok]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826
    if not np.isfinite(mad) or mad < 1e-6:
        mad = max(float(np.std(vals)), 1e-6)
    z = np.clip((vals - med) / mad, -clip, clip)
    out[ok] = z.astype(np.float32)
    return out


def _pos_unit(a: np.ndarray, valid: np.ndarray, pct: float = 99.0) -> np.ndarray:
    out = np.zeros(a.shape, dtype=np.float32)
    ok = valid & np.isfinite(a)
    if not ok.any():
        return out
    vals = a[ok]
    lo = float(np.percentile(vals, 5.0))
    hi = float(np.percentile(vals, pct))
    scale = max(hi - lo, 1e-6)
    out[ok] = np.clip((vals - lo) / scale, 0.0, 1.0).astype(np.float32)
    return out


def _grad_mag(a: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    return np.hypot(gx, gy).astype(np.float32)


def _hessian_sym_ridge(a: np.ndarray, sigma: float, mode_sign: str = "both") -> np.ndarray:
    s2 = np.float32(sigma * sigma)
    axx = ndi.gaussian_filter(a, sigma, order=(0, 2), mode="nearest") * s2
    ayy = ndi.gaussian_filter(a, sigma, order=(2, 0), mode="nearest") * s2
    axy = ndi.gaussian_filter(a, sigma, order=(1, 1), mode="nearest") * s2
    tr = 0.5 * (axx + ayy)
    rad = np.sqrt(np.maximum(0.25 * (axx - ayy) ** 2 + axy * axy, 0.0))
    l1 = tr + rad
    l2 = tr - rad
    if mode_sign == "ridge":
        return np.maximum(-l2, 0.0).astype(np.float32)
    if mode_sign == "valley":
        return np.maximum(l1, 0.0).astype(np.float32)
    return np.maximum(np.abs(l1), np.abs(l2)).astype(np.float32)


def _spin2_edge_director(a: np.ndarray, grad_sigma: float, tensor_sigma: float):
    """Spin-2 edge/contour strike director (cos2, sin2, coh) matching network.local_strike.

    For gradient (gy, gx) = (df/drow, df/dcol), the edge tangent is (-gx, gy) with
    geological strike theta = atan2(gy, gx), so cos(2*theta) = (gx^2 - gy^2)/norm^2
    and sin(2*theta) = (2*gx*gy)/norm^2.
    """
    gy = ndi.gaussian_filter(a, grad_sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, grad_sigma, order=(0, 1), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, tensor_sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, tensor_sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, tensor_sigma, mode="nearest")
    tr = np.maximum(jxx + jyy, 1e-12)
    dx = jxx - jyy
    dy = 2.0 * jxy
    mag = np.hypot(dx, dy)
    coh = np.clip(mag / tr, 0.0, 1.0).astype(np.float32)
    denom = np.maximum(mag, 1e-12)
    cos2 = (dx / denom).astype(np.float32)
    sin2 = (dy / denom).astype(np.float32)
    return cos2, sin2, coh


def _axial_chain_excess(field: np.ndarray, length: int = 9, n_angles: int = 8) -> np.ndarray:
    """Fast overlap-add FFT directional collinearity excess over isotropic background."""
    half = length // 2
    acc_sum = np.zeros(field.shape, dtype=np.float32)
    acc_max = np.full(field.shape, -1e9, dtype=np.float32)
    t_vals = np.linspace(-half, half, length)
    f32 = np.asarray(field, dtype=np.float32)
    for k in range(n_angles):
        ang = np.pi * k / n_angles
        ker = np.zeros((length, length), dtype=np.float32)
        rr = np.clip(np.rint(half + t_vals * np.sin(ang)).astype(int), 0, length - 1)
        cc = np.clip(np.rint(half + t_vals * np.cos(ang)).astype(int), 0, length - 1)
        ker[rr, cc] = 1.0
        ker /= max(float(ker.sum()), 1.0)
        resp = oaconvolve(f32, ker, mode="same").astype(np.float32)
        np.maximum(acc_max, resp, out=acc_max)
        acc_sum += resp
    return np.maximum(acc_max - acc_sum / float(n_angles), 0.0).astype(np.float32)


def filament_enhance(
    prob: np.ndarray,
    valid: np.ndarray,
    sig_par: float = 3.8,
    sig_perp: float = 1.0,
    n_angles: int = 8,
) -> np.ndarray:
    """8-azimuth anisotropic Difference-of-Gaussians curvilinear filament enhancer."""
    p = np.where(valid & np.isfinite(prob), np.clip(prob, 0.0, 1.0), 0.0).astype(np.float32)
    rad = int(np.ceil(2.5 * sig_par))
    yy, xx = np.mgrid[-rad : rad + 1, -rad : rad + 1].astype(np.float32)
    best = np.zeros(p.shape, dtype=np.float32)
    for k in range(n_angles):
        ang = np.pi * k / n_angles
        ca, sa = float(np.cos(ang)), float(np.sin(ang))
        u_par = xx * ca + yy * sa
        u_perp = -xx * sa + yy * ca
        g_pos = np.exp(-0.5 * ((u_par / sig_par) ** 2 + (u_perp / sig_perp) ** 2))
        g_neg = np.exp(-0.5 * ((u_par / sig_par) ** 2 + (u_perp / (3.0 * sig_perp)) ** 2))
        g_pos /= max(float(g_pos.sum()), 1e-6)
        g_neg /= max(float(g_neg.sum()), 1e-6)
        ker = (g_pos - 0.45 * g_neg).astype(np.float32)
        # Calibrate so an ideal 1-px line along `ang` preserves unit amplitude
        line_mask = (np.abs(u_perp) <= 0.5).astype(np.float32)
        norm_line = max(float((ker * line_mask).sum()), 1e-4)
        ker /= norm_line
        resp = oaconvolve(p, ker, mode="same").astype(np.float32)
        np.maximum(best, resp, out=best)
    best = np.where(valid, np.clip(best, 0.0, 1.0), 0.0)
    return best


def _save_plane(pdir: Path, name: str, arr: np.ndarray, footprint: np.ndarray) -> dict:
    pdir.mkdir(parents=True, exist_ok=True)
    out = np.where(footprint & np.isfinite(arr), arr, 0.0).astype(np.float32)
    path = pdir / f"{name}.npy"
    np.save(path, out)
    return dict(
        name=name,
        file=str(path.name),
        sha256=_sha256_file(path),
        min=float(out[footprint].min()),
        max=float(out[footprint].max()),
        std=float(out[footprint].std()),
    )


def build_physical_planes(data_dir: Path | None = None, force: bool = False) -> dict:
    """Build or verify all 48 label-free physical planes + spin-2 director & consensus."""
    d = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    pdir = plane_dir_for(d)
    adir = aux_dir_for(d)
    manifest_path = pdir / "manifest.json"
    aux_needed = ("phys_cos2.npy", "phys_sin2.npy", "phys_coh.npy", "c_multi.npy")
    if (
        not force
        and manifest_path.is_file()
        and all((adir / nm).is_file() for nm in aux_needed)
    ):
        man = json.loads(manifest_path.read_text())
        if [p["name"] for p in man.get("planes", [])] == list(PHYS_FEATURES) and all(
            (pdir / p["file"]).is_file() for p in man["planes"]
        ):
            return man

    t0 = time.time()
    pdir.mkdir(parents=True, exist_ok=True)
    adir.mkdir(parents=True, exist_ok=True)

    # Read ONLY sample_submission.tif for footprint geometry (never existing_faults.tif!)
    with rasterio.open(d / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
        shape = fp.shape

    planes_meta: list[dict] = []
    tf_path = d / "training_features.tif"

    # ------------------------------------------------------------------ #
    # Block 1: Seamless 10m 3DEP, 1m LiDAR & Lahontan Shoreline Deconf   #
    # ------------------------------------------------------------------ #
    with rasterio.open(d / "external" / "dem10_chi_100m_i16.tif") as cds:
        zmean_raw = cds.read(5).astype(np.float32)
    z_ok = fp & (zmean_raw != -32768)
    zmean_m = np.where(z_ok, zmean_raw, float(np.median(zmean_raw[z_ok]))).astype(np.float32)
    del zmean_raw

    with rasterio.open(d / "external" / "topo_10m_derived_100m_u8.tif") as tds:
        t10_slope_p90 = tds.read(1).astype(np.float32)
        t10_relief = tds.read(5).astype(np.float32)
        t10_curv_prof = tds.read(6).astype(np.float32)
        t10_aspect_coh = tds.read(7).astype(np.float32)
        t10_hs_lin = tds.read(8).astype(np.float32)
    t10_ok = fp & (t10_slope_p90 > 0)

    topo10_curv_prof_z = _robust_z(t10_curv_prof, t10_ok)
    topo10_hs_lineament_z = _robust_z(t10_hs_lin, t10_ok)
    topo10_aspect_coh_z = _robust_z(t10_aspect_coh, t10_ok)
    topo10_slope_p90_z = _robust_z(t10_slope_p90, t10_ok)

    t10_pied_raw = (
        (t10_curv_prof / 255.0)
        * (0.35 + 0.65 * (t10_aspect_coh / 255.0))
        * (0.40 + 0.60 * (t10_hs_lin / 255.0))
        / (0.20 + (t10_relief / 255.0) + 0.65 * (t10_slope_p90 / 255.0))
    ).astype(np.float32)
    t10_pied_raw[~t10_ok] = 0.0
    topo10_piedmont_scarp = _robust_z(t10_pied_raw, t10_ok)
    t10_pied_01 = _pos_unit(t10_pied_raw, t10_ok, 99.0)
    topo10_scarp_chain = _robust_z(_axial_chain_excess(t10_pied_01, length=9, n_angles=8), t10_ok)

    # Regional elevation contour spin-2 director for Lake Lahontan shoreline rejection
    c2_cont, s2_cont, coh_cont = _spin2_edge_director(zmean_m, grad_sigma=3.5, tensor_sigma=5.0)
    # 10m scarp ridge spin-2 director
    c2_t10, s2_t10, coh_t10 = _spin2_edge_director(t10_pied_01, grad_sigma=1.0, tensor_sigma=2.5)

    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as lds:
        ex_max = lds.read(1).astype(np.float32)
        ex_mean = lds.read(2).astype(np.float32)
        step_max = lds.read(3).astype(np.float32)
        lapneg = lds.read(4).astype(np.float32)
        lappos = lds.read(5).astype(np.float32)
        downf = lds.read(6).astype(np.float32)
        upf = lds.read(7).astype(np.float32)
        l_relief = lds.read(9).astype(np.float32)
        l_coh100 = lds.read(10).astype(np.float32)
        l_strike_u8 = lds.read(11).astype(np.float32)
        l_val = (lds.read(12) > 0) & fp

    lidar_valid = l_val.astype(np.float32)
    lidar_step_z = _robust_z(step_max, l_val)
    lidar_face_asym = _robust_z(0.6 * np.maximum(downf, upf) + 0.4 * np.maximum(lapneg, lappos), l_val)
    l_pied_raw = (
        (step_max / 255.0)
        * (0.35 + 0.65 * (l_coh100 / 255.0))
        * (0.50 + 0.50 * (0.6 * ex_max + 0.4 * ex_mean) / 255.0)
        / (0.18 + (l_relief / 255.0) + 0.70 * (t10_slope_p90 / 255.0))
    ).astype(np.float32)
    l_pied_raw[~l_val] = 0.0
    l_pied_01 = _pos_unit(l_pied_raw, l_val, 99.0)

    # Convert LiDAR strike_u8 (empirically verified tangent (dc=cos(th), dr=sin(th)), th=pi*u8/255)
    # to spin-2 geological strike (cos(2s) = -cos(2*th), sin(2s) = -sin(2*th))
    th_lid = np.pi * l_strike_u8 / 255.0
    c2_lid = (-np.cos(2.0 * th_lid)).astype(np.float32)
    s2_lid = (-np.sin(2.0 * th_lid)).astype(np.float32)
    coh_lid = np.where(l_val, np.clip(l_coh100 / 255.0, 0.0, 1.0), 0.0).astype(np.float32)

    # Fused scarp spin-2 director (1m LiDAR where valid & coherent, else 10m 3DEP)
    w_lid_dir = np.where(l_val, np.clip(coh_lid * (0.4 + 0.6 * l_pied_01), 0.0, 1.0), 0.0)
    w_t10_dir = np.clip(coh_t10 * (0.3 + 0.7 * t10_pied_01), 0.0, 1.0)
    sc_dx = w_lid_dir * c2_lid + 0.75 * w_t10_dir * c2_t10
    sc_dy = w_lid_dir * s2_lid + 0.75 * w_t10_dir * s2_t10
    sc_mag = np.hypot(sc_dx, sc_dy)
    c2_scarp = np.divide(sc_dx, sc_mag, out=np.zeros_like(sc_dx), where=sc_mag > 1e-6)
    s2_scarp = np.divide(sc_dy, sc_mag, out=np.zeros_like(sc_dy), where=sc_mag > 1e-6)
    coh_scarp = np.clip(sc_mag / np.maximum(w_lid_dir + 0.75 * w_t10_dir, 1e-6), 0.0, 1.0).astype(np.float32)

    # Pleistocene Lake Lahontan shoreline zone (1180-1355 m ASL; highstand ~1338 m)
    lahontan_zone_weight = np.where(
        fp,
        np.exp(-0.5 * ((zmean_m - 1272.0) / 62.0) ** 2),
        0.0,
    ).astype(np.float32)
    # Alignment with regional elevation contour: +1 when contour-parallel (shoreline), 0 when orthogonal
    contour_parallel = np.clip(
        0.5 * (1.0 + c2_scarp * c2_cont + s2_scarp * s2_cont), 0.0, 1.0
    ).astype(np.float32)
    fused_scarp_01 = np.where(l_val, np.maximum(l_pied_01, 0.80 * t10_pied_01), t10_pied_01).astype(np.float32)
    shoreline_prob = (lahontan_zone_weight * coh_cont * coh_scarp * (contour_parallel ** 2)).astype(np.float32)
    lahontan_shoreline_mimic = _robust_z(shoreline_prob * fused_scarp_01, fp)
    tect_scarp_01 = (fused_scarp_01 * (1.0 - 0.78 * shoreline_prob)).astype(np.float32)
    tectonic_scarp_deconf = _robust_z(tect_scarp_01, fp)
    tectonic_scarp_chain = _robust_z(_axial_chain_excess(tect_scarp_01, length=11, n_angles=8), fp)

    del (
        ex_max, ex_mean, step_max, lapneg, lappos, downf, upf, l_relief, l_coh100, l_strike_u8,
        l_pied_raw, l_pied_01, th_lid, c2_lid, s2_lid, coh_lid, c2_cont, s2_cont, coh_cont,
        c2_t10, s2_t10, coh_t10, w_lid_dir, w_t10_dir, sc_dx, sc_dy, sc_mag,
        contour_parallel, fused_scarp_01, shoreline_prob, t10_pied_raw, t10_pied_01, t10_aspect_coh, t10_hs_lin,
    )
    gc.collect()

    with rasterio.open(tf_path) as tf:
        det_elev, de_ok = _clean_band(tf.read(12), fp)
        det_slope, ds_ok = _clean_band(tf.read(19), fp)
    lap_elev = ndi.laplace(det_elev).astype(np.float32)
    dem_piedmont_hinge = _robust_z(
        0.65 * _pos_unit(_hessian_sym_ridge(det_slope, 1.5, "ridge"), ds_ok)
        + 0.35 * _pos_unit(-lap_elev, de_ok),
        de_ok & ds_ok,
    )
    valley_raw = _pos_unit(_hessian_sym_ridge(det_elev, 1.5, "valley"), de_ok)
    dem_valley_chain = _robust_z(_axial_chain_excess(valley_raw, length=9, n_angles=8), de_ok)
    del det_elev, det_slope, lap_elev, valley_raw

    for nm, ar in (
        ("topo10_curv_prof_z", topo10_curv_prof_z),
        ("topo10_hs_lineament_z", topo10_hs_lineament_z),
        ("topo10_aspect_coh_z", topo10_aspect_coh_z),
        ("topo10_piedmont_scarp", topo10_piedmont_scarp),
        ("topo10_scarp_chain", topo10_scarp_chain),
        ("lahontan_zone_weight", lahontan_zone_weight),
        ("lahontan_shoreline_mimic", lahontan_shoreline_mimic),
        ("tectonic_scarp_deconf", tectonic_scarp_deconf),
        ("tectonic_scarp_chain", tectonic_scarp_chain),
        ("lidar_valid", lidar_valid),
        ("lidar_step_z", lidar_step_z),
        ("lidar_face_asym", lidar_face_asym),
        ("dem_piedmont_hinge", dem_piedmont_hinge),
        ("dem_valley_chain", dem_valley_chain),
    ):
        planes_meta.append(_save_plane(pdir, nm, ar, fp))

    fam_geomorph = np.clip(
        0.55 * tect_scarp_01 + 0.45 * _pos_unit(tectonic_scarp_chain, fp, 99.0), 0.0, 1.0
    ).astype(np.float32)
    del (
        topo10_curv_prof_z, topo10_hs_lineament_z, topo10_aspect_coh_z,
        topo10_piedmont_scarp, topo10_scarp_chain, lahontan_zone_weight,
        lahontan_shoreline_mimic, tectonic_scarp_deconf, tectonic_scarp_chain,
        lidar_valid, lidar_step_z, lidar_face_asym, dem_piedmont_hinge, dem_valley_chain, l_val,
    )
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 2: 10m Fluvial ksn Knickzones, Chi Steps & Rad-Topo Discord  #
    # ------------------------------------------------------------------ #
    with rasterio.open(d / "external" / "dem10_chi_100m_i16.tif") as cds:
        chi_step_max = cds.read(1).astype(np.float32)
        chi_step_min = cds.read(2).astype(np.float32)
        ksn_raw = cds.read(3).astype(np.float32)
        log_area = cds.read(4).astype(np.float32)
    ch_ok = fp & (ksn_raw != -32768) & (log_area != -32768)

    area_wt = np.where(ch_ok, np.clip((log_area * 1e-3 - 5.4) / 1.8, 0.0, 1.0), 0.0).astype(np.float32)
    ksn_pos = np.where(ch_ok, np.maximum(ksn_raw, 0.0) * area_wt, 0.0).astype(np.float32)
    # Normalize channel steepness by smoothed background relief to highlight transient knickzones
    bg_rel = ndi.gaussian_filter((t10_relief / 255.0).astype(np.float32), 6.0, mode="nearest")
    ksn_anom = ksn_pos / (0.15 + bg_rel)
    ksn_s2 = ndi.gaussian_filter(ksn_anom, 2.0, mode="constant")
    fluv_ksn_knick_s2 = _robust_z(ksn_s2, fp)
    ksn_chain_raw = _axial_chain_excess(_pos_unit(ksn_s2, fp, 99.2), length=11, n_angles=8)
    fluv_ksn_chain_s5 = _robust_z(ndi.gaussian_filter(ksn_chain_raw, 1.5, mode="nearest"), fp)

    chi_disp = np.where(
        ch_ok,
        (np.maximum(chi_step_max, 0.0) + 0.5 * np.abs(chi_step_max - chi_step_min)) * 1e-3 * area_wt,
        0.0,
    ).astype(np.float32)
    fluv_chi_step_s3 = _robust_z(ndi.gaussian_filter(chi_disp, 3.0, mode="constant"), fp)
    ksn_chain_01 = _pos_unit(fluv_ksn_chain_s5, fp, 99.0)
    fluv_scarp_knick_couple = _robust_z(tect_scarp_01 * (0.25 + 0.75 * ksn_chain_01), fp)
    zmean_elev_z = _robust_z(zmean_m, z_ok)

    fam_geomorph = np.clip(np.maximum(fam_geomorph, 0.65 * tect_scarp_01 + 0.35 * ksn_chain_01), 0.0, 1.0)
    del chi_step_max, chi_step_min, ksn_raw, log_area, area_wt, ksn_pos, bg_rel, ksn_anom, ksn_s2, ksn_chain_raw, chi_disp, ksn_chain_01, tect_scarp_01, t10_relief
    gc.collect()

    # Radiometric-Topographic Discordance on 10m true elevation, slope, curvature
    with rasterio.open(d / "external" / "geodawn_rad_u8.tif") as rds:
        K_raw = rds.read(1).astype(np.float32)
    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as eds:
        ThK_raw = eds.read(1).astype(np.float32)
        UTh_raw = eds.read(3).astype(np.float32)
    rad_ok = fp & (K_raw > 0) & (ThK_raw > 0) & (UTh_raw > 0) & z_ok & t10_ok
    rng = np.random.default_rng(2026863)
    ry, rx = np.nonzero(rad_ok)
    sub = rng.choice(ry.size, size=min(200_000, ry.size), replace=False)
    X_topo = np.column_stack([zmean_m[ry[sub], rx[sub]], t10_slope_p90[ry[sub], rx[sub]], t10_curv_prof[ry[sub], rx[sub]]])

    m_k = HuberRegressor(alpha=0.1, max_iter=200).fit(X_topo, K_raw[ry[sub], rx[sub]])
    k_res = np.where(
        rad_ok,
        K_raw - (m_k.coef_[0] * zmean_m + m_k.coef_[1] * t10_slope_p90 + m_k.coef_[2] * t10_curv_prof + m_k.intercept_),
        0.0,
    ).astype(np.float32)
    k_edge = 0.5 * _pos_unit(_grad_mag(k_res, 1.2), rad_ok) + 0.5 * _pos_unit(_hessian_sym_ridge(k_res, 1.5, "both"), rad_ok)
    rad_topo_discord_K = _robust_z(_axial_chain_excess(k_edge, length=7, n_angles=8), rad_ok)

    rmix = (0.6 * UTh_raw - 0.4 * ThK_raw).astype(np.float32)
    m_u = HuberRegressor(alpha=0.1, max_iter=200).fit(X_topo, rmix[ry[sub], rx[sub]])
    u_res = np.where(
        rad_ok,
        rmix - (m_u.coef_[0] * zmean_m + m_u.coef_[1] * t10_slope_p90 + m_u.coef_[2] * t10_curv_prof + m_u.intercept_),
        0.0,
    ).astype(np.float32)
    u_edge = 0.5 * _pos_unit(_grad_mag(u_res, 1.2), rad_ok) + 0.5 * _pos_unit(_hessian_sym_ridge(u_res, 1.5, "both"), rad_ok)
    rad_topo_discord_UTh = _robust_z(_axial_chain_excess(u_edge, length=7, n_angles=8), rad_ok)
    del K_raw, ThK_raw, UTh_raw, zmean_m, t10_slope_p90, t10_curv_prof, k_res, u_res, k_edge, u_edge, rmix, X_topo

    for nm, ar in (
        ("fluv_ksn_knick_s2", fluv_ksn_knick_s2),
        ("fluv_ksn_chain_s5", fluv_ksn_chain_s5),
        ("fluv_chi_step_s3", fluv_chi_step_s3),
        ("fluv_scarp_knick_couple", fluv_scarp_knick_couple),
        ("zmean_elev_z", zmean_elev_z),
        ("topo10_slope_p90_z", topo10_slope_p90_z),
        ("rad_topo_discord_K", rad_topo_discord_K),
        ("rad_topo_discord_UTh", rad_topo_discord_UTh),
    ):
        planes_meta.append(_save_plane(pdir, nm, ar, fp))
    del (
        fluv_ksn_knick_s2, fluv_ksn_chain_s5, fluv_chi_step_s3, fluv_scarp_knick_couple,
        zmean_elev_z, topo10_slope_p90_z, rad_topo_discord_K, rad_topo_discord_UTh,
    )
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 3: Blakely Tilt Zero-Crossings, Contact-Offsets & Basement   #
    # ------------------------------------------------------------------ #
    with rasterio.open(tf_path) as tf:
        rtp, rtp_ok = _clean_band(tf.read(2), fp)
        tmi_hg, hg_ok = _clean_band(tf.read(3), fp)
        grav_slope, gs_ok = _clean_band(tf.read(5), fp)
        tc, tc_ok = _clean_band(tf.read(6), fp)
        tmi_vg, vg_ok = _clean_band(tf.read(9), fp)
        grav_vg, gvg_ok = _clean_band(tf.read(11), fp)
        tmi, tmi_ok = _clean_band(tf.read(14), fp)
        bdepth, bd_ok = _clean_band(tf.read(15), fp)
        grav_hg, ghg_ok = _clean_band(tf.read(18), fp)

    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as eds:
        tmi_up150 = eds.read(4).astype(np.float32)
    up_ok = tmi_ok & (tmi_up150 > 0)

    # Blakely-Miller tilt zero-crossing contact ridges (sub-vertical fault contacts -> tilt = 0)
    tilt_m = np.arctan2(tmi_vg, np.maximum(np.abs(tmi_hg), 1e-6)).astype(np.float32)
    m_zc_raw = (_grad_mag(tilt_m, 1.2) * np.exp(-((tilt_m / 0.35) ** 2))).astype(np.float32)
    mag_blakely_zerocross = _robust_z(m_zc_raw, vg_ok & hg_ok)

    tilt_g = np.arctan2(grav_vg, np.maximum(np.abs(grav_hg), 1e-6)).astype(np.float32)
    g_zc_raw = (_grad_mag(tilt_g, 1.5) * np.exp(-((tilt_g / 0.35) ** 2))).astype(np.float32)
    grav_blakely_zerocross = _robust_z(g_zc_raw, gvg_ok & ghg_ok)

    m_zc_01 = _pos_unit(m_zc_raw, vg_ok & hg_ok, 99.0)
    g_zc_01 = _pos_unit(g_zc_raw, gvg_ok & ghg_ok, 99.0)
    blakely_joint_zerocross = _robust_z(
        _axial_chain_excess(np.sqrt(m_zc_01 * g_zc_01).astype(np.float32), length=9, n_angles=8),
        vg_ok & hg_ok & gvg_ok & ghg_ok,
    )
    del tilt_m, tilt_g, m_zc_raw, g_zc_raw, tmi_vg, grav_vg

    mag_rtp_grad_s1 = _robust_z(_grad_mag(rtp, 1.2), rtp_ok)
    mag_rtp_ridge_s1 = _robust_z(_hessian_sym_ridge(rtp, 1.2, "both"), rtp_ok)
    mag_rtp_ridge_s3 = _robust_z(_hessian_sym_ridge(rtp, 3.0, "both"), rtp_ok)
    mag_tc_z = _robust_z(tc, tc_ok)
    del tmi_hg, tc

    atten_diff = (_robust_z(tmi, up_ok) - _robust_z(tmi_up150, up_ok)).astype(np.float32)
    mag_up150_atten_grad = _robust_z(_grad_mag(atten_diff, 1.2), up_ok)
    del tmi, tmi_up150, atten_diff

    c2_m1, s2_m1, coh_m1 = _spin2_edge_director(rtp, 1.0, 2.0)
    c2_m5, s2_m5, coh_m5 = _spin2_edge_director(rtp, 1.5, 5.5)
    turn_disrupt_raw = (coh_m1 * coh_m5 * np.hypot(c2_m1 - c2_m5, s2_m1 - s2_m5)).astype(np.float32)
    mag_turn_disruption = _robust_z(turn_disrupt_raw, rtp_ok)
    del rtp, c2_m5, s2_m5, coh_m5

    grav_hg_z = _robust_z(0.6 * _robust_z(grav_hg, ghg_ok) + 0.4 * _robust_z(grav_slope, gs_ok), ghg_ok & gs_ok)
    c2_g2, s2_g2, coh_g2 = _spin2_edge_director(grav_hg, 1.0, 2.8)
    grav_pos = _pos_unit(grav_hg, ghg_ok, 99.0)
    contact_offset_grav_mag = _robust_z(turn_disrupt_raw * grav_pos, rtp_ok & ghg_ok)
    dot_mg = np.clip(0.5 * (1.0 + c2_m1 * c2_g2 + s2_m1 * s2_g2), 0.0, 1.0)
    grav_mag_concord = _robust_z((coh_m1 * coh_g2 * dot_mg).astype(np.float32), rtp_ok & ghg_ok)

    base_depth_z = _robust_z(bdepth, bd_ok)
    hinge_raw = (_pos_unit(_hessian_sym_ridge(bdepth, 2.2, "both"), bd_ok, 99.0) * (0.30 + 0.70 * grav_pos)).astype(np.float32)
    base_hinge_flexure = _robust_z(hinge_raw, bd_ok & ghg_ok)

    # Composite label-free physical spin-2 strike director (scarp + RTP + gravity)
    p_dx = 1.0 * coh_scarp * c2_scarp + 0.55 * coh_m1 * c2_m1 + 0.55 * coh_g2 * c2_g2
    p_dy = 1.0 * coh_scarp * s2_scarp + 0.55 * coh_m1 * s2_m1 + 0.55 * coh_g2 * s2_g2
    p_mag = np.hypot(p_dx, p_dy)
    phys_cos2 = np.where(fp & (p_mag > 1e-6), p_dx / np.maximum(p_mag, 1e-6), 0.0).astype(np.float32)
    phys_sin2 = np.where(fp & (p_mag > 1e-6), p_dy / np.maximum(p_mag, 1e-6), 0.0).astype(np.float32)
    phys_coh = np.where(
        fp,
        np.clip(p_mag / np.maximum(coh_scarp + 0.55 * coh_m1 + 0.55 * coh_g2, 1e-6), 0.0, 1.0),
        0.0,
    ).astype(np.float32)
    np.save(adir / "phys_cos2.npy", phys_cos2)
    np.save(adir / "phys_sin2.npy", phys_sin2)
    np.save(adir / "phys_coh.npy", phys_coh)

    fam_subsurf = np.clip(
        np.maximum.reduce([
            0.5 * m_zc_01 + 0.5 * g_zc_01,
            hinge_raw,
            _pos_unit(grav_mag_concord, fp, 99.0),
        ]),
        0.0,
        1.0,
    ).astype(np.float32)

    del (
        c2_scarp, s2_scarp, coh_scarp, c2_m1, s2_m1, coh_m1, c2_g2, s2_g2, coh_g2,
        p_dx, p_dy, p_mag, phys_cos2, phys_sin2, phys_coh,
        grav_slope, grav_hg, bdepth, turn_disrupt_raw, grav_pos, dot_mg, m_zc_01, g_zc_01, hinge_raw,
    )

    for nm, ar in (
        ("mag_blakely_zerocross", mag_blakely_zerocross),
        ("grav_blakely_zerocross", grav_blakely_zerocross),
        ("blakely_joint_zerocross", blakely_joint_zerocross),
        ("mag_rtp_grad_s1", mag_rtp_grad_s1),
        ("mag_rtp_ridge_s1", mag_rtp_ridge_s1),
        ("mag_rtp_ridge_s3", mag_rtp_ridge_s3),
        ("mag_tc_z", mag_tc_z),
        ("mag_up150_atten_grad", mag_up150_atten_grad),
        ("mag_turn_disruption", mag_turn_disruption),
        ("grav_hg_z", grav_hg_z),
        ("contact_offset_grav_mag", contact_offset_grav_mag),
        ("grav_mag_concord", grav_mag_concord),
        ("base_depth_z", base_depth_z),
        ("base_hinge_flexure", base_hinge_flexure),
    ):
        planes_meta.append(_save_plane(pdir, nm, ar, fp))
    del (
        mag_blakely_zerocross, grav_blakely_zerocross, blakely_joint_zerocross,
        mag_rtp_grad_s1, mag_rtp_ridge_s1, mag_rtp_ridge_s3, mag_tc_z,
        mag_up150_atten_grad, mag_turn_disruption, grav_hg_z,
        contact_offset_grav_mag, grav_mag_concord, base_depth_z, base_hinge_flexure,
    )
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 4: GDR-1391 Geothermometer, Conductivity & Seismicity-Strain #
    # ------------------------------------------------------------------ #
    diseq_grid = np.zeros(shape, dtype=np.float32)
    kinlag_grid = np.zeros(shape, dtype=np.float32)
    therm_grid = np.zeros(shape, dtype=np.float32)

    ws_csv = d / "external" / "gdr_wellspring_in_footprint.csv"
    with ws_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        allowed_cols = set(reader.fieldnames or []) - FORBIDDEN_CSV_COLUMNS
        assert "dist_known_fault_px" not in allowed_cols
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]):
                continue
            t_meas = np.nan
            try:
                if row["temp_c"]:
                    t_meas = float(row["temp_c"])
            except ValueError:
                pass
            chem_vals = []
            chalc_v = cat_v = np.nan
            for key_name in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                try:
                    v = float(row[key_name]) if row[key_name] else np.nan
                except ValueError:
                    v = np.nan
                if np.isfinite(v) and 0.0 < v < 400.0:
                    chem_vals.append(v)
                    if key_name == "geothermchalc_c":
                        chalc_v = v
                    elif key_name == "geothermcat_c":
                        cat_v = v
            if chem_vals:
                t_chem = max(chem_vals)
                base_t = t_meas if (np.isfinite(t_meas) and t_meas > 5.0) else 14.0
                diseq = max(0.0, min(t_chem - base_t, 250.0)) / 150.0
                if diseq > diseq_grid[r, c]:
                    diseq_grid[r, c] = diseq
            if np.isfinite(cat_v) and np.isfinite(chalc_v):
                klag = max(0.0, min(abs(cat_v - chalc_v), 180.0)) / 100.0
                if klag > kinlag_grid[r, c]:
                    kinlag_grid[r, c] = klag
            t_cls = (row.get("thermalclass") or "").strip().lower()
            w_th = 0.0
            if np.isfinite(t_meas) and t_meas > 20.0:
                w_th = max(w_th, min((t_meas - 20.0) / 80.0, 1.5))
            if t_cls == "hot":
                w_th = max(w_th, 1.0)
            elif t_cls == "warm":
                w_th = max(w_th, 0.45)
            if w_th > therm_grid[r, c]:
                therm_grid[r, c] = w_th

    vv_csv = d / "external" / "gdr_volcanic_vents_in_footprint.csv"
    vent_grid = np.zeros(shape, dtype=np.float32)
    with vv_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        assert "dist_known_fault_px" not in (set(reader.fieldnames or []) - FORBIDDEN_CSV_COLUMNS)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if 0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]:
                vent_grid[r, c] = 1.0

    gt_diseq_s8 = _pos_unit(ndi.gaussian_filter(diseq_grid, 8.0, mode="constant"), fp, 99.5)
    gt_diseq_s22 = _pos_unit(ndi.gaussian_filter(diseq_grid, 22.0, mode="constant"), fp, 99.5)
    gt_kinlag_s15 = _pos_unit(ndi.gaussian_filter(kinlag_grid, 15.0, mode="constant"), fp, 99.5)
    gt_thermal_s12 = _pos_unit(
        ndi.gaussian_filter(therm_grid, 12.0, mode="constant")
        + 0.75 * ndi.gaussian_filter(vent_grid, 20.0, mode="constant"),
        fp,
        99.5,
    )
    del diseq_grid, kinlag_grid, therm_grid, vent_grid

    with rasterio.open(tf_path) as tf:
        s2inv, s2_ok = _clean_band(tf.read(4), fp)
        shear, sh_ok = _clean_band(tf.read(7), fp)
        dilat, dl_ok = _clean_band(tf.read(8), fp)
        deq, deq_ok = _clean_band(tf.read(10), fp)
        ieq, ieq_ok = _clean_band(tf.read(16), fp)
        cond_raw, cond_ok = _clean_band(tf.read(17), fp)

    cond_surf_z = _robust_z(cond_raw, cond_ok)
    cond_surf_grad = _robust_z(_grad_mag(cond_raw, 1.5), cond_ok)
    cond_pos = _pos_unit(np.maximum(cond_surf_z, cond_surf_grad), fp, 99.0)
    gt_conduit_couple = (np.maximum(gt_diseq_s22, gt_thermal_s12) * (0.25 + 0.75 * cond_pos)).astype(np.float32)

    strain_2ndinv_z = _robust_z(s2inv, s2_ok)
    strain_dilat_z = _robust_z(dilat, dl_ok)
    strain_transtension = _robust_z(
        (dilat / (np.hypot(shear, dilat) + 1e-6)).astype(np.float32), sh_ok & dl_ok
    )

    seis_density_z = _robust_z(0.65 * _robust_z(ieq, ieq_ok) - 0.35 * _robust_z(deq, deq_ok), ieq_ok & deq_ok)
    _, _, coh_ieq = _spin2_edge_director(ieq, 1.5, 4.0)
    seis_strain_fabric = _robust_z(
        coh_ieq * _pos_unit(ieq, ieq_ok, 99.0) * (0.30 + 0.70 * _pos_unit(shear, sh_ok, 99.0)),
        ieq_ok & sh_ok,
    )

    fam_crustal = np.clip(
        np.maximum.reduce([
            gt_conduit_couple,
            0.5 * cond_pos + 0.5 * _pos_unit(seis_strain_fabric, fp, 99.0),
            0.5 * _pos_unit(strain_2ndinv_z, fp, 99.0) + 0.5 * _pos_unit(seis_density_z, fp, 99.0),
        ]),
        0.0,
        1.0,
    ).astype(np.float32)

    # Top-2 of 3 independent physical families (Geomorphic/Fluvial, Subsurface Mag/Grav/Base, Hydrothermal/Seis/Strain)
    stack3 = np.sort(np.stack([fam_geomorph, fam_subsurf, fam_crustal], axis=0), axis=0)
    c_multi = np.where(fp, np.sqrt(np.maximum(stack3[2] * stack3[1], 0.0)), 0.0).astype(np.float32)
    np.save(adir / "c_multi.npy", c_multi)

    del cond_raw, cond_pos, s2inv, shear, dilat, deq, ieq, coh_ieq, fam_geomorph, fam_subsurf, fam_crustal, stack3, c_multi

    for nm, ar in (
        ("gt_diseq_s8", gt_diseq_s8),
        ("gt_diseq_s22", gt_diseq_s22),
        ("gt_kinlag_s15", gt_kinlag_s15),
        ("gt_thermal_s12", gt_thermal_s12),
        ("cond_surf_z", cond_surf_z),
        ("cond_surf_grad", cond_surf_grad),
        ("gt_conduit_couple", gt_conduit_couple),
        ("strain_2ndinv_z", strain_2ndinv_z),
        ("strain_dilat_z", strain_dilat_z),
        ("strain_transtension", strain_transtension),
        ("seis_density_z", seis_density_z),
        ("seis_strain_fabric", seis_strain_fabric),
    ):
        planes_meta.append(_save_plane(pdir, nm, ar, fp))
    del (
        gt_diseq_s8, gt_diseq_s22, gt_kinlag_s15, gt_thermal_s12,
        cond_surf_z, cond_surf_grad, gt_conduit_couple,
        strain_2ndinv_z, strain_dilat_z, strain_transtension,
        seis_density_z, seis_strain_fabric,
    )
    gc.collect()

    assert [p["name"] for p in planes_meta] == list(PHYS_FEATURES)
    man = dict(
        schema="h86c-kslb-physical-planes-v1",
        catalogue_used=False,
        sgmc_used=False,
        forbidden_csv_columns_excluded=sorted(FORBIDDEN_CSV_COLUMNS),
        n_features=len(planes_meta),
        elapsed_s=round(time.time() - t0, 2),
        planes=planes_meta,
    )
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    return man


def compute_kslb_kinematics(
    visible: np.ndarray,
    phys_cos2: np.ndarray,
    phys_sin2: np.ndarray,
    phys_coh: np.ndarray,
    bbox: tuple[slice, slice] | None = None,
    pad: int = 44,
) -> dict[str, np.ndarray]:
    """Compute strictly visible-only crack-tip cones, two-host relays, and
    strike-concordant / bend-hinge damage fields (eliminating isotropic straight-fault halos).
    """
    vis_full = np.asarray(visible, dtype=bool)
    H_full, W_full = vis_full.shape
    if bbox is not None:
        r0, r1 = bbox[0].start, bbox[0].stop
        c0, c1 = bbox[1].start, bbox[1].stop
        pr0, pr1 = max(0, r0 - pad), min(H_full, r1 + pad)
        pc0, pc1 = max(0, c0 - pad), min(W_full, c1 + pad)
        vis = vis_full[pr0:pr1, pc0:pc1]
        pc2 = phys_cos2[pr0:pr1, pc0:pc1]
        ps2 = phys_sin2[pr0:pr1, pc0:pc1]
        pcoh = phys_coh[pr0:pr1, pc0:pc1]
        out_sl = (slice(r0 - pr0, r1 - pr0), slice(c0 - pc0, c1 - pc0))
    else:
        vis = vis_full
        pc2, ps2, pcoh = phys_cos2, phys_sin2, phys_coh
        out_sl = (slice(None), slice(None))

    h, w = vis.shape
    if not vis.any():
        zeros = np.zeros((h, w), dtype=np.float32)[out_sl].copy()
        inf_d = np.full((h, w), np.inf, dtype=np.float32)[out_sl].copy()
        return dict(
            tip_cone=zeros,
            relay_bridge=zeros.copy(),
            hinge_concord_splay=zeros.copy(),
            m_kin=zeros.copy(),
            d1=inf_d,
        )

    comp_lbl, ncomp, st = _fragment_stats(vis)
    tip_cone = np.zeros((h, w), dtype=np.float32)
    R_TIP = 28
    for info in st.values():
        L = float(info["length_px"])
        if L < 3.0:
            continue
        w_len = float(min(1.0, np.log1p(L) / np.log(30.0)))
        axis = info["axis"]
        for pt, uvec in ((info["p0"], -axis), (info["p1"], axis)):
            ty, tx = float(pt[0]), float(pt[1])
            uy, ux = float(uvec[0]), float(uvec[1])
            y0 = max(0, int(np.floor(ty)) - R_TIP)
            y1 = min(h, int(np.ceil(ty)) + R_TIP + 1)
            x0 = max(0, int(np.floor(tx)) - R_TIP)
            x1 = min(w, int(np.ceil(tx)) + R_TIP + 1)
            if y1 <= y0 or x1 <= x0:
                continue
            yy = np.arange(y0, y1, dtype=np.float32)[:, None] - np.float32(ty)
            xx = np.arange(x0, x1, dtype=np.float32)[None, :] - np.float32(tx)
            r_par = yy * np.float32(uy) + xx * np.float32(ux)
            r_perp = -yy * np.float32(ux) + xx * np.float32(uy)
            sig_perp = 1.55 + 0.21 * np.maximum(r_par, 0.0)
            cone = np.where(
                r_par > 0.5,
                w_len * np.exp(-r_par / 11.5) * np.exp(-0.5 * (r_perp / sig_perp) ** 2),
                0.0,
            ).astype(np.float32)
            np.maximum(tip_cone[y0:y1, x0:x1], cone, out=tip_cone[y0:y1, x0:x1])

    bend = host_bend_fields(vis, fine_px=3.0, coarse_px=9.0)
    s_host, c_host = local_strike(vis, smooth_px=4.0)

    if ncomp >= 2:
        th = two_host_frame(vis)
        d1 = th["d1"]
        d2 = th["d2"]
        iy1, ix1 = th["iy1"], th["ix1"]
        L1 = th["comp_len"][th["c1"]]
        L2 = th["comp_len"][th["c2"]]

        yg = np.arange(h, dtype=np.float32)[:, None]
        xg = np.arange(w, dtype=np.float32)[None, :]
        dy1 = yg - iy1.astype(np.float32)
        dx1 = xg - ix1.astype(np.float32)
        dy2 = yg - th["iy2"].astype(np.float32)
        dx2 = xg - th["ix2"].astype(np.float32)
        facing = np.clip(-(dy1 * dy2 + dx1 * dx2) / np.maximum(d1 * d2, 1e-6), 0.0, 1.0)

        len_pair = np.minimum(1.0, np.sqrt(np.log1p(L1) * np.log1p(L2)) / np.float32(np.log(25.0)))
        relay_bridge = (
            np.exp(-(d1 + d2) / 16.0) * (facing ** 1.5) * len_pair * (d1 + d2 <= 40.0)
        ).astype(np.float32)
    else:
        d1_f64, (iy1, ix1) = ndi.distance_transform_edt(~vis, return_indices=True)
        d1 = d1_f64.astype(np.float32)
        l_only = float(st[1]["length_px"]) if 1 in st else float(vis.sum())
        L1 = np.full((h, w), l_only, dtype=np.float32)
        relay_bridge = np.zeros((h, w), dtype=np.float32)

    # Host strike spin-2 anchor at nearest visible fault pixel (iy1, ix1)
    sh_anchor = s_host[iy1, ix1]
    ch_anchor = np.where(np.isfinite(sh_anchor), np.clip(c_host[iy1, ix1], 0.0, 1.0), 0.0).astype(np.float32)
    th2_anchor = np.where(np.isfinite(sh_anchor), np.radians(2.0 * sh_anchor), 0.0)
    hc2 = (np.cos(th2_anchor) * ch_anchor).astype(np.float32)
    hs2 = (np.sin(th2_anchor) * ch_anchor).astype(np.float32)

    # Strike concordance between local physical director and visible host fault:
    # requires actual sub-parallel / synthetic-Riedel alignment (no isotropic straight-fault sausage!)
    align_cos2 = np.clip(0.5 * (1.0 + pc2 * hc2 + ps2 * hs2), 0.0, 1.0)
    concord = (pcoh * ch_anchor * (align_cos2 ** 2)).astype(np.float32)
    turn_at_host = np.clip(bend["turn"][iy1, ix1], 0.0, 1.0)

    w_scale = 5.0 + 1.25 * np.log1p(L1)
    # Zero baseline along straight uncorroborated flanks (replaces H86B's 0.35 isotropic constant!)
    hinge_concord_splay = (
        np.exp(-np.maximum(d1 - 2.5, 0.0) / w_scale)
        * np.clip(0.75 * turn_at_host + 0.65 * concord, 0.0, 1.0)
    ).astype(np.float32)

    off_flank = d1 > 2.0
    tip_cone = np.where(off_flank, tip_cone, 0.0)
    relay_bridge = np.where(off_flank, relay_bridge, 0.0)
    hinge_concord_splay = np.where(off_flank, hinge_concord_splay, 0.0)
    m_kin = np.clip(
        np.maximum.reduce([tip_cone, 0.92 * relay_bridge, 0.55 * hinge_concord_splay]),
        0.0,
        1.0,
    )

    return dict(
        tip_cone=tip_cone[out_sl].copy(),
        relay_bridge=relay_bridge[out_sl].copy(),
        hinge_concord_splay=hinge_concord_splay[out_sl].copy(),
        m_kin=m_kin[out_sl].copy(),
        d1=d1[out_sl].copy(),
    )


if __name__ == "__main__":
    man = build_physical_planes()
    print(f"Built {man['n_features']} H86C-KSLB physical planes in {man['elapsed_s']}s")
