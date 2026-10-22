# GEMSDOE86 — Audited Fault-Prediction Research & Submission Pipeline (`Lane H86B-GFCO`)

## 🔴 FORMAT-VALID CANDIDATE GENERATED (`15/15` CHECKS PASS) — DO NOT SPEND A WEEKLY SLOT AUTOMATICALLY (`verdict: "negative"`, `approved_for_weekly_slot: false`)

- **Primary GeoTIFF Download:** [`docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif`](docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif) (`158,348` bytes · SHA-256 `897ebf7b790efb9b5668934f5929ae766d81d9ec2a4bee3faa7ef2ebaedc1116`)
- **Single-TIF ZIP Download:** [`docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.zip`](docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.zip) (`158,528` bytes · single `.tif` inside)
- **Validator & Writer Receipt:** [`docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.json`](docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.json) · **Authoritative Run Card:** [`docs/evidence/run-card.json`](docs/evidence/run-card.json) · **Full Experiment Evidence:** [`docs/evidence/lane86b_results.json`](docs/evidence/lane86b_results.json)
- **GitHub Pages Readiness Portal:** [`docs/index.html`](docs/index.html) (`https://buffedlizard55-lab.github.io/GEMSDOE86/`) · **Executive Summary & Step-by-Step Submission Guide:** [`docs/executive-summary.html`](docs/executive-summary.html) · **PhD Scientific Review:** [`research/REVIEW.md`](research/REVIEW.md)
- **Unique Submission Name:** `gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b`
- **Submission Note (`92 / 140` chars):** `H86B-GFCO LOQO geotherm-diseq+mag-contact-offset+LiDAR x tip/relay, 44090 dots d>2px, zeros`

### Instant Gate Readout (100% Automated — Zero Human Intervention)

| Gate | Automated Verdict | Exact Verified Measurement |
|---|---|---|
| **1. GeoTIFF / ZIP Format & `[0, 1]` Range** | **PASS (`15/15`)** | Single-band `float32`, exact `[0.0, 1.0]`, `0 NaN`, `0 Inf`, `0` sentinels, `EPSG:32611`, `3730 × 3292` (`100 m`), `0` on-catalogue mass, finite `0.0` outside footprint (`44,090` binary dots). DrivenData portal error *"Predicted values must be in range [0, 1]"* is impossible by construction. |
| **2. Single-Feature Leakage Canary (`Rule 4`)** | **PASS (`42/42 <= 0.90`)** | `38` label-free physical/geothermal/geomorphic planes (`max disc AUC = 0.6486`) + `4` strictly visible-only kinematic components (`max disc AUC = 0.8485 <= 0.90`). AST unit test guarantees `dist_known_fault_px` & `gdr_qfaults_traces.csv` are never read. |
| **3. Spatial Holdout Skill (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`)** | **POINT ESTIMATE BEATS INCUMBENTS ON ALL 3; WHOLE-COMP CI STRADDLES `0`** | **Segment-Hide `all` (`22,641` pos):** `0.1396 [0.1286, 0.1513]` vs `d2.8 = 0.1011` (`Δ = +0.0385 [+0.0269, +0.0524]`, **+38.1%**).<br>**Segment-Hide `detached` (`22,619` pos):** `0.1521 [0.1378, 0.1662]` vs `d2.8 = 0.1035` (`Δ = +0.0486 [+0.0343, +0.0627]`, **+47.0%**).<br>**Whole-Component 3-px Buffered LOQO (`11,321` pos):** `0.1078 [0.0908, 0.1254]` vs `H33-2-B2 = 0.0961` (**+12.1%**) & `d2.8 = 0.0919` (**+17.3%**), paired `Δ vs d2.8 = +0.0159 [-0.0007, +0.0343]`. |
| **4. Registry Uniqueness (`28` Rasters Across `16` Repos, `Rule 1`)** | **UNIQUE vs ALL 25 MODERN CANDIDATES (`<= 0.6342`); LITERAL `> 0.70` ON 3 DENSE LEGACY RASTERS** | Pre-placement surface `|ρ| <= 0.1366`; final dots `|ρ| <= 0.0530`, Jaccard `<= 0.0311`. Overlap vs `GEMSDOE32 H33-2-B2` = **`0.3012`**, vs `d2.8` = **`0.3352`**, max across all `25` comparable rasters (`<= 61k` dots) = **`0.6342`** (`GEMSDOE83`). Literal `> 0.70` fires on 3 dense legacy `GEMSDOE24` rasters (`13gems` 207k-dot lattice `0.9988`; `gems10-h25` 174k-dot `0.7656`; `gems10-h28` 69k-dot `0.7170`) → logged & stopped per Rule 1. |
| **5. Budget & Live Weekly Slot (`Rule 6`)** | **`3 / 3` EXPS USED · `0` SLOTS SPENT** | Stopped cleanly after 3 pre-declared experiments (`16.6 min` CPU). Automatic weekly-slot approval withheld (`approved_for_weekly_slot: false`). |

---

## Session-2 Advances Over Session 1 (PR #6)

Session 1 (PR #6) established the shared-template safety harness (`vendor/gems57`) and tested Rank-1 label-free radiometric residual × RTP persistence (`H86-RMRB`), recording a negative baseline (`HOLDOUT-DTI = 0.0420` pre-mask / `0.0038` full-catalogue-masked vs `0.1011` incumbent) and queueing magnetic contact-offset + radiometric–topographic discordance next. Session 2 executed that roadmap end-to-end:

1. **Restored & SHA-256-verified the complete multi-physics + geothermal + cross-repo registry stack (`scripts/restore_lane_data.py`):** Verified `22/22` non-qfaults competition/GDR-1391/scored files (`research/upstream/data_manifest.json`) plus `15/15` primary champion GeoTIFFs across sibling repositories `GEMSDOE32..GEMSDOE83` (`research/upstream/cross_repo_champions_manifest.json`).
2. **Resolved the Holdout Calibration Paradox:** Demonstrated that withholding **whole 8-connected fault components + 3-px buffer** (`holdout.buffered_component_draw`, `11,321` positives) monotonically reproduces the owner-reported live progression (`H19-5: 0.0654 < d2.8: 0.0919 < H33-2-B2: 0.0961 < H86B-GFCO: 0.1078`), whereas unbuffered 12-px cut-branch holdouts (`d2.8: 0.1011 > H33-2-B2: 0.0910`) reward artificial cut-end proximity at `d = 1–2 px`.
3. **Eliminated Submodular `1.0 px` Clumping & Tile-Seam Redundancy Before Touching Real Data:** Synthetic ridge testing caught `allocate_patient` saturating `k_self = 1.0` (`min_nn = 1.0 px`, `DTI = 0.1636`) and `emit_decimated` creating 1-px tile-seam pairs (`DTI = 0.2361`); ranking by `emit.expected_credit` + seam-free `r = 2.8 px` priority disc thinning achieved `DTI = 0.2822 (+72.5%)` with guaranteed `min_nn >= 2.828 px`.
4. **Built 38 Label-Free Physical/Geothermal/Geomorphic Planes + 3-Experiment LOQO Evaluation (`scripts/h86b_features.py`, `scripts/run_lane86b.py`):** Raised `HOLDOUT-DTI` from PR #6's `0.0038 / 0.0420` to **`0.1396 [0.1286, 0.1513]`** on `segment_all` (`+38.1%` over `d2.8`), **`0.1521 [0.1378, 0.1662]`** on `segment_detached` (`+47.0%` over `d2.8`), and **`0.1078 [0.0908, 0.1254]`** on strict whole-component 3-px buffered LOQO (`+17.3%` over `d2.8`, `+12.1%` over `H33-2-B2`).
5. **Fixed Audit Side-Effect Bug & Expanded Automated Suite (`8 -> 13` tests):** Fixed `scripts/audit.py` so running `unittest` never clobbers `docs/evidence/run-card.json`, fixed `scripts/restore_lane_data.py` to verify all 22 core + 15 cross-repo files, and added AST static leakage tests and published GeoTIFF/ZIP round-trip tests in `tests/test_audit.py`.

---

## Summary of Why `H33-2-B2` Scored Well & Preregistered Hypotheses

Full PhD structural-geology analysis, equations, and literature citations are in [`research/REVIEW.md`](research/REVIEW.md):
- **Why `h33-h33-2-b2-...-zeros` (`37,654` dots) reached its cited benchmark:** Under `DTI` (`α = 0.2, β = 0.8`, `300 m` triangular kernel), thinning `H19-5` (`121,131` px) to `2.83 px` spacing (`d2.8`, `44,090` dots) cuts redundant kernel overlap, and pruning the `6,436` flank dots within `d_cat <= 2 px` removes precision waste on masked known faults. Historical live figures in the prompt (`0.2778`, `0.3195`, `0.4413`) have no organizer receipts in-repo and are treated strictly as unverified owner reports.
- **5 Ranked Untried Hypotheses & Obtainability (`research/REVIEW.md` §3):**
  1. **`H86B-GFCO` (Executed Session 2 — Viable & Verified):** Cover-adaptive GDR-1391 geothermometer disequilibrium (`T_chem - T_meas`) + 3D MT + TMI-vs-150m contact-offset + 1 m LiDAR scarplet chains + Huber topo-deconfounded `K`/`U/Th` × visible fracture-tip/relay mechanics.
  2. **`H86C-TDPL` (Viable Locally):** Multi-scale (`5/9/17 px`) steerable Radon 1 m LiDAR scarplet collinearity tensor with contour-parallel pluvial-shoreline rejection.
  3. **`H86D-PFCO` (Viable Locally — Top Candidate for Session 3):** Explicit bipartite graph matching of truncated conjugate RTP magnetic phase-symmetry ridges across transverse CBA gravity steps.
  4. **`H86E-MTDA` (Viable Locally, Coarse Station Resolution):** Lateral migration vector of `|∇log σ(z)|` across 6 MT depths (`500 m → 10 km`) projected updip (`50°–65°`) to `z = 0`.
  5. **`H86F-RLSL` (Blocked in Sandbox — Flagged Non-Viable Here):** 3D RANSAC planar hypocenter fits on relocated USGS ComCat / UNR NSL microseismicity (`https://earthquake.usgs.gov/fdsnws/event/1/version` verified TLS-blocked in this sandbox on `2026-10-22`).

---

## Exact Reproduction Commands (CPU-Only, `< 1.8 GB` RAM)

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Restore & SHA-256-verify all 22 core GDR/competition files + 15 cross-repo champion rasters
.venv/bin/python scripts/restore_lane_data.py

# 2. Build all 38 label-free physical, geothermal, and geomorphic planes (~98s)
.venv/bin/python scripts/h86b_features.py

# 3. Run 42 leakage canaries, 4-quadrant LOQO ensemble, 3 experiments (E1-E3), 28-raster uniqueness, & GeoTIFF writer
.venv/bin/python scripts/run_lane86b.py

# 4. Run fail-closed independent repository audit & 13-test automated verification suite
.venv/bin/python scripts/audit.py
.venv/bin/python -m unittest discover -s tests -v
```

---

## Official Verified Links & Provenance Scope Limitations

- **DrivenData Competition 306 — Problem Description, Metric & Format:** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- **DrivenData Official Public Leaderboard:** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- **DrivenData Official Reference Solution:** <https://github.com/drivendataorg/gems-prize-reference-solution> (`research/upstream/official-reference-README.md`)
- **DOE GDR Submission 1391 — INGENIOUS Great Basin Dataset (`DOI: 10.15121/1887495`, CC BY 4.0):** <https://gdr.openei.org/submissions/1391>
- **USGS GeoDAWN Airborne Magnetic, Radiometric & LiDAR Compilation (`DOI: 10.5066/P93LGLVQ`, CC0 1.0):** <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
- **USGS State Geologic Map Compilation (`SGMC`, DS 1052, `DOI: 10.3133/ds1052`):** <https://pubs.usgs.gov/ds/1052/> · **EPSG:32611:** <https://epsg.io/32611>
- **Stated Scope Limitations:** Local data files are SHA-256-verified against `research/upstream/data_manifest.json` and `research/upstream/cross_repo_champions_manifest.json` (`28` rasters across `16` repositories), not downloaded directly through a live DrivenData login session; un-fetched sibling repos are a stated scope boundary, never claimed as cleared; predicting concealed fault likelihood does not prove active geothermal fluid production.

---

## Starting Brief — Read at the Beginning of Every Session

The operational starting brief preserved from Session 1 (read alongside [`research/REVIEW.md`](research/REVIEW.md) at the start of every session):

- Review previous work first; maximize probability of winning through evidence, and own the outcome end to end. Do not trade scientific integrity for an optimistic claim.
- Generate a UNIQUE competition-format single-band GeoTIFF, never copy an earlier submission except for education. Make download and readiness status obvious at the beginning of the site. Supply a distinct name and note of at most 140 characters.
- Work autonomously through implementation, bug/edge-case review and final requirements review (`3` passes). Research official free data, preserve provenance and links, flag irregularities, distinguish verified facts from hypotheses. Explain access limits and next steps honestly.
- Parallel-run lane is the single assigned method paragraph (**none was present in the supplied request — irregularity logged**). Surface and final-dot checks must stop on rank correlation `> 0.90` or `> 70%` dots within `3 px` of any registered raster.
- Reuse cached features, `evaluate_holdout.py` and `submission_writer.py`; do not privately fork shared tools (`vendor/gems57` pinned in `research/template_pin.json`). Hide complete fault segments with buffers. Derive catalogue features from visible faults only and mask visible faults pixel-exactly. Pool distance-tolerant Tversky components: `alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel.
- Test each feature alone; holdout `AUC > 0.90` means suspected leakage until disproven. Generate/rank 3–5 untested geological hypotheses with named layers, signatures, missing-fault mechanism, mimics, novelty and cost before experiments. Confirm external data availability before treating an external-data idea as viable.
- Benchmark against the best comparable spatial holdout before touching a weekly slot. Stop after 3 experiments or 2 hours. Selection/promotion into a real slot is separate and must respect the authenticated weekly cap.
- Report scores ONLY as `HOLDOUT-DTI` (version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (actual submission receipt).
- End with one JSON run card: hypothesis, mechanism, named non-fault mimic, holdout result + CI, registry comparisons, SHA-256, serialized raster validation, submission name, short note (`<= 140` chars), `promote` / `negative`. Negative results are deliverables.
- Build a clean GitHub Pages site (`docs/index.html`) with an executive summary (`docs/executive-summary.html`) explaining exactly how to submit. Reject NaN/Inf/sentinels and values outside `[0, 1]`, and match the template's CRS/shape/transform. Open and merge a PR onto `main`, then list remaining limitations.
