#!/usr/bin/env python3
"""Prepare and audit the competition rasters for GEMSDOE86.

Reads training_features.tif (19 bands), labels.tif/existing_faults.tif, and
sample_submission.tif from data_dir, audits CRS (EPSG:32611), shape (3730x3292),
100 m geotransform, and sentinel pixels inside the 5,167,373-pixel footprint,
writes per-band .npy arrays to work_dir/bands when training_features.tif is present,
and saves the live audit receipt next to the prepared arrays at
.cache/gems_work/prepared_manifest.json by default. The tracked
``data/prepared_manifest.json`` is a historical receipt, not a live cache.
"""
from __future__ import annotations

import argparse
import fcntl
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gems86.io import BANDS, BY_NAME, NODATA

EXPECTED_EPSG = 32611
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
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


def _rel_or_str(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def audit_input_grid(src, name: str, *, count: int) -> dict:
    """Validate every input, not just the sample; never repair a shifted grid."""
    epsg = src.crs.to_epsg() if src.crs else None
    if epsg != EXPECTED_EPSG:
        raise ValueError(f"{name}: expected EPSG:{EXPECTED_EPSG}, got {src.crs}")
    if src.shape != EXPECTED_SHAPE:
        raise ValueError(f"{name}: expected shape {EXPECTED_SHAPE}, got {src.shape}")
    transform = tuple(float(v) for v in src.transform)[:6]
    if transform != EXPECTED_TRANSFORM:
        raise ValueError(f"{name}: geotransform mismatch: {transform} != {EXPECTED_TRANSFORM}")
    if src.count != count:
        raise ValueError(f"{name}: expected {count} bands, got {src.count}")
    return {"epsg": epsg, "shape": list(src.shape), "transform": list(transform),
            "bands": src.count, "crs_shape_transform_match": True}


def publish_native_cache(stage: Path, bands_dir: Path, manifest_path: Path, manifest: dict) -> None:
    """Publish a fully staged native array set; roll back on ordinary failure.

    A POSIX advisory lock serializes local preparers. Directory and manifest
    replacements cannot be jointly crash-atomic across directories; this is
    explicitly recorded, not presented as an actual shared-cache transaction.
    """
    if manifest_path.resolve().is_relative_to(bands_dir.resolve()):
        raise ValueError("Manifest must not be inside the directory being replaced")
    if bands_dir.is_symlink() or (bands_dir.exists() and not bands_dir.is_dir()):
        raise ValueError("Native band output must be a real directory")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=f".{manifest_path.name}.",
                                     suffix=".partial", dir=manifest_path.parent, delete=False) as stream:
        temporary_manifest = Path(stream.name)
        try:
            json.dump(manifest, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary_manifest.unlink(missing_ok=True)
            raise
    try:
        with (bands_dir.parent / ".native-prepare.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            backup = Path(tempfile.mkdtemp(prefix=".native-bands-backup-", dir=bands_dir.parent))
            backup.rmdir()
            backed_up = published = False
            try:
                if bands_dir.exists():
                    os.replace(bands_dir, backup)
                    backed_up = True
                os.replace(stage, bands_dir)
                published = True
                os.replace(temporary_manifest, manifest_path)
            except BaseException:
                if published:
                    os.replace(bands_dir, stage)
                if backed_up:
                    os.replace(backup, bands_dir)
                raise
            else:
                if backed_up:
                    shutil.rmtree(backup, ignore_errors=True)
    finally:
        temporary_manifest.unlink(missing_ok=True)


def prepare(
    data_dir: Path | None = None,
    work_dir: Path | None = None,
    fetch_if_missing: bool = False,
    manifest_path: Path | None = None,
) -> dict:
    if data_dir is None:
        data_dirs = [ROOT / "data", ROOT / "data" / "bridge"]
    else:
        data_dirs = [Path(data_dir).resolve()]

    if work_dir is None:
        work_dir = ROOT / ".cache" / "gems_work"
    else:
        work_dir = Path(work_dir).resolve()

    bands_dir = work_dir / "bands"
    # The repository's tracked manifest is frozen historical evidence used by
    # the site and must never be replaced by a new workspace receipt, even if
    # explicitly supplied or reached through a symlink.
    out_path = (Path(manifest_path).resolve() if manifest_path is not None
                else work_dir / "prepared_manifest.json")
    if out_path.resolve() == (ROOT / "data/prepared_manifest.json").resolve():
        raise ValueError("Cannot overwrite the frozen historical preparation manifest")
    # Do not publish arrays or a manifest until ALL input identities and grids
    # pass. A same-shape CRS/transform mismatch used to be silently accepted.

    tmpl_path = find_file(data_dirs, ["sample_submission.tif", "example_submission.tif"])
    lab_path = find_file(data_dirs, ["existing_faults.tif", "labels.tif"])
    feat_path = find_file(data_dirs, ["training_features.tif", "gems-geodawn-numerical-features.tif"])

    if fetch_if_missing and (tmpl_path is None or lab_path is None or feat_path is None):
        restore_script = ROOT / "scripts" / "restore_data.py"
        if restore_script.is_file():
            print("Fetching missing files via scripts/restore_data.py...", flush=True)
            command = [sys.executable, str(restore_script)]
            if data_dir is not None:
                command += ["--dest", str(data_dirs[0])]
            subprocess.run(command, check=True)
            tmpl_path = find_file(data_dirs, ["sample_submission.tif", "example_submission.tif"])
            lab_path = find_file(data_dirs, ["existing_faults.tif", "labels.tif"])
            feat_path = find_file(data_dirs, ["training_features.tif", "gems-geodawn-numerical-features.tif"])

    if tmpl_path is None or lab_path is None:
        raise FileNotFoundError(
            "Missing required competition template or fault files. "
            "Run `python scripts/restore_protocol_data.py` or `bash scripts/download_competition_data.sh`."
        )

    # 1. Audit the grid and band count of EVERY input before publishing arrays.
    input_grids = {}
    with rasterio.open(tmpl_path) as tmpl:
        input_grids["sample_submission"] = audit_input_grid(tmpl, "sample_submission", count=1)
        epsg = tmpl.crs.to_epsg()
        shape_hw = tmpl.shape
        transform_tuple = tuple(float(v) for v in tmpl.transform)[:6]
        foot = np.isfinite(tmpl.read(1))
        if not (tmpl.read_masks(1)[foot] > 0).all():
            raise ValueError("sample_submission: validity mask excludes finite footprint cells")

    with rasterio.open(lab_path) as lab_src:
        input_grids["existing_faults"] = audit_input_grid(lab_src, "existing_faults", count=1)
        lab_raw = lab_src.read(1)
        if not (lab_src.read_masks(1)[foot] > 0).all():
            raise ValueError("existing_faults: validity mask excludes footprint cells")
        if not np.isin(lab_raw[foot], (0, 1)).all():
            raise ValueError("existing_faults: labels inside footprint must already be binary")
        lab = (lab_raw == 1) & foot
    if int(foot.sum()) != EXPECTED_FOOTPRINT_PIXELS:
        raise ValueError("sample_submission: footprint count mismatch")
    if int(lab.sum()) != EXPECTED_CATALOGUE_PIXELS:
        raise ValueError("existing_faults: catalogue count mismatch")

    has_features = feat_path is not None and feat_path.is_file()
    if has_features:
        with rasterio.open(feat_path) as feat_src:
            input_grids["training_features"] = audit_input_grid(feat_src, "training_features", count=len(BANDS))

    # Hash identity is a gate, not an informational false flag in a successful
    # manifest. Alias filenames must match the same canonical pins.
    source_paths = {"sample_submission": tmpl_path, "existing_faults": lab_path}
    if has_features:
        source_paths["training_features"] = feat_path
    source_hashes = {key: sha256_file(path) for key, path in source_paths.items()}
    for key, digest in source_hashes.items():
        if digest != PINS[f"{key}.tif"]:
            raise ValueError(f"{key}: SHA-256 mismatch; no prepared arrays published")

    work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-bands-", dir=work_dir) as staged:
        stage = Path(staged)
        np.save(stage / "_footprint.npy", foot)
        np.save(stage / "_labels.npy", lab)

        band_stats = []
        total_sentinel_in_foot = 0
        any_sentinel_in_foot = np.zeros(shape_hw, dtype=bool)

        if has_features:
            with rasterio.open(feat_path) as feat_src:
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
                    np.save(stage / f"{idx:02d}_{bname}.npy", arr)

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

        if any(sha256_file(path) != source_hashes[key] for key, path in source_paths.items()):
            raise ValueError("Input changed during preparation; no successful manifest published")

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
                "sample_submission": _rel_or_str(tmpl_path),
                "existing_faults": _rel_or_str(lab_path),
                "training_features": _rel_or_str(feat_path) if feat_path else None,
            },
            "source_hashes": source_hashes,
            "input_grid_checks": input_grids,
            "shared_template_feature_stack": False,
            "preparation_scope": "Hash-verified native bands only, not the shared cached feature stack or submission authorization.",
            "pins_verified": {
                key: source_hashes[key] == PINS[f"{key}.tif"]
                for key in source_hashes
                if f"{key}.tif" in PINS
            },
            "bands": band_stats,
        }

        manifest["prepared_arrays"] = [dict(file=_rel_or_str(bands_dir / path.name),
            sha256=sha256_file(path), bytes=path.stat().st_size) for path in sorted(stage.glob("*.npy"))]
        manifest["publication"] = dict(complete_array_set_staged=True, rollback_on_exception=True,
            local_preparers_serialized=True, crash_atomic_across_cache_and_manifest=False,
            scope="Native bands only; not the actual shared template cached feature stack")
        publish_native_cache(stage, bands_dir, out_path, manifest)
        return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=None, help="Directory containing competition TIFFs (data/ or data/bridge/)")
    parser.add_argument("--work-dir", default=None, help="Directory for band cache output (.cache/gems_work/)")
    parser.add_argument("--manifest", default=None, help="Output path for live receipt (default: <work-dir>/prepared_manifest.json)")
    parser.add_argument("--fetch", action="store_true", help="Attempt to restore missing files via scripts/restore_data.py")
    args = parser.parse_args()

    manifest = prepare(
        data_dir=Path(args.data_dir) if args.data_dir else None,
        work_dir=Path(args.work_dir) if args.work_dir else None,
        fetch_if_missing=args.fetch,
        manifest_path=Path(args.manifest) if args.manifest else None,
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
