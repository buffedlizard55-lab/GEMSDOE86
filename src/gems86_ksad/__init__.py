"""H86I-KSAD: Kostrov-Byerlee Azimuthal Slip/Dilation Tendency, Upward-Continued
Depth Persistence, and SAR Cover-Propensity Dinkelbach Submodular K3 Allocation.
"""
from .allocator import (
    dinkelbach_submodular_k3_allocate,
    elkan_bayes_recalibrate,
    pointwise_disc_thin,
)
from .physics import (
    COVER_BLIND_STATIC_NAMES,
    ELASTIC_FEATURE_NAMES,
    STATIC_FEATURE_NAMES,
    TOPO100_NATIVE_NAMES,
    build_static_features,
    compute_exposure_propensity,
    compute_kostrov_elastic_fields,
)

__all__ = [
    "COVER_BLIND_STATIC_NAMES",
    "ELASTIC_FEATURE_NAMES",
    "STATIC_FEATURE_NAMES",
    "TOPO100_NATIVE_NAMES",
    "build_static_features",
    "compute_exposure_propensity",
    "compute_kostrov_elastic_fields",
    "dinkelbach_submodular_k3_allocate",
    "elkan_bayes_recalibrate",
    "pointwise_disc_thin",
]
