"""Unit, physics-identity, and fail-closed governance tests for Session H86F-EWCS."""
from __future__ import annotations

import ast
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

from gems86_ewcs.features import (  # noqa: E402
    ELASTIC_COUPLED_NAMES,
    STATIC_FEATURE_NAMES,
    compute_elastic_fields,
    compute_laplace_gzz_and_curl,
)
from scripts import run_h86f_ewcs  # noqa: E402


def test_laplace_gzz_sign_and_conservative_zero_curl_identity():
    """Verify g_zz = -(d_col B18 + d_row B11) and zero curl on exact quadratic potential."""
    rows, cols = np.indices((80, 90), dtype=np.float32)
    # Potential g(row, col) = 1.5 * col^2 - 0.5 * row^2 + 0.7 * row * col
    # d^2g/dx_east^2 = d^2g/dcol^2 = +3.0
    # d^2g/dy_north^2 = d^2g/drow_south^2 = -1.0
    # Horizontal Laplacian = +2.0 => harmonic g_zz = -2.0; curl = 0.0
    b18_east = 3.0 * cols + 0.7 * rows     # +dg/dcol
    b11_south = -1.0 * rows + 0.7 * cols   # +dg/drow_south
    g_zz, curl_defect = compute_laplace_gzz_and_curl(b18_east, b11_south, sigma=2.0)
    interior = slice(12, -12), slice(12, -12)
    # Discrete Gaussian derivative kernel with truncate=4.0 has ~7e-4 truncation error at sigma=2
    np.testing.assert_allclose(g_zz[interior], -2.0, atol=2e-3)
    np.testing.assert_allclose(curl_defect[interior], 0.0, atol=2e-3)


def test_static_features_ast_never_touches_fault_labels():
    """AST guard: executable code in build_static_features must never reference fault labels."""
    src = (ROOT / "src/gems86_ewcs/features.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    func = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "build_static_features"
    )
    # Exclude leading docstring expression if present
    body_stmts = func.body[1:] if (
        func.body
        and isinstance(func.body[0], ast.Expr)
        and isinstance(func.body[0].value, ast.Constant)
    ) else func.body
    forbidden = {"existing_faults", "labels.tif", "qfaults", "dist_known_fault_px"}
    for stmt in body_stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                for bad in forbidden:
                    assert bad not in low, f"Forbidden token {bad!r} in literal {node.value!r}"


def test_pollard_segall_elastic_fields_distinguish_opposing_stepover_and_broadside():
    """Opposing tips create a stronger stepover bridge between tips than behind segments."""
    fp = np.ones((120, 140), dtype=bool)
    vis = np.zeros((120, 140), dtype=bool)
    # Two horizontal segments stepping across a central relay gap (cols 50..88)
    vis[54, 15:52] = True
    vis[66, 86:125] = True
    fields = compute_elastic_fields(vis, fp)
    assert set(ELASTIC_COUPLED_NAMES).issubset(fields.keys())
    for arr in fields.values():
        assert np.isfinite(arr).all()
    # Relay interior (row 60, col 69) must exceed far corner background (row 10, col 10)
    assert float(fields["stepover_bridge"][60, 69]) > float(fields["stepover_bridge"][10, 10])
    assert float(fields["wing_crack_lobe"][46, 62]) > float(fields["wing_crack_lobe"][54, 30])
    # Mid-segment broadside flank (row 45, col 33, 9 px perpendicular to interior col 33)
    assert float(fields["broadside_stress_shadow"][45, 33]) > float(fields["broadside_stress_shadow"][60, 69])


def test_h86f_preregistration_and_hypothesis_queue_are_valid():
    queue = json.loads((ROOT / "registry/h86f_hypotheses.json").read_text(encoding="utf-8"))
    hyps = queue["hypotheses"]
    assert 3 <= len(hyps) <= 5
    ids = [h["id"] for h in hyps]
    assert ids == ["H86F-EWCS", "H86F-GDFB", "H86F-PFSB", "H86F-USGS-3DGF"]
    ext = [h for h in hyps if h["external_data_required"]]
    assert len(ext) == 1
    assert ext[0]["obtainability"].startswith("NOT_VERIFIED_THIS_SESSION")
    assert ext[0]["data_readiness"].startswith("NOT_VIABLE_YET")

    prereg = run_h86f_ewcs.require_preregistration()
    assert [a["id"] for a in prereg["arms"]] == [
        "E1_ewcs_coupled_pu",
        "E2_ewcs_cover_blind_pu",
        "E3_ewcs_isotropic_tip_ablation",
    ]
    assert prereg["budget"]["max_experiments"] == 3


def test_h86f_ewcs_run_card_and_v2_surface_receipt_are_fail_closed():
    card = json.loads((ROOT / "docs/evidence/h86f-ewcs-run-card.json").read_text(encoding="utf-8"))
    assert card["lane"] == "H86F-EWCS"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["new_candidate_generated"] is True
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert isinstance(card["raster_sha256"], str) and len(card["raster_sha256"]) == 64
    assert isinstance(card["submission_name"], str) and 1 <= len(card["submission_name"]) <= 140
    assert 1 <= len(card["note"]) <= 140
    tif_path = ROOT / card["submission_file"]
    assert tif_path.is_file()
    import hashlib
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == card["raster_sha256"]
    assert card["validator_output"]["all_checks_passed"] is True
    assert card["validator_output"]["values_in_0_1"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True

    hd = card["holdout_dti"]
    assert hd["evidence_class"] == "HOLDOUT-DTI"
    assert hd["evaluator_version"] == "gems57-pooled-hide-v2"
    assert hd["withheld_positive_pixels"] == 11321
    assert hd["candidate"]["dti"] > hd["same_split_comparators"]["H86C_KSLB_E3_44k"]["dti"]
    assert hd["candidate"]["ci95"][0] > hd["same_split_comparators"]["H86C_KSLB_E3_44k"]["ci95"][1]
    assert hd["paired_differences"]["E3_ewcs_isotropic_tip_ablation"]["ci95"][0] > 0.0
    assert hd["paired_differences"]["R0_D28_visible_collar"]["ci95"][0] > 0.0
    assert len(hd["leakage_canary"]) == len(STATIC_FEATURE_NAMES) + 5
    assert all(not v["leakage_flag"] and v["discriminative_auc"] <= 0.90
               for v in hd["leakage_canary"].values())

    surf_meta = card["correlation_overlap_vs_registry"]["surface_preplacement"]
    surf_doc = json.loads((ROOT / surf_meta["report"]).read_text(encoding="utf-8"))
    assert surf_doc["schema"] == "gems86.registry-candidate.v2"
    assert surf_doc["surface_gate_pass"] is False
    assert surf_doc["literal_gate_pass"] is False
    assert surf_doc["registry_complete_for_index"] is False
    assert len(surf_doc["errors"]) == 2
    assert surf_doc["two_phase"]["literal_reading"]["worst_spearman_full_footprint"] <= 0.90
    assert surf_doc["two_phase"]["literal_reading"]["rho_firings"] == 0

    dots_meta = card["correlation_overlap_vs_registry"]["final_dots"]
    dots_doc = json.loads((ROOT / dots_meta["report"]).read_text(encoding="utf-8"))
    assert dots_doc["schema"] == "gems86.registry-candidate.v2"
    assert dots_doc["final_dots_gate_pass"] is False
    assert dots_doc["literal_gate_pass"] is False
    assert dots_doc["registry_complete_for_index"] is False
    assert card["correlation_overlap_vs_registry"]["pa86_02"]["gate_pass"] is False
    # Zero discrete <= 50,000-dot firings across the entire 689-entry registry
    dot_firings_50k = [
        r for r in dots_doc["two_phase"]["literal_firings"]
        if r["representation"] == "dot_field" and r["their_dots"] <= 50000
    ]
    assert dot_firings_50k == []


def test_mmt_legacy_surface_and_runner_fail_closed_repairs():
    mmt_surf = json.loads(
        (ROOT / "docs/evidence/h86e-mmt-registry-surface.json").read_text(encoding="utf-8")
    )
    assert mmt_surf["surface_gate_pass"] is False
    assert len(mmt_surf["errors"]) == 2

    mmt_src = (ROOT / "scripts/run_h86e_mmt.py").read_text(encoding="utf-8")
    assert 'raise RuntimeError("STOP: H86E-MMT final-dot registry gate failed before serialization")' in mmt_src


def test_h86f_runner_halts_on_preflight_failure_before_grid_load(monkeypatch):
    from scripts import protocol_preflight

    def blocked():
        raise RuntimeError("PREFLIGHT_BLOCKED")

    monkeypatch.setattr(protocol_preflight, "require_feasible", blocked)
    monkeypatch.setattr(run_h86f_ewcs.grid, "load_grid", lambda _: pytest.fail("loaded grid after preflight stop"))
    with pytest.raises(RuntimeError, match="PREFLIGHT_BLOCKED"):
        run_h86f_ewcs.main()

