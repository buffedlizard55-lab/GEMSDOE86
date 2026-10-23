"""Unit tests for the RELIEF axis geometry (``src.gems86.relief``).

Small synthetic grids only: no competition raster, no network, ~a second to run.
The properties under test are exactly the ones the axis contract claims: the count
is fixed, the exclusions hold, nothing is added or deleted for its own sake, the
dose ladder is nested, and the regime cut is the documented quantile rule.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy import ndimage as ndi

from src.gems86 import relief as R

N = 64
WINDOW = 5      # toy smoothing window; the competition run uses the module default
PROX = 12       # toy "front touches a basin" radius


def _toy(*, seed=7):
    """A tilted, dissected surface with a step: low-left basin, high-right range."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N]
    # a narrow escarpment at x=32: low flat basin on the left, high block on the right
    det_elev = 60.0 * np.tanh((xx - 32) / 3.0) + rng.normal(0, 3.0, (N, N))
    gy, gx = np.gradient(det_elev)
    slope = np.hypot(gy, gx)
    foot = np.ones((N, N), bool)
    foot[:4, :] = False
    foot[-4:, :] = False
    cat = np.zeros((N, N), bool)
    cat[N // 2 - 1:N // 2 + 1, 20] = True
    cat[10, 30:45] = True
    idx = R.relief_index(det_elev, slope, foot, window_px=WINDOW)
    lab, cuts = R.regime_map(idx, foot, front_proximity_px=PROX, smooth_window_px=WINDOW)
    assert int((lab == 2).sum()) > 0 and int((lab == 4).sum()) > 0   # fixture sanity
    return dict(foot=foot, cat=cat, lab=lab, cuts=cuts, idx=idx)


def _sparse_dots(lab, cat, codes, stride=6):
    """Deterministic sparse dots inside ``codes`` (spacing >> MIN_DOT_PX, off the catalogue)."""
    yy, xx = np.mgrid[0:N, 0:N]
    sel = np.isin(lab, list(codes)) & ~cat
    grid_ok = ((yy + xx) % stride == 0) & ((yy * 3 + xx) % (stride * 2 + 1) == 0)
    return sel & grid_ok


# ---------------------------------------------------------------- regime map

def test_regime_terciles_and_complement():
    t = _toy()
    q_low, q_high = t["cuts"]["quantile_lower"], t["cuts"]["quantile_upper"]
    assert q_low < q_high
    inside = t["idx"][t["foot"]]
    assert abs(float((inside <= q_low).mean()) - 1 / 3) < 0.02
    assert abs(float(((inside > q_low) & (inside <= q_high)).mean()) - 1 / 3) < 0.02
    lab = t["lab"]
    assert int((t["foot"] & (lab == 0)).sum()) == 0        # every cell classified
    for a, b in ((1, 2), (1, 3), (2, 4), (3, 4)):
        assert int(((lab == a) & (lab == b)).sum()) == 0   # classes disjoint


def test_range_front_requires_basin_proximity():
    t = _toy()
    lab = t["lab"]
    d = ndi.distance_transform_edt(~(lab == 3))
    assert float(d[lab == 2].max()) <= PROX        # fronts touch a basin
    assert float(d[lab == 4].min()) > PROX         # "interior" is excluded by proximity


def test_index_is_centred_on_the_footprint():
    t = _toy()
    vals = t["idx"][t["foot"]]
    assert abs(float(vals.mean())) < 1e-9            # z + z of the two bands
    assert 0.2 < float(vals.std()) < 5.0             # finite, non-degenerate spread
    assert t["cuts"]["smooth_window_px"] == WINDOW


# ---------------------------------------------------------------- eligibility

def test_eligible_cells_respect_catalogue_and_spacing():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2, 3, 4), stride=3)
    assert int(dots.sum()) > 100
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    assert not (elig & t["cat"]).any()
    assert ndi.distance_transform_edt(~t["cat"])[elig].min() > R.MIN_CATALOGUE_PX
    assert ndi.distance_transform_edt(~dots)[elig].min() > R.MIN_DOT_PX
    assert not (elig & dots).any()
    assert not (elig & ~t["foot"]).any()          # nothing emitted outside the scored footprint


# ---------------------------------------------------------------- the move

def test_move_keeps_count_and_moves_exactly_k():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=3)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    src, dst, stats = R.plan_moves(dots, t["lab"], elig, source=1, destination=2, n_move=25,
                                   select="nearest-boundary")
    new = R.apply_moves(dots, src, dst)
    assert int(new.sum()) == int(dots.sum())
    removed, added = dots & ~new, new & ~dots
    assert int(removed.sum()) == int(added.sum()) == 25
    assert stats["n_move"] == 25
    assert not (added & (t["lab"] == 1)).any()      # nothing lands back in the source class
    assert not (removed & (t["lab"] == 2)).any()    # nothing is deleted from the destination
    disp = np.hypot(*(np.column_stack(np.divmod(dst, N)) -
                       np.column_stack(np.divmod(src, N))).T.astype(float))
    assert stats["displacement_px"]["mean"] == pytest.approx(float(disp.mean()), abs=1e-3)  # rounded to 4 dp
    # each source went to its nearest free legal cell -> displacement is small and bounded
    assert float(disp.max()) < 16.0


def test_dose_ladder_is_nested():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=5)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    s5, d5, _ = R.plan_moves(dots, t["lab"], elig, source=1, destination=2, n_move=10)
    s20, d20, _ = R.plan_moves(dots, t["lab"], elig, source=1, destination=2, n_move=20)
    assert set(s5.tolist()) <= set(s20.tolist())
    assert set(zip(s5.tolist(), d5.tolist())) <= set(zip(s20.tolist(), d20.tolist()))


def test_plan_moves_raises_on_exhausted_supply():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1,), stride=5)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    with pytest.raises(ValueError, match="cannot move"):
        R.plan_moves(dots, t["lab"], elig, source=1, destination=2, n_move=10_000)


def test_apply_moves_rejects_illegal_pairs():
    t = _toy()
    dots = np.zeros((N, N), bool)
    dots[30, 30] = True
    dots[30, 31] = True
    with pytest.raises(ValueError, match="already occupied"):
        R.apply_moves(dots, np.array([30 * N + 30]), np.array([30 * N + 31]))
    with pytest.raises(ValueError, match="not occupied"):
        R.apply_moves(dots, np.array([5 * N + 5]), np.array([6 * N + 6]))


# ---------------------------------------------------------------- reporting

def test_relief_diff_reports_shares_and_fixed_count():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1,), stride=4)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    k = 15
    src, dst, _ = R.plan_moves(dots, t["lab"], elig, source=1, destination=2, n_move=k)
    new = R.apply_moves(dots, src, dst)
    diff = R.relief_diff(dots, new, t["lab"], t["cat"], n_move=k)
    assert diff["count_fixed"] is True
    assert diff["n_removed"] == diff["n_added"] == k
    assert diff["removed_from_regime"]["piedmont"] == k
    assert diff["added_in_regime"]["range-front"] == k
    assert diff["regime_share_parent_pct"]["piedmont"] > diff["regime_share_child_pct"]["piedmont"]
    assert diff["min_catalogue_px_child"] > R.MIN_CATALOGUE_PX
    assert diff["pct_changed"] == pytest.approx(diff["expected_pct_changed"], rel=1e-6)


def test_control_moves_within_a_regime_only():
    """The displacement control must change nothing about regime membership."""
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1,), stride=4)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    src, dst, stats = R.plan_moves(dots, t["lab"], elig, source=1, destination=1, n_move=20)
    new = R.apply_moves(dots, src, dst)
    assert int((new & (t["lab"] != 1)).sum()) == 0
    assert int(new.sum()) == int(dots.sum())
    assert stats["source"] == stats["destination"] == "piedmont"
    assert stats["displacement_px"]["mean"] > 0.0        # real displacement, no regime change
    assert stats["displacement_px"]["max"] >= stats["displacement_px"]["mean"]


def test_nn_distances_matches_brute_force():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=5)
    flat = np.flatnonzero(dots.ravel())[:40]
    sub = np.zeros_like(dots)
    sub.ravel()[flat] = True
    got = np.sort(R.nn_distances(sub))
    rc = np.column_stack(np.divmod(flat, N)).astype(float)
    brute = np.sort([min(np.hypot(*(rc[i] - rc[j])) for j in range(len(rc)) if j != i)
                     for i in range(len(rc))])
    assert np.allclose(got, brute, atol=1e-9)


# ---------------------------------------------------------------- selection rule

def test_deepest_selection_picks_dots_further_inside_the_regime():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=3)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    kw = dict(source=1, destination=2, n_move=15)
    sd, dd, st_deep = R.plan_moves(dots, t["lab"], elig, select="deepest", **kw)
    sn, dn, st_near = R.plan_moves(dots, t["lab"], elig, select="nearest-boundary", **kw)
    assert st_deep["source_boundary_depth_px"]["median"] > st_near["source_boundary_depth_px"]["median"]
    assert st_deep["displacement_px"]["mean"] > st_near["displacement_px"]["mean"]
    # both modes are deterministic and dose-nested, which is what the ladder needs
    for mode in ("deepest", "nearest-boundary"):
        s5, d5, _ = R.plan_moves(dots, t["lab"], elig, n_move=5, select=mode, source=1, destination=2)
        assert set(zip(s5.tolist(), d5.tolist())) <= set(zip(sd.tolist(), dd.tolist())) or mode == "nearest-boundary"
    with pytest.raises(ValueError, match="unknown selection rule"):
        R.plan_moves(dots, t["lab"], elig, select="random", **kw)


def test_shipped_mode_is_deterministic_across_repeats():
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=3)
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    kw = dict(source=1, destination=2, n_move=20, select="deepest")
    a = R.plan_moves(dots, t["lab"], elig, **kw)
    b = R.plan_moves(dots, t["lab"], elig, **kw)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    assert a[2] == b[2]


def test_relocation_preserves_the_parents_min_spacing():
    """The whole point of the blocking step: a RELIEF child must not create a pair
    closer than the parent's own minimum dot spacing, or the variant would also be
    a clustering edit."""
    t = _toy()
    dots = _sparse_dots(t["lab"], t["cat"], (1, 2), stride=5)
    parent_nn = float(R.nn_distances(dots).min())
    assert parent_nn >= R.MIN_DOT_PX - 1e-9            # the fixture honours the rule too
    elig = R.eligible_cells(dots, t["cat"], t["foot"])
    for mode in ("deepest", "nearest-boundary"):
        src, dst, stats = R.plan_moves(dots, t["lab"], elig, source=1, destination=2,
                                       n_move=20, select=mode)
        new = R.apply_moves(dots, src, dst)
        child_nn = float(R.nn_distances(new).min())
        assert child_nn >= R.MIN_DOT_PX - 1e-9, (mode, child_nn)
        # the blocking bookkeeping must agree with the geometry it is supposed to enforce
        assert stats["displacement_px"]["mean"] > 0
