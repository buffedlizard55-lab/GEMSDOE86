"""Lane H86M-BMGS: Out-of-Quadrant Spectral Basement Mass-Balance Gravity Residual (BMR),
8-Azimuth Steerable Quadrature Odd-Step vs Even-Dike Phase Asymmetry (GSST),
Transtensional Conductance-Neck Bridge (CNT), Axial Geodesic Strand Coherence,
and Exact 6-Ring Bernoulli Survival Dinkelbach-CELF Allocation.
"""

from .features import (
    ABLATION_RAW_NAMES,
    BANNED_CSV_COLUMNS,
    BMGS_STATIC_NAMES,
    build_bmgs_static_stack,
    dilatation_gated_shallow_pullback,
    out_of_quadrant_bmr_gravity,
    steerable_quadrature_step_asymmetry,
    transtensional_conductance_neck,
    verify_bmgs_input_contract,
)
from .model import (
    BMGSConfig,
    axial_geodesic_strand_sharpen,
    elkan_quadrant_aligned_posterior,
    fit_predict_bmgs_arms_fold,
    fit_predict_bmgs_full_surface,
    quadrant_grid,
)

__all__ = [
    "ABLATION_RAW_NAMES",
    "BANNED_CSV_COLUMNS",
    "BMGSConfig",
    "BMGS_STATIC_NAMES",
    "axial_geodesic_strand_sharpen",
    "build_bmgs_static_stack",
    "dilatation_gated_shallow_pullback",
    "elkan_quadrant_aligned_posterior",
    "fit_predict_bmgs_arms_fold",
    "fit_predict_bmgs_full_surface",
    "out_of_quadrant_bmr_gravity",
    "quadrant_grid",
    "steerable_quadrature_step_asymmetry",
    "transtensional_conductance_neck",
    "verify_bmgs_input_contract",
]
