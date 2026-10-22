"""Read-only preflight for the checked-in negative candidate.

This command deliberately writes to ``docs/evidence/preflight.json`` rather than
``run-card.json``.  The scientific run card is evidence, not a cache that a unit
test or routine audit may overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

CANDIDATE_RECEIPT = ROOT / "docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.json"
RUN_CARD = ROOT / "docs/evidence/run-card.json"
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_pins() -> bool:
    """Return whether every vendored shared-tool byte matches its upstream pin."""
    pin_path = ROOT / "research/template_pin.json"
    if not pin_path.is_file():
        return False
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    files = pin.get("files")
    if not isinstance(files, dict) or not files:
        return False
    return all(
        isinstance(relative, str)
        and isinstance(expected, str)
        and (ROOT / relative).is_file()
        and sha256(ROOT / relative) == expected
        for relative, expected in files.items()
    )


def _validate_artifact() -> dict:
    """Validate the checked-in TIFF bytes; never infer scientific readiness."""
    from gems57 import grid, validate

    if not CANDIDATE_RECEIPT.is_file():
        return {"present": False, "checks": {"receipt_present": False}}
    receipt = json.loads(CANDIDATE_RECEIPT.read_text(encoding="utf-8"))
    filename = receipt.get("file")
    zip_filename = receipt.get("zip_file")
    if (not filename or Path(filename).name != filename
            or not zip_filename or Path(zip_filename).name != zip_filename):
        return {"present": False, "checks": {"receipt_path_safe": False}}
    tif = CANDIDATE_RECEIPT.parent / filename
    zip_path = CANDIDATE_RECEIPT.parent / zip_filename
    checks = {"receipt_path_safe": True, "tif_present": tif.is_file()}
    if not tif.is_file():
        return {"present": False, "checks": checks}

    data_dir = ROOT / "data"
    full_grid = None
    input_grid_error = None
    if (data_dir / "sample_submission.tif").is_file() and (data_dir / "existing_faults.tif").is_file():
        try:
            full_grid = grid.load_grid(data_dir)
        except (OSError, ValueError, RuntimeError) as exc:
            input_grid_error = type(exc).__name__
    if full_grid is None:
        report = validate.validate(tif)
        checks["footprint_and_catalogue_rechecked"] = False
        checks["input_mirror_hashes_match"] = False
    else:
        report = validate.validate(tif, footprint=full_grid.footprint, catalogue=full_grid.catalogue)
        checks["footprint_and_catalogue_rechecked"] = True
        checks["input_mirror_hashes_match"] = (
            sha256(data_dir / "sample_submission.tif") == grid.SHA256_SAMPLE_SUBMISSION
            and sha256(data_dir / "existing_faults.tif") == grid.SHA256_EXISTING_FAULTS
        )

    checks["sha256_matches_writer_receipt"] = report["sha256"] == receipt.get("sha256")
    checks["writer_checks_match"] = bool(report["all_checks_passed"])
    checks["single_band_float32"] = report["meta"]["count"] == 1 and report["meta"]["dtype"] == "float32"
    checks["crs_shape_transform_match_pinned_grid"] = (
        report["meta"]["crs"] == f"EPSG:{grid.EPSG}"
        and tuple(report["meta"]["shape"]) == grid.SHAPE
        and report["meta"]["transform"] == list(tuple(grid.TRANSFORM)[:6])
    )
    checks["finite_range_0_1"] = (
        report["n_nan"] == 0 and report["n_infinite"] == 0
        and report["min"] is not None and report["min"] >= 0
        and report["max"] is not None and report["max"] <= 1
    )
    checks["sha256_matches_run_card"] = True
    if RUN_CARD.is_file():
        card = json.loads(RUN_CARD.read_text(encoding="utf-8"))
        checks["sha256_matches_run_card"] = report["sha256"] == card.get("raster_sha256")

    zip_ok = False
    if zip_path.is_file():
        try:
            with zipfile.ZipFile(zip_path) as archive:
                names = archive.namelist()
                zip_ok = names == [filename] and archive.read(filename) == tif.read_bytes()
        except (OSError, zipfile.BadZipFile, KeyError):
            zip_ok = False
    checks["zip_contains_only_byte_identical_tif"] = zip_ok
    checks["zip_sha256_matches_receipt"] = zip_path.is_file() and sha256(zip_path) == receipt.get("zip_sha256")

    return {
        "present": True,
        "file": str(tif.relative_to(ROOT)),
        "bytes": report["bytes"],
        "sha256": report["sha256"],
        "positive_pixels": report["emitted_positive_pixels"],
        "min": report["min"],
        "max": report["max"],
        "meta": report["meta"],
        "checks": checks,
        "input_grid_error_type": input_grid_error,
        "all_local_format_checks_pass": bool(all(checks.values())),
        "validation_scope": "local format/range audit; not scientific clearance, registry uniqueness, or organizer acceptance",
    }


def _finite_metric(value, lower: float, upper: float) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and lower <= number <= upper else None


def run() -> dict:
    """Build a read-only preflight report; do not mutate any evidence file."""
    pin_ok = check_pins()
    artifact = _validate_artifact()
    run_card = json.loads(RUN_CARD.read_text(encoding="utf-8")) if RUN_CARD.is_file() else {}
    uniqueness = run_card.get("correlation_overlap_vs_registry", {})
    holdout = run_card.get("holdout_dti", {})
    protocol = run_card.get("protocol_conformance", {})

    surface_rho = _finite_metric(uniqueness.get("surface_worst_spearman_recorded"), -1.0, 1.0)
    pre_dot_overlap = _finite_metric(uniqueness.get("preplacement_dot_overlap"), 0.0, 1.0)
    final_dot_overlap = _finite_metric(uniqueness.get("final_worst_dot_overlap_verified"), 0.0, 1.0)
    literal_unique = (
        uniqueness.get("duplicate_gate_fired") is False
        and surface_rho is not None and surface_rho <= 0.90
        and pre_dot_overlap is not None and pre_dot_overlap <= 0.70
        and final_dot_overlap is not None and final_dot_overlap <= 0.70
    )
    checks = {
        "shared_template_hashes_match": pin_ok,
        "shared_feature_stack_available": bool(protocol.get("template_cached_feature_stack_available", False)),
        "shared_feature_stack_used": bool(protocol.get("template_cached_feature_stack_used", False)),
        "lane_authorized": bool(protocol.get("lane_authorized", False)),
        "candidate_tif_present": bool(artifact.get("present")),
        "candidate_local_format_checks_pass": bool(artifact.get("all_local_format_checks_pass")),
        "literal_uniqueness_gate_clear": literal_unique,
        "complete_registry_available": bool(uniqueness.get("complete_accessible_scan", False)),
        "holdout_protocol_conformant": bool(protocol.get("holdout_conformant", False)),
        "holdout_comparison_beats_best": bool(protocol.get("beats_current_holdout_best", False)),
    }
    ready = bool(all(checks.values()))
    decision = (
        "OK TO SUBMIT to the separate slot selector; this preflight does not authorize or spend a weekly slot."
        if ready else
        "DO NOT SUBMIT; at least one scientific/provenance gate is not satisfied."
    )
    return {
        "schema": "gemsdoe86-preflight-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "evidence_class": "LOCAL-PREFLIGHT (not a competition score)",
        "checks": checks,
        "artifact": artifact,
        "holdout_dti": holdout,
        "registry": uniqueness,
        "submission_ready": ready,
        "approved_for_weekly_slot": False,
        "verdict": "promote" if ready else "negative",
        "submission_decision": decision,
        "run_card_unchanged_by_design": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/evidence/preflight.json")
    args = parser.parse_args()
    report = run()
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
