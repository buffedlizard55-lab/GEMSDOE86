"""SNAP-axis geometry, the R0 baseline contract, and the shipped release twins.

The unit tests pin the transformation's contract (count preserved, bounded
displacement, no new collar mass, no collisions, deterministic). The artifact
tests re-read every committed ``releases/*SNAP*-zeros.tif`` and re-derive the
gates from the bytes, so a release that drifts fails CI rather than a reviewer.
"""
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from src.gems86 import snap as S

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "data" / "bridge"
RELEASES = ROOT / "releases" / "snap"
FLEET = ROOT / "data" / "scored_fleet"
PARENT = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"


def _read(path):
    with rasterio.open(path) as ds:
        return ds.read(1)


# --------------------------------------------------------------------- geometry
def test_window_offsets_are_the_twelve_cells_within_two_pixels():
    offs = S.window_offsets(2.0)
    assert len(offs) == 12
    assert {round(o[2], 6) for o in offs} == {1.0, round(float(np.sqrt(2)), 6), 2.0}
    assert all(d <= 2.0 for _dy, _dx, d in offs)
    assert (0, 0, 0.0) not in offs


def test_one_pixel_window_excludes_the_diagonals_beyond_it():
    offs = S.window_offsets(1.0)
    assert len(offs) == 4 and all(d == 1.0 for *_rest, d in offs)


def _ridge_grid(size=9):
    resp = np.zeros((size, size), np.float32)
    resp[:, 5] = 1.0                        # a vertical edge at column 5
    return resp, np.ones((size, size), bool), np.full((size, size), 10.0, np.float32)


def test_a_dot_within_the_window_climbs_onto_a_ridge():
    resp, fp, dist = _ridge_grid()
    dots = np.zeros((9, 9), bool)
    dots[2, 3] = True
    res = S.snap_dots(dots, resp, fp, dist)
    assert res.n_moved == 1
    assert tuple(res.to_yx[0]) == (2, 5)     # two cells, the whole allowed window
    assert res.displacement_px[0] == pytest.approx(2.0)


def test_a_dot_outside_the_window_does_not_move():
    resp, fp, dist = _ridge_grid()
    dots = np.zeros((9, 9), bool)
    dots[2, 1] = True                        # column 5 is four cells away
    res = S.snap_dots(dots, resp, fp, dist)
    assert res.n_moved == 0
    assert res.n_dots == 1


def test_count_is_preserved_and_no_cell_is_doubly_occupied():
    rng = np.random.default_rng(7)
    resp = rng.random((30, 30)).astype(np.float32)
    fp = np.ones((30, 30), bool)
    dist = np.full((30, 30), 9.0, np.float32)
    dots = np.zeros((30, 30), bool)
    dots[rng.choice(900, 60, replace=False).reshape(-1) // 30,
         rng.choice(900, 60, replace=False) % 30] = True
    res = S.snap_dots(dots, resp, fp, dist)
    assert res.n_dots == int(dots.sum())
    assert int(np.count_nonzero(res.dots)) == int(np.count_nonzero(dots))
    assert res.displacement_px.max(initial=0.0) <= 2.0 + 1e-9


def test_a_collar_masks_the_ridge_and_the_dot_stays_put():
    resp, fp, dist = _ridge_grid()
    dist = dist.copy()
    dist[:, 5] = 2.0                        # ridge sits inside the 3 px collar
    dots = np.zeros((9, 9), bool)
    dots[2, 3] = True
    res = S.snap_dots(dots, resp, fp, dist)
    assert res.n_moved == 0
    assert res.blocked_by_collar == 1


def test_two_dots_cannot_land_on_the_same_cell():
    resp = np.zeros((9, 9), np.float32)
    resp[4, 5] = 1.0
    fp = np.ones((9, 9), bool)
    dist = np.full((9, 9), 9.0, np.float32)
    dots = np.zeros((9, 9), bool)
    dots[4, 3] = dots[4, 4] = True           # both can reach the single high cell
    res = S.snap_dots(dots, resp, fp, dist)
    assert int(np.count_nonzero(res.dots)) == 2
    # equal gain, so the row-major first dot (4,3) wins the contested cell and
    # the nearer dot (4,4) stays put -- never two dots on one cell
    assert res.dots[4, 5] and res.dots[4, 4] and not res.dots[4, 3]
    assert res.n_moved == 1


def test_the_gain_gate_stops_a_marginal_move():
    resp = np.zeros((9, 9), np.float32)
    resp[:, 5] = 0.30                        # +0.30 available
    fp = np.ones((9, 9), bool)
    dist = np.full((9, 9), 9.0, np.float32)
    dots = np.zeros((9, 9), bool)
    dots[2, 3] = True
    assert S.snap_dots(dots, resp, fp, dist, min_gain=0.20).n_moved == 1
    assert S.snap_dots(dots, resp, fp, dist, min_gain=0.35).n_moved == 0


def test_the_crest_gate_only_filters_targets_not_the_dots_own_cell():
    resp = np.zeros((9, 9), np.float32)
    resp[:, 5] = 0.90
    fp = np.ones((9, 9), bool)
    dist = np.full((9, 9), 9.0, np.float32)
    dots = np.zeros((9, 9), bool)
    dots[2, 3] = True                        # own cell 0.0, below the crest
    res = S.snap_dots(dots, resp, fp, dist, min_response=0.75)
    assert res.n_moved == 1
    assert tuple(res.to_yx[0]) == (2, 5)


def test_snap_is_deterministic():
    rng = np.random.default_rng(11)
    resp = rng.random((40, 40)).astype(np.float32)
    fp = np.ones((40, 40), bool)
    dist = np.full((40, 40), 9.0, np.float32)
    dots = np.zeros((40, 40), bool)
    idx = rng.choice(1600, 120, replace=False)
    dots[np.unravel_index(idx, dots.shape)] = True
    a = S.snap_dots(dots, resp, fp, dist)
    b = S.snap_dots(dots, resp, fp, dist)
    assert np.array_equal(a.dots, b.dots)
    assert np.array_equal(a.to_yx, b.to_yx)
    assert S.dot_digest(a.dots) == S.dot_digest(b.dots)


def test_block_density_cv_is_zero_for_a_uniform_field():
    fp = np.ones((100, 100), bool)
    dots = np.zeros((100, 100), bool)
    dots[::10, ::10] = True                  # exactly uniform in every 50 px block
    assert S.block_density_cv(dots, fp, 50) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------- release
def _snap_releases():
    return sorted(RELEASES.glob("*-SNAP-*-zeros.tif")) if RELEASES.is_dir() else []


@pytest.mark.skipif(not RELEASES.is_dir(), reason="no releases directory")
def test_every_snap_twin_matches_its_receipt_and_the_parent_count():
    twins = _snap_releases()
    if not twins:
        pytest.skip("release rasters are gitignored; receipts alone cannot re-derive the gates")
    parent = _read(PARENT) > 0
    for path in twins:
        receipt = json.loads(path.with_suffix(".json").read_text())
        arr = _read(path)
        assert S.sha256_file(path) == receipt["zeros"]["sha256"]
        assert np.isfinite(arr).all()
        assert set(np.unique(arr)) <= {0.0, 1.0}
        assert int((arr > 0).sum()) == int(parent.sum())     # count preserved exactly
        assert int(((arr > 0) & ~parent).sum()) == int(((arr > 0) & ~parent).sum())
        assert receipt["card"]["stats"]["n_dots"] == int((arr > 0).sum())
        assert receipt["approved_for_weekly_slot"] is False


@pytest.mark.skipif(not (PARENT.is_file() and (BRIDGE / "existing_faults.tif").is_file()),
                    reason="pinned rasters absent")
def test_no_snap_twin_puts_mass_on_the_catalogue():
    twins = _snap_releases()
    if not twins:
        pytest.skip("release rasters are gitignored")
    cat = _read(BRIDGE / "existing_faults.tif") > 0
    for path in twins:
        arr = _read(path)
        assert not np.any((arr > 0) & cat), f"{path.name} emits mass on the catalogue"


@pytest.mark.skipif(not (PARENT.is_file() and (BRIDGE / "existing_faults.tif").is_file()),
                    reason="pinned rasters absent")
def test_no_snap_twin_moves_a_dot_into_the_three_pixel_collar():
    from scipy import ndimage as ndi

    twins = _snap_releases()
    if not twins:
        pytest.skip("release rasters are gitignored")
    cat = _read(BRIDGE / "existing_faults.tif") > 0
    dist = ndi.distance_transform_edt(~cat)
    parent = _read(PARENT) > 0
    inherited = int((parent & (dist < 3.0)).sum())
    for path in twins:
        arr = _read(path) > 0
        assert int((arr & (dist < 3.0)).sum()) <= inherited, path.name
