#!/usr/bin/env python3
"""GEMSDOE86-SPT: signed paired-throw consistency (basement step x gravity step,
same downthrown sign, surface-step penalised). Bands 15/13/12 of pinned
training_features.tif. Emission identical to R0 control: collar>2px, sep 2.8px,
37654 dots. Holdout = 4 quadrant whole-component folds, gems57 dti_binary pooled."""
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"vendor")); sys.path.insert(0,str(ROOT/"vendor/template66"))
from gems57.metric import dti_binary
from gems57.grid import load_grid
BUDGET=37654; MINSEP=2.8
g=load_grid(ROOT/"data/bridge"); foot,cat=g.footprint,g.catalogue
FEAT=ROOT/"data/bridge/training_features.tif"
def band(i):
    with rasterio.open(FEAT) as s: a=s.read(i).astype(np.float64)
    a[~np.isfinite(a)]=np.nan; a[a<=-1e30]=np.nan
    med=np.nanmedian(a[foot]); a[~foot]=med; a=np.where(np.isfinite(a),a,med); return a
def rz(a):
    v=a[foot]; med=np.median(v); mad=np.median(np.abs(v-med))*1.4826 or 1.0
    return np.clip((a-med)/mad,-10,10).astype(np.float32)
B=rz(ndi.gaussian_filter(band(15),1.0)); G=rz(ndi.gaussian_filter(band(13),1.0)); E=rz(ndi.gaussian_filter(band(12),1.0))
dirs=[(dy,dx) for dy in(-1,0,1) for dx in(-1,0,1) if (dy,dx)!=(0,0)]
best=np.zeros(foot.shape,np.float32)
for dy,dx in dirs:
    L=np.hypot(dy,dx); oy,ox=int(round(dy/L*3)),int(round(dx/L*3))
    def sh(a,sy,sx): return ndi.shift(a,(sy,sx),order=1,mode="nearest")
    dB=sh(B,oy,ox)-sh(B,-oy,-ox); dG=sh(G,oy,ox)-sh(G,-oy,-ox); dE=np.abs(sh(E,oy,ox)-sh(E,-oy,-ox))
    agree=(np.sign(dB)==np.sign(dG)).astype(np.float32)
    s=np.minimum(np.abs(dB),np.abs(dG))*agree-float(__import__('os').environ.get('SPT_PENALTY','0.5'))*dE
    best=np.maximum(best,s)
score=np.where(foot,best,0).astype(np.float32)
print("score pct",np.percentile(score[foot],[50,90,99,99.9]))
dist_cat=ndi.distance_transform_edt(~cat); allowed=foot&(dist_cat>2.0)
def spaced_select(score,allowed,budget):
    ys,xs=np.nonzero(allowed&(score>np.percentile(score[allowed],90)))
    order=np.argsort(-score[ys,xs],kind="stable"); ys,xs=ys[order],xs[order]
    from collections import defaultdict
    buckets=defaultdict(list); sel=np.zeros(score.shape,bool); n=0
    for y,x in zip(ys,xs):
        by,bx=y//3,x//3; ok=True
        for ddy in(-1,0,1):
            for ddx in(-1,0,1):
                for py,px in buckets.get((by+ddy,bx+ddx),[]):
                    if (py-y)**2+(px-x)**2<MINSEP**2: ok=False;break
                if not ok: break
            if not ok: break
        if ok:
            sel[y,x]=True; buckets[(by,bx)].append((y,x)); n+=1
            if n>=budget: break
    return sel
sel=spaced_select(score,allowed,BUDGET); print("dots",int(sel.sum()))
# holdout folds
lab,ncomp=ndi.label(cat); yy,xx=np.nonzero(cat); lb=lab[cat]
cy=np.bincount(lb,weights=yy,minlength=ncomp+1); cx=np.bincount(lb,weights=xx,minlength=ncomp+1); cnt=np.bincount(lb,minlength=ncomp+1)
cents=np.column_stack([cy[1:]/np.maximum(cnt[1:],1),cx[1:]/np.maximum(cnt[1:],1)])
H,W=cat.shape; folds={}
for nm,(qy,qx) in {"NW":(0,0),"NE":(0,1),"SW":(1,0),"SE":(1,1)}.items():
    ids=[i+1 for i,(cyy,cxx) in enumerate(cents) if (cyy<H/2)==(qy==0) and (cxx<W/2)==(qx==0)]
    folds[nm]=np.isin(lab,ids)&cat
def pooled(s):
    tp=fp=fn=0.0; per={}
    for nm,t in folds.items():
        r=dti_binary(s,t,valid=foot,known=cat&~t); tp+=r["tp"]; fp+=r["fp"]; fn+=r["fn"]; per[nm]=round(r["dti"],5)
    return round(float(tp/(tp+0.2*fp+0.8*fn+1e-12)),5),per
spt_dti,per=pooled(sel)
# canary AUC of score alone
from sklearn.metrics import roc_auc_score
rng=np.random.default_rng(0); bg=foot&(dist_cat>3)
ni=np.argwhere(bg); ni=ni[rng.choice(len(ni),20000,replace=False)]
y=np.r_[np.ones(int(cat.sum())),np.zeros(len(ni))]; s=np.r_[score[cat],score[tuple(ni.T)]]
auc=float(roc_auc_score(y,s)); print("SPT holdout",spt_dti,per,"canary AUC",auc)
# uniqueness vs fleet + R0
uniq={}
for f in sorted((ROOT/"data/scored_fleet").glob("*.tif")):
    with rasterio.open(f) as d: a=d.read(1)
    m=np.isfinite(a)&(a>0)&foot
    dr=ndi.distance_transform_edt(~m)
    uniq[f.name]=round(float((dr[sel]<=3).mean()),4)
worst=max(uniq.values()); print("worst 3px overlap",worst)
pred=sel.astype(np.float32); digest=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
stamp="20261024T010000Z"; name=f"gems86-spt-throwcons-{int(sel.sum())}dots-{stamp}-{digest}-zeros"
outdir=ROOT/"docs/downloads"; out=outdir/f"{name}.tif"
with rasterio.open(ROOT/"data/bridge/sample_submission.tif") as src: prof=src.profile.copy()
prof.update(dtype="float32",count=1,nodata=None,compress="deflate")
with rasterio.open(out,"w",**prof) as d: d.write(pred,1)
with zipfile.ZipFile(outdir/f"{name}.zip","w",zipfile.ZIP_DEFLATED) as z: z.write(out,out.name)
sha=hashlib.sha256(out.read_bytes()).hexdigest()
card=dict(schema="gems86.spt.run-card.v1",date_utc="2026-10-24",
 hypothesis="H-SPT: a concealed fault offsets basement and gravity with the SAME downthrown sign while lacking a strong surface step; requiring signed flank consistency (not unsigned edges) finds catalogue-missing buried faults.",
 mechanism="8-orientation +/-3px flank steps on depth_to_base_surf(15) x iso_grav_anom(13): min(|dB|,|dG|) if sign(dB)==sign(dG), minus 0.5*|det_elev(12) step|; max over orientations. Emission: collar>2px from catalogue, 2.8px spacing, 37654 dots (=R0 budget).",
 named_non_fault_process="Unfaulted erosional basement escarpment / basin-fill density change; gravity-basement inversion artefacts sharing a sign by construction.",
 evidence_class="HOLDOUT-DTI", evaluator="vendor/gems57/metric.py dti_binary alpha=0.2 beta=0.8 R=3px, pooled 4 quadrant whole-component folds",
 holdout_dti_spt=spt_dti, holdout_per_fold=per, holdout_dti_r0_control_same_folds=0.00479,
 withheld_positive_px=int(sum(int(t.sum()) for t in folds.values())), canary_score_auc=round(auc,4),
 caveat="Catalogue hide-and-recover proxy is comparative only; fleet/SPT surfaces were derived with full-catalogue knowledge of the study area and this proxy is documented sign-unstable vs live scores (IR-86-PRUNE-03). Not a live-score projection. ORGANIZER-CONFIRMED: none.",
 uniqueness_vs_scored_fleet_dot_overlap_within3px=uniq, worst_dot_overlap=worst,
 raster_sha256=sha, submission_file=f"docs/downloads/{name}.tif", submission_name=name,
 note="SPT signed basement+gravity throw-consistency, surface-penalised; 37654d collar>2 sep2.8 zeros [0,1]",
 validator=dict(all_finite=bool(np.isfinite(pred).all()),values_in_0_1=bool(pred.min()>=0 and pred.max()<=1),
  outside_footprint_zero=bool((pred[~foot]==0).all()),on_catalogue_dots=int((sel&cat).sum()),dots=int(sel.sum()),
  crs="EPSG:32611",shape=[3730,3292]))
assert len(card["note"])<=140
card["verdict"]="promote-candidate" if (spt_dti>0.00479 and worst<=0.70 and auc<=0.90) else "negative"
(ROOT/"docs/evidence/spt-run-card.json").write_text(json.dumps(card,indent=2)+"\n")
(outdir/f"{name}.json").write_text(json.dumps(card,indent=2)+"\n")
print(json.dumps({"file":str(out),"sha256":sha,"verdict":card["verdict"]},indent=2))
