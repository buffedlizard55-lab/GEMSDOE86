"""Lane H86P-TCWB: Downslope Radiometric Total-Count Wash-Blanket Asymmetry,
Vector-Gravity-Signed Basement Hinge Kink, One-Sided Hydrothermal Clay-Cap
Lateral Fault-Seal Termination, Seismicity-Conditioned Dilatancy Gate, and
Radial-Cover Elkan-Bayes 6-Ring Bernoulli Survival Dinkelbach-CELF."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from .features import (
    ABLATION_LOCAL_NAMES,
    TCWB_ELASTIC_NAMES,
    TCWB_STATIC_NAMES,
    build_tcwb_static_stack,
    verify_tcwb_input_contract,
)
from .model import (
    ABLATION_ELASTIC_NAMES,
    TCWBConfig,
    calibrate_global_sparse_posterior,
    fit_predict_loqo_tcwb_surfaces,
    fuse_radial_cover_tcwb,
)
from .operators import (
    aitchison_clr_radiometric_jacobian,
    claycap_lateral_fault_seal_termination,
    downslope_tc_wash_asymmetry,
    gravity_signed_basement_hinge_kink,
    seismicity_conditioned_dilatancy_gate,
)

__all__ = [
    "ABLATION_ELASTIC_NAMES",
    "ABLATION_LOCAL_NAMES",
    "TCWBConfig",
    "TCWB_ELASTIC_NAMES",
    "TCWB_STATIC_NAMES",
    "aitchison_clr_radiometric_jacobian",
    "build_tcwb_static_stack",
    "calibrate_global_sparse_posterior",
    "claycap_lateral_fault_seal_termination",
    "downslope_tc_wash_asymmetry",
    "fit_predict_loqo_tcwb_surfaces",
    "fuse_radial_cover_tcwb",
    "gravity_signed_basement_hinge_kink",
    "seismicity_conditioned_dilatancy_gate",
    "verify_tcwb_input_contract",
]
