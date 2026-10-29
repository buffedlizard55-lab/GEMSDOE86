"""The shared metric must equal a literal transcription of the published equations."""
import numpy as np
from gems57 import metric


def _toy():
    truth = np.zeros((14, 14), bool)
    truth[4:10, 6] = True
    pred = np.zeros((14, 14), np.float32)
    pred[5, 5:8] = 1.0
    pred[8, 6:9] = 0.5
    return pred, truth


def test_binary_equals_bruteforce():
    truth = np.zeros((12, 12), bool)
    truth[3:9, 5] = True
    pred = np.zeros((12, 12), bool)
    pred[4, 4:7] = True
    fast = metric.dti_binary(pred, truth)
    slow = metric.dti_bruteforce(pred.astype(float), truth)
    assert abs(fast["tp"] - slow["tp"]) < 1e-9
    assert abs(fast["fp"] - slow["fp"]) < 1e-9
    assert abs(fast["dti"] - slow["dti"]) < 1e-9


def test_soft_equals_bruteforce():
    pred, truth = _toy()
    fast = metric.dti_exact(pred, truth)
    slow = metric.dti_bruteforce(pred, truth)
    for k in ("tp", "fp", "fn", "dti"):
        assert abs(fast[k] - slow[k]) < 1e-9, k


def test_kernel_radius_and_alpha_beta():
    assert metric.ALPHA == 0.2 and metric.BETA == 0.8 and metric.RADIUS_PX == 3.0
    assert metric.kernel(0) == 1.0
    assert abs(metric.kernel(1.5) - 0.5) < 1e-12
    assert metric.kernel(3.0) == 0.0 and metric.kernel(3.1) == 0.0


def test_perfect_prediction_is_one():
    truth = np.zeros((10, 10), bool)
    truth[4, 2:8] = True
    r = metric.dti_binary(truth.copy(), truth)
    assert r["dti"] > 0.999


def test_marginal_truth_credit_can_exceed_one_dot_self_credit():
    """Synthetic counterexample to the pinned shared metric's dT <= k prose.

    One dot can credit several truth cells. This does not modify the pinned
    evaluator or imply any competition or holdout score.
    """
    truth = np.zeros((9, 9), bool)
    truth[4, 3:6] = True
    before = np.zeros_like(truth)
    after = before.copy()
    after[4, 4] = True
    r0 = metric.dti_binary(before, truth)
    r1 = metric.dti_binary(after, truth)
    d_t = r1["tp"] - r0["tp"]
    k_self = 1.0 - (r1["fp"] - r0["fp"])
    assert np.isclose(d_t, 1.0 + 2.0 * (2.0 / 3.0))
    assert np.isclose(k_self, 1.0)
    assert d_t > k_self
    assert metric.marginal_accept(d_t, k_self, r0["tp"], 0.0, 0, truth.sum())
    assert r1["dti"] > r0["dti"]


def test_exact_marginal_accept_agrees_with_synthetic_additions():
    rng = np.random.default_rng(20261029)
    for _ in range(100):
        truth = rng.random((9, 9)) < 0.15
        dots = rng.random((9, 9)) < 0.08
        empty = np.argwhere(~dots)
        y, x = empty[rng.integers(len(empty))]
        r0 = metric.dti_binary(dots, truth)
        new_dots = dots.copy()
        new_dots[y, x] = True
        r1 = metric.dti_binary(new_dots, truth)
        if abs(r1["dti"] - r0["dti"]) < 1e-12:
            continue  # Float rounding at exact equality is not a strict improvement.
        d_t = r1["tp"] - r0["tp"]
        k_self = 1.0 - (r1["fp"] - r0["fp"])
        n = int(dots.sum())
        m = n - r0["fp"]
        assert metric.marginal_accept(d_t, k_self, r0["tp"], m, n, int(truth.sum())) == (r1["dti"] > r0["dti"])


def test_out_of_range_rejected():
    pred, truth = _toy()
    bad = pred.copy()
    bad[0, 0] = 1.5
    try:
        metric.dti_exact(bad, truth)
    except ValueError:
        return
    raise AssertionError("out-of-range prediction must be rejected")
