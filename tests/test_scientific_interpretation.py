"""Synthetic metric invariants, NOT holdout experiments or leaderboard scores.

Guard the qualified H33 explanation using the unchanged shared implementation.
No candidate raster, model fit, catalogue feature, or submission is constructed.
"""
import numpy as np

from gems57.metric import RADIUS_PX, dti_binary, dti_bruteforce, kernel


def test_one_radius_dot_spacing_does_not_make_kernel_support_disjoint():
    # Integer separation 3 is even larger than the historical 2.8-pixel rule.
    truth_x = 4
    dots_x = np.array([3, 6])
    assert np.diff(dots_x)[0] == RADIUS_PX
    weights = kernel(np.abs(dots_x - truth_x))
    assert (weights > 0).all()  # Both cones cover this same truth pixel.
    pred = np.zeros((9, 10)); pred[4, dots_x] = 1
    truth = np.zeros_like(pred, dtype=bool); truth[4, truth_x] = True
    measured = dti_bruteforce(pred, truth)
    assert np.isclose(measured['tp'], weights.max())
    assert measured['tp'] < weights.sum()  # Max-credit, not sum-credit.


def test_off_catalogue_collar_dot_can_recover_hidden_truth():
    known = np.zeros((11, 11), dtype=bool); known[5, 4] = True
    truth = np.zeros_like(known); truth[5, 7] = True
    pred = np.zeros_like(known); pred[5, 6] = True
    # Dot is two pixels from known fault, one pixel from hidden fault.
    kept = dti_binary(pred, truth, known=known)
    removed = dti_binary(np.zeros_like(pred), truth, known=known)
    assert kept['tp'] > 0
    assert kept['dti'] > removed['dti']


def test_greater_dot_density_can_improve_truth_recovery():
    truth = np.zeros((15, 15), dtype=bool)
    truth[3, 3] = truth[11, 11] = True
    sparse = np.zeros_like(truth); sparse[3, 3] = True
    denser = sparse.copy(); denser[11, 11] = True
    a = dti_binary(sparse, truth)
    b = dti_binary(denser, truth)
    assert denser.sum() > sparse.sum()
    assert b['tp'] > a['tp']
    assert b['dti'] > a['dti']


def test_redundant_off_truth_dot_can_reduce_metric():
    truth = np.zeros((11, 11), dtype=bool); truth[5, 5] = True
    exact = truth.copy()
    redundant = exact.copy(); redundant[5, 6] = True
    a = dti_binary(exact, truth)
    b = dti_binary(redundant, truth)
    assert np.isclose(a['tp'], b['tp'])
    assert b['fp'] > a['fp']
    assert b['dti'] < a['dti']
