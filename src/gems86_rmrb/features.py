"""RMRB-86 label-blind radiometric mixing-residual boundary features.

The modelled object is not a geothermal vent. It is a candidate fault-related
boundary: a narrow departure from the broad K~Th+U lithologic mixing relation
that is spatially persistent and aligned with an RTP magnetic edge. Weathering,
transported sediment and unfaulted lithologic contacts are explicit mimics.

No catalogue raster is accepted by this module. Catalogue labels are used only
later by the fold-proper positive/unlabelled learner.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from sklearn.linear_model import HuberRegressor

CORE_BANDS = (
    (2, "rtp"),
    (3, "tmi_hg"),
    (5, "iso_grav_anom_slope"),
    (6, "tc"),
    (11, "iso_grav_anom_vg"),
    (12, "det_elev"),
    (15, "depth_to_base_surf"),
    (17, "cond_surf"),
    (18, "iso_grav_anom_hg"),
    (19, "det_elev_slope"),
)
CORE_NAMES = tuple(name for _, name in CORE_BANDS)
RAD_NAMES = ("rad_K", "rad_Th", "rad_U")
DERIVED_NAMES = (
    "mix_residual",
    "residual_edge_s1p5",
    "residual_edge_s3",
    "rtp_edge_persistence",
    "cross_gradient_alignment",
    "rmrb_joint",
    "residual_line_coherence",
)
NAMES = CORE_NAMES + RAD_NAMES + DERIVED_NAMES
BASE_COLUMNS = tuple(range(len(CORE_NAMES)))
RAW_RAD_COLUMNS = tuple(range(len(CORE_NAMES) + len(RAD_NAMES)))
JOINT_COLUMNS = tuple(range(len(NAMES)))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sample(a: np.ndarray, valid: np.ndarray, step: int = 37) -> np.ndarray:
    idx = np.flatnonzero(valid.ravel())
    # Tiny synthetic/test grids need more than one value; full rasters retain
    # the fixed stride used to bound robust-quantile memory.
    if idx.size > step * 10:
        idx = idx[::step]
    return np.asarray(a.ravel()[idx], np.float64)


def clean_scale(a: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, dict]:
    """Median-fill and robustly map a label-blind layer to [0,1]."""
    a = np.asarray(a, np.float32)
    good = valid & np.isfinite(a) & (a > -1e30) & (a < 1e30)
    if a.shape != valid.shape or not good.any():
        raise ValueError("invalid feature layer/grid")
    sample = _sample(a, good)
    lo, med, hi = (float(v) for v in np.percentile(sample, (1, 50, 99)))
    if not hi > lo:
        raise ValueError("feature has no robust variation")
    out = np.where(good, a, med).astype(np.float32, copy=False)
    out -= np.float32(lo)
    out /= np.float32(hi - lo)
    np.clip(out, 0.0, 1.0, out=out)
    return out, {
        "valid_pixels": int(good.sum()),
        "missing_inside_footprint": int((valid & ~good).sum()),
        "p01": lo,
        "median": med,
        "p99": hi,
    }


def weighted_gaussian(a: np.ndarray, valid: np.ndarray, sigma: float,
                      order=(0, 0)) -> np.ndarray:
    """Footprint-normalized Gaussian operation; avoids false survey-boundary edges."""
    weight = valid.astype(np.float32)
    if order == (0, 0):
        numerator = gaussian_filter(a * weight, sigma=sigma, mode="constant", output=np.float32)
        denominator = gaussian_filter(weight, sigma=sigma, mode="constant", output=np.float32)
        return numerator / np.maximum(denominator, np.float32(1e-6))
    # Derivatives of a normalized smoothed field are more stable than dividing
    # derivative numerators by a signed derivative of the weight mask.
    smooth = weighted_gaussian(a, valid, sigma)
    return gaussian_filter(smooth, sigma=max(0.6, sigma / 3.0), order=order,
                           mode="nearest", output=np.float32)


def gradients(a: np.ndarray, valid: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    smooth = weighted_gaussian(a, valid, sigma)
    gy = gaussian_filter(smooth, sigma=0.7, order=(1, 0), mode="nearest", output=np.float32)
    gx = gaussian_filter(smooth, sigma=0.7, order=(0, 1), mode="nearest", output=np.float32)
    return gy, gx


def robust01(a: np.ndarray, valid: np.ndarray, upper=99.5) -> tuple[np.ndarray, dict]:
    sample = _sample(a, valid)
    lo, hi = (float(v) for v in np.percentile(sample, (1, upper)))
    if not hi > lo:
        return np.zeros(a.shape, np.float32), {"p01": lo, f"p{upper}": hi}
    out = (np.asarray(a, np.float32) - np.float32(lo)) / np.float32(hi - lo)
    np.clip(out, 0.0, 1.0, out=out)
    out[~valid] = 0.0
    return out, {"p01": lo, f"p{upper}": hi}


def _mixing_fit(k: np.ndarray, th: np.ndarray, u: np.ndarray,
                valid: np.ndarray, seed: int = 8601) -> tuple[np.ndarray, dict]:
    """Robust full-data production fit plus label-blind spatial cross-fit diagnostic."""
    idx_all = np.flatnonzero(valid.ravel())
    rng = np.random.default_rng(seed)
    fit_idx = rng.choice(idx_all, min(180_000, len(idx_all)), replace=False)
    xflat = np.stack((th.ravel()[fit_idx], u.ravel()[fit_idx]), axis=1)
    yflat = k.ravel()[fit_idx]
    model = HuberRegressor(epsilon=1.5, alpha=1e-4, max_iter=150).fit(xflat, yflat)
    predicted = (model.intercept_ + model.coef_[0] * th + model.coef_[1] * u).astype(np.float32)
    residual = (k - predicted).astype(np.float32)

    # Cross-fitting is a diagnostic of relation stability, not a score and not a
    # source of labels. Each quadrant model is fitted outside the held quadrant.
    yy, xx = np.indices(valid.shape, sparse=True)
    ym, xm = valid.shape[0] // 2, valid.shape[1] // 2
    quadrant = ((yy >= ym).astype(np.int8) * 2 + (xx >= xm).astype(np.int8))
    cv = []
    for q in range(4):
        train = fit_idx[quadrant.ravel()[fit_idx] != q]
        if len(train) > 55_000:
            train = rng.choice(train, 55_000, replace=False)
        test = idx_all[quadrant.ravel()[idx_all] == q][::53]
        local = HuberRegressor(epsilon=1.5, alpha=1e-4, max_iter=150).fit(
            np.stack((th.ravel()[train], u.ravel()[train]), axis=1), k.ravel()[train]
        )
        pred = local.predict(np.stack((th.ravel()[test], u.ravel()[test]), axis=1))
        cv.append({
            "quadrant": int(q),
            "test_pixels": int(len(test)),
            "mae": float(np.mean(np.abs(k.ravel()[test] - pred))),
            "coefficients": [float(v) for v in local.coef_],
            "intercept": float(local.intercept_),
        })
    return residual, {
        "formula": "K = intercept + b_Th*Th + b_U*U; Huber epsilon=1.5",
        "fit_pixels": int(len(fit_idx)),
        "coefficients": [float(v) for v in model.coef_],
        "intercept": float(model.intercept_),
        "spatial_crossfit": cv,
        "uses_fault_catalogue": False,
    }


def build_cache(core_path: Path, radiometric_path: Path, footprint: np.ndarray,
                cache_path: Path, receipt_path: Path) -> dict:
    """Build the immutable-on-reuse float32 (channel, pixel) cache."""
    core_path, radiometric_path = Path(core_path), Path(radiometric_path)
    cache_path, receipt_path = Path(cache_path), Path(receipt_path)
    source = {
        "core_sha256": sha256(core_path),
        "radiometric_sha256": sha256(radiometric_path),
        "builder_sha256": sha256(Path(__file__)),
    }
    if cache_path.is_file() and receipt_path.is_file():
        old = json.loads(receipt_path.read_text())
        if old.get("source") == source and old.get("names") == list(NAMES):
            expected = len(NAMES) * footprint.size * np.dtype("float32").itemsize
            if cache_path.stat().st_size == expected and old.get("cache_sha256") == sha256(cache_path):
                return {**old, "reused": True}

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.memmap(cache_path, mode="w+", dtype="float32", shape=(len(NAMES), footprint.size))
    metadata: dict[str, object] = {"layers": {}}
    rtp = None
    with rasterio.open(core_path) as src:
        if src.shape != footprint.shape or src.count < 19:
            raise ValueError("core feature stack does not match required grid")
        for col, (band, expected_name) in enumerate(CORE_BANDS):
            found = src.tags(band).get("band_name")
            if found is not None and found != expected_name:
                raise ValueError(f"band {band}: expected {expected_name}, got {found}")
            clean, stats = clean_scale(src.read(band), footprint)
            clean[~footprint] = 0.0
            mm[col] = clean.ravel()
            metadata["layers"][expected_name] = {"band": band, **stats}
            if expected_name == "rtp":
                rtp = clean.copy()
    if rtp is None:
        raise AssertionError("RTP band was not loaded")

    rad = []
    radiometric_valid = footprint.copy()
    with rasterio.open(radiometric_path) as src:
        if src.shape != footprint.shape or src.count < 3:
            raise ValueError("radiometric stack does not match required grid")
        for i, expected_name in enumerate(("K", "Th", "U"), start=1):
            if src.descriptions[i - 1] != expected_name:
                raise ValueError(f"radiometric band {i}: expected {expected_name}")
            raw = src.read(i).astype(np.float32)
            good = footprint & (raw > 0)
            radiometric_valid &= good
            # Zero is this uint8 product's nodata value. Convert it to NaN so
            # the common cleaner reports/fills it rather than treating it as a
            # valid low concentration.
            raw[~good] = np.nan
            clean, stats = clean_scale(raw, footprint)
            clean[~footprint] = 0.0
            mm[len(CORE_NAMES) + i - 1] = clean.ravel()
            metadata["layers"][f"rad_{expected_name}"] = {"band": i, **stats}
            rad.append(clean)
    k, th, u = rad
    residual, mixing = _mixing_fit(k, th, u, radiometric_valid)
    broad = weighted_gaussian(residual, radiometric_valid, sigma=20.0)
    residual -= broad
    residual[~radiometric_valid] = 0.0
    residual01, residual_stats = robust01(residual, radiometric_valid, upper=99.5)
    # Preserve both residual signs around zero; the edge transforms below are sign-invariant.
    abs_scale = float(np.percentile(np.abs(_sample(residual, radiometric_valid)), 99.5))
    residual_signed = np.clip(residual / max(abs_scale, 1e-6), -1.0, 1.0).astype(np.float32)
    residual_signed = (0.5 + 0.5 * residual_signed).astype(np.float32)
    residual_signed[~radiometric_valid] = 0.0

    ry1, rx1 = gradients(residual, radiometric_valid, 1.5)
    ry3, rx3 = gradients(residual, radiometric_valid, 3.0)
    edge1, edge1_stats = robust01(np.hypot(ry1, rx1), radiometric_valid)
    edge3, edge3_stats = robust01(np.hypot(ry3, rx3), radiometric_valid)
    residual_edge = np.sqrt(edge1 * edge3).astype(np.float32)

    my2, mx2 = gradients(rtp, footprint, 2.0)
    my4, mx4 = gradients(rtp, footprint, 4.0)
    mag2, mag2_stats = robust01(np.hypot(my2, mx2), footprint)
    mag4, mag4_stats = robust01(np.hypot(my4, mx4), footprint)
    magnetic_persistence = np.sqrt(mag2 * mag4).astype(np.float32)
    alignment = np.abs(ry1 * my2 + rx1 * mx2) / np.maximum(
        np.hypot(ry1, rx1) * np.hypot(my2, mx2), np.float32(1e-7)
    )
    np.clip(alignment, 0.0, 1.0, out=alignment)
    alignment[~radiometric_valid] = 0.0

    # Structure-tensor coherence suppresses isolated blobs while retaining ribbons.
    jxx = gaussian_filter(rx1 * rx1, sigma=3.0, mode="nearest", output=np.float32)
    jyy = gaussian_filter(ry1 * ry1, sigma=3.0, mode="nearest", output=np.float32)
    jxy = gaussian_filter(rx1 * ry1, sigma=3.0, mode="nearest", output=np.float32)
    coherence = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2) / np.maximum(jxx + jyy, 1e-8)
    np.clip(coherence, 0.0, 1.0, out=coherence)
    coherence[~radiometric_valid] = 0.0
    joint = np.sqrt(residual_edge * magnetic_persistence).astype(np.float32)
    joint *= (0.25 + 0.75 * alignment).astype(np.float32)
    joint *= (0.35 + 0.65 * coherence).astype(np.float32)
    joint, joint_stats = robust01(joint, radiometric_valid, upper=99.5)

    derived = (residual_signed, edge1, residual_edge, magnetic_persistence,
               alignment.astype(np.float32), joint, coherence.astype(np.float32))
    for col, layer in enumerate(derived, start=len(CORE_NAMES) + len(RAD_NAMES)):
        if not np.isfinite(layer).all() or (layer < 0).any() or (layer > 1).any():
            raise ValueError(f"derived feature {NAMES[col]} is invalid")
        mm[col] = layer.ravel()
    mm.flush()
    del mm

    receipt = {
        "schema": "gems86.feature-cache.v1",
        "source": source,
        "cache_file": str(cache_path),
        "cache_bytes": cache_path.stat().st_size,
        "cache_sha256": sha256(cache_path),
        "shape": [len(NAMES), *footprint.shape],
        "dtype": "float32",
        "names": list(NAMES),
        "base_columns": list(BASE_COLUMNS),
        "raw_radiometric_columns": list(RAW_RAD_COLUMNS),
        "joint_columns": list(JOINT_COLUMNS),
        "mixing_model": mixing,
        "transforms": {
            "mix_residual": "Huber K~Th+U residual minus 20 px normalized-Gaussian background",
            "residual_edges": {"sigma_px": [1.5, 3.0], "persistence": "geometric mean"},
            "rtp_edges": {"sigma_px": [2.0, 4.0], "persistence": "geometric mean"},
            "joint": "sqrt(residual_edge*RTP_edge)*(0.25+0.75*abs_gradient_alignment)*(0.35+0.65*line_coherence)",
        },
        "normalization": {
            "residual": residual_stats,
            "residual_edge_s1p5": edge1_stats,
            "residual_edge_s3_persistence": edge3_stats,
            "rtp_edge_s2": mag2_stats,
            "rtp_edge_s4": mag4_stats,
            "joint": joint_stats,
        },
        "layers": metadata["layers"],
        "catalogue_free": True,
        "reused": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def open_cache(cache_path: Path, shape: tuple[int, int]) -> np.memmap:
    expected = len(NAMES) * int(np.prod(shape)) * np.dtype("float32").itemsize
    if Path(cache_path).stat().st_size != expected:
        raise ValueError("feature cache byte length mismatch")
    return np.memmap(cache_path, mode="r", dtype="float32", shape=(len(NAMES), int(np.prod(shape))))
