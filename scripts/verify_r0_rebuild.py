#!/usr/bin/env python3
"""Gate 0 of session brief v2 section 5: rebuild R0 and match its sha256.

The H33 model itself is not vendored (IR-86-PRUNE-02), so R0 is rebuilt as the *lineage
step*: take the pinned 40,199-dot solo-d2.8 base and delete every dot within 2.0 px of a
mapped-fault cell.  The result is serialised with the parent's own GeoTIFF profile and the
byte digest is compared to the published file.  If the digest differs, the session stops:
the parent is never approximated.

Writes ``evidence/r0_rebuild_20261023.json``.  No DrivenData endpoint is contacted.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]

PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
}
PINS = {
    "sample": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "catalogue": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
}
CLEARANCE_PX = 2.0


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> int:
    receipt: dict = {"task": "rebuild R0 from pinned bytes and match sha256",
                     "inputs": {}, "cleared": True}
    for name, path in PATHS.items():
        digest = sha256(path)
        if digest != PINS[name]:
            print(f"FAIL pinned input {name}: {digest} != {PINS[name]}")
            return 1
        receipt["inputs"][name] = {"path": str(path.relative_to(ROOT)), "sha256": digest}

    with rasterio.open(PATHS["sample"]) as src:
        footprint = np.isfinite(src.read(1))
        sample_grid = {"crs": str(src.crs), "transform": list(src.transform)[:6],
                       "shape": [src.height, src.width]}
    with rasterio.open(PATHS["catalogue"]) as src:
        catalogue = src.read(1) == 1
    with rasterio.open(PATHS["base"]) as src:
        base_arr = src.read(1)
        base_profile = src.profile.copy()
    with rasterio.open(PATHS["parent"]) as src:
        parent_arr = src.read(1)
        parent_profile = src.profile.copy()

    base = footprint & np.isfinite(base_arr) & (base_arr > 0.5)
    parent_dots = footprint & (np.nan_to_num(parent_arr, nan=0.0) > 0.5)
    rebuilt = base & (ndi.distance_transform_edt(~catalogue) > CLEARANCE_PX)

    receipt["dots"] = {"base": int(base.sum()), "rebuilt": int(rebuilt.sum()),
                       "published_parent": int(parent_dots.sum())}
    receipt["dot_set_identity"] = {
        "differing_cells_vs_published_parent": int((rebuilt ^ parent_dots).sum()),
        "identical": bool(np.array_equal(rebuilt, parent_dots)),
    }
    if not receipt["dot_set_identity"]["identical"]:
        print("FAIL rebuilt dot set differs from the published parent")
        (ROOT / "evidence").mkdir(exist_ok=True)
        (ROOT / "evidence/r0_rebuild_20261023.json").write_text(json.dumps(receipt, indent=2))
        return 1

    profile = parent_profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                   predictor=3, zlevel=9, interleave="band",
                   tiled=True, blockxsize=256, blockysize=256, nodata=None)
    arr = np.where(footprint, rebuilt, 0.0).astype(np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "r0-rebuild-zeros.tif"
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(arr, 1)
        rebuilt_sha = sha256(out)
        rebuilt_bytes = out.stat().st_size

    published_sha = PINS["parent"]
    receipt["file_identity"] = {
        "rebuilt_sha256": rebuilt_sha, "published_sha256": published_sha,
        "sha256_match": rebuilt_sha == published_sha,
        "rebuilt_bytes": rebuilt_bytes,
        "published_bytes": PATHS["parent"].stat().st_size,
        "serialisation": {k: str(profile[k]) for k in
                          ("compress", "tiled", "blockxsize", "blockysize", "nodata")},
    }
    receipt["grid"] = sample_grid
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/r0_rebuild_20261023.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt["dots"], indent=2))
    print(json.dumps(receipt["file_identity"], indent=2))
    if not receipt["file_identity"]["sha256_match"]:
        print("FAIL byte digest differs: the parent is not reproducible and no variant may be built")
        return 1
    print("PASS R0 rebuilt byte-exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
