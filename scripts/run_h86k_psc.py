#!/usr/bin/env python3
"""H86K-PSC runner: canary -> pooled hide-and-recover holdout -> uniqueness -> writer.
Uses only shared vendored gems57 evaluator/writer and gems86_mcsp CELF allocator."""
from __future__ import annotations
import hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT/"src", ROOT/"vendor/template66"):
    sys.path.insert(0, str(p))
from gems57 import evaluate_holdout as EH, grid as G, holdout, submission_writer, uniqueness
from gems86.io import read_band
from gems86_mcsp.celf import celf_allocate_dots, static_ek_spacing_allocate
from gems86_psc.features import build_surfaces

BUDGET = 37654
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    t0=time.time()
    grid = G.load_grid(ROOT/"data/bridge")
    fp, cat = grid.footprint, grid.catalogue
    tf = ROOT/"data/training_features.tif"
    bands = {"rtp": read_band(tf,"rtp"), "grav": read_band(tf,"iso_grav_anom"), "depth": read_band(tf,"depth_to_base_surf")}
    # sentinel cleanup already in read_band; zero outside footprint for ranking mask
    planes = build_surfaces(bands, fp)
    planes["E2_saddle_ridge"] = np.sqrt(np.clip(planes["E1_psc"],0,1)*np.clip(planes["C1_ridge"],0,1)).astype(np.float32)
    print("planes built", time.time()-t0, flush=True)

    folds, quad = holdout.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    # ---- leakage canary: each plane alone, AUC vs withheld truth on active pixels
    rng = np.random.default_rng(86)
    canary = {}
    hidden_all = folds[0]["hidden_all"]
    visible_all = cat & ~hidden_all
    active = fp & ~visible_all
    idx = np.flatnonzero(active); samp = rng.choice(idx, size=min(400_000, idx.size), replace=False)
    y = hidden_all.ravel()[samp]
    for name, pl in planes.items():
        canary[name] = float(roc_auc_score(y, pl.ravel()[samp]))
    print("canary", canary, flush=True)
    if max(canary.values()) > 0.90:
        raise SystemExit(f"LEAKAGE CANARY FAIL {canary}")

    # ---- holdout arms, per-fold allocation proportional to region footprint
    arms = ["E2_saddle_ridge","E1_psc","C1_ridge"]
    terms_by_arm = {a: [] for a in arms}
    total_fp = int(fp.sum())
    dist_cat_full = ndi.distance_transform_edt(~cat)
    for fold in folds:
        region = fold["region"]; visible = fold["visible"]
        dist_vis = ndi.distance_transform_edt(~visible)
        allowed = region & fp & (dist_vis > 3.0)
        budget_f = int(round(BUDGET * int((region & fp).sum())/total_fp))
        for arm in arms:
            dots = static_ek_spacing_allocate(planes[arm], allowed, known_faults=visible, valid=fp, budget=budget_f, min_spacing_px=2.8)
            pred = dots.astype(np.float32)
            res, terms = EH.evaluate(pred, fold, fp)
            terms_by_arm[arm].append(terms)
            print(fold["name"], arm, res["dti"], res["n_emitted"], flush=True)
    # pooled_summary needs aligned block terms: evaluate() returns per-fold terms on global grid -> stack by summing? It expects (nblocks,4) aligned; concatenate folds is wrong if overlapping blocks.
    # Folds are disjoint quadrants; terms arrays share global block indexing, so SUM across folds aligns.
    pooled_terms = {a: np.sum(np.stack(v), axis=0) for a,v in terms_by_arm.items()}
    summary = EH.pooled_summary(pooled_terms, draws=1000, seed=520810, candidate="E2_saddle_ridge")
    print(json.dumps(summary["scores"], indent=1), flush=True)

    # ---- final surface registry pre-check vs locally available rasters, then CELF dots
    allowed_final = fp & (dist_cat_full > 3.0)
    cand_files = sorted((ROOT/"data/scored_fleet").glob("*.tif")) + sorted((ROOT/"docs/downloads").glob("*.tif"))
    def check_rho_overlap(surf_or_dots, is_dots):
        worst_rho, worst_ov, n=0.0,0.0,0
        import rasterio
        from scipy.stats import spearmanr
        mine_dots = surf_or_dots>0 if is_dots else None
        near_mine = ndi.binary_dilation(mine_dots, iterations=3) if is_dots else None
        for f in cand_files:
            try:
                with rasterio.open(f) as s:
                    if (s.height,s.width)!=(3730,3292): continue
                    a=s.read(1).astype(np.float32)
            except Exception: continue
            n+=1
            finite=np.isfinite(a)
            m=fp & finite
            # spearman on sample for speed, deterministic
            idx=np.flatnonzero(m); sidx=rng.choice(idx,size=min(200_000,idx.size),replace=False)
            rho,_=spearmanr(surf_or_dots.ravel()[sidx], a.ravel()[sidx])
            if np.isfinite(rho): worst_rho=max(worst_rho, abs(float(rho))) if False else max(worst_rho,float(rho))
            if is_dots:
                theirs=np.isfinite(a)&(a>0)
                if theirs.sum()<=100_000 and theirs.sum()>0:
                    ov=float((near_mine & theirs).sum()/max(1,mine_dots.sum()))  # fraction of THEIR dots near mine? compute forward: my dots near theirs
                    theirs_near=ndi.binary_dilation(theirs, iterations=3)
                    ov=float((theirs_near & mine_dots).sum()/max(1,int(mine_dots.sum())))
                    worst_ov=max(worst_ov,ov)
        return {"rasters_measured":n,"worst_spearman_rho":worst_rho,"worst_dot_overlap_3px":worst_ov,"scope":"data/scored_fleet + docs/downloads only; INCOMPLETE vs full 692-entry registry; disclosed, never called complete"}
    surf_check = check_rho_overlap(planes["E2_saddle_ridge"], False)
    print("surface check", surf_check, flush=True)
    alloc = celf_allocate_dots(planes["E2_saddle_ridge"], allowed_final, known_faults=cat, valid=fp, budget=BUDGET, min_spacing_px=2.8)
    dots = alloc.dots
    print("dots", alloc.n_dots, flush=True)
    dot_check = check_rho_overlap(dots.astype(np.float32), True)
    print("dot check", dot_check, flush=True)

    e1 = summary["scores"]["E2_saddle_ridge"]
    paired = summary["paired_differences"]
    beats = all(e1["dti"] > summary["scores"][c]["dti"] and paired[c]["ci95"][0] > 0 for c in ("E1_psc","C1_ridge"))
    uniq_ok = surf_check["worst_spearman_rho"]<=0.90 and dot_check["worst_spearman_rho"]<=0.90 and dot_check["worst_dot_overlap_3px"]<=0.70
    verdict = "promote" if (beats and uniq_ok) else "negative"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pred = np.where(dots, 1.0, 0.0).astype(np.float32)  # all-finite zeros mode: fixes DrivenData [0,1] rejection of NaN-outside files
    assert np.isfinite(pred).all() and pred.min()>=0 and pred.max()<=1
    name = f"gems86-h86k-psc-saddleridge-{alloc.n_dots}dots-{stamp}"
    note = f"H86K-PSC saddle-persist CELF {alloc.n_dots}d HOLDOUT-DTI {e1['dti']:.4f}; zeros finite [0,1]; verdict {verdict}"[:140]
    out = ROOT/"docs/downloads"/f"{name}-zeros.tif"
    receipt = submission_writer.write_submission(out, pred, ROOT/"data/bridge/sample_submission.tif", fp, note=note, name=name, catalogue=cat, metadata={"lane":"H86K-PSC"})
    card = {
      "schema":"gems86.lane_run_card.v1","lane_id":"H86K-PSC","generated_utc":stamp,
      "hypothesis":"Persistent potential-field saddle connectors (rtp b2 + Bouguer b13 Hessian-saddle persistence, depth b15 concordance) mark buried fault passes between basement blocks lacking scarps/ridges.",
      "mechanism":"sqrt(-det Hessian) saddle strength sigma1&3 persistence x low-gradient gate; geometric mean rtp x gravity; x(0.5+0.5 depth saddle); CELF submodular 37,654 dots, spacing 2.8px, catalogue collar >3px",
      "named_non_fault_mimic":"Intrusive lithologic contacts and erosional basement relief creating superposed-source saddles",
      "leakage_canary_auc": canary, "canary_pass": bool(max(canary.values())<=0.90),
      "holdout":{"evidence_class":"HOLDOUT-DTI","evaluator_version":EH.VERSION,"scores":summary["scores"],"paired_differences":summary["paired_differences"],"bootstrap":summary["bootstrap"]},
      "correlation_overlap_vs_registry":{"surface":surf_check,"final_dots":dot_check,"unique_like_for_like_measured_scope":bool(uniq_ok)},
      "raster_sha256": receipt["sha256"], "file": out.name,
      "validator_output": receipt["validator"],
      "submission_name": name, "note": note, "note_chars": len(note),
      "verdict": verdict, "submission_ready_format": bool(receipt["validator"]["all_checks_passed"]),
      "safe_to_submit": bool(verdict=="promote" and receipt["validator"]["all_checks_passed"] and uniq_ok),
      "approved_for_weekly_slot": False, "submission_slots_used": 0,
      "organizer_confirmed_score": None,
      "runtime_s": time.time()-t0}
    (ROOT/"docs/evidence/h86k-psc-run-card.json").write_text(json.dumps(card,indent=2)+"\n")
    print(json.dumps(card,indent=2))

if __name__=="__main__": main()
