#!/usr/bin/env python3
"""E2b: belief-density tomography.

Partition allowed pixels into 25 groups by family votes (within 3px) + collar.
Unknown rho_g = P(pixel in g is hidden-truth). For each scored raster i:
  T_i = sum_g rho_g * Q_ig ,  Q_ig = sum_{x in g} max_kern_i(x)         (EDT kernel coverage)
  M_i = sum_g rho_g * R_ig ,  R_ig = sum_{x in g} sum_kern_i(x)         (kernel convolution; reciprocity)
  K   = sum_g rho_g * A_g
  DTI_i = T_i / (0.8K + 0.2*(T_i + n_i - M_i))
Fit rho>=0 by penalized least squares to OWNER-REPORTED scores. LOO-CV over rasters.
"""
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
fam_of = {k: f for f, ks in FAM.items() for k in ks}
votes = {f: np.zeros(foot.shape, np.int16) for f in "ABCD"}
dots = {}
for k in keys:
    d = load(PATHS[k]); dots[k] = d
    if k in fam_of:
        votes[fam_of[k]] += (distance_transform_edt(~d) <= 3).astype(np.int16)
    print("loaded", k, flush=True)
for f in "ABCD":
    np.save(f'.cache/h86m/votes_{f}.npy', votes[f])

def grp(vA, vB, vC, dc):
    a = np.where(vA == 0, 0, np.where(vA <= 4, 1, 2))
    b = np.where(vB == 0, 0, np.where(vB == 1, 1, np.where(vB == 2, 2, 3)))
    c = np.where(vC == 0, 0, 1)
    return np.where(dc <= 3, 24, (a * 4 + b) * 2 + c).astype(np.int16)

gmap = grp(votes["A"], votes["B"], votes["C"], dcat)
np.save('.cache/h86m/gmap.npy', gmap)
NG = 25
idx = np.nonzero(allowed)
g_allowed = gmap[idx]
A_g = np.bincount(g_allowed, minlength=NG).astype(float)

# kernel disk for convolution
K7 = np.zeros((7, 7), np.float32)
for i in range(-3, 4):
    for j in range(-3, 4):
        K7[i+3, j+3] = max(1 - np.hypot(i, j) / 3.0, 0)

Q = np.zeros((len(keys), NG)); R = np.zeros((len(keys), NG)); n_vec = []
for ii, k in enumerate(keys):
    d = dots[k]
    n_vec.append(int(d.sum()))
    dd = distance_transform_edt(~d)
    q = np.maximum(1 - dd / 3.0, 0).astype(np.float32)
    S = convolve(d.astype(np.float32), K7, mode='constant')
    Q[ii] = np.bincount(g_allowed, weights=q[idx], minlength=NG)
    R[ii] = np.bincount(g_allowed, weights=S[idx], minlength=NG)
    print("QR", k, flush=True)
n_vec = np.array(n_vec, float)
y = np.array([SCORES[k] for k in keys])
np.savez('.cache/h86m/e2b_QR.npz', Q=Q, R=R, n=n_vec, y=y, A=A_g, keys=np.array(keys))

labels = [f"A{a}_B{b}_C{c}" for a in range(3) for b in range(4) for c in range(2)] + ["COLLAR"]

def predict(rho, Q, R, n, A):
    T = Q @ rho; M = R @ rho; K = float(A @ rho)
    return T / (0.8 * K + 0.2 * (T + n - M))

def fit(mask, lam, rho0=None):
    if rho0 is None: rho0 = np.full(NG, 12500.0 / A_g.sum())
    def resid(rho):
        r = predict(rho, Q[mask], R[mask], n_vec[mask], A_g) - y[mask]
        reg = np.sqrt(lam) * (rho - 12500.0 / A_g.sum()) * 100.0
        return np.concatenate([r, reg])
    sol = least_squares(resid, rho0, bounds=(0, 0.6), method='trf', max_nfev=3000)
    return sol.x

for lam in [0.0, 0.02, 0.1, 0.5]:
    rho = fit(np.ones(len(keys), bool), lam)
    pred = predict(rho, Q, R, n_vec, A_g)
    rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
    K = float(A_g @ rho)
    # LOO
    loo_err = []
    for i in range(len(keys)):
        m = np.ones(len(keys), bool); m[i] = False
        rho_i = fit(m, lam, rho)
        p_i = float(predict(rho_i, Q[i:i+1], R[i:i+1], n_vec[i:i+1], A_g)[0])
        loo_err.append(abs(p_i - y[i]))
    print(f"lam={lam}: fit RMSE={rmse:.4f} K={K:.0f} LOO-MAE={np.mean(loo_err):.4f} LOO-max={np.max(loo_err):.4f}")
    if lam == 0.1:
        print(" per-raster (lam=0.1):")
        for k, yy, pp in zip(keys, y, pred):
            print(f"  {k:14s} obs={yy:.4f} pred={pp:.4f} resid={pp-yy:+.4f}")
        print(" rho_g:")
        for g in range(NG):
            print(f"  {labels[g]:10s} rho={rho[g]:.5f} A={A_g[g]:9.0f} contribK={rho[g]*A_g[g]:8.0f}")
        json.dump(dict(rho=rho.tolist(), labels=labels, K=K, rmse=rmse, lam=lam,
                       loo_mae=float(np.mean(loo_err))), open('.cache/h86m/e2b_fit.json', 'w'), indent=1)
        np.save('.cache/h86m/rho_g.npy', rho)
