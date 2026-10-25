"""H86J-MPC: monogenic log-Gabor phase-congruency step responses.

Preregistration: ``research/H86J_MPC_PREREGISTRATION.md`` (+ .json), frozen
before implementation.  No catalogue-derived quantity is constructed here;
the footprint is used only to clean/standardise each field and to zero the
outputs outside the study area.

Method (Kovesi monogenic phase congruency, simplified and frozen):
for each log-Gabor radial bandpass scale ``s`` (centre wavelength in px,
``sigmaonf = 0.55``), the even response ``E_s`` and the odd Riesz-transform
vector ``O_s = (Ox_s, Oy_s)`` are computed in the Fourier domain.  With
``E = sum_s E_s``, ``O = sum_s O_s`` and ``A_s = sqrt(E_s^2 + |O_s|^2)``::

    PC       = sqrt(E^2 + |O|^2) / (sum_s A_s + eps)      in [0, 1]
    stepness = |O| / sqrt(E^2 + |O|^2)                    (odd symmetry)
    lineness = |E| / sqrt(E^2 + |O|^2)                    (even symmetry)
    PC_step  = PC * stepness
    PC_line  = PC * lineness

PC is 1 only where every scale shares the same local phase/orientation; it
is invariant to a global contrast rescaling of the input (unit-tested).
A fault *offset* of a marker horizon is a step (odd); a dike/ridge/crest is
a line (even).  The synthetic step/ridge unit tests in
``tests/test_h86j_mpc.py`` pin this convention empirically -- it is not
assumed from sign conventions in the literature.

Boundary handling: sentinel/non-finite cells are filled with the footprint
median (``gems86_edti.features._clean``, reused), the field is standardised
by footprint median/IQR, outside-footprint cells are smoothly extended by
one normalised-convolution (Gaussian sigma=16 px) fill so the irregular
footprint border does not itself become a phase-congruent step, and the
array is reflect-padded by 64 px before the FFT (cropped back after).
Outputs are exactly 0 outside the footprint.
"""
from __future__ import annotations

import numpy as np
from scipy import fft as sfft
from scipy import ndimage as ndi

from gems86_edti.features import _clean

SIGMAONF = 0.55
PAD_PX = 64
EPS = 1e-6
WAVELENGTHS_FINE = (4.0, 8.0, 16.0, 32.0)    # RTP, DEM
WAVELENGTHS_COARSE = (8.0, 16.0, 32.0, 64.0)  # gravity (smoother field)


def _standardise(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = _clean(a, footprint).astype(np.float64)
    inside = a[footprint]
    med = float(np.median(inside))
    q25, q75 = (float(np.quantile(inside, q)) for q in (0.25, 0.75))
    iqr = (q75 - q25) or 1.0
    a = (a - med) / iqr
    # Smooth extension outside the footprint (normalised convolution):
    # prevents the study-area border from acting as a synthetic step.
    mask = footprint.astype(np.float64)
    num = ndi.gaussian_filter(a * mask, 16.0, mode="nearest")
    den = ndi.gaussian_filter(mask, 16.0, mode="nearest")
    fill = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0.0)
    a = np.where(footprint, a, fill)
    return a


def monogenic_pc(field: np.ndarray, footprint: np.ndarray,
                 wavelengths: tuple[float, ...],
                 sigmaonf: float = SIGMAONF) -> dict[str, np.ndarray]:
    """Phase-congruency products for one standardised field (see module doc)."""
    a = _standardise(np.asarray(field, np.float32), footprint)
    padded = np.pad(a, PAD_PX, mode="reflect")
    del a
    H, W = padded.shape
    F = sfft.rfft2(padded, workers=2)
    del padded
    fy = sfft.fftfreq(H)[:, None]                     # cycles/px, rows
    fx = sfft.rfftfreq(W)[None, :]                    # cycles/px, cols
    radius = np.sqrt(fy * fy + fx * fx)                # float64 (H, W//2+1)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_r = np.where(radius > 0, np.log(np.maximum(radius, 1e-12)), 0.0)
        riesz_x = np.where(radius > 0, 1j * fx / np.maximum(radius, 1e-12), 0j)
        riesz_y = np.where(radius > 0, 1j * fy / np.maximum(radius, 1e-12), 0j)
    log_sigma = float(np.log(sigmaonf))
    E = np.zeros((H, W), np.float32)
    Ox = np.zeros((H, W), np.float32)
    Oy = np.zeros((H, W), np.float32)
    sumA = np.zeros((H, W), np.float32)
    for wl in wavelengths:
        fo = 1.0 / float(wl)
        with np.errstate(invalid="ignore"):
            gabor = np.exp(-((log_r - np.log(fo)) ** 2) / (2.0 * log_sigma ** 2))
        gabor[radius == 0] = 0.0
        Fb = F * gabor
        del gabor
        e_s = sfft.irfft2(Fb, s=(H, W), workers=2).astype(np.float32)
        ox_s = sfft.irfft2(Fb * riesz_x, s=(H, W), workers=2).astype(np.float32)
        oy_s = sfft.irfft2(Fb * riesz_y, s=(H, W), workers=2).astype(np.float32)
        del Fb
        E += e_s
        Ox += ox_s
        Oy += oy_s
        sumA += np.sqrt(e_s * e_s + ox_s * ox_s + oy_s * oy_s)
        del e_s, ox_s, oy_s
    del F, radius, log_r, riesz_x, riesz_y, fy, fx
    sl = (slice(PAD_PX, PAD_PX + footprint.shape[0]),
          slice(PAD_PX, PAD_PX + footprint.shape[1]))
    E, Ox, Oy, sumA = E[sl], Ox[sl], Oy[sl], sumA[sl]
    energy = np.sqrt(E * E + Ox * Ox + Oy * Oy)
    pc = energy / (sumA + EPS)
    odd = np.sqrt(Ox * Ox + Oy * Oy)
    stepness = odd / (energy + EPS)
    lineness = np.abs(E) / (energy + EPS)
    out = {
        "pc": pc,
        "pc_step": pc * stepness,
        "pc_line": pc * lineness,
        "stepness": stepness,
        "log_amp": np.log1p(sumA),
    }
    for v in out.values():
        v[~footprint] = 0.0
        np.clip(v, 0.0, None, out=v)
    np.clip(out["pc"], 0.0, 1.0, out=out["pc"])
    np.clip(out["pc_step"], 0.0, 1.0, out=out["pc_step"])
    np.clip(out["pc_line"], 0.0, 1.0, out=out["pc_line"])
    np.clip(out["stepness"], 0.0, 1.0, out=out["stepness"])
    return {k: v.astype(np.float32) for k, v in out.items()}


def corroborate(ranks: list[np.ndarray], footprint: np.ndarray) -> np.ndarray:
    """EDTI-L corroboration form (reused formula, new physical inputs):
    mean footprint-rank x (0.5 + 0.5 x fraction of ranks above 0.5)."""
    mean_r = np.mean(ranks, axis=0)
    agree = np.mean([r > 0.5 for r in ranks], axis=0)
    s = (mean_r * (0.5 + 0.5 * agree)).astype(np.float32)
    s[~footprint] = 0.0
    return s
