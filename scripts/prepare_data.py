#!/usr/bin/env python3
"""Prepare and audit the competition rasters for GEMSDOE86.

Reads training_features.tif (19 bands), labels.tif/existing_faults.tif, and
sample_submission.tif from data_dir, audits CRS (EPSG:32611), shape (3730x3292),
100 m geotransform, and sentinel pixels inside the 5,167,373-pixel footprint,
writes per-band .npy arrays to work_dir/bands when training_features.tif is present,
and saves the full audit receipt to data/prepared_manifest.json.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gems86.io import BANDS, BY_NAME, NODATA

EXPECTED_EPSG = 32611
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_TRANSFORM = (100.0, 0.0, 275500.0, 0.0, -100.0, 4496600.0)
EXPECTED_FOOTPRINT_PIXELS = 5167373
EXPECTED_CATALOGUE_PIXELS = 60988

PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_file(dirs: list[Path], filenames: list[str]) -> Path | None:
    for d in dirs:
        for fn in filenames:
            candidate = d / fn
            if candidate.is_file():
                return candidate
    return None


def prepare(data_dir: Path | None = None, work_dir: Path | None = None, fetch_if_missing: bool = False) -> dict:
    if data_dir is None:
        data_dirs = [ROOT / "data", ROOT / "data" / "bridge"]
    else:
        data_dirs = [Path(data_dir)]

    if work_dir is None:
        work_dir = ROOT / ".cache" / "gems_work"
    else:
        work_dir = Path(work_dir)

    bands_dir = work_dir / "bands"
    bands_dir.mkdir(parents=True, exist_ok=True)

    tmpl_path = find_file(data_dirs, ["sample_submission.tif", "example_submission.tif"])
    lab_path = find_file(data_dirs, ["existing_faults.tif", "labels.tif"])
    feat_path = find_file(data_dirs, ["training_features.tif", "gems-geodawn-numerical-features.tif"])

    if fetch_if_missing and (tmpl_path is None or lab_path is None or feat_path is None):
        restore_script = ROOT / "scripts" / "restore_data.py"
        if restore_script.is_file():
            print("Fetching missing files via scripts/restore_data.py...", flush=True)
            subprocess.run([sys.executable, str(restore_script)], check=False)
            tmpl_path = find_file(data_dirs, ["sample_submission.tif", "example_submission.tif"])
            lab_path = find_file(data_dirs, ["existing_faults.tif", "labels.tif"])
            feat_path = find_file(data_dirs, ["training_features.tif", "gems-geodawn-numerical-features.tif"])

    if tmpl_path is None or lab_path is None:
        raise FileNotFoundError(
            "Missing required competition template or fault files. "
            "Run `python scripts/restore_protocol_data.py` or `bash scripts/download_competition_data.sh`."
        )

    # 1. Audit sample_submission template
    with rasterio.open(tmpl_path) as tmpl:
        epsg = tmpl.crs.to_epsg() if tmpl.crs else None
        if epsg != EXPECTED_EPSG:
            raise ValueError(f"Expected EPSG:{EXPECTED_EPSG}, got {tmpl.crs}")
        shape_hw = (tmpl.height, tmpl.width)
        if shape_hw != EXPECTED_SHAPE:
            raise ValueError(f"Expected shape {EXPECTED_SHAPE}, got {shape_hw}")
        transform_tuple = tuple(float(v) for v in tmpl.transform)[:6]
        foot_arr = tmpl.read(1)
        foot = np.isfinite(foot_arr)

    # 2. Audit existing faults / labels
    with rasterio.open(lab_path) as lab_src:
        if (lab_src.height, lab_src.width) != shape_hw:
            raise ValueError("labels/existing_faults shape mismatch")
        lab_raw = lab_src.read(1)
        lab = (lab_raw == 1) & foot

    np.save(bands_dir / "_footprint.npy", foot)
    np.save(bands_dir / "_labels.npy", lab)

    band_stats = []
    total_sentinel_in_foot = 0
    any_sentinel_in_foot = np.zeros(shape_hw, dtype=bool)
    has_features = feat_path is not None and feat_path.is_file()

    if has_features:
        with rasterio.open(feat_path) as feat_src:
            if (feat_src.height, feat_src.width) != shape_hw:
                raise ValueError("training_features.tif shape mismatch")
            nd = feat_src.nodata
            for idx in range(1, 20):
                bname = BANDS.get(idx, f"band_{idx}")
                arr = feat_src.read(idx).astype(np.float32)
                is_sentinel = (~np.isfinite(arr)) | (arr < -1e38)
                if nd is not None and not np.isnan(nd):
                    is_sentinel |= arr == nd
                sentinel_in_foot = int(np.sum(is_sentinel & foot))
                total_sentinel_in_foot += sentinel_in_foot
                any_sentinel_in_foot |= is_sentinel & foot

                arr[is_sentinel] = np.nan
                arr[~foot] = np.nan
                np.save(bands_dir / f"{idx:02d}_{bname}.npy", arr)

                valid_vals = arr[foot & np.isfinite(arr)]
                band_stats.append({
                    "index": idx,
                    "name": bname,
                    "finite_in_footprint": int(valid_vals.size),
                    "sentinel_in_footprint": sentinel_in_foot,
                    "min": float(np.min(valid_vals)) if valid_vals.size else None,
                    "p05": float(np.percentile(valid_vals, 5)) if valid_vals.size else None,
                    "median": float(np.median(valid_vals)) if valid_vals.size else None,
                    "p95": float(np.percentile(valid_vals, 95)) if valid_vals.size else None,
                    "max": float(np.max(valid_vals)) if valid_vals.size else None,
                })

    source_hashes = {
        "sample_submission": sha256_file(tmpl_path),
        "existing_faults": sha256_file(lab_path),
    }
    if has_features and feat_path:
        source_hashes["training_features"] = sha256_file(feat_path)

    manifest = {
        "schema_version": 1,
        "prepared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grid": {
            "epsg": epsg,
            "height": shape_hw[0],
            "width": shape_hw[1],
            "total_cells": int(shape_hw[0] * shape_hw[1]),
            "transform": list(transform_tuple),
            "pixel_size_m": [100.0, 100.0],
        },
        "counts": {
            "footprint_valid_pixels": int(foot.sum()),
            "outside_footprint_pixels": int((~foot).sum()),
            "positive_catalogue_label_pixels": int(lab.sum()),
            "negative_in_footprint_pixels": int(foot.sum() - lab.sum()),
            "has_features": has_features,
            "total_sentinel_band_pixels_inside_footprint": total_sentinel_in_foot,
            "unique_footprint_pixels_with_any_sentinel": int(any_sentinel_in_foot.sum()),
        },
        "source_paths": {
            "sample_submission": str(tmpl_path.relative_to(ROOT)),
            "existing_faults": str(lab_path.relative_to(ROOT)),
            "training_features": str(feat_path.relative_to(ROOT)) if feat_path else None,
        },
        "source_hashes": source_hashes,
        "bands": band_stats,
    }

    out_path = ROOT / "data" / "prepared_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=None, help="Directory containing competition TIFFs (data/ or data/bridge/)")
    parser.add_argument("--work-dir", default=None, help="Directory for band cache output (.cache/gems_work/)")
    parser.add_argument("--fetch", action="store_true", help="Attempt to restore missing files via scripts/restore_data.py")
    args = parser.parse_args()

    manifest = prepare(
        data_dir=Path(args.data_dir) if args.data_dir else None,
        work_dir=Path(args.work_dir) if args.work_dir else None,
        fetch_if_missing=args.fetch,
    )
    counts = manifest["counts"]
    print(
        f"[GEMSDOE86 prepare_data] Grid: {manifest['grid']['height']}x{manifest['grid']['width']} "
        f"EPSG:{manifest['grid']['epsg']} | Footprint={counts['footprint_valid_pixels']:,} px | "
        f"Catalogue={counts['positive_catalogue_label_pixels']:,} px | "
        f"Features: {'19 bands prepared' if counts['has_features'] else 'pending training_features.tif'}"
    )


if __name__ == "__main__":
    main()
