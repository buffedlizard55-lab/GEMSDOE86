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
    # Research promotion must never override false authorization fields.
    assert "NO FILE AUTHORIZED" in html
    assert "IS THIS FILE OK TO SUBMIT? NO" in html
    assert "IS THIS FILE OK TO SUBMIT? YES" not in html
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


def test_promoted_lane_does_not_authorize_upload_in_any_published_guide():
    """A PROMOTE label cannot contradict the card's false slot permissions."""
    card = json.loads((DOCS / "evidence/h86g-edti-run-card.json").read_text())
    summary = json.loads((DOCS / "data/summary.json").read_text())
    assert card["verdict"] == "promote"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    for flag in ("safe_to_submit", "approved_for_weekly_slot", "selector_run"):
        assert summary[flag] is False
    historical = summary["historical_h86g_lane"]
    assert historical["raster_sha256"] == card["raster_sha256"]
    assert historical["historical_verdict"] == "promote"
    assert historical["current_verdict"] == "negative"
    assert historical["safe_to_submit"] is False
    assert historical["approved_for_weekly_slot"] is False
    for guide in ("index.html", "executive-summary.html"):
        html = (DOCS / guide).read_text()
        assert "IS THIS FILE OK TO SUBMIT? NO — DO NOT SUBMIT" in html
        assert "SAFE TO DOWNLOAD FOR AUDIT ONLY" in html
        for unsafe in ("IS THIS FILE OK TO SUBMIT? YES", "SUBMIT THIS FILE",
                       "submit this file", "OK to download and submit",
                       "One file is OK to submit", "SUBMIT ONLY H86G-EDTI"):
            assert unsafe not in html
