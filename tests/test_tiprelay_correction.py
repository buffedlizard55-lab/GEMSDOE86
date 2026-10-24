"""PR #63's format-valid TIPRELAY cannot be promoted over a literal registry stop."""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import shutil
import sys
import types
import zipfile

import pytest

from scripts import audit_legacy_tiprelay, build_site
from scripts.check_site import check

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path, monkeypatch):
    rel = audit_legacy_tiprelay.REL
    for source in (
        rel, str(Path(rel).with_suffix(".zip")), str(Path(rel).with_suffix(".json")),
        audit_legacy_tiprelay.REPORT,
        "docs/evidence/h86-tiprelay-run-card.json",
        "docs/evidence/protocol-preflight.json",
        "research/registry_witness_pin.json",
        "research/upstream/tiprelay-original-run-card.json",
        "research/upstream/tiprelay-original-download-card.json",
        "data/bridge/sample_submission.tif", "data/bridge/existing_faults.tif",
    ):
        dst = tmp_path / source
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, dst)
    monkeypatch.setattr(audit_legacy_tiprelay, "verify_shared_pins", lambda _: {"pinned": True})
    return tmp_path


def test_actual_pr63_file_is_format_valid_but_literal_registry_duplicate():
    record = audit_legacy_tiprelay.check_snapshot(ROOT)
    assert record["sha256"] == audit_legacy_tiprelay.SHA
    assert record["validator"]["all_checks_passed"] is True
    assert record["validator"]["nan_inside_footprint"] == 0
    assert record["validator"]["values_in_0_1"] is True
    assert record["validator"]["crs_shape_transform_match"] is True
    assert record["validator"]["positive_pixels"] == 37654
    assert record["registry"]["surface_preplacement"] is None
    assert record["registry"]["final_dots_forward_overlap_3px"] == 1.0
    assert record["registry"]["spearman_full_footprint"] == audit_legacy_tiprelay.FILE_RHO
    assert record["holdout_dti"]["value"] is record["holdout_dti"]["ci95"] is None
    assert record["verdict"] == "negative" and record["submission_ready"] is False
    card = json.loads((ROOT / "docs/evidence/h86-tiprelay-run-card.json").read_text())
    assert card["verdict"] == "negative" and card["submission_ready"] is False
    assert card["original_card_sha256"] == audit_legacy_tiprelay.RUN_ORIGINAL_SHA
    assert len(card["note"]) <= 140
    assert "UNVALIDATED-PROJECTION" == card["historical_claims_not_promotion_evidence"]["class"]
    for page in ("docs/index.html", "docs/executive-summary.html", "docs/submit.html"):
        html = (ROOT / page).read_text()
        assert "✅ VALIDATED" not in html
        assert "Download TIFF — submit this file" not in html
        assert "why this file is obviously submittable" not in html.lower()
    assert "TIPRELAY" in (ROOT / "docs/submit.html").read_text()
    assert "DO NOT SUBMIT" in (ROOT / "docs/submit.html").read_text()
    session = json.loads((ROOT / "docs/evidence/session-20261024-spt-correction-run-card.json").read_text())
    inherited = session["concurrent_inherited_tiprelay"]
    assert session["verdict"] == "negative" and session["submission_ready"] is False
    assert session["raster_sha256"] is session["submission_name"] is None
    assert inherited["sha256"] == record["sha256"]
    assert inherited["registry_forward_dot_overlap_3px"] == record["registry"]["final_dots_forward_overlap_3px"]
    assert inherited["registry_spearman_full_footprint"] == record["registry"]["spearman_full_footprint"]
    assert inherited["verdict"] == "negative" and inherited["submission_ready"] is False
    assert len(session["note"]) <= 140
    assert build_site.render()["docs/submit.html"] == (ROOT / "docs/submit.html").read_text()


@pytest.mark.parametrize("file,change", [
    ("docs/evidence/h86-tiprelay-run-card.json", {"submission_ready": True}),
    ("docs/evidence/h86-tiprelay-run-card.json", {"download_url": "https://example.org/unsafe.tif"}),
    ("docs/evidence/h86-tiprelay-run-card.json", {"raster_sha256": "0" * 64}),
    ("docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.json", {"status": "READY"}),
    ("docs/evidence/protocol-preflight.json", {"direct_support_uncovered_allowed_pixels": 1}),
    ("docs/evidence/protocol-preflight.json", {"overlap_limit": 1.0}),
])
def test_optimistic_cards_and_stale_proof_fail_closed(tmp_path, monkeypatch, file, change):
    root = fixture(tmp_path, monkeypatch)
    p = root / file
    doc = json.loads(p.read_text()); doc.update(change); p.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        audit_legacy_tiprelay.check_snapshot(root)


def test_modified_bytes_or_zip_payload_fail_closed(tmp_path, monkeypatch):
    root = fixture(tmp_path, monkeypatch)
    p = root / audit_legacy_tiprelay.REL
    p.write_bytes(p.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit_legacy_tiprelay.inspect(root)
    shutil.copyfile(ROOT / audit_legacy_tiprelay.REL, p)
    z = p.with_suffix(".zip")
    with zipfile.ZipFile(z, "w") as bundle:
        bundle.writestr(p.name, b"wrong bytes")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit_legacy_tiprelay.inspect(root)


def test_offline_audit_cannot_invent_a_new_rho_or_slot_approval(tmp_path, monkeypatch):
    root = fixture(tmp_path, monkeypatch)
    assert audit_legacy_tiprelay.inspect(root)["registry"]["spearman_full_footprint"] is None
    with pytest.raises((OSError, ValueError)):
        audit_legacy_tiprelay.inspect(root, with_witness=True)
    path = root / audit_legacy_tiprelay.REPORT
    record = json.loads(path.read_text())
    record["registry"]["spearman_full_footprint"] = 0.35
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="pinned measurement"):
        audit_legacy_tiprelay.check_snapshot(root)
    record["registry"]["spearman_full_footprint"] = audit_legacy_tiprelay.FILE_RHO
    record["submission_ready"] = True
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="stale, modified or optimistic"):
        audit_legacy_tiprelay.check_snapshot(root)


def test_retired_generator_stops_even_if_preflight_later_allows_import(monkeypatch):
    fake = types.ModuleType("scripts.protocol_preflight")
    fake.require_feasible = lambda: None
    monkeypatch.setitem(sys.modules, "scripts.protocol_preflight", fake)
    with pytest.raises(RuntimeError, match="RETIRED_TIPRELAY_BUILDER"):
        runpy.run_path(str(ROOT / "scripts/gen_tip_final.py"))


def test_only_exact_separately_audited_tiprelay_path_is_allowed(tmp_path, monkeypatch):
    from scripts import check_site
    dl = tmp_path / "docs/downloads"
    dl.mkdir(parents=True)
    (tmp_path / "index.html").write_text('<p>local site</p>')
    tip = tmp_path / audit_legacy_tiprelay.REL
    tip.write_bytes(b"test input; actual byte checks are covered above")
    tip.with_suffix(".zip").write_bytes(b"fake zip for path test")
    (dl / "surprise-tiprelay-copy.tif").write_bytes(b"new unregistered input")
    (dl / "surprise-tiprelay-copy.zip").write_bytes(b"new unregistered zip")
    monkeypatch.setattr(check_site, "load_inventory", lambda _: {})
    monkeypatch.setattr(audit_legacy_tiprelay, "check_snapshot", lambda _: {
        "verdict": "negative", "submission_ready": False})
    errors = check_site.check(tmp_path)
    assert any("surprise-tiprelay-copy.tif" in error for error in errors)
    assert any("surprise-tiprelay-copy.zip" in error for error in errors)
    assert not any(audit_legacy_tiprelay.NAME in error and "Unregistered" in error
                   for error in errors)


def test_site_rejects_green_tiprelay_claim_without_manual_review(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/index.html").write_text('<h1>✅ VALIDATED - submit this file</h1>')
    (tmp_path / "docs/submit.html").write_text('<h1>DO NOT SUBMIT</h1>')
    (tmp_path / "index.html").write_text('<a href="docs/index.html">site</a>')
    errors = check(tmp_path)
    assert any("unsafe TIPRELAY promotion" in error for error in errors)
