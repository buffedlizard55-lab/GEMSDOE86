# GEMSDOE86 — Audited Subsurface Fault-Prediction Research (`Lane H86-WVB`)

## 🔴 AUTOMATED PROTOCOL DECISION: DO NOT SUBMIT TO WEEKLY PORTAL SLOT (`verdict: negative`)

- **Unique Validated GeoTIFF (`.tif`):** [`docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif`](docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif) (`134 KB`, `SHA-256: d0231888c4567816d706cca360c8fe0cd98fc0b673409edb3ffc5649e3d1bdf3`)
- **Single-TIFF Archive (`.zip`):** [`docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.zip`](docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.zip) (`SHA-256: b5c38a4a4a8664003b7a4601c926f0093ae791ae292222f7f5d0e8d627d5281e`)
- **GitHub Pages Dashboard & Executive Summary:** [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html) · [Live GitHub Pages](https://buffedlizard55-lab.github.io/GEMSDOE86/)
- **Machine-Readable Evidence:** [`docs/evidence/run-card.json`](docs/evidence/run-card.json) · [`docs/evidence/h86_wvb_results.json`](docs/evidence/h86_wvb_results.json) · [`research/REVIEW.md`](research/REVIEW.md) · [`research/VERIFICATION.md`](research/VERIFICATION.md)
- **Submission Name:** `gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros`
- **Portal Note (`94 <= 140` chars):** `GEMS86 H86-WVB wavenumber+geotherm+scarp+valve submod300 37654d HOLDOUT-DTI=0.1579 [0,1] zeros`

### Automated 4-Gate Verdict Summary (Zero Human Inspection)

| Gate | Requirement | Measured Result (`H86-WVB` / `E3_dual_submod300`) | Status |
|---|---|---|---|
| **Gate 1 · Format & `[0, 1]`** | Single-band `float32`, `EPSG:32611`, `3730x3292`, `100 m`, no NaN/Inf/sentinels, strict `[0, 1]` | **`15 / 15` checks passed** (`min=0.0, max=1.0, nan=0, inf=0`, `37,654` dots in footprint, `0` outside, `0` on catalogue) | **✅ PASS** |
| **Gate 2 · Leakage Canary** | Single-feature discriminative holdout `AUC <= 0.90` | **`36 / 36` features `<= 0.90`** (`seed=20` `0.87047`, `seed=21` `0.86697`, shuffled `0.51399`) | **✅ PASS** |
| **Gate 3 · Buffered Holdout DTI** | Beat `d2.8` & fold-fair `H33` on `gems57-pooled-hide-v2` (`22,893` px, 95% CI) | **`HOLDOUT-DTI = 0.15792 [0.13884, 0.17587]`** vs `d2.8 = 0.10093` (**`+56.5%`**, `Δ = +0.05700 [+0.03513, +0.07752]`) & `h33_foldfair = 0.10564` (**`+49.5%`**) | **✅ PASS** |
| **Gate 4 · 43-Raster Uniqueness** | Surface & dot `|Spearman| <= 0.90` AND 3-px dot overlap `<= 0.70` vs every registry raster | Spearman `PASS` (`0.1271` / `0.0949`); **30/30 sibling champions (`GEMSDOE32..88`) `PASS`** (`max = 0.6353`; `H33-2-B2 = 0.2928`); **2 upstream `gems10` priors `> 0.70`** (`gems10-h25 = 0.7853`, `gems10-h28 = 0.7415`) | **❌ FAIL -> `negative`** |

> **Why `DO NOT SUBMIT` (`verdict: negative`):** Even though `H86-WVB` achieved a statistically significant `+0.0570` buffered `HOLDOUT-DTI` gain over `d2.8` (and `+0.1159` over prior PR #6 `H86-RMRB`) while remaining distinct from all 30 modern sibling champions (`GEMSDOE32..GEMSDOE88`), **Parallel-Run Protocol Rule 1 & Rule 5** require stopping and logging `verdict: "negative"` when >70% of candidate dots fall within 3 px of any registered raster after `3/3` budgeted experiments. **Zero weekly DrivenData submission slots were spent.**

---

## Starting brief — read at the beginning of every session

The following is a **condensed operational record** of the owner's long request, not a verbatim transcript. The original conversation remains the complete prompt. Read this AND `research/REVIEW.md` before work. Unfulfilled requirements remain explicit blockers rather than completed checkboxes.

- Review previous work first; maximize probability of winning through evidence, and own the outcome end to end. Do not trade scientific integrity for an optimistic claim.
- Generate a UNIQUE competition-format single-band GeoTIFF, never copy an earlier submission except for education. Make download and readiness status obvious at the beginning of the site. Supply a distinct name and note of at most 140 characters.
- Work autonomously through implementation, bug/edge-case review and final requirements review. Research official free data, preserve provenance and links, flag irregularities, distinguish verified facts from hypotheses. Explain access limits and next steps honestly.
- Parallel-run lane is the single assigned method paragraph. **None was present in the supplied request.** Do not guess authorization or drift into another lane. Surface and final-dot checks must stop on rank correlation >0.90 or >70% dots within 3 px of any registered raster.
- Reuse cached features, `evaluate_holdout.py` and `submission_writer.py`; do not privately fork shared tools. Hide complete fault segments with buffers. Derive catalogue features from visible faults only and mask visible faults exactly. Pool distance-tolerant Tversky components: alpha 0.2, beta 0.8, 300 m triangular kernel.
- Test each feature alone; holdout AUC >0.90 means suspected leakage until disproven. Generate/rank three to five untested geological hypotheses with named layers, signatures, missing-fault mechanism, mimics, novelty and cost before experiments. Confirm external data availability before treating an external-data idea as viable.
- Benchmark against the best comparable spatial holdout before touching a weekly slot. Stop after three experiments or two hours. Selection/promotion into a real slot is separate and must respect the authenticated weekly cap.
- Report scores ONLY as `HOLDOUT-DTI` (version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (actual submission receipt). User-reported values and projections are not confirmed scores. The request contains conflicting leaderboard highs; resolve against official evidence, not repetition.
- End with one JSON run card: hypothesis, mechanism, named non-fault mimic, holdout result+CI, registry comparisons, SHA256, serialized raster validation, submission name, short note, promote/negative. Negative results are deliverables.
- Build a clean GitHub Pages site with an executive summary explaining exactly how to submit. Reject NaN/Inf/sentinels and values outside `[0,1]`, and match the template's CRS/shape/transform. Automated inspection must replace unsupported “human inspected” claims.
- Preserve source knowledge for future projects. Target fault prediction relevant to geothermal exploration; do not pretend a prediction proves a geothermal vent. Open and merge a PR, then list remaining limitations.

---

## 1. PhD Analysis: Why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778`) Led Listed GEMSDOE Sites & How to Score Higher

*(Score-label audit `IR-32-SCORE-01`: Neither `0.2778` for `GEMSDOE32` nor the prompt's cited leaderboard highs `0.3195` / `0.4413` carry local DrivenData submission-page HTML/screenshot receipts in git; they are cited strictly as owner/user-reported historical context, never `ORGANIZER-CONFIRMED`.)*

1. **Numerator Saturation vs Additive Denominator (`vendor/gems57/metric.py`):** Under official pooled Distance-Tolerant IoU ($\text{DTI} = \text{TP}_w / (\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w)$, 300 m = 3 px triangular kernel), truth credit $s_p(y) = \max_{\|x-y\|_2 \le 3} p(x)(1 - \|x-y\|_2/3)$ saturates at **one binary dot per 300 m fault segment**, whereas false-positive penalty $0.2 \sum_x p(x)(1 - s_q(x))$ accumulates **linearly** across every emitted pixel. Replacing continuous 1-px ridges (`gems19-h19-5`, `121,131` px, owner-reported `0.1922`) with `2.8 px` (`280 m`) Poisson-disk dots (`gems24 d2.8`, `44,090` dots, owner-reported `0.2600`) eliminated `63.6%` of redundant ridge mass while preserving ~93% of kernel coverage.
2. **Known-Catalogue Flank Collar (`B = 2 px`) + Finite `zeros` Serialization:** Because organizers confirmed (DrivenData forum thread `11516`) that mapped USGS/INGENIOUS catalogue traces are excluded from evaluation truth, `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `37,654` dots) pruned `6,436` flank dots within `200 m` (`d_cat <= 2 px`) of `d2.8` whose 300 m disks overlapped masked catalogue pixels (verified on our fold-fair buffered holdout: `0.10093 -> 0.10564`, `Δ = +0.00472 [+0.00379, +0.00577]`) and wrote finite `0.0` outside the footprint (`zeros` mode) to fix the portal `"Predicted values must be in range [0, 1]"` rejection.
3. **Can We Score Higher (`0.3195`–`0.4413`), and How?** Yes — algebraic inversion shows `H33-2-B2` earns ~`0.102` weighted truth pixels per emitted dot, and even zeroing `FP_w` completely at fixed recall caps below `0.34`. Reaching `0.3195`–`0.4413` requires raising per-dot truth credit to `0.118`–`0.165` by discovering **concealed intrabasin, piedmont, and stepover geothermal faults** beneath Cenozoic cover using potential-field source-depth concordance, fluid geothermometry/sinter vents, relief-normalized sub-100m scarps, and kernel-aware `2.8 px` allocation (`research/REVIEW.md` §1).

---

## 2. Pre-Implementation Ranking of 5 Untried Candidate Geological Hypotheses

| Rank & ID | Named Layers | Physical Transform & Missing-Fault Target | Named Non-Fault Mimic & Guard | Novelty, Cost & Viability |
|---|---|---|---|---|
| **1. `H86-WVB`** *(Executed)* | `training_features.tif` (14 geophysical/MT/geodetic/DEM bands), `geodawn_extensions_u8` (`TMI_up150`), `geodawn_rad_u8` (`K, Th`), `lidar_scarp_features_u8` (verified bands 1,3,6,7,9,10,12), `topo_10m_derived_100m_u8` (5–9), GDR #1391 wells/springs + `Paleo_geothermal_final.csv`, buffered `visible` traces + slip sense | Salem tilt local-wavenumber depth $z_{\text{mag}}$ concordant with `depth_to_base_surf`, 150 m upward-continuation persistence, silica/cation geothermometer disequilibrium ($T_{\text{res}} - T_{\text{out}}$) & sinter vents, relief-normalized 1 m/10 m scarps, and buffered crack-tip/two-host relays -> LOQO GBM + `2.8 px` kernel allocator | Miocene basalt flow margins & Pleistocene Lake Lahontan beach benches (~1,190–1,345 m), suppressed via `TMI_up150` persistence, 3D Mag/Grav concordance, and shoreline contour guard | Untried across `GEMSDOE28..88`; fixed `IR-86-LIDAR-01` & `IR-86-PR6-EVAL-01`; **`+0.0570` buffered `HOLDOUT-DTI` lift** (`20.7 min`, `<1.5 GiB` RAM) |
| **2. `H86-CCMO`** | `rtp` (2), `tmi_hg` (3), `tmi_vg` (9), `iso_grav_anom_hg` (18), `det_elev_slope` (19) | Conjugate displaced endpoints of passive magnetic contacts across 200–1,200 m cross-strike transfer corridors corroborated by gravity gradient rotation | Primary lava-channel terminations and aeromagnetic flight-line seams | Moderate-high precision on accommodation zones; ~60 s CPU (held in reserve) |
| **3. `H86-RTDR`** | `geodawn_rad_u8` (`K, Th, U`), `cond_surf` (17), `det_elev` (12), `det_elev_slope` (19) | Topographically deconfounded `K/Th` alteration ribbons + MT clay-cap gradient edges targeting sealed epithermal conduits | Felsic ash-flow tuff outcrops and playa evaporite fringes | Incorporated as channel `s_rad_kth_deconf` inside `H86-WVB`; ~35 s CPU |
| **4. `H86-TSBA`** | `geod_2ndinv` (4), `geod_shearrate` (7), `geod_dilaterate` (8), `depth_to_base_surf` (15) | Transtensional strain index weighting 2nd-derivative basement-step inflection crests | Unfaulted buried bedrock pediments | Coarse >15 km GPS wavelength standalone; incorporated as `s_transtens_idx` in `H86-WVB` |
| **5. `H86-SEIS-3D`** *(Blocked)* | USGS ANSS ComCat FDSN relocated hypocentres (`https://earthquake.usgs.gov/fdsnws/event/1/query`) | 3D RANSAC hypocentral plane-fitting projected up-dip to `EPSG:32611` for blind seismogenic geothermal swarms | Magmatic dike swarms and open-pit quarry blasts | **Non-viable in sandbox:** verified egress blocks `earthquake.usgs.gov` (`HTTP 000`) |

---

## 3. Budgeted 3-Experiment `HOLDOUT-DTI` Progression (`gems57-pooled-hide-v2`)

| Experiment / Baseline | Emitted Dots | Primary Buffered Whole-Component `HOLDOUT-DTI` (`22,893` px, 95% CI) | Paired `Δ` vs `d2.8` (95% CI) | Secondary `build_holdout` `all` (`22,641` px) | `build_holdout` `detached` (`22,619` px) |
|---|---:|---|---|---|---|
| `uniform_random_37654` | `37,654` | `0.04797 [0.04343, 0.05208]` | `-0.05296 [-0.06320, -0.04263]` | `0.04568` | `0.01361` |
| PR #6 `H86-RMRB` (fold-fair / pruned TIFF) | `37,654` / `60,000` | `0.00361 [0.00294, 0.00430]` (TIFF) | `-0.09732 [-0.10789, -0.08645]` | `0.04199` (fold-fair) | `0.04318` |
| `d28_incumbent` (`gems24 d2.8`) | `44,090` | `0.10093 [0.08974, 0.11164]` | `+0.00000` (baseline) | `0.10107` | `0.10346` |
| `h33_foldfair` (`d2.8` pruned `d_vis > 2 px`) | `~41,980` | `0.10564 [0.09373, 0.11728]` | `+0.00472 [+0.00379, +0.00577]` | `0.10482` | `0.03333` |
| **Exp 1 · `E1_static_physics_nms`** (0 catalogue bytes) | `37,654` | `0.07209 [0.05835, 0.08572]` | `-0.02883 [-0.04400, -0.01467]` | `0.07196` | `0.02538` |
| **Exp 2 · `E2_coupled_valve_nms`** (36 features + 3x3 NMS) | `37,654` | **`0.14237 [0.12739, 0.15614]`** | **`+0.04144 [+0.02257, +0.05904]`** | **`0.24734`** | **`0.11454`** |
| **Exp 3 · `E3_dual_submod300` (`H86-WVB`)** | `37,654` | **`0.15792 [0.13884, 0.17587]`** | **`+0.05700 [+0.03513, +0.07752]`** | **`0.30237`** | **`0.12233`** |

---

## 4. Verified Official Sources & Auditable Provenance

| Source / Asset | Official Provider & Link / DOI | Local Verification & Role |
|---|---|---|
| GEMS Competition Spec & Reference Code | U.S. DOE GTO / DrivenData ([Competition 300](https://www.drivendata.org/competitions/300/competition-gem-faults/), [Reference Repo](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b)) | Defines `EPSG:32611` `3730x3292` `100 m` grid, `[0, 1]` range, pooled 300 m DTI (`α=0.2, β=0.8`), and CPU support |
| Competition Rasters (`training_features`, `existing_faults`, `sample_submission`) | DOE GTO / USGS INGENIOUS Release (restored via `research/upstream/data_manifest.json`) | SHA-256 `4371c82e...`, `7ba308cc...`, `2176d08e...` (`mismatch_count = 0`) |
| USGS GeoDAWN Airborne Magnetic & Radiometric Survey | USGS Data Release ([doi:10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), CC0 1.0) | `geodawn_rad_u8.tif` (`c22420f7...`) & `geodawn_extensions_u8.tif` (`a35a9c6d...`, `TMI_up150`) |
| USGS 3DEP 1 m LiDAR & Seamless 10 m DEM | USGS National Map ([3DEP](https://www.usgs.gov/3d-elevation-program), public domain) | `lidar_scarp_features_u8.tif` (`d580bb8b...`, verified 12-band headers) & `topo_10m_derived_100m_u8.tif` (`a6398d99...`) |
| DOE GDR #1391 INGENIOUS Great Basin Compilation | DOE Geothermal Data Repository ([GDR #1391](https://gdr.openei.org/submissions/1391), [doi:10.15121/1881483](https://doi.org/10.15121/1881483), CC BY 4.0) | `ing_wells_geotherm_metrics.csv` (`122718e6...`, `dist_known_fault_px` excluded), `Paleo_geothermal_final.csv` (`faffcf69...`), `flt_attr_100m.tif` (`c5edf9df...`) |
| USGS State Geologic Map Compilation (SGMC) | Horton et al. (2017), USGS DS 1052 ([doi:10.3133/ds1052](https://doi.org/10.3133/ds1052)) | `usgs_sgmc_faults_100m.tif` (`643cbe99...`, **read-only post-hoc off-catalogue proxy**, never used in training) |
| Shared Evaluation & Serialization Package | [`60GEMSDOE@b99591ee`](https://github.com/buffedlizard55-lab/60GEMSDOE/tree/b99591eede63c6d45c8a896255b8cd34824fa00b/src/gems57) | `vendor/gems57/` (`23/23` files byte-verified against `research/template_pin.json`) |

---

## 5. Reproducibility & Automated Verification

Large input rasters (`data/`) and `.venv/` are excluded from Git via `.gitignore`. Reproduce the full pipeline and audit without manual intervention:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Restore SHA-256-verified competition + external + 30 sibling champion rasters into gitignored data/
.venv/bin/python scripts/restore_lane_data.py

# 2. Run the full 3-experiment H86-WVB suite, 36-feature canary, dual holdout, 43-raster uniqueness & GeoTIFF export
.venv/bin/python scripts/run_h86_wvb.py

# 3. Run read-only template-pin + GeoTIFF + Run-Card audit and automated test suite
.venv/bin/python scripts/audit.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts vendor tests
```

### Honest Limitations & Selector Handoff Notes
1. **`gems10` Halo Overlap (`0.7853 > 0.70`):** `H86-WVB` cleared `<0.70` 3-px dot overlap against all 30 modern sibling champions (`GEMSDOE32..GEMSDOE88`), `gems24 d2.8` (`0.3488`), and PR #6 (`0.1912`), but `33.1%` of its dots remain inside the near-catalogue tip/stepover envelope densely covered by `gems10-h25-ctx-ridge` (`174,232` px). Do not upload standalone; in a future selector cycle, raising the static-physics weight in $p_{\text{coupled}}^{1-\gamma}\,p_{\text{static}}^{\gamma}$ ($\gamma \in [0.35, 0.50]$) can reduce `gems10` overlap below `0.70`.
2. **Sandbox Egress & Portal Receipts:** DrivenData pages require browser login and `earthquake.usgs.gov` is egress-blocked (`HTTP 000`), so live weekly slot counts, organizer submission receipts, and USGS ComCat microseismic feeds (`H86-SEIS-3D`) cannot be fetched from inside this container.

---

## Protocol Run Card (`docs/evidence/run-card.json`)

```json
{
  "schema": "gemsdoe86-parallel-run-card-v2",
  "generated_at_utc": "2026-10-23T00:16:15.595111+00:00",
  "lane_id": "H86-WVB",
  "hypothesis": "Concealed Great Basin geothermal faults missed by the USGS/INGENIOUS surface catalogue offset magnetic/dense basement at depths matching Cenozoic basin-fill thickness (Salem tilt-angle local wavenumber z_mag ~ depth_to_base_surf with persistent 150 m upward-continued TMI gradients), channel deep silica/cation-equilibrated hydrothermal fluids (T_reservoir - T_outflow disequilibrium and paleo-sinter/travertine vents coupled to MT smectite clay-cap edges), leave subtle relief-normalized scarps across seamless 1 m LiDAR / 10 m 3DEP piedmonts, and propagate along anisotropic crack-tip cones and two-host stepover relays.",
  "mechanism": "24 zero-catalogue physical/geothermometric/scarp channels + 12 strictly fold-visible (`buffer_px=3` = 300 m) anisotropic crack-tip & bitplane two-host relay channels -> Leave-One-Quadrant-Out (LOQO, 2.4 km spatial moat) HistGradientBoosting with Elkan Bayes prior-shift calibration -> preregistered geometric dual-regime posterior (p_coupled^0.85 * p_static^0.15) -> 2.8 px (280 m) 300 m-kernel-matched Poisson-disk allocation with `gems57.emit.surrogate_terms` (37654 binary `{0.0, 1.0}` dots, `d_catalogue > 2 px`, `zeros` outside footprint).",
  "named_non_fault_mimic": "Shallow Miocene-Quaternary basalt lava-flow margins and Pleistocene Lake Lahontan wave-cut shoreline benches (~1,190-1,345 m elevation), suppressed via 150 m upward-continuation attenuation, 3D gravity+magnetic analytic-signal basement concordance, and a low-basin shoreline-contour mimic guard.",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2 (buffered-whole-components-loqo-v2, seeds=(20,21), buffer_px=3)",
    "withheld_positive_pixels": 22893,
    "dti": 0.15792,
    "ci95": [0.13884, 0.17587],
    "coverage": 0.22689,
    "incumbent_d28_dti": 0.10093,
    "incumbent_d28_ci95": [0.08974, 0.11164],
    "delta_vs_d28": 0.057,
    "delta_vs_d28_ci95": [0.03513, 0.07752],
    "incumbent_h33_foldfair_dti": 0.10564,
    "incumbent_h33_foldfair_ci95": [0.09373, 0.11728],
    "delta_vs_h33_foldfair": 0.05228,
    "delta_vs_h33_foldfair_ci95": [0.02978, 0.07336],
    "segment_holdout_22641px_all": { "dti": 0.30237, "ci95": [0.28745, 0.31908], "withheld_positive_pixels": 22641 },
    "segment_holdout_22619px_detached": { "dti": 0.12233, "ci95": [0.10909, 0.13428], "withheld_positive_pixels": 22619 }
  },
  "organizer_confirmed_score": null,
  "leakage_canary": {
    "max_single_feature_discriminative_auc_seed20": 0.87047,
    "max_single_feature_discriminative_auc_seed21": 0.86697,
    "max_feature_name": "v_aniso_strike_reach",
    "shuffled_control_max_discriminative_auc": 0.51399,
    "limit": 0.9,
    "passed": true
  },
  "registry_uniqueness": {
    "reference_rasters_checked": 43,
    "non_lattice_fault_rasters_checked": 42,
    "surface_max_abs_spearman": 0.1271,
    "dots_max_abs_spearman": 0.09489,
    "non_lattice_max_dot_overlap_3px": 0.78531,
    "non_lattice_closest_overlap_reference": "gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif",
    "sibling_champions_30_max_dot_overlap_3px": 0.63531,
    "h33_2_b2_champion_dot_overlap_3px": 0.2928,
    "h33_2_b2_champion_spearman": 0.01513,
    "spearman_limit": 0.9,
    "dot_overlap_limit": 0.7,
    "non_lattice_passed": false
  },
  "raster_sha256": "d0231888c4567816d706cca360c8fe0cd98fc0b673409edb3ffc5649e3d1bdf3",
  "zip_sha256": "b5c38a4a4a8664003b7a4601c926f0093ae791ae292222f7f5d0e8d627d5281e",
  "validator": {
    "ok": true,
    "passed_checks": 15,
    "total_checks": 15,
    "nan_inside_footprint": 0,
    "nan_total": 0,
    "inf_total": 0,
    "min_value": 0.0,
    "max_value": 1.0,
    "values_in_0_1": true,
    "crs": "EPSG:32611",
    "shape": [3730, 3292],
    "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
    "positive_dots": 37654,
    "positive_outside_footprint": 0,
    "positive_on_catalogue": 0
  },
  "submission_name": "gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros",
  "submission_note": "GEMS86 H86-WVB wavenumber+geotherm+scarp+valve submod300 37654d HOLDOUT-DTI=0.1579 [0,1] zeros",
  "submission_note_length": 94,
  "experiments_used": 3,
  "experiment_budget": 3,
  "verdict": "negative"
}
```
