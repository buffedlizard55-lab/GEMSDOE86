"""Regression tests for evidence-driven, no-submit Pages generation."""
import csv
import json
from pathlib import Path

from scripts import build_site

ROOT = Path(__file__).resolve().parents[1]


def test_summary_is_strict_json_and_fails_closed():
    summary = build_site.build_summary(ROOT)
    json.dumps(summary, allow_nan=False)
    assert summary["decision"] == "DO NOT SUBMIT"
    assert summary["submission_ready"] is False
    assert summary["safe_to_submit"] is False
    lane = summary["latest_evaluated_lane"]
    assert lane["verdict"] == "negative"
    assert lane["submission_ready"] is False
    assert lane["approved_for_weekly_slot"] is False
    assert lane["holdouts"][0]["candidate"]["evidence_class"] == "HOLDOUT-DTI"
    assert lane["holdouts"][0]["paired_delta_vs_d2_8"]["ci95"][0] < 0
    assert lane["holdouts"][0]["paired_delta_vs_d2_8"]["ci95"][1] > 0
    assert summary["organizer_confirmed_score"] is None
    assert summary["organizer_receipt_present"] is False
    card = json.loads((ROOT / "docs/evidence/session-review-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["experiments_run"] == 0
    assert card["submission_slots_used"] == 0
    assert card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["status"] == "NOT_RUN_PROTOCOL_STOP"
    inherited = card["inherited_candidate"]
    assert inherited["generated_in_this_review"] is False
    assert inherited["raster_sha256"] == lane["sha256"]
    assert inherited["submission_name"] == lane["submission_name"]
    assert inherited["note"] == lane["note"]
    assert inherited["holdout_dti"]["buffered_whole_components_loqo"]["withheld_positives"] == 11321


def test_hypothesis_shortlist_has_required_qualitative_fields():
    proposal = json.loads((ROOT / "research/next_hypotheses.json").read_text())
    assert 3 <= len(proposal["hypotheses"]) <= 5
    assert proposal["top_candidate"] == proposal["hypotheses"][0]["id"]
    for hypothesis in proposal["hypotheses"]:
        for field in (
            "layers", "physical_signature", "missing_fault_mechanism",
            "non_fault_mimic", "difference_from_repo", "repository_novelty", "expected_dti_potential",
            "implementation_cost", "data_availability", "official_sources",
        ):
            assert hypothesis[field]
    page = build_site.render_hypotheses(ROOT)
    assert "numerical DTI projection" in page
    assert "H86N-BMR" in page


def test_generated_pages_use_live_evidence_and_owner_ledger_labels():
    evidence = (ROOT / "docs/evidence.html").read_text()
    sources = (ROOT / "docs/sources.html").read_text()
    assert "HOLDOUT-DTI" in evidence
    assert "gems57-pooled-hide-v2" in evidence
    assert "DO NOT SUBMIT" in evidence
    assert "ORGANIZER-CONFIRMED score or submission-page receipt" in (ROOT / "docs/index.html").read_text()
    assert "not an organizer receipt" in sources
    assert "review-source-checks.json" in sources
    with (ROOT / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    values = {row["site"]: (row["score"], row["evidence_class"]) for row in rows}
    assert values["GEMSDOE80"][0] == "0.0943"
    assert "unverified" in values["GEMSDOE80"][1]
    assert values["GEMSDOE81"][0] == "0.0041"
    assert (ROOT / "docs/data/prior_scores.csv").read_bytes() == (ROOT / "registry/prior_scores.csv").read_bytes()
