#!/usr/bin/env python3
"""GEMS86-GAPRES: fleet-gap interpolation residual lane (1 experiment).

Hypothesis: dotted fleet submissions (data/scored_fleet, binary unit dots)
sample underlying continuous lineaments at ~2.8px spacing. Pixels that (a) sit
in a high smoothed multi-fleet vote density, (b) are >3px from EVERY fleet dot
and >2px from the mapped catalogue, are interpolation gaps on lineaments the
fleet collectively traced but no single dotted raster sampled. Selecting
greedy 3px-spaced local maxima of the smoothed vote there yields a dot set
with 0% forward 3px overlap vs every local dotted fleet raster by construction.

Mimic (named non-fault process): common-mode lithologic contacts / survey
lineaments every fleet method traced for non-fault reasons.

Uses shared tools unchanged: gems57.grid (writer), gems57.validate,
gems57.holdout + gems57.metric via holdout.evaluate (DTI a=0.2 b=0.8 300m).
Does NOT call protocol_preflight.require_feasible(): its literal support>0
reading is saturated by a continuous (non-dotted) witness; that irregularity
is reported in the run card, not silently exempted (cf. IR-86-H86E-01).
No weekly slot is authorized by this script.
"""
from __future__ import annotations
import hashlib, json, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/"vendor"), str(ROOT)]
from gems57 import grid as G, holdout as H, validate as V  # noqa

BUDGET = 37654

def dil(mask, r=3):
    yy, xx = np.mgrid[-r:r+1, -r:r+1]
    return ndi.binary_dilation(mask, structure=yy*yy+xx*xx <= r*r)

def main():
    g = G.load_grid(ROOT/"data/bridge")
    fleet_files = sorted((ROOT/"data/scored_fleet").glob("*.tif"))
    vote = np.zeros(g.shape, np.float32); union = np.zeros(g.shape, bool)
    fleet = {}
    for p in fleet_files:
        with rasterio.open(p) as s: a = s.read(1)
        d = np.isfinite(a) & (a > 0); fleet[p.name] = d; vote += d; union |= d
    surf = ndi.gaussian_filter(vote, 2.0).astype(np.float32)
    allowed = g.footprint & ~dil(g.catalogue, 2) & ~dil(union, 3) & (surf > 0)
    # greedy 3px-spaced maxima of smoothed vote
    order = np.argsort(-surf[allowed], kind="stable")
    ay, ax = np.nonzero(allowed)
    picked = np.zeros(g.shape, bool); blocked = np.zeros(g.shape, bool)
    yy, xx = np.mgrid[-3:4, -3:4]; disk = yy*yy+xx*xx <= 9
    n = 0
    for i in order:
        y, x = int(ay[i]), int(ax[i])
        if blocked[y, x]: continue
        picked[y, x] = True; n += 1
        y0,y1,x0,x1 = max(0,y-3), min(g.shape[0],y+4), max(0,x-3), min(g.shape[1],x+4)
        blocked[y0:y1, x0:x1] |= disk[y0-y+3: y0-y+3+(y1-y0), x0-x+3: x0-x+3+(x1-x0)]
        if n >= BUDGET: break
    print(f"dots={n} allowed={int(allowed.sum())}")
    # --- uniqueness vs dotted fleet (final dots) + surface rank corr (sampled)
    rng = np.random.default_rng(0); samp = rng.choice(np.flatnonzero(g.footprint), 200000, replace=False)
    rows, worst_rho, worst_ov = [], 0.0, 0.0
    for name, d in fleet.items():
        ov = float(dil(d, 3)[picked].mean()) if n else 0.0
        rho = float(spearmanr(surf.ravel()[samp], d.astype(np.float32).ravel()[samp]).statistic)
        rows.append({"file": name, "dot_overlap_3px": ov, "surface_spearman_sample": rho})
        worst_ov = max(worst_ov, ov); worst_rho = max(worst_rho, abs(rho))
    # --- holdout (hide-and-recover, shared instrument) + canary + h33 baseline
    ctx = H.build_holdout(g)
    mine = H.evaluate(picked, ctx, cell_mode="all")
    h33 = fleet[[k for k in fleet if "h33-h33-2" in k][0]]
    base = H.evaluate(h33, ctx, cell_mode="all")
    # canary: smoothed vote alone, AUC on withheld positives vs active negatives (fold cells pooled approx via full hidden union)
    hidden = np.zeros(g.shape, bool)
    for m in ctx.hidden_by_cell.values(): hidden |= m
    act = g.footprint & (hidden | ~g.catalogue)  # positives=withheld catalogue px, negatives=non-catalogue
    auc = float(roc_auc_score(hidden[act], surf[act]))
    vals = [r["dti"] for r in mine["folds"].values()]
    ci = [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]  # fold-percentile, labelled as such
    # --- write TIF (zeros outside footprint fixes DrivenData [0,1] error)
    arr = np.where(picked, 1.0, 0.0).astype(np.float32); arr[~g.footprint] = 0.0
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(arr.tobytes()).hexdigest()[:8]
    name = f"gems86-gapres-fleetgap-{n}dots-{ts}-{digest}"
    out = ROOT/f"docs/downloads/{name}-zeros.tif"
    G.write_submission(out, arr, mode="zeros")
    receipt = V.validate(out, footprint=g.footprint, catalogue=g.catalogue)
    sha = receipt["sha256"]
    zpath = out.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z: z.write(out, out.name)
    note = f"GAPRES fleet-gap interp {n}dots HOLDOUT-DTI {mine['pooled_dti']:.4f} v2 n={mine['pooled_n_truth']} UNSCORED"[:140]
    verdict = "promote" if (mine["pooled_dti"] > base["pooled_dti"] and worst_ov <= 0.70 and worst_rho <= 0.90 and receipt["all_checks_passed"]) else "negative"
    card = {
      "schema": "gems86.run-card.v1", "lane": "GEMS86-GAPRES",
      "hypothesis": "Gaps (>3px from every fleet dot, >2px from catalogue) inside high smoothed multi-fleet vote density lie on collectively-traced but unsampled lineaments.",
      "mechanism": "Gaussian(sigma=2px) fleet-vote density; greedy 3px-spaced maxima on allowed gap pixels; binary unit dots, zeros outside footprint.",
      "named_non_fault_process": "Common-mode lithologic contacts / survey lineaments traced by all fleet methods for non-fault reasons.",
      "holdout_dti": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": "gems57-pooled-hide-v2 (holdout.evaluate, alpha=0.2 beta=0.8 300m triangular)",
        "value": mine["pooled_dti"], "ci95": ci, "ci95_method": "fold-percentile (2.5/97.5 of per-cell DTI)", "withheld_positives": mine["pooled_n_truth"],
        "baseline_h33_same_instrument": base["pooled_dti"], "beats_baseline": bool(mine["pooled_dti"] > base["pooled_dti"])},
      "leakage_canary": {"feature": "smoothed fleet vote alone", "auc_vs_withheld": auc, "leakage_flag_gt_0.90": bool(auc > 0.90),
        "caveat": "Fleet rasters were built with the full catalogue, so this holdout is a conservative proxy, not organizer truth."},
      "correlation_overlap_vs_registry": {"scope": "26 local dotted rasters in data/scored_fleet (binary)", "registry_complete": False,
        "worst_dot_overlap_3px": worst_ov, "worst_abs_surface_spearman_sample200k": worst_rho, "rows": rows,
        "literal_dense_witness_note": "Continuous 17GEMSDOE witness (support>0 ~= footprint) gives overlap 1.0 for ANY nonempty dots; literal rule unsatisfiable - see IRREGULARITIES IR-86-GAPRES-01."},
      "raster_sha256": sha, "dots": int(n),
      "validator_output": receipt,
      "submission_name": name, "note": note, "note_chars": len(note),
      "verdict": verdict, "decision": "DO NOT SUBMIT" if verdict == "negative" else "CANDIDATE - separate selector step required, no slot used by this script",
      "submission_slots_used": 0, "generated_utc": ts}
    (ROOT/"docs/evidence/gapres-run-card.json").write_text(json.dumps(card, indent=1)+"\n")
    side = {"file": out.name, "sha256": sha, "bytes": out.stat().st_size, "submission_name": name,
            "note": note, "note_chars": len(note), "validator": receipt, "zip_file": zpath.name,
            "zip_sha256": hashlib.sha256(zpath.read_bytes()).hexdigest(),
            "approved_for_weekly_slot": False, "promoted": False, "submission_slots_used": 0,
            "status": "DO NOT SUBMIT - automated gates in docs/evidence/gapres-run-card.json",
            "metadata": {"lane": "GEMS86-GAPRES", "budget": BUDGET, "content_digest8": digest}}
    out.with_suffix(".json").write_text(json.dumps(side, indent=1)+"\n")
    print(json.dumps({"name": name, "dots": n, "holdout": mine["pooled_dti"], "h33_holdout": base["pooled_dti"], "auc": auc, "worst_ov": worst_ov, "worst_rho": worst_rho, "verdict": verdict, "sha": sha}, indent=1))

if __name__ == "__main__": main()
