"""The shared fail-closed writer: round-trip, refusal, and no silent repair."""
import numpy as np
import pytest

from gems57.submission_writer import write_submission
from gems57.grid import load_grid
from conftest import BRIDGE

pytestmark = pytest.mark.skipif(not (BRIDGE / "sample_submission.tif").is_file(),
                                reason="bridge rasters absent")


def test_roundtrip(tmp_path):
    g = load_grid(BRIDGE)
    p = np.zeros(g.footprint.shape, np.float32)
    ys, xs = np.nonzero(g.footprint)
    p[ys[0], xs[0]] = 1.0
    p[ys[len(ys) // 2], xs[len(xs) // 2]] = 1.0
    rec = write_submission(tmp_path / "t.tif", p, BRIDGE / "sample_submission.tif",
                           g.footprint, note="unit test", name="unit-test",
                           catalogue=g.catalogue)
    assert rec["validator"]["all_checks_passed"]
    assert rec["template_report"]["n_nonzero"] == 2
    assert (tmp_path / "t.zip").is_file() and (tmp_path / "t.json").is_file()


def test_refuses_outside_footprint(tmp_path):
    g = load_grid(BRIDGE)
    p = np.zeros(g.footprint.shape, np.float32)
    p[~g.footprint] = 0.5
    with pytest.raises(Exception):
        write_submission(tmp_path / "t.tif", p, BRIDGE / "sample_submission.tif",
                         g.footprint, note="x", name="x")


def test_refuses_on_catalogue(tmp_path):
    g = load_grid(BRIDGE)
    p = np.zeros(g.footprint.shape, np.float32)
    y, x = np.argwhere(g.catalogue)[0]
    p[y, x] = 1.0
    with pytest.raises(Exception):
        write_submission(tmp_path / "t.tif", p, BRIDGE / "sample_submission.tif",
                         g.footprint, note="x", name="x", catalogue=g.catalogue)
