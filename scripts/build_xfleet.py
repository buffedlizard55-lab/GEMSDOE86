#!/usr/bin/env python3
"""GEMSDOE86 XFLEET experiment: cross-fleet consensus anchored to R0 (h33).
Exp1 anchored consensus, Exp2 pure consensus, Exp3 R0 respaced control.
Holdout: quadrant whole-component hide-and-recover, gems57 metric dti_binary pooled.
Writes only Exp1 TIF (zeros outside footprint, float32, values {0,1})."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.protocol_preflight import require_feasible
require_feasible()
sys.path.insert(0, str(ROOT/"vendor")); sys.path.insert(0, str(ROOT/"vendor/template66"))
from gems57.metric import dti_binary
from gems57.grid import load_grid

BUDGET=37654; MINSEP=2.8
g=load_grid(ROOT/"data/bridge")
foot, cat = g.footprint, g.catalogue
fleet=sorted((ROOT/"data/scored_fleet").glob("*.tif"))
votes=np.zeros(foot.shape, np.float32); r0=None; masks={}
for f in fleet:
    with rasterio.open(f) as d: a=d.read(1)
    m=np.isfinite(a)&(a>0)&foot
    masks[f.name]=m; votes+=m
    if "h33-h33-2-b2" in f.name: r0=m
print(f"fleet={len(fleet)} r0_dots={int(r0.sum())} maxvotes={votes.max()}")
dist_cat=ndi.distance_transform_edt(~cat)
allowed=foot&(dist_cat>2.0)

def spaced_select(score, allowed, budget):
    ys,xs=np.nonzero(allowed&(score>=2)) if score.max()>2 else np.nonzero(allowed&(score>0))
    order=np.argsort(-score[ys,xs],kind="stable"); ys,xs=ys[order],xs[order]
    sel=np.zeros(score.shape,bool); r=int(np.ceil(MINSEP))
    # grid-bucket greedy
    from collections import defaultdict
    buckets=defaultdict(list)
    n=0
    for y,x in zip(ys,xs):
        by,bx=y//3,x//3; ok=True
        for dy in(-1,0,1):
            for dx in(-1,0,1):
                for (py,px) in buckets.get((by+dy,bx+dx),[]):
                    if (py-y)**2+(px-x)**2 < MINSEP**2: ok=False;break
                if not ok: break
            if not ok: break
        if ok:
            sel[y,x]=True; buckets[(by,bx)].append((y,x)); n+=1
            if n>=budget: break
    return sel

exps={
 "E1_anchored_consensus": spaced_select(votes+2.0*r0, allowed, BUDGET),
 "E2_pure_consensus": spaced_select(votes, allowed, BUDGET),
 "E3_r0_control": spaced_select(r0.astype(np.float32), allowed, BUDGET),
}
# holdout: connected components assigned by centroid quadrant
lab,ncomp=ndi.label(cat)
objs=ndi.find_objects(lab)
yy,xx=np.nonzero(cat); lb=lab[cat]
cy=np.bincount(lb,weights=yy,minlength=ncomp+1); cx=np.bincount(lb,weights=xx,minlength=ncomp+1); cnt=np.bincount(lb,minlength=ncomp+1)
cents=np.column_stack([cy[1:]/np.maximum(cnt[1:],1),cx[1:]/np.maximum(cnt[1:],1)])
H,W=cat.shape; folds={}
for name,(qy,qx) in {"NW":(0,0),"NE":(0,1),"SW":(1,0),"SE":(1,1)}.items():
    ids=[i+1 for i,(cy,cx) in enumerate(cents) if (cy<H/2)==(qy==0) and (cx<W/2)==(qx==0)]
    folds[name]=np.isin(lab,ids)&cat
results={}
for ename,sel in exps.items():
    tp=fp=fn=0.0; per={}
    for fname,truth in folds.items():
        r=dti_binary(sel,truth,valid=foot,known=cat&~truth)
        tp+=r["tp"]; fp+=r["fp"]; fn+=r["fn"]; per[fname]=round(r["dti"],5)
    pooled=tp/(tp+0.2*fp+0.8*fn+1e-12)
    results[ename]=dict(dots=int(sel.sum()),pooled_holdout_dti=round(float(pooled),5),per_fold=per,
                        withheld_positive_px=int(sum(int(t.sum()) for t in folds.values())))
    print(ename,results[ename])
# canary AUC: votes vs withheld-all (full catalogue as positive proxy, background >3px)
from sklearn.metrics import roc_auc_score
bg=foot&(dist_cat>3)
samp=np.zeros(foot.shape,bool); rng=np.random.default_rng(0)
pos_idx=np.argwhere(cat); neg_idx=np.argwhere(bg)
sel_neg=neg_idx[rng.choice(len(neg_idx),size=min(20000,len(neg_idx)),replace=False)]
y=np.r_[np.ones(len(pos_idx)),np.zeros(len(sel_neg))]
s=np.r_[votes[cat],votes[tuple(sel_neg.T)]]
auc=float(roc_auc_score(y,s)); print("canary votes AUC",auc)
# uniqueness of E1 vs every fleet raster
sel=exps["E1_anchored_consensus"]
dist_sel=ndi.distance_transform_edt(~sel)
uniq={}
for name,m in masks.items():
    dist_reg=ndi.distance_transform_edt(~m)
    cand_frac=float((dist_reg[sel]<=3).mean())
    # spearman on 200k footprint sample
    idx=np.argwhere(foot); sidx=idx[rng.choice(len(idx),size=min(200000,len(idx)),replace=False)]
    from scipy.stats import spearmanr
    rho=float(spearmanr(sel[tuple(sidx.T)].astype(float),m[tuple(sidx.T)].astype(float)).statistic) if m[tuple(sidx.T)].std()>0 and sel[tuple(sidx.T)].std()>0 else 0.0
    uniq[name]=dict(dot_overlap_within3px_of_candidate=round(cand_frac,4),spearman_sample=round(rho,4))
worst=max(uniq.values(),key=lambda v:v["dot_overlap_within3px_of_candidate"])
worst_rho=max(abs(v["spearman_sample"]) for v in uniq.values())
print("worst overlap",worst,"worst |rho|",worst_rho)
# write E1
stamp="20261024T000000Z"
pred=sel.astype(np.float32)
digest=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
name=f"gems86-xfleet-consensus-{int(sel.sum())}dots-{stamp}-{digest}-zeros"
outdir=ROOT/"docs/downloads"; outdir.mkdir(parents=True,exist_ok=True)
out=outdir/f"{name}.tif"
with rasterio.open(ROOT/"data/bridge/sample_submission.tif") as s: prof=s.profile.copy()
prof.update(dtype="float32",count=1,nodata=None,compress="deflate")
with rasterio.open(out,"w",**prof) as d: d.write(pred,1)
import zipfile
with zipfile.ZipFile(outdir/f"{name}.zip","w",zipfile.ZIP_DEFLATED) as z: z.write(out,out.name)
sha=hashlib.sha256(out.read_bytes()).hexdigest()
card=dict(schema="gems86.xfleet.run-card.v1",date_utc="2026-10-24",evidence_class_holdout="HOLDOUT-DTI",
 hypothesis="Cross-fleet consensus (independent scored submissions agreeing off-catalogue) marks hidden-fault habitat better than any single lane; anchoring to R0 (0.2778 owner-reported) retains its geometry.",
 mechanism="Vote surface over 25 scored-fleet rasters in data/scored_fleet + 2x R0 anchor weight; catalogue collar >2px (dist to mapped fault), 2.8px min spacing, 37654-dot budget matching R0.",
 named_non_fault_process="Shared catalogue-avoidance geometry and shared GeoDAWN edge artefacts (survey seams, lithologic contacts) can make independent-looking lanes agree off-fault.",
 holdout=dict(evaluator="vendor/gems57/metric.py dti_binary alpha=0.2 beta=0.8 R=3px pooled over 4 quadrant whole-component folds",
   results=results, canary_votes_auc=round(auc,4), canary_note="AUC vs catalogue proxy; >0.90 would flag leakage",
   caveat="Fleet rasters were built against the full catalogue, so this hide-and-recover proxy is comparative only and known sign-unstable vs live scores (IR-86-PRUNE-03); not a live-score projection."),
 uniqueness_vs_scored_fleet=uniq, worst_dot_overlap=worst, worst_abs_spearman=round(worst_rho,4),
 registry_note="Checked vs the 25 locally scored fleet rasters only. The pinned dense continuous witness in docs/evidence/uniqueness.json is positive everywhere and would block ANY nonempty raster under the literal rule; that contradiction is flagged, not hidden (IR-86-PRUNE-01).",
 raster_sha256=sha, submission_file=f"docs/downloads/{name}.tif",
 submission_name=name, note="XFLEET consensus+R0 anchor 37654d collar>2px sep2.8 HOLDOUT-DTI proxy in run card; zeros [0,1]",
 validator=dict(all_finite=bool(np.isfinite(pred).all()),values_in_0_1=bool(pred.min()>=0 and pred.max()<=1),
   outside_footprint_zero=bool((pred[~foot]==0).all()),on_catalogue_dots=int((sel&cat).sum()),dots=int(sel.sum())))
assert len(card["note"])<=140
(ROOT/"docs/evidence/xfleet-run-card.json").write_text(json.dumps(card,indent=2)+"\n")
(outdir/f"{name}.json").write_text(json.dumps(card,indent=2)+"\n")
print(json.dumps({"file":str(out),"sha256":sha,"name":name},indent=2))
