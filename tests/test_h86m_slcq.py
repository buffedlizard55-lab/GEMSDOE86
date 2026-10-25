"""Mathematical-oracle and protocol-invariant unit tests for Lane H86M-SLCQ."""

from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np
import pytest

from src.gems86.io import BANDS
from src.gems86_slcq.model import (
    fuse_cover_conditioned_noisy_or,
    partition_visible_components_k,
    true_footprint_quadrants,
)
from src.gems86_slcq.operators import (
    adaptive_vector_updip_pullback,
    build_bmr_basis,
    fit_bmr_weights,
    fit_predict_fold_safe_bmr,
    garland_poisson_admittance_jump,
    salem_adaptive_dip_and_sharpness,
    steerable_log_cauchy_step_vs_dike,
)

ROOT = Path(__file__).resolve().parents[1]


def test_salem_adaptive_dip_zero_on_vertical_fault_and_positive_on_dipping_fault():
    """Vertical (90 deg) strike-slip step must produce ~0 cot(dip) and zero off-trace shift,
    whereas an asymmetric dipping normal-fault contact must produce positive down-dip cot_c
    and shift buried hanging-wall responses updip toward surface emergence."""
    H, W = 128, 128
    valid = np.ones((H, W), dtype=bool)
    _, xx = np.indices((H, W), dtype=np.float32)

    # 1. Purely odd vertical contact at col = 64 (arctan potential step at top depth 200 m)
    x_rel = (xx - 64.0) * 100.0
    phi_vert = np.arctan2(x_rel, 200.0).astype(np.float32)
    zb_flat = np.full((H, W), 800.0, dtype=np.float32)

    sharp_v, cot_v, cr_v, cc_v = salem_adaptive_dip_and_sharpness(
        phi_vert, None, valid, z1_m=150.0, z2_m=750.0
    )
    # Peak sharpness sits at col 64, and cot_mag right on the vertical fault is near zero!
    assert abs(int(np.argmax(sharp_v[64, 20:108])) + 20 - 64) <= 1
    assert float(cot_v[64, 64]) < 0.05

    # Vertical fault under 800 m cover does NOT mis-shift off col = 64 (unlike cot(60)*8 = 4.6 px)
    deep_peak_vert = np.exp(-(((xx - 64.0) / 2.5) ** 2)).astype(np.float32)
    pulled_vert = adaptive_vector_updip_pullback(deep_peak_vert, zb_flat, cr_v, cc_v, valid)
    assert abs(int(np.argmax(pulled_vert[64, :])) - 64) <= 1

    # 2. Dipping normal fault emerging at col = 48 and dipping toward +col (cot(dip) = 0.70):
    # Integrate 12 horizontal depth laminae z in [150 m, 1400 m] shifted down-dip by z * 0.70.
    phi_dip = np.zeros((H, W), dtype=np.float32)
    for zeta_m in np.linspace(150.0, 1400.0, 14):
        x_lam = (xx - 48.0) * 100.0 - 0.70 * float(zeta_m)
        phi_dip -= np.arctan2(x_lam, float(zeta_m)).astype(np.float32)
    zb_basin = np.clip((xx - 48.0) * 80.0, 0.0, 1200.0).astype(np.float32)

    _, cot_d, cr_d, cc_d = salem_adaptive_dip_and_sharpness(
        phi_dip, zb_basin, valid, z1_m=150.0, z2_m=750.0
    )
    # Polarity & positive-scale invariance check: flipping sign and scaling by 7.5x
    _, cot_flip, cr_flip, cc_flip = salem_adaptive_dip_and_sharpness(
        -7.5 * phi_dip, zb_basin, valid, z1_m=150.0, z2_m=750.0
    )
    assert np.allclose(cot_d[32:96, 32:96], cot_flip[32:96, 32:96], atol=1e-3)
    assert np.allclose(cc_d[32:96, 32:96], cc_flip[32:96, 32:96], atol=1e-3)
    assert np.allclose(cr_d[32:96, 32:96], cr_flip[32:96, 32:96], atol=1e-3)

    # Down-dip cot_c in hanging wall near emergence is strictly positive (> 0.25)
    assert float(np.mean(cc_d[64, 48:58])) > 0.25

    # Buried step centered 4 px down-dip (col = 52) pulls updip closer to emergence (col = 48)
    buried_step = np.exp(-(((xx - 52.0) / 2.2) ** 2)).astype(np.float32)
    pulled_dip = adaptive_vector_updip_pullback(buried_step, zb_basin, cr_d, cc_d, valid)
    peak_before = int(np.argmax(buried_step[64, :]))
    peak_after = int(np.argmax(pulled_dip[64, :]))
    assert peak_after < peak_before
    assert abs(peak_after - 48) < abs(peak_before - 48)


def test_steerable_log_cauchy_vetoes_symmetric_dikes_and_detects_oblique_steps():
    """Steerable 8-azimuth log-Cauchy quadrature filter must yield zero step score on a
    linear ramp and on the crest of an even-symmetric Gaussian volcanic dike, while peaking
    sharply on an oblique odd-symmetric fault step."""
    H, W = 128, 128
    valid = np.ones((H, W), dtype=bool)
    yy, xx = np.indices((H, W), dtype=np.float32)

    # 1. Pure DC + 2-D linear ramp -> near-zero interior response
    ramp = 120.0 + 1.7 * xx - 0.9 * yy
    s_ramp, _, _ = steerable_log_cauchy_step_vs_dike(ramp, valid, wavelength_m=500.0)
    assert float(np.max(s_ramp[24:104, 24:104])) < 1e-2

    # Oblique coordinate at 35 deg normal azimuth through grid center (64, 64)
    theta = np.deg2rad(35.0)
    u_perp = (xx - 64.0) * np.cos(theta) + (yy - 64.0) * np.sin(theta)

    # 2. Even-symmetric Gaussian volcanic dike: crest at (64, 64) must be 100% vetoed (== 0)
    dike = 50.0 * np.exp(-((u_perp / 2.2) ** 2)).astype(np.float32)
    s_dike, pc_dike, e_dike = steerable_log_cauchy_step_vs_dike(dike, valid, wavelength_m=500.0)
    assert float(s_dike[64, 64]) == pytest.approx(0.0, abs=1e-4)
    assert float(pc_dike[64, 64]) == pytest.approx(0.0, abs=1e-4)
    assert float(e_dike[64, 64]) > 1.0

    # 3. Odd-symmetric tanh fault step at same 35 deg azimuth: strong step energy & PC > 0.55
    step = 50.0 * np.tanh(u_perp / 2.0).astype(np.float32)
    s_step, pc_step, _ = steerable_log_cauchy_step_vs_dike(step, valid, wavelength_m=500.0)
    assert float(s_step[64, 64]) > 5.0
    assert float(pc_step[64, 64]) > 0.55
    # Off-fault interior background (>16 px away) is at least 10x weaker than fault center
    assert float(s_step[20, 108]) < 0.1 * float(s_step[64, 64])


def test_garland_poisson_admittance_jump_localizes_demagnetization_contact():
    H, W = 96, 96
    valid = np.ones((H, W), dtype=bool)
    _, xx = np.indices((H, W), dtype=np.float32)
    grav_slope = np.full((H, W), 5.0, dtype=np.float32)
    # Left half has strong magnetic gradient; right half has weak magnetic gradient (alteration)
    rtp = np.where(xx < 48.0, 10.0 * xx, 10.0 * 48.0 + 0.5 * (xx - 48.0)).astype(np.float32)
    jump = garland_poisson_admittance_jump(rtp, grav_slope, valid)
    peak_col = int(np.argmax(jump[48, 16:80])) + 16
    assert abs(peak_col - 48) <= 2
    assert float(jump[48, peak_col]) > 5.0 * float(jump[48, 20])


def test_fold_safe_bmr_zero_target_quadrant_leakage_and_horst_recovery():
    """Corrupting target-quadrant gravity by +1e6 mGal must not alter out-of-quadrant BMR
    weights by a single bit, and BMR must isolate an unmodeled intrabasin horst step."""
    H, W = 96, 96
    valid = np.ones((H, W), dtype=bool)
    yy, xx = np.indices((H, W), dtype=np.float32)
    train_mask = ~((yy < H // 2) & (xx < W // 2))  # Hold out NW quadrant

    # Smooth basin Z_b + true Bouguer gravity + unmodeled intrabasin horst step in NW quadrant
    zb = (400.0 + 600.0 * np.sin(np.pi * xx / W) * np.sin(np.pi * yy / H)).astype(np.float32)
    psi = build_bmr_basis(zb, valid)
    true_w = np.array([-15.0, -8.5, -12.0, -3.0, -2.0, -1.0], dtype=np.float32)
    g_clean = np.tensordot(true_w, psi, axes=([0], [0])).astype(np.float32)
    horst = 6.0 * np.tanh((xx - 24.0) / 1.8).astype(np.float32) * (yy < H // 2).astype(np.float32)
    g_obs = g_clean + horst

    g_pull, lc_pull, w1 = fit_predict_fold_safe_bmr(g_obs, zb, valid, train_mask, psi=psi)

    # Corrupt held-out NW quadrant with +1,000,000 mGal -> weights must be bit-identical!
    g_corrupt = g_obs.copy()
    g_corrupt[~train_mask] += 1_000_000.0
    w2 = fit_bmr_weights(psi, g_corrupt, train_mask)
    assert np.array_equal(w1, w2)

    # Residual step peaks right at col = 24 inside the held-out NW quadrant!
    peak_c_grad = int(np.argmax(g_pull[24, 8:40])) + 8
    peak_c_lc = int(np.argmax(lc_pull[24, 8:40])) + 8
    assert abs(peak_c_grad - 24) <= 1
    assert abs(peak_c_lc - 24) <= 1


def test_five_fold_80_20_component_partition_and_cover_noisy_or():
    H, W = 64, 64
    vis = np.zeros((H, W), dtype=bool)
    for k in range(15):
        r0 = (k // 5) * 20 + 4
        c0 = (k % 5) * 12 + 3
        vis[r0 : r0 + 5, c0 : c0 + 2] = True

    parts = partition_visible_components_k(vis, 5, seed=42)
    assert len(parts) == 5
    union = np.zeros_like(vis)
    for i, pi in enumerate(parts):
        for j in range(i + 1, 5):
            assert not np.any(pi & parts[j]), "Splits must be pairwise disjoint"
        union |= pi
        # Each 80/20 split retains ~80% of components
        vis_80 = vis & ~pi
        frac_vis = float(vis_80.sum()) / float(vis.sum())
        assert 0.75 <= frac_vis <= 0.85
    assert np.array_equal(union, vis)

    valid = np.ones((H, W), dtype=bool)
    valid[0, :] = False
    pb = np.full((H, W), 0.5, dtype=np.float32)
    pk = np.full((H, W), 0.3, dtype=np.float32)
    c_zero = np.zeros((H, W), dtype=np.float32)
    c_one = np.ones((H, W), dtype=np.float32)
    s_exposed = fuse_cover_conditioned_noisy_or(pb, pk, c_zero, valid)
    s_covered = fuse_cover_conditioned_noisy_or(pb, pk, c_one, valid)
    assert np.all(s_exposed[~valid] == 0.0) and np.all(s_covered[~valid] == 0.0)
    assert np.all((s_covered >= 0.0) & (s_covered <= 1.0))
    assert float(s_covered[10, 10]) > float(s_exposed[10, 10])


def test_h86m_preregistration_and_hypothesis_contracts():
    hyp = json.loads((ROOT / "registry/h86m_slcq_hypotheses.json").read_text(encoding="utf-8"))
    pre = json.loads((ROOT / "research/H86M_SLCQ_PREREGISTRATION.json").read_text(encoding="utf-8"))
    assert hyp["declared_before_implementation"] is True
    assert pre["declared_before_implementation"] is True
    assert 3 <= len(hyp["hypotheses"]) <= 5
    assert hyp["experiments_budget_max"] <= 3
    assert len(pre["protocol"]["arms"]) == 3

    for row in hyp["hypotheses"]:
        blob = " ".join([*row["layers"], row["signature"], row["why_unmapped"], row["difference_from_repo"]])
        assert "tc (Band 6) magnetic tilt zero-crossings" not in blob
        for key, b_str in re.findall(r"\b([a-z0-9_]+)\s*\(Band\s+(\d+)\b", blob):
            assert BANDS[int(b_str)] == key
        if row["external_data_required"]:
            assert "NOT_VIABLE" in row["data_readiness"]


def test_true_footprint_quadrants_matches_gems57_holdout():
    """Ensure quadrant partitioning splits at footprint median (not bounding-box H//2, W//2)."""
    import sys
    sys.path.insert(0, str(ROOT / "vendor"))
    from gems57.holdout import quadrant_ids

    fp = np.zeros((100, 100), dtype=bool)
    fp[10:50, 20:80] = True  # Footprint concentrated in upper rows (median row ~ 29 != 50)
    q_slcq = true_footprint_quadrants(fp)
    q_gems = quadrant_ids(fp)
    assert np.array_equal(q_slcq, q_gems)
    for q in range(4):
        assert 500 <= int((q_slcq == q).sum()) <= 700  # Balanced ~25% split (vs 0 in SW/SE for H//2=50!)
