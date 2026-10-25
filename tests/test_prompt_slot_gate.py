"""The full owner-request gate must override a lane-local proxy promotion."""
import json
from pathlib import Path

from scripts.prompt_slot_gate import build_gate

ROOT = Path(__file__).resolve().parents[1]


def test_prompt_gate_is_reproducible_negative_and_bound_to_tif():
    evidence = json.loads((ROOT / "docs/evidence/prompt-slot-gate.json").read_text())
    assert evidence == build_gate(ROOT)
    assert evidence["decision"] == "DO_NOT_SUBMIT_UNDER_CURRENT_REQUEST"
    assert evidence["verdict"] == "negative"
    assert evidence["weekly_slot_authorized"] is False
    assert evidence["organizer_confirmed_score"] is None
    assert evidence["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    candidate = evidence["holdout_dti"]
    incumbent = candidate["current_same_evaluator_same_count_incumbent"]
    assert candidate["evaluator_version"] == incumbent["evaluator_version"]
    assert candidate["withheld_positive_count"] == incumbent["withheld_positive_count"]
    assert candidate["value"] < incumbent["value"]
    assert evidence["correlation_overlap_vs_registry"]["local_gate_pass"] is True
    assert evidence["correlation_overlap_vs_registry"]["full_registry_clearance"] is False
    assert evidence["shared_feature_cache_restored"] is False
    assert evidence["validator_output"]["all_local_checks_passed"] is True
    assert len(evidence["note"]) <= 140
    assert evidence["raster_sha256"] == "ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d"
    assert evidence["submission_name"] == "gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros"
    assert evidence["reasons_not_approved"]
