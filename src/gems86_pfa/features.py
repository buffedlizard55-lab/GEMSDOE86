"""H86P-PFA paired-flank multi-physics cross-strike asymmetry features.

Frozen in research/H86P_PFA_PREREGISTRATION.md (2026-10-26, session
5620a35f).  Label-free contract: this module reads ONLY native
training_features.tif bands (indices verified in src/gems86/io.py:BANDS)
and the footprint mask.  It never opens existing_faults.tif.
"""
from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems86.io import read_band
from gems86_ewcs.features import (
    _hessian_ridge_abs,
    _robust_standardize,
    fill_outside_footprint,
)

# 4 cross-strike axes as (row, col) unit normals; sign is irrelevant (|A| used).
AXES: tuple[tuple[float, float], ...] = (
    (0.0, 1.0), (1.0, 0.0), (0.70710678, 0.70710678), (0.70710678, -0.70710678),
)
OFFSETS_PX: tuple[float, ...] = (4.0, 7.0)
SMOOTH_SIGMA = 1.5
DISPERSION_SIGMA = 5.0
CONCORDANCE_CUT = 1.0  # raw |A|*purity units (dispersion z), frozen in prereg

PFA_FIELDS: tuple[str, ...] = ("tc", "cond_surf", "depth_to_base_surf", "iso_grav_anom", "rtp")
PFA_NAMES: tuple[str, ...] = (
    "pfa_tc", "pfa_cond", "pfa_depth", "pfa_grav", "pfa_rtp",
    "pfa_max", "pfa_second", "pfa_concordance",
)
BASELINE_NAMES: tuple[str, ...] = (
    "grav_slope_b5", "rtp_gradmag_s2", "tmi_hg_b3", "depth_gradmag_s3",
    "dem_hess_scarp_s2", "det_elev_slope_b19", "tc_gradmag_s2", "cond_gradmag_s2",
    "dilatation_hp_b8", "shear_hp_b7", "secondinv_hp_b4", "seismic_prox_exp",
)
STATIC_NAMES: tuple[str, ...] = BASELINE_NAMES + PFA_NAMES


def _local_dispersion(f: np.ndarray, fp: np.ndarray) -> np.ndarray:
    mu = ndi.gaussian_filter(f, DISPERSION_SIGMA)
    var = ndi.gaussian_filter(f * f, DISPERSION_SIGMA) - mu * mu
    disp = np.sqrt(np.maximum(var, 0.0)).astype(np.float32)
    if fp.any():
        floor = float(np.percentile(disp[fp], 25.0))
        disp = np.maximum(disp, max(floor, 1e-6)).astype(np.float32)
    return disp


def paired_flank_asymmetry(
    field: np.ndarray, fp: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Step-purity-weighted paired-flank contrast for one field.

    Returns (score, best_axis).  Per axis the score is the *cross-offset
    persistence* min(score_4px, score_7px), where
    score_d = |f(+d n) - f(-d n)| / local_dispersion * purity_d and
    purity = |f(+) - f(-)| / (|f(+) - f(-)| + |f(0) - (f(+)+f(-))/2| + eps).
    A pure step has f(0) midway between its flanks (purity -> 1) at both
    offsets.  A narrow ridge/dike crest has contrast -> 0, and its *edges*
    only mimic a step at the smaller offset (one flank lands on the crest):
    the min over offsets suppresses exactly that single-offset mimic, which
    a naive max over offsets retained (synthetic-oracle amendment A1 in the
    preregistration, made before any real-data run).
    Outside-footprint cells are exactly 0.
    """
    fp = np.asarray(fp, dtype=bool)
    f = np.asarray(field, dtype=np.float32)
    if f.shape != fp.shape:
        raise ValueError("field/footprint shape mismatch")
    fs = ndi.gaussian_filter(f, SMOOTH_SIGMA)
    disp = _local_dispersion(fs, fp)
    best = np.zeros(fp.shape, dtype=np.float32)
    best_axis = np.zeros(fp.shape, dtype=np.int8)
    for ai, (ny, nx) in enumerate(AXES):
        axis_score: np.ndarray | None = None
        for d in OFFSETS_PX:
            plus = ndi.shift(fs, shift=(d * ny, d * nx), order=1, mode="nearest")
            minus = ndi.shift(fs, shift=(-d * ny, -d * nx), order=1, mode="nearest")
            diff = plus - minus
            mid_dev = np.abs(fs - 0.5 * (plus + minus))
            purity = np.abs(diff) / (np.abs(diff) + mid_dev + 1e-9)
            score = (np.abs(diff) / disp) * purity
            axis_score = score if axis_score is None else np.minimum(axis_score, score)
            del plus, minus, diff, mid_dev, purity, score
        assert axis_score is not None
        better = axis_score > best
        best[better] = axis_score[better].astype(np.float32)
        best_axis[better] = np.int8(ai)
        del axis_score
    best[~fp] = 0.0
    best_axis[~fp] = 0
    return best.astype(np.float32), best_axis


def _gradmag(f: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(f, sigma, order=(1, 0))
    gx = ndi.gaussian_filter(f, sigma, order=(0, 1))
    return np.hypot(gx, gy).astype(np.float32)


def build_static_stack(
    feature_tif: Path, fp: np.ndarray, out_path: Path
) -> np.ndarray:
    """Build the frozen 20-plane static stack (12 baseline + 8 PFA) as float16 memmap."""
    fp = np.asarray(fp, dtype=bool)
    elev = read_band(feature_tif, "det_elev")
    valid0 = fp & np.isfinite(elev) & (np.abs(elev) < 1e20)
    _, nearest = ndi.distance_transform_edt(~valid0, return_indices=True)

    def load(name: str) -> np.ndarray:
        return fill_outside_footprint(read_band(feature_tif, name), fp, nearest)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float16,
        shape=(len(STATIC_NAMES), fp.shape[0], fp.shape[1]),
    )

    def put(name: str, arr: np.ndarray, standardize: bool = True) -> None:
        z = _robust_standardize(arr, fp) if standardize else np.where(fp, arr, 0.0).astype(np.float32)
        mm[STATIC_NAMES.index(name)] = z.astype(np.float16)
        mm.flush()

    # --- 12-plane baseline (derivatives / high-pass only, no raw levels) ---
    put("grav_slope_b5", np.maximum(load("iso_grav_anom_slope"), 0.0))
    rtp = load("rtp")
    put("rtp_gradmag_s2", _gradmag(rtp, 2.0))
    put("tmi_hg_b3", np.maximum(load("tmi_hg"), 0.0))
    depth = load("depth_to_base_surf")
    put("depth_gradmag_s3", _gradmag(depth, 3.0))
    dem = load("det_elev")
    put("dem_hess_scarp_s2", _hessian_ridge_abs(dem, 2.0))
    del dem
    put("det_elev_slope_b19", np.maximum(load("det_elev_slope"), 0.0))
    tc = load("tc")
    put("tc_gradmag_s2", _gradmag(tc, 2.0))
    cond = load("cond_surf")
    put("cond_gradmag_s2", _gradmag(cond, 2.0))
    for name, band in (("dilatation_hp_b8", "geod_dilaterate"),
                       ("shear_hp_b7", "geod_shearrate"),
                       ("secondinv_hp_b4", "geod_2ndinv")):
        f = load(band)
        put(name, f - ndi.gaussian_filter(f, 10.0))
        del f
    eq = load("deq_n100a15") > 0
    eq |= load("ieq_n100a15") > 0
    eq &= fp
    d_eq = ndi.distance_transform_edt(~eq) if eq.any() else np.full(fp.shape, 1e4, np.float32)
    put("seismic_prox_exp", np.exp(-d_eq.astype(np.float32) / 8.0), standardize=False)
    del eq, d_eq

    # --- 8-plane PFA ---
    grav = load("iso_grav_anom")
    fields = {"pfa_tc": tc, "pfa_cond": cond, "pfa_depth": depth,
              "pfa_grav": grav, "pfa_rtp": rtp}
    raw_scores: list[np.ndarray] = []
    axes_list: list[np.ndarray] = []
    for name in ("pfa_tc", "pfa_cond", "pfa_depth", "pfa_grav", "pfa_rtp"):
        score, axis = paired_flank_asymmetry(fields[name], fp)
        raw_scores.append(score)
        axes_list.append(axis)
        put(name, score)
        del score, axis
        gc.collect()
    stack = np.stack(raw_scores)  # (5,H,W) float32
    axes = np.stack(axes_list)
    srt = np.sort(stack, axis=0)
    put("pfa_max", srt[-1])
    put("pfa_second", srt[-2])
    strong = stack > CONCORDANCE_CUT
    top_axis = axes[np.argmax(stack, axis=0), np.arange(fp.shape[0])[:, None], np.arange(fp.shape[1])[None, :]]
    agree = (axes == top_axis[None]) & strong
    concordance = (agree.sum(axis=0).astype(np.float32) / float(len(PFA_FIELDS)))
    put("pfa_concordance", np.where(fp, concordance, 0.0), standardize=False)
    del stack, axes, srt, strong, top_axis, agree, concordance, raw_scores, axes_list
    mm.flush()
    del mm
    return np.load(out_path, mmap_mode="r")
