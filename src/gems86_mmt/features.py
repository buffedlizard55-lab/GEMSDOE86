"""Catalogue-blind magnetic-marker translation features.

The lane tests a specific, falsifiable alternative to pointwise magnetic-edge
ranking: a buried marker should be laterally translated across a structural
corridor, so a local cross-correlation between two independent magnetic
representations should peak at a *non-zero* cross-corridor lag.  The
competition layers are used as supplied; the physical interpretation of Band
6 as radiometric total count is pinned by ``docs/evidence/band-physics-...``.

No catalogue pixels or labels are read here.  The catalogue enters only in the
holdout/emission code, where the visible-fault mask is recomputed per fold.
This module deliberately returns diagnostic component fields as well as the
candidate score so feature-alone leakage canaries can be recorded.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

try:  # works both as ``gems86`` for CLIs and ``src.gems86`` for tests
    from gems86.io import NODATA
except ModuleNotFoundError:  # pragma: no cover - import-layout compatibility
    from src.gems86.io import NODATA


# Tangent directions in image row/column coordinates.  theta=0 is E-W in the
# projected grid; theta=90 is N-S.  GeoDAWN's verified release metadata records
# E-W flight lines and N-S tie lines, so seam-parallel responses are downweighted
# rather than treated as geological evidence.
ORIENTATIONS_DEG = tuple(float(x) for x in np.arange(0.0, 180.0, 22.5))
NONZERO_LAGS_PX = (2, 3, 4, 5, 6)  # 200--600 m on the 100 m competition grid


def feature_names() -> tuple[str, ...]:
    return (
        "mmt_translation",
        "mmt_tc_decoupled",
        "mmt_coherence",
        "mmt_edge_control",
        "mmt_radiometric_gradient",
    )


def _read_band(src: rasterio.DatasetReader, index: int, footprint: np.ndarray) -> np.ndarray:
    a = src.read(index).astype(np.float32)
    good = footprint & np.isfinite(a) & (a > NODATA * 0.5)
    if not good.any():
        raise ValueError(f"band {index} has no finite values in the footprint")
    fill = float(np.median(a[good]))
    a[~good] = fill
    a[~footprint] = fill
    return a


def _robust_z(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    v = a[footprint]
    lo, hi = np.percentile(v, [1.0, 99.0])
    med = float(np.median(v))
    scale = max(float(np.percentile(v, 75.0) - np.percentile(v, 25.0)), 1e-6)
    return np.clip((a - med) / scale, -8.0, 8.0).astype(np.float32)


def rank01(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Tie-invariant empirical-CDF min-rank inside the footprint, in [0, 1].

    Tied floor cells (e.g., 0.0 background or binary off-support cells) receive
    0.0 uniformly across all rows rather than a row-major ``argsort`` ramp
    (see ``IR-86-MMT-RANK01-TIE-20261024``). Non-finite values inside the
    footprint are mapped safely to the floor (0.0) rather than propagating NaN.
    """
    footprint = np.asarray(footprint, bool)
    out = np.zeros(a.shape, np.float32)
    v = np.asarray(a, np.float32)[footprint]
    if v.size <= 1:
        return out
    finite = np.isfinite(v)
    if not finite.any():
        return out
    fmin = float(v[finite].min())
    fmax = float(v[finite].max())
    if fmin == fmax and finite.all():
        return out
    clean = np.where(finite, v, fmin - 1.0)
    ranks = (rankdata(clean, method="min").astype(np.float64) - 1.0) / float(v.size - 1)
    out[footprint] = np.clip(ranks, 0.0, 1.0).astype(np.float32)
    return out


def _shift(a: np.ndarray, dy: float, dx: float) -> np.ndarray:
    # Interpolation is only used to evaluate a continuous field on the fixed
    # 100 m grid; no labels or catalogue values are interpolated.
    return ndi.shift(a, (dy, dx), order=1, mode="nearest", prefilter=False).astype(np.float32)


def _directional_difference(a: np.ndarray, theta_deg: float) -> tuple[np.ndarray, float]:
    theta = np.deg2rad(theta_deg)
    # normal=(sin,cos), strike=(-cos,sin) in row/column coordinates
    dy, dx = float(np.sin(theta)), float(np.cos(theta))
    plus = _shift(a, dy, dx)
    minus = _shift(a, -dy, -dx)
    # obliquity is 0 for the two principal survey axes and 1 at 45 degrees.
    obliquity = float(abs(np.sin(2.0 * theta)))
    return (plus - minus) * 0.5, obliquity


def _lag_shift_vector(theta_deg: float, lag: float, *, shift_axis: str = "strike") -> tuple[float, float]:
    """Return (dy, dx) for lag evaluation relative to gradient normal (sin θ, cos θ).

    ``shift_axis="strike"`` shifts orthogonal to the gradient normal along
    corridor strike ``(-cos θ, sin θ)``. ``shift_axis="normal"`` reproduces the
    historical PR #93 across-edge shift (``IR-86-MMT-SHIFT-AXIS-20261024``).
    """
    rad = np.deg2rad(theta_deg)
    if shift_axis == "strike":
        return float(-np.cos(rad) * lag), float(np.sin(rad) * lag)
    if shift_axis == "normal":
        return float(np.sin(rad) * lag), float(np.cos(rad) * lag)
    raise ValueError(f"Unsupported shift_axis {shift_axis!r}; expected 'strike' or 'normal'")


def build_marker_features(
    features_tif: Path,
    footprint: np.ndarray,
    *,
    shift_axis: str = "strike",
) -> dict[str, np.ndarray]:
    """Build H86E-MMT fields from Bands 2, 3, 6, and 9.

    ``mmt_translation`` is the largest positive non-zero-lag local product of
    directional RTP and magnetic-tilt gradients after subtracting the zero-lag
    product.  It is not a learned label score.  ``mmt_tc_decoupled`` weights it
    toward locations where the marker translation is not simply coincident with
    a strong radiometric TC boundary.  The other returned arrays are controls or
    feature-canary inputs.
    """
    footprint = np.asarray(footprint, bool)
    with rasterio.open(features_tif) as src:
        rtp = _read_band(src, 2, footprint)
        tmi_hg = _read_band(src, 3, footprint)
        tc = _read_band(src, 6, footprint)
        tmi_vg = _read_band(src, 9, footprint)

    # Multi-scale fields suppress individual 100 m interpolation noise while
    # retaining the 200--600 m marker-lag range declared above.
    rtp_hp = rtp - ndi.gaussian_filter(rtp, 8.0, mode="nearest")
    tilt = np.arctan2(tmi_vg, np.abs(tmi_hg) + 1e-6).astype(np.float32)
    tilt_hp = tilt - ndi.gaussian_filter(tilt, 8.0, mode="nearest")
    rtp_hp = _robust_z(ndi.gaussian_filter(rtp_hp, 1.0, mode="nearest"), footprint)
    tilt_hp = _robust_z(ndi.gaussian_filter(tilt_hp, 1.0, mode="nearest"), footprint)

    translation = np.zeros(footprint.shape, np.float32)
    coherence = np.zeros(footprint.shape, np.float32)
    edge = np.zeros(footprint.shape, np.float32)
    zero_lag_best = np.zeros(footprint.shape, np.float32)

    for theta in ORIENTATIONS_DEG:
        rgrad, obliquity = _directional_difference(rtp_hp, theta)
        tgrad, _ = _directional_difference(tilt_hp, theta)
        seam_weight = np.float32(0.25 + 0.75 * obliquity)
        local_zero = np.abs(ndi.gaussian_filter(rgrad * tgrad, 4.0, mode="nearest"))
        local_best = np.zeros(footprint.shape, np.float32)
        for lag in NONZERO_LAGS_PX:
            # A non-zero lag is the hypothesis; lag 0 is retained as its
            # within-pixel registration control.
            s_dy, s_dx = _lag_shift_vector(theta, lag, shift_axis=shift_axis)
            shifted = _shift(tgrad, s_dy, s_dx)
            lag_product = np.abs(ndi.gaussian_filter(rgrad * shifted, 4.0, mode="nearest"))
            local_best = np.maximum(local_best, lag_product)
            del shifted, lag_product
        gain = np.maximum(local_best - local_zero, 0.0) * seam_weight
        translation = np.maximum(translation, gain)
        zero_lag_best = np.maximum(zero_lag_best, local_zero * seam_weight)
        coh = ndi.gaussian_filter(np.abs(rgrad), 4.0, mode="nearest")
        coh *= ndi.gaussian_filter(np.abs(tgrad), 4.0, mode="nearest")
        coherence = np.maximum(coherence, coh * seam_weight)
        edge = np.maximum(edge, ndi.gaussian_filter(np.abs(rgrad), 2.0, mode="nearest") * seam_weight)
        del rgrad, tgrad, local_zero, local_best, gain, coh

    # TC is radiometric total count, not a magnetic tilt band.  A quiet TC
    # gradient is a conservative decoupling factor, not proof of alteration.
    tc_grad = np.hypot(
        ndi.gaussian_filter(tc, 2.0, order=(0, 1), mode="nearest"),
        ndi.gaussian_filter(tc, 2.0, order=(1, 0), mode="nearest"),
    ).astype(np.float32)
    tc_rank = rank01(tc_grad, footprint)
    quiet = 1.0 - tc_rank

    fields = {
        "mmt_translation": translation,
        "mmt_tc_decoupled": translation * (0.5 + 0.5 * quiet),
        "mmt_coherence": coherence,
        "mmt_edge_control": edge,
        "mmt_radiometric_gradient": tc_grad,
    }
    for name, field in fields.items():
        field = np.nan_to_num(field, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        field[~footprint] = 0.0
        fields[name] = field

    return fields
