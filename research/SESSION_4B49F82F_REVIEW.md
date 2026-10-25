# Independent repository review — Arena branch 4b49f82f

## Executive decision

**DO NOT SUBMIT. No new TIFF generated in this review.** The existing homepage and executive submission guide correctly distinguish an audit download from an approved competition upload. A local format pass does not establish uniqueness, scientific merit, organizer acceptance, or quota availability.

Read `README.md`, `PROMPT.md`, and the complete request archive before resuming. The current request is already preserved in `research/REQUEST_20261024.md` and linked from the README; avoid adding another enormous duplicate to the README.

## Pass 1 — execution and source verification

- Installed the locked dependencies in an ignored `.venv`, not the system Python. Initial audit attempts lacked NumPy; those attempts did not validate anything.
- Restored hash-pinned grid inputs and the registered full-support witness with `restore_protocol_data.py --include-registry`. These are owner mirrors, **not organizer-authenticated data**.
- Ran `audit_release.py --measure-registry`: all published research TIFFs remain negative. This measures the pinned witness, not the entire fleet and not a new candidate surface.
- Rebuilt the evidence-derived site and checked its links and registered downloads. Automated download audit passed for every published research TIFF. No new format or scientific clearance is claimed.
- Re-fetched the immutable official reference README and H33 artifact audit via `review_sources.py`; both match their archived bytes. See `docs/evidence/review-source-checks.json` for URLs, content hashes and access time.

### Why H33 could improve, and what is actually established

The immutable owner artifact audit describes H33 as deleting parent dots in the two-pixel mapped-fault collar, leaving 37,654 positive cells. That establishes the declared operation and file metadata; it does not establish the cause of a hidden-test improvement. Its own submission note says `UNSCORED` and includes a projection, not a submission-page receipt.

A plausible mechanism is reducing prediction mass that contributes little additional truth coverage. But off-catalogue collar dots can still recover hidden faults, and overlapping triangular kernels use maximum credit rather than additive credit. Thus removing collar dots can also hurt recovery. The nonlinear tradeoff must be tested on identical hidden segments with paired uncertainty; historical fleet score differences are not a causal ablation. Existing synthetic tests in `tests/test_scientific_interpretation.py` guard these statements.

The user-supplied H33 `0.2778` and conflicting leaderboard `0.3195` / `0.4413` remain **OWNER-REPORTED, UNVERIFIED**, not HOLDOUT-DTI or ORGANIZER-CONFIRMED. No available evidence warrants predicting that a new strategy will beat them.

Sources:
- Official baseline software: https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md
- Owner artifact, not official scoring evidence: https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json
- Official competition description, supplied for browser review, not fetched here: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

## Pass 2 — conflicting assumptions and fail-closed boundaries

1. **No single-method lane paragraph is supplied.** Do not silently adopt another session's MMT, SPBT, RIDF or geothermal lane. Existing hypotheses are historical research, not authorization to duplicate a lane.
2. **Literal uniqueness is infeasible for a nonempty raster.** The pinned registered witness has positive support at every allowed cell. Any nonempty allowed dot subset has forward overlap of one. A single witness proves failure; it cannot prove registry completeness.
3. **PA-86-01/02 need authority reconciliation.** Existing code describes these as owner directives, but this request explicitly repeats the literal threshold. Do not assume the general desire for a unique TIFF authorizes changing the representation or stop rule. This review changes neither interpretation nor thresholds, and does not invoke the alternative path to generate a candidate.
4. **Shared cached features are absent.** A mirrored raw feature TIFF is not the template cache. Do not quietly rebuild a private substitute or describe mirror hashes as organizer authentication.
5. **No untried geological hypothesis can be certified across the fleet from this review.** The existing five-hypothesis queue includes already executed or negative ideas. Relabeling it as five new discoveries would be false. No new external-data candidate is presented as viable without successful acquisition.
6. **Readiness is not a leaderboard estimate.** Current local format validity addresses the range error but cannot repair failed scientific and duplication gates. No slot is spent, and no upload is attempted.

## Ranked next-work queue (not new model experiments)

Expected benefit is qualitative evidence quality, not predicted DTI improvement.

| Priority | Action | Cost | Exit condition |
|---|---|---|---|
| First | Reconcile the literal registry rule and recorded amendments; assign exactly one method lane | Low engineering, governance dependency | One authoritative rule with tests, no private bypass |
| Next | Restore the actual shared feature cache with provenance/hash pins | Data-transfer dependent | Cache identity and band semantics verified |
| Next | De-duplicate the hypothesis ledger against executed arms before selecting a genuinely untried mechanism | Moderate | Explicit novelty comparison, named geological confounder, contemporaneous preregistration |
| Next | Run isolated-feature canaries, then buffered whole-segment hide-and-recover and paired baseline comparison | Moderate; within experiment budget | Same split/evaluator, withheld positives, pooled DTI and confidence intervals recorded |
| Last | Surface registry check before placement; final-dot check before shared serialization; format and selector gates | Registry-transfer dependent | Complete bound evidence and separate promotion decision |

The official GeoDAWN release and DOE GDR resources remain relevant source leads, not newly downloaded data in this review:
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
and https://gdr.openei.org/submissions/1391 . Outbound network access in this session is restricted; no fresh verification of those hosts is claimed. No DrivenData credentials are requested or stored. The official baseline documents CPU-only execution, so a GPU is not a universal prerequisite.

## Pass 3 — final verification

Final verification results are recorded below after the full suite finishes. Fresh audit timestamps do not refresh historical model results. The session run card is `docs/evidence/latest-review-run-card.json`: no new raster, no new HOLDOUT-DTI, negative verdict. The unmet unique-and-approved submission requirement remains explicit.

Verification completed: **640 passed, 24 skipped, 41 subtests passed**, with 42 warnings, in the locked virtual environment. Skips are not model validation; warnings include Rasterio affine-transform deprecations. `audit_release.py --measure-registry`, `build_site.py --check`, `check_site.py`, `audit_downloads.py`, and `git diff --check` passed. The download audit covered 15 registered research TIFFs; none was authorized. No shared evaluator/writer bytes, thresholds, or candidate generation code were changed.
