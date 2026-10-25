"""Regression checks for the 2026-10-25 follow-up review and current research queue."""
import json
from pathlib import Path

from src.gems86.io import BANDS

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_followup_queue_contains_only_scoped_unrun_native_layer_hypotheses():
    queue = load("registry/followup_hypotheses_20261025.json")
    assert queue["lane_assignment"] is None
    assert queue["status"] == "PROPOSALS_ONLY_NOT_AUTHORIZED_OR_IMPLEMENTED"
    assert queue["common_data_requirement"]["new_external_data_required"] is False
    assert queue["common_data_requirement"]["actual_shared_feature_stack_restored"] is False
    assert [item["rank"] for item in queue["hypotheses"]] == [1, 2, 3]
    assert all(item["status"] == "NOT_RUN_PROTOCOL_STOP" for item in queue["hypotheses"])
    assert [item["id"] for item in queue["hypotheses"]] == ["BMR", "GSST", "CNT"]
    for hypothesis in queue["hypotheses"]:
        assert hypothesis["physical_signature"]
        assert hypothesis["catalogue_missing_rationale"]
        assert hypothesis["non_fault_mimic"]
        assert hypothesis["novelty"]
        assert hypothesis["falsifier"]
        assert "holdout_dti" not in hypothesis
        assert "projected_score" not in hypothesis
        for layer in hypothesis["layers"]:
            assert BANDS[layer["band"]] == layer["name"]
    # The historical proposals are explicitly superseded rather than mislabeled untried.
    excluded = " ".join(
        f"{row['method']} {row['evidence']} {row['disposition']}"
        for row in queue["excluded_as_already_tried"]
    )
    assert "H86J-CSGD" in excluded
    assert "H86J-MPC" in excluded
    assert "H86K-PSC" in excluded
    assert "GDSC" in excluded
    assert "GEMSDOE52" in " ".join(row["evidence"] for row in queue["excluded_as_already_tried"])


def test_current_site_uses_followup_queue_and_preserves_no_submit_status():
    hypotheses = (ROOT / "docs/hypotheses.html").read_text(encoding="utf-8")
    home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert "2026-10-25 follow-up: three unrun native-band hypotheses" in hypotheses
    assert "H86J-CSGD subsequently implemented" in hypotheses
    assert "H86J-MPC implemented and evaluated" in hypotheses
    assert "H86K-PSC implemented saddle persistence" in hypotheses
    assert "New proposal 1 · BMR · NOT RUN" in hypotheses
    assert "New proposal 3 · CNT · NOT RUN" in hypotheses
    assert "New proposal 4 · CNT · NOT RUN" not in hypotheses
    assert "New proposal 1 · H86G-CSPA · NOT RUN" not in hypotheses
    assert "New proposal 2 · H86G-MPC · NOT RUN" not in hypotheses
    assert "Latest follow-up run card" in home
    assert "this follow-up produced no TIFF, experiment, or slot" in home
    assert "Current independent review" in home
    assert "training_features.tif available = <strong>false</strong>" in home
    assert "Data restored. Submission still blocked." not in home
    assert "NO FILE AUTHORIZED · DO NOT SUBMIT" in home
    submit = (ROOT / "docs/submit.html").read_text(encoding="utf-8")
    assert "Prior forensic reviews found" in submit
    assert "does not rerun those PR-specific forensic investigations" in submit


def test_followup_run_card_is_negative_and_does_not_borrow_historical_scores():
    card = load("docs/evidence/session-20261025-followup-run-card.json")
    preflight = load("docs/evidence/protocol-preflight.json")
    # A dated review binds its original bytes, not a later refreshed audit.
    # Live timestamp/hash binding is separately tested in test_current_review.py.
    import hashlib
    source = card["registry_measurement_source"]
    source_path = (ROOT / source["file"]).resolve()
    assert source_path.is_relative_to((ROOT / "docs/evidence/session-followup-snapshot").resolve())
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source["sha256"]
    registry = load(source["file"])
    assert card["hypothesis"].startswith("BMR:")
    assert card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["status"] == "NOT_RUN_NO_LANE_ASSIGNED_AND_PROTOCOL_STOP"
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert card["correlation_overlap_vs_registry"]["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert card["correlation_overlap_vs_registry"]["witness_sha256"] == preflight["witness_sha256"]
    # This is a historical, immutable follow-up. A later --measure-registry
    # refreshes the current proof and registry timestamps without rerunning the
    # archived follow-up or falsifying its measurement clock.
    from datetime import datetime
    assert (datetime.fromisoformat(card["correlation_overlap_vs_registry"]["witness_measured_utc"])
            <= datetime.fromisoformat(preflight["measured_utc"]))
    assert (datetime.fromisoformat(card["correlation_overlap_vs_registry"]["registry_measurement_utc"])
            <= datetime.fromisoformat(registry["measured_utc"]))
    assert card["correlation_overlap_vs_registry"]["uncovered_allowed_pixels"] == 0
    assert card["correlation_overlap_vs_registry"]["universal_overlap_for_any_nonempty_allowed_candidate"] == 1.0
    assert card["correlation_overlap_vs_registry"]["registry_complete"] is False
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert card["new_candidate_generated"] is card["unique_tiff_requirement_satisfied"] is False
    assert card["submission_ready"] is card["safe_to_submit"] is card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["verdict"] == "negative"
    assert 0 < len(card["note"]) <= 140


def test_gdsc_writer_receipt_explicitly_records_negative_download_only_state():
    receipt = load(
        "docs/downloads/gems86-gdsc-dilatational-37654dots-20261025T134427Z-70224321-zeros.json"
    )
    assert receipt["zip_file"] == "gems86-gdsc-dilatational-37654dots-20261025T134427Z-70224321-zeros.zip"
    assert receipt["promoted"] is False
    assert receipt["approved_for_weekly_slot"] is False
    assert receipt["safe_to_submit"] is False


def test_h33_analysis_has_a_prominent_noncausal_correction():
    analysis = (ROOT / "research/H33_ANALYSIS.md").read_text(encoding="utf-8")
    assert "Correction / interpretation limit (2026-10-25)" in analysis
    assert "cannot be causally assigned the score change" in analysis
    assert "coverage-efficient emission is one plausible, unverified mechanism" in analysis
    assert "score moved from 0.2708 to 0.2778 (+0.0070 owner-reported) purely" not in analysis


def test_merged_h33_phd_note_is_historical_and_noncausal():
    analysis = (ROOT / "research/H33_PHDPH_ANALYSIS.md").read_text(encoding="utf-8")
    assert "not the current untried queue" in analysis
    assert "may still cover a withheld fault" in analysis
    assert "does not measure either lost truth credit" in analysis
    assert "It is not a score or a leaderboard projection" in analysis
    assert "Selection for implementation: **GDSC Rank 1**" not in analysis
