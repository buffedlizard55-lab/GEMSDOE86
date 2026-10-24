"""The legacy SPT release claim may never become a positive site decision."""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import shutil
import sys
import types
import zipfile

import pytest

from scripts import audit_legacy_spt, build_site
from scripts.check_site import check

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path, monkeypatch):
    for rel in (
        audit_legacy_spt.REL,
        str(Path(audit_legacy_spt.REL).with_suffix(".json")),
        str(Path(audit_legacy_spt.REL).with_suffix(".zip")),
        "docs/evidence/spt-run-card.json", "docs/evidence/spt-legacy-audit.json",
        "docs/evidence/protocol-preflight.json",
        "research/registry_witness_pin.json", "research/upstream/spt-original-run-card.json",
        "data/bridge/sample_submission.tif", "data/bridge/existing_faults.tif",
    ):
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    monkeypatch.setattr(audit_legacy_spt, "verify_shared_pins", lambda _: {"pinned": True})
    return tmp_path


def test_actual_pr60_file_is_format_valid_but_registry_duplicate():
    r = audit_legacy_spt.check_snapshot(ROOT)
    assert r["sha256"] == audit_legacy_spt.FILE_SHA256
    assert r["validator"]["all_checks_passed"] is True
    assert r["validator"]["nan_inside_footprint"] == 0
    assert r["validator"]["values_in_0_1"] is True
    assert r["validator"]["crs_shape_transform_match"] is True
    assert r["validator"]["shared_writer_used"] is False
    assert r["registry"]["final_dots_forward_overlap_3px"] == 1.0
    assert r["registry"]["surface_preplacement"] is None
    assert r["holdout_dti"]["value"] is r["holdout_dti"]["ci95"] is None
    assert r["submission_ready"] is r["safe_to_submit"] is False
    card = json.loads((ROOT / "docs/evidence/spt-run-card.json").read_text())
    assert card["original_card_sha256"] == audit_legacy_spt.ARCHIVED_CARD_SHA256
    assert card["historical_claims_not_promotion_evidence"]["class"] == "IN_SAMPLE_CATALOGUE_PROXY"
    assert len(card["note"]) <= 140
    assert "DO NOT SUBMIT" in (ROOT / "docs/submit.html").read_text()
    assert "READY TO DOWNLOAD" not in (ROOT / "docs/submit.html").read_text()
    assert "raw.githubusercontent.com/" not in (ROOT / "docs/submit.html").read_text()
    assert build_site.render()["docs/submit.html"] == (ROOT / "docs/submit.html").read_text()


@pytest.mark.parametrize("file,change", [
    ("docs/evidence/spt-run-card.json", {"submission_ready": True}),
    ("docs/evidence/spt-run-card.json", {"download_url": "https://example.org/wrong.tif"}),
    ("docs/evidence/spt-run-card.json", {"raster_sha256": "x" * 64}),
    ("docs/evidence/protocol-preflight.json", {"direct_support_uncovered_allowed_pixels": 1}),
    ("docs/evidence/protocol-preflight.json", {"overlap_limit": 1.0}),
])
def test_stale_cards_and_proof_fail_closed(tmp_path, monkeypatch, file, change):
    root = fixture(tmp_path, monkeypatch)
    p = root / file
    record = json.loads(p.read_text()); record.update(change); p.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        audit_legacy_spt.check_snapshot(root)


def test_modified_tiff_and_zip_fail_closed(tmp_path, monkeypatch):
    root = fixture(tmp_path, monkeypatch)
    p = root / audit_legacy_spt.REL
    p.write_bytes(p.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit_legacy_spt.inspect(root)
    shutil.copyfile(ROOT / audit_legacy_spt.REL, p)
    z = p.with_suffix(".zip")
    with zipfile.ZipFile(z, "w") as archive:
        archive.writestr(p.name, b"not the TIFF")
    with pytest.raises(ValueError, match="zip_bytes_equal_tif"):
        audit_legacy_spt.inspect(root)


def test_offline_review_cannot_manufacture_a_witness_score(tmp_path, monkeypatch):
    root = fixture(tmp_path, monkeypatch)
    r = audit_legacy_spt.inspect(root)
    assert r["registry"]["spearman_full_footprint"] is None
    with pytest.raises((OSError, ValueError)):
        audit_legacy_spt.inspect(root, with_witness=True)
    stored = json.loads((root / audit_legacy_spt.REPORT).read_text())
    stored["registry"]["spearman_full_footprint"] = 0.35
    (root / audit_legacy_spt.REPORT).write_text(json.dumps(stored))
    with pytest.raises(ValueError, match="pinned measurement"):
        audit_legacy_spt.check_snapshot(root)
    stored["registry"]["spearman_full_footprint"] = audit_legacy_spt.FILE_RHO
    stored["safe_to_submit"] = True
    (root / audit_legacy_spt.REPORT).write_text(json.dumps(stored))
    with pytest.raises(ValueError, match="stale or has optimistic"):
        audit_legacy_spt.check_snapshot(root)


def test_legacy_builder_stops_even_if_future_preflight_allows_import(monkeypatch):
    fake = types.ModuleType("scripts.protocol_preflight")
    fake.require_feasible = lambda: None
    monkeypatch.setitem(sys.modules, "scripts.protocol_preflight", fake)
    with pytest.raises(RuntimeError, match="RETIRED_SPT_BUILDER"):
        runpy.run_path(str(ROOT / "scripts/build_spt.py"))


def test_publication_check_rejects_original_unsafe_upload_page(tmp_path):
    (tmp_path / "docs/evidence").mkdir(parents=True)
    (tmp_path / "index.html").write_text('<a href="docs/index.html">site</a>')
    (tmp_path / "docs/index.html").write_text('<h1>negative</h1>')
    (tmp_path / "docs/submit.html").write_text('<h1>READY TO DOWNLOAD</h1><p>DO NOT SUBMIT</p>')
    (tmp_path / "docs/evidence/spt-run-card.json").write_text(json.dumps({
        "verdict": "negative", "submission_ready": False, "approved_for_weekly_slot": False,
        "safe_to_submit": False, "download_url": None}))
    assert any("Legacy SPT page" in e for e in check(tmp_path))


def test_negative_session_run_card_never_treats_legacy_bytes_as_a_new_candidate():
    current = json.loads((ROOT / "docs/evidence/session-20261024-spt-correction-run-card.json").read_text())
    legacy = json.loads((ROOT / audit_legacy_spt.REPORT).read_text())
    assert current["verdict"] == "negative" and current["submission_ready"] is False
    assert current["new_candidate_generated"] is False and current["experiments_run"] == 0
    assert current["submission_slots_used"] == 0
    assert current["raster_sha256"] is current["submission_name"] is None
    assert current["validator_output"]["new_raster_status"] == "NOT_RUN_NO_NEW_RASTER"
    assert current["validator_output"]["legacy_spt_sha256"] == legacy["sha256"]
    assert current["correlation_overlap_vs_registry"]["legacy_spt_final_dot_forward_overlap_3px"] == legacy["registry"]["final_dots_forward_overlap_3px"] == 1.0
    assert current["correlation_overlap_vs_registry"]["legacy_spt_final_dot_spearman_full_footprint"] == legacy["registry"]["spearman_full_footprint"]
    assert current["holdout_dti"]["value"] is current["holdout_dti"]["ci95"] is None
    assert len(current["note"]) <= 140


def test_current_untried_register_retires_spt():
    plan = json.loads((ROOT / "registry/hypotheses_20261024.json").read_text())
    assert len(plan["hypotheses"]) == 3
    assert [h["rank"] for h in plan["hypotheses"]] == [1, 2, 3]
    assert "SPT" not in " ".join(h["id"] for h in plan["hypotheses"])
    assert plan["retired_from_previous_register"]["id"] == "H86C-SPT"
    for h in plan["hypotheses"]:
        assert all(h[k] for k in ("layers", "signature", "why_unmapped", "difference_from_repo", "non_fault_mimic", "implementation_cost"))
        assert h["holdout_dti"] is None and h["ci95"] is None
    assert plan["hypotheses"][-1]["data_readiness"].startswith("NOT_VIABLE_YET")
