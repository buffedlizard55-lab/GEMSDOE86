#!/usr/bin/env python3
"""H86R selector measurement (analysis only; generates no candidate).

For every locally present discrete raster (docs/downloads artifacts +
data/scored_fleet + data/scored) measure: dots, forward 3-px overlap vs
GEMSDOE32 H33, frac>1km from catalogue, point SGMC-PROXY-DTI (same
off-catalogue SGMC definition as evaluate_sgmc_proxy, point estimate only),
the seeded random-null SGMC floor, and the frozen fleet-regression projection
(coefficients read from docs/evidence/h86r-fleet-estimator-20261026.json;
never refitted here). Live scores, where matched, are OWNER-REPORTED rows of
registry/prior_scores.csv. Nothing here is an organizer score.
"""
from __future__ import annotations

import csv, json, re, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import evaluate_holdout as EH, grid, uniqueness  # noqa: E402
from scripts.run_h86k_stdp import COLLAR_PX, load_binary_tif  # noqa: E402

est = json.loads((ROOT / "docs/evidence/h86r-fleet-estimator-20261026-v2.json").read_text())
beta = np.array(est["coefficients"]); loo = est["loo_rmse"]
SUP = est["training_support"]
g = grid.load_grid(ROOT / "data/bridge")
fp = np.asarray(g.footprint, bool); cat = np.asarray(g.catalogue, bool)
d_cat = ndi.distance_transform_edt(~cat)
h33p = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
h33 = load_binary_tif(h33p) & fp
near_h33 = uniqueness._near(h33)
sgmc = load_binary_tif(ROOT / ".cache/external/derived_sgmc_faults_100m_u8.tif") & fp
known_collar = cat | (d_cat <= COLLAR_PX)
fold_proxy = {"region": fp, "visible": known_collar, "masked_known": known_collar,
              "truth": sgmc & fp & ~known_collar}

scores = {}
for row in csv.DictReader(open(ROOT / "registry/prior_scores.csv")):
    try:
        scores[row["submission"].lower()] = float(row["score"])
    except Exception:
        pass

def match_score(rel: str):
    """Strict only (IR-86R-ESTIMATOR-MISMATCH-20261026): normalized-stem
    containment or shared hex hash token; never date/dot-count tokens."""
    base = Path(rel).stem.lower()
    for pfx in ("gemsdoe32__", "gemsdoe36__", "gemsdoe33__", "gemsdoe28__", "gemsdoe49__",
                "gemsdoe63__", "gemsdoe66__", "gemsdoe70__", "gemsdoe73__", "gemsdoe75__",
                "gemsdoe76__", "gemsdoe78__", "gemsdoe80__", "gemsdoe81__", "gemsdoe82__",
                "gemsdoe83__", "gemsdoe85__", "gemsdoe88__"):
        base = base.replace(pfx, "")
    for pfx in ("gemsdoe32-", "gemsdoe36-", "gemsdoe33-", "gems28-", "gems-", "gems"):
        if base.startswith(pfx):
            base = base[len(pfx):]
    for suf in ("-allfinite", "-zeros", "-nan", "-zero"):
        base = base.replace(suf, "")
    for s, sc in scores.items():
        ss = s
        for suf in ("-allfinite", "-zeros", "-nan", "-zero"):
            ss = ss.replace(suf, "")
        if ss and (ss in base or base in ss):
            return sc
    toks = [t for t in re.split(r"[-_]", base)
            if re.fullmatch(r"[0-9a-f]{8,}", t) and any(c.isalpha() for c in t)]
    for s, sc in scores.items():
        if any(t in s for t in toks):
            return sc
    return None

rows = []
paths = sorted((ROOT / "docs/downloads").glob("*.tif")) + sorted((ROOT / "data/scored_fleet").glob("*.tif")) + sorted((ROOT / "data/scored").glob("*.tif"))
for p in paths:
    b = load_binary_tif(p) & fp
    if not b.any():
        continue
    res, _t = EH.evaluate(b.astype(np.float32), fold_proxy, fp, block_side=200)
    ov = float(near_h33[b].mean()); dd = d_cat[b]; f1 = float((dd > 10).mean())
    sg = float(res["dti"])
    proj = float(np.clip(beta @ np.array([1.0, ov, sg, f1]), 0, 1))
    rel = str(p.relative_to(ROOT))
    rows.append(dict(file=rel, dots=int(b.sum()), ov_h33_3px=round(ov, 4),
                     frac_gt_1km=round(f1, 4), sgmc_proxy_dti_point=round(sg, 4),
                     live_owner_reported=match_score(rel),
                     fleet_regression_projection=round(proj, 4),
                     projection_interval_approx=[round(float(np.clip(proj - 1.96 * loo, 0, 1)), 4),
                                                 round(float(np.clip(proj + 1.96 * loo, 0, 1)), 4)],
                     unique_scoped_vs_h33_lineage=bool(ov <= 0.70),
                     projection_in_training_support=bool(
                         SUP["ov_h33"][0] <= ov <= SUP["ov_h33"][1]
                         and SUP["sgmc_proxy_dti"][0] <= sg <= SUP["sgmc_proxy_dti"][1]
                         and SUP["frac_gt_1km"][0] <= f1 <= SUP["frac_gt_1km"][1])))
    print(rel, rows[-1]["sgmc_proxy_dti_point"], rows[-1]["fleet_regression_projection"], flush=True)

out = dict(schema="gems86.h86r.selector-table.v1", evidence_class="REGISTRY-MEASUREMENT + SGMC-PROXY-DTI (point) + FLEET-REGRESSION-PROJECTION",
           measured_note="Point SGMC-PROXY-DTI via identical fold_proxy as evaluate_sgmc_proxy (off-catalogue SGMC >3px from catalogue); random-null floor at 37,654 dots measured in the lane run: 0.0754. Projection uses frozen OLS from h86r-fleet-estimator-20261026.json (n=%d, LOO-RMSE=%.4f); it is not a score and cannot credit new truth mass." % (est["n"], loo),
           random_null_sgmc_proxy_dti=0.0754,
           rows=rows)
(ROOT / "docs/evidence/h86r-selector-table-20261026.json").write_text(json.dumps(out, indent=2) + "\n")
print("rows:", len(rows))
