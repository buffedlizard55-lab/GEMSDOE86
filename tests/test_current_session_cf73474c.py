"""Read-only review facts must not become a fabricated candidate or score."""
import hashlib
from pathlib import Path
import shutil

import pytest

from scripts.audit_release import strict_json
from scripts.build_review_card import SNAPSHOT, build_card, main as review_card_main
from src.gems86.io import BANDS

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return strict_json(ROOT / name)


def test_ranked_proposals_are_scoped_unrun_and_use_actual_band_indices():
    plan = load("registry/h86g_hypotheses.json")
    assert plan["lane_assignment"] is None
    assert len(plan["hypotheses"]) == 4
    assert [h["rank"] for h in plan["hypotheses"]] == [1, 2, 3, 4]
    for h in plan["hypotheses"]:
        assert h["status"] == "NOT_RUN_PROTOCOL_STOP"
        assert h["non_fault_mimic"] and h["falsifier"] and h["novelty"]
        assert isinstance(h["expected_holdout_potential"], str)
        assert "holdout_dti" not in h and "projected_score" not in h
        for layer in h["layers"]:
            assert BANDS[layer["band"]] == layer["name"]


def test_native_receipt_cannot_claim_actual_shared_cache_or_organizer_authentication():
    receipt = load("docs/evidence/session-cf73474c-data.json")
    manifest = load("data/prepared_manifest.json")
    assert receipt["actual_shared_feature_stack_restored"] is False
    assert receipt["organizer_authenticated"] is False
    prep = receipt["native_band_preparation"]
    assert prep["prepared_array_count"] == len(manifest["prepared_arrays"]) == 21
    assert prep["sha256"] == hashlib.sha256((ROOT / prep["manifest"]).read_bytes()).hexdigest()
    assert manifest["shared_template_feature_stack"] is False
    assert manifest["counts"]["has_features"] is True
    assert all(manifest["pins_verified"].values())
    assert prep["publication"]["crash_atomic_across_cache_and_manifest"] is False
    trees = receipt["shared_cache_obtainability"]["trees"]
    assert len(trees) == 2
    assert all(t["truncated"] is False and t["cached_array_objects"] == [] for t in trees)


def test_all_registry_bytes_can_be_present_while_two_grids_still_block_clearance():
    audit = load("docs/evidence/registry-input-grid-review-20261025.json")
    assert audit["byte_coverage_complete"] is True
    assert audit["indexed_rasters_expected"] == len(audit["records"]) == audit["byte_verified_rasters"] == 690
    assert audit["grid_compatible_rasters"] == sum(r["grid_compatible"] for r in audit["records"]) == 688
    assert audit["grid_incompatible_or_invalid_rasters"] == 2
    assert audit["all_grids_compatible"] is False
    assert audit["probability_values_checked"] is False
    assert audit["candidate_comparisons_run"] is audit["uniqueness_clearance"] is audit["submission_authorized"] is False
    bad = {r["sha256"]: r for r in audit["incompatible_or_invalid_records"]}
    horse = bad["ccbe1de0cfd70cbe7257c04669195f390ca652fa3a76c51505f461f01a1424c6"]
    qfaults = bad["538b45735833b341fc455dbbf06c47bc82a8bd8943c254ae6d3a5a07e72e22ca"]
    assert horse["grid_checks"]["transform"] is False and horse["grid_checks"]["crs"] is True
    assert qfaults["grid"]["bands"] == 3 and qfaults["grid_checks"]["transform"] is True
    assert all(row["bytes_verified"] and row["status"] == "GRID_INCOMPATIBLE_DO_NOT_EXCLUDE" for row in bad.values())


def test_pair_and_h33_measurements_do_not_rebrand_inherited_files_as_new_candidates():
    audit = load("docs/evidence/concurrent-artifact-review-20261025.json")
    assert len(audit["comparisons"]) == 2
    for comparison in audit["comparisons"]:
        shared = comparison["shared_result"]
        assert shared["registry_rasters_checked"] == 1
        assert shared["complete_accessible_scan"] is False and shared["unique"] is False
        assert shared["source_errors"]
        assert shared["worst_spearman_full_footprint"] < 0.90
        assert shared["worst_dot_overlap"] < 0.70
    lineage = audit["h33_lineage"]
    assert lineage["exact_parent_minus_2px_catalogue_collar"] is True
    assert lineage["parent_dots"] == lineage["h33_dots"] + lineage["removed_dots"] == 40199
    assert lineage["removed_dots"] == 2545 and lineage["added_dots"] == 0
    assert lineage["organizer_confirmed"] is False
    assert audit["new_candidate_generated"] is audit["submission_authorized"] is audit["preplacement_surfaces_measured"] is False


def test_session_card_is_reproducible_and_leaves_unmeasured_fields_empty():
    card = load("docs/evidence/session-cf73474c-run-card.json")
    assert card == build_card(ROOT)
    assert card["hypothesis"].startswith("H86G-CSPA:")
    assert card["holdout_dti"]["status"] == "NOT_RUN_PROTOCOL_STOP"
    for key in ("value", "ci95", "evaluator_version", "withheld_positive_count", "paired_delta", "paired_ci95"):
        assert card["holdout_dti"][key] is None
    registry = card["correlation_overlap_vs_registry"]
    assert registry["candidate_rho"] is registry["candidate_dot_overlap_3px"] is None
    assert registry["universal_witness_overlap_for_any_nonempty_allowed_candidate"] == 1.0
    assert registry["uncovered_allowed_cells"] == 0
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert card["validator_output"]["inherited_artifact_format_passes"] == card["validator_output"]["inherited_artifact_count"] == 18
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["unique_tiff_requirement_satisfied"] is card["new_candidate_generated"] is card["submission_ready"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["verdict"] == "negative" and 0 < len(card["note"]) <= 140


def test_site_puts_decision_and_download_access_before_long_historical_receipts():
    home = (ROOT / "docs/index.html").read_text()
    executive = (ROOT / "docs/executive-summary.html").read_text()
    for html in (home, executive):
        assert "The requested new, uniqueness-cleared TIFF was not generated in this review." in html
        assert "GZZD/PCC audit gap is now closed" in html
        assert "690 / 690" in html
        assert "parallel lanes: neither was measured" not in html
        assert html.index("DO NOT SUBMIT") < html.index('id="h86f-gzzd"')
    assert home.index('href="#downloads"') < home.index('id="current-review"')
    assert home.index('id="downloads"') < home.index('id="h86f-gzzd"')
    assert executive.index("Download research TIFFs — audit only") < executive.index('id="h86f-gzzd"')


def test_legacy_pages_root_redirect_is_negative_not_a_false_uniqueness_claim():
    root = (ROOT / "index.html").read_text()
    assert 'url=docs/index.html' in root
    assert "DO NOT SUBMIT" in root
    assert "generated a new unique GeoTIFF" not in root
    assert "No new submission was generated" in root


def test_frozen_card_survives_live_daily_audit_refresh_without_rebranding(tmp_path):
    shutil.copytree(ROOT / SNAPSHOT, tmp_path / SNAPSHOT)
    expected = build_card(ROOT)
    # Only immutable evidence is needed. New live audit clocks, changed counts
    # and even a future assigned lane must not rewrite this historical review.
    for rel in ("docs/evidence/protocol-preflight.json", "docs/evidence/release-readiness.json",
                "docs/evidence/all-artifacts-registry.json", "registry/h86g_hypotheses.json"):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"measured_utc":"2099-01-01T00:00:00+00:00","artifact_count":999,"lane_assignment":"future"}')
    assert build_card(tmp_path) == expected
    assert expected["evidence_source_revision"] == "5aabaf2fa780e9e589c40ca58d9819a55280ce54"
    assert len(expected["original_input_snapshots"]) == 9
    assert expected["measured_registry_utc"].startswith("2026-10-25")
    assert expected["verdict"] == "negative"


@pytest.mark.parametrize("defect", ["hash", "missing", "escape"])
def test_frozen_card_rejects_missing_tampered_or_escaping_evidence(tmp_path, defect):
    shutil.copytree(ROOT / SNAPSHOT, tmp_path / SNAPSHOT)
    manifest_path = tmp_path / SNAPSHOT / "manifest.json"
    manifest = strict_json(manifest_path)
    first = next(iter(manifest["sources"].values()))
    path = tmp_path / first["file"]
    if defect == "hash":
        path.write_bytes(path.read_bytes() + b"\n")
    elif defect == "missing":
        path.unlink()
    else:
        first["file"] = "outside.json"
        (tmp_path / "outside.json").write_text("{}")
        import json
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises((OSError, ValueError)):
        build_card(tmp_path)


def test_frozen_card_cli_check_is_read_only():
    path = ROOT / "docs/evidence/session-cf73474c-run-card.json"
    before = path.read_bytes()
    assert review_card_main(["--check"]) == 0
    assert path.read_bytes() == before
