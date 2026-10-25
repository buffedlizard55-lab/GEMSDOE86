"""Hydrothermal-Vent Thermal-Wall, Paleo-Sinter & Bi-Harmonic Basement Flexure Gated Fault-Valve Discovery (H86I-HVFD).

Physics & Anti-Leakage Architecture
-----------------------------------
1. Static planes (``STATIC_FEATURE_NAMES``) are 100% catalogue-blind:
   - Never reads ``existing_faults.tif``, ``labels.tif``, ``trace_segments_utm11.csv``, or
     ``derived_sgmc_faults_100m_u8.tif``.
   - Point CSV readers (``gdr_wellspring_in_footprint.csv``, ``gdr_volcanic_vents_in_footprint.csv``)
     explicitly ban ``dist_known_fault_px`` and record ``ACCESSED_CSV_COLUMNS`` for unit-test verification.
2. Uses tie-invariant ``rank01`` (``scipy.stats.rankdata(v, method="min")``) so tied zero-floor
   cells map uniformly to ``0.0`` across all rows (preventing the north-to-south tie ramp logged
   in ``IR-86-MMT-RANK01-TIE-20261024``).
3. Visible-network trap planes (``TRAP_FEATURE_NAMES``) are computed strictly from the provided
   ``visible`` fault mask (``fold["visible"]`` inside holdout; ``g.catalogue`` only after pre-placement
   surface clearance) via unmodified ``vendor/gems57/network.py`` and ``vendor/gems57/relay_bend_anatomy.py``,
   clamping nearest-fault distance at ``d_vis >= 3.5 px`` so no immediate-collar leakage can occur.
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

from gems57 import network as NET
from gems57 import relay_bend_anatomy as RBA

NODATA_FLOOR = -1.0e37

BANNED_CSV_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})
ACCESSED_CSV_COLUMNS: dict[str, tuple[str, ...]] = {}

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    "t2m_thermal_wall_plume",
    "paleo_sinter_vent_halo",
    "upslope_geotherm_excess",
    "claycap_rad_alteration",
    "hvfd_vent_composite",
    "biharmonic_basement_flexure",
    "laplace_gzz_hinge",
    "poisson_mag_destruction",
    "hvfd_potential_composite",
    "lidar_dem10_chi_scarp",
    "coulomb_seismic_valve",
    "hvfd_mimic_suppression",
    "hvfd_blind_conduit_surface",
)

TRAP_FEATURE_NAMES: tuple[str, ...] = (
    "vis_tip_cone",
    "vis_relay_bridge",
    "vis_bend_hinge",
    "vis_vent_x_trap",
    "vis_trap_composite",
)


def rank01(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Tie-invariant percentile rank in [0, 1] on footprint, 0 outside (exact method='min')."""
    out = np.zeros(a.shape, dtype=np.float32)
    mask = np.asarray(footprint, dtype=bool)
    if not mask.any():
        return out
    v = np.asarray(a[mask], dtype=np.float32)
    v = np.where(np.isfinite(v), v, np.float32(0.0))
    n = v.size
    if n <= 1 or float(v.max()) <= float(v.min()):
        return out
    order = np.argsort(v, kind="mergesort")
    sorted_v = v[order]
    first_idx = np.empty(n, dtype=np.int32)
    first_idx[0] = 0
    same = sorted_v[1:] == sorted_v[:-1]
    idx = np.arange(n, dtype=np.int32)
    first_idx[1:] = np.where(same, 0, idx[1:])
    np.maximum.accumulate(first_idx, out=first_idx)
    del sorted_v, same, idx
    ranks = np.empty(n, dtype=np.float32)
    ranks[order] = first_idx.astype(np.float32) / np.float32(n - 1)
    del order, first_idx
    out[mask] = ranks
    return out


class _LazyBand:
    """Read a single GeoTIFF band on demand so 13 full-grid bands never reside in RAM at once."""

    def __init__(self, tif_path: Path, band_idx: int) -> None:
        self.tif_path = tif_path
        self.band_idx = band_idx

    def __array__(self, dtype=None) -> np.ndarray:
        with rasterio.open(self.tif_path) as src:
            arr = src.read(self.band_idx)
        return arr.astype(dtype or np.float32, copy=False)


def _clean_band(raw: np.ndarray | _LazyBand, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(raw, dtype=np.float32)
    fp = np.asarray(footprint, dtype=bool)
    valid = fp & np.isfinite(arr) & (arr > NODATA_FLOOR)
    med = float(np.median(arr[valid])) if np.any(valid) else 0.0
    out = np.where(valid, arr, np.float32(med))
    out = np.where(fp, out, np.float32(0.0))
    return out, valid.astype(np.float32)


def _smooth_masked(arr: np.ndarray, weights: np.ndarray, sigma_px: float) -> np.ndarray:
    if sigma_px <= 0.0:
        return np.where(weights > 0.0, arr, np.float32(0.0)).astype(np.float32)
    num = ndi.gaussian_filter((arr * weights).astype(np.float32), sigma=float(sigma_px), mode="nearest")
    den = ndi.gaussian_filter(weights.astype(np.float32), sigma=float(sigma_px), mode="nearest")
    return np.where(den > 1e-5, num / np.maximum(den, np.float32(1e-5)), np.float32(0.0)).astype(np.float32)


def _robust_z(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    fp = np.asarray(footprint, dtype=bool)
    vals = arr[fp & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75.0) - np.percentile(vals, 25.0))
    scale = max(iqr / 1.3489795, float(np.std(vals)), 1e-6)
    z = (arr.astype(np.float32) - np.float32(med)) / np.float32(scale)
    return np.where(fp & np.isfinite(arr), np.clip(z, -8.0, 8.0), np.float32(0.0)).astype(np.float32)


def compute_hvfd_static_from_arrays(
    *,
    b2_rtp: np.ndarray,
    b4_geod_inv: np.ndarray,
    b7_shear: np.ndarray,
    b8_dilate: np.ndarray,
    b9_tmi_vg: np.ndarray,
    b10_deq: np.ndarray,
    b11_grav_south: np.ndarray,
    b12_det_elev: np.ndarray,
    b15_depth_base: np.ndarray,
    b16_eq: np.ndarray,
    b17_cond: np.ndarray,
    b18_grav_east: np.ndarray,
    b19_slope: np.ndarray,
    t2m_wall_plume: np.ndarray,
    sinter_halo: np.ndarray,
    upslope_geotherm: np.ndarray,
    volc_vent_halo: np.ndarray,
    rad_kth_uth: np.ndarray,
    lidar_dem10_chi: np.ndarray,
    pluvial_seam_mimic: np.ndarray,
    footprint: np.ndarray,
    sigma_grav_px: float = 4.5,
    sigma_flank_px: float = 12.0,
) -> dict[str, np.ndarray]:
    """Compute the 13 catalogue-blind HVFD static planes from in-memory 2D arrays."""
    fp = np.asarray(footprint, dtype=bool)

    # 1. Hydrothermal vent & alteration planes
    t2m_r = rank01(np.asarray(t2m_wall_plume, dtype=np.float32), fp)
    sinter_r = rank01(
        0.80 * np.asarray(sinter_halo, dtype=np.float32) + 0.20 * np.asarray(volc_vent_halo, dtype=np.float32),
        fp,
    )
    geoth_r = rank01(np.asarray(upslope_geotherm, dtype=np.float32), fp)

    c17, w17 = _clean_band(b17_cond, fp)
    cond_sm = _smooth_masked(c17, w17, 2.0)
    cond_gy = ndi.gaussian_filter(cond_sm, sigma=2.0, order=(1, 0), mode="nearest")
    cond_gx = ndi.gaussian_filter(cond_sm, sigma=2.0, order=(0, 1), mode="nearest")
    cond_grad = np.hypot(cond_gy, cond_gx)
    del cond_gy, cond_gx
    cond_hi = np.maximum(cond_sm - _smooth_masked(c17, w17, 16.0), 0.0)
    del c17, w17, cond_sm
    clay_rad = (
        0.45 * rank01(cond_grad, fp)
        + 0.25 * rank01(cond_hi, fp)
        + 0.30 * rank01(np.asarray(rad_kth_uth, dtype=np.float32), fp)
    ).astype(np.float32)
    del cond_grad, cond_hi
    clay_rad_r = rank01(clay_rad, fp)
    del clay_rad

    v_vent = rank01(
        0.32 * t2m_r + 0.26 * sinter_r + 0.24 * geoth_r + 0.18 * clay_rad_r,
        fp,
    )
    gc.collect()

    # 2. Bi-harmonic basement plate flexure |nabla^4 z_b| + Laplace g_zz + Poisson magnetite destruction
    c15, w15 = _clean_band(b15_depth_base, fp)
    dtb_sm = _smooth_masked(c15, w15, 2.5)
    del c15, w15
    lap_zb = (
        ndi.gaussian_filter(dtb_sm, sigma=2.2, order=(2, 0), mode="nearest")
        + ndi.gaussian_filter(dtb_sm, sigma=2.2, order=(0, 2), mode="nearest")
    ).astype(np.float32)
    biharm_zb = np.abs(
        ndi.gaussian_filter(lap_zb, sigma=2.2, order=(2, 0), mode="nearest")
        + ndi.gaussian_filter(lap_zb, sigma=2.2, order=(0, 2), mode="nearest")
    ).astype(np.float32)
    del lap_zb
    grad_zb = np.hypot(
        ndi.gaussian_filter(dtb_sm, sigma=2.0, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(dtb_sm, sigma=2.0, order=(0, 1), mode="nearest"),
    ).astype(np.float32)
    del dtb_sm
    biharm_flex = rank01(0.55 * rank01(biharm_zb, fp) + 0.45 * rank01(grad_zb, fp), fp)
    del biharm_zb, grad_zb
    gc.collect()

    c11, w11 = _clean_band(b11_grav_south, fp)
    c18, w18 = _clean_band(b18_grav_east, fp)
    w_grav = np.minimum(w11, w18)
    del w11, w18
    g_east = _smooth_masked(c18, w_grav, sigma_grav_px)
    g_south = _smooth_masked(c11, w_grav, sigma_grav_px)
    del c11, c18
    dg_east_dcol = (g_east[:, np.r_[1:g_east.shape[1], g_east.shape[1] - 1]] - g_east[:, np.r_[0, 0:g_east.shape[1] - 1]]) * 0.5
    dg_south_drow = (g_south[np.r_[1:g_south.shape[0], g_south.shape[0] - 1], :] - g_south[np.r_[0, 0:g_south.shape[0] - 1], :]) * 0.5
    g_zz = (-(dg_east_dcol + dg_south_drow)).astype(np.float32)
    del dg_east_dcol, dg_south_drow
    g_h_mag = np.hypot(g_east, g_south).astype(np.float32)
    del g_east, g_south
    laplace_hinge = rank01(
        rank01(np.abs(g_zz), fp) * (0.35 + 0.65 * rank01(g_h_mag, fp)),
        fp,
    )
    del g_h_mag

    _, w2 = _clean_band(b2_rtp, fp)
    c9, w9 = _clean_band(b9_tmi_vg, fp)
    z_gzz = _robust_z(g_zz, fp)
    del g_zz
    z_mz = _robust_z(_smooth_masked(c9, np.minimum(w9, w2), 2.0), fp)
    del c9, w2
    mu_g = _smooth_masked(z_gzz, w_grav, sigma_flank_px)
    mu_m = _smooth_masked(z_mz, w9, sigma_flank_px)
    cov_gm = _smooth_masked((z_gzz - mu_g) * (z_mz - mu_m), np.minimum(w_grav, w9), sigma_flank_px)
    var_g = _smooth_masked((z_gzz - mu_g) ** 2, w_grav, sigma_flank_px) + np.float32(0.25)
    del w_grav, w9
    alpha_flank = np.clip(cov_gm / var_g, -2.5, 2.5).astype(np.float32)
    del cov_gm, var_g
    pred_mz = alpha_flank * (z_gzz - mu_g) + mu_m
    del alpha_flank, z_gzz, mu_g, mu_m
    poisson_dest = rank01(
        np.maximum(0.0, pred_mz - z_mz).astype(np.float32) * (0.30 + 0.70 * laplace_hinge),
        fp,
    )
    del pred_mz, z_mz

    c_pot = rank01(
        0.38 * biharm_flex + 0.34 * laplace_hinge + 0.28 * poisson_dest,
        fp,
    )
    gc.collect()

    # 3. 3DEP 1 m LiDAR / 10 m DEM / Fluvial chi scarp + Coulomb strain-seismic valve
    c19, _ = _clean_band(b19_slope, fp)
    det_r = rank01(c19, fp)
    scarp_r = rank01(
        0.75 * rank01(np.asarray(lidar_dem10_chi, dtype=np.float32), fp) + 0.25 * det_r,
        fp,
    )
    del det_r
    c4, _ = _clean_band(b4_geod_inv, fp)
    c7, _ = _clean_band(b7_shear, fp)
    c8, _ = _clean_band(b8_dilate, fp)
    c10, _ = _clean_band(b10_deq, fp)
    c16, _ = _clean_band(b16_eq, fp)
    coulomb_valve = rank01(
        0.30 * rank01(np.abs(c7), fp)
        + 0.25 * rank01(c8, fp)
        + 0.15 * rank01(c4, fp)
        + 0.15 * rank01(c16, fp)
        + 0.15 * rank01(c10, fp),
        fp,
    )
    del c4, c7, c8, c10, c16
    gc.collect()

    # 4. Non-fault mimic suppression (Lahontan/Bonneville shorelines, high-mountain ridges, GeoDAWN seams)
    c12, _ = _clean_band(b12_det_elev, fp)
    high_topo_mimic = rank01(np.maximum(c12, 0.0) * np.maximum(c19, 0.0), fp)
    del c12, c19
    mimic_supp = rank01(
        0.65 * rank01(np.asarray(pluvial_seam_mimic, dtype=np.float32), fp) + 0.35 * high_topo_mimic,
        fp,
    )
    del high_topo_mimic

    g_scarp_valve = rank01(0.68 * scarp_r + 0.32 * coulomb_valve, fp)
    raw_blind = (
        (0.36 * v_vent + 0.34 * c_pot + 0.30 * g_scarp_valve)
        * (1.0 - 0.38 * mimic_supp)
    ).astype(np.float32)
    del g_scarp_valve
    blind_conduit = rank01(raw_blind, fp)
    del raw_blind
    gc.collect()

    return {
        "t2m_thermal_wall_plume": t2m_r,
        "paleo_sinter_vent_halo": sinter_r,
        "upslope_geotherm_excess": geoth_r,
        "claycap_rad_alteration": clay_rad_r,
        "hvfd_vent_composite": v_vent,
        "biharmonic_basement_flexure": biharm_flex,
        "laplace_gzz_hinge": laplace_hinge,
        "poisson_mag_destruction": poisson_dest,
        "hvfd_potential_composite": c_pot,
        "lidar_dem10_chi_scarp": scarp_r,
        "coulomb_seismic_valve": coulomb_valve,
        "hvfd_mimic_suppression": mimic_supp,
        "hvfd_blind_conduit_surface": blind_conduit,
    }


def _parse_2m_thermal_wall_and_plume(
    zpath: Path, shape: tuple[int, int], footprint: np.ndarray
) -> np.ndarray:
    """Parse DOE GDR 1391 2m temperature probes (`F2mDAB`) and compute plume + |grad T_2m| thermal wall."""
    with zipfile.ZipFile(zpath) as zf:
        dbf = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")
        shp = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp")

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

    num = ndi.gaussian_filter(imp_anom, sigma=10.0, mode="constant")
    den = ndi.gaussian_filter((imp_cnt > 0).astype(np.float32), sigma=10.0, mode="constant")
    plume = (num / (den + 0.008)).astype(np.float32)

    # Lateral thermal-wall gradient |grad T_2m| at sigma = 4.0 px (400 m)
    ty = ndi.gaussian_filter(plume, sigma=4.0, order=(1, 0), mode="nearest")
    tx = ndi.gaussian_filter(plume, sigma=4.0, order=(0, 1), mode="nearest")
    t_wall = np.hypot(ty, tx).astype(np.float32)
    comb = (0.55 * rank01(t_wall, footprint) + 0.45 * rank01(plume, footprint)).astype(np.float32)
    comb[~footprint] = 0.0
    return comb


def _parse_paleo_sinter(zpath: Path, shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    """Parse DOE GDR 1391 paleogeothermal sinter, travertine & tufa vent deposits (726 sites)."""
    with zipfile.ZipFile(zpath) as zf:
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
    dist = ndi.distance_transform_edt(~src).astype(np.float32)
    prox = (0.65 * np.exp(-dist / 7.0) + 0.35 * np.exp(-dist / 22.0)).astype(np.float32)
    prox[~footprint] = 0.0
    return prox


def _parse_wellspring_upslope(
    cpath: Path, shape: tuple[int, int], footprint: np.ndarray, dem_mean: np.ndarray
) -> np.ndarray:
    """Read thermal wells/springs WITHOUT `dist_known_fault_px` and advect 300 m upslope."""
    allowed_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c")
    ACCESSED_CSV_COLUMNS[cpath.name] = allowed_cols
    assert not (set(allowed_cols) & BANNED_CSV_COLUMNS)

    dem_clean, dem_w = _clean_band(dem_mean, footprint)
    dem_sm = _smooth_masked(dem_clean, dem_w, 4.0)
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
        0.65 * ndi.gaussian_filter(imp, sigma=5.5, mode="constant")
        + 0.35 * ndi.gaussian_filter(imp, sigma=16.0, mode="constant")
    ).astype(np.float32)
    out[~footprint] = 0.0
    return out


def _parse_volcanic_vents(cpath: Path, shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    """Read Quaternary volcanic vents WITHOUT `dist_known_fault_px`."""
    allowed_cols = ("row", "col")
    ACCESSED_CSV_COLUMNS[cpath.name] = allowed_cols
    assert not (set(allowed_cols) & BANNED_CSV_COLUMNS)

    src = np.zeros(shape, dtype=bool)
    with cpath.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            r, c = int(row["row"]), int(row["col"])
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                src[r, c] = True
    dist = ndi.distance_transform_edt(~src).astype(np.float32)
    out = np.exp(-dist / 32.0).astype(np.float32)
    out[~footprint] = 0.0
    return out


def build_hvfd_static_features(
    feature_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Load competition + SHA-pinned GDR-1391 & USGS 3DEP/GeoDAWN inputs and compute static HVFD planes."""
    fp = np.asarray(footprint, dtype=bool)
    shape = fp.shape

    topo_man = json.loads((external_dir / "topo_10m_derived_100m_u8.manifest.json").read_text())
    bmeta = {b["band_name"]: b for b in topo_man["bands"]}
    with rasterio.open(external_dir / "topo_10m_derived_100m_u8.tif") as ds_t10:
        slope_p90_u8 = ds_t10.read(1)
        relief_u8 = ds_t10.read(5)
        curv_u8 = ds_t10.read(6)
        asp_coh_u8 = ds_t10.read(7)
        hs_lin_u8 = ds_t10.read(8)
        dem_u8 = ds_t10.read(9)

    def _dequant(u8: np.ndarray, bname: str) -> np.ndarray:
        lo, hi = float(bmeta[bname]["lo"]), float(bmeta[bname]["hi"])
        v = lo + ((np.clip(u8.astype(np.float32), 1.0, 255.0) - 1.0) / 254.0) * (hi - lo)
        return np.where((u8 > 0) & fp, v, np.nan).astype(np.float32)

    dem_mean = _dequant(dem_u8, "dem_mean")
    relief_local = _dequant(relief_u8, "relief_local")

    t2m_wall_plume = _parse_2m_thermal_wall_and_plume(
        external_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip", shape, fp
    )
    sinter_halo = _parse_paleo_sinter(external_dir / "paleo_geothermal_regional.zip", shape, fp)
    upslope_geotherm = _parse_wellspring_upslope(
        external_dir / "gdr_wellspring_in_footprint.csv", shape, fp, dem_mean
    )
    volc_vent_halo = _parse_volcanic_vents(
        external_dir / "gdr_volcanic_vents_in_footprint.csv", shape, fp
    )

    with rasterio.open(external_dir / "geodawn_rad_u8.tif") as ds_rad:
        k_u8 = ds_rad.read(1).astype(np.float32)
        th_u8 = ds_rad.read(2).astype(np.float32)
        u_u8 = ds_rad.read(3).astype(np.float32)
    rad_valid = fp & (k_u8 > 0) & (th_u8 > 0) & (u_u8 > 0)
    kth = np.where(rad_valid, k_u8 / (th_u8 + 8.0), 0.0).astype(np.float32)
    uth = np.where(rad_valid, u_u8 / (th_u8 + 8.0), 0.0).astype(np.float32)
    kth_anom = np.maximum(
        ndi.gaussian_filter(kth, sigma=1.8, mode="nearest") - ndi.gaussian_filter(kth, sigma=14.0, mode="nearest"),
        0.0,
    )
    uth_grad = np.hypot(
        ndi.gaussian_filter(uth, sigma=1.8, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(uth, sigma=1.8, order=(0, 1), mode="nearest"),
    )
    rad_kth_uth = (0.55 * rank01(kth_anom, fp) + 0.45 * rank01(uth_grad, fp)).astype(np.float32)
    del k_u8, th_u8, u_u8, rad_valid, kth, uth, kth_anom, uth_grad

    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_ex = ds_lid.read(1).astype(np.float32)
        lid_step = ds_lid.read(3).astype(np.float32)
        lid_down = ds_lid.read(6).astype(np.float32)
        lid_valid = (ds_lid.read(12) > 0) & fp
    lid_comp = np.where(lid_valid, (0.45 * lid_ex + 0.35 * lid_step + 0.20 * lid_down) / 255.0, 0.0).astype(np.float32)
    del lid_ex, lid_step, lid_down, lid_valid
    lid_r = rank01(lid_comp, fp)
    del lid_comp

    with rasterio.open(external_dir / "dem10_chi_100m_i16.tif") as ds_chi:
        step_max = np.maximum(ds_chi.read(1).astype(np.float32), 0.0)
        ksn_max = np.maximum(ds_chi.read(3).astype(np.float32), 0.0)
    chi_comp = (0.55 * rank01(step_max, fp) + 0.45 * rank01(ksn_max, fp)).astype(np.float32)
    del step_max, ksn_max

    curv_r = rank01(np.nan_to_num(_dequant(curv_u8, "curv_prof_absmax"), nan=0.0), fp)
    del curv_u8
    acoh_r = rank01(np.nan_to_num(_dequant(asp_coh_u8, "aspect_coherence"), nan=0.0), fp)
    del asp_coh_u8
    hslin_r = rank01(np.nan_to_num(_dequant(hs_lin_u8, "hs_lineament"), nan=0.0), fp)
    del hs_lin_u8
    slp90_r = rank01(np.nan_to_num(_dequant(slope_p90_u8, "slope_p90"), nan=0.0), fp)
    del slope_p90_u8
    dem10_comp = (0.35 * curv_r + 0.25 * acoh_r + 0.25 * hslin_r + 0.15 * slp90_r).astype(np.float32)
    del curv_r, acoh_r, hslin_r, slp90_r
    lidar_dem10_chi = (0.42 * lid_r + 0.33 * dem10_comp + 0.25 * chi_comp).astype(np.float32)
    del lid_r, dem10_comp, chi_comp
    gc.collect()

    # Pluvial shoreline highstands (Lahontan 1270, 1332 m; Bonneville 1463, 1552 m) + GeoDAWN block seams
    dem_clean, _ = _clean_band(np.nan_to_num(dem_mean, nan=1400.0), fp)
    rel_clean, _ = _clean_band(np.nan_to_num(relief_local, nan=30.0), fp)
    del dem_mean, relief_local, dem_u8, relief_u8
    shore = np.zeros(shape, dtype=np.float32)
    for z_hs in (1270.0, 1332.0, 1463.0, 1552.0):
        np.maximum(shore, np.exp(-0.5 * ((dem_clean - z_hs) / 16.0) ** 2).astype(np.float32), out=shore)
    shore *= np.exp(-np.maximum(rel_clean, 0.0) / 32.0).astype(np.float32)
    del dem_clean, rel_clean

    with rasterio.open(external_dir / "acquisition_block_id_100m.tif") as ds_blk:
        blk = ds_blk.read(1)
    seam = (ndi.maximum_filter(blk, size=3) != ndi.minimum_filter(blk, size=3)) & (blk > 0)
    del blk
    seam_halo = np.exp(-ndi.distance_transform_edt(~seam).astype(np.float32) / 3.0).astype(np.float32)
    del seam
    pluvial_seam_mimic = (0.65 * shore + 0.35 * seam_halo).astype(np.float32)
    del shore, seam_halo
    gc.collect()

    return compute_hvfd_static_from_arrays(
        b2_rtp=_LazyBand(feature_tif, 2),
        b4_geod_inv=_LazyBand(feature_tif, 4),
        b7_shear=_LazyBand(feature_tif, 7),
        b8_dilate=_LazyBand(feature_tif, 8),
        b9_tmi_vg=_LazyBand(feature_tif, 9),
        b10_deq=_LazyBand(feature_tif, 10),
        b11_grav_south=_LazyBand(feature_tif, 11),
        b12_det_elev=_LazyBand(feature_tif, 12),
        b15_depth_base=_LazyBand(feature_tif, 15),
        b16_eq=_LazyBand(feature_tif, 16),
        b17_cond=_LazyBand(feature_tif, 17),
        b18_grav_east=_LazyBand(feature_tif, 18),
        b19_slope=_LazyBand(feature_tif, 19),
        t2m_wall_plume=t2m_wall_plume,
        sinter_halo=sinter_halo,
        upslope_geotherm=upslope_geotherm,
        volc_vent_halo=volc_vent_halo,
        rad_kth_uth=rad_kth_uth,
        lidar_dem10_chi=lidar_dem10_chi,
        pluvial_seam_mimic=pluvial_seam_mimic,
        footprint=fp,
    )


def compute_visible_trap_fields(
    visible: np.ndarray,
    footprint: np.ndarray,
    v_vent: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible structural stress-transfer traps (clamped at d_vis >= 3.5 px)."""
    vis = np.asarray(visible, dtype=bool)
    fp = np.asarray(footprint, dtype=bool)
    H, W = vis.shape
    if not vis.any():
        zeros = np.zeros((H, W), dtype=np.float32)
        return {name: zeros.copy() for name in TRAP_FEATURE_NAMES}

    strike_vis, _ = NET.local_strike(vis, smooth_px=3.0)
    seg, n_seg = NET.segments(vis, max_len_px=12)[:2]
    tab = NET.segment_table(seg, n_seg)
    comp, ncomp = ndi.label(vis, structure=NET.STRUCT3)
    comp_len = np.bincount(comp.ravel(), minlength=ncomp + 1).astype(np.float32)

    d, iy, ix = NET.nearest_frame(vis)
    rows_grid, cols_grid = np.indices((H, W), dtype=np.int32)
    dy = (rows_grid - iy).astype(np.float32)
    dx = (cols_grid - ix).astype(np.float32)
    del rows_grid, cols_grid

    anc_seg = seg[iy, ix]
    s_anchor = strike_vis[iy, ix]
    s_seg = tab.strike[np.clip(anc_seg, 0, len(tab.strike) - 1)]
    s_host = np.where(np.isfinite(s_anchor), s_anchor, s_seg)
    s_host = np.where(np.isfinite(s_host), s_host, 0.0).astype(np.float32)
    del strike_vis, seg, anc_seg, s_anchor, s_seg

    d_par, d_perp, _ = NET.offset_components(dy.ravel(), dx.ravel(), s_host.ravel())
    d_par_abs = np.abs(d_par).reshape(H, W).astype(np.float32)
    d_perp_2d = d_perp.reshape(H, W).astype(np.float32)
    del dy, dx, d_par, d_perp, s_host

    ln = comp_len[np.clip(comp[iy, ix], 0, len(comp_len) - 1)]
    del comp, comp_len, d, iy, ix

    tip_gate = np.clip((d_par_abs - 0.5) / 1.5, 0.0, 1.0)
    cross_beam = np.exp(-0.5 * (d_perp_2d / 2.2) ** 2)
    along_decay = np.exp(-np.maximum(d_par_abs, 3.5) / 18.0)
    vis_tip = (tip_gate * cross_beam * along_decay * np.minimum(np.log1p(ln) / 4.5, 1.5)).astype(np.float32)
    vis_tip[~fp | vis] = 0.0
    del d_par_abs, d_perp_2d, tip_gate, cross_beam, along_decay, ln
    gc.collect()

    f2 = RBA.two_host_frame(vis)
    bf = RBA.host_bend_fields(vis)
    act_ys, act_xs = np.nonzero(fp & ~vis)
    d1 = f2["d1"][act_ys, act_xs]
    d2 = f2["d2"][act_ys, act_xs]
    ay1 = f2["iy1"][act_ys, act_xs]
    ax1 = f2["ix1"][act_ys, act_xs]
    ay2 = f2["iy2"][act_ys, act_xs]
    ax2 = f2["ix2"][act_ys, act_xs]

    dy1 = (act_ys - ay1).astype(np.float32)
    dx1 = (act_xs - ax1).astype(np.float32)
    dy2 = (act_ys - ay2).astype(np.float32)
    dx2 = (act_xs - ax2).astype(np.float32)
    facing = np.clip(-(dy1 * dy2 + dx1 * dx2) / np.maximum(d1 * d2, 1e-6), 0.0, 1.0)
    ratio = 2.0 * np.clip(d1 / np.maximum(d1 + d2, 1e-6), 0.0, 0.5)
    span_clamp = np.maximum(d1 + d2, 7.0)

    vis_relay = np.zeros((H, W), dtype=np.float32)
    vis_relay[act_ys, act_xs] = ((facing**2) * ratio * np.exp(-span_clamp / 28.0)).astype(np.float32)

    turn1 = bf["turn"][ay1, ax1]
    d1_clamp = np.maximum(d1, 3.5).astype(np.float32)
    vis_bend = np.zeros((H, W), dtype=np.float32)
    vis_bend[act_ys, act_xs] = (np.nan_to_num(turn1, nan=0.0) * np.exp(-d1_clamp / 18.0)).astype(np.float32)
    del f2, bf, d1, d2, ay1, ax1, ay2, ax2, dy1, dx1, dy2, dx2, facing, ratio, span_clamp, turn1, d1_clamp, act_ys, act_xs
    gc.collect()

    tip_r = rank01(vis_tip, fp)
    relay_r = rank01(vis_relay, fp)
    bend_r = rank01(vis_bend, fp)
    m_trap = np.clip(0.46 * relay_r + 0.36 * tip_r + 0.18 * bend_r, 0.0, 1.0).astype(np.float32)
    m_trap[~fp | vis] = 0.0

    vent_x_trap = rank01(m_trap * (0.40 + 0.60 * np.asarray(v_vent, dtype=np.float32)), fp)
    vent_x_trap[vis] = 0.0

    return {
        "vis_tip_cone": tip_r,
        "vis_relay_bridge": relay_r,
        "vis_bend_hinge": bend_r,
        "vis_vent_x_trap": vent_x_trap,
        "vis_trap_composite": m_trap,
    }


def compose_hvfd_surface(
    p_blind: np.ndarray,
    v_vent: np.ndarray,
    m_trap: np.ndarray,
    footprint: np.ndarray,
) -> np.ndarray:
    """Dual-Regime Noisy-OR Discovery Posterior coupling blind conduit physics with visible traps."""
    fp = np.asarray(footprint, dtype=bool)
    pb = np.where(fp & np.isfinite(p_blind), np.clip(p_blind, 0.0, 1.0), 0.0).astype(np.float32)
    vv = np.where(fp & np.isfinite(v_vent), np.clip(v_vent, 0.0, 1.0), 0.0).astype(np.float32)
    mt = np.where(fp & np.isfinite(m_trap), np.clip(m_trap, 0.0, 1.0), 0.0).astype(np.float32)

    p_link = np.clip(np.power(pb, 0.58) * mt * (0.75 + 0.25 * vv), 0.0, 1.0)
    p_distal = np.clip(0.55 * np.power(pb, 1.35) * (0.65 + 0.35 * vv), 0.0, 1.0)
    surf = (1.0 - (1.0 - p_link) * (1.0 - p_distal)).astype(np.float32)
    surf[~fp] = 0.0
    return surf


def disc_thin_prefix(
    score: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    radius_px: float = 2.8,
) -> np.ndarray:
    """Greedy Euclidean inhibition-disc thinning (r=2.8 px) selecting up to ``budget`` unit dots."""
    H_h, W_w = score.shape
    mask = np.asarray(allowed, dtype=bool) & np.isfinite(score) & (score > 0.0)
    ys, xs = np.nonzero(mask)
    if ys.size == 0 or budget <= 0:
        return np.zeros((H_h, W_w), dtype=bool)

    vals = score[ys, xs]
    # Deterministic tie-breaking: descending score, then ascending row, then ascending col
    order = np.lexsort((xs, ys, -vals))
    ys = ys[order]
    xs = xs[order]

    ir = int(np.ceil(radius_px))
    dy_g, dx_g = np.mgrid[-ir : ir + 1, -ir : ir + 1]
    in_disc = (dy_g * dy_g + dx_g * dx_g) <= (radius_px * radius_px + 1e-6)
    dy_d = dy_g[in_disc]
    dx_d = dx_g[in_disc]

    blocked = np.zeros((H_h, W_w), dtype=bool)
    dots = np.zeros((H_h, W_w), dtype=bool)
    cnt = 0
    for i in range(ys.size):
        if cnt >= budget:
            break
        y, x = int(ys[i]), int(xs[i])
        if blocked[y, x]:
            continue
        dots[y, x] = True
        cnt += 1
        ny = y + dy_d
        nx = x + dx_d
        ok = (ny >= 0) & (ny < H_h) & (nx >= 0) & (nx < W_w)
        blocked[ny[ok], nx[ok]] = True
    return dots
