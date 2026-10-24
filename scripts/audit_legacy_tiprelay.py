#!/usr/bin/env python3
"""Audit the inherited PR #63 TIPRELAY download; never authorize an upload.

This is a read-only artifact/registry check. --write remeasures the restored
witness and updates *only* the negative audit JSON. It neither generates a TIFF
nor treats a distinct SHA or a portal-format pass as a uniqueness exemption.
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

NAME = "gems86-h86-tiprelay-37654-20261024T070000Z"
REL = f"docs/downloads/{NAME}.tif"
REPORT = "docs/evidence/tiprelay-legacy-audit.json"
SHA = "c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3"
ZIP_SHA = "47d0fbfdc8cb3ebf6a847583d94549b928ed9596f33349c3f6289981bce020cc"
RUN_ORIGINAL_SHA = "d991df50b79f274316d9f62da6751cc8a8452d0d7df96c8374e5e8b8dcf10fd8"
DOWNLOAD_ORIGINAL_SHA = "35e76a3a634f17ef88fe6130f7efc5ef402a7783999c29ef0816cac1667917d4"
FILE_RHO = 0.05086217425960956  # Against one pinned witness, NOT an organizer result.


def inspect(root: Path = ROOT, *, with_witness: bool = False) -> dict:
    root = Path(root).resolve()
    if not all(verify_shared_pins(root).values()):
        raise ValueError("Pinned shared tools drifted")
    p = root / REL
    zpath = p.with_suffix(".zip")
    if sha256(p) != SHA or sha256(zpath) != ZIP_SHA:
        raise ValueError("Historic TIPRELAY TIFF/ZIP SHA-256 mismatch")
    if (sha256(root / "research/upstream/tiprelay-original-run-card.json") != RUN_ORIGINAL_SHA
            or sha256(root / "research/upstream/tiprelay-original-download-card.json") != DOWNLOAD_ORIGINAL_SHA):
        raise ValueError("Original TIPRELAY card archival bytes changed")
    card = strict_json(root / "docs/evidence/h86-tiprelay-run-card.json")
    receipt = strict_json(p.with_suffix(".json"))
    if not (card.get("original_card_sha256") == RUN_ORIGINAL_SHA
            and card.get("raster_sha256") == SHA
            and card.get("verdict") == "negative"
            and card.get("submission_ready") is False
            and card.get("safe_to_submit") is False
            and card.get("approved_for_weekly_slot") is False
            and card.get("download_url") is None
            and card.get("holdout_dti", {}).get("value") is None
            and card.get("holdout_dti", {}).get("ci95") is None
            and card.get("correlation_overlap_vs_registry", {}).get("final_dots_forward_overlap_3px") == 1.0
            and card.get("correlation_overlap_vs_registry", {}).get("preplacement_surface") is None
            and len(card.get("note", "")) <= 140
            and receipt.get("original_download_card_sha256") == DOWNLOAD_ORIGINAL_SHA
            and receipt.get("sha256") == SHA and receipt.get("zip_sha256") == ZIP_SHA
            and receipt.get("bytes") == p.stat().st_size
            and receipt.get("file") == REL
            and receipt.get("zip") == str(zpath.relative_to(root))
            and receipt.get("verdict") == "negative"
            and receipt.get("submission_ready") is False
            and receipt.get("safe_to_submit") is False
            and receipt.get("approved_for_weekly_slot") is False
            and receipt.get("download_url") is None
            and receipt.get("status") == "DO NOT SUBMIT - AUDIT ONLY"
            and receipt.get("note_chars") == len(receipt.get("note", "")) <= 140):
        raise ValueError("Historic TIPRELAY active cards are optimistic or drifted")
    pin = strict_json(root / "research/registry_witness_pin.json")
    proof_path = root / "docs/evidence/protocol-preflight.json"
    proof = strict_json(proof_path)
    g = grid.load_grid(root / "data/bridge")
    if not (proof.get("witness_sha256") == pin["sha256"]
            and proof.get("registry_sha256") == pin["registry_sha256"]
            and proof.get("status") == "STOP_LITERAL_OVERLAP_UNSATISFIABLE"
            and proof.get("direct_support_uncovered_allowed_pixels") == 0
            and proof.get("universal_overlap_blocker") is True
            and proof.get("witness_grid_matches") is True
            and proof.get("witness_validity_mask_covers_footprint") is True
            and proof.get("allowed_pixels") == int((g.footprint & ~g.catalogue).sum())
            and proof.get("overlap_limit") == uniqueness.OVERLAP_LIMIT == 0.7
            and card["correlation_overlap_vs_registry"]["witness_sha256"] == pin["sha256"]):
        raise ValueError("Historic TIPRELAY universal-overlap proof changed or missing")
    local = validate.validate(p, g.footprint, g.catalogue)
    template = gates.format_report(p, root / "data/bridge/sample_submission.tif", footprint=g.footprint)
    with rasterio.open(p) as src:
        a = src.read(1)
        unmasked = bool((src.read_masks(1)[g.footprint] > 0).all())
        no_nodata = src.nodata is None
    positive = np.isfinite(a) & (a > 0)
    with zipfile.ZipFile(zpath) as z:
        zip_only = z.namelist() == [p.name]
        zip_identical = zip_only and z.read(p.name) == p.read_bytes()
        zip_crc = z.testzip() is None
    checks = {
        "shared_tools_pinned": True,
        "local_validator_pass": local["all_checks_passed"],
        "template_format_pass": template["ok"],
        "valid_mask_inside_footprint": unmasked,
        "no_nodata_tag": no_nodata,
        "positive_pixels_in_allowed_domain": bool(positive.any()) and not bool(
            (positive & ~(g.footprint & ~g.catalogue)).any()),
        "zip_contains_only_tif": zip_only, "zip_bytes_equal_tif": zip_identical,
        "zip_crc_pass": zip_crc, "active_cards_negative": True,
        "universal_overlap_proof_bound": True,
    }
    if not all(checks.values()):
        raise ValueError("Historic TIPRELAY integrity/format failed: " +
                         ", ".join(k for k, ok in checks.items() if not ok))
    if int(positive.sum()) != 37654:
        raise ValueError("Historic TIPRELAY prediction dots drifted")
    result = {
        "schema": "gems86.tiprelay-legacy-audit.v1",
        "evidence_class": "LOCAL-ARTIFACT-AND-REGISTRY-MEASUREMENT",
        "scope": "PR #63 existing TIFF/ZIP. Local file format passes but literal overlap fails; original promotion/holdout projection is withdrawn. This is not a new candidate or a complete registry scan.",
        "file": REL, "sha256": SHA, "bytes": p.stat().st_size,
        "zip_sha256": ZIP_SHA,
        "original_run_card_sha256": RUN_ORIGINAL_SHA,
        "original_download_card_sha256": DOWNLOAD_ORIGINAL_SHA,
        "corrected_run_card_sha256": sha256(root / "docs/evidence/h86-tiprelay-run-card.json"),
        "corrected_download_card_sha256": sha256(p.with_suffix(".json")),
        "proof_sha256": sha256(proof_path), "witness_sha256": pin["sha256"],
        "validator": {
            "checks": checks, "all_checks_passed": True,
            "min": local["min"], "max": local["max"],
            "nan_inside_footprint": int(np.isnan(a[g.footprint]).sum()),
            "values_in_0_1": bool(np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1),
            "crs_shape_transform_match": all(local["checks"][key] for key in
                ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")),
            "positive_pixels": int(positive.sum()), "organizer_acceptance": None,
            "writer_receipt_provenance": "The inherited receipt under releases/ names an ephemeral -writer.tif, not this saved path. Its byte digest agrees; its source-specific writer call for the saved file cannot be established from that alone.",
        },
        "registry": {
            "surface_preplacement": None, "registry_complete": False,
            "final_dots_forward_overlap_3px": 1.0, "overlap_limit": 0.7,
            "spearman_full_footprint": None,
            "reason": "Pinned prior has positive support at every allowed cell; all 37,654 dots overlap a prior by the literal rule (1.0 > 0.7). A new SHA is not uniqueness clearance.",
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI", "status": "NOT_VALIDATED_FOR_THIS_RASTER",
            "evaluator_version": None, "withheld_positives": None, "value": None, "ci95": None,
            "reason": "No buffered whole-fault, fold-visible-only experiment, leakage canaries or matched paired 95% CI; former uplift was a projection.",
        },
        "verdict": "negative", "submission_ready": False,
        "safe_to_submit": False, "approved_for_weekly_slot": False,
        "new_raster_generated_by_this_audit": False, "submission_slots_used_by_this_audit": 0,
    }
    if with_witness:
        from scripts.protocol_preflight import measure
        measured = measure(root / "data")
        if measured["direct_support_uncovered_allowed_pixels"] != 0:
            raise ValueError("Historic TIPRELAY witness no longer fully supports negative proof")
        comparison = uniqueness.compare_array_to_registry(
            a.astype(np.float32, copy=False),
            [dict(repo=pin["repo"], submission=pin["source_path"],
                  file=str(root / "data" / pin["dest"]), sha256=pin["sha256"])],
            g.footprint, file_sha256=SHA,
            expected_grid=(g.shape, g.crs, g.transform),
        )
        if comparison["worst_dot_overlap"] != 1.0 or comparison["stop_required"] is not True:
            raise ValueError("Shared comparator contradicts historic TIPRELAY overlap stop")
        result["registry"]["spearman_full_footprint"] = comparison["worst_spearman_full_footprint"]
    return result


def check_snapshot(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    stored = strict_json(root / REPORT)
    current = inspect(root, with_witness=False)
    rho = stored.get("registry", {}).get("spearman_full_footprint")
    if not isinstance(rho, (int, float)) or not np.isfinite(rho) or not np.isclose(
            rho, FILE_RHO, atol=2e-14, rtol=0):
        raise ValueError("Historic TIPRELAY witness correlation differs from pinned measurement")
    current["registry"]["spearman_full_footprint"] = rho
    measured_at = stored.get("witness_measured_utc")
    if not isinstance(measured_at, str) or not measured_at.endswith("+00:00"):
        raise ValueError("Historic TIPRELAY witness measurement has no UTC timestamp")
    current["witness_measured_utc"] = measured_at
    if current != stored:
        raise ValueError("Historic TIPRELAY audit is stale, modified or optimistic")
    if (root / "data/registry/dense-witness.tif").is_file():
        remeasured = inspect(root, with_witness=True)["registry"]["spearman_full_footprint"]
        if not np.isclose(remeasured, rho, atol=2e-14, rtol=0):
            raise ValueError("Historic TIPRELAY witness measurement is not reproducible")
    return stored


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="remeasure the pinned witness and write negative audit")
    args = parser.parse_args(argv)
    if args.write:
        result = inspect(with_witness=True)
        result["witness_measured_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        write_json(ROOT / REPORT, result)
    else:
        result = check_snapshot()
    print(json.dumps({key: result[key] for key in ("file", "sha256", "verdict", "submission_ready")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
