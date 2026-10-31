# Three-pass repository review — 2026-10-30

**Branch:** `arena/9b7ca9b8-gemsdoe86`
**Decision:** **DO NOT SUBMIT.** No new TIFF was generated, no candidate holdout was run, and no weekly slot was used.
**Machine card:** [`docs/evidence/session-9b7ca9b8-run-card.json`](../docs/evidence/session-9b7ca9b8-run-card.json)

## Executive decision and answer about GEMSDOE32 H33

The highest score claim among the nine requested sites remains **GEMSDOE32 H33, 0.2778 OWNER-REPORTED / UNVERIFIED**. The current audited score-source record says no submission-page receipt binds this number to the exact TIFF bytes. It is not an organizer-confirmed result, a new-file score estimate, or proof that this is the all-competition maximum. A new candidate's score is **not estimable** from the evidence available.

The repository's pixel-forensic account offers a plausible, limited explanation: H33 appears to be a 37,654-dot subset of a 40,199-dot H27-4 raster after removal of 2,545 dots in the `1 < d_cat <= 2 px` collar. Under the competition's distance-tolerant asymmetric DTI (as transcribed in this repository: alpha 0.2, beta 0.8, 300 m triangular kernel), removing redundant near-catalogue predictions could reduce false-positive penalty while retaining much of the spatial coverage. The competing mechanism is equally credible: those same dots could recover withheld fault segments, so pruning could reduce true-positive credit. The reported H33–H27-4 difference is descriptive, based on unverified owner/user claims, not a controlled causal estimate. The separate D32 repository rescore in the pinned source audit is HOLDOUT-DTI from a different evaluator and must not be compared to either owner claim or treated as an organizer-score prediction.

**Conclusion:** H33 may have done well because of its spatial arrangement and its collar-pruning precision/recall tradeoff under a tolerant metric. The available evidence cannot establish that causal story, and cannot support a claim that a new submission will exceed 0.2778 (or conflicting prompt leaderboard claims of 0.3195/0.4413). No DrivenData page, leaderboard, submission receipt, login-protected resource, or quota was accessed.

## Requested nine-site executive table

The full current historical per-site table is in [`docs/executive-summary.html#focus9-summary`](../docs/executive-summary.html#focus9-summary) and `README.md`. All values in the score-claim column are owner/user supplied, not organizer-confirmed. Historical TIFFs remain forensic-only; local formatting does not make them unique or approved. As of this review, no new TIFF is safe to download as a submission; **there is no submission file to upload**.

| Site | Highest supplied historical claim in the repository | Evidence / present recommendation |
|---|---:|---|
| GEMSDOE24 | 0.2477 | Owner-reported/unverified; historical file audit-only |
| GEMSDOE25 | 0.2600 | Owner-reported/unverified; historical file audit-only |
| GEMSDOE27 | 0.2449 | Owner-reported/unverified; historical file audit-only |
| GEMSDOE28 | 0.2710 | User-reported/unverified; historical file audit-only |
| GEMSDOE30 | 0.2600 | Owner-reported/unverified; historical file audit-only |
| GEMSDOE31 | 0.2708 | User-reported/unverified; historical file audit-only |
| GEMSDOE32 | **0.2778** | Highest supplied Focus-9 claim, owner-reported/unverified; no score-to-bytes receipt; forensic-only |
| GEMSDOE33 | 0.2632 | Cross-repository owner-reported/unverified; historical file audit-only |
| GEMSDOE36 | 0.2750 | Owner-reported/unverified; historical file audit-only |

These are **not score estimates**. For a candidate that does not exist and has not passed a protocol-compliant holdout, an estimate is not defensible. “Unique” is also not a blanket status: earlier nine-file pairwise results show every one of the 72 directed comparisons exceeds the 0.70 dot-overlap rule (0.8672–1.0000), and that cohort-only result is not a full-registry clearance.

## Current checks (evidence class is explicit)

- **INPUT-INTEGRITY-MEASUREMENT:** fresh audit [`session-9b7ca9b8-inputs-20261030.json`](../docs/evidence/session-9b7ca9b8-inputs-20261030.json) found `training_features.tif` missing at both expected paths, all 21/21 prepared arrays/masks missing, and the shared template cache not established. `sample_submission.tif` and `existing_faults.tif` are hash-pinned owner-mirrored bytes, not authenticated directly by the organizer.
- **REGISTRY-MEASUREMENT:** restored the pinned historical support witness from its immutable Git blob and re-ran `scripts/protocol_preflight.py`. Witness SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be` has positive support on all 5,106,385 allowed pixels. The unchanged literal rule therefore implies forward overlap 1.0 for every nonempty candidate, exceeding 0.70. Preflight status: `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. This is a negative feasibility result, **not** a uniqueness pass; its snapshot has 655 indexed entries and only one measured raster.
- **SOFTWARE/INTEGRITY AUDIT:** `scripts/audit_release.py --measure-registry` passed 50/50 inherited published artifacts and retained **DO NOT SUBMIT**. A format/integrity audit is not a scientific holdout, not a full-registry uniqueness pass, and not upload authorization.
- **REPOSITORY-METADATA:** refreshed the explicit 92-repository GitHub feed on 2026-10-30; 92/92 snapshots succeeded. Comparing against the prior committed feed found 9 added TIFF paths across GEMSDOE32 and GEMSDOE33. These are Git metadata observations, not scores: their TIFF bytes were not fetched/validated by the feed, no score receipt was found in metadata, and score status remains unknown. In GEMSDOE32 these newly added tree entries include files already known from other cohort repositories; that is not new performance evidence. See [`focus9-feed-delta-20261030.json`](../docs/evidence/focus9-feed-delta-20261030.json) and the refreshed [`fleet-feed-current.json`](../docs/evidence/fleet-feed-current.json).
- **HOLDOUT-DTI:** none run this session. Evaluator version, withheld positive count, estimate, and CI: **not available**. No feature-alone canaries were run.

## Ranked untried hypotheses (repository-screened; no execution authorized)

These are the three concepts already screened in [`registry/focus9_novel_hypotheses_20261028.json`](../registry/focus9_novel_hypotheses_20261028.json), not newly invented in this session. “Expected DTI improvement” below is qualitative prior judgment only, not a numeric estimate. All depend on external inputs absent from this checkout and therefore are **not presently viable for holdout validation**.

| Rank | Layers and targeted signature | Why potentially uncatalogued / difference from implemented work | Main non-fault mimic | Cost and required official source |
|---:|---|---|---|---|
| 1 | Raw USGS 3DEP 1 m DEM plus age/level-tagged Lake Lahontan shoreline geometry; Native Bands 12/19 for context. Detect repeated, strike-coherent step/tilt across a single age-matched shoreline bench. | A buried fault may displace a paleogeodetic surface with little modern scarp. Existing repo operators mainly detect scarps, channel anomalies, edges, or suppress shoreline morphology; no exact age-matched shoreline positive-datum displacement test was located in the screened code/registry. | Wave-cut/facies relief, age or lake-level mismatch, differential compaction, terrace risers, volcanic-flow margins. | **High.** Official free source candidates: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) and [USGS NGMDB](https://ngmdb.usgs.gov/). AOI tile coverage, exact dated shoreline geometry, scale, and current byte retrieval were not independently verified; current sandbox cannot reach those hosts. No numerical gain claimed. |
| 2 | USGS ComCat origin times, hypocenters, depth, magnitude and uncertainty, with native Bands 7/8/13/17 as independent context. Detect quality-controlled time-ordered migration along fitted blind planes. | A blind active fault may host a migrating sequence unlike static native event-density fields; a time-direction operator was not found in the screened implementation. A spatial hypocenter-plane proposal exists in earlier work, so this is specifically temporal migration, not generic clustering. | Geothermal injection/production swarms, mining/quarry blasts, volcanic swarms, aftershock migration on known faults, time-varying catalog completeness/location uncertainty. | **Very high.** [USGS ComCat FDSN](https://earthquake.usgs.gov/fdsnws/event/1/) is the named official source; this sandbox cannot query it, and local coverage/completeness is unknown. |
| 3 | Attributed lithostratigraphic unit polygons from USGS NGMDB or a specifically pinned state survey map, plus native Bands 2/13/15/17 as independent context. Build a graph matching multiple age/lithology-compatible contacts and test repeated offsets/terminations. | Contact displacement could reveal concealed structures, but mere contacts are not faults. This differs from existing potential-field edges and fault-proxy layers because it matches age-tagged polygon contacts; fault-line attributes would be excluded. | Intrusive/volcanic contacts, facies and alluvial boundaries, map joins/generalization, age correlation and georeferencing error. | **High.** [USGS NGMDB](https://ngmdb.usgs.gov/) or a named state geological survey product; no precise product, polygon schema, scale, license, AOI coverage, or bytes are verified. |

**Ranking caveat:** order reflects qualitative potential and information value relative to cost, not a guaranteed ranking in DTI. Since none can be validated with currently available source bytes, none should be implemented or considered a slot candidate yet. The user-supplied “highest leaderboard score” numbers conflict and are not verified; there is no calibrated scoring model that turns these hypotheses into organizer-score estimates.

## Three-pass review log

1. **Pass 1 — inspect and verify:** read `PROMPT.md`, `README.md`, `AGENTS.md`, the current Focus-9 audit, score-source audit, input audit, hypothesis register, and prior feed. Installed repository-pinned dependencies in ignored `.venv`; performed fresh workspace input audit; refreshed GitHub metadata; restored the pinned witness; ran release remeasurement; added this session record and JSON card. No feature builder or candidate writer was run.
2. **Pass 2 — challenge assumptions and edge cases:** distinguished owner claims, repository-specific holdout results, format audits, metadata observations, and organizer receipts. Confirmed a witness support saturation blocks every nonempty candidate under the exact literal rule, even though the registry is incomplete; did **not** turn the diagnostic into a candidate pass or modify thresholds. Compared prior and current Git trees by immutable path metadata. New paths do not establish score, raster bytes, submission, or uniqueness.
3. **Pass 3 — requirements/reproducibility:** verified no lane assignment, no eligible feature stack, no holdout, no score estimate, no candidate TIFF, no validator pass, and no slot use. Checked that all requested per-site claims remain labeled unverified and that the summary gives no upload authorization. Final software test and generated-site checks are recorded after execution below.

## Limitations, irregularities, and next work

1. **Protocol blocker:** the literal full-support witness makes the stated uniqueness gate unsatisfiable for any nonempty prediction. Do not bypass or reinterpret it locally. It needs a documented owner-level protocol resolution; without one, no candidate can be unique under that rule.
2. **Inputs:** current native feature raster and prepared masks are absent. Restore the hash-pinned source mirror if permitted, then establish the actual shared cached feature stack and visible-fault feature provenance. A mirror hash proves byte consistency with the recorded owner mirror, not organizer authenticity.
3. **Lane/holdout:** no single lane is assigned. After input restoration and protocol resolution, preregister one method and reuse the shared `evaluate_holdout.py`/`submission_writer.py` equivalent. Withhold whole fault segments with buffers; recompute all catalogue-derived features from visible faults only; mask visible faults pixel-exactly; use pooled DTI alpha 0.2/beta 0.8/300 m triangular kernel; report evaluator version, withheld positives and 95% CI. Run each feature alone as a canary first; AUC >0.90 is a leakage stop. Do not exceed three experiments/two hours.
4. **Registry:** current witness scan is a sufficient negative counterexample, not comprehensive uniqueness. A full registry scan is required for a future candidate after the literal blocker has a formally resolved representation. Surface correlation and dot-overlap checks must be performed before placement and again after final dots.
5. **Submission:** organizer receipts and weekly-slot/quota state are unavailable to automated access; no portal action is authorized. A selector decision is distinct from science and format checks. No existing file in this checkout is authorized for upload.
6. **New source paths:** metadata-only entries in the newly refreshed feed (especially candidate paths) are not recommendations to download or submit. GEMSDOE30's duplicate-stop owner disposition remains a reason not to use its specified path.

Official competition/source references for manual review (not newly fetched this session): [DrivenData problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN DOI](https://doi.org/10.5066/P93LGLVQ), [GDR submission 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [submission guidance PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [EPSG:32611](https://epsg.io/32611). No external scientific source claims beyond repo-registered statements were asserted as freshly verified.

## Verification commands and outcome

- `.venv/bin/python scripts/audit_workspace_inputs.py` — PASS, current input audit saved; training raster and all prepared arrays remain missing.
- `.venv/bin/python scripts/refresh_fleet.py --workers 4` — PASS, 92/92 current GitHub metadata snapshots; output versioned as `fleet-feed-current.json`, preserving the prior 10/29 snapshot.
- `.venv/bin/python scripts/restore_protocol_data.py --include-registry` — PASS, verified pinned witness and template mirror hashes; owner-mirrored files are not organizer-authenticated.
- `.venv/bin/python scripts/protocol_preflight.py` — measurement complete; `STOP_LITERAL_OVERLAP_UNSATISFIABLE`, no candidate.
- `.venv/bin/python scripts/audit_release.py --measure-registry` — PASS integrity on 50/50 inherited artifacts; decision remains DO NOT SUBMIT.
- `.venv/bin/python scripts/build_site.py` and `--check` — PASS after versioned current-feed rendering; no generated HTML numbers edited manually.
- `.venv/bin/python scripts/check_site.py` — PASS links, download integrity and negative-state safety; explicitly not scientific clearance.
- `.venv/bin/python -m pytest -q -p no:cacheprovider` — final post-rebase PASS on updated mainline `f14f584`: **1,209 passed, 24 skipped, 48 warnings, 58 subtests passed**. Warnings are Rasterio `Affine` multiplication pending deprecation; no failures.
- `.venv/bin/python scripts/build_site.py --check`, `scripts/check_site.py`, and `git diff --check` — PASS after the final evidence refresh.
- The historical 2026-10-29 feed and preflight/release evidence bytes are preserved as dated snapshots; the current feed is separately versioned as `fleet-feed-current.json` so a refresh does not invalidate a prior session's hash receipt.
