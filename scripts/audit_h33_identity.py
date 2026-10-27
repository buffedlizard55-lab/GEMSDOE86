#!/usr/bin/env python3
"""Remeasure H33 vs its historical parent; does not fit or write a candidate."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
PARENT = ("data/scored_fleet/"
          "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")
CHILD = ("data/scored_fleet/"
         "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
CATALOGUE = "data/bridge/existing_faults.tif"
PINS = {
    PARENT: "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    CHILD: "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    CATALOGUE: "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
}


def compare_arrays(parent: np.ndarray, child: np.ndarray, catalogue: np.ndarray) -> dict:
    """Measure pixel changes only; never infer hidden-truth credit or scores."""
    if parent.ndim != 2 or parent.shape != child.shape or child.shape != catalogue.shape:
        raise ValueError("Rasters must have the same two-dimensional shape")
    if not np.isin(catalogue, (-1, 0, 1)).all() or not np.any(catalogue == 1):
        raise ValueError("Catalogue must have a known footprint and mapped faults")
    footprint = catalogue >= 0
    for arr in (parent, child):
        if not np.isfinite(arr[footprint]).all() or not np.isin(arr[footprint], (0, 1)).all():
            raise ValueError("In-footprint historical rasters must be finite binary values")
    parent_dots = (parent == 1) & footprint
    child_dots = (child == 1) & footprint
    deleted = parent_dots & ~child_dots
    added = child_dots & ~parent_dots
    distance = distance_transform_edt(catalogue != 1)
    expected = parent[footprint].copy()
    expected[deleted[footprint]] = 0
    return {
        "footprint_pixels": int(footprint.sum()),
        "parent_positive_pixels": int(parent_dots.sum()),
        "child_positive_pixels": int(child_dots.sum()),
        "deleted_pixels": int(deleted.sum()),
        "added_pixels": int(added.sum()),
        "deleted_in_one_to_two_pixel_collar": int(((distance > 1) & (distance <= 2) & deleted).sum()),
        "in_footprint_differences_after_deletion": int(np.count_nonzero(expected != child[footprint])),
        "outside_footprint_pixels": int((~footprint).sum()),
        "parent_outside_nan": int(np.isnan(parent[~footprint]).sum()),
        "child_outside_nan": int(np.isnan(child[~footprint]).sum()),
        "child_outside_zero": int((child[~footprint] == 0).sum()),
    }


def audit() -> dict:
    datasets = []
    for name, expected in PINS.items():
        path = ROOT / name
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != expected:
            raise ValueError(f"Pinned input changed: {name}")
        with rasterio.open(path) as source:
            if source.count != 1:
                raise ValueError(f"Expected one raster band: {name}")
            datasets.append((source.read(1), source.crs, source.transform, source.shape))
    if any(x[1:] != datasets[0][1:] for x in datasets[1:]):
        raise ValueError("Historical grids do not match")
    result = compare_arrays(*(x[0] for x in datasets))
    return {
        "schema": "gems86.h33-identity-audit.v1",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "PIXEL-MEASUREMENT",
        "inputs_sha256": PINS,
        "grid": {"crs": str(datasets[0][1]), "rows": datasets[0][3][0], "columns": datasets[0][3][1]},
        "comparison": result,
        "interpretation": "Pixel differences do not establish hidden-truth credit or a causal score gain. Owner claims lack organizer receipts.",
        "organizer_receipts_obtained": 0,
        "model_experiments_run": 0,
        "new_rasters_written": 0,
        "submission_slots_used": 0,
    }


def main() -> None:
    result = audit()
    destination = ROOT / "docs/evidence/h33-identity-20261027.json"
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
