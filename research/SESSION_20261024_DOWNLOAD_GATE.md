# Download authorization review — 2026-10-24

## Outcome

**DO NOT SUBMIT. No new unique TIFF was generated. This requested deliverable remains unmet.**
No model experiment or competition submission occurred. Existing downloads remain audit-only. The complete request is already archived in `research/REQUEST_20261024.md`, embedded in the README, and represented by the standing `PROMPT.md`; this review read both the README and standing prompt before editing.

## Three passes actually performed

1. **Implementation:** inspected the standing protocol, registry witness, prior H33 analysis, provisional hypothesis table, release audit, and independent download validator. Restored SHA-pinned mirrored grid inputs and the registry witness using `restore_protocol_data.py --include-registry`. Fixed `validate_download.py`: an optimistic `promote`, `submission_ready`, or `approved_for_weekly_slot` flag now requires a complete, explicitly unique, non-stopped registry scan. Previously `stop_required=false` alone could bypass its readiness consistency check. This is a necessary check, not sufficient authorization or a replacement for holdout evaluation.
2. **Adversarial review:** added regression coverage crossing all three promotion fields with incomplete, duplicate, and null-completeness registry reports. All must fail even when `stop_required=false`. Rechecked the inherited artifact and ZIP bytes without altering either. Full suite: **445 passed, 24 skipped, 4 warnings**, plus **41 subtests passed**. Skipped tests are not evidence of successful model training; raw feature/cache-dependent paths were not exercised. The four warnings concern rasterio/Affine pending deprecation.
3. **End-to-end recheck:** `audit_release.py --measure-registry`, `build_site.py`, `build_site.py --check`, `check_site.py`, `validate_download.py`, `audit_downloads.py`, and `build_ledger.py --check` all exited successfully. All ten inherited TIFFs passed local format/integrity checks; all remain negative against the literal registry rule. Current measurement receipts and generated site were refreshed. No new feature-alone canary, candidate surface, final dots, or HOLDOUT-DTI was produced.

## Why the generation request cannot be completed under the supplied rule

The pinned historical continuous prediction is positive on every allowed footprint cell. Therefore every nonempty allowed dot set has forward overlap equal to one against that registry raster, which exceeds the allowed overlap. This is a mathematical obstruction, not a failure that changing geological hypotheses or TIFF compression can fix. The complete registry need not be measured to establish this negative counterexample; it would be required for positive clearance. Do not privately exempt dense rasters or edit thresholds.

Reproducible evidence: [current run card](../docs/evidence/latest-review-run-card.json), [actual final-artifact registry measurements](../docs/evidence/all-artifacts-registry.json), [release report](../docs/evidence/release-readiness.json), and [immutable witness pin](registry_witness_pin.json). Measurements are geometry/format diagnostics, not scores.

## H33 answer and candidate research

The [earlier detailed H33 review](SESSION_20261024_REVIEW.md) documents its pixel-exact collar-pruning relation to the older dotted raster. Sparse emission can reduce redundant false-positive mass under the asymmetric distance-weighted metric; collar pruning can reduce wasted support near already mapped faults. Neither mechanism establishes new geothermal vents or guarantees leaderboard improvement. The quoted leaderboard values are owner claims without organizer submission-page receipts, not verified scores. No new live leaderboard or external official-source verification was performed in this review.

The [four ranked provisional hypotheses](../registry/h86c_hypotheses.json) remain plans, not experimental results: signed basement/gravity flank polarity; magnetic marker translation; MT-conductance/geodetic coupling; and watershed-crossing LiDAR micro-scarp curvature persistence. The first two use existing competition bands; external-data proposals remain unavailable for execution until their official raw bytes are obtainable and pinned. Novelty is scoped to the reviewed checkout, not asserted across inaccessible parallel work. Do not repeatedly invent new lanes while the mandatory stop remains active.

Official starting points for manual source review (links, not a claim of fresh verification):
- [Organizer reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [GEMS report](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DOE GDR 1391](https://gdr.openei.org/submissions/1391)

## Remaining actions and limitations

An explicit protocol amendment distinguishing continuous surfaces from sparse dots is required before model construction may resume. A single method lane is also absent from the supplied request. Next obtain the actual shared cached feature stack and establish a comparable buffered whole-segment holdout baseline; then run feature-alone canaries and paired spatial confidence intervals before the separate selector considers a slot. Official authenticated data identity, current leaderboard, organizer receipts, weekly quota, and submission acceptance remain unverified. GitHub mirrors prove pinned-byte identity only. No human inspection is substituted for automated checks, and format validation is never represented as scientific readiness.
