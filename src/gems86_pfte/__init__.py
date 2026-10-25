"""Lane H86M-PFTE:
3-D Cordell-Parker Spectral Compaction-Stripped Marussi Gravity Tensor Eigensystem,
Baranov Pseudogravity Decoupling & Strike-Guided Peclet Dispersion with
3-Strand Frechet-Comonotonic Fault-Tube Survival Dinkelbach-CELF Allocation."""

from .comonotonic_dcelf import (
    ComonotonicDCELFAllocation,
    comonotonic_dcelf_allocate_dots,
    comonotonic_tube_self_credit,
    static_ek_spacing_allocate,
)
from .features import (
    FOLD_ELASTIC_NAMES,
    PFTE_ABLATION_NAMES,
    PFTE_STATIC_NAMES,
    baranov_pseudogravity_decoupling,
    build_pfte_static_stack,
    cordell_parker_3d_basin_strip,
    marussi_curvature_eigensystem,
    peclet_across_strike_barrier,
    verify_pfte_input_contract,
)
from .model import (
    PFTEConfig,
    calibrate_quadrant_sparse_posterior,
    fit_predict_loqo_blind_pfte,
    fit_predict_loqo_kinematic_pfte,
    fuse_calibrated_noisy_or,
    quadrant_grid,
    rank01_on_mask,
)

__all__ = [
    "ComonotonicDCELFAllocation",
    "FOLD_ELASTIC_NAMES",
    "PFTEConfig",
    "PFTE_ABLATION_NAMES",
    "PFTE_STATIC_NAMES",
    "baranov_pseudogravity_decoupling",
    "build_pfte_static_stack",
    "calibrate_quadrant_sparse_posterior",
    "comonotonic_dcelf_allocate_dots",
    "comonotonic_tube_self_credit",
    "cordell_parker_3d_basin_strip",
    "fit_predict_loqo_blind_pfte",
    "fit_predict_loqo_kinematic_pfte",
    "fuse_calibrated_noisy_or",
    "marussi_curvature_eigensystem",
    "peclet_across_strike_barrier",
    "quadrant_grid",
    "rank01_on_mask",
    "static_ek_spacing_allocate",
    "verify_pfte_input_contract",
]
