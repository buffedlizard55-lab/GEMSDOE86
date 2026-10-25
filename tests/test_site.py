"""The published site must expose real downloads and fail closed on slot authorization."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_download_links_and_fail_closed_decision():
    html = (DOCS / "index.html").read_text()
    parallel = json.loads((ROOT / "evidence/run_card.json").read_text())
    rmrb = json.loads((DOCS / "evidence/rmrb86-run-card.json").read_text())
    for name in (parallel["raster_name"], Path(rmrb["download_file"]).name):
        assert name in html
        assert (DOCS / "downloads" / name).is_file()
    assert "DO NOT SUBMIT" in html
    # The lane's own A4 PROMOTE is not enough under the owner's stricter full-request gates.
    assert "NO FILE CLEARS THE FULL CURRENT REQUEST" in html
    assert "IS THIS FILE OK TO SUBMIT? NO" in html
    assert "SAFE TO DOWNLOAD FOR REVIEW ONLY" in html
    assert "Do not upload H86G-EDTI or spend a weekly slot" in html
    executive = (DOCS / "executive-summary.html").read_text()
    assert "CURRENT DECISION: DO NOT SUBMIT" in executive
    assert "PROMOTE (LANE ONLY) · DO NOT SUBMIT UNDER FULL REQUEST" in executive
    assert "OK TO SUBMIT (selector-ready)" not in html + executive
    assert "Download TIFF — review/audit only" in html
    gate = json.loads((DOCS / "evidence/prompt-slot-gate.json").read_text())
    assert gate["decision"] == "DO_NOT_SUBMIT_UNDER_CURRENT_REQUEST"
    assert gate["verdict"] == "negative" and gate["weekly_slot_authorized"] is False
    assert gate["holdout_dti"]["value"] < gate["holdout_dti"]["current_same_evaluator_same_count_incumbent"]["value"]
    assert gate["shared_feature_cache_restored"] is False
    assert gate["correlation_overlap_vs_registry"]["full_registry_clearance"] is False
    summary = json.loads((DOCS / "data/summary.json").read_text())
    assert summary["approved_for_weekly_slot"] is False
    assert summary["selector_run"] is False
    assert summary["promoted_for_selector_review"]["safe_to_submit"] is False
    assert summary["request_level_gate"]["decision"] == gate["decision"]
    assert summary["request_level_gate"]["weekly_slot_authorized"] is False
    assert summary["request_level_gate"]["organizer_confirmed_score"] is None
    assert rmrb["safe_to_download"] is True
    assert rmrb["safe_to_submit"] is False


def test_h33_claim_and_holdout_scores_show_evidence_class_and_context():
    html = (DOCS / "index.html").read_text()
    # Fleet-page scores are owner claims, not organizer-confirmed results.
    assert "0.2778</code> OWNER-REPORTED; not organizer-confirmed" in html
    assert "0.3195</code> and <code>0.4413</code> current-leaderboard values are OWNER-REPORTED and unverified" in html
    # Every visible holdout score includes its evaluator, withheld-positive count,
    # and interval; the paired delta is explicitly labeled as holdout evidence.
    assert "<strong>HOLDOUT-DTI</strong> (<code>gems57-pooled-hide-v2</code>, <code>22,893</code> withheld positives)" in html
    assert "<code>H86D-CTHB</code> = <code>0.1133</code>, 95% CI <code>[0.0965, 0.1297]</code>" in html
    assert "<code>H33-2-B2</code> fold-fair control = <code>0.1056</code>, 95% CI <code>[0.0936, 0.1166]</code>" in html
    assert "paired HOLDOUT-DTI delta = <code>+0.0076</code>, 95% CI <code>[-0.0101, +0.0241]</code>" in html
    assert "Do not infer a leaderboard projection from holdout results." in html


def test_zip_contains_single_tiff():
    import zipfile
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    archive = DOCS / "downloads" / (card["raster_name"][:-4] + ".zip")
    assert archive.is_file()
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert names == [card["raster_name"]]
        assert bundle.getinfo(names[0]).file_size > 100_000
