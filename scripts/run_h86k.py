#!/usr/bin/env python3
"""H86K-STC lane: structure-tensor coherence x coincident mag/gravity edge.

Catalogue-independent surface (geophysics only). Holdout = template
hide-and-recover (whole segments, quadrants, visible masked pixel-exactly).
Emission: binary dots, min separation 3px, off-catalogue, budget 40000.
Writes candidate ONLY via template fail-closed writer; verdict in run card.
"""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"vendor"/"template66"))
from gems57.grid import load_grid
from gems57 import holdout as ho
from gems57.submission_writer import write_submission
from src.gems86.io import read_band

BUDGET = 40000

def rank_norm(a, valid):
    out = np.zeros(a.shape, np.float64); v = a[valid]
    order = np.argsort(v, kind="stable"); r = np.empty(v.size); r[order] = np.arange(v.size)
    out[valid] = r / max(v.size-1, 1); return out

def main():
    g = load_grid(ROOT/"data/bridge"); fp, cat = g.footprint, g.catalogue
    rtp = read_band(ROOT/"data/bridge/training_features.tif", "rtp").astype(np.float64)
    feats_raw = {}
    # structure tensor coherence of smoothed RTP (5px)
    gx = ndi.sobel(ndi.gaussian_filter(rtp, 2.0), axis=1); gy = ndi.sobel(ndi.gaussian_filter(rtp, 2.0), axis=0)
    jxx = ndi.gaussian_filter(gx*gx, 2.5); jyy = ndi.gaussian_filter(gy*gy, 2.5); jxy = ndi.gaussian_filter(gx*gy, 2.5)
    coh = np.sqrt((jxx-jyy)**2 + 4*jxy**2) / (jxx+jyy+1e-12)
    feats_raw["stc_coherence"] = coh
    feats_raw["tmi_hg"] = read_band(ROOT/"data/bridge/training_features.tif", "tmi_hg").astype(np.float64)
    feats_raw["grav_hg"] = read_band(ROOT/"data/bridge/training_features.tif", "iso_grav_anom_slope").astype(np.float64)
    depth = read_band(ROOT/"data/bridge/training_features.tif", "depth_to_base_surf").astype(np.float64)
    feats_raw["depth_grad"] = np.hypot(ndi.sobel(depth,0), ndi.sobel(depth,1))
    feats = {k: rank_norm(v, fp) for k, v in feats_raw.items()}

    # leakage canary: each feature alone, AUC vs catalogue on deterministic sample
    rng = np.random.default_rng(86); idx = np.flatnonzero(fp); samp = rng.choice(idx, 200000, replace=False)
    y = cat.ravel()[samp]
    canary = {k: float(roc_auc_score(y, feats[k].ravel()[samp])) for k in feats}
    print("canary AUC", canary, flush=True)
    assert all(v <= 0.90 for v in canary.values()), "LEAKAGE CANARY FAIL"

    surfaces = {
        "stc": feats["stc_coherence"]*np.sqrt(feats["tmi_hg"]*feats["grav_hg"])*(0.5+0.5*feats["depth_grad"]),
        "tmi_hg_only": feats["tmi_hg"],
        "edge_only": np.sqrt(feats["tmi_hg"]*feats["grav_hg"]),
    }

    def emit(surface):
        order = np.argsort(-surface[fp], kind="stable"); coords = np.column_stack(np.nonzero(fp))[order]
        blocked = cat.copy(); dots = np.zeros(fp.shape, bool); chosen=[]
        # greedy with 3px suppression via dilation each 2000 dots (fast enough on cpu blocks)
        taken = np.zeros(fp.shape, bool)
        for (r,c) in coords:
            if taken[r,c] or cat[r,c]: continue
            chosen.append((r,c)); dots[r,c]=True
            r0,r1,c0,c1 = max(0,r-3), min(fp.shape[0],r+4), max(0,c-3), min(fp.shape[1],c+4)
            yy,xx = np.mgrid[r0:r1,c0:c1]; taken[r0:r1,c0:c1] |= (yy-r)**2+(xx-c)**2 <= 9
            if len(chosen) >= BUDGET: break
        return dots

    ctx = ho.build_holdout(g, seeds=(20,21), modes=("all",))
    results = {}
    emitted = {}
    for name, surf in surfaces.items():
        dots = emit(surf); emitted[name]=dots
        res = ho.evaluate(dots, ctx, cell_mode="all")
        # pooled DTI recomputed from per-fold sums is inside evaluate; capture dti via totals
        results[name] = res
        print(name, {k: res[k] for k in list(res)[:6]}, flush=True)

    # choose candidate arm = stc regardless (pre-registered); report comparisons
    dots = emitted["stc"]; surf = surfaces["stc"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha_surf = hashlib.sha256(np.ascontiguousarray(surf.astype(np.float32)).tobytes()).hexdigest()[:8]
    name = f"gems86-h86k-stc-40000dots-{stamp}-{sha_surf}-zeros"
    out = ROOT/f"docs/downloads/{name}.tif"
    pred = dots.astype(np.float32)
    receipt = write_submission(out, pred, ROOT/"data/bridge/sample_submission.tif", fp,
        note="H86K-STC coherence x coincident mag/grav edge, 40k dotted; audit only unless run card promotes",
        name=name, catalogue=cat, metadata={"lane":"H86K-STC","budget":BUDGET})
    card = {"hypothesis":"Coherent-strike coincident mag+gravity basement edge catches buried faults missing from catalogue",
      "mechanism":"structure-tensor coherence(RTP) * sqrt(rank tmi_hg * rank grav_hg) * depth-grad gate; 3px-separated binary dots",
      "named_non_fault_process":"unfaulted pluton wall-rock contacts / lithologic basement ridges",
      "canary_auc": canary, "holdout_arms": {k: {"pooled": v} for k,v in results.items()},
      "surface_sha256": hashlib.sha256(np.ascontiguousarray(surf.astype(np.float32)).tobytes()).hexdigest(),
      "raster_sha256": receipt["sha256"], "submission_name": name,
      "note": "H86K-STC coherence x coincident mag/grav edge, 40k dotted; audit only unless run card promotes",
      "validator": receipt["validator"], "slots_used": 0}
    (ROOT/f"docs/evidence/h86k-run-card.json").write_text(json.dumps(card, indent=2, default=str))
    print(json.dumps({"name":name,"sha":receipt["sha256"],"canary":canary}, indent=2))
if __name__ == "__main__": main()
