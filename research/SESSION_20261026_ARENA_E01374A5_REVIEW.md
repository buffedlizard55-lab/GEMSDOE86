# Repository review — Arena session `e01374a5` (2026-10-26)

## Decision

**No new TIFF was generated, and no file is authorized for competition submission.** This is a fail-closed negative review, not a claim that the user-requested unique submission was delivered. No model experiment was run and no submission slot was used.

## Current state verified in this checkout

- Branch: `arena/e01374a5-gemsdoe86`; starting tree was clean at `c90f6f9`.
- `scripts/audit_workspace_inputs.py`: `INPUT-INTEGRITY-MEASUREMENT`; `training_features.tif` is absent from both expected locations; the 19 prepared arrays, footprint and labels are absent; the recorded shared feature cache is absent and not provenance-established. The bridge `existing_faults.tif` and `sample_submission.tif` are present and hash-verified, but they are not substitutes for native training features or the template cache.
- `scripts/audit_release.py`: audit passes for 45 registered existing artifacts; decision remains **DO NOT SUBMIT**; 0 experiments and 0 slots in this audit.
- `scripts/build_site.py --check`, `scripts/check_site.py`: pass. The site is clearly in research-only / negative authorization state. These checks establish site consistency and download integrity, not model merit or upload approval.
- `.venv/bin/python -m pytest -q`: **1,091 passed, 24 skipped, 58 subtests passed**. 48 Rasterio affine-operator pending-deprecation warnings were emitted.
- Dependency environment was created from `requirements-lock.txt`; ignored `.venv/` does not alter tracked files.

### Focus-9 executive-summary finding

The repository's existing Focus-9 forensic record (`research/SESSION_20261026_H86Q_BFRA_REVIEW.md` and `docs/evidence/focus9-forensics-20261026-rev2.json`) names GEMSDOE32's H33-2-B2 raster as the largest supplied Focus-9 leaderboard claim, **0.2778 OWNER-REPORTED**. This is not an organizer receipt and not HOLDOUT-DTI. The same record reports `HOLDOUT-DTI` under `gems57-pooled-hide-v2` for the H33 visible-collar control as **0.0036 [0.0029, 0.0043]**, with 11,321 withheld positives. These are different evidence types and must not be conflated. The scientific discussion of collar pruning is a plausible post-hoc mechanism, not proof that the pruning caused the leaderboard difference; no causal claim or upload recommendation follows.

The user-supplied `0.3195` and `0.4413` are not confirmed leaderboard values in this checkout. The recorded review identifies the `0.3195` GEMSDOE87 attribution as retracted; see `IRREGULARITIES.md`. No automated DrivenData access was attempted.

## Why no compliant candidate experiment was possible

The current workspace cannot support the requested reuse of the actual shared template feature cache or a data-derived candidate; both the native 19-band input and prepared/cache artifacts are missing. In addition, the current protocol's pinned full-support registry witness is documented as a literal stop for every nonempty candidate under the existing overlap threshold. This session did not restore or reinterpret that witness, alter a threshold, infer a new method lane, construct a private cache, or treat a format check as scientific clearance. The complete earlier investigation and limits are recorded in `research/SESSION_20261026_ARENA_REVIEW.md`'s predecessor reviews and `AGENTS.md`.

## Next actions (ordered; blockers first)

1. Resolve the full-support witness contradiction through an explicit authorized protocol clarification; do not change thresholds or bypass the guard in a private experiment.
2. Re-establish the source-native competition inputs and the actual pinned shared feature cache with complete hashes/provenance, then run `audit_workspace_inputs.py --require-native`.
3. Explicitly assign one method paragraph/lane and preregister it. Before candidate placement, run the registry surface correlation/overlap checks; test each feature alone for leakage; then use buffered whole-segment hide-and-recover with the shared evaluator and paired intervals. Stop on any gate failure, within the three-experiment/two-hour budget.
4. Only if a candidate beats its registered same-design holdout control, passes the full registry uniqueness checks on both surface and final dots, and the common writer's format validation, forward it to the separate slot selector. A local format pass is not upload authorization.
5. Keep organizer scores and remaining weekly quota unset until a permitted human-viewed submission-page receipt is recorded. Never automate DrivenData scraping.

## Sources for manual review

- Competition rules and submission format: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Competition problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- DOE GEMS final report: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- DOE GDR submission #1391: https://gdr.openei.org/submissions/1391
- USGS GeoDAWN data record: https://doi.org/10.5066/P93LGLVQ
- Official USGS 3DEP: https://www.usgs.gov/3d-elevation-program
- DrivenData reference solution: https://github.com/drivendataorg/gems-prize-reference-solution

## Run card

See adjacent `docs/evidence/session-e01374a5-run-card.json`. It records that no candidate was run and no raster exists for this session; null values are intentional, not score estimates.
