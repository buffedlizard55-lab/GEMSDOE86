#!/usr/bin/env python3
"""E2d: belief tomography with A/B/C/D near-votes; poisson81 excluded from fit (suspect pairing)."""
import rasterio, numpy as np, json
from scipy.ndimage import distance_transform_edt, convolve
from scipy.optimize import least_squares

def load(p):
    return np.nan_to_num(rasterio.open(p).read(1)) > 0

samp = rasterio.open('data/bridge/sample_submission.tif').read(1)
foot = ~np.isnan(samp)
known = load('data/bridge/existing_faults.tif') & foot
allowed = foot & ~known
dcat = distance_transform_edt(~known)
exec(open('.cache/h86m/e2_tomography.py').read().split("keys = list(PATHS)")[0].split("dcat = distance_transform_edt(~known)")[1])
keys = list(PATHS)
votes = {f: np.load(f'.cache/h86m/votes_{f}.npy') for f in "ABCD"}

def abin(v): return np.where(v == 0, 0, np.where(v <= 2, 1, np.where(v <= 5, 2, np.where(v <= 8, 3, 4))))
def bbin(v): return np.clip(v, 0, 5)
def cbin(v): return np.clip(v, 0, 3)
def dbin(v): return np.clip(v, 0, 2)

A_b, B_b, C_b, D_b = abin(votes["A"]), bbin(votes["B"]), cbin(votes["C"]), dbin(votes["D"])
gmap = np.where(dcat <= 3, 360, ((A_b * 6 + B_b) * 4 + C_b) * 3 + D_b).astype(np.int16)
np.save('.cache/h86m/gmap_e2d.npy', gmap)
NG = 361
idx = np.nonzero(allowed)
g_allowed = gmap[idx]
A_g = np.bincount(g_allowed, minlength=NG).astype(float)
gg = np.arange(NG)
core = gg < 360
gA = np.where(core, gg // 72, 0) / 4.0
gB = np.where(core, (gg // 12) % 6, 0) / 5.0
gC = np.where(core, (gg // 3) % 4, 0) / 3.0
gD = np.where(core, gg % 3, 0) / 2.0
gCOL = (gg == 360).astype(float)

K7 = np.zeros((7, 7), np.float32)
for i in range(-3, 4):
    for j in range(-3, 4):
        K7[i+3, j+3] = max(1 - np.hypot(i, j) / 3.0, 0)
Q = np.zeros((len(keys), NG)); R = np.zeros((len(keys), NG)); n_vec = []
for ii, k in enumerate(keys):
    d = load(PATHS[k]); n_vec.append(int(d.sum()))
    q = np.maximum(1 - distance_transform_edt(~d) / 3.0, 0).astype(np.float32)
    S = convolve(d.astype(np.float32), K7, mode='constant')
    Q[ii] = np.bincount(g_allowed, weights=q[idx], minlength=NG)
    R[ii] = np.bincount(g_allowed, weights=S[idx], minlength=NG)
n_vec = np.array(n_vec, float); y = np.array([SCORES[k] for k in keys])
np.savez('.cache/h86m/e2d_QR.npz', Q=Q, R=R, n=n_vec, y=y, A=A_g, keys=np.array(keys))

def predict(rho, Qm, Rm, n):
    T = Qm @ rho; M = Rm @ rho; K = float(A_g @ rho)
    return T / (0.8 * K + 0.2 * (T + n - M))

FEATS = np.stack([np.ones(NG), gA, gB, gC, gD, gA*gB, gA*gC, gB*gC, gC*gC, gB*gB, gCOL], axis=1)
def rho_param(theta):
    return np.clip(np.exp(FEATS @ theta), 0, 0.6)

fit_mask = np.array([k != "poisson81" for k in keys])
def fit_param(mask, theta0=None):
    if theta0 is None: theta0 = np.array([np.log(0.0003), 2, 2, 1, 0, 0, 0, 0, 0, 0, -1.0])
    def resid(th): return predict(rho_param(th), Q[mask], R[mask], n_vec[mask]) - y[mask]
    best = None
    rng = np.random.default_rng(3)
    for t in range(4):
        th0 = theta0 if t == 0 else theta0 + rng.normal(0, 1.5, len(theta0))
        sol = least_squares(resid, th0, method='trf', max_nfev=3000)
        if best is None or sol.cost < best.cost: best = sol
    return best.x

th = fit_param(fit_mask)
rho_p = rho_param(th)
pred = predict(rho_p, Q, R, n_vec)
rmse = float(np.sqrt(np.mean((pred[fit_mask] - y[fit_mask]) ** 2)))
print(f"PARAM(e2d) fit RMSE(excl poisson)={rmse:.4f} K={float(A_g@rho_p):.0f} theta={np.round(th,3)}")
for k, yy, pp in zip(keys, y, pred): print(f"  {k:14s} obs={yy:.4f} pred={pp:.4f} resid={pp-yy:+.4f}")

# LOO over fit rasters
errs = []
for i, k in enumerate(keys):
    if not fit_mask[i]: continue
    m = fit_mask.copy(); m[i] = False
    th_i = fit_param(m, th)
    p_i = float(predict(rho_param(th_i), Q[i:i+1], R[i:i+1], n_vec[i:i+1])[0])
    errs.append(abs(p_i - y[i])); print(f"  LOO {k:14s} obs={y[i]:.4f} pred={p_i:.4f}")
print(f"LOO-MAE={np.mean(errs):.4f} max={np.max(errs):.4f}")

# free-rho with smoothing initialized at param (smoothing only across A,B,C,D neighbor bins via FEATS-distance-free simple: penalize rho - rho_param scaled)
def fit_free(mask, lam, rho0):
    def resid(rho):
        r = predict(rho, Q[mask], R[mask], n_vec[mask]) - y[mask]
        reg = np.sqrt(lam) * (rho - rho0) / 0.01 * 0.01  # shrink to param surface
        return np.concatenate([r, reg])
    return least_squares(resid, rho0, bounds=(0, 0.6), method='trf', max_nfev=1500).x

out = dict(theta=th.tolist(), rmse=rmse, K=float(A_g@rho_p), loo_mae=float(np.mean(errs)), loo_max=float(np.max(errs)), rho_param=rho_p.tolist())
for lam in [0.001, 0.01]:
    rho_f = fit_free(fit_mask, lam, rho_p)
    pred_f = predict(rho_f, Q, R, n_vec)
    print(f"FREE shrink lam={lam}: fit RMSE={float(np.sqrt(np.mean((pred_f[fit_mask]-y[fit_mask])**2))):.4f} K={float(A_g@rho_f):.0f}")
    out[f'rho_free_{lam}'] = rho_f.tolist()
json.dump(out, open('.cache/h86m/e2d_fit.json', 'w'))
print("\nrho_param by (A,B,C) at D=0 / D=2:")
rr = rho_p[:360].reshape(5, 6, 4, 3)
for a in range(5):
    for b in range(6):
        print(f"A{a} B{b} D0: " + " ".join(f"{rr[a,b,c,0]:.4f}" for c in range(4)) + " | D2: " + " ".join(f"{rr[a,b,c,2]:.4f}" for c in range(4)))
print("COLLAR", rho_p[360])
