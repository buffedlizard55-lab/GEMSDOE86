"""Registration regression tests for H86N-EQL and the H86M-LT publication repair.

Session 92f9e0e8: H86M-LT shipped unregistered with safe_to_submit=true and an
"OK TO SUBMIT? YES" page while the generated site said DO NOT SUBMIT. These
tests pin the repaired state so the contradiction cannot silently return.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EQL_STEM = "gems86-h86n-eql-seislineation-37654dots-20261025T181759Z-zeros"
LT_STEM = "gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_eql_and_lt_registered_in_both_indexes():
    inv = json.loads((ROOT / "docs/evidence/download-inventory.json").read_text())
    idx = json.loads((ROOT / "registry/artifact_cards.json").read_text())
    inv_files = {a["file"] for a in inv["artifacts"]}
    idx_stems = {a["stem"]: a for a in idx["artifacts"]}
    for stem, kind in ((EQL_STEM, "h86n_eql"), (LT_STEM, "h86m_lt_unvalidated")):
        assert f"docs/downloads/{stem}.tif" in inv_files
        assert idx_stems[stem]["holdout_kind"] == kind
        entry = next(a for a in inv["artifacts"] if a["file"].endswith(stem + ".tif"))
        assert entry["status"] == "DO NOT SUBMIT"
        assert entry["approved_for_weekly_slot"] is False
        assert entry["sha256"] == _sha(ROOT / entry["file"])


def test_eql_run_card_is_measured_negative_no_slot():
    card = json.loads((ROOT / "docs/evidence/h86n-eql-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["gates"]["paired_ci_low_gt_0_vs_C0"] is False
    assert card["gates"]["paired_ci_low_gt_0_vs_C1"] is False
    assert card["holdout"]["evaluator_version"] == "gems57-pooled-hide-v2"
    assert card["holdout"]["candidate"]["withheld_positive_pixels"] == 11321
    assert card["raster_sha256"] == _sha(ROOT / f"docs/downloads/{EQL_STEM}.tif")
    assert len(card["submission_note_le140"]) <= 140
    assert "DO NOT SUBMIT" in card["submission_note_le140"]


def test_lt_historical_promotion_is_separate_from_current_negative_disposition():
    # Preserve the historical lane result, but gate the artifact using the
    # separately registered current protocol disposition.
    card = json.loads((ROOT / "docs/evidence/h86m-lt-run-card.json").read_text())
    assert card["verdict"] == "promote"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    current = json.loads((ROOT / "docs/evidence/h86m-lt-current-disposition.json").read_text())
    assert current["historical_lane_verdict"] == "promote"
    assert current["verdict"] == "negative"
    assert current["decision"] == "DO NOT SUBMIT"
    assert current["holdout_dti"] is None
    page = (ROOT / "docs/h86m-lt.html").read_text()
    assert "IS THIS FILE OK TO SUBMIT? YES" not in page
    assert "DO NOT SUBMIT" in page
