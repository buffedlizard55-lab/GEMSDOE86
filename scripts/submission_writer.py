#!/usr/bin/env python3
"""Thin CLI wrapper delegating directly to unmodified `vendor/gems57/submission_writer.py`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import grid as GRID, submission_writer as SW  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_tif", type=Path, help="Input 2D float32 prediction GeoTIFF or .npy")
    ap.add_argument("output_tif", type=Path, help="Destination validated .tif path")
    ap.add_argument("--name", required=True, help="Submission name (<=140 chars)")
    ap.add_argument("--note", required=True, help="DrivenData portal note (<=140 chars)")
    args = ap.parse_args()

    g = GRID.load_grid(ROOT / "data" / "bridge")
    if args.input_tif.suffix.lower() == ".npy":
        pred = np.load(args.input_tif).astype(np.float32)
    else:
        with rasterio.open(args.input_tif) as ds:
            pred = ds.read(1).astype(np.float32)

    receipt = SW.write_submission(
        args.output_tif,
        pred,
        ROOT / "data" / "bridge" / "sample_submission.tif",
        g.footprint,
        note=args.note,
        name=args.name,
        catalogue=g.catalogue,
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
