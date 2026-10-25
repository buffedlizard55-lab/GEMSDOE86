#!/usr/bin/env python3
"""H86M-LT full-registry uniqueness scan (PA-86 like-for-like).

Restores must have been run first (scripts/restore_registry_inventory.py -> data/registry_ext/).
For every registry raster: forward/reverse 3-px overlap for discrete dot-fields
(support <= 90k, KDTree) and Pearson correlation of (a) final dots and (b) the
reconstructed belief surface vs the registry values over the footprint.
Binary-binary Pearson == Spearman with ties. Writes docs/evidence/h86m-lt-full-registry-uniqueness.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/h86m"
NAME = "gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros"

def load(p): return np.nan_to_num(rasterio.open(p).read(1)) > 0

samp = rasterio.open(ROOT / 'data/bridge/sample_submission.tif').read(1)
foot = ~np.isnan(samp)
known = load(ROOT / 'data/bridge/existing_faults.tif') & foot
allowed = foot & ~known
dcat = distance_transform_edt(~known)
dots = np.load(CACHE / 'dots_final.npy')
tif_dots = load(ROOT / f'docs/downloads/{NAME}.tif')
assert np.array_equal(dots, tif_dots), "dots_final mismatch vs shipped TIFF"
my_pts = np.argwhere(dots)
my_tree = cKDTree(my_pts)

# --- reconstruct belief surface exactly as scripts/run_h86m_lt.py ---
exec(open(CACHE / 'e2_tomography.py').read().split("keys = list(PATHS)")[0].split("dcat = distance_transform_edt(~known)")[1])
qr = np.load(CACHE / 'e2e_QR.npz'); Q, R, n_vec, y, A_g = qr['Q'], qr['R'], qr['n'], qr['y'], qr['A']
NG = 1081; gg = np.arange(NG); core = gg < 1080
levA = np.where(core, gg // 216, 0); levB = np.where(core, (gg // 36) % 6, 0)
levC = np.where(core, (gg // 9) % 4, 0); levD = np.where(core, (gg // 3) % 3, 0)
levE = np.where(core, gg % 3, 0); isCOL = (gg == 1080)
def rho_from_theta(th):
    a = np.concatenate([[0], np.cumsum(th[1:5])]); b = np.concatenate([[0], np.cumsum(th[5:10])])
    c = np.concatenate([[0], np.cumsum(th[10:13])]); e = np.concatenate([[0], np.cumsum(th[14:16])])
    eta = th[0] + a[levA] + b[levB] + c[levC] + th[13] * levD + e[levE]
    return np.clip(np.exp(np.where(isCOL, th[0] + th[16], eta)), 0, 0.6)
def predict(rho, Qm, Rm, n):
    T = Qm @ rho; M = Rm @ rho; K = float(A_g @ rho)
    return T / (0.8 * K + 0.2 * (T + n - M))
fit_mask = np.array([k != "poisson81" for k in list(PATHS)])
LB = np.array([-20] + [0]*4 + [0]*5 + [0]*3 + [-5] + [0]*2 + [-10], float)
UB = np.array([0] + [5]*4 + [5]*5 + [5]*3 + [5] + [5]*2 + [5], float)
TH0 = np.array([np.log(0.0002)] + [0.7]*4 + [0.5]*5 + [0.4]*3 + [0.0] + [0.5]*2 + [-1.0])
theta = least_squares(lambda th: predict(rho_from_theta(th), Q[fit_mask], R[fit_mask], n_vec[fit_mask]) - y[fit_mask],
                      TH0, bounds=(LB, UB), method='trf', max_nfev=3000).x
gmap = np.load(CACHE / 'gmap_e2e.npy')
rho_map = rho_from_theta(theta)[gmap].astype(np.float32); rho_map[~allowed] = 0; rho_map[dcat <= 3] = 0
maskA = allowed & (dcat > 3)
def norm_map(m, K=16000.0):
    m = np.where(maskA, m, 0).astype(np.float64); return (m * (K / max(m.sum(), 1e-9))).astype(np.float32)
_f2 = json.load(open(CACHE / 'e2d_fit.json')); _b2 = np.load(CACHE / 'e2b_QR.npz')
def _pred_b(rho, Qm, Rm, n, A):
    T = Qm @ rho; M = Rm @ rho; K = float(A @ rho); return T / (0.8*K + 0.2*(T + n - M))
_rhb = least_squares(lambda r: _pred_b(r, _b2['Q'], _b2['R'], _b2['n'], _b2['A']) - _b2['y'],
                     np.full(25, 0.0025), bounds=(0, 0.6), method='trf', max_nfev=2000).x
combined = ((norm_map(rho_map).astype(np.float64)
             + norm_map(np.array(_f2['rho_param'])[np.load(CACHE / 'gmap_e2d.npy')].astype(np.float32))
             + norm_map(_rhb[np.load(CACHE / 'gmap.npy')].astype(np.float32))) / 3.0).astype(np.float32)
S = np.load(CACHE / 'S_surface.npy')
idx_allowed = np.nonzero(allowed); g_allowed = gmap[idx_allowed]
meanS_g = np.bincount(g_allowed, weights=S[idx_allowed], minlength=NG) / np.maximum(np.bincount(g_allowed, minlength=NG), 1)
rho_px = combined * np.clip(S / np.maximum(meanS_g[gmap], 1e-9), 0, 3.0).astype(np.float32)
rho_px[~allowed] = 0; rho_px[dcat <= 3] = 0
rho_px = (rho_px * (16000.0 / float(rho_px[idx_allowed].sum()))).astype(np.float32)
np.save(CACHE / 'rho_px_final.npy', rho_px)
print("surface reconstructed; K=", float(rho_px.sum()), flush=True)

surf_f = rho_px[foot].astype(np.float64); dots_f = dots[foot].astype(np.float64)
def pearson_pre(x):
    xm = x - x.mean(); return xm, float(np.sqrt((xm * xm).sum()))
surf_c, surf_n = pearson_pre(surf_f); dots_c, dots_n = pearson_pre(dots_f)

files = sorted((ROOT / 'data/registry_ext').glob('*.tif'))
rows = []
for i, p in enumerate(files):
    try:
        a = np.nan_to_num(rasterio.open(p).read(1).astype(np.float32))
    except Exception as e:
        rows.append(dict(file=p.name, error=str(e))); continue
    if a.shape != foot.shape:
        rows.append(dict(file=p.name, error=f"shape {a.shape}")); continue
    sup = a > 0; nb = int(sup.sum())
    af = a[foot].astype(np.float64); ac = af - af.mean(); an = float(np.sqrt((ac * ac).sum()))
    r_surf = float((surf_c @ ac) / (surf_n * an)) if an > 0 else 0.0
    r_dots = float((dots_c @ ac) / (dots_n * an)) if an > 0 else 0.0
    row = dict(file=p.name, support=nb, pearson_surface=r_surf, pearson_dots=r_dots)
    if 0 < nb <= 90000:
        their_pts = np.argwhere(sup)
        d_fwd, _ = cKDTree(their_pts).query(my_pts, k=1)
        d_rev, _ = my_tree.query(their_pts, k=1)
        row['dotfield'] = True
        row['forward_overlap_3px'] = float((d_fwd <= 3).mean())
        row['reverse_overlap_3px'] = float((d_rev <= 3).mean())
    else:
        row['dotfield'] = False
    rows.append(row)
    if (i + 1) % 100 == 0: print(i + 1, flush=True)

ok = [r for r in rows if 'error' not in r]
df = [r for r in ok if r.get('dotfield')]
summary = dict(
    candidate=NAME, registry_files=len(files), measured=len(ok), errors=len(rows) - len(ok),
    dotfields=len(df), non_dotfields=len(ok) - len(df),
    max_forward_overlap_3px=max((r['forward_overlap_3px'] for r in df), default=None),
    max_pearson_dots=max((abs(r['pearson_dots']) for r in ok), default=None),
    max_pearson_surface=max((abs(r['pearson_surface']) for r in ok), default=None),
    firings_forward_gt_070=[r for r in df if r['forward_overlap_3px'] > 0.70],
    firings_pearson_dots_gt_090=[r for r in ok if abs(r['pearson_dots']) > 0.90],
    firings_pearson_surface_gt_090=[r for r in ok if abs(r['pearson_surface']) > 0.90],
    top10_forward=sorted(df, key=lambda r: -r['forward_overlap_3px'])[:10],
    top10_pearson_dots=sorted(ok, key=lambda r: -abs(r['pearson_dots']))[:10],
    note="PA-86 like-for-like: dot-field gate support<=90k; binary-binary Pearson==Spearman with ties; "
         "continuous registry surfaces use Pearson (point-biserial) as a conservative rank proxy and are not dot-gated. "
         "Registry is the hash-verified restore (655 entries); completeness is snapshot scope, not an organizer registry.",
)
summary['pass'] = bool(not summary['firings_forward_gt_070'] and not summary['firings_pearson_dots_gt_090'] and not summary['firings_pearson_surface_gt_090'])
json.dump(dict(summary=summary, rows=rows), open(ROOT / 'docs/evidence/h86m-lt-full-registry-uniqueness.json', 'w'), indent=1)
print(json.dumps({k: summary[k] for k in ['registry_files','measured','errors','dotfields','max_forward_overlap_3px','max_pearson_dots','max_pearson_surface','pass']}, indent=1))
print("top forward:", [(r['file'][:60], round(r['forward_overlap_3px'], 3)) for r in summary['top10_forward']])
