# 2026-10-26 H86P-TCWB and Focus-9 review — evidence-qualified H33 analysis, 3 ranked untried hypotheses, and a negative release decision

> The H86P result below is a historical `HOLDOUT-DTI` measurement, not a leaderboard score: `0.1727007956`, 95% CI `[0.1560010, 0.1893807]`, evaluator `gems57-pooled-hide-v2`, `11,321` withheld positives. It was not rerun in this review.

- **Current review branch:** `arena/87dd4f8f-gemsdoe86`
- **Historical H86P execution branch:** `arena/1595e23f-gemsdoe86`
- **Date (UTC):** `2026-10-26`
- **Immediate Upload Authorization Verdict:** **`DO NOT SUBMIT`** (`verdict = "negative"`, `submission_ready = false`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`).
- **Newest Unique GeoTIFF (`15/15` automated format & `[0, 1]` checks PASS, audit-only download):**
  - TIFF: [`docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif`](../docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif) (`SHA-256: 8c8951653dcb4ac8c175136953dcb0a138147ab216327a461d430ce2698ab159`, `37,654` unit dots, `EPSG:32611`, `3730×3292`, `min = 0.0`, `max = 1.0`, `0` NaN, `0` Inf, `0` mapped-catalogue dots)
  - Single-TIFF ZIP: [`docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.zip`](../docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.zip)
  - Writer Receipt: [`docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.json`](../docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.json)
  - Canonical Lane Run Card: [`docs/evidence/h86p-tcwb-run-card.json`](../docs/evidence/h86p-tcwb-run-card.json)
  - Frozen Preregistration: [`research/H86P_TCWB_PREREGISTRATION.json`](H86P_TCWB_PREREGISTRATION.json) · [`research/H86P_TCWB_PREREGISTRATION.md`](H86P_TCWB_PREREGISTRATION.md) · [`registry/h86p_hypotheses_20261026.json`](../registry/h86p_hypotheses_20261026.json)

---

## 1. Fleet-Wide Review (`92` Repos, `119` Scored Claims) & Dedicated Focus-9 Executive Summaries

### 1.1 Fleet-Wide Ranking & Evidence-Class Discipline (`OWNER-REPORTED` vs `HOLDOUT-DTI`)

All user-supplied leaderboard numbers in [`research/REQUEST_20261026.md`](REQUEST_20261026.md) (`119` scored claims across `92` repositories in [`registry/prior_scores.csv`](../registry/prior_scores.csv)) carry evidence class **`OWNER-REPORTED`** (`CLAIM` in [`ledger/submissions.csv`](../ledger/submissions.csv)) because official DrivenData receipt JSONs are not attached in git. Under `OWNER-REPORTED` claims:

1. **Overall 92-repo fleet leader (`OWNER-REPORTED`):** **`GEMSDOE87`** (`gemsdoe87-opt-33851dots-20261015-zeros`, **`0.3195`** `OWNER-REPORTED`; earlier sibling `gemsdoe87-h1-opt-37010dots-20261014`: `0.3143`), followed by **`GEMSDOE65`** (`0.2951`), **`GEMSDOE88`** (`0.2943`), **`GEMSDOE84`** (`0.2939`), **`GEMSDOE77`** (`0.2933`), **`GEMSDOE75`** (`0.2899`), and **`GEMSDOE32`** (**`0.2778`** — **#1 among the Focus-9 cohort**). Competition external top value referenced in the prompt: **`0.4413` OWNER-REPORTED; no receipt located**.
2. **2026-10-26 Feed Delta & Irregularities (`IR-86P-FLEET-20261026`):**
   - `GEMSDOE91` added `gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros: 0.1367` (`OWNER-REPORTED`, verified in `GEMSDOE91` `HEAD` at `sha256 = 792af6255a7e1048...`), which duplicates `0.1367` previously reported on `bf21d9a4bd` (absent at `GEMSDOE91` `HEAD`), alongside `gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros: 0.1823`.
   - Unscored `GEMSDOE91-S18-UNIQUE-curvtilt-20000dots-20261025T193000Z-zeros:` corresponds on `GEMSDOE91` `HEAD` to `docs/downloads/gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405.tif` (`20,000` dots, `sha256 = af01bc7190ce736d...`, stem/timestamp mismatch).
   - `GEMSDOE92` (`gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros: 0.0255` `OWNER-REPORTED`) has `0` `.tif` files committed in `GEMSDOE92` `HEAD`.

### 1.2 Dedicated Executive Summaries for the Focus-9 Sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`)

Every Focus-9 repository was directly audited via zero-REST `codeload.github.com` tarball inspection (`27` GeoTIFFs verified against `sample_submission.tif` `3730×3292` `EPSG:32611` footprint `fp` and `existing_faults.tif` catalogue `cat`):

- **Which Focus-9 submission is best?** **`GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` `OWNER-REPORTED`)** has the highest owner-reported value in the Focus-9 cohort, ahead of `GEMSDOE36` (`0.2750`), `GEMSDOE28`/`GEMSDOE31` (`0.2708`), `GEMSDOE33` (`0.2632`), `GEMSDOE25`/`GEMSDOE30` (`0.2600`), `GEMSDOE24` (`0.2477`), and `GEMSDOE27` (`0.2449`).
- **Are the `.tif` files across the Focus-9 sites (or in `GEMSDOE86`) approved to upload to a live weekly competition slot right now?** **NO — all 9 Focus-9 repositories currently post `DO NOT SUBMIT` at `HEAD`, and all `43` currently published research `.tif` files in `GEMSDOE86/docs/downloads/` pass the local download/format audits for research/audit use ONLY (`DO NOT SUBMIT`; `15/15` format checks are not submission clearance).** In addition, legacy `-nan` / `-nanoutside` sibling files in `GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36` contain `3,109,522` outside-footprint `NaN`s (`-zeros` / `-allfinite` siblings have `0` `NaN`s and `[0, 1]` range, but historical winning rasters are already submitted/duplicated in the fleet registry).

| Site | Best Scored Submission (`OWNER-REPORTED`) | Latest 2026-10-25/26 Submission (`OWNER-REPORTED`) | Verified Raster Geometry (`EPSG:32611` `3730×3292`) & Radial Profile | Site `HEAD` Gate & Download Safety |
|---|---|---|---|---|
| **`GEMSDOE32` (BEST OF FOCUS-9)** | **`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`** (`-zeros` `sha256: c55bafc4...`) | Same (`H33` retained at `HEAD`) | **`37,654` dots**, `0` cat hits, `min_dcat = 2.24 px`, **`>1 km` = `69.8%`**, exact subset of `D28` (`44,090`) & `H27-4` (`40,199`) minus `2,545` `1 < d_cat <= 2 px` collar dots | **`DO NOT SUBMIT`** (`-zeros` format-valid `[0,1]`; already submitted in fleet; `-nan` sibling has outside-fp `NaN`) |
| **`GEMSDOE36`** | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros`: **`0.2750`** (`sha256: 043cb1ee...`) | Same | **`38,854` dots**, `0` cat hits, `min_dcat = 2.24 px`, `>1 km` = `69.6%`; exact superset `H33 (37,654) + 1,200` Andersonian PINN dots (`-0.0028` DTI dilution vs `H33`) | **`DO NOT SUBMIT`** (`-zeros` format-valid `[0,1]`; duplicate of `H33` at `96.9%` overlap) |
| **`GEMSDOE28`** | `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc`: **`0.2708`** (`40,199` dots; also `h36-1`: `0.2683`, `h32-1`: `0.2649`, `h38-1`: `0.2498`) | `gems28-s18-mxtp-20261025-3e95505c011a`: **`0.0217`** (`11,082` dots) | `H27-4`: `40,199` dots (`min_dcat = 1.41 px`, `>1 km` = `65.4%`); `s18-mxtp`: severely under-budget (`11,082` dots -> `TP_w` collapse) | **`DO NOT SUBMIT`** (`-allfinite` valid `[0,1]`; `-nan` siblings carry outside-fp `NaN`) |
| **`GEMSDOE31`** | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1`: **`0.2708`** | Same | **`40,199` dots**, pixel-identical inside `fp` to `GEMSDOE28` `H27-4` (`8acb75e1`, `min_dcat = 1.41 px`, `>1 km` = `65.4%`) | **`DO NOT SUBMIT`** (exact cross-site duplicate of `GEMSDOE28` `H27-4`) |
| **`GEMSDOE33`** | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e`: **`0.2632`** | Same | **`41,865` dots** in `HEAD` TIFF (`min_dcat = 2.24 px`, `>1 km` = `66.1%`), `H33` + `4,211` analog tip-stepover dots (`-0.0146` DTI dilution vs `H33`) | **`DO NOT SUBMIT`** (audit-only; `-nanoutside` sibling has outside-fp `NaN`) |
| **`GEMSDOE25`** | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros`: **`0.2600`** (`D28` root) | `gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros`: **`0.0742`** | `D28`: `44,090` dots (`min_dcat = 1.00 px`, `>1 km` = `60.2%`); `h66`: `44,832` dots crowded near catalogue (`>1 km` = **`24.3%`** -> `0.0742` collapse) | **`DO NOT SUBMIT`** (`-zeros` format-valid `[0,1]`; audit-only) |
| **`GEMSDOE30`** | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca`: **`0.2600`** | `gems30-MSDB1-edge44090-20261025-e7856ec3f14a`: **`0.1462`** | `d28`: `44,090` dots (exact `GEMSDOE25` `D28` support); `MSDB1`: `44,090` dots with `>1 km` = **`33.4%`** (`-0.1138` vs `D28`) | **`DO NOT SUBMIT`** (audit-only) |
| **`GEMSDOE24`** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1`: **`0.2477`** | `gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros`: **`0.0859`** | `h25-1`: `60,069` dots (`d_min = 1.5 px` over-packed); `gvc1`: `37,654` dots crowded near catalogue (`>1 km` = **`25.7%`** -> `0.0859`) | **`DO NOT SUBMIT`** (`-zeros` / `-allfinite` format-valid `[0,1]`; audit-only) |
| **`GEMSDOE27`** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1`: **`0.2449`** | `gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886`: **`0.2190`** (`-allfinite` at `HEAD`) | `topo-gap-closure`: `61,328` dots (`d_min = 1.5 px` ancestor of `h25-1`); `h29`: `37,654` dots with **`>1 km` = `61.8%`**, scoring **`0.2190`** (`2.5x–3.0x` higher than halo-crowded `gvc1` `0.0859` & `h66` `0.0742`!) | **`DO NOT SUBMIT`** (`-allfinite` valid `[0,1]`; audit-only) |

---

## 2. PhD-Level Forensic Analysis of `GEMSDOE32` (`h33-h33-2-b2`, `0.2778` `OWNER-REPORTED`)

### 2.1 What the raster lineage and metric establish—and what they do not

The cohort's reported scores are **OWNER-REPORTED** claims; no organizer submission receipt was located. The accepted competition result for H33 is therefore unknown here. The archived pixel comparison records a sparse lineage: `D28` (44,090 dots) → `H27-4` (40,199 dots) → `H33` (37,654 dots), with H33 a 2,545-dot subset change relative to H27-4. This is evidence about prediction support, not a measurement of hidden organizer truth or per-dot credit. The reported H33-minus-H27-4 score difference (`0.2778 - 0.2708 = 0.0070`) is arithmetic on two **OWNER-REPORTED** claims; it is not a controlled causal effect.

The shared metric (`vendor/gems57/metric.py`; synthetic formula checks in `tests/test_scientific_interpretation.py`) uses a triangular kernel with radius 3 px (300 m), `alpha = 0.2`, `beta = 0.8`. Each truth pixel receives its maximum nearby prediction credit, while false-positive mass is accumulated across predictions with a distance-dependent weight. Thus nearby dots may be redundant for truth credit but still incur false-positive cost; conversely, a dot in the 1–2 px catalogue collar may recover an unmasked hidden fault. The mapped-fault pixels are masked exactly—the surrounding kernel is not. Dots separated by 2.8 px do not have disjoint 3 px supports. Neither dot density nor catalogue distance alone determines DTI.

For a specified prediction and truth set, write `T = TP_w`, `F = FP_w`, and `K = |G|`. Since `FN_w = K - T`,

`DTI = T / (T + alpha F + beta(K - T)) = T / (beta K + (1 - beta)T + alpha F)`.

If pruning changes the *actual weighted components* by `Delta T >= 0` and `Delta F >= 0`, then (for `Delta F > 0`) the pruned prediction has a higher DTI exactly when

`Delta T / Delta F < alpha * DTI / (1 - (1 - beta) * DTI)`.

This finite-change identity is not an estimate of H33's score mechanism: `Delta F` is weighted false-positive mass, not the number of removed dots, and the hidden truth required to evaluate either change is unavailable. No claim that the 2,545 removed dots had zero truth credit, were “already covered,” or caused an exact `+0.0070` gain is supported.

The reported `69.8%` H33 share more than 1 km from the mapped catalogue is a geometric property of the raster. It does not establish that hidden organizer faults occur there or explain a reported leaderboard result. Likewise, comparisons across different sites, algorithms, training labels, geographic support and dot budgets are descriptive associations, not controlled evidence for a radial-allocation law.

### 2.2 Can this work establish a result above GEMSDOE32's reported value?

**No conclusion about a higher live competition score is supported.** H33's `0.2778` is **OWNER-REPORTED**, not organizer-confirmed. The supplied `0.3195` and `0.4413` figures are also user/owner claims without receipts in this checkout. This review did not scrape DrivenData or verify current leaderboard standings.

The inherited H86P-TCWB experiment records **HOLDOUT-DTI = `0.1727007956`**, 95% CI **[`0.1560010`, `0.1893807`]**, evaluator `gems57-pooled-hide-v2`, **11,321 withheld positives**. Its paired change against E3 is **HOLDOUT-DTI Δ = `+0.0161572`**, 95% CI **[`+0.0040447`, `+0.0286042`]**. Those are spatial-holdout measurements, not live scores and not directly comparable with H33's owner-reported result. The separate `0.0954` **SGMC-PROXY-DTI** value is an off-catalogue diagnostic on an external proxy set, not a competition score.

No numeric leaderboard projection is made. The earlier `0.31–0.36+` roadmap and its unvalidated dot-allocation recipe are withdrawn: available holdout and proxy evidence cannot support that forecast. The valid research next step is to restore verified native features and the shared cache, select one still-untried preregistered lane, and test it under the buffered whole-segment spatial holdout and leakage canaries. **No weekly slot may be considered** while the literal registry stop remains in force; a higher holdout score would not override it.
---

## 3. Three ranked untried geological hypotheses (`registry/h86p_hypotheses_20261026.json`)

The frozen H86P queue contained four candidates and was declared **before** its historical holdout evaluation. Its original Rank 1 (`H86P-1_TCWB`) has since been tested; it is not counted as untried here. This review renumbers the three remaining, untested hypotheses as a current research queue (original preregistration ranks 2–4). The ordering weighs qualitative expected holdout-DTI improvement against implementation cost and present data viability. No defensible numerical ΔDTI forecast is available; all expectations are unmeasured research judgments, not scores or leaderboard projections.

The original queue and physical rationales are preserved in [`registry/h86p_hypotheses_20261026.json`](../registry/h86p_hypotheses_20261026.json) and [`research/H86P_TCWB_PREREGISTRATION.md`](H86P_TCWB_PREREGISTRATION.md). The historical tested Rank 1 achieved `HOLDOUT-DTI = 0.1727007956`, 95% CI `[0.1560010, 0.1893807]` (`gems57-pooled-hide-v2`, 11,321 withheld positives); that is historical holdout evidence, not leaderboard evidence.

**Current data-viability check:** `data/training_features.tif`, the prepared native-band arrays, `.cache/external/` and the shared feature cache are absent. Current Rank 1 / original `H86P-2_BCSF` uses native bands only and needs no new external dataset; it is scientifically testable in principle but **not operationally runnable in this checkout** without the shared native stack/cache. Current Rank 2 / original `H86P-3_RCSD` needs official USGS GeoDAWN radiometrics (DOI `10.5066/P93LGLVQ`); a historical SHA-pinned mirror was used by H86P, but no current bytes are present, and this review did not fetch new external data. Restore only through the pinned provenance path before calling it obtainable. Current Rank 3 / original `H86P-4_USMT` needs the free official EarthScope/USArray 3-D MT volume; it is neither mirrored nor retrievable directly from the sandbox's host allowlist, so it remains deferred. No hypothesis was run against partial or substituted inputs.

1. **Current Rank 1 — `H86P-2_BCSF` (original Rank 2; untried; top candidate):** Competition Bands 15 (basement depth), 12 (elevation), 18/11 (signed gravity gradients). Target a signed cross-strike third-derivative basement-flexure/shear signal, paired with footwall residual uplift and a hanging-wall gravity moat. The geological rationale is blind piedmont slip flexing the buried basement and footwall pediment after fan aggradation obscures a narrow scarp—faults that may be missing from the USGS/INGENIOUS catalogue because no narrow surface trace is preserved. It differs from prior `H86I-HVFD` use of an unsigned isotropic basement biharmonic. **Expected holdout-DTI improvement potential:** medium-high (qualitative, conditional on the signed cross-strike pattern surviving spatial holdout); **implementation cost:** low once the native stack/cache is restored. Mimics include caldera margins, pluton roofs and fluvial/glacial valley walls.
2. **Current Rank 2 — `H86P-3_RCSD` (original Rank 3; untried):** Band 6 Total Count, Band 2 RTP, and official GeoDAWN K/eTh/eU and ratio layers. Target the orientation and eigenstructure of centered-log-ratio compositional gradients to distinguish lithologic provenance juxtaposition from hydrothermal alteration near faults. Intended for buried or eroded volcanic/epithermal conduits without preserved surface scarps, hence potentially missing from mapped-fault catalogues. It extends prior scalar K/Th or U/Th gradients into a two-endmember tensor decomposition. **Expected holdout-DTI improvement potential:** moderate and geology-dependent; **implementation cost:** low–medium, plus obtaining and integrity-checking the official GeoDAWN mirror. Mimics include ash-flow-tuff boundaries, potash playas and fertilizer runoff. It is not yet data-viable because the required bytes are absent.
3. **Current Rank 3 — `H86P-4_USMT` (original Rank 4; untried, deferred):** Band 17 shallow conductance, Band 15 basement depth, and seismicity/strain bands paired with official EarthScope/USArray three-dimensional magnetotelluric conductivity. Target a deep conductive fault-root curtain aligned with shallow clay-cap termination—structures that may be concealed beneath basin fill and lack a mapped surface scarp. It adds mid-crustal depth information absent from previous near-surface lanes. **Expected holdout-DTI improvement potential:** moderate-high at regional scale but spatially coarse; **implementation cost:** medium. The required free official volume is not mirrored or hash-pinned here, and its source hosts are outside the sandbox egress allowlist. It is not proposed as obtainable until the bytes can be acquired and provenance-checked. Graphitic black shales and broad magmatic conductors are key mimics.

Only the previously tested TCWB hypothesis has holdout measurements; these three have no measured DTI. The ordering is a qualitative feasibility-adjusted research judgment, not a numerical projection. The top untried candidate, BCSF, cannot be validated from the present checkout: the native feature stack/shared cache are absent and the unchanged literal witness rule blocks every nonempty candidate. No experiment or weekly slot was used.
---

## 4. Lane `H86P-TCWB` Experimental Results (`3` Arms Executed, Zero Tuning)

### 4.1 `LEAKAGE-CANARY` (`43` Static, Ablation & Fold-Visible Planes)
- **Status:** **PASS (`43 / 43` planes `<= 0.90`, `0` leakage flags)**
- **Worst discriminative AUC:** `0.8061 <= 0.90` (`fold_visible_releasing_stepover_bridge`); worst static geophysical/topographic plane: `0.5898` (`log_cauchy_step_nodike`); DOE GDR `#1391` `dist_known_fault_px` verified strictly unread.

### 4.2 Strict 4-Fold Eroded-Domain `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `n = 11,321` Withheld Positives)

| Arm / Comparator | Evidence Class | NW | NE | SW | SE | Pooled `HOLDOUT-DTI` (`95% CI`) | Paired $\Delta$ vs `E1` (`95% CI`) |
|---|---|---:|---:|---:|---:|---|---|
| **`E1_tcwb_coupled_radial_dcelf` (Candidate)** | `HOLDOUT-DTI` | **`0.1548`** | **`0.1612`** | **`0.1871`** | **`0.1701`** | **`0.1727 [0.1560, 0.1894]`** | — |
| `E3_local_unpulled_staticek_ablation` (Control) | `HOLDOUT-DTI` | `0.1478` | `0.1254` | `0.1870` | `0.1488` | `0.1565 [0.1394, 0.1741]` | **`+0.0162 [+0.0040, +0.0286]`** (strictly `> 0`) |
| `E2_tcwb_blind_piedmont_basement_dcelf` (`0` cat inputs) | `HOLDOUT-DTI` | `0.0000` | `0.0236` | `0.0900` | `0.0961` | `0.0736 [0.0564, 0.0910]` | `+0.0991 [+0.0793, +0.1190]` |
| `R0_D28_visible_collar` (`GEMSDOE28` baseline) | `HOLDOUT-DTI` | `0.0246` | `0.0298` | `0.0215` | `0.0344` | `0.0273 [0.0216, 0.0338]` | `+0.1454 [+0.1286, +0.1621]` |
| `H33_visible_collar` (`GEMSDOE32` baseline) | `HOLDOUT-DTI` | `0.0032` | `0.0044` | `0.0029` | `0.0040` | `0.0036 [0.0022, 0.0052]` | `+0.1691 [+0.1525, +0.1858]` |
| Prior `main` `H86M-SLCQ` (`37,654` dots) | `HOLDOUT-DTI` | `0.1667` | `0.1497` | `0.1458` | `0.1528` | `0.1527 [0.1364, 0.1679]` | `E1` leads by **`+0.0200`** |
| Prior `H86I-KSAD` (`37,654` dots) | `HOLDOUT-DTI` | — | — | — | — | `0.1671 [0.1497, 0.1835]` | `E1` leads by **`+0.0056`** |
| Prior `H86C-KSLB` (`44,090` dots) | `HOLDOUT-DTI` | — | — | — | — | `0.1241 [0.1072, 0.1422]` | Separated 95% CIs (`0.1560 > 0.1422`) |

### 4.3 Read-Only Off-Catalogue `SGMC-PROXY-DTI` (`51,648` USGS SGMC Bedrock Fault Pixels `> 300 m` Off-Catalogue)
- **`E2_tcwb_blind_piedmont_basement_dcelf` (`0` known-fault inputs):** **SGMC-PROXY-DTI = `0.0954`** vs locally recomputed H33 and D28 proxy comparators (SGMC-PROXY-DTI = `0.0937` each). This is an off-catalogue diagnostic comparison only—not a leaderboard result or organizer-confirmed score.
- **`E1_tcwb_coupled_radial_dcelf`:** `0.0809` (beats `E3` local unpulled ablation `0.0650` by **`+0.0159`**; lower than pure-blind `E2` because unconstrained global Dinkelbach-CELF places `66.7%` of `E1` dots in `[3, 10] px` stepover corridors vs `33.3%` at `> 1 km`).

### 4.4 Full-Registry (`711 / 713`), Focus-9 (`27 / 27`) & PR #179 Uniqueness Audit (`REGISTRY-MEASUREMENT`)
- **Pre-placement continuous surface (`711` valid-grid rasters measured, `0` missing):** worst Spearman `rho = 0.4797 <= 0.90` (**`0` firings**).
- **Final binary dots (`37,654` dots):**
  - Byte-unique & pixel-unique across all `711` measured rasters.
  - **`0 / 469` firings `> 0.70`** across all `469` discrete `<= 90k`-dot submissions in the restored 92-repo universe (`worst = 0.6986 <= 0.70` vs `GEMSDOE37` 80k-dot raster).
  - **`0 / 27` firings `> 0.70`** across all `27` Focus-9 rasters (`0.2735` vs `GEMSDOE32` `H33`; `0.2791` vs `GEMSDOE36`; `0.2858` vs `GEMSDOE28`/`31` `H27-4`; `0.2905` vs `GEMSDOE25`/`30` `D28`; `0.2913` vs `GEMSDOE33`; `0.3046` vs `GEMSDOE24` `h25-1`; `0.3286` vs `GEMSDOE27` `topo-gap`; `0.6205` vs `GEMSDOE25` `h66`).
  - **`0.6398 <= 0.70`** 3-px overlap against unmerged PR #179 (`H86N-SHPB`).
  - **Fail-closed stop triggers (`verdict = "negative"`, `DO NOT SUBMIT`):** literal continuous witness `17GEMSDOE` (`1.0000`), `19` space-filling lattices (`> 70%` halo coverage), `8` ultra-dense `246k–985k`-dot archive scatter rasters, and `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`).

---

## 5. Historical H86P execution — three-pass verification log

The following records the earlier H86P experiment session; it is not a claim that this current re-review restored or executed those inputs again.

- **Pass 1 (Implementation & Execution):** Restored and SHA-verified competition rasters (`training_features.tif`, `sample_submission.tif`, `existing_faults.tif`), all 11 externalUSGS/OpenEI inputs, and all `655 / 655` accessible registry rasters (`IR-86P-RESTORE-INVENTORY-DUP-SHA` fixed in `scripts/restore_registry_inventory.py`); synced 2026-10-26 `GEMSDOE91`/`92` feed (`119` scored claims in `registry/prior_scores.csv`); froze `registry/h86p_hypotheses_20261026.json` and `research/H86P_TCWB_PREREGISTRATION.json`; implemented `src/gems86_tcwb/` (`operators.py`, `features.py`, `model.py`) and `scripts/run_h86p_tcwb.py`; executed the 3-arm preregistered experiment (`HOLDOUT-DTI = 0.1727 [0.1560, 0.1894]`) and generated validated `-zeros` GeoTIFF + ZIP + JSON receipt.
- **Pass 2 (Edge-Case, Assumption & Leakage Review):** Caught and prevented `IR-86M-STDP-QUAD-SEAM` by using `gems57.holdout.quadrant_ids(fp)` (`ym=936, xm=1504`) with `12 px` training-domain erosion (`2.4 km` total dead-zone) while predicting seamlessly across all 4 quadrant masks; verified `Band 6 = tc`, `Band 10 = deq_n100a15` (distance -> inverted via `exp(-d/median)`), `Band 16 = ieq_n100a15` (intensity), `Band 11 = +dg/drow_S`, `Band 18 = +dg/dx_E`, and `spin2_from_row_col_grad(dr_south, dc_east)` azimuth convention; cleaned redundant ternary in `src/gems86_tcwb/features.py`; wrote `tests/test_h86p_tcwb.py` testing CLR multiplicative scale invariance, downslope TC polarity, gravity-signed basement hinge mimic suppression, clay-cap one-sided polarity, eroded LOQO separation, and run-card / artifact invariants.
- **Pass 3 (Full Prompt Audit, Site Polish & Snapshot Hygiene):** Synchronized `docs/evidence/download-inventory.json`, `registry/artifact_cards.json`, `scripts/audit_release.py`, `docs/evidence/latest-review-run-card.json`, `README.md`, and `scripts/build_site.py` (including Focus-9 executive summaries, `GEMSDOE32` `0.2778` forensic summary, and DrivenData step-by-step submission guide subpage); verified all `7/7` gates in `scripts/review_repository.py`; unlinked untracked heavy caches (`data/training_features.tif`, `data/bridge/training_features.tif`, `data/registry_ext/`, `/tmp/focus9_inspect`) prior to turn completion.

## 6. Current review — three passes and handoff (2026-10-26)

1. **Pass 1 — evidence, inputs and protocol.** Installed the repository's locked Python dependencies, ran `scripts/audit_workspace_inputs.py` (snapshot: [`docs/evidence/current-workspace-input-audit-20261026.json`](../docs/evidence/current-workspace-input-audit-20261026.json)), restored only the SHA-pinned historical witness and proof inputs (`scripts/restore_protocol_data.py --include-registry`), and ran `scripts/protocol_preflight.py`. The native feature TIFF, prepared arrays and shared feature cache are absent. The measured witness is positive over all `5,106,385` allowed pixels (`0` uncovered; direct-support overlap `1.0`), so the unchanged literal `>0.70` rule returns `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. This is one witness sufficient for a negative stop, not a complete-registry uniqueness pass. No model experiment, TIFF, or slot was used.
2. **Pass 2 — scientific interpretation and content.** Re-read [`research/H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md), the H86P preregistration/run card, shared DTI implementation and Focus-9 report. Corrected the H33 causal claims and pruning inequality, withdrew the unsupported live-score roadmap, distinguished OWNER-REPORTED claims from HOLDOUT-DTI and SGMC-PROXY-DTI, and logged `IR-86-H33-INTERPRETATION-01`. Rank 2 BCSF is the top untested, native-band hypothesis; Rank 3 requires absent USGS GeoDAWN mirror bytes; Rank 4 USMT remains blocked by the egress allowlist and absent source volume.
3. **Pass 3 — publication order, release audit and tests.** Replaced stale current-status wording in `PROMPT.md`, corrected the 2026-10-26 archive heading while preserving the full owner prompt in `README.md`, moved the current H86P negative/download-only banner before historical H86N/H86L banners in the site generator, and added regression tests for order and download/submission labels. The first integrated run exposed four stale test assumptions (the old request path, prior homepage wording, and the witness's former location); those tests now match the current prompt and pinned restore layout. The final `make all` is green: `audit_release.py --measure-registry` reports `audit_ok=true`, decision `DO NOT SUBMIT`, `43/43` locally valid artifacts, `0` experiments and `0` slots; `build_site.py`, its `--check`, `check_site.py`, and `audit_downloads.py` all pass (43 TIFFs/receipts); full pytest reports `1,085 passed, 24 skipped, 58 subtests passed` (48 Rasterio deprecation warnings).

**Current file decision:** the inherited H86P-TCWB TIFF is safe to download for research/audit only; **it is not okay to submit**. This review created no replacement TIFF. The machine-readable no-lane/current-negative card is [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json). No full-registry clearance, new HOLDOUT-DTI, organizer-confirmed result, live score projection or remaining-slot determination is claimed.

### Limitations and next steps

- No new experiment can run from this checkout: `training_features.tif`, the native prepared arrays, and the verifiable shared feature cache are missing. Restore required inputs through the pinned protocol pipeline only; do not rebuild or relabel a private stack as the shared cache.
- The literal full-support witness blocks every nonempty allowed candidate. Do not change the 0.90 correlation / 0.70 overlap rules, bypass `require_feasible()`, place a TIFF, or select a slot. Any change to this rule needs an explicit owner decision and a documented protocol revision.
- Focus-9 and fleet leaderboard values—including H33 `0.2778`—remain OWNER-REPORTED without organizer receipts. The current review did not access/scrape DrivenData; live performance and quota are unknown.
- After inputs and protocol are resolved: read the full README prompt; assign one method lane; preregister 3–5 hypotheses; verify official mirror hashes; test each feature alone for AUC leakage; run whole-segment buffered hide-and-recover on the shared evaluator with pooled DTI and paired CIs; check correlation before placement and overlap after placement; finish with a JSON card. Keep every negative result and use a separate selector only after every mandatory gate passes.
