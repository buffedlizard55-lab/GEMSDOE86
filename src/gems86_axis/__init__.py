"""Single-AXIS edits of a named parent raster (brief v2, section 5).

This package deliberately does *not* contain a model.  Every function takes the parent's
own dot mask plus hash-pinned inputs and returns a new dot mask that differs from the
parent on exactly one declared axis, so a live-score delta can be attributed.

Evidence discipline (brief section 8): nothing in here produces a score.  The DTI numbers
this package can compute are labelled MODEL (local arithmetic on the official metric) or
PROXY (catalogue hide-and-recover).  Only a submission-page receipt is a RECEIPT.
"""
from __future__ import annotations

__all__ = ["grid_io", "bands", "variants", "gates"]
