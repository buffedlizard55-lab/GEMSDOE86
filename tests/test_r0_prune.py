"""Unit and pinned-data checks for the R0 PRUNE experiment."""
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems57 import metric
from scripts.build_r0_prune import (
    PATHS, build_prune_refill, original_visit_rank, read_binary, reconstruct_r0,
)

ROOT = Path(__file__).resolve().parents[1]


def test_binary_dti_algebra_matches_exact_metric():
    rng = np.random.default_rng(306)
    for _ in range(8):
        truth = rng.random((19, 23)) < 0.08
        pred = rng.random((19, 23)) < 0.11
        if not truth.any() or not pred.any():
            continue
        result = metric.dti_binary(pred, truth)
        # T is truth coverage, S is emitted unit mass, M is dot self-credit.
        t = result["tp"]
        s = float(pred.sum())
        m = s - result["fp"]
        k = float(truth.sum())
        algebraic = t / (0.2 * t + 0.2 * (s - m) + 0.8 * k + metric.EPS)
        assert algebraic == pytest.approx(result["dti"], rel=1e-12, abs=1e-12)


def test_fifo_rank_is_unique_on_support_and_deterministic():
    mask = np.zeros((17, 19), bool)
    mask[2:14, 4] = True
    mask[6, 4:15] = True
    mask[15, 16] = True
    first = original_visit_rank(mask)
    second = original_visit_rank(mask)
    assert np.array_equal(first, second)
    assert (first[~mask] == -1).all()
    ranks = np.sort(first[mask])
    assert np.array_equal(ranks, np.arange(mask.sum()))
    # Component seeds and traversal start at the lowest raster index.
    assert first[2, 4] == 0
    assert first[15, 16] == int(mask.sum()) - 1


def test_prune_refill_holds_count_and_excludes_collar():
    footprint = np.ones((25, 25), bool)
    catalogue = np.zeros_like(footprint)
    catalogue[12, 12] = True
    h19 = np.zeros_like(footprint)
    h19[12, 14] = True  # parent dot at d=2
    h19[12, 15] = True  # parent dot at d=3
    h19[0, 0] = True    # retained parent dot
    h19[2, 2] = h19[2, 3] = h19[3, 2] = True  # ranked refills, all d>3
    r0 = h19 & np.isin(np.arange(h19.size).reshape(h19.shape), [12 * 25 + 14, 12 * 25 + 15, 0])
    candidate, stats = build_prune_refill(r0, h19, catalogue, footprint, 3.0)
    distance = ndi.distance_transform_edt(~catalogue)
    assert candidate.sum() == r0.sum() == 3
    assert not (candidate & catalogue).any()
    assert not (candidate & (distance <= 3)).any()
    assert stats["removed_dots"] == 2
    assert stats["added_dots"] == 2
    assert stats["changed_grid_cells"] == 4
    assert stats["pct_changed_vs_parent_dots"] == pytest.approx(100 * 4 / 3)


def test_prune_375_refill_removes_sqrt10_shell_and_holds_count():
    footprint = np.ones((41, 41), bool)
    catalogue = np.zeros_like(footprint)
    catalogue[20, 20] = True
    h19 = np.zeros_like(footprint)
    # R0 contains one dot at 3 px and one at sqrt(10) px, both inside 3.75;
    # two retained dots are farther away. The BFS-ranked H19 cells are also >3.75.
    h19[20, 23] = True
    h19[23, 21] = True
    h19[20, 24] = True
    h19[20, 25] = True
    h19[0, 0] = True
    h19[1, 1] = True
    h19[2, 3] = h19[2, 4] = True
    parent = np.zeros_like(footprint)
    parent[20, 23] = parent[23, 21] = parent[20, 24] = parent[20, 25] = True
    parent[0, 0] = parent[1, 1] = True

    candidate, stats = build_prune_refill(parent, h19, catalogue, footprint, 3.75)
    distance = ndi.distance_transform_edt(~catalogue)
    assert candidate.sum() == parent.sum() == 6
    assert not (candidate & (distance <= 3.75)).any()
    assert stats["removed_dots"] == stats["added_dots"] == 2
    assert stats["changed_grid_cells"] == 4
    assert stats["pct_changed_vs_parent_dots"] == pytest.approx(100 * 4 / 6)


@pytest.mark.skipif(not all(path.is_file() for path in PATHS.values()),
                    reason="pinned R0 experiment inputs are not restored")
def test_pinned_r0_mask_reproduces_exactly():
    import rasterio
    with rasterio.open(PATHS["sample"]) as src:
        footprint = np.isfinite(src.read(1))
    with rasterio.open(PATHS["catalogue"]) as src:
        catalogue = footprint & (src.read(1) > 0.5)
    base = read_binary(PATHS["base"], footprint)
    parent = read_binary(PATHS["parent"], footprint)
    rebuilt = reconstruct_r0(base, catalogue)
    assert np.array_equal(rebuilt, parent)
    assert base.sum() == 40199
    assert (base & ~rebuilt).sum() == 2545
    assert rebuilt.sum() == 37654
