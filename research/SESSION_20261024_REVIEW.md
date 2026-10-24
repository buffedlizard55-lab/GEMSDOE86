# Session review — 2026-10-24 UTC

## Decision at a glance

**No new submission TIFF was generated. No artifact in this repository is authorized for upload.** This is a negative result, not a claim that an experiment or candidate passed. The literal parallel-run overlap rule is unsatisfiable for every nonempty candidate under the pinned witness; bypassing it, copying a prior TIFF, or emitting an empty file merely to evade the rule would not satisfy the scientific task.

The evidence below is local, reproducible project evidence and public GitHub metadata. It is not an organizer receipt. The public competition/leaderboard pages and authenticated account state were not queried in this session; no current competition score or quota is asserted.

## Three-pass review

### Pass 1 — repository and prior-results review

- Read `PROMPT.md`, `README.md`, `AGENTS.md`, the current request archive, the H33 forensic analysis, the H86C candidate register, and the existing negative run card before taking action.
- The H33 answer and three prospective hypotheses already exist in `README.md`, `research/H86_RESULTS.md`, and `registry/h86c_hypotheses.json`. The proposed hypotheses are planning only: cross-fault magnetic-marker translation (RTP/TMI), signed paired-throw consistency (basement depth/gravity/elevation), and watershed-crossing scarp persistence (official native-resolution DEM). They are not newly claimed discoveries or validated candidates.
- The explanation for the H33 site's comparatively high owner-reported result is plausible metric engineering, not proof of a geological discovery: a spaced lineament surface can avoid redundant false-positive mass, while pruning close to mapped faults can spend less prediction mass on already-known traces; zero-valued outside cells also avoid out-of-range predictions. These operations can improve distance-weighted Tversky utility if retained predictions cover new truth, but pruning can remove useful coverage. The actual private competition truth is unavailable here, so the result's causal explanation and any expected improvement remain unverified.
- The number shown by the H33 site is an **OWNER-REPORTED claim**, not ORGANIZER-CONFIRMED evidence in this checkout. The H33 upstream audit marks the file `UNSCORED` in its captured state; that does not prove a later owner-reported score false. See `research/upstream/h33-best-audit.json` and `research/H86_RESULTS.md`.

### Pass 2 — fresh pinned-input and artifact checks

- Restored the integrity-pinned `existing_faults.tif`, `sample_submission.tif`, and one historical registry witness from public GitHub using `scripts/restore_protocol_data.py --include-registry`. These are owner mirrors, **not organizer-authenticated data**. SHA-256 and byte-length checks passed; generated raster data remains ignored and is not a new output.
- Ran `scripts/protocol_preflight.py`. **REGISTRY-MEASUREMENT:** one hash-pinned historical witness has positive support at every allowed pixel (5,106,385 allowed pixels; zero uncovered). Consequently every nonempty candidate subset has forward overlap 1.0 against this witness, above the literal 0.70 limit. This proves a gate conflict for this witness; it is not a uniqueness clearance, since the registry snapshot is incomplete.
- Ran `scripts/audit_release.py --measure-registry`. The audit rechecked all 10 inherited TIFFs; all pass local file-format checks, but the release decision remains **DO NOT SUBMIT**. These historical artifacts are not new submissions.
- Refreshed the GitHub project metadata feed: all 88 of 88 named repositories were snapshotted successfully. This feed is current main-branch Git metadata, not a complete historical-raster registry, current leaderboard, organizer score, or remaining submission quota.

### Pass 3 — independent consistency and release review

- Ran `scripts/audit_downloads.py`, `scripts/check_site.py`, and `scripts/build_site.py --check`; all passed after regenerating the site from the refreshed feed and freshly measured evidence.
- The separate SHA-256 pin for the shared template metric/writer/validator is enforced by the release audit. The actual shared cached feature stack is absent. No private replacement stack was created.
- No method paragraph was assigned in the supplied parallel-run prompt. The H86C magnetic-marker idea is therefore still provisional, and no placement, holdout fitting, leakage canary, or final-dot check was performed.
- **HOLDOUT-DTI:** not run; evaluator `gems57-pooled-hide-v2`; withheld-positive count and 95% CI are unavailable. The mandatory pre-placement stop precedes the experiment; no holdout number is imputed from historical runs.
- No new TIFF exists, so candidate rank-correlation, final-dot overlap, raster SHA-256 and candidate format-validator fields are all not measured. Do not treat the witness overlap as a measurement of a nonexistent candidate.
- No weekly slot was used. No selector was run and no portal upload was attempted.

## Research decision and next steps

The requested next candidates are already recorded, ranked qualitatively, with feature layers, physical signatures, non-fault mimics, repository novelty comparisons and data-readiness limits in `registry/h86c_hypotheses.json`. Their expected gains are not numeric projections. The top magnetic-marker candidate cannot be responsibly validated until the protocol has an authorized lane, an explicit resolution of the literal uniqueness contradiction, the actual shared cache, and a complete-enough registry for the requested screen. The watershed/DEM idea additionally requires official native DEM bytes and coverage; metadata alone does not establish obtainability. Do not spend a submission slot on any of these ideas before matched spatial-block validation and separate selector approval.

To make progress, the project owner or governing protocol must resolve the contradiction in the overlap rule explicitly. This implementation does not weaken the thresholds, exempt a dense raster, or silently change the support definition. After an authorized protocol revision: authenticate the shared cache and registry; preregister one lane; freeze visible-only buffered whole-segment holdouts and controls; run each feature's leakage canary; then use the pinned shared evaluator and writer. Only a positive, paired spatial-block result against a rerunnable matched control can justify a later selector review.

## Evidence and source scope

- Current machine card: [`docs/evidence/session-20261024-run-card.json`](../docs/evidence/session-20261024-run-card.json).
- Fresh artifact/file checks: [`docs/evidence/release-readiness.json`](../docs/evidence/release-readiness.json).
- Fresh witness and inherited-dot measurement: [`docs/evidence/all-artifacts-registry.json`](../docs/evidence/all-artifacts-registry.json).
- Refreshed repository metadata only: [`docs/evidence/fleet-feed.json`](../docs/evidence/fleet-feed.json).
- Hypothesis register: [`registry/h86c_hypotheses.json`](../registry/h86c_hypotheses.json).
- Manual review: [official DrivenData problem/format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN metadata](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), and [USGS magnetic-offset report](https://pubs.usgs.gov/pp/1658/pdf/ch5.pdf). These links are provided for inspection; the external non-GitHub hosts were not accessed in this session.

## Limitations / irregularities

1. The supplied prompt names a “single method paragraph,” but no separate lane paragraph was present. No lane was guessed or run.
2. A pinned historical raster creates a universal forward-overlap blocker under the literal rule. The accessible registry is incomplete. The valid conclusion is “cannot clear,” not “the candidate duplicates a complete registry.”
3. Competition source rasters are owner-mirrored, hash-pinned files; they are not authenticated from DrivenData in this session. Official competition data download requires account access not available to this process.
4. H33 and other site score figures are owner/site claims unless a submission-page receipt is captured. No receipt is present for the H33 result in this checkout.
5. The refreshed project feed covers the named owner repositories' current Git trees, not all projects, historical rasters, organizer submissions, scores, or quota.
6. No published TIFF is safe to submit. “Format valid” means local byte/format checks only; it is not competition acceptance or scientific promotion.
