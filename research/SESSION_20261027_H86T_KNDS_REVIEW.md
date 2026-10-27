# Session Review — 2026-10-27 (`H86T-KNDS`, Focus-9 Forensics & 3-Pass Audit)

- **Branch:** `arena/70644855-gemsdoe86`
- **Date (UTC):** `2026-10-27`
- **Current Repository Upload Decision:** **`DO NOT SUBMIT`** (`safe_to_submit: false`, `approved_for_weekly_slot: false`, `submission_slots_used: 0`)
- **Newest Research GeoTIFF (#48):** `docs/downloads/gems86-h86t-knds-37654dots-20261027T194957Z-3d7f3677-zeros.tif` (`136,641` bytes, SHA-256 `c6870a5708e5ff8222e84281d942d9d6afd1b9feac73c27a1508937e441d18c2`, ZIP SHA-256 `d925fba286f531ee6fcfa830156671a5e3a083dacd2395d3f976541746b30c7c`, `37,654` binary dots in `{0.0, 1.0}`, `0` NaN/Inf, `EPSG:32611`, `3730×3292` @ `100 m`, `min d_cat = 3.1623 px > 3.0 px`, `55.25% > 1 km` off-catalogue, `verdict: "negative"`).

---

## 1. Executive Summary — Focus-9 Best Submissions & `GEMSDOE86` Downloadable Candidates

> **Evidence-Labeling Contract:** Every leaderboard figure reported by a repository owner without an organizer-signed receipt in this workspace is labeled **`OWNER-REPORTED`** (never `ORGANIZER-CONFIRMED`). Every internal evaluation is labeled **`HOLDOUT-DTI`** (`gems57-pooled-hide-v2`, `11,321` withheld fault pixels, 1,000-draw 20 km spatial block bootstrap 95% CI) or **`SGMC-PROXY-DTI`** (`62,122` off-catalogue USGS SGMC 1:500k bedrock fault pixels $>3\text{ px}$ from `existing_faults.tif`). Empirical fleet regression numbers are labeled **`FLEET-REGRESSION-PROJECTION (not a score)`** (`n = 20` strict-matched `OWNER-REPORTED` fleet rasters, `LOO-RMSE = 0.0410`).

### 1.1 Focus-9 Sites (`GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, `36`) — Per-Site Best Scored Submissions

| Rank | Focus Site | Best Scored Submission (`OWNER-REPORTED`) | Score (`OWNER-REPORTED`) | Dots · Collar · `>1 km` Share | 3-px Forward Overlap vs `GEMSDOE32 H33` | Uniqueness & Upload Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | **`GEMSDOE32`** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **`0.2778`** (#1 of 92 repos) | `37,654` · `2.24 px` · **`69.83%`** | `100.00%` (self) | Reference champion; **NO — exact duplicate if re-uploaded** |
| **2** | **`GEMSDOE36`** | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | **`0.2750`** | `38,854` · `2.24 px` · `69.71%` | `97.40%` (`> 70%`) | `H19-5` family clone; **NO — duplicate (`>70%` overlap)** |
| **3** | **`GEMSDOE28`** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` *(also `h27-4` `0.2708`, `h38-1` `0.2707`, `h32-1` `0.2649`)* | **`0.2710`** | `37,660` · `1.41 px` · `65.65%` | `95.47%` (`> 70%`) | `H19-5` family clone + `-nan` outside footprint; **NO — DO NOT SUBMIT** |
| **4** | **`GEMSDOE31`** | `gemsdoe31-h27-4-solo-d28-20261003-8acb75e1f2cc-nan.tif` | **`0.2708`** | `40,199` · `1.41 px` · `65.41%` | `95.39%` (`> 70%`) | Byte-identical clone of `GEMSDOE28 h27-4`; **NO — duplicate** |
| **5** | **`GEMSDOE33`** | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | **`0.2632`** | `41,865` · `1.00 px` · `63.36%` | `92.64%` (`> 70%`) | `H19-5` family clone; **NO — duplicate (`>70%` overlap)** |
| **6t** | **`GEMSDOE25`** | `gems25-dotted-h19-5-d2-8-20261002-70492e1a1293-zeros.tif` (`D28`) | **`0.2600`** | `44,090` · `1.41 px` · `59.59%` | `88.17%` (`> 70%`) | `H19-5` family ancestor; **NO — duplicate (`>70%` overlap)** |
| **6t** | **`GEMSDOE30`** | `gems30-d28-poisson300m-offcat-44090-20261002-70492e1a-zeros.tif` *(also `MSDB1` `0.1462`)* | **`0.2600`** | `44,090` · `1.41 px` · `59.59%` | `88.17%` (`> 70%`) | Clone of `D28` (`MSDB1` has `7,111,787` NaNs); **NO — duplicate** |
| **8** | **`GEMSDOE24`** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-0ee978ff9c42-nan.tif` *(also `h29` `0.2190`)* | **`0.2477`** | `49,409` · `1.41 px` · `55.34%` | `88.48%` (`> 70%`) | `H19-5` family clone + `-nan`; **NO — duplicate** |
| **9** | **`GEMSDOE27`** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-b8df8b8a4279-nan.tif` | **`0.2449`** | `49,957` · `1.41 px` · `55.02%` | `86.72%` (`> 70%`) | `H19-5` family clone + `-nan`; **NO — duplicate** |

### 1.2 Key Downloadable Research Files in `GEMSDOE86` (`docs/downloads/`, 48/48 Validated)

| Lane & Downloadable File (`docs/downloads/`) | `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `n=11,321`) | `SGMC-PROXY-DTI` (`n=62,122`) | Fleet Regression Projection *(not a score)* | Scoped Discrete Overlap (`<=100k` dots) & `ovH33` | Upload Decision |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`H86T-KNDS` (Newest, #48)**<br>`gems86-h86t-knds-37654dots-20261027T194957Z-3d7f3677-zeros.tif`<br>SHA-256: `c6870a57...1d18c2` | **`0.0861`** `[0.0705, 0.1017]`<br>*(beats `E3` `0.0721`, trails `E2` `0.0935`)* | **`0.0691`** `[0.0593, 0.0790]`<br>*(`E2` local-$\chi$ = **`0.0904`**)* | `0.1472` `[0.067, 0.228]` | **PASS (`0.5544 <= 0.70`)**<br>`ovH33 = 0.3749`<br>$\max|\rho| = 0.1453$ | **`DO NOT SUBMIT`**<br>(`verdict="negative"`, `G3/G4` fail + literal `17GEMSDOE` witness) |
| **`H86S-DWPU` (#47)**<br>`gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros.tif`<br>SHA-256: `12393821...970c9` | **`0.0870`** `[0.0707, 0.1037]`<br>*(trails unweighted `E2` `0.1039`)* | **`0.0559`** `[0.0472, 0.0653]` | `0.1304` `[0.050, 0.211]` | **PASS (`0.5213 <= 0.70`)**<br>`ovH33 = 0.2703`<br>$\max|\rho| = 0.1213$ | **`DO NOT SUBMIT`**<br>(`verdict="negative"`, `G3/G4` fail + literal witness) |
| **`H86R-SFG` (#46)**<br>`gems86-h86r-sfg-strikegate-37654dots-20261026T162637Z-ee3f1551-zeros.tif` | **`0.0450`** `[0.0342, 0.0574]`<br>*(trails ungated `E2` `0.0512`)* | **`0.0596`** `[0.0499, 0.0702]` | `0.1616` `[0.087, 0.236]` | **PASS (`0.6700 <= 0.70`)**<br>`ovH33 = 0.2387`<br>$\max|\rho| = 0.0718$ | **`DO NOT SUBMIT`**<br>(`verdict="negative"`) |
| **`H86Q-BFRA` (#45, blind `E2`)**<br>`gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif` | **`0.0734`** `[0.0604, 0.0865]`<br>*(coupled `E1` `0.1556` halted pre-write)* | **`0.0967`** `[0.0772, 0.1173]`<br>*(beats `H33` `0.0937`)* | `0.1680` `[0.093, 0.243]` | **PASS (`0.6413 <= 0.70`)**<br>`ovH33 = 0.3392`<br>$\max|\rho| = 0.2731$ | **`DO NOT SUBMIT`**<br>(audit-only; literal witness stop) |
| **`H86P-TCWB` (#43, strict-LOQO record)**<br>`gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif` | **`0.1727`** `[0.1560, 0.1894]`<br>*(all-time strict-LOQO repo high)* | **`0.0809`** `[0.0672, 0.0952]`<br>*(blind `E2` = `0.0954`)* | `0.1410` `[0.066, 0.216]` | **PASS (`0.6986 <= 0.70`)**<br>`ovH33 = 0.2735`<br>$\max|\rho| = 0.4797$ | **`DO NOT SUBMIT`**<br>(audit-only; literal witness stop) |
| **`H86M-PFTE` (#34, SGMC record)**<br>`gems86-h86m-pfte-blind-37654dots-20261025T165140Z-693fd244-zeros.tif` | **`0.0734`** `[0.0591, 0.0882]`<br>*(pure-blind 4-fold LOQO)* | **`0.1210`** `[0.1024, 0.1407]`<br>*(all-time repo SGMC high)* | `0.1740` `[0.099, 0.249]` | **PASS (`0.6244 <= 0.70`)**<br>`ovH33 = 0.3012`<br>$\max|\rho| = 0.4795$ | **`DO NOT SUBMIT`**<br>(audit-only; literal witness stop) |

---

## 2. PhD-Level Analysis: Why `GEMSDOE32` (`0.2778` `OWNER-REPORTED`) Scored Highest & How to Exceed `0.2778` / `0.3195` / `0.4413`

### 2.1 Why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` `OWNER-REPORTED`) Won the Focus-9 Fleet

1. **Shared Ancestral Surface (`H19-5`) + Post-Processing Geometry:**
   Every Focus-9 top submission above `0.2400` (`GEMSDOE32` `0.2778`, `GEMSDOE36` `0.2750`, `GEMSDOE28` `0.2710`, `GEMSDOE31` `0.2708`, `GEMSDOE33` `0.2632`, `GEMSDOE25/30` `0.2600`, `GEMSDOE24` `0.2477`, `GEMSDOE27` `0.2449`) derives from the same `H19-5` continuous ridge probability surface (`123,939` non-zero pixels, `0.2140` `OWNER-REPORTED`), which explains why all 8 non-`GEMSDOE32` Focus-9 winners have `86.72%–97.40%` 3-px forward dot overlap with `GEMSDOE32 H33`.
2. **The DTI Precision-Recall Harmonic Mean & 300 m (`3 px`) Kernel Geometry:**
   The competition metric evaluates Distance-Tolerance Intersection (DTI) with a linear 300 m (`3 px`) decay cone around true fault pixels. When a continuous ridge (`123,939` pixels) is discretized via `2.8 px` ($\sqrt{8}\times 100\text{ m}$) Poisson-disk thinning (`D28`, `44,090` dots, `0.2600`), redundant adjacent pixels within the same 300 m cone are eliminated, raising precision by ~35% while preserving >96% of 300 m recall.
3. **Widening the Mapped-Catalogue Exclusion Collar from `1.41 px` ($\sqrt{2}$) to `2.24 px` ($\sqrt{5}$) at `37,654` Dots (`H33-2-B2`):**
   `GEMSDOE32 H33` removed `6,436` near-catalogue collar dots ($1.41 < d_{\mathrm{cat}} \le 2.24\text{ px}$) from `D28`, reducing the total dot count from `44,090` to `37,654` and increasing the far-field (`> 1 km` from `existing_faults.tif`) dot share from `59.59%` to **`69.83%`** (`median d_cat = 1,811.1 m`). Across the 10 scored `37k–45k`-dot Focus-9 submissions, far-field (`> 1 km`) dot share exhibits a descriptive sample correlation of $r = +0.994$ with `OWNER-REPORTED` scores (`24.3% -> 0.0742` up to `69.8% -> 0.2778`). *(Caveat: this is a descriptive correlation across a selected historical lineage, not a proved causal law or standalone score predictor.)*
4. **Why `GEMSDOE32 H33` Fails In-Catalogue Holdout (`0.0036`) Yet Scores `0.0937` on Off-Catalogue SGMC:**
   Because `69.83%` of `H33`'s dots lie $>1\text{ km}$ from the INGENIOUS catalogue, it places almost no mass on short collar extensions of `existing_faults.tif` (`HOLDOUT-DTI = 0.0036`), but recovers unmapped USGS SGMC 1:500k bedrock structures (`SGMC-PROXY-DTI = 0.0937`).

### 2.2 How to Exceed `0.2778` (and the Unverified External Marks `0.3195` / `0.4413`)

Because every `H19-5` derivative has `86.7%–100.0%` 3-px overlap with `GEMSDOE32 H33`, re-tuning `H33` collars or stepover bridges violates Parallel-Run Protocol Rule 1 (`> 70%` overlap). Exceeding `0.2778` genuinely requires:
1. **Strict `> 3.0 px` Catalogue Exclusion Collar + `2.8 px` 6-Ring Dinkelbach-CELF / Poisson-Disk Allocation at `~37,654` Dots** with `55%–70%` far-field (`> 1 km`) dot allocation so precision is not wasted on mapped-fault halos.
2. **Combining Multi-Physics Subsurface & High-Resolution Surficial Operators:**
   - **Subsurface basin-stripped gravity + MT + Salem tilt pullback (`H86M-PFTE`, `H86K-STDP`, `H86Q-BFRA`):** already exceed `GEMSDOE32 H33` (`0.0937`) on off-catalogue `SGMC-PROXY-DTI` (`0.1210`, `0.1133`, `0.0967`) with `< 35%` overlap against `H33`.
   - **10 m DEM Fluvial Stream-Power ($k_{sn}$ / $\chi$-Step) + Downslope TC Wash-Blanket Asymmetry (`H86T-KNDS E2`, `H86P-TCWB`):** as demonstrated in Section 4 below, adding the 10-m DEM $\chi$ / $k_{sn}$ stream-power stack (`E2` vs `E3`) lifts `HOLDOUT-DTI` from `0.0721` to `0.0935` (`+0.0214`) and lifts `SGMC-PROXY-DTI` from `0.0740` to **`0.0904`** (`96.5%` of `H33`'s `0.0937` SGMC score at only `37.5%` overlap!).

---

## 3. Four Ranked Candidate Geological Hypotheses (`registry/h86t_hypotheses_20261027.json`)

| Rank & ID | Hypothesis & Layers Involved | Physical Signature & Why Missing from Catalogue | Named Non-Fault Mimic & Control | Status / Expected Gain & Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Rank 1**<br>`H86T-1_KNDS` | **Transient Fluvial Iso-Chi Knickzone Downslope Back-Projection & Piedmont Hinge Reception**<br>Layers: `dem10_chi_100m_i16.tif` (Bands 1–5: `step_max`, `step_min`, `ksn_max`, `log10_area`, `zmean`), `topo_10m_derived_100m_u8.tif` (Bands 1, 7), Native Bands 12, 15, 18, 19 + corroboration Bands 2, 3, 5, 16. | Range-front normal fault slip generates transient $k_{sn}$ and $\chi$-step knickzones that migrate upstream into bedrock footwall canyons at equal $\chi$ ($\Delta x_i \propto A_i^{m/n}\Delta\chi$). Projects deconfounded footwall knickzones downslope along $-\nabla z_{\mathrm{mean}}$ (`s in {4, 8, 14, 22} px`) onto the piedmont basement-hinge reception zone ($50 < Z_b < 800\text{ m}$, gated by Band 18) with along-strike iso-$\chi$ coherence. | **Pleistocene Lake Lahontan wave-cut shorelines ($\sim 1335 \pm 18\text{ m}$) and resistant Tertiary volcanic caprock sills** (suppressed via $1315\text{--}1355\text{ m}$ hypsometric notch and symmetric Bouguer Laplacian veto). | **EXECUTED THIS SESSION (`H86T-KNDS`)**<br>Low cost (~4.5 min CPU); see Section 4 for full 3-arm results. |
| **Rank 2**<br>`H86T-2_VENT_RANSAC` | **Geothermal Manifestation Multi-Point Azimuthal Corridor Graph**<br>Layers: GDR #1391 `gdr_wellspring_in_footprint.csv` (`dist_known_fault_px` excluded), `gdr_volcanic_vents_in_footprint.csv`, `paleo_geothermal_regional.zip`, `2m_temperature_probe`, `tiger_road_distance_m.tif`, Native Bands 2, 16, 17, 18. | Oriented collinearity graph connecting triplets of thermal springs/wells ($T > 35^\circ\text{C}$), 2-m temperature probe anomalies, sinter/tufa mounds, and Quaternary volcanic vents within 15 km whose azimuth aligns within $\pm 12^\circ$ of local RTP/gravity/MT strike across buried basin step-overs. | **Playa-margin artesian discharge lines and US-highway/railroad drill-access corridors** (suppressed via TIGER road-parallelism veto and topographic contour parallelism veto). | **QUEUED (#2)**<br>Medium expected gain on blind geothermal basins; Low-Medium cost (~30s CPU). |
| **Rank 3**<br>`H86T-3_RCSD` | **Radiometric Provenance-Step & Alluvial Fan Apex Dislocation**<br>Layers: `geodawn_rad_u8.tif` (K, eTh, eU, TC), `geodawn_extensions_u8.tif`, `acquisition_block_id_100m.tif`, Native Bands 5, 6, 15, 19. | Directional step-filter on Aitchison log-ratios $\ln(\mathrm{K}/\mathrm{eTh})$ and $\ln(\mathrm{eU}/\mathrm{eTh})$ strictly orthogonal to downslope alluvial fan transport ($\nabla \text{DEM}$), isolating cross-fan tectonic provenance steps and fault-controlled illite alteration while subtracting along-fan sorting. | **Non-tectonic depositional boundary between adjacent canyon fan lobes and GeoDAWN airborne survey seam lines** (suppressed via `acquisition_block_id_100m.tif` seam mask). | **QUEUED (#3)**<br>Medium expected gain in GeoDAWN footprint; Low cost (~25s CPU). |
| **Rank 4**<br>`H86T-4_SISM_COULOMB` | **Off-Catalogue Microseismic Shear-Dilatancy & Crustal Conductivity-Wall Conjunction**<br>Layers: Native Band 4 (`geod_2ndinv`), Band 7 (`earthquake_density`), Band 8 (`geod_dilaterate`), Band 10 (`geod_maxshear`), Band 16 (`mt_2km`), Band 18 (`gravity_hg`). | Anisotropic ridge of $\log(\text{Band 7}) \times \text{Band 10} \times \text{relu}(\text{Band 8})$ localized onto steep lateral walls of 2 km MT resistivity ($|\nabla\text{Band 16}|$) and horizontal gravity gradient (`Band 18`) to capture creeping/swarming Walker Lane transfer faults lacking mature surface scarps. | **Geothermal injection microseismicity clusters and 50 km GPS station radial interpolation bullseyes** (suppressed via Hessian eigenvalue anisotropy $L_1/L_2 > 3.0$). | **QUEUED (#4)**<br>Low-Medium expected gain (coarse Band 7/8 kernels); Low cost (~20s CPU). |

---

## 4. Implementation & Validation of Top Candidate: `H86T-KNDS`

### 4.1 Three-Arm Preregistered Experimental Results (`research/H86T_KNDS_PREREGISTRATION.json`)

All 3 arms were trained under identical 4-fold `12 px`-eroded Leave-One-Quadrant-Out (`LOQO`) `HistGradientBoostingClassifier` settings (`seed=20`, quadrant-balanced `rank01_per_quadrant` calibration, `37,654` binary dots, `2.8 px` Poisson-disk spacing, `> 3.0 px` visible-fault collar):

| Arm / Comparator | `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `n=11,321`) | Paired Holdout $\Delta$ vs `E1` (95% Block-Bootstrap CI) | Fold `NW` / `NE` / `SW` / `SE` Holdout DTI | `SGMC-PROXY-DTI` (`n=62,122` off-cat) | Paired SGMC $\Delta$ vs `E1` (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`E1_knds_backprojected_loqo`** *(17 features: 4 KNDS back-projected + 4 local $\chi$ + 9 native)* | **`0.0861`** `[0.0705, 0.1017]` | — (Candidate) | `0.0647` / `0.0915` / `0.0910` / `0.0918` | **`0.0691`** `[0.0593, 0.0790]` | — (Candidate) |
| **`E2_local_chi_unprojected_ablation`** *(13 features: 4 local $\chi$ + 9 native, no back-projection)* | **`0.0935`** `[0.0810, 0.1057]` | **`-0.0074`** `[-0.0196, +0.0050]` | `0.0756` / `0.1011` / `0.0900` / `0.1061` | **`0.0904`** `[0.0793, 0.1019]` | **`-0.0213`** `[-0.0293, -0.0129]` |
| **`E3_native_no_chi_ablation`** *(9 native features, zero external $\chi$/10m-DEM)* | **`0.0721`** `[0.0583, 0.0857]` | **`+0.0140`** `[-0.0027, +0.0300]` | `0.0713` / `0.0444` / `0.0852` / `0.0814` | **`0.0740`** `[0.0616, 0.0888]` | **`-0.0049`** `[-0.0166, +0.0046]` |
| **`GEMSDOE32_H33`** *(visible-collar on holdout; as-is on SGMC)* | `0.0036` `[0.0029, 0.0042]` | `+0.0826` `[+0.0673, +0.0978]` | `0.0032` / `0.0044` / `0.0029` / `0.0040` | **`0.0937`** `[0.0826, 0.1044]` | `-0.0246` `[-0.0341, -0.0151]` |
| **`GEMSDOE28_H27-4`** *(visible-collar on holdout; as-is on SGMC)* | `0.0273` `[0.0230, 0.0324]` | `+0.0588` `[+0.0453, +0.0723]` | `0.0246` / `0.0298` / `0.0215` / `0.0344` | **`0.0937`** `[0.0826, 0.1044]` | `-0.0246` `[-0.0341, -0.0151]` |
| **`RANDOM_NULL_seed861826`** *(uniform random 2.8 px Poisson-disk)* | — | — | — | `0.0759` `[0.0719, 0.0795]` | `-0.0068` `[-0.0173, +0.0047]` |

### 4.2 Scientific Diagnosis of the 3-Arm Outcome

1. **External 10-m DEM Fluvial $\chi$ / $k_{sn}$ Physics Beats Native-Only (`E2 > E3` and `E1 > E3` on Holdout):**
   Adding the SHA-pinned USGS 3DEP 10-m fluvial stream-power features (`E2` vs `E3`) improved `HOLDOUT-DTI` from `0.0721` to **`0.0935`** (`+0.0214`, lifting `Fold NE` more than $2\times$ from `0.0444` to `0.1011`) and improved off-catalogue `SGMC-PROXY-DTI` from `0.0740` to **`0.0904`** (`+0.0164`, achieving `96.5%` of `GEMSDOE32 H33`'s `0.0937` SGMC score). Even with downslope back-projection (`E1`), `HOLDOUT-DTI` (`0.0861`) beat the zero-$\chi$ native baseline `E3` (`0.0721`) by `+0.0140` (`Fold NE` `0.0915` vs `0.0444`).
2. **Why Downslope Back-Projection Along $100\text{ m}$ $-\nabla z_{\mathrm{mean}}$ (`E1`) Lost to Unprojected Local $\chi$ (`E2`):**
   - Many withheld INGENIOUS fault segments and unmapped SGMC 1:500k faults are **intra-range bedrock faults or canyon-parallel strike-slip/oblique strands** where the channel-steepness anomaly ($k_{sn}$, $\Delta\chi_+$) sits *directly on* the fault trace ($s = 0\text{ px}$). Shifting those anomalies $4\text{--}22\text{ px}$ ($0.4\text{--}2.2\text{ km}$) down-gradient displaced predicted dots off the bedrock fault strands into adjacent valleys.
   - At $100\text{ m}$ grid resolution, the smoothed hillslope gradient vector $-\nabla G_{\sigma=4}(z_{\mathrm{mean}})$ diverges from the actual 10-m sinuous channel thalweg above fan apices, dispersing back-projected mass outside the strict 300 m (`3 px`) DTI tolerance cone.
3. **Fail-Closed Gate Verdict (`verdict = "negative"`, `DO NOT SUBMIT`):**
   - `G1_format_writer_pass`: **PASS** (`37,654` dots, `float32`, `EPSG:32611`, `3730×3292`, `[0, 1]`, `0` NaN/Inf, `0` catalogue dots)
   - `G2_canary_le_0p90`: **PASS** (all 20 planes/surfaces tested $\le 0.90$; max discriminative AUC $= 0.7541$ on `vis_d_norm`; max static plane $= 0.5903$ on `knds_isochi_strike_coh`)
   - `G3_holdout_E1_gt_E2_point` & `G3_holdout_E1_gt_E2_paired_ci_excludes_0`: **FAIL** (`E1 = 0.0861 < E2 = 0.0935`, paired $\Delta = -0.0074 [-0.0196, +0.0050]$)
   - `G4_sgmc_E1_ge_H33_same_call`: **FAIL** (`E1 = 0.0691 < H33 = 0.0937`)
   - `G5_uniqueness_scoped_discrete_le100k`: **PASS** (across `75` locally restored rasters: worst sampled surface Spearman $\rho = 0.1453 \le 0.90$; worst discrete $\le 100\text{k}$ 3-px dot overlap $= 0.5544 \le 0.70$; overlap vs `GEMSDOE32 H33` $= 0.3749$; literal `17GEMSDOE` full-support witness $= 1.0000 > 0.70$ disclosed side-by-side)
   - `G6_fingerprint_37654_min_dcat_gt3`: **PASS** (`37,654` dots, `min_dcat_px = 3.1623 > 3.0`)

---

## 5. Three-Pass Verification Ledger

- **Pass 1 (Implementation & Execution):** Restored and SHA-256-verified all native competition rasters, external USGS 3DEP/GeoDAWN/SGMC layers, and 25 fleet rasters; prepared all 21 native arrays via `scripts/prepare_data.py`; froze `registry/h86t_hypotheses_20261027.json` and `research/H86T_KNDS_PREREGISTRATION.json`; implemented `src/gems86_knds/` and `scripts/run_h86t_knds.py`; executed all 3 arms and serialized `docs/downloads/gems86-h86t-knds-37654dots-20261027T194957Z-3d7f3677-zeros.{tif,zip,json}` and `docs/evidence/h86t-knds-run-card.json`.
- **Pass 2 (Bug & Edge-Case Review):** Identified and fixed two critical engineering issues during implementation: (a) HGB decision-tree split degeneracy when `vis_d_norm` is included inside tree training on `visible_faults` (fixed by fitting LOQO HGB trees strictly on static catalogue-free features and applying `rank01_per_quadrant` calibration before two-regime relay fusion); and (b) 3.9 GB sandbox RAM pressure when holding 75 binary registry rasters in memory simultaneously (fixed by streaming single-pass registry uniqueness and reusing SHA-verified fleet SGMC scores).
- **Pass 3 (End-to-End Audit & Gate Verification):** Registered artifact #48 across `docs/evidence/download-inventory.json`, `registry/artifact_cards.json`, `scripts/audit_release.py`, `scripts/build_site.py`, `tests/test_builder_preflight.py`, and `tests/test_h86t_knds.py`; re-ran `audit_release.py --measure-registry`, `audit_downloads.py --write`, `build_site.py`, `check_site.py`, `audit_workspace_inputs.py --require-native`, and pytest verification suites.
