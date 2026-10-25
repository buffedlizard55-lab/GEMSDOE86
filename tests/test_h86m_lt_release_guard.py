"""The upstream H86M-LT lane-local promote card must not authorize global upload."""
import json
from pathlib import Path
import shutil

from scripts.h86m_lt_release_guard import (
    CARD_REL,
    CANDIDATE_REL,
    OVERLAY_REL,
    valid_h86m_lt_release_overlay,
)

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_h86m_lt_overlay_preserves_lane_promote_but_blocks_global_release():
    assert valid_h86m_lt_release_overlay(ROOT)
    card = json.loads((ROOT / CARD_REL).read_text())
    overlay = json.loads((ROOT / OVERLAY_REL).read_text())
    assert card["verdict"] == "promote" and card["safe_to_submit"] is True
    assert card["approved_for_weekly_slot"] is False
    assert overlay["global_release_decision"] == "DO NOT SUBMIT"
    assert overlay["global_safe_to_submit"] is False
    assert overlay["holdout_dti_status"] == "NOT_RUN_ALTERNATE_EVIDENCE_DESIGN"


def test_h86m_lt_overlay_rejects_mutated_global_decision(tmp_path):
    for relative in (CARD_REL, OVERLAY_REL, CANDIDATE_REL):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    overlay_path = tmp_path / OVERLAY_REL
    overlay = json.loads(overlay_path.read_text())
    overlay["global_safe_to_submit"] = True
    overlay_path.write_text(json.dumps(overlay))
    assert not valid_h86m_lt_release_overlay(tmp_path)
