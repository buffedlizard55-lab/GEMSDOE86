"""The 2026-10-29 Focus-9 reconciliation preserves source and score evidence classes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "research/run_cards/focus9_review_20261029_arena_9934389d.json"
SOURCE_PATH = ROOT / "docs/evidence/focus9-source-review-20261029.json"


def test_current_source_review_is_pinned_to_metadata_refresh_and_fails_closed():
    card = json.loads(CARD_PATH.read_text())
    source = json.loads(SOURCE_PATH.read_text())
    feed = json.loads((ROOT / "docs/evidence/fleet-feed.json").read_text())
    preflight = json.loads((ROOT / "docs/evidence/protocol-preflight.json").read_text())
    release = json.loads((ROOT / "docs/evidence/release-readiness.json").read_text())

    assert source["session_branch"] == card["session_branch"] == "arena/9934389d-gemsdoe86"
    assert source["fleet_refresh"]["refreshed_utc"] == feed["refreshed_utc"]
    assert source["fleet_refresh"]["projects_snapshotted"] == 92
    assert source["fleet_refresh"]["organizer_receipts_obtained"] == 0
    assert source["scope"]["official_drivendata_page_accessed_this_review"] is False
    projects = {row["repository"]: row for row in feed["projects"]}
    assert len(source["focus9_current_repository_snapshots"]) == 9
    for snapshot in source["focus9_current_repository_snapshots"]:
        project = projects[snapshot["repository"]]
        assert snapshot["current_main_commit"] == project["commit_sha"]
        assert snapshot["current_tree_tif_count"] == project["current_tree_tif_count"]
        assert snapshot["published_download_tif_count"] == project["published_download_tif_count"]
        assert snapshot["source_commit_date_utc"] == project["source_commit_date"]
        assert snapshot["organizer_score_verified"] is False
        assert snapshot["raster_bytes_verified"] is False
        expected_recent = {
            item["path"]: {"git_blob_sha1": item["git_blob_sha1"], "git_blob_bytes": item["git_blob_bytes"]}
            for item in project["tif_git_objects"]
            if "20261028" in item["path"] or "20261029" in item["path"]
        }
        actual_recent = {
            item["path"]: {"git_blob_sha1": item["git_blob_sha1"], "git_blob_bytes": item["git_blob_bytes"]}
            for item in snapshot["tif_git_objects_named_2026_10_28_or_29"]
        }
        assert actual_recent == expected_recent
    assert source["new_tif_metadata"]["path_count"] == 23
    assert source["new_tif_metadata"]["path_count_is_raster_count"] is False
    assert source["current_file_byte_revalidation"]["status"] == "BLOCKED_BY_GITHUB_API_RATE_LIMIT"
    assert source["current_file_byte_revalidation"]["independent_current_sha256_verified"] is False
    assert card["new_candidate_generated"] is False
    assert card["experiment_budget"]["experiments_used"] == 0
    assert card["submission"]["weekly_slots_used"] == 0
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False

    assert preflight["status"] == card["binding_preflight"]["status"] == "STOP_LITERAL_OVERLAP_UNSATISFIABLE"
    assert preflight["allowed_pixels"] == card["binding_preflight"]["allowed_pixels"] == 5_106_385
    assert preflight["uncovered_allowed_pixels"] == 0
    assert card["binding_preflight"]["literal_forward_overlap_lower_bound_for_any_nonempty_candidate"] == 1.0
    assert card["binding_preflight"]["overlap_limit"] == 0.70
    assert card["binding_preflight"]["thresholds_unchanged"] is True
    assert release["decision"] == card["release_audit"]["decision"] == "DO NOT SUBMIT"
    assert card["release_audit"]["artifacts"] == card["release_audit"]["locally_valid"] == 50
    verification = card["verification"]
    assert verification["make_verify"] == verification["site_build_check"] == "PASS"
    assert verification["site_links_integrity_safety"].startswith("PASS")
    assert verification["download_audit"]["research_tiffs_revalidated"] == 50
    assert verification["download_audit"]["selector_decision_made"] is False
    assert verification["pytest"] == {
        "passed": 1166, "skipped": 24, "warnings": 48, "subtests_passed": 58,
    }


def test_nine_site_rows_keep_owner_claims_estimates_and_uniqueness_separate():
    card = json.loads(CARD_PATH.read_text())
    rows = card["focus9_owner_claims"]
    assert len(rows) == 9
    assert {row["site"] for row in rows} == {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    }
    top = max(rows, key=lambda row: row["score"])
    assert top["site"] == "GEMSDOE32"
    assert top["score"] == 0.2778
    assert all(row["score_evidence_class"] == "OWNER-REPORTED / UNVERIFIED" for row in rows)
    assert all(row["estimated_leaderboard_score"] is None for row in rows)
    assert all(row["estimate_status"] == "NOT ESTIMATED" for row in rows)
    assert all(row["unique_within_nine_site_cohort"] is False for row in rows)
    assert all(row["max_directed_3px_overlap_vs_other_eight"] > 0.70 for row in rows)
    assert all(row["current_main_path_still_listed_in_metadata"] for row in rows)
    assert all(row["current_main_bytes_verified_against_historical_sha256"] is False for row in rows)
    assert all(row["download_status"] == "FORENSIC / AUDIT ONLY" for row in rows)
    assert all(row["submit_authorized"] is False for row in rows)
    assert card["correlation_overlap_vs_registry"]["directed_pair_count"] == 72
    assert card["correlation_overlap_vs_registry"]["full_registry_clearance"] is False


def test_global_leaderboard_and_g36_receipt_anomaly_are_not_upgraded():
    source = json.loads(SOURCE_PATH.read_text())
    card = json.loads(CARD_PATH.read_text())
    by_value = {row["value"]: row for row in source["leaderboard_conflicts"]}
    assert {0.3195, 0.4413, 0.4437, 0.4544} <= set(by_value)
    assert all(row["accepted_as_current_official_score"] is False for row in by_value.values())
    assert card["leaderboard_evidence_boundary"]["official_drivendata_page_accessed"] is False
    assert card["leaderboard_evidence_boundary"]["current_global_leader_verified"] is False

    anomaly = source["artifact_receipt_irregularity"]
    assert anomaly["site"] == "GEMSDOE36"
    assert anomaly["owner_field"] == "organizer_confirmed_dti"
    assert anomaly["owner_field_value"] == 0.275
    assert anomaly["receipt_reference_in_record"] is False
    assert anomaly["classification_for_this_report"] == "OWNER-REPORTED / UNVERIFIED pending an artifact-bound submission-page receipt"


def test_h33_owner_claim_and_holdout_record_remain_separate():
    source = json.loads(SOURCE_PATH.read_text())
    card = json.loads(CARD_PATH.read_text())
    h33 = source["h33_interpretation"]
    assert h33["owner_reported_public_score"] == 0.2778
    assert h33["score_delta_owner_claims"] == 0.0070
    assert h33["causality_asserted"] is False
    holdout = card["historical_h33_holdout_context"]
    assert holdout["evidence_class"] == "HOLDOUT-DTI"
    assert holdout["evaluator_version"] == "gems57-pooled-hide-v2"
    assert holdout["withheld_positive_count"] == 11_321
    assert round(holdout["value"], 4) == 0.0961
    assert [round(x, 4) for x in holdout["ci95"]] == [0.0828, 0.1083]
    assert holdout["not_comparable_as"] == "leaderboard score or causal estimate"
    assert card["holdout_dti"]["status"] == "NOT_RUN_IN_THIS_REVIEW_NO_LANE_ASSIGNED"
    assert card["holdout_dti"]["value"] is None


def test_three_ranked_hypotheses_remain_unrun_and_data_availability_is_scoped():
    card = json.loads(CARD_PATH.read_text())
    hypotheses = card["hypotheses"]
    assert hypotheses["count"] == 3
    assert hypotheses["status"] == "PROPOSED_NOT_RUN"
    assert hypotheses["data_availability"].startswith("Official 3DEP, NGMDB, and ComCat links retained")
    assert "no local required data" in hypotheses["data_availability"]
