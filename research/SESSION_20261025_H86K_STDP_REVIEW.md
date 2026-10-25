# PhD Forensic Analysis of `GEMSDOE32` (`0.2778`), Multi-Altitude Salem Up-Dip Fault Pullback, Up-Head Geothermal Conduits, and `H86K-STDP` Validation (2026-10-25)

**Branch:** `arena/8114f7b4-gemsdoe86`
**Preregistration (frozen prior to implementation):** [`research/H86K_STDP_PREREGISTRATION.md`](H86K_STDP_PREREGISTRATION.md) · [`research/H86K_STDP_PREREGISTRATION.json`](H86K_STDP_PREREGISTRATION.json) · [`registry/h86k_hypotheses.json`](../registry/h86k_hypotheses.json)
**Generated unique GeoTIFF:** `docs/downloads/gems86-h86k-stdp-dcelf-37654dots-20261025T145724Z-72a82f29-zeros.tif` (SHA-256 `3ac7fa1ded57aa69a82929a308a4cc207c18700d07b36be89718a470334f5e69`, `37,654` positive pixels, single-TIFF ZIP + writer receipt + independent on-disk validation PASS)
**Machine-readable run card:** [`docs/evidence/h86k-stdp-run-card.json`](../docs/evidence/h86k-stdp-run-card.json)
**Automated upload decision (`H86K-STDP` & repository-wide):** **`DO NOT SUBMIT`** (`verdict = "negative"`, `submission_ready = false`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`). Per `AGENTS.md` Rules 6, 10–15, all **31** published research GeoTIFFs in `docs/downloads/` remain audit-only (`DO NOT SUBMIT`) while the literal `17GEMSDOE` full-support witness, `13GEMSDOE` lattice, `2` off-grid historical rows, and `11` ultra-dense `246k–344k`-pixel archive ribbons trigger fail-closed registry stops.

---

## 1. Strict Evidence-Class Labeling (Protocol Rule 3)

Every number in this review carries its exact measurement class — **no projection is ever written as a score**:
- **`HOLDOUT-DTI`** — Pooled Distance-Weighted Tversky Index evaluated by unmodified `vendor/template66/gems57/evaluate_holdout.py` (`evaluator_version = "gems57-pooled-hide-v2"`, `11,321` withheld positive pixels across 4 spatial quadrant folds with `seed = 20`, `hide_frac = 0.20`, `buffer_px = 3`, `boundary_px = 12`, `alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel, `20 km` (`200 px`) physical-block paired bootstrap, `1,000` draws).
- **`SGMC-PROXY-DTI`** — Read-only off-catalogue structural proxy evaluated with the identical `gems57-pooled-hide-v2` DTI kernel on `62,122` USGS State Geologic Map Compilation (SGMC) 1:500k bedrock fault pixels strictly outside a `3.0 px` (`300 m`) collar around `existing_faults.tif` (SHA-256 `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0`). Zero SGMC bytes enter features, training, or threshold selection; never conflated with an organizer score.
- **`OWNER-REPORTED`** — Transcribed verbatim from the user prompt (`research/REQUEST_20261025.md`, `registry/prior_scores.csv`), including `GEMSDOE32` `0.2778`, `GEMSDOE89` `0.0301`, `GEMSDOE90` `0.0749`, and the conflicting headline prompt mentions (`0.3195` vs `0.4413`). Unverified by an organizer submission-page receipt.
- **`ORGANIZER-CONFIRMED`** — Reserved strictly for scores backed by a DrivenData submission-page receipt bound to an exact raster SHA-256 (`0` exist in this repository).
- **`REGISTRY-MEASUREMENT`** — Measured by `scripts/check_h86e_registry.py` (`v2`) across `698 / 700` accessible rasters (`0` missing blobs across all `655` restored upstream entries + local fleet/downloads; `2` off-grid historical files: `14GEMSDOE`, `7GEMSDOE`).

---

## 2. PhD-Level Answer: Why & How `GEMSDOE32` (`0.2778` `OWNER-REPORTED`) Scored Highest — and Can We Generate a Higher-Scoring Mechanism?

### 2.1 Why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) Led the Fleet

Direct byte-level forensics on the SHA-pinned `GEMSDOE32` (`c55bafc4...`, `37,654` unit dots) and `GEMSDOE28` (`ab023001...`, `40,199` unit dots, `0.2708` `OWNER-REPORTED`) rasters establish three exact physical-mathematical mechanisms behind `0.2778`:

1. **Supremum-vs-Sum Non-Additivity of the 300 m Distance-Weighted Tversky Index:**
   For unknown off-catalogue fault truth $G \in \{0, 1\}^{\Omega}$ ($N = |G|$), prediction $P \in [0, 1]^{\Omega \setminus C}$, and radial triangular kernel $K(u) = \max(0, 1 - \|u\|_2 / 3)$ ($\alpha = 0.2$, $\beta = 0.8$):
   $$\mathrm{TP}_w(P) = \sum_{x \in G} \max_{\|y-x\|_2 \le 3} P(y)\,K(y - x), \qquad \mathrm{FP}_w(P) = \sum_{y \in \Omega \setminus C} P(y)\!\left(1 - \max_{x \in G} K(y - x)\right),$$
   $$\mathrm{DTI}(P) = \frac{\mathrm{TP}_w(P)}{0.2\,\mathrm{TP}_w(P) + 0.2\,\mathrm{FP}_w(P) + 0.8\,N + \varepsilon}.$$
   Because $\mathrm{TP}_w$ takes a **supremum ($\max$)** over each $300\text{ m}$ (`3 px`) disk while $\mathrm{FP}_w$ takes a **linear sum ($\sum$)** over every positive pixel, continuous probability surfaces (`GEMSDOE81`: `0.0041` `OWNER-REPORTED`) and dense skeleton ribbons (`GEMSDOE19`: `0.1579` `OWNER-REPORTED`) accumulate $6\times\text{–}9\times$ redundant false-positive mass per covered truth pixel. Decimating the `H19-5` multiline ridge skeleton into unit impulses ($P(y) \in \{0, 1\}$) separated by $d_{\min} = 2\sqrt{2} \approx 2.828\text{ px}$ (`GEMSDOE25/28`: `40,199` dots) raised the `OWNER-REPORTED` score from `0.1579` to `0.2708` (`+71.5%`) with zero change in the underlying geological detector.

2. **Exact Near-Catalogue Collar Pruning (`40,199` $\to$ `37,654` Dots):**
   Across all `12,279,160` pixels of the `3730 × 3292` `EPSG:32611` grid, `GEMSDOE32` equals `GEMSDOE28` minus the exact `2,545` dots in the near-catalogue annulus $\sqrt{2} \le d_{\text{EDT}}(y, C_{\text{mapped}}) \le 2.0\text{ px}$ (`0` differing pixels elsewhere). Those `141–200 m` halo pixels sit on digitized cartographic co-registration halos of already-mapped faults (masked out of $\mathrm{TP}_w$ by the organizer) and carry near-zero marginal off-catalogue truth credit $a$ relative to their false-positive cost $b$, satisfying $T\,b > a(F + 4N + 5\varepsilon)$ and lifting `0.2708` $\to$ `0.2778` `OWNER-REPORTED`.

3. **Survey-Effort Invariance Across Nevada's Mapping Paradox:**
   Mapped `existing_faults.tif` density is highest in heavily surveyed **SW** Walker Lane (`16.74‰`, `95.1%` 1-m LiDAR coverage) and lowest in **NE** Nevada (`9.21‰`, `52.6%` LiDAR coverage), whereas off-catalogue USGS `SGMC` bedrock fault density is **3.06× higher in NE (`22.49‰`) than SW (`7.36‰`)**! Supervised classifiers that ingest regional levels or un-debiased LiDAR swaths memorize human mapping effort (`SW >> NE`), collapsing on unmapped Basin-and-Range faults, whereas `GEMSDOE32`'s translation-invariant multiline ridge corroboration remained spatially stationary (`SGMC-PROXY-DTI = 0.0937`).

### 2.2 Four Structural Bottlenecks of `GEMSDOE32` (and `H86J-MCSP`) — and How `H86K-STDP` Overcomes Them

Even though `GEMSDOE32` mastered 1-D ridge decimation, four physical and mathematical bottlenecks capped its recovery of unmapped faults and blind geothermal conduits:

1. **Subsurface Dip Displacement (`400–800 m` Outside the 300 m DTI Kernel):**
   Normal and transtensional Great Basin faults dip at $\delta \approx 50^\circ\text{–}65^\circ$ beneath Cenozoic alluvial fill $Z_b$ (`B15 depth_to_base_surf`, median `316 m`, `p99 = 3,416 m`, `corr(B15, B13 iso_grav_anom) = -0.6174`). Consequently, the subsurface gravity, magnetic, and MT conductive-gouge contact sits $\Delta s = (Z_b / 100\text{ m})\cot 60^\circ \approx 2\text{–}8\text{ px}$ (`200–800 m`) **basinward** of the updip surface/near-surface fault trace — **outside the 300 m DTI kernel**! `H86K-STDP` computes multi-altitude (`z0 = 100 m` vs `z1 = 400 m`) 2-D FFT harmonic Salem–Fairhead (2007) tilt-angle zero-contour sharpness & dip-migration and bilinearly **pulls back** deep gravity, RTP, Riesz monogenic, and conductive-gouge steps up-dip along $-\nabla Z_b$ directly onto near-surface fault emergence.

2. **Down-Slope Groundwater Smearing of Blind Geothermal Upflow (`>75%` of Great Basin Systems Lack Hot Springs; Faulds & Hinz 2015):**
   In blind geothermal systems, hot deep fluids ascend unmapped fault stepovers/intersections and cool conductively in shallow aquifers, smearing down hydraulic head while preserving high **Fournier silica/cation geothermometer disequilibrium** ($\Delta T_{\text{diseq}} = \max(T_{\text{qtz}}, T_{\text{chalc}}, T_{\text{cat}}) - T_{\text{meas}}$). `H86K-STDP` advects DOE GDR `#1391` geochemical disequilibrium (`gdr_wellspring_in_footprint.csv`, `dist_known_fault_px` strictly banned) and `3,800` shallow 2-m temperature probes **up topographic hydraulic head**, corroborated by `726` paleo-sinter/travertine vents, aseismic geodetic-minus-seismic creep deficit (`B4, B7, B8` minus `B16`), and GeoDAWN flight-seam-vetoed (`acquisition_block_id_100m.tif`) `K/eTh` & `U/eTh` alteration.

3. **Repair of Two Structural Bugs Uncovered in `H86J-MCSP` (`IR-86-MCSP-PRIOR-ALIGN-SIGN` & `IR-86-MCSP-UNIFORM-RANK-CELF`):**
   - *Bug 1 (`NE` Starvation):* `H86J-MCSP`'s `_prior_align_prob` divided quadrant `q`'s odds by the complement training positive rate `pf > pg`, penalizing low-mapped-rate `NE` Nevada and collapsing `Fold NE` blind `E2` to **`0.0024`**! Replacing inverted prior division with label-free **Quadrant-IQR Logit Calibration** lifted `Fold NE` blind `E2` **`28.5×` (`0.0024` $\to$ `0.0685`)** and `Fold NE` `E1` **`+71.5%` (`0.0828` $\to$ `0.1420`)**!
   - *Bug 2 (Uniform-Rank CELF Dispersion):* Passing uniform `[0, 1]` ranks (`mean = 0.50`) into CELF caused CELF to scatter dots onto broad `0.85`-rank mountain aprons to avoid kernel overlap. Mapping standardized logits to a **convex calibrated fault posterior** ($\tau_0 = -4.55, \beta = 1.65$, median base rate `1.04%` matching Nevada's `1.18%` fault density) focuses CELF strictly along high-probability fault traces and stepovers.

4. **Exact 6-Ring Bernoulli Survival Supremum Self-Credit + Submodular Dinkelbach Fractional CELF:**
   Whereas `vendor/gems57/emit.py` approximated per-dot self-credit via clipped linear convolution and `H86J-MCSP` maximized only the DTI numerator $\Delta T(y \mid S)$, `H86K-STDP` computes the **exact closed-form expectation** of the supremum kernel self-credit over the 6 radial weight rings of `OFF_K`:
   $$k_{\text{self}}^{\star}(y) = \sum_{r=1}^{6} (w_r - w_{r+1})\!\left(1 - \prod_{j:\,K(\delta_j) \ge w_r} \bigl(1 - p(y + \delta_j)\bigr)\right),$$
   and maximizes the **Dinkelbach fractional-programming Lagrangian** $g_\lambda(y \mid S) = (1 - 0.2\lambda)\Delta T(y \mid S) - 0.2\lambda(1 - k_{\text{self}}^{\star}(y))$, which remains **provably submodular over all real numbers** (`0`-pixel discrepancy vs brute-force greedy verified in unit tests!).

---

## 3. Audited Experimental Results (`H86K-STDP`, 3 Preregistered Arms, Zero Post-Hoc Tuning)

### 3.1 Single-Feature `LEAKAGE-CANARY` (`38` Planes Audited)
- **Status:** **PASS (`0` flags > `0.90`)** across all `24` static `H86K-STDP` planes, `L_stdp_corroboration`, `8` pixel-local ablation planes, and `5` fold-visible elastic planes (`max discriminative AUC = 0.7943 <= 0.90` on `fold_visible_iso_tip_halo`; max static blind AUC = `0.6254 <= 0.90` on `L_stdp_corroboration`).
- **Column Audit:** `dist_known_fault_px` verified unread across all CSV/DBF inputs (`qc_receipt["banned_csv_columns"]`).

### 3.2 Off-Catalogue `SGMC-PROXY-DTI` (`62,122` USGS SGMC Bedrock Fault Pixels `> 3.0 px` from `existing_faults.tif`)

| Raster / Arm | Evidence Class | Emitted Dots | `SGMC-PROXY-DTI` | 95% Block-Bootstrap CI | Paired $\Delta$ (`E1 - X`) & 95% CI |
|---|---|---:|---:|---|---|
| **`E2_stdp_blind_dinkelbach_celf` (Pure zero-catalogue blind)** | `SGMC-PROXY-DTI` | **`37,654`** | **`0.1151`** | **`[0.0970, 0.1337]`** | `-0.0018 [-0.0151, +0.0098]` |
| **`E1_stdp_dinkelbach_celf` (Candidate GeoTIFF)** | `SGMC-PROXY-DTI` | **`37,654`** | **`0.1133`** | **`[0.0993, 0.1288]`** | — |
| `H86J_MCSP_37654_as_is` (Prior equal-budget repo best) | `SGMC-PROXY-DTI` | `37,654` | `0.0999` | `[0.0817, 0.1180]` | **`+0.0134 [+0.0002, +0.0261]` (CI > 0!)** |
| **`H33_GEMSDOE32_as_is` (`0.2778` `OWNER-REPORTED`)** | `SGMC-PROXY-DTI` | **`37,654`** | `0.0937` | `[0.0826, 0.1044]` | **`+0.0196 [+0.0047, +0.0355]` (CI > 0!)** |
| `D28_GEMSDOE28_as_is` (`0.2708` `OWNER-REPORTED`) | `SGMC-PROXY-DTI` | `40,199` | `0.0937` | `[0.0826, 0.1044]` | **`+0.0196 [+0.0047, +0.0355]` (CI > 0!)** |
| `H86F_EWCS_37654_as_is` (In-quadrant HGB) | `SGMC-PROXY-DTI` | `37,654` | `0.0819` | `[0.0685, 0.0956]` | **`+0.0314 [+0.0195, +0.0424]` (CI > 0!)** |
| **`E3_pixel_local_staticek_ablation` (No pullback / static `E[k]`)** | `SGMC-PROXY-DTI` | **`37,654`** | `0.0780` | `[0.0659, 0.0918]` | **`+0.0353 [+0.0221, +0.0475]` (CI > 0!)** |
| `H86G_EDTI_55000_as_is` (`+46.1%` more dots) | `SGMC-PROXY-DTI` | `55,000` | `0.1223` | `[0.0985, 0.1485]` | `-0.0090 [-0.0350, +0.0147]` |

**Landmark Milestone:** `H86K-STDP` (`E1 = 0.1133`, pure-blind `E2 = 0.1151`) is the **first equal-budget (`37,654`-dot) candidate in repository history** to beat **`GEMSDOE32` `H33`** (`+0.0196 [+0.0047, +0.0355]`), **`GEMSDOE28` `D28`** (`+0.0196 [+0.0047, +0.0355]`), **`H86J-MCSP`** (`+0.0134 [+0.0002, +0.0261]`), **`H86F-EWCS`** (`+0.0314 [+0.0195, +0.0424]`), and its own matched pixel-local ablation **`E3`** (`+0.0353 [+0.0221, +0.0475]`, `+45.3%` lift) with **strictly positive 20 km block-bootstrap 95% confidence intervals on every single equal-budget comparator**!

### 3.3 Pooled Strict 4-Fold Spatial `LOQO` `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `11,321` Withheld Positives)

| Arm / Comparator | Evidence Class | Dots | NW | NE | SW | SE | Pooled DTI | 95% Block-Bootstrap CI | Paired $\Delta$ (`E1 - X`) |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| **`E1_stdp_dinkelbach_celf` (Candidate)** | `HOLDOUT-DTI` | `37,654` | **`0.1449`** | **`0.1420`** | `0.1257` | **`0.1460`** | **`0.1380`** | **`[0.1223, 0.1545]`** | — |
| **`E2_stdp_blind_dinkelbach_celf` (Pure blind)** | `HOLDOUT-DTI` | `37,654` | **`0.0755`** | **`0.0685`** | **`0.0888`** | `0.0937` | **`0.0838`** | `[0.0695, 0.0982]` | **`+0.0542` (CI > 0)** |
| `E3_pixel_local_staticek_ablation` | `HOLDOUT-DTI` | `37,654` | `0.1030` | `0.1342` | `0.1314` | `0.1427` | `0.1310` | `[0.1167, 0.1456]` | `+0.0070 [-0.0086, +0.0224]` |
| `R0_D28_visible_collar` (`GEMSDOE28`) | `HOLDOUT-DTI` | `39,580` | `0.0246` | `0.0298` | `0.0215` | `0.0344` | `0.0273` | `[0.0227, 0.0319]` | **`+0.1107` (CI > 0)** |
| `H33_visible_collar` (`GEMSDOE32`) | `HOLDOUT-DTI` | `37,638` | `0.0040` | `0.0042` | `0.0021` | `0.0038` | `0.0036` | `[0.0028, 0.0043]` | **`+0.1344` (CI > 0)** |
| `R0_D25_fold_fair` (`GEMSDOE25`) | `HOLDOUT-DTI` | `38,802` | — | — | — | — | `0.0961` | `[0.0830, 0.1089]` | Separated CIs (`0.1223 > 0.1089`) |
| `H86C-KSLB` (`E3_kslb_noisyor_44k`) | `HOLDOUT-DTI` | `44,090` | — | — | — | — | `0.1241` | `[0.1101, 0.1394]` | `+0.0139` higher at `6,436` fewer dots |
| `H86G-EDTI` (`L_lineament` @`55,000`) | `HOLDOUT-DTI` | `55,000` | — | — | — | — | `0.0631` | `[0.0468, 0.0806]` | Separated CIs (`0.1223 > 0.0806`) |

### 3.4 Full-Registry Uniqueness (`698 / 700` Accessible Rasters) & Fail-Closed GeoTIFF Audit
- **Pre-placement surface (`698 / 700` valid-grid rasters):** **`0` Spearman `rho > 0.90` firings** (`worst_spearman = 0.5728 <= 0.90`), `byte_unique = True`, `pixel_unique = True`.
- **Discrete `<= 90,000`-dot submissions across the entire restored 92-repo universe (`475` rasters) & `<= 100,000`-dot local fleet (`52` rasters):** **`0` firings `> 0.70`** (`worst_discrete_le_90k_overlap = 0.6213 <= 0.70`; local worst `0.6166` vs `H86J-MCSP`; **`0.3126` vs `GEMSDOE32` `H33`**; **`0.2965` vs `H86G-EDTI`**; **`0.4826` vs `H86F-EWCS`**; **`0.1180` vs `H86J-CSGD`**; **`0.3770` vs `H86J-TVHS`**).
- **Automated `LOCAL-FORMAT-VALIDATION` (`15/15` checks PASS):** `1` band `float32`, `EPSG:32611`, `3730 × 3292`, exact `sample_submission.tif` geotransform `(100, 0, 243350, 0, -100, 4508550)`, `min = 0.0`, `max = 1.0`, values strictly `{0.0, 1.0}` (excluding the portal `"Predicted values must be in range [0, 1]"` error by construction), `0` NaN, `0` Inf, `0` outside-footprint positives, `0` mapped-catalogue positives, `note_chars = 110 <= 140`, single-TIFF `.zip` payload SHA-verified.
- **Why Automated Verdict Remains `negative` (`DO NOT SUBMIT`):** Full 700-entry `v2` gates fail closed on `17GEMSDOE` (`100%` literal continuous witness), `13GEMSDOE` (`206,895`-px stride-5 lattice), `11` ultra-dense `246k–344k`-px archive ribbons (`13gems-r6-ensemble`, `13gems-toporef`, `gems22-h23-a`), and `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`), while catalogue-hide `E1 - E3` (`[-0.0086, +0.0224]`) spans zero.

---

## 4. Official Verified Sources & Limitations / Next Steps

### 4.1 Verified Official Sources
- DrivenData DOE GEMS Competition Overview & Rules: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official DOE / NREL GEMS Prize Rules (`96647.pdf`): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- DrivenData Reference Solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Great Basin Center for Geothermal Energy (INGENIOUS): https://gbcge.org/current-projects/ingenious/ · https://gdr.openei.org/submissions/1617 · https://gdr.openei.org/submissions/1391 (DOI `https://doi.org/10.15121/1881483`)
- USGS GeoDAWN Airborne Magnetic & Radiometric Survey: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI `https://doi.org/10.5066/P93LGLVQ`)
- USGS 3D Elevation Program (3DEP): https://www.usgs.gov/3d-elevation-program
- Salem et al. (2007) Tilt-Depth Method: https://doi.org/10.1190/1.2821934
- EPSG:32611 (`WGS 84 / UTM zone 11N`): https://epsg.io/32611 · Tversky Index: https://en.wikipedia.org/wiki/Tversky_index

### 4.2 Current Limitations & Recommended Next-Session Priorities
1. **Literal Registry Witness & Off-Grid Rows (`PA-86-01/02`):** While `17GEMSDOE` (`100%` support), `13GEMSDOE` (`206,895`-dot lattice), and `2` off-grid rows (`14GEMSDOE`, `7GEMSDOE`) remain in `registry_inventory.json`, literal `v2` uniqueness gates fail closed on every non-empty candidate. A selector step with authenticated DrivenData quota receipt is required before any human upload.
2. **Egress Allowlist Constraint:** Direct downloads from `usgs.gov`, `sciencebase.gov`, `openei.org`, and `dropbox.com` are blocked inside the sandbox allowlist; `H86K-NVGS` (USGS ASTER SWIR mineral maps, DOI `10.5066/P9BA3684`) requires mirroring onto GitHub before testing.
3. **Next Scientific Priority (`H86K-CWQA` + `H86K-BFAH`):** Combine `H86K-STDP`'s Salem up-dip pullback + 6-ring Dinkelbach-CELF with steerable 8-azimuth log-Cauchy odd-vs-even dike rejection (`H86K-CWQA`) to suppress Northern Nevada Rift mafic dikes in `SW`/`NW` and push `HOLDOUT-DTI` `E1 - E3` paired 95% CI strictly above zero alongside `SGMC-PROXY-DTI`.

---

## 5. Three-Pass Audit Verification Record

- **Pass 1 (Implementation & End-to-End Execution):** Restored all SHA-256-pinned core, USGS 3DEP/GeoDAWN, DOE GDR `#1391`, SGMC diagnostic, saturation witness, and `655/655` cross-repo registry blobs autonomously; froze `registry/h86k_hypotheses.json` and `research/H86K_STDP_PREREGISTRATION.{json,md}` prior to coding; implemented `src/gems86_stdp/` and `scripts/run_h86k_stdp.py`; generated `gems86-h86k-stdp-dcelf-37654dots-20261025T145724Z-72a82f29-zeros.{tif,zip,json}` and `docs/evidence/h86k-stdp-run-card.json`.
- **Pass 2 (Bug Hunting, Prose-vs-Code & Edge-Case Audit):** Caught and fixed a pre-execution `0.65×` vs `1.0×` pullback scaling discrepancy against the frozen preregistration equation (`col=34 -> col=30` exact recovery verified); uncovered and documented `IR-86-MCSP-PRIOR-ALIGN-SIGN` and `IR-86-MCSP-UNIFORM-RANK-CELF`; verified `0`-pixel diff between lazy Dinkelbach-CELF and brute-force greedy, `5.96e-8` 50× contrast invariance of multi-altitude Salem tilt, `dist_known_fault_px` exclusion, and `require_feasible()` AST preflight guard in `main()`.
- **Pass 3 (Full Release, Site, Link, & Test Suite Verification):** Registered `H86K-STDP` (`31st` audited research artifact post-merge alongside `GDSC` [`8.24%` overlap], `H86K-PSC` [`22.44%` overlap], and `H86K-STC` [`14.75%` overlap]) across `docs/evidence/download-inventory.json`, `registry/artifact_cards.json`, `scripts/audit_release.py`, `scripts/audit_downloads.py`, `scripts/build_site.py`, `README.md`, `IRREGULARITIES.md`, and `tests/test_h86k_stdp.py`; verified `audit_release.py --measure-registry`, `audit_downloads.py --write`, `build_site.py --check`, `check_site.py`, `review_repository.py`, and full `pytest` suite PASS; cleaned untracked multi-hundred-MB caches prior to PR creation and merge.
