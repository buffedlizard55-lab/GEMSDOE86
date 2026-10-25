"""H86I-RKSC: Lahontan-Deconfounded Piedmont Scarp Profile-Curvature Dipole
coupled with GeoDAWN Radiometric K/eTh/TC Provenance-Metasomatism Step and
Thermal-Seismic Upflow Conduit.
"""
from .features import (
    ARM_NAMES,
    FEATURE_NAMES,
    REQUIRED_BANDS,
    compose_rksc_arms,
    compute_rksc_arrays,
    compute_rksc_from_tif,
)

__all__ = [
    "ARM_NAMES",
    "FEATURE_NAMES",
    "REQUIRED_BANDS",
    "compose_rksc_arms",
    "compute_rksc_arrays",
    "compute_rksc_from_tif",
]
