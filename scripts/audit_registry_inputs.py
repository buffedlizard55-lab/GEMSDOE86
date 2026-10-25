#!/usr/bin/env python3
"""Read-only byte/grid audit of the pinned registry plus local extras.

No candidate, model, placement, reprojecting, row exclusion or uniqueness pass.
A complete download is not a complete VALID uniqueness registry: incompatible
rasters remain indexed and prevent clearance. Uses the common registry index
and pinned grid, not a private comparison algorithm.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from scripts.audit_release import sha256, verify_shared_pins, write_json  # noqa: E402
from scripts.check_h86e_registry import build_index, index_identity  # noqa: E402


def inspect_record(record: dict, reference) -> dict:
    path = Path(record["cache_file"])
    result = dict(sha256=record["sha256"], sources=record["sources"], repo=record["repo_first"],
                  expected_bytes=record["bytes"], bytes_verified=False, grid_compatible=False,
                  probability_values_checked=False)
    try:
        digest = sha256(path)
        size = path.stat().st_size
        result.update(measured_sha256=digest, measured_bytes=size)
        if digest != record["sha256"] or size != record["bytes"]:
            raise ValueError("registry file hash/byte-length mismatch")
        result["bytes_verified"] = True
        with rasterio.open(path) as src:
            result["grid"] = dict(shape=list(src.shape), crs=str(src.crs),
                                  transform=list(src.transform)[:6], bands=src.count)
            checks = dict(shape=src.shape == reference.shape, crs=src.crs == reference.crs,
                          transform=src.transform == reference.transform, single_band=src.count == 1)
        result["grid_checks"] = checks
        result["grid_compatible"] = all(checks.values())
        result["status"] = "GRID_COMPATIBLE_VALUES_NOT_AUDITED" if result["grid_compatible"] else "GRID_INCOMPATIBLE_DO_NOT_EXCLUDE"
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        result.update(status="INVALID_INPUT", error=str(exc))
    return result


def measure() -> dict:
    if not all(verify_shared_pins(ROOT).values()):
        raise ValueError("Shared tool SHA drift")
    reference = grid.load_grid(ROOT / "data/bridge")
    index, missing = build_index()
    rows = [inspect_record(record, reference) for record in index["rasters"]]
    expected = len(rows) + len(missing)
    verified = sum(row["bytes_verified"] for row in rows)
    compatible = sum(row["grid_compatible"] for row in rows)
    return dict(
        schema="gems86.registry-input-grid-review.v1", evidence_class="REGISTRY-INPUT-MEASUREMENT",
        measured_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        registry_index_sha256=index_identity(index), inventory_rasters_missing=missing,
        indexed_rasters_expected=expected, indexed_rasters_present=len(rows),
        byte_verified_rasters=verified, byte_coverage_complete=bool(expected > 0 and verified == expected),
        grid_compatible_rasters=compatible, grid_incompatible_or_invalid_rasters=len(rows) - compatible,
        all_grids_compatible=bool(expected > 0 and not missing and compatible == expected),
        incompatible_or_invalid_records=[row for row in rows if not row["grid_compatible"]],
        records=rows, probability_values_checked=False, candidate_comparisons_run=False,
        uniqueness_clearance=False, submission_authorized=False, new_candidate_generated=False,
        experiments_run=0, submission_slots_used=0,
        scope="Pinned historical inventory plus local extras at this measurement, not all current projects or organizer submissions. Byte/metadata audit only; no pixel-value or candidate uniqueness clearance.",
        disposition="No row excluded, repaired, warped or relabeled. Any missing or incompatible row remains a blocker; a successful integrity audit is not a gate pass.",
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/evidence/registry-input-grid-review-20261025.json")
    args = parser.parse_args(argv)
    result = measure()
    write_json(args.output, result)
    print({key: result[key] for key in (
        "indexed_rasters_expected", "byte_verified_rasters", "byte_coverage_complete",
        "grid_compatible_rasters", "grid_incompatible_or_invalid_rasters", "uniqueness_clearance")})
    # This CLI audits the input inventory, never signals a submission pass.
    return 0 if result["byte_coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
