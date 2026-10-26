"""Unit and artifact-integrity tests for Lane H86P-TCWB (2026-10-26)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from src.gems86_tcwb import (
    ABLATION_LOCAL_NAMES,
    TCWB_ELASTIC_NAMES,
    TCWB_STATIC_NAMES,
    aitchison_clr_radiometric_jacobian,
    claycap_lateral_fault_seal_termination,
    downslope_tc_wash_asymmetry,
    gravity_signed_basement_hinge_kink,
    seismicity_conditioned_dilatancy_gate,
)
from src.gems86_tcwb.model import (
    _eroded_out_of_fold_domain,
    calibrate_global_sparse_posterior,
    fuse_radial_cover_tcwb,
)

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_downslope_tc_wash_asymmetry_one_sided_polarity():
    h, w = 64, 64
    valid = np.ones((h, w), dtype=bool)
    _, c = np.meshgrid(
        np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij"
    )
    elev = 1600.0 - 9.0 * c
    tc_fault = np.where(c < 32, 130.0, 48.0).astype(np.float32)
    tc_reversed = np.where(c < 32, 48.0, 130.0).astype(np.float32)

    asym_pos, cont_pos = downslope_tc_wash_asymmetry(tc_fault, elev, valid)
    asym_rev, cont_rev = downslope_tc_wash_asymmetry(tc_reversed, elev, valid)

    assert float(asym_pos[:, 30:34].max()) > 0.5
    assert float(asym_rev[:, 30:34].max()) < 1e-5
    assert np.allclose(cont_pos[:, 30:34], cont_rev[:, 30:34], atol=1e-4)


def test_gravity_signed_basement_hinge_kink_suppresses_discordant_mimic():
    h, w = 64, 64
    valid = np.ones((h, w), dtype=bool)
    _, c = np.meshgrid(
        np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij"
    )
    zb = np.where(c < 28, 120.0, 120.0 + 38.0 * (c - 28.0)).astype(np.float32)
    b11 = np.zeros_like(zb)
    b18_concord = np.full_like(zb, -2.5)  # Bouguer gravity drops into deeper basin
    b18_discord = np.full_like(zb, +2.5)  # Discordant mimic (mafic sill / pluton)

    k_ok, nr, nc = gravity_signed_basement_hinge_kink(zb, b11, b18_concord, valid)
    k_bad, _, _ = gravity_signed_basement_hinge_kink(zb, b11, b18_discord, valid)

    assert float(k_ok[:, 26:31].max()) > 1.0
    assert float(k_bad.max()) == 0.0
    assert float(nc[:, 30].mean()) > 0.9


def test_claycap_lateral_fault_seal_one_sided_hanging_wall():
    h, w = 64, 64
    valid = np.ones((h, w), dtype=bool)
    _, c = np.meshgrid(
        np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij"
    )
    nr = np.zeros((h, w), dtype=np.float32)
    nc = np.ones((h, w), dtype=np.float32)
    demag = np.ones((h, w), dtype=np.float32)
    cond_hw = np.where(c >= 30, 90.0, 2.0).astype(np.float32)
    cond_fw = np.where(c < 30, 90.0, 2.0).astype(np.float32)

    seal_hw = claycap_lateral_fault_seal_termination(cond_hw, nr, nc, demag, valid)
    seal_fw = claycap_lateral_fault_seal_termination(cond_fw, nr, nc, demag, valid)
    assert float(seal_hw[:, 28:33].max()) > 2.5 * float(seal_fw[:, 28:33].max())


def test_seismicity_conditioned_dilatancy_gate_band10_distance_inversion():
    h, w = 48, 48
    valid = np.ones((h, w), dtype=bool)
    r, c = np.meshgrid(
        np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij"
    )
    b7_dil = np.where((c >= 20) & (c <= 28), 35.0, -5.0).astype(np.float32)
    b8_strain = np.where((c >= 20) & (c <= 28), 55.0, 5.0).astype(np.float32)
    b10_dist = (np.hypot(r - 24.0, c - 24.0) * 500.0 + 100.0).astype(np.float32)
    b16_int = np.exp(-((r - 24.0) ** 2 + (c - 24.0) ** 2) / 36.0).astype(np.float32)

    gate = seismicity_conditioned_dilatancy_gate(
        b7_dil, b8_strain, b10_dist, b16_int, valid
    )
    assert float(gate[22:27, 22:27].mean()) > 4.0 * float(gate[0:8, 22:27].mean())
    assert float(gate[22:27, 22:27].mean()) > 4.0 * float(gate[22:27, 0:8].mean())


def test_aitchison_clr_radiometric_jacobian_scale_invariance():
    rng = np.random.default_rng(86)
    h, w = 48, 48
    valid = np.ones((h, w), dtype=bool)
    tc = rng.uniform(30.0, 150.0, size=(h, w)).astype(np.float32)
    k = rng.uniform(10.0, 90.0, size=(h, w)).astype(np.float32)
    th = rng.uniform(15.0, 80.0, size=(h, w)).astype(np.float32)
    u = rng.uniform(8.0, 60.0, size=(h, w)).astype(np.float32)

    j_base = aitchison_clr_radiometric_jacobian(tc, k, th, u, valid)
    j_scaled = aitchison_clr_radiometric_jacobian(
        4.25 * tc, 4.25 * k, 4.25 * th, 4.25 * u, valid
    )
    assert float(np.max(np.abs(j_base - j_scaled))) < 1e-4


def test_eroded_loqo_domain_and_elkan_bayes_monotonicity():
    h, w = 64, 64
    valid = np.ones((h, w), dtype=bool)
    r, c = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    eval_region = (r < 32) & (c < 32)
    tr_dom = _eroded_out_of_fold_domain(eval_region, valid, erode_px=12)
    assert float(distance_transform_edt(~eval_region)[tr_dom].min()) > 12.0

    p_raw = np.linspace(0.05, 0.95, h * w, dtype=np.float32).reshape(h, w)
    p_cal = calibrate_global_sparse_posterior(p_raw, valid)
    assert np.all(np.diff(p_cal.ravel()) >= 0.0) and float(p_cal.ravel()[-1]) > float(p_cal.ravel()[0])
    assert float(p_cal.min()) > 0.0 and float(p_cal.max()) < 1.0

    cov = np.full((h, w), 0.8, dtype=np.float32)
    dvis = np.full((h, w), 20.0, dtype=np.float32)
    fused = fuse_radial_cover_tcwb(p_cal, p_cal, cov, dvis, valid)
    assert float(fused.min()) >= 0.0 and float(fused.max()) <= 1.0
    assert np.all(fused >= 0.77 * p_cal - 1e-6)


def test_h86p_tcwb_preregistration_run_card_and_artifact_invariants():
    hyp = json.loads((ROOT / "registry/h86p_hypotheses_20261026.json").read_text())
    assert len(hyp["hypotheses"]) == 4
    assert hyp["lane_assignment"] == "H86P-TCWB"

    prereg = json.loads((ROOT / "research/H86P_TCWB_PREREGISTRATION.json").read_text())
    assert prereg["static_features"] == list(TCWB_STATIC_NAMES)
    assert prereg["fold_visible_elastic_features"] == list(TCWB_ELASTIC_NAMES)
    assert prereg["ablation_control_features"] == list(ABLATION_LOCAL_NAMES)
    assert len(prereg["arms"]) == 3

    card = json.loads((ROOT / "docs/evidence/h86p-tcwb-run-card.json").read_text())
    assert card["lane_id"] == "H86P-TCWB"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert len(card["note"]) <= 140

    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["candidate"]["dti"] > 0.17
    assert h["paired_delta_vs_best_preregistered_control"]["ci95"][0] > 0.0
    assert h["leakage_canary_summary"]["any_leakage_flag"] is False
    assert h["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90

    reg = card["correlation_overlap_vs_registry"]
    assert reg["surface_preplacement"]["worst_spearman_full_footprint"] <= 0.90
    assert (
        reg["full_registry_informative_dot_field_audit"][
            "discrete_le_90k_firings_over_0p70"
        ]
        == 0
    )

    tif = ROOT / card["submission_file"]
    zip_path = ROOT / card["submission_zip"]
    assert tif.is_file() and _sha256(tif) == card["raster_sha256"]
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif.name]
        assert zf.read(tif.name) == tif.read_bytes()
    with rasterio.open(tif) as ds:
        assert ds.count == 1 and ds.shape == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        arr = ds.read(1)
    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert int((arr > 0.5).sum()) == 37654
