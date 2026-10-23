"""SNAP axis geometry: pure functions, synthetic fixtures, no experiment.

Nothing here reads a competition raster, fits a model, or claims a score. The
tests pin the three properties the axis contract depends on: the dot count is
preserved, no dot moves farther than the stated radius, and no dot lands on an
excluded cell.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "vendor" / "template66")]

from src.gems86 import snap as S  # noqa: E402


def test_rank01_is_monotone_masked_and_tie_averaged():
    v = np.array([[3.0, 1.0], [2.0, np.nan]])
    valid = np.array([[True, True], [True, False]])
    out = S.rank01(v, valid)
    assert out[0, 1] == 0.0 and out[1, 0] == 0.5 and out[0, 0] == 1.0
    assert out[0, 1] < out[1, 0] < out[0, 0]
    assert out[~valid].sum() == 0.0
    tie = S.rank01(np.array([[5.0, 5.0], [5.0, 5.0]]), np.ones((2, 2), bool))
    assert np.allclose(tie, 0.5)


def test_edge_response_requires_normalised_weights_and_combines_bands():
    valid = np.ones((4, 4), bool)
    a = np.arange(16, dtype=float).reshape(4, 4)
    b = a[::-1].copy()
    with pytest.raises(ValueError):
        S.edge_response({"a": a}, valid, {"a": 0.5})
    with pytest.raises(ValueError):
        S.edge_response({"a": a, "b": b}, valid, {"a": 0.5, "b": 0.6})
    mixed = S.edge_response({"a": a, "b": b}, valid, {"a": 0.5, "b": 0.5})
    assert mixed.shape == a.shape
    # two mirrored rank fields average to 0.5 +/- 0.1, never outside [0, 1]
    assert mixed.min() >= 0.0 and mixed.max() <= 1.0
    only_b = S.edge_response({"a": a, "b": b}, valid, {"a": 0.0, "b": 1.0})
    assert np.allclose(only_b, S.rank01(b, valid))


def test_window_offsets_are_within_the_radius_and_symmetric():
    for radius, expected in ((1.0, 4), (1.5, 8), (2.0, 12)):
        dy, dx, d = S.window_offsets(radius)
        assert len(d) == expected
        assert (d <= radius + 1e-12).all() and (d > 0).all()
        assert set(zip(dy.tolist(), dx.tolist())) == {(-j, -i) for j, i in zip(dy.tolist(), dx.tolist())}


def test_snap_preserves_count_and_respects_radius_and_exclusions():
    rng = np.random.default_rng(7)
    shape = (60, 60)
    dots = np.zeros(shape, bool)
    dots[rng.choice(60, 80), rng.choice(60, 80)] = True          # collisions are fine
    response = rng.random(shape)
    allowed = np.ones(shape, bool)
    allowed[:5, :] = False                                        # a masked strip
    dots[:5, :] = False                                           # the parent must obey it
    for radius in (1.0, 2.0):
        result = S.snap_dots(dots, response, allowed, radius=radius)
        assert result.dots.sum() == dots.sum()
        assert not np.any(result.dots & ~allowed)
        assert result.displacement.size <= dots.sum()
        if result.displacement.size:
            assert result.displacement.max() <= radius + 1e-12
            assert (result.gain > 0).all()
        # deterministic
        again = S.snap_dots(dots, response, allowed, radius=radius)
        assert np.array_equal(result.dots, again.dots)


def test_snap_moves_a_dot_onto_the_local_maximum_and_is_a_bijection():
    dots = np.zeros((9, 9), bool)
    dots[4, 4] = True
    response = np.zeros((9, 9))
    response[4, 6] = 1.0                    # exactly 2 px away
    allowed = np.ones((9, 9), bool)
    allowed[4, 5] = False                   # a hole in between must be skipped
    res = S.snap_dots(dots, response, allowed, radius=2.0)
    assert res.dots[4, 6] and not res.dots[4, 4]
    assert res.n_snapped == 1 and res.displacement[0] == pytest.approx(2.0)
    diff = S.move_diff(dots, res.dots, np.ones((9, 9)))
    assert diff["removed"] == diff["added"] == 1
    assert diff["n_parent"] == diff["n_candidate"] == 1
    assert diff["pct_of_parent_changed"] == 200.0


def test_no_gain_means_no_move():
    dots = np.zeros((7, 7), bool)
    dots[3, 3] = True
    response = np.zeros((7, 7))
    response[3, 3] = 1.0                    # the dot already sits on the maximum
    res = S.snap_dots(dots, response, np.ones((7, 7), bool), radius=2.0)
    assert res.n_snapped == 0 and res.dots[3, 3]


def test_snap_never_takes_an_occupied_cell():
    dots = np.zeros((5, 5), bool)
    dots[2, 2] = True
    dots[2, 3] = True                       # neighbour occupies the best target
    response = np.zeros((5, 5))
    response[2, 3] = 1.0
    response[2, 1] = 0.5
    res = S.snap_dots(dots, response, np.ones((5, 5), bool), radius=1.0)
    assert res.dots.sum() == 2
    assert res.dots[2, 3]
    # the only free improving cell for (2,2) is (2,1); it must not be skipped in
    # favour of the higher-valued but occupied (2,3)
    assert res.dots[2, 1] and not res.dots[2, 2]


def test_snap_rejects_a_parent_dot_outside_the_landing_mask():
    dots = np.zeros((6, 6), bool)
    dots[0, 0] = True
    allowed = np.ones((6, 6), bool)
    allowed[0, 0] = False
    with pytest.raises(ValueError):
        S.snap_dots(dots, np.random.default_rng(1).random((6, 6)), allowed, radius=1.0)


def test_move_diff_rejects_count_change():
    a = np.zeros((4, 4), bool)
    b = np.zeros((4, 4), bool)
    a[0, 0] = True
    with pytest.raises(ValueError):
        S.move_diff(a, b, np.ones((4, 4)))


def test_nearest_neighbour_matches_bruteforce():
    dots = np.zeros((10, 10), bool)
    dots[1, 1] = dots[1, 4] = dots[8, 8] = True
    nn = S.nearest_neighbour(dots)
    assert np.allclose(sorted(nn), [3.0, 3.0, np.hypot(7, 4)])
