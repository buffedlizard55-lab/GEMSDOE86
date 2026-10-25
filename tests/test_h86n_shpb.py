"""End-to-end verification tests for H86N-SHPB (Steerable Odd-Step / Even-Dike Pullback + Kostrov-Riedel + Elkan Bayes LOQO)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
for _rel in ("", "src", "vendor", "scripts"):
    _p = str(ROOT / _rel) if _rel else str(ROOT)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems86_shpb import ABLATION_LOCAL_NAMES, SHPB_ELASTIC_NAMES, SHPB_STATIC_NAMES
from gems86_shpb.features import (
    seismic_geodetic_lineation_alignment,
    steerable_odd_step_minus_even_dike,
)
from gems86_shpb.model import calibrate_global_sparse_posterior


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_h86n_preregistration_and_hypothesis_queue() -> None:
    hyp_path = ROOT / "registry/h86n_hypotheses.json"
    prereg_path = ROOT / "research/H86N_SHPB_PREREGISTRATION.json"
    md_path = ROOT / "research/H86N_SHPB_PREREGISTRATION.md"

    assert hyp_path.is_file()
    assert prereg_path.is_file()
    assert md_path.is_file()

    hyps = json.loads(hyp_path.read_text(encoding="utf-8"))
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))

    assert hyps["lane_series"] == "H86N"
    assert len(hyps["hypotheses"]) == 4
    ids = [h["id"] for h in hyps["hypotheses"]]
    assert ids[0] == "H86N-SHPB"
    assert hyps["hypotheses"][0]["status"] == "SELECTED_FOR_VALIDATION"
    for h in hyps["hypotheses"]:
        assert h["layers"]
        assert h["physical_signature"]
        assert h["why_off_catalogue"]
        assert h["differs_from_repo"]
        assert h["non_fault_mimic"]

    assert prereg["lane_id"] == "H86N-SHPB"
    assert prereg["budget"]["max_experiments"] == 3
    assert len(prereg["arms"]) == 3
    assert list(SHPB_STATIC_NAMES) == prereg["static_features"]
    assert list(SHPB_ELASTIC_NAMES) == prereg["fold_visible_elastic_features"]
    assert list(ABLATION_LOCAL_NAMES) == prereg["ablation_control_features"]


def test_steerable_odd_step_vs_even_dike_distinguishes_step_from_ridge() -> None:
    """Verify A_step is positive on an odd-symmetric fault step and negative on an even-symmetric dike ridge."""
    ny, nx = 64, 64
    fp = np.ones((ny, nx), dtype=bool)
    y, x = np.mgrid[0:ny, 0:nx].astype(np.float32)

    # 1. Odd-symmetric fault step at x = 32: tanh((x - 32)/2.5)
    step_field = np.tanh((x - 32.0) / 2.5).astype(np.float32)
    fx_step = (1.0 / np.cosh((x - 32.0) / 2.5) ** 2 / 2.5).astype(np.float32)
    fy_step = np.zeros_like(step_field)
    a_step, _ = steerable_odd_step_minus_even_dike(
        step_field, fp, gx_override=fx_step, gy_override=fy_step, sigmas=(2.0,)
    )

    # 2. Even-symmetric dike ridge at x = 32: exp(-((x - 32)/2.5)^2)
    ridge_field = np.exp(-(((x - 32.0) / 2.5) ** 2)).astype(np.float32)
    fx_ridge = (-2.0 * (x - 32.0) / (2.5**2) * ridge_field).astype(np.float32)
    fy_ridge = np.zeros_like(ridge_field)
    a_ridge, _ = steerable_odd_step_minus_even_dike(
        ridge_field, fp, gx_override=fx_ridge, gy_override=fy_ridge, sigmas=(2.0,)
    )

    # At the centerline x = 32, the odd step must score strictly positive and the even ridge negative
    step_center = float(np.mean(a_step[16:48, 31:33]))
    ridge_center = float(np.mean(a_ridge[16:48, 31:33]))
    assert step_center > 0.25
    assert ridge_center < 0.0
    assert step_center - ridge_center > 0.50


def test_earthquake_lineation_kostrov_coupling_and_elkan_bayes() -> None:
    ny, nx = 48, 48
    fp = np.ones((ny, nx), dtype=bool)
    y, x = np.mgrid[0:ny, 0:nx].astype(np.float32)

    # Create a N-S linear seismic corridor at x = 24
    deq = np.exp(-(((x - 24.0) / 2.0) ** 2)).astype(np.float32)
    ieq = deq.copy()
    shr = np.ones((ny, nx), dtype=np.float32) * 0.5
    dil = np.ones((ny, nx), dtype=np.float32) * 0.5
    inv2 = np.ones((ny, nx), dtype=np.float32) * 0.5

    align, coupled = seismic_geodetic_lineation_alignment(deq, ieq, shr, dil, inv2, fp)
    assert align.shape == (ny, nx)
    assert coupled.shape == (ny, nx)
    assert np.isfinite(align).all()
    assert np.isfinite(coupled).all()
    # Linear corridor should exceed diffuse background
    assert float(np.mean(align[12:36, 23:26])) > float(np.mean(align[12:36, 5:12]))

    # Verify calibrate_global_sparse_posterior preserves strict ordering on valid pixels
    rng = np.random.default_rng(86)
    p_sub = rng.uniform(0.01, 0.99, size=(ny, nx)).astype(np.float32)
    p_cal = calibrate_global_sparse_posterior(p_sub, fp)
    assert p_cal.shape == p_sub.shape
    assert np.all((p_cal > 0.0) & (p_cal < 1.0))
    order_sub = np.argsort(p_sub.ravel())
    order_cal = np.argsort(p_cal.ravel())
    assert np.array_equal(order_sub, order_cal)


def test_h86n_shpb_run_card_and_artifact_integrity() -> None:
    rc_path = ROOT / "docs/evidence/h86n-shpb-run-card.json"
    assert rc_path.is_file()
    rc = json.loads(rc_path.read_text(encoding="utf-8"))

    assert rc["lane_id"] == "H86N-SHPB"
    assert rc["verdict"] == "negative"
    assert rc["decision"] == "DO NOT SUBMIT"
    assert rc["safe_to_submit"] is False
    assert rc["approved_for_weekly_slot"] is False
    assert rc["budget_compliance"]["experiments_run"] == 3
    assert rc["budget_compliance"]["weekly_submission_slots_used"] == 0

    # Leakage canary checks
    lc = rc["leakage_canary"]
    assert lc["evidence_class"] == "LEAKAGE-CANARY"
    assert lc["any_flagged"] is False
    assert lc["max_discriminative_auc"] <= 0.90

    # Holdout DTI checks
    h = rc["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["candidate"]["dti"] > 0.165
    assert h["ablation_control_arm_E3"]["dti"] > 0.130
    assert h["paired_delta_vs_ablation_E3"]["delta"] > 0.025
    assert h["paired_delta_vs_ablation_E3"]["ci95"][0] > 0.010
    assert h["paired_delta_vs_R0_D28_visible_collar"]["ci95"][0] > 0.10
    assert h["paired_delta_vs_R0_GEMSDOE25_fold_fair"]["ci95"][0] > 0.05

    # SGMC proxy checks
    sgmc = rc["sgmc_off_catalogue_proxy"]
    assert sgmc["evidence_class"] == "SGMC-PROXY-DTI"
    assert sgmc["off_catalogue_positive_pixels"] == 62122
    e1_sgmc = sgmc["scores"]["E1_shpb_coupled_dinkelbach_celf"]["dti"]
    h33_sgmc = sgmc["scores"]["H33_3px_collar"]["dti"]
    d28_sgmc = sgmc["scores"]["R0_D28_3px_collar"]["dti"]
    assert e1_sgmc > 0.100
    assert e1_sgmc > h33_sgmc
    assert e1_sgmc > d28_sgmc

    # Registry uniqueness checks
    reg = rc["correlation_overlap_vs_registry"]
    assert reg["pre_placement_surface"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["pre_placement_surface"]["rho_firings_over_0p90"] == 0
    inf = reg["informative_dot_field_audit"]
    assert inf["discrete_le_90k_firings_over_0p70"] == 0
    assert inf["worst_discrete_le_90k_overlap_3px"] <= 0.70

    # Artifact & [0, 1] portal range checks
    tif_path = ROOT / rc["artifact"]["tif"]
    zip_path = ROOT / rc["artifact"]["zip"]
    rec_path = ROOT / rc["artifact"]["receipt"]
    assert tif_path.is_file()
    assert zip_path.is_file()
    assert rec_path.is_file()

    assert _sha256(tif_path) == rc["raster_sha256"]
    assert _sha256(zip_path) == rc["artifact"]["zip_sha256"]
    assert len(rc["submission_note"]) <= 140

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    with rasterio.open(tif_path) as src:
        assert src.count == 1
        assert src.dtypes[0] == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.nodata is None
        arr = src.read(1)
        assert not np.isnan(arr).any()
        assert not np.isinf(arr).any()
        assert float(arr.min()) == 0.0
        assert float(arr.max()) == 1.0
        assert int((arr > 0.5).sum()) == 37654
