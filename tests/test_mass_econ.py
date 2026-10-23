"""Unit tests for the kernel-budget MASS axis (``src/gems86/mass_econ.py``).

The point of these tests is that the axis's *selection* never touches a label, a band or a
surrogate: it is a decomposition of the metric's own numerator.  So the tests check the algebra
against brute force, and the geometry against the constraints the brief forbids anyone to break.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems57 import metric  # noqa: E402
from gems86 import mass_econ as ME  # noqa: E402


def _field(shape=(80, 90), pts=((10, 10), (10, 12), (40, 40), (41, 44), (70, 80))):
    m = np.zeros(shape, bool)
    for r, c in pts:
        m[r, c] = True
    return m


def test_marginal_credit_matches_bruteforce_removal():
    """``u_x`` must equal the numerator lost by removing exactly dot ``x``, for every dot."""
    dots = _field()
    u, st = ME.marginal_credit(dots)
    rows, cols = np.nonzero(dots)
    brute = []
    for i, (r, c) in enumerate(zip(rows, cols)):
        total = 0.0
        for rr in range(max(0, r - 3), min(dots.shape[0], r + 4)):
            for cc in range(max(0, c - 3), min(dots.shape[1], c + 4)):
                mine = max(1.0 - float(np.hypot(rr - r, cc - c)) / ME.R_PX, 0.0)
                if mine <= 0:
                    continue
                other = 0.0
                for j, (r2, c2) in enumerate(zip(rows, cols)):
                    if j == i:
                        continue
                    other = max(other, max(1.0 - float(np.hypot(rr - r2, cc - c2)) / ME.R_PX, 0.0))
                total += max(mine - other, 0.0)
        brute.append(total)
    assert u == pytest.approx(np.array(brute), abs=1e-6)
    assert u.max() <= st["disc_kernel_sum"] + 1e-9
    assert st["disc_cells"] == 29
    assert st["disc_kernel_sum"] == pytest.approx(
        float(np.maximum(1 - np.hypot(*np.mgrid[-3:4, -3:4]) / 3.0, 0).sum()), abs=1e-5)


def test_isolated_dot_keeps_its_whole_disc_and_a_close_pair_splits_credit():
    lone = np.zeros((40, 40), bool)
    lone[20, 20] = True
    u, st = ME.marginal_credit(lone)
    assert u[0] == pytest.approx(st["disc_kernel_sum"], abs=1e-6)
    pair = np.zeros((40, 40), bool)
    pair[20, 20] = True
    pair[20, 22] = True
    u2, st2 = ME.marginal_credit(pair)
    assert u2[0] == pytest.approx(u2[1], abs=1e-6)          # symmetric
    assert u2.max() < st["disc_kernel_sum"]                 # credit is shared, not doubled
    assert st2["overlap_writeoff_fraction"] > 0.0


def test_exact_terms_match_the_shared_metric_implementation():
    """T, M and DTI must agree with ``vendor/gems57/metric.py`` on a synthetic truth raster."""
    dots = _field(shape=(60, 60), pts=((10, 10), (10, 12), (30, 30), (31, 33)))
    truth = np.zeros((60, 60), bool)
    truth[9, 11] = truth[30, 31] = truth[45, 45] = True
    got = ME.exact_terms(dots, truth)
    oracle = metric.dti_exact(dots.astype(np.float32), truth.astype(np.float32))
    assert got["T"] == pytest.approx(oracle["tp"], abs=1e-4)
    assert got["dti"] == pytest.approx(oracle["dti"], abs=1e-7)


def test_selection_drops_the_least_unique_dots_and_is_deterministic():
    dots = _field(shape=(60, 70), pts=((10, 10), (10, 11), (35, 50)))
    u, _ = ME.marginal_credit(dots)
    sel, st = ME.select_lowest_marginal(dots, 1)
    assert int(sel.sum()) == 1
    # the isolated dot keeps a full disc, the close pair cannot both
    assert u[2] > u[0]
    assert sel[10, 10] or sel[10, 11]
    sel2, _ = ME.select_lowest_marginal(dots, 1)
    assert np.array_equal(sel, sel2)


def test_add_arms_hold_the_kernel_floor_and_clearance():
    ctx = _ctx()
    parent = np.zeros(ctx["footprint"].shape, bool)
    r, c = np.nonzero(ctx["footprint"])
    parent[r[::400], c[::400]] = True
    extend, st_e = ME.add_extension(ctx, parent, 25)
    rnd, st_r = ME.add_random(ctx, parent, 25)
    from scipy import ndimage
    for mask, st in ((extend, st_e), (rnd, st_r)):
        assert st["n_picked"] == int(mask.sum())
        assert not bool((mask & parent).any())
        assert not bool((mask & ctx["catalogue"]).any())
        edt_parent = ndimage.distance_transform_edt(~parent)
        assert float(edt_parent[mask].min()) >= ME.R_PX - 1e-9
        from scipy.spatial import cKDTree
        pts = np.argwhere(mask).astype(np.float64)
        if len(pts) > 1:
            assert float(cKDTree(pts).query(pts, k=2)[0][:, 1].min()) >= ME.R_PX - 1e-9
    # the extend arm's admissible set is a strict subset of the random arm's window
    assert st_e["admissible_cells"] <= st_r["candidate_cells"]


def test_mass_bar_reproduces_the_two_thresholds():
    bar = ME.mass_bar(0.2778)
    assert bar["alpha_dti"] == pytest.approx(0.05556, abs=1e-5)
    assert bar["add_bar_nonredundant_dot"]["max_distance_px"] == pytest.approx(2.8333, abs=1e-3)
    assert bar["remove_bar"]["coefficient_on_fp_charge"] == pytest.approx(0.0588, abs=1e-3)


def _ctx() -> dict:
    """Small synthetic grid: the tests must not need the pinned competition rasters."""
    shape = (90, 100)
    foot = np.zeros(shape, bool)
    foot[2:-2, 2:-2] = True
    cat = np.zeros(shape, bool)
    cat[45, 3:-3] = True
    return {"footprint": foot, "catalogue": cat,
            "grid": {"shape": shape, "dtype": "float32"},
            "sample_path": "", "catalogue_path": ""}
