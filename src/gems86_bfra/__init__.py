"""Lane H86Q-BFRA: Broken-Plate Basement Flexural Shear & Rollover + Two-Endmember
Piedmont Regolith/Metasomatic Unmixing + Oblique TMI-vs-RTP Remanence Dislocation
+ Quadrant-Repaired Eroded LOQO + 1-D Strand-Sharp Two-Regime Dinkelbach-CELF."""

from .features import (
    ABLATION_LOCAL_NAMES,
    BFRA_ELASTIC_NAMES,
    BFRA_STATIC_NAMES,
    build_bfra_static_stack,
    verify_bfra_input_contract,
)
from .model import BFRAConfig, fit_predict_loqo_bfra_surfaces
from .operators import (
    broken_plate_flexural_shear_and_rollover,
    regolith_and_metasomatic_unmixing,
    strand_tangent_sharpen_posterior,
    tmi_vs_rtp_remanence_dislocation,
)

__all__ = [
    "ABLATION_LOCAL_NAMES",
    "BFRAConfig",
    "BFRA_ELASTIC_NAMES",
    "BFRA_STATIC_NAMES",
    "broken_plate_flexural_shear_and_rollover",
    "build_bfra_static_stack",
    "fit_predict_loqo_bfra_surfaces",
    "regolith_and_metasomatic_unmixing",
    "strand_tangent_sharpen_posterior",
    "tmi_vs_rtp_remanence_dislocation",
    "verify_bfra_input_contract",
]
