"""The current session must stay a no-file negative stop."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_h86l_run_card_forbids_submission_and_names_no_raster():
    card = json.loads((ROOT / "docs/evidence/h86l-vfgr-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_file"] is None
    assert card["raster_sha256"] is None
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["ok_to_submit_to_portal"] is False
    paired = card["holdout_dti"]["paired_differences"]["E2_raw_edge"]
    assert paired["ci95"][1] < 0
    repos = {hit["repo"] for hit in card["correlation_overlap_vs_registry"]["final_dots"]["informative_overlap_firings"]}
    assert "GEMSDOE46" in repos


def test_homepage_states_the_no_file_decision():
    home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert "NO FILE AUTHORIZED · DO NOT SUBMIT" in home
    assert 'id="h86l-vfgr"' in home
    assert "This review generated no new candidate TIFF" in home
    assert "Is it OK to submit to DrivenData? NO" in home
    assert "DO NOT SUBMIT" in home
    assert "0 weekly slots used" in home
    executive = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
    assert executive.index('id="h86l-vfgr"') < executive.index("Future submission steps")
