# Session `95a42d60` PhD Structural-Geophysical Analysis, `H86I` Hypotheses & Three-Pass Review (`2026-10-25`)

- **Branch:** `arena/95a42d60-gemsdoe86`
- **Primary candidate receipt:** [`docs/evidence/h86i-sacd-run-card.json`](../docs/evidence/h86i-sacd-run-card.json)
- **Generated unique GeoTIFF (audit-only):** [`docs/downloads/gems86-h86i-sacd-spin2-submod-37654dots-20261025T040150Z-0544ef05-zeros.tif`](../docs/downloads/gems86-h86i-sacd-spin2-submod-37654dots-20261025T040150Z-0544ef05-zeros.tif) (`SHA-256: b15a89fa1917526c1ce32081c1802d39333dc497d0d0d1034dc962df47c691e0`)
- **Automated submission status:** **`DO NOT SUBMIT`** (`verdict: "negative"`, `safe_to_submit: false`, `approved_for_weekly_slot: false`, `submission_slots_used: 0`)

---

## 1. PhD Analysis: Why `GEMSDOE32` (`h33-h33-2-b2`: `0.2778` `OWNER-REPORTED`) Led the Supplied Fleet — and How to Surpass `0.2778` / `0.3195` / `0.4413`

### 1.1 Exact Pixel & Metric Forensics of `GEMSDOE32` (`h33-h33-2-b2`)

Direct pixel-level comparison on the `3730 × 3292` (`12,279,160`-cell, `100 m`, `EPSG:32611`) competition grid between `GEMSDOE28` (`h27-4-r1-solo-d2-8`, SHA-256 `ab0230015224...`, `0.2708` `OWNER-REPORTED`, `40,199` unit dots) and `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, SHA-256 `c55bafc4...`, `0.2778` `OWNER-REPORTED`, `37,654` unit dots) establishes an exact mathematical identity:

1. **Zero new geological detections were added:** `0` pixels are positive in `H33` that were zero in `GEMSDOE28`.
2. **Exact `2,545`-dot collar subtraction:** `H33` removed `2,545` unit dots sitting at Euclidean distances $\sqrt{2} \le d_{\text{cat}}(u) \le 2.0\text{ px}$ (`141–200 m`) from mapped `existing_faults.tif` traces.
3. **Why collar pruning & `~2.8 px` Poisson-disc spacing raised `DTI` without changing the underlying classifier:**
   Under the official Distance-Weighted Tversky Index (`vendor/gems57/metric.py`, $\alpha = 0.2$, $\beta = 0.8$, $R = 3.0\text{ px} = 300\text{ m}$ triangular kernel $K_3(d) = \max(0, 1 - d/3)$):
   $$\text{DTI}(P, G) = \frac{T}{T + 0.2\,F + 0.8\,(N - T) + \epsilon} = \frac{T}{0.2\,T + 0.2\,F + 0.8\,N + \epsilon}$$
   where $T = \sum_{g \in G} \max_{u \in P} p(u) K_3(\|u-g\|_2)$ and $F = \sum_{u \in P \setminus M_{\text{cat}}} p(u)\big(1 - \max_{g \in G} K_3(\|u-g\|_2)\big)$.
   - **Max-envelope non-additivity (why continuous probabilities and narrow ribbons collapse):** Because $T$ takes a **pointwise $\max$** over $u \in P$ whereas $F$ **sums linearly** over every positive pixel $u \notin M_{\text{cat}}$, a continuous posterior map (e.g., `GEMSDOE2` `0.0680` `OWNER-REPORTED`) or dense `1`-px streak pays `5x–25x` redundant `FP` mass per unit of captured `TP_w`, driving `DTI < 0.09`. Emitting discrete unit dots ($p(u) \in \{0, 1\}$) spaced near $2.8\text{ px}$ keeps adjacent `3 px` kernels nearly non-overlapping while maintaining ridge coverage.
   - **Exact collar-pruning inequality:** Because organizer scoring masks **only exact mapped fault pixels** ($d_{\text{cat}} = 0$, Forum Thread 11516), dots placed at $1 < d_{\text{cat}} \le 2\text{ px}$ along already-mapped fault flanks incur full `FP = 1.0` unless an unmapped splay branches within $300\text{ m}$. Removing a subset of dots that sacrifices truth credit $\Delta T = a \ge 0$ while shedding false-positive mass $\Delta F = b > 0$ strictly increases `DTI` if and only if:
     $$T\,b > a\,(F + 4N + 5\epsilon)$$
     In `H33`, removing `2,545` near-catalogue flank dots shed $b \approx 2{,}400+$ unmasked `FP` units while losing almost zero `TP_w` ($a \approx 0$), accounting for the `0.2708 -> 0.2778` (`+0.0070` `OWNER-REPORTED`) jump.
   - **Lineage ceiling across the 92-site fleet:** Every `OWNER-REPORTED` score above `0.2600` in `registry/prior_scores.csv` (`GEMSDOE32` `0.2778`, `GEMSDOE36` `0.2750`, `GEMSDOE29` `0.2719`, `GEMSDOE28` `0.2708`) shares `92.64%–100.0%` 3-px dot overlap with the same `H19-5 / D2.8` parent surface. Re-pruning or re-spacing that fixed surface cannot cross `~0.28`.

### 1.2 What Separates `~0.278` from `0.3195` / `0.4413` (`OWNER-REPORTED` Context Only)

*(Evidence-class discipline: `0.2778`, `0.3195`, `0.4413`, `GEMSDOE89 = 0.0301`, and `GEMSDOE90 = 0.0749` are `OWNER-REPORTED` prompt inputs without organizer receipts, and `HOLDOUT-DTI` is never projected onto leaderboard scale.)*

To recover genuinely unmapped private-test faults beyond `H33`'s `100 m` static feature surface, three structural-geophysical barriers must be overcome simultaneously:

1. **Resolution barrier across Holocene alluvial fan aprons (`1 m` & `10 m` 3DEP vs `100 m` `det_elev`):** Degraded `< 1.5 m` piedmont scarps are smoothed below noise in `100 m` `Band 12 (det_elev)` / `Band 19 (det_elev_slope)` (`single-feature AUC = 0.5163`), whereas SHA-pinned `10 m` 3DEP profile curvature (`AUC = 0.5943`) and `1 m` bare-earth LiDAR crest-toe dipoles (`AUC = 0.5913`) resolve subtle Holocene ruptures directly, provided Pleistocene Lake Lahontan (`~1,255–1,345 m`) shoreline benches are deconfounded where scarp strike parallels regional elevation contours.
2. **Cover-blind basement & hydrothermal fluid-conduit physics:** Completely buried intrabasin relay ramps and geothermal production structures have zero surface scarp (`c(x) -> c_min`) and must be detected via **vector-consistent Laplace vertical gravity curvature** $g_{zz} = -(\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11}) = 0$, **Verduzco analytical magnetic tilt** $\theta_{\text{mag}} = \arctan2(\text{B9}, \text{B3}) = 0$, **Jacobsen (1987) shallow-vs-150 m upward-continuation magnetic attenuation** (`Band 14` vs `TMI_up150`), and **GeoDAWN potassic/uraniferous hydrothermal alteration** (`K/Th`, `U/Th`) paired with `Band 17 (cond_surf)` smectite-illite boundaries.
3. **Directional Coulomb stress-transfer specificity:** Blindly extending scalar halos around mapped fault terminations (`H86F-EWCS`) admits transverse non-tectonic edges (shorelines, E–W survey leveling seams, cross-range drainages). Requiring **spin-2 strike concordance** $\cos 2(\theta_{\text{obs}} - \theta_{\text{stress}}) > 0$ between observed multi-physics directors and projected Pollard–Segall wing-crack / collinear-tip / releasing-stepover trajectories provides a first-principles directional filter.

---

## 2. Four Novel Candidate Geological Hypotheses (`registry/h86i_hypotheses.json`)

Declared and SHA-pinned **prior to any model implementation or holdout evaluation**:

| Rank | ID | Layers (Verified vs `src/gems86/io.py` & `EXTERNAL_PINS`) | Physical Signature & Transform | Why Missing from USGS/INGENIOUS Catalogue | Named Non-Fault Mimic | Status |
|---:|---|---|---|---|---|---|
| **1** | **`H86I-SACD`** | Native `B2, B3, B4, B6, B7, B8, B9, B10, B11, B12, B14, B15, B16, B17, B18, B19` + USGS CC0 `lidar_scarp`, `topo_10m`, `dem10_chi`, `geodawn_rad`, `geodawn_extensions` + fold-visible `vis_cat` | Spin-2 Coulomb failure-strike inner product $\cos 2(\theta_m - \theta_{\text{stress}})$ across LiDAR/10 m scarps, Laplace $g_{zz}=0$, and Verduzco magnetic tilt $\theta_{\text{mag}}=0$ + Jacobsen `150 m` upward-continuation attenuation + `K/Th` & `U/Th` alteration + Bekker–Davis propensity PU + Minoux `300 m` submodular allocation | Recovers buried piedmont/intrabasin splay & stepover continuations where low geomorphic exposure $c(x)$ caused airphoto mapping omissions while rejecting orthogonal Lahontan shorelines and flight-line seams | Subvertical Tertiary mafic dike swarms / welded tuff cooling joints subparallel to NNE extension; Lahontan highstand bars parallel to range fronts | **VALIDATED IN PASS 1 (`3` arms; negative; `DO NOT SUBMIT`)** |
| **2** | **`H86I-BHGD`** | Native `B15, B18, B11, B12` + USGS CC0 `dem10_chi_100m_i16.tif` | Biharmonic thin-plate basement flexure $\nabla^4 \text{B15}$ intersected with cross-divide fluvial $\Delta\chi$ jumps (`step_max_x1000`) & $k_{sn}$ knickzones | Blind normal faults (`200–600 m` tip burial) warp fans into broad monoclines without surface scarps while driving active drainage divide migration | Differential compaction of Plio-Pleistocene clays over paleotopographic ridges; resistant volcanic ledges | `VIABLE_NOW` (deferred under 3-experiment cap) |
| **3** | **`H86I-RGDW`** | Native `B4, B7, B8, B10, B16, B2, B3, B9` | Dimensionless kinematic vorticity/partitioning gradient $|\nabla[(B7 - |B8|)/(B4 + \epsilon)]|$ focused onto Verduzco magnetic tilt hinges & microseismicity | Low-vertical-throw strike-slip Walker Lane / Humboldt accommodation faults lack tall topographic scarps despite sharp basement magnetic truncations | Sparse GPS kriging transitions; 1915/1954 CNSB viscoelastic relaxation halos | `VIABLE_NOW` (deferred under 3-experiment cap) |
| **4** | **`H86I-INSAR`** | NASA ASF DAAC ARIA / COMET LiCSAR Sentinel-1 2015–2025 Asc+Desc LOS velocity & coherence (`100 m`) + Native `B7, B8, B12, B17, B19` | `100 m` vertical ($v_U$) & east-west ($v_E$) creep-rate `300 m` cross-strike step filter along MT conductivity boundaries (`B17`) | Detects active interseismic fault creep & geothermal pore-pressure compartments across flat playas with zero scarp (`100x` finer than GPS) | Agricultural groundwater-pumping subsidence bowl margins; seasonal playa smectite swelling rings | **`NOT_VIABLE_YET`** (egress restricted; no pinned GitHub mirror) |

---

## 3. Pre-Coding Empirical Layer Physics Verification (`AGENTS.md` Rule 8)

Before encoding `src/gems86_sacd/features.py`, we verified coordinate frames empirically across `395,607` high-coherence `1 m` LiDAR scarp cells and all `60,988` mapped fault cells:

- **`lidar_scarp_features_u8.tif` Band 11 (`strike`):** Spans `[1, 255]` and encodes $\theta = \pi \cdot \text{strike}_{u8} / 256$ directly in the `(dx_east, dr_south)` image frame (`mean spin-2 dot = +0.5005` vs `100 m` DEM scarp strike; a clockwise-from-North assumption would have inverted the sign to `-0.5005`).
- **Spin-2 alignment with real mapped fault tangents across `60,988` positive cells:**
  - `1 m` LiDAR scarp director: `+0.0942`
  - Vector gravity density-step director `(-B11, +B18)`: `+0.1753`
  - Verduzco magnetic tilt zero-contour director: `+0.1384`

---

## 4. Strict Spatial LOQO Holdout, Leakage Canary & Registry Results (`H86I-SACD`)

### 4.1 Single-Feature Leakage Canary (`33 / 33 PASS`)
Tested on `11,321` buffered whole-component withheld positives vs `300,000` footprint negatives (`gems57-pooled-hide-v2`, `seed=20`, `buffer_px=3`):
- **Maximum symmetric AUC:** `0.7639 <= 0.90` (`collinear_tip_cone`) — **0 leakage flags**.
- Notable standalone physical signals on unmapped whole components: `topo10_prof_scarp` (`0.5943`), `lidar_crest_toe_dipole` (`0.5913`), `topo10_lineament_relief` (`0.5855`), `lidar_scarp_lahontan_deconf` (`0.5787`), `strain_vorticity_part` (`0.5621`), `spin2_concord_scarp` (`0.5563`), `spin2_concord_grav` (`0.5495`), `spin2_concord_mag` (`0.5348`).

### 4.2 Pooled Holdout Results (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`, `11,321` Withheld Positives, `1,000` Paired `20 km` Block-Bootstrap Draws)

| Arm / Comparator | Evidence Class | Design Scope | `HOLDOUT-DTI` | `95% CI` | `TP_w` | `FP_w` |
|---|---|---|---:|---|---:|---:|
| `E1_sacd_full_submod` (`37,654` dots) | `HOLDOUT-DTI` | Strict spatial LOQO (`quad != fold_i`) | **`0.0832`** | `[0.0673, 0.0997]` | `1,354.8` | `34,763.9` |
| `E2_sacd_scalar_unweighted_thin` (`37,654` dots) | `HOLDOUT-DTI` | Strict spatial LOQO (`quad != fold_i`) | **`0.1055`** | `[0.0878, 0.1257]` | `1,710.7` | `34,099.0` |
| `E3_sacd_cover_blind_subsurface` (`37,654` dots) | `HOLDOUT-DTI` | Strict spatial LOQO (`quad != fold_i`, zero topo/LiDAR/χ) | **`0.0843`** | `[0.0693, 0.0995]` | `1,364.2` | `34,227.9` |
| `R0_D25_foldfair` (`GEMSDOE25` masked at `d_vis > 3`) | `HOLDOUT-DTI` | Zero-extra-fit external baseline | `0.0931` | `[0.0802, 0.1067]` | `1,506.9` | `34,128.3` |
| `R0_D28_visible_collar` (`GEMSDOE28` masked at `d_vis > 3`) | `HOLDOUT-DTI` | Zero-extra-fit external baseline | `0.0273` | `[0.0228, 0.0318]` | `434.8` | `33,915.3` |
| Archived `H86C-KSLB` (`44,090` dots) | `HOLDOUT-DTI` | Same split (`docs/evidence/lane86c_results.json`) | `0.1241` | `[0.1080, 0.1403]` | — | — |
| Archived `H86F-EWCS` (`37,654` dots) | `HOLDOUT-DTI` | Same split, trans-quadrant PU (`IR-86-H86F-EWCS-TRANSQUAD-PU-20261025`) | `0.1723` | `[0.1530, 0.1898]` | — | — |

**Key Diagnostic Insights from the Honest Negative Result (`E1 - E2 = -0.0223 [-0.0352, -0.0104]`):**
1. **Pure cover-blind subsurface (`E3 = 0.0843`) matched full `E1` (`0.0832`):** Subsurface potential-field + GeoDAWN alteration + Spin-2 gravity/magnetic concordance alone recovered `1,364.2` weighted truth pixels with zero DEM, LiDAR, or fluvial inputs.
2. **Why `E2` (`0.1055`, beating `R0_D25` `0.0931`) outperformed `E1` (`0.0832`):** Two mechanisms degraded `E1`: (a) forcing Fold-1/2/3 predicted quantile distributions to match Fold-0 (`NW`) over-allocated `10,797` dots into lower-fault-density `NE` (`NE DTI = 0.0292` vs `NW DTI = 0.1459`), and (b) `submodular_kernel_allocate` with `bg_floor = q0.72, gamma = 1.20` favored broad `29-px` moderate-posterior basin plateaus (`29 * 0.08`) over sharp `2-px` fault ridges (`3 * 0.50`), whereas `disc_thin(2.8)` in `E2` locked directly onto sharp ridge crests (`TP_w = 1,710.7`).
3. **Forensic discovery `IR-86-H86F-EWCS-TRANSQUAD-PU-20261025`:** Line-by-line review of `scripts/run_h86f_ewcs.py` (`line 519`) revealed that `H86F-EWCS` sampled visible positives and unlabeled background across all 4 quadrants simultaneously (zero hidden-truth leakage, as `vis` stripped `hidden` + `3 px` globally, but trans-quadrant rather than strict `quad != fold_i` spatial out-of-quadrant training).

### 4.3 Full-Registry `v2` Uniqueness & Local Format Validation
- **Pre-placement surface (`docs/evidence/h86i-sacd-registry-surface.json`):** `688 / 690` valid competition-grid rasters checked (`0` missing), **`0` Spearman `rho > 0.90` firings (`worst = 0.7734`)**.
- **Final dots (`docs/evidence/h86i-sacd-registry-final-dots.json`):** `byte_unique = true`, `pixel_unique = true`, **`0` Spearman `rho > 0.90` firings (`worst = 0.1022`)**, and **`0 / 365` discrete `<= 50,000`-dot rasters exceeding `0.70` 3-px forward overlap** (`max = 0.6926`; **`31.17%`** vs `GEMSDOE32` `h33-h33-2-b2`; **`55.60%`** vs `H86F-EWCS`).
- **Fail-closed blockers:** Space-filling lattices (`13GEMSDOE` `99.87%` halo) and continuous-support `17GEMSDOE` (`100.0%` support) exceed `0.70` literal overlap, and `2` off-grid upstream rows (`14GEMSDOE`, `7GEMSDOE`) make `registry_complete_for_index = false` (`PA-86-02` `FAILED_CLOSED_NO_REPORT`).
- **On-disk validator (`validate.validate` + `gates.format_report`):** `15 / 15` checks `PASS` (`single_band`, `float32`, `3730×3292`, `EPSG:32611`, `[0.0, 1.0]`, `0` NaN/Inf, `0` outside-footprint mass, `0` catalogue dots, valid single-TIFF `.zip` and `.json` writer receipt).

---

## 5. Three-Pass Engineering & Governance Audit Log

- **Pass 1 (Autonomous Data Restoration, Physics Verification, Preregistration & Execution):**
  Restored all SHA-pinned native competition rasters, 5 USGS CC0 external rasters, 21 native band `.npy` arrays (reproducing `data/prepared_manifest.json` bit-for-bit across all 21 SHA-256 digests), and all `655` cross-repo registry blobs; empirically verified `lidar_scarp` `strike_u8` (`pi * u8 / 256` in `(dx_east, dr_south)`); froze `registry/h86i_hypotheses.json` & `research/H86I_SACD_PREREGISTRATION.json`; executed `H86I-SACD` in `1,323.96 s` (`<= 2 h` cap) generating audit-only `gems86-h86i-sacd-spin2-submod-37654dots-20261025T040150Z-0544ef05-zeros.{tif,zip,json}`; locked `require_feasible()` in `scripts/run_h86i_sacd.py`.
- **Pass 2 (Bug, Edge-Case & Assumption Hunt):**
  1. Caught and avoided `-3.4028235e+38` float32 out-of-footprint sentinel overflow (`np.isfinite` is `True` on `-3.4e38`; `_read_native_band` enforces `footprint & (raw > -1e20)`).
  2. Verified `strike_u8` sign empirically before coding (`+0.5005` vs `-0.5005` under clockwise-from-North).
  3. Added `--manifest` CLI option to `scripts/prepare_data.py` so standalone cache builds do not overwrite pinned `data/prepared_manifest.json`.
  4. Documented `IR-86-H86F-EWCS-TRANSQUAD-PU-20261025` without mutating historical run cards.
  5. Fixed accidental HTML `</li>` truncation in `scripts/build_site.py` `irregularities()` before rendering.
  6. Caught and fixed a real `ENOSPC` (`[Errno 28] No space left on device`) fixture defect in `tests/test_release_audit.py::release_copy`, which previously copied the `418 MB` `data/bridge/training_features.tif` `16` times (`6.7 GB` per `pytest` run, `20.1 GB` across pytest's 3-run cache) whenever full competition data was restored locally, even though `audit_release.py` only reads `existing_faults.tif` and `sample_submission.tif`.
- **Pass 3 (Full Prompt, CI Workflow & Live Preview Audit):**
  Re-ran `audit_downloads.py --write`, `audit_release.py --measure-registry`, `build_site.py`, `build_site.py --check`, `check_site.py`, `build_review_card.py --check`, `audit.py`, `validate_download.py`, `compileall`, `pytest -q`, and `unittest discover`, plus inspected live HTTP preview of `docs/index.html` and `docs/executive-summary.html`.

---

## 6. Prioritized Handoff Recommendations

1. **Combine `H86I` multi-resolution `1 m` LiDAR / `10 m` 3DEP + Spin-2 Concordance with `E2` Sharp `disc_thin(2.8)` Ridge Decoding (No Forced Inter-Quadrant Quantile Equalization):** Our `H86I` experiment proved that `E2` (`disc_thin(2.8)`) captured `+355.9` more `TP_w` than `bg_floor = q0.72` submodular plateau allocation; keeping sharp ridge thinning (`gamma >= 3.0` or `disc_thin(2.8)`) and raw un-equalized PU posteriors across quadrants directly eliminates both failure modes observed in `E1`.
2. **Selector-Level Registry Hygiene Resolution:** Quarantining the `2` non-competition-grid upstream inventory rows (`14GEMSDOE` shifted transform, `7GEMSDOE` 3-band visualization) in a future selector-authorized `v3` registry manifest is required before `PA-86-02` can run end-to-end; until then, `0` weekly slots should be spent.
