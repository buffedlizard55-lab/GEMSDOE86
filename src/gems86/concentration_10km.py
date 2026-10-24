"""10 km fault-system-scale CONCENTRATION dispersal prior for GEMSDOE86.

Why this module exists
----------------------
``IR-86-TRACKB-08`` and ``SLOT_PLAN.md`` proposal 2 identify the 10 km
(100 px, fault-system scale) block as the one ``CONCENTRATION`` scale never
built: the 1 km and 5 km sessions are spent (9 BUILT rows).  This module adds
exactly one new ingredient on top of the audited 5 km machinery
(``gems86.concentration_5km``): an *occupied-block density* prior whose sign is
flipped, so the existing ``relocate_5km_ridge_up`` engine — donors taken from
the lowest-prior blocks in ascending unique-credit order, destinations placed
greedily on unused ancestor-ridge cells in the highest-prior blocks at
``> 3.0 px`` catalogue clearance and ``>= sqrt(8) px`` spacing — becomes a
*dispersal* engine: donors come out of the densest occupied 10 km blocks and
destinations land in the sparsest occupied 10 km blocks.

Blocks with no parent dot are excluded from both roles (prior = ``-inf``):
the 1 km CV-band session showed that scattering into unoccupied desert blocks
is what the off-ridge builds died of (``IR-86-CONC-10``), and an occupied
sparse block at least carries one piece of parent evidence.  Every other
constraint (count fixed, ridge support, clearance, spacing, prefix nesting
across doses at a fixed destination fraction) is inherited unchanged from the
5 km module and is re-asserted by the runner, not assumed here.
"""
from __future__ import annotations

from typing import Any

import numpy as np

try:
    from gems86 import concentration_5km as C5
except ImportError:  # pragma: no cover
    from src.gems86 import concentration_5km as C5


def occupied_density_blocks(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    *,
    block_px: int = 100,
    min_foot_frac: float = 0.05,
) -> dict[str, Any]:
    """Occupied-block dot density on the padded ``block_px`` grid.

    Returns the density blocks, raw counts, the valid (occupied and at least
    ``min_foot_frac`` footprint) mask, and ``prior_blocks = -density`` on
    valid blocks (``-inf`` elsewhere) in the exact shape
    ``concentration_5km.relocate_5km_ridge_up`` consumes.  With that prior the
    relocation engine's donors are the dots in the *densest* occupied blocks
    and its destinations are the *sparsest* occupied blocks.
    """
    parent = np.asarray(parent_dots, dtype=bool) & np.asarray(footprint, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    counts = C5._block_sum_padded(parent, block_px)
    foot_cells = C5._block_sum_padded(foot, block_px)
    density = counts / np.maximum(foot_cells, 1.0)
    valid = (counts > 0) & (foot_cells >= float(min_foot_frac) * float(block_px) ** 2)
    prior = np.where(valid, -density, -np.inf).astype(np.float64)
    return dict(
        density_blocks=density.astype(np.float64),
        count_blocks=counts.astype(np.float64),
        footprint_blocks=foot_cells.astype(np.float64),
        valid_blocks=valid,
        prior_blocks=prior,
        block_px=int(block_px),
        n_valid_blocks=int(valid.sum()),
    )


def relocate_b10km_down(
    parent_dots: np.ndarray,
    footprint: np.ndarray,
    edt_cat: np.ndarray,
    ridge_union: np.ndarray,
    density: dict[str, Any],
    *,
    n_move: int,
    dest_block_frac: float,
    unique_credit_dots: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Disperse ``n_move`` dots from dense to sparse occupied 10 km blocks.

    Thin, auditable wrapper: all placement logic, spacing, clearance and
    statistics come from ``concentration_5km.relocate_5km_ridge_up`` with
    ``block_px=100`` and the sign-flipped density prior.  At a fixed
    ``dest_block_frac`` the source and destination orderings are computed
    once, so a smaller ``n_move`` is a strict prefix of a larger one.
    """
    out, src_rc, dst_rc, stats = C5.relocate_5km_ridge_up(
        parent_dots,
        footprint,
        edt_cat,
        ridge_union,
        density["prior_blocks"],
        n_move=int(n_move),
        block_px=int(density["block_px"]),
        dest_block_frac=float(dest_block_frac),
        unique_credit_dots=unique_credit_dots,
    )
    stats["dest_block_frac"] = float(dest_block_frac)
    stats["block_px"] = int(density["block_px"])
    stats["n_valid_occupied_blocks"] = int(density["n_valid_blocks"])
    return out, src_rc, dst_rc, stats
