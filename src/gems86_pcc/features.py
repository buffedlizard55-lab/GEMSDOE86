"""Catalogue-blind signed basement-step polarity features.

A normal-fault basement step under basin fill has a signed polarity that an
unsigned magnetic-gravity alignment does not:

* isostatic-gravity and RTP gradients point toward the footwall (shallower,
  usually more magnetic basement);
* the depth-to-basement gradient points the opposite way, toward the hanging
  wall;
* an unfaulted topographic density residual points the same way as the
  detrended-elevation gradient and is down-weighted, not used as a label.

No catalogue pixel is read here.  Band 6 is not used: pixel verification showed
it is radiometric total count, not magnetic tilt.  Flight-line and tie-line
azimuths are the GeoDAWN values published by USGS (DOI 10.5066/P93LGLVQ):
flight lines at 90 degrees, tie lines at 180 degrees.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

try:
    from gems86.io import NODATA
except ModuleNotFoundError:  # pragma: no cover
    from src.gems86.io import NODATA

# Competition band indices, 1-based, matching src/gems86/io.py.
BAND_RTP = 2
BAND_ELEV = 12
BAND_GRAV = 13
BAND_DEPTH = 15
BAND_SLOPE = 19

SCALES_PX = (1.5, 4.0)


def feature_names() -> tuple[str, ...]:
    return (
        "pcc_signed",
        "pcc_cover",
        "pcc_unsigned",
        "pcc_polarity",
        "pcc_coherence",
        "pcc_oblique",
        "pcc_topo_veto",
        "pcc_cover_weight",
    )


def rank01(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Deterministic empirical-CDF rank inside the footprint, in [0, 1]."""
    out = np.zeros(a.shape, np.float32)
    v = np.asarray(a, np.float64)[footprint]
    order = np.argsort(v, kind="stable")
    ranks = np.empty(order.size, np.float64)
    ranks[order] = np.linspace(0.0, 1.0, order.size, dtype=np.float64)
    out[footprint] = ranks.astype(np.float32)
    return out


def _clean(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    v = a.astype(np.float64, copy=True)
    good = footprint & np.isfinite(v) & (np.abs(v) < 1e20)
    if not good.any():
        raise ValueError("band has no finite footprint values")
    v[~good] = float(np.median(v[good]))
    return v


def _read_band(src: rasterio.DatasetReader, index: int, footprint: np.ndarray) -> np.ndarray:
    if index < 1 or index > src.count:
        raise ValueError(f"band {index} is outside the {src.count}-band feature stack")
    return _clean(src.read(index), footprint)


def horizontal_gradients(field: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """East and north derivatives of a north-up raster.

    ``np.gradient`` row increases south on this grid, so the north component
    is the negation of the row derivative.
    """
    smooth = ndi.gaussian_filter(field, sigma=float(sigma), mode="nearest")
    d_south, d_east = np.gradient(smooth)
    return d_east, -d_south


def _unit_dot(ax, ay, bx, by) -> np.ndarray:
    na = np.hypot(ax, ay)
    nb = np.hypot(bx, by)
    return (ax * bx + ay * by) / np.maximum(na * nb, 1e-12)


def oblique_weight(east: np.ndarray, north: np.ndarray) -> np.ndarray:
    """1 on 45-degree gradients, 0 on cardinal (flight-line / tie-line) gradients.

    A gradient pointing east or north is the cross-strike direction of an
    N-S tie-line corrugation or an E-W flight-line corrugation.  ``sin(2*az)^2``
    is zero on those axes and one at the oblique Basin-and-Range / Walker Lane
    directions.
    """
    radius2 = np.maximum(east * east + north * north, 1e-12)
    # sin(2*atan2(north, east))^2 = 4 * east^2 * north^2 / r^4
    return (4.0 * east * east * north * north) / (radius2 * radius2)


def structure_coherence(magnitude: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    """Eigenvalue coherence of the gradient structure tensor, in [0, 1]."""
    d_south, d_east = np.gradient(magnitude)
    jxx = ndi.gaussian_filter(d_east * d_east, sigma, mode="nearest")
    jyy = ndi.gaussian_filter(d_south * d_south, sigma, mode="nearest")
    jxy = ndi.gaussian_filter(d_east * d_south, sigma, mode="nearest")
    trace = jxx + jyy
    det = jxx * jyy - jxy * jxy
    gap = np.sqrt(np.maximum(trace * trace - 4.0 * det, 0.0))
    major = 0.5 * (trace + gap)
    minor = 0.5 * (trace - gap)
    return (major - minor) / (major + minor + 1e-12)


def polarity_at_scale(grav, rtp, depth, elev, sigma: float) -> dict[str, np.ndarray]:
    """Signed footwall concordance at one smoothing scale."""
    ge, gn = horizontal_gradients(grav, sigma)
    me, mn = horizontal_gradients(rtp, sigma)
    de, dn = horizontal_gradients(depth, sigma)
    ee, en = horizontal_gradients(elev, sigma)
    cos_gm = _unit_dot(ge, gn, me, mn)
    cos_gd = _unit_dot(ge, gn, de, dn)
    cos_ge = _unit_dot(ge, gn, ee, en)
    # Footwall: gravity and RTP agree; depth increases the other way.
    polarity = np.clip(cos_gm, 0.0, 1.0) * np.clip(-cos_gd, 0.0, 1.0)
    return {
        "polarity": polarity,
        "unsigned": cos_gm * cos_gm,
        "topo_align": np.clip(cos_ge, 0.0, 1.0),
        "grav_east": ge,
        "grav_north": gn,
        "grav_mag": np.hypot(ge, gn),
        "rtp_mag": np.hypot(me, mn),
        "depth_mag": np.hypot(de, dn),
    }


def assemble_scores(grav, rtp, depth, elev, slope, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Build the three preregistered arms and the canary component fields."""
    fp = np.asarray(footprint, bool)
    if any(a.shape != fp.shape for a in (grav, rtp, depth, elev, slope)):
        raise ValueError("feature arrays must match the footprint")
    fine = polarity_at_scale(grav, rtp, depth, elev, SCALES_PX[0])
    coarse = polarity_at_scale(grav, rtp, depth, elev, SCALES_PX[1])
    # Persistence: both scales must show the same signed polarity.
    polarity = np.minimum(fine["polarity"], coarse["polarity"])
    unsigned = np.minimum(fine["unsigned"], coarse["unsigned"])
    coherence = structure_coherence(fine["grav_mag"], sigma=3.0)
    oblique = oblique_weight(fine["grav_east"], fine["grav_north"])
    mag_gate = (
        rank01(fine["grav_mag"], fp)
        * rank01(fine["rtp_mag"], fp)
        * rank01(fine["depth_mag"], fp)
    )
    slope_rank = rank01(slope, fp)
    topo_explain = fine["topo_align"] * slope_rank
    topo_veto = 1.0 - 0.7 * topo_explain
    cover_weight = rank01(depth, fp) * (1.0 - slope_rank)
    signed = polarity * coherence * oblique * mag_gate * topo_veto
    cover = signed * cover_weight
    unsigned_score = unsigned * coherence * oblique * rank01(fine["grav_mag"], fp) * rank01(fine["rtp_mag"], fp)
    fields = {
        "pcc_signed": signed,
        "pcc_cover": cover,
        "pcc_unsigned": unsigned_score,
        "pcc_polarity": polarity,
        "pcc_coherence": coherence,
        "pcc_oblique": oblique,
        "pcc_topo_veto": topo_veto,
        "pcc_cover_weight": cover_weight,
    }
    out = {}
    for name in feature_names():
        field = np.zeros(fp.shape, np.float32)
        field[fp] = np.asarray(fields[name], np.float32)[fp]
        if not np.isfinite(field).all():
            raise ValueError(f"{name} is not finite")
        out[name] = field
    return out


def build_polarity_features(path: Path, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Load pinned competition bands and return catalogue-blind score fields."""
    fp = np.asarray(footprint, bool)
    path = Path(path)
    with rasterio.open(path) as src:
        if (src.height, src.width) != fp.shape:
            raise ValueError(f"feature grid {src.shape} != footprint {fp.shape}")
        if src.count < BAND_SLOPE:
            raise ValueError(f"feature stack has {src.count} bands; band {BAND_SLOPE} required")
        rtp = _read_band(src, BAND_RTP, fp)
        elev = _read_band(src, BAND_ELEV, fp)
        grav = _read_band(src, BAND_GRAV, fp)
        depth = _read_band(src, BAND_DEPTH, fp)
        slope = _read_band(src, BAND_SLOPE, fp)
    return assemble_scores(grav, rtp, depth, elev, slope, fp)
