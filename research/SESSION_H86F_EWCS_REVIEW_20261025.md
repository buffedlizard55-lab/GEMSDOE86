# Session H86F-EWCS Three-Pass PhD Review, H33 Synthesis & Holdout Validation (2026-10-25)

**Branch:** `arena/6edaf567-gemsdoe86`
**Automated Decision:** **`DO NOT SUBMIT`** (`verdict: "negative"`, `new_candidate_generated: true` [audit-only GeoTIFF], `submission_slots_used: 0`)
**Primary Machine-Readable Evidence:**
- Preregistration (frozen prior to implementation): [`research/H86F_EWCS_PREREGISTRATION.json`](H86F_EWCS_PREREGISTRATION.json) · [`research/H86F_EWCS_PREREGISTRATION.md`](H86F_EWCS_PREREGISTRATION.md)
- Four newly formulated H86F geological hypotheses: [`registry/h86f_hypotheses.json`](../registry/h86f_hypotheses.json)
- Session Run Card: [`docs/evidence/h86f-ewcs-run-card.json`](../docs/evidence/h86f-ewcs-run-card.json)
- Audit-only GeoTIFF & ZIP: [`docs/downloads/gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif`](../docs/downloads/gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif) (`SHA-256 8322dcf157851e07dfdd4391ed5164916479e4dce17af2d0e14afab5592a697d`)
- SHA-bound `v2` 689-entry surface & final-dot registry receipts (including `H86F-PCC` & `H86F-GZZD`): [`docs/evidence/h86f-ewcs-registry-surface.json`](../docs/evidence/h86f-ewcs-registry-surface.json) · [`docs/evidence/h86f-ewcs-registry-final-dots.json`](../docs/evidence/h86f-ewcs-registry-final-dots.json)

---

## 1. Executive Decision & Arena Core Values (`Maximize P(Win)` & `Own the Outcome`)

1. **Is any GeoTIFF in `GEMSDOE86` authorized for DrivenData upload right now? NO (`DO NOT SUBMIT`).**
   - All **18** published research GeoTIFFs in `docs/downloads/` pass automated local format/range checks (`float32`, single-band, `EPSG:32611`, `3730 × 3292`, `100 m` grid matching `sample_submission.tif`, finite `[0, 1]` inside footprint, `0.0` outside footprint, `0` mapped-catalogue dots, `<= 140`-character note, valid single-TIFF `.zip` and SHA-256 receipt), resolving the portal `"Predicted values must be in range [0, 1]"` failure class at serialization time.
   - None is authorized for upload: every artifact fails the binding literal registry witness (`17GEMSDOE` `ab0a0a62...`, positive across `100.0%` = `5,106,385 / 5,106,385` allowed cells; plus discrete binary stride-5 lattice `13GEMSDOE` `b4570b40...` covering `99.8724%` of allowed cells within `3 px`).
2. **What new scientific advance did Session H86F-EWCS deliver?**
   - We formulated and froze **four genuinely novel geological hypotheses (`H86F-EWCS`, `H86F-GDFB`, `H86F-PFSB`, `H86F-USGS-3DGF`)** never previously implemented or sketched in `GEMSDOE86` or audited sibling repositories through `GEMSDOE92`.
   - We implemented and validated Rank 1 (**`H86F-EWCS`**) across **3 preregistered arms** within budget on the pinned buffered whole-component holdout (`gems57-pooled-hide-v2`, `seed=20, hide_frac=0.20, buffer_px=3`, `11,321` withheld positives):
     - **`E1_ewcs_coupled_pu` (`37,654` dots, `2.8 px` spacing): `HOLDOUT-DTI = 0.1723` (`[0.1530, 0.1898]`)**
     - **`E3_ewcs_isotropic_tip_ablation` (`37,654` dots): `HOLDOUT-DTI = 0.1592` (`[0.1402, 0.1782]`)** — paired delta **`+0.0131` (`[+0.0012, +0.0261]`, strictly positive 95% CI!)**
     - **`E2_ewcs_cover_blind_pu` (subsurface-only, zero DEM/slope, zero fault geometry): `HOLDOUT-DTI = 0.1003` (`[0.0835, 0.1188]`)** — paired delta `+0.0721` (`[+0.0568, +0.0891]`)
     - **`R0_D28_visible_collar` (fold-fair geometry control): `HOLDOUT-DTI = 0.0273` (`[0.0229, 0.0321]`)** — paired delta **`+0.1450` (`[+0.1258, +0.1628]`)**
     - **Fold-fair `GEMSDOE25` `R0` (`38,802` dots): `HOLDOUT-DTI = 0.0961` (`[0.0830, 0.1089]`)** — `H86F-EWCS` exceeds fold-fair `R0` by `+0.0762` with non-overlapping 95% CIs.
     - **Same-split historical best (`H86C-KSLB` `E3`, `44,090` dots): `HOLDOUT-DTI = 0.1241` (`[0.1080, 0.1403]`)** — `H86F-EWCS` exceeds `H86C-KSLB` by `+0.0483` with non-overlapping 95% CIs while using `6,436` fewer dots (`37,654` vs `44,090`), and far exceeds concurrent 2026-10-25 lanes `H86F-PCC` (`0.0327`) and `H86F-GZZD` (`0.0303`).
     - **Single-feature leakage canaries:** All `23` static and fold-visible features passed (`max discriminative AUC = 0.7949 <= 0.90`, `0` leakage flags).
     - **SHA-bound `v2` surface & final-dot registry checks (`687 / 689` rasters comparable, explicitly including `H86F-PCC` & `H86F-GZZD`):** `worst_spearman_full_footprint = 0.7508 <= 0.90` (`0` rho firings; `byte_unique = true`; `pixel_unique = true`); **`0` forward-overlap firings `> 0.70` across all discrete `<= 50,000`-dot rasters** (`26.96%` vs `GEMSDOE32` `h33-h33-2-b2`, `37.57%` vs `H86C-KSLB`, `9.46%` vs `H86F-PCC`, `9.90%` vs `H86F-GZZD`).
3. **Why is `H86F-EWCS` nevertheless blocked (`DO NOT SUBMIT`, `verdict: "negative"`, `0` slots used)?**
   - Under `AGENTS.md` Rules 6, 10, and 11 (`PA-86-01/02`), `0` Spearman `rho > 0.90` firings permitted audit-only `37,654`-dot placement and serialization via shared `vendor/gems57/submission_writer.py`, **but** `2` grid/CRS-incompatible historical entries in SHA-pinned `research/upstream/registry_inventory.json` (`14GEMSDOE` and `7GEMSDOE`), `39` space-filling `>= 56,605`-dot firings, literal `1.0000` overlap against `17GEMSDOE`, and `PA-86-02` failing closed (`ValueError: Incomplete registry cannot pass`) mandate `verdict = "negative"` and **`DO NOT SUBMIT`** (`0` weekly slots used).

---

## 2. PhD-Level Analysis: Why `GEMSDOE32` (`h33-h33-2-b2`: `0.2778` `OWNER-REPORTED`) Led the Supplied Fleet List — and What Is Required to Beat It

### 2.1 Epistemic Status of Scores
Every leaderboard scalar in the prompt — including `GEMSDOE32` `0.2778`, `GEMSDOE28` `0.2708`, `GEMSDOE36` `0.2750`, and the conflicting headline leaderboard figures `0.3195` vs `0.4413` — is **`OWNER-REPORTED` (unverified)**, not `ORGANIZER-CONFIRMED`, because zero DrivenData submission-page receipts exist in this checkout. Furthermore, H33's own archived sidecar (`GEMSDOE32` commit `780a5a534269`) carries `UNSCORED` and a model projection in its note.

### 2.2 Exact Pixel-Level Identity & Distance-Weighted Tversky (`DTI`) Mechanics
Direct pixel comparison across all `12,279,160` cells (`3730 × 3292`, `EPSG:32611`) establishes an exact algebraic identity (`0` differing pixels):
$$\text{R0}_{\text{H33}} \; (37,654\text{ unit dots}) \;=\; \text{D2.8}_{\text{GEMSDOE28}} \; (40,199\text{ unit dots}) \;\setminus\; \{x : 1.0 < d_{\text{cat}}(x) \le 2.0\text{ px}\}\; (2,545\text{ collar dots}).$$
Similarly, `GEMSDOE36` (`0.2750` `OWNER-REPORTED`) equals `R0` verbatim (`100%` containment) plus `1,200` extra dots. Across all `92` repositories snapshotted in `docs/evidence/fleet-feed.json`, every `OWNER-REPORTED` entry above `0.2600` (`GEMSDOE27`, `GEMSDOE28`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE36`) belongs to the `H19-5 / D2.8` sparse unit-dot ridge family (`92.64%–100%` 3-px overlap).

Why does sparse Poisson-disc emission (`s ≈ 2.8 px`) plus mapped-collar pruning match the mathematical structure of the competition metric?
In `vendor/gems57/metric.py`, Distance-Weighted Tversky (`alpha = 0.2` false-positive weight, `beta = 0.8` false-negative weight, `R = 300 m = 3 px` triangular kernel $K_R$, truth count $N = |G|$) evaluates **supremum (max-envelope) kernel recovery** on hidden truth $g \in G$ against **additive mass penalty** on false positives:
$$\text{DTI}(P, G) = \frac{T(P, G)}{0.2\,T(P, G) + 0.2\,F(P, G) + 0.8\,N + \epsilon}, \qquad T(P, G) = \sum_{g \in G} \max_{p} \big(P(p)\,K_R(\|p - g\|)\big).$$

Three rigorous consequences (and mandatory counterexamples guarded in `tests/test_scientific_interpretation.py`) follow:
1. **Continuous probability wash (`GEMSDOE79` `0.0005`, `GEMSDOE81` `0.0041` `OWNER-REPORTED`) vs unit-amplitude sparse dots:** Because $T(P, G)$ takes a *maximum* rather than a sum over the `R = 3 px` disk while $F(P, G)$ accumulates false-positive mass across unrecovered cells, spreading continuous mass $P \in (0, 0.3)$ or packing adjacent pixels inflates $F$ without increasing $\max_p P(p) K_R(\|p-g\|)$ beyond `1.0`. Sparse `P(p) = 1.0` dots separated by `~2.8 px` achieve full `1.0` peak amplitude while cutting redundant neighboring mass by `~7–9x`. *Caveat:* `2.8 px` spacing does **not** make `R = 3 px` kernels disjoint (two dots `3 px` apart still overlap on intermediate pixels).
2. **Exact pruning condition for the `2,545` collar dots (`1 < d_cat <= 2 px`):** Deleting a subset $\Delta P$ that loses truth credit $a = \Delta T \ge 0$ and removes false-positive mass $b = \Delta F \ge 0$ strictly increases DTI if and only if:
   $$T \cdot b \;>\; a \cdot (F + 4N + 5\epsilon).$$
   If the organizer's hidden test set masks mapped `existing_faults.tif` traces and consists primarily of distinct unmapped segments rather than `100–200 m` parallel splays ($a \approx 0$), removing `b ≈ 2,545` collar dots yields a pure denominator reduction (for `R0` vs `GEMSDOE36`'s `+1,200` zero-credit dots on an identical public chunk, the `0.2778` vs `0.2750` ratio implies $0.2\,T + 0.2\,F + 0.8\,N \approx 23,540$, placing $N$ on the order of `1.5×10^4–2.9×10^4` pixels). *Caveat:* Proximity to a mapped fault does **not** guarantee $a = 0$; unmapped branch splays within `200 m` of a known trace can lose real truth credit when pruned, and pixel identity between `D2.8` and `R0` is an observational forensic fact, not a randomized causal experiment on the private test set.
3. **Why geometry tuning on `H19-5` saturates near `~0.28` — and what is physically needed to reach `0.32–0.44`:**
   `H19-5` relies heavily on 3DEP topographic scarp ridges (`Bands 12, 19`). Across Great Basin alluvial basins, playas, and transfer zones, `35%–55%` of permeable geothermal/tectonic faults lack surface scarps. Closing the recall gap ($0.8\,N$ dominates the denominator `4:1` over $0.2\,F$) requires **cover-blind harmonic potential-field & hydrothermal damage-zone observables** coupled with **physically selective crack-tip/stepover transfer** — provided those predictions are calibrated against real organizer receipts rather than projected from buffered `HOLDOUT-DTI`.

---

## 3. Four Newly Formulated Geological Hypotheses (`registry/h86f_hypotheses.json`)

All four hypotheses below were formulated prior to implementation, verified against `src/gems86/io.py` (`BANDS` + `BAND_PHYSICS_VERIFIED`), and checked for non-overlap against all 15 published `GEMSDOE86` lanes, the 5 archived `H86E` entries (`SPBT`, `MMT`, `HMDC`, `MTCS`, `WCS`), the 4 qualitative sketches in `SESSION_20261024_4D79B443.md`, and sibling repositories through `GEMSDOE92`:

| Rank | ID | Layers (verified `src/gems86/io.py`) | Physical Signature & Transform | Why Unmapped vs Mimic | Cost / Status |
|---|---|---|---|---|---|
| **1** | **`H86F-EWCS`** | `B18 (+dg/dx_east)`, `B11 (+dg/drow_south)`, `B13`, `B2`, `B3`, `B9`, `B6 (TC)`, `B4/B7/B8`, `B10/B16`, `B15`, `B17`, `B12/B19` + fold-visible `vis_cat` | Verduzco tilt-depth $|\nabla \arctan2(\text{B9},\text{B3})|$ at $\theta_{\text{mag}}=0$ + Laplace $g_{zz} = -(\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11})$ zero-crossing steepness + Pollard–Segall off-axis wing-crack lobes & opposing-tip stepover bridges minus mid-segment broadside elastic stress shadows in nested cross-component PU HGB | Catches blind range-tip propagations & releasing stepovers where broadside flanks sit in stress shadows; mimics: pluton/caldera walls, Lahontan benches over basalt | Low-medium · **HOLDOUT VALIDATED (`0.1723`); AUDIT TIFF `DO NOT SUBMIT` (REGISTRY BLOCKED)** |
| **2** | **`H86F-GDFB`** | `B18`, `B11`, `B13`, `B2`, `B3`, `B9`, `B8`, `B17` | Garland (1951) Poisson tensor eigenvector misalignment $\sin^2(\psi_{\text{grav}}-\psi_{\text{mag}})$ weighted by $|\mathbf{g}_h|\,|\nabla\text{RTP}|$ in dilatant smectite zones (`B8>0`, `B17`), vetted by conservative gravity curl $|\partial_{\text{row}}\text{B18}-\partial_{\text{col}}\text{B11}|$ | Hydrothermal magnetite destruction rotates/destroys magnetic susceptibility while preserving fault-block density step; mimics: reversed basalt over Paleozoic carbonate | Low-medium (`~15 min` CPU) · Deferred (3-exp budget) |
| **3** | **`H86F-PFSB`** | `B6 (TC)`, `B12`, `B19`, `B15`, `B18/B11`, `B17`, `B10/B16` | Bekker–Davis Selected-At-Random propensity PU correction $P(\text{fault}\mid x) = P(\text{labelled}\mid x)/c(x)$ where canyon-mouth alluvial-fan burial propensity $c(x)$ is diagnosed by piedmont concavity + low slope (`B19`) + smooth high-TC potassic fan-wash plumes (`B6`) | Directly corrects `1–8 km` catalog gaps across active Holocene debris-flow fan apexes; mimics: buried non-tectonic pediment ledges | Medium (`~25 min` CPU) · Deferred (3-exp budget) |
| **4** | **`H86F-USGS-3DGF`** | External USGS SIR 2010-5193 Great Basin 3D Hydrogeologic Framework basin-fill thickness grids + `B15`, `B13`, `B18/B11`, `B7/B8` | Borehole/seismic-constrained Cenozoic fill thickness minus Jachens–Moring gravity basement (`B15`) to isolate `<1.5 km` intrabasin horst/graben steps independent of gravity-inversion circularity | Catches closely spaced intrabasin faults smoothed out by `2 km` regional gravity inversion; mimics: volcanic-edifice differential compaction / well kriging bullseyes | High · `NOT_VIABLE_YET` (ScienceBase outside sandbox allowlist) |

---

## 4. Three-Pass Execution & Verification Log

### Pass 1 — Implementation, Holdout Validation & Pre-Placement Stop
1. Fast-forwarded to latest `origin/main` (`b28b022`, incorporating PRs #93–#96), restored SHA-pinned competition mirrors (`training_features.tif`, `existing_faults.tif`, `sample_submission.tif`) and all `655` registry blobs (`728.3 MB`), and refreshed live GitHub metadata across all `92 / 92` named repositories (`scripts/refresh_fleet.py`).
2. Froze `registry/h86f_hypotheses.json` and `research/H86F_EWCS_PREREGISTRATION.{json,md}` prior to writing `src/gems86_ewcs/features.py` and `scripts/run_h86f_ewcs.py`.
3. Executed `scripts/run_h86f_ewcs.py` (`3` arms + `R0_D28` control; nested cross-component visible-fault splitting to prevent zero-distance self-overfitting; `float16` memmap streaming to keep RSS `< 700 MB`; clean child-process `check_h86e_registry.py --surface` across `687` rasters). Recorded `docs/evidence/h86f-ewcs-run-card.json` and `docs/evidence/h86f-ewcs-registry-surface.json`, halting cleanly before placement/serialization per `AGENTS.md` Rule 11.

### Pass 2 — Adversarial Code & Repository Defect Review
1. **Caught and fixed `IR-86-MMT-UNBOUND-SURFACE-PASS-20261024`:** Discovered that PR #93's `docs/evidence/h86e-mmt-registry-surface.json` still carried `"surface_gate_pass": true` despite `2` invalid registry rows in `"errors"`, contradicting `h86e-mmt-run-card.json` (`false`) and `AGENTS.md` Rule 11. Repaired to `"surface_gate_pass": false` with an explicit archive note.
2. **Caught and fixed `IR-86-MMT-SERIALIZE-AFTER-FAILED-DOT-GATE-20261024`:** Discovered that `scripts/run_h86e_mmt.py` called `write_candidate(...)` unconditionally even when `final_dots_gate_pass`, `literal_gate_pass`, or `chance["gate_pass"]` was `False`, and called `subprocess.run(..., check=True)` before inspecting `surface_report`. Hardened `run_h86e_mmt.py` to fail closed before both placement and serialization.
3. **Caught raster-vs-Cartesian sign subtlety in Laplace $g_{zz}$:** Because `Band 11` is $+\partial g / \partial\text{row}_{\text{south}} = -\partial g / \partial y_{\text{north}}$ while `Band 18` is $+\partial g / \partial\text{col}_{\text{east}}$, the horizontal Laplacian in image coordinates `(row, col)` is $+\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11}$ (not minus!), giving $g_{zz} = -(\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11})$ and conservative curl $\partial_{\text{row}}\text{B18} - \partial_{\text{col}}\text{B11} = 0$. Added exact polynomial potential unit tests in `tests/test_h86f_ewcs.py`.
4. **Checked `tmp_path` test compatibility in `scripts/build_site.py`:** Ensured `render(root)` enforces `h86f-ewcs-run-card.json` on the canonical repository root while remaining compatible with synthetic partial `tmp_path` fixtures in `tests/test_current_review.py`.

### Pass 3 — Line-by-Line Prompt Audit, Source Recheck & Full Suite Verification
- Verified all official non-portal sources via `scripts/review_sources.py` (`docs/evidence/review-source-checks.json`; zero automated `drivendata.org` requests per `AGENTS.md` Rule 9):
  - DrivenData Competition Overview & Metric (manual browser reference): <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
  - Official DOE/NLR Prize Rules PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
  - Official Reference Solution (SHA-verified): <https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md>
  - USGS GeoDAWN Airborne Magnetic & Radiometric Surveys: <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
  - DOE GDR INGENIOUS Regional Dataset (#1391): <https://gdr.openei.org/submissions/1391>
  - Great Basin Center for Geothermal Energy (INGENIOUS): <https://gbcge.org/current-projects/ingenious/>
  - EPSG:32611 WGS 84 / UTM Zone 11N: <https://epsg.io/32611>
- Re-ran `audit_release.py --measure-registry`, `audit_downloads.py --write`, `build_site.py`, `build_site.py --check`, `check_site.py`, `build_ledger.py --check`, `audit.py`, `validate_download.py`, `compileall`, and full `pytest -q`.

---

## 5. Remaining Limitations & Recommended Next Steps for Future Sessions

1. **Resolve the dual upstream registry blockers in `60GEMSDOE` / owner protocol:**
   - Remove or reclassify non-submission continuous probability surfaces (`17GEMSDOE` `ab0a0a62...`, `100%` support) and non-grid/auxiliary files (`14GEMSDOE` wrong origin `(500000, 4500000)` and `7GEMSDOE` 3-band `uint8` `qfaults_prior_u8.tif`) in the upstream canonical registry index, and address dense `180k–344k`-dot rasters (`13GEMSDOE` stride-5 lattice `b4570b40...` covering `99.87%` within `3 px`) via an owner-ratified protocol update rather than private threshold edits.
2. **Calibrate holdout ranking against human-obtained `ORGANIZER-CONFIRMED` submission receipts:**
   - Buffered hide-and-recover `HOLDOUT-DTI`withholds segments from the existing USGS/INGENIOUS catalog, whereas the private DrivenData test set scores fault traces *absent* from that catalog. Before claiming leaderboard improvement over `0.2778` (`OWNER-REPORTED`), bind organizer submission receipts into `ledger/submissions.csv`.
3. **Test `H86F-GDFB` (Rank 2) and `H86F-PFSB` (Rank 3) as incremental features on top of `H86F-EWCS`:**
   - `H86F-EWCS` already established `+0.0483` `HOLDOUT-DTI` gain over `H86C-KSLB` (`0.1723` vs `0.1241`) and `+0.0131` (`[+0.0012, +0.0261]`) over its isotropic-tip ablation. Adding Bekker–Davis canyon-mouth fan-burial propensity reweighting (`H86F-PFSB`) is the highest-leverage next pure-competition experiment once a new 3-experiment session budget opens.
