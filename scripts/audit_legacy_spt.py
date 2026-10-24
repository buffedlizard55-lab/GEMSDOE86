#!/usr/bin/env python3
"""Fail-closed review of PR #60's off-dashboard SPT raster (NOT a submission).

The original, optimistic card is preserved for forensics. This read-only audit
validates the *existing* TIFF/ZIP with pinned shared tools, then checks the
unchanged literal overlap rule. It never fits, repairs, copies or emits a TIFF.
``--write`` requires the restored, hash-verified witness and records its actual
rank correlation. ``--check`` is usable offline, but remeasures the witness if
present. A missing witness is never interpreted as uniqueness clearance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import gates, grid, validate, uniqueness  # noqa: E402
from scripts.audit_release import sha256, strict_json, verify_shared_pins, write_json  # noqa: E402

NAME = "gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros"
REL = "submission/" + NAME + ".tif"
FILE_SHA256 = "26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342"
ARCHIVED_CARD_SHA256 = "10aa9e54a11660e48db376a47c72d98b5d4a3124e804e227e1992da4b61dc0b2"
# Measured against the exact pinned witness, not a registry-wide clearance.
FILE_RHO = 0.009411845173808513
REPORT = "docs/evidence/spt-legacy-audit.json"


def inspect(root: Path = ROOT, *, with_witness: bool = False) -> dict:
    root = Path(root).resolve()
    shared = verify_shared_pins(root)
    if not all(shared.values()):
        raise ValueError("Pinned shared tools have drifted")
    p = root / REL
    archive = p.with_suffix(".zip")
    if sha256(p) != FILE_SHA256:
        raise ValueError("Historical SPT TIFF SHA-256 mismatch")
    original_path = root / "research/upstream/spt-original-run-card.json"
    if sha256(original_path) != ARCHIVED_CARD_SHA256:
        raise ValueError("Original optimistic SPT run card has changed")
    original = strict_json(original_path)
    if (original.get("submission_ready") is not True or original.get("verdict") != "promote-candidate"
            or original.get("raster_sha256") != FILE_SHA256):
        raise ValueError("Original run-card provenance does not match its archive")
    card = strict_json(root / "docs/evidence/spt-run-card.json")
    adjacent = strict_json(p.with_suffix(".json"))
    if card != adjacent:
        raise ValueError("Corrective run card and adjacent artifact card differ")
    if (card.get("verdict") != "negative" or card.get("submission_ready") is not False
            or card.get("safe_to_submit") is not False
            or card.get("approved_for_weekly_slot") is not False
            or card.get("raster_sha256") != FILE_SHA256
            or card.get("submission_file") != REL
            or card.get("original_card_sha256") != ARCHIVED_CARD_SHA256
            or card.get("download_url") is not None):
        raise ValueError("Legacy SPT card still suggests release or has stale identity")
    note = card.get("note")
    if not isinstance(note, str) or not note.startswith("DO NOT SUBMIT:") or len(note) > 140:
        raise ValueError("The SPT note must be short and explicitly negative")

    pin = strict_json(root / "research/registry_witness_pin.json")
    proof_path = root / "docs/evidence/protocol-preflight.json"
    proof = strict_json(proof_path)
    g = grid.load_grid(root / "data/bridge")
    for name, expected in (("sample_submission.tif", grid.SHA256_SAMPLE_SUBMISSION),
                           ("existing_faults.tif", grid.SHA256_EXISTING_FAULTS)):
        if sha256(root / "data/bridge" / name) != expected:
            raise ValueError("Grid-mirror SHA-256 mismatch: " + name)
    if (proof.get("witness_sha256") != pin["sha256"]
            or proof.get("registry_sha256") != pin["registry_sha256"]
            or proof.get("status") != "STOP_LITERAL_OVERLAP_UNSATISFIABLE"
            or proof.get("overlap_limit") != uniqueness.OVERLAP_LIMIT
            or proof.get("universal_overlap_blocker") is not True
            or proof.get("direct_support_uncovered_allowed_pixels") != 0
            or proof.get("allowed_pixels") != int((g.footprint & ~g.catalogue).sum())
            or proof.get("witness_grid_matches") is not True
            or proof.get("witness_validity_mask_covers_footprint") is not True):
        raise ValueError("Saturation proof is stale or no longer binding")

    local = validate.validate(p, g.footprint, g.catalogue)
    template = gates.format_report(p, root / "data/bridge/sample_submission.tif", footprint=g.footprint)
    with rasterio.open(p) as ds:
        a = ds.read(1)
        mask_inside = bool((ds.read_masks(1)[g.footprint] > 0).all())
        nodata_is_none = ds.nodata is None
    # The proof covers the entire allowed domain, but the historic dots must
    # really lie there: otherwise one cannot deduce their forward overlap.
    positive = np.isfinite(a) & (a > 0)
    in_allowed = bool(not (positive & ~(g.footprint & ~g.catalogue)).any())
    with zipfile.ZipFile(archive) as z:
        zip_names = z.namelist() == [p.name]
        zip_identical = zip_names and z.read(p.name) == p.read_bytes()
        zip_crc = z.testzip() is None
    checks = {
        "shared_tools_pinned": True,
        "local_validator_pass": local["all_checks_passed"],
        "template_format_pass": template["ok"],
        "valid_mask_inside_footprint": mask_inside,
        "no_nodata_tag": nodata_is_none,
        "nonempty_predictions_all_in_allowed_domain": bool(positive.any()) and in_allowed,
        "zip_only_this_tif": zip_names,
        "zip_bytes_equal_tif": zip_identical,
        "zip_crc_pass": zip_crc,
        "corrected_card_is_negative": True,
        "universal_overlap_proof_bound": True,
    }
    if not all(checks.values()):
        raise ValueError("Historical SPT local format/integrity failure: " +
                         ", ".join(k for k, v in checks.items() if not v))
    result = {
        "schema": "gems86.spt-legacy-audit.v1", "evidence_class": "LOCAL-ARTIFACT-AND-REGISTRY-MEASUREMENT",
        "scope": "One pre-existing PR #60 raster outside Pages. Format passes; historical holdout/uniqueness claims do not establish submission readiness.",
        "file": REL, "sha256": FILE_SHA256, "bytes": p.stat().st_size,
        "zip_sha256": sha256(archive), "original_card_sha256": ARCHIVED_CARD_SHA256,
        "corrected_card_sha256": sha256(root / "docs/evidence/spt-run-card.json"),
        "proof_sha256": sha256(proof_path), "witness_sha256": pin["sha256"],
        "validator": {
            "checks": checks, "min": local["min"], "max": local["max"],
            "nan_inside_footprint": int(np.isnan(a[g.footprint]).sum()),
            "values_in_0_1": bool(np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1),
            "crs_shape_transform_match": all(local["checks"][k] for k in
                ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")),
            "positive_pixels": int(positive.sum()), "shared_writer_used": False,
            "all_checks_passed": True, "organizer_acceptance": None,
        },
        "registry": {
            "surface_preplacement": None, "registry_complete": False,
            "final_dots_forward_overlap_3px": 1.0,
            "overlap_limit": uniqueness.OVERLAP_LIMIT,
            "spearman_full_footprint": None,
            "reason": "Pinned dense registry witness covers every allowed pixel; every nonempty subset has forward overlap 1.0 (>0.70).",
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI", "status": "NOT_VALIDATED_FOR_THIS_RASTER",
            "evaluator_version": None, "withheld_positives": None, "value": None, "ci95": None,
            "reason": "Historical folds used a full-catalogue collar and no buffered visible-only placement, paired physical-block CI or shared holdout evaluator. The stored scalar is only an in-sample diagnostic.",
        },
        "verdict": "negative", "submission_ready": False, "approved_for_weekly_slot": False,
        "safe_to_submit": False, "new_raster_generated": False, "submission_slots_used": 0,
    }
    if with_witness:
        from scripts.protocol_preflight import measure
        witness_proof = measure(root / "data")
        if witness_proof["direct_support_uncovered_allowed_pixels"] != 0:
            raise ValueError("The registry witness no longer supports the direct overlap proof")
        comparison = uniqueness.compare_array_to_registry(
            a.astype(np.float32, copy=False),
            [dict(repo=pin["repo"], submission=pin["source_path"],
                  file=str(root / "data" / pin["dest"]), sha256=pin["sha256"])],
            g.footprint, file_sha256=FILE_SHA256,
            expected_grid=(g.shape, g.crs, g.transform),
        )
        if comparison["worst_dot_overlap"] != 1.0 or not comparison["stop_required"]:
            raise ValueError("Shared registry comparator contradicts the universal proof")
        result["registry"]["spearman_full_footprint"] = comparison["worst_spearman_full_footprint"]
    return result


def check_snapshot(root: Path = ROOT) -> dict:
    """Verify the checked-in report against *bytes*, not just the old claim."""
    root = Path(root).resolve()
    stored = strict_json(root / REPORT)
    current = inspect(root, with_witness=False)
    # Spearman is remeasured on --write/when the ignored witness is restored,
    # but a data-free CI run cannot invent a score from a missing raster.
    if (stored.get("registry", {}).get("spearman_full_footprint") is None
            or not np.isfinite(stored["registry"]["spearman_full_footprint"])
            or abs(stored["registry"]["spearman_full_footprint"]) > 1):
        raise ValueError("Stored witness rank correlation is missing or invalid")
    rho = stored["registry"]["spearman_full_footprint"]
    # On a data-free CI runner, do not accept an arbitrary plausible scalar.
    # This frozen value is not an organizer score or a uniqueness clearance.
    if not np.isclose(rho, FILE_RHO, atol=2e-14, rtol=0):
        raise ValueError("Historic SPT witness correlation differs from pinned measurement")
    current["registry"]["spearman_full_footprint"] = rho
    measured = stored.get("witness_measured_utc")
    if not isinstance(measured, str) or not measured.endswith("+00:00"):
        raise ValueError("Witness measurement lacks a UTC timestamp")
    current["witness_measured_utc"] = measured
    if stored != current:
        raise ValueError("Historical SPT audit is stale or has optimistic/modified fields")
    if (root / "data/registry/dense-witness.tif").is_file():
        measured_result = inspect(root, with_witness=True)
        if (measured_result["registry"]["spearman_full_footprint"] is None
                or not np.isclose(measured_result["registry"]["spearman_full_footprint"], rho,
                                  atol=2e-14, rtol=0)):
            raise ValueError("Historic SPT witness correlation is not reproducible")
    return stored


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="remeasure the restored witness and write the negative report")
    args = parser.parse_args(argv)
    if args.write:
        result = inspect(with_witness=True)
        result["witness_measured_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        write_json(ROOT / REPORT, result)
    else:
        result = check_snapshot()
    print(json.dumps({k: result[k] for k in ("file", "sha256", "verdict", "submission_ready")}, indent=2))


if __name__ == "__main__":
    main()
