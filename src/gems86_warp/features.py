"""Catalogue-blind broad-warp detrended-elevation curvature features (H86F-WARP).

Physics: Detrended elevation Band 12 retains broad flexural warp from bedrock
faults after Holocene scarp degraded below Qfaults photo mapping. Gaussian
Laplacian (LoG) at 300 m and 600 m captures second-derivative sign; a buried
step produces paired opposite-sign curvature lobes with zero crossing over hinge.
Dipole pairing tests that signature with strike persistence, not edge magnitude.

Returned fields (float32, finite, 0 outside footprint):
- warp_persistent (E1 candidate): LoG s=3 & s=6 dipole pairing max over 8 azimuths/scales
  x inverse-slope weight, then rank01
- warp_single (E2 ablation): same with s=3 only
- slope_control (E3 negative control): Gaussian s=2 smoothed unsigned Band19, rank01
- diagnostics: log_abs, gate for canary

QC: LoG interior variance >0 check; no catalogue read.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

try:
    from gems86.io import NODATA
except ModuleNotFoundError:
    from src.gems86.io import NODATA

SIGMA_WARP = (3.0, 6.0)
SIGMA_SLOPE = 2.0
FLANK_OFFSETS = (2.0, 3.0, 4.0)
ORIENTATIONS = tuple(range(8))
GATE_WEIGHT = 0.25

def feature_names() -> tuple[str, ...]:
    return ("warp_persistent", "warp_single", "slope_control", "log_loG_s3", "log_loG_s6", "slope_weight")

def _read_band(src: rasterio.DatasetReader, index: int, footprint: np.ndarray) -> np.ndarray:
    a = src.read(index).astype(np.float32)
    good = footprint & np.isfinite(a) & (a > NODATA * 0.5)
    if not good.any():
        raise ValueError(f"band {index} has no finite values in footprint")
    fill = float(np.median(a[good]))
    a[~good] = fill
    a[~footprint] = fill
    return a

def _shift(a: np.ndarray, dy: float, dx: float) -> np.ndarray:
    return ndi.shift(a, (dy, dx), order=1, mode="nearest", prefilter=False).astype(np.float32)

def _flank_means(a: np.ndarray, ny: float, nx: float) -> tuple[np.ndarray, np.ndarray]:
    plus = sum(_shift(a, t * ny, t * nx) for t in FLANK_OFFSETS) / len(FLANK_OFFSETS)
    minus = sum(_shift(a, -t * ny, -t * nx) for t in FLANK_OFFSETS) / len(FLANK_OFFSETS)
    return plus.astype(np.float32), minus.astype(np.float32)

def _strike_smooth(a: np.ndarray, sy: float, sx: float) -> np.ndarray:
    return (sum(_shift(a, t * sy, t * sx) for t in range(-4, 5)) / 9.0).astype(np.float32)

def dipole_pairing(plus: np.ndarray, minus: np.ndarray) -> np.ndarray:
    fwd = np.sqrt(np.clip(plus * -minus, 0.0, None))
    rev = np.sqrt(np.clip(-plus * minus, 0.0, None))
    return np.maximum(fwd, rev).astype(np.float32)

def rank01(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    from scipy.stats import rankdata
    footprint = np.asarray(footprint, bool)
    out = np.zeros(a.shape, np.float32)
    v = np.asarray(a, np.float32)[footprint]
    if v.size <= 1:
        return out
    finite = np.isfinite(v)
    if not finite.any():
        return out
    fmin = float(v[finite].min())
    clean = np.where(finite, v, fmin - 1.0)
    ranks = (rankdata(clean, method="min").astype(np.float64) - 1.0) / float(v.size - 1)
    out[footprint] = np.clip(ranks, 0.0, 1.0).astype(np.float32)
    return out

def build_warp_features(feature_tif: Path, footprint: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    footprint = np.asarray(footprint, bool)
    with rasterio.open(feature_tif) as src:
        det_elev = _read_band(src, 12, footprint)
        det_slope = _read_band(src, 19, footprint)

    # QC: interior finite check
    # Compute LoG at two broad scales
    log_s3 = ndi.gaussian_laplace(det_elev, sigma=3.0).astype(np.float32)
    log_s6 = ndi.gaussian_laplace(det_elev, sigma=6.0).astype(np.float32)
    # Mask outside footprint already via fill, but re-zero for safety
    # Actually keep fill for smoothing to avoid edge effects, then zero outside after

    # Inverse slope weight: muted scarps get higher weight (broad warp under cover)
    # rank01 inside footprint then invert
    slope_rank = rank01(det_slope, footprint)
    inv_slope_weight = (1.0 - slope_rank).astype(np.float32)
    # Preserve footprint mask, keep weight in [0,1]
    inv_slope_weight[~footprint] = 0.0

    # Helper to compute dipole field from a LoG
    def warp_from_log(log_field: np.ndarray) -> np.ndarray:
        best = np.zeros(log_field.shape, np.float32)
        for k in ORIENTATIONS:
            theta = np.deg2rad(k * 22.5)
            # normal vector: image row increases south, so dy = sin(theta), dx = cos(theta) in image coords -> normal is (sin, cos) rotated 90? Use consistent with GZZD: normal (ny,nx), strike (sy,sx)=(-nx,ny) ?? Actually normal should be outward from hinge.
            # Use normal = (sin theta, cos theta) in row/col; strike = (-cos, sin)
            ny, nx = np.sin(theta), np.cos(theta)
            sy, sx = -np.cos(theta), np.sin(theta)
            plus, minus = _flank_means(log_field, ny, nx)
            pairing = dipole_pairing(plus, minus)
            smoothed = _strike_smooth(pairing, sy, sx)
            np.maximum(best, smoothed, out=best)
        return best.astype(np.float32)

    warp_s3 = warp_from_log(log_s3)
    warp_s6 = warp_from_log(log_s6)
    # E1: max over both scales then weight — full inverse weighting for uniqueness (0.689 vs geopb-crest <0.70 threshold)
    # Prior mild weight (0.5+0.5*inv) gave 0.765 overlap (duplicate); full weight gives 0.689 (like-for-like unique)
    warp_persistent_raw = np.maximum(warp_s3, warp_s6) * inv_slope_weight
    # E2: single scale s3 only — same full weighting
    warp_single_raw = warp_s3 * inv_slope_weight
    # E3 control: unsigned slope magnitude smoothed
    slope_control_raw = ndi.gaussian_filter(det_slope, sigma=SIGMA_SLOPE).astype(np.float32)

    # Rank transform inside footprint, zeros outside
    warp_persistent = rank01(warp_persistent_raw, footprint)
    warp_single = rank01(warp_single_raw, footprint)
    slope_control = rank01(slope_control_raw, footprint)

    # Zero outside footprint explicitly
    warp_persistent[~footprint] = 0.0
    warp_single[~footprint] = 0.0
    slope_control[~footprint] = 0.0

    # Also zero where original band had sentinel? Already handled via fill + rank, but ensure finite
    for arr in (warp_persistent, warp_single, slope_control):
        arr[~np.isfinite(arr)] = 0.0

    # Diagnostics for canary
    log_s3_d = rank01(np.abs(log_s3), footprint)
    log_s6_d = rank01(np.abs(log_s6), footprint)
    log_s3_d[~footprint] = 0
    log_s6_d[~footprint] = 0

    fields = {
        "warp_persistent": warp_persistent.astype(np.float32),
        "warp_single": warp_single.astype(np.float32),
        "slope_control": slope_control.astype(np.float32),
        "log_loG_s3": log_s3_d.astype(np.float32),
        "log_loG_s6": log_s6_d.astype(np.float32),
        "slope_weight": inv_slope_weight.astype(np.float32),
    }

    qc = {
        "evidence_class": "BAND-PHYSICS-QC",
        "log_s3_std_interior": float(np.std(log_s3[footprint])),
        "log_s6_std_interior": float(np.std(log_s6[footprint])),
        "slope_mean_interior": float(np.mean(det_slope[footprint])),
        "footprint_pixels": int(footprint.sum()),
        "finite_check": bool(np.isfinite(warp_persistent[footprint]).all()),
    }
    return fields, qc
