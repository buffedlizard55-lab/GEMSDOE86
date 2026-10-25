"""Synthetic checks for the frozen H86L residual operators. No competition raster."""
from __future__ import annotations

import numpy as np

from gems86_vfgr.features import (
    SIGMA_EDGE_PX,
    basement_mass_balance_surface,
    corroborated_residual_surface,
    fit_edge_residual,
)


def test_visible_fault_residual_keeps_the_unexplained_strand():
    edge = np.zeros((40, 30), np.float32)
    edge[:, 8] = 1.0
    edge[:, 20] = 1.0
    visible = np.zeros_like(edge, bool)
    visible[:20, 8] = True
    dist = np.full(edge.shape, 99.0, np.float32)
    dist[:, 7:10] = 0.0
    dist[:20, 8] = 0.0
    # Distance is to the visible column only. The second strand is unexplained.
    yy = np.arange(40)[:, None]
    dist = np.where(yy < 20, np.abs(np.arange(30) - 8), 99.0).astype(np.float32)
    train = np.zeros_like(edge, bool)
    train[:20, :] = True
    residual, scale = fit_edge_residual(edge, dist, train, sigma=SIGMA_EDGE_PX)
    # A wide Gaussian cannot perfectly erase a one-pixel spike. It must still
    # suppress the visible strand relative to an equal unexplained strand.
    assert scale > 0.0
    assert residual[5, 8] < edge[5, 8]
    assert residual[30, 20] > residual[5, 8]


def test_subtraction_changes_the_surface_and_stays_in_unit_interval():
    rng = np.random.default_rng(7)
    edge = rng.random((48, 48)).astype(np.float32)
    edge[:, 12] += 3.0
    dist = np.abs(np.arange(48) - 12).astype(np.float32)[None, :].repeat(48, axis=0)
    train = np.zeros((48, 48), bool)
    train[:24, :] = True
    footprint = np.ones((48, 48), bool)
    subtracted, meta = corroborated_residual_surface(edge, edge, dist, train, footprint, subtract=True)
    raw, raw_meta = corroborated_residual_surface(edge, edge, dist, train, footprint, subtract=False)
    assert meta["subtract"] is True and raw_meta["a_mag"] == 0.0
    assert subtracted.min() >= 0.0 and subtracted.max() <= 1.0
    assert not np.allclose(subtracted, raw)


def test_basement_residual_removes_a_linear_slab():
    depth = np.linspace(0, 10, 36, dtype=np.float64)[None, :].repeat(36, axis=0)
    gravity = 4.0 + 2.5 * depth
    gravity = gravity.copy()
    gravity[:, 18] += 6.0
    train = np.ones_like(depth, bool)
    train[:, 16:21] = False
    footprint = np.ones_like(depth, bool)
    surface, fit = basement_mass_balance_surface(gravity, depth, train, footprint, sigma=0.5)
    assert fit["training_r2"] > 0.95
    assert abs(fit["slope"] - 2.5) < 0.15
    assert surface.min() >= 0.0 and surface.max() <= 1.0
    assert surface[10, 18] > surface[10, 2]
