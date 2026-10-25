# Session `arena/94cbed2d-gemsdoe86` (2026-10-25): PhD Forensic Synthesis (`GEMSDOE32` `0.2778`, `GEMSDOE91` `0.1823`, `GEMSDOE92` `0.0255`), `IR-H` Repair, `H86M-BMGS` Validation, & 3-Pass Verification

**Immediate Submission Verdict:** **`DO NOT SUBMIT`** (`verdict = "negative"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`).
- **Newly generated unique GeoTIFF (audit-only download):** [`docs/downloads/gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.tif`](../docs/downloads/gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.tif) · [`one-TIFF ZIP`](../docs/downloads/gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.zip) · [`writer receipt`](../docs/downloads/gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.json) · [`JSON Run Card`](../docs/evidence/h86m-bmgs-run-card.json)
- **SHA-256:** `7c7662e53df2f02cf9a6d3193a7f7d5d61e0b01b18c3d6b0a5de6a4676a583cb` (`139,168` bytes; `37,654` unit dots; `min = 0.0`, `max = 1.0`, `0` NaN, `0` Inf, `0` dots on `existing_faults.tif`, `EPSG:32611`, `3730 × 3292`, exact `sample_submission.tif` geotransform; `15/15` automated format checks `PASS`, eliminating the `"Predicted values must be in range [0, 1]"` portal rejection class).
- **Arena Core Values Guiding This Session:**
  - **Maximize P(Win):** Repair inherited CI/site breakage first (`IR-H` on `main`), extract every physical and metric lesson from the full 92-site `GEMSDOE` fleet (`GEMSDOE1`–`GEMSDOE92`), preregister 4 genuinely untried geological hypotheses before touching code, and validate the highest-upside subsurface+strand model (`H86M-BMGS`) under strict 12-px-eroded spatial Leave-One-Quadrant-Out (`LOQO`) holdout + independent off-catalogue `SGMC-PROXY-DTI` without burning a scarce weekly submission slot (`<= 3/week`, `1` blind final pick).
  - **Own the Outcome:** Verify every claim from SHA-pinned bytes and official primary sources, label every metric strictly by evidence class (`HOLDOUT-DTI`, `SGMC-PROXY-DTI`, `LEAKAGE-CANARY`, `REGISTRY-MEASUREMENT`, `OWNER-REPORTED`, `ORGANIZER-CONFIRMED`), never project a holdout metric onto a live leaderboard score, and make the `DO NOT SUBMIT` decision unmistakable at the top of `README.md`, `docs/index.html`, and `docs/executive-summary.html`.

---

## 1. PhD-Level Forensic Analysis: Why `GEMSDOE32` (`h33-h33-2-b2`, `0.2778` `OWNER-REPORTED`) Achieved the Highest Fleet Score & What `GEMSDOE91`/`GEMSDOE92` Prove

### 1.1 Exact DTI Algebra & Pixel Lineage of `GEMSDOE32` `H33`
On the canonical `3730 × 3292` UTM Zone 11N (`EPSG:32611`, `100 m` cell) grid (`5,167,373` valid footprint pixels; `199,704` mapped catalogue pixels in `existing_faults.tif`), the official INGENIOUS Distance-Tolerant Tversky Index (`alpha = 0.2`, `beta = 0.8`, `R = 300 m = 3 px` linear kernel $K_3(\Delta) = \max(0, 1 - \|\Delta\|_2 / 3)$; verified byte-for-byte against [`gb-ingenious/INGENIOUS_libs`](https://github.com/gb-ingenious/INGENIOUS_libs) and `vendor/template66/gems/metric.py`) evaluates a prediction field $P \in [0, 1]^\Omega$ against hidden off-catalogue fault pixels $G$ via:
$$\mathrm{DTI}(P, G) = \frac{\mathrm{TP}_w}{\mathrm{TP}_w + 0.2\,\mathrm{FP}_w + 0.8\,\mathrm{FN}_w}, \quad \mathrm{TP}_w = \sum_{g \in G} (P \oplus K_3)(g), \quad \mathrm{FP}_w = \sum_{x \in \Omega} P(x)\bigl(1 - (\mathbf{1}_G \oplus K_3)(x)\bigr), \quad \mathrm{FN}_w = |G| - \mathrm{TP}_w.$$

 Notice the fundamental **supremum-vs-sum asymmetry**:
1. **Truth credit $\mathrm{TP}_w$ is a morphological dilation ($\max$) over each 3-px disk**, whereas **false-positive penalty $0.2\,\mathrm{FP}_w$ sums every positive pixel linearly**. Continuous ridges (`GEMSDOE20` `H19-5`: `297,817` px, `0.1579`/`0.1922` `OWNER-REPORTED`) pay $5\times$–$7\times$ redundant $\mathrm{FP}_w$ inside every 300 m kernel disk without raising the local supremum $(P \oplus K_3)(g)$.
2. **Poisson-disc decimation (`GEMSDOE28` `h27-4-r1` -> `0.2708` `OWNER-REPORTED`):** Decimating the `H19-5` multi-geophysical surface to `40,199` unit-mass dots at spacing $d_{\min} = \sqrt{8} \approx 2.828\text{ px}$ keeps peak disk coverage near $1.0$ along predicted strands while slashing $\mathrm{FP}_w$ by $86.5\%$.
3. **Near-catalogue collar pruning (`GEMSDOE32` `h33-h33-2-b2` -> `0.2778` `OWNER-REPORTED`):** Pixel-exact verification (`research/session-679d92e7-h33-lineage.json` & `IR-B`) confirms `H33` (`37,654` unit dots, `0` NaN) equals `D28` (`40,199` dots) minus `2,545` dots in the $1 < d_{\mathrm{cat}} \le 2\text{ px}$ (`100–200 m`) near-catalogue collar (plus NaN$\to$0 outside-footprint encoding, which is score-neutral under `vendor/template66/gems/metric.py`). Deleting a subset $\Delta S$ strictly increases DTI iff its marginal weighted truth-to-FP ratio obeys:
   $$\frac{\Delta \mathrm{TP}_w}{\Delta \mathrm{FP}_w} < \frac{0.2\,\mathrm{DTI}_0}{1 - 0.8\,\mathrm{DTI}_0} \approx 0.0714 \quad (\text{at }\mathrm{DTI}_0 = 0.2708).$$
   Because organizer scoring masks mapped faults or withholds whole unmapped strands rather than `100–200 m` halos of already-mapped traces, the `2,545` collar dots earned virtually zero incremental $\Delta \mathrm{TP}_w$ while paying `2,545` units of $\mathrm{FP}_w$, yielding the `+0.0070` `OWNER-REPORTED` gain (`0.2708 -> 0.2778`).
4. **Evidence boundary:** All `118` scored rows in `registry/prior_scores.csv` (including `0.2778` and the prompt's conflicting `0.4413` and `0.3195` figures) are `OWNER-REPORTED` without archived DrivenData portal receipts (`0` `ORGANIZER-CONFIRMED` rows).

### 1.2 Three Structural Lessons from `GEMSDOE91` (`0.1823`) and `GEMSDOE92` (`0.0255`) (`OWNER-REPORTED`, rev2 update)
Inspecting the newly added `GEMSDOE91` and `GEMSDOE92` repositories alongside our internal `H86I`/`H86J`/`H86K`/`H86L` experiments exposes three decisive failure modes that explain why naive ML and uniform dip shifts underperform `H33` on hidden off-catalogue Great Basin faults:

| Mechanism / Failure Mode | Empirical Evidence (`OWNER-REPORTED` / `HOLDOUT-DTI` / `SGMC-PROXY-DTI`) | Physical & Statistical Root Cause | Architectural Fix in `H86M-BMGS` |
|---|---|---|---|
| **1. Near-Catalogue Halo Crowding** | `GEMSDOE91` `S17-LFTG` (`0.1823` `OWNER-REPORTED`, `+0.0456` over `S17-CWPC` `0.1367`) placed **`68.5%`** of its `37,654` dots within `300–1,000 m` of `existing_faults.tif` (`31.5%` far-field `> 1 km`), whereas `GEMSDOE32` `H33` (`0.2778` `OWNER-REPORTED`) places **`69.8%`** of dots `> 1 km` off-catalogue. | In-sample Positive-Unlabeled (`PU`) trees trained on `existing_faults.tif` memorize long-wavelength regional fields & range-front proximity around mapped scarps, starving blind intrabasin grabens. | Strict 12-px-eroded out-of-quadrant (`quad != q`) LOQO + zero regional levels + Elkan (2001) Bayes prior recalibration (`E1` far-field `46.6%`, `E2` blind **`70.21%`** matching `H33`!). |
| **2. Uniform Deep-Basin Dip Pullback Over-Shift** | `GEMSDOE92` `LISTRICDIP` (`0.0255` `OWNER-REPORTED`) shifted predictions up-dip by $Z_b \cot 50^\circ \in [5, 28]\text{ px}$ (`500–2,800 m`), and `H86K-STDP` shifted up to `8 px` (`800 m`). | Walker Lane strike-slip faults (`80°–90°` dip) and intrabasin horst/relay steps have near-vertical upper-crustal cutoffs; shifting by `5–28 px` moves dots completely outside the `300 m` (`3 px`) DTI kernel! | Unshifted `0 px` primary contact crests (`BMR` + `GSST`) plus **dilatation-gated shallow pullback capped at `<= 3.0 px`** (`300 m`, activated only where `B8` dilatation confirms normal extension). |
| **3. Quantile Flattening vs Log-Odds Geometric Crush** | `H86K-STDP`'s quantile map lifted desert background to $p \approx 0.0105$ (`~0.145` disk survival credit everywhere), while log-odds stencil averaging multiplicatively crushed curved 1-px fault crests (`0.0305` on `E2`). | Rank-quantile calibration destroys peak-to-background likelihood ratios; geometric-mean odds (`mean(logit p)`) collapse whenever one stencil arm touches desert background. | **Exact Elkan (2001) Bayes likelihood recalibration** ($p_{\text{bg}} \approx 0.0005$, $p_{\text{crest}} \approx 0.5+$) + **additive probability-space 8-azimuth axial strand reinforcement**. |

---

## 2. Repair of Previous-Session Next Steps First (`IR-H` + `REV2` Fleet Sync)

Before designing or running any new experiment, we completed all pending repairs from `main`:
1. **Resolved `IR-H` (`H86L-FMC` registration & preflight guard):** PR #150 had committed `docs/downloads/gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros.{tif,zip,json}` without registering it in `docs/evidence/download-inventory.json` or `registry/artifact_cards.json`, and omitted `require_feasible()` in `scripts/run_h86l_fmc.py::main()`, causing `17` pytest failures and broken `check_site.py` on `main`. We registered `H86L-FMC` (`holdout_kind: "h86l_fmc"`, `DO NOT SUBMIT`), added `require_feasible()` + AST preflight coverage in `tests/test_builder_preflight.py`, and restored green site/audit checks.
2. **Synchronized `GEMSDOE91` & `GEMSDOE92` (`REQUEST_20261025_REV2.md`):** Preserving `research/REQUEST_20261025.md` byte-for-byte, we archived `research/REQUEST_20261025_REV2.md`, added the 3 new `OWNER-REPORTED` rows (`GEMSDOE91` `0.1367` & `0.1823`; `GEMSDOE92` `0.0255`) to `registry/prior_scores.csv` (`118` scored rows), rebuilt `ledger/submissions.csv`, and refreshed `docs/evidence/fleet-feed.json` (`92/92` repositories snapshotted).

---

## 3. Preregistered `H86M` Candidate Hypotheses (Declared Before Implementation)

Frozen prior to code execution in [`registry/h86m_bmgs_hypotheses.json`](../registry/h86m_bmgs_hypotheses.json) and [`research/H86M_BMGS_PREREGISTRATION.md`](../research/H86M_BMGS_PREREGISTRATION.md):

| Rank | ID & Status | Specific Layers | Physical Signature & Transform | Why Missing from USGS/INGENIOUS Catalogue & Novelty vs Repo | Expected DTI Gain & Cost | Official Obtainability |
|---:|---|---|---|---|---|---|
| **1** | **`H86M-BMGS`** (`EXECUTED_NEGATIVE_AUDIT_ONLY`) | Native `B2, B3, B5, B7, B8, B9, B11, B13, B15, B16, B17, B18` (`B12/B19` banned from blind specialist) + SHA-pinned `.cache/external/` (`GeoDAWN`, `3DEP 1m/10m`, `GDR-1391` w/ `dist_known_fault_px` unread) | Out-of-quadrant (`quad != q`) 2-D FFT upward-continued Athy-compacted ($Z_b^2/(Z_b + 1200\text{ m})$) basement mass-balance gravity residual (`BMR`), 8-azimuth steerable quadrature odd-step vs even-dike asymmetry (`GSST`, $\mathrm{relu}(|O_\theta| - 0.85|E_\theta|)$ + energy-weighted spin-2 coherence + Garland Poisson jump), transtensional MT neck (`CNT`), dilatation-gated $\le 3\text{ px}$ pullback, Elkan-Bayes recalibration, 8-azimuth probability-space strand coherence, & 6-ring survival Dinkelbach-CELF (`37,654`d). | Separates sediment-compaction gravity bowls from uncompacted basement horst/graben steps under playas while vetoing symmetric volcanic dikes/plutons (`|E_\theta|`) without shifting steep (`80°–90°`) strike-slip faults out of the `300 m` kernel. First out-of-quadrant FFT Athy forward-gravity stripping + odd-vs-even quadrature asymmetry lane in repo. | **Rank 1** · Medium (`~9 min` end-to-end on CPU) | 100% SHA-256-verified in `.cache/bridge/` & `.cache/external/`. |
| **2** | **`H86M-BFLI`** (`QUEUED_SELF_CONTAINED`) | 25 locally cached `data/scored_fleet/*.tif` rasters + native strike tensor `(B18, -B11)` & `B2` | Bounded logistic-link ($\sigma(u) \in (0, 1)$, $\|\beta\|_1 \le 0.25$) strike-aligned anisotropic-TV fleet live-score inversion via concave Tversky surrogate $1 - \prod(1 - p_i)$. | Directly targets the spatial support difference between `OWNER-REPORTED` live scores and catalogue-hide `HOLDOUT-DTI` while fixing `H86J-LSI`'s unbounded $\lambda > 1$ pathology. Ranked #2 because fleet scores lack `ORGANIZER-CONFIRMED` receipts. | **Rank 2** · Low-Medium (`~15 min` L-BFGS-B) | Self-contained (`data/scored_fleet/`). |
| **3** | **`H86M-ORTF`** (`QUEUED_SELF_CONTAINED`) | Native `B4, B7, B8, B11, B13, B17, B18` + `existing_faults.tif` visible fold | Orthorhombic conjugate Riedel ($R/R'$ at $\pm(45^\circ - \phi/2)$ to principal strain axes of `B7, B8`) & minimum-dissipation Steiner stepover fault-mesh transport between high-probability basement seeds. | Reconstructs discrete concealed transfer/relay strands across Walker Lane & Humboldt stepovers rather than isotropic tip halos (`H86F-EWCS`) or pixel-local kernels. | **Rank 3** · Medium (`~20 min` Dijkstra/FMM) | 100% native 19-band stack. |
| **4** | **`H86M-OPERA`** (`DEFERRED_EXTERNAL_SOURCE_EGRESS_BLOCKED`) | NASA/JPL OPERA `DISP-S1` L3 Sentinel-1A/C InSAR LOS velocity & seasonal phase jump + native `B7, B8, B15` | Cross-fault `100–300 m` $\nabla_\perp v_{\mathrm{LOS}}$ & seasonal aquitard hydraulic-head step $\Delta A_{\mathrm{seasonal}}$ where fault-core clay gouge ponds seasonal groundwater across flat playas. | Resolves `100 m` fault-trace creep/aquitard steps invisible to `50 km`-smoothed GPS (`B4/B7/B8`) and eroded scarps (`B12/B19`). | **Rank 4** · High external value (egress-blocked here) | Free public US Gov open data: [ASF DAAC OPERA](https://asf.alaska.edu/datasets/daac/opera/) · DOI [`10.5067/SNWG/OPERA-L3_DISP-S1-V1`](https://doi.org/10.5067/SNWG/OPERA-L3_DISP-S1-V1). |

---

## 4. `H86M-BMGS` Measured Validation Results (All Evidence Classes Strictly Labeled)

### 4.1 `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `11,321` Withheld Positives, Strict 12-px-Eroded 4-Fold Spatial LOQO, 1,000-Draw 20 km Block Bootstrap)

| Arm / Comparator | Evidence Class | Pooled DTI | 95% Block-Bootstrap CI | `NW` (`1,923`) | `NE` (`2,367`) | `SW` (`3,781`) | `SE` (`3,250`) | Paired $\Delta$ (`E1 - Comparator`) |
|---|---|---:|---|---:|---:|---:|---:|---|
| **`E1_bmgs_strand_dinkelbach_celf` (`37,654`d)** | `HOLDOUT-DTI` | **`0.1310`** | **`[0.1121, 0.1509]`** | `0.1438` | `0.1112` | `0.1267` | `0.1387` | — |
| `E3_raw_grav_iso_staticek_ablation` (`37,654`d) | `HOLDOUT-DTI` | `0.1197` | `[0.1059, 0.1333]` | `0.1041` | `0.1312` | `0.1202` | `0.1183` | **`+0.0113 [-0.0085, +0.0304]`** |
| `E2_bmgs_blind_zero_catalogue` (`37,654`d, 0 DEM, 0 cat) | `HOLDOUT-DTI` | `0.0644` | `[0.0480, 0.0807]` | `0.0563` | `0.0242` | `0.0494` | `0.0945` | `+0.0667 [+0.0504, +0.0825]` |
| `R0_D28_visible_collar` (`GEMSDOE28` masked) | `HOLDOUT-DTI` | `0.0273` | `[0.0226, 0.0320]` | `0.0246` | `0.0298` | `0.0215` | `0.0344` | **`+0.1037 [+0.0853, +0.1228]`** |
| `H33_visible_collar` (`GEMSDOE32` masked) | `HOLDOUT-DTI` | `0.0036` | `[0.0020, 0.0054]` | — | — | — | — | **`+0.1275 [+0.1086, +0.1474]`** |
| Historical strict-LOQO `H86C-KSLB` (`44,090`d) | `HOLDOUT-DTI` | `0.1241` | `[0.1080, 0.1403]` | — | — | — | — | (`E1` higher point estimate `+0.0069`, overlapping CIs) |
| Repo strict-LOQO record `H86I-KSAD` `E2` (`37,654`d) | `HOLDOUT-DTI` | `0.1599` | `[0.1459, 0.1742]` | — | — | — | — | (`E1` trails surface-DEM-inclusive `KSAD` by `-0.0289`) |

### 4.2 Independent Off-Catalogue `SGMC-PROXY-DTI` (`62,122` USGS SGMC Bedrock Fault Pixels `> 300 m` from `existing_faults.tif`) & Far-Field Macro-Allocation

| Candidate / Benchmark (`37,654` dots unless noted) | Evidence Class | `SGMC-PROXY-DTI` | 95% Spatial Bootstrap CI | Far-Field Dots `> 1 km` Off-Catalogue | Paired $\Delta$ (`E1 - Benchmark`) |
|---|---|---:|---|---:|---|
| **`E2_bmgs_blind_zero_catalogue` (0 cat, 0 DEM)** | `SGMC-PROXY-DTI` | **`0.1111`** | **`[0.0906, 0.1322]`** | **`70.21%`** | `-0.0030 [-0.0185, +0.0132]` |
| **`E1_bmgs_strand_dinkelbach_celf` (exported audit `.tif`)** | `SGMC-PROXY-DTI` | **`0.1082`** | **`[0.0862, 0.1319]`** | **`46.60%`** | — |
| `H86K_STDP_37654_as_is` (`PR #149`) | `SGMC-PROXY-DTI` | `0.1133` | `[0.0913, 0.1365]` | `47.56%` | `-0.0052 [-0.0188, +0.0080]` |
| `H86J_MCSP_37654_as_is` | `SGMC-PROXY-DTI` | `0.0999` | `[0.0793, 0.1219]` | `43.25%` | **`+0.0083 [-0.0046, +0.0209]`** |
| **`H33_GEMSDOE32_as_is` (`0.2778` `OWNER-REPORTED` leader)** | `SGMC-PROXY-DTI` | **`0.0937`** | **`[0.0731, 0.1157]`** | **`69.80%`** | **`+0.0145 [-0.0033, +0.0319]`** |
| `H86F_EWCS_37654_as_is` | `SGMC-PROXY-DTI` | `0.0819` | `[0.0642, 0.1008]` | `30.88%` | **`+0.0263 [+0.0119, +0.0405]`** |
| `E3_raw_grav_iso_staticek_ablation` | `SGMC-PROXY-DTI` | `0.0818` | `[0.0648, 0.0996]` | `30.42%` | **`+0.0264 [+0.0117, +0.0409]`** |

**Key scientific takeaway:** Replacing raw Bouguer/isostatic gravity + isotropic tips + static `E[k]` (`E3`) with `H86M-BMGS` (`E1`) lifted independent off-catalogue `SGMC-PROXY-DTI` by **`+0.0264 [+0.0117, +0.0409]`** (`+32.3%` relative gain, CI strictly excluding zero!) and lifted `HOLDOUT-DTI` on `NW` (`+0.0397`), `SW` (`+0.0065`), and `SE` (`+0.0204`), while pure zero-catalogue blind `E2` achieved **`70.21%`** far-field allocation (`> 1 km` off-catalogue — matching `GEMSDOE32` `H33`'s `69.80%` to within `0.41%` without seeing a single catalogue pixel at inference!) and scored **`0.1111`** vs `H33`'s `0.0937`. However, on `Fold NE` (sparse mapped ranges), `E1` trailed `E3` (`0.1112` vs `0.1312`) so pooled `HOLDOUT-DTI` paired $\Delta$ vs `E3` (`+0.0113 [-0.0085, +0.0304]`) spanned zero, and `E1` remained below surface-DEM-heavy `H86I-KSAD` (`0.1599`). Under our preregistered fail-closed rules, `verdict = "negative"` (`DO NOT SUBMIT`).

### 4.3 `LEAKAGE-CANARY` & Full-Registry `REGISTRY-MEASUREMENT` (`702` Rasters)
- **`LEAKAGE-CANARY` (`38/38` PASS):** Every static, ablation, and fold-visible plane cleared the `AUC <= 0.90` gate (`max discriminative AUC = 0.7941` on `fold_visible_iso_tip_halo`; `0` flags; `dist_known_fault_px` inside `gdr_geothermal_w8_u8.tif` verified unread by unit test and code audit).
- **Pre-placement continuous surface scan (`702/704` valid-grid rasters):** **`0` Spearman `rho > 0.90` firings** (`worst_spearman = 0.5650 <= 0.90`).
- **Final 37,654-dot scan (`702/704` valid-grid rasters):**
  - Across all **`460` discrete `<= 90,000`-dot submissions** in the entire 92-repository restored universe (and all `56` local `<= 100,000`-dot rasters): **`0` firings over `0.70`** (`worst = 0.6369` vs `H86J-MCSP`; `0.6351` vs `H86K-STDP`; `0.5216` vs `H86F-EWCS`; `0.3035` vs `H86G-EDTI`; **`0.2974` vs `GEMSDOE32` `H33`**).
  - Full-registry `v2` gate fails closed on literal full-support continuous witness `17GEMSDOE` (`1.0000 > 0.70`), `19` space-filling `> 70%`-halo rasters, `13` ultra-dense `91.5k–624k`-pixel rasters (`13GEMSDOE`, `GEMSDOE22`, `GEMSDOE23`, `GEMSDOE3`, `GEMSDOE50`), and `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`).

---

## 5. Explicit Three-Pass Verification Log

### Pass 1 — End-to-End Implementation & Pipeline Execution
- Repaired `IR-H` (`H86L-FMC` inventory/card registration + `require_feasible()` guard), updated `registry/prior_scores.csv` + `ledger/submissions.csv` + `docs/evidence/fleet-feed.json` (`92/92` repos) for `REQUEST_20261025_REV2.md`, preregistered `registry/h86m_bmgs_hypotheses.json` & `research/H86M_BMGS_PREREGISTRATION.{json,md}`, implemented `src/gems86_bmgs/{features,model}.py` + `scripts/run_h86m_bmgs.py` + `tests/test_h86m_bmgs.py`, executed `run_pa86_lane()` end-to-end across all `655` restored external registry blobs, and generated + machine-validated `gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.{tif,zip,json}` and `docs/evidence/h86m-bmgs-run-card.json`.

### Pass 2 — Self-Audit, Bug Fixes, & Edge-Case Hardening
During implementation and testing we caught and fixed **five concrete bugs/edge cases** before finalizing artifacts:
1. **`EXTERNAL_PINS` dict-unpacking bug (`features.py` & `run_h86m_bmgs.py`):** `scripts/restore_data.py::EXTERNAL_PINS` maps `{filename: sha256_hex}` (2-item dict, not 3-tuples); fixed iteration and verified via `tests/test_h86m_bmgs.py`.
2. **Spin-2 directional coherence cancellation on symmetric quadrature filters (`features.py`):** Uniform-weight $\cos 2\theta_k$ across 8 evenly spaced azimuths sums identically to zero unless weighted by odd-step energy $w_k = S_k^2$; fixed to energy-weighted spin-2 vector summation and added synthetic step (`> 0.38`) vs circular dome (`< 0.05`) regression test.
3. **Log-odds geometric-mean crush on curved fault strands (`model.py`):** Averaging $\mathrm{logit}(p)$ across a `7×7` directional stencil crushed curved 1-px fault crests (`E2` dropped to `0.0305`); replaced with additive probability-space axial strand reinforcement (`p_sharp >= 0.70 * p_bayes` regression-tested).
4. **4× redundant LOQO refit inside `evaluate_holdout` loop (`run_h86m_bmgs.py`):** Verified `folds[0]["visible"]` (`48,340` px) is byte-identical across all 4 quadrant folds (`assert shared_vis`), reducing 4-fold eroded-LOQO fit + Dinkelbach-CELF runtime from ~22 min to `396.9s` with zero cross-quadrant leakage.
5. **Snapshot & pytest symlink hygiene (`data/registry_ext` & `data/bridge/training_features.tif`):** Kept large restored binaries strictly inside snapshot-excluded `.cache/`, linked `data/registry_ext` only during full-registry measurement, synced `research/session-0c60b079-run-card.json` `registry_measurement_utc` to `docs/evidence/registry-input-grid-audit.json` `measured_utc`, and unlinked temporary `data/` symlinks prior to final `pytest -q` and turn completion.

### Pass 3 — Final Line-by-Line Re-Check Against Original Prompt & All Repository Gates
- Unique GeoTIFF generated via shared `vendor/gems57/submission_writer.py`, values strictly in `[0, 1]` (`0.0..1.0`, `0` NaN), matching `sample_submission.tif` CRS/shape/transform, unique name & `106`-char note (`<= 140`): **VERIFIED**.
- Unmistakable top-of-site & top-of-README `DO NOT SUBMIT` status (`safe_to_submit = false`, `approved_for_weekly_slot = false`): **VERIFIED**.
- Prompt archived in `README.md` (`REV2` + `20261025` + `20261024` + `20261023`), official links & data tables verified, JSON Run Card emitted, `audit_release.py --measure-registry`, `audit_downloads.py --write`, `build_site.py --check`, `check_site.py`, and full `pytest -q` all passing (`0` failures): **VERIFIED**.

---

## 6. Limitations & Next-Session Recommendations

1. **Unresolved governance/external blockers (require owner action outside sandbox):**
   - **Literal dense-witness uniqueness rule (`PA-86-01` / `IR-A`):** Decide whether full-support continuous rasters (`17GEMSDOE`, halo coverage `1.0`) and `> 90k`-pixel dense fields are governed by the PA-86-01 like-for-like discrete `<= 90k`-dot / excess-over-chance rule (`H86M-BMGS` has `0/460` firings on discrete `<= 90k`-dot submissions, max `0.6369`).
   - **Organizer score receipts:** Upload or transcribe at least 1–2 `ORGANIZER-CONFIRMED` DrivenData submission-page receipts into `ledger/submissions.csv` (currently `0` `ORGANIZER-CONFIRMED` rows).
   - **Weekly slot discipline:** Do **not** upload `H86M-BMGS` (`DO NOT SUBMIT`). If the human selector chooses to spend 1 of the 3 weekly slots, consult `SLOT_PLAN.md` (`H86G-EDTI` under PA-86-01 like-for-like review or `PRUNE-le3p000` paired probe against `0.2778`).
2. **Highest-value technical next step (`H86N` candidate):**
   - Notice why `H86M-BMGS` jumped `+0.0264` on off-catalogue `SGMC-PROXY-DTI` (`0.1082` `E1`, `0.1111` `E2` with `70.21%` far-field `> 1 km`) while `H86I-KSAD` led surface-catalogue `HOLDOUT-DTI` (`0.1599`): **two-regime domain decomposition** — route range-front/bedrock pixels (`Z_b < 150 m`) through the `H86I-KSAD` 3DEP/LiDAR kinematic scarp specialist and route concealed basin/playa pixels (`Z_b >= 150 m`) through the `H86M-BMGS` cover-blind `BMR + GSST + CNT` specialist (`E2`), coupled via `H86M-ORTF` conjugate Riedel Steiner stepover transport across basin-margin structural relays.
