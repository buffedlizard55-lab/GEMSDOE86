"""Unit, preregistration, and run-card contract tests for Lane H86T-KNDS."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from src.gems86_knds.features import (
    ALL_FEATURE_NAMES,
    E1_FEATURES,
    E2_FEATURES,
    E3_FEATURES,
    KNDS_BACKPROJ_FEATURES,
    LOCAL_CHI_FEATURES,
    NATIVE_BASELINE_FEATURES,
    build_fold_visible_features,
    build_static_knds_stack,
    clean,
    fit_predict_loqo_arm,
    rank01,
)

ROOT = Path(__file__).resolve().parents[1]


def test_rank01_ties_constant_fields_and_permutation_are_not_spatial_ramps():
    mask = np.ones((3, 4), dtype=bool)
    np.testing.assert_array_equal(rank01(np.ones((3, 4), np.float32), mask), 0)
    values = np.array([[0, 0, 4], [2, 4, 0]], dtype=np.float32)
    mask = np.ones_like(values, dtype=bool)
    result = rank01(values, mask)
    assert np.all(result[values == 0] == 0)
    assert np.all(result[values == 4] == result[values == 4][0])
    permutation = np.array([5, 3, 0, 4, 2, 1])
    permuted = values.ravel()[permutation]
    np.testing.assert_allclose(
        rank01(permuted, np.ones_like(permuted, dtype=bool)),
        result.ravel()[permutation],
    )
    assert rank01(values, np.zeros_like(mask)).sum() == 0


def test_rank01_rejects_nonfinite_selected_values_and_shape_mismatch():
    for bad in (np.nan, np.inf, -np.inf):
        with pytest.raises(ValueError, match="finite"):
            rank01(np.array([0.0, bad]), np.array([True, True]))
    with pytest.raises(ValueError, match="matching shapes"):
        rank01(np.zeros((2, 2)), np.ones((2, 1), dtype=bool))
    # Masked invalid values are not ranked.
    np.testing.assert_array_equal(
        rank01(np.array([3.0, np.nan]), np.array([True, False])), [0, 0]
    )


def test_archived_h86t_runner_refuses_to_overwrite_history_even_if_feasible(monkeypatch):
    from scripts import protocol_preflight, run_h86t_knds

    card = ROOT / "docs/evidence/h86t-knds-run-card.json"
    before = card.read_bytes()
    monkeypatch.setattr(protocol_preflight, "require_feasible", lambda: None)
    with pytest.raises(FileExistsError, match="archived"):
        run_h86t_knds.run_pa86_lane()
    assert card.read_bytes() == before


def test_h86t_preregistration_and_hypothesis_queue_contracts():
    hyp = json.loads((ROOT / "registry/h86t_hypotheses_20261027.json").read_text())
    prereg = json.loads((ROOT / "research/H86T_KNDS_PREREGISTRATION.json").read_text())
    assert 3 <= len(hyp["hypotheses"]) <= 5
    selected = [
        h for h in hyp["hypotheses"]
        if h["status"] == "SELECTED_FOR_EXECUTION_THIS_SESSION"
    ]
    assert len(selected) == 1
    assert selected[0]["id"] == prereg["hypothesis_id"] == "H86T-1_KNDS"
    assert prereg["lane_id"] == "H86T-KNDS"
    assert prereg["budget"]["max_experiments"] == len(prereg["arms"]) == 3
    assert prereg["budget"]["dot_budget"] == 37654
    assert tuple(prereg["knds_backprojected_features"]) == KNDS_BACKPROJ_FEATURES
    assert tuple(prereg["local_chi_features"]) == LOCAL_CHI_FEATURES
    assert tuple(prereg["native_baseline_features"]) == NATIVE_BASELINE_FEATURES


def test_synthetic_knds_stack_and_loqo_arm(tmp_path: Path):
    h, w = 64, 64
    fp = np.ones((h, w), dtype=bool)
    fp[:2, :] = False

    chi_path = tmp_path / "chi.tif"
    topo_path = tmp_path / "topo10.tif"
    transform = Affine.translation(243350.0, 4508550.0) @ Affine.scale(100.0, -100.0)

    rng = np.random.default_rng(42)
    with rasterio.open(
        chi_path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=5,
        dtype="int16",
        crs="EPSG:32611",
        transform=transform,
    ) as dst:
        dst.write(rng.integers(-200, 1500, size=(h, w), dtype=np.int16), 1)
        dst.write(rng.integers(-500, 200, size=(h, w), dtype=np.int16), 2)
        dst.write(rng.integers(5, 250, size=(h, w), dtype=np.int16), 3)
        dst.write(rng.integers(3800, 7500, size=(h, w), dtype=np.int16), 4)
        # Sloping elevation from N to S through Lahontan 1335 m band
        z_grid = np.linspace(1800, 1200, h, dtype=np.float32)[:, None] * np.ones((1, w), dtype=np.float32)
        dst.write(z_grid.astype(np.int16), 5)

    with rasterio.open(
        topo_path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=9,
        dtype="uint8",
        crs="EPSG:32611",
        transform=transform,
    ) as dst:
        for b in range(1, 10):
            dst.write(rng.integers(10, 240, size=(h, w), dtype=np.uint8), b)

    def fake_read_band(idx: int) -> np.ndarray:
        r = np.random.default_rng(100 + idx)
        arr = r.normal(loc=100.0, scale=25.0, size=(h, w)).astype(np.float32)
        arr[0, 0] = np.float32(-3.4028234663852886e38)
        return arr

    planes = build_static_knds_stack(fake_read_band, fp, chi_path, topo_path)
    vis = np.zeros((h, w), dtype=bool)
    vis[15:48, 30] = True
    vis_feats = build_fold_visible_features(vis, fp, planes["_geophys_theta"])
    planes.update(vis_feats)

    for name in ALL_FEATURE_NAMES:
        assert name in planes
        arr = planes[name]
        assert arr.shape == (h, w)
        assert float(arr[fp].min()) >= 0.0 and float(arr[fp].max()) <= 1.0
        assert float(arr[~fp].max()) == 0.0

    surf_e1 = fit_predict_loqo_arm(planes, E1_FEATURES, vis, fp, arm_id="E1", n_neg_per_fold=200)
    surf_e2 = fit_predict_loqo_arm(planes, E2_FEATURES, vis, fp, arm_id="E2", n_neg_per_fold=200)
    surf_e3 = fit_predict_loqo_arm(planes, E3_FEATURES, vis, fp, arm_id="E3", n_neg_per_fold=200)
    for s in (surf_e1, surf_e2, surf_e3):
        assert s.shape == (h, w)
        assert np.all(np.isfinite(s))
        assert float(s[fp].min()) >= 0.0 and float(s[fp].max()) <= 1.0


def test_h86t_run_card_is_negative_unique_and_format_bound():
    card = json.loads((ROOT / "docs/evidence/h86t-knds-run-card.json").read_text())
    assert card["lane_id"] == "H86T-KNDS"
    assert card["verdict"] == "negative" and card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False and card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3 and len(card["note"]) <= 140
    assert card["leakage_canary_summary"]["any_leakage_flag"] is False
    assert card["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90
    assert card["gates"]["G1_format_writer_pass"] is True
    assert card["gates"]["G2_canary_le_0p90"] is True
    assert card["gates"]["G3_holdout_E1_gt_E2_point"] is False
    assert card["gates"]["G5_uniqueness_scoped_discrete_le100k"] is True
    assert card["uniqueness_scoped"]["overlap_vs_H33"] <= 0.70
    assert card["uniqueness_scoped"]["final_dots_worst_discrete"]["forward_overlap_3px"] <= 0.70
    assert abs(card["uniqueness_scoped"]["surface_worst_sampled_rho"]["sampled_spearman"]) <= 0.90
    v = card["validator_output"]
    assert v["all_checks_passed"] and v["min"] >= 0.0 and v["max"] <= 1.0
    assert v["emitted_positive_pixels"] == 37654
    assert (ROOT / card["submission_file"]).is_file()
    assert (ROOT / card["submission_zip"]).is_file()
    assert (ROOT / card["submission_receipt"]).is_file()
