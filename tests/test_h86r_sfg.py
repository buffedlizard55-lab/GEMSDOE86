"""Unit & preregistration contract tests for Lane H86R-SFG (strike-field gate)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.gems86_sfg.features import (
    alignment_A, catalogue_strike_field, emit_poisson_disk, fuse_E, gated,
)

ROOT = Path(__file__).resolve().parents[1]
NAMES5 = ["sfg_grav_edge_b5_rank", "sfg_mag_edge_b3_rank", "sfg_rtp_gradmag_s1p5_rank",
          "sfg_basement_gradmag_rank", "sfg_elev_slope_b19_rank"]


def test_h86r_preregistration_and_hypothesis_queue_contracts():
    hyp = json.loads((ROOT / "registry/h86r_hypotheses_20261026.json").read_text())
    prereg = json.loads((ROOT / "research/H86R_SFG_PREREGISTRATION.json").read_text())
    assert 3 <= len(hyp["hypotheses"]) <= 5
    selected = [h for h in hyp["hypotheses"] if h["selected_for_validation"]]
    assert len(selected) == 1
    assert selected[0]["id"] == prereg["selected_hypothesis_id"] == "H86R-1_SFG"
    assert prereg["budget"]["max_experiments"] == len(prereg["arms"]) == 3
    assert prereg["budget"]["weekly_submission_slots_authorized"] == 0
    assert prereg["budget"]["dot_budget"] == 37654
    # the rejected PCPD duplicate must stay recorded as rejected, never selected
    pcpd = [h for h in hyp["hypotheses"] if "PCPD_REJECTED" in h["id"]]
    assert len(pcpd) == 1 and pcpd[0]["selected_for_validation"] is False


def test_fuse_E_second_highest_exact_including_ties():
    rng = np.random.default_rng(3)
    planes = {k: rng.random((30, 40)).astype(np.float32) for k in NAMES5}
    planes[NAMES5[1]][0, 0] = planes[NAMES5[0]][0, 0] = 0.99  # tie at top
    got = fuse_E(planes)
    stack = np.stack([planes[k] for k in NAMES5])
    ref = 0.5 * stack.mean(axis=0) + 0.5 * np.sort(stack, axis=0)[-2]
    assert float(np.abs(got - ref).max()) == 0.0


def test_strike_gate_rewards_parallel_and_penalizes_perpendicular_edges():
    H, W = 200, 200
    fp = np.ones((H, W), bool)
    cat = np.zeros((H, W), bool)
    cat[:, 100] = True  # N-S catalogue trace (constant col): strike along rows
    cosC, sinC = catalogue_strike_field(cat, fp)
    # gravity step across a N-S fault: gradient purely E-W (gcol), grow=0 -> parallel
    b18_par = np.full((H, W), 5.0, np.float32)
    b11_0 = np.zeros((H, W), np.float32)
    a_par = alignment_A(b11_0, b18_par, fp, cosC, sinC)
    # gravity gradient purely N-S (grow) -> edge strike E-W, perpendicular to catalogue
    a_perp = alignment_A(np.full((H, W), 5.0, np.float32), np.zeros((H, W), np.float32), fp, cosC, sinC)
    assert float(a_par[100, 150]) > 0.9
    assert float(a_perp[100, 150]) < 0.1
    base = np.ones((H, W), np.float32)
    assert gated(base, a_par)[100, 150] > gated(base, a_perp)[100, 150]
    assert float(gated(base, a_perp)[100, 150]) >= 0.349  # 0.35 soft floor (float32) keeps transfer faults


def test_emission_budget_spacing_and_determinism():
    rng = np.random.default_rng(1)
    surf = rng.random((200, 200)).astype(np.float32)
    elig = np.ones((200, 200), bool)
    d1 = emit_poisson_disk(surf, elig, budget=500)
    d2 = emit_poisson_disk(surf, elig, budget=500)
    assert (d1 == d2).all() and int(d1.sum()) == 500
    from scipy.spatial import cKDTree
    yx = np.argwhere(d1)
    dist, _ = cKDTree(yx).query(yx, k=2)
    assert float(dist[:, 1].min()) >= 2.8 - 1e-9


def test_h86r_run_card_disk_artifact_and_negative_governance():
    card = json.loads((ROOT / "docs/evidence/h86r-sfg-run-card.json").read_text())
    import hashlib, zipfile
    tif = ROOT / card["submission_file"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    with zipfile.ZipFile(ROOT / card["submission_zip"]) as z:
        assert z.namelist() == [tif.name] and z.read(tif.name) == tif.read_bytes()
    v = card["validator_output"]
    assert v["all_checks_passed"] and sum(x is True for x in v["checks"].values()) == len(v["checks"]) == 15
    assert card["verdict"] == "negative" and card["decision"] == "DO NOT SUBMIT"
    assert card["scoped_download_candidate"] is False
    assert card["gates"]["G3_holdout_E1_gt_E2_point"] is False
    assert card["gates"]["G4_sgmc_E1_ge_H33_same_call"] is False
    assert card["gates"]["G5_uniqueness_scoped_discrete_le100k"] is True
    assert card["submission_ready"] is False and card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False and card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert len(card["submission_name"]) <= 140 and len(card["note"]) <= 140
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI" and h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    # historical comparators replicated on the identical split (instrument sanity)
    assert abs(h["all_arms"]["H33_visible_collar"]["dti"] - 0.0036) < 5e-4
    assert abs(card["sgmc_proxy"]["scores"]["GEMSDOE32_H33"]["dti"] - 0.0937) < 5e-4
    assert all(not c["leakage_flag"] for c in card["leakage_canary"].values())


def test_h86r_estimator_is_labelled_projection_not_score():
    est = json.loads((ROOT / "docs/evidence/h86r-fleet-estimator-20261026-v2.json").read_text())
    assert "not a score" in est["evidence_class"] and "never an organizer-confirmed score" in est["caveat"].lower()
    assert est["version"] == "v2-corrected-strict-matching"
    assert est["n"] == 23 and est["loo_rmse"] > 0
    files = {r["file"] for r in est["rows"]}
    assert len(est["dropped_false_matches"]) == 5
    assert not any("GEMSDOE88" in f or "GEMSDOE70" in f for f in files)
    lo, hi = est["candidate"]["interval_approx"]
    assert 0.0 <= lo <= est["candidate"]["projection"] <= hi <= 1.0


def test_h86r_selector_table_no_false_live_score_on_unscored_candidate():
    tab = json.loads((ROOT / "docs/evidence/h86r-selector-table-20261026.json").read_text())
    mine = [r for r in tab["rows"] if "h86r-sfg" in r["file"]]
    assert len(mine) == 1 and mine[0]["live_owner_reported"] is None
    assert mine[0]["unique_scoped_vs_h33_lineage"] is True
