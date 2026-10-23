"""Unit tests for the SPACING axis geometry (``src/gems86/spacing.py``).

These encode the axis contract so a reviewer does not have to: SPACING may only *re-arrange*
mass.  It may not add or delete a dot, put mass on the catalogue, tighten the parent's spacing
floor, let a placement depend on a random draw (except the control arm), or read a band or a
label.  Two of these tests were written after the property failed on an earlier draft.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86 import spacing as S  # noqa: E402


def ctx_for(shape=(40, 40), catalogue=None):
    return {"footprint": np.ones(shape, bool),
            "catalogue": np.zeros(shape, bool) if catalogue is None else catalogue}


def toy():
    """A crowded horizontal line (every dot sub-kernel) plus well-separated anchors."""
    d = np.zeros((40, 40), bool)
    for c in range(4, 36, 2):
        d[20, c] = True
    for r in range(6, 36, 6):
        d[r, 8] = True
        d[r, 32] = True
    return d


def nearest_neighbour(mask):
    p = np.argwhere(mask)
    if len(p) < 2:
        return np.zeros(0)
    return cKDTree(p).query(p, k=2)[0][:, 1]


# --------------------------------------------------------------------- the mechanism measure
def test_disc_offsets_are_the_triangular_support():
    off = S.disc_offsets(3.0)
    assert len(off) == 29                                   # the full-disc ceiling on R0
    assert all(np.hypot(*row) <= 3.0 + 1e-9 for row in off)
    assert len(S.disc_offsets(2.0)) < len(off)


def test_isolated_dots_earn_the_whole_disc():
    d = np.zeros((30, 30), bool)
    d[5, 5] = d[25, 25] = True
    per, st = S.exclusive_credit(d)
    assert list(per) == [len(S.disc_offsets(3.0))] * 2
    assert st["redundancy_fraction"] == pytest.approx(0.0)


def test_adjacent_dots_lose_credit_which_is_exactly_the_redundancy():
    far = np.zeros((10, 40), bool)
    far[5, 5] = far[5, 25] = True
    near = np.zeros((10, 40), bool)
    near[5, 5] = near[5, 7] = True
    p_far, s_far = S.exclusive_credit(far)
    p_near, s_near = S.exclusive_credit(near)
    assert p_near.sum() < p_far.sum()
    assert s_near["redundancy_fraction"] > s_far["redundancy_fraction"] == pytest.approx(0.0)
    assert S.disc_cover(near).sum() < S.disc_cover(far).sum()
    assert s_near["exclusive_cells_total"] == S.disc_cover(near).sum()


# --------------------------------------------------------------------- selection
def test_threshold_selection_needs_no_tie_break():
    d = toy()
    per, _ = S.exclusive_credit(d)
    t = int(np.median(per))
    sel, order, info = S.select_redundant(d, t)
    assert info["n_selected"] == int(sel.sum()) == len(order)
    rows, cols = d.nonzero()
    flat = np.int64(d.shape[1]) * rows + cols
    chosen = np.isin(flat, order)
    assert per[chosen].max() <= t
    if (~chosen).any():
        assert per[~chosen].min() > t             # a count-based cut would have split this class


def test_selection_is_a_nonempty_proper_subset():
    d = toy()
    sel, _o, _i = S.select_redundant(d, 20)
    assert bool((sel & ~d).sum() == 0)
    assert 0 < int(sel.sum()) < int(d.sum())


# --------------------------------------------------------------------- the arms
@pytest.mark.parametrize("law", S.LAWS)
def test_count_is_fixed_and_only_selected_dots_move(law):
    d = toy()
    out, st = S.relocate(d, ctx_for(d.shape), law, 20, window_px=8, seed=3)
    sel, _o, _i = S.select_redundant(d, 20)
    assert int(out.sum()) == int(d.sum()) == st["n_dots_variant"]
    assert st["moved_placed"] + st["moved_unplaced"] == st["moved_target"] == int(sel.sum())
    # every dot outside the selection survives; nothing unselected is deleted or shifted
    assert int(((d & ~sel) & ~out).sum()) == 0
    assert int(((out & ~sel) & ~d).sum()) == st["moved_placed"] - st[
        "destinations_on_vacated_source_cells"]      # destinations are all new cells


@pytest.mark.parametrize("law", S.LAWS)
def test_no_mass_on_the_catalogue_and_new_mass_clears_three_px(law):
    d = toy()
    cat = np.zeros(d.shape, bool)
    cat[3:6, 18:22] = True
    out, _st = S.relocate(d, ctx_for(d.shape, catalogue=cat), law, 20, window_px=8,
                          clearance_px=3.0, seed=3)
    assert int((out & cat).sum()) == 0
    edt = ndi.distance_transform_edt(~cat)
    new = out & ~d
    if new.any():
        assert float(edt[new].min()) > 3.0 - 1e-9


@pytest.mark.parametrize("law", S.LAWS)
def test_floor_respected_and_parent_floor_never_tightened(law):
    d = toy()
    out, st = S.relocate(d, ctx_for(d.shape), law, 20, window_px=8, floor_px=3.0, seed=3)
    p_dist, c_dist = nearest_neighbour(d), nearest_neighbour(out)
    assert c_dist.min() >= min(p_dist.min(), 3.0) - 1e-9     # the arm never tightens the parent
    assert (c_dist < 3.0 - 1e-9).sum() <= (p_dist < 3.0 - 1e-9).sum()   # the axis's whole purpose
    # every cell this arm emits respects the hard core it was given
    new = out & ~d
    if new.any():
        pts_new, pts_all = np.argwhere(new), np.argwhere(out)
        dd, _ii = cKDTree(pts_all).query(pts_new, k=2)
        assert dd[:, 1].min() >= 3.0 - 1e-9


@pytest.mark.parametrize("law", S.LAWS)
def test_displacement_is_local(law):
    """The window is the axis's promise: nothing here is a regional relocation (that is RELIEF)."""
    d = toy()
    out, st = S.relocate(d, ctx_for(d.shape), law, 20, window_px=6, seed=3)
    if st["moved_placed"]:
        assert st["max_displacement_px"] <= 2 * 6 + 1e-9     # window, or one widening of it


def test_lattice_is_a_verified_covering():
    lat = S.hex_lattice((64, 64))
    assert lat["covers_at_radius"]
    assert lat["interior_max_cell_to_node_px"] <= S.R_PX + 0.5
    assert lat["min_node_separation_px"] > 2.0
    assert lat["spacing_px"] <= S.HEX_SPACING_PX + 1e-9


def test_lattice_destinations_sit_on_lattice_nodes():
    d = toy()
    out, _st = S.relocate(d, ctx_for(d.shape), "lattice", 20, window_px=8, seed=3)
    nodes = S.hex_lattice(d.shape)["mask"]
    new = out & ~d
    if new.any():
        assert bool(nodes[new].all())


def test_strike_arm_stays_on_its_ridge_unless_it_reports_a_fallback():
    d = np.zeros((40, 60), bool)
    for c in range(4, 56, 2):
        d[20, c] = True                                      # a straight, crowded line
    out, st = S.relocate(d, ctx_for(d.shape), "strike", 20, window_px=8, seed=3)
    new = out & ~d
    if int(new.sum()) and st["strike_fallback_isotropic"] == 0:
        rows = np.unique(np.nonzero(new)[0])
        # the law's promise is the stated across-trace tolerance, not the exact row
        assert int(np.abs(rows - 20).max()) <= 1, "an on-trace law must stay within across_tol"
        assert int(new.sum()) == st["moved_placed"]


def test_ridge_axes_find_a_horizontal_trace():
    d = np.zeros((30, 30), bool)
    d[15, 4:26] = True
    vec, coh = S.ridge_axes(d, k=8)
    assert np.all(np.abs(vec[:, 1]) > 0.9)                   # unit vector along columns
    assert np.all(coh > 0.5)                                 # perfectly line-like neighbourhood


def test_reproducibility_and_control_seed_sensitivity():
    d = toy()
    a, _ = S.relocate(d, ctx_for(d.shape), "random", 20, window_px=8, seed=11)
    b, _ = S.relocate(d, ctx_for(d.shape), "random", 20, window_px=8, seed=11)
    c, _ = S.relocate(d, ctx_for(d.shape), "random", 20, window_px=8, seed=12)
    assert bool((a == b).all())
    assert not bool((a == c).all())                          # the control really is a draw
    for law in ("pdisk", "lattice", "strike"):
        x, _ = S.relocate(d, ctx_for(d.shape), law, 20, window_px=8, seed=11)
        y, _ = S.relocate(d, ctx_for(d.shape), law, 20, window_px=8, seed=999)
        assert bool((x == y).all()), f"{law} must not depend on the seed"


def test_unplaced_dots_stay_put_and_are_counted():
    d = np.zeros((12, 12), bool)
    d[5, 4] = d[5, 5] = d[5, 6] = d[5, 7] = True             # crowded, and no room in a 1 px window
    out, st = S.relocate(d, ctx_for(d.shape), "lattice", 20, window_px=1, seed=3)
    assert int(out.sum()) == int(d.sum())
    assert st["moved_unplaced"] + st["moved_placed"] == st["moved_target"]


def test_guards():
    with pytest.raises(ValueError):
        S.relocate(toy(), ctx_for(), "pdisk", 5, floor_px=2.0)     # tightens the parent's floor
    with pytest.raises(ValueError):
        S.relocate(toy(), ctx_for(), "magnetism", 5)               # not a spacing law
    with pytest.raises(ValueError):
        S.exclusive_credit(np.zeros((5, 5), bool))                 # empty field


# --------------------------------------------------------------------- parent identity
FLEET = ROOT / "data" / "scored_fleet"
PARENT = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
BASE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
BRIDGE = ROOT / "data" / "bridge"


@pytest.mark.skipif(not (PARENT.is_file() and BASE.is_file() and (BRIDGE / "existing_faults.tif").is_file()),
                    reason="pinned parent/base rasters are not in this checkout")
def test_r0_is_reproducible_from_the_pinned_base_by_the_two_px_prune():
    """The lineage step R0 was made of, re-executed - the brief's stop condition, in CI."""
    import rasterio

    foot = np.isfinite(rasterio.open(BRIDGE / "sample_submission.tif").read(1))
    cat = rasterio.open(BRIDGE / "existing_faults.tif").read(1) == 1
    base = rasterio.open(BASE).read(1)
    parent = rasterio.open(PARENT).read(1)
    rebuilt = (np.nan_to_num(base, nan=0.0) > 0) & foot & (ndi.distance_transform_edt(~cat) > 2.0)
    assert rebuilt.shape == parent.shape
    assert int((rebuilt != ((np.nan_to_num(parent, nan=0.0) > 0) & foot)).sum()) == 0
    assert int(rebuilt.sum()) == 37_654


def test_parent_diff_reports_both_readings_of_changed():
    d = toy()
    out, st = S.relocate(d, ctx_for(d.shape), "pdisk", 20, window_px=8, seed=3)
    diff = S.parent_diff(d, out, np.ones(d.shape, bool))
    assert diff["count_delta"] == 0
    assert diff["dropped"] == diff["added"]
    # a relocation changes two cells (the vacated source and the new destination), except where a
    # later dot re-uses a cell an earlier one vacated: that cell is unchanged in the final set
    reuse = st["destinations_on_vacated_source_cells"]
    assert diff["dots_changed"] == 2 * (st["moved_placed"] - reuse)
    assert diff["dropped"] == diff["added"] == st["moved_placed"] - reuse
    assert diff["pct_changed_of_parent"] == pytest.approx(diff["dots_changed"] * 100.0
                                                           / diff["parent_dots"], abs=1e-3)
    assert diff["shared_dots"] == diff["parent_dots"] - diff["dropped"]
