"""Lane H86-RMRB: radiometric mixing-residual boundary (declared lane for GEMSDOE86).

IRREGULARITY LOGGED: the supplied prompt says the lane is 'the single method
paragraph below' but contains no such paragraph. This session therefore
declares, before any experiment, the preregistered-but-never-implemented
rank-1 hypothesis of research/REVIEW.md as its lane and stays inside it:
  surface = boundary strength of the residual of a robust global
  K ~ Th + U + TC mixing regression (GeoDAWN radiometrics, USGS
  doi:10.5066/P93LGLVQ via hash-pinned owner mirror), gated by multi-scale
  RTP magnetic-edge persistence, down-weighted where a broad (sigma=5 px)
  Th step is co-located (lithologic-contact mimic rejection).
No catalogue/label bytes enter the surface. The catalogue is used only
(a) by the shared hide-and-recover evaluator as withheld truth, and
(b) to zero final dots on/near mapped faults (visible-fault masking).
Shared tools are reused unmodified: vendor/gems57 {grid,holdout,metric,
evaluate_holdout,uniqueness,validate,submission_writer}.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"vendor"))
from gems57 import grid as G, holdout as H, evaluate_holdout as EH, uniqueness as U, validate as V
from gems57.submission_writer import write_submission

BUDGET_MAIN = 37654

def robust_unit(a, valid, pct=99.0):
    out = np.zeros(a.shape, np.float32); v = valid & np.isfinite(a)
    if not v.any(): return out
    vals = a[v]; med = np.median(vals); q25,q75 = np.percentile(vals,[25,75])
    scale = max((q75-q25)/1.349, 1e-9); z=(a-med)/scale
    hi = max(float(np.percentile(z[v],pct)),1e-6)
    out[v]=np.clip(z[v]/hi,0,1); return out

def gradmag(a, sigma, valid):
    f = np.where(valid & np.isfinite(a), a, np.nan)
    med = np.nanmedian(f); f=np.where(np.isfinite(f),f,med).astype(np.float32)
    gy = ndi.gaussian_filter(f,sigma,order=(1,0),mode="nearest"); gx = ndi.gaussian_filter(f,sigma,order=(0,1),mode="nearest")
    return np.hypot(gx,gy).astype(np.float32)

def line_response(a, sigma, valid):
    f = np.where(valid & np.isfinite(a), a, np.nan); med=np.nanmedian(f)
    f=np.where(np.isfinite(f),f,med).astype(np.float32)
    axx=ndi.gaussian_filter(f,sigma,order=(0,2),mode="nearest"); ayy=ndi.gaussian_filter(f,sigma,order=(2,0),mode="nearest"); axy=ndi.gaussian_filter(f,sigma,order=(1,1),mode="nearest")
    tmp=np.sqrt(np.maximum(((axx-ayy)*.5)**2+axy**2,0)); l1=(axx+ayy)*.5+tmp; l2=(axx+ayy)*.5-tmp
    small=np.where(np.abs(l1)>=np.abs(l2),l2,l1); return (-small).astype(np.float32)

def build_surface():
    cache = ROOT/"data/cache/h86_components.npz"
    if cache.exists():
        z=np.load(cache); return {k:z[k] for k in z.files}
    g = G.load_grid(ROOT/"data")
    fp, cat = g.footprint, g.catalogue
    with rasterio.open(ROOT/"data/external/geodawn_rad_u8.tif") as ds:
        K,Th,Uu,TC = [ds.read(i).astype(np.float32) for i in (1,2,3,4)]
    valid = fp & (K>0)&(Th>0)&(Uu>0)&(TC>0)
    print(f"rad valid {valid.sum()} / footprint {fp.sum()}", flush=True)
    # robust global mixing regression K ~ Th+U+TC on a deterministic subsample (label-free)
    from sklearn.linear_model import HuberRegressor
    rng=np.random.default_rng(86); ys,xs=np.nonzero(valid)
    idx=rng.choice(len(ys), size=min(200_000,len(ys)), replace=False)
    X=np.column_stack([Th[ys[idx],xs[idx]],Uu[ys[idx],xs[idx]],TC[ys[idx],xs[idx]]])
    y=K[ys[idx],xs[idx]]
    m=HuberRegressor(alpha=0.1,max_iter=200).fit(X,y)
    print("mixing coefs", m.coef_, m.intercept_, flush=True)
    pred=(m.coef_[0]*Th+m.coef_[1]*Uu+m.coef_[2]*TC+m.intercept_).astype(np.float32)
    resid=np.where(valid, K-pred, 0).astype(np.float32)
    with rasterio.open(ROOT/"data/training_features.tif") as ds:
        rtp=ds.read(2)
    rtp_valid = fp & np.isfinite(rtp) & (rtp>-1e30)
    rg1=robust_unit(gradmag(resid,1.0,valid),valid); rl=robust_unit(line_response(resid,1.2,valid),valid)
    resid_b=(0.6*rg1+0.4*rl).astype(np.float32)
    mg1=robust_unit(gradmag(rtp,1.0,rtp_valid),fp); mg25=robust_unit(gradmag(rtp,2.5,rtp_valid),fp)
    mag_persist=np.minimum(mg1,mg25).astype(np.float32)
    broad_th=robust_unit(gradmag(Th,5.0,valid),valid)
    rawk_grad=robust_unit(gradmag(K,1.0,valid),valid)
    surface=(resid_b*(0.35+0.65*mag_persist)*(1.0-0.5*broad_th)).astype(np.float32)
    surface[~valid]=0
    comps=dict(surface=surface,resid_boundary=resid_b,mag_persist=mag_persist,broad_th=broad_th,
               rawk_grad=rawk_grad,valid=valid,footprint=fp,catalogue=cat,
               mixing_coef=m.coef_.astype(np.float64),mixing_intercept=np.array([m.intercept_]))
    np.savez_compressed(cache, **{k:v for k,v in comps.items()})
    return comps

def emit(surface, allowed, budget):
    """Local-maximum (3x3 NMS) dots, top-`budget` by surface; fills from non-NMS if short."""
    s=np.where(allowed, surface, 0).astype(np.float32)
    mx=ndi.maximum_filter(s,size=3,mode="constant",cval=0)
    cand=(s>0)&(s>=mx)
    ys,xs=np.nonzero(cand); order=np.argsort(-s[ys,xs],kind="stable")
    dots=np.zeros(s.shape,bool)
    take=order[:budget]; dots[ys[take],xs[take]]=True
    if dots.sum()<budget:
        rest=(s>0)&~dots; ys,xs=np.nonzero(rest); order=np.argsort(-s[ys,xs],kind="stable")
        take=order[:(budget-int(dots.sum()))]; dots[ys[take],xs[take]]=True
    return dots

def pooled_ci(per_cell, draws=2000, seed=86):
    cells=[c for c in per_cell.values() if c["n_truth"]>0]
    tp=np.array([c["tp"] for c in cells]); fp=np.array([c["fp"] for c in cells]); fn=np.array([c["fn"] for c in cells])
    rng=np.random.default_rng(seed); vals=[]
    for _ in range(draws):
        i=rng.integers(0,len(cells),len(cells)); T,F,N=tp[i].sum(),fp[i].sum(),fn[i].sum()
        vals.append(T/(T+0.2*F+0.8*N+1e-12))
    return [float(np.percentile(vals,2.5)),float(np.percentile(vals,97.5))]

def main():
    # Preserve this historical runner for audit, but do not repeat its bypass of
    # the literal pre-placement gate. A missing/untrusted witness also stops.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t0=time.time(); ev={}
    comps=build_surface(); surface,fp,cat=comps["surface"],comps["footprint"],comps["catalogue"]
    print("surface built", time.time()-t0, flush=True)
    g=G.load_grid(ROOT/"data"); ctx=H.build_holdout(g, seeds=(20,21), modes=("all",))
    ev["evaluator"]=dict(version=EH.VERSION, hashes=EH.implementation_hashes(),
                         withheld_positives=int(sum(c.n_truth for c in ctx.cells)), cells=[c.key for c in ctx.cells])
    # ---- leakage canary: each component alone, AUC hidden-truth vs active negatives
    from sklearn.metrics import roc_auc_score
    canary={}
    rng=np.random.default_rng(7)
    for name in ["resid_boundary","mag_persist","broad_th","rawk_grad","surface"]:
        comp=comps[name]; ys_all=[]; xs_all=[]; lab=[]; sco=[]
        for c in ctx.cells:
            ty,tx=c.truth_yx; sub=comp[c.bbox]
            pos=sub[ty,tx]
            neg_idx=np.argwhere(c.active); neg_idx=neg_idx[~np.isin(neg_idx[:,0]*100000+neg_idx[:,1], ty*100000+tx)]
            take=neg_idx[rng.choice(len(neg_idx),size=min(20000,len(neg_idx)),replace=False)]
            sco.append(np.concatenate([pos, sub[take[:,0],take[:,1]]]))
            lab.append(np.concatenate([np.ones(len(pos)),np.zeros(len(take))]))
        auc=float(roc_auc_score(np.concatenate(lab),np.concatenate(sco)))
        canary[name]=dict(auc=auc, leakage_flag=auc>0.90)
        print("canary",name,round(auc,4),flush=True)
    # shuffled control AUC
    sh=surface.copy(); flat=sh[fp]; rng.shuffle(flat); sh[fp]=flat
    ev["canary"]=canary
    # ---- Experiment 1: candidate vs magnetic-only control vs registry incumbent (benchmark only)
    def arm(surf, budget, allowed):
        dots=emit(surf, allowed, budget); r=H.evaluate(dots, ctx, cell_mode="all")
        r["ci95_cell_bootstrap"]=pooled_ci(r["folds"]); return dots, r
    allowed_fp=fp
    dots_c, cand = arm(surface, BUDGET_MAIN, allowed_fp)
    _, magctl = arm(comps["mag_persist"], BUDGET_MAIN, allowed_fp)
    from gems57.uniqueness import _dots
    reg_dots=np.zeros(fp.shape,bool)
    with rasterio.open(ROOT/"data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        reg_dots=_dots(ds.read(1)) & fp
    incumbent=H.evaluate(reg_dots, ctx, cell_mode="all"); incumbent["ci95_cell_bootstrap"]=pooled_ci(incumbent["folds"])
    ev["experiment1"]=dict(budget=BUDGET_MAIN, candidate=cand, mag_only_control=magctl, registry_incumbent_benchmark_only=incumbent)
    print("EXP1 cand",cand["pooled_dti"],"mag",magctl["pooled_dti"],"incumbent",incumbent["pooled_dti"],flush=True)
    # ---- Experiment 2: budget sweep
    sweep={}
    for b in (20000,60000):
        _,r=arm(surface,b,allowed_fp); sweep[str(b)]=r; print("EXP2 budget",b,r["pooled_dti"],flush=True)
    ev["experiment2_budget_sweep"]=sweep
    # ---- Experiment 3: ablation, no magnetic gate
    _, abl = arm(comps["resid_boundary"], BUDGET_MAIN, allowed_fp)
    ev["experiment3_ablation_resid_only"]=abl; print("EXP3 resid-only",abl["pooled_dti"],flush=True)
    # choose budget = best pooled among {20000,37654,60000} (predeclared sweep, exp2)
    cand_by_budget={20000:sweep["20000"], BUDGET_MAIN:cand, 60000:sweep["60000"]}
    best_budget=max(cand_by_budget, key=lambda b: cand_by_budget[b]["pooled_dti"])
    ev["chosen_budget"]=best_budget
    print("chosen budget",best_budget,flush=True)
    # ---- uniqueness: surface (pre-placement) Spearman vs registry, then final dots
    man=json.loads((ROOT/"research/upstream/data_manifest.json").read_text())
    records=[]
    for e in man["files"]:
        if e["group"]=="scored":
            records.append(dict(repo=e["repo"], submission=Path(e["dest"]).name, file=str(ROOT/"data"/e["dest"]), sha256=e["sha256"]))
    surf_rows=[]
    for rec in records:
        with rasterio.open(rec["file"]) as ds: theirs=ds.read(1)
        theirs=np.where(np.isfinite(theirs),theirs,0)
        r=U.surface_rho(surface, theirs, fp); surf_rows.append(dict(submission=rec["submission"], **r))
    ev["surface_uniqueness"]=[dict(submission=r["submission"],spearman_full_footprint=r["spearman_full_footprint"]) for r in surf_rows]
    print("surface worst rho", max(r["spearman_full_footprint"] for r in surf_rows), flush=True)
    # final dots: zero on catalogue dilated 2px (visible-fault masking for live submission)
    near_cat=ndi.binary_dilation(cat, iterations=2)
    dots_final=emit(surface, fp & ~near_cat, best_budget)
    ev["final_dots"]=int(dots_final.sum()); ev["dots_on_catalogue"]=int((dots_final&cat).sum())
    pred=np.where(dots_final,1.0,0.0).astype(np.float32)
    # surface+final rho/overlap via shared checker (list registry = diagnostic scope, not complete)
    uniq=U.compare_array_to_registry(pred, records, fp)
    ev["final_uniqueness"]=uniq
    print("final uniqueness summary:", {k:uniq.get(k) for k in ("unique","worst_rho","worst_overlap","registry_rasters_checked")}, flush=True)
    # ---- write submission through shared writer
    ts=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem=f"gems86-h86-rmrb-{best_budget}dots-{ts}"
    out=ROOT/"docs/downloads"/f"{stem}-zeros.tif"
    note=f"H86 radiometric mixing-residual boundary x RTP edge persistence, {best_budget} dots, catalogue+2px masked; HOLDOUT screen only"
    assert len(note)<=140, len(note)
    meta=dict(lane="H86-RMRB", budget=best_budget)
    receipt=write_submission(out, pred, ROOT/"data/sample_submission.tif", fp, note=note, name=stem, catalogue=cat, metadata=meta)
    ev["writer_receipt"]=receipt
    val=V.validate(out, footprint=fp, catalogue=cat); ev["validator"]=val
    ev["raster_sha256"]=val["sha256"]; ev["submission_file"]=str(out.relative_to(ROOT)); ev["submission_name"]=stem; ev["note"]=note
    ev["elapsed_s"]=time.time()-t0
    (ROOT/"docs/evidence/lane86_results.json").write_text(json.dumps(ev,indent=2,default=str)+"\n")
    print(json.dumps(dict(submission=str(out), sha=val["sha256"], dots=int(dots_final.sum()),
                          cand_dti=cand["pooled_dti"], best_budget=best_budget, validator=val["all_checks_passed"]),indent=2))
if __name__=="__main__": main()
