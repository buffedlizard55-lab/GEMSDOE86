#!/usr/bin/env python3
"""Report-only instrument audit: is the SGMC off-catalogue surrogate monotone in dot count?

The session's three arms read −0.0036 / +0.0057 / +0.0063 on that surrogate, i.e. every arm that
adds mass gains and the arm that removes mass loses.  Before any of that can be called evidence,
the instrument has to be asked whether it can rank mass at all.  This script adds and deletes
random dots over a symmetric dose ladder and reports the response curve.

If the curve is monotone in the dot count, then the surrogate is measuring *coverage of its own
truth inventory*, not the marginal value of mass under the competition's metric, and no
mass-changing arm's MODEL number (this session's, CONCENTRATION's +0.006, SPACING's +0.002, or any
future one) may be promoted on that instrument alone.  Nothing here is a gate and nothing selects a
slot.

Usage::  .venv/bin/python scripts/audit_mass_instrument.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems86 import mass_econ as ME  # noqa: E402
from gems86_axis import grid_io  # noqa: E402

PARENT = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
SGMC = ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"
OUT = ROOT / "evidence" / "mass_instrument_monotonicity.json"
SEED = 20261023
DOSES = (-0.20, -0.10, -0.05, 0.05, 0.10, 0.20)


def main() -> int:
    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]
    parent = grid_io.load_dots(PARENT, foot)
    n0 = int(parent.sum())
    with rasterio.open(SGMC) as src:
        sg = src.read(1) > 0
    truth = sg & foot & ~cat
    base = ME.exact_terms(parent, truth)
    rng = np.random.default_rng(SEED)
    rows, cols = parent.nonzero()
    cat_edt = ndi.distance_transform_edt(~cat)

    curve = []
    for dose in DOSES:
        k = int(round(abs(dose) * n0))
        if dose < 0:
            keep = np.ones(n0, bool)
            keep[rng.choice(n0, size=k, replace=False)] = False
            mask = np.zeros_like(parent)
            mask[rows[keep], cols[keep]] = True
            how = "delete random"
        else:
            cand = foot & ~cat & (cat_edt > grid_io.PARENT_CAT_CLEARANCE_PX) & ~parent
            cr, cc = np.nonzero(cand)
            pick = rng.choice(cr.size, size=k, replace=False)
            mask = parent.copy()
            mask[cr[pick], cc[pick]] = True
            how = "add random"
        terms = ME.exact_terms(mask, truth)
        curve.append({"dose": dose, "how": how, "n_dots": int(mask.sum()),
                      "dti": terms["dti"], "delta_dti": round(terms["dti"] - base["dti"], 6)})

    deltas = [c["delta_dti"] for c in curve]
    monotone = all(b >= a - 1e-9 for a, b in zip(deltas, deltas[1:]))
    # Live-metric contrast: T/|G| on the surrogate vs the bound implied by the incumbent's score.
    cov = base["T"] / base["G"]
    live = {}
    for g in (5000, 10000, 20000, 40000):
        t = (0.2 * (base["n"] - base["M"]) + 0.8 * g) / 4.2     # 1/0.2778 + 0.6 = 4.2
        live[g] = {"implied_T": round(t, 1), "implied_T_over_G": round(t / g, 4)}
    out = {
        "evidence_class": "MODEL-INSTRUMENT-AUDIT",
        "instrument": "exact DTI against USGS SGMC off-catalogue pixels (the repo's MODEL surrogate)",
        "source_url": "https://www.usgs.gov/science-plan/conterminous-synthetic-geologic-map-compiler-sgmc",
        "parent": base, "curve": curve, "monotone_in_dot_count": bool(monotone),
        "surrogate_T_over_G": round(cov, 4),
        "live_T_over_G_implied": live,
        "reading": ("The surrogate credits only a small share of its own truth inventory "
                    f"({cov:.3f} of |G|) whereas the incumbent's claimed live score implies "
                    "0.26-0.34 at plausible new-fault truth sizes, so the surrogate sits far from "
                    "the live operating point and prices extra mass much too highly."
                    if monotone else
                    "The response curve is not monotone; the surrogate discriminates within mass."),
        "consequence": ("A MODEL delta from this instrument cannot rank mass-changing arms. It may "
                        "still order arrangements at fixed count, which is how SPACING used it."),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"monotone_in_dot_count": out["monotone_in_dot_count"],
                      "curve": [{k: c[k] for k in ("dose", "n_dots", "delta_dti")} for c in curve],
                      "surrogate_T_over_G": out["surrogate_T_over_G"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
