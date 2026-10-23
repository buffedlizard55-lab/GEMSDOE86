"""New transforms: finite, bounded, and physically oriented."""
import numpy as np
from src.gems86.features import gmc, rank_normalize


def test_gmc_parallel_vs_antiparallel():
    rng = np.random.default_rng(0)
    x = np.linspace(0, 1, 128, dtype=np.float32)
    ramp = np.tile(x, (128, 1))                      # gradient purely +x
    a = gmc(ramp, ramp, sigma=2.0, sharp=3.0)        # parallel   -> oppose ~ 0
    b = gmc(ramp, -ramp, sigma=2.0, sharp=3.0)       # anti-parallel -> oppose > 0
    assert a["oppose"].max() < 1e-6
    assert b["oppose"].max() > 0.0
    for k in ("contact", "oppose", "strike_coh", "aligned"):
        assert np.isfinite(a[k]).all() and a[k].min() >= 0.0


def test_rank_normalize_bounds_and_ties():
    a = np.array([[0.0, 1.0], [2.0, np.nan]], np.float32)
    r = rank_normalize(a)
    assert r.shape == a.shape and r.min() >= 0.0 and r.max() <= 1.0
    assert r[1, 1] == 0.0                            # non-finite maps to 0
    const = rank_normalize(np.ones((4, 4), np.float32))
    assert np.allclose(const, 0.0) or np.allclose(const, 0.5)
