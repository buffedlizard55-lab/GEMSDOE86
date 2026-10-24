"""The all-artifact audit must measure bytes and fail closed, not trust a badge."""
import json
from pathlib import Path
import shutil
import zipfile

import pytest

from scripts import audit_release as audit

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release_copy(tmp_path):
    for rel in ("data/bridge", "docs/downloads", "docs/evidence", "vendor", "registry"):
        shutil.copytree(ROOT / rel, tmp_path / rel, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "research").mkdir()
    for rel in ("research/template_pin.json", "research/registry_witness_pin.json", "evidence/run_card.json"):
        target = tmp_path / rel
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    return tmp_path


def rewrite(path, change):
    content = audit.strict_json(path)
    change(content)
    path.write_text(json.dumps(content))


def first_artifact(root):
    return audit.strict_json(root / "docs/evidence/download-inventory.json")["artifacts"][0]


def test_real_report_checks_every_published_raster_and_all_remain_negative():
    report = audit.build_report()
    assert report["audit_ok"]
    assert report["artifact_count"] == report["locally_valid_artifacts"] == 15  # 10 inherited + faulthalo + H86E + GAPRES + H86E-MMT + blind-geothermal
    assert report["all_final_artifacts_remeasured"]
    assert not report["safe_to_submit"]
    assert not report["selector_run"]
    fvmb = next(a["historical_holdout"] for a in report["artifacts"] if "fvmb" in a["file"])
    assert "cut-segment" in fvmb["design"]
    assert "paired_delta" not in fvmb  # malformed archived text must not become a numeric gain
    assert report["authenticated_remaining_quota"] is None
    for artifact in report["artifacts"]:
        assert artifact["validator"]["all_checks_passed"]
        assert artifact["registry_measurement"]["forward_overlap_3px"] == 1.0
        assert artifact["safe_to_download_for_audit"]
        assert not artifact["safe_to_submit"]
        assert artifact["note_chars"] == len(artifact["note"]) <= 140
    offcat = next(a for a in report["artifacts"] if "offcat" in a["file"])
    assert offcat["historical_holdout"]["value"] is None
    gfco = next(a for a in report["artifacts"] if "gfco" in a["file"])
    assert gfco["bytes"] == 145410  # catches the inherited stale 158,348 headline
    assert gfco["note_chars"] == 91  # catches the inherited stale 92 headline
    assert gfco["historical_holdout"]["paired_delta_ci95"][0] < 0


def test_empty_zip_member_is_not_a_download_pass(release_copy):
    entry = first_artifact(release_copy)
    tif = release_copy / entry["file"]
    with zipfile.ZipFile(tif.with_suffix(".zip"), "w") as bundle:
        bundle.writestr(tif.name, b"")
    report = audit.build_report(release_copy)
    assert not report["audit_ok"]
    artifact = report["artifacts"][0]
    assert not artifact["validator"]["checks"]["zip_payload_equals_tif"]
    assert not artifact["safe_to_download_for_audit"]
    assert not artifact["safe_to_submit"]


def test_note_length_and_receipt_counts_are_recomputed(release_copy):
    receipt = (release_copy / first_artifact(release_copy)["file"]).with_suffix(".json")
    rewrite(receipt, lambda doc: doc.update(note="x" * 141, note_chars=107))
    report = audit.build_report(release_copy)
    checks = report["artifacts"][0]["validator"]["checks"]
    assert not checks["note_1_to_140_chars"]
    assert not checks["receipt_note_count_matches"]
    assert not report["audit_ok"]


def test_optimistic_scientific_card_cannot_promote(release_copy):
    card = release_copy / "docs/evidence/h86b-gfco-run-card.json"
    rewrite(card, lambda doc: doc.update(verdict="promote", submission_ready=True))
    report = audit.build_report(release_copy)
    artifact = next(a for a in report["artifacts"] if "gfco" in a["file"])
    assert not artifact["validator"]["checks"]["scientific_card_is_negative"]
    assert not artifact["safe_to_submit"]
    assert not report["audit_ok"]


def test_missing_inventory_member_fails(release_copy):
    tif = release_copy / first_artifact(release_copy)["file"]
    tif.unlink()
    with pytest.raises(ValueError, match="missing published TIFF"):
        audit.build_report(release_copy)


def test_duplicate_inventory_paths_fail(release_copy):
    path = release_copy / "docs/evidence/download-inventory.json"
    rewrite(path, lambda doc: doc["artifacts"].append(doc["artifacts"][0]))
    with pytest.raises(ValueError, match="duplicate artifact"):
        audit.build_report(release_copy)


def test_stale_registry_hash_is_not_current_measurement(release_copy):
    path = release_copy / "docs/evidence/all-artifacts-registry.json"
    rewrite(path, lambda doc: doc["artifacts"][0].update(sha256="bad"))
    with pytest.raises(ValueError, match="Final-dot measurements drifted"):
        audit.build_report(release_copy)


def test_saturation_contradiction_never_certifies(release_copy):
    path = release_copy / "docs/evidence/protocol-preflight.json"
    rewrite(path, lambda doc: doc.update(covered_allowed_fraction=0.75))
    with pytest.raises(ValueError, match="Changed/missing protocol proof"):
        audit.build_report(release_copy)


def test_vendor_copy_drift_is_not_a_private_validator(release_copy):
    path = release_copy / "vendor/template66/gems57/validate.py"
    path.write_text(path.read_text() + "\n# drift\n")
    with pytest.raises(ValueError, match="Shared tool SHA drift"):
        audit.build_report(release_copy)


def test_json_nonfinite_duplicate_keys_and_path_escape_fail(tmp_path):
    for content in ('{"x": NaN}', '{"x": Infinity}', '{"x": 1, "x": 2}'):
        path = tmp_path / "invalid.json"
        path.write_text(content)
        with pytest.raises(ValueError):
            audit.strict_json(path)
    outside = tmp_path / "outside.txt"
    outside.write_text("test")
    root = tmp_path / "root"
    root.mkdir()
    for rel in ("../outside.txt", str(outside)):
        with pytest.raises(ValueError):
            audit.inside(root, rel)


def test_session_card_does_not_rebrand_old_hashes_or_metrics():
    report = audit.strict_json(ROOT / "docs/evidence/release-readiness.json")
    card = audit.session_card(report)
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["holdout_dti"]["value"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert not card["new_candidate_generated"]
    assert card["verdict"] == "negative"
    assert 0 < len(card["note"]) <= 140
    assert len(card["inherited_artifacts"]["files"]) == 15  # 10 inherited + faulthalo + H86E + GAPRES + H86E-MMT + blind-geothermal


def test_session_card_date_cannot_contradict_its_live_artifact_inventory():
    """A pinned card date plus a later-dated file must be explained, not silent.

    ``session_card()`` re-derives ``inherited_artifacts`` from the live release
    report on every audit run while ``date_utc`` stays pinned to 2026-10-23.
    Without explicit provenance that combination reads as an archived card being
    mutated -- the false irregularity raised against PR #80
    (IR-86-FAULTHALO-01). These fields make the drift self-describing so a
    later-dated artifact is provably expected provenance.
    """
    report = audit.strict_json(ROOT / "docs/evidence/release-readiness.json")
    card = audit.session_card(report)
    inventory = card["inherited_artifacts"]

    assert card["date_utc"] == "2026-10-23"
    assert inventory["inventory_is_live"] is True
    assert isinstance(card["date_utc_basis"], str) and card["date_utc_basis"].strip()
    assert isinstance(inventory["inventory_basis"], str) and inventory["inventory_basis"].strip()
    # The current-review card reuses session_card() but restates date_utc as the
    # measurement date, so it must also restate what that date means.
    registry = audit.strict_json(ROOT / "docs/evidence/all-artifacts-registry.json")
    review = audit.current_review_card(report, registry)
    assert review["date_utc"] != card["date_utc"] or review["registry_measured_utc"].startswith(card["date_utc"])
    assert review["date_utc_basis"] != card["date_utc_basis"]
    assert "remeasurement" in review["date_utc_basis"]
    # The live inventory must actually track the report it is derived from.
    assert inventory["checked"] == report["artifact_count"] == len(inventory["files"])
    assert [f["file"] for f in inventory["files"]] == [a["file"] for a in report["artifacts"]]
    # Self-description must not weaken the negative verdict or authorize anything.
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["new_candidate_generated"] is False
    assert inventory["submission_authorized"] is False


def test_h86b_imported_call_has_no_preflight_bypass(monkeypatch):
    from scripts import run_lane86b
    from scripts import protocol_preflight
    built = []
    monkeypatch.setattr(run_lane86b.F, "build_physical_planes", lambda: built.append(True))
    monkeypatch.setattr(protocol_preflight, "measure", lambda: {"universal_overlap_blocker": True})
    with pytest.raises(TypeError):
        run_lane86b.main(skip_literal_preflight=True)
    with pytest.raises(RuntimeError, match="STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
        run_lane86b.main()
    assert built == []


def test_direct_feature_builder_cannot_bypass_literal_stop(monkeypatch):
    from scripts import h86b_features
    from scripts import protocol_preflight
    built = []
    monkeypatch.setattr(h86b_features, "build_physical_planes", lambda: built.append(True))
    monkeypatch.setattr(protocol_preflight, "measure", lambda: {"universal_overlap_blocker": True})
    with pytest.raises(RuntimeError, match="STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
        h86b_features.main()
    assert built == []


def test_raw_name_and_note_lengths_include_padding(release_copy):
    receipt = (release_copy / first_artifact(release_copy)["file"]).with_suffix(".json")
    rewrite(receipt, lambda doc: doc.update(
        submission_name="x" + " " * 140, note="y" + " " * 140, note_chars=141))
    report = audit.build_report(release_copy)
    checks = report["artifacts"][0]["validator"]["checks"]
    assert not checks["name_1_to_140_chars"]
    assert not checks["note_1_to_140_chars"]
    assert not report["audit_ok"]


@pytest.mark.parametrize("extra", [
    "docs/downloads/nested/extra.TIFF",
    "docs/extra.TIF",
    "docs/downloads/extra.ZIP",
    "submission/extra.TIF",
    "submission/extra.ZIP",
])
def test_unregistered_public_files_cannot_hide_in_subdirectories_or_uppercase(release_copy, extra):
    path = release_copy / extra
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"unregistered")
    with pytest.raises(ValueError, match="Unregistered or missing published"):
        audit.build_report(release_copy)


def test_optimistic_unlinked_sidecar_card_fails_release_audit(release_copy):
    sidecar = release_copy / "docs/evidence/rogue-spt-run-card.json"
    sidecar.write_text('{"verdict": "promote-candidate", "submission_ready": true}\n', encoding="utf-8")
    report = audit.build_report(release_copy)
    assert not report["audit_ok"]
    assert not report["safe_to_submit"]


def test_receipt_symlink_cannot_escape_public_download_directory(release_copy):
    receipt = (release_copy / first_artifact(release_copy)["file"]).with_suffix(".json")
    outside = release_copy / "not-a-public-receipt.json"
    receipt.rename(outside)
    receipt.symlink_to(outside)
    with pytest.raises(ValueError, match="Missing or escaping input"):
        audit.build_report(release_copy)


def test_direct_protocol_measurement_checks_shared_pins_before_reading_data(monkeypatch):
    from scripts import protocol_preflight
    calls = []
    monkeypatch.setattr(audit, "verify_shared_pins", lambda _: {"modified-tool": False})
    monkeypatch.setattr(protocol_preflight.grid, "load_grid", lambda _: calls.append(True))
    with pytest.raises(ValueError, match="Shared tool SHA drift"):
        protocol_preflight.measure()
    assert calls == []


def test_missing_final_dot_measurements_fail_closed(release_copy):
    (release_copy / "docs/evidence/all-artifacts-registry.json").unlink()
    with pytest.raises(FileNotFoundError):
        audit.build_report(release_copy)


@pytest.mark.parametrize("name", ["run_h86_fvmb_pipeline", "prepare_h86_fvmb_data"])
def test_concurrent_fvmb_entrypoints_stop_before_cache_or_fitting(monkeypatch, name):
    import importlib
    from scripts import protocol_preflight
    module = importlib.import_module("scripts." + name)
    built = []
    monkeypatch.setattr(module, "build_static60_memmap", lambda *a, **k: built.append(True))
    monkeypatch.setattr(protocol_preflight, "measure", lambda: {"universal_overlap_blocker": True})
    with pytest.raises(RuntimeError, match="STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
        module.main()
    assert built == []


def test_tampered_quarantined_submission_bytes_or_zip_fail_release_audit(release_copy):
    shutil.copytree(ROOT / "submission", release_copy / "submission")
    assert audit.build_report(release_copy)["audit_ok"]
    spt_doc = audit.strict_json(release_copy / "docs/evidence/spt-full-support-witness-audit.json")
    cand_tif = release_copy / spt_doc["candidate_file"]
    cand_zip = cand_tif.with_suffix(".zip")
    with zipfile.ZipFile(cand_zip, "w") as bundle:
        bundle.writestr(cand_tif.name, b"substituted")
    with pytest.raises(ValueError, match="Quarantined submission/ ZIP payload mismatch"):
        audit.build_report(release_copy)
    cand_tif.write_bytes(b"substituted")
    with pytest.raises(ValueError, match="Quarantined submission/ TIFF SHA mismatch"):
        audit.build_report(release_copy)
