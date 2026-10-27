"""Read-only evidence, identity, and stop regressions; never run a model."""
from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
import csv
import hashlib
import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from scripts import focus9, score_identity
from scripts.audit_h33_identity import audit as audit_h33, compare_arrays
from scripts.audit_release import strict_json

ROOT = Path(__file__).resolve().parents[1]


def _claim(name, score, site="GEMSDOE24"):
    return {"site": site, "submission": name, "score": score,
            "evidence_class": "OWNER-REPORTED", "source_url": "https://example.invalid/"}


def test_exact_same_site_score_identity_never_falls_back_to_hash_token():
    rows = [_claim("alpha-abcdef1234-nan", "0.25", "GEMSDOE28"),
            _claim("different-abcdef1234-zeros", "0.90", "GEMSDOE32")]
    assert score_identity.submission_stem_matches("GEMSDOE28", rows[0]["submission"],
                                                  "gems28-alpha-abcdef1234-nan.tif")
    assert score_identity.owner_score_for_path(
        "data/scored_fleet/GEMSDOE28__gems28-alpha-abcdef1234-nan.tif", rows) == 0.25
    assert score_identity.owner_score_for_path("data/scored/gems28-alpha-abcdef1234-nan.tif", rows) == 0.25
    # Shared token, changed fill suffix, different site and local downloads cannot establish identity.
    for path in ("data/scored/gems28-unrelated-abcdef1234-nan.tif",
                 "data/scored/gems28-alpha-abcdef1234-zeros.tif",
                 "data/scored_fleet/GEMSDOE32__gems28-alpha-abcdef1234-nan.tif",
                 "docs/downloads/gems28-alpha-abcdef1234-nan.tif",
                 "data/scored/alpha-abcdef1234-nan.tif"):
        assert score_identity.owner_score_for_path(path, rows) is None
    assert not score_identity.submission_stem_matches("GEMSDOE28", rows[0]["submission"],
                                                       "../gems28-alpha-abcdef1234-nan.tif")
    assert score_identity.owner_score_for_path(None, rows) is None


def test_score_identity_rejects_conflicts_and_invalid_values():
    one = _claim("alpha-nan", "0.2500")
    same = _claim("alpha-nan", "0.25")
    match = lambda records: score_identity.match_owner_score("GEMSDOE24", "gems24-alpha-nan.tif", records)
    assert match([one, same]) == one
    assert match([one, _claim("alpha-nan", "0.26")]) is None
    assert match([one, _claim("alpha-nan", "NaN")]) is None
    assert match([_claim("alpha-nan", "1.1")]) is None
    # Two distinct ledger stems match the same prefixed filename: fail closed.
    assert match([one, _claim("gems24-alpha-nan", "0.25")]) is None
    assert match([{"site": None, "score": "0.25", "submission": "alpha-nan"}]) is None
    assert score_identity.match_owner_score(None, "gems24-alpha-nan.tif", [one]) is None
    for filename in ("scripts/analyze_h86r_selector.py", "scripts/run_h86r_sfg.py"):
        assert "owner_score_for_path(rel, score_records)" in (ROOT / filename).read_text()


def test_focus9_ties_show_all_and_conflicts_or_bad_scores_fail_closed():
    rows = [_claim("one-nan", "0.24"), _claim("two-nan", "0.2400"),
            _claim("two-nan", "0.24"), _claim("lower-nan", "0.1")]
    winners = focus9.best_claims(rows)
    assert {r["submission"] for r in winners["GEMSDOE24"]} == {"one-nan", "two-nan"}
    assert all(not winners[site] for site in focus9.SITES if site != "GEMSDOE24")
    with pytest.raises(ValueError, match="conflicting"):
        focus9.best_claims(rows + [_claim("one-nan", "0.25")])
    for bad in ("NaN", "Infinity", "-0.1", "1.1", "not-a-number"):
        with pytest.raises(ValueError):
            focus9.best_claims([_claim("one-nan", bad)])
    invalid = _claim("one-nan", "0.2")
    invalid["evidence_class"] = "ORGANIZER-CONFIRMED"
    with pytest.raises(ValueError, match="non-owner"):
        focus9.best_claims([invalid])


def test_canonical_ledger_does_not_merge_different_names_with_the_same_token():
    from scripts import build_ledger
    rows = build_ledger.build_rows()
    claims = {(r["site"], r["name"], r["score"]) for r in rows}
    # These genuinely different names and different claims were previously
    # collapsed solely because their filename tokens matched.
    assert ("GEMSDOE10", "H25-ctx-ridge-20260927T232947704150Z-6452ae1d00", "0.1280") in claims
    assert ("GEMSDOE10", "h28-dotted-ridge-20260928T020256236880Z-6452ae1d00", "0.1839") in claims
    assert ("GEMSDOE40", "h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1", "0.0355") in claims
    assert ("GEMSDOE40", "h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard", "0.0397") in claims
    original = _claim("same-file-nan", "0.20")
    assert len(build_ledger.group_prior_rows([original, _claim("same-file-nan", "0.2000")])) == 1
    with pytest.raises(ValueError, match="Conflicting"):
        build_ledger.group_prior_rows([original, _claim("same-file-nan", "0.21")])


def test_new_owner_claims_are_preserved_as_claims_not_receipts():
    ledger = focus9.read_ledger(ROOT / "registry/prior_scores.csv")
    expected = {
        ("GEMSDOE27", "gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite", "0.2250"),
        ("GEMSDOE28", "gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite", "0.0206"),
        ("GEMSDOE33", "gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros", "0.0963"),
        ("GEMSDOE36", "gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros", "0.1647"),
        ("GEMSDOE91", "gems91-s22-omtj-e1-20261026-a99b8923f0-zeros", "0.0298"),
    }
    matching = [row for row in ledger if (row["site"], row["submission"], row["score"]) in expected]
    assert len(matching) == len(expected)
    assert all(row["evidence_class"].startswith("OWNER-REPORTED") for row in matching)


def test_all_nine_historical_winners_are_byte_bound_but_not_new_submissions():
    actual = focus9.rows(ROOT)
    assert len(actual) == 9 and {x["site"] for x in actual} == set(focus9.SITES)
    expected = {"GEMSDOE24": "0.2477", "GEMSDOE25": "0.2600", "GEMSDOE27": "0.2449",
                "GEMSDOE28": "0.2710", "GEMSDOE30": "0.2600", "GEMSDOE31": "0.2708",
                "GEMSDOE32": "0.2778", "GEMSDOE33": "0.2632", "GEMSDOE36": "0.2750"}
    assert {x["site"]: x["claim"]["score"] for x in actual} == expected
    for row in actual:
        assert row["claim"]["evidence_class"].startswith("OWNER-REPORTED")
        assert row["witness"]["git_object_matches"] and row["witness"]["archived_sha256_matches"]
        assert row["url"].startswith("https://github.com/buffedlizard55-lab/")
        assert len(row["witness"]["sha256"]) == 64
        assert 0 <= row["overlap_3px_vs_h33"] <= 1
    receipt = strict_json(ROOT / "docs/evidence/focus9-champions-20261027.json")
    assert receipt["organizer_receipts_obtained"] == receipt["new_rasters_generated"] == receipt["submission_slots_used"] == 0
    published = strict_json(ROOT / "docs/data/focus9.json")
    assert published["rows"] == actual


def test_byte_auditor_verifies_all_ties_and_stops_on_corrupt_bytes(tmp_path, monkeypatch):
    from scripts import audit_focus9_champions as auditor
    monkeypatch.setattr(focus9, "SITES", ("GEMSDOE24",))
    monkeypatch.setattr(auditor, "SITES", ("GEMSDOE24",))
    (tmp_path / "registry").mkdir()
    (tmp_path / "docs/evidence").mkdir(parents=True)
    claims = [_claim("tie-one-nan", "0.25"), _claim("tie-two-zeros", "0.2500")]
    ledger_path = tmp_path / "registry/prior_scores.csv"
    with ledger_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(claims[0]))
        writer.writeheader()
        writer.writerows(claims)
    payloads = {"tie-one-nan": b"first historical raster", "tie-two-zeros": b"second historical raster"}
    archived, blobs, by_sha = [], [], {}
    for name, payload in payloads.items():
        filename = f"gems24-{name}.tif"
        blob = auditor.git_blob_sha1(payload)
        by_sha[blob] = payload
        archived.append({"file": f"GEMSDOE24__{filename}", "sha256": hashlib.sha256(payload).hexdigest()})
        blobs.append({"path": "docs/downloads/" + filename, "git_blob_sha1": blob, "git_blob_bytes": len(payload)})
    (tmp_path / "docs/evidence/focus9-forensics-20261026-rev2.json").write_text(json.dumps(
        {"evidence_class": "REGISTRY-MEASUREMENT", "measured_utc": "2026-10-26T00:00:00Z", "rasters": archived}))
    (tmp_path / "docs/evidence/fleet-feed.json").write_text(json.dumps({"projects": [{
        "repository": "buffedlizard55-lab/GEMSDOE24", "status": "SNAPSHOT_OK",
        "commit_sha": "a" * 40, "tif_git_objects": blobs}]}))
    monkeypatch.setattr(auditor, "write_blob", lambda repo, blob, out: out.write(by_sha[blob]))
    receipt = auditor.measure(tmp_path)
    assert {row["submission"] for row in receipt["winners"]} == set(payloads)
    assert all(row["git_object_matches"] and row["archived_sha256_matches"] for row in receipt["winners"])
    monkeypatch.setattr(auditor, "write_blob", lambda repo, blob, out: out.write(b"wrong bytes"))
    with pytest.raises(ValueError, match="Git object, size or archived SHA-256 mismatch"):
        auditor.measure(tmp_path)


@pytest.mark.parametrize("field,value", [
    ("sha256", "0" * 64), ("sha256", None), ("source_commit", "not-a-commit"),
    ("git_blob_sha1", None), ("git_object_matches", False), ("archived_sha256_matches", False),
    ("source_repository", "someone-else/GEMSDOE24"), ("source_path", "../unrelated.tif"),
    ("forensic_file", "GEMSDOE24__different.tif"), ("bytes", 0),
    ("evidence_class", "ORGANIZER-CONFIRMED"),
])
def test_missing_or_altered_byte_evidence_never_produces_a_verified_link(field, value):
    rows = focus9.rows(ROOT)
    row = rows[0]
    evidence = strict_json(ROOT / "docs/evidence/focus9-champions-20261027.json")
    forensic = strict_json(ROOT / "docs/evidence/focus9-forensics-20261026-rev2.json")
    changed = deepcopy(evidence)
    changed["winners"][0][field] = value
    assert focus9.validated_witness(row["site"], row["claim"], changed, forensic) is None
    changed = deepcopy(evidence)
    changed["winners"].append(deepcopy(changed["winners"][0]))
    assert focus9.validated_witness(row["site"], row["claim"], changed, forensic) is None


def test_h33_comparison_distinguishes_footprint_identity_and_nan_encoding():
    cat = np.array([[-1, -1, -1], [0, 1, 0], [0, 0, 0]])
    parent = np.array([[np.nan, np.nan, np.nan], [0, 0, 0], [1, 0, 0]], dtype=float)
    child = np.zeros((3, 3), dtype=float)
    result = compare_arrays(parent, child, cat)
    assert result["deleted_pixels"] == 1 and result["added_pixels"] == 0
    assert result["deleted_in_one_to_two_pixel_collar"] == 1
    assert result["in_footprint_differences_after_deletion"] == 0
    assert result["parent_outside_nan"] == result["child_outside_zero"] == 3
    with pytest.raises(ValueError):
        compare_arrays(parent, child[:, :2], cat)
    invalid = child.copy()
    invalid[1, 0] = np.nan
    with pytest.raises(ValueError):
        compare_arrays(parent, invalid, cat)


def test_fresh_h33_audit_matches_saved_facts_not_a_score():
    saved = strict_json(ROOT / "docs/evidence/h33-identity-20261027.json")
    now = audit_h33()
    assert now["inputs_sha256"] == saved["inputs_sha256"]
    assert now["comparison"] == saved["comparison"]
    assert now["comparison"]["deleted_pixels"] == 2545
    assert now["comparison"]["in_footprint_differences_after_deletion"] == 0
    assert now["comparison"]["parent_outside_nan"] == now["comparison"]["child_outside_zero"] == 7111787
    assert now["model_experiments_run"] == now["submission_slots_used"] == 0


def test_featured_candidate_and_run_card_are_negative_not_authorization():
    from scripts.build_site import current_audit_candidate, focus9_summary
    report = strict_json(ROOT / "docs/evidence/release-readiness.json")
    panel = current_audit_candidate(report)
    assert "H86R-SFG TIFF — audit only" in panel and "DO NOT SUBMIT" in panel
    assert "Estimated leaderboard score: unavailable" in panel
    modified = deepcopy(report)
    target = next(a for a in modified["artifacts"] if a.get("source_card") == "docs/evidence/h86r-sfg-run-card.json")
    target["safe_to_submit"] = True
    with pytest.raises(ValueError):
        current_audit_candidate(modified)
    table = focus9_summary(focus9.rows(ROOT))
    assert table.count("Historical TIFF — audit only") == 9
    assert "0.2710" in table and "not a complete registry scan" in table
    card = strict_json(ROOT / "docs/evidence/session-20261027-b934a117-run-card.json")
    assert card["verdict"] == "negative" and card["safe_to_submit"] is False
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert card["correlation_overlap_vs_registry"]["candidate_final_dot_overlap_3px"] is None
    assert card["experiments_run"] == card["submission_slots_used"] == 0


def test_primary_pages_have_unique_ids_and_copy_buttons_target_one_element():
    class Ids(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = []
            self.targets = []

        def handle_starttag(self, tag, attributes):
            attrs = dict(attributes)
            if attrs.get("id"):
                self.ids.append(attrs["id"])
            if attrs.get("data-copy-target"):
                self.targets.append(attrs["data-copy-target"])

    for page in ("docs/index.html", "docs/executive-summary.html"):
        parsed = Ids()
        parsed.feed((ROOT / page).read_text())
        assert len(parsed.ids) == len(set(parsed.ids))
        assert all(parsed.ids.count(target) == 1 for target in parsed.targets)
        assert {"h86i-sacd-name", "h86i-rksc-name"} <= set(parsed.ids)
        if page == "docs/index.html":
            # Preserve the established archive anchor while giving the newer panel its own ID.
            assert {"h86l-fmc", "h86l-fmc-answer"} <= set(parsed.ids)


@pytest.mark.parametrize("module,entry,args", [
    ("run_h86r_sfg", "main", ()), ("run_h86j_lsi", "main", (["all"],)),
    ("run_h86j_mpc", "main", (["all"],)), ("run_h86k_psc", "main", ()),
    ("run_h86l_vfgr", "main", ()), ("run_h86m_bmr", "main", ()),
    ("run_h86m_cnt", "main", ()), ("run_h86n_eql", "main", ()),
    ("run_h86n_gsst", "main", ()), ("generate_gdsc_unique", "main", ()),
    ("generate_h86m_damagering", "main", ()), ("build_h86e_final", "main", ()),
    ("generate_unique_geothermal_submission", "build_prediction", ()),
])
def test_reviewed_historical_entrypoints_stop_before_candidate_work(module, entry, args, monkeypatch):
    from scripts import protocol_preflight
    def blocked():
        raise RuntimeError("STOP_LITERAL_OVERLAP_UNSATISFIABLE")
    monkeypatch.setattr(protocol_preflight, "require_feasible", blocked)
    script = importlib.import_module("scripts." + module)
    with pytest.raises(RuntimeError, match="STOP_LITERAL"):
        getattr(script, entry)(*args)


def test_historical_import_time_builder_stops_before_io(monkeypatch):
    from scripts import protocol_preflight
    def blocked():
        raise RuntimeError("STOP_LITERAL_OVERLAP_UNSATISFIABLE")
    monkeypatch.setattr(protocol_preflight, "require_feasible", blocked)
    sys.modules.pop("scripts.run_h86m_lt", None)
    with pytest.raises(RuntimeError, match="STOP_LITERAL"):
        importlib.import_module("scripts.run_h86m_lt")
