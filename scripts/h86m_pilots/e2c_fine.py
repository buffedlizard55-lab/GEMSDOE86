#!/usr/bin/env python3
"""E2c: fine-group belief tomography + parametric (log-linear in votes) belief. LOO selects."""
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

def abin(v):
    return np.where(v == 0, 0, np.where(v <= 2, 1, np.where(v <= 5, 2, np.where(v <= 8, 3, 4))))
def bbin(v):
    return np.clip(v, 0, 5)
def cbin(v):
    return np.clip(v, 0, 3)

A_b, B_b, C_b = abin(votes["A"]), bbin(votes["B"]), cbin(votes["C"])
gmap = np.where(dcat <= 3, 120, (A_b * 6 + B_b) * 4 + C_b).astype(np.int16)
np.save('.cache/h86m/gmap_fine.npy', gmap)
NG = 121
idx = np.nonzero(allowed)
g_allowed = gmap[idx]
A_g = np.bincount(g_allowed, minlength=NG).astype(float)
# group vote-level features
gA = np.array([ (g // 24) if g < 120 else 0 for g in range(NG)], float) / 4.0
gB = np.array([ ((g // 4) % 6) if g < 120 else 0 for g in range(NG)], float) / 5.0
gC = np.array([ (g % 4) if g < 120 else 0 for g in range(NG)], float) / 3.0
gD_ = np.array([1.0 if g == 120 else 0.0 for g in range(NG)])

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
    print("QR", k, flush=True)
n_vec = np.array(n_vec, float); y = np.array([SCORES[k] for k in keys])
np.savez('.cache/h86m/e2c_QR.npz', Q=Q, R=R, n=n_vec, y=y, A=A_g, keys=np.array(keys), gA=gA, gB=gB, gC=gC)

def predict(rho, Q, R, n):
    T = Q @ rho; M = R @ rho; K = float(A_g @ rho)
    return T / (0.8 * K + 0.2 * (T + n - M))

def rho_param(theta):
    # theta: log_base, wA, wB, wC, wAB, wAC, wBC, collar_delta
    eta = theta[0] + theta[1]*gA + theta[2]*gB + theta[3]*gC + theta[4]*gA*gB + theta[5]*gA*gC + theta[6]*gB*gC + theta[7]*gD_
    return np.clip(np.exp(eta), 0, 0.6)

def fit_param(mask, theta0=None):
    if theta0 is None: theta0 = np.array([np.log(0.0003), 2.0, 2.0, 1.0, 0, 0, 0, -1.0])
    def resid(th): return predict(rho_param(th), Q[mask], R[mask], n_vec[mask]) - y[mask]
    return least_squares(resid, theta0, method='trf', max_nfev=2000).x

def fit_free(mask, smooth=0.0, rho0=None):
    if rho0 is None: rho0 = np.full(NG, 0.0025)
    def resid(rho):
        r = predict(rho, Q[mask], R[mask], n_vec[mask]) - y[mask]
        if smooth > 0:
            d = []
            rr = rho[:120].reshape(5, 6, 4)
            d.append((rr[1:] - rr[:-1]).ravel()); d.append((rr[:, 1:] - rr[:, :-1]).ravel()); d.append((rr[:, :, 1:] - rr[:, :, :-1]).ravel())
            r = np.concatenate([r, np.sqrt(smooth) * np.concatenate(d) * 10.0])
        return r
    return least_squares(resid, rho0, bounds=(0, 0.6), method='trf', max_nfev=3000).x

def loo(fitter, getter):
    errs = []
    for i in range(len(keys)):
        m = np.ones(len(keys), bool); m[i] = False
        sol = fitter(m)
        rho = getter(sol)
        errs.append(abs(float(predict(rho, Q[i:i+1], R[i:i+1], n_vec[i:i+1])[0]) - y[i]))
    return float(np.mean(errs)), float(np.max(errs))

results = {}
th = fit_param(np.ones(len(keys), bool))
rho_p = rho_param(th)
pred = predict(rho_p, Q, R, n_vec)
results['param'] = dict(theta=th.tolist(), rmse=float(np.sqrt(np.mean((pred-y)**2))), K=float(A_g@rho_p))
print(f"PARAM rmse={results['param']['rmse']:.4f} K={results['param']['K']:.0f} theta={np.round(th,3)}")
for k, yy, pp in zip(keys, y, pred): print(f"  {k:14s} obs={yy:.4f} pred={pp:.4f} resid={pp-yy:+.4f}")
mae, mx = loo(lambda m: fit_param(m, th), rho_param)
results['param']['loo_mae'] = mae; results['param']['loo_max'] = mx
print(f"PARAM LOO-MAE={mae:.4f} max={mx:.4f}")

for smooth in [0.0, 0.05, 0.2]:
    rho_f = fit_free(np.ones(len(keys), bool), smooth, rho_p)
    pred_f = predict(rho_f, Q, R, n_vec)
    rmse = float(np.sqrt(np.mean((pred_f-y)**2)))
    mae, mx = loo(lambda m, s=smooth: fit_free(m, s, rho_f), lambda r: r)
    results[f'free_s{smooth}'] = dict(rmse=rmse, K=float(A_g@rho_f), loo_mae=mae, loo_max=mx, rho=rho_f.tolist())
    print(f"FREE smooth={smooth} rmse={rmse:.4f} K={float(A_g@rho_f):.0f} LOO-MAE={mae:.4f} max={mx:.4f}")

json.dump(results, open('.cache/h86m/e2c_results.json', 'w'), indent=1)
# show param rho table at representative vote levels
print("\nparam rho at (A_bin,B_bin,C_bin):")
rr = rho_p[:120].reshape(5, 6, 4)
for a in range(5):
    for b in range(6):
        print(f"A{a} B{b}: " + " ".join(f"{rr[a,b,c]:.4f}" for c in range(4)) + f"   A_px={A_g[:120].reshape(5,6,4)[a,b].sum():.0f}")
print("COLLAR rho=", rho_p[120])
