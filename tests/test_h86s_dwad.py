"""Unit, schema, and fail-closed safety tests for Lane H86S-DWAD (2026-10-27)."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.audit_release import strict_json  # noqa: E402
from gems86_dwad.features import (  # noqa: E402
    BANNED_CSV_COLUMNS,
    DWAD_ABLATION_NAMES,
    DWAD_CONT_NAMES,
    DWAD_STATIC_NAMES,
)
from gems86_dwad.operators import (  # noqa: E402
    compute_survey_observability,
    dilatational_stepover_sharpen,
    downslope_canyon_knickzone_backprojection,
    prior_weighted_quadrant_blend,
    sub_claycap_geothermal_feeder_disjunction,
)


def _sha256(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def test_survey_observability_and_downslope_knickzone_backproj_physics():
    shape = (64, 64)
    fp = np.ones(shape, dtype=bool)
    yy, xx = np.indices(shape, dtype=np.float32)
    # West half = steep exposed bedrock range; east half = deep covered alluvial basin
    zb_m = np.where(xx < 28, 60.0, 1800.0).astype(np.float32)
    det_slope = np.where(xx < 28, 18.0, 1.5).astype(np.float32)
    topo_rel = np.where(xx < 28, 210.0, 20.0).astype(np.float32)
    lidar_v = np.where(xx < 28, 255.0, 0.0).astype(np.float32)

    obs, obs_b, obs_r, obs_l = compute_survey_observability(zb_m, det_slope, topo_rel, lidar_v, fp)
    assert obs.shape == shape and np.isfinite(obs).all()
    assert np.isfinite(obs_b).all() and np.isfinite(obs_r).all() and np.isfinite(obs_l).all()
    assert float(obs[:, :20].mean()) > float(obs[:, 40:].mean()) + 0.30

    # Trunk-stream knickzone at x=18 upslope of buried range-front apex at x=28
    zmean_m = (2200.0 - 20.0 * xx).astype(np.float32)
    ksn_max = (40.0 + 5.0 * np.sin(yy / 4.0) + np.where(np.abs(xx - 18) <= 1, 260.0, 0.0)).astype(np.float32)
    log10_area = np.full(shape, 5200.0, dtype=np.float32)
    ksn_sm, adv_800, adv_1500, kn_apex, kn_coh = downslope_canyon_knickzone_backprojection(
        ksn_max, log10_area, zmean_m, zb_m, fp, steps_px=(8.0, 12.0)
    )
    assert np.isfinite(ksn_sm).all() and np.isfinite(adv_800).all() and np.isfinite(adv_1500).all()
    assert np.isfinite(kn_apex).all() and np.isfinite(kn_coh).all()
    assert float(kn_apex[:, 26:31].mean()) > float(kn_apex[:, 48:58].mean())


def test_sub_clay_cap_feeder_and_prior_weighted_quadrant_blend():
    shape = (48, 48)
    fp = np.ones(shape, dtype=bool)
    seam_keep = np.ones(shape, dtype=np.float32)
    yy, xx = np.indices(shape, dtype=np.float32)
    cond = (10.0 / (1.0 + np.exp(-(xx - 24.0) / 1.5)) + 0.5).astype(np.float32)
    rtp = (-30.0 * np.exp(-((xx - 24.0) ** 2) / 6.0)).astype(np.float32)
    grav_s = np.where(np.abs(xx - 24.0) <= 2.0, 18.0, 1.5).astype(np.float32)
    uphead = np.exp(-((xx - 24.0) ** 2) / 9.0).astype(np.float32)
    probe = uphead.copy()
    sinter = uphead.copy()

    margin, feeder, wall, vent = sub_claycap_geothermal_feeder_disjunction(
        cond, rtp, grav_s, uphead, probe, sinter, fp, seam_keep
    )
    assert float(feeder[:, 22:27].mean()) > float(feeder[:, 2:10].mean())
    assert np.isfinite(margin).all() and np.isfinite(wall).all() and np.isfinite(vent).all()

    dil = np.where((xx > 18) & (xx < 30), 25.0, -10.0).astype(np.float32)
    prob = (0.5 * np.exp(-((xx - 24.0) ** 2) / 8.0)).astype(np.float32)
    sharp = dilatational_stepover_sharpen(prob, dil, fp)
    assert np.isfinite(sharp).all() and float(sharp.min()) >= 0.0 and float(sharp.max()) <= 1.0

    raw = np.zeros(shape, dtype=np.float32)
    raw[:24, :24] = 0.15 * np.linspace(0, 1, 24 * 24, dtype=np.float32).reshape(24, 24)
    raw[:24, 24:] = 0.90 * np.linspace(0, 1, 24 * 24, dtype=np.float32).reshape(24, 24)
    raw[24:, :24] = 0.50 * np.linspace(0, 1, 24 * 24, dtype=np.float32).reshape(24, 24)
    raw[24:, 24:] = 0.50 * np.linspace(0, 1, 24 * 24, dtype=np.float32).reshape(24, 24)
    qids = ((yy >= 24).astype(np.int8) * 2 + (xx >= 24).astype(np.int8)).astype(np.int8)
    blended = prior_weighted_quadrant_blend(raw, fp, qids, alpha_pool=0.5)
    assert abs(float(blended[qids == 0].mean()) - float(blended[qids == 1].mean())) < abs(
        float(raw[qids == 0].mean()) - float(raw[qids == 1].mean())
    )
    all_names = set(DWAD_STATIC_NAMES) | set(DWAD_ABLATION_NAMES) | set(DWAD_CONT_NAMES)
    assert BANNED_CSV_COLUMNS.isdisjoint(all_names)
    assert len(DWAD_STATIC_NAMES) == 24 and len(DWAD_ABLATION_NAMES) == 6 and len(DWAD_CONT_NAMES) == 4


def test_h86s_dwad_run_card_artifact_estimator_and_site_banners():
    card = strict_json(ROOT / "docs/evidence/h86s-dwad-run-card.json")
    est = strict_json(ROOT / "docs/evidence/h86s-fleet-estimator-20261027-v3.json")
    f9 = strict_json(ROOT / "docs/evidence/focus9-and-siblings-forensics-20261027.json")

    assert card["lane_id"] == "H86S-DWAD"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False and card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0 and card["experiments_run"] == 3
    assert card["note_chars"] <= 140

    e1 = card["holdout_dti"]["candidate"]["dti"]
    e2 = card["holdout_dti"]["all_arms"]["E2_dwad_zero_catalogue_blind_dcelf"]["dti"]
    assert e2 > 0.080  # new pure-blind 37,654-dot DCELF record (0.0825)
    assert e1 > 0.115
    assert card["leakage_canary_summary"]["any_leakage_flag"] is False
    assert card["leakage_canary_summary"]["dist_known_fault_px_read"] is False
    assert card["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90
    assert card["leakage_canary_summary"]["features_tested"] == 37

    inf = card["correlation_overlap_vs_registry"]["full_registry_informative_dot_field_audit"]
    assert inf["discrete_le_90k_firings_over_0p70"] == 0
    assert inf["worst_discrete_le_90k_overlap_3px"] <= 0.70
    assert card["correlation_overlap_vs_registry"]["live_focus9_and_sibling_orgs_final_dots"]["firings_over_0p70"] == 0

    tif = ROOT / card["submission_file"]
    zp = ROOT / card["submission_zip"]
    assert tif.is_file() and zp.is_file()
    assert _sha256(tif) == card["raster_sha256"]
    with rasterio.open(tif) as src:
        arr = src.read(1)
        assert src.shape == (3730, 3292) and str(src.crs) == "EPSG:32611"
        assert np.isfinite(arr).all()
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
        assert int((arr > 0).sum()) == 37654
    with zipfile.ZipFile(zp) as zf:
        assert zf.namelist() == [tif.name]

    assert est["n_fit_25k_to_65k_dots"] == 29
    assert est["loo_rmse"] < 0.0380
    assert len(f9["focus9_executive_summary"]) == 9
    assert len(f9["sibling_orgs_20261027"]) == 12

    for page_rel in ("docs/index.html", "docs/executive-summary.html"):
        html = (ROOT / page_rel).read_text(encoding="utf-8")
        assert card["submission_name"] in html
        assert "IS THIS FILE OK TO SUBMIT? NO" in html
        assert "Focus-9 Executive Summary" in html
