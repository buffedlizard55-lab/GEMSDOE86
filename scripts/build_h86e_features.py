#!/usr/bin/env python3
"""Build the catalogue-blind H86E feature memmap (data/work/h86e_features.npy).

Gated by the pinned protocol preflight: historical H86E-RIDF lane is complete and negative.
"""
from __future__ import annotations

from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]

from gems57 import grid  # noqa: E402
from gems86_ridf import features  # noqa: E402


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t0 = time.time()
    g = grid.load_grid(ROOT / "data")
    names = features.build(
        ROOT / "data/training_features.tif",
        g.footprint,
        ROOT / "data/work/h86e_features.npy",
    )
    print(len(names), names, time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
