# GEMSDOE86 repository review — 2026-10-27

> **Historical point-in-time snapshot; superseded for current artifact count and page ordering by [the current review](SESSION_20261027_ARENA_SITE_REVIEW.md).** This review counted 46 inherited TIFFs before H86S-DWPU was included. Its statement that *this review itself* produced no experiment/TIFF remains true; the current release inventory is 47/47 local format-valid artifacts, all still DO NOT SUBMIT.

## Decision

**DO NOT SUBMIT. This review produced no new model experiment, candidate surface, TIFF, or submission-slot use.** The checkout's machine release decision is negative. This is a scoped repository/software review, not a competition score report.

- Current workspace inspection (`scripts/audit_workspace_inputs.py`): `training_features.tif` is absent; prepared band arrays and the required shared-template cache are absent. `existing_faults.tif` and `sample_submission.tif` are present as hash-verified bridge mirrors. Hashes establish identity with their pinned mirror bytes, not organizer provenance.
- Read-only release audit (`scripts/audit_release.py`): **46/46 inherited TIFF artifacts pass local format/integrity checks**, while `decision=DO NOT SUBMIT`, `safe_to_submit=false`, `approved_for_weekly_slot=false`, no selector run, and zero slots used. A format pass is not scientific or upload approval.
- Current source of truth for the Focus-9 investigation is the prior forensic table in [`SESSION_20261026_H86R_SFG_REVIEW.md`](SESSION_20261026_H86R_SFG_REVIEW.md). Its historical scores are explicitly `OWNER-REPORTED`, not `ORGANIZER-CONFIRMED`. The conflicting leaderboard values in the prompt were not independently checked.

## Pass 1 — project state and evidence review

Read `AGENTS.md`, `PROMPT.md`, `README.md`, the current status/evidence, the shared `gems57` evaluator/writer/uniqueness code, the H86R queue and run card, the Focus-9 review, the input auditor, the site source, and the release/download audit entrypoints.

The repository already contains the user's standing request in `README.md`/`PROMPT.md`, a static site with a conspicuous submission-status page, an executive submission procedure, machine-readable artifact receipts, and a per-site Focus-9 analysis. The per-site table identifies GEMSDOE32 H33 at 0.2778 as the highest *reported historical submission* among the nine named sites. That number is not a model estimate or an organizer receipt.

The repository's bounded H33 forensics describe its relation to the D28/H27 lineage: 2,545 dots were removed, concentrated in the mapped-fault collar; the retained raster has 37,654 dots. Removing predictions that may add little incremental credit while reducing false-positive mass is a plausible DTI mechanism. It is not causal proof of the score change: hidden faults can occur near mapped faults, and the score's distance-kernel credit can change nonlinearly. The owner-reported 0.2778 remains unverified by a submission-page receipt. See the pixel-measurement and interpretation evidence linked from the prior Focus-9 report.

No new non-GitHub source was fetched. Repository policy prohibits automated DrivenData access; current outbound access is also restricted. Official source URLs for manual review are retained in [`docs/sources.html`](../docs/sources.html), including the DrivenData problem/rules, reference solution, USGS GeoDAWN, DOE GDR/INGENIOUS, and the EPSG grid reference. No statement here represents a current leaderboard check.

## Pass 2 — adversarial review and ranked research queue

The latest pre-registered H86R lane already used its three-arm budget and returned a **negative** verdict. Its tested strike-field-gated edge-fusion candidate scored below its ungated control on the same catalogue-hide holdout and failed its registered auxiliary-proxy gate. Do not tune or relabel that lane. The repository records three follow-up mechanisms that were queued but not executed; the source-level differences below are based on the current tracked source and registry, not a claim of novelty across other repositories.

Ranking is qualitative **information value versus cost**, not a projected leaderboard score. Exact DTI gains cannot responsibly be estimated without a runnable, pre-registered, same-split holdout. All three are currently blocked by missing native inputs/shared cache, and no weekly slot is authorized.

| Rank | Unexecuted hypothesis and layers | Physical signature and why it might reveal a missing fault | Difference from checked-in methods | Named non-fault mimic | External-data need / cost / status |
|---:|---|---|---|---|---|
| 1 | **Detectability-weighted positive-unlabelled learning (H86R-2_DWPU):** native Bands 2, 3, 5, 11, 13, 15, 18, 19; Band 6 radiometric total count; GeoDAWN K/Th/U | Use basement depth (B15) and terrain slope (B19) to estimate where a fault would be observable; down-weight pseudo-negatives in deeply covered terrain. This targets buried structures omitted because they are hard to map, rather than teaching the learner that undocumented terrain is fault-free. | The existing KSAD lane used detectability/completeness as a prediction/fusion prior; the queued mechanism uses it to weight negative training examples. Do not treat this as a validated improvement. | Unfaulted playa/playette basins could be over-promoted when pseudo-negative evidence is discounted. | No new product proposed; GeoDAWN has an official USGS release link in the source catalog. **High implementation cost** (spatially blocked, fold-safe HGB); native feature raster and verified shared cache absent, so not runnable here. |
| 2 | **Transient-fluvial iso-χ knickzone back-projection (H86R-3_KNDS):** USGS 3DEP elevation-derived χ plus native Bands 12, 15, 19 | Detect aligned knickzones across neighboring footwall catchments, then project their inferred break down-channel toward the bedrock/alluvium boundary. In principle, catchment-scale drainage response may preserve evidence of a buried range-front fault after a surface scarp is muted. | The queued operator is a catchment-graph back-projection; repo search/registry distinguish it from pixelwise terrain/χ covariates and local fault-tip or scarp features. | Resistant welded-tuff or carbonate ledges can create aligned lithologic knickpoints without faulting. | Requires an exact, hash-pinned public DEM/product and reproducible χ derivation. The queued `dem10_chi` input is not in the checked-in upstream manifest; no data were retrieved in this review. **Medium-high cost; not currently obtainable as a validated input.** Official source lead: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program). |
| 3 | **Geothermal manifestation point-alignment corridors (H86R-4_VENT_RANSAC):** DOE GDR spring/well/vent coordinates and native Band 17 surface conductivity | Test whether several independent thermal-fluid manifestations form a persistent linear corridor, with conductivity as corroboration. A blind permeable fault may lack a mapped scarp while controlling aligned upflow. | Explicit robust point-line alignment is different from using vent/spring distance as a pixel covariate. The repository queue says no such primary geometric operator was implemented; this claim is scoped to this checkout. | Wells, springs, roads, ranch access and range-front water availability can create human/siting alignments; isolated vents also have low recall. | Candidate CSVs are referenced in the manifest from [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391), but their bytes were not present/verified in this workspace. **Low-medium implementation cost; not runnable until hashes and coordinates are verified.** |

No candidate was implemented or run. These are existing registered follow-ups, not newly discovered or globally unique ideas. Historical expected-gain fields in prior preregistrations are hypotheses only and are deliberately not restated as score estimates here.

## Pass 3 — execution, defect checks and final verification

The first audit attempt used system Python and failed because NumPy/Pytest were not installed; it established nothing. Created an ignored virtual environment and installed exact versions from `requirements-lock.txt`, then reran checks successfully.

```text
scripts/audit_workspace_inputs.py   completed; training_features missing, prep/cache unavailable; safe_to_submit=false
scripts/audit_release.py            audit_ok=true; 46/46 local artifacts valid; DO NOT SUBMIT; 0 slots
scripts/audit.py                    all recorded audit predicates true (integrity/audit scope only)
scripts/build_site.py --check       PASS
scripts/check_site.py               PASS
scripts/audit_downloads.py          PASS; 46 research TIFFs/receipts revalidated; still DO NOT SUBMIT
git diff --check                    PASS
pytest -q                           1101 passed, 24 skipped, 58 subtests passed; 48 third-party warnings
```

The 48 warnings are Rasterio pending deprecations involving Affine multiplication in test fixtures. The tests establish software/regression properties, not scientific merit. Skipped tests are not gate passes. No holdout, candidate surface, registry comparison of a new candidate, TIFF validation, or organizer receipt was produced by this review.

## Findings and next steps

1. **Current blocker:** restore the exact native training feature input and the required shared-template feature stack with source/hash/band provenance; do not substitute ad-hoc arrays or a private cache. The input audit currently says these are missing.
2. **Method authorization:** the user protocol refers to a single method paragraph, but this review is not assigned a fresh lane. Choose one of the queued mechanisms only in a subsequent authorized lane, after source-level novelty and budget are reconfirmed.
3. **Holdout first:** reuse the shared evaluator/writer and execute feature-alone leakage canaries, buffered whole-segment hide-and-recover, pooled DTI with withheld-positive count and spatial-block 95% CI, against a same-split control. Do not compare across holdout designs and do not translate holdout DTI into a live-score projection.
4. **Registry protocol:** preserve surface checks before placement and final-dot checks before serialization. The tracked release decision is fail-closed; a partial scan or local format check does not clear uniqueness. Resolve the documented full-support witness/rule conflict through authorized project governance, not a private threshold change.
5. **Separate selection:** a scientific promotion does not spend or authorize a DrivenData slot. Obtain the current quota/selector decision and record a submission-page receipt before claiming an organizer score.
6. **Focus-9 table:** retain the existing per-site historical table and its `OWNER-REPORTED` labels; do not call those nine already-submitted rasters unique new submissions. 0.2778 is the top provided/reported Focus-9 value, not a defensible projection for a future submission.

## Run card

See [`SESSION_20261027_REPO_REVIEW_RUN_CARD.json`](SESSION_20261027_REPO_REVIEW_RUN_CARD.json) for the machine-readable negative result. No model experiment or submission TIFF was generated in this review.
