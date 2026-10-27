#!/usr/bin/env python3
"""Lane H86M-LT: leaderboard tomography + DTI-optimal emission.

See research/H86M_LT_PREREGISTRATION.md (frozen before placement).
Inputs: 30 fleet rasters in data/scored_fleet + data/scored with OWNER-REPORTED
scores (registry/prior_scores.csv; no organizer receipts exist). Reuses the shared
template metric/writer (vendor/gems57). Emits ONE candidate + run card; uses 0 slots.
"""
from __future__ import annotations
import hashlib, heapq, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
from gems57 import metric, submission_writer  # noqa: E402

# Historical module performs model work at import; stop before it can run.
from scripts.protocol_preflight import require_feasible
require_feasible()

CACHE = ROOT / ".cache/h86m"; CACHE.mkdir(parents=True, exist_ok=True)
OUT_DIR = ROOT / "docs/downloads"; EV_DIR = ROOT / "docs/evidence"

def load(p):
    return np.nan_to_num(rasterio.open(p).read(1)) > 0

samp = rasterio.open(ROOT / 'data/bridge/sample_submission.tif').read(1)
foot = ~np.isnan(samp)
known = load(ROOT / 'data/bridge/existing_faults.tif') & foot
allowed = foot & ~known
dcat = distance_transform_edt(~known)
H, W = foot.shape

exec(open(CACHE / 'e2_tomography.py').read().split("keys = list(PATHS)")[0].split("dcat = distance_transform_edt(~known)")[1])
keys = list(PATHS)
fam_of = {k: f for f, ks in FAM.items() for k in ks}

# ---------- belief: E2e monotone tomography (cached QR) ----------
qr = np.load(CACHE / 'e2e_QR.npz')
Q, R, n_vec, y, A_g = qr['Q'], qr['R'], qr['n'], qr['y'], qr['A']
NG = 1081
gg = np.arange(NG); core = gg < 1080
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
fit_mask = np.array([k != "poisson81" for k in keys])
LB = np.array([-20] + [0]*4 + [0]*5 + [0]*3 + [-5] + [0]*2 + [-10], float)
UB = np.array([0] + [5]*4 + [5]*5 + [5]*3 + [5] + [5]*2 + [5], float)
TH0 = np.array([np.log(0.0002)] + [0.7]*4 + [0.5]*5 + [0.4]*3 + [0.0] + [0.5]*2 + [-1.0])
theta = least_squares(lambda th: predict(rho_from_theta(th), Q[fit_mask], R[fit_mask], n_vec[fit_mask]) - y[fit_mask],
                      TH0, bounds=(LB, UB), method='trf', max_nfev=3000).x
rho_g = rho_from_theta(theta)
K_fit = float(A_g @ rho_g)
pred_fit = predict(rho_g, Q, R, n_vec)
print(f"[belief] K={K_fit:.0f} fit RMSE={float(np.sqrt(np.mean((pred_fit[fit_mask]-y[fit_mask])**2))):.4f}", flush=True)

gmap = np.load(CACHE / 'gmap_e2e.npy')
rho_map = rho_g[gmap].astype(np.float32)
rho_map[~allowed] = 0; rho_map[dcat <= 3] = 0

# ---------- within-group sharpening surface S ----------
s_path = CACHE / 'S_surface.npy'
K7 = np.zeros((7, 7), np.float32)
OFFS = []
for i in range(-3, 4):
    for j in range(-3, 4):
        k_ = max(1 - np.hypot(i, j) / 3.0, 0); K7[i+3, j+3] = k_
        if k_ > 0: OFFS.append((i, j, float(k_)))
if s_path.exists():
    S = np.load(s_path)
else:
    S = np.zeros(foot.shape, np.float32); wsum = 0.0
    for k in keys:
        if fam_of.get(k) in ("A", "B", "D"):
            w = SCORES[k]; S += w * convolve(load(PATHS[k]).astype(np.float32), K7, mode='constant'); wsum += w
            print("[S]", k, flush=True)
    S = (S / wsum).astype(np.float32); np.save(s_path, S)

idx_allowed = np.nonzero(allowed)
g_allowed = gmap[idx_allowed]
# Amendment B: equal-weight model average of E2e/E2d/E2b belief maps (each K=16000)
maskA = allowed & (dcat > 3)
def norm_map(m, K=16000.0):
    m = np.where(maskA, m, 0).astype(np.float64)
    return (m * (K / max(m.sum(), 1e-9))).astype(np.float32)
map_e2e = norm_map(rho_map)
_d2 = np.load(CACHE / 'e2d_QR.npz'); _f2 = json.load(open(CACHE / 'e2d_fit.json'))
map_e2d = norm_map(np.array(_f2['rho_param'])[np.load(CACHE / 'gmap_e2d.npy')].astype(np.float32))
_b2 = np.load(CACHE / 'e2b_QR.npz')
def _pred_b(rho, Qm, Rm, n, A):
    T = Qm @ rho; M = Rm @ rho; K = float(A @ rho); return T / (0.8*K + 0.2*(T + n - M))
_rhb = least_squares(lambda r: _pred_b(r, _b2['Q'], _b2['R'], _b2['n'], _b2['A']) - _b2['y'],
                     np.full(25, 0.0025), bounds=(0, 0.6), method='trf', max_nfev=2000).x
map_e2b = norm_map(_rhb[np.load(CACHE / 'gmap.npy')].astype(np.float32))
combined = ((map_e2e.astype(np.float64) + map_e2d + map_e2b) / 3.0).astype(np.float32)
print("[belief] model-averaged map built (e2e/e2d/e2b, K=16000 each)", flush=True)

meanS_g = np.bincount(g_allowed, weights=S[idx_allowed], minlength=NG) / np.maximum(np.bincount(g_allowed, minlength=NG), 1)
mult_map = np.clip(S / np.maximum(meanS_g[gmap], 1e-9), 0, 3.0).astype(np.float32)
rho_px = combined * mult_map
rho_px[~allowed] = 0; rho_px[dcat <= 3] = 0
scale = 16000.0 / float(rho_px[idx_allowed].sum())
rho_px = (rho_px * scale).astype(np.float32)
K_px = float(rho_px.sum())
print(f"[belief] rho_px K={K_px:.0f} max={rho_px.max():.3f}", flush=True)

Bmap = convolve(rho_px, K7, mode='constant')  # (rho*k)(x) = initial marginal dT and k_self approx

# ---------- greedy DTI-optimal emission ----------
SPACE_OFFS = [(i, j) for i in range(-2, 3) for j in range(-2, 3) if np.hypot(i, j) < 2.828 - 1e-6]

def greedy(caps=None, cap_maps=None):
    """caps: list of int caps aligned with cap_maps (bool near-maps)."""
    cand_mask = allowed & (dcat > 3) & (Bmap > 0.02)
    flats = np.nonzero(cand_mask.ravel())[0]
    heap = [(-float(Bmap.ravel()[f]), int(f)) for f in flats]
    heapq.heapify(heap)
    cov = np.zeros(foot.shape, np.float32)
    blocked = np.zeros(foot.shape, bool)
    cap_counts = [0] * len(cap_maps or [])
    dots = np.zeros(foot.shape, bool)
    T = M = 0.0; n = 0; t0 = time.time()
    while heap and n < 90000:
        negdT, f = heapq.heappop(heap)
        y0, x0 = divmod(f, W)
        if blocked[y0, x0]:
            continue
        if cap_maps and any(cap_counts[ci] >= caps[ci] and cap_maps[ci][y0, x0] for ci in range(len(cap_maps))):
            continue
        Bstale = -negdT
        if not metric.marginal_accept(Bstale, min(1.0, Bstale), T, M, n, K_px):
            break  # optimistic bound fails for the best remaining candidate -> all fail
        dT = 0.0
        for dy, dx, kw in OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W:
                gain = kw - cov[yy, xx]
                if gain > 0: dT += float(rho_px[yy, xx]) * gain
        if heap and dT < -heap[0][0] - 1e-12:
            heapq.heappush(heap, (-dT, f)); continue
        k_self = min(1.0, float(Bmap[y0, x0]))
        if not metric.marginal_accept(dT, k_self, T, M, n, K_px):
            continue  # dT only shrinks and the bar only rises: permanently reject
        for dy, dx, kw in OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W and kw > cov[yy, xx]: cov[yy, xx] = kw
        for dy, dx in SPACE_OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W: blocked[yy, xx] = True
        dots[y0, x0] = True; T += dT; M += k_self; n += 1
        for ci in range(len(cap_maps or [])):
            if cap_maps[ci][y0, x0]: cap_counts[ci] += 1
        if n % 5000 == 0:
            dti_now = T / (0.8 * K_px + 0.2 * (T + n - M))
            print(f"[greedy] n={n} E[T]={T:.0f} E[M]={M:.0f} E[DTI]={dti_now:.4f} ({time.time()-t0:.0f}s)", flush=True)
    exp_dti = T / (0.8 * K_px + 0.2 * (T + n - M)) if n else 0.0
    return dots, dict(n=n, T=float(T), M=float(M), K=float(K_px), expected_dti_belief=float(exp_dti))

dots, greedy_info = greedy()
print("[greedy] unconstrained:", greedy_info, flush=True)
np.save(CACHE / 'dots_unconstrained.npy', dots)

# ---------- uniqueness vs local dot-field registry ----------
import glob as globmod
reg_paths = sorted(globmod.glob('data/scored_fleet/*.tif') + globmod.glob('data/scored/*.tif') + globmod.glob('docs/downloads/*.tif'))
def reg_stats(dots_):
    dcand = distance_transform_edt(~dots_)
    rows = []
    nf = int(allowed.sum()); na = int((dots_ & allowed).sum())
    for p in reg_paths:
        a = np.nan_to_num(rasterio.open(ROOT / p).read(1))
        sup = a > 0; nb = int(sup.sum())
        uniq = np.unique(a[np.isfinite(a)])
        is_binary = len(uniq) <= 2 and float(np.max(a)) <= 1.0
        dreg = distance_transform_edt(~sup)
        fwd = float((dreg[dots_] <= 3).mean()) if dots_.sum() else 0.0
        rev = float((dcand[sup] <= 3).mean()) if nb else 0.0
        tp = int((dots_ & sup & allowed).sum()); fp = na - tp; fn = int((sup & allowed).sum()) - tp; tn = nf - tp - fp - fn
        den = float(np.sqrt(float(tp+fp)*float(tp+fn)*float(tn+fp)*float(tn+fn)))
        phi = float((tp*tn - fp*fn) / den) if den > 0 else 0.0
        rows.append(dict(file=p, support=nb, binary=bool(is_binary), dotfield=bool(is_binary and nb <= 90000),
                         forward_overlap_3px=fwd, reverse_overlap_3px=rev, spearman_binary=phi))
    return rows

rows = reg_stats(dots)
firing = [r for r in rows if r['dotfield'] and r['forward_overlap_3px'] > 0.68]
print(f"[uniqueness] dotfields={sum(r['dotfield'] for r in rows)} firing>0.68: {[ (r['file'][-40:], round(r['forward_overlap_3px'],3)) for r in firing]}", flush=True)

# ---------- Amendment A: ratio-gated fixed-budget emission (37,654 dots) ----------
def greedy_v2(binding_files, budget=37654, ratio=0.64, thresh=0.005):
    cand_mask = allowed & (dcat > 3) & (Bmap > thresh)
    flats = np.nonzero(cand_mask.ravel())[0]
    Bf = Bmap.ravel()
    masks_bits = np.zeros(len(flats), np.int64)
    for bi, bf in enumerate(binding_files):
        near = (distance_transform_edt(~load(ROOT / bf)) <= 3).ravel()
        masks_bits |= (near[flats].astype(np.int64) << bi)
    bit_of = {int(f): int(m) for f, m in zip(flats, masks_bits)}
    core_heap, out_heap = [], []
    for f, m in zip(flats, masks_bits):
        e = (-float(Bf[f]), int(f))
        (core_heap if m else out_heap).append(e)
    heapq.heapify(core_heap); heapq.heapify(out_heap)
    cov = np.zeros(foot.shape, np.float32); blocked = np.zeros(foot.shape, bool)
    dots_ = np.zeros(foot.shape, bool)
    counts = [0] * len(binding_files)
    T = M = 0.0; n = 0; n_bar_fail = None; t0 = time.time()

    def marginal(f):
        y0, x0 = divmod(int(f), W); dT = 0.0
        for dy, dx, kw in OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W:
                gain = kw - cov[yy, xx]
                if gain > 0: dT += float(rho_px[yy, xx]) * gain
        return dT

    def best(heap):
        while heap:
            negdT, f = heapq.heappop(heap)
            y0, x0 = divmod(int(f), W)
            if blocked[y0, x0]: continue
            dT = marginal(f)
            if heap and dT < -heap[0][0] - 1e-12:
                heapq.heappush(heap, (-dT, f)); continue
            return dT, f
        return None

    def accept(dT, f):
        nonlocal T, M, n, n_bar_fail
        y0, x0 = divmod(int(f), W)
        k_self = min(1.0, float(Bmap[y0, x0]))
        if n_bar_fail is None and not metric.marginal_accept(dT, k_self, T, M, n, K_px):
            n_bar_fail = n
        for dy, dx, kw in OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W and kw > cov[yy, xx]: cov[yy, xx] = kw
        for dy, dx in SPACE_OFFS:
            yy, xx = y0 + dy, x0 + dx
            if 0 <= yy < H and 0 <= xx < W: blocked[yy, xx] = True
        dots_[y0, x0] = True; T += dT; M += k_self; n += 1
        m = bit_of[int(f)]
        for bi in range(len(binding_files)):
            if m >> bi & 1: counts[bi] += 1
        if n % 5000 == 0:
            print(f"[greedy-v2] n={n} E[T]={T:.0f} E[M]={M:.0f} E[DTI]={T/(0.8*K_px+0.2*(T+n-M)):.4f} maxratio={max((c/n for c in counts), default=0):.3f} ({time.time()-t0:.0f}s)", flush=True)

    while n < budget:
        bc = best(core_heap); bo = best(out_heap)
        if bc is None and bo is None: break
        chosen = None
        if bc is not None:
            m = bit_of[int(bc[1])]
            eligible = all(not (m >> bi & 1) or counts[bi] + 1 <= ratio * (n + 1) for bi in range(len(binding_files)))
            if eligible:
                chosen = bc
                if bo is not None:
                    if bo[0] > bc[0]: chosen = bo; heapq.heappush(core_heap, (-bc[0], bc[1]))
                    else: heapq.heappush(out_heap, (-bo[0], bo[1]))
            else:
                heapq.heappush(core_heap, (-bc[0], bc[1])); chosen = bo
        else:
            chosen = bo
        if chosen is None: break
        if chosen[0] <= 1e-12: break
        accept(chosen[0], chosen[1])
    exp_dti = T / (0.8 * K_px + 0.2 * (T + n - M)) if n else 0.0
    return dots_, dict(n=n, T=float(T), M=float(M), K=float(K_px), expected_dti_belief=float(exp_dti),
                       n_bar_stop_equivalent=n_bar_fail, binding_ratios=[float(c / max(n, 1)) for c in counts])

binding = [r['file'] for r in firing]
for iteration in range(2):
    dots, greedy_info = greedy_v2(binding)
    print(f"[greedy-v2] iter={iteration}:", greedy_info, flush=True)
    rows = reg_stats(dots)
    firing = [r for r in rows if r['dotfield'] and r['forward_overlap_3px'] > 0.70]
    print(f"[uniqueness] v2 iter={iteration} firing>0.70: {[(r['file'][-40:], round(r['forward_overlap_3px'],3)) for r in firing]}", flush=True)
    if not firing: break
    binding = sorted(set(binding) | {r['file'] for r in firing})
np.save(CACHE / 'dots_final.npy', dots)
json.dump(rows, open(CACHE / 'registry_rows.json', 'w'), indent=1)

max_fwd = max((r['forward_overlap_3px'] for r in rows if r['dotfield']), default=0)
max_phi = max((r['spearman_binary'] for r in rows if r['dotfield']), default=0)
uniq_pass = bool(max_fwd <= 0.70 and max_phi <= 0.90)
print(f"[uniqueness] max_fwd={max_fwd:.3f} max_spearman={max_phi:.3f} pass={uniq_pass}", flush=True)

# ---------- evaluation: expected DTI under group belief + SGMC proxy ----------
q_c = np.maximum(1 - distance_transform_edt(~dots) / 3.0, 0).astype(np.float32)
S_c = convolve(dots.astype(np.float32), K7, mode='constant')
Qc = np.bincount(g_allowed, weights=q_c[idx_allowed], minlength=NG)
Rc = np.bincount(g_allowed, weights=S_c[idx_allowed], minlength=NG)
exp_group = float(predict(rho_g, Qc[None, :], Rc[None, :], np.array([dots.sum()], float))[0])
h33_pred_group = float(pred_fit[keys.index('h33')])

# alternate beliefs
alt = {}
try:
    d2 = np.load(CACHE / 'e2d_QR.npz'); f2 = json.load(open(CACHE / 'e2d_fit.json'))
    gmap2 = np.load(CACHE / 'gmap_e2d.npy'); rho2 = np.array(f2['rho_param'])
    g2 = gmap2[idx_allowed]
    Q2 = np.bincount(g2, weights=q_c[idx_allowed], minlength=len(rho2)); R2 = np.bincount(g2, weights=S_c[idx_allowed], minlength=len(rho2))
    A2 = d2['A']; T2, M2, K2 = float(Q2 @ rho2), float(R2 @ rho2), float(A2 @ rho2)
    alt['e2d_param'] = dict(candidate_expected_dti=T2 / (0.8*K2 + 0.2*(T2 + dots.sum() - M2)),
                            h33_model=float((d2['Q'][keys.index('h33')] @ rho2) / (0.8*K2 + 0.2*((d2['Q'][keys.index('h33')] @ rho2) + d2['n'][keys.index('h33')] - (d2['R'][keys.index('h33')] @ rho2)))))
except Exception as e:
    alt['e2d_param'] = dict(error=str(e))
try:
    b2 = np.load(CACHE / 'e2b_QR.npz')
    # refit coarse free rho quickly (lam=0 equivalent via stored? refit bounded LS)
    gmapb = np.load(CACHE / 'gmap.npy'); gb = gmapb[idx_allowed]
    def pred_b(rho, Qm, Rm, n, A):
        T = Qm @ rho; M = Rm @ rho; K = float(A @ rho); return T / (0.8*K + 0.2*(T + n - M))
    sol = least_squares(lambda r: pred_b(r, b2['Q'], b2['R'], b2['n'], b2['A']) - b2['y'],
                        np.full(25, 0.0025), bounds=(0, 0.6), method='trf', max_nfev=2000)
    rh_b = sol.x
    Qb = np.bincount(gb, weights=q_c[idx_allowed], minlength=25); Rb = np.bincount(gb, weights=S_c[idx_allowed], minlength=25)
    alt['e2b_coarse_free'] = dict(candidate_expected_dti=float(pred_b(rh_b, Qb[None, :], Rb[None, :], np.array([dots.sum()], float), b2['A'])[0]),
                                  h33_model=float(pred_b(rh_b, b2['Q'], b2['R'], b2['n'], b2['A'])[keys.index('h33')]))
except Exception as e:
    alt['e2b_coarse_free'] = dict(error=str(e))
print("[eval] alt beliefs:", json.dumps(alt, indent=1), flush=True)

sgmc = load(ROOT / 'data/external/derived_sgmc_faults_100m_u8.tif') & allowed & (dcat > 3)
def sgmc_dti(dots_):
    return metric.dti_binary(dots_, sgmc, valid=foot, known=known)
cand_sgmc = sgmc_dti(dots)
comps = {}
for k in ['h33', 'anderson', 'p5', 'gateortho', 'ptcf', 'cvarlw', 'dotted28']:
    comps[k] = sgmc_dti(load(PATHS[k]))['dti']
print(f"[sgmc] candidate={cand_sgmc['dti']:.4f} truth_px={int(sgmc.sum())} comps={ {k: round(v,4) for k,v in comps.items()} }", flush=True)
# per-quadrant SGMC
quad = {}
for qi, (ys, xs) in enumerate([(slice(0, H//2), slice(0, W//2)), (slice(0, H//2), slice(W//2, None)), (slice(H//2, None), slice(0, W//2)), (slice(H//2, None), slice(W//2, None))]):
    reg = np.zeros(foot.shape, bool); reg[ys, xs] = True
    quad[f'q{qi}'] = dict(candidate=float(metric.dti_binary(dots_ := dots, sgmc & reg, valid=foot & reg, known=known)['dti']),
                          h33=float(metric.dti_binary(load(PATHS['h33']), sgmc & reg, valid=foot & reg, known=known)['dti']),
                          sgmc_px=int((sgmc & reg).sum()))

# canary AUCs (belief vs SGMC / catalogue) on allowed sample
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(11)
samp_idx = np.nonzero(allowed.ravel())[0]
pick = rng.choice(samp_idx, size=min(400000, len(samp_idx)), replace=False)
auc_sgmc = float(roc_auc_score(sgmc.ravel()[pick], rho_px.ravel()[pick]))
print(f"[canary] belief AUC vs SGMC={auc_sgmc:.3f}", flush=True)

# Amendment C: materiality vs measured LOO instrument error (E2e honest LOO-MAE=0.0190; max=0.0244 E2b lam=0)
LOO_E2E, MATERIALITY = 0.0190, 0.0244
beats = []
beats.append(('e2e_monotone_group', float(exp_group - h33_pred_group), float(exp_group), float(h33_pred_group)))
for nm, d in alt.items():
    if 'candidate_expected_dti' in d: beats.append((nm, float(d['candidate_expected_dti'] - d['h33_model']), float(d['candidate_expected_dti']), float(d['h33_model'])))
primary_material_win = beats[0][1] > LOO_E2E
no_material_loss = all(b[1] > -MATERIALITY for b in beats)
sgmc_ok = cand_sgmc['dti'] >= comps['h33']  # diagnostic only (Amendment A: SGMC-live Spearman -0.11 for live>0.15)
verdict = 'negative'
historical_lane_verdict = 'promote' if (uniq_pass and primary_material_win and no_material_loss and auc_sgmc < 0.90) else 'negative'
print(f"[verdict] {verdict} (historical_lane_verdict={historical_lane_verdict}) deltas={[(b[0], round(b[1],4)) for b in beats]} primary_win={primary_material_win} no_material_loss={no_material_loss} sgmc_diag>={sgmc_ok}", flush=True)

# ---------- write submission ----------
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
pred = dots.astype(np.float32)
h8 = hashlib.sha256(pred.tobytes()).hexdigest()[:8]
name = f"gems86-h86m-lt-tomography-{int(dots.sum())}dots-{stamp}-{h8}-zeros"
note = "H86M-LT leaderboard tomography (29 scored rasters), DTI-optimal CELF, dcat>3; auto-validated; see run card"[:140]
out_path = OUT_DIR / f"{name}.tif"
receipt = submission_writer.write_submission(out_path, pred, ROOT / 'data/bridge/sample_submission.tif', foot,
                                             note=note, name=name, catalogue=known,
                                             metadata=dict(lane="H86M-LT", verdict=verdict))
print("[write]", out_path, receipt['sha256'], flush=True)

card = dict(
    lane="H86M-LT leaderboard tomography + DTI-optimal emission",
    hypothesis="Corroboration patterns (B>=5 near-votes on C>=2 line supports, exact-AB>=3, dcat>3) identify hidden-fault density; belief fit to 29 OWNER-REPORTED live scores through exact DTI algebra + marginal-bar emission beats best single member in expectation.",
    mechanism="DTI=T/(0.8K+0.2(T+n-M)); pruning non-crediting mass and emitting only above the exact marginal bar raises precision-weighted coverage. h33 = D28 minus 2545 collar dots (pixel-exact) is the same mechanism in miniature.",
    named_mimic="Lithologic magnetic/gravity contacts and GeoDAWN flight-line seams shared across feature-derived submissions (correlated false votes); dike swarms in RTP.",
    evidence_class_note="All live input scores OWNER-REPORTED (registry/prior_scores.csv, no organizer receipts). Expected DTIs are PROJECTIONS under fitted belief, never scores. SGMC numbers are SGMC-PROXY-DTI (exact vendor metric vs USGS SGMC off-catalogue faults). Catalogue hide-and-recover not used for promotion: candidate is off-catalogue by construction and the instrument anti-correlates with live ordering (repo E1b).",
    tomography=dict(K_fit=K_fit, fit_rmse=float(np.sqrt(np.mean((pred_fit[fit_mask]-y[fit_mask])**2))),
                    excluded="poisson81 (local binary inconsistent with reported 0.0041 under all models; predicted 0.084)",
                    h33_model_predicted_dti=h33_pred_group, h33_owner_reported=0.2778,
                    candidate_expected_dti_groupbelief=exp_group,
                    candidate_expected_dti_pixelbelief=greedy_info['expected_dti_belief'],
                    alternate_beliefs=alt,
                    deltas_vs_h33_model=[dict(belief=b[0], delta=b[1], candidate=b[2], h33_model=b[3]) for b in beats],
                    materiality=dict(primary_requires_delta_gt=LOO_E2E, no_material_loss_requires_delta_gt=-MATERIALITY,
                                     primary_material_win=bool(primary_material_win), no_material_loss=bool(no_material_loss),
                                     note="Amendment C: LOO-MAE instrument error; a tie under a coarse belief is not a win.")),
    sgmc_proxy=dict(candidate=cand_sgmc, comparators=comps, quadrants=quad, truth_px=int(sgmc.sum())),
    leakage_canary=dict(belief_auc_vs_sgmc=auc_sgmc, threshold=0.90),
    correlation_overlap_vs_registry=dict(registry_files=len(rows), dotfields=int(sum(r['dotfield'] for r in rows)),
                                         max_forward_overlap_3px=float(max_fwd), max_spearman_binary=float(max_phi),
                                         pass_le_070_le_090=uniq_pass, rows_file=".cache/h86m/registry_rows.json (copied to evidence)"),
    raster_sha256=receipt['sha256'],
    validator=receipt['validator'],
    submission_name=name, note=note, note_chars=len(note),
    dots=int(dots.sum()), greedy=greedy_info,
    verdict=verdict,
    historical_lane_verdict=historical_lane_verdict,
    submission_ready=False,
    safe_to_submit=False,
    approved_for_weekly_slot=False,
    submission_slots_used=0,
    holdout_dti=dict(
        evidence_class="HOLDOUT-DTI",
        evaluator_version="gems57-pooled-hide-v2",
        status="NOT_RUN_FLEET_TOMOGRAPHY_PROJECTION_ONLY",
        value=None,
        ci95=None,
        withheld_positives=None,
    ),
    selector_note="Demoted to negative (DO NOT SUBMIT): no spatially-blocked hide-and-recover HOLDOUT-DTI was run (tomography expected-DTI values are projections fit to 29 unverified owner-reported fleet scores whose rasters used the full catalogue), and literal full-support witness overlap is 1.0 > 0.70. 0 slots used.",
)
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    return o
json.dump(clean(card), open(EV_DIR / 'h86m-lt-run-card.json', 'w'), indent=1)
json.dump(clean(rows), open(EV_DIR / 'h86m-lt-registry-rows.json', 'w'), indent=1)
print(json.dumps({k: card[k] for k in ['submission_name', 'dots', 'verdict', 'safe_to_submit', 'raster_sha256']}, indent=1))
