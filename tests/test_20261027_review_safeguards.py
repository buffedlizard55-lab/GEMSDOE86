"""Review-only regressions: no experiments or candidate rasters are produced."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import check_hypothesis_bands, verify_focus9_downloads
from scripts.audit_h86t_input_semantics import ksn_zero_tie
from src.gems86.io import BANDS

ROOT = Path(__file__).resolve().parents[1]


def test_current_hypotheses_are_unrun_and_identify_native_band_physics():
    queue = json.loads(check_hypothesis_bands.QUEUE.read_text())
    assert len(check_hypothesis_bands.validate(queue)["hypotheses"]) == 4
    assert BANDS[5] == "iso_grav_anom_slope"
    assert BANDS[7] == "geod_shearrate"
    assert BANDS[10] == "deq_n100a15"
    assert BANDS[12] == "det_elev"
    assert BANDS[16] == "ieq_n100a15"
    assert BANDS[17] == "cond_surf"
    for row in queue["hypotheses"]:
        assert row["named_non_fault_mimic"] and row["availability"]
        assert "no numeric gain or score forecast" in row["expected_improvement_rank"]


@pytest.mark.parametrize("mutation", ["wrong_band_name", "false_physics", "unrun_status", "duplicate_id", "empty_source"])
def test_proposal_validation_rejects_unsafe_or_mislabeled_claims(mutation):
    queue = json.loads(check_hypothesis_bands.QUEUE.read_text())
    if mutation == "wrong_band_name":
        queue["hypotheses"][0]["native_bands"][0]["name"] = "gravity_bouguer"
    elif mutation == "false_physics":
        claim = queue["hypotheses"][1]["native_bands"][1]
        assert claim["index"] == 5
        claim["physical_label"] = "det_elev"
    elif mutation == "unrun_status":
        queue["status"] = "PROMOTE"
    elif mutation == "duplicate_id":
        queue["hypotheses"][1]["id"] = queue["hypotheses"][0]["id"]
    else:
        queue["hypotheses"][0]["sources"] = []
    with pytest.raises(ValueError):
        check_hypothesis_bands.validate(queue)


def test_h86t_zero_tie_measurement_matches_archived_input_logic():
    ksn = np.array([[0, 3, -32000], [4, -1, 8]])
    area = np.array([[5, 5, 5], [5, 5, -32000]])
    elev = np.full((2, 3), 100)
    fp = np.array([[1, 1, 1], [1, 0, 1]], dtype=bool)
    result = ksn_zero_tie(ksn, area, elev, fp)
    assert result["footprint_pixels"] == 5
    assert result["input_zero_ties"] == 3  # zero, invalid KSN, invalid area
    assert result["legacy_first_zero_rank"] == 0.0
    assert result["legacy_last_zero_rank"] == 0.5
    assert result["corrected_all_zero_tie_rank"] == 0.0
    with pytest.raises(ValueError, match="matching"):
        ksn_zero_tie(ksn, area, elev[:, :1], fp)


def test_h86t_posthoc_receipt_does_not_relabel_or_rerun_holdout():
    evidence = json.loads((ROOT / "docs/evidence/h86t-input-provenance-20261027.json").read_text())
    assert evidence["chi_ksn_zero_tie"]["input_zero_ties"] == 4404851
    assert evidence["chi_ksn_zero_tie"]["footprint_pixels"] == 5167373
    assert evidence["new_model_experiments"] == evidence["submission_slots_used"] == 0
    assert evidence["new_candidate_generated"] is False
    historic = json.loads((ROOT / evidence["historical_run_card"]).read_text())
    assert historic["holdout_dti"]["candidate"]["dti"] == pytest.approx(0.0861, abs=0.0001)
    assert historic["verdict"] == "negative"


def test_focus9_download_proof_is_bound_to_historical_forensics_and_is_audit_only():
    proof = json.loads(verify_focus9_downloads.OUTPUT.read_text())
    verify_focus9_downloads.validate_proof(proof)
    assert len(proof["rows"]) == 9
    assert all(r["download_authorized_for_submission"] is False for r in proof["rows"])
    assert all(verify_focus9_downloads.raw_url(r).startswith("https://github.com/") for r in proof["rows"])
    for key, bad in (("sha256", "0" * 64), ("path", "../../outside.tif"),
                     ("commit_sha", "0" * 40), ("git_blob_sha1", "0" * 40),
                     ("bytes", 1), ("download_authorized_for_submission", True)):
        changed = deepcopy(proof)
        changed["rows"][0][key] = bad
        with pytest.raises(ValueError):
            verify_focus9_downloads.validate_proof(changed)


def test_corrected_site_displays_review_before_archived_historical_claims():
    from scripts import build_site
    page = build_site.render(ROOT)["docs/executive-summary.html"]
    assert page.index('id="focus9-summary"') < page.index('id="h86t-knds-banner"')
    assert "4,404,851 tied zero inputs" in page
    assert "Both paired CIs cross zero" in page
    assert "portal rejection cannot occur from this file" not in page
    assert "high <code>&gt;1 km</code> off-catalogue share is necessary" not in page
    assert "Record discrepancy:" in page
    assert "would not reproduce the portal error" not in page
    assert page.count("Historical TIFF — audit only") == 9


def test_negative_session_card_cannot_be_mistaken_for_a_generated_submission():
    card = json.loads((ROOT / "research/SESSION_20261027_0A171468_RUN_CARD.json").read_text())
    assert card["verdict"] == "negative"
    assert card["new_candidate_generated"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["raster_sha256"] is card["submission_name"] is card["note"] is None
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert card["correlation_overlap_vs_registry"]["universal_forward_overlap"] == 1.0
    assert card["correlation_overlap_vs_registry"]["registry_complete"] is False
    assert card["safe_to_submit"] is card["approved_for_weekly_slot"] is False


def test_scheduled_pages_fails_closed_and_refreshes_download_identities():
    pages = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "scripts/audit_release.py --measure-registry" in pages
    assert "scripts/refresh_fleet.py --allow-partial" in pages
    assert "scripts/check_hypothesis_bands.py" in pages
    assert "scripts/verify_focus9_downloads.py --write" in pages
    assert pages.index("refresh_fleet.py") < pages.index("verify_focus9_downloads.py --write")
    assert pages.index("verify_focus9_downloads.py --write") < pages.index("scripts/build_site.py")
    assert "scripts/build_site.py --check" in pages and "scripts/check_site.py" in pages
    assert "python -m pytest -q" in pages
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "scripts/check_hypothesis_bands.py" in ci
    assert "scripts/verify_focus9_downloads.py" in ci
