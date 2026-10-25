"""Unit and protocol-integrity tests for H86H-PSTD and the H86E-MMT R0 comparator fix."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems86_pstd.features import FEATURE_NAMES, compose_pstd_arms, compute_pstd_arrays  # noqa: E402
from scripts import run_h86e_mmt, run_h86h_pstd  # noqa: E402


def test_poisson_dislocation_detects_magnetite_destruction_on_density_hinge():
    h, w = 96, 96
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fp = np.ones((h, w), dtype=bool)
    fp[:4, :] = False
    fp[-4:, :] = False
    fp[:, :4] = False
    fp[:, -4:] = False

    # Steep N-S density boundary centered at col x0 = 48:
    # g_east = sech^2((x - 48)/5) => g_zz = -d(g_east)/dx has dipole hinge across x0
    u = (xx - 48.0) / 5.0
    g_east = (1.0 / np.cosh(u) ** 2).astype(np.float32)
    g_south = np.zeros((h, w), dtype=np.float32)
    true_gzz = (2.0 * np.sinh(u) / (5.0 * (np.cosh(u) ** 3))).astype(np.float32)

    zeros = np.zeros((h, w), dtype=np.float32)
    ones = np.ones((h, w), dtype=np.float32)

    # Case A: Unfaulted Poisson-consistent contact (M_z = 2.5 * true_gzz everywhere)
    mz_unfaulted = (2.5 * true_gzz).astype(np.float32)
    # Case B: Hydrothermal magnetite destruction along the fault conduit (x in [46..50])
    conduit = np.exp(-0.5 * ((xx - 48.0) / 1.8) ** 2).astype(np.float32)
    mz_faulted = (2.5 * true_gzz - 1.5 * conduit).astype(np.float32)

    planes_unfaulted = compute_pstd_arrays(
        b2_rtp=zeros,
        b3_tmi_hg=conduit,
        b7_shear=ones,
        b8_dilate=ones,
        b9_tmi_vg=mz_unfaulted,
        b11_grav_south=g_south,
        b17_cond=ones,
        b18_grav_east=g_east,
        b19_slope=ones * 0.2,
        footprint=fp,
        sigma_grav_px=2.0,
        sigma_flank_px=8.0,
    )
    planes_faulted = compute_pstd_arrays(
        b2_rtp=zeros,
        b3_tmi_hg=conduit,
        b7_shear=ones,
        b8_dilate=ones,
        b9_tmi_vg=mz_faulted,
        b11_grav_south=g_south,
        b17_cond=ones,
        b18_grav_east=g_east,
        b19_slope=ones * 0.2,
        footprint=fp,
        sigma_grav_px=2.0,
        sigma_flank_px=8.0,
    )
    arms_faulted = compose_pstd_arms(planes_faulted, fp)
    core_slice = (slice(24, 72), slice(47, 50))
    flank_slice = (slice(24, 72), slice(18, 28))

    assert float(planes_faulted["poisson_mag_destruction_residual"][core_slice].mean()) > float(
        planes_unfaulted["poisson_mag_destruction_residual"][core_slice].mean()
    )
    assert float(arms_faulted["E1_pstd_full"][core_slice].mean()) > float(
        arms_faulted["E1_pstd_full"][flank_slice].mean()
    ) + 0.25
    assert float(arms_faulted["E1_pstd_full"][core_slice].mean()) > float(
        arms_faulted["E3_pstd_inverted_polarity_control"][core_slice].mean()
    )


def test_nodata_sentinel_immunity_and_bounded_outputs():
    h, w = 64, 64
    yy, xx = np.mgrid[0:h, 0:w]
    fp = ((yy - 32) ** 2 + (xx - 32) ** 2) <= 22 ** 2
    rng = np.random.default_rng(42)

    def mk_band() -> np.ndarray:
        arr = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
        arr[~fp] = np.float32(-3.4028235e38)
        arr[0, 0] = np.nan
        return arr

    planes = compute_pstd_arrays(
        b2_rtp=mk_band(),
        b3_tmi_hg=np.abs(mk_band()),
        b7_shear=mk_band(),
        b8_dilate=mk_band(),
        b9_tmi_vg=mk_band(),
        b11_grav_south=mk_band(),
        b17_cond=mk_band(),
        b18_grav_east=mk_band(),
        b19_slope=np.abs(mk_band()),
        footprint=fp,
    )
    assert set(planes) == set(FEATURE_NAMES)
    arms = compose_pstd_arms(planes, fp)
    for name, arr in {**planes, **arms}.items():
        assert arr.dtype == np.float32, name
        assert np.isfinite(arr).all(), f"{name} contains non-finite values"
        assert np.all(arr[~fp] == 0.0), f"{name} nonzero outside footprint"
        assert float(arr[fp].min()) >= 0.0 and float(arr[fp].max()) <= 1.0, f"{name} out of [0, 1]"


def test_pstd_feature_module_never_loads_catalogue():
    import ast

    src_text = (ROOT / "src/gems86_pstd/features.py").read_text()
    tree = ast.parse(src_text)
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                doc_nodes.add(first.value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in doc_nodes:
            assert "existing_faults" not in node.value
            assert "catalogue" not in node.value
            assert "labels.tif" not in node.value
        if isinstance(node, ast.Attribute):
            assert node.attr != "catalogue"


def test_preregistration_and_run_card_contracts(tmp_path):
    prereg = run_h86h_pstd.require_preregistration()
    assert prereg["status"] == "frozen_before_implementation"
    assert prereg["candidate_hypotheses_count"] == 4
    assert len(prereg["experiment_arms"]) == 3

    prereg_doc = json.loads((ROOT / "research/H86H_PSTD_PREREGISTRATION.json").read_text())
    h4 = prereg_doc["candidate_hypotheses"][3]
    assert h4["id"] == "H86H-4_3DMT"
    assert h4["selected_for_validation"] is False
    assert h4["official_data_obtainability"].startswith("NOT_VIABLE_IN_SANDBOX_YET")

    bad_prereg = tmp_path / "bad.json"
    bad_md = tmp_path / "bad.md"
    bad_md.write_text("# test\n")
    bad_doc = dict(prereg_doc, status="retrospective")
    bad_prereg.write_text(json.dumps(bad_doc))
    with pytest.raises(ValueError, match="frozen_before_implementation"):
        run_h86h_pstd.require_preregistration(bad_prereg, bad_md)

    card = json.loads((ROOT / "docs/evidence/h86h-pstd-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["raster_sha256"] is None
    assert card["validator_output"]["candidate_tif_serialized"] is False
    reg = card["correlation_overlap_vs_registry"]
    assert reg["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert reg["final_dots_placed"] is False
    assert reg["surface_gate_pass"] is False
    assert reg["literal_gate_pass"] is False
    assert reg["rho_firings_over_0_90"] == 0
    assert reg["inventory_rasters_expected"] >= 687
    assert reg["valid_comparable_rasters"] == reg["inventory_rasters_expected"] - 2
    assert reg["dot_field_rasters"] + reg["continuous_surface_rasters"] == reg["valid_comparable_rasters"]
    assert isinstance(reg["candidate_decoded_sha256"], str) and len(reg["candidate_decoded_sha256"]) == 64
    e1 = card["holdout_evaluation"]["arms"]["E1_pstd_full"]
    assert e1["full_footprint_budget_dots"] == 37654
    assert e1["total_emitted_across_4_quadrants"] == 35392
    assert card["leakage_canary"]["all_pass"] is True
    assert card["leakage_canary"]["worst_discriminative_auc"] <= 0.90
    assert card["budget"]["experiments_run"] == 3
    assert card["budget"]["submission_slots_used"] == 0
    assert len(card["submission_note"]) <= 140
    assert (
        card["holdout_evaluation"]["fold_fair_r0_control"]["source_sha256"]
        == "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"
    )

    surf = json.loads((ROOT / "docs/evidence/h86h-pstd-registry-surface.json").read_text())
    assert surf["schema"] == "gems86.registry-candidate.v2"
    assert surf["mode"] == "surface"
    assert not surf["candidate"].startswith("/")
    assert surf["surface_gate_pass"] is False
    assert surf["literal_gate_pass"] is False
    assert surf["inventory_rasters_missing"] == []
    assert surf["registry_rasters_expected"] >= 687
    assert surf["registry_rasters_measured"] == surf["registry_rasters_expected"] - 2
    assert len(surf["errors"]) == 2


def test_mmt_holdout_binary_control_never_pads_zero_ties():
    fp = np.ones((40, 40), dtype=bool)
    vis = np.zeros((40, 40), dtype=bool)
    vis[10, 10] = True
    truth = np.zeros((40, 40), dtype=bool)
    truth[10, 10] = True
    truth[30, 30] = True
    fold = {
        "name": "Q0",
        "region": fp,
        "visible": vis,
        "masked_known": vis,
        "truth": truth,
    }
    sparse_dots = np.zeros((40, 40), dtype=bool)
    sparse_dots[10, 11] = True  # within 2 px of visible fault -> must be pruned
    sparse_dots[30, 30] = True  # far from visible fault -> must survive
    sparse_dots[25, 25] = True  # far from visible fault -> must survive

    _, per_fold, example = run_h86e_mmt.holdout_binary_control(sparse_dots, [fold], fp, collar_px=2.0)
    assert int(example.sum()) == 2
    assert per_fold["Q0"]["emitted"] == 2
    assert not bool(example[10, 11])


def test_pstd_rank01_tie_invariance():
    from gems86_pstd.features import _rank01

    fp = np.ones((20, 20), dtype=bool)
    arr = np.zeros((20, 20), dtype=np.float32)
    arr[2, 5] = 10.0
    arr[18, 15] = 20.0
    ranked = _rank01(arr, fp)
    zero_mask = fp & (arr == 0.0)
    assert np.all(ranked[zero_mask] == 0.0)
    assert float(ranked[18, 15]) == pytest.approx(1.0)

