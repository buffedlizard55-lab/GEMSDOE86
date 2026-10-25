"""Lane H86I-RLMS: Riedel-Listric Multi-Scale Submodular blind-fault package."""

from .allocator import bayes_prior_calibrate, disc_thin, submodular_kernel_allocate
from .features import (
    ALL_STATIC_NAMES,
    CONTINUATION_NAMES,
    E3_SCALAR_SUBSET,
    EXTERNAL_STATIC_NAMES,
    NATIVE_STATIC_NAMES,
    build_rlms_static_features,
    compute_continuation_fields,
)

__all__ = [
    "ALL_STATIC_NAMES",
    "CONTINUATION_NAMES",
    "E3_SCALAR_SUBSET",
    "EXTERNAL_STATIC_NAMES",
    "NATIVE_STATIC_NAMES",
    "bayes_prior_calibrate",
    "build_rlms_static_features",
    "compute_continuation_fields",
    "disc_thin",
    "submodular_kernel_allocate",
]
