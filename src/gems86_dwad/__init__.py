"""Lane H86S-DWAD: Detectability-Weighted Exposure-Deconfounded PU +
Downslope Canyon-Mouth Fluvial Knickzone Back-Projection + Sub-Clay-Cap
Geothermal Feeder-Margin Disjunction + Dual-Regime Stepover-Preserving
6-Ring Dinkelbach-CELF."""

from .features import (
    DWAD_ABLATION_NAMES,
    DWAD_CONT_NAMES,
    DWAD_STATIC_NAMES,
    build_dwad_static_stack,
    verify_dwad_input_contract,
)
from .model import (
    DWADConfig,
    compute_dwad_continuation_fields,
    fit_predict_loqo_dwad_surfaces,
)
from .operators import (
    compute_survey_observability,
    dilatational_stepover_sharpen,
    downslope_canyon_knickzone_backprojection,
    mohr_coulomb_conjugate_slip_tendency,
    prior_weighted_quadrant_blend,
    sub_claycap_geothermal_feeder_disjunction,
)

__all__ = [
    "DWADConfig",
    "DWAD_ABLATION_NAMES",
    "DWAD_CONT_NAMES",
    "DWAD_STATIC_NAMES",
    "build_dwad_static_stack",
    "compute_dwad_continuation_fields",
    "compute_survey_observability",
    "dilatational_stepover_sharpen",
    "downslope_canyon_knickzone_backprojection",
    "fit_predict_loqo_dwad_surfaces",
    "mohr_coulomb_conjugate_slip_tendency",
    "prior_weighted_quadrant_blend",
    "sub_claycap_geothermal_feeder_disjunction",
    "verify_dwad_input_contract",
]
