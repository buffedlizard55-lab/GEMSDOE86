"""H86E-RIDF holdout experiments (budget: at most 3 emission experiments).

Usage: python scripts/run_h86e_ridf.py   (needs data/training_features.tif and
data/work/h86e_features.npy built by scripts/build_h86e_features.py)

Writes docs/evidence/h86e_holdout.json.  Every number is HOLDOUT-DTI on the
shared buffered whole-component LOQO split (seed 20, hide 0.20, buffer 3 px),
evaluator gems57-pooled-hide-v2, paired 20 km spatial-block bootstrap.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]
from gems57 import grid, holdout as H, evaluate_holdout as E  # noqa: E402
from gems86_ridf import pipeline as P  # noqa: E402
from gems86_ridf.features import feature_names  # noqa: E402

BUDGET = 37_654
D28 = ROOT / "data/registry_ext/91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8.tif"


def main():
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t0 = time.time()
    g = grid.load_grid(ROOT / "data")
    fp = g.footprint
    folds, quad = H.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]
    hidden = folds[0]["hidden_all"]
    dvis = ndi.distance_transform_edt(~visible)
    feats = np.load(ROOT / "data/work/h86e_features.npy", mmap_mode="r")
    names = feature_names()
    assert feats.shape[0] == len(names)
    log = {"split": [f["receipt"] for f in folds], "withheld_positive_pixels": int(hidden.sum())}

    # 1. Leakage canary: each feature alone vs withheld truth inside fold regions.
    rng = np.random.default_rng(7)
    regions = np.zeros(fp.shape, bool)
    for f in folds:
        regions |= f["region"]
    active = regions & fp & ~folds[0]["masked_known"]
    truth = active & hidden
    neg = active & ~truth
    canary = {n: P.single_feature_auc(np.asarray(feats[k], np.float32), truth, neg, rng)
              for k, n in enumerate(names)}
    canary["dist_to_visible_catalogue"] = P.single_feature_auc(-dvis, truth, neg, rng)
    log["leakage_canary_auc"] = canary
    log["leakage_canary_max"] = max(canary.values())
    print("canary max", round(log["leakage_canary_max"], 4), max(canary, key=canary.get), flush=True)
    if log["leakage_canary_max"] > 0.90:
        raise RuntimeError("STOP: single-feature AUC > 0.90 (leakage until proven otherwise)")

    # 2. Spatially blocked LOQO surface: train outside quadrant q, predict inside q.
    p_oof = np.zeros(fp.shape, np.float32)
    for q in range(4):
        allowed = fp & (quad != q) & (quad >= 0)
        X, y = P.sample_training(feats, visible, allowed, seed=q)
        model = P.fit(X, y, seed=q)
        tgt = fp & (quad == q)
        p_oof += P.predict(model, feats, tgt)
        print(f"fold {q}: n={len(y)} pos={int(y.sum())} t={time.time()-t0:.0f}s", flush=True)
    np.save(ROOT / "data/work/h86e_p_oof.npy", p_oof)

    allowed = fp & (dvis > P.COLLAR_PX)
    arms = {}
    # E1: plain disc thinning on the supervised surface.
    arms["E1_hgb_thin"] = P.disc_thin(p_oof, allowed, BUDGET)
    # E2: same surface, distal d_cat profile quotas (R0 histogram, visible catalogue).
    arms["E2_hgb_distal"] = P.stratified_thin(p_oof, allowed, BUDGET, dvis)
    # E3: distal quotas on a range-interior-weighted surface (slope gate, no labels).
    slope = np.asarray(feats[names.index("det_elev_slope")], np.float32)
    s_rank = np.zeros(fp.shape, np.float32)
    v = slope[fp]
    s_rank[fp] = (np.argsort(np.argsort(v)) / max(v.size - 1, 1)).astype(np.float32)
    arms["E3_hgb_distal_slope"] = P.stratified_thin(p_oof * np.sqrt(s_rank), allowed, BUDGET, dvis)
    with rasterio.open(D28) as src:
        d28 = np.nan_to_num(src.read(1)) > 0
    arms["R0_foldfair_d28_visible_collar"] = d28 & fp & (dvis > P.COLLAR_PX)

    terms = {}
    log["arms"] = {}
    for name, dots in arms.items():
        t, per = P.holdout_terms(dots, folds, fp)
        terms[name] = t
        log["arms"][name] = dict(dots=int(dots.sum()), per_fold=per,
                                 dcat_median_visible=float(np.median(dvis[dots])))
        print(name, int(dots.sum()), round(float(E.from_terms(t.sum(0))), 4), flush=True)
    summaries = {}
    for cand in [k for k in arms if not k.startswith("R0")]:
        summaries[cand] = E.pooled_summary({cand: terms[cand],
                                            "R0_foldfair": terms["R0_foldfair_d28_visible_collar"]},
                                           draws=1000, candidate=cand)
    log["paired_vs_R0_foldfair"] = summaries
    for name, dots in arms.items():
        np.save(ROOT / f"data/work/h86e_{name}.npy", dots)
    log["runtime_s"] = time.time() - t0
    out = ROOT / "docs/evidence/h86e_holdout.json"
    out.write_text(json.dumps(log, indent=2, allow_nan=False) + "\n")
    for cand, s in summaries.items():
        sc = s["scores"][cand]
        d = s["paired_differences"]["R0_foldfair"]
        print(cand, "HOLDOUT-DTI", round(sc["dti"], 4), [round(x, 4) for x in sc["ci95"]],
              "delta vs R0ff", round(d["delta"], 4), [round(x, 4) for x in d["ci95"]])


if __name__ == "__main__":
    main()
