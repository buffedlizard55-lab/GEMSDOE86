# Repository review — 2026-10-25 — session 63051e73

## Decision and scope

**DO NOT SUBMIT. No new TIFF, no new geological experiment, no weekly slot.** The requested unique, submission-cleared raster is not delivered. Generating arbitrary pixels or copying an inherited raster would not satisfy the protocol. No single method paragraph is assigned in this request, and the required shared cache is absent.

## Pass 1 — reproduce and repair

Read AGENTS.md, PROMPT.md and the entire README before changes. Reproduced the inherited H86L-FMC publication defect: the TIFF and ZIP existed but were not registered. Added the existing byte hash to the inventory and joined its original negative scientific card. The release auditor now explicitly recognizes its schema and preserves its full-catalogue ancestry leakage warning. It rejects promotion, authorization, changed evaluator, erased leakage warning and invalid numerical evidence through the existing fail-closed normalization checks. No archived scientific card, evaluator, writer, threshold or TIFF was edited.

Installed the declared Python dependencies in an ignored virtual environment. Restored the immutable historical witness with `scripts/restore_protocol_data.py --include-registry` and reran `scripts/audit_release.py --measure-registry`. All 32 published TIFFs pass local format/integrity; all fail the unchanged literal forward-overlap rule against that witness. This is a sufficient rejection, **not a complete-registry uniqueness scan**. The restored witness is an owner historical prediction, not official training data.

## Pass 2 — scientific and code review

The H86L input fleet used the full catalogue, so its archived HOLDOUT-DTI cannot demonstrate hide-and-recover discovery. The repaired page says this explicitly; its numeric result remains archived, not recomputed. Added regression tests for evidence extraction and rejection of authorization drift/erased warnings. Rebuilt the HTML from its source rather than retaining the manually inserted “NEWEST UNIQUE TIFF” banner, which conflicted with the duplicate finding. The `#h86l-fmc` anchor remains available.

Live input report: `session-63051e73-inputs.json`. Native training features, prepared arrays and a verified shared cache are unavailable. The existing downloader can restore mirrored native data, but that alone cannot establish the required shared-cache provenance. Restoring a large raw TIFF solely to claim training readiness would be misleading.

## H33: why a gain is plausible, not established causation

The earlier pixel audit (`SESSION_0C60B079_REVIEW.md`, not rerun here) found H33 is its parent minus 2,545 in-footprint dots, with zero added, plus an outside-footprint NaN-to-zero encoding change. The vendored DTI penalizes false-positive mass with alpha 0.2 and missed truth with beta 0.8, using a 300 m triangular tolerance kernel. Pruning dots that earn little truth credit can therefore improve DTI, but pruning can also remove useful coverage. This explains a mechanism, not the observed live score or causation. The owner-reported 0.2778 is **not ORGANIZER-CONFIRMED**. The two incompatible current-leader claims in the request are likewise unverified. No credible estimate that a candidate will exceed them can be derived from these anecdotes, especially across incompatible holdouts.

## Ranked hypotheses before implementation

Reuse the exact three-item queue in `registry/followup_hypotheses_20261025.json`; no experiment is authorized here. “Untried” means no exact executed method identified in that queue's checkout review, not global novelty. Priority reflects expected scientific information per cost, **not projected DTI**.

| Priority / cost | Native layers | Signature and concealed-fault rationale | Difference from implemented approaches | Named mimic |
|---|---|---|---|---|
| 1 / high | iso_grav_anom (13), depth_to_base_surf (15) | Fold-fitted forward basement gravity residual, then persistent narrow residual gradients; seeks buried displacement under basin fill | Explicit physical forward-response subtraction rather than SPBT paired steps or PSC saddle/ridge topology | Sediment-density changes and basement inversion error |
| 2 / medium | iso_grav_anom (13), slope (5), directional derivatives (11,18) | Extended-step versus compact-source response competition; seeks long buried density discontinuities | Explicit competing source-shape likelihood rather than derivative/tensor magnitude | Elongated intrusive contacts |
| 3 / medium | cond_surf (17), geod_dilaterate (8), geod_shearrate (7) | Threshold-persistent conductivity necks conditioned on strain; possible concealed permeability pathways | Connectivity topology, not raw conductivity halos; CNT remains a reserve proposal | Saline paleochannels and interpolation bottlenecks |

All use native bands, so no new external dataset is needed by design; none is currently executable under the required shared-cache contract. Band 15 is gravity-derived and is **not independent corroboration**. Bands 11 and 18 are signed directional derivatives in this repository, not conventional vertical derivatives. Conductance is not depth-resolved MT. These are explicit hypotheses, not verified fault/vent detections.

The highest-priority hypothesis was **not validated** because inputs and protocol feasibility are missing. No HOLDOUT-DTI, confidence interval or withheld-positive count is invented. A future experiment must freeze whole-segment buffered folds, derive catalogue features only from visible faults, run every feature canary first, then compare a paired spatial-block CI against the same-design baseline. Keep the three-experiment/two-hour limit and separate slot selection.

## Sources and access limitations

- Official reference implementation: https://github.com/drivendataorg/gems-prize-reference-solution . GitHub API resolved HEAD to `aebe92f7c8a990f0e3443451b7a825d9afd6336b` this session. This verifies repository identity/version only; it is not a fresh full literature review.
- Official competition description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ . Manual-review link only; not fetched (repository rule against automated DrivenData access).
- Official data page: https://www.drivendata.org/competitions/306/competition-doe-gems/data/ . No DrivenData authenticated browser session here.
- Official rules supplied by owner: https://docs.nlr.gov/docs/fy26osti/96647.pdf . Manual-review link, not newly retrieved or verified in this restricted network.
- Official GeoDAWN source supplied by owner: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and . Not fetched; no new external-data feasibility claim is based on it.

Outbound access is restricted to GitHub and package registries. Current organizer receipts, eligibility, weekly quota and live leaderboard are not verified. Automated project checks remove the need for a human raster inspection; they cannot impersonate organizer acceptance or certify legal eligibility.

## Next actions

1. Restore the actual shared template cache with preprocessing/version/visible-mask provenance, not merely mirrored native TIFFs.
2. Resolve the literal overlap rule's saturation using an explicit owner-approved protocol amendment; do not silently exclude dense/lattice witnesses.
3. Assign one method paragraph; freeze the above first hypothesis and matched controls before running it. Compare only like-for-like spatial holdouts.
4. Identify the actual file rejected by the portal before attributing its range error. All 32 currently audited outputs are finite [0,1], but that does not identify the rejected upload.
5. Keep organizer receipts separate from owner claims and from HOLDOUT-DTI. Promotion and slot authorization remain separate.

## Pass 3

Final commands and test outcome are recorded in the accompanying session run card. Generated evidence and site checks must pass on the final tree before PR creation. No software pass is scientific clearance.

### Parallel-run reconciliation

While this audit ran, PR #156 independently merged the same inventory repair. Merged `origin/main` into this session branch and reused its archive schema, stronger lane-identity tests and hash-bound historical snapshot rather than maintaining a second implementation. The final diff adds this review, the current input/run-card records, and a deterministic H86L homepage anchor/negative-state warning with a regression test. The earlier measured audit remains a session measurement; current published audit evidence uses the reconciled main receipts. The initial full suite had five failures (two from files edited while it ran, one incomplete README link, one count wording, one obsolete timestamp assumption); the focused recheck passed. A second attempt was stopped for reconciliation; the final full suite runs only after that reconciliation.

Final verification: reconciled full suite **1015 passed, 24 skipped**; the H86L module including the subsequently added homepage regression **13 passed**. Release audit, build-site check, site links, all-download audit, frozen-review check and diff-whitespace check passed. Skipped data-dependent tests are not scientific validation.

### Second upstream integration — PR #158

Main changed again before merging this PR: PR #158 added H86M-DAMAGERING, one new inherited TIFF, and again omitted its release-card mapping. Integrated that main commit on this branch, registered its original negative card, and reran the shared witness/format audit for **33** published TIFFs. No pixels were changed or generated by this session. Its archived “no public labels” and “catalogue-only leakage structurally impossible” claims are irregularities, not adopted facts: the pinned catalogue/labels exist locally, and hide-and-recover requires rebuilding catalogue features from visible faults. The auditor exposes the export as unvalidated with null metrics. Rebuilding now removes its hand-edited banner but preserves its audited download and negative card. Shared cache absence remains a separate genuine blocker.

### Third upstream integration — PR #155

Integrated the concurrently merged VFGR no-file negative lane and retained its generated homepage/executive warning and tests. Combined its banner with the H86L-FMC audit anchor; retained the complete 33-file release mapping and witness audit instead of regressing to an older mapping. The full-suite attempt after PR #158 was stopped for this reconciliation rather than reported as passed. The final merged full-suite result is recorded in the run card.
