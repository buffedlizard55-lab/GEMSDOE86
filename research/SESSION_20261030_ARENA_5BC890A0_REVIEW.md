# Three-pass repository review — 2026-10-30 UTC

**Branch:** `arena/5bc890a0-gemsdoe86`
**Decision:** **DO NOT SUBMIT. No new TIFF was generated.**
**Why:** No single geological method paragraph was assigned for this lane; the current registry witness still blocks every nonempty candidate under the unchanged literal overlap rule; and the native training raster, prepared arrays, and verified shared feature cache are absent.

This is a repository/workspace review, not a model experiment. It does not choose a candidate for a weekly slot, infer an organizer score, or authorize downloading a historical TIFF for submission. The latest machine-readable audit is [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json); its measurement date is bound to the fresh registry witness remeasurement. Current local input bytes are separately recorded in [`docs/evidence/session-5bc890a0-inputs-20261030.json`](../docs/evidence/session-5bc890a0-inputs-20261030.json). The witness receipt is [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json).

## Executive decision and Focus-9 results

The repository already has a Focus-9 executive summary and a commit-pinned table for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36 in [`README.md`](../README.md#executive-table--requested-sites-historical-files-for-forensic-audit-only) and [`docs/executive-summary.html#focus9-summary`](../docs/executive-summary.html#focus9-summary). Its status labels are correct for the evidence present: **historical files are audit-only; none is cleared to submit**. The nine historical files pass local file/grid/range checks, but all 72 directed three-pixel overlap comparisons within this nine-file cohort exceed 0.70 (reported range 0.8672–1.0000). This is a within-cohort duplicate warning, not complete-registry uniqueness clearance.

| Site | Highest supplied historical claim | Evidence class | New-candidate organizer-score estimate | Distinct among these nine? | Submit? |
|---|---:|---|---|---|---|
| GEMSDOE24 | 0.2477 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE25 | 0.2600 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE27 | 0.2449 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE28 | 0.2710 | USER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE30 | 0.2600 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE31 | 0.2708 | USER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE32 | 0.2778 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE33 | 0.2632 | CROSS-REPOSITORY OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |
| GEMSDOE36 | 0.2750 | OWNER-REPORTED / UNVERIFIED | Not estimable | No — cohort overlap gate failed | **No** |

All decimals in this table are **owner/user score claims**, not ORGANIZER-CONFIRMED scores. No submission-page receipt binds any of them to the exact TIFF bytes. No calibrated relationship between holdout performance and organizer score was established, so “not estimable” is deliberate, not a zero-valued forecast. The detailed filenames, immutable source revisions, local hashes, pairwise overlap values, and caveats remain in the linked executive table and evidence records.

### What can and cannot be said about GEMSDOE32 H33

The supplied **0.2778 OWNER-REPORTED / UNVERIFIED** value is the largest claim in this nine-site table; it is not shown to be the all-fleet maximum and is not organizer-confirmed. The current score-source audit reports zero organizer receipts linking a score to exact bytes. The conflicting user-supplied 0.3195 and 0.4413 leaderboard figures have not been independently checked and are not used as targets.

A pixel-forensics comparison in [`research/H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md) finds H33 differs from its H27-4 parent partly by removing 2,545 prediction dots in a one-to-two-pixel catalogue collar; outside-footprint encodings also differ. A plausible mechanism is a precision/false-positive tradeoff under the asymmetric DTI weighting, but removing collar dots can also lose credit for hidden faults because only catalogue pixels are masked exactly—not their entire surrounding metric kernel. Thus the pixel difference suggests a hypothesis about the reported ordering; it does **not** establish why the organizer score differed or that the collar change caused the result. The score itself lacks a receipt, so the scientific explanation must remain qualified.

The distinct owner-repository result is **HOLDOUT-DTI** under `GEMSDOE32-HIDE-RECOVER-v3.0`: 0.004515 [0.003816, 0.005262], 22,232 withheld positives. It is not this session's experiment, uses a different evaluator/scale, is not comparable numerically with 0.2778, and is neither a competition score nor an estimate for a new file. The session's own pooled holdout was not run.

## Three ranked, repository-screened hypotheses (none run)

The register [`registry/focus9_novel_hypotheses_20261028.json`](../registry/focus9_novel_hypotheses_20261028.json) contains three repository-screened, **PROPOSED_NOT_RUN** ideas. Ranks express only qualitative prior plausibility and engineering cost; numeric DTI gains are unknown. The repository novelty search is scoped to local source/scripts/research/hypothesis registers, not a claim of global novelty.

| Rank | Candidate / inputs and physical target | Why it may reveal an uncatalogued fault; difference from existing repo work | Non-fault mimic | Cost / source readiness |
|---|---|---|---|---|
| 1 | **Lahontan paleoshoreline offsets:** raw USGS 3DEP 1 m DEM, age/level-tagged USGS NGMDB shoreline geometry, native Band 12 `det_elev` and Band 19 `det_elev_slope` for context. Detect repeated cross-bench steps/tilt along the same mapped shoreline level. | Treat a dated former lake-level surface as a positive displacement datum, unlike the repo's scarp/knickpoint edge detectors that treat shoreline morphology as a confound. A subdued blind fault could offset a former near-level bench without a fresh modern scarp. | Wave-cut bench variability, shoreline-age mismatch, compaction, terraces, volcanic margins. | High. Official catalogues identified, but exact AOI tiles, dated shoreline features, availability, and raw bytes are unverified and absent; **not viable in this checkout**. Sources: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [USGS NGMDB](https://ngmdb.usgs.gov/). |
| 2 | **Time-ordered ComCat sequence migration:** USGS ComCat event origin time, hypocenter, magnitude, event type, and uncertainty; native Bands 7/8 only as independent context. Detect repeated migration along a fitted buried plane rather than static event density. | A blind active strand may appear as a migrating sequence before a mapped surface expression; existing repo event-count features are static and no time-migration operator was found in the scoped local search. | Geothermal injection/production, mining/blasts, volcanic swarms, aftershocks on mapped faults, network detection changes. | Very high. Official endpoint identified, but no local time series and no AOI query; host is outside sandbox egress. **Not viable in this checkout.** Source: [USGS ComCat FDSN](https://earthquake.usgs.gov/fdsnws/event/1/). |
| 3 | **Age-tagged stratigraphic-contact displacement graph:** attributed unit polygons from an exact USGS/state map plus native Band 15 depth-to-basement, Band 2 RTP, Band 13 gravity, and Band 17 conductivity. Detect several age/lithology-matched contacts that terminate or step coherently across one corridor. | Tests correspondence and displacement of mapped unit boundaries, not the presence of mapped fault lines or generic potential-field edges; several concordant contacts could bridge a gap in a surface fault catalogue. | Intrusive/volcanic contacts, depositional boundaries, alluvial cover edges, map joins, age/georeferencing error. | High. No exact product, map scale, polygon layer, AOI coverage, or bytes verified; fault-only derivative is not a substitute. [USGS NGMDB](https://ngmdb.usgs.gov/). **Not viable in this checkout.** |

**No top candidate can be validated on holdout here.** The required native `training_features.tif` is absent from both expected paths; all 21 native prepared arrays/masks are missing; and `.cache/h86_features/static60_fp.f16` is absent and lacks a verified shared-template cache identity. The no-login public feature mirror is not a substitute for the cached feature stack, and the competition data page is login-walled. No isolated-feature canary, holdout, or experiment is reported. No weekly slot was touched.

## Current hard stops and irregularities

1. **Literal registry rule is unsatisfiable for any nonempty allowed prediction.** The refreshed hash-pinned witness [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json) covers 5,106,385 / 5,106,385 allowed pixels; direct support leaves zero allowed pixels uncovered. Under the unchanged support rule (finite prediction > 0) every nonempty candidate therefore has implied forward overlap 1.0, exceeding 0.70. This is a negative stop, not uniqueness clearance; only one of the 655 indexed raster records was measured. Thresholds were not changed and no bypass was used.
2. **Native data/cache missing.** [`docs/evidence/session-5bc890a0-inputs-20261030.json`](../docs/evidence/session-5bc890a0-inputs-20261030.json) records current local input status. Integrity-pinned owner mirrors for the fault and sample rasters exist, but their provenance explicitly does not authenticate organizer origin.
3. **Feed is not a score receipt.** The 2026-10-29 upstream GitHub refresh found nine new TIFF paths on five Focus-9 sites by metadata only. Their raster content, scores, format, and uniqueness were not verified; score status is unknown, not zero. A GEMSDOE30 path was explicitly marked by its owner as no-holdout/duplicate-stop/not for download. Do not use new paths as submission candidates.
4. **No current candidate.** There is no new TIFF name/hash, no raster validator result for a new file, no candidate rank-correlation or final-dot overlap measurement, and no submission-score estimate. Historical valid TIFFs are research/audit artifacts only.
5. **Highest leaderboard values remain conflicting owner/user claims.** Automated access to DrivenData is prohibited by repository instructions. Obtain any future ORGANIZER-CONFIRMED value only from a human-provided submission-page receipt; this review did not access that site.

## Three-pass verification record

### Pass 1 — inspect and verify

Read the standing [`PROMPT.md`](../PROMPT.md), [`README.md`](../README.md), [`AGENTS.md`](../AGENTS.md), the Focus-9 source reconciliation, H33 interpretation, prior hypothesis register, and current review card. Confirmed the package already exposes the historical nine-site executive table, explains how to submit, and fails closed against submission. Refreshed the integrity-pinned protocol witness from its immutable GitHub blob and independently reran the measurement. No candidate or experiment was created.

### Pass 2 — test for gaps and contradictions

Re-ran current workspace input audit: missing training raster, 21 prepared arrays/masks, and shared cache. Ran the full registry-witness preflight and release audit. Confirmed all 50 inherited published research TIFFs pass local format/integrity checks, while their local validity does not confer scientific or upload authorization. Found that the old independent `GEMSDOE32-HIDE-RECOVER-v3.0` score is a different evaluator and must not be compared with the reported leaderboard claim. No thresholds, evaluator, writer, or weekly selector were altered or bypassed.

### Pass 3 — final checks

Full test suite: **1,203 passed, 24 skipped, 58 subtests passed**, with 48 rasterio pending-deprecation warnings. After the fresh witness measurement and generated-page rebuild, final `scripts/build_site.py --check`, `scripts/check_site.py`, `scripts/audit_release.py`, and `git diff --check` all passed. The separate `scripts/audit_release.py --measure-registry` run also passed: 50/50 inherited artifacts remain locally valid and decision remains DO NOT SUBMIT. The `--require-native` audit correctly exited nonzero because required native data is missing. This is an expected fail-closed data-readiness result, not a test-suite failure.

## Next work that can unblock a real experiment

1. The project owner must explicitly resolve the contradiction between the literal dense-witness overlap rule and the requirement for a nonempty, unique prediction. Do not change thresholds or invent a dense-surface exemption in a candidate lane.
2. Restore the exact native competition feature raster/data under the allowed data process, prepare the pinned arrays, and establish the real shared-template cache with an identity receipt. Do not label the mirrored feature TIFF as that cache.
3. Assign one method paragraph and preregister a single lane. Then run isolated-feature leakage canaries and the specified buffered whole-segment hide-and-recover evaluator using only visible faults, exact masking, pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel), and 95% CI.
4. Only if the top candidate beats the comparable current holdout best, complete full-registry surface checks before placement and final-dot checks before serialization; use the shared writer, validate the final TIFF, and stop at three experiments or two hours. Selection for a real submission slot is a separate step requiring the live weekly cap and organizer receipt.

Official references for manual review (not accessed through DrivenData this session): [competition overview and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), and DOE/NLR [competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). The competition pages were not queried automatically.
