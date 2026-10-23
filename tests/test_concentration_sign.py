"""Tests for the CONCENTRATION sign builder (``scripts/build_concentration_sign.py``).

Synthetic grid only: these tests pin the *rules* (count invariance, clearance, determinism,
prior shape), not the session's numbers.  The real-grid numbers live in
``evidence/concentration_sign_20261023.json`` and are re-derived by re-running the script.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

spec = importlib.util.spec_from_file_location(
    "build_concentration_sign", ROOT / "scripts" / "build_concentration_sign.py")
bcs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bcs)


def _grid(h=200, w=200, seed=7):
    foot = np.ones((h, w), bool)
    cat = np.zeros((h, w), bool)
    cat[20:180, 100:102] = True                 # a straight mapped trace
    rng = np.random.default_rng(seed)
    dots = np.zeros((h, w), bool)
    rows, cols = np.nonzero(foot)
    pick = rng.choice(rows.size, size=600, replace=False)
    dots[rows[pick], cols[pick]] = True
    from scipy import ndimage as ndi

    dots &= ndi.distance_transform_edt(~cat) > 3.0
    ctx = {"footprint": foot, "catalogue": cat}
    return ctx, foot, cat, dots


def test_prior_is_finite_only_on_footprint_blocks():
    ctx, foot, cat, _ = _grid()
    prior = bcs.catalogue_prior(foot, cat)
    p = prior["prior"]
    assert p.shape == (foot.shape[0] // bcs.BLOCK_PX, foot.shape[1] // bcs.BLOCK_PX)
    assert np.isfinite(p).all()
    # the block holding the mapped trace must out-rank blocks far from it
    assert p[10, 10] > p[10, 19]


def test_arms_preserve_count_and_clearance():
    ctx, foot, cat, dots = _grid()
    prior = bcs.catalogue_prior(foot, cat)
    from scipy import ndimage as ndi

    edt = ndi.distance_transform_edt(~cat)
    for value, s, d, _role in bcs.ARMS:
        mask, stats = bcs.build_arm(dots, ctx, prior, value, s, d, 0.15, 11)
        assert stats["n_dots_variant"] == int(dots.sum()), value
        assert stats["moved_shortfall"] == 0, value
        new = mask & ~dots
        assert (new & cat).sum() == 0, value
        if new.any():
            assert edt[new].min() >= bcs.CLEARANCE_PX, value
        assert stats["min_cat_edt_variant"] >= 2.0


def test_control_is_deterministic_and_nested_in_its_seed():
    ctx, foot, cat, dots = _grid()
    prior = bcs.catalogue_prior(foot, cat)
    a, sa = bcs.build_arm(dots, ctx, prior, "rand15", +1, 0, 0.15, 11)
    b, sb = bcs.build_arm(dots, ctx, prior, "rand15", +1, 0, 0.15, 11)
    assert (a == b).all() and sa["moved_placed"] == sb["moved_placed"]
    c, _ = bcs.build_arm(dots, ctx, prior, "rand15", +1, 0, 0.15, 12)
    assert not (a == c).all(), "a different seed must choose different destination blocks"


def test_spread_and_dense_move_the_same_dots_apart():
    ctx, foot, cat, dots = _grid()
    prior = bcs.catalogue_prior(foot, cat)
    spr, s_spr = bcs.build_arm(dots, ctx, prior, "spr15", +1, -1, 0.15, 11)
    den, s_den = bcs.build_arm(dots, ctx, prior, "dens15", -1, +1, 0.15, 11)
    # the two arms must not be the same edit, and the spread arm must end up further from the
    # catalogue on average than the dense arm (that is what "spread" means here)
    assert not (spr == den).all()
    assert s_spr["moved_placed"] == s_den["moved_placed"]
    assert s_spr["cat_edt_mean_variant"] > s_den["cat_edt_mean_variant"]


def test_truth_models_are_masks_inside_the_footprint():
    ctx, foot, cat, _ = _grid()
    models = bcs.truth_models(foot, cat)
    assert set(models) == {"annulus_2_4px", "annulus_3_8px", "uniform_far_0p8pct",
                           "uniform_all_0p8pct", "catalogue_shift_6px"}
    for name, m in models.items():
        assert m.dtype == bool and m.shape == foot.shape, name
        assert not (m & ~foot).any(), name
        assert m.any(), name
