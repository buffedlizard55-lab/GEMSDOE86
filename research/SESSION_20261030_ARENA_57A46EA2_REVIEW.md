# Three-pass review — 2026-10-30 UTC

**Branch:** `arena/57a46ea2-gemsdoe86`  
**Disposition:** **DO NOT SUBMIT.** Repository/software review passed; scientific candidate validation did not run and no new TIFF exists. No weekly slot was used.

## Executive decision

There is no defensible submission file to recommend today. The nine historical Focus-9 files are useful as forensic references, not as recommended downloads: prior byte-pinned comparisons show every selected site-best overlaps at least one other of the nine beyond the 0.70 threshold. Those 72 directed comparisons range from 0.8672 to 1.0000; this is a cohort comparison, not a complete fleet clearance. No submission-page receipt was found that binds any supplied score to exact TIFF bytes. Accordingly, the “estimated score” for a new submission is **not estimable**: this review produced no candidate or HOLDOUT-DTI. Do not download a historical TIFF for upload.

The H33 value 0.2778 is a user/owner-reported claim, not an ORGANIZER-CONFIRMED result. Existing byte-level forensics show GEMSDOE32 H33 is pixel-identical to the GEMSDOE28 parent after deleting 2,545 prediction dots in the 1–2 px mapped-catalogue collar. This is evidence of what changed, not evidence that the deleted dots had low false-positive cost, that deletion caused the reported score change, or that the claim is correct. DTI's maximum kernel credit can make redundant nearby predictions costly without adding recall, so more efficient allocation is a plausible mechanism—but it is not causally established for H33. Whether any new submission can beat 0.2778 is **unknown**. The conflicting 0.3195 and 0.4413 leaderboard claims are likewise unresolved and unverified in this repository.

Official competition references for manual review (not queried automatically): [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), and [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). Repository policy prohibits automated access to DrivenData, so this session did not query the leaderboard or submission page.

## Pass 1 — implement/reproduce the existing audit

Read `PROMPT.md`, `README.md`, and `AGENTS.md`; retained the standing parallel-run safeguards. Installed the pinned Python dependencies into ignored `.venv/` from `requirements-lock.txt`. Restored only the small hash-pinned protocol witness via `scripts/restore_protocol_data.py --include-registry`; no training raster or candidate was restored. Re-ran `scripts/protocol_preflight.py` and refreshed `docs/evidence/protocol-preflight.json`.

Measured witness facts: SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`; registry snapshot has 655 indexed entries but only one measured raster; witness grid/validity mask matches; 5,106,385 allowed pixels and 0 uncovered allowed pixels; witness is positive throughout the allowed domain. Under the literal inherited rule this is a **STOP**: any non-empty prediction has 1.0 forward overlap with this single witness, above 0.70. The registry snapshot is incomplete; the measurement is a negative blocker, never uniqueness clearance. The checked-in `require_feasible()` remains unchanged. Do not use an alternate lane or interpretation to bypass this hard stop.

## Pass 2 — review for gaps and edge cases

`python scripts/review_repository.py --timeout 900` completed its seven checks successfully:

- `audit_release.py`: 50/50 published TIFF artifacts were locally remeasured and format-valid; release decision remains **DO NOT SUBMIT**.
- `pytest -q`: **1,206 passed, 24 skipped, 48 warnings, 58 subtests passed** (456.50 seconds).
- Frozen review card, generated site, local links/integrity/safety, and 50 downloads: all passed.
- Live input audit: `training_features.tif` missing at both expected paths; `existing_faults.tif` and `sample_submission.tif` are hash-verified mirrors; 21/21 prepared arrays/masks are missing; the shared `.cache/h86_features/static60_fp.f16` cache is absent and its identity is not established.

The official competition feature raster is login-walled, and no DrivenData auth is available in the repository. A separate concurrent `daf34cc5` review recorded a temporary hash-verified mirror restore, but a read-only input audit after merging concurrent mainline changes again found `training_features.tif` missing at both expected paths. Treat that as a time-scoped workspace discrepancy, not proof that the large raster or cache persisted. A mirrored input or small reference GeoTIFF does not substitute for the missing native raster or shared cached stack. The holdout cannot be rerun honestly with what is currently available.

## Pass 3 — re-check request, evidence classes, and current work decision

The user requested 3–5 hypotheses before implementation. The repository's extant Focus-9 hypothesis file already has three ranked, explicitly unrun proposals. They were re-reviewed, not represented as new discoveries or executed. All remain data-blocked, qualitative, and not authorized as a method lane:

| Rank | Candidate hypothesis and signature | Why potentially uncatalogued | Main mimic / difference from repo | Official free source and current viability |
|---|---|---|---|---|
| 1 | **Age-matched Lake Lahontan shoreline displacement.** Use raw USGS 3DEP elevations plus age/level-attributed shoreline or lacustrine polygons; fit local shoreline benches and detect repeated cross-bench steps/tilt, contextualized by native Bands 12/19 and optionally 15/13. | A subdued blind fault could offset an old, originally near-level bench without leaving a modern scarp. | Wave-cut/facies relief, lake-level miscorrelation, compaction, erosion, volcanic-flow margins. Unlike repository edge/scarp detectors, this uses a mapped dated shoreline as a positive displacement datum; focused novelty is not revalidated in this session. | [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) and [USGS NGMDB](https://ngmdb.usgs.gov/). Exact tiles and attributed shoreline geometry are absent; AOI coverage and product attributes were not checked, and USGS is outside this sandbox's egress allowlist. **Not viable now.** Highest qualitative priority, not an expected numeric DTI lift. High implementation cost. |
| 2 | **Time-ordered earthquake-sequence migration.** Use USGS ComCat origin time, hypocenter, magnitude, and uncertainty to test migration along fitted planes; native Bands 7/8/13/17 are context only. | A blind active fault could produce an ordered sequence before a surface fault is mapped; time order is lost in static event-density layers. | Geothermal operations, quarry/blast events, dike swarms, aftershock migration on mapped faults, and changing detection thresholds. Differs from repository static seismic-density/strain coupling; this is not a claim that seismic clustering is globally novel. | [USGS ComCat FDSN](https://earthquake.usgs.gov/fdsnws/event/1/). No local event time series or query; host outside egress allowlist, completeness/coverage unverified. **Not viable now.** Low-to-moderate, high-uncertainty potential; very high cost. |
| 3 | **Age-tagged stratigraphic-contact offset graph.** Acquire attributed lithostratigraphic polygons and test matched contacts for repeated termination/offset with native Bands 15/2/13/17 as independent context; exclude mapped fault attributes. | Multiple displaced bedrock contacts can indicate concealed fault continuation where the Quaternary-fault catalogue omits the trace. | Primary igneous contacts, depositional boundaries, alluvial margins, map-sheet joins, generalization/georeferencing errors. Differs from available fault-proxy rasters by explicitly matching age/lithology polygon contacts; focused novelty is not revalidated now. | [USGS NGMDB](https://ngmdb.usgs.gov/). No verified AOI product/vector polygons, map scale, or attributes in checkout; direct USGS unavailable here. **Not viable now.** Low-to-moderate potential, high cost. |

No “top candidate” was selected or tested: a lane is not assigned, and the native inputs/cache are missing. The pinned literal witness is also a binding stop under current rules. Thus, running an experiment or writing a TIFF would contradict the protocol. No leakage canary, DTI, 95% CI, or candidate uniqueness statistic is claimed. Surface/final-dot rank-correlation checks are not possible without a candidate. No local format pass is represented as submission approval.

### Run-card facts

- Hypothesis/mechanism/mimic: none executed; no candidate constructed.
- HOLDOUT-DTI: **NOT RUN** (`gems57-pooled-hide-v2`); withheld positives, DTI, and 95% CI: **not applicable / not measured**.
- Correlation/overlap vs registry for a candidate: **NOT RUN**. The one-raster witness blocker measurement is separately recorded above; snapshot completeness is false.
- Candidate TIFF SHA-256 / validator: **none / NOT RUN**.
- Submission name/comment: **none**.
- Experiments: 0 of 3; elapsed scientific experiment budget: 0; weekly slots: 0.
- Verdict: `negative`; `safe_to_submit=false`; `approved_for_weekly_slot=false`.

## Next actions and limitations

1. Preserve the immutable witness measurement and resolve the literal overlap/protocol issue through an authorized, shared-template change—not a private bypass. Any allowed representation-aware interpretation still requires full-registry surface and final-dot checks and must follow the governing protocol.
2. Obtain the actual DrivenData `training_features.tif` through a user-authorized login route and pin its hash/provenance; only then prepare features and establish a cache bound to exact shared template bytes, source arrays, and visible-fault masks.
3. Select one method paragraph/lane and preregister its controls. Run per-feature leakage canaries and the specified buffered hide-and-recover HOLDOUT-DTI against matched controls, with CI. Stop on any AUC >0.90 or uniqueness violation.
4. Only after a holdout win and complete uniqueness/format gates may a separate selector consider the weekly cap. A receipt from the organizer is needed to record a competition score.

## Review artifacts

- [Machine-readable run card](../docs/evidence/session-57a46ea2-run-card.json)
- [Fresh protocol witness measurement](../docs/evidence/protocol-preflight-20261030.json)
- [Current input audit](../docs/evidence/session-57a46ea2-inputs-20261030.json) (tracked receipt; current workspace inspection only)
- Full software-check log: `.cache/repository-review.json` (ignored, local workspace artifact)
- [Nine-site score/uniqueness table](../docs/executive-summary.html#focus9-summary)
- [H33 forensic record](H33_ANALYSIS.md)
- [Standing prompt and parallel protocol](../PROMPT.md)
