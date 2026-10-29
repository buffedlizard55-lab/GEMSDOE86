"""Focus-9 rendering must bind dated owner claims to measured files and scope."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_site import focus9_current_status_banner, focus9_summary  # noqa: E402


def test_focus9_uses_latest_owner_claims_and_scoped_pairwise_measurements():
    html = focus9_summary()
    assert "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros" in html
    assert "0.2778</strong> OWNER-REPORTED" in html
    assert "0.2750</strong> OWNER-REPORTED" in html
    assert "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan" in html
    assert "0.2710</strong> OWNER-REPORTED" in html
    assert "0.2708</strong> OWNER-REPORTED" in html
    assert "0.2449</strong> OWNER-REPORTED" in html
    assert "72 directed pairwise 3-px overlaps" in html
    assert "86.7%" in html and "100.0%" in html
    assert "not a complete cross-repository registry scan" in html
    assert "GEMSDOE27 H31" in html or "gems27-h31-drcg-wl-celf28" in html
    assert "99.17%" in html
    assert "MSDB1-edge44090" in html
    expected_audited_files = {
        "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
        "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
        "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
        "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
        "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
        "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
    }
    for site, filename in expected_audited_files.items():
        row_start = html.index(f'<tr><th scope="row"><a href="https://buffedlizard55-lab.github.io/{site}/">')
        row_end = html.index("</tr>", row_start)
        assert filename in html[row_start:row_end]


def test_scores_download_status_and_h33_causality_are_labeled():

    html = focus9_summary()
    assert "0 ORGANIZER-CONFIRMED receipts" in html
    assert "DOWNLOAD FOR AUDIT ONLY" in html
    assert "SUBMIT: NO" in html
    assert "single-band GeoTIFF" in html
    assert "values in [0,1]" in html
    assert "no NaNs in the footprint" in html
    assert "not proof of causation" in html
    assert "not a controlled causal test" in html
    assert "separate H32d run (0.2591" in html
    assert "no upload authorized" in html


def test_current_status_banner_fails_closed_and_names_scope():
    html = focus9_current_status_banner(include_h33_explanation=True)
    assert "FOCUS-9 EXECUTIVE SUMMARY · DO NOT SUBMIT" in html
    assert "Descriptive association, not a causal explanation" in html
    assert "0.2778 OWNER-REPORTED" in html
    assert "No Focus-9 score is ORGANIZER-CONFIRMED" in html
    assert "5,106,385/5,106,385 allowed pixels" in html
    assert "1.0 &gt; 0.70" in html
    assert "75/730" in html
    assert "probability values were not audited" in html
    assert "655 entries and only 1 measured raster" in html
    assert "72 directed 3-px measurements" in html
    assert "no new Focus-9 candidate; no upload" in html
    assert "G86-BGC" in html
    assert "HOLDOUT-DTI" in html
    assert "22,641 withheld positives" in html
    assert "67 dot-overlap firings" in html
    assert "not a Focus-9 score or this review's experiment" in html
    assert "G86-BGC run card" in html
    assert "nine-site-audit-20261029.json" in html
    assert "workspace-inputs-20261029.json" in html
    assert "training TIFF, prepared bands/labels/footprint" in html


def test_current_banner_requires_complete_fresh_20261029_overlap_audit(tmp_path, monkeypatch):
    import json
    import shutil
    import pytest
    import scripts.build_site as builder

    required = (
        "docs/evidence/protocol-preflight.json",
        "docs/evidence/registry-input-grid-review-20261028.json",
        "docs/evidence/release-readiness.json",
        "docs/evidence/fleet-feed.json",
        "docs/evidence/nine-site-audit-20261029.json",
        "docs/evidence/session-5ca0743e-inputs-20261029.json",
        "docs/evidence/workspace-inputs-20261029.json",
        "evidence/gems86-bgc-conduit-24365d-20261028T164808Z-85d93518-zeros-run-card.json",
        "registry/prior_scores.csv",
    )
    for rel in required:
        target=tmp_path / rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT / rel,target)
    monkeypatch.setattr(builder,"ROOT",tmp_path)
    audit_path=tmp_path / "docs/evidence/nine-site-audit-20261029.json"
    audit=json.loads(audit_path.read_text())
    audit["pairwise_overlap"].pop(next(iter(audit["pairwise_overlap"])))
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError,match="Nine-site overlap audit is incomplete"):
        builder.focus9_current_status_banner()


def test_generated_site_promotes_current_focus9_status_not_stale_fleet_claims():
    for rel in ("docs/index.html", "docs/executive-summary.html"):
        html = (ROOT / rel).read_text()
        assert 'id="focus9-current-status"' in html
        assert "FOCUS-9 EXECUTIVE SUMMARY · DO NOT SUBMIT" in html
        assert "All 12 Scored Runs Verified" not in html
        assert "Best submission across Focus-9 and all 92" not in html
        assert "r = +0.994" not in html
    executive = (ROOT / "docs/executive-summary.html").read_text()
    assert 'id="focus9-summary"' in executive
    assert executive.index('id="focus9-current-status"') < executive.index('id="focus9-summary"')


def test_generated_executive_summary_links_current_hypotheses():
    html = (ROOT / "docs/executive-summary.html").read_text()
    assert "focus9_novel_hypotheses_20261028.json" in html
    assert "three unrun proposals" in html


def test_home_links_the_current_review_and_hypothesis_register():
    html = (ROOT / "docs/index.html").read_text()
    assert "focus9_novel_hypotheses_20261028.json" in html
    assert "SESSION_20261029_ARENA_CAD53211_REVIEW.md" in html
    assert "review_20261029_arena_cad53211.json" in html
    assert "nine-site-audit-20261029.json" in html
    assert "workspace-inputs-20261029.json" in html
    assert "SESSION_20261029_5CA0743E_REVIEW.md" in html


def _isolated_inputs(tmp_path, monkeypatch):
    import csv
    import shutil
    import scripts.build_site as builder

    (tmp_path / "registry").mkdir()
    (tmp_path / "docs/evidence").mkdir(parents=True)
    (tmp_path / "evidence").mkdir(parents=True)
    rels = (
        "registry/prior_scores.csv",
        "docs/evidence/focus9-and-siblings-forensics-20261027.json",
        "docs/evidence/nine-site-audit-20261027.json",
        "docs/evidence/focus9-immutable-files-20261029.json",
        "docs/evidence/workspace-inputs-20261029.json",
        "docs/evidence/fleet-feed.json",
        "docs/evidence/protocol-preflight.json",
        "docs/evidence/registry-input-grid-review-20261028.json",
        "evidence/gems86-bgc-conduit-24365d-20261028T164808Z-85d93518-zeros-run-card.json",
    )
    for rel in rels:
        shutil.copyfile(ROOT / rel, tmp_path / rel)
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    score_path = tmp_path / "registry/prior_scores.csv"
    with score_path.open() as stream:
        rows = list(csv.DictReader(stream))
    snapshot_path = tmp_path / "docs/evidence/focus9-and-siblings-forensics-20261027.json"
    audit_path = tmp_path / "docs/evidence/nine-site-audit-20261027.json"
    fleet_path = tmp_path / "docs/evidence/fleet-feed.json"
    return builder, score_path, rows, snapshot_path, audit_path, fleet_path


def test_changed_score_claim_cannot_inherit_old_binary_measurement(tmp_path, monkeypatch):
    import csv
    import pytest

    builder, score_path, rows, _, _, _ = _isolated_inputs(tmp_path, monkeypatch)
    row = next(row for row in rows if row["site"] == "GEMSDOE24")
    row["score"] = "0.9999"
    with score_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="score snapshot disagrees with the score ledger"):
        builder.focus9_summary()


def test_removed_owner_file_is_flagged_but_historical_link_stays_commit_pinned(tmp_path, monkeypatch):
    import json

    builder, _, _, _, _, fleet_path = _isolated_inputs(tmp_path, monkeypatch)
    feed = json.loads(fleet_path.read_text())
    site = next(row for row in feed["projects"] if row["repository"].endswith("/GEMSDOE24"))
    site["tif_git_objects"] = [
        item for item in site["tif_git_objects"]
        if "gems24-h25-1-dotted-h19-5-d1-5" not in item["path"]
    ]
    fleet_path.write_text(json.dumps(feed))
    html = builder.focus9_summary()
    row = html.split('<tr><th scope="row"><a href="https://buffedlizard55-lab.github.io/GEMSDOE24/">', 1)[1].split('</tr>', 1)[0]
    assert 'CHANGED OR MISSING' in row
    assert '/raw/f4d5a5ef3f3cf6cbe5a24ee0b29c6d592910d308/' in row
    assert 'SUBMIT: NO' in row


def test_incomplete_nine_site_pairwise_audit_fails_closed(tmp_path, monkeypatch):
    import json
    import pytest

    builder, _, _, _, audit_path, _ = _isolated_inputs(tmp_path, monkeypatch)
    audit = json.loads(audit_path.read_text())
    audit["pairwise_overlap"].pop(next(iter(audit["pairwise_overlap"])))
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="Nine-site overlap audit is incomplete"):
        builder.focus9_summary()


def test_h87_page_does_not_present_missing_receipt_as_downloadable_tiff():
    import json
    import scripts.build_site as builder

    def load(path):
        return json.loads((ROOT / path).read_text())

    html = builder.nine_sites_page(
        load("docs/evidence/nine-site-audit-20261027.json"),
        load("docs/evidence/h87-fcb-candidate-receipt-20261027.json"),
        load("docs/evidence/h87-fcb-experiment1-20261027.json"),
        load("docs/evidence/h87-fcb-experiment2-20261027.json"),
    )
    assert "UNAVAILABLE: the historical TIFF is absent from this checkout" in html
    assert "receipt is not a TIFF download" in html
    assert "ABSENT from this checkout; not downloadable" in html
    assert "Download status: unavailable in this checkout; SUBMIT: NO" in html
    assert "Current literal full-support witness gate" in html
    assert "0 uncovered allowed pixels; 100.0% coverage" in html
    assert "Historical owner-reported result (not an estimate)" in html
    assert "Estimated score (owner-reported)" not in html


def test_summary_orders_claims_descending_not_by_site_number():
    import re
    html = focus9_summary()
    section = html[html.index('id="focus9-summary"'):]
    rows = re.findall(r'<tr><th scope="row"><a href="https://buffedlizard55-lab.github.io/(GEMSDOE\d+)/', section)
    assert rows[:9] == ["GEMSDOE32", "GEMSDOE36", "GEMSDOE28", "GEMSDOE31", "GEMSDOE33", "GEMSDOE25", "GEMSDOE30", "GEMSDOE24", "GEMSDOE27"]


def test_same_score_different_name_does_not_inherit_audit(tmp_path, monkeypatch):
    import csv
    import pytest
    builder, score_path, rows, _, _, _ = _isolated_inputs(tmp_path, monkeypatch)
    next(row for row in rows if row["site"] == "GEMSDOE24")["submission"] = "different-unverified-file"
    with score_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="not bound to the top score claim and name"):
        builder.focus9_summary()


def test_replaced_directed_pair_does_not_pass_by_count(tmp_path, monkeypatch):
    import json
    import pytest
    builder, _, _, _, audit_path, _ = _isolated_inputs(tmp_path, monkeypatch)
    audit = json.loads(audit_path.read_text())
    audit["pairwise_overlap"]["GEMSDOE24->GEMSDOE24"] = audit["pairwise_overlap"].pop("GEMSDOE24->GEMSDOE25")
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="overlap audit is incomplete"):
        builder.focus9_summary()


def test_maxima_must_match_the_actual_directed_pairs(tmp_path, monkeypatch):
    import json
    import pytest
    builder, _, _, _, audit_path, _ = _isolated_inputs(tmp_path, monkeypatch)
    audit = json.loads(audit_path.read_text())
    audit["max_overlap_by_site"]["GEMSDOE24"] = {"value": 0.3, "vs": "GEMSDOE25"}
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="maximum disagrees"):
        builder.focus9_summary()


def test_duplicate_site_records_are_rejected(tmp_path, monkeypatch):
    import json
    import pytest
    builder, _, _, _, audit_path, _ = _isolated_inputs(tmp_path, monkeypatch)
    audit = json.loads(audit_path.read_text())
    audit["files"].append(audit["files"][0])
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="exactly the nine requested sites"):
        builder.focus9_summary()


def test_historical_projection_table_does_not_claim_global_uniqueness_or_validated_ci():
    html = (ROOT / "docs/index.html").read_text()
    assert "not a validated 95% prediction interval" in html
    assert "Overlap vs measured discrete subset only" in html
    assert "LEAKAGE-CANARY &amp; FULL-UNIVERSE UNIQUENESS" not in html
    assert "Unique vs Focus-9 &amp; Discrete Fleet?" not in html
    assert "historical profile reports 15/15 checks, although the archived format gate below failed" in html


def test_nonfinite_dated_snapshot_score_is_rejected(tmp_path, monkeypatch):
    import json
    import pytest
    builder, _, _, snapshot_path, _, _ = _isolated_inputs(tmp_path, monkeypatch)
    snapshot = json.loads(snapshot_path.read_text())
    row = next(r for r in snapshot["focus9_executive_summary"] if r["site"] == "GEMSDOE24")
    row["highest_score_owner_reported"] = "NaN"
    snapshot_path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match="Invalid owner-reported score"):
        builder.focus9_summary()


def test_nonfinite_owner_claims_are_rejected(tmp_path, monkeypatch):
    import csv
    import pytest
    builder, score_path, rows, _, _, _ = _isolated_inputs(tmp_path, monkeypatch)
    next(row for row in rows if row["site"] == "GEMSDOE24")["score"] = "NaN"
    with score_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="Invalid owner-reported score"):
        builder.focus9_summary()
