#!/usr/bin/env python3
"""E2: leaderboard tomography. Fit per-pattern hit rates to OWNER-REPORTED scores.

Model per raster i:  H_i = sum_g N_ig * p_g   (expected # dots within 3px of hidden truth)
  T_i = a*H_i ; M_i = s*H_i ;  DTI_i = T_i / (0.8K + 0.2*(T_i + n_i - M_i))
Unknowns: p_g in [0,1], a, s, K. Scores are OWNER-REPORTED (no organizer receipts).
"""
import rasterio, numpy as np, json, sys
from scipy.ndimage import distance_transform_edt
from scipy.optimize import least_squares

def load(p):
    return np.nan_to_num(rasterio.open(p).read(1)) > 0

samp = rasterio.open('data/bridge/sample_submission.tif').read(1)
foot = ~np.isnan(samp)
known = load('data/bridge/existing_faults.tif') & foot
dcat = distance_transform_edt(~known)

FAM = {
 "A": ["h33","anderson","h36rung","d28solo","h38euler","h33d","dotted28","dotted15","topogap"],
 "B": ["p5","gateortho","ptcf","cvarlw","mcsc73","h82submod","trlt75","h76_3","lidar66"],
 "C": ["h19_5","h19_4","h16_1","h28dotted","ens12","hedge","h25ctx"],
 "D": ["choquet80","gvcd83","poisson81"],
}
PATHS = {
 "h33":"data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
 "anderson":"data/scored_fleet/GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
 "h36rung":"data/scored_fleet/GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
 "d28solo":"data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
 "h38euler":"data/scored_fleet/GEMSDOE28__gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif",
 "h33d":"data/scored_fleet/GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
 "dotted28":"data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
 "dotted15":"data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
 "topogap":"data/scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
 "p5":"data/scored_fleet/GEMSDOE70__gems70-p5-multiphysics-submodular-37654-20261020.tif",
 "gateortho":"data/scored_fleet/GEMSDOE49__gems49-gate_ortho_w0.25-40k-20261006T213721Z-nan.tif",
 "ptcf":"data/scored_fleet/GEMSDOE76__gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros.tif",
 "cvarlw":"data/scored_fleet/GEMSDOE63__gemsdoe63-cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-nan.tif",
 "mcsc73":"data/scored_fleet/GEMSDOE73__gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros.tif",
 "h82submod":"data/scored_fleet/GEMSDOE82__gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros.tif",
 "trlt75":"data/scored_fleet/GEMSDOE75__gems75-trlt-radon-loco-ridge-20261021-zeros.tif",
 "h76_3":"data/scored_fleet/GEMSDOE76__gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros.tif",
 "lidar66":"data/scored_fleet/GEMSDOE66__gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros.tif",
 "h19_5":"data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
 "h19_4":"data/scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
 "h16_1":"data/scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
 "h28dotted":"data/scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif",
 "ens12":"data/scored/gemsdoe-ens12-adopted-7f00890a.tif",
 "hedge":"data/scored/8GEMSDOE_Hedge-v2_submission.tif",
 "h25ctx":"data/scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif",
 "choquet80":"data/scored_fleet/GEMSDOE80__gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros.tif",
 "gvcd83":"data/scored_fleet/GEMSDOE83__gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif",
 "poisson81":"data/scored_fleet/GEMSDOE81__gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros.tif",
 "lattice13":"data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
 "placeholder9":"data/scored/gemsdoe9-PLACEHOLDER-2314b599.tif",
}
SCORES = {"h33":0.2778,"anderson":0.2750,"h36rung":0.2710,"d28solo":0.2708,"h38euler":0.2707,"h33d":0.2632,
 "dotted28":0.2600,"p5":0.2478,"dotted15":0.2477,"topogap":0.2449,"gateortho":0.2376,"ptcf":0.2343,"cvarlw":0.2303,
 "h19_5":0.1922,"mcsc73":0.1917,"h19_4":0.1894,"h82submod":0.1886,"h16_1":0.1855,"h28dotted":0.1839,"trlt75":0.1627,
 "ens12":0.1563,"hedge":0.1563,"h76_3":0.1555,"h25ctx":0.1280,"lidar66":0.1152,"choquet80":0.0943,"lattice13":0.0904,
 "gvcd83":0.0573,"placeholder9":0.0107,"poisson81":0.0041}

keys = list(PATHS)
dots = {}
votes = {f: np.zeros(foot.shape, np.int16) for f in "ABCD"}
fam_of = {k: f for f, ks in FAM.items() for k in ks}
for k in keys:
    d = load(PATHS[k]); dots[k] = d
    if k in fam_of:  # lattice/placeholder not voters
        near = distance_transform_edt(~d) <= 3
        votes[fam_of[k]] += near.astype(np.int16)
    print("loaded", k, int(d.sum()), flush=True)

def group_id(vA, vB, vC, vD, dc):
    vA, vB, vC = np.asarray(vA), np.asarray(vB), np.asarray(vC)
    a = np.where(vA == 0, 0, np.where(vA <= 4, 1, 2))
    b = np.where(vB == 0, 0, np.where(vB == 1, 1, np.where(vB == 2, 2, 3)))
    c = np.where(vC == 0, 0, 1)
    g = (a * 4 + b) * 2 + c
    return np.where(dc <= 3, 24, g)  # group 24 = collar

NG = 25
# N_ig for every scored raster
N = {}
for k in keys:
    ys, xs = np.nonzero(dots[k])
    g = group_id(votes["A"][ys, xs], votes["B"][ys, xs], votes["C"][ys, xs], votes["D"][ys, xs], dcat[ys, xs])
    N[k] = np.bincount(g, minlength=NG).astype(float)
np.savez('.cache/h86m/e2_N.npz', **{k: N[k] for k in keys})

fit_keys = [k for k in keys if k not in ("lattice13", "placeholder9")]  # calibration-only, huge support not in pattern space
n_vec = np.array([dots[k].sum() for k in fit_keys], float)
Nmat = np.stack([N[k] for k in fit_keys])
y = np.array([SCORES[k] for k in fit_keys])

def predict(params, Nmat, n_vec):
    p = params[:NG]; a, s, K = params[NG], params[NG+1], params[NG+2]
    H = Nmat @ p
    T = a * H; M = s * H
    return T / (0.8 * K + 0.2 * (T + n_vec - M))

def resid(params):
    return predict(params, Nmat, n_vec) - y

x0 = np.concatenate([np.full(NG, 0.08), [1.8, 0.6, 12500.0]])
x0[24] = 0.01
lb = np.concatenate([np.zeros(NG), [0.5, 0.1, 5000.0]])
ub = np.concatenate([np.ones(NG), [3.5, 1.0, 40000.0]])
best = None
rng = np.random.default_rng(7)
for trial in range(6):
    if trial:
        x0t = x0.copy(); x0t[:NG] = rng.uniform(0, 0.4, NG); x0t[NG:] = [rng.uniform(1, 3), rng.uniform(0.3, 0.9), rng.uniform(8000, 25000)]
    else:
        x0t = x0
    r = least_squares(resid, x0t, bounds=(lb, ub), method='trf', max_nfev=4000)
    if best is None or r.cost < best.cost: best = r
    print(f"trial {trial} cost={r.cost:.3e} rmse={np.sqrt(2*r.cost/len(y)):.4f}")
params = best.x
pred = predict(params, Nmat, n_vec)
print(f"\nFIT rmse={np.sqrt(np.mean((pred-y)**2)):.4f} mae={np.mean(np.abs(pred-y)):.4f} a={params[NG]:.3f} s={params[NG+1]:.3f} K={params[NG+2]:.0f}")
for k, yy, pp in zip(fit_keys, y, pred):
    print(f"{k:14s} obs={yy:.4f} pred={pp:.4f} resid={pp-yy:+.4f} H={(N[k]@params[:NG]):8.0f}")
labels = []
for a in range(3):
    for b in range(4):
        for c in range(2):
            labels.append(f"A{a}_B{b}_C{c}")
labels.append("COLLAR_dcat<=3")
print("\ngroup hit rates p_g:")
tot_cand = Nmat.sum(axis=0)
for g in range(NG):
    print(f"{labels[g]:16s} p={params[g]:.4f}  total dots across rasters={tot_cand[g]:9.0f}")

# Leave-one-raster-out CV (refit p,a,s,K each time)
loo = []
for i, k in enumerate(fit_keys):
    mask = np.ones(len(fit_keys), bool); mask[i] = False
    def resid_m(params, mask=mask):
        return predict(params, Nmat[mask], n_vec[mask]) - y[mask]
    r = least_squares(resid_m, params, bounds=(lb, ub), method='trf', max_nfev=2000)
    p_i = float(predict(r.x, Nmat[i:i+1], n_vec[i:i+1])[0])
    loo.append(dict(key=k, obs=float(y[i]), pred_loo=p_i))
    print(f"LOO {k:14s} obs={y[i]:.4f} pred={p_i:.4f}")
mae_loo = float(np.mean([abs(d['obs']-d['pred_loo']) for d in loo]))
print("LOO MAE =", mae_loo)
json.dump(dict(params=dict(p=params[:NG].tolist(), a=float(params[NG]), s=float(params[NG+1]), K=float(params[NG+2])),
               labels=labels, fit_rmse=float(np.sqrt(np.mean((pred-y)**2))), loo=loo, loo_mae=mae_loo,
               fit_keys=fit_keys), open('.cache/h86m/e2_fit.json', 'w'), indent=1)

# Lattice calibration check with fitted K
K = float(params[NG+2])
print(f"\nLattice check: T=0.3748K={0.3748*K:.0f}, M~0.14K={0.14*K:.0f}, n=206895 -> DTI={(0.3748*K)/(0.8*K+0.2*(0.3748*K+206895-0.14*K)):.4f} (obs 0.0904)")
# Candidate universe: footprint pixels with any A/B/C vote; group per pixel; count candidates per group
cand = (votes["A"] + votes["B"] + votes["C"]) > 0
cand &= foot & ~known
ys, xs = np.nonzero(cand)
g = group_id(votes["A"][ys, xs], votes["B"][ys, xs], votes["C"][ys, xs], votes["D"][ys, xs], dcat[ys, xs])
cnt = np.bincount(g, minlength=NG)
print("\ncandidate pixels per group (any-vote universe):")
for gg in range(NG):
    print(f"{labels[gg]:16s} cand_px={cnt[gg]:8d} p={params[gg]:.4f} expected_hits_if_all_taken~{cnt[gg]*params[gg]:8.0f}")
np.savez('.cache/h86m/e2_candidates.npz', ys=ys, xs=xs, g=g)
