# PhD Scientific Review, Hypothesis Ranking, and Experimental Audit (`H86-WVB`)

- **Audit Date:** 2026-10-22 UTC
- **Active Lane:** `H86-WVB` (*Depth-Matched Potential-Field Local-Wavenumber & Geothermometric Fault-Valve Bridge*)
- **Primary Deliverable:** `docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif` (`SHA-256: d0231888c4567816d706cca360c8fe0cd98fc0b673409edb3ffc5649e3d1bdf3`)
- **Automated Verdict:** **`negative` (`🔴 DO NOT SUBMIT TO WEEKLY PORTAL SLOT`)** — Passed Gate 1 (`15/15` format + `[0, 1]`), Gate 2 (`36/36` leakage canaries `<= 0.90`), and Gate 3 (`+56.5%` buffered `HOLDOUT-DTI` over `d2.8`), and passed 3-px dot overlap against **30/30 modern sibling champions (`GEMSDOE32..GEMSDOE88`, max `0.6353 <= 0.70`)**, but exceeded `0.70` forward 3-px overlap on **2 historical `gems10` catalogue-context ridge priors** (`gems10-h25-ctx-ridge = 0.78531`, `gems10-h28-dotted-ridge = 0.74146`) plus the regular 5x5 covering lattice (`0.99644`).

> **Scope discipline:** The competition target is subsurface and concealed fault prediction relevant to geothermal exploration across the northwestern Great Basin (`EPSG:32611`, `3730 x 3292` at `100 m`), not direct confirmation of an economic geothermal reservoir. Every holdout figure in this document is explicitly tagged `HOLDOUT-DTI` with its evaluator version, withheld positive pixel count, and 20 km spatial-block bootstrap 95% confidence interval. No live portal score is tagged `ORGANIZER-CONFIRMED` because no DrivenData submission-page HTML/screenshot receipt is committed in git.

---

## 1. Forensic Analysis: Why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, Owner-Reported `0.2778`) Achieved the Top Score Among Listed GEMSDOE Sites

### 1.1 Exact Official Metric Mechanics (`vendor/gems57/metric.py`)
The GEMS competition scores single-band probability rasters $p(x) \in [0, 1]$ on active footprint cells $\mathcal{F}$ (`9,151,277` valid `100 m` cells) against withheld off-catalogue fault pixels $Y^\star = \{y : q(y) = 1\}$ using pooled **Distance-Tolerant Tversky / IoU** with $\alpha = 0.2$, $\beta = 0.8$, and linear triangular kernel $k(d) = \max(0, 1 - d / R)$ at $R = 300\text{ m} = 3\text{ px}$:

$$\text{DTI}(p, q) = \frac{\text{TP}_w}{\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w}$$

where:
- $\text{TP}_w = \sum_{y \in Y^\star} s_p(y)$ and $\text{FN}_w = |Y^\star| - \text{TP}_w$, with **pointwise supremum** truth coverage $s_p(y) = \max_{x:\,\|x-y\|_2 \le 3\text{ px}} p(x)\,k(\|x-y\|_2)$.
- $\text{FP}_w = \sum_{x \in \mathcal{F}} p(x)\,(1 - s_q(x))$, with $s_q(x) = \max_{y \in Y^\star:\,\|x-y\|_2 \le 3\text{ px}} k(\|x-y\|_2)$.

This creates a **fundamental structural asymmetry** between numerator and denominator:
1. **Submodular / saturating numerator (`max` operator):** Along a 1-px fault trace, a single binary dot $p(x_0) = 1$ already credits $y = x_0$ with `1.000`, its two 1-px neighbors with `0.667` each, and its two 2-px neighbors with `0.333` each (`3.00` weighted truth pixel equivalents per isolated hit). Placing continuous 1-px ridge pixels (`p = 1` at every step) adds almost nothing once dots are spaced every $d \approx 2.8\text{ px}$ (`280 m`), while 2D probability blobs (`>1 px` wide) add **zero** additional along-strike coverage.
2. **Strictly modular / additive false-positive penalty (`sum` operator):** Every off-fault pixel emitted with $p(x) = 1$ outside $3\text{ px}$ of $Y^\star$ adds a full $+0.2$ penalty to the denominator.
3. **Zero-reward known-catalogue collar (DrivenData forum thread `11516`):** Organizers confirmed that mapped USGS/INGENIOUS catalogue traces (`existing_faults.tif`, `278,948` positive pixels) are excluded from target evaluation truth. Any dot placed at $d_{\text{cat}} \le 2\text{ px}$ (`200 m`) has nearly its entire 300 m kernel disk occupied by masked catalogue traces and earns near-zero off-catalogue $\text{TP}_w$ while still paying $0.2\,\text{FP}_w$.

### 1.2 Quantitative Decomposition of the `H16-1` -> `d2.8` -> `H33-2-B2` Progression
Byte-level inspection of `research/upstream/h33.py`, `research/upstream/h33-best-audit.json`, `data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`, and `data/scored_ext/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`SHA-256: c55bafc4...`) establishes the exact 3-step progression *(all live scores below are owner-reported historical figures without local portal receipts, per `IR-32-SCORE-01`)*:

| Stage | Artifact | Emitted Dots $N$ | Owner-Reported Live Score | Verified Mechanism |
|---|---|---:|---:|---|
| Continuous ridge | `gems19-h19-5` | `121,131` | `0.1922` | Supervised structural ridge probability (`H16` physics + catalogue tip/corridor distance features), severely penalized by additive `0.2 * FP_w` along continuous 1-px lines |
| Poisson-disk dotting (`d=2.8 px`) | `gems24-h25-1-dotted-h19-5-d2-8` | `44,090` | `0.2600` | Greedy 2.8-px spacing strips `63.6%` of redundant ridge pixels while preserving ~93% of 300 m triangular-kernel coverage (`+0.0678` owner-reported lift) |
| Collar prune (`B=1 px` -> `B=2 px`) + `zeros` | `H27-4` -> **`GEMSDOE32 H33-2-B2`** | `40,199` -> **`37,654`** | `0.2708` -> **`0.2778`** | Exact deletion of `6,436` near-catalogue flank dots from `d2.8` (`3,891` at `d_cat <= 1` and `2,545` more at `1 < d_cat <= 2`) plus replacing outside-footprint `NaN` with finite `0.0` (`zeros` mode) to pass portal `[0, 1]` validation |

We verified Step 3 directly on our fold-fair buffered whole-component holdout (`gems57-pooled-hide-v2`, `22,893` withheld pixels): applying the exact `d_visible > 2 px` collar inside each fold (`h33_foldfair`) improves `d2.8` from **`HOLDOUT-DTI = 0.10093 [0.08974, 0.11164]`** to **`0.10564 [0.09373, 0.11728]`** (`paired delta = +0.00472 [+0.00379, +0.00577]`, strictly positive across all 20 km spatial bootstrap resamples).

### 1.3 Algebraic Inversion: Can We Score Higher (`0.3195`–`0.4413`), and How?
Assuming hidden test fault cardinality $|Y^\star|$ lies in the physically grounded Great Basin range `30,000–40,000` pixels (say $|Y^\star| \approx 35,000$):
- At $N = 37,654$ binary dots and $\text{DTI} \approx 0.2778$, solving $\text{TP}_w / (0.2\,\text{TP}_w + 0.8|Y^\star| + 0.2\,\text{FP}_w) = 0.2778$ gives $\text{TP}_w \approx 9,920$ (`28.3%` weighted recall) and **$\approx 0.102$ truth credit per emitted dot** (up from `0.089` on `d2.8`).
- Even if one deleted *every* remaining false positive from `H33-2-B2` (`FP_w -> 0`) without losing a single true hit, fixed-recall DTI caps at $9,920 / (0.2 \times 9,920 + 0.8 \times 35,000) = \mathbf{0.3308}$ — **mathematically below `0.4413`**.
- Reaching `0.3195`–`0.4413` at $N \approx 38,000\text{–}45,000$ dots requires raising $\text{TP}_w$ to `11,700–17,800` (**`0.118–0.165` truth credit per dot**), which requires genuine geological discovery of **concealed intrabasin, piedmont, and stepover hydrothermal faults** where surface bedrock DEM scarps vanish under Quaternary alluvium and Lake Lahontan lacustrine fill.

---

## 2. Pre-Implementation Ranking of 5 Untried Candidate Geological Hypotheses

Before writing model code, we audited every local raster header, CSV column, and external data endpoint, plus sibling lanes `GEMSDOE28..GEMSDOE88`, and ranked five geological hypotheses:

| Rank & ID | Specific Verified Layers | Physical Signature & Mathematical Transform | Why Missing From USGS/INGENIOUS Catalogue | Named Non-Fault Mimic & Physical Guard | Novelty vs Existing Repos, Expected Lift & Cost |
|---|---|---|---|---|---|
| **1. `H86-WVB`** *(Selected & Executed)* | `training_features.tif` (bands 2,3,4,6,7,8,9,11,12,13,15,17,18,19), `geodawn_extensions_u8` (4: `TMI_up150`), `geodawn_rad_u8` (1,2), `lidar_scarp_features_u8` (**verified bands 1,3,6,7,9,10,12**), `topo_10m_derived_100m_u8` (5–9), GDR #1391 wells/springs & `Paleo_geothermal_final.csv`, buffered `visible` traces + slip sense | **Salem tilt local-wavenumber basement depth** $z_{\text{mag}} = 1 / (\|\nabla \theta_{\text{tilt}}\| + \varepsilon)$ concordant with gravity-derived `depth_to_base_surf`, 150 m upward-continuation persistence, 3D Mag/Grav analytic signals, **silica/cation geothermometer disequilibrium** ($\Delta T = T_{\text{res}} - T_{\text{out}}$) & sinter vents, relief-normalized 1 m/10 m scarps, and 3-px-buffered anisotropic crack-tip / bitplane two-host relays -> LOQO GBM + `2.8 px` greedy kernel allocator | Concealed basin-interior and piedmont geothermal faults are buried by 50–1,500 m of Cenozoic fill and lack bedrock scarps, yet juxtapose basement blocks at $z_{\text{mag}} \approx H_{\text{base}}$, leak silica-equilibrated fluids & sinter, and bridge across stepover relays | **Miocene flood-basalt flow margins** (shallow $z_{\text{mag}} \ll H_{\text{base}}$, fast upward-continuation decay, weak Bouguer step) and **Pleistocene Lake Lahontan wave-cut shorelines** (~1,190–1,345 m contour-parallel benches with no basement step) | Untried across `GEMSDOE28..88` (prior PR #6 `H86-RMRB` used unsupervised K/Th/U Huber residuals only; `GEMSDOE32` lacked Salem depth concordance, GDR #1391 geothermometry, sinter conduits, seamless 10 m DEM, and submodular 300 m placement, and mis-indexed `lidar_scarp` bands). **Achieved `+0.0570` buffered `HOLDOUT-DTI` lift**; ~20 min CPU, `<1.5 GiB` RAM |
| **2. `H86-CCMO`** *(Curvature-Conditioned Magnetic Contact Offset)* | `rtp` (2), `tmi_hg` (3), `tmi_vg` (9), `iso_grav_anom_hg` (18), `det_elev_slope` (19) | Detects laterally displaced conjugate endpoints of passive magnetic contact ridges across 200–1,200 m cross-strike corridors corroborated by transverse gravity gradient rotation | Accommodation transfer cross-faults under thin pediment veneer create no scarp of their own, expressing only by offsetting older magnetic units | Primary sinuous lava-channel terminations and aeromagnetic survey tie-line seams (guarded by multi-scale persistence and gravity corroboration) | Distinct from direct ridge tracking; moderate-high precision on transfer zones, lower recall in non-magnetic playas; ~60 s CPU (held in reserve) |
| **3. `H86-RTDR`** *(Radiometric–Topographic Discordance & MT Clay-Cap Ribbon)* | `geodawn_rad_u8` (`K, Th, U`), `cond_surf` (17), `det_elev` (12), `det_elev_slope` (19) | Topographically deconfounded `K/Th` residual ridges crossing elevation contours paired with lateral gradient of shallow MT smectite clay-cap conductivity | Sealed epithermal/geothermal conduits alter surface regolith (adularia/illite + smectite) without Holocene surface rupture | Felsic ash-flow tuff outcrops and alkaline playa evaporite rings (suppressed by slope/elevation deconfounding) | Upgrades PR #6 `H86-RMRB` by stripping geomorphic fan sorting (incorporated as static channel `s_rad_kth_deconf` inside `H86-WVB`); low-moderate standalone lift due to 30–50 cm gamma skin depth |
| **4. `H86-TSBA`** *(Transtensional Strain-Weighted Basement-Step Inflection)* | `geod_2ndinv` (4), `geod_shearrate` (7), `geod_dilaterate` (8), `depth_to_base_surf` (15) | Crustal transtensional index $\dot{\varepsilon}_{\text{dil}} / (\dot{\varepsilon}_{2\text{nd}} + \varepsilon)$ weighting 2nd-derivative basement-depth inflection crests | Targets blind releasing-step basin-margin faults accommodating modern GPS extension under rapid sedimentation | Unfaulted erosional bedrock pediments buried by Neogene fill | Low standalone 300 m precision because geodetic GPS strain bands have >15 km wavelength (incorporated as regional stress gate `s_transtens_idx` in `H86-WVB`) |
| **5. `H86-SEIS-3D`** *(Relocated Microseismic Hypocentral Plane Up-Dip Projection)* | USGS ANSS ComCat FDSN API (`https://earthquake.usgs.gov/fdsnws/event/1/query`) relocated hypocentres & focal mechanisms | 3D RANSAC plane-fitting of microseismic swarms ($M_w$ 1.0–4.0, 2–8 km depth) projected up-dip to surface `EPSG:32611` cells | Blind seismogenic geothermal swarm faults rupture at depth with zero surface expression | Magmatic dike swarms and open-pit mine blasts (filtered by `eventtype=earthquake` & depth `>2 km`) | **Non-viable in this sandbox:** live check confirmed `earthquake.usgs.gov` returns `HTTP 000` (egress restricted to GitHub/PyPI/npm) and raw hypocentre tables are absent from pinned manifests |

---

## 3. Executed `H86-WVB` Architecture & 4-Gate Verification Results

### 3.1 Gate 2: Single-Feature Leakage Canary (`36 / 36` Features PASS `<= 0.90`)
Every individual feature in `scripts/run_h86_wvb.py` was tested alone against withheld buffered whole-component labels on both `seed=20` and `seed=21` before trusting any model (`docs/evidence/h86_wvb_results.json`):
- **24 Static Zero-Catalogue Physical Channels (`STATIC_NAMES`, zero bytes of `existing_faults.tif`):** `max_disc_AUC = 0.65941` (`seed=20`, `s_mag_grav_concord`) and `0.66346` (`seed=21`, `s_topo10_break`). Top static physical signals: `s_mag_grav_concord` (`0.659`), `s_topo10_break` (`0.655`), `s_relief_norm_scarp` (`0.635`), `s_mag3d_log` (`0.619`), `s_grav3d_log` (`0.619`), `s_sinter_trav_log` (`0.587`), `s_geotherm_diseq` (`0.578`), and `s_lahontan_mimic` (`0.574`, negatively weighted by GBM as a shoreline suppressor). Note: `dist_known_fault_px` inside `ing_wells_geotherm_metrics.csv` was explicitly banned to guarantee zero catalogue leakage in `E1`.
- **12 Fold-Recomputed Buffered Structural Channels (`COUPLED_NAMES`, derived strictly from `visible & ~(EDT <= 3 px)`):** `max_disc_AUC = 0.87047` (`seed=20`, `v_aniso_strike_reach`) and `0.86697` (`seed=21`, `v_aniso_strike_reach`), both safely below the `0.90` protocol stop ceiling.
- **Controls:** Shuffled control `disc_AUC = 0.51399` (`seed=20`) / `0.50608` (`seed=21`); constant control `= 0.50000`.

### 3.2 Gate 3: Strictly Budgeted 3-Experiment Progression (`HOLDOUT-DTI`)
All models used 4-quadrant Leave-One-Quadrant-Out (LOQO) `HistGradientBoostingClassifier` (`max_iter=150, max_leaf_nodes=31, min_samples_leaf=80, learning_rate=0.06, l2_regularization=2.0`) evaluated via unmodified `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`) at matched budget `N = 37,654` dots:

| Arm / Experiment | Evaluator: Buffered Whole-Components (`22,893` px, `159` 20 km clusters) | Paired $\Delta$ vs `d2.8` (95% CI) | Paired $\Delta$ vs `h33_foldfair` | Evaluator: `build_holdout` `all` (`22,641` px) | `build_holdout` `detached` (`22,619` px) | Read-Only SGMC Off-Cat Proxy (`62,122` px) |
|---|---|---|---|---|---|---|
| `uniform_random_37654` | `0.04797 [0.04343, 0.05208]` | `-0.05296 [-0.06320, -0.04263]` | `-0.05768` | `0.04568 [0.04261, 0.04882]` | `0.01361 [0.01246, 0.01479]` | — |
| PR #6 `H86-RMRB` (fold-fair / pruned TIFF) | `0.00361 [0.00294, 0.00430]` (TIFF) | `-0.09732 [-0.10789, -0.08645]` | `-0.10204` | `0.04199` (fold-fair) / `0.00376` | `0.04318` / `0.00388` | — |
| `d28_incumbent` (`44,090` dots) | `0.10093 [0.08974, 0.11164]` | `0.00000` (baseline) | `-0.00472` | `0.10107 [0.08586, 0.11671]` | `0.10346 [0.08795, 0.11941]` | `0.09369` |
| `h33_foldfair` (`d_vis > 2 px`) | `0.10564 [0.09373, 0.11728]` | `+0.00472 [+0.00379, +0.00577]` | `0.00000` | `0.10482 [0.08935, 0.12119]` | `0.03333 [0.02581, 0.04166]` | — |
| **Exp 1 · `E1_static_physics_nms`** (0 catalogue bytes) | **`0.07209 [0.05835, 0.08572]`** | `-0.02883 [-0.04400, -0.01467]` | `-0.03355` | `0.07196 [0.06046, 0.08377]` | `0.02538 [0.02124, 0.02975]` | `0.04029` |
| **Exp 2 · `E2_coupled_valve_nms`** (36 features + 3x3 NMS) | **`0.14237 [0.12739, 0.15614]`** | **`+0.04144 [+0.02257, +0.05904]`** | **`+0.03673 [+0.01760, +0.05456]`** | **`0.24734 [0.23338, 0.26213]`** | **`0.11454 [0.10113, 0.12687]`** | `0.03437` |
| **Exp 3 · `E3_dual_submod300` (`H86-WVB`)** | **`0.15792 [0.13884, 0.17587]`** | **`+0.05700 [+0.03513, +0.07752]`** | **`+0.05228 [+0.02978, +0.07336]`** | **`0.30237 [0.28745, 0.31908]`** | **`0.12233 [0.10909, 0.13428]`** | **`0.05301`** |

**Why `E3_dual_submod300` beat `E2` by another `+0.01555` (`+10.9%`) on buffered whole components and `+54%` on read-only SGMC (`0.03437 -> 0.05301`):**
1. **Resolving the 29-px kernel blob bias:** `EM.greedy_allocate` convolves probabilities with `W29` (`sum = 205.72`), which inflates diffuse 2D probability blobs `3.7x` over sharp 1-px fault traces (`sum = 56.0`). Multiplicative physical corroboration $s_{\text{dual}} = p_{E2}^{0.85}\,p_{E1}^{0.15}$ paired with `min_dist_px = 2.8 px` suppresses uncorroborated geometric halos while enforcing exact 280 m spacing along real physical structures.
2. **Off-catalogue discovery footprint:** In the full-data inference raster (`37,654` dots), **`25,194` dots (`66.9%`) lie strictly beyond `500 m` (`d_cat > 5 px`)** of mapped USGS/INGENIOUS faults, recovering a read-only SGMC off-catalogue DTI of `0.05301` without ever training on SGMC.

### 3.3 Gate 4: 43-Raster Two-Phase Uniqueness Audit & Why Verdict Is `negative`
Audited via `vendor/gems57/uniqueness.py` across all **43 deduplicated full-grid GeoTIFFs** (12 upstream `data/scored/` + 30 deduplicated sibling champions `GEMSDOE32..GEMSDOE88` in `data/scored_ext/` + PR #6 `H86-RMRB`):
- **Pre-placement surface Spearman:** `max |rho| = 0.12710 <= 0.90` (`PASS`).
- **Final dot raster Spearman:** `max |rho| = 0.09489 <= 0.90` (`PASS`), `max jaccard_dot_sets = 0.05358`.
- **Modern sibling champions (`30 / 30 PASS <= 0.70`):** Maximum 3-px forward dot overlap across all 30 sibling champions (`GEMSDOE32..GEMSDOE88`) is **`0.63531`** (`GEMSDOE78`), followed by `0.63194` (`GEMSDOE81`), and only **`0.29280`** against **`GEMSDOE32 H33-2-B2`** (`rho = +0.01513`, reverse 3-px overlap `0.21302`, Jaccard `0.01128`).
- **Protocol Rule 1 Blockers (`> 0.70` forward 3-px overlap):**
  1. `gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif` (`174,232` positive pixels): forward 3-px overlap **`0.78531 > 0.70`** (reverse overlap `0.38961`, `rho = +0.04649`).
  2. `gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif` (`69,281` positive pixels): forward 3-px overlap **`0.74146 > 0.70`** (reverse overlap `0.33976`, `rho = +0.02604`).
  3. `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (`206,895`-dot regular 5x5 grid covering `99.8724%` of all allowed footprint cells within 3 px; forward `0.99644`, reverse `0.12139`, `rho = +0.00053`, logged under `IR-86-LATTICE-01`).

Because `3/3` budgeted experiments were consumed (`E1`, `E2`, `E3`) and two genuine `gems10` ridge priors exceed `0.70` forward 3-px overlap, **Protocol Rule 1 and Rule 5 require `verdict = "negative"`** with zero weekly submission slots spent.

---

## 4. Verified Official Sources, Flagged Irregularities & Honest Limitations

### 4.1 Verified Official & Pinned Provenance
1. **DrivenData / U.S. DOE GTO GEMS Specification:** `https://www.drivendata.org/competitions/300/competition-gem-faults/` & official reference repo `https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b` (`research/upstream/official-reference-README.md`).
2. **USGS GeoDAWN Airborne Magnetic & Radiometric Survey:** USGS Data Release `https://doi.org/10.5066/P93LGLVQ` (CC0 1.0 public domain; local `geodawn_rad_u8.tif` `c22420f7...` & `geodawn_extensions_u8.tif` `a35a9c6d...`).
3. **USGS 3DEP 1 m LiDAR & Seamless 10 m DEM:** `https://www.usgs.gov/3d-elevation-program` (public domain; local `lidar_scarp_features_u8.tif` `d580bb8b...` & `topo_10m_derived_100m_u8.tif` `a6398d99...`).
4. **DOE Geothermal Data Repository GDR #1391 (INGENIOUS Great Basin Compilation):** `https://gdr.openei.org/submissions/1391` / `https://doi.org/10.15121/1881483` (CC BY 4.0; local `ing_wells_geotherm_metrics.csv` `122718e6...`, `Paleo_geothermal_final.csv` `faffcf69...`, `flt_attr_100m.tif` `c5edf9df...`).
5. **USGS State Geologic Map Compilation (SGMC):** Horton et al. (2017), `https://doi.org/10.3133/ds1052` (local `usgs_sgmc_faults_100m.tif` `643cbe99...`, **read-only post-hoc diagnostic only**).
6. **Shared Evaluation & Serialization Template:** `60GEMSDOE@b99591eede63c6d45c8a896255b8cd34824fa00b` (`23/23` SHA-256 pins verified intact in `vendor/gems57/`).

### 4.2 Flagged Irregularities (Resolved or Explicitly Documented)
- **`IR-32-SCORE-01` (Unreceipted Historical Leaderboard Scalars):** `0.2778` (`GEMSDOE32`), `0.3195`, and `0.4413` have no attached DrivenData submission-page receipts in git; `research/upstream/h33-best-audit.json` itself marks `H33-2-B2` `"UNSCORED"` at export time with a projected range. All three numbers are treated strictly as owner/user-reported context, never `ORGANIZER-CONFIRMED`.
- **`IR-86-LANE-01` (Missing Explicit Lane Paragraph):** The prompt referenced a single assigned lane paragraph that was omitted from the pasted brief; `H86-WVB` was explicitly declared after auditing `GEMSDOE28..GEMSDOE88` to guarantee zero cross-lane duplication.
- **`IR-86-PR6-EVAL-01` (Post-Catalogue-Masking Holdout Trap):** Prior PR #6 masked full `existing_faults.tif` (`B=2 px`) before calling `evaluate_holdout`, zeroing withheld segments adjacent to visible splits (`0.04199 -> 0.00376`). Fixed in `scripts/run_h86_wvb.py` by masking only fold-visible `d_visible <= 2 px` on holdout folds and full `d_cat <= 2 px` only on final full-data inference.
- **`IR-86-LIDAR-01` (Upstream Band-Index Mismatch in `lidar_scarp_features_u8.tif`):** Upstream `h33.py` read bands `(1, 2, 5)` for `(ex_max, step_max, downface_max)`, whereas actual GeoTIFF descriptions are `1=ex_max, 2=ex_mean, 3=step_max, 6=downface_max, 7=upface_max, 9=relief, 10=coh100, 12=valid`. Fixed in `scripts/run_h86_wvb.py`.
- **`IR-86-LATTICE-01` (`r13-lattice-s5` Trivial Covering Artifact):** The 5x5 lattice (`206,895` dots) covers `99.8724%` of all allowed footprint cells within `3 px`; reported transparently (`0.99644`) while also documenting that 2 genuine `gems10` ridge priors exceed `0.70`.
- **`IR-86-AUDIT-CLOBBER-01` (`scripts/audit.py` Evidence Overwrite):** Earlier `scripts/audit.py:run()` unconditionally overwrote `docs/evidence/run-card.json` whenever unit tests ran. Fixed in Pass 2 so `audit.run()` is read-only unless `--write-out` / `write_out` is explicitly passed.

### 4.3 Remaining Limitations & Recommended Next Steps for Selector / Future Session
1. **Uniqueness vs `gems10` Catalogue Halo:** Because `66.9%` (`25,194 / 37,654`) of `E3` dots are >500 m from the catalogue (`d_cat > 5 px`) while `33.1%` remain in the near-tip/stepover halo heavily populated by `gems10-h25-ctx-ridge` (`174,232` px), standalone `E3` hits `0.7853` forward 3-px overlap. In a selector-authorized follow-up, increasing the static-physics exponent in $p_{\text{coupled}}^{1-\gamma}\,p_{\text{static}}^{\gamma}$ (e.g., $\gamma \in [0.35, 0.50]$) or applying an explicit `gems10` envelope novelty regularizer can push off-catalogue share above `78%` and clear `< 0.70` against every historical `gems10` raster.
2. **Sandbox Network Egress:** `drivendata.org` is login-walled and `earthquake.usgs.gov` is egress-blocked (`HTTP 000`), preventing live portal quota checks and live USGS ComCat microseismic ingestion (`H86-SEIS-3D`) inside this container.
3. **Private Truth Distribution Shift:** `labels.tif` equals public `existing_faults.tif` (`278,948` px); holdout recovery measures buffered whole-component concealment proxies and read-only SGMC faults, which cannot guarantee exact alignment with private organizer borehole/seismic truth.
