# Session 2026-10-27 Review — Lane `H86S-DWAD`, Focus-9 & 12-Sibling-Org Executive Forensics, Fleet Estimator v3 (`n=29`), and 3-Pass Audit

- **Date (UTC):** `2026-10-27`
- **Branch:** `arena/8074001e-gemsdoe86`
- **Newest Unique Artifact (`docs/downloads/`):** `gems86-h86s-dwad-dcelf-37654dots-20261027T182859Z-22804bdb-zeros.tif`
  - **SHA-256 (`.tif`):** `cb66bc028b149d5f895453c0573fea63ec3729d8ca25c3f5ce9b5fb215af4b0d` (`138,212` bytes)
  - **Companion `.zip` / `.json` receipt:** `gems86-h86s-dwad-dcelf-37654dots-20261027T182859Z-22804bdb-zeros.zip` / `.json`
  - **Canonical Run Card:** [`docs/evidence/h86s-dwad-run-card.json`](../docs/evidence/h86s-dwad-run-card.json)
  - **Automated Human-Free Verdict:** **`DO NOT SUBMIT`** (`verdict = "negative"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`, `experiments_run = 3`; safe to download for research/audit reproducibility only).

---

## 1. Prior-Session Next-Steps Execution (Worked First)

Before designing any new experiment, we audited [`SESSION_20261026_H86R_SFG_REVIEW.md`](SESSION_20261026_H86R_SFG_REVIEW.md), [`SESSION_20261026_H86Q_BFRA_REVIEW.md`](SESSION_20261026_H86Q_BFRA_REVIEW.md), and [`SESSION_20261026_WORKSPACE_REVIEW.md`](SESSION_20261026_WORKSPACE_REVIEW.md) and executed their queued next steps in order:

1. **Full 655/655 Upstream Registry + SHA-Pinned External Cache Restored:** Restored all competition inputs, all 11 external USGS 3DEP / GeoDAWN / DOE GDR `#1391` / SGMC layers into `.cache/external/` (confirming `dem10_chi_100m_i16.tif`, SHA-256 `8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5`, was already pinned in `scripts/restore_data.py::EXTERNAL_PINS`), and all `655/655` accessible external registry rasters (`728,345,463` bytes) via `scripts/restore_registry_inventory.py --receipt .cache/registry-inventory-restore.json` without mutating tracked `data/prepared_manifest.json` (`IR-86S-LIVE-PREP-MANIFEST-20261026`).
2. **Executed Top Queued Next Steps from `H86R-SFG` & `H86Q-BFRA` Together in One Clean Preregistered Lane (`H86S-DWAD`):**
   - `H86R` Next Step #1 (`DWPU` — observability-weighted exposure-deconfounded PU negative sampling $w_{\text{neg}} = O(x)^{1.25}$);
   - `H86R` Next Step #2 & `H86Q` Rank-3 (`KNDS` — downslope canyon-mouth fluvial knickzone back-projection `800–1,500 m` onto `Band 15` alluvial-apex steps);
   - `H86Q` §6 Next Steps #1–2 (prior-weighted quadrant calibration $\alpha_{\text{pool}} = 0.62$ curing `SW` compression and `NE` starvation + 2-D stepover-preserving 6-ring Bernoulli Dinkelbach-CELF inside positive geodetic dilatation `Band 8 > 0`);
   - Untried geothermal sub-clay-cap feeder-margin disjunction (`Band 17` lateral log-gradient $\times$ `Band 2` magnetite-oxidation trough $\times$ `Band 5` gravity step $\times$ up-head GDR `#1391` 2-m probe/sinter/geothermometer walls).
3. **Repaired Two Inherited Repository Defects (`Own the Outcome`):**
   - `IR-86S-RUN-H86R-SFG-MISSING-PREFLIGHT-20261027`: `scripts/run_h86r_sfg.py` (merged in PR `#193`) lacked `protocol_preflight.require_feasible()` in `main()` and omitted both `run_h86q_bfra` and `run_h86r_sfg` from `tests/test_builder_preflight.py::BUILDERS`. Fixed in `scripts/run_h86r_sfg.py` and pinned in `tests/test_builder_preflight.py` alongside `run_h86s_dwad`.
   - `IR-86S-BFRA-PROSE-MT-BANDS-20261027`: `SESSION_20261026_H86Q_BFRA_REVIEW.md` §3 row 2 referred to nonexistent `Bands 16, 17, 19 (mt_500m, mt_2000m, mt_4000m)`, whereas `src/gems86/io.py::BANDS` proves `Band 16 = ieq_n100a15`, `Band 17 = cond_surf` (single MT layer), and `Band 19 = det_elev_slope`. Recorded in `IRREGULARITIES.md` and enforced via regex test on `registry/h86s_dwad_hypotheses_20261027.json`.

---

## 2. Executive Summary — Focus-9 Sites, 12 New Sibling-Org Sites, Candidate Download Table & Score Projections

Full machine-readable receipts: [`docs/evidence/focus9-and-siblings-forensics-20261027.json`](../docs/evidence/focus9-and-siblings-forensics-20261027.json) and [`docs/evidence/h86s-fleet-estimator-20261027-v3.json`](../docs/evidence/h86s-fleet-estimator-20261027-v3.json).

### 2.1 Focus-9 Executive Summary (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`)

All live scores below are **`OWNER-REPORTED`** from user prompt transcriptions (`0` `ORGANIZER-CONFIRMED` submission-page receipts exist in the workspace). Every one of the **9 Focus-9 site champions (`0.2449–0.2778`)** belongs to a **single non-unique `H19-5` emission lineage** (`86.7%–100.0%` 3-px cross-overlap) and must never be copied or re-submitted. Among **unique (`<= 70%` 3-px overlap)** Focus-9 runs, newly scored **`GEMSDOE27` `gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite` (`0.2250` `OWNER-REPORTED`)** is now `#1` in Focus-9 (up from `h29 = 0.2190`). As of `2026-10-27`, **all 9 of 9 Focus-9 sites post `DO NOT SUBMIT` / not authorized for weekly upload at `HEAD`**.

| Focus-9 Site (`HEAD` SHA) | Highest Scored Submission (`OWNER-REPORTED`) | Newly Scored / Other Runs (`OWNER-REPORTED`) | Champion Dots · Collar · `>1 km` | Unique vs Other GEMSDOE Sites? | Live `HEAD` Gate (`2026-10-27`) |
|---|---|---|---|---|---|
| **`GEMSDOE32`** (`1398109a23`) | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: **`0.2778`** (`#1` across 92 repos) | `h32d-submodular-multipysics-46090`: `0.2591` | `37,654` · `2.24 px` · **`69.8%`** | **NO** (`97.4%` vs `G36`, `95.5%` vs `G28`, pruned subset of `G25/G30`) | `DO NOT SUBMIT` |
| **`GEMSDOE36`** (`7576942352`) | `gemsdoe36-anderson-geothermal-pinn-38854-...-zeros`: **`0.2750`** | **NEW:** `gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros`: **`0.1647`** (`37,654`d, `ovH33=0.5613`, `SGMC=0.0655`, `>1km=61.5%`) | `38,854` · `2.24 px` · `69.7%` | **NO** (`0.2750` is `97.4%` vs `H33`; `kpl36` flagged `99.17%` vs `reg-052` by `G36` on `2026-10-27`) | `DO NOT SUBMIT` |
| **`GEMSDOE28`** (`67dbdf4da8`) | `gems28-h36-1-rung30-blind-r1-...-nan`: **`0.2710`** | `h27-4`: `0.2708`; `h38-1`: `0.2707`; `h32-1`: `0.2649`; `s18-mxtp`: `0.0217`; **NEW:** `gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite`: **`0.0206`** (`ovH33=0.2866`, `>1km=10.4%`, `SGMC=0.0533`) | `37,660` · `1.41 px` · `65.7%` | **NO** for `0.2710` (`95.5%` vs `H33`); **YES** for `s18` (`0.0217`) & `s21-puhgb` (`0.0206`) | `DO NOT SUBMIT` |
| **`GEMSDOE31`** (`fbebc01703`) | `gemsdoe31-h27-4-solo-d28-...-nan`: **`0.2708`** | — | `40,199` · `1.41 px` · `65.4%` | **NO** (`100.0%` pixel clone of `GEMSDOE28 h27-4`) | `DO NOT SUBMIT` |
| **`GEMSDOE33`** (`122e2240a8`) | `GEMSDOE33-h33d-analog-tip-stepover-r30`: **`0.2632`** | **NEW:** `gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros`: **`0.0963`** (`ovH33=0.3478`, `SGMC=0.0804`, `NE=2.0%` dots) | `41,865` · `1.00 px` · `63.4%` | **NO** for `0.2632` (`92.6%` vs `H33`); **YES** for `s33-seisdil` (`0.0963`) | `DO NOT SUBMIT` |
| **`GEMSDOE25`** (`5a60fb475b`) | `gems25-dotted-h19-5-d2-8-...-zeros`: **`0.2600`** | `gems25-h66-mgd-flank-...-zeros`: `0.0742` (`ovH33=0.3038`, `>1km=24.3%`) | `44,090` · `1.41 px` · `59.6%` | **NO** for `0.2600` (`100%` clone of `G30 d28` & unpruned parent of `H33`); **YES** for `h66` | `DO NOT SUBMIT` |
| **`GEMSDOE30`** (`3c3d7255fd`) | `gemsdoe30-d28-poisson300m-offcat-44090`: **`0.2600`** | `gems30-MSDB1-edge44090-20261025-e7856ec3f14a`: `0.1462` (`ovH33=0.3918`, `7.11M` ext NaNs) | `44,090` · `1.41 px` · `59.6%` | **NO** for `0.2600` (`100%` clone of `G25 d2-8`); **YES** for `MSDB1` (`0.1462`) | `DO NOT SUBMIT` |
| **`GEMSDOE24`** (`2521cb676e`) | `gems24-h25-1-dotted-h19-5-d1-5-...-nan`: **`0.2477`** | `gems24-gvc1-...-zeros`: `0.0859` (`ovH33=0.3662`, `>1km=25.7%`) | `60,069` · `1.00 px` · `59.3%` | **NO** for `0.2477` (`H19-5` `d=1.5`); **YES** for `gvc1` (`0.0859`) | `DO NOT SUBMIT` |
| **`GEMSDOE27`** (`69d6f03375`) | `gems27-topo-gap-closure-t-v2-on-d1-5-...-nan`: **`0.2449`** | **NEW #1 UNIQUE FOCUS-9:** `gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite`: **`0.2250`** (`ovH33=0.5023`, `SGMC=0.0839`, `>1km=63.1%`); `h29`: `0.2190` | `61,328` · `1.00 px` · `58.4%` | **NO** for `0.2449`; **YES** for `h31-drcg` (**`0.2250`**) & `h29` (`0.2190`) | `DO NOT SUBMIT` (Session 13: selector review only) |

### 2.2 Newly Added External-Organization Sibling Sites (`2026-10-27` Prompt)

Live tarball & API inspection across all 12 newly listed sibling repositories (`42` published `.tif` files total; cached in `.cache/focus9_and_siblings_20261027/` and checked against `H86S-DWAD` with `0` collisions):
- `kanlerxz87-cyber/KANLERGEMSDOE1` (`510b85dc74`, `10` TIFFs, unscored), `KANLERGEMSDOE2` (`c605e8fa65`, `20` TIFFs; prompt-named unscored `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` verified at SHA-256 `f482d3bad4b39047...`, `37,654` dots, `min d_cat = 2.24 px`, `38.9% > 1 km`, `ovH33 = 0.3966`, `SGMC-PROXY-DTI = 0.1116`), `KANLERGEMSDOE3` (`d9f0eb2f3a`, `4` TIFFs, unscored).
- `wingbangboozle1-lang/WBGGEMSDOE1` (`cc78f43a64`, `4` TIFFs), `WBGGEMSDOE2` (`eccb7f4961`, `1` TIFF), `WBGGEMSDOE3` (`045d2952cf`, `3` TIFFs) — all unscored.
- `eugboogieman123-ops/EUGGEMSDOE1..3` (`81ac8521ea`, `3ae1fc951e`, `8fbb61b58e`) and `ginnymcfiner23-ux/GINNYGEMSDOE1..3` (`761158ab9f`, `91d564fcda`, `4e00b89ed1`) — `0` published download TIFFs at `HEAD` and `0` reported scores.
- Also recorded in `registry/prior_scores.csv`: `GEMSDOE91` `gems91-s22-omtj-e1-20261026-a99b8923f0-zeros` = **`0.0298` `OWNER-REPORTED`** (`37,654` dots, `>1km = 76.2%`, `ovH33 = 0.1612`, `SGMC = 0.0646`) and `GEMSDOE88` unscored `gems88-bpwd88-baranov-worm-conduit-37654-20261025-b8543782-zeros-DO-NOT-SUBMIT`.

### 2.3 Candidate Download & Score-Estimation Table (`FLEET-REGRESSION-PROJECTION v3`, `n = 29`, `LOO-RMSE = 0.0355`)

Fitting leave-one-out OLS on `29` byte-verified `25k–65k`-dot `OWNER-REPORTED` submissions (`[1, ov_h33, sgmc_proxy_dti, frac_gt_1km]`, coefficients `[-0.0724, +0.2261, +0.8550, +0.0857]`, reducing `LOO-RMSE` from `0.0380` in `v2` to **`0.0355`** in `v3`):

| Downloadable File (`docs/downloads/`) | Estimated Score `[95% LOO Interval]` (`PROJECTION`, Not a Score) | `SGMC-PROXY-DTI` | `ovH33` (3-px) | `>1 km` Share | Unique vs Focus-9 & Discrete Fleet? | Automated Upload Verdict |
|---|---|---|---|---|---|---|
| **NEW (`H86S-DWAD`):** `gems86-h86s-dwad-dcelf-37654dots-20261027T182859Z-22804bdb-zeros.tif` | **`0.1161 [0.047, 0.186]`** | `0.0781` | `0.3625` | `46.4%` | **YES** (`max 0.6520` vs 474 reg; `max 0.5715` vs 487 live discrete peers) | **`DO NOT SUBMIT`** (audit only) |
| `gems86-h86m-pfte-blind-comonodcelf-37654dots-20261025T175515Z-04d0022f-zeros.tif` | `0.1570 [0.087, 0.227]` | **`0.1210`** | `0.3014` | `67.5%` | **YES** (`<= 0.70` vs `H33` & discrete peers) | **`DO NOT SUBMIT`** (audit only) |
| `gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros.tif` | `0.2132 [0.144, 0.283]` | `0.1136` | `0.5643` | `71.1%` | **YES** (`<= 0.70` vs `H33` & discrete peers) | **`DO NOT SUBMIT`** (audit only) |
| `gems86-h86k-stdp-dcelf-37654dots-20261025T145724Z-72a82f29-zeros.tif` | `0.1377 [0.068, 0.207]` | `0.1133` | `0.3126` | `49.7%` | **YES** (`<= 0.70` vs `H33` & discrete peers) | **`DO NOT SUBMIT`** (audit only) |
| `gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.tif` | `0.1273 [0.058, 0.197]` | `0.1082` | `0.2974` | `46.6%` | **YES** (`<= 0.70` vs `H33` & discrete peers) | **`DO NOT SUBMIT`** (audit only) |
| `gems86-h86j-mcsp-celf-37654dots-20261025T065104Z-b80b7702-zeros.tif` | `0.1319 [0.062, 0.202]` | `0.0999` | `0.3377` | `49.6%` | **YES** (`<= 0.70` vs `H33` & discrete peers) | **`DO NOT SUBMIT`** (audit only) |

---

## 3. PhD Forensic Answer — Why `GEMSDOE32` (`0.2778` `OWNER-REPORTED`) Scored Highest & Whether/How We Can Score Higher Uniquely

1. **Exact Metric Mechanics & Byte-Verified Lineage of `0.2778`:**
   - Under DrivenData `#306`'s Distance-Weighted Tversky Index ($\alpha = 0.2$ FP weight, $\beta = 0.8$ FN weight, $300\text{ m}$ triangular kernel $K_{300}$):
     $$\mathrm{DTI}(P, G) = \frac{\sum_{y \in G} s(y)}{\sum_{y \in G} s(y) + 0.2 \sum_{x \notin G} P(x)(1 - s(x)) + 0.8 \sum_{y \in G}(1 - s(y))}, \quad s(z) = \max_{u} P(u) K_{300}(z, u).$$
   - Because $s(y)$ uses a **`max`** operator, a single unit dot within `100–200 m` of a hidden fault recovers `67%–100%` of $K_{300}$ credit, whereas extra dots inside the `<= 2.24 px` flank of already-mapped `existing_faults.tif` mostly fall on pixels that are *not* newly added hidden labels, inflating the false-positive denominator $0.2\,\mathrm{FP}_w$.
   - Byte-exact set algebra across the `H19-5` family proves: `H19-5` (`121,131` px, `0.1922`) $\to$ `d=1.5` (`60,069` dots, `0.2477`) $\to$ `d=2.8` (`44,090` dots, `0.2600`) $\to$ prune `d_cat <= 1 px` (`40,199` dots, `0.2708`) $\to$ prune `d_cat <= 2 px` (**`37,654` dots = `GEMSDOE32 H33`, `0.2778`**). Deleting those `6,436` near-catalogue dots trimmed pure $\mathrm{FP}_w$ denominator bloat while retaining `69.8%` off-catalogue `>1 km` coverage.
2. **What Today's 5 New Live Scores Prove Causally (`2026-10-27` Natural Experiment):**
   - **Failure Mode 1 — Survey-Exposure Collapse (`GEMSDOE28 s21-puhgb = 0.0206`):** Naive PU-HGB placed `89.6%` of its `37,654` dots within `1 km` of mapped range-front faults (`median d_cat = 412 m`), failing catastrophically on hidden off-catalogue labels (`0.0206`).
   - **Failure Mode 2 — Regional Quadrant Starvation (`GEMSDOE33 s33-seisdil = 0.0963`):** Despite `65.5% > 1 km` and `SGMC = 0.0804`, uncalibrated seismicity/strain placed `86.8%` of dots in `SW+SE` and only **`2.0%` in `NE`**, starving northern Great Basin faults (`0.0963`).
   - **Failure Mode 3 — High `>1 km` Share Without Subsurface Precision (`GEMSDOE91 s22-omtj = 0.0298`):** Placed `76.2% > 1 km` off catalogue (`ovH33 = 0.1612`), yet its underlying detector (`SGMC = 0.0646 < 0.0754` random uniform null) missed real bedrock structures and scored **`0.0298`**.
   - **Positive Proof (`GEMSDOE27 h31-drcg = 0.2250`):** Combining dual-regime subsurface+exposed features, balanced regional shares (`NW=26.9%, NE=20.3%, SW=32.2%, SE=20.6%`), `63.1% > 1 km`, and `SGMC = 0.0839` lifted live score to **`0.2250`** while *lowering* `H33` overlap (`0.5612 -> 0.5023 <= 0.70`).
3. **Can We Generate a Unique Submission Above `0.2778` (and Note on `0.3195` / `0.4413` / `0.4437`)?**
   - First, `0.3195` and `0.4413` (and a peer README mention of `0.4437`) are conflicting unverified external leaderboard quotes with zero receipts in this repository; `0.2778` remains the highest `OWNER-REPORTED` `GEMSDOE` fleet result.
   - Second, **honest scientific assessment:** no unique (`<= 0.70` overlap) raster currently in `GEMSDOE86` has an honest point projection above `0.2778` (`Fleet Estimator v3` peaks at `0.2132 [0.144, 0.283]` on `H86M-LT` and `0.1570 [0.087, 0.227]` on `H86M-PFTE E2`).
   - Third, **exact quantitative path to surpass `0.2778` uniquely:** under Fleet Estimator v3 (`coef_SGMC = +0.855`), a genuinely independent candidate (`ov_h33 ~ 0.30–0.45`, `frac_gt_1km ~ 0.65–0.70`) requires raising off-catalogue bedrock/subsurface fault recovery from `SGMC ~ 0.08–0.12` to **`SGMC >= 0.19–0.23`** — which requires pre-staging external high-resolution spaceborne geodetic/thermal/crustal-EM observables (Sentinel-1 InSAR velocity steps, 3-D USMTArray phase-tensor skew, and predawn ASTER TIR thermal/sinter reststrahlen scenes) onto `EPSG:32611` alongside observability-weighted PU learning.

---

## 4. Ranked Untried Candidate Hypotheses (`registry/h86s_dwad_hypotheses_20261027.json`) & `H86S-DWAD` Validation Results

Four genuinely untried hypotheses were declared prior to model execution in [`registry/h86s_dwad_hypotheses_20261027.json`](../registry/h86s_dwad_hypotheses_20261027.json) and [`research/H86S_DWAD_PREREGISTRATION.md`](H86S_DWAD_PREREGISTRATION.md):
1. **Rank 1 (`H86S-1_DWAD` — Executed):** Detectability-Weighted Exposure-Deconfounded PU + Downslope Canyon-Mouth Fluvial Knickzone Back-Projection (`KNDS`) + Sub-Clay-Cap Hydrothermal Feeder-Margin Disjunction + Dual-Regime Stepover-Preserving 6-Ring Dinkelbach-CELF (`VIABLE_IN_SANDBOX_NOW`).
2. **Rank 2 (`H86S-2_EULER3D` — Queued):** Joint Magnetic (`Bands 2, 3, 9, 14`) & Vector-Gravity (`Bands 11, 13, 18`) 3-D Euler Deconvolution $N=0$ Contact Clustering concordant with `depth_to_base_surf (Band 15)` (`VIABLE_IN_SANDBOX_NOW`).
3. **Rank 3 (`H86S-3_COULOMB_CONJ` — Queued):** Anderson–Mohr–Coulomb Conjugate Critical-Stress Slip & Dilatation Tendency on Blind Transtensional Accommodation Lineaments (`Bands 2, 4, 7, 8, 10, 11, 16, 17, 18`; `VIABLE_IN_SANDBOX_NOW`).
4. **Rank 4 (`H86S-4_ASTER_TIR_SINTER` — Deferred External Data):** Predawn Radiative-Cooling-Corrected NASA/USGS ASTER `AST_08` Nighttime Thermal Inertia & `AST_05` TIR Quartz-Opaline Sinter Reststrahlen Emissivity Index (`https://doi.org/10.5067/ASTER/AST_08.003`, `https://doi.org/10.5067/ASTER/AST_05.003`, USGS Great Basin Heat-Flow `https://www.sciencebase.gov/catalog/item/589097b9e4b072a7ac132312`; `BLOCKED_SANDBOX_EGRESS`).

### `H86S-DWAD` Experimental Results (`<= 3` Arms, Zero Post-Holdout Tuning)

| Arm (`37,654` dots, `d_min = 2.8 px`, `d_cat > 3.0 px`) | Pooled `HOLDOUT-DTI` `[95% CI]` (`n=11,321`) | `NW` | `NE` | `SW` | `SE` | `SGMC-PROXY-DTI` `[95% CI]` | `>1 km` Share |
|---|---|---|---|---|---|---|---|
| **`E1_dwad_deconfounded_dualregime_dcelf` (Serialized Audit TIFF)** | **`0.1195 [0.1040, 0.1368]`** | `0.0886` | `0.1030` | `0.1167` | **`0.1581`** | **`0.0781 [0.0628, 0.0942]`** | `46.44%` |
| **`E2_dwad_zero_catalogue_blind_dcelf` (Pure Zero-Catalogue Blind)** | **`0.0825 [0.0679, 0.0984]`** *(New Repo Blind Record)* | `0.0553` | `0.0764` | `0.0681` | **`0.1226`** | `0.0770 [0.0609, 0.0928]` | `63.30%` |
| **`E3_unweighted_unadvected_local_ablation` (Control)** | `0.1230 [0.1078, 0.1366]` | `0.1222` | `0.1185` | `0.1385` | `0.1088` | `0.0700 [0.0574, 0.0837]` | — |
| `R0_D28_visible_collar` (`GEMSDOE28`) | `0.0273 [0.0241, 0.0306]` | `0.0246` | `0.0298` | `0.0215` | `0.0344` | `0.0937 [0.0809, 0.1080]` | `59.6%` |
| `H33_visible_collar` (`GEMSDOE32`) | `0.0036 [0.0029, 0.0044]` | `0.0032` | `0.0044` | `0.0029` | `0.0040` | `0.0937 [0.0809, 0.1080]` | `69.8%` |

- **Key Scientific Takeaways:**
  1. **New Repository Pure-Blind Record (`E2 = 0.0825`):** Without a single catalogue geometry feature at inference, `E2` achieved `HOLDOUT-DTI = 0.0825 [0.0679, 0.0984]`, surpassing every prior 37,654-dot pure-blind DCELF arm in `GEMSDOE86` (`H86M-SLCQ = 0.0755`, `H86P-TCWB = 0.0736`, `H86Q-BFRA = 0.0734`, `H86M-PFTE = 0.0681`, `H86K-STDP = 0.0655`).
  2. **First Coupled `E1` to Clear All 970 Discrete Registry + Live Peer Overlap Checks (`<= 0.70`):** Worst 3-px dot overlap is `0.6520` across all `474` restored discrete `<=90k` rasters (`0.3625` vs `GEMSDOE32 H33`) and `0.5715` across all `487` discrete (`496` total) live Focus-9 & sibling-org rasters; pre-placement surface Spearman max is `0.4957 <= 0.90` (`716` registry rows) and `0.3452 <= 0.90` (`496` live peer rows).
  3. **Honest Gate Failure (`DO NOT SUBMIT`):** While `E1` crushed `E3` by **`+0.0493` on `SE`** (`0.1581 vs 0.1088`) and beat `E3` (`0.0781 vs 0.0700`) and the random null (`0.0754`) on `SGMC-PROXY-DTI`, enforcing `dual_regime_blind_floor_weight >= 0.52` traded near-tip `<600 m` halo density in `NW/NE/SW`, leaving pooled `E1 - E3 = -0.0034 [-0.0208, +0.0168]`. Combined with the active repo-wide literal `17GEMSDOE` full-support witness stop (`1.0000`), `H86S-DWAD` is strictly marked **`DO NOT SUBMIT`** (`verdict = "negative"`).

---

## 5. Limitations & Verified Official Public Sources

### Current Sandbox & Project Limitations
1. **Network Egress Allowlist:** Outbound network access is restricted to `github.com`, `codeload.github.com`, `api.github.com`, `pypi.org`, `files.pythonhosted.org`, and `registry.npmjs.org`. DrivenData (`https://www.drivendata.org/competitions/306/competition-doe-gems/`), DOE GDR (`https://gdr.openei.org/submissions/1391`), USGS ScienceBase, and NASA/USGS LP DAAC cannot be queried directly from inside the sandbox; external datasets (`H86S-4_ASTER_TIR_SINTER`, `H86Q-4_SENT1_USMT`) must be mirrored and SHA-256-pinned offline first.
2. **Unverified Live Scores & Account Quota:** All `129` scored entries in `registry/prior_scores.csv` are `OWNER-REPORTED` (`0` `ORGANIZER-CONFIRMED` submission-page receipts), and remaining weekly DrivenData submission slots are observable only to a logged-in human on DrivenData.
3. **Literal `17GEMSDOE` Full-Support Witness:** `17GEMSDOE` (`ab0a0a62...`) has positive support across `100%` of allowed footprint pixels, mathematically forcing `1.0000 > 0.70` 3-px overlap on any nonempty prediction until the owner explicitly scopes uniqueness to discrete `<= 90k`-dot submissions.

### Line-by-Line Official Verified Sources
- **Competition Specification & Rules:** DrivenData Competition `#306` (DOE GEMS) (`https://www.drivendata.org/competitions/306/competition-doe-gems/`) and NREL Technical Report `NREL/TP-5700-96647` (`https://docs.nlr.gov/docs/fy26osti/96647.pdf`).
- **Regional Geothermal Play Fairway & INGENIOUS Data:** DOE Geothermal Data Repository Submission `#1391` (`https://gdr.openei.org/submissions/1391`, SHA-256 verified in `.cache/external/`).
- **Airborne Magnetics & Gamma-Ray Radiometrics:** USGS GeoDAWN (`https://doi.org/10.5066/P9X65X7E`, SHA-256 verified in `.cache/external/`).
- **High-Resolution Elevation & Fluvial $\chi$/$k_{sn}$ Geomorphometry:** USGS 3D Elevation Program (`https://www.usgs.gov/3d-elevation-program`, SHA-256 verified `lidar_scarp_features_u8.tif`, `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_i16.tif`).
- **Off-Catalogue Bedrock Fault Diagnostic (Read-Only):** USGS State Geologic Map Compilation (`https://doi.org/10.3133/ds1052`, SHA-256 verified `derived_sgmc_faults_100m_u8.tif`).
- **Deferred External Public-Domain Targets (`H86S-4`):** NASA/USGS LP DAAC ASTER `AST_08` (`https://doi.org/10.5067/ASTER/AST_08.003`), `AST_05` (`https://doi.org/10.5067/ASTER/AST_05.003`), and USGS Great Basin Heat-Flow (`https://www.sciencebase.gov/catalog/item/589097b9e4b072a7ac132312`).

---

## 6. Three-Pass Engineering & Scientific Review Log

- **Pass 1 — End-to-End Implementation & Execution:**
  - Restored and SHA-256-verified all competition, external (`11/11`), lane, and external registry (`655/655`) inputs plus `497` live Focus-9, `GEMSDOE91`, and 12-sibling-org `.tif`s.
  - Preregistered 4 untried hypotheses (`registry/h86s_dwad_hypotheses_20261027.json`, `research/H86S_DWAD_PREREGISTRATION.json`), implemented `src/gems86_dwad/` and `scripts/run_h86s_dwad.py`, executed all 3 frozen arms, verified 37-plane leakage canary (`max AUC = 0.7772 <= 0.90`), 716-registry + 496-live-peer surface & dot uniqueness, serialized `gems86-h86s-dwad-dcelf-37654dots-20261027T182859Z-22804bdb-zeros.tif` + `.zip` + `.json`, fit Fleet Estimator v3 (`n=29`, `LOO-RMSE = 0.0355`), and updated `prior_scores.csv` (`129` scored claims), `ledger/submissions.csv`, `fleet-feed.json`, and `scripts/build_site.py`.
- **Pass 2 — Bug, Edge-Case, and Inherited-Defect Audit & Fixes:**
  - Found and fixed `IR-86S-RUN-H86R-SFG-MISSING-PREFLIGHT-20261027` in `scripts/run_h86r_sfg.py` (`main()` now enforces `require_feasible()` before any I/O) and added `run_h86q_bfra`, `run_h86r_sfg`, and `run_h86s_dwad` to `tests/test_builder_preflight.py::BUILDERS` and subprocess fail-closed checks.
  - Found and documented `IR-86S-BFRA-PROSE-MT-BANDS-20261027` in `IRREGULARITIES.md`, and added band-index regex verification for `registry/h86s_dwad_hypotheses_20261027.json` in `tests/test_fleet_feed.py`.
  - Hardened `_log()` in `scripts/run_h86s_dwad.py` against `BrokenPipeError` on closed stdout pipes and added synthetic-grid unit tests (`tests/test_h86s_dwad.py`) covering survey observability, downslope canyon-mouth knickzone advection, sub-clay-cap feeder-margin disjunction, prior-weighted quadrant blending, and banned-column enforcement.
- **Pass 3 — Full Line-by-Line Verification Against Standing Request & Snapshot Hygiene:**
  - Re-ran `audit_release.py --measure-registry`, `build_site.py`, `build_site.py --check`, `audit_downloads.py --write`, `audit_downloads.py`, `check_site.py`, `build_ledger.py --check`, full `pytest -q`, and `review_repository.py`.
  - Unlinked untracked bulk working files under `data/` (`data/registry_ext/`, `data/training_features.tif`, etc.) after completing all full-registry measurements so `git status` is clean and workspace snapshot size stays well below the 128 MB cap.

---

## 7. Next-Session Recommendations

1. **Test Queued `H86S-2_EULER3D` + `H86S-3_COULOMB_CONJ` Coupled onto the `H86S-DWAD E2` (`0.0825`) Blind Core with Distance-Gated Near-Tip Coupling:** In `H86S-DWAD`, `E2` set a new blind record (`0.0825`), while `E1` trailed `E3` (`0.1195 vs 0.1230`) only because `w_blind >= 0.52` was enforced even at `3.1–7.0 px` ahead of visible tips. Using `w_blind ~ 0.25` strictly inside `3–7 px` conjugate tip-cones and ramping `w_blind -> 0.85` at `d_vis > 8 px` should preserve `0` discrete overlap firings (`<= 0.70`) while lifting coupled `HOLDOUT-DTI` above `0.165+`.
2. **Stage External Public-Domain ASTER Nighttime TIR + Sentinel-1 InSAR + USMTArray (`H86S-4` / `H86Q-4`):** Mirror and SHA-256-pin `EPSG:32611` (`3730x3292`) rasters on an unrestricted machine to break through the native-19 + 3DEP/GeoDAWN off-catalogue `SGMC-PROXY-DTI ~ 0.12` ceiling toward `>= 0.19`.
