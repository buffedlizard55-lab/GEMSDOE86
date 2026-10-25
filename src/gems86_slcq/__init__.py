"""Lane H86M-SLCQ: Dip-Adaptive Salem Tilt-Contact Pullback x Steerable 8-Azimuth
Log-Cauchy Step-vs-Dike Symmetry + Fold-Safe Basement Mass-Balance Residual (BMR)
& Up-Hydraulic-Head Geothermal Conduit Discovery with 5-Fold (80/20 Hide-Matched)
Strict LOQO and Exact 6-Ring Bernoulli Survival Dinkelbach-CELF."""

from .operators import (
    adaptive_vector_updip_pullback,
    fit_predict_fold_safe_bmr,
    garland_poisson_admittance_jump,
    salem_adaptive_dip_and_sharpness,
    steerable_log_cauchy_step_vs_dike,
)
from .features import (
    ABLATION_LOCAL_NAMES,
    BLIND_CONDUIT_NAMES,
    BMR_FOLD_NAMES,
    ELASTIC_NAMES,
    SLCQ_STATIC_NAMES,
    build_slcq_static_stack,
)
from .model import (
    SLCQConfig,
    calibrate_footprint_quadrant_posterior,
    fit_predict_oof_slcq,
    fuse_cover_conditioned_noisy_or,
    true_footprint_quadrants,
)

__all__ = [
    "ABLATION_LOCAL_NAMES",
    "BLIND_CONDUIT_NAMES",
    "BMR_FOLD_NAMES",
    "ELASTIC_NAMES",
    "SLCQConfig",
    "SLCQ_STATIC_NAMES",
    "adaptive_vector_updip_pullback",
    "build_slcq_static_stack",
    "calibrate_footprint_quadrant_posterior",
    "fit_predict_fold_safe_bmr",
    "fit_predict_oof_slcq",
    "fuse_cover_conditioned_noisy_or",
    "garland_poisson_admittance_jump",
    "salem_adaptive_dip_and_sharpness",
    "steerable_log_cauchy_step_vs_dike",
    "true_footprint_quadrants",
]
