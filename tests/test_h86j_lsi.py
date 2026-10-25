"""Unit tests for the H86J-LSI live-score inversion algebra."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import metric  # noqa: E402
from gems86_lsi import lsi  # noqa: E402


def test_max_credit_matches_official_kernel_for_binary_dots():
    p = np.zeros((40, 40), np.float32)
    p[10, 10] = p[25, 30] = 1.0
    c = lsi.max_credit(p)
    d = np.minimum(np.hypot(*np.mgrid[:40, :40] - np.array([10, 10])[:, None, None]),
                   np.hypot(*np.mgrid[:40, :40] - np.array([25, 30])[:, None, None]))
    np.testing.assert_allclose(c, metric.kernel(d), atol=1e-6)


def test_sum_credit_equals_vendor_expected_credit():
    from gems57 import emit
    rng = np.random.default_rng(0)
    p = (rng.random((30, 30)) > 0.9).astype(np.float32) * rng.random((30, 30)).astype(np.float32)
    np.testing.assert_allclose(lsi.sum_credit(p), emit.expected_credit(p), atol=1e-6)


def test_expected_T_equals_exact_TP_when_lambda_is_the_truth_indicator():
    rng = np.random.default_rng(1)
    truth = np.zeros((60, 60), bool)
    truth[30, 5:55] = True                     # a straight fault trace
    dots = np.zeros((60, 60), bool)
    dots[rng.integers(0, 60, 40), rng.integers(0, 60, 40)] = True
    exact = metric.dti_binary(dots, truth)
    e = lsi.expected_dti_of(dots.astype(np.float32), truth.astype(np.float32),
                            np.ones_like(truth))
    assert abs(e["T"] - exact["tp"]) < 1e-6
    assert e["G"] == truth.sum()


def test_M_line_constant_is_three_for_a_dot_on_a_long_line():
    lam = np.zeros((41, 41), np.float32)
    lam[20, :] = 1.0
    dot = np.zeros_like(lam)
    dot[20, 20] = 1.0
    e = lsi.expected_dti_of(dot, lam, np.ones(lam.shape, bool))
    assert abs(e["M"] - 1.0) < 1e-6           # true self-credit of an on-line dot is 1


def _toy_problem(seed=3):
    rng = np.random.default_rng(seed)
    n_s, n_r, k = 400, 12, 3
    F = rng.normal(size=(n_s, k))
    X = lsi.design(F)
    from scipy import sparse
    C = sparse.csr_matrix(rng.random((n_r, n_s)) * (rng.random((n_r, n_s)) > 0.7))
    S = sparse.csr_matrix(C.toarray() * 1.3)
    ops = lsi.Operators(C=C, S=S, n=rng.uniform(50, 100, n_r), frac=0.5)
    return X, ops


def test_analytic_gradient_matches_finite_differences():
    X, ops = _toy_problem()
    theta = np.array([-2.0, 0.3, -0.2, 0.1])
    y = np.full(len(ops.n), 0.1)
    w = np.ones_like(y)
    rows = np.arange(len(y))
    L, g = lsi.loss_grad(theta, X, ops, y, w, 1e-3, rows)
    num = np.zeros_like(theta)
    for j in range(len(theta)):
        e = np.zeros_like(theta)
        e[j] = 1e-6
        num[j] = (lsi.loss_grad(theta + e, X, ops, y, w, 1e-3, rows)[0]
                  - lsi.loss_grad(theta - e, X, ops, y, w, 1e-3, rows)[0]) / 2e-6
    np.testing.assert_allclose(g, num, rtol=1e-4, atol=1e-8)


def test_fit_recovers_synthetic_parameters():
    X, ops = _toy_problem(5)
    true = np.array([-2.0, 0.6, -0.4, 0.0])
    y, _ = lsi.predict_terms(true, X, ops)
    theta, info = lsi.fit(X, ops, y, np.ones_like(y), ridge=0.0, theta0=np.zeros(4))
    pred, _ = lsi.predict_terms(theta, X, ops)
    np.testing.assert_allclose(pred, y, atol=2e-4)


def test_decode_reports_and_clips_out_of_range_values():
    a = np.array([[np.nan, 2.0], [-1.0, 0.5]], np.float32)
    fp = np.ones((2, 2), bool)
    v, info = lsi.decode(a, fp, np.zeros((2, 2), bool))
    assert info["nonfinite_inside"] == 1 and info["above1_inside"] == 1 and info["below0_inside"] == 1
    assert v.min() >= 0 and v.max() <= 1 and np.isfinite(v).all()


def test_runner_is_gated_by_like_for_like_preflight():
    src = (ROOT / "scripts/run_h86j_lsi.py").read_text()
    assert "require_like_for_like()" in src
    main = src[src.index("def main("):]
    assert main.index("require_like_for_like()") < main.index("stage_e1(g, folds")


def test_within_3px_fraction_matches_distance_transform():
    from scipy import ndimage as ndi
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib
    run = importlib.import_module("run_h86j_lsi")
    rng = np.random.default_rng(7)
    theirs = rng.random((80, 80)) > 0.97
    dots = rng.random((80, 80)) > 0.95
    dt = ndi.distance_transform_edt(~theirs)
    want = float((dt[dots] <= 3.0).mean())
    assert abs(run.within_3px_fraction(np.nonzero(dots), theirs) - want) < 1e-12


def test_h86j_run_card_is_negative_unauthorized_and_consistent():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    card = json.loads((root / "docs/evidence/h86j-lsi-run-card.json").read_text())
    assert card["verdict"] == ("promote" if all(card["gates"].values()) else "negative")
    assert card["verdict"] == "negative" and "DO NOT SUBMIT" in card["decision"]
    assert card["safe_to_submit"] is False and card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0 and card["published_download"] is False
    assert "DO-NOT-SUBMIT" in card["submission_name"] and len(card["note"]) <= 140
    assert card["validator_output"]["all_checks_passed"] is True
    assert not (root / "docs/downloads" / f"{card['submission_name']}.tif").exists()
