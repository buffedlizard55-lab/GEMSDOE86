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


def test_out_of_range_rejected():
    pred, truth = _toy()
    bad = pred.copy()
    bad[0, 0] = 1.5
    try:
        metric.dti_exact(bad, truth)
    except ValueError:
        return
    raise AssertionError("out-of-range prediction must be rejected")
