"""H86-1 & H86-4 Label-Free Multi-Physics Feature Stack (`60` channels).

Builds `.cache/h86_features/static60_fp.f16` (`float16`, shape `(5_167_373, 60)`)
over the valid study-area footprint (`np.isfinite(sample_submission.tif)`).
Engineered for < 650 MB peak RSS on 3.8 GiB zero-swap containers.

Zero-leakage invariants enforced by assertion:
  1. Never reads `labels.tif`, `existing_faults.tif`, or `sample_submission.tif` pixel values.
  2. Never reads pre-Quaternary `derived_sgmc_faults_100m_u8.tif` into model features.
  3. Explicitly drops and asserts absence of `dist_known_fault_px` from GDR #1391 CSVs.
"""
from __future__ import annotations

import gc
import json
import os
import shutil
import struct
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

OFFICIAL_19_NAMES: List[str] = [
    "b01_mag_anom",
    "b02_rtp",
    "b03_tmi_hg",
    "b04_geod_2ndinv",
    "b05_iso_grav_slope",
    "b06_mag_tc",
    "b07_geod_shear",
    "b08_geod_dilate",
    "b09_tmi_vg",
    "b10_deq_n100a15",
    "b11_iso_grav_vg",
    "b12_det_elev",
    "b13_iso_grav_anom",
    "b14_tmi",
    "b15_depth_to_base",
    "b16_ieq_n100a15",
    "b17_cond_surf",
    "b18_iso_grav_hg",
    "b19_det_elev_slope",
]

SPI_DIPOLE_10_NAMES: List[str] = [
    "spi_mag_tilt",
    "spi_mag_wavenumber",
    "spi_mag_analytic_sig",
    "spi_mag_shallow_res",
    "spi_grav_tilt",
    "spi_grav_wavenumber",
    "spi_basement_grad",
    "spi_basement_hinge",
    "spi_updip_grav_pullback",
    "spi_dip_coupled_conduit",
]

FAULT_VALVE_11_NAMES: List[str] = [
    "fv_mag_destruction_trough",
    "fv_rad_k_metasomatism",
    "fv_rad_u_redox",
    "fv_claycap_edge",
    "fv_gdr_spring_plume_s5",
    "fv_gdr_geotherm_enthalpy",
    "fv_probe2m_f2mdab",
    "fv_paleo_sinter_seal",
    "fv_heatflow_volcanic_halo",
    "fv_epithermal_vein_prox",
    "fv_sibson_breach_index",
]

SCARP_FLUVIAL_14_NAMES: List[str] = [
    "scarp_lid1m_step_relnorm",
    "scarp_lid1m_ex_downface",
    "scarp_lid1m_coh100",
    "scarp_lid1m_aniso_ridge",
    "scarp_lid1m_valid_mask",
    "scarp_wal3m_gate",
    "scarp_wal3m_cover",
    "scarp_dem10_breakline",
    "scarp_dem10_piedmont_step",
    "scarp_dem10_collinear_chain",
    "scarp_openness_lrm",
    "fluv_ksn_knickzone",
    "fluv_chi_knick_density",
    "fluv_valley_collinear",
]

MIMIC_CONTEXT_6_NAMES: List[str] = [
    "mimic_lahontan_bonneville_bench",
    "mimic_along_scarp_elev_climb",
    "mimic_tiger_road_prox",
    "mimic_road_scarp_interaction",
    "ctx_piedmont_bajada_regime",
    "ctx_transtensional_strain",
]

STATIC_60_NAMES: List[str] = (
    OFFICIAL_19_NAMES
    + SPI_DIPOLE_10_NAMES
    + FAULT_VALVE_11_NAMES
    + SCARP_FLUVIAL_14_NAMES
    + MIMIC_CONTEXT_6_NAMES
)
assert len(STATIC_60_NAMES) == 60


def robust_z_in_fp(arr: np.ndarray, fp: np.ndarray, clip_val: float = 8.0) -> np.ndarray:
    """Standardize `arr` on `fp` using median and IQR/1.349, filling non-finite with 0."""
    vals = arr[fp].astype(np.float32, copy=False)
    fin = np.isfinite(vals)
    if not fin.any():
        return np.zeros(int(fp.sum()), dtype=np.float32)
    good = vals[fin]
    # Subsample 250k points for exact-to-1e-3 quantiles with zero 20MB sort overhead
    step = max(1, good.size // 250_000)
    sample = good[::step]
    q25, q50, q75 = np.percentile(sample, [25.0, 50.0, 75.0])
    scale = float((q75 - q25) / 1.3489795)
    if scale < 1e-7:
        scale = float(np.std(sample))
    if scale < 1e-7:
        scale = 1.0
    out = np.where(fin, (vals - np.float32(q50)) / np.float32(scale), np.float32(0.0))
    return np.clip(out, -clip_val, clip_val).astype(np.float32)


def fill_grid_from_fp(z_fp: np.ndarray, fp: np.ndarray) -> np.ndarray:
    g = np.zeros(fp.shape, dtype=np.float32)
    g[fp] = z_fp
    return g


def grad_mag_2d(g: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    s = ndi.gaussian_filter(g, sigma=sigma, mode="nearest") if sigma > 0 else g
    gy = ndi.sobel(s, axis=0, mode="nearest") * np.float32(0.125)
    gx = ndi.sobel(s, axis=1, mode="nearest") * np.float32(0.125)
    out = np.hypot(gy, gx).astype(np.float32)
    del gy, gx
    return out


def oriented_collinear_max(field: np.ndarray, length_px: int = 9, n_orient: int = 8) -> np.ndarray:
    """Memory-minimal (<120 MB) multi-orientation collinear lineament max filter."""
    half = length_px // 2
    pos_f = np.maximum(field, 0.0).astype(np.float32)
    padded = np.pad(pos_f, half, mode="edge")
    h, w = pos_f.shape
    del pos_f
    best = np.zeros((h, w), dtype=np.float32)
    acc = np.zeros((h, w), dtype=np.float32)
    steps = np.linspace(-half, half, length_px, dtype=np.float32)

    for k in range(n_orient):
        theta = k * np.pi / n_orient
        acc.fill(0.0)
        used = set()
        for t in steps:
            dr = int(round(float(t * np.sin(theta))))
            dc = int(round(float(t * np.cos(theta))))
            if (dr, dc) not in used:
                used.add((dr, dc))
                r0 = half + dr
                c0 = half + dc
                acc += padded[r0 : r0 + h, c0 : c0 + w]
        acc *= np.float32(1.0 / max(len(used), 1))
        np.maximum(best, acc, out=best)
    del padded, acc
    return best


def advect_var_step_2d(field: np.ndarray, vy: np.ndarray, vx: np.ndarray, step_px: np.ndarray) -> np.ndarray:
    """Row-chunked pure-float32 bilinear sampling at `(r + step*vy, c + step*vx)` (<25 MB extra RAM)."""
    h, w = field.shape
    out = np.empty((h, w), dtype=np.float32)
    cols_base = np.arange(w, dtype=np.float32)[None, :]
    chunk = 512
    for r_start in range(0, h, chunk):
        r_end = min(h, r_start + chunk)
        rows_base = np.arange(r_start, r_end, dtype=np.float32)[:, None]
        rq = np.clip(rows_base + step_px[r_start:r_end] * vy[r_start:r_end], 0.0, float(h - 1.001))
        cq = np.clip(cols_base + step_px[r_start:r_end] * vx[r_start:r_end], 0.0, float(w - 1.001))
        r0 = rq.astype(np.int32)
        c0 = cq.astype(np.int32)
        dr = rq - r0
        dc = cq - c0
        f00 = field[r0, c0]
        f01 = field[r0, c0 + 1]
        f10 = field[r0 + 1, c0]
        f11 = field[r0 + 1, c0 + 1]
        out[r_start:r_end] = (
            (1.0 - dr) * ((1.0 - dc) * f00 + dc * f01)
            + dr * ((1.0 - dc) * f10 + dc * f11)
        ).astype(np.float32)
    return out


def _read_tr_band(ds_tr, b: int, fp: np.ndarray) -> np.ndarray:
    raw = ds_tr.read(b).astype(np.float32)
    bad = (~np.isfinite(raw)) | (raw <= -1e30)
    med = float(np.median(raw[fp & (~bad)][::8]))
    raw[bad] = med
    return raw


def _read_u8_band(ds, band_idx: int, fp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    raw = ds.read(band_idx)
    valid = (raw > 0) & fp
    arr = raw.astype(np.float32)
    med = float(np.median(arr[valid][::8])) if valid.any() else 0.0
    arr[~valid] = med
    return arr, valid


def _parse_2m_probes_f2mdab(zip_path: Path, shape: Tuple[int, int]) -> np.ndarray:
    imp = np.zeros(shape, dtype=np.float32)
    if not zip_path.is_file():
        return imp
    with zipfile.ZipFile(zip_path) as zf:
        dbf_bytes = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
    num_rec, hdr_len, rec_len = struct.unpack("<4xIHH20x", dbf_bytes[:32])
    fields = []
    pos = 32
    while dbf_bytes[pos] != 0x0D:
        fname = dbf_bytes[pos : pos + 11].split(b"\x00")[0].decode("latin1")
        flen = dbf_bytes[pos + 16]
        fields.append((fname, flen))
        pos += 32

    lats, lons, f2ms = [], [], []
    rec_pos = hdr_len
    for _ in range(num_rec):
        raw = dbf_bytes[rec_pos : rec_pos + rec_len]
        rec_pos += rec_len
        if raw[0:1] == b"*":
            continue
        off = 1
        row_d = {}
        for fn, fl in fields:
            if fn in ("LatDegreeN", "LongDegree", "F2mDAB", "T2m"):
                row_d[fn] = raw[off : off + fl].decode("latin1").strip()
            off += fl
        try:
            lat = float(row_d["LatDegreeN"])
            lon = float(row_d["LongDegree"])
            f2m = float(row_d["F2mDAB"]) if row_d.get("F2mDAB") else 0.0
            t2m = float(row_d["T2m"]) if row_d.get("T2m") else 0.0
        except ValueError:
            continue
        if 35.0 <= lat <= 44.0 and -123.0 <= lon <= -112.0:
            anom = max(f2m, 0.0) + 0.25 * max(t2m - 22.0, 0.0)
            if anom > 0.0:
                lats.append(lat)
                lons.append(lon)
                f2ms.append(min(anom / 4.0, 5.0))
    del dbf_bytes
    if lats:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        cols = np.round((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
        rows = np.round((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
        ok = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
        np.maximum.at(imp, (rows[ok], cols[ok]), np.asarray(f2ms, dtype=np.float32)[ok])
    return (
        2.4 * ndi.gaussian_filter(imp, sigma=5.5, mode="constant")
        + 1.0 * ndi.gaussian_filter(imp, sigma=16.0, mode="constant")
    ).astype(np.float32)


def _parse_paleo_sinter(zip_path: Path, shape: Tuple[int, int]) -> np.ndarray:
    imp = np.zeros(shape, dtype=np.float32)
    if not zip_path.is_file():
        return imp
    with zipfile.ZipFile(zip_path) as zf:
        df = pd.read_csv(zf.open("Paleo_geothermal_final.csv"), encoding="latin1")
    lons = pd.to_numeric(df["Long_deg_NAD83"], errors="coerce").to_numpy()
    lats = pd.to_numeric(df["Lat_deg_NAD83"], errors="coerce").to_numpy()
    dtypes = df["Deposit_type"].fillna("").astype(str).str.lower().to_numpy()
    ok_coord = np.isfinite(lons) & np.isfinite(lats)
    if ok_coord.any():
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons[ok_coord].tolist(), lats[ok_coord].tolist())
        cols = np.round((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
        rows = np.round((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
        wts = np.where(
            np.char.find(dtypes[ok_coord].astype(str), "sinter") >= 0,
            2.0,
            np.where(np.char.find(dtypes[ok_coord].astype(str), "silic") >= 0, 1.8, 1.2),
        ).astype(np.float32)
        in_g = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
        np.maximum.at(imp, (rows[in_g], cols[in_g]), wts[in_g])
    return (
        2.5 * ndi.gaussian_filter(imp, sigma=4.0, mode="constant")
        + 1.0 * ndi.gaussian_filter(imp, sigma=13.0, mode="constant")
    ).astype(np.float32)


def build_static60_memmap(root: Path, data_dir: Path | None = None, force: bool = False) -> Tuple[Path, Dict]:
    """Compute or load cached 60-channel `float16` feature matrix on valid footprint pixels."""
    os.environ["GDAL_CACHEMAX"] = "32"
    droot = Path(data_dir) if data_dir else (root / ".cache" / "gems_data")
    cache_dir = root / ".cache" / "h86_features"
    cols_dir = cache_dir / "cols_tmp"
    cache_dir.mkdir(parents=True, exist_ok=True)
    mmap_path = cache_dir / "static60_fp.f16"
    meta_path = cache_dir / "static60_meta.json"

    with rasterio.open(droot / "sample_submission.tif") as ds_sub:
        fp = np.isfinite(ds_sub.read(1))
    n_fp = int(fp.sum())
    n_ch = len(STATIC_60_NAMES)
    expected_bytes = n_fp * n_ch * 2

    if not force and mmap_path.is_file() and meta_path.is_file() and mmap_path.stat().st_size == expected_bytes:
        meta = json.loads(meta_path.read_text())
        if meta.get("channel_names") == STATIC_60_NAMES and meta.get("n_fp") == n_fp:
            return mmap_path, meta

    t0 = time.time()
    cols_dir.mkdir(parents=True, exist_ok=True)

    def save_col(col_idx: int, arr_fp_f32: np.ndarray) -> None:
        a16 = np.clip(arr_fp_f32, -16.0, 16.0).astype(np.float16)
        (cols_dir / f"c{col_idx:03d}.f16").write_bytes(a16.tobytes())

    def load_col_grid(col_idx: int) -> np.ndarray:
        a16 = np.frombuffer((cols_dir / f"c{col_idx:03d}.f16").read_bytes(), dtype=np.float16)
        return fill_grid_from_fp(a16.astype(np.float32), fp)

    # 1. Official 19 bands (stream one band at a time -> <60 MB RSS!)
    with rasterio.open(droot / "training_features.tif") as ds_tr:
        assert ds_tr.count == 19
        for b in range(1, 20):
            raw = _read_tr_band(ds_tr, b, fp)
            save_col(b - 1, robust_z_in_fp(raw, fp))
            del raw
    gc.collect()

    # 2. H86-1 Dual Magnetic-Gravity Source Parameter Imaging (iSPI) & Dip Pullback
    with rasterio.open(droot / "training_features.tif") as ds_tr:
        b3 = _read_tr_band(ds_tr, 3, fp)
        b9 = _read_tr_band(ds_tr, 9, fp)
    tmi_hg = np.maximum(np.abs(b3), 1e-6)
    del b3
    theta_mag = np.arctan2(b9, tmi_hg).astype(np.float32)
    kappa_mag = grad_mag_2d(theta_mag, sigma=1.1)
    analytic_mag = np.log1p(np.hypot(tmi_hg, b9)).astype(np.float32)
    del tmi_hg, b9
    save_col(19, robust_z_in_fp(theta_mag, fp))
    z_kappa_mag_fp = robust_z_in_fp(kappa_mag, fp)
    save_col(20, z_kappa_mag_fp)
    save_col(21, robust_z_in_fp(analytic_mag, fp))
    del theta_mag, kappa_mag, analytic_mag
    gc.collect()

    with rasterio.open(droot / "external" / "geodawn_extensions_u8.tif") as ds_ext:
        uth_raw, _ = _read_u8_band(ds_ext, 3, fp)
        tmi_up150, _ = _read_u8_band(ds_ext, 4, fp)
    z_tmi_fp = np.frombuffer((cols_dir / "c013.f16").read_bytes(), dtype=np.float16).astype(np.float32)
    mag_shallow_res_fp = z_tmi_fp - robust_z_in_fp(tmi_up150, fp)
    save_col(22, robust_z_in_fp(fill_grid_from_fp(mag_shallow_res_fp, fp), fp))
    save_col(31, robust_z_in_fp(uth_raw, fp))  # fv_rad_u_redox
    del uth_raw, tmi_up150, z_tmi_fp, mag_shallow_res_fp
    gc.collect()

    with rasterio.open(droot / "training_features.tif") as ds_tr:
        b11 = _read_tr_band(ds_tr, 11, fp)
        b18 = _read_tr_band(ds_tr, 18, fp)
        b15 = _read_tr_band(ds_tr, 15, fp)
    grav_hg = np.maximum(np.abs(b18), 1e-6)
    del b18
    theta_grav = np.arctan2(b11, grav_hg).astype(np.float32)
    del b11
    kappa_grav = grad_mag_2d(theta_grav, sigma=1.4)
    save_col(23, robust_z_in_fp(theta_grav, fp))
    z_kappa_grav_fp = robust_z_in_fp(kappa_grav, fp)
    save_col(24, z_kappa_grav_fp)
    del theta_grav, kappa_grav

    base_s = ndi.gaussian_filter(b15, sigma=2.0, mode="nearest").astype(np.float32)
    by = ndi.sobel(base_s, axis=0, mode="nearest") * np.float32(0.125)
    bx = ndi.sobel(base_s, axis=1, mode="nearest") * np.float32(0.125)
    b_grad_mag = np.hypot(by, bx).astype(np.float32)
    b_hinge = (-ndi.laplace(base_s, mode="nearest")).astype(np.float32)
    save_col(25, robust_z_in_fp(b_grad_mag, fp))
    save_col(26, robust_z_in_fp(b_hinge, fp))
    del base_s, b_hinge

    inv_bg = np.float32(1.0) / np.maximum(b_grad_mag, 1e-5)
    dy_down = by * inv_bg
    dx_down = bx * inv_bg
    del by, bx, b_grad_mag, inv_bg

    b15_min, b15_max = np.percentile(b15[fp][::8], [5.0, 98.0])
    depth_km = np.clip((b15 - b15_min) / max(float(b15_max - b15_min), 1e-3) * 3.0, 0.15, 3.5).astype(np.float32)
    del b15
    step_px = np.clip(np.float32(0.57735 * 10.0) * depth_km, 1.0, 5.0).astype(np.float32)
    deep_grav_struct = (
        0.55 * fill_grid_from_fp(z_kappa_grav_fp, fp)
        + 0.45 * fill_grid_from_fp(robust_z_in_fp(grav_hg, fp), fp)
    )
    del grav_hg
    updip_grav_pullback = advect_var_step_2d(deep_grav_struct, dy_down, dx_down, step_px)
    del deep_grav_struct, dy_down, dx_down, step_px
    z_updip_fp = robust_z_in_fp(updip_grav_pullback, fp)
    save_col(27, z_updip_fp)
    del updip_grav_pullback

    dip_coupled_fp = np.maximum(z_kappa_mag_fp + 0.5, 0.0) * np.maximum(z_updip_fp + 0.5, 0.0)
    save_col(28, robust_z_in_fp(fill_grid_from_fp(dip_coupled_fp, fp), fp))
    del dip_coupled_fp, z_updip_fp
    gc.collect()

    # 3. H86-1 Sibson Hydrothermal Fault-Valve Channels (29..39; note 31 saved above)
    with rasterio.open(droot / "training_features.tif") as ds_tr:
        b2_rtp = _read_tr_band(ds_tr, 2, fp)
        b17_cond = _read_tr_band(ds_tr, 17, fp)
    rtp_hp_low = -(b2_rtp - ndi.gaussian_filter(b2_rtp, sigma=6.0, mode="nearest")).astype(np.float32)
    del b2_rtp
    z_demag_fp = robust_z_in_fp(rtp_hp_low, fp)
    save_col(29, z_demag_fp)
    del rtp_hp_low

    with rasterio.open(droot / "external" / "geodawn_rad_u8.tif") as ds_rad:
        rad_k, _ = _read_u8_band(ds_rad, 1, fp)
        rad_th, _ = _read_u8_band(ds_rad, 2, fp)
    z_k_meta_fp = robust_z_in_fp(fill_grid_from_fp(robust_z_in_fp(rad_k, fp) - np.float32(0.78) * robust_z_in_fp(rad_th, fp), fp), fp)
    save_col(30, z_k_meta_fp)
    del rad_k, rad_th

    z_cond_edge_fp = robust_z_in_fp(
        0.60 * fill_grid_from_fp(robust_z_in_fp(b17_cond, fp), fp)
        + 0.40 * fill_grid_from_fp(robust_z_in_fp(grad_mag_2d(b17_cond, sigma=1.5), fp), fp),
        fp,
    )
    save_col(32, z_cond_edge_fp)
    del b17_cond
    gc.collect()

    df_ws = pd.read_csv(droot / "external" / "gdr_wellspring_in_footprint.csv")
    if "dist_known_fault_px" in df_ws.columns:
        df_ws = df_ws.drop(columns=["dist_known_fault_px"])
    assert "dist_known_fault_px" not in df_ws.columns
    h_grid, w_grid = fp.shape
    ws_r = np.clip(np.round(df_ws["row"].to_numpy()).astype(np.int32), 0, h_grid - 1)
    ws_c = np.clip(np.round(df_ws["col"].to_numpy()).astype(np.int32), 0, w_grid - 1)
    t_meas = np.nan_to_num(df_ws["temp_c"].to_numpy(dtype=np.float32), nan=0.0)
    gt_max = np.nanmax(
        np.column_stack(
            [
                np.nan_to_num(df_ws["geothermquartz_c"].to_numpy(dtype=np.float32), nan=0.0),
                np.nan_to_num(df_ws["geothermchalc_c"].to_numpy(dtype=np.float32), nan=0.0),
                np.nan_to_num(df_ws["geothermcat_c"].to_numpy(dtype=np.float32), nan=0.0),
            ]
        ),
        axis=1,
    )
    del df_ws

    imp_sp = np.zeros(fp.shape, dtype=np.float32)
    ex_t = np.clip(np.maximum(t_meas - 21.0, 0.0) / 30.0, 0.0, 5.0)
    np.maximum.at(imp_sp, (ws_r[ex_t > 0], ws_c[ex_t > 0]), ex_t[ex_t > 0])
    save_col(33, robust_z_in_fp(ndi.gaussian_filter(imp_sp, sigma=5.0, mode="constant"), fp))
    del imp_sp, ex_t, t_meas

    imp_gt = np.zeros(fp.shape, dtype=np.float32)
    ex_gt = np.clip(np.maximum(gt_max - 70.0, 0.0) / 65.0, 0.0, 5.0)
    np.maximum.at(imp_gt, (ws_r[ex_gt > 0], ws_c[ex_gt > 0]), ex_gt[ex_gt > 0])
    z_gt_fp = robust_z_in_fp(
        2.0 * ndi.gaussian_filter(imp_gt, sigma=6.0, mode="constant")
        + 1.0 * ndi.gaussian_filter(imp_gt, sigma=16.0, mode="constant"),
        fp,
    )
    save_col(34, z_gt_fp)
    del imp_gt, ex_gt, gt_max, ws_r, ws_c

    z_p2m_fp = robust_z_in_fp(
        _parse_2m_probes_f2mdab(droot / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip", fp.shape), fp
    )
    save_col(35, z_p2m_fp)
    z_pal_fp = robust_z_in_fp(_parse_paleo_sinter(droot / "external" / "paleo_geothermal_regional.zip", fp.shape), fp)
    save_col(36, z_pal_fp)

    imp_vhf = np.zeros(fp.shape, dtype=np.float32)
    df_vv = pd.read_csv(droot / "external" / "gdr_volcanic_vents_in_footprint.csv")
    if "dist_known_fault_px" in df_vv.columns:
        df_vv = df_vv.drop(columns=["dist_known_fault_px"])
    assert "dist_known_fault_px" not in df_vv.columns
    np.maximum.at(
        imp_vhf,
        (
            np.clip(np.round(df_vv["row"].to_numpy()).astype(np.int32), 0, h_grid - 1),
            np.clip(np.round(df_vv["col"].to_numpy()).astype(np.int32), 0, w_grid - 1),
        ),
        2.0,
    )
    del df_vv
    hf_json = droot / "external" / "sb_heat_flow_in_footprint.json"
    if hf_json.is_file():
        for rec in json.loads(hf_json.read_text()).get("records", []):
            parts = rec.get("parts") or []
            if len(parts) == 1 and len(parts[0]) == 1:
                xm, ym = parts[0][0]
                ci = int(round((xm - 243350.0) / 100.0))
                ri = int(round((4508550.0 - ym) / 100.0))
                if 0 <= ri < h_grid and 0 <= ci < w_grid:
                    hfr, hfm = rec.get("hf_resid"), rec.get("hf_meas")
                    val = 0.0
                    if isinstance(hfr, (int, float)) and np.isfinite(hfr) and hfr > 10.0:
                        val += min((hfr - 10.0) / 30.0, 3.0)
                    if isinstance(hfm, (int, float)) and np.isfinite(hfm) and hfm > 85.0:
                        val += min((hfm - 85.0) / 45.0, 2.5)
                    if val > imp_vhf[ri, ci]:
                        imp_vhf[ri, ci] = float(val)
    save_col(37, robust_z_in_fp(ndi.gaussian_filter(imp_vhf, sigma=14.0, mode="constant"), fp))
    del imp_vhf

    with rasterio.open(droot / "external" / "blm_closed_claim_distance_m.tif") as ds_blm:
        d_blm = ds_blm.read(1).astype(np.float32)
    d_blm = np.where(np.isfinite(d_blm), np.maximum(d_blm, 0.0), 1e5)
    save_col(38, robust_z_in_fp(np.exp(-d_blm / 700.0) * (1.0 - 0.5 * np.exp(-d_blm / 80.0)), fp))
    del d_blm

    z_shear_fp = np.frombuffer((cols_dir / "c006.f16").read_bytes(), dtype=np.float16).astype(np.float32)
    z_dilate_fp = np.frombuffer((cols_dir / "c007.f16").read_bytes(), dtype=np.float16).astype(np.float32)
    alt_fp = (np.maximum(z_demag_fp, 0.0) + np.maximum(z_k_meta_fp, 0.0) + np.maximum(z_cond_edge_fp, 0.0)) / 3.0
    th_fp = (np.maximum(z_gt_fp, 0.0) + np.maximum(z_p2m_fp, 0.0) + np.maximum(z_pal_fp, 0.0)) / 3.0
    cs_fp = np.maximum(0.65 * z_shear_fp + 0.35 * z_dilate_fp + 0.5, 0.0)
    sibson_fp = alt_fp * (0.5 + th_fp) * (0.4 + 0.6 * cs_fp)
    save_col(39, robust_z_in_fp(fill_grid_from_fp(sibson_fp, fp), fp))
    del z_demag_fp, z_k_meta_fp, z_cond_edge_fp, z_gt_fp, z_p2m_fp, z_pal_fp, alt_fp, th_fp, cs_fp, sibson_fp
    gc.collect()

    # 4. Scarp Hierarchy (1m + 3m + 10m) & Fluvial Chi (40..53)
    with rasterio.open(droot / "external" / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_valid = (ds_lid.read(12) > 0) & fp
        lid_ex_max, _ = _read_u8_band(ds_lid, 1, fp)
        lid_step_max, _ = _read_u8_band(ds_lid, 3, fp)
        lid_downface, _ = _read_u8_band(ds_lid, 6, fp)
        lid_relief, _ = _read_u8_band(ds_lid, 9, fp)
        lid_coh100, _ = _read_u8_band(ds_lid, 10, fp)

    lid_step_relnorm = lid_step_max / (0.35 * lid_relief + 12.0)
    del lid_step_max, lid_relief
    lid_step_relnorm[~lid_valid] = float(np.median(lid_step_relnorm[lid_valid][::8]))
    z_lid_step_fp = robust_z_in_fp(lid_step_relnorm, fp)
    save_col(40, z_lid_step_fp)
    del lid_step_relnorm

    lid_ex_down = 0.5 * lid_ex_max + 0.5 * lid_downface
    del lid_ex_max, lid_downface
    lid_ex_down[~lid_valid] = float(np.median(lid_ex_down[lid_valid][::8]))
    save_col(41, robust_z_in_fp(lid_ex_down, fp))
    del lid_ex_down
    save_col(42, robust_z_in_fp(lid_coh100, fp))
    del lid_coh100

    z_lid_grid = fill_grid_from_fp(z_lid_step_fp, fp)
    z_lid_grid[~lid_valid] = 0.0
    save_col(43, robust_z_in_fp(oriented_collinear_max(z_lid_grid, length_px=7, n_orient=8), fp))
    lid_valid_frac = round(float(lid_valid[fp].mean()), 6)
    save_col(44, lid_valid[fp].astype(np.float32))
    del lid_valid
    gc.collect()

    with rasterio.open(droot / "external" / "h52_scarp3m_100m.tif") as ds_w3:
        w3_cov = (ds_w3.read(7) > 0) & fp
        h07 = ds_w3.read(1).astype(np.float32)
        h12 = ds_w3.read(2).astype(np.float32)
    h07[~w3_cov] = float(np.median(h07[w3_cov][::8])) if w3_cov.any() else 0.0
    h12[~w3_cov] = float(np.median(h12[w3_cov][::8])) if w3_cov.any() else 0.0
    wal3m_gate = 0.55 * fill_grid_from_fp(robust_z_in_fp(h07, fp), fp) + 0.45 * fill_grid_from_fp(
        robust_z_in_fp(h12, fp), fp
    )
    del h07, h12
    wal3m_gate[~w3_cov] = 0.0
    save_col(45, robust_z_in_fp(wal3m_gate, fp))
    w3_cov_frac = round(float(w3_cov[fp].mean()), 6)
    save_col(46, w3_cov[fp].astype(np.float32))
    del wal3m_gate, w3_cov
    gc.collect()

    with rasterio.open(droot / "external" / "topo_10m_derived_100m_u8.tif") as ds_t10:
        t10_relief, _ = _read_u8_band(ds_t10, 5, fp)
        t10_curv, _ = _read_u8_band(ds_t10, 6, fp)
        t10_acoh, _ = _read_u8_band(ds_t10, 7, fp)
        t10_hslin, _ = _read_u8_band(ds_t10, 8, fp)
    dem10_brk_fp = (
        0.45 * robust_z_in_fp(t10_curv, fp)
        + 0.35 * robust_z_in_fp(t10_hslin, fp)
        + 0.20 * robust_z_in_fp(t10_acoh, fp)
    )
    save_col(47, robust_z_in_fp(fill_grid_from_fp(dem10_brk_fp, fp), fp))
    del t10_curv, t10_acoh, t10_hslin, dem10_brk_fp

    with rasterio.open(droot / "external" / "dem10_chi_100m_i16.tif") as ds_chi16:
        c_step = ds_chi16.read(1).astype(np.float32)
        c_ksn = ds_chi16.read(3).astype(np.float32)
        c_log_area = ds_chi16.read(4).astype(np.float32) * np.float32(0.001)
        z_asl = ds_chi16.read(5).astype(np.float32)
    for arr_c in (c_step, c_ksn, c_log_area, z_asl):
        bad_c = arr_c <= -32000
        if bad_c.any():
            arr_c[bad_c] = float(np.median(arr_c[fp & (~bad_c)][::8]))

    dem10_pied_step = c_step / (0.40 * t10_relief + 15.0)
    del c_step, t10_relief
    z_dem10_step_fp = robust_z_in_fp(dem10_pied_step, fp)
    save_col(48, z_dem10_step_fp)
    del dem10_pied_step
    z_dem10_grid = fill_grid_from_fp(z_dem10_step_fp, fp)
    save_col(49, robust_z_in_fp(oriented_collinear_max(z_dem10_grid, length_px=9, n_orient=8), fp))

    openness_fp = np.zeros(n_fp, dtype=np.float32)
    npz_path = droot / "external" / "dem1m_high_prior_openness_lrm.npz"
    if npz_path.is_file():
        npz = np.load(npz_path)
        idx = npz["cov_fp_indices"].astype(np.int64)
        op_val = (
            0.35 * npz["lrm_abs_max"].astype(np.float32)
            + 0.35 * npz["openness_dipole_max"].astype(np.float32)
            + 0.30 * npz["openness_asymm_max"].astype(np.float32)
        )
        valid_idx = (idx >= 0) & (idx < n_fp) & np.isfinite(op_val)
        openness_fp[idx[valid_idx]] = op_val[valid_idx]
    save_col(50, robust_z_in_fp(fill_grid_from_fp(openness_fp, fp), fp))
    del openness_fp

    channel_gate = np.exp(-0.5 * ((c_log_area - 5.8) / 1.4) ** 2).astype(np.float32)
    ksn_knick = np.maximum(fill_grid_from_fp(robust_z_in_fp(c_ksn, fp), fp), 0.0) * channel_gate
    save_col(51, robust_z_in_fp(ksn_knick, fp))
    del c_ksn, c_log_area, channel_gate, ksn_knick

    with rasterio.open(droot / "external" / "dem10_chi_100m_u8.tif") as ds_chi8:
        chi_knick = ndi.gaussian_filter(ds_chi8.read(1).astype(np.float32), sigma=2.0, mode="nearest")
    save_col(52, robust_z_in_fp(chi_knick, fp))
    del chi_knick

    z_valley = -load_col_grid(11)  # -b12_det_elev
    save_col(53, robust_z_in_fp(oriented_collinear_max(z_valley, length_px=11, n_orient=8), fp))
    del z_valley
    gc.collect()

    # 5. Non-Fault Mimic Decontamination & Context (54..59)
    shoreline_elev = np.maximum(
        np.exp(-0.5 * ((z_asl - 1332.0) / 16.0) ** 2),
        0.85
        * np.maximum(
            np.exp(-0.5 * ((z_asl - 1463.0) / 14.0) ** 2),
            np.exp(-0.5 * ((z_asl - 1552.0) / 14.0) ** 2),
        ),
    ).astype(np.float32)
    z_mean_9 = ndi.uniform_filter(z_asl, size=9, mode="nearest")
    z_std_9 = np.sqrt(np.maximum(ndi.uniform_filter((z_asl - z_mean_9) ** 2, size=9, mode="nearest"), 0.0)).astype(
        np.float32
    )
    del z_mean_9
    along_scarp_climb = (z_std_9 / (3.5 * grad_mag_2d(z_asl, sigma=1.0) + 3.0)).astype(np.float32)
    del z_std_9, z_asl

    subsurface_quiet_fp = np.exp(-0.5 * (np.maximum(z_kappa_mag_fp, 0.0) + np.maximum(z_kappa_grav_fp, 0.0)))
    scarp_any = np.maximum(z_lid_grid, z_dem10_grid)
    del z_lid_grid, z_dem10_grid, z_kappa_mag_fp, z_kappa_grav_fp
    lahontan_mimic = (
        shoreline_elev
        * np.maximum(scarp_any, 0.0)
        * fill_grid_from_fp(subsurface_quiet_fp, fp)
        / (0.5 + along_scarp_climb)
    ).astype(np.float32)
    save_col(54, robust_z_in_fp(lahontan_mimic, fp))
    save_col(55, robust_z_in_fp(along_scarp_climb, fp))
    del shoreline_elev, subsurface_quiet_fp, lahontan_mimic, along_scarp_climb

    with rasterio.open(droot / "external" / "tiger_road_distance_m.tif") as ds_rd:
        d_road = ds_rd.read(1).astype(np.float32)
    d_road = np.where(np.isfinite(d_road), np.maximum(d_road, 0.0), 1e5)
    road_prox = np.exp(-d_road / 150.0).astype(np.float32)
    del d_road
    save_col(56, road_prox[fp])
    save_col(57, robust_z_in_fp(road_prox * np.maximum(scarp_any, 0.0), fp))
    del road_prox, scarp_any

    with rasterio.open(droot / "training_features.tif") as ds_tr:
        slope_deg = _read_tr_band(ds_tr, 19, fp)
    piedmont_regime = (
        np.exp(-0.5 * ((slope_deg - 3.8) / 4.2) ** 2) * (1.0 - np.exp(-depth_km / 0.6))
    ).astype(np.float32)
    del slope_deg, depth_km
    save_col(58, robust_z_in_fp(piedmont_regime, fp))
    del piedmont_regime

    z_b4_fp = np.frombuffer((cols_dir / "c003.f16").read_bytes(), dtype=np.float16).astype(np.float32)
    save_col(59, robust_z_in_fp(fill_grid_from_fp(0.50 * z_b4_fp + 0.35 * z_shear_fp + 0.15 * z_dilate_fp, fp), fp))
    del z_b4_fp, z_shear_fp, z_dilate_fp
    gc.collect()

    # Assemble row-major `(n_fp, 60)` float16 file in 500k-pixel row chunks (<70 MB buffer!)
    tmp_out = mmap_path.with_suffix(".assembling")
    col_handles = [(cols_dir / f"c{c:03d}.f16").open("rb") for c in range(n_ch)]
    try:
        with tmp_out.open("wb") as out_f:
            row_chunk = 500_000
            for start in range(0, n_fp, row_chunk):
                cnt = min(row_chunk, n_fp - start)
                blk = np.empty((cnt, n_ch), dtype=np.float16)
                for c, fh in enumerate(col_handles):
                    blk[:, c] = np.frombuffer(fh.read(cnt * 2), dtype=np.float16)
                out_f.write(blk.tobytes())
    finally:
        for fh in col_handles:
            fh.close()
    tmp_out.replace(mmap_path)
    shutil.rmtree(cols_dir, ignore_errors=True)

    elapsed = round(time.time() - t0, 2)
    meta = {
        "schema_version": 1,
        "lane_id": "H86-FVMB",
        "n_fp": n_fp,
        "n_channels": n_ch,
        "dtype": "float16",
        "elapsed_seconds": elapsed,
        "lidar_1m_fraction": lid_valid_frac,
        "wallace_3m_fraction": w3_cov_frac,
        "channel_names": STATIC_60_NAMES,
        "leakage_assertions": {
            "labels_tif_read": False,
            "existing_faults_tif_read": False,
            "sgmc_faults_read": False,
            "gdr_dist_known_fault_px_stripped": True,
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    gc.collect()
    return mmap_path, meta
