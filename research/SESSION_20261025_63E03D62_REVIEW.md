# Repository review — 2026-10-25 — session `63e03d62`

## Executive decision

**DO NOT SUBMIT. No new candidate TIFF, scientific experiment, holdout, leakage test, or weekly-slot selection was performed in this review.** The user request does not contain an actual single-method paragraph to define the lane. Separately, the repository's unchanged literal registry preflight has a pinned full-support counterexample covering every allowed cell. These two fail-closed conditions prohibit choosing a substitute lane or placing a new surface.

A previously generated H86L-FMC TIFF was already in `docs/downloads/` but omitted from the format-audit and artifact manifests. This review repaired that metadata/publication inconsistency; it did not generate, alter, rename, or promote the raster. Its scientific run card explicitly calls its holdout leakage-suspect and its verdict negative. The homepage and executive summary continue to say **DO NOT SUBMIT**.

## Three-pass review

### Pass 1 — inventory, source, and protocol

- Read `AGENTS.md`, `PROMPT.md`, `README.md`, the full archived current owner request, the current negative run card, and the latest prior review.
- Confirmed the branch is `arena/63e03d62-gemsdoe86`; the working tree was clean at review start.
- Installed the pinned Python environment from `requirements-lock.txt`. No DrivenData page was scraped or accessed.
- Initial full release checks found one concrete integrity defect: the already-published H86L-FMC TIFF/ZIP pair was unregistered. The release auditor, download auditor, and tests all failed closed.
- Live input inspection found `training_features.tif` absent, all prepared `.npy` arrays absent, and no verifiable actual shared-template feature cache. The two tracked bridge rasters alone do not enable the requested hide-and-recover validation.
- The current method paragraph is missing. The repository's existing H86G proposal table is historical; some formerly listed methods have since been run (for example MPC and PSC). It cannot safely be presented as a fresh, fully untried queue without another status reconciliation.

### Pass 2 — repair and focused tests

- Registered the unchanged H86L-FMC TIFF against its recorded SHA-256, existing negative run card, and associated single-TIFF ZIP; added only the file identity and ZIP integrity fields needed for repeatable auditing.
- Added a narrowly scoped archived-holdout normalizer. It accepts H86L only when the card is explicitly leakage-suspect, negative, and has zero submission authorization/slots; this does not reinterpret the result as independent validation.
- Added regression coverage for H86L's `HOLDOUT-DTI` fields, negative gate state, and registration. The archived report's **HOLDOUT-DTI** is `gems57-pooled-hide-v2`, 11,321 withheld positives, 0.0000, 95% CI [0.0000, 0.0000]; this belongs to the prior H86L experiment and is not a leaderboard score or a result from this review.
- Re-ran the common release audit against the full-support witness and regenerated the derived format report and site. No thresholds, shared evaluator/writer code, TIFF bytes, holdout numbers, or slot flags were changed.

### Pass 3 — end-to-end verification and remaining blockers

- At the initial review audit (17:04 UTC), 32/32 registered historical TIFFs passed local byte/format checks and were measured against the pinned witness. While the PR was open, `main` advanced to `6a859ed` through parallel research PRs; those independent commits add three further historical H86M rasters. I merged that updated `main` into this fixed session branch, then re-ran the release audit. The reconciled current inventory is 35/35; no scientific experiment was run by this review while reconciling the branches.
- The fresh **REGISTRY-MEASUREMENT** rechecked all 35 inherited final artifacts against the pinned witness; each had 1.0 forward overlap under the literal witness-support rule. This is a sufficiency stop, not complete-registry uniqueness clearance and not a measurement of a new candidate.
- Registry completeness remains false: only the pinned witness was measured in this current final-artifact pass; broader registry inputs include incompatible records already documented in the prior audit.
- The current **HOLDOUT-DTI** is `NOT_RUN_NO_LANE_ASSIGNED`; withheld positives, value, and CI are null. No feature-alone canary was run because no candidate feature or lane was selected.
- No new raster was written, so its SHA-256 and candidate validator results are not applicable. The H86L historical raster has its own format checks; this review does not authorize its upload.
- Two contradictory leaderboard values in the owner request, 0.3195 and 0.4413, are **OWNER-REPORTED** claims without a submission-page receipt in this checkout. They must not be treated as verified current leaderboard results. H33's 0.2778 is likewise not ORGANIZER-CONFIRMED here.

## H33 (`GEMSDOE32`) interpretation and limits

The repository's pixel-lineage audit supports a narrow observation: H33 is represented as a pruned variant of its D28 parent, removing 2,545 in-footprint dots and adding none. Under the competition's asymmetric distance-weighted Tversky objective (alpha 0.2, beta 0.8) and 300 m triangular kernel, removing low marginal-credit false positives can improve the precision-weighted term; the same deletion can lose recall if the removed dots coincide with withheld positives. This explains a plausible mechanism, not the private test outcome. The claimed H33 score remains **OWNER-REPORTED**, not organizer-confirmed; its exact causal score decomposition cannot be recovered from the public TIFF alone.

## Hypothesis queue and scientific data limits

No new hypothesis was selected or tested. The four previously ranked candidates in `research/SESSION_20261025_CF73474C_REVIEW.md` are a historical planning queue, not current approvals. In particular, its monogenic phase-congruency and persistent-saddle ideas overlap conceptually with later negative H86J-MPC and H86K-PSC experiments; do not label those two “untested.” The cross-spectral family also needs reconciliation with H86J-CSGD before claiming novelty. Conduct a complete method-registry search and obtain an explicit lane assignment before restarting the three-experiment budget.

Official links retained for independent review (not freshly fetched in this session):

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [official rules](https://www.drivendata.org/competitions/306/competition-doe-gems/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391) and [UNR INGENIOUS project](https://gbcge.org/current-projects/ingenious/).
- [NLR competition technical PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

## Follow-up priorities

1. Obtain an explicit method-paragraph assignment and resolve whether the literal full-support witness is an intended registry member. Do not change the 0.70 rule or comparison semantics privately.
2. Restore the true shared-template cached feature stack with a content hash, preprocessing provenance, grid/footprint identity, and visible-label mask contract. Native-band restoration alone is not equivalent.
3. Reconcile H33's differing footprint/mask provenance before claiming reproducibility.
4. Refresh the full method ledger against all completed lanes, including H86J-MPC, H86J-CSGD, H86K-PSC, and H86L-FMC; only then rank genuinely untried ideas.
5. Once the gates are legitimately resolved, run the pinned evaluator/writer, whole-segment buffered hide-and-recover, feature-alone canaries, surface uniqueness before placement, final-dot uniqueness after placement, and all-finite [0,1] grid validation. A future `promote` does not choose a weekly slot.
6. Any eventual organizer result must be copied from a submission-page receipt. Automated DrivenData access remains prohibited by the project instructions.

## Verification record

| Check | Result |
|---|---|
| `scripts/audit_release.py --measure-registry` | PASS; after main reconciliation, all 35 inherited TIFFs checked; decision remains DO NOT SUBMIT. |
| `scripts/audit_downloads.py --write` | PASS; 35 registered TIFF/ZIP/receipt sets checked; format only. |
| `scripts/build_site.py --check` | PASS after evidence-driven rebuild. |
| `scripts/check_site.py` | PASS; links, registered binary integrity, and negative-state safety. |
| Focused tests | PASS; initial focused run 52 tests / 22 subtests; post-merge focused run 47 tests. |
| Full test suite (final post-merge run) | **1021 passed, 24 skipped, 58 subtests passed** in 430.84 seconds. An earlier full run exposed stale README/timestamp assertions and one overly specific H86L audit assertion; all were corrected without redating frozen evidence or changing scientific values. |
| Python warnings | 48 existing Rasterio affine multiplication deprecation warnings; no new scientific model was run. |

This is a negative review deliverable. It neither creates a leaderboard projection nor satisfies the requested new-TIFF requirement.
