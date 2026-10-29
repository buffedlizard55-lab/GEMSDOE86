"""The 2026-10-29 Focus-9 review card must preserve its negative gates and provenance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "docs/evidence/session-6ad5bdd2-run-card.json"


def test_session_card_is_an_explicit_negative_no_candidate_result():
    card = json.loads(CARD_PATH.read_text())
    assert card["session_branch"] == "arena/6ad5bdd2-gemsdoe86"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["verdict"] == "negative"
    assert card["lane_assignment"] is None
    assert card["new_candidate_generated"] is False
    assert card["unique_tiff_requirement_satisfied"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["organizer_score_estimate_for_new_candidate"] is None
    assert card["note_character_count"] == len(card["note"]) <= 140
    assert "DO NOT SUBMIT" in card["note"]


def test_session_card_keeps_proposed_hypothesis_and_non_fault_mimics_unrun():
    card = json.loads(CARD_PATH.read_text())
    assert card["hypothesis"]["id"] == "F9N-1_LAHONTAN_SHORELINE_OFFSETS"
    assert card["hypothesis"]["status"] == "PROPOSED_NOT_RUN_NOT_SELECTED"
    assert card["hypothesis"]["selection_for_execution"] is False
    assert card["mechanism"]["status"] == "NOT_MEASURED"
    assert card["named_non_fault_process"]["status"] == "PROPOSED_MIMICS_NOT_TESTED"
    assert card["holdout_dti"]["status"].startswith("NOT_RUN")
    assert card["holdout_dti"]["evaluator_version"] is None
    assert card["holdout_dti"]["withheld_positives"] is None
    assert card["holdout_dti"]["value"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["leakage_canary"]["status"] == "NOT_RUN_NO_FEATURES"


def test_session_card_labels_the_owner_claim_and_separate_holdout_dti():
    card = json.loads(CARD_PATH.read_text())
    claim = card["highest_supplied_focus9_claim"]
    assert claim["site"] == "GEMSDOE32"
    assert claim["score"] == 0.2778
    assert claim["evidence_class"] == "OWNER-REPORTED / UNVERIFIED"
    assert claim["organizer_confirmed"] is False
    assert claim["receipt_links_score_to_exact_raster_bytes"] is False
    holdout = card["separate_owner_repository_holdout_context"]
    assert holdout["evidence_class"].startswith("HOLDOUT-DTI")
    assert holdout["evaluator"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
    assert holdout["withheld_positives"] == 22232
    assert holdout["value"] == 0.00451537871535044
    assert holdout["ci95"] == [0.0038164175817344387, 0.005261598301920283]
    assert holdout["is_this_session_experiment"] is False
    assert holdout["is_leaderboard_score"] is False
    assert holdout["is_calibrated_estimate_for_new_file"] is False
    assert holdout["source_commit_sha"] == "0ffda7162e76291df34359345488ff08b4115aac"
    assert holdout["source_git_blob_sha1"] == "2db3e712919496376f4810f625a17294bccbe3c1"
    assert holdout["source_content_sha256"] == "eebd75b181f89dfe36262d25ccc068bba1b2b0afb589ef675af1cffa630d8e9b"


def test_input_and_witness_stops_are_machine_bound():
    card = json.loads(CARD_PATH.read_text())
    inputs = card["current_inputs"]
    assert inputs["native_training_features_tif_available"] is False
    assert inputs["training_features_copies_missing"] == 2
    assert inputs["prepared_arrays_and_masks_missing"] == inputs["prepared_array_total"] == 21
    assert inputs["shared_feature_cache_ready"] is False
    assert inputs["safe_to_submit"] is False
    reg = card["correlation_overlap_vs_registry"]
    assert reg["status"] == "NO_CANDIDATE_MEASURED; UNIVERSAL_LITERAL_STOP"
    assert reg["direct_support_uncovered_allowed_pixels"] == 0
    assert reg["witness_implied_forward_overlap_for_any_nonempty_allowed_candidate"] == 1.0
    assert reg["overlap_limit"] == 0.70
    assert reg["registry_complete"] is False
    assert reg["separate_focus9_cohort_measurement"]["directed_3px_pairs"] == 72
    assert len(reg["separate_focus9_cohort_measurement"]["pairs_exceeding_0p70"]) == 72


def test_new_path_metadata_and_all_evidence_hashes_are_not_overstated():
    card = json.loads(CARD_PATH.read_text())
    feed = card["upstream_github_feed"]
    assert feed["repositories_snapshotted"] == feed["repositories_requested"] == 92
    assert feed["new_focus9_tif_paths"] == 9
    assert feed["sites_with_new_paths"] == 5
    assert feed["new_path_content_bytes_verified"] is False
    assert feed["new_path_scores"].startswith("UNKNOWN_NOT_ZERO")
    assert feed["organizer_receipts"] == 0
    assert card["safe_for_forensic_download"] is True
    assert card["safe_to_download"] is False
    for path, expected in card["evidence_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
