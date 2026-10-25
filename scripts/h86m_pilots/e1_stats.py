#!/usr/bin/env python3
"""E1 exploratory: per-raster geometry vs OWNER-REPORTED score. No fitting to truth (unknown)."""
import rasterio, numpy as np, json
from scipy.ndimage import distance_transform_edt

def load(p):
    a = rasterio.open(p).read(1)
    return np.nan_to_num(a) > 0

samp = rasterio.open('data/bridge/sample_submission.tif').read(1)
foot = ~np.isnan(samp)
known = load('data/bridge/existing_faults.tif') & foot
# existing_faults: 1=fault,0=bg,-1=outside; load()>0 gives faults only. ok.
allowed = foot & ~known
dcat = distance_transform_edt(~known)

LABELLED = [
 # (key, path, owner_reported_score)
 ("h33", "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778),
 ("anderson", "data/scored_fleet/GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750),
 ("h36rung", "data/scored_fleet/GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710),
 ("d28solo", "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", 0.2708),
 ("h38euler", "data/scored_fleet/GEMSDOE28__gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif", 0.2707),
 ("h33d", "data/scored_fleet/GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", 0.2632),
 ("dotted28", "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600),
 ("p5", "data/scored_fleet/GEMSDOE70__gems70-p5-multiphysics-submodular-37654-20261020.tif", 0.2478),
 ("dotted15", "data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477),
 ("topogap", "data/scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
 ("gateortho", "data/scored_fleet/GEMSDOE49__gems49-gate_ortho_w0.25-40k-20261006T213721Z-nan.tif", 0.2376),
 ("ptcf", "data/scored_fleet/GEMSDOE76__gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros.tif", 0.2343),
 ("cvarlw", "data/scored_fleet/GEMSDOE63__gemsdoe63-cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-nan.tif", 0.2303),
 ("h19_5", "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922),
 ("mcsc73", "data/scored_fleet/GEMSDOE73__gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros.tif", 0.1917),
 ("h19_4", "data/scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894),
 ("h82submod", "data/scored_fleet/GEMSDOE82__gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros.tif", 0.1886),
 ("h16_1", "data/scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855),
 ("h28dotted", "data/scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839),
 ("trlt75", "data/scored_fleet/GEMSDOE75__gems75-trlt-radon-loco-ridge-20261021-zeros.tif", 0.1627),
 ("ens12", "data/scored/gemsdoe-ens12-adopted-7f00890a.tif", 0.1563),
 ("hedge", "data/scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563),
 ("h76_3", "data/scored_fleet/GEMSDOE76__gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros.tif", 0.1555),
 ("h25ctx", "data/scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280),
 ("lidar66", "data/scored_fleet/GEMSDOE66__gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros.tif", 0.1152),
 ("choquet80", "data/scored_fleet/GEMSDOE80__gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros.tif", 0.0943),
 ("lattice13", "data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904),
 ("gvcd83", "data/scored_fleet/GEMSDOE83__gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif", 0.0573),
 ("placeholder9", "data/scored/gemsdoe9-PLACEHOLDER-2314b599.tif", 0.0107),
 ("poisson81", "data/scored_fleet/GEMSDOE81__gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros.tif", 0.0041),
]
rows = []
H, W = foot.shape
for key, path, score in LABELLED:
    dots = load(path)
    n = int(dots.sum())
    dd = distance_transform_edt(~dots)
    kern = np.maximum(1 - dd / 3.0, 0)
    c_mean = float(kern[allowed].mean())          # E[T]/K if truth uniform on allowed
    cov3 = float((dd[allowed] <= 3).mean())
    d = dcat[dots]
    # quadrant dot density (footprint-normalized)
    quads = {}
    for qi, (ys, xs) in enumerate([((slice(0, H//2), slice(0, W//2))), ((slice(0, H//2), slice(W//2, None))), ((slice(H//2, None), slice(0, W//2))), ((slice(H//2, None), slice(W//2, None)))]):
        quads[f"q{qi}"] = float(dots[ys].sum() / max(foot[ys].sum(), 1))
    row = dict(key=key, score=score, n=n, c_mean_kernel=c_mean, cov_le3=cov3,
               frac_on_known=float((d == 0).mean()), frac_d_le2=float((d <= 2).mean()),
               frac_d_2_3=float(((d > 2) & (d <= 3)).mean()), frac_d_gt10=float((d > 10).mean()),
               median_dcat=float(np.median(d)), outside_footprint=int((dots & ~foot).sum()), **quads)
    rows.append(row)
    print(f"{key:14s} score={score:.4f} n={n:7d} c={c_mean:.4f} cov3={cov3:.3f} d<=2={row['frac_d_le2']:.3f} med_d={row['median_dcat']:.1f} qdens={[round(quads[f'q{i}'],4) for i in range(4)]}")
json.dump(rows, open('.cache/h86m/e1_rows.json', 'w'), indent=1)

# Implied K under uniform-truth assumption per raster: DTI = cK/(0.8K+0.2(cK + n - M)), M approx n*c' where c' = mean kernel at random pixel wrt truth...
# Use symmetric approx M = n * c_mean_truth where c_mean_truth = dilated-truth kernel mass / footprint - unknown; instead solve bounds:
# M in [0, T_max]... simpler: use M ≈ n * (K * S / A) where S=sum of kernel disk ≈ compute: sum over offsets k.
S = float(sum(max(1 - np.hypot(i, j) / 3, 0) for i in range(-3, 4) for j in range(-3, 4)))
A = float(allowed.sum())
print("kernel disk sum S =", S, "allowed px A =", A)
for r in rows:
    c, n, D = r['c_mean_kernel'], r['n'], r['score']
    # unknowns K; T=cK; M=n*K*S/A (expected if truth uniform independent); solve D = cK/(0.8K+0.2(cK+n-nKS/A))
    # => D*(0.8K+0.2cK+0.2n-0.2nKS/A)=cK => 0.2Dn = K*(c - D*(0.8+0.2c-0.2nS/A)) => K=0.2Dn/(...)
    den = c - D * (0.8 + 0.2 * c - 0.2 * n * S / A)
    K = 0.2 * D * n / den if den > 0 else float('nan')
    print(f"{r['key']:14s} implied K (uniform-truth model) = {K:10.0f}")
