"""GEMSDOE86 lane: gravity–magnetic cross-gradient structural coherence (GMC).

The shared instruments (metric, holdout, emission, uniqueness, writer, validator)
are vendored byte-identically in ``vendor/template66`` and imported, never forked.
This package only adds the new structural transforms and the lane driver.
"""

__all__ = ["features", "io", "emission"]
