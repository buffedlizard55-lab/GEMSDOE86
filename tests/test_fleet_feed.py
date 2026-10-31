"""The feed verifies repository metadata, never authenticates a reported score."""
import json
from pathlib import Path

import pytest

from scripts.refresh_fleet import snapshot
from scripts.audit_release import strict_json, sha256

ROOT = Path(__file__).resolve().parents[1]


def fake_api(endpoint):
    if "/commits/" in endpoint:
        return {"sha": "test-commit", "commit": {"tree": {"sha": "test-tree"},
                "committer": {"date": "2026-10-23T00:00:00Z"}}}
    return {"truncated": False, "tree": [
        {"type": "blob", "path": "docs/downloads/candidate.tif", "sha": "test-blob", "size": 100},
        {"type": "blob", "path": "data/input.tif", "sha": "input-blob", "size": 200},
        {"type": "blob", "path": "README.md", "sha": "readme-blob", "size": 50},
        {"type": "tree", "path": "docs", "sha": "directory"},
    ]}


def test_snapshot_does_not_turn_claims_or_git_objects_into_verified_predictions():
    target = {"repository": "buffedlizard55-lab/GEMSDOE32", "site_url": "https://example.test/"}
    claims = [{"value": "0.2778", "evidence_class": "OWNER-REPORTED"}]
    result = snapshot(target, claims, api=fake_api)
    assert result["status"] == "SNAPSHOT_OK"
    assert result["current_tree_tif_count"] == 2
    assert result["published_download_tif_count"] == 1
    assert result["owner_reported_results"] == claims
    assert not result["organizer_score_verified"]
    assert not result["raster_bytes_verified"]
    assert "git_blob_sha1" in result["tif_git_objects"][0]
    assert "sha256" not in result["tif_git_objects"][0]


def test_failed_and_truncated_requests_stay_explicit():
    target = {"repository": "buffedlizard55-lab/GEMSDOE32", "site_url": "https://example.test/"}

    def failed(_):
        raise RuntimeError("FORBIDDEN_OR_RATE_LIMITED")

    result = snapshot(target, [], api=failed)
    assert result["status"] == "FORBIDDEN_OR_RATE_LIMITED"
    assert result["current_tree_tif_count"] is None

    def truncated(endpoint):
        result = fake_api(endpoint)
        if "tree" in result:
            result["truncated"] = True
        return result

    assert snapshot(target, [], api=truncated)["status"] == "INCOMPLETE_TRUNCATED_TREE"
    with pytest.raises(ValueError):
        snapshot({**target, "repository": "someone/else"}, [], api=fake_api)


def test_checked_in_feed_covers_named_targets_without_score_promotion():
    targets = strict_json(ROOT / "registry/site_targets.json")
    feed = strict_json(ROOT / "docs/evidence/fleet-feed-current.json")
    assert feed["projects_requested"] == len(targets["sites"]) == 92
    assert {p["repository"] for p in feed["projects"]} == {t["repository"] for t in targets["sites"]}
    assert feed["owner_ledger_sha256"] == sha256(ROOT / "registry/prior_scores.csv")
    assert feed["organizer_receipts_obtained"] == feed["submission_slots_used"] == 0
    assert all(not row["organizer_score_verified"] for row in feed["projects"])
    scores = [c for row in feed["projects"] for c in row["owner_reported_results"] if c["value"]]
    assert all((c["evidence_class"].startswith(("OWNER-REPORTED", "USER-REPORTED", "CROSS-REPOSITORY OWNER-REPORTED"))
                or c["evidence_class"].startswith("UNSUPPORTED AS GEMSDOE28 SCORE")) for c in scores)
    assert all(not p["organizer_score_verified"] for p in feed["projects"])


def test_provisional_hypotheses_do_not_invent_validation_or_data_obtainability():
    import re
    from src.gems86.io import BANDS
    plan = strict_json(ROOT / "registry/h86c_hypotheses.json")
    assert 3 <= len(plan["hypotheses"]) <= 5
    assert plan["experiments_run"] == 0
    for row in plan["hypotheses"]:
        assert row["holdout_dti"] is row["ci95"] is None
        assert row["status"].startswith("NOT_RUN")
        for field in ("layers", "signature", "why_unmapped", "difference_from_repo", "non_fault_mimic", "implementation_cost"):
            assert row[field]
        if row["external_data_required"]:
            assert "NOT_VIABLE" in row["data_readiness"]
            assert row["free_official_source_needed"]
            assert row["obtainability"]
        text_blob = " ".join([*row["layers"], row["signature"], row["why_unmapped"], row["difference_from_repo"]])
        assert "tc (Band 6) magnetic tilt zero-crossings" not in text_blob
        for key, band_str in re.findall(r"\b([a-z0-9_]+)\s*\(Band\s+(\d+)\b", text_blob):
            assert BANDS[int(band_str)] == key, f"Band mismatch in {row['id']}: Band {band_str} is {BANDS[int(band_str)]}, not {key}"

    plan86m = strict_json(ROOT / "registry/h86m_slcq_hypotheses.json")
    assert 3 <= len(plan86m["hypotheses"]) <= 5
    for row in plan86m["hypotheses"]:
        assert row.get("holdout_dti") is row.get("ci95") is None and "projected_score" not in row
        for key, band_str in re.findall(r"\b([a-z0-9_]+)\s*\(Band\s+(\d+)\b", " ".join(row["layers"])):
            assert BANDS[int(band_str)] == key

    plan86s = strict_json(ROOT / "registry/h86s_dwad_hypotheses_20261027.json")
    assert 3 <= len(plan86s["hypotheses"]) <= 5
    for row in plan86s["hypotheses"]:
        assert row.get("holdout_dti") is row.get("ci95") is None and "projected_score" not in row
        for key, band_str in re.findall(r"\b([a-z0-9_]+)\s*\(Band\s+(\d+)\b", " ".join(row["layers"])):
            assert BANDS[int(band_str)] == key, f"Band mismatch in {row['id']}: Band {band_str} is {BANDS[int(band_str)]}, not {key}"


def test_band_physics_verification_receipt_blocks_header_mislabels():
    receipt = strict_json(ROOT / "docs/evidence/band-physics-verification-20261024.json")
    assert receipt["schema"] == "gems86.band-physics-verification.v1"
    b6 = receipt["band6_tc_verification"]
    assert b6["band_index"] == 6
    assert b6["min"] > 0.0 and b6["nonpositive_pixel_count"] == 0 and b6["zero_crossing_possible"] is False
    assert b6["correlations_vs_geodawn_radiometrics"]["TC"]["pearson_r"] > 0.995
    assert abs(b6["pearson_r_vs_true_magnetic_tilt_atan2_b9_b3"]) < 0.05
    grav = receipt["gravity_derivative_vector_verification"]["pearson_correlations"]
    assert grav["corr_b18_vs_plus_dg_dx_east"] > 0.94
    assert abs(grav["corr_b18_vs_scalar_grad_mag"]) < 0.05
    assert grav["corr_b11_vs_plus_dg_drow_south"] > 0.93
    assert grav["corr_hypot_b11_b18_vs_b5_slope"] > 0.94
    lap = receipt["gravity_derivative_vector_verification"]["laplace_gzz_multiscale_verification"]["corr_minus_div_b18_b11_vs_minus_laplacian_b13"]
    assert lap["sigma_0px_0m"] < 0.50
    assert lap["sigma_4px_400m"] > 0.85
    assert lap["sigma_6px_600m"] > 0.91


def test_workflow_may_publish_fresh_partial_feed_but_cannot_hide_fatal_errors(monkeypatch, tmp_path):
    from scripts import refresh_fleet
    result = dict(projects_requested=1, projects_snapshotted=0, refresh_complete=False,
                  organizer_receipts_obtained=0, submission_slots_used=0,
                  projects=[dict(status="FORBIDDEN_OR_RATE_LIMITED")])
    monkeypatch.setattr(refresh_fleet, "ROOT", tmp_path)
    monkeypatch.setattr(refresh_fleet, "refresh", lambda **_: result)
    assert refresh_fleet.main([]) == 1
    assert refresh_fleet.main(["--allow-partial"]) == 0
    assert strict_json(tmp_path / "docs/evidence/fleet-feed-current.json") == result
    def fatal(**_):
        raise OSError("Local write/input failure")
    monkeypatch.setattr(refresh_fleet, "refresh", fatal)
    with pytest.raises(OSError):
        refresh_fleet.main(["--allow-partial"])
