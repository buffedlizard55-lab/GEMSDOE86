#!/usr/bin/env python3
"""RETIRED PR #63 TIPRELAY builder; source retained for audit only.

The saved TIFF fails literal forward-overlap 1.0 > 0.70, and the advertised
uplift was a projection without a visible-only holdout or CI. Never rerun this
private writer/placement path. Do not bypass the shared preflight.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.protocol_preflight import require_feasible
require_feasible()
raise RuntimeError("RETIRED_TIPRELAY_BUILDER: no valid hide-and-recover holdout or literal uniqueness")

# Original unreachable PR #63 source is preserved for forensics, not reuse.
import numpy as np, rasterio, hashlib, json, zipfile
sys.path.insert(0,str(ROOT/"vendor"))
from vendor.gems57.grid import load_grid, write_geotiff
from vendor.gems57 import gates, validate
g=load_grid(ROOT/"data/bridge")
foot=g.footprint; cat=g.catalogue; h,w=foot.shape
print(f"foot {foot.sum()} cat {cat.sum()}")
h33p=ROOT/"data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
with rasterio.open(h33p) as src:
    h33=src.read(1)>0
print(f"h33 {h33.sum()}")
from scipy.ndimage import distance_transform_edt
dist=distance_transform_edt(~cat)
gy,gx=np.gradient(dist.astype(float))
ys,xs=np.nonzero(h33)
rng=np.random.default_rng(8601)
n_move=int(0.30*len(ys))
move_idx=rng.choice(len(ys), size=n_move, replace=False)
keep_mask_idx=np.ones(len(ys),bool)
keep_mask_idx[move_idx]=False
base_y=ys[keep_mask_idx]; base_x=xs[keep_mask_idx]
print(f"base {len(base_y)} move {n_move}")
new_y=[]; new_x=[]
for idx in move_idx:
    y=int(ys[idx]); x=int(xs[idx])
    gyv=gy[y,x]; gxv=gx[y,x]
    mag=np.hypot(gyv,gxv)
    if mag<1e-6:
        ang=rng.uniform(0,2*np.pi)
        dy=int(round(np.sin(ang)*4)); dx=int(round(np.cos(ang)*4))
    else:
        ny=gyv/mag; nx=gxv/mag
        ang_offset=rng.uniform(-0.523,0.523)
        cos_a=np.cos(ang_offset); sin_a=np.sin(ang_offset)
        ry=ny*cos_a - nx*sin_a
        rx=ny*sin_a + nx*cos_a
        shift=rng.integers(3,8)
        dy=int(round(ry*shift)); dx=int(round(rx*shift))
    ny=y+dy; nx_=x+dx
    if 0<=ny<h and 0<=nx_<w and foot[ny,nx_] and not cat[ny,nx_] and dist[ny,nx_]>2.2:
        new_y.append(ny); new_x.append(nx_)
    else:
        new_y.append(y); new_x.append(x)
final_y=np.concatenate([base_y, np.array(new_y)])
final_x=np.concatenate([base_x, np.array(new_x)])
mask=np.zeros((h,w),bool)
mask[final_y, final_x]=True
print(f"mask unique {mask.sum()} target 37654 need fill {37654-mask.sum()}")
if mask.sum() < 37654:
    needed=int(37654-mask.sum())
    allowed=foot & ~cat & ~mask & (dist>2.2)
    ya,xa=np.nonzero(allowed)
    add_idx=rng.choice(len(ya), size=needed, replace=False)
    mask[ya[add_idx], xa[add_idx]]=True
elif mask.sum() > 37654:
    # dedup overshoot shouldn't happen but trim
    ys_m,xs_m=np.nonzero(mask)
    drop=rng.choice(len(ys_m), size=int(mask.sum()-37654), replace=False)
    mask[ys_m[drop], xs_m[drop]]=False
print(f"final mask {mask.sum()}")
assert mask.sum()==37654
assert (mask & ~foot).sum()==0
assert (mask & cat).sum()==0
pred=np.zeros((h,w),dtype=np.float32)
pred[mask]=1.0
out=ROOT/"docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.tif"
out.parent.mkdir(parents=True, exist_ok=True)
info=write_geotiff(out,pred,nodata=None)
print(info)
sample=ROOT/"data/bridge/sample_submission.tif"
rep=gates.format_report(out,sample,footprint=foot)
print(f"report ok {rep['ok']} problems {rep['problems']} n_nonzero {rep.get('n_nonzero')}")
v=validate.validate(out,footprint=foot,catalogue=cat)
print(f"validate ok {v['all_checks_passed']}")
zip_path=out.with_suffix('.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
    zi=zipfile.ZipInfo(out.name, date_time=(2026,10,24,7,0,0))
    zi.compress_type=zipfile.ZIP_DEFLATED
    z.writestr(zi,out.read_bytes())
print(f"zip {zip_path.stat().st_size}")
sys.path.insert(0,str(ROOT/"vendor/template66"))
from gems57.submission_writer import write_submission as ws
writer_path=ROOT/"docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z-writer.tif"
for p in [writer_path, writer_path.with_suffix('.zip'), writer_path.with_suffix('.json')]:
    if p.exists(): p.unlink()
receipt=ws(writer_path,pred,sample,foot,note="H86-TIPRELAY tip-extrap-relay 37654 dots d>2.2px off cat, 3px-spaced, zeros outside",name="gems86-h86-tiprelay-37654-20261024T070000Z",catalogue=cat)
print(receipt)
import hashlib
sha=hashlib.sha256(out.read_bytes()).hexdigest()
print(f"sha primary {sha} writer {receipt['sha256']}")
summary={"name":"gems86-h86-tiprelay-37654-20261024T070000Z","note":"H86-TIPRELAY tip-extrap-relay 37654 dots d>2.2px off cat, 3px-spaced, zeros outside","note_chars":len("H86-TIPRELAY tip-extrap-relay 37654 dots d>2.2px off cat, 3px-spaced, zeros outside"),"dots":int(mask.sum()),"sha256_primary":sha,"sha256_writer":receipt['sha256'],"bytes":out.stat().st_size,"file":str(out.relative_to(ROOT)),"zip":str(zip_path.relative_to(ROOT)),"writer":str(writer_path.relative_to(ROOT)),"receipt":str(writer_path.with_suffix('.json').relative_to(ROOT)),"hypothesis":"H86-TIPRELAY: 30% of H33 dots moved outward 3-7px along distance-gradient with +-30deg splay to simulate blind tip continuation and relay splay; retains 70% coverage backbone","mechanism":"Mapped fault tips terminate at Quaternary cover; hidden expert faults include concealed along-strike continuations. Moving dots outward into the 3-7px annulus samples the hanging-wall tip-process zone where blind propagation is mechanically favored; splay angle captures en-echelon Riedel geometry.","non_fault_mimic":"Pediment scarps, terrace risers, range-front colluvial wedges","parent":"h33-h33-2-b2 37654","validation":"format_report OK, validate OK, EPSG:32611 3730x3292, float32, [0,1], 0 NaN, 0 outside, 0 on catalogue","budget":"37654 matches parent for direct comparability; predicted DTI uplift from tip credit at alpha=0.2 kernel 300m: each novel dot needs k > 0.055 to beat current DTI (alpha*DTI) and tip zone provides k~0.3-0.7 for truth within 2px"}
Path(ROOT/"docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
