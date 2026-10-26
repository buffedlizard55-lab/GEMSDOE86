"""Regression tests for the H86I-RLMS lane, physics operators, allocator, and run-card gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts import run_h86i_rlms  # noqa: E402
from scripts.audit_release import strict_json  # noqa: E402
from src.gems86.io import BANDS  # noqa: E402
from src.gems86_rlms.allocator import (  # noqa: E402
    bayes_prior_calibrate,
    disc_thin,
    submodular_kernel_allocate,
)
from src.gems86_rlms.features import (  # noqa: E402
    ALL_STATIC_NAMES,
    CONTINUATION_NAMES,
    EXTERNAL_STATIC_NAMES,
    NATIVE_STATIC_NAMES,
    _sample_hw_offset,
    _structure_nematic,
    compute_continuation_fields,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_h86i_hypotheses_register_and_preregistration_are_frozen_and_valid():
    hyp = strict_json(ROOT / "registry/h86i_rlms_hypotheses.json")
    assert hyp["lane_assignment"] == "H86I-RLMS"
    assert [h["rank"] for h in hyp["hypotheses"]] == [1, 2, 3, 4]
    assert [h["id"] for h in hyp["hypotheses"]] == [
        "H86I-RLMS",
        "H86I-CHTD",
        "H86I-PBLS",
        "H86I-SGBD",
    ]
    for h in hyp["hypotheses"]:
        assert h["physical_signature"] and h["why_blind_not_mapped"]
        assert h["non_fault_mimic"] and h["falsifier"] and h["novelty"]
        for layer in h["layers"]:
            assert BANDS[layer["band"]] == layer["name"]

    prereg_path = ROOT / "research/H86I_RLMS_PREREGISTRATION.json"
    hyp_path = ROOT / "registry/h86i_rlms_hypotheses.json"
    card = strict_json(ROOT / "docs/evidence/h86i-rlms-run-card.json")
    assert _sha256(prereg_path) == "f53b80b3130836d3e35d7dcb40e3201fcb0409cc32512e97fca1ce01a9cb7a7e"
    assert card["preregistration"]["preregistration_sha256"] == _sha256(prereg_path)
    assert card["preregistration"]["hypothesis_queue_sha256"] == _sha256(hyp_path)


def test_spin2_nematic_director_sign_invariance_and_orientation():
    h, w = 64, 64
    fp = np.ones((h, w), dtype=bool)
    yy, xx = np.indices((h, w), dtype=np.float32)
    # N-S striking step (gradient purely along +x -> strike along y: psi = pi/2 -> cos 2psi = -1)
    step_pos = np.tanh((xx - 32.0) / 2.0).astype(np.float32)
    step_neg = (-step_pos).astype(np.float32)
    c2_p, s2_p, wt_p = _structure_nematic(step_pos, fp)
    c2_n, s2_n, wt_n = _structure_nematic(step_neg, fp)
    np.testing.assert_allclose(c2_p, c2_n, atol=1e-6)
    np.testing.assert_allclose(s2_p, s2_n, atol=1e-6)
    np.testing.assert_allclose(wt_p, wt_n, atol=1e-6)
    assert float(c2_p[32, 32]) < -0.95
    assert abs(float(s2_p[32, 32])) < 1e-4

    # E-W striking step (gradient purely along +y -> strike along x: psi = 0 -> cos 2psi = +1)
    ew_step = np.tanh((yy - 32.0) / 2.0).astype(np.float32)
    c2_ew, s2_ew, _ = _structure_nematic(ew_step, fp)
    assert float(c2_ew[32, 32]) > 0.95
    assert abs(float(s2_ew[32, 32])) < 1e-4


def test_updip_hanging_wall_projection_shifts_hanging_wall_peak_onto_footwall_trace():
    h, w = 40, 50
    yy, xx = np.indices((h, w), dtype=np.float32)
    # Footwall trace at x=18, hanging-wall gravity gradient peak displaced +7 px east at x=25
    plane = np.exp(-0.5 * ((xx - 25.0) / 1.5) ** 2).astype(np.float32)
    ny = np.zeros((h, w), dtype=np.float32)
    nx = np.ones((h, w), dtype=np.float32)  # +n_HW points east (+x)
    projected = _sample_hw_offset(plane, ny, nx, offset_px=7.0)
    assert float(projected[20, 18]) > 0.99
    assert float(plane[20, 18]) < 1e-4
    assert np.isfinite(projected).all()


def test_continuation_fields_depend_only_on_visible_faults_and_nematic_directors():
    assert len(NATIVE_STATIC_NAMES) == 25
    assert len(EXTERNAL_STATIC_NAMES) == 8
    assert len(ALL_STATIC_NAMES) == 33
    assert len(CONTINUATION_NAMES) == 6
    h, w = 48, 48
    fp = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    vis[20, 8:20] = True
    vis[28, 28:40] = True  # right-stepping relay across rows 20..28, cols 20..28
    c2 = np.ones((h, w), dtype=np.float32)
    s2 = np.zeros((h, w), dtype=np.float32)
    cont = compute_continuation_fields(vis, fp, c2, s2)
    assert set(CONTINUATION_NAMES).issubset(cont.keys())
    for k in CONTINUATION_NAMES:
        assert cont[k].shape == (h, w)
        assert np.isfinite(cont[k]).all()
    # Relay interior (row 24, col 24, d_vis > 5 px) receives elevated wing-crack + stepover continuation vs far corner
    assert float(cont["wing_crack_lobe"][24, 24]) > float(cont["wing_crack_lobe"][2, 45])
    assert float(cont["stepover_bridge"][24, 24]) > float(cont["stepover_bridge"][2, 45])


def test_submodular_allocator_and_disc_thin_invariants():
    rng = np.random.default_rng(42)
    h, w = 40, 40
    fp = np.ones((h, w), dtype=bool)
    raw = rng.uniform(0.01, 0.99, size=(h, w)).astype(np.float32)
    cal = bayes_prior_calibrate(raw, pi_train=0.25, pi_target=0.01, footprint=fp)
    assert cal.shape == (h, w)
    assert float(cal.min()) >= 0.0 and float(cal.max()) <= 1.0
    assert float(cal.mean()) < float(raw.mean())

    allowed = np.ones((h, w), dtype=bool)
    allowed[:4, :] = False  # simulate masked catalogue / outside footprint
    dots_sub = submodular_kernel_allocate(cal, allowed, budget=35, eta=0.042, candidate_cap=500)
    assert dots_sub.dtype == bool and dots_sub.shape == (h, w)
    assert int(dots_sub.sum()) == 35
    assert not (dots_sub & ~allowed).any()

    dots_disc = disc_thin(cal, allowed, budget=35, spacing=2.8)
    assert dots_disc.dtype == bool and dots_disc.shape == (h, w)
    assert not (dots_disc & ~allowed).any()
    ys, xs = np.nonzero(dots_disc)
    if ys.size > 1:
        dy = ys[:, None] - ys[None, :]
        dx = xs[:, None] - xs[None, :]
        d2 = dy * dy + dx * dx + np.eye(ys.size) * 100.0
        assert float(d2.min()) >= 2.8 * 2.8 - 1e-6


def test_h86i_rlms_run_card_artifact_and_registry_evidence_are_honest_and_bound():
    card = strict_json(ROOT / "docs/evidence/h86i-rlms-run-card.json")
    assert card["lane"] == "H86I-RLMS"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert 1 <= card["note_chars"] == len(card["note"]) <= 140

    tif_path = ROOT / card["submission_file"]
    zip_path = tif_path.with_suffix(".zip")
    receipt_path = tif_path.with_suffix(".json")
    assert tif_path.is_file() and zip_path.is_file() and receipt_path.is_file()
    assert _sha256(tif_path) == card["raster_sha256"] == (
        "ad4474b4d78ed3e8eaf5114fc63e3d858afcc0c016f7932baaaca06e99247b2d"
    )
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    val = card["validator_output"]
    assert val["all_checks_passed"] is True
    assert val["no_nan_inside_footprint"] is True
    assert val["values_in_0_1"] is True
    assert val["crs_shape_transform_match"] is True
    assert val["checks"]["zero_dots_on_mapped_catalogue"] is True
    assert val["positive_pixels"] == 37_654
    assert val["min"] == 0.0 and val["max"] == 1.0

    h = card["holdout_dti"]
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11_321
    # External 3DEP + GeoDAWN ablation E1 - E2 is strictly positive in paired CI and all 4 folds
    d_ext = h["paired_delta_vs_native19_ablation"]
    assert d_ext["delta"] > 0.02 and d_ext["ci95"][0] > 0.01
    for fold_id in ("NW", "NE", "SW", "SE"):
        assert (
            h["per_fold"]["E1_rlms_full_submodular"][fold_id]["dti"]
            > h["per_fold"]["E2_rlms_native19_only_ablation"][fold_id]["dti"]
        ), fold_id
    # Overall E1 trails reproduced H86F-EWCS -> negative verdict enforced
    assert h["candidate"]["dti"] < h["H86F_EWCS_reproduced"]["dti"]
    assert h["beats_same_split_ewcs_paired_ci"] is False

    # Leakage canary passes across all 40 features
    lc = h["leakage_canary_summary"]
    assert lc["features_tested"] == 40
    assert lc["any_leakage_flag"] is False
    assert lc["max_discriminative_auc"] <= 0.90

    # Dual-phase registry checks + discrete <=100k-dot diagnostic + 691-file post-build review
    reg = card["correlation_overlap_vs_registry"]
    assert reg["surface_preplacement"]["rho_firings_over_0p90"] == 0
    assert reg["surface_preplacement"]["worst_spearman_full_footprint"] <= 0.90
    info = reg["informative_discrete_dot_diagnostic"]
    assert info["discrete_rasters_checked"] == 469
    assert info["firings_over_0p70"] == 0
    assert info["worst_discrete_overlap"] <= 0.70
    assert 0.35 < info["overlap_vs_GEMSDOE32_h33"] < 0.45
    assert 0.25 < info["overlap_vs_H86F_EWCS"] < 0.35
    assert reg["final_dots"]["literal_gate_pass"] is False

    post_grid = strict_json(ROOT / "docs/evidence/registry-input-grid-review-6bbd9586.json")
    assert post_grid["indexed_rasters_expected"] == post_grid["byte_verified_rasters"] == 697
    assert post_grid["grid_compatible_rasters"] == 695
    assert post_grid["grid_incompatible_or_invalid_rasters"] == 2
    assert post_grid["uniqueness_clearance"] is False


def test_run_h86i_rlms_cli_stops_at_protocol_preflight(monkeypatch):
    # Pinned grid/witness live under data/bridge/ or data/ (witness gitignored, restored
    # per-session). Present -> protocol STOP; absent inputs fail closed, never pass.
    witness_present = (
        (ROOT / "data/bridge/registry/dense-witness.tif").is_file()
        or (ROOT / "data/registry/dense-witness.tif").is_file()
    )
    pinned_present = (
        (ROOT / "data/bridge/sample_submission.tif").is_file()
        and (ROOT / "data/bridge/existing_faults.tif").is_file()
        and witness_present
    )
    if pinned_present:
        with pytest.raises(RuntimeError, match="STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
            run_h86i_rlms.main([])
    else:
        with pytest.raises(FileNotFoundError):
            run_h86i_rlms.main([])
    called = []

    def fake_stop():
        called.append(True)
        raise RuntimeError("STOP_LITERAL_OVERLAP_UNSATISFIABLE")

    from scripts import protocol_preflight

    monkeypatch.setattr(protocol_preflight, "require_feasible", fake_stop)
    with pytest.raises(RuntimeError, match="STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
        run_h86i_rlms.main([])
    assert called == [True]
