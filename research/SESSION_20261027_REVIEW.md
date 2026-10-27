# GEMSDOE86 repository review — 2026-10-27

## Decision

**DO NOT SUBMIT any file from this repository. No new TIFF, score estimate, or model experiment was produced; no weekly slot was used.** This review corrected the Focus-9 executive table, audited the current checkout, ranked four untested hypotheses, and did not bypass the lane, shared-cache, or duplicate stops.

- Current machine release report: [`docs/evidence/release-readiness.json`](../docs/evidence/release-readiness.json): 46/46 registered TIFF artifacts pass the repository's local format/integrity checks; `safe_to_submit=false`, `approved_for_weekly_slot=false`, `selector_run=false`, and 0 submission slots used. A format pass is not scientific or upload clearance.
- Fresh workspace audit: `.venv/bin/python scripts/audit_workspace_inputs.py --require-native` exits **1** with `NATIVE_INPUTS_MISSING_OR_INVALID`, `NATIVE_PREPARATION_NOT_AVAILABLE`, and `SHARED_FEATURE_CACHE_NOT_ESTABLISHED`. `data/bridge/training_features.tif`, `data/training_features.tif`, `.cache/gems_work/bands/*.npy`, and `.cache/h86_features/static60_fp.f16` are absent in this checkout. The bridge sample and fault rasters are present and hash-verified. This audit did not establish organizer provenance.
- The current request contains no designated single-method paragraph. The repository's shared-cache requirement is also not met. No candidate was constructed, so HOLDOUT-DTI, feature-only canaries, surface correlation, candidate/final-dot overlap, and candidate TIFF validation are **NOT RUN**. Historical witness measurements in the October 26 release audit remain historical evidence, not a new measurement.
- 0.2778 for GEMSDOE32 H33 remains **OWNER-REPORTED**, not organizer-confirmed. It is the highest reported score among the nine requested sites, not a verified current leaderboard record. The prompt's 0.3195 and 0.4413 claims conflict and remain unverified. No new live-score estimate is warranted.

## Focus-9 executive answer and repair

The generated executive summary is [`docs/executive-summary.html#focus9-summary`](../docs/executive-summary.html#focus9-summary). The nine rows now identify each site's highest numeric entry in `registry/prior_scores.csv`, label its score OWNER-REPORTED, show its measured 3-pixel overlap against the common H33 reference from [`docs/evidence/focus9-forensics-20261026-rev2.json`](../docs/evidence/focus9-forensics-20261026-rev2.json), and state whether the literal 70% overlap screen is passed.

| Site | Highest named entry | Score evidence class | Measured 3-px overlap vs H33 | Unique under the stated 70% rule? |
|---|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5` | 0.2477 OWNER-REPORTED | 88.48% | No |
| GEMSDOE25 | `dotted-h19-5-d2-8` | 0.2600 OWNER-REPORTED | 88.17% | No |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5` | 0.2449 OWNER-REPORTED | 86.72% | No |
| GEMSDOE28 | `h36-1-rung30-blind-r1` | 0.2710 OWNER-REPORTED | 95.47% | No |
| GEMSDOE30 | `d28-poisson300m-offcat-44090` | 0.2600 OWNER-REPORTED | 88.17% | No |
| GEMSDOE31 | `h27-4-solo-d28` | 0.2708 OWNER-REPORTED | 95.39% | No |
| GEMSDOE32 | `h33-h33-2-b2` | 0.2778 OWNER-REPORTED | 100.00% (self-reference) | No; already submitted |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30` | 0.2632 OWNER-REPORTED | 92.64% | No |
| GEMSDOE36 | `anderson-geothermal-pinn-38854` | 0.2750 OWNER-REPORTED | 97.40% | No |

**Correction:** the prior executive renderer incorrectly listed GEMSDOE28 H27-4 at 0.2708 rather than GEMSDOE28 H36-1 at 0.2710. The source ledger already contained the higher H36-1 claim and the raster audit already measured its pixels; only the summary's hard-coded row was stale. The builder now picks the per-site maximum from `registry/prior_scores.csv`, joins the keyed raster measurement, fails closed on missing/ambiguous evidence, and labels all score claims. Added `tests/test_focus9_summary.py` pins the corrected winner and all nine uniqueness results. This is a reporting correction, not a new score or a new measurement.

The common-reference overlap is a duplicate-screen measurement, not a proof of exact pixel identity or a complete upstream-registry comparison. All nine rows are over the stated overlap limit against at least one existing raster, so none is a new submission candidate. The Focus-9 comparison is not an instruction to copy or resubmit any historic file.

### Why the H33 0.2778 claim may have occurred

The repository's pixel forensics describe H33 as a collar-pruned D28/H27-4 lineage raster: it retains 37,654 dots and removes 2,545 parent dots in a 1–2-pixel catalogue collar. Under the documented DTI's asymmetric false-positive penalty, removing dots that add little hidden-truth coverage could improve the score. This is a **plausible mechanism, not causal proof**: the historical runs were not randomized matched experiments, and proximity to a known fault does not prove a dot has zero hidden-truth credit. The score itself is owner-reported. The answer to “can a unique submission beat it?” is **not established**; no valid prospective estimate or holdout result in this review supports that claim.

## Ranked untested hypotheses (no numerical score forecasts)

“Expected improvement” here is a qualitative scientific prior for experiment selection only. None of the rows below has a measured HOLDOUT-DTI uplift, and none predicts a leaderboard score. Only one lane may be selected for a future execution; the first item is the least-cost next validation, not a claim of likely success.

| Rank | Hypothesis / specific data layers | Signature and why it could reveal missing faults | Difference from implemented work / named mimic | Expected DTI direction (prior only) | Cost / data status |
|---:|---|---|---|---|---|
| 1 | **Detectability-weighted PU negatives (queued H86R-2_DWPU, still unrun):** native `training_features.tif` Band 15 `depth_to_base_surf`, Band 19 `det_elev_slope`, and the fold-visible fault catalogue used only for training labels. | Estimate mapping/detection completeness from cover and relief. Give low-completeness unlabeled pixels little or no negative weight while retaining well-exposed, catalogue-free terrain as higher-confidence negatives. The mechanism targets faults buried beneath basin fill, where absence from a surface catalogue is weak evidence of absence. | Related cover-propensity features and PU learners exist, so this is **not a claim of wholly new repo theory**. The proposed distinction is an explicit negative-sample-weight intervention versus adding a cover score as an inference feature. Named mimic: a genuinely unfaulted deep playa whose negative evidence is discounted. | Most plausible near-term positive or neutral improvement over the matched unweighted PU control; sign remains uncertain because catalogue-hide labels inherit catalogue detectability bias. | Low–medium after data restore; no extra external source. **Not runnable now:** native TIFF, prepared bands, and verified shared feature cache are absent; no lane paragraph was assigned. |
| 2 | **NURE-HSSR stream/water geochemical residuals:** USGS NURE-HSSR sample coordinates and analytes (verify fields, units, censoring, and spatial coverage before feature construction); existing native Band 17 conductivity and Bands 15/19 can be secondary context, not labels. | Catchment-aware robust residual anomalies and aligned upstream/downstream change points in documented elements (the official sediment dataset identifies As, Cu, Zn, Th, U among mapped analytes). Hydrothermal fluid-rock interaction and leaching may leave a geochemical signal beyond mapped fault traces; sample-to-catchment routing is essential. | No NURE point chemistry is implemented in this repo's candidate feature modules or pinned input inventory. Distinct from airborne radiometrics and GDR-1391 well/spring temperatures. Mimics: mineralized lithologies/mining, sediment sorting, analytical batch effects, and stream-network transport unrelated to geothermal faults. | Potentially positive but highly uncertain; likely sparse and vulnerable to sampling bias. Not an evidence-based score forecast. | Medium–high: official USGS pages offer area downloads and CSV archives, but no download or footprint sample-count query was completed here. It is **not sandbox-validated/viable yet**; first retrieve a bounded Nevada/footprint subset, inspect analyte schema/limits and sample density, hash-pin it, then preregister. |
| 3 | **Drainage-network capture and junction geometry:** USGS 3DEP DEM-derived channel network (10 m if available; otherwise native elevation Band 12 only for a coarser pilot), plus Band 15 basement depth and Band 19 slope as conditioning layers. | Graph-level, multi-catchment channel elbows, capture-like tributary junction changes, and persistent steepness contrasts across range fronts, conditioned on basin structure. These are network/topology signatures rather than pixelwise slope, curvature, χ or ksn peaks; they could register fault-related drainage reorganization where a scarp was eroded. | Repo modules already use DEM/χ/ksn, curvature, and LiDAR scarp response. The candidate is specifically a graph/topology measurement, but still shares a geomorphic family and must be treated as a possible family duplicate. Mimics: lithologic knickpoints, paleolake base-level change, ephemeral channel engineering, and DEM channel-extraction artifacts. | Small/uncertain positive potential; only rank above zero if graph features add information beyond existing χ/ksn controls on the same folds. | Medium. The official USGS 3DEP source is public; the repo's historical external-data manifest describes 3DEP derivatives, but none are present in the current workspace. Restore and hash-check the exact DEM product before calling this viable. |
| 4 | **Seasonal groundwater-head compartment boundary:** USGS Water Data for the Nation well locations and groundwater-level time series (measurement date, head, site construction/aquifer metadata) paired with native Band 17 conductivity and Bands 7/8 geodetic strain only as independent context. | Search for adjacent-well seasonal amplitude/phase discontinuities and persistent head gradients that delineate hydraulic compartments along buried permeable structures. This is a temporal hydrologic boundary signature, not another static spring-point or heatflow raster. | No time-series groundwater-head feature is present in the inspected `src/gems86*` lane modules. Named mimics: pumping/irrigation, aquifer lithology, well completion/screen differences, and sparse irregular observation schedules. | Low/uncertain prior: could be distinctive, but spatial coverage is the main risk. | High. USGS describes public programmatic water-data access, but local AOI well counts and time-series coverage were not queried. Do not implement until that coverage check is performed and pinned data are present. |

**Candidate set exclusions:** ASTER-based hydrothermal alteration and ComCat/focal-mechanism geometry have appeared in earlier repository hypothesis queues/reviews; neither is presented as a new idea here. The existing `registry/h86r_hypotheses_20261026.json` already contains the first item. This audit searched source/research names for the data families and differentiating feature types; that is a code/research-document search, not proof that no external sibling project has ever tried them.

## Validation status and exact blockers

The requested top-candidate validation was **attempted only as a read-only readiness audit and could not proceed**. This checkout lacks the native feature TIFF and `.cache`-prepared bands, while `audit_workspace_inputs.py --require-native` also says the shared cache provenance contract is not established. The parallel-run protocol further requires a designated lane paragraph; none was selected in the current request archive. We therefore did not run a hide-and-recover fold, derive a label-dependent feature, inspect leakage AUCs, build a candidate surface, or emit a raster. A missing experiment is not silently reported as a negative score.

The pinned full-support witness measurement in the October 26 release evidence has `forward_overlap_3px = 1.0` and exceeds the literal `0.70` stop for every nonempty candidate; this is a prior registered measurement, not a new candidate uniqueness check. It remains an unsatisfied protocol stop. Do not evade it by emitting empty/degenerate predictions, changing thresholds, or relabeling format validation as uniqueness approval.

## Three-pass review log

1. **Pass 1 — repository and requirement review:** read `AGENTS.md`, `PROMPT.md`, `README.md`, current review/request archives, release gates, evidence, and Focus-9 scoring/measurement sources. Confirmed no assigned method paragraph, no locally generated TIFF, no use of submission slots, and no organizer receipts. Identified a stale GEMSDOE28 best-row in `focus9_summary()`.
2. **Pass 2 — repair and independent review:** changed `scripts/build_site.py` to take best scores from the CSV and overlaps from the measured Focus-9 evidence; added a regression test for GEMSDOE28 H36-1 = 0.2710 and explicit duplicate labels. Reviewed the joins for duplicate `-nan`/`-zeros` sibling rasters; they are accepted only when repeated overlap values agree. The renderer raises on missing or ambiguous joins. Reviewed the four hypotheses against existing lane modules and explicitly disclosed related/previous ideas.
3. **Pass 3 — final verification:** locked Python dependencies in ignored `.venv`; `scripts/audit_release.py` passes for all 46 artifacts; the evidence-generated site build and read-only freshness check pass; `scripts/check_site.py` and `scripts/audit_downloads.py` pass; focused site tests pass (11 passed, 3 subtests); final full suite passes **1,102 passed, 24 skipped, 48 warnings, 58 subtests**. The initial new regression test had one assertion expecting a raw fraction while the UI intentionally renders a percentage; corrected that test to verify the percentage. No experiment ran.

### Verification and known failure

- `.venv/bin/python scripts/build_site.py` — PASS (generated evidence-based pages).
- `.venv/bin/python scripts/build_site.py --check` — PASS.
- `.venv/bin/python scripts/check_site.py` — PASS; site download/integrity checks do not establish science or upload clearance.
- `.venv/bin/pytest -q tests/test_focus9_summary.py tests/test_site.py tests/test_protocol_site.py` — PASS, 11 passed, 3 subtests.
- `.venv/bin/pytest -q` after the final renderer/site changes — PASS, 1,102 passed, 24 skipped, 48 warnings, 58 subtests.
- `.venv/bin/python scripts/audit_downloads.py` — PASS, all 46 published research TIFFs and their receipts validated; no upload authorization.
- `.venv/bin/python scripts/audit_workspace_inputs.py --require-native` — expected blocker, exit 1; see exact missing inputs above.
- `.venv/bin/python scripts/audit_release.py` — PASS for all 46 registered TIFF artifacts and receipts; release remains DO NOT SUBMIT.
- `.venv/bin/python scripts/audit_release.py --measure-registry` — **not run** in this checkout; the required registry witness bytes are not present. We retain the dated October 26 witness evidence without asserting a fresh remeasurement.

## Limitations and next work

1. **Before merge:** if any source/evidence edits are made after this review, rerun `pytest -q`, `audit_release.py`, `build_site.py --check`, `check_site.py`, and `git diff --check`. The final verification listed above covers the present code and site tree. Do not fabricate local registry remeasurement.
2. **Restore actual inputs:** use the repository-pinned restore process for the native feature raster and any exact external data required. Verify hashes and band indices against `src/gems86/io.py`. Native data preparation still does not replace the shared template cache; obtain the precise template cache/evaluator/writer identity contract.
3. **Resolve experiment authorization:** select one explicit method paragraph and obey the shared 3-experiment / 2-hour budget. Do not fit or place candidates without it.
4. **Resolve the registry contradiction through the shared approved protocol:** the literal dense full-support witness blocks any nonempty raster. No private threshold or evaluator change is acceptable.
5. **Implement one scientific test only after gates permit:** preregister DWPU vs the matched unweighted PU control and a direct visibility-only baseline; compute every single-feature AUC; use whole-component buffered hide/recover folds with catalogue features derived from visible segments only; require pooled DTI paired confidence interval improvement and the pre-placement/final-dot uniqueness checks. If it fails, publish the negative result.
6. **Do not announce a submission candidate or live estimate:** only an organizer page receipt can confirm a live result; no authenticated remaining-quota information is available. `safe_to_submit=false` and `approved_for_weekly_slot=false` remain binding.
7. **Automate a fresh workspace preflight in CI:** today the test suite and static site check pass while the native model inputs are absent. Add an explicit status test or CI artifact that makes this distinction visible, without requiring proprietary DrivenData credentials or downloading from the competition portal.

## Official sources checked for hypothesis/data feasibility

- USGS NURE-HSSR sediment data (official catalog, analyte list, area search/download and archive formats): <https://mrdata.usgs.gov/nure/sediment/>.
- USGS NURE-HSSR water chemistry data: <https://mrdata.usgs.gov/nure/water/>.
- USGS NURE data release/catalog metadata: <https://mrdata.usgs.gov/metadata/nurehssr.html>.
- USGS 3D Elevation Program: <https://www.usgs.gov/3d-elevation-program>.
- USGS Water Data for the Nation: <https://waterdata.usgs.gov/nwis/>; official groundwater overview: <https://waterdata.usgs.gov/nwis/gw>.
- USGS ComCat documentation (prior idea, excluded from new queue): <https://earthquake.usgs.gov/data/comcat/index.php>.
- USGS ASTER hydrothermal alteration release (prior idea, excluded from new queue): <https://www.usgs.gov/data/digital-maps-hydrothermal-alteration-type-key-mineral-groups-and-green-vegetation-western>.
- GEMS official rules PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>.
- Repository source index: [`docs/sources.html`](../docs/sources.html).

Official source documentation confirms that the NURE downloads, 3DEP program, and water-data interfaces exist; **it does not confirm adequate sample coverage in the exact competition footprint**. The current runtime cannot access the USGS hosts under its network allowlist, and this session did not query or download those external files. No external score, coverage statistic, or model result is claimed.

## Machine-readable run card

See [`docs/evidence/session-20261027-run-card.json`](../docs/evidence/session-20261027-run-card.json). It records this as a no-candidate/no-experiment review and a negative operational decision; null HOLDOUT-DTI and raster fields mean not run, not zero.
