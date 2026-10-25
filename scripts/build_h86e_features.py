"""Build the catalogue-blind H86E feature memmap (data/work/h86e_features.npy)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    sys.path[:0] = [str(ROOT / "vendor"), str(ROOT / "src")]
    from gems57 import grid
    from gems86_ridf import features

    t = time.time()
    g = grid.load_grid(ROOT / "data")
    n = features.build(
        ROOT / "data/training_features.tif",
        g.footprint,
        ROOT / "data/work/h86e_features.npy",
    )
    print(len(n), n, time.time() - t)


if __name__ == "__main__":
    main()
