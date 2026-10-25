"""Unit and integration tests for H86N-GSST and H86M-LT reconciliation."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.gems86_gsst.features import (
    NODATA,
    clean_band,
    compute_gsst_features,
    gsst_scale_score,
)

ROOT = Path(__file__).resolve().parents[1]


def test_clean_band_replaces_in_footprint_nodata_sentinels():
    fp = np.ones((16, 16), dtype=bool)
    fp[0, :] = False
    arr = np.full((16, 16), 10.0, dtype=np.float32)
    arr[0, :] = NODATA
    arr[5, 5] = NODATA  # in-footprint float32 sentinel (-3.4028235e38)
    arr[6, 6] = np.nan
    cleaned = clean_band(arr, fp)
    assert np.all(np.isfinite(cleaned))
    assert np.allclose(cleaned, 10.0)


def test_gsst_prefers_extended_step_over_compact_plug():
    h, w = 64, 64
    yy, xx = np.meshgrid(np.arange(h, dtype=np.float64), np.arange(w, dtype=np.float64), indexing="ij")
    fp = np.ones((h, w), dtype=bool)
    fp[:2, :] = False

    # Synthetic N-S extended step at x = 32 vs compact plug at (32, 32)
    grav_step = 5.0 * np.tanh((xx - 32.0) / 4.0)
    gy_step, gx_step = np.gradient(grav_step)
    slope_step = np.hypot(gx_step, gy_step)

    r2 = (yy - 32.0) ** 2 + (xx - 32.0) ** 2
    grav_plug = 5.0 * np.exp(-r2 / (2.0 * 3.0**2))
    gy_plug, gx_plug = np.gradient(grav_plug)

    sc_step = gsst_scale_score(grav_step, gx_step, gy_step, sigma=3.0)
    sc_plug = gsst_scale_score(grav_plug, gx_plug, gy_plug, sigma=3.0)

    # At the step crest (32, 32), step persistence and along-strike coherence are near 1
    assert float(sc_step["step_persistence"][32, 32]) > 0.70
    assert float(sc_step["along_coherence"][32, 32]) > 0.90
    # On the compact plug, radial curvature is much higher than on the planar step
    assert float(sc_plug["radial_curv"][32, 35]) > float(sc_step["radial_curv"][32, 32]) + 0.10

    out = compute_gsst_features(grav_step, slope_step, gy_step, gx_step, fp)
    surf = out["surfaces"]["H86N_GSST"]
    assert surf.dtype == np.float32
    assert np.all(np.isfinite(surf))
    assert float(surf[~fp].max()) == 0.0
    assert 0.0 <= float(surf[fp].min()) <= float(surf[fp].max()) <= 1.0


def test_h86n_preregistration_and_run_card_invariants():
    reg = json.loads((ROOT / "registry/h86n_gsst_hypotheses.json").read_text())
    assert reg["schema"] == "gems86.h86n-hypotheses.v1"
    assert reg["lane_assignment"] == "H86N-GSST"
    ids = [h["id"] for h in reg["hypotheses"]]
    assert ids == ["H86N-GSST", "H86N-EQL", "H86N-MTC", "H86N-DSR"]
    for h in reg["hypotheses"]:
        assert h["non_fault_mimic"]
        assert h["falsifier"]
        assert h["layers"]

    card = json.loads((ROOT / "docs/evidence/h86n-gsst-run-card.json").read_text())
    assert card["lane_id"] == "H86N-GSST"
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["dots"] == 37654
    assert 1 <= card["note_chars"] <= 140
    assert card["note_chars"] == len(card["submission_note_le140"])

    ho = card["holdout"]
    assert ho["evidence_class"] == "HOLDOUT-DTI"
    assert ho["evaluator_version"] == "gems57-pooled-hide-v2"
    assert ho["withheld_positive_pixels"] == 11321
    cand = ho["candidate"]
    assert 0.0 < cand["dti"] < 1.0
    assert len(cand["ci95"]) == 2 and cand["ci95"][0] < cand["ci95"][1]
    assert card["leakage_canary"]["gate_le_0.90"] is True
    assert max(card["leakage_canary"]["single_feature_auc"].values()) <= 0.90

    uni = card["correlation_overlap_vs_registry"]
    assert abs(uni["max_surface_spearman_abs"]) <= 0.90
    assert abs(uni["max_dot_spearman_abs"]) <= 0.90
    assert uni["max_overlap3"] <= 0.70

    stem = card["submission_name"] + "-zeros"
    tif_path = ROOT / "docs/downloads" / f"{stem}.tif"
    zip_path = ROOT / "docs/downloads" / f"{stem}.zip"
    rcp_path = ROOT / "docs/downloads" / f"{stem}.json"
    assert tif_path.is_file() and zip_path.is_file() and rcp_path.is_file()


def test_h86m_lt_historical_card_and_current_disposition_are_separate():
    lt_card = json.loads((ROOT / "docs/evidence/h86m-lt-run-card.json").read_text())
    current = json.loads((ROOT / "docs/evidence/h86m-lt-current-disposition.json").read_text())
    assert lt_card["verdict"] == "promote"
    assert lt_card["safe_to_submit"] is False
    assert lt_card["approved_for_weekly_slot"] is False
    assert lt_card["submission_slots_used"] == 0
    assert "holdout_dti" not in lt_card
    assert current["historical_lane_verdict"] == "promote"
    assert current["verdict"] == "negative"
    assert current["decision"] == "DO NOT SUBMIT"
    assert current["holdout_dti"] is None
    assert current["safe_to_submit"] is False

    lt_html = (ROOT / "docs/h86m-lt.html").read_text()
    assert "DO NOT SUBMIT" in lt_html
    assert "is this file ok to submit? yes" not in lt_html.lower()
    home = (ROOT / "docs/index.html").read_text()
    assert "historical lane-level" in home
    assert "current disposition is" in home
