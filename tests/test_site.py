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


def test_hypothesis_page_labels_h86p_inputs_as_historical_and_current_queue_as_unrun():
    """Do not let preregistration-time cache claims masquerade as current availability."""
    html = (DOCS / "hypotheses.html").read_text()
    assert "Current 2026-10-26 re-audit (not the historical pre-run environment)" in html
    assert "native feature TIFF, prepared arrays and shared feature cache are absent" in html
    assert "three remaining hypotheses (BCSF, RCSD, USMT) are unrun" in html
    assert "literal registry witness blocks every nonempty candidate" in html
    assert "current-workspace-input-audit-20261026.json" in html
    assert "SESSION_20261026_H86P_TCWB_REVIEW.md" in html


def test_current_h86p_decision_precedes_historical_session_banners():
    """Keep the newest file and its negative release decision ahead of stale lanes."""
    name = "gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif"
    for guide in ("index.html", "executive-summary.html"):
        html = (DOCS / guide).read_text()
        current = html.index('id="h86p-tcwb-banner"')
        historical_h86n = html.index('id="h86n-gsst"')
        historical_h86l = html.index('id="h86l-vfgr"')
        assert current < historical_h86n < historical_h86l
        decision_text = ("NO FILE AUTHORIZED · DO NOT SUBMIT" if guide == "index.html"
                         else "CURRENT DECISION: DO NOT SUBMIT ANY FILE")
        assert html.index(decision_text) < historical_h86n
        assert name in html
        assert "Download safety: SAFE FOR RESEARCH/AUDIT ONLY" in html
        assert "Submission safety: NOT APPROVED — DO NOT SUBMIT" in html
        assert "This session wrote no TIFF." not in html
