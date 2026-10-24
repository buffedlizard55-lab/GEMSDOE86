"""Pediment-window CONCENTRATION arms on R0 (pre-registered unbuilt proposal #2).

Slot plan 2026-10-23 (``IR-86-TRACKB-08`` proposal 2, ``evidence/concentration-5km-mechanism.md``):
restrict the sparse-block ridge additions of the session's best both-instruments arm
``concb5kmdown4`` to *thin-alluvium pediment windows*, and attribute the gain by splitting
the destination pool into pediment / non-pediment halves.

* *Mechanism:* Concealed Quaternary faults under thin (10-40 m) alluvium more than 1 km
  from a range front are systematically under-represented in the mapped catalogue (SGMC
  maps bedrock expression, not buried traces), so a relocated lineament dot placed on the
  pinned ancestor-ridge surface inside such a window has a higher probability of paying
  against *new-fault* truth than one placed in an already well-mapped bedrock corridor.
* *Confounder:* Fluvial terrace risers and pluvial (Lahontan) shoreline scarps occupy the
  exact same low-relief elevation band -- the window is not fault-specific.
* *Falsifier:* the non-pediment complement arm matching or beating the pediment arm on
  the SGMC ``MODEL`` surrogate says the gain is generic sparse-ridge coverage, not the
  pediment prior.

The window is built ONLY from truth-free evidence bands (USGS 3DEP-derived local relief
and the detrended-elevation relief-regime map the RELIEF axis already uses). No catalogue
byte, no SGMC byte, and no scored-truth byte enters :func:`pediment_window`, which is what
makes the mask fold-fair by construction.

All three arms reuse ``concentration_5km.relocate_cvband_down`` unchanged: identical
source shave (>= 3-dot 1 km clusters, lowest unique-credit dot popped first), identical
count fix, identical ``> 3 px`` catalogue clearance and ``>= sqrt(8) px`` spacing. The
arms differ ONLY in where the vacated dots land:

* ``b5km-ped-down2p5``     941 dots (5.00 % changed), dest inside the pediment window
                           (the window's spacing-limited capacity is 1,045 moved);
* ``b5km-nonped-down2p5``  941 dots, dest = the exact complement (dose-matched
                           attribution control);
* ``b5km-ped-down5``       1,882 dots (10.00 % changed), dest pediment-first with
                           spillover (``dest_prefer``; dose-response arm).
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage as ndi

from gems86 import mass_econ
from gems86.concentration_5km import block_density_stats, relocate_cvband_down

#: Pre-registered window bounds (evidence/concentration-5km-mechanism.md, 2026-10-23).
PEDIMENT_RELIEF_LO_M = 10.0
PEDIMENT_RELIEF_HI_M = 40.0
#: ">1 km from range front" at the pinned 100 m grid.
FRONT_DIST_PX = 10.0


def pediment_window(
    relief_local_m: np.ndarray,
    range_front: np.ndarray,
    footprint: np.ndarray,
    *,
    relief_lo_m: float = PEDIMENT_RELIEF_LO_M,
    relief_hi_m: float = PEDIMENT_RELIEF_HI_M,
    front_dist_px: float = FRONT_DIST_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Truth-free pediment mask: local relief in ``[lo, hi]`` m, > ``front_dist_px`` from any
    range-front cell (the RELIEF axis's regime-2 scarp, so "front" means the same thing on
    every axis that reuses the regime map).

    Raises if the window selects nothing or if the relief band carries non-finite values
    inside the footprint (a scrubbed-reader bug, not a geological result -- the sentinel
    failure mode recorded in IRREGULARITIES.md for the first RELIEF pass).
    """
    foot = np.asarray(footprint, bool)
    rl = np.asarray(relief_local_m, np.float64)
    fr = np.asarray(range_front, bool)
    if rl.shape != foot.shape or fr.shape != foot.shape:
        raise ValueError("relief/range-front/footprint must share a shape")
    if not np.all(np.isfinite(rl[foot])):
        raise ValueError("relief_local has non-finite values inside the footprint")
    if fr.any() and not (fr & foot).any():
        raise ValueError("range-front mask lies entirely outside the footprint")
    dist_front = ndi.distance_transform_edt(~fr)
    ped = foot & (rl >= float(relief_lo_m)) & (rl <= float(relief_hi_m)) & (dist_front > float(front_dist_px))
    info = dict(
        relief_lo_m=float(relief_lo_m),
        relief_hi_m=float(relief_hi_m),
        front_dist_px=float(front_dist_px),
        front_dist_source="EDT of RELIEF-axis regime-2 (range-front) cells",
        n_window_px=int(ped.sum()),
        pct_footprint=round(float(ped.sum()) / max(int(foot.sum()), 1), 4),
        evidence_sources=[
            "ext_topo_10m_derived_100m_u8 band relief_local (USGS 3DEP 10 m derived, public domain)",
            "training_features bands 12/19 det_elev & det_elev_slope -> gems86.relief regime map",
        ],
        truth_inputs_used="NONE (mask is fold-fair by construction)",
    )
    if not ped.any():
        raise ValueError("pediment window selected nothing; check band scrubbing/bounds")
    return ped, info


def build_ped_down(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    pediment: np.ndarray,
    *,
    n_move: int,
    mode: str,
    unique_credit_dots: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """One pediment CONCENTRATION arm. ``mode`` is one of

    ``"ped"``       destinations strictly inside the pediment window;
    ``"nonped"``    destinations strictly in the complement (attribution control);
    ``"ped_first"`` destinations pediment-first with spillover (dose arm).

    Raises ``ValueError`` (capacity) exactly like the base builder; callers decide the
    fallback (the script logs it and switches the fold/probe to ``ped_first``).
    """
    ped = np.asarray(pediment, bool)
    if mode == "ped":
        return relocate_cvband_down(
            parent_dots, footprint, edt_cat, ridge_union,
            n_move=n_move, unique_credit_dots=unique_credit_dots, dest_filter=ped,
        )
    if mode == "nonped":
        return relocate_cvband_down(
            parent_dots, footprint, edt_cat, ridge_union,
            n_move=n_move, unique_credit_dots=unique_credit_dots, dest_filter=~ped,
        )
    if mode == "ped_first":
        return relocate_cvband_down(
            parent_dots, footprint, edt_cat, ridge_union,
            n_move=n_move, unique_credit_dots=unique_credit_dots, dest_prefer=ped,
        )
    raise ValueError(f"unknown mode {mode!r}")


def destination_regime_shares(
    dst_rc: np.ndarray, pediment: np.ndarray, ridge_union: np.ndarray
) -> dict[str, float]:
    """Where did the moved dots land: pediment / non-pediment, on-ridge fractions."""
    if len(dst_rc) == 0:
        return dict(n_dst=0, ped_fraction=0.0, nonped_fraction=0.0, ridge_fraction=0.0)
    r, c = dst_rc[:, 0], dst_rc[:, 1]
    on_ped = pediment[r, c]
    on_ridge = np.asarray(ridge_union, bool)[r, c]
    n = float(len(dst_rc))
    return dict(
        n_dst=int(n),
        ped_fraction=round(float(on_ped.sum()) / n, 4),
        nonped_fraction=round(float((~on_ped).sum()) / n, 4),
        ridge_fraction=round(float(on_ridge.sum()) / n, 4),
    )


def block_density_cv_filtered(
    dots: np.ndarray, footprint: np.ndarray, block_px: int, min_fb_frac: float = 1.0
) -> float:
    """Occupied block-density CV over blocks with at least ``min_fb_frac`` footprint cover.

    ``IR-86-TRACKB-08``'s 10 km numbers (R0 = 0.570, top files 0.547-0.570) are
    reproduced exactly by ``min_fb_frac=1.0`` (fully covered 100 px blocks only);
    the unfiltered 10 km value on R0 is 0.736. Both are reported so the scales
    never get mixed.
    """
    m = np.asarray(dots, bool) & np.asarray(footprint, bool)
    f = np.asarray(footprint, bool)
    h, w = m.shape
    nb, mb = h // block_px, w // block_px
    d = m[: nb * block_px, : mb * block_px].astype(np.float64).reshape(nb, block_px, mb, block_px).sum((1, 3))
    fb = f[: nb * block_px, : mb * block_px].astype(np.float64).reshape(nb, block_px, mb, block_px).sum((1, 3))
    dens = d / np.maximum(fb, 1.0)
    occ = (d > 0) & (fb >= min_fb_frac * block_px * block_px)
    if not occ.any():
        return float("nan")
    return float(dens[occ].std() / dens[occ].mean())


def cv_report(
    parent: np.ndarray, arms: dict[str, np.ndarray], footprint: np.ndarray
) -> dict[str, Any]:
    """Occupied block-density CV at 1 km / 5 km / 10 km for R0 and every arm.

    1 km / 5 km reuse the committed ``density_cv_occupied`` definition (matches the
    5 km session's R0 values 0.6235 / 0.7442).  The 10 km column uses the
    fully-covered-block definition that reproduces ``IR-86-TRACKB-08`` (R0 0.570);
    REPORT ONLY, never a gate.
    """
    out: dict[str, Any] = {}
    for name, dots in {"R0": parent, **arms}.items():
        out[name] = {
            "cv_1km": round(float(block_density_stats(dots, footprint, 10)["density_cv_occupied"]), 4),
            "cv_5km": round(float(block_density_stats(dots, footprint, 50)["density_cv_occupied"]), 4),
            "cv_10km_fullcover": round(block_density_cv_filtered(dots, footprint, 100, 1.0), 4),
            "cv_10km_all_occupied": round(block_density_cv_filtered(dots, footprint, 100, 0.0), 4),
        }
    return out


def marginal_credit_or_none(dots: np.ndarray) -> np.ndarray:
    """Per-dot unique kernel credit in the builder's dot order (shared by all arms)."""
    u, _ = mass_econ.marginal_credit(np.asarray(dots, bool))
    return u
