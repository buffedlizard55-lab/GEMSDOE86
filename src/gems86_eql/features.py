"""Catalogue-only earthquake-lineation features for the H86N lane.

The feature family is intentionally small and auditable: it reads only the
supplied earthquake-intensity and distance-to-nearest-earthquake bands from the
pinned native TIFF.  Multi-scale Hessian lineation is used as a structural
proxy for a persistent earthquake-field corridor; no fault labels, DEM, or
other catalogue-derived channels are read.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata


# The native 19-band input's supplied seismic channels.  These are kept here,
# rather than inferred from a prepared-array directory, to make the source
# binding explicit and reproducible.
IEQ_BAND = 16
DEQ_BAND = 10


def _clean_band(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    finite = np.isfinite(values) & (values > -1.0e20) & footprint
    if not finite.any():
        raise ValueError("seismic band has no finite in-footprint values")
    fill = float(np.median(values[finite]))
    out = np.where(finite, values, fill).astype(np.float32)
    out[~footprint] = fill
    return out


def rank01(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Tie-aware in-footprint percentile rank in [0, 1], zero outside."""
    out = np.zeros(values.shape, dtype=np.float32)
    flat = np.asarray(values, dtype=np.float32)[footprint]
    if flat.size == 0 or not np.isfinite(flat).all():
        raise ValueError("cannot rank an empty/non-finite feature")
    if np.ptp(flat) == 0:
        out[footprint] = 0.5
        return out
    ranks = rankdata(flat, method="average").astype(np.float32)
    out[footprint] = (ranks - 1.0) / float(flat.size - 1)
    return out


def _hessian_lineation(image: np.ndarray, sigma: float, footprint: np.ndarray):
    """Bright-ridge strength and local anisotropy at one Gaussian scale."""
    # scipy's order is (row derivatives, column derivatives).
    hrr = gaussian_filter(image, sigma=sigma, order=(2, 0), mode="nearest")
    hcc = gaussian_filter(image, sigma=sigma, order=(0, 2), mode="nearest")
    hrc = gaussian_filter(image, sigma=sigma, order=(1, 1), mode="nearest")
    mean = 0.5 * (hrr + hcc)
    discr = np.sqrt(np.maximum(0.0, (0.5 * (hrr - hcc)) ** 2 + hrc ** 2))
    eig_hi = mean + discr
    eig_lo = mean - discr
    # A bright corridor has negative normal curvature.  The ratio suppresses
    # isotropic point-like clusters and keeps line-like response.
    ridge = np.maximum(-eig_lo, 0.0)
    anisotropy = np.clip((np.abs(eig_lo) - np.abs(eig_hi)) /
                         (np.abs(eig_lo) + np.abs(eig_hi) + 1.0e-12), 0.0, 1.0)
    ridge[~footprint] = 0.0
    anisotropy[~footprint] = 0.0
    return ridge.astype(np.float32), anisotropy.astype(np.float32)


def build_features_from_arrays(ieq: np.ndarray, deq: np.ndarray,
                               footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Build the H86N candidate and controls from two shared-cache arrays."""
    ieq = _clean_band(ieq, footprint)
    deq = _clean_band(deq, footprint)

    # The supplied bands are already catalogue transforms.  log1p limits the
    # influence of the largest swarm and makes the scale response stable.
    intensity = np.log1p(np.maximum(ieq, 0.0)).astype(np.float32)
    distance = np.log1p(np.maximum(deq, 0.0)).astype(np.float32)
    intensity_rank = rank01(intensity, footprint)
    closeness = 1.0 - rank01(distance, footprint)
    closeness[~footprint] = 0.0

    # E2 is intentionally a simple non-fault-control feature: sharp catalogue
    # edges, rather than persistent lineation, should not receive the proposed
    # mechanism's structural boost.
    smooth = gaussian_filter(intensity, sigma=2.0, mode="nearest")
    grad_row, grad_col = np.gradient(smooth)
    edge = np.hypot(grad_row, grad_col).astype(np.float32)
    edge_rank = rank01(edge, footprint)

    ridge2, _anis2 = _hessian_lineation(intensity, sigma=2.0, footprint=footprint)
    ridge4, anis4 = _hessian_lineation(intensity, sigma=4.0, footprint=footprint)
    ridge2_rank = rank01(ridge2, footprint)
    ridge4_rank = rank01(ridge4, footprint)
    anis4_rank = rank01(anis4, footprint)

    # EQL: multi-scale persistent lineation, gently gated by catalogue
    # intensity.  Distance is not multiplied into the candidate: it is held as
    # a separate catalogue-control so the mechanism can be falsified cleanly.
    lineation = np.sqrt(ridge2_rank * ridge4_rank)
    candidate = lineation * (0.35 + 0.65 * anis4_rank) * (0.50 + 0.50 * intensity_rank)
    candidate[~footprint] = 0.0

    return {
        "H86N_EQL": candidate.astype(np.float32),
        "E0_IEQ_intensity": intensity_rank.astype(np.float32),
        "E1_DEQ_closeness": closeness.astype(np.float32),
        "E2_catalogue_edge": edge_rank.astype(np.float32),
        "E3_single_scale_ridge": (ridge4_rank * (0.5 + 0.5 * anis4_rank)).astype(np.float32),
    }


def build_features(feature_tif: Path, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compatibility helper for unit tests; lane execution must use the cache."""
    with rasterio.open(feature_tif) as src:
        if src.count < max(IEQ_BAND, DEQ_BAND):
            raise ValueError("native feature TIFF does not contain seismic bands")
        return build_features_from_arrays(src.read(IEQ_BAND), src.read(DEQ_BAND), footprint)
