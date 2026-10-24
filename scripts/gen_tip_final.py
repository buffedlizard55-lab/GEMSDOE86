#!/usr/bin/env python3
"""Historical diagnostic script for PR #63's H86-TIPRELAY experiment, now gated
fail-closed behind ``scripts.protocol_preflight.require_feasible()``.

Forensic status (IR-86-TIPRELAY-01, 2026-10-24):
  - Revoked as ``verdict: "negative"`` (``DO NOT SUBMIT``).
  - Even against sparse fleet rasters alone, PR #63's raster
    (``c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3``) had
    ``my_dots_within_3px_of_theirs = 0.8508 > 0.70`` vs ``GEMSDOE32``
    ``h33-h33-2-b2``, ``0.8510 > 0.70`` vs ``GEMSDOE28`` ``h27-4-r1-solo-d2-8``,
    and ``1.0 > 0.70`` vs the pinned ``17GEMSDOE`` continuous witness, with
    zero spatially-blocked holdout evaluation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
