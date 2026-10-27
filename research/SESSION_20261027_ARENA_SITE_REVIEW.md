# GEMSDOE86 — three-pass repository and site review (2026-10-27)

## Executive decision

**DO NOT SUBMIT any repository TIFF.** This was a repository/site consistency review, not a new geological experiment. No model was run, no new TIFF was created, and no weekly slot was used. The newest existing experimental artifact is the H86S-DWPU TIFF; its hypothesis was falsified on holdout and it fails the literal registry rule. It is downloadable from the site **for audit only**, not for competition upload.

This report supersedes the earlier same-date snapshot [`SESSION_20261027_REPO_REVIEW.md`](SESSION_20261027_REPO_REVIEW.md) for current artifact counts and site ordering. That earlier report recorded 46 artifacts before the H86S TIFF was included. The present release inventory records **47/47** local TIFF integrity/format passes. The earlier report's statement that its own review generated no candidate remains true; its 46-file count is historical, not current.

## Why GEMSDOE32 H33 led the requested nine-site cohort

The highest value supplied for the Focus-9 set is **0.2778 OWNER-REPORTED** for GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`. It is not an organizer receipt and was not independently confirmed in this review. The repository's pixel forensics report H33 as a 37,654-dot derivative of the D28/H27-4 family that removed 2,545 dots concentrated in the mapped-fault collar. Under the competition's asymmetric distance-weighted Tversky objective (false-positive weight α=0.2, false-negative weight β=0.8, 300 m triangular distance kernel), removing redundant emissions may reduce false-positive mass while retaining far-field coverage. That is a **plausible mechanism, not a causal estimate**: pruning collar predictions could also remove credit for withheld faults near mapped structures, and the single reported score does not isolate the effect experimentally.

### Best reported entry from each requested site

Scores below are transcribed from `registry/prior_scores.csv` and rendered by `scripts/build_site.py`; they are **OWNER-REPORTED**, not ORGANIZER-CONFIRMED. The 3-pixel overlaps are measured in `docs/evidence/focus9-forensics-20261026-rev2.json`, relative to H33. They are a relatedness/duplicate screen, not a proof of exact pixel identity. Every row exceeds the repository's 0.70 overlap stop; these already-submitted entries are not unique new upload choices.

| Site | Best reported TIFF stem | Reported result | 3-px overlap vs H33 | Uniqueness / action |
|---|---|---:|---:|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 OWNER-REPORTED | 88.5% | Fails 70% screen; do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 OWNER-REPORTED | 88.2% | Fails 70% screen; do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 OWNER-REPORTED | 86.7% | Fails 70% screen; do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 OWNER-REPORTED | 95.5% | Site best; fails 70% screen; do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 OWNER-REPORTED | 88.2% | D28-family related; fails 70% screen; do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 OWNER-REPORTED | 95.4% | Cross-site H27-4 lineage; fails 70% screen; do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778 OWNER-REPORTED** | 100.0% | Cohort leader/reference; already submitted, not a new unique upload |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 OWNER-REPORTED | 92.6% | H33-derived family; fails 70% screen; do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 OWNER-REPORTED | 97.4% | H33 superset family; fails 70% screen; do not resubmit |

**Score estimate caution:** no reliable per-site estimate for a new upload follows from this table. The numbers above are historical reported outcomes for already-submitted files, not estimates. H86S's separate `FLEET-REGRESSION-PROJECTION` is 0.130 [0.050, 0.211] with n=20 strictly matched OWNER-REPORTED entries; it is a projection, not a competition score. The quoted 0.3195 and 0.4413 leaderboard values conflict and were not checked against an authenticated submission/leaderboard receipt. No current-leader claim is made.

## Existing candidate: download is not approval

- **Audit-only file:** [`docs/downloads/gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros.tif`](../docs/downloads/gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros.tif)
- **SHA-256:** `123938217b733a959124578a5218c0d513e0842f2bbb4025f023ae2b829c70c9`
- **Submission name / note:** `gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros`; `H86S-DWPU detect-weighted PU 37654d HOLD 0.0870 SGMC 0.0559 ovH33 0.270; audit, selector decides` (96 chars).
- **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, 11,321 withheld positives): 0.0870, 95% CI [0.0707, 0.1037]. The same-split unweighted ablation scored 0.1039; paired difference E1−E2 = −0.0169, 95% CI [−0.0278, −0.0062]. This falsifies the preregistered detectability-weighting mechanism; do not retune it post hoc.
- **Registry:** scoped measurements were below thresholds (H33 overlap 0.2703; worst sampled surface |ρ| 0.1213; worst discrete ≤100k-dot 3-px overlap 0.5213), but these are not a complete accessible registry clearance. The release audit records **literal full-support witness overlap = 1.0**, which exceeds 0.70. Thus the file is **not unique under the literal protocol**, irrespective of its scoped comparison.
- **FORMAT-VALIDATION:** one float32 band, EPSG:32611, 3730×3292, exact sample transform, 0 NaN/Inf, min 0, max 1, 37,654 positive pixels. These checks address the numerical range error class locally; they do not establish DrivenData acceptance.
- **Verdict:** negative; `safe_to_submit=false`; `approved_for_weekly_slot=false`; 0 slots used. Full evidence: [`H86S run card`](../docs/evidence/h86s-dwpu-run-card.json) and [`release-readiness`](../docs/evidence/release-readiness.json).

The static site's executive summary now puts H86S first, explicitly labels H86N/VFGR as historical, and calls out the literal witness failure in the download-decision table. It retains the direct TIFF and one-TIFF ZIP controls as **audit-only**; no “submit this file” recommendation is displayed.

## Three unexecuted research candidates; none is currently testable here

These are ranked by qualitative expected information value and implementation cost, not by a numerical DTI projection. Each has a plausible way to find faults omitted from a surface-mapping catalogue; each also has a stated non-fault mimic. KNDS was already preregistered in older queues but not executed; RANSAC and the daily-GNSS changepoint operator are new at the operator level based on the checked-in implementation search. Current native training data and the shared template feature cache are absent, so **none is viable for the prescribed holdout today**. No slot should be considered before a future run beats a same-split control.

| Priority | Candidate / layers | Targeted physical signature and missing-catalogue rationale | Difference from implemented repo methods | Non-fault mimic | Cost, official source, and current availability |
|---:|---|---|---|---|---|
| 1 | **Catchment-graph iso-χ knickzone back-projection** — official USGS 3DEP elevation/derived χ plus native Bands 12 (det_elev), 15 (depth_to_base_surf), 19 (det_elev_slope) | Find co-linear knickzone responses across adjacent footwall catchments, then back-project the channel break toward the concealed bedrock/alluvium step. A distributed drainage response may persist where a basin-fill cover hides the scarp of a blind fault. | The repo already has pixelwise χ/knickzone features; the untried unit is the catchment graph and cross-catchment, down-channel projection (not another local χ edge plane). Source/code search found no matching graph operator. | Resistant welded tuff or carbonate beds can create aligned knickpoints without a fault. | **Expected DTI:** uncertain, plausible moderate information gain; no score delta claimed. **Cost:** medium-high (DEM conditioning, catchment graph, leakage-safe folds). Official free source: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program). Exact hash-pinned input is not present locally and native/shared caches are missing; **not currently obtainable/validated in this workspace**. |
| 2 | **Geothermal-manifestation RANSAC alignment** — DOE GDR spring/well/vent coordinates from [GDR submission 1391](https://gdr.openei.org/submissions/1391) plus native Band 17 (cond_surf) | Fit robust point-line corridors through independent thermal-fluid manifestations and require conductivity corroboration. This could flag a permeable blind structure without a mapped scarp. | Springs/wells appear in prior repo covariates, but source search found no RANSAC/robust line-alignment primary detector; novelty claim is limited to this checkout. | Road/ranch/well access, range-front hydrology, and exploration siting can make non-tectonic alignments; sample size may be too sparse. | **Expected DTI:** unknown; likely high precision/low recall. **Cost:** low-medium once verified coordinates exist. DOE GDR is the named public source, but its local CSV mirror is absent and GDR is outside this sandbox's network allowlist; **not currently obtainable/validated here**. |
| 3 | **Daily-GNSS transient strain-step / changepoint mapping** — daily station east/north/up positions from the [UNR Nevada Geodetic Laboratory](http://geodesy.unr.edu/), registered against native Bands 7–8 (coarse geodetic shear/dilation) and Band 17 (conductivity) | Estimate detrended station velocity-change epochs and cross-fault transient displacement gradients; a localized transient across a conductive corridor could indicate episodic aseismic slip or geothermal reservoir pressure change not represented by the static mapped-fault inventory. | The repository uses gridded geodetic strain covariates; source search found no raw daily station time-series ingestion, common-mode removal, or temporal changepoint operator. Distinct from the previously queued Sentinel-1 InSAR operators. | Groundwater extraction, seasonal hydrology, monument instability, reference-frame errors and reservoir operations can mimic a tectonic transient. | **Expected DTI:** unknown; likely low/moderate spatial recall given sparse stations. **Cost:** medium-high (time-series quality control, common-mode filtering, event/station coverage and interpolation). Public source needed: UNR Nevada Geodetic Laboratory daily GNSS position products. Host is outside the sandbox's network allowlist; no exact station series were downloaded or hash-verified, so **not currently obtainable/validated here**. |

**Novelty correction logged:** a proposed radiometric provenance-step candidate was excluded from this queue after source review found it already implemented: `src/gems86_bfra/operators.py::regolith_and_metasomatic_unmixing` computes the K/U/Th log-ratio provenance contrast and `src/gems86_bfra/features.py` exposes the feature. This is recorded as `IR-86S-RCSD-ALREADY-IMPLEMENTED-20261027`; do not re-propose RCSD as a new method without a materially distinct preregistered operator.

## Three-pass audit and changes

### Pass 1 — inspect project and evidence

Read the standing prompt and project instructions, current registry/run cards, input audit, release/download audit, generator, source list, and Focus-9 summary. Checked the H86S TIFF/receipt hashes and the release inventory. H86S is the newest experiment in the committed evidence; this review did not rerun it. The full user prompt is retained in `PROMPT.md` and the README archive.

### Pass 2 — adversarial review and repairs

Found that the generated `executive-summary.html` started with the older H86N-GSST entry although the home page and README identify H86S-DWPU as newest. The H86S banner was generated later in the page. Corrected `scripts/build_site.py` so the newest H86S decision appears first on the executive page, and changed old H86N/VFGR labels from “current” to “historical.” Also removed a claim that the H86S file could not produce the prior portal range rejection; now the page only states that the serialized TIFF passes the local [0,1] check, not that the portal must accept it. Clarified that H86S is only scoped-unique and its literal witness overlap is 1.0. Added a regression test for order and stop messaging.

Found the H86S hypothesis register's RCSD novelty claim was incorrect because BFRA already includes the radiometric provenance log-ratio operator. Excluded it from new candidates and logged the correction above. No data, model scores, holdout claims, historical receipts, thresholds, or submission authorizations were changed.

### Pass 3 — recheck full requirements and execution

Current input inspection:

```text
.venv/bin/python scripts/audit_workspace_inputs.py
  completed inspection; native training_features.tif MISSING;
  19 band arrays and footprint/label arrays MISSING;
  shared template cache SHARED_CACHE_NOT_ESTABLISHED;
  safe_to_submit=false; experiments_run=0; slots=0
.venv/bin/python scripts/audit_workspace_inputs.py --require-native
  exit 1 (expected fail-closed result; required native feature raster unavailable)
```

Software/site checks:

```text
.venv/bin/python scripts/build_site.py               PASS
.venv/bin/python scripts/build_site.py --check        PASS
.venv/bin/python scripts/check_site.py               PASS
.venv/bin/python scripts/audit_downloads.py           PASS — 47 TIFFs/receipts revalidated; no submission decision
.venv/bin/python -m pytest -q                         PASS — 1108 passed, 24 skipped, 58 subtests; 48 Rasterio pending-deprecation warnings
 git diff --check                                     PASS (also checked before publishing)
```

Tests validate software behavior and local integrity, not geological truth or organizer acceptance. The 24 skips are not gate passes. The template shared cache and native feature stack are not available, so no experiment or candidate can be reproduced in this checkout. The H86S run's historical holdout result remains clearly labeled as such, not as a new measurement from this review.

## Trusted source links for review

- [DrivenData competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — not queried in this review; owner values are not confirmed
- [Official submission rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE Geothermal Data Repository, GDR 1391](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [NASA ASF Sentinel-1](https://asf.alaska.edu/datasets/daac/aria-sentinel-1-gunw/)
- [EarthScope USMT3D](https://ds.iris.edu/ds/products/emc-usmt3d/)
- Project source index: [`docs/sources.html`](../docs/sources.html)

## Limitations and next session's order of operations

1. Restore the exact training feature TIFF and create/prove the shared template feature cache only through the pinned shared entrypoints; retain source hashes, CRS/grid, band order, visible-label masks, and cache identity. Current mirrors do not establish organizer provenance.
2. Resolve the literal-registry blocker through an explicit authorized protocol change upstream, not a private threshold relaxation. Under the current literal rule, every nonempty TIFF overlaps the full-support witness by 1.0 and must stop.
3. Only after inputs, shared cache, and a satisfiable approved registry rule exist, preregister one untried method from the three candidates above, use the shared evaluator/writer unchanged, run per-feature leakage canaries, and compare buffered whole-segment holdout versus a same-split control with pooled DTI and spatial-block 95% CI. Stop after the registered three experiments or 2 hours.
4. Do not call a holdout DTI a live score. An authenticated organizer submission receipt is required for ORGANIZER-CONFIRMED score labels; this sandbox cannot access the private competition data/portal and does not scrape DrivenData.
5. A separate selector, not this review or the TIFF download link, must check the authenticated weekly quota, exact file SHA, all gates and the one-final-submission rule before any slot use.

## Canonical experiment card

This review made no new experiment. The complete run card for the referenced H86S experiment (including feature canaries, holdout protocol, raster identity, validator output and negative verdict) is [`docs/evidence/h86s-dwpu-run-card.json`](../docs/evidence/h86s-dwpu-run-card.json). The minimal review-status card is [`SESSION_20261027_ARENA_SITE_REVIEW_RUN_CARD.json`](SESSION_20261027_ARENA_SITE_REVIEW_RUN_CARD.json).
