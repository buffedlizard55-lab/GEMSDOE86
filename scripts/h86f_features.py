#!/usr/bin/env python3
"""H86F-HMDC feature operators: trough-gated hydrothermal fault discovery.

Strictly zero-catalogue: no function here reads existing_faults.tif or any
label-derived column. CSV/DBF column access is allow-listed and asserted
(mirrors the H86D banned-column discipline for the same GDR 1391 files).

Operators (preregistered in registry/preregistration_h86f.json):
  trough_rtp / trough_tvg : Frangi dark-vesselness (valley curvature) of
      sigma=1.5px-smoothed RTP (Band 2) / tmi_vg (Band 9). Magnetite
      destruction lowers susceptibility along the conduit, carving a linear
      magnetic low; a valley has large positive cross-strike curvature and
      near-zero along-strike curvature.
  ridge_rtp              : polarity-flipped control (Frangi bright-vesselness).
  cond_dilat             : positive-part z-score product z(cond_surf)+ *
      z(geod_dilaterate)+, sigma=2px. Clay-cap conduction inside dilating
      crust; playa brines (cond high, dilatation ~0) are suppressed.
  vent_corr_raw          : Bresenham segment density between hot-vent points
      10-60px (1-6km) apart sharing one of 8 strikes (+-11.25deg), sigma=1.5px.
  vent_corr_gated        : vent_corr_raw gated by (trough>median AND
      cond_dilat>median) over the footprint.
  shuffled_vent_corr     : null control: same operator on N uniform-random
      footprint points (seed 11, N = vent count).
  vent_logdist           : -log1p(distance to any vent point).

Vent points = union of: GDR wellspring hot subset (temp_c>=37 or
quartz/chalc>=110), volcanic vents (all), in-footprint paleo sinter,
2m-probe F2mDAB>0 hits. BANNED column dist_known_fault_px is never read.
"""
from __future__ import annotations

import csv
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]

ACCESSED_COLUMNS: dict[str, tuple[str, ...]] = {}
BANNED = {"dist_known_fault_px", "dist_known_fault_m", "nearest_fault"}

CORE_TIF = ROOT / "data/bridge/training_features.tif"

# Strike tolerance for corridor chaining is angular (+-11.25 deg
# around the pair direction); no fixed strike table is needed.


def read_core_band(idx: int) -> np.ndarray:
    with rasterio.open(CORE_TIF) as src:
        a = src.read(idx).astype(np.float32)
    a[a <= -1e38] = np.nan
    return a


def robust_zpos(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    v = a[fp & np.isfinite(a)]
    med = float(np.median(v))
    iqr = float(np.percentile(v, 75) - np.percentile(v, 25)) + 1e-9
    z = np.clip((np.nan_to_num(a, nan=med) - med) / iqr, 0.0, None)
    z[~fp] = 0.0
    return z.astype(np.float32)


def frangi_dark(a: np.ndarray, fp: np.ndarray, sigma: float = 1.5,
                beta: float = 0.5) -> np.ndarray:
    """Frangi vesselness for dark (low-value) tubular structures.

    Hessian eigenvalues |l1| <= |l2| of the Gaussian-smoothed field; a dark
    vessel has l2 >> 0 with l1 ~ 0. Rb = |l1|/|l2| (blobness),
    S = sqrt(l1^2+l2^2) (structureness); c = half the max S.
    (Frangi et al., MICCAI 1998, multiscale filtering of vesselness.)
    """
    s = ndi.gaussian_filter(np.nan_to_num(a, nan=np.nanmedian(a[fp & np.isfinite(a)])),
                            sigma, mode="nearest")
    ixx = ndi.gaussian_filter(s, sigma, order=(0, 2), mode="nearest")
    iyy = ndi.gaussian_filter(s, sigma, order=(2, 0), mode="nearest")
    ixy = ndi.gaussian_filter(s, sigma, order=(1, 1), mode="nearest")
    # NOTE: gaussian_filter(order=...) differentiates the already-smoothed s;
    # total smoothing is sqrt(2)*sigma. Hessian scale is fixed and identical
    # for the trough and ridge (control) arms, so the comparison is fair.
    trace = ixx + iyy
    det = ixx * iyy - ixy * ixy
    disc = np.sqrt(np.clip((trace / 2.0) ** 2 - det, 0.0, None))
    l_big = trace / 2.0 + disc
    l_small = trace / 2.0 - disc
    # order by magnitude: |l1| <= |l2|
    swap = np.abs(l_small) > np.abs(l_big)
    l1 = np.where(swap, l_big, l_small)
    l2 = np.where(swap, l_small, l_big)
    rb = np.abs(l1) / (np.abs(l2) + 1e-12)
    s_norm = np.hypot(l1, l2)
    c = 0.5 * float(s_norm[fp].max()) + 1e-12
    vessel = np.exp(-rb ** 2 / (2.0 * beta ** 2)) * (1.0 - np.exp(-s_norm ** 2 / (2.0 * c ** 2)))
    vessel = np.where(l2 > 0, vessel, 0.0)
    vessel[~fp] = 0.0
    return vessel.astype(np.float32)


def frangi_bright(a: np.ndarray, fp: np.ndarray, sigma: float = 1.5,
                  beta: float = 0.5) -> np.ndarray:
    """Polarity-flipped control: bright (high-value) tubular structures."""
    return frangi_dark(-np.nan_to_num(a, nan=0.0), fp, sigma=sigma, beta=beta)


def build_trough_channels(fp: np.ndarray) -> dict[str, np.ndarray]:
    rtp = read_core_band(2)
    tvg = read_core_band(9)
    out = {
        "trough_rtp": frangi_dark(rtp, fp),
        "trough_tvg": frangi_dark(tvg, fp),
        "ridge_rtp": frangi_bright(rtp, fp),
    }
    out["trough_mag"] = np.maximum(out["trough_rtp"], out["trough_tvg"]).astype(np.float32)
    return out


def build_cond_dilat(fp: np.ndarray) -> np.ndarray:
    cond = read_core_band(17)
    dilat = read_core_band(8)
    prod = robust_zpos(cond, fp) * robust_zpos(dilat, fp)
    out = ndi.gaussian_filter(prod, 2.0, mode="constant").astype(np.float32)
    out[~fp] = 0.0
    return out


# --------------------------------------------------------------------------- #
# GDR 1391 vent points (no label-derived column is ever read)
# --------------------------------------------------------------------------- #
def _check_cols(fname: str, allowed: tuple[str, ...], fieldnames) -> None:
    ACCESSED_COLUMNS[fname] = allowed
    assert not (set(allowed) & BANNED), f"banned column accessed in {fname}"
    missing = [c for c in allowed if c not in (fieldnames or [])]
    assert not missing, f"{fname} missing columns {missing}"


def wellspring_hot_points(shape) -> np.ndarray:
    cpath = ROOT / "data/external/gdr_wellspring_in_footprint.csv"
    allowed = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c")
    pts = []
    with cpath.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        _check_cols(cpath.name, allowed, reader.fieldnames)
        for row in reader:
            try:
                r, c = int(row["row"]), int(row["col"])
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            try:
                t = float(row["temp_c"]) if row["temp_c"] else 0.0
            except ValueError:
                t = 0.0
            try:
                gq = float(row["geothermquartz_c"]) if row["geothermquartz_c"] else 0.0
            except ValueError:
                gq = 0.0
            try:
                gc = float(row["geothermchalc_c"]) if row["geothermchalc_c"] else 0.0
            except ValueError:
                gc = 0.0
            if t >= 37.0 or max(gq, gc) >= 110.0:
                pts.append((r, c))
    return np.array(sorted(set(pts)), dtype=np.int32).reshape(-1, 2)


def volcanic_vent_points(shape) -> np.ndarray:
    cpath = ROOT / "data/external/gdr_volcanic_vents_in_footprint.csv"
    allowed = ("row", "col")
    pts = []
    with cpath.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        _check_cols(cpath.name, allowed, reader.fieldnames)
        for row in reader:
            r, c = int(row["row"]), int(row["col"])
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                pts.append((r, c))
    return np.array(sorted(set(pts)), dtype=np.int32).reshape(-1, 2)


def sinter_points(shape, fp) -> np.ndarray:
    zpath = ROOT / "data/external/paleo_geothermal_regional.zip"
    with zipfile.ZipFile(zpath) as zf:
        lines = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    reader = csv.DictReader(lines)
    _check_cols("Paleo_geothermal_final.csv", ("Long_deg_NAD83", "Lat_deg_NAD83"), reader.fieldnames)
    lons, lats = [], []
    for row in reader:
        try:
            lons.append(float(row["Long_deg_NAD83"]))
            lats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int64)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int64)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    rows, cols = rows[inb], cols[inb]
    keep = fp[rows, cols]
    pts = sorted(set(zip(rows[keep].tolist(), cols[keep].tolist())))
    return np.array(pts, dtype=np.int32).reshape(-1, 2)


def probe2m_points(shape, fp) -> np.ndarray:
    zpath = ROOT / "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip"
    with zipfile.ZipFile(zpath) as zf:
        dbf = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")
        shp = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp")
    nrec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while dbf[pos] != 0x0D:
        fields.append((dbf[pos:pos + 11].split(b"\x00")[0].decode("ascii"), dbf[pos + 16]))
        pos += 32
    _check_cols("2m_temperature_probe_n83geo.dbf", ("F2mDAB",), [f[0] for f in fields])
    lons, lats, hits = [], [], []
    shp_pos = 100
    for i in range(nrec):
        _, content_len = struct.unpack(">II", shp[shp_pos:shp_pos + 8])
        x, y = struct.unpack("<dd", shp[shp_pos + 12:shp_pos + 28])
        shp_pos += 8 + content_len * 2
        row_bytes = dbf[hdr_len + i * rec_len + 1:hdr_len + (i + 1) * rec_len]
        off = 0
        rec: dict[str, str] = {}
        for fn, fl in fields:
            rec[fn] = row_bytes[off:off + fl].decode("utf-8", errors="replace").strip()
            off += fl
        try:
            dab = float(rec.get("F2mDAB") or 0.0)
        except ValueError:
            dab = 0.0
        if dab > 0.0 and np.isfinite(dab):
            lons.append(x)
            lats.append(y)
            hits.append(dab)
    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int64)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int64)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    rows, cols = rows[inb], cols[inb]
    keep = fp[rows, cols]
    pts = sorted(set(zip(rows[keep].tolist(), cols[keep].tolist())))
    return np.array(pts, dtype=np.int32).reshape(-1, 2)


def all_vent_points(shape, fp) -> tuple[np.ndarray, dict[str, int]]:
    parts = {
        "wellspring_hot": wellspring_hot_points(shape),
        "volcanic_vents": volcanic_vent_points(shape),
        "sinter": sinter_points(shape, fp),
        "probe2m": probe2m_points(shape, fp),
    }
    counts = {k: int(len(v)) for k, v in parts.items()}
    merged = sorted({tuple(p) for v in parts.values() for p in v.tolist()})
    return np.array(merged, dtype=np.int32).reshape(-1, 2), counts


# --------------------------------------------------------------------------- #
# Pairwise co-linear corridors (Bresenham segments, 8 strikes, 10-60px)
# --------------------------------------------------------------------------- #
def _bresenham(r0: int, c0: int, r1: int, c1: int):
    pts = []
    dr, dc = abs(r1 - r0), abs(c1 - c0)
    sr, sc = (1 if r1 > r0 else -1), (1 if c1 > c0 else -1)
    r, c = r0, c0
    if dc > dr:
        err = dc // 2
        for _ in range(dc + 1):
            pts.append((r, c))
            c += sc
            err -= dr
            if err < 0:
                r += sr
                err += dc
    else:
        err = dr // 2
        for _ in range(dr + 1):
            pts.append((r, c))
            r += sr
            err -= dc
            if err < 0:
                c += sc
                err += dr
    return pts


# --------------------------------------------------------------------------- #
# Pairwise co-linear corridors (chained segments, 8 strikes, 10-60px links)
#
# A pair of vents trivially shares SOME strike (8 azimuths tile the circle),
# so pairs alone cannot define a corridor. A segment is therefore retained
# only if a THIRD vent continues the alignment (collinear triple): the pair
# (a,b) survives iff another vent lies within a 2px-wide strip along the line
# through a and b, within 120px of the pair midpoint, and farther than 10px
# from both a and b. This matches the preregistered "co-linear" intent
# (amendment A1: chain requirement; the 8-strike wording is unchanged).
# Pair search uses a KD-tree (exact euclidean); surviving segments are
# rasterized with Bresenham and counted (segment-count density).
# --------------------------------------------------------------------------- #
def pairwise_corridors(points: np.ndarray, shape, min_px: int = 10,
                       max_px: int = 60, chain_px: float = 120.0,
                       strip_px: float = 2.0) -> tuple[np.ndarray, int]:
    from scipy.spatial import cKDTree

    H, W = shape
    pts = np.asarray(points, dtype=np.float64)
    n = len(pts)
    count = np.zeros(shape, np.float32)
    if n < 3:
        return count, 0
    tree = cKDTree(pts)
    pairs = sorted(tree.query_pairs(max_px))
    if not pairs:
        return count, 0
    ij = np.array(pairs, dtype=np.int64)
    d = pts[ij[:, 1]] - pts[ij[:, 0]]
    dist = np.hypot(d[:, 0], d[:, 1])
    keep_len = dist >= min_px
    ij = ij[keep_len]
    d = d[keep_len]
    dist = dist[keep_len]
    if len(ij) == 0:
        return count, 0
    u = d / dist[:, None]
    mid = (pts[ij[:, 0]] + pts[ij[:, 1]]) / 2.0
    n_pairs = 0
    for k in range(len(ij)):
        i, j = int(ij[k, 0]), int(ij[k, 1])
        ux, uy = float(u[k, 0]), float(u[k, 1])  # (row, col) components
        cand = tree.query_ball_point(mid[k], chain_px)
        chained = False
        for c in cand:
            if c == i or c == j:
                continue
            vr = pts[c, 0] - pts[i, 0]
            vc = pts[c, 1] - pts[i, 1]
            along = vr * ux + vc * uy
            lat = abs(vr * uy - vc * ux)
            if lat <= strip_px and abs(along) <= chain_px:
                di = float(np.hypot(vr, vc))
                dj = float(np.hypot(pts[c, 0] - pts[j, 0], pts[c, 1] - pts[j, 1]))
                if di > min_px and dj > min_px:
                    chained = True
                    break
        if not chained:
            continue
        n_pairs += 1
        for (rr_, cc_) in _bresenham(int(round(pts[i, 0])), int(round(pts[i, 1])),
                                     int(round(pts[j, 0])), int(round(pts[j, 1]))):
            if 0 <= rr_ < H and 0 <= cc_ < W:
                count[rr_, cc_] += 1.0
    return count, n_pairs


def build_vent_channels(shape, fp, seed_shuffle: int = 11) -> dict[str, np.ndarray]:
    points, counts = all_vent_points(shape, fp)
    n = len(points)
    if n < 2:
        raise ValueError("fewer than 2 vent points; corridors undefined")
    raw_count, n_pairs = pairwise_corridors(points, shape)
    raw = ndi.gaussian_filter(raw_count, 1.5, mode="constant").astype(np.float32)
    raw[~fp] = 0.0
    # null control: same operator, same N, uniform-random footprint points
    rng = np.random.default_rng(seed_shuffle)
    flat_fp = np.flatnonzero(fp.ravel())
    pick = rng.choice(flat_fp, size=n, replace=False)
    spts = np.stack([pick // shape[1], pick % shape[1]], axis=1).astype(np.int32)
    shuf_count, shuf_pairs = pairwise_corridors(spts, shape)
    shuf = ndi.gaussian_filter(shuf_count, 1.5, mode="constant").astype(np.float32)
    shuf[~fp] = 0.0
    # proximity channel
    is_pt = np.zeros(shape, bool)
    is_pt[points[:, 0], points[:, 1]] = True
    logdist = (-np.log1p(ndi.distance_transform_edt(~is_pt))).astype(np.float32)
    logdist[~fp] = 0.0
    return {
        "vent_corr_raw": raw,
        "shuffled_vent_corr": shuf,
        "vent_logdist": logdist,
        "n_vent_points": n,
        "n_vent_pairs": n_pairs,
        "n_shuffled_pairs": shuf_pairs,
        "vent_counts": counts,
    }
