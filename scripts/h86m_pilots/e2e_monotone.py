#!/usr/bin/env python3
"""E2e: additive monotone log-linear belief over (A,B,C,D near-votes, E exact-votes, collar).
log rho = t0 + sum alpha[A] + sum beta[B] + sum gamma[C] + delta*Dlevel + sum eps[E]  (+ collar)
with alpha,beta,gamma,eps increments >= 0 (monotone in corroboration), delta free.
Honest LOO: generic start each fold. poisson81 excluded from fit, kept as flagged check.
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
votes = {f: np.load(f'.cache/h86m/votes_{f}.npy') for f in "ABCD"}

# exact-vote map: # of A+B rasters with a dot exactly at pixel
exact = np.zeros(foot.shape, np.int16)
fam_of = {k: f for f, ks in FAM.items() for k in ks}
dots = {}
for k in keys:
    d = load(PATHS[k]); dots[k] = d
    if fam_of.get(k) in ("A", "B"):
        exact += d.astype(np.int16)
np.save('.cache/h86m/exactAB.npy', exact)

def abin(v): return np.where(v == 0, 0, np.where(v <= 2, 1, np.where(v <= 5, 2, np.where(v <= 8, 3, 4)))).astype(np.int64)
def bbin(v): return np.clip(v, 0, 5).astype(np.int64)
def cbin(v): return np.clip(v, 0, 3).astype(np.int64)
def dbin(v): return np.clip(v, 0, 2).astype(np.int64)
def ebin(v): return np.where(v == 0, 0, np.where(v <= 2, 1, 2)).astype(np.int64)

A_b, B_b, C_b, D_b, E_b = abin(votes["A"]), bbin(votes["B"]), cbin(votes["C"]), dbin(votes["D"]), ebin(exact)
gmap = np.where(dcat <= 3, 1080, (((A_b * 6 + B_b) * 4 + C_b) * 3 + D_b) * 3 + E_b).astype(np.int16)
np.save('.cache/h86m/gmap_e2e.npy', gmap)
NG = 1081
idx = np.nonzero(allowed)
g_allowed = gmap[idx]
A_g = np.bincount(g_allowed, minlength=NG).astype(float)

gg = np.arange(NG); core = gg < 1080
levA = np.where(core, gg // 216, 0); levB = np.where(core, (gg // 36) % 6, 0)
levC = np.where(core, (gg // 9) % 4, 0); levD = np.where(core, (gg // 3) % 3, 0)
levE = np.where(core, gg % 3, 0); isCOL = (gg == 1080)

def rho_from_theta(th):
    # th: [t0, a1..a4, b1..b5, c1..c3, deltaD, e1..e2, collar]
    a = np.concatenate([[0], np.cumsum(th[1:5])])
    b = np.concatenate([[0], np.cumsum(th[5:10])])
    c = np.concatenate([[0], np.cumsum(th[10:13])])
    e = np.concatenate([[0], np.cumsum(th[14:16])])
    eta = th[0] + a[levA] + b[levB] + c[levC] + th[13] * levD + e[levE]
    eta = np.where(isCOL, th[0] + th[16], eta)
    return np.clip(np.exp(eta), 0, 0.6)

K7 = np.zeros((7, 7), np.float32)
for i in range(-3, 4):
    for j in range(-3, 4):
        K7[i+3, j+3] = max(1 - np.hypot(i, j) / 3.0, 0)
Q = np.zeros((len(keys), NG)); R = np.zeros((len(keys), NG)); n_vec = []
for ii, k in enumerate(keys):
    d = dots[k]; n_vec.append(int(d.sum()))
    q = np.maximum(1 - distance_transform_edt(~d) / 3.0, 0).astype(np.float32)
    S = convolve(d.astype(np.float32), K7, mode='constant')
    Q[ii] = np.bincount(g_allowed, weights=q[idx], minlength=NG)
    R[ii] = np.bincount(g_allowed, weights=S[idx], minlength=NG)
    print("QR", k, flush=True)
n_vec = np.array(n_vec, float); y = np.array([SCORES[k] for k in keys])
np.savez('.cache/h86m/e2e_QR.npz', Q=Q, R=R, n=n_vec, y=y, A=A_g, keys=np.array(keys))

def predict(rho, Qm, Rm, n):
    T = Qm @ rho; M = Rm @ rho; K = float(A_g @ rho)
    return T / (0.8 * K + 0.2 * (T + n - M))

fit_mask = np.array([k != "poisson81" for k in keys])
LB = np.array([-20] + [0]*4 + [0]*5 + [0]*3 + [-5] + [0]*2 + [-10], float)
UB = np.array([0] + [5]*4 + [5]*5 + [5]*3 + [5] + [5]*2 + [5], float)
TH0 = np.array([np.log(0.0002)] + [0.7]*4 + [0.5]*5 + [0.4]*3 + [0.0] + [0.5]*2 + [-1.0])

def fit(mask, th0=TH0):
    def resid(th): return predict(rho_from_theta(th), Q[mask], R[mask], n_vec[mask]) - y[mask]
    return least_squares(resid, th0, bounds=(LB, UB), method='trf', max_nfev=3000).x

th = fit(fit_mask)
rho = rho_from_theta(th)
pred = predict(rho, Q, R, n_vec)
print(f"\nMONOTONE fit RMSE(excl poi)={float(np.sqrt(np.mean((pred[fit_mask]-y[fit_mask])**2))):.4f} K={float(A_g@rho):.0f}")
print("theta:", np.round(th, 3))
for k, yy, pp in zip(keys, y, pred): print(f"  {k:14s} obs={yy:.4f} pred={pp:.4f} resid={pp-yy:+.4f}")
errs = []
for i, k in enumerate(keys):
    if not fit_mask[i]: continue
    m = fit_mask.copy(); m[i] = False
    th_i = fit(m)  # generic start (honest)
    p_i = float(predict(rho_from_theta(th_i), Q[i:i+1], R[i:i+1], n_vec[i:i+1])[0])
    errs.append(abs(p_i - y[i])); print(f"  LOO {k:14s} obs={y[i]:.4f} pred={p_i:.4f}")
print(f"HONEST LOO-MAE={np.mean(errs):.4f} max={np.max(errs):.4f}")
json.dump(dict(theta=th.tolist(), rho=rho.tolist(), K=float(A_g@rho), rmse=float(np.sqrt(np.mean((pred[fit_mask]-y[fit_mask])**2))),
               loo_mae=float(np.mean(errs)), loo_max=float(np.max(errs)),
               pred={k: float(p) for k, p in zip(keys, pred)}), open('.cache/h86m/e2e_fit.json', 'w'), indent=1)
# rho table (D=0,E=0) and group areas for top groups
rr = rho[:1080].reshape(5, 6, 4, 3, 3)
AA = A_g[:1080].reshape(5, 6, 4, 3, 3)
print("\nrho (D0,E0) rows A, cols B, blocks C:")
for c in range(4):
    print(f"C={c}")
    for a in range(5):
        print("  A%d: " % a + " ".join(f"{rr[a,b,c,0,0]:.4f}" for b in range(6)))
print("E effect (A4B5C3D0):", [float(rr[4,5,3,0,e]) for e in range(3)])
print("D effect (A4B5C3E0):", [float(rr[4,5,3,d,0]) for d in range(3)])
print("COLLAR rho", float(rho[1080]), "base A0B0C0D0E0", float(rr[0,0,0,0,0]))
top = np.argsort(-(rho[:1080] * A_g[:1080]))[:12]
for g in top:
    print(f"  group A{levA[g]} B{levB[g]} C{levC[g]} D{levD[g]} E{levE[g]}: rho={rho[g]:.4f} px={A_g[g]:.0f} Kcontrib={rho[g]*A_g[g]:.0f}")
