"""Instrument identity: the shared draw must reproduce the published positive count."""
import pytest
from gems57.grid import load_grid
from src.gems86 import instrument
from conftest import BRIDGE

pytestmark = pytest.mark.skipif(not (BRIDGE / "existing_faults.tif").is_file(),
                                reason="bridge rasters absent")


def test_withheld_positive_count():
    g = load_grid(BRIDGE)
    folds = instrument.build(g.footprint, g.catalogue)
    assert len(folds) == 4
    assert sum(int(f.truth.sum()) for f in folds) == 11321


def test_no_truth_on_visible_and_buffer():
    import numpy as np
    from scipy import ndimage as ndi
    g = load_grid(BRIDGE)
    folds = instrument.build(g.footprint, g.catalogue)
    for f in folds:
        assert not np.any(f.truth & f.visible)
        d = ndi.distance_transform_edt(~f.visible)[f.truth]
        assert d.min() > 3.0
