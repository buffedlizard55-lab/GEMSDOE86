"""Unit and evidence-contract tests for Lane H86I-KSAD (session 53d26a87)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src", ROOT / "vendor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems86_ksad.allocator import (  # noqa: E402
    dinkelbach_submodular_k3_allocate,
    elkan_bayes_recalibrate,
    expected_self_credit_k3,
    pointwise_disc_thin,
)
from gems86_ksad.physics import (  # noqa: E402
    COVER_BLIND_STATIC_NAMES,
    ELASTIC_FEATURE_NAMES,
    STATIC_FEATURE_NAMES,
    build_static_features,
    compute_exposure_propensity,
    compute_kostrov_elastic_fields,
    kostrov_azimuthal_tendencies,
    spin2_from_row_col_grad,
    verify_band_table,
)


def _write_tif(path: Path, arr_3d: np.ndarray, dtype: str) -> None:
    bands, h, w = arr_3d.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=bands,
        dtype=dtype,
        crs="EPSG:32611",
        transform=from_origin(300000.0, 4500000.0, 100.0, 100.0),
    ) as dst:
        dst.write(arr_3d.astype(dtype))


def test_spin2_polarity_flip_invariance_and_kostrov_tendency() -> None:
    verify_band_table()
    rng = np.random.default_rng(862026)
    dr = rng.normal(size=(32, 32)).astype(np.float32)
    dc = rng.normal(size=(32, 32)).astype(np.float32)
    c2_a, s2_a, e_a = spin2_from_row_col_grad(dr, dc, smooth_sigma=1.5)
    c2_b, s2_b, e_b = spin2_from_row_col_grad(-dr, -dc, smooth_sigma=1.5)
    np.testing.assert_allclose(c2_a, c2_b, atol=1e-6)
    np.testing.assert_allclose(s2_a, s2_b, atol=1e-6)
    np.testing.assert_allclose(e_a, e_b, atol=1e-6)

    # Strike N22E (normal azimuth 22 deg clockwise from N -> dr_south = sin(22), dc_east = cos(22))
    # should strictly outscore N112E perpendicular strike on normal dilation tendency.
    th_opt = np.deg2rad(22.0)
    th_orth = np.deg2rad(112.0)
    c2_opt = np.full((8, 8), np.cos(2.0 * th_opt), dtype=np.float32)
    s2_opt = np.full((8, 8), np.sin(2.0 * th_opt), dtype=np.float32)
    c2_orth = np.full((8, 8), np.cos(2.0 * th_orth), dtype=np.float32)
    s2_orth = np.full((8, 8), np.sin(2.0 * th_orth), dtype=np.float32)
    dil = np.ones((8, 8), dtype=np.float32)
    shr = np.ones((8, 8), dtype=np.float32)
    td_opt, _ = kostrov_azimuthal_tendencies(c2_opt, s2_opt, dil, shr)
    td_orth, _ = kostrov_azimuthal_tendencies(c2_orth, s2_orth, dil, shr)
    assert float(td_opt.mean()) > 0.99
    assert float(td_orth.mean()) < 1e-5


def test_build_static_features_masks_int16_minus_32768_sentinels(tmp_path: Path) -> None:
    h, w = 40, 44
    rng = np.random.default_rng(42)
    fp = np.ones((h, w), dtype=bool)
    fp[:3, :] = False  # verify outside-footprint zeroing

    feat = rng.normal(loc=10.0, scale=3.0, size=(19, h, w)).astype(np.float32)
    _write_tif(tmp_path / "training_features.tif", feat, "float32")

    ext = tmp_path / "external"
    ext.mkdir()
    _write_tif(ext / "geodawn_extensions_u8.tif", rng.integers(10, 220, size=(4, h, w)), "uint8")
    _write_tif(ext / "topo_10m_derived_100m_u8.tif", rng.integers(5, 240, size=(8, h, w)), "uint8")
    _write_tif(ext / "geodawn_rad_u8.tif", rng.integers(10, 200, size=(3, h, w)), "uint8")
    lid = rng.integers(5, 220, size=(12, h, w), dtype=np.uint8)
    lid[11, :20, :] = 1
    lid[11, 20:, :] = 0
    _write_tif(ext / "lidar_scarp_features_u8.tif", lid, "uint8")

    # Inject -32768 ocean/nodata sentinels in Bands 1..4 of dem10_chi_100m_i16.tif
    # (IR-86-DEM10-CHI-SENTINEL-20261025) and Lahontan ~1285m shoreline elevations in Band 5.
    chi = np.zeros((5, h, w), dtype=np.int16)
    chi[0] = 900
    chi[1] = 300
    chi[2] = 450
    chi[3] = 6500
    chi[4] = 1285
    chi[:4, 10:25, 12:30] = -32768
    _write_tif(ext / "dem10_chi_100m_i16.tif", chi, "int16")

    out_mm = tmp_path / "static_f16.npy"
    mm = build_static_features(tmp_path / "training_features.tif", ext, fp, out_mm)
    assert mm.shape == (26, h, w)
    assert len(STATIC_FEATURE_NAMES) == 26
    assert len(COVER_BLIND_STATIC_NAMES) == 24
    assert np.isfinite(mm).all()
    assert np.all(mm[:, ~fp] == 0.0)

    ksn_idx = STATIC_FEATURE_NAMES.index("fluv_ksn_knickzone")
    chi_idx = STATIC_FEATURE_NAMES.index("fluv_chi_step_knick")
    # Sentinel interior cells must not explode into negative-32768 edge spikes, and must
    # remain near zero (up to sigma=2.5 Gaussian boundary tail) vs ~1.0 on valid cells:
    assert float(mm[ksn_idx].min()) >= 0.0
    assert float(mm[chi_idx].min()) >= 0.0
    assert float(mm[chi_idx, 17, 21]) < 0.01
    assert float(mm[chi_idx, 5, 5]) > 0.50

    c_hat = compute_exposure_propensity(ext, fp)
    assert c_hat.shape == (h, w)
    assert float(c_hat[fp].min()) >= 0.35 - 1e-6
    assert float(c_hat[fp].max()) <= 1.0 + 1e-6


def test_kostrov_elastic_fields_only_use_visible_mask() -> None:
    h, w = 48, 48
    fp = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    # Two opposing collinear N-S segments separated by a releasing stepover gap
    vis[8:18, 22] = True
    vis[28:38, 24] = True
    fields = compute_kostrov_elastic_fields(vis, fp)
    assert set(fields.keys()) == set(ELASTIC_FEATURE_NAMES)
    for arr in fields.values():
        assert arr.shape == (h, w)
        assert np.isfinite(arr).all()
        # Inside 2.6 px collar of visible catalogue must be strictly zero
        assert np.all(arr[vis] == 0.0)
    # Releasing stepover bridge must fire in the gap between the two tips (rows 20..26)
    assert float(fields["releasing_stepover_bridge"][21:26, 22:25].max()) > 0.0


def test_dinkelbach_submodular_k3_allocator_stops_on_negative_marginal_gain() -> None:
    h, w = 36, 36
    prob_raw = np.full((h, w), 0.02, dtype=np.float32)
    # Two isolated high-probability fault spots far apart
    prob_raw[10, 10] = 0.96
    prob_raw[26, 26] = 0.95
    cal = elkan_bayes_recalibrate(prob_raw, neg_subsample_ratio=20.0)
    assert float(cal[10, 10]) > 0.50
    assert float(cal[0, 0]) < 0.005

    m_hat = expected_self_credit_k3(cal)
    assert float(m_hat[10, 10]) >= float(cal[10, 10]) - 1e-5

    allowed = np.ones((h, w), dtype=bool)
    dots = dinkelbach_submodular_k3_allocate(
        cal,
        allowed,
        budget_cap=100,
        lambda_dti=0.20,
        min_sep_px=2.4,
    )
    # Even with budget_cap=100, Dinkelbach stops once marginal expected DTI gain <= 0!
    assert 2 <= int(dots.sum()) <= 6
    assert bool(dots[10, 10]) and bool(dots[26, 26])

    thin = pointwise_disc_thin(cal, allowed, budget=2, spacing_px=2.8)
    assert int(thin.sum()) == 2


def test_h86i_ksad_run_card_and_site_invariants() -> None:
    prereg_path = ROOT / "research/H86I_KSAD_PREREGISTRATION.json"
    card_path = ROOT / "docs/evidence/h86i-ksad-run-card.json"
    surf_path = ROOT / "docs/evidence/h86i-ksad-registry-surface.json"
    dots_path = ROOT / "docs/evidence/h86i-ksad-registry-final-dots.json"
    hyps_path = ROOT / "registry/h86i_ksad_hypotheses.json"

    for p in (prereg_path, card_path, surf_path, dots_path, hyps_path):
        assert p.is_file(), f"Missing required H86I-KSAD artifact: {p}"

    card = json.loads(card_path.read_text(encoding="utf-8"))
    surf = json.loads(surf_path.read_text(encoding="utf-8"))
    dots = json.loads(dots_path.read_text(encoding="utf-8"))
    hyps = json.loads(hyps_path.read_text(encoding="utf-8"))

    # Preregistration SHA binding
    expected_prereg_sha = hashlib.sha256(prereg_path.read_bytes()).hexdigest()
    assert card["preregistration"]["sha256"] == expected_prereg_sha
    assert card["preregistration"]["experiments_used"] == 3

    # Fail-closed negative posture & pre-serialization halt
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["raster_sha256"] is None
    assert card["validator_output"]["candidate_tif_serialized"] is False
    assert card["note_length"] == len(card["note"]) <= 140

    # Strict-LOQO holdout ordering & leakage canary
    scores = card["holdout_dti"]["pooled_summary"]["scores"]
    e1 = scores["E1_ksad_dinkelbach_submod"]["dti"]
    e2 = scores["E2_ksad_pointwise_d28_ablation"]["dti"]
    c1 = scores["C1_H86F_EWCS_strict_loqo_ctrl"]["dti"]
    assert e2 > e1 > c1 > 0.124
    gain_vs_ewcs = card["holdout_dti"]["strict_loqo_gain_e1_minus_ewcs_loqo"]
    assert gain_vs_ewcs["delta"] > 0.0
    assert gain_vs_ewcs["ci95"][0] > 0.0
    assert card["leakage_canary"]["max_discriminative_auc"] <= 0.90
    assert card["leakage_canary"]["any_flagged"] is False

    # Registry bindings
    reg = card["correlation_overlap_vs_registry"]
    assert reg["pre_placement_surface"]["compared"] == surf["registry_rasters_measured"] == 688
    assert reg["final_dots"]["compared"] == dots["registry_rasters_measured"] == 688
    assert reg["pre_placement_surface"]["rho_firings"] == 0
    assert len(reg["discrete_dot_overlap_firings_le_55k"]) == 3
    assert any("GEMSDOE80" in r["submission"] and r["forward_overlap_3px"] > 0.70 for r in reg["discrete_dot_overlap_firings_le_55k"])

    # 4 hypotheses with H86I-4 explicitly NOT_VIABLE_IN_SANDBOX_YET
    assert len(hyps["hypotheses"]) == 4
    h4 = next(h for h in hyps["hypotheses"] if h["id"] == "H86I-4")
    assert h4["status"] == "NOT_VIABLE_IN_SANDBOX_YET"

    # Executive summary surfaces H86I-KSAD clearly at the top
    exec_html = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
    assert 'id="h86i-ksad"' in exec_html
    assert "H86I-KSAD" in exec_html
    assert "DO NOT SUBMIT" in exec_html
