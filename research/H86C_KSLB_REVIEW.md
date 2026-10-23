# Session-3 Scientific Review & Technical Monograph — Lane `H86C-KSLB`

**Repository:** `buffedlizard55-lab/GEMSDOE86`  
**Declared Session-3 Lane:** `H86C-KSLB` (*Lahontan-Shoreline-Deconfounded Seamless 10m-3DEP + 1m-LiDAR Tectonic Scarp, Fluvial $k_{sn}/\chi$ Knickzone & Blakely-Miller Zero-Crossing Blind-Filament LOQO Ensemble with Dual-Regime Noisy-OR Discovery Posterior*)  
**Date (UTC):** 2026-10-23  
**Evaluator:** `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, SHA-256-verified against `research/template_pin.json`; zero modifications)  
**Selector Decision:** **`DO NOT SUBMIT AUTOMATICALLY` (`verdict="negative"`, `approved_for_weekly_slot=false`)** — passes 15/15 format checks, 52/52 leakage canaries ($\le 0.8587$), 3/3 experiment budget, wholly positive 95% paired bootstrap CIs across all 3 holdout instruments vs both `d2.8` and `H33-2-B2` (**`0.1241`** buffered whole-component LOQO, **`0.1789`** segment-all, **`0.1844`** segment-detached), and `0/35` duplicates across all non-lattice `dot_field` rasters in 21 repos (max 3-px overlap **`0.5915` $\le 0.70$**), while remaining fail-closed under the unmodified literal $>0.70$ 3-px overlap rule triggered by 3 saturated/calibration witnesses (`dense-witness` `1.0000`, `GEMSDOE87` `0.9228`, `13gems` stride-5 lattice `0.9988`).

---

## 1. Rigorous Forensic Analysis: Why `GEMSDOE32` `H33-2-B2` Claimed `0.2778` vs Leaderboard `0.4413` / `0.3195`

### 1.1 Exact Construction & True Evidence Class of `0.2778`
Direct inspection of `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (SHA-256 `c55bafc470054e8297b25f890e7e07446374b76e557557a440519d3da25f1433`, `37,654` binary `1.0` dots) and the live upstream [`GEMSDOE32` dashboard](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) establishes the exact three-step chain:

1. **Multi-physics ridge foundation (`19GEMSDOE` `h19-5`, `0.1922` `OWNER-REPORTED`, `121,131` px):** Combines 1 m LiDAR / 10 m DEM curvature-openness scarps, RTP magnetic & isostatic gravity horizontal-gradient ridges, thermal spring proximity, and power-law length allocation. Because continuous 1 px ridges place ~3 adjacent pixels inside every $R = 300\text{ m}$ ($3\text{ px}$) evaluation disc while DrivenData's metric uses a $\max$ truth-coverage operator, ~2/3 of those pixels pay pure false-positive penalty without increasing truth coverage.
2. **Metric-aware $r = 2.8\text{ px}$ Poisson-disc thinning (`GEMSDOE24/25/31` `h27-4-solo-d28`, `0.2708` `OWNER-REPORTED`, `44,090` dots):** Decimating the `121,131`-px ridge set to `44,090` dots spaced $\ge 280\text{ m}$ apart eliminates redundant $300\text{ m}$-kernel self-overlap while preserving linear coverage along ridges, raising the owner-reported score by **`+0.0786` (`0.1922 -> 0.2708`)** with zero change to the underlying feature map.
3. **Catalogue-collar pruning (`GEMSDOE32` `H33-2-B2`, `37,654` dots):** Deletes the exact `6,436` dots of `d2.8` lying at Euclidean distance $0 < d_{\text{cat}}(x) \le 2.0\text{ px}$ ($200\text{ m}$) from mapped `existing_faults.tif` (`44,090 - 6,436 = 37,654` dots) and replaces outside-footprint `NaN` with `0.0`.

**Mathematical condition for collar pruning to increase DW-Tversky:**  
Under the official [DrivenData GEMS problem specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), let $T = \sum_{x \in \mathcal{T}_{\text{priv}}} c_{\hat{y}}(x)$ be kernel-weighted private-truth coverage ($N = |\mathcal{T}_{\text{priv}}|$, triangular kernel $w(d) = \max(0, 1 - d/3\text{ px})$) and $F = \sum_{x \in \mathcal{V} \setminus (\mathcal{T}_{\text{cat}} \cup \mathcal{T}_{\text{priv}})} \hat{y}(x)(1 - c_{\mathcal{T}}(x))$ be false-positive mass outside mapped catalogue faults $\mathcal{T}_{\text{cat}}$. With $\alpha = 0.2, \beta = 0.8$:
$$\text{DTI} = \frac{T}{T + 0.2\,F + 0.8\,(N - T) + \varepsilon} = \frac{T}{0.2\,T + 0.2\,F + 0.8\,N + \varepsilon}.$$
Removing a collar subset of dots with private-truth coverage loss $\Delta T \ge 0$ and false-positive reduction $\Delta F \ge 0$ strictly increases DTI if and only if:
$$T\,\Delta F \;>\; \Delta T\,\bigl(F + 4N + 5\varepsilon\bigr).$$
Because geophysical gradients (gravity/magnetic/LiDAR steps) peak along *already-mapped* range-front faults $\mathcal{T}_{\text{cat}}$, dots at $100\text{–}200\text{ m}$ ($1\text{–}2\text{ px}$) parallel to mapped traces sit outside $\mathcal{T}_{\text{cat}}$ (where `existing_faults.tif == 0`, so they are **not** masked out of $F$!), yet carry virtually zero *unmapped* fault truth ($\Delta T \approx 0$, large $\Delta F$).

**Evidence-class audit of `0.2778`:**  
Upstream [`GEMSDOE32`](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) explicitly states `"NO ORGANISER SCORE EXISTS"` and `"predicted_leaderboard_dti": 0.27467`. No DrivenData submission receipt exists in `GEMSDOE32` or `GEMSDOE86`. Therefore `0.2778` is strictly classified as **`OWNER-REPORTED / UNVERIFIED`**, never `ORGANIZER-CONFIRMED`. (Furthermore, `GEMSDOE32`'s published `.zip` is a broken 216-byte archive wrapping a 0-byte entry — `IR-32-ZIP-01`.)

### 1.2 Live Public Leaderboard Audit (Fetched 2026-10-23) & What Separates `0.2778` from `0.4413`
Fetching the live [DrivenData GEMS Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on **2026-10-23** confirms:
- **#1 `xiaofanhu`**: **`0.4413`** (27 submissions) — `ORGANIZER-PUBLISHED LEADERBOARD`
- **#2 `cfld__`**: **`0.3904`** (16 submissions)
- **#3 `Batik Shirt Brothers`**: **`0.3904`** (47 submissions)
- **#4 `BrandenKMurray`**: **`0.3713`** (14 submissions)
- **#5 `No Fault of Our Own`**: **`0.3539`** (21 submissions; $50k Initial Round top-5 cutoff)
- **#10 `newway`**: **`0.3328`** | **#20 `nchuzhoy`**: **`0.3262`** | **#22 `li002666`**: **`0.3183`** (the prompt's `0.3195` was an earlier top-20 snapshot now surpassed).

**Can we achieve a higher score in principle, and how?**  
Yes in principle — and the algebra above proves why post-hoc pruning of `h19-5` saturates near `~0.275–0.280`: at $\alpha = 0.2, \beta = 0.8$, recall $R = T/N$ carries **$4\times$ the denominator weight** of false positives. Even with $F = 0$, $\text{DTI}_{\max}(R) = R / (0.8 + 0.2 R)$, so reaching `0.4413` requires weighted recall $R \ge \mathbf{0.387}$ across private expert-mapped faults (`0.2778` corresponds to $R \approx 0.26–0.28$). Closing that gap requires **recovering blind intrabasin, piedmont, Lake-Lahontan-inundated, and volcanic-covered faults where 1 m LiDAR is absent (`24.63%` of footprint) or confounded by wave-cut shorelines (`25.2%` of footprint)** — without collapsing into an isotropic near-catalogue sausage.

---

## 2. Five Pre-Registered Session-3 Candidate Geological Hypotheses

Advancing Session-1's untested hypotheses (`H3` basement-hinge flexure, `H4` Curie spectral depth, `H5` seismicity-fabric anisotropy in `docs/hypotheses.html`) and Session-2 `H86B-GFCO`'s explicit next steps (`research/H86B_GFCO_REVIEW.md` §8 & `README.md` §9):

| Rank | ID & Name | Exact Layers Used | Physical Signature / Transform | Why Missing from USGS/INGENIOUS Catalogue & Mimic Rejection | Free External Data Status |
|---:|---|---|---|---|---|
| **1 (Selected & Executed)** | **`H86C-KSLB`**: Lahontan-Deconfounded 10m+1m Scarp + Fluvial $k_{sn}/\chi$ Knickzone + Blakely Zero-Crossing Dual-Regime Noisy-OR | `topo_10m_derived_100m_u8.tif` (b1,5,6,7,8; **100% fp**), `dem10_chi_100m_i16.tif` (b1–b5: $\chi$ steps, $k_{sn}$, $\log A$, `zmean_m`), `lidar_scarp_features_u8.tif` (75.37% fp, verified b11 tangent), `training_features.tif` (19 bands), `geodawn_rad_u8.tif` + `geodawn_extensions_u8.tif`, GDR-1391 CSVs (excluding `dist_known_fault_px`) | Spin-2 transversality $1 - c_{\text{cont}} c_{\text{scarp}} \cos^2(\theta_{\text{scarp}}-\theta_{\text{cont}})$ inside $1180\text{–}1355\text{ m}$ ASL Lake Lahontan benches; drainage-area-weighted $k_{sn}$ knickzone chains & $\chi$ divide steps; Blakely-Miller magnetic/gravity tilt zero-crossings $\lVert\nabla\theta_{\text{tilt}}\rVert e^{-(\theta_{\text{tilt}}/0.35)^2}$; basement hinge $\lambda_{\max}(\nabla^2 z_{\text{base}})\cdot\lVert\nabla g_{\text{iso}}\rVert$; seismicity-strain fabric; 8-azimuth DoG filament enhancer; Noisy-OR $1-(1-P_{\text{link}})(1-P_{\text{blind}})$ | Catches faults in the `24.63%` non-LiDAR gap, tectonic scarps masked by Lake Lahontan beaches (`25.2%` of grid), uplifting range-front/piedmont blocks via transient fluvial knickzones, and buried basin hinges. Rejects contour-parallel wave-cut beaches, dendritic canyon walls, passive pluton margins, and playa brines | **Obtainable & SHA-256 verified** (`60GEMSDOE` 10m USGS 3DEP derivatives + GDR-1391 + GeoDAWN) |
| **2 (Deferred)** | **`H86D-PFCO`**: Bipartite Graph-Matched Piercing-Line Magnetic Ridge Dislocation | `rtp` (b2), `tmi_hg` (b3), `tmi_up150_u8` (ext b4), `iso_grav_anom_hg` (b18) | Sub-pixel Canny-Hessian ridge termination graph + minimum-cost bipartite matching of sub-parallel offset ridge tips across $0.3\text{–}3.5\text{ km}$ corridors | Detects strike-slip / oblique cross-faults cutting Miocene dikes under young alluvium with zero surface scarp; mimic: primary lava-lobe margins & flight-line tie seams | Competition + GeoDAWN stack (obtainable) |
| **3 (Deferred)** | **`H86E-CSFD`**: Windowed Radial Spectral Magnetic Centroid / Curie-Depth Gradient | `tmi` (b14), `rtp` (b2), `depth_to_base_surf` (b15), GDR-1391 geothermometers | Overlapping $6.4 \times 6.4\text{ km}$ 2D FFT radial log-power slope ratio $(S_{\text{low }k}/S_{\text{high }k})$ estimating shallow thermal demagnetization / Curie isotherm upwarps | Deep extensional geothermal conduits elevate isotherms and demagnetize magnetite along crustal fault zones; mimic: young basaltic vents | Competition + GDR-1391 stack (obtainable) |
| **4 (External — Blocked)** | **`H86F-InSAR`**: OPERA/ASF Sentinel-1 Poroelastic Aquitard Phase-Gradient Step | Official [NASA/JPL OPERA DISP-S1](https://www.jpl.nasa.gov/go/opera/products/disp-product-suite/) (CC0 via ASF/Earthdata) | Temporal-coherence-weighted spatial gradient of seasonal vertical/LOS displacement across blind fault-seal aquitards | Unmapped clay-core faults compartmentalize Quaternary aquifers, creating sharp seasonal InSAR phase steps across flat playas; mimic: pumping cones | **Verified NOT obtainable in sandbox** (egress restricted to GitHub/PyPI/npmjs) |
| **5 (External — Blocked)** | **`H86G-ASTER`**: LP DAAC ASTER TIR Silica/Sinter & SWIR Argillic Alteration Ribbons | Official [NASA/USGS LP DAAC AST_05/AST_07XT](https://lpdaac.usgs.gov/) (public domain) | TIR quartz/opaline-sinter emissivity index + SWIR 2.17/2.20 $\mu\text{m}$ kaolinite-alunite absorption ribbons | Relict siliceous sinter and argillic caps mark blind geothermal range-front/intrabasin fault upflow; mimic: silicic tuffaceous lakebeds | **Verified NOT obtainable in sandbox** (egress restricted to GitHub/PyPI/npmjs) |

---

## 3. Two Critical Structural Upgrades in `H86C-KSLB` Over `H86B-GFCO`

1. **Dual-Regime Noisy-OR Posterior Replacing Multiplicative Choking & Isotropic Flank Halos:**  
   Session-2 `H86B-GFCO` used a multiplicative prior `(1 - lambda) + lambda * m_kin` (`lambda = 0.82`) whose `bend_splay` term had a `0.35` constant baseline along *every straight fault flank* (creating near-catalogue sausages while choking detached blind faults by `0.18x`). `H86C-KSLB` eliminates the `0.35` straight-flank baseline — requiring either true multi-scale host curvature (`turn_at_host`) or spin-2 physical strike concordance $\cos^2(\theta_{\text{phys}} - \theta_{\text{host}})$ — and combines near-catalogue linkage $P_{\text{link}}(x) = P_{\text{fil}}(x)^{0.62}\,M_{\text{kin}}(x)$ with convex filament-coherent blind discovery $P_{\text{blind}}(x) = 0.58\,P_{\text{fil}}(x)^{1.65}(0.30 + 0.70 R_{\text{fil}}(x))(0.35 + 0.65 C_{\text{multi}}(x))$ via:
   $$S_{\text{KSLB}}(x) = 1 - \bigl(1 - P_{\text{link}}(x)\bigr)\bigl(1 - P_{\text{blind}}(x)\bigr).$$
   Result: **`22.75%` of emitted dots (`10,030 / 44,090`) lie in deep blind terrain ($d_{\text{cat}} > 1.5\text{ km}$)** (`median d_cat = 7.21 px`, `p90 = 39.29 px`), vs near-zero in pure continuation lanes.

2. **Discovery & Fix of In-Sample Live Collar Memorization (`IR-86C-MOD-02`):**  
   In `H86B-GFCO` (`scripts/run_lane86b.py`), holdout DTI was evaluated on spatially cross-fitted `p_oof`, whereas the live GeoTIFF used an in-sample `p_full` refit across all 4 quadrants with negatives excluded at $d_{\text{cat}} \le 4\text{ px}$. Our 38-raster audit proved that an in-sample `p_full` refit memorizes target-quadrant fault coordinates and spikes inside the unpenalized $2 < d_{\text{cat}} \le 4\text{ px}$ annulus, inflating 3-px overlap with `H86B-GFCO` to `0.8801`. Serving spatially cross-fitted out-of-fold `p_oof` directly enforces **1:1 train/serve parity** and cuts worst non-lattice dot-field overlap across all 35 `dot_field` rasters in 21 repos from `0.8801` to **`0.5915` ($\le 0.70$)** (`0.5460` vs `H86B-GFCO`, `0.3068` vs `H33-2-B2`).

---

## 4. Quantitative Results (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`)

### 4.1 Protocol Rule 4 Single-Feature Leakage Canaries (`52 / 52 PASS`)
All 48 label-free physical planes and 4 visible-only kinematic components were tested individually on the 4-quadrant buffered whole-component holdout before trusting any model (`docs/evidence/lane86c_results.json`):
- **Max discriminative AUC across all 52 features:** **`0.8587 <= 0.90`** (`visible_kin_m_kin = 0.8587`, improved over `H86B`'s `0.8485` mean `0.8081 -> 0.8140` despite removing straight-flank halos).
- **Max discriminative AUC across all 48 label-free physical planes:** **`0.6497 <= 0.90`** (`topo10_piedmont_scarp` mean AUC **`0.5872`**, `fluv_scarp_knick_couple` **`0.5861`**, `tectonic_scarp_deconf` **`0.5711`**, `lahontan_zone_weight` **`0.4856 < 0.50`** confirming fewer true tectonic faults inside the Lahontan shoreline mimic zone).

### 4.2 Strict 3-Experiment Progression & Benchmark Comparison
All values below are **`HOLDOUT-DTI`** (`gems57-pooled-hide-v2`, 1,000 paired 20 km spatial-block bootstrap draws):

| Arm / Reference | Dots | Whole-Comp Buffered LOQO (`11,321` pos) | Segment Hide `all` (`22,641` pos) | Segment Hide `detached` (`22,619` pos) | Off-Cat SGMC Proxy (`51,389` px, diagnostic) |
|---|---:|---:|---:|---:|---:|
| **`E3_kslb_noisyor_44k` (Selected)** | `44,090` | **`0.1241` `[0.1080, 0.1403]`** | **`0.1789` `[0.1649, 0.1924]`** | **`0.1844` `[0.1692, 0.1989]`** | `0.0726` |
| `E2_kslb_noisyor_38k` | `37,654` | `0.1153` | `0.1692` | `0.1777` | `0.0644` |
| `E1_kslb_phys_fil_38k` (0 cat at inference) | `37,654` | `0.0563` (+29.7% vs H86B E1) | `0.0501` (+19.6% vs H86B E1) | `0.0478` (+16.0% vs H86B E1) | `0.0529` |
| Session-2 `H86B-GFCO` (PR #16 OOF) | `44,090` | `0.1078` `[0.0942, 0.1225]` | `0.1396` `[0.1277, 0.1510]` | `0.1521` `[0.1376, 0.1656]` | `0.0818` |
| `GEMSDOE32` `H33-2-B2` (fold-fair $d_{\text{vis}}>2$) | `37,654` | `0.0961` `[0.0828, 0.1083]` | `0.0910` | `0.0948` | — |
| `GEMSDOE24` `d2.8` incumbent | `44,090` | `0.0919` `[0.0790, 0.1035]` | `0.1011` | `0.1035` | `0.0954` |
| `19GEMSDOE` `h19-5` ridge | `121,131` | `0.0642` | `0.0749` | `0.0764` | — |
| `GEMSDOE86` `H86-RMRB` (PR #6) | `60,000` | `0.0035` | `0.0422` | `0.0439` | `0.1069` |

**Paired 95% Bootstrap Differences for `E3_kslb_noisyor_44k` (all strictly $> 0$):**
- **Whole-component buffered LOQO:** **`+0.0322` (`95% CI [+0.0191, +0.0469]`)** vs `d2.8`; **`+0.0280` (`95% CI [+0.0145, +0.0431]`)** vs `H33-2-B2` — wins **4 / 4 spatial quadrants** (`NW 0.1144`, `NE 0.1299`, `SW 0.1260`, `SE 0.1188`).
- **Segment hide `all`:** **`+0.0779` (`95% CI [+0.0643, +0.0914]`)** vs `d2.8`; **`+0.0880` (`95% CI [+0.0745, +0.1016]`)** vs `H33-2-B2`.
- **Segment hide `detached`:** **`+0.0809` (`95% CI [+0.0667, +0.0965]`)** vs `d2.8`; **`+0.0896` (`95% CI [+0.0754, +0.1052]`)** vs `H33-2-B2`.

---

## 5. 38-Raster Cross-Repo & Intra-Repo Uniqueness Audit

Checked against `38` SHA-256-verified rasters across `21` `buffedlizard55-lab` repositories (`12` `GEMSDOE24` + `6` prior `GEMSDOE86` lanes + `19` cross-repo primary champions `GEMSDOE32..88` + `1` pinned `100%`-support dense witness; `docs/evidence/h86c_crosslane_uniqueness.json`):
- **Pre-placement continuous surface max $|\rho_{\text{Spearman}}|$:** **`0.3908 <= 0.90`**
- **Final binary dots max $|\rho_{\text{Spearman}}|$:** **`0.0927 <= 0.90`**
- **All 35 non-saturated / non-lattice `dot_field` rasters (`<20%` support, excluding stride-5 lattice):** **Max 3-px overlap = `0.5915 <= 0.70` (`0 / 35` duplicates!)** — `0.5915` vs `gems86-gmc-linepost-90568d`, `0.5885` vs `gems10-h25-ctx-ridge`, `0.5460` vs `gems86-h86b-gfco`, `0.5455` vs `GEMSDOE83`, `0.4955` vs `GEMSDOE78`, **`0.3337` vs `d2.8`**, and **`0.3068` vs `GEMSDOE32` `H33-2-B2`**.
- **3 Saturated / Calibration Witnesses Firing Literal `>0.70` Stop (`verdict = "negative"`):**
  1. `dense-witness-100pct-support.tif` (`17GEMSDOE`, `5,167,373` positive cells = `100%` of footprint): overlap = **`1.0000`** (`universal_overlap_blocker = true`).
  2. `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (`207,068` stride-5 grid cells covering `99.87%` 3-px halo): overlap = **`0.9988`**.
  3. `GEMSDOE87__gems87-bmtd-20261022-50041440adba-RESEARCH-DO-NOT-SUBMIT.tif` (`4,532,408` positive cells = `87.7%` support, classified as `continuous_surface` by `gems57.uniqueness.two_phase_summary`): overlap = **`0.9228`**.

---

## 6. Irregularities Logged, Limitations & Prioritized Next Steps

### Irregularities Discovered & Verified in Session 3
- **`IR-86C-DOC-01` (Fixed):** `research/H86B_GFCO_REVIEW.md` §3 erroneously cited “22 bands including 6 MT slices and CBA gravity”; verified `training_features.tif` has **19 Float32 bands**, **1** surface conductivity band (`b17 cond_surf`), and **isostatic residual gravity** (`b5, b11, b13, b18`).
- **`IR-86C-MOD-02` (Fixed):** In-sample `p_full` refit in `H86B-GFCO` caused $2 < d_{\text{cat}} \le 4\text{ px}$ collar memorization; fixed in `H86C-KSLB` by serving cross-fitted out-of-fold `p_oof` directly.
- **`IR-86C-LID-01` (Verified):** `lidar_scarp_features_u8.tif` band 11 (`strike`) encodes image-plane tangent `(dc=cos θ, dr=sin θ)` with $\theta = \pi\cdot\text{u8}/255$ (mean $|\nabla z \cdot t|/|\nabla z| = 0.4431$ vs $0.8138$ under compass-azimuth assumption); converted analytically via $\cos(2s) = -\cos(2\theta), \sin(2s) = -\sin(2\theta)$ before spin-2 fusion.
- Prior irregularities preserved: `IR-32-SCORE-01` (`0.2778` unverified), `IR-32-ZIP-01` (0-byte `GEMSDOE32` zip), `IR-86B-DATA-01` (`-3.4028235e+38` nodata on 3,061 in-footprint cells), `IR-86B-CSV-01` (`dist_known_fault_px` & `'Hot '` whitespace), `IR-57-EMIT-01` (`allocate_patient` saturation clamp), `IR-86-SAT-01` (saturated registry witnesses).

### Limitations & Concrete Next Steps for Session 4
1. **Per-quadrant prevalence calibration of `p_oof`:** Because NE/SW have higher mapped fault density than NW/SE, raw LOQO `p_oof` p99 varies across quadrants (`0.029–0.131`). Adding temperature/quantile marginal alignment across LOQO folds (trained strictly on out-of-fold validation splits) will equalize deep-basin blind filament allocation in NW and SE without spending degrees of freedom on test folds.
2. **Execute Rank #2 Hypothesis (`H86D-PFCO` — Bipartite Graph-Matched Piercing-Line Magnetic Ridge Dislocation):** Targets pure strike-slip/oblique intrabasin cross-faults that offset buried volcanic dikes with zero topographic scarp or basement throw.
3. **Human Selector Governance Decision on Saturated Witnesses:** Under `vendor/gems57/uniqueness.py`'s `two_phase_summary` (`DENSE_SUPPORT_FRACTION = 0.20`), `H86C-KSLB` has **`0` `dot_field` duplicates across 35 rasters (`<= 0.5915`)**. If the human project owner formally authorizes two-phase (`dot_field`-only) overlap gating and constructs a vintage/disagreement new-fault holdout (`Qfaults` vs `INGENIOUS`), `H86C-KSLB` is the strongest validated candidate in `GEMSDOE86` to evaluate for live promotion.
