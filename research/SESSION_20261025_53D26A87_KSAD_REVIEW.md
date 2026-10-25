# Session `53d26a87` Review — `GEMSDOE32` (`0.2778`) Forensics, `H86I` Geological Hypotheses, Strict-LOQO `H86I-KSAD` Validation & Fleet Overlap Saturation (`2026-10-25`)

**Branch:** `arena/53d26a87-gemsdoe86`  
**Decision:** **`DO NOT SUBMIT`** (`verdict = "negative"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `0` of `3` weekly DrivenData submission slots used).  
**Primary New Evidence Artifacts:**
- Frozen Hypothesis Queue (`4` untried hypotheses): `registry/h86i_ksad_hypotheses.json`
- Frozen Preregistration: `research/H86I_KSAD_PREREGISTRATION.json`, `research/H86I_KSAD_PREREGISTRATION.md`
- Complete Run Card: `docs/evidence/h86i-ksad-run-card.json`
- Bound `v2` Pre-Placement Surface Audit: `docs/evidence/h86i-ksad-registry-surface.json` (`0` Spearman $\rho > 0.90$ firings across `688 / 690` compatible rasters; `worst_rho = 0.6344`)
- Bound `v2` Pre-Serialization Final-Dot Audit: `docs/evidence/h86i-ksad-registry-final-dots.json` (`0` Spearman $\rho > 0.90$ firings; halted fail-closed pre-TIFF on `3` informative discrete `<= 40k`-dot overlaps led by `71.31%` vs `GEMSDOE80` `adpt-kkt-lagrangian-36500d` at `chance_c = 14.65%`)

---

## 1. How `GEMSDOE32` Achieved `0.2778` (`OWNER-REPORTED`) and When We Can Beat It

### 1.1 Pixel-Exact Lineage of `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`
Direct byte-and-pixel inspection of SHA-pinned fleet rasters in `data/scored_fleet/` establishes an exact deterministic identity (`0` differing pixels across all `12,279,160` cells):
1. **Parent (`GEMSDOE28`, `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc`, SHA-256 `ab023001...`):** A positive-unlabeled multi-scale geophysical/geomorphic ensemble (`HistGradientBoostingClassifier` + `ExplainableBoostingClassifier` + isotonic calibration) thinned by greedy Poisson-disc suppression at `2.8 px` (`280 m`) spacing outside `d_cat <= 1.0 px`, emitting **`40,199` binary unit dots** (`0.2708` `OWNER-REPORTED`, not `ORGANIZER-CONFIRMED`).
2. **Collar-Pruning Step (`GEMSDOE32`, `h33-h33-2-b2`, SHA-256 `c55bafc4...`):** Deletes every parent dot lying at Euclidean distance $1.0 < d_{\text{cat}}(x) \le 2.0\text{ px}$ (`100–200 m`) from mapped `existing_faults.tif` (`60,988` pixels) and adds **`0` new pixels**, leaving **`37,654` unit dots** (`40,199 - 2,545 = 37,654`; `0.2778` `OWNER-REPORTED`, `+0.0070` over parent).

### 1.2 Exact DTI Algebraic Mechanism & Failure Counterexample
Under the official Distance-Weighted Tversky Index ($\alpha = 0.2$, $\beta = 0.8$, $R = 300\text{ m} = 3\text{ px}$, $K_3(d) = \max(1 - d/3, 0)$):
$$\text{DTI}(P, G) = \frac{T}{T + 0.2\,F + 0.8\,(K - T) + \epsilon} = \frac{T}{0.2\,T + 0.2\,F + 0.8\,K + \epsilon}, \qquad K = |G|.$$
Per organizer forum thread `11516`, mapped catalogue pixels are masked out of scoring, so a predicted dot sitting `100–200 m` parallel to an already-mapped fault strand earns **zero credit** from that mapped strand and incurs full `0.2` false-positive weight unless a genuinely *new* unmapped test splay happens to nucleate within `300 m`. Deleting a collar subset that sacrifices truth credit $a = \Delta T \ge 0$ while shedding false-positive mass $b = \Delta F > 0$ strictly increases DTI if and only if:
$$\frac{T - a}{0.2(T - a) + 0.2(F - b) + 0.8 K + \epsilon} > \frac{T}{0.2 T + 0.2 F + 0.8 K + \epsilon} \iff T \cdot b > a\,(F + 4K + 5\epsilon).$$
At `DTI ≈ 0.2708`, each shed pure-halo dot ($a = 0, b = 1$) raises the ratio without reducing $T$; across `2,545` stripped halo dots whose lost splay-junction credit $a$ was small, denominator reduction produced the `+0.0070` gain. **Crucially, collar pruning is not universally beneficial:** when applied to a weaker skeleton parent (`GEMSDOE77` `gems85-h85-edti-collar35-skel-r33`), `3.5 px` pruning yielded `0.0964` (`OWNER-REPORTED`).

### 1.3 Fleet Score Landscape (`92` Sites) and How Higher DTI Is Physically Achievable
- **Headline Discrepancy (`0.3195` vs `0.4413`, both `OWNER-REPORTED`):** Across the refreshed 92-site fleet (`docs/evidence/fleet-feed.json`), `GEMSDOE79` and `GEMSDOE81` report `0.3195` (`OWNER-REPORTED` continuous/hybrid Poisson-disc lineages), whereas `GEMSDOE73` claims `0.4413` without a verifiable DrivenData submission-page receipt. Conversely, `GEMSDOE89` (`0.0301` `OWNER-REPORTED`) and `GEMSDOE90` (`0.0749` `OWNER-REPORTED`) illustrate catastrophic precision collapse when zero-catalogue geophysical filters emit tens of thousands of dots onto non-tectonic volcanic contacts and Pleistocene Lake Lahontan shoreline benches (`1,180–1,345 m ASL`).
- **No Uncalibrated Projections (`Parallel-Run Protocol Rule 3` & `AGENTS.md` Rule 4):** Local `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `11,321` withheld positives) is **not** monotone-calibrated to the unknown private test catalogue size $K_{\text{test}}$ (`R0` scores `0.0961` on fold-fair `gems57-pooled-hide-v2` vs `0.2778` `OWNER-REPORTED`). Never project a local holdout score as a live leaderboard number.
- **How Genuine Structural Gains Are Achieved:** Surpassing `R0` (`37,654` dots) requires improving **numerator recall $T$ per unit false-positive mass $F$** outside the `~2.5 px` mapped-fault collar via:
  1. **True sub-100m tectonic vs mimic discrimination:** Unilateral 1-m LiDAR scarp polarity $|\text{downface} - \text{upface}|$ (rejecting V-gullies), sentinel-clean 10-m fluvial $k_{sn}$/$\chi$ transient knickpoints, and absolute-elevation `zmean_m` (`1,180–1,345 m ASL`) contour-parallelism deconfounding (rejecting Lake Lahontan shorelines).
  2. **Harmonic depth-persistence & crustal mechanics:** `150 m` upward-continued magnetic gradient persistence $|\nabla\text{TMI}_{\text{up150}}|/(|\nabla\text{TMI}|+\tau)$ + vector-consistent Laplace $g_{zz} = -(\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11})$ + Morris–Byerlee–Kostrov azimuthal normal-dilation ($\cos^2(\theta - 22^\circ)$) and Riedel shear ($\sin^2(2(\theta - 22^\circ))$) tendency.
  3. **Anisotropic crack-tip mechanics + calibrated posterior allocation:** Pollard–Segall off-axis wing-crack lobes and opposing-tip releasing stepover bridges combined with SAR alluvial exposure-propensity weighting and Elkan (2001) Bayes subsampling odds calibration.

---

## 2. Four New Preregistered `H86I` Geological Hypotheses (`registry/h86i_ksad_hypotheses.json`)

All four hypotheses were formulated, checked for official source obtainability, and frozen in `registry/h86i_ksad_hypotheses.json` **before** writing any `H86I` feature or model code:

| Rank | ID / Lane | Specific Verified Layers | Physical Signature & Transform | Why Unmapped Faults Are Caught | Named Non-Fault Mimic | Sandbox Data Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **`H86I-1` (`H86I-KSAD`)** | Native `B2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19` + SHA-pinned USGS `geodawn_extensions_u8`, `geodawn_rad_u8`, `lidar_scarp_features_u8`, `topo_10m_derived_100m_u8`, `dem10_chi_100m_i16` + `vis_cat` | Roest 3-D analytic signal + `150 m` upward-continuation persistence + Laplace $g_{zz}$ + Morris–Byerlee–Kostrov $T_d, T_s$ + 1-m LiDAR unilateral polarity + channel $k_{sn}$ + Lahontan `zmean_m` deconfounder + SAR/Elkan Bayes PU + Minoux Dinkelbach Submodular $K_3$ allocator | Boosts low-slope alluvial aprons via SAR inverse propensity, resolves oblique ENE/NW transfer splays via $T_s$ + $k_{sn}$, and spaces cones adaptively via submodular $K_3$ envelope | Lahontan `1,180–1,345 m` wave-cut benches; symmetric V-gullies; shallow basalt float & E–W `090°` flight lines | **`VIABLE_IN_SANDBOX`** (**Executed: 3 arms**) |
| **2** | **`H86I-2` (`H86I-EULER3D`)** | Native `B13`, `B18 (+dg/dx)`, `-B11 (+dg/dy)`, FFT $g_z$; `B14, B3, B9`; `B15` | Sliding $9\times 9$ Reid 3-D Euler deconvolution comparing structural index $N=0$ (fault contact) vs $N=2$ (channel/dike), cross-checked against `B15` basement depth | Recovers horizontal updip trace of dipping blind intrabasin faults where gradient maxima shift `300–900 m` downdip | Non-reactivated Mesozoic pluton walls or pre-Cenozoic thrust contacts | `VIABLE_IN_SANDBOX` (Deferred: 3-exp cap) |
| **3** | **`H86I-3` (`H86I-THCD`)** | DOE GDR-1391 2-m probe, geothermometry (`dist_known_fault_px` excluded), sinter/tufa + `zmean_m` + `B15, B17` | Upslope Péclet advection–dispersion adjoint back-projection along $-\nabla z_{\text{mean}}$ onto `B15` basement hinges | Relocates laterally advected `1–6 km` playa thermal outflow plumes back onto concealed upflow fault conduits | Stratigraphically confined warm artesian fan-toe pinchouts | `VIABLE_IN_SANDBOX` (Deferred: 3-exp cap) |
| **4** | **`H86I-4` (`H86I-INSAR-VERT`)** | External NASA/USGS `OPERA_L3_DISP-S1_V1` vertical/east InSAR velocity + `B8, B15, B17` | `< 500 m` spatial phase-velocity gradient $|\nabla \dot{u}_z|$ across clay-gouge aquifer barriers | Detects sharp poroelastic hydraulic-head steps across zero-relief playas invisible to `~20 km` GPS kriging | Agricultural / mine dewatering subsidence bowls at clay-facies pinchouts | **`NOT_VIABLE_IN_SANDBOX_YET`** (Free at ASF DAAC, blocked by outbound host allowlist) |

---

## 3. Forensic Discoveries & `H86I-KSAD` Same-Split `HOLDOUT-DTI` Results

### 3.1 Discovery of `IR-86-H86F-INQUAD-TRAINING-20261025`
Line-by-line inspection of `scripts/run_h86f_ewcs.py` (`line 528`) vs `scripts/run_lane86c.py` (`line 206`) uncovered a critical training-domain difference on `gems57-pooled-hide-v2` (`seed=20`, `hide_frac=0.20`, `buffer_px=3`, `11,321` withheld positives):
- `H86C-KSLB` (`0.1241`) trained **strictly Leave-One-Quadrant-Out** (`quad != q` eroded `12 px = 1.2 km`).
- `H86F-EWCS` (`0.1723`) withheld all `11,321` hidden whole-component pixels + `3 px` buffer, **but** trained on the remaining `80%` visible components inside all 4 quadrants (`vis`), allowing tree splits to adapt to in-quadrant background distributions.
- When `H86F-EWCS` is re-evaluated under **strict outer Leave-One-Quadrant-Out** (`C1_H86F_EWCS_strict_loqo_ctrl`), its pooled `HOLDOUT-DTI` is **`0.133311 [0.117836, 0.150210]`** (`-0.039014` below its in-quadrant visible score).

### 3.2 Preregistered 3-Arm Strict-LOQO Results (`gems57-pooled-hide-v2`, `11,321` Withheld Positives)
All `32 / 32` single-feature leakage canaries passed (`max_discriminative_auc = 0.8074 <= 0.90`; `lahontan_contour_mimic` scored raw `AUC = 0.4787 < 0.50`, confirming negative association with real faults):

| Arm / Comparator | Outer Training Regime | Pooled `HOLDOUT-DTI` | `20 km` Block-Bootstrap `95% CI` | Paired $\Delta$ vs `E1` (`95% CI`) |
| :--- | :--- | :---: | :---: | :---: |
| **`E2_ksad_pointwise_d28_ablation`** (`37,654`d, `2.8 px`) | **Strict LOQO (`quad != q`)** | **`0.1599`** (`0.159867`) | **`[0.1459, 0.1742]`** | `-0.0046 [-0.0100, +0.0010]` |
| **`E1_ksad_dinkelbach_submod`** (Primary, Dinkelbach $K_3$) | **Strict LOQO (`quad != q`)** | **`0.1553`** (`0.155275`) | **`[0.1396, 0.1718]`** | — *(Primary Candidate)* |
| **`C1_H86F_EWCS_strict_loqo_ctrl`** (`37,654`d, `2.8 px`) | **Strict LOQO (`quad != q`)** | `0.1333` (`0.133311`) | `[0.1178, 0.1502]` | **`+0.0220 [+0.0038, +0.0405]`** |
| Historical `H86C-KSLB` (`E3_kslb_noisyor_44k`) | Strict LOQO (`quad != q`) | `0.1241` (`0.124063`) | `[0.1080, 0.1403]` | `+0.0312` *(same-split archive)* |
| `R0_GEMSDOE25_fold_fair` (`d_vis > 2.0 px`) | External `R0` fold-fair | `0.0961` (`0.096086`) | `[0.0830, 0.1089]` | **`+0.0592 [+0.0439, +0.0751]`** |
| **`E3_ksad_cover_blind_no_catalogue`** (Zero-cat, no 100m DEM) | **Strict LOQO (`quad != q`)** | **`0.0624`** (`0.062413`) | **`[0.0498, 0.0762]`** | `+0.0929 [+0.0749, +0.1095]` |
| `R0_D28_visible_collar` (`d_vis > 3.0 px`) | External `D28` fold-fair | `0.0273` (`0.027299`) | `[0.0217, 0.0329]` | **`+0.1280 [+0.1127, +0.1438]`** |
| Historical `H86F-EWCS` (`E1_ewcs_coupled_pu`) | *In-quadrant visible (`4` quads)* | `0.1723` (`0.172325`) | `[0.1530, 0.1898]` | *Different outer training domain* |

**Key Takeaways:**
1. Under like-for-like **strict Leave-One-Quadrant-Out**, `H86I-KSAD` sets the **new all-time repository record** (`E2: 0.1599`, `E1: 0.1553`), beating strict-LOQO `H86F-EWCS` (`0.1333`) in **every single quadrant** (`NW: 0.1748 vs 0.1637`, `NE: 0.1468 vs 0.1082`, `SW: 0.1511 vs 0.1262`, `SE: 0.1527 vs 0.1396`) with a **strictly positive paired `20 km` block-bootstrap 95% CI (`+0.0220 [+0.0038, +0.0405]`)**, and nearly **doubling** all prior 2026-10-25 zero-catalogue cover-blind baselines (`E3: 0.0624` vs `PCC 0.0327`, `PSTD 0.0314`, `GZZD 0.0303`).
2. Comparing `E1` vs `E2` on the identical posterior shows Dinkelbach Submodular $K_3$ allocation wins cleanly in wide-basin `NW` (`0.1748` vs `0.1647`, `+0.0101`), while early stopping at $\lambda^* = 0.17$ under-emits slightly in steeper `NE/SW/SE` ranges relative to full `37,654`-dot `2.8 px` emission (`-0.0046 [-0.0100, +0.0010]`, statistically tied).

---

## 4. Pre-Placement & Pre-Serialization Registry Audit (`690` Rasters)

1. **Pre-Placement Surface Check (`docs/evidence/h86i-ksad-registry-surface.json`):** `0` Spearman $\rho > 0.90$ firings across all `688 / 690` compatible rasters (`worst_spearman = 0.6344` vs `5GEMSDOE:context_detector_prob_topo_rad.tif`, lower than `H86F-EWCS`'s `0.7508`).
2. **Pre-Serialization Final-Dot Check (`docs/evidence/h86i-ksad-registry-final-dots.json`):** `E1` emitted `28,197` binary dots (`0` on catalogue, `min_distance_to_catalogue = 2.83 px`, `worst_spearman = 0.0933`). However, **3 genuinely informative discrete (`<= 40,000`-dot) registry rasters exceeded the `0.70` forward 3-px overlap limit**:
   - `GEMSDOE80__gems80-adpt-kkt-lagrangian-36500d-20261022T012049Z-5bd11c85-zeros.tif` (`36,500` dots, 3-px chance halo **`c = 14.65% << 70%`**): **`71.31%` forward overlap** (`4.87x` chance);
   - `GEMSDOE43:gems43-sup01-hgb21-sep40-n40000` (`-nan` and `-zeros`, `40,000` dots, **`c = 18.45% << 70%`**): **`70.19%` forward overlap** (`3.80x` chance).
3. **Fail-Closed Halt:** Per Parallel-Run Protocol Rule 1 and `AGENTS.md` Rules 10–11, `scripts/run_h86i_ksad.py` halted **before writing a duplicate GeoTIFF**, recorded the negative Run Card, and locked `main()` behind `protocol_preflight.require_feasible()`.

---

## 5. Remaining Work & Limitations

1. **Governance & Registry Blockers Require Human Selector Decision:** No automated pipeline in `GEMSDOE86` can legitimately flip `DO NOT SUBMIT` while (a) `17GEMSDOE` (`ab0a0a62...`) saturates `100.0%` of allowed pixels under the literal support rule, (b) `2` historical inventory rows (`14GEMSDOE`, `7GEMSDOE`) fail CRS/band compatibility (`688 / 690`), and (c) the pinned external inventory ends at `56GEMSDOE` rather than covering all `92` sites (`GEMSDOE57..92`).
2. **Fleet Corridor Saturation (`IR-86-H86I-KSAD-OVERLAP-STOP-20261025`):** Even apart from `17GEMSDOE`, high-precision Dinkelbach/Lagrangian submodular core-corridor dot sets (`~28k` dots) now cross `70%` 3-px overlap with `GEMSDOE80` (`36.5k` KKT-Lagrangian dots). Meanwhile, the already-published audit artifact `docs/downloads/gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif` (`HOLDOUT-DTI = 0.1723` in-quadrant visible; `37,654` dots) had **`0` discrete `<= 55k`-dot firings** (max discrete overlap `26.96%` vs `GEMSDOE32`, `68.69%` reverse/forward check below `70%`).
3. **Deferred Untried Hypotheses:** `H86I-2` (`H86I-EULER3D` sliding 3-D vector-gravity/magnetic Euler deconvolution) and `H86I-3` (`H86I-THCD` upslope Péclet thermal-plume back-projection) remain clean, viable next-session candidates once a human selector resolves the upstream registry policy; `H86I-4` (`OPERA_L3_DISP-S1_V1` InSAR) requires mirroring a SHA-pinned competition-grid velocity derivative raster into an allowed GitHub release first.
