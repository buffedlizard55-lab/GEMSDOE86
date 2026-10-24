"""H86E-RIDF unit tests: emission geometry and PA-86-02 chance-level logic (synthetic only)."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]

from gems86_ridf import pipeline as P  # noqa: E402
from scripts.pa86_chance_overlap import halo_coverage_array, is_space_filling  # noqa: E402


def test_disc_thin_spacing_budget_and_order():
    rng = np.random.default_rng(0)
    score = rng.random((60, 60)).astype(np.float32)
    allowed = np.ones_like(score, bool)
    allowed[:, :5] = False
    dots = P.disc_thin(score, allowed, budget=50)
    yx = np.argwhere(dots)
    assert len(yx) == 50
    assert not dots[:, :5].any()
    d = np.hypot(*(yx[:, None, :] - yx[None, :, :]).transpose(2, 0, 1))
    np.fill_diagonal(d, np.inf)
    assert d.min() >= P.SPACING_PX
    # the global maximum allowed pixel is always selected first
    masked = np.where(allowed, score, -1)
    assert dots.flat[int(np.argmax(masked))]


def test_stratified_thin_respects_band_quotas():
    score = np.ones((80, 80), np.float32)
    dcat = np.tile(np.arange(80, dtype=float), (80, 1))
    dots = P.stratified_thin(score, dcat > 2, 40, dcat,
                             profile=(0.5, 0.5), bins=(2.0, 30.0, np.inf))
    assert dots[:, :3].sum() == 0
    assert dots[(dcat > 2) & (dcat <= 30)].sum() == 20
    assert dots[dcat > 30].sum() == 20


def test_space_filling_lattice_vs_sparse_line():
    allowed = np.ones((100, 100), bool)
    lattice = np.zeros_like(allowed)
    lattice[::5, ::5] = True
    line = np.zeros_like(allowed)
    line[50, :] = True
    c_lat = halo_coverage_array(lattice, allowed)
    c_line = halo_coverage_array(line, allowed)
    assert is_space_filling(c_lat)          # a 5 px lattice fires on any candidate by chance
    assert not is_space_filling(c_line)     # a single trace is an informative comparator
    assert 0.06 < c_line < 0.08             # 7 of 100 rows lie within 3 px


def test_like_for_like_gate_is_not_the_legacy_gate():
    import scripts.protocol_preflight as pp
    assert hasattr(pp, "require_feasible") and hasattr(pp, "require_like_for_like")
    src = Path(pp.__file__).read_text()
    # the legacy stop must remain unchanged for historical builders
    assert "STOP_LITERAL_OVERLAP_UNSATISFIABLE: no new model experiment" in src
    assert "saturating witness is a dot field" in src
