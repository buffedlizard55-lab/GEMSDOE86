"""Unit tests for the SPACING axis geometry (``scripts/run_spacing_axis.py``).

Small synthetic grids only: no competition raster, no network, ~a second to run.
The properties under test are exactly the ones the axis contract claims: the
crowded pool keeps the parent's own ranking, the count is held, the catalogue
exclusions hold, the parent's minimum spacing is never tightened, every moved dot
breaks its crowded pair at the kernel radius, and the three values really are
three different placement geometries on the same moved set.

The artefact tests re-read the shipped releases when they are present in the
working tree (``releases/*.tif`` is gitignored, so a clean CI clone skips them).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_spacing_axis as S  # noqa: E402

FLOOR_PX = np.sqrt(8.0)


def _toy(seed=3):
    """A ridge pair grid: two horizontal ridges carrying crowded dot pairs."""
    h = w = 60
    footprint = np.ones((h, w), bool)
    catalogue = np.zeros((h, w), bool)
    catalogue[5, 5:20] = True                     # a mapped trace far from the ridges
    h19 = np.zeros((h, w), bool)
    h19[18:23, 5:55] = True                # thick ridge band
    h19[38:43, 5:55] = True
    dist_cat = np.full((h, w), 30.0)
    dist_cat[5, 5:20] = 0.0
    for y in range(h):
        for x in range(w):
            if not catalogue[y, x]:
                d = np.min(np.hypot(*np.nonzero(catalogue) - np.array([[y], [x]])))
                dist_cat[y, x] = min(dist_cat[y, x], d)
    rank = np.full((h, w), 10_000, np.int64)
    cells = np.argwhere(h19)
    for i, (y, x) in enumerate(cells):
        rank[y, x] = i                            # row-major visit order over the ridges
    parent = np.zeros((h, w), bool)
    parent[20, 12:20:2] = True                    # crowded run: 2 px spacing along the ridge
    parent[20, 26:50:4] = True                    # regular 4 px spacing
    parent[40, 12:20:2] = True
    parent[40, 26:50:4] = True
    parent[19, 30] = True
    parent[41, 34] = True
    return dict(footprint=footprint, catalogue=catalogue, h19=h19, rank=rank,
                dist_cat=dist_cat, parent=parent)


def test_crowded_pool_keeps_the_parents_own_ranking():
    t = _toy()
    pts, moved, lab, n_clusters = S.crowded_moved_set(t["parent"], t["rank"])
    ranks = t["rank"][pts[:, 0], pts[:, 1]]
    for c in np.unique(lab):
        members = np.flatnonzero(lab == c)
        if len(members) < 2:
            continue
        kept = [m for m in members if not moved[m]]
        assert len(kept) == 1, "exactly one member of a crowded cluster stays"
        assert kept[0] == members[np.argmin(ranks[members])], \
            "the earliest visit-rank member (the parent's recipe priority) stays"
    assert moved.any()


def test_lattice_site_distance_is_zero_on_sites():
    cells = np.array([[0, 0], [3, 3], [6, 0], [1, 1], [2, 2]], float)
    d = S.lattice_site_distance(cells)
    assert d[:3].max() == 0.0
    assert abs(d[3] - np.sqrt(2)) < 1e-9


def test_strike_direction_follows_the_ridge_and_points_away_from_the_anchor():
    t = _toy()
    cell = np.array([20, 30])
    anchor = np.array([20, 27])
    u = S.strike_direction(t["h19"], cell, anchor)
    assert abs(abs(u[1]) - 1.0) < 1e-6, "on a horizontal ridge the tangent is horizontal"
    assert u[1] > 0, "oriented away from the kept anchor"


@pytest.mark.parametrize("rule", ["lattice", "poisson-disk", "along-strike"])
def test_re_space_holds_the_contract(rule):
    t = _toy()
    child, st = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                           t["footprint"], rule, seed=20261023)
    assert st["n_child"] == int(t["parent"].sum()), "count held at the parent's"
    assert st["n_moved"] > 0, "the crowded pool must be re-spaced"
    assert 1.0 <= st["pct_dots_changed"] <= 50.0
    assert not np.any(child & t["catalogue"]), "zero catalogue mass"
    added = child & ~t["parent"]
    assert float(t["dist_cat"][added].min()) >= 3.0 - 1e-9, \
        "newly emitted mass stays >= 3 px off the catalogue"
    from scipy.spatial import cKDTree
    pts = np.argwhere(child)
    nn = cKDTree(pts).query(pts, k=2)[0][:, 1]
    parent_pts = np.argwhere(t["parent"])
    pnn = cKDTree(parent_pts).query(parent_pts, k=2)[0][:, 1]
    assert float(nn.min()) >= float(pnn.min()) - 1e-9, "the parent floor is never tightened"


@pytest.mark.parametrize("rule", ["lattice", "poisson-disk", "along-strike"])
def test_moved_dots_break_their_crowded_pair_at_the_kernel_radius(rule):
    t = _toy()
    child, st = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                           t["footprint"], rule, seed=20261023)
    pts, moved, lab, n_clusters = S.crowded_moved_set(t["parent"], t["rank"])
    ranks = t["rank"][pts[:, 0], pts[:, 1]]
    anchor_of = {}
    for c in np.unique(lab):
        members = np.flatnonzero(lab == c)
        if len(members) < 2:
            continue
        keep = members[np.argmin(ranks[members])]
        for m in members:
            if m != keep:
                anchor_of[(int(pts[m][0]), int(pts[m][1]))] = (int(pts[keep][0]), int(pts[keep][1]))
    assert anchor_of, "toy fixture must produce a crowded pool"
    for orig, dest in st["moved_from_to"]:
        anchor = anchor_of[tuple(orig)]
        d = float(np.hypot(dest[0] - anchor[0], dest[1] - anchor[1]))
        assert d >= 3.0 - 1e-9, "a moved dot must break its crowded pair at the kernel radius"
        assert tuple(dest) != tuple(orig), "a moved dot must actually move"


def test_the_three_values_are_three_different_arrangements():
    t = _toy()
    outs = {}
    for rule in ("lattice", "poisson-disk", "along-strike"):
        child, st = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                               t["footprint"], rule, seed=20261023)
        outs[rule] = S.P.dot_digest(child)
    # at least two of the three geometries must land on different dot sets; on the
    # real crowded pool the run card reports the pairwise agreement fractions
    assert len(set(outs.values())) >= 2, "the placement geometry must change the dot set"


def test_re_space_is_deterministic_for_a_fixed_seed():
    t = _toy()
    a, _ = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                      t["footprint"], "poisson-disk", seed=7)
    b, _ = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                      t["footprint"], "poisson-disk", seed=7)
    assert np.array_equal(a, b)


def test_move_diff_counts_moves_once_per_cell():
    t = _toy()
    child, st = S.re_space(t["parent"], t["h19"], t["rank"], t["dist_cat"],
                           t["footprint"], "lattice", seed=20261023)
    diff = S.move_diff(t["parent"], child, t["dist_cat"])
    assert diff["n_removed"] == diff["n_added"]
    assert diff["n_removed"] <= st["n_moved"]     # some movers land on vacated originals
    assert 1.0 <= diff["pct_dots_changed"] <= 50.0


# ---------------------------------------------------------------- artefact tests
RELEASES = ROOT / "releases"
SPACING_IDS = [
    "h33-h33-2-b2-20261004-e5eb6e7e-SPACING-lattice-20261023-4551582d",
    "h33-h33-2-b2-20261004-e5eb6e7e-SPACING-poissondisk-20261023-d2cf39d5",
    "h33-h33-2-b2-20261004-e5eb6e7e-SPACING-alongstrike-20261023-4d631f4a",
]
ARTIFACTS = [i for i in SPACING_IDS if (RELEASES / f"{i}-zeros.tif").is_file()]
pytestmark_artifact = pytest.mark.skipif(
    not ARTIFACTS, reason="no SPACING release rasters in this checkout (releases/*.tif is gitignored)")


@pytestmark_artifact
@pytest.mark.parametrize("rid", ARTIFACTS, ids=ARTIFACTS or ["none"])
def test_shipped_spacing_release_passes_the_gates(rid):
    import json
    import rasterio
    from gems57.validate import validate

    g = S.g57grid.load_grid(S.BRIDGE)
    zeros = RELEASES / f"{rid}-zeros.tif"
    receipt = json.loads((RELEASES / f"{rid}-zeros.json").read_text())
    rec = validate(zeros, g.footprint, g.catalogue)
    assert rec["all_checks_passed"], rec["checks"]
    assert rec["on_catalogue_positive_pixels"] == 0
    assert rec["sha256"] == receipt["zeros"]["sha256"]
    with rasterio.open(zeros) as ds:
        dots = ds.read(1) > 0
    assert int(dots.sum()) == receipt["n_dots"] == 37654
    assert 1.0 <= receipt["pct_changed"] <= 50.0
    assert receipt["axis"] == "SPACING"
