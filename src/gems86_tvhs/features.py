"""Feature physics for H86J-TVHS.

All competition band indices and derivative sign conventions are verified against
``src/gems86/io.py`` (``BANDS`` and ``BAND_PHYSICS_VERIFIED``):
  * Band 6 (``tc``)  = USGS GeoDAWN Radiometric Total Count (NOT magnetic tilt).
  * Band 11 (``iso_grav_anom_vg``) = +d(Band 13)/d(row_south) = -dg/dy_north.
  * Band 18 (``iso_grav_anom_hg``) = +d(Band 13)/dx_east.

Every external CSV reader enforces ``BANNED_CSV_COLUMNS = {'dist_known_fault_px'}``
so no precomputed distance to mapped faults can enter any static feature plane.
"""
from __future__ import annotations

import csv
import gc
import json
import struct
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

from src.gems86.io import BY_NAME, NODATA

BANNED_CSV_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})
ACCESSED_CSV_COLUMNS: dict[str, tuple[str, ...]] = {}

NATIVE_ABLATION_NAMES: tuple[str, ...] = (
    "theta_mag_abs",
    "verduzco_tilt_depth_inv_s2",
    "verduzco_tilt_depth_inv_s5",
    "laplace_gzz_zerocross_s3",
    "laplace_gzz_zerocross_s6",
    "grav_vec_mag_s2",
    "rtp_grad_s2",
    "poisson_tensor_misalign_s4",
    "base_hinge_curv_s4",
    "tc_decouple_quiet",
    "cond_smectite_s2",
    "cond_margin_grad_s2",
    "strain_transtens",
    "eq_prox_exp",
    "dem_hess_scarp_s2",
    "slope_local",
)

TVHS_NOVEL_STATIC_NAMES: tuple[str, ...] = (
    "ggt_diff_curv_s3",
    "ggt_2d_sheet_index_s4",
    "ggt_updip_throw_proj_s3",
    "geophys_conjugate_intersection_s4",
    "gdr_t2m_thermal_wall_plume",
    "gdr_paleo_sinter_vent_halo",
    "gdr_upslope_geotherm_excess",
    "lidar1m_scarp_step_coh",
    "dem10_chi_knick_diseq",
    "geodawn_k_th_u_alteration_deconf",
)

ALL_STATIC_NAMES: tuple[str, ...] = NATIVE_ABLATION_NAMES + TVHS_NOVEL_STATIC_NAMES

COUPLED_KINEMATIC_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "conjugate_intersection_cone",
    "broadside_stress_shadow",
)


def rank01(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Tie-invariant midpoint percentile rank on ``[0, 1]`` inside ``footprint``.

    Assigns identical values their exact average rank (preventing the row-major
    southern-packing defect ``IR-86-MMT-RANK01-TIE-20261024``) and zeros outside
    ``footprint``.
    """
    fp = np.asarray(footprint, dtype=bool)
    out = np.zeros(arr.shape, dtype=np.float32)
    valid = fp & np.isfinite(arr)
    n = int(valid.sum())
    if n <= 1:
        if n == 1:
            out[valid] = 0.5
        return out
    vals = np.asarray(arr[valid], dtype=np.float64)
    uniq, inv, counts = np.unique(vals, return_inverse=True, return_counts=True)
    if uniq.size <= 1:
        out[valid] = 0.5
        return out
    cum = np.cumsum(counts, dtype=np.float64)
    starts = cum - counts
    mid_ranks = (starts + 0.5 * (counts - 1.0)) / float(n - 1)
    out[valid] = mid_ranks[inv].astype(np.float32)
    return out


def _read_native_band(features_tif: Path, name: str) -> np.ndarray:
    idx = BY_NAME[name]
    with rasterio.open(features_tif) as src:
        raw = src.read(idx).astype(np.float32)
    bad = (~np.isfinite(raw)) | (np.abs(raw) > 1e20) | (raw == NODATA)
    raw[bad] = np.nan
    return raw


def _fill_outside_footprint(
    raw: np.ndarray, footprint: np.ndarray, nearest_idx: tuple[np.ndarray, np.ndarray] | None = None
) -> np.ndarray:
    valid = np.asarray(footprint, dtype=bool) & np.isfinite(raw)
    if not valid.any():
        return np.zeros_like(raw, dtype=np.float32)
    if nearest_idx is None or not np.all(np.isfinite(raw[footprint])):
        _, nearest_idx = ndi.distance_transform_edt(~valid, return_indices=True)
    filled = raw[nearest_idx[0], nearest_idx[1]].astype(np.float32, copy=True)
    if not np.isfinite(filled).all():
        med = float(np.nanmedian(raw[valid]))
        filled = np.where(np.isfinite(filled), filled, med).astype(np.float32)
    return filled


def _robust_standardize(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=np.float32)
    fp = np.asarray(footprint, dtype=bool)
    valid = fp & np.isfinite(a)
    if not valid.any():
        return np.zeros_like(a, dtype=np.float32)
    vals = a[valid]
    lo, hi = np.percentile(vals, [1.0, 99.0])
    scale = max(float(hi - lo), float(np.std(vals)), 1e-6)
    normed = np.clip((a - float(lo)) / scale, -2.0, 4.0)
    return np.where(valid, normed, 0.0).astype(np.float32)


def _zerocross_sharpness(
    field: np.ndarray, footprint: np.ndarray, sigma_grad: float = 1.5, width_frac: float = 0.35
) -> np.ndarray:
    gy = ndi.gaussian_filter(field, sigma_grad, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(field, sigma_grad, order=(0, 1), mode="nearest")
    gmag = np.hypot(gx, gy)
    scale = float(np.std(field[footprint])) if np.any(footprint) else 1.0
    scale = max(scale * width_frac, 1e-6)
    return (gmag * np.exp(-((field / scale) ** 2))).astype(np.float32)


def _principal_axis_spin2(field: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    fxx = ndi.gaussian_filter(field, sigma, order=(0, 2), mode="nearest")
    fyy = ndi.gaussian_filter(field, sigma, order=(2, 0), mode="nearest")
    fxy = ndi.gaussian_filter(field, sigma, order=(1, 1), mode="nearest")
    dx = fxx - fyy
    dy = 2.0 * fxy
    norm = np.hypot(dx, dy) + 1e-8
    return (dx / norm).astype(np.float32), (dy / norm).astype(np.float32)


def _hessian_ridge_abs(field: np.ndarray, sigma: float) -> np.ndarray:
    fxx = ndi.gaussian_filter(field, sigma, order=(0, 2), mode="nearest")
    fyy = ndi.gaussian_filter(field, sigma, order=(2, 0), mode="nearest")
    fxy = ndi.gaussian_filter(field, sigma, order=(1, 1), mode="nearest")
    tr = 0.5 * (fxx + fyy)
    disc = np.sqrt(0.25 * (fxx - fyy) ** 2 + fxy**2)
    return (np.maximum(np.abs(tr + disc), np.abs(tr - disc)) * (sigma * sigma)).astype(np.float32)


def compute_ggt_invariants(
    b18_grav_east: np.ndarray,
    b11_grav_south: np.ndarray,
    footprint: np.ndarray,
    sigma: float = 3.0,
) -> dict[str, np.ndarray]:
    """Compute Pedersen-Rasmussen (1990) Harmonic Gravity-Gradient Tensor (GGT) invariants.

    Using verified sign conventions on the north-up 100 m UTM grid:
      * ``b18_grav_east``  = +dg/dx_east
      * ``b11_grav_south`` = +dg/drow_south = -dg/dy_north

    In Cartesian (x = east, r = south):
      * T_xx = d(g_east)/dx_east
      * T_rr = d(g_south)/drow_south  (= T_yy in north coordinates)
      * T_xr = 0.5 * (d(g_east)/drow_south + d(g_south)/dx_east)
      * Curl defect = |d(g_east)/drow_south - d(g_south)/dx_east| (non-conservative seam detector)
      * Laplace vertical curvature: T_zz = -(T_xx + T_rr)

    Pedersen & Rasmussen (1990) horizontal-gradient tensor invariants:
      * Differential curvature: T_Delta = sqrt((T_xx - T_rr)^2 + 4 * T_xr^2)
      * Second invariant (horizontal+vertical trace-free sheet determinant):
          I_1_sheet = T_xx * T_rr - T_xr^2
        For an ideal infinite 2-D normal-fault step of arbitrary strike alpha, one
        horizontal principal curvature vanishes along strike, so ``I_1_sheet == 0``
        while ``T_Delta > 0``! Conversely, for an axisymmetric 3-D stock/plug/caldera
        center, ``T_xx == T_rr`` and ``T_xr == 0``, so ``T_Delta == 0`` while
        ``|I_1_sheet|`` is maximal!
      * Quasi-2D fault-step dimensionality index:
          D_2D = T_Delta^2 / (T_Delta^2 + 4 * |I_1_sheet| + eps) in [0, 1].
    """
    fp = np.asarray(footprint, dtype=bool)
    ge = np.asarray(b18_grav_east, dtype=np.float32)
    gs = np.asarray(b11_grav_south, dtype=np.float32)

    txx = ndi.gaussian_filter(ge, sigma=sigma, order=(0, 1), mode="nearest")
    trr = ndi.gaussian_filter(gs, sigma=sigma, order=(1, 0), mode="nearest")
    dge_dr = ndi.gaussian_filter(ge, sigma=sigma, order=(1, 0), mode="nearest")
    dgs_dx = ndi.gaussian_filter(gs, sigma=sigma, order=(0, 1), mode="nearest")

    txr = 0.5 * (dge_dr + dgs_dx)
    curl_def = np.abs(dge_dr - dgs_dx).astype(np.float32)
    tzz = (-(txx + trr)).astype(np.float32)

    t_delta = np.hypot(txx - trr, 2.0 * txr).astype(np.float32)
    i1_sheet = (txx * trr - txr * txr).astype(np.float32)

    td_scale = max(float(np.percentile(t_delta[fp], 75.0)) if fp.any() else 1.0, 1e-6)
    eps_i1 = float((0.15 * td_scale) ** 2)
    d_2d = ((t_delta * t_delta) / (t_delta * t_delta + 4.0 * np.abs(i1_sheet) + eps_i1)).astype(np.float32)
    sheet_2d_score = (d_2d * np.tanh(t_delta / td_scale)).astype(np.float32)

    # Spin-2 horizontal GGT principal axis (cos 2psi, sin 2psi)
    norm_spin = t_delta + 1e-8
    c2_ggt = ((txx - trr) / norm_spin).astype(np.float32)
    s2_ggt = ((2.0 * txr) / norm_spin).astype(np.float32)

    # Updip fault-tip curvature-to-differential-curvature zero-crossing projection
    ratio_z = tzz / (t_delta + 0.5 * td_scale)
    updip_proj = (_zerocross_sharpness(ratio_z, fp, sigma_grad=1.5) * np.tanh(t_delta / td_scale)).astype(np.float32)

    return {
        "t_zz": tzz,
        "curl_defect": curl_def,
        "t_delta": t_delta,
        "d_2d": d_2d,
        "sheet_2d_score": sheet_2d_score,
        "updip_proj": updip_proj,
        "c2_ggt": c2_ggt,
        "s2_ggt": s2_ggt,
    }


def _parse_2m_probes(zpath: Path, shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    with zipfile.ZipFile(zpath) as zf:
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
        rec: dict[str, str] = {}
        for fn, fl in fields:
            rec[fn] = row_bytes[off : off + fl].decode("utf-8", errors="replace").strip()
            off += fl
        lons.append(x)
        lats.append(y)
        dabs.append(float(rec["F2mDAB"]) if rec.get("F2mDAB") else 0.0)

    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])

    imp_anom = np.zeros(shape, dtype=np.float32)
    imp_cnt = np.zeros(shape, dtype=np.float32)
    dab_pos = np.clip(np.nan_to_num(np.asarray(dabs, dtype=np.float32), nan=0.0), 0.0, 15.0)
    np.maximum.at(imp_anom, (rows[inb], cols[inb]), dab_pos[inb])
    np.add.at(imp_cnt, (rows[inb], cols[inb]), 1.0)

    plume = (
        ndi.gaussian_filter(imp_anom, sigma=9.0, mode="constant")
        / (ndi.gaussian_filter((imp_cnt > 0).astype(np.float32), sigma=9.0, mode="constant") + 0.008)
    ).astype(np.float32)
    ty = ndi.gaussian_filter(plume, sigma=3.5, order=(1, 0), mode="nearest")
    tx = ndi.gaussian_filter(plume, sigma=3.5, order=(0, 1), mode="nearest")
    t_wall = np.hypot(ty, tx).astype(np.float32)
    out = (0.58 * rank01(t_wall, footprint) + 0.42 * rank01(plume, footprint)).astype(np.float32)
    out[~footprint] = 0.0
    return out


def _parse_paleo_sinter_and_vents(
    sinter_zip: Path, vents_csv: Path, shape: tuple[int, int], footprint: np.ndarray
) -> np.ndarray:
    with zipfile.ZipFile(sinter_zip) as zf:
        lines = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    lons: list[float] = []
    lats: list[float] = []
    for row in csv.DictReader(lines):
        try:
            lons.append(float(row["Long_deg_NAD83"]))
            lats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    src = np.zeros(shape, dtype=bool)
    src[rows[inb], cols[inb]] = True
    d_sinter = ndi.distance_transform_edt(~src).astype(np.float32)
    sinter_halo = (0.68 * np.exp(-d_sinter / 6.5) + 0.32 * np.exp(-d_sinter / 20.0)).astype(np.float32)

    allowed_cols = ("row", "col")
    ACCESSED_CSV_COLUMNS[vents_csv.name] = allowed_cols
    if set(allowed_cols) & BANNED_CSV_COLUMNS:
        raise AssertionError("Banned column requested")
    vsrc = np.zeros(shape, dtype=bool)
    with vents_csv.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            r, c = int(row["row"]), int(row["col"])
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                vsrc[r, c] = True
    d_vent = ndi.distance_transform_edt(~vsrc).astype(np.float32)
    vent_halo = np.exp(-d_vent / 28.0).astype(np.float32)

    out = (0.82 * sinter_halo + 0.18 * vent_halo).astype(np.float32)
    out[~footprint] = 0.0
    return out


def _parse_wellspring_upslope(
    cpath: Path, shape: tuple[int, int], footprint: np.ndarray, elev_filled: np.ndarray
) -> np.ndarray:
    allowed_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c")
    ACCESSED_CSV_COLUMNS[cpath.name] = allowed_cols
    if set(allowed_cols) & BANNED_CSV_COLUMNS:
        raise AssertionError("Banned column requested")

    dem_sm = ndi.gaussian_filter(elev_filled, sigma=4.0, mode="nearest")
    gy = ndi.gaussian_filter(dem_sm, sigma=4.0, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(dem_sm, sigma=4.0, order=(0, 1), mode="nearest")
    gn = np.hypot(gy, gx) + 1e-6
    uy = gy / gn
    ux = gx / gn

    imp = np.zeros(shape, dtype=np.float32)
    with cpath.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                r = int(row["row"])
                c = int(row["col"])
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            tc = float(row["temp_c"]) if row.get("temp_c") else 0.0
            tq = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") else 0.0
            tch = float(row["geothermchalc_c"]) if row.get("geothermchalc_c") else 0.0
            geoth = max(tq, tch)
            diseq = max(geoth - max(tc, 15.0), 0.0) / 90.0
            score = max(tc - 20.0, 0.0) / 40.0 + 0.65 * max(geoth - 80.0, 0.0) / 100.0 + 0.35 * diseq
            if score <= 0.02:
                continue
            ru = int(np.clip(round(r + 3.0 * float(uy[r, c])), 0, shape[0] - 1))
            cu = int(np.clip(round(c + 3.0 * float(ux[r, c])), 0, shape[1] - 1))
            if score > imp[ru, cu]:
                imp[ru, cu] = min(score, 4.5)
    out = (
        0.65 * ndi.gaussian_filter(imp, sigma=5.0, mode="constant")
        + 0.35 * ndi.gaussian_filter(imp, sigma=15.0, mode="constant")
    ).astype(np.float32)
    out[~footprint] = 0.0
    return out


def compute_exposure_propensity_weights(
    features_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
) -> np.ndarray:
    """Estimate smooth surficial fault-exposure propensity ``c_expo(x)`` WITHOUT touching labels.

    Alluvial bajadas, valley floors, and Lake Lahontan playas have low topographic slope,
    low local relief, and thick unconsolidated cover where active faults lose surface
    scarps; steep bedrock range fronts have high exposure propensity. Returns bounded
    inverse-propensity positive weights ``w_sar(x) = clip(1 / c_expo(x), 1.0, 2.5)`` on
    ``footprint`` (and ``1.0`` outside) for Bekker-Davis SAR PU sample reweighting.
    """
    fp = np.asarray(footprint, dtype=bool)
    slope_raw = _read_native_band(features_tif, "det_elev_slope")
    slope_r = rank01(np.where(np.isfinite(slope_raw), slope_raw, 0.0), fp)
    del slope_raw

    with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as ds_t10:
        relief_u8 = ds_t10.read(5).astype(np.float32)
        steep_u8 = ds_t10.read(3).astype(np.float32)
    relief_r = rank01(relief_u8, fp)
    steep_r = rank01(steep_u8, fp)
    del relief_u8, steep_u8

    raw_expo = ndi.gaussian_filter(
        0.45 * slope_r + 0.35 * relief_r + 0.20 * steep_r, sigma=6.0, mode="nearest"
    )
    del slope_r, relief_r, steep_r
    expo_rank = rank01(raw_expo, fp)
    # Map [0, 1] exposure rank smoothly onto c_expo in [0.40, 1.00] -> w_sar in [1.00, 2.50]
    c_expo = 0.40 + 0.60 * expo_rank
    w_sar = np.where(fp, np.clip(1.0 / c_expo, 1.0, 2.5), 1.0).astype(np.float32)
    return w_sar


def build_tvhs_static_features(
    features_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
    out_memmap_path: Path | None = None,
) -> dict[str, np.ndarray] | np.ndarray:
    """Compute all 26 label-free TVHS static planes (16 native + 10 novel GGT/GDR/3DEP/GeoDAWN).

    Streams directly into a ``float16`` memmap ``(26, H, W)`` when ``out_memmap_path``
    is provided so peak RAM stays well below 1.5 GiB.
    """
    fp = np.asarray(footprint, dtype=bool)
    elev_raw = _read_native_band(features_tif, "det_elev")
    valid0 = fp & np.isfinite(elev_raw)
    _, nearest_idx = ndi.distance_transform_edt(~valid0, return_indices=True)

    def load(name: str) -> np.ndarray:
        return _fill_outside_footprint(_read_native_band(features_tif, name), fp, nearest_idx)

    mm = None
    out: dict[str, np.ndarray] = {}
    if out_memmap_path is not None:
        out_memmap_path.parent.mkdir(parents=True, exist_ok=True)
        mm = np.lib.format.open_memmap(
            out_memmap_path,
            mode="w+",
            dtype=np.float16,
            shape=(len(ALL_STATIC_NAMES), fp.shape[0], fp.shape[1]),
        )

    def store(key: str, arr: np.ndarray) -> None:
        std_arr = _robust_standardize(arr, fp)
        if mm is not None:
            mm[ALL_STATIC_NAMES.index(key)] = std_arr.astype(np.float16)
        else:
            out[key] = std_arr

    # 1. Magnetic Verduzco tilt-depth & RTP gradients (Bands 2, 3, 9)
    tmi_hg = np.maximum(load("tmi_hg"), 1e-6)
    tmi_vg = load("tmi_vg")
    theta_mag = np.arctan2(tmi_vg, tmi_hg).astype(np.float32)
    del tmi_hg, tmi_vg
    store("theta_mag_abs", np.abs(theta_mag))

    tilt_s3 = ndi.gaussian_filter(theta_mag, 3.0, mode="nearest")
    ty3 = ndi.gaussian_filter(tilt_s3, 1.0, order=(1, 0), mode="nearest")
    tx3 = ndi.gaussian_filter(tilt_s3, 1.0, order=(0, 1), mode="nearest")
    tilt_edge_s3 = (np.hypot(tx3, ty3) * np.exp(-((tilt_s3 / 0.35) ** 2))).astype(np.float32)
    del tilt_s3, ty3, tx3

    for s, key in ((2.0, "verduzco_tilt_depth_inv_s2"), (5.0, "verduzco_tilt_depth_inv_s5")):
        th_s = ndi.gaussian_filter(theta_mag, s, mode="nearest")
        gy = ndi.gaussian_filter(th_s, 1.0, order=(1, 0), mode="nearest")
        gx = ndi.gaussian_filter(th_s, 1.0, order=(0, 1), mode="nearest")
        store(key, np.hypot(gx, gy) * np.exp(-((th_s / 0.35) ** 2)))
        del th_s, gy, gx
    del theta_mag
    gc.collect()

    # 2. Verified signed Gravity Vector (Bands 18, 11) + Pedersen-Rasmussen GGT Invariants
    b18 = load("iso_grav_anom_hg")
    b11 = load("iso_grav_anom_vg")
    ggt3 = compute_ggt_invariants(b18, b11, fp, sigma=3.0)
    curl_med = max(float(np.median(ggt3["curl_defect"][fp])), 1e-6) if fp.any() else 1.0
    curl_veto = (1.0 / (1.0 + (ggt3["curl_defect"] / (2.5 * curl_med)) ** 2)).astype(np.float32)

    store("laplace_gzz_zerocross_s3", _zerocross_sharpness(ggt3["t_zz"], fp, sigma_grad=1.5) * curl_veto)
    store("ggt_diff_curv_s3", ggt3["t_delta"] * curl_veto)
    store("ggt_updip_throw_proj_s3", ggt3["updip_proj"] * curl_veto)
    c2_ggt = ggt3["c2_ggt"]
    s2_ggt = ggt3["s2_ggt"]
    t_delta_s3 = ggt3["t_delta"]
    del ggt3

    ggt4 = compute_ggt_invariants(b18, b11, fp, sigma=4.0)
    store("ggt_2d_sheet_index_s4", ggt4["sheet_2d_score"] * curl_veto)
    del ggt4

    ggt6 = compute_ggt_invariants(b18, b11, fp, sigma=6.0)
    store("laplace_gzz_zerocross_s6", _zerocross_sharpness(ggt6["t_zz"], fp, sigma_grad=2.0) * curl_veto)
    del ggt6

    gvec = ndi.gaussian_filter(np.hypot(b18, b11), 2.0, mode="nearest").astype(np.float32)
    del b18, b11
    store("grav_vec_mag_s2", gvec)
    gc.collect()

    # 3. Garland-Poisson & Multi-Physics GGT x RTP Conjugate Structural Intersection (Bands 13, 2)
    iso_g = load("iso_grav_anom")
    cg, sg = _principal_axis_spin2(iso_g, sigma=4.0)
    del iso_g
    rtp = load("rtp")
    cm, sm = _principal_axis_spin2(rtp, sigma=4.0)
    sin2_misalign = 0.5 * (1.0 - np.clip(cg * cm + sg * sm, -1.0, 1.0))
    del cg, sg
    rtp_gm = np.hypot(
        ndi.gaussian_filter(rtp, 2.0, order=(0, 1), mode="nearest"),
        ndi.gaussian_filter(rtp, 2.0, order=(1, 0), mode="nearest"),
    ).astype(np.float32)
    del rtp
    g_scale = max(float(np.percentile(gvec[fp], 75.0)), 1e-6) if fp.any() else 1.0
    m_scale = max(float(np.percentile(rtp_gm[fp], 75.0)), 1e-6) if fp.any() else 1.0
    store("poisson_tensor_misalign_s4", sin2_misalign * np.tanh(gvec / g_scale) * np.tanh(rtp_gm / m_scale) * curl_veto)
    store("rtp_grad_s2", rtp_gm)

    # High-angle GGT sheet-step x RTP magnetic-tilt conjugate intersection (30-90 deg crossing)
    sin2_ggt_mag = 0.5 * (1.0 - np.clip(c2_ggt * cm + s2_ggt * sm, -1.0, 1.0))
    td_s = max(float(np.percentile(t_delta_s3[fp], 75.0)), 1e-6) if fp.any() else 1.0
    te_s = max(float(np.percentile(tilt_edge_s3[fp], 75.0)), 1e-6) if fp.any() else 1.0
    conj_geophys = sin2_ggt_mag * np.tanh(t_delta_s3 / td_s) * np.tanh(tilt_edge_s3 / te_s) * curl_veto
    store("geophys_conjugate_intersection_s4", conj_geophys)
    del cm, sm, c2_ggt, s2_ggt, t_delta_s3, tilt_edge_s3, sin2_misalign, rtp_gm, gvec, curl_veto, conj_geophys
    gc.collect()

    # 4. Basement hinge (Band 15), Radiometric TC quietness (Band 6), Smectite clay-cap margin (Band 17)
    base_d = load("depth_to_base_surf")
    store("base_hinge_curv_s4", _hessian_ridge_abs(base_d, sigma=4.0))
    del base_d

    tc = load("tc")
    tc_gm = np.hypot(
        ndi.gaussian_filter(tc, 2.0, order=(0, 1), mode="nearest"),
        ndi.gaussian_filter(tc, 2.0, order=(1, 0), mode="nearest"),
    )
    del tc
    tc_med = max(float(np.median(tc_gm[fp])), 1e-6) if fp.any() else 1.0
    store("tc_decouple_quiet", 1.0 / (1.0 + tc_gm / tc_med))
    del tc_gm

    cond = load("cond_surf")
    cond_s2 = ndi.gaussian_filter(cond, 2.0, mode="nearest")
    store("cond_smectite_s2", cond_s2)
    cond_grad = np.hypot(
        ndi.gaussian_filter(cond_s2, 1.5, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(cond_s2, 1.5, order=(0, 1), mode="nearest"),
    )
    store("cond_margin_grad_s2", cond_grad)
    del cond, cond_s2, cond_grad
    gc.collect()

    # 5. Geodetic transtension & microseismicity (Bands 4, 7, 8, 10, 16)
    dilat = load("geod_dilaterate")
    shear = load("geod_shearrate")
    inv2 = load("geod_2ndinv")
    pos_dilat = np.maximum(dilat - float(np.median(dilat[fp]) if fp.any() else 0.0), 0.0)
    store("strain_transtens", np.sqrt(np.maximum(shear, 0.0) * pos_dilat + 1e-12) + 0.25 * inv2)
    del dilat, shear, inv2, pos_dilat

    eq_d = np.maximum(load("deq_n100a15"), 0.0)
    ieq = load("ieq_n100a15")
    eq_scale = max(float(np.median(eq_d[fp])), 1.0) if fp.any() else 1000.0
    store("eq_prox_exp", 0.5 * np.exp(-eq_d / (0.5 * eq_scale)) + 0.5 * np.tanh(np.maximum(ieq, 0.0)))
    del eq_d, ieq

    # 6. Native DEM scarp curvature & slope (Bands 12, 19)
    elev_filled = _fill_outside_footprint(elev_raw, fp, nearest_idx)
    del elev_raw, nearest_idx
    store("dem_hess_scarp_s2", _hessian_ridge_abs(elev_filled, sigma=2.0))
    slope = _read_native_band(features_tif, "det_elev_slope")
    store("slope_local", np.where(fp & np.isfinite(slope), slope, 0.0))
    del slope
    gc.collect()

    # 7. Official DOE GDR-1391 Hydrothermal Vent, Sinter & Upslope Geothermometry Planes
    t2m = _parse_2m_probes(
        external_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip", fp.shape, fp
    )
    store("gdr_t2m_thermal_wall_plume", t2m)
    del t2m

    sinter = _parse_paleo_sinter_and_vents(
        external_dir / "paleo_geothermal_regional.zip",
        external_dir / "gdr_volcanic_vents_in_footprint.csv",
        fp.shape,
        fp,
    )
    store("gdr_paleo_sinter_vent_halo", sinter)
    del sinter

    geoth = _parse_wellspring_upslope(
        external_dir / "gdr_wellspring_in_footprint.csv", fp.shape, fp, elev_filled
    )
    store("gdr_upslope_geotherm_excess", geoth)
    del geoth, elev_filled
    gc.collect()

    # 8. USGS 3DEP 1-m LiDAR Scarplets + 10-m DEM Profile Curvature + Fluvial Chi Knickzones
    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as ds_lid:
        step_u8 = ds_lid.read(3).astype(np.float32)
        cross_u8 = ds_lid.read(8).astype(np.float32)
        coh_u8 = ds_lid.read(10).astype(np.float32)
        valid_lid = ds_lid.read(12) > 0
    lid_score = np.where(
        valid_lid & fp,
        (step_u8 / 255.0) * (0.40 + 0.60 * (coh_u8 / 255.0)) + 0.35 * (cross_u8 / 255.0),
        0.0,
    ).astype(np.float32)
    del step_u8, cross_u8, coh_u8, valid_lid

    topo_man = json.loads((external_dir / "topo_10m_derived_100m_u8.manifest.json").read_text())
    bmeta = {b["band_name"]: b for b in topo_man["bands"]}
    with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as ds_t10:
        curv10_u8 = ds_t10.read(6).astype(np.float32)
        hs10_u8 = ds_t10.read(8).astype(np.float32)
        dem10_u8 = ds_t10.read(9).astype(np.float32)
    lo_d, hi_d = float(bmeta["dem_mean"]["lo"]), float(bmeta["dem_mean"]["hi"])
    dem10_m = lo_d + ((np.clip(dem10_u8, 1.0, 255.0) - 1.0) / 254.0) * (hi_d - lo_d)
    del dem10_u8

    store(
        "lidar1m_scarp_step_coh",
        0.60 * rank01(lid_score, fp) + 0.25 * rank01(curv10_u8, fp) + 0.15 * rank01(hs10_u8, fp),
    )
    del lid_score, curv10_u8, hs10_u8

    with rasterio.open(external_dir / "dem10_chi_100m_u8.tif") as ds_chi:
        knick_u8 = ds_chi.read(2).astype(np.float32)
        raised_u8 = ds_chi.read(3).astype(np.float32)
        vchi = ds_chi.read(4) > 0
    chi_score = np.where(
        vchi & fp,
        0.62 * (knick_u8 / 255.0) + 0.38 * (raised_u8 / 255.0),
        0.0,
    ).astype(np.float32)
    del knick_u8, raised_u8, vchi
    store("dem10_chi_knick_diseq", ndi.gaussian_filter(chi_score, 1.5, mode="nearest"))
    del chi_score

    # 9. USGS GeoDAWN K/Th & U/Th Hydrothermal Alteration Deconfounded for Survey Seams & Pluvial Shorelines
    with rasterio.open(external_dir / "geodawn_extensions_u8.tif") as ds_ge:
        thk_u8 = ds_ge.read(1).astype(np.float32)
        uk_u8 = ds_ge.read(2).astype(np.float32)
        uth_u8 = ds_ge.read(3).astype(np.float32)
    # Potassium enrichment relative to Thorium (low Th/K -> high 255 - ThK) + U/Th redox front
    k_enrich = np.where(thk_u8 > 0, (255.0 - thk_u8) / 255.0, 0.0)
    u_redox = np.where(uth_u8 > 0, uth_u8 / 255.0, 0.0)
    rad_alt = 0.55 * rank01(k_enrich, fp) + 0.30 * rank01(u_redox, fp) + 0.15 * rank01(uk_u8, fp)
    del thk_u8, uk_u8, uth_u8, k_enrich, u_redox

    with rasterio.open(external_dir / "acquisition_block_id_100m.tif") as ds_blk:
        blk = ds_blk.read(1)
    seam_raw = (ndi.maximum_filter(blk, size=3) != ndi.minimum_filter(blk, size=3)).astype(np.float32)
    del blk
    seam_halo = ndi.gaussian_filter(seam_raw, sigma=2.5, mode="constant")
    del seam_raw

    # Pleistocene Lake Lahontan (1270, 1332 m) & Bonneville (1463, 1552 m) wave-cut shoreline bands
    shore = np.zeros_like(dem10_m, dtype=np.float32)
    for level_m in (1270.0, 1332.0, 1463.0, 1552.0):
        shore = np.maximum(shore, np.exp(-(((dem10_m - level_m) / 14.0) ** 2)).astype(np.float32))
    del dem10_m

    mimic_veto = np.clip(1.0 - 0.60 * np.clip(seam_halo * 2.5, 0.0, 1.0) - 0.35 * shore, 0.15, 1.0)
    del seam_halo, shore
    store("geodawn_k_th_u_alteration_deconf", rad_alt * mimic_veto)
    del rad_alt, mimic_veto
    gc.collect()

    if mm is not None:
        mm.flush()
        del mm
        return np.load(out_memmap_path, mmap_mode="r")
    return out


def compute_faulds_hinz_kinematic_fields(
    vis_cat: np.ndarray, footprint: np.ndarray
) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible Faulds-Hinz structural-complexity fields.

    Includes:
      1. ``wing_crack_lobe``: Pollard-Segall (~27 deg off-axis) tensile horsetail lobes.
      2. ``collinear_tip_cone``: Along-strike fault-tip propagation cone across fan gaps.
      3. ``stepover_bridge``: Opposing-tip releasing-stepover / relay-ramp bridge.
      4. ``conjugate_intersection_cone``: Rotationally invariant spin-2 nematic defect
         ``sqrt(max(M^2 - (C_2^2 + S_2^2), 0))`` isolating high-angle conjugate fault
         intersections and accommodation zones (35-90 deg azimuth crossings).
      5. ``broadside_stress_shadow``: Mid-segment elastic normal-fault stress shadow.
    """
    fp = np.asarray(footprint, dtype=bool)
    v = (np.asarray(vis_cat, dtype=bool) & fp).astype(np.float32)
    h, w = fp.shape
    if v.sum() == 0:
        z = np.zeros((h, w), dtype=np.float16)
        return {k: z.copy() for k in COUPLED_KINEMATIC_NAMES}

    yy, xx = np.indices((h, w), dtype=np.float32)
    sigma_tip = 6.0
    mass = ndi.gaussian_filter(v, sigma_tip, mode="constant") + 1e-8
    mx = ndi.gaussian_filter(v * xx, sigma_tip, mode="constant") / mass - xx
    my = ndi.gaussian_filter(v * yy, sigma_tip, mode="constant") / mass - yy
    asym = np.hypot(mx, my)

    ux_prop = np.where(asym > 1e-4, -mx / (asym + 1e-6), 0.0).astype(np.float32)
    uy_prop = np.where(asym > 1e-4, -my / (asym + 1e-6), 0.0).astype(np.float32)
    tip_ness = np.clip((asym - 1.6) / 2.6, 0.0, 1.0) * (v > 0.5)
    tip_mask = (v > 0.5) & (asym >= 2.2)
    if not tip_mask.any():
        tip_mask = v > 0.5

    # Local fault ridge orientation via Hessian second-derivative spin-2 director (unit on v==1 crests!)
    c2_ridge, s2_ridge = _principal_axis_spin2(v, sigma=2.2)
    # Convert spin-2 normal axis (cos 2psi_n, sin 2psi_n) to unit tangent (tx, ty) up to sign for broadside test
    psi_n = 0.5 * np.arctan2(s2_ridge, c2_ridge)
    tx_tan = (-np.sin(psi_n)).astype(np.float32)
    ty_tan = np.cos(psi_n).astype(np.float32)
    del psi_n

    # Distance & nearest-tip projection
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

    wing_angular = (forward**1.2) * np.exp(-(((alpha_abs - 0.47) / 0.30) ** 2))
    del alpha_abs
    wing_crack_lobe = _robust_standardize(
        np.exp(-r_tip / 28.0) * wing_angular * (r_tip > 2.0), fp
    ).astype(np.float16)
    del wing_angular

    collinear_tip_cone = _robust_standardize(
        np.exp(-r_tip / 30.0) * (forward**3.0) * (r_tip > 2.0), fp
    ).astype(np.float16)
    del forward, r_tip

    # Opposing-tip releasing-stepover bridge
    tip_wt = tip_ness.astype(np.float32)
    scalar_tip = ndi.gaussian_filter(tip_wt, 18.0, mode="constant")
    vec_x = ndi.gaussian_filter(tip_wt * ux_prop, 18.0, mode="constant")
    vec_y = ndi.gaussian_filter(tip_wt * uy_prop, 18.0, mode="constant")
    del tip_wt, ux_prop, uy_prop, mx, my, asym
    stepover_bridge = _robust_standardize(
        np.sqrt(np.maximum(scalar_tip**2 - (vec_x**2 + vec_y**2), 0.0)), fp
    ).astype(np.float16)
    del scalar_tip, vec_x, vec_y

    # High-angle conjugate fault-intersection nematic defect (Faulds & Hinz 2015 setting #2)
    c2_v = v * c2_ridge
    s2_v = v * s2_ridge
    del c2_ridge, s2_ridge
    m_int = ndi.gaussian_filter(v, 14.0, mode="constant")
    c2_int = ndi.gaussian_filter(c2_v, 14.0, mode="constant")
    s2_int = ndi.gaussian_filter(s2_v, 14.0, mode="constant")
    del c2_v, s2_v
    nematic_defect = np.sqrt(np.maximum(m_int * m_int - (c2_int * c2_int + s2_int * s2_int), 0.0))
    del m_int, c2_int, s2_int

    d_vis_f64, (vy_i, vx_i) = ndi.distance_transform_edt(~(v > 0.5), return_indices=True)
    d_vis = d_vis_f64.astype(np.float32)
    del d_vis_f64, v

    conj_raw = nematic_defect * (d_vis > 2.0)
    del nematic_defect
    # Preserve absolute physical scale floor so straight isolated faults stay near 0
    conj_hi = max(float(np.percentile(conj_raw[fp], 99.0)) if fp.any() else 0.0, 5e-3)
    conjugate_intersection_cone = np.where(
        fp, np.clip(conj_raw / conj_hi, 0.0, 4.0), 0.0
    ).astype(np.float16)
    del conj_raw

    # Broadside mid-segment elastic stress shadow
    dx_v = xx - vx_i.astype(np.float32)
    dy_v = yy - vy_i.astype(np.float32)
    del xx, yy
    interior_wt = 1.0 - tip_ness[vy_i, vx_i]
    del tip_ness
    along_tan = np.abs(dx_v * tx_tan[vy_i, vx_i] + dy_v * ty_tan[vy_i, vx_i]) / (d_vis + 1e-5)
    del dx_v, dy_v, vy_i, vx_i, tx_tan, ty_tan
    broadside_orient = np.clip(1.0 - (along_tan / 0.40) ** 2, 0.0, 1.0)
    del along_tan
    radial_band = np.exp(-(((d_vis - 9.0) / 7.5) ** 2)) * (d_vis > 3.0)
    del d_vis
    broadside_stress_shadow = _robust_standardize(
        interior_wt * broadside_orient * radial_band, fp
    ).astype(np.float16)
    del interior_wt, broadside_orient, radial_band

    return {
        "wing_crack_lobe": wing_crack_lobe,
        "collinear_tip_cone": collinear_tip_cone,
        "stepover_bridge": stepover_bridge,
        "conjugate_intersection_cone": conjugate_intersection_cone,
        "broadside_stress_shadow": broadside_stress_shadow,
    }
