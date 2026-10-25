"""Unit and integration tests for Lane H86J-CSGD and H86G-EDTI full-registry revocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest
import rasterio

from scripts.run_h86j_csgd import sar_censoring_weight
from src.gems86.io import BANDS
from src.gems86_csgd import features as csgd

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_h86j_hypotheses_and_preregistration_respect_band_indices_and_budget():
    hyp = json.loads((ROOT / "registry/h86j_hypotheses.json").read_text(encoding="utf-8"))
    assert len(hyp["hypotheses"]) == 4
    assert [h["rank"] for h in hyp["hypotheses"]] == [1, 2, 3, 4]
    selected = [h for h in hyp["hypotheses"] if h["selected_for_validation"]]
    assert len(selected) == 1 and selected[0]["lane_code"] == "H86J-CSGD"
    for h in hyp["hypotheses"]:
        assert h["non_fault_mimic"] and h["novelty_vs_repo_and_fleet"]
        for lyr in h["layers"]:
            if "band" in lyr:
                assert BANDS[lyr["band"]] == lyr["name"]

    prereg = json.loads((ROOT / "research/H86J_CSGD_PREREGISTRATION.json").read_text(encoding="utf-8"))
    assert prereg["lane"] == "H86J-CSGD"
    assert prereg["budget"]["max_experiments"] == 3
    assert prereg["budget"]["max_wall_clock_hours"] <= 2.0
    assert prereg["budget"]["weekly_submission_slots_used"] == 0
    assert len(prereg["arms"]) == 3
    assert prereg["safety_and_uniqueness_gates"]["leakage_canary_max_discriminative_auc"] == 0.90


def test_csgd_deep_features_exclude_dem_and_forbid_gdr_fault_distance():
    dem_tokens = {"dem_elevation", "slope", "curv_profile", "sar_slope", "sar_relief", "sar_curv"}
    for fname in csgd.DEEP_FEATURE_NAMES:
        assert not any(tok in fname for tok in dem_tokens), fname
    assert len(csgd.DEEP_FEATURE_NAMES) == 18
    assert len(csgd.EXPOSURE_FEATURE_NAMES) == 5
    assert "dist_known_fault_px" in csgd.FORBIDDEN_GDR_COLUMNS

    fp = np.ones((16, 16), dtype=bool)
    fp[0, :] = False
    e_hat = np.linspace(0.05, 0.95, 16 * 16, dtype=np.float32).reshape(16, 16)
    w0 = sar_censoring_weight(e_hat, fp, gamma=0.0)
    w1 = sar_censoring_weight(e_hat, fp, gamma=0.85)
    assert np.allclose(w0[fp], 1.0, atol=1e-5)
    assert w1[1, 0] > w1[-1, -1]  # low-exposure buried cells receive higher SAR inverse-propensity weight
    assert float(w1[~fp].sum()) == 0.0


def test_h86j_csgd_run_card_raster_zip_and_full_registry_uniqueness():
    card_path = ROOT / "docs/evidence/h86j-csgd-run-card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    assert card["lane"] == "H86J-CSGD"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert 0 < len(card["note"]) == card["note_chars"] <= 140

    tif_path = ROOT / card["submission_file"]
    zip_path = tif_path.with_suffix(".zip")
    rec_path = tif_path.with_suffix(".json")
    assert tif_path.is_file() and zip_path.is_file() and rec_path.is_file()
    assert _sha256(tif_path) == card["raster_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    sample = ROOT / "data/bridge/sample_submission.tif"
    with rasterio.open(sample) as s_src, rasterio.open(tif_path) as c_src:
        assert (c_src.count, c_src.shape, c_src.crs, c_src.transform) == (
            1, s_src.shape, s_src.crs, s_src.transform
        )
        arr = c_src.read(1)
    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    assert int((arr > 0).sum()) == 37654

    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["leakage_canary_summary"]["any_leakage_flag"] is False
    assert h["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90
    assert h["paired_delta_vs_R0_D28_visible_collar"]["ci95"][0] > 0.0
    assert h["all_arms"]["E2_csgd_unweighted_pu_ablation"]["dti"] > 0.15

    reg = card["correlation_overlap_vs_registry"]
    surf_file = ROOT / reg["surface_preplacement"]["report"]
    dots_file = ROOT / reg["final_dots"]["report"]
    assert _sha256(surf_file) == reg["surface_preplacement"]["report_sha256"]
    assert _sha256(dots_file) == reg["final_dots"]["report_sha256"]
    assert reg["surface_preplacement"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["final_dots"]["worst_spearman_full_footprint"] <= 0.90
    dots_doc = json.loads(dots_file.read_text(encoding="utf-8"))
    assert dots_doc["shared_summary"]["registry_rasters_checked"] == 690
    assert dots_doc["two_phase"]["like_for_like_reading"]["dot_field_rasters"] == 636

    # Verify zero informative (halo_coverage <= 0.70) dot-field firings on primary E1
    inf_e1 = card["informative_registry_overlap_by_arm"]["E1_csgd_sar_debiased"]
    dot_inf_hits = [
        r for r in inf_e1["top_informative_firings"]
        if r["registry_positive_pixels"] < int(0.20 * 5167373)
    ]
    assert dot_inf_hits == []


def test_h86g_edti_full_registry_revocation_audit_is_bound():
    rev_path = ROOT / "docs/evidence/h86g-edti-full-registry-audit-20261025.json"
    rev = json.loads(rev_path.read_text(encoding="utf-8"))
    assert rev["verdict"] == "negative_duplicate_revoked_do_not_submit"
    assert rev["restored_compatible_rasters_checked_excl_self"] == 689
    assert rev["dot_field_forward_overlap_firings_gt_0p70"] == 44
    assert rev["informative_dot_firings_halo_le_0p70_count"] == 25
    assert any(
        r["their_dots"] <= 45000 and r["fwd_overlap"] > 0.70
        for r in rev["informative_dot_firings_halo_le_0p70"]
    )
