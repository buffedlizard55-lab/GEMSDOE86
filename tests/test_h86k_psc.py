import numpy as np
from gems86_psc.features import saddle_persistence, build_surfaces

def test_saddle_detects_pass_between_highs():
    y, x = np.mgrid[:41, :41]
    f = (np.exp(-(((x-10)**2+(y-20)**2)/50.)) + np.exp(-(((x-30)**2+(y-20)**2)/50.))).astype(np.float32)
    mask = np.ones(f.shape, bool)
    s = saddle_persistence(f, mask)
    assert s[20, 20] > s[20, 10]  # saddle midpoint outranks a peak

def test_surfaces_in_unit_range():
    rng = np.random.default_rng(0)
    bands = {k: rng.normal(size=(30,30)).astype(np.float32) for k in ("rtp","grav","depth")}
    out = build_surfaces(bands, np.ones((30,30), bool))
    for v in out.values():
        assert np.isfinite(v).all() and v.min() >= 0 and v.max() <= 1
