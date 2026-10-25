# Session Review — 2026-10-25 (`H86N-GSST` Lane & `H86M-LT` Reconciliation, Branch `arena/b623d71a-gemsdoe86`)

## 1. Immediate Decision & Deliverable Summary

- **Is any GeoTIFF in this repository OK to submit to DrivenData right now?**
  **NO — `DO NOT SUBMIT` (`verdict = "negative"`, `submission_ready = false`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`).**
- **Is the newly generated GeoTIFF safe to download for local audit and reproducibility?**
  **YES — audit download only (`15 / 15` shared validator checks PASS, `37 / 37` repository artifacts locally format-valid).**
- **New unique GeoTIFF generated in this session (`H86N-GSST`):**
  * **File:** [`docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.tif`](../docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.tif)
  * **One-TIFF ZIP:** [`docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.zip`](../docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.zip)
  * **Writer receipt:** [`docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.json`](../docs/downloads/gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z-zeros.json)
  * **Run card:** [`docs/evidence/h86n-gsst-run-card.json`](../docs/evidence/h86n-gsst-run-card.json)
  * **SHA-256:** `ee7a14a602d6db0a08704d652aecee1493fb452c417597e232ccf8157af1e5b2` (`118,958` bytes)
  * **Submission name (`<= 64` chars, identity only):** `gems86-h86n-gsst-stepshape-37654dots-20261025T183736Z`
  * **Submission note (`92 <= 140` chars, identity only):** `H86N-GSST gravity step-vs-compact shape dotted 37654; HOLDOUT-DTI in run card; DO NOT SUBMIT`
  * **Automated format & range verification (zero human intervention):** single-band `float32`, `EPSG:32611`, shape `3730 × 3292` at `100 m` resolution, affine geotransform `[100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]` matching `sample_submission.tif`, `nodata = None`, `n_nan = 0`, `n_infinite = 0`, `min = 0.0`, `max = 1.0`, `emitted_positive_pixels = 37,654` strictly inside footprint, `0` positive pixels outside footprint, `0` positive pixels on mapped faults (`existing_faults.tif`).

---

## 2. Four Preregistered Untried Geological Hypotheses (`registry/h86n_hypotheses.json`)

Before running any experiment, we inspected `registry/followup_hypotheses_20261025.json` and recent merges (PR #157 executed `H86M-BMR` and `H86M-CNT`, leaving only `GSST` unrun from that 3-item queue) and preregistered four ranked, untried native-band geological hypotheses in [`registry/h86n_hypotheses.json`](../registry/h86n_hypotheses.json) and [`research/H86N_GSST_PREREGISTRATION.md`](H86N_GSST_PREREGISTRATION.md):

1. **`H86N-GSST` (Rank 1 — Selected & Executed This Session): Multi-Scale Gravity Step-versus-Compact-Source Shape Test**
   - **Layers:** Band 13 (`iso_grav_anom`, $g$), Band 5 (`iso_grav_anom_slope`, $|\nabla_H g|$), Band 11 (`iso_grav_anom_vg`, $+\partial g/\partial\text{row}_{\text{south}}$), Band 18 (`iso_grav_anom_hg`, $+\partial g/\partial\text{col}_{\text{east}}$).
   - **Physical signature & transform:** For scales $\sigma \in \{3, 6\}\text{ px}$ ($300\text{ m}, 600\text{ m}$), let $\mathbf{u}_\sigma = G_\sigma * (+\text{B18}, +\text{B11})$ and unit gradient normal $\hat{\mathbf{n}} = \mathbf{u}_\sigma / (|\mathbf{u}_\sigma| + \varepsilon)$. An extended buried basement fault step maintains one-sided cross-strike flank gradients ($\min(g_n(\mathbf{x}+\sigma\hat{\mathbf{n}}), g_n(\mathbf{x}-\sigma\hat{\mathbf{n}})) > 0$), positive potential step drop $g(\mathbf{x}+\sigma\hat{\mathbf{n}}) - g(\mathbf{x}-\sigma\hat{\mathbf{n}}) > 0$, along-strike normal coherence at $\pm 1.5\sigma\hat{\mathbf{s}}$, and low radial normal divergence $|\nabla \cdot \hat{\mathbf{n}}|$, whereas compact 3-D intrusive plugs or symmetric ridges reverse flank gradient sign or curve rapidly.
   - **Why it catches unmapped faults:** Play Fairway and INGENIOUS gravity inversions show that basin-interior intra-graben accommodation faults and buried range-front relay steps are expressed as extended one-sided density steps beneath unbroken Quaternary alluvium where surface scarp mapping is blind.
   - **Named non-fault mimic:** Elongated lithologic/intrusive contacts and basin-margin alluvial-fan density ramps producing a one-sided density step without brittle fault offset.

2. **`H86N-EQL` (Rank 2 — Deferred Behind Rank 1): Shallow-to-Intermediate Earthquake Lineament Tensor Anisotropy × Geodetic Shear Stress Alignment**
   - **Layers:** Band 10 (`deq_n100a15`), Band 12 (`ieq_n100a15`), Band 19 (`meq_n100a15`), Band 8 (`geod_maxshear`), Band 7 (`geod_2ndinv`).
   - **Physical signature & transform:** Multi-scale structure tensor anisotropy $\mathcal{A}_{\text{eq}} = (\lambda_1 - \lambda_2)/(\lambda_1 + \lambda_2 + \varepsilon)$ of the shallow-over-deep seismicity excess $\log(1+\text{B10}) + 0.5\log(1+\text{B12}) - 0.5\log(1+\text{B19})$ multiplied by Band 8 `geod_maxshear`.
   - **Named non-fault mimic:** Geothermal production/injection microseismic swarms, mining blasts, or volcanic-dike earthquake clusters.

3. **`H86N-MTC` (Rank 3 — Deferred Behind Rank 1): Magnetotelluric Upper-to-Lower Crustal Conductance Ratio Gradient × Heat-Flow Upflow Step**
   - **Layers:** Band 16 (`mt2023_con9 km`), Band 2 (`mt2023_con15 km`), Band 1 (`mt2023_con30 km`), Band 14 (`heatflow`), Band 15 (`basement_depth`).
   - **Physical signature & transform:** Spatial gradient magnitude $|\nabla_H \mathcal{R}_{9/30}|$ of the log upper-to-lower crustal conductance ratio $\log((\text{B16}+\varepsilon)/(\text{B1}+\varepsilon))$ multiplied by positive sediment-blanket-adjusted heat-flow residual.
   - **Named non-fault mimic:** Conductive play-lake evaporite/clay pans and stratabound volcano-sedimentary tuff aquifers.

4. **`H86N-DSR` (Rank 4 — Deferred Behind Rank 1): Dilatational-to-Shear Strain Partition Ratio Across Basement Depth Inflections**
   - **Layers:** Band 17 (`geod_dilaterate`), Band 8 (`geod_maxshear`), Band 7 (`geod_2ndinv`), Band 15 (`basement_depth`).
   - **Physical signature & transform:** Positive dilatational strain partitioning fraction $\mathcal{P}_{\text{dil}} = \max(0, \text{B17}) / (|\text{B17}| + \text{B8} + \varepsilon) \times \text{rankpct}(\text{B7})$ co-located with basement-depth inflection crests $|\nabla_H \text{B15}|$.
   - **Named non-fault mimic:** Long-wavelength GPS interpolation lobes and nontectonic hydrological/pumping basin subsidence bowls.

---

## 3. Experimental Validation of `H86N-GSST` (`HOLDOUT-DTI`, Canaries, and Uniqueness)

### 3.1 Spatially-Blocked 4-Fold Hide-and-Recover Evaluation (`gems57-pooled-hide-v2`)
All three preregistered arms were evaluated on the unchanged shared evaluator (`vendor/gems57/evaluate_holdout.py`, `VERSION = "gems57-pooled-hide-v2"`, `11,321` withheld positive pixels across 4 spatially blocked folds with 500 m buffer and 1,000 physical-block bootstrap draws, seed `86_2026`, `37,654` binary dots per arm with `>= 2.8 px` greedy Poisson-disc spacing and visible-only `> 3 px` fault collar inside each fold):

| Arm | Description | Evidence Class | Evaluator Version | Withheld Positives | Pooled `HOLDOUT-DTI` | 95% Block Bootstrap CI | Paired $\Delta$ (`Candidate - Control`) | Paired 95% CI |
|---|---|---|---|---:|---:|---|---:|---|
| **`H86N_GSST` (Candidate E1)** | Multi-scale ($\sigma=3,6\text{ px}$) gravity step-vs-compact shape test | `HOLDOUT-DTI` | `gems57-pooled-hide-v2` | `11,321` | **`0.0310`** | `[0.0210, 0.0423]` | — | — |
| **`E0_raw_grav_slope` (Control 1)** | Raw horizontal gravity gradient magnitude (`Band 5`) | `HOLDOUT-DTI` | `gems57-pooled-hide-v2` | `11,321` | **`0.0349`** | `[0.0238, 0.0473]` | **`-0.0039`** | `[-0.0078, -0.0001]` |
| **`E2_compact_curv` (Control 2)** | Compact-curvature weighted gravity slope (`Band 5 * |\nabla \cdot \hat{n}|`) | `HOLDOUT-DTI` | `gems57-pooled-hide-v2` | `11,321` | **`0.0407`** | `[0.0305, 0.0529]` | **`-0.0097`** | `[-0.0229, +0.0033]` |

### 3.2 Single-Feature Leakage Canary (`AUC <= 0.90` Gate)
Evaluated on the `11,321` withheld positive pixels vs `200,000` random allowed background pixels:
- `gsst_s3`: **`0.5169`** ($\le 0.90$ PASS)
- `gsst_s6`: **`0.5074`** ($\le 0.90$ PASS)
- `ctrl_raw_grav_slope`: **`0.5233`** ($\le 0.90$ PASS)
- `ctrl_compact_curv`: **`0.5213`** ($\le 0.90$ PASS)

### 3.3 Registry Uniqueness Gate (`PA-86-01` Like-for-Like vs Literal Witness)
- **Local like-for-like scan (`61` local registry rasters in `data/scored*` + `docs/downloads`):**
  * Max pre-placement surface $|\rho_{\text{Spearman}}|$: **`0.0745 <= 0.90`** (vs `gems86-h86f-pcc-signed-44090dots-20261025T002755Z-94f74d4e-zeros.tif`) — PASS
  * Max final-dot binary $|\phi|$: **`0.0562 <= 0.90`** (vs `gems86-faulthalo-4210938px-20261024T181838Z-219b3357-zeros.tif`) — PASS
  * Max 3-px dot-field forward overlap: **`0.5856 <= 0.70`** (vs `GEMSDOE85__gems85-geopb-crest-90000dots-sep4-20261022T222707Z-a4e1f57c-zeros.tif`) — PASS
- **Pinned literal full-support witness (`17GEMSDOE`, `data/registry/dense-witness.tif`, SHA-256 `ab0a0a62...`):**
  * Forward 3-px overlap = **`1.0 > 0.70`**, full-footprint Spearman = **`-0.0036`**, `unique = false`, `stop_required = true`.

### 3.4 Why `H86N-GSST` Was Falsified on Holdout
In the USGS/INGENIOUS Great Basin fault catalogue, mapped Quaternary and Cenozoic fault traces frequently curve, bifurcate, and step over across $300\text{--}600\text{ m}$ relay ramps, horsetail splays, and range-front salients. At these fault-complexity loci (which are also primary geothermal permeability targets), the horizontal gravity gradient normal $\hat{\mathbf{n}}$ rotates rapidly ($|\nabla \cdot \hat{\mathbf{n}}|$ is elevated) and cross-strike flank symmetry breaks down. Consequently, penalizing $|\nabla \cdot \hat{\mathbf{n}}|$ and requiring strict $\pm\sigma$ flank sign persistence suppressed genuine fault stepovers (causing `E2_compact_curv` at `0.0407` and `E0_raw_grav_slope` at `0.0349` to outperform `H86N_GSST` at `0.0310`), while elongated non-fault lithologic contacts and alluvial-fan density ramps (the preregistered mimic) passed the shape test. Under our preregistered falsification criteria, `H86N-GSST` is **scientifically negative (`DO NOT SUBMIT`)**.

---

## 4. Forensic Audit & Repairs Executed in This Session

### 4.1 `IR-86-H86M-LT-UNREGISTERED-PROMOTE-20261025` (PR #165 Repair)
When this session started on `HEAD` (`3deca67`, Merge PR #165), `make verify`, `audit_release.py`, `audit_downloads.py`, `check_site.py`, and 19 pytest cases failed because PR #165 (`H86M-LT`) had:
1. Placed `docs/downloads/gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros.{tif,zip,json}` in `docs/downloads/` without registering it in `docs/evidence/download-inventory.json` or `registry/artifact_cards.json`.
2. Set `"verdict": "promote"` and `"safe_to_submit": true` in `docs/evidence/h86m-lt-run-card.json` without running any spatially-blocked hide-and-recover `HOLDOUT-DTI` evaluation (it evaluated only belief-model projections `0.3317` / `0.3515` / `0.2714` fit to 29 unverified owner-reported fleet scores whose rasters used the full `existing_faults.tif` catalogue).
3. Placed `"IS THIS FILE OK TO SUBMIT? YES"` in `docs/h86m-lt.html` and a `PROMOTE — OK TO SUBMIT` banner at the top of `README.md`.

**Repair:** We registered `gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros` in `docs/evidence/download-inventory.json`, `registry/artifact_cards.json`, and `scripts/audit_release.py` (`holdout_kind = "h86m_lt_unvalidated"`), demoted `docs/evidence/h86m-lt-run-card.json` to `"verdict": "negative"`, `"safe_to_submit": false`, `"submission_ready": false` (preserving `"historical_lane_verdict": "promote"` and all tomography measurements intact), updated `docs/h86m-lt.html` and `README.md` to `DO NOT SUBMIT`, and re-measured all 37 published TIFFs against the pinned witness.

### 4.2 `IR-86-H86M-BMR-CNT-NODATA-SENTINEL-20261025` (In-Footprint Float32 Sentinel Discovery)
During Pass 2 verification of `training_features.tif` (`4371c82e...`), we discovered that **3,061 pixels inside `sample_submission.tif`'s valid footprint `fp`** carry the finite float32 nodata sentinel `-3.4028234663852886e+38` (`<= NODATA * 0.5`) across bands 5, 7, 8, 11, 13, 15, 17, 18. Scripts that call `rasterio.open(tf).read(b)` and only replace `~fp` with `np.nanmean(a[fp])` (such as PR #157's `run_h86m_bmr.py` and `run_h86m_cnt.py`) leave `-3.403e+38` inside `fp`, corrupting `np.nanmean(a[fp])` to `-2.02e+35` and causing float32 overflow in spatial derivatives.
**Fix:** In `src/gems86_gsst/features.py`, `clean_band(arr, fp)` masks `~np.isfinite(a) | (a <= NODATA * 0.5)` both inside and outside `fp` and fills with the valid in-footprint mean before any smoothing or gradient operator. Cleaning those 3,061 sentinel pixels eliminated all runtime overflow warnings and raised `H86N-GSST` `HOLDOUT-DTI` from `0.0148` (uncleaned edge ringing) to `0.0310` (`[0.0210, 0.0423]`).

---

## 5. PhD-Level Analysis: Why `GEMSDOE32` (`h33-h33-2-b2`) Achieved `0.2778` (`OWNER-REPORTED`) and Whether We Can Beat `0.2778` / `0.3195`

### 5.1 Exact Mathematical & Pixel Forensics of `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`
1. **Evidence boundary:** Every leaderboard number in the prompt (`0.2778` for `GEMSDOE32`, `0.2750` for `GEMSDOE36`, `0.2708` for `GEMSDOE28`, `0.2673` for `GEMSDOE25`, and the conflicting `0.3195` / `0.4413` top-score claims) is **`OWNER-REPORTED`**, not **`ORGANIZER-CONFIRMED`** (no DrivenData portal receipt or submission ID is stored in the repository).
2. **Exact pixel identity (`docs/evidence/concurrent-artifact-review-20261025.json`):**
   - `GEMSDOE28` (`h31-h19-5-d28-new-20261002T013956Z-4271da31`, `0.2708` `OWNER-REPORTED`) is a binary dot field (`{0.0, 1.0}`) with **`40,199` positive pixels** inside the `5,167,373`-pixel footprint (`0.778%` footprint support), generated by greedy $d_{\min} \approx 2.8\text{ px}$ ($280\text{ m}$) Poisson-disc thinning on the `H19-5` multi-band geophysical lineament surface outside a 1-px mapped-fault mask ($d_{\text{cat}} > 1\text{ px}$).
   - `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` `OWNER-REPORTED`) has **`37,654` positive pixels** inside the footprint and `0.0` outside (`-zeros` encoding, with `7,111,787` outside-footprint cells set to `0.0` instead of `NaN`).
   - Inside the footprint, `GEMSDOE32` adds **0 pixels** to `GEMSDOE28` and deletes **2,545 pixels** (`40,199 - 37,654 = 2,545`). Every single deleted pixel lies in the $1 < d_{\text{cat}} \le 2\text{ px}$ ($100\text{--}200\text{ m}$) collar around `existing_faults.tif`, yielding **0 differing cells across all `12,279,160` grid pixels** once that collar is removed.
3. **Why sparse $2.8\text{ px}$ dots + $2\text{ px}$ collar pruning optimize the asymmetric Tversky index:**
   The competition metric (`vendor/gems57/metric.py`) evaluates predictions $P \in [0, 1]^{\Omega}$ against hidden truth $G \in \{0, 1\}^{\Omega}$ (after masking known catalogue faults $C$) with a 300 m ($R = 3\text{ px}$) linear distance-decay kernel $k(\Delta r) = \max(0, 1 - \|\Delta r\|_2 / 3)$:
   $$\tilde{G}(x) = \max_{y:\,\|y-x\|_2 \le 3} P(y)\,k(y-x), \qquad \tilde{P}(x) = \max_{y:\,\|y-x\|_2 \le 3} G(y)\,k(x-y)$$
   $$\text{TP}_w = \sum_{x \in \Omega \setminus C} \tilde{G}(x)\,G(x), \quad \text{FP}_w = \sum_{x \in \Omega \setminus C} P(x)\,(1 - \tilde{P}(x)), \quad \text{FN}_w = \sum_{x \in \Omega \setminus C} (1 - \tilde{G}(x))\,G(x)$$
   $$\text{DTI} = \frac{\text{TP}_w}{\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w} = \frac{\text{TP}_w}{0.8\,|G| + 0.2\,(\text{TP}_w + \|P\|_1 - M)}$$
   where $M = \sum_x P(x)\tilde{P}(x)$ is the self-credit of prediction mass near truth.
   - **Why continuous/dense rasters collapse (`0.0041–0.056` `OWNER-REPORTED`):** A continuous probability field or dense halo puts massive $\|P\|_1 \sim 10^5\text{--}10^6$ into the denominator $0.2\,\text{FP}_w$, while $\tilde{G}(x)$ uses a $\max$ operator over the 3-px disk — so interior pixels within $< 2.8\text{ px}$ of a unit dot contribute redundant false-positive mass $\alpha P(x)$ without raising the local supremum $\tilde{G}(x)$.
   - **Exact marginal acceptance threshold (`metric.marginal_accept`):** Adding or keeping a unit dot with expected truth gain $\Delta \text{TP}_w$ and self-credit $k_{\text{self}}$ increases $\text{DTI}$ if and only if:
     $$\Delta \text{TP}_w \cdot (0.8\,|G| + 0.2\,(\|P\|_1 - M)) > 0.2\,\text{TP}_w\,(1 - k_{\text{self}})$$
     At `H33`'s operating point, a unit dot needs $\Delta \text{TP}_w \gtrsim 0.088$ to pay for its $0.2(1 - k_{\text{self}})$ false-positive tax. Because the `2,545` collar dots at $1 < d_{\text{cat}} \le 2\text{ px}$ sit immediately adjacent to already-masked catalogue pixels $C$, most of their 3-px kernel disk covers masked cells in $C$ rather than unmapped truth $G \setminus C$, so deleting them reduces $\|P\|_1$ by `2,545` while losing minimal $\text{TP}_w$ (accounting for the $+0.0070$ `OWNER-REPORTED` difference from `0.2708` to `0.2778`, subject to the caveat in `research/H33_INTERPRETATION_REVIEW.md` that no organizer receipt or private-test truth mask is available locally).

### 5.2 Fleet Structure Across the 92 GEMSDOE Projects (`registry/prior_scores.csv`)
- **Top cluster (`0.2602–0.2778` `OWNER-REPORTED`, 12 projects):** Every scored raster above `0.2600` (`GEMSDOE32` `0.2778`, `GEMSDOE36` `0.2750`, `GEMSDOE28` `0.2708`, `GEMSDOE34` `0.2698`, `GEMSDOE25` `0.2673`, `GEMSDOE37` `0.2665`, `GEMSDOE39` `0.2663`, `GEMSDOE40` `0.2662`, `GEMSDOE41` `0.2654`, `GEMSDOE42` `0.2640`, `GEMSDOE27` `0.2627`, `GEMSDOE31` `0.2602`) is a $2.8\text{ px}$ Poisson-disc dot field (`35k–48k` dots) derived from the `H19-5` / `D2.8` family (`92.6%–100%` 3-px overlap with `GEMSDOE28`).
- **Independent non-H19 feature families (`0.1552–0.2478` `OWNER-REPORTED`):** `GEMSDOE70` (`0.2478`), `GEMSDOE76` (`0.2343`), `GEMSDOE68` (`0.2143`), `GEMSDOE65` (`0.1972`), `GEMSDOE29` (`0.1950`), `GEMSDOE46` (`0.1840`), `GEMSDOE50` (`0.1552`) place sparse binary dots on independent potential-field/strain/geothermal surfaces.
- **Dense/continuous/ribbon rasters (`0.0001–0.0561` `OWNER-REPORTED`):** `17GEMSDOE` (`0.0561`), `18GEMSDOE` (`0.0394`), `GEMSDOE79` (`0.0369`), `GEMSDOE78` (`0.0110`), `GEMSDOE81` (`0.0041`), `GEMSDOE82` (`0.0001`).
- **Can we beat `0.2778` / `0.3195`?**
  * Scientifically on same-split buffered whole-component holdouts (`gems57-pooled-hide-v2`, `11,321` withheld positives), multi-layer physics + submodular CELF allocation (`H86F-EWCS` `HOLDOUT-DTI = 0.1723 [0.1530, 0.1898]`, `H86I-KSAD` strict-LOQO `0.1553 [0.1396, 0.1718]`, `H86J-MCSP` strict-LOQO `0.1463 [0.1280, 0.1647]`, `H86K-STDP` strict-LOQO `0.1380 [0.1223, 0.1545]` and `SGMC-PROXY-DTI = 0.1133 [0.0993, 0.1288]`) substantially outperform single-operator potential-field baselines (`0.0220–0.0467`) and fold-fair `R0` (`0.0931–0.0961`).
  * However, **no holdout score is a leaderboard projection**, and under the unchanged literal full-support witness rule (`17GEMSDOE` overlap `1.0 > 0.70`), **no candidate in this repository is cleared for DrivenData upload**.

---

## 6. Diagnosis of the `"Predicted values must be in range [0, 1]"` Portal Error

1. **Root causes in legacy GeoTIFF exports:**
   - **Outside-footprint sentinel `-1.0` or `-3.4028235e+38`:** `existing_faults.tif` stores `-1` outside the study footprint, and `training_features.tif` stores `-3.4028235e+38` both outside the footprint and at **3,061 pixels inside the footprint** (`IR-86-H86M-BMR-CNT-NODATA-SENTINEL-20261025`). Any pipeline that copies `existing_faults.tif` metadata or fails to clean in-footprint sentinels before linear combinations can emit negative or `NaN`/`Inf` values.
   - **Uncapped float32 arithmetic or `NaN` handling:** While the public competition problem page mentions `null`/`NaN` outside the region, any `NaN` inside the footprint or any value `< 0.0` or `> 1.0` triggers `"Predicted values must be in range [0, 1]"`.
2. **Automated prevention in this repository:**
   - `vendor/gems57/submission_writer.py` and `vendor/template66/gems57/validate.py` enforce all-finite `float32` values in `[0.0, 1.0]` across all `12,279,160` pixels (`0` NaN, `0` Inf, `0.0` outside the footprint, `nodata = None`), and `scripts/audit_release.py` + `scripts/audit_downloads.py` verify all **37** published `.tif` and `.zip` files automatically without human intervention.

---

## 7. Three-Pass Verification Ledger

- **Pass 1 (Implementation & Verification):**
  * Restored SHA-pinned protocol inputs (`existing_faults.tif`, `sample_submission.tif`, `data/registry/dense-witness.tif`, `.cache/training_features.tif`).
  * Preregistered `registry/h86n_hypotheses.json` and `research/H86N_GSST_PREREGISTRATION.md`.
  * Implemented `src/gems86_gsst/features.py` and `scripts/run_h86n_gsst.py` and executed `H86N-GSST`.
- **Pass 2 (Edge-Case & Bug Review):**
  * Caught and fixed the 3,061 in-footprint `-3.4028235e+38` sentinel pixels in `training_features.tif` via `clean_band()` in `src/gems86_gsst/features.py` (`IR-86-H86M-BMR-CNT-NODATA-SENTINEL-20261025`), eliminating all float32 overflow warnings.
  * Reconciled and repaired PR #165's unregistered `H86M-LT` artifact (`IR-86-H86M-LT-UNREGISTERED-PROMOTE-20261025`), registering both `H86M-LT` and `H86N-GSST` across `docs/evidence/download-inventory.json`, `registry/artifact_cards.json`, `scripts/audit_release.py`, `scripts/build_site.py`, and `README.md`.
- **Pass 3 (Full Verification Against Original Request):**
  * `scripts/audit_release.py --measure-registry` -> PASS (`37/37` valid, `decision = "DO NOT SUBMIT"`, `0` slots used).
  * `scripts/audit_downloads.py --write` -> PASS (`37` research TIFFs and receipts revalidated).
  * `scripts/build_site.py --check` -> PASS.
  * `scripts/check_site.py` -> PASS.
  * `pytest -q` -> Full test suite PASS including `tests/test_h86n_gsst.py`.
