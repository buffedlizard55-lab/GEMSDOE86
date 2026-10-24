"""H86E (2026-10-24) artifact/card consistency.  Read-only: no model is fit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs/evidence/h86e-run-card.json"


def _card():
    return json.loads(CARD.read_text())


def test_h86e_card_is_negative_and_never_authorizes():
    c = _card()
    assert c["verdict"] == "negative"
    assert c["decision"] == "DO NOT SUBMIT"
    assert c["submission_ready"] is False
    assert c["safe_to_submit"] is False
    assert c["approved_for_weekly_slot"] is False
    assert c["submission_slots_used"] == 0
    assert set(c["gates"]) == {"G1_format", "G2_canary", "G3_holdout_vs_controls",
                               "G4_holdout_best", "G5_sgmc_proxy", "G6_uniqueness"}
    assert c["gates"]["G1_format"]["passed"] is True
    assert c["gates"]["G4_holdout_best"]["passed"] is False
    assert sorted(c["gates_failed"]) == ["G4_holdout_best", "G5_sgmc_proxy", "G6_uniqueness"]


def test_h86e_raster_matches_card_and_note_limits():
    c = _card()
    tif = ROOT / c["submission_file"]
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == c["raster_sha256"]
    assert 0 < len(c["note"]) <= 140 and c["note_chars"] == len(c["note"])
    assert 0 < len(c["submission_name"]) <= 140
    v = c["validator_output"]
    assert v["all_checks_passed"] is True
    assert v["n_nan_inside_footprint"] == 0
    assert 0.0 <= v["min"] and v["max"] <= 1.0
    assert v["emitted_dots"] == 44090


def test_h86e_holdout_is_labelled_with_ci_and_design():
    h = _card()["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positives"] == 11321
    lo, hi = h["ci95"]
    assert lo < h["value"] < hi
    assert "buffered whole components" in h["design"]


def test_h86e_registered_in_inventory_and_cards():
    c = _card()
    inv = json.loads((ROOT / "docs/evidence/download-inventory.json").read_text())
    hits = [e for e in inv["artifacts"] if e["file"] == c["submission_file"]]
    assert len(hits) == 1 and hits[0]["sha256"] == c["raster_sha256"]
    assert hits[0]["approved_for_weekly_slot"] is False
    idx = json.loads((ROOT / "registry/artifact_cards.json").read_text())
    stem = Path(c["submission_file"]).stem
    assert any(a["stem"] == stem and a["card"] == "docs/evidence/h86e-run-card.json"
               for a in idx["artifacts"])
