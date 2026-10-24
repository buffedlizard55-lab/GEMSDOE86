#!/usr/bin/env python3
"""Audit EVERY published TIFF, ZIP and identity receipt without fitting a model.

Reuses the pinned shared validators and literal registry checker; never edits
model evidence, raster bytes, thresholds, or a scientific verdict. This audit
cannot authorize a submission. A negative scientific result is a successful
integrity audit, whereas corrupted/missing evidence is a failing audit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import gates, grid, validate  # noqa: E402


def sha256(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def strict_json(path: Path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON token {value} in {path.name}")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key} in {path.name}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=reject, object_pairs_hook=pairs)


def inside(root: Path, relative: str, *, directory: str | None = None) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Expected a nonempty repository-relative path")
    path = (root / relative).resolve()
    base = (root / directory).resolve() if directory else root.resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError(f"Missing or escaping input: {relative}")
    return path


def verify_shared_pins(root: Path) -> dict:
    pin = strict_json(root / "research/template_pin.json")
    checks = {name: sha256(inside(root, name)) == expected
              for name, expected in pin["files"].items()}
    # Check the other vendored import path too: tests use template66, whereas
    # several model entrypoints use vendor/gems57. Never accept private drift.
    for line in (root / "vendor/template66/TEMPLATE_SHA256.txt").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        rel = "vendor/template66/" + name.strip()
        checks[rel] = sha256(inside(root, rel)) == expected
    return checks


def archived_holdout(config: dict, context: dict) -> dict:
    """Normalize only explicitly known schemas; do not manufacture comparability."""
    kind = config["holdout_kind"]
    base = dict(evidence_class="HOLDOUT-DTI", status="ARCHIVED_NOT_RECOMPUTED",
                source=config["context"], evaluator_version="gems57-pooled-hide-v2",
                withheld_positives=None, value=None, ci95=None)
    if kind == "unvalidated_variant":
        return {**base, "status": "NOT_VALIDATED_FOR_THIS_VARIANT",
                "caveat": "The archived GMC HOLDOUT-DTI belongs to the catalogue-following configuration, not this off-catalogue export."}
    if kind == "gmc_control":
        return {**base, "withheld_positives": context["withheld_positive_pixels"],
                "value": context["holdout_dti"], "ci95": context["holdout_ci95"],
                "design": "buffered whole components; one seed",
                "caveat": "Historical configuration only. Hidden-positive counts were used for the prior and dot budget; not an independent promotion benchmark."}
    h = context["holdout_dti"]
    if kind == "wvb_whole_components":
        if h.get("label") != "HOLDOUT-DTI":
            raise ValueError("Archived WVB performance lacks its evidence class")
        return {**base, "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["dti"], "ci95": h["ci95"],
                "paired_delta": h["delta_vs_d28"], "paired_delta_ci95": h["delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; two seeds; physical-block interval",
                "caveat": "Concurrent archived experiment, not rerun or certified by this audit. Its paired delta is positive, but literal overlap fails; model-selection and cache-provenance limits still apply. Not a repository-wide best."}
    if h.get("evidence_class") != "HOLDOUT-DTI":
        raise ValueError("Historical performance lacks its evidence class")
    base["evaluator_version"] = h["evaluator_version"]
    if kind == "fvmb_segments":
        w = h["dual_seed_segment_all"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "design": "two-seed cut-segment holdout, not buffered whole components",
                "caveat": "Concurrent archive only, not rerun. Both stored numeric paired-delta fields contain the text HOLDOUT-DTI and are not treated as numeric evidence. Literal overlap fails. Its three-stage/four-ablation budget convention and separate stale pin manifest need reconciliation. No cross-design champion claim is accepted."}
    if kind == "cut_segments":
        return {**base, "withheld_positives": h["withheld_positives"],
                "value": h["candidate_at_final_budget_60000"], "ci95": h["ci95_cell_bootstrap"],
                "design": "cut-segment holdout; cell bootstrap interval",
                "caveat": "Not the required buffered whole-component / physical-block-bootstrap instrument. Do not rank against other designs."}
    if kind == "gfco_whole_components":
        w = h["buffered_whole_components_loqo"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; one seed",
                "caveat": "Paired physical-block delta interval includes zero. Larger cut-segment values are different instruments, not a repository-wide best."}
    if kind == "kslb_whole_components":
        w = h["buffered_whole_components_loqo"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; physical-block interval",
                "caveat": "Concurrent Session-3 archive; paired whole-component delta interval is positive vs d2.8 and H33-2-B2 and 0/37 non-lattice dot-field rasters exceed 0.70, but literal overlap fails on saturated witnesses and catalogue-recovery holdout is not a private-test score."}
    if kind == "cthb_submod":
        w = h["segment_hide_detached"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "detached isolated segments + buffered whole components (two seeds, LOQO, physical-block interval)",
                "caveat": "Concurrent H86D-CTHB archive; paired detached (+0.1553 [+0.1389, +0.1730]) and all (+0.1495 [+0.1353, +0.1644]) intervals are positive vs d2.8 and H33-2-B2 (buffered whole-component point DTI 0.1133 vs d2.8 0.1009, CI [-0.0050, +0.0287]) and 0/45 non-lattice dot-field rasters exceed 0.70, but literal overlap fails on saturated witnesses."}
    if kind == "pooled":
        return {**base, "withheld_positives": h["withheld_positives"],
                "value": h["value"], "ci95": h["ci95"],
                "design": "buffered whole components; two seeds; physical-block bootstrap",
                "caveat": "Archived pipeline evidence only; not recomputed in this audit, not a private-test score."}
    raise ValueError(f"Unsupported holdout schema: {kind}")


def audit_artifact(root: Path, entry: dict, config: dict, g) -> dict:
    tif = inside(root, entry["file"], directory="docs/downloads")
    receipt_path = inside(root, str(tif.with_suffix(".json").relative_to(root)), directory="docs/downloads")
    zip_path = inside(root, str(tif.with_suffix(".zip").relative_to(root)), directory="docs/downloads")
    receipt = strict_json(receipt_path)
    report = validate.validate(tif, g.footprint, g.catalogue)
    fmt = gates.format_report(tif, root / "data/bridge/sample_submission.tif", footprint=g.footprint)
    file_sha = sha256(tif)
    checks = dict(report["checks"])
    checks.update(
        template_format_report_passed=fmt["ok"],
        sha_matches_inventory=file_sha == entry["sha256"],
        sha_matches_writer_receipt=file_sha == receipt["sha256"],
        receipt_filename_matches=receipt["file"] == tif.name,
        receipt_bytes_match=receipt["bytes"] == tif.stat().st_size,
        name_1_to_140_chars=isinstance(receipt.get("submission_name"), str)
            and bool(receipt["submission_name"].strip()) and len(receipt["submission_name"]) <= 140,
        note_1_to_140_chars=isinstance(receipt.get("note"), str)
            and bool(receipt["note"].strip()) and len(receipt["note"]) <= 140,
        receipt_note_count_matches=receipt.get("note_chars") == len(receipt.get("note", "")),
        inventory_explicitly_negative=entry.get("approved_for_weekly_slot") is False
            and "DO NOT SUBMIT" in entry.get("status", ""),
    )
    with rasterio.open(tif) as src:
        checks["no_nodata_tag"] = src.nodata is None
        checks["validity_mask_covers_footprint"] = bool((src.read_masks(1)[g.footprint] > 0).all())
    with zipfile.ZipFile(zip_path) as bundle:
        checks["zip_one_exact_tif"] = bundle.namelist() == [tif.name]
        checks["zip_payload_equals_tif"] = checks["zip_one_exact_tif"] and bundle.read(tif.name) == tif.read_bytes()
        checks["zip_crc_passed"] = bundle.testzip() is None
    checks["zip_sha_matches_receipt"] = sha256(zip_path) == receipt["zip_sha256"]
    context = strict_json(inside(root, config["context"]))
    if config["card"]:
        card = strict_json(inside(root, config["card"]))
        checks["sha_matches_scientific_card"] = card["raster_sha256"] == file_sha
        checks["scientific_card_is_negative"] = card.get("verdict") == "negative"
        checks["scientific_card_does_not_authorize"] = all(
            card.get(field) is not True for field in ("submission_ready", "safe_to_submit", "approved_for_weekly_slot"))
    passed = all(value is True for value in checks.values())
    return dict(lane=config["lane"], file=entry["file"], sha256=file_sha,
                bytes=tif.stat().st_size, zip_file=str(zip_path.relative_to(root)),
                zip_sha256=sha256(zip_path), receipt_file=str(receipt_path.relative_to(root)),
                source_card=config["card"],
                submission_name=receipt["submission_name"], note=receipt["note"], note_chars=len(receipt["note"]),
                validation_class="FORMAT-VALIDATION: local all-finite zero-outside export policy, not organizer acceptance",
                validator=dict(checks=checks, all_checks_passed=passed,
                               min=report["min"], max=report["max"], n_nan=report["n_nan"],
                               n_inf=report["n_infinite"], emitted_dots=report["emitted_positive_pixels"],
                               outside_footprint_positive=fmt["mass_outside_footprint"],
                               on_catalogue_positive=report["on_catalogue_positive_pixels"], meta=report["meta"]),
                historical_holdout=archived_holdout(config, context),
                safe_to_download_for_audit=passed, safe_to_submit=False,
                approved_for_weekly_slot=False, verdict="negative", status="DO NOT SUBMIT")


def measure_all_registry(root: Path = ROOT) -> dict:
    """Re-measure final inherited dots against one witness; never claim clearance."""
    from scripts.protocol_preflight import measure
    from gems57.uniqueness import compare_array_to_registry

    if root.resolve() != ROOT:
        raise ValueError("Registry measurement requires this checkout's pinned inputs")
    cert = measure()  # verifies witness, inventory membership, size, SHA and grid
    g = grid.load_grid(root / "data")
    pin = strict_json(root / "research/registry_witness_pin.json")
    records = [dict(repo=pin["repo"], submission=pin["source_path"],
                    file=str(root / "data" / pin["dest"]), sha256=pin["sha256"])]
    rows = []
    inventory = strict_json(root / "docs/evidence/download-inventory.json")
    for entry in inventory["artifacts"]:
        tif = inside(root, entry["file"], directory="docs/downloads")
        digest = sha256(tif)
        if digest != entry["sha256"]:
            raise ValueError(f"Artifact hash drift: {tif.name}")
        with rasterio.open(tif) as src:
            if (src.count, src.shape, src.crs, src.transform) != (1, g.shape, g.crs, g.transform):
                raise ValueError(f"Artifact grid drift: {tif.name}")
            prediction = src.read(1)
        result = compare_array_to_registry(prediction, records, g.footprint,
            file_sha256=digest, expected_grid=(g.shape, g.crs, g.transform))
        rows.append(dict(file=entry["file"], sha256=digest,
                         spearman_full_footprint=result["worst_spearman_full_footprint"],
                         forward_overlap_3px=result["worst_dot_overlap"],
                         unique=result["unique"], stop_required=result["stop_required"],
                         complete_accessible_scan=result["complete_accessible_scan"]))
    return dict(schema="gems86.all-artifacts-registry.v1", evidence_class="REGISTRY-MEASUREMENT",
                measured_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                witness_sha256=pin["sha256"], witness_source=cert["witness_source"],
                proof_sha256=sha256(root / "docs/evidence/protocol-preflight.json"),
                registry_rasters_measured=1, registry_complete=False,
                preplacement_surfaces_measured=False, new_candidate_generated=False,
                experiments_run=0, submission_slots_used=0, artifacts=rows,
                scope="Rechecks all inherited final TIFFs against one immutable witness, not the full registry. Sufficient to reject, never to clear or rank candidates.")


def build_report(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    shared = verify_shared_pins(root)
    if not all(shared.values()):
        raise ValueError("Shared tool SHA drift; no private evaluator/validator is accepted")
    for filename, expected in (("sample_submission.tif", grid.SHA256_SAMPLE_SUBMISSION),
                               ("existing_faults.tif", grid.SHA256_EXISTING_FAULTS)):
        if sha256(root / "data/bridge" / filename) != expected:
            raise ValueError(f"Mirrored template SHA mismatch: {filename}")
    g = grid.load_grid(root / "data/bridge")
    inventory_path = root / "docs/evidence/download-inventory.json"
    index_path = root / "registry/artifact_cards.json"
    proof_path = root / "docs/evidence/protocol-preflight.json"
    cert = strict_json(proof_path)
    pin = strict_json(root / "research/registry_witness_pin.json")
    if cert["witness_sha256"] != pin["sha256"] or cert["registry_sha256"] != pin["registry_sha256"]:
        raise ValueError("Protocol proof is not bound to the pinned historical witness")
    if not (cert["universal_overlap_blocker"] is True
            and cert["uncovered_allowed_pixels"] == 0
            and cert["direct_support_uncovered_allowed_pixels"] == 0
            and cert["covered_allowed_fraction"] == 1.0
            and cert["allowed_pixels"] == int((g.footprint & ~g.catalogue).sum())
            and cert["footprint_pixels"] == int(g.footprint.sum())
            and cert["catalogue_pixels"] == int(g.catalogue.sum())
            and cert["witness_grid_matches"] is True
            and cert["witness_validity_mask_covers_footprint"] is True
            and cert["thresholds_unchanged"] is True
            and cert["dense_surface_exemption"] is False
            and cert["overlap_limit"] == 0.70):
        raise ValueError("Changed/missing protocol proof: this negative-only audit cannot certify a release")
    inventory = strict_json(inventory_path)["artifacts"]
    configs = strict_json(index_path)["artifacts"]
    by_stem = {c["stem"]: c for c in configs}
    paths = [entry["file"] for entry in inventory]
    if not inventory or len(paths) != len(set(paths)) or len(by_stem) != len(configs):
        raise ValueError("Empty or duplicate artifact inventory/card mapping")
    inventory_stems = {Path(p).stem for p in paths}
    if inventory_stems != set(by_stem):
        raise ValueError("Inventory and card mappings do not describe the same artifacts")
    registered = set(paths)
    published = {str(p.relative_to(root)) for p in (root / "docs").rglob("*")
                 if p.suffix.lower() in {".tif", ".tiff"}}
    if registered != published:
        raise ValueError("Unregistered or missing published TIFF")
    registered_zips = {str(Path(p).with_suffix(".zip")) for p in registered}
    published_zips = {str(p.relative_to(root)) for p in (root / "docs").rglob("*")
                      if p.suffix.lower() == ".zip"}
    if registered_zips != published_zips:
        raise ValueError("Unregistered or missing published ZIP")
    submission_dir = root / "submission"
    if submission_dir.exists():
        smuggled = [str(p.relative_to(root)) for p in submission_dir.rglob("*")
                    if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
        if smuggled:
            raise ValueError(f"Unregistered or missing published binary in submission/: {smuggled[0]}")
    artifacts = [audit_artifact(root, entry, by_stem[Path(entry["file"]).stem], g) for entry in inventory]
    linked_cards = {c["source_card"] for c in configs if c.get("source_card")}
    sidecar_cards_negative = True
    for card_path in sorted((root / "docs/evidence").glob("*card*.json")):
        rel_card = str(card_path.relative_to(root))
        if rel_card in linked_cards:
            continue
        card_doc = strict_json(card_path)
        if (card_doc.get("verdict") != "negative"
                or card_doc.get("submission_ready") is True
                or card_doc.get("safe_to_submit") is True
                or card_doc.get("approved_for_weekly_slot") is True):
            sidecar_cards_negative = False
    inputs = {str(p.relative_to(root)): sha256(p) for p in (inventory_path, index_path, proof_path)}
    for config in configs:
        inputs[config["context"]] = sha256(root / config["context"])
    registry_path = root / "docs/evidence/all-artifacts-registry.json"
    registry = strict_json(registry_path)
    if registry["witness_sha256"] != pin["sha256"] or registry["proof_sha256"] != sha256(proof_path):
        raise ValueError("Final-dot measurements have a stale witness/proof binding")
    registry_rows = {r["file"]: r for r in registry["artifacts"]}
    if set(registry_rows) != set(paths) or len(registry_rows) != len(registry["artifacts"]):
        raise ValueError("Final-dot measurements are incomplete or contain duplicates")
    for artifact in artifacts:
        row = registry_rows[artifact["file"]]
        rho = row["spearman_full_footprint"]
        if (row["sha256"] != artifact["sha256"] or row["stop_required"] is not True
                or row["unique"] is not False or row["forward_overlap_3px"] != 1.0
                or not isinstance(rho, (int, float)) or not np.isfinite(rho) or abs(rho) > 1.0
                or row["complete_accessible_scan"] is not False):
            raise ValueError("Final-dot measurements drifted or contradict the mandatory stop")
        artifact["registry_measurement"] = row
    inputs[str(registry_path.relative_to(root))] = sha256(registry_path)
    names = [r["submission_name"] for r in artifacts]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate human-readable submission names")
    all_integrity = all(a["validator"]["all_checks_passed"] for a in artifacts) and sidecar_cards_negative
    return dict(schema="gems86.release-readiness.v1", audit_ok=all_integrity,
                decision="DO NOT SUBMIT", submission_ready=False, safe_to_submit=False,
                approved_for_weekly_slot=False, selector_run=False, authenticated_remaining_quota=None,
                new_candidate_generated=False, experiments_run=0, submission_slots_used=0,
                artifact_count=len(artifacts), locally_valid_artifacts=sum(a["safe_to_download_for_audit"] for a in artifacts),
                method="Read-only, all-artifact byte/ZIP/receipt validation using unchanged shared validators. This audit cannot promote or submit a file.",
                shared_tool_hashes_match=all(shared.values()), shared_tools_checked=len(shared),
                input_evidence_sha256=inputs, all_final_artifacts_remeasured=bool(registry_rows),
                registry_scope="One historical witness is sufficient for a negative, never for clearance. No new pre-placement surface was constructed.",
                universal_overlap_blocker=True, witness_sha256=pin["sha256"],
                witness_positive_support_allowed_fraction=cert["covered_allowed_fraction"],
                overlap_limit=cert["overlap_limit"], artifacts=artifacts,
                limitations=[
                    "No nonempty candidate can pass the literal overlap rule while this full-support prior remains in the registry. No exception or revised threshold is authorized.",
                    "No method paragraph was supplied; the actual shared cached stack and a current complete registry are not present.",
                    "Historical holdouts have different folds, buffers, training contexts and CI methods. Their maxima are not a comparable current best.",
                    "All-finite zeros outside the footprint are a local conservative export policy; the public specification describes null/NaN outside bounds. Portal acceptance is not established.",
                    "The rejected upload bytes and an organizer receipt were not supplied; the prior range error's cause and historical scores remain unverified.",
                    "Fault prediction is not confirmation of a geothermal vent, heat supply, permeability, or commercial viability.",
                    "The FVMB archive has malformed paired-delta fields, a separate pin manifest describing absent amendments, and a three-stage/four-ablation budget convention. Its original cards are preserved, not silently repaired into trusted measurements.",
                    "PR #60 (IR-86-SPT-02) bypassed protocol_preflight, masked withheld test faults via full existing_faults.tif, yielded canary AUC 0.4947 (<0.50), omitted 95% CIs, misrepresented SPT prose vs code, and placed unregistered binaries in submission/. Those binaries have been removed and spt-run-card.json / xfleet-run-card.json / submit.html revoked to DO NOT SUBMIT.",
                ])


def session_card(report: dict, root: Path = ROOT) -> dict:
    """Describe this audit only; inherited metrics/hashes are never a new result."""
    plan = strict_json(root / "registry/h86c_hypotheses.json")
    top = plan["hypotheses"][0]
    return dict(
        schema="gems86.session-negative.v1", date_utc="2026-10-23",
        hypothesis=f"{top['id']}: {top['name']} (provisional, NOT RUN; no method lane was assigned)",
        mechanism=top["signature"], named_non_fault_process=top["non_fault_mimic"],
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", status="NOT_RUN_PROTOCOL_STOP",
                         evaluator_version="gems57-pooled-hide-v2", withheld_positives=None, value=None, ci95=None),
        correlation_overlap_vs_registry=dict(status="UNIVERSAL_LITERAL_BLOCKER",
            preplacement_surface=None, new_final_dots=None,
            inherited_final_artifacts_remeasured=report["all_final_artifacts_remeasured"],
            registry_complete=False, witness_sha256=report["witness_sha256"],
            universal_forward_overlap=report["witness_positive_support_allowed_fraction"],
            allowed_overlap_limit=report["overlap_limit"],
            evidence="docs/evidence/all-artifacts-registry.json"),
        raster_sha256=None,
        validator_output=dict(status="NOT_RUN_NO_NEW_RASTER", no_nan_inside_footprint=None,
                              values_in_0_1=None, crs_shape_transform_match=None),
        inherited_artifacts=dict(checked=report["artifact_count"], local_format_pass=report["locally_valid_artifacts"],
            files=[dict(file=a["file"], sha256=a["sha256"], verdict=a["verdict"]) for a in report["artifacts"]],
            evidence="docs/evidence/release-readiness.json", submission_authorized=False),
        submission_name=None,
        note="Protocol STOP: every nonempty allowed candidate overlaps a full-support prior. No new TIF, model experiment or slot used.",
        verdict="negative", submission_ready=False, approved_for_weekly_slot=False,
        new_candidate_generated=False, experiments_run=0, submission_slots_used=0,
        requirement_unmet="No new unique submission TIFF can satisfy the supplied literal rule. Historical files are audit-only, not a substitute new submission.")


def current_review_card(report: dict, registry: dict, root: Path = ROOT) -> dict:
    """Date this remeasurement honestly; do not relabel historical model evidence.

    Called only after --measure-registry, never by a read-only site build.
    The original dated session card remains reproducible archive content.
    """
    card = session_card(report, root)
    measured = datetime.fromisoformat(registry["measured_utc"])
    if measured.tzinfo is None or measured.utcoffset().total_seconds() != 0:
        raise ValueError("Registry measurement must carry a UTC timestamp")
    card.update(schema="gems86.current-review.v1", date_utc=measured.date().isoformat(),
                registry_measured_utc=registry["measured_utc"],
                scope="Fresh byte/format and final-artifact witness audit only. No new scientific experiment, surface, dots or submission.",
                release_report_sha256=sha256(root / "docs/evidence/release-readiness.json"),
                registry_measurement_sha256=sha256(root / "docs/evidence/all-artifacts-registry.json"))
    return card


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # This is an evidence file, not a release raster. Avoid partial JSON on failure.
    temporary = path.with_suffix(path.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure-registry", action="store_true", help="recheck all inherited final dots against the restored witness (no model experiment)")
    args = parser.parse_args(argv)
    if args.measure_registry:
        write_json(ROOT / "docs/evidence/all-artifacts-registry.json", measure_all_registry())
    report = build_report()
    write_json(ROOT / "docs/evidence/release-readiness.json", report)
    write_json(ROOT / "docs/evidence/session-20261023-run-card.json", session_card(report))
    if args.measure_registry and report["audit_ok"]:
        registry = strict_json(ROOT / "docs/evidence/all-artifacts-registry.json")
        write_json(ROOT / "docs/evidence/latest-review-run-card.json", current_review_card(report, registry))
    print(json.dumps({k: report[k] for k in ("audit_ok", "decision", "artifact_count", "locally_valid_artifacts", "all_final_artifacts_remeasured", "experiments_run", "submission_slots_used")}, indent=2))
    return 0 if report["audit_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
