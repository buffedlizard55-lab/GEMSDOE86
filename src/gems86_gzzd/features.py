"""Catalogue-blind Laplace gravity-curvature dipole features (H86F-GZZD).

Frozen design: ``research/H86F_GZZD_PREREGISTRATION.json``. No catalogue
pixels or labels are read here; the catalogue enters only in the runner's
holdout/emission masks, recomputed from visible faults per fold.

Physics (pixel-verified, ``docs/evidence/band-physics-verification-20261024.json``
and re-measured in ``docs/evidence/h86f-h33-forensics.json``): the signed
horizontal gravity vector is ``(dg/dx_east, dg/dy_north) = (+Band 18, -Band 11)``
with Band 11 = ``dg/drow_south``. In image coordinates (row increases
southward) the horizontal divergence is ``d_x Band18 + d_row Band11``, and by
Laplace's equation in the source-free half-space the vertical gravity
curvature is ``gzz = -(d_x Band18 + d_row Band11)``, Gaussian-regularized at
sigma=5 px (500 m). A buried basement step gives ``gzz`` an antisymmetric
dipole (opposite-sign lobes, zero crossing over the step); the statistic
below scores that *pairing*, not edge magnitude.

Returned fields (all float32, finite, exactly 0 outside the footprint):

- ``gzzd_concordant`` (E1 candidate): dipole pairing x soft polarity gate
  (1.0 when the Band 15 basement-depth flank step and the Band 13 gravity
  flank step have opposite signs, else 0.25), max over 8 strike azimuths.
- ``gzzd_dipole`` (E2 ablation): identical pairing, gate fixed at 1.0.
- ``gzzd_edge_control`` (E3 negative control): sigma=2 px smoothed Band 5
  unsigned gravity-gradient magnitude.
- ``gzzd_abs_gzz`` / ``gzzd_polarity_gate``: diagnostics for the
  feature-alone leakage canary (never emitted as candidates).

The QC dict reports corr(gzz, -Laplacian Band 13) on the 30-px-eroded
footprint interior; the runner fails closed below +0.80.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

try:  # works both as ``gems86`` for CLIs and ``src.gems86`` for tests
    from gems86.io import NODATA
except ModuleNotFoundError:  # pragma: no cover - import-layout compatibility
    from src.gems86.io import NODATA

SIGMA_GZZ_PX = 5.0
SIGMA_STEP_PX = 2.0
FLANK_OFFSETS_PX = (2.0, 3.0, 4.0)
ORIENTATIONS = tuple(range(8))  # strike azimuth k * 22.5 degrees
GATE_CONCORDANT = 1.0
GATE_DISCORDANT = 0.25


def feature_names() -> tuple[str, ...]:
    return (
        "gzzd_concordant",
        "gzzd_dipole",
        "gzzd_edge_control",
        "gzzd_abs_gzz",
        "gzzd_polarity_gate",
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


def _shift(a: np.ndarray, dy: float, dx: float) -> np.ndarray:
    return ndi.shift(a, (dy, dx), order=1, mode="nearest", prefilter=False).astype(np.float32)


def _flank_means(a: np.ndarray, ny: float, nx: float) -> tuple[np.ndarray, np.ndarray]:
    """Mean of ``a`` at +2..4 px and -2..4 px along the unit normal (ny, nx)."""
    plus = sum(_shift(a, t * ny, t * nx) for t in FLANK_OFFSETS_PX) / len(FLANK_OFFSETS_PX)
    minus = sum(_shift(a, -t * ny, -t * nx) for t in FLANK_OFFSETS_PX) / len(FLANK_OFFSETS_PX)
    return plus.astype(np.float32), minus.astype(np.float32)


def _strike_smooth(a: np.ndarray, sy: float, sx: float) -> np.ndarray:
    """9-tap mean along the strike direction (>=900 m continuity at 100 m/px)."""
    return (sum(_shift(a, t * sy, t * sx) for t in range(-4, 5)) / 9.0).astype(np.float32)


def dipole_pairing(plus: np.ndarray, minus: np.ndarray) -> np.ndarray:
    """Geometric-mean lobe pairing; >0 only when the flanks have opposite signs.

    Both step polarities are accepted (upthrown side may lie on either side of
    the arbitrary normal direction); a monopolar curvature lobe scores 0.
    """
    forward = np.sqrt(np.clip(plus * -minus, 0.0, None))
    reverse = np.sqrt(np.clip(-plus * minus, 0.0, None))
    return np.maximum(forward, reverse).astype(np.float32)


def build_gzzd_features(
    features_tif: Path, footprint: np.ndarray
) -> tuple[dict[str, np.ndarray], dict]:
    """Build the five preregistered H86F-GZZD fields plus the Laplace QC."""
    footprint = np.asarray(footprint, bool)
    with rasterio.open(features_tif) as src:
        b5 = _read_band(src, 5, footprint)
        b11 = _read_band(src, 11, footprint)
        b13 = _read_band(src, 13, footprint)
        b15 = _read_band(src, 15, footprint)
        b18 = _read_band(src, 18, footprint)

    # Laplace vertical gravity curvature in image coordinates (see module docstring).
    gzz = -(
        ndi.gaussian_filter(b18, SIGMA_GZZ_PX, order=(0, 1), mode="nearest")
        + ndi.gaussian_filter(b11, SIGMA_GZZ_PX, order=(1, 0), mode="nearest")
    ).astype(np.float32)
    interior = ndi.binary_erosion(footprint, iterations=30)
    neg_laplacian = -(
        ndi.gaussian_filter(b13, SIGMA_GZZ_PX, order=(0, 2), mode="nearest")
        + ndi.gaussian_filter(b13, SIGMA_GZZ_PX, order=(2, 0), mode="nearest")
    )
    qc_corr = float(
        np.corrcoef(
            gzz[interior].astype(np.float64), neg_laplacian[interior].astype(np.float64)
        )[0, 1]
    )
    del neg_laplacian

    # Smoothed step fields for the polarity gate (sign only; Bands 13/15 share
    # inversion ancestry, so concordance is never additive evidence).
    grav_step = ndi.gaussian_filter(b13, SIGMA_STEP_PX, mode="nearest")
    depth_step = ndi.gaussian_filter(b15, SIGMA_STEP_PX, mode="nearest")

    dipole_best = np.zeros(footprint.shape, np.float32)
    concordant_best = np.zeros(footprint.shape, np.float32)
    gate_best = np.full(footprint.shape, GATE_DISCORDANT, np.float32)
    for k in ORIENTATIONS:
        theta = np.radians(k * 22.5)  # strike azimuth in image coordinates
        sx, sy = float(np.cos(theta)), float(-np.sin(theta))  # strike unit vector
        nx, ny = float(np.sin(theta)), float(np.cos(theta))  # normal unit vector
        gplus, gminus = _flank_means(gzz, ny, nx)
        pair = _strike_smooth(dipole_pairing(gplus, gminus), sy, sx)
        del gplus, gminus
        dplus, dminus = _flank_means(depth_step, ny, nx)
        vplus, vminus = _flank_means(grav_step, ny, nx)
        concordant = ((dplus - dminus) * (vplus - vminus)) < 0
        gate = np.where(concordant, GATE_CONCORDANT, GATE_DISCORDANT).astype(np.float32)
        del dplus, dminus, vplus, vminus, concordant
        better = pair > dipole_best
        gate_best = np.where(better, gate, gate_best).astype(np.float32)
        dipole_best = np.maximum(dipole_best, pair)
        concordant_best = np.maximum(concordant_best, pair * gate)
        del pair, gate, better

    edge = ndi.gaussian_filter(b5, SIGMA_STEP_PX, mode="nearest").astype(np.float32)

    fields = {
        "gzzd_concordant": concordant_best,
        "gzzd_dipole": dipole_best,
        "gzzd_edge_control": edge,
        "gzzd_abs_gzz": np.abs(gzz).astype(np.float32),
        "gzzd_polarity_gate": gate_best,
    }
    for name, field in fields.items():
        field = np.nan_to_num(field, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        field[~footprint] = 0.0
        fields[name] = field

    qc = {
        "evidence_class": "BAND-PHYSICS-QC",
        "formula_image_coordinates": "gzz = -(d_x Band18 + d_row Band11)",
        "sigma_px": SIGMA_GZZ_PX,
        "interior_erosion_px": 30,
        "interior_pixels": int(interior.sum()),
        "corr_gzz_vs_neg_laplacian_band13": qc_corr,
        "fail_closed_below": 0.80,
    }
    return fields, qc
