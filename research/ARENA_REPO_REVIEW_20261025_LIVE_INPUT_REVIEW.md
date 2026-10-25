# Three-pass repository review — live-input audit and site correction (2026-10-25)

## Decision first

**DO NOT SUBMIT. No new TIFF was generated; no candidate surface, final dots, or geological experiment were evaluated; no weekly slot was selected or used.** The user's highest-priority request to produce a new, unique submission TIFF remains unmet. This is a deliberate fail-closed result, not a successful TIFF-delivery claim.

The complete archived request at [`REQUEST_20261025.md`](REQUEST_20261025.md) assigns no method paragraph. The required shared-template cache is not established, and the current protocol preflight records a pinned full-support witness that covers every allowed non-catalogue cell. Under the unchanged literal overlap rule, every nonempty allowed candidate would have forward overlap `1.0`, above the `0.70` limit. The checker therefore blocks work before candidate construction. A complete like-for-like measurement of a candidate's rank correlation and final dots is impossible because no candidate was permitted or created. Registry measurement here is one pinned witness, not a complete current registry clearance.

## What the H33 `0.2778` does and does not tell us

`0.2778` is **OWNER-REPORTED**, not ORGANIZER-CONFIRMED: no submission-page receipt is present. The prompt's other current-leader numbers `0.3195` and `0.4413` are likewise claims without receipts in this checkout. They must not be treated as authenticated leaderboard values or as targets a local holdout can prove it exceeded.

The pixel-forensic record in [`H33_ANALYSIS.md`](H33_ANALYSIS.md) says the H33 raster is the GEMSDOE28 parent after removal of exactly the `2,545` dots in the `1 < d_cat <= 2` pixel collar, with no additions. That establishes the raster edit, not why the owner-reported score changed. Under the stated asymmetric distance-weighted Tversky metric, redundant prediction mass can increase the false-positive term without increasing the maximum truth credit; removing such mass could therefore help if useful hidden-fault coverage is preserved. But collar proximity is not a truth mask: a removed dot could still cover an unmapped fault, and deleting the only useful cover could hurt. The available raster comparison cannot distinguish those cases.

**Conclusion:** sparse, coverage-efficient emission is a plausible explanation to test, not a causal finding. Whether a new method can beat the reported `0.2778` is **not established**. The correct next evidence would be a preregistered same-fold HOLDOUT-DTI comparison with a positive paired interval, followed by the mandatory uniqueness and format gates and, separately, an organizer receipt. No holdout number is projected or borrowed here.

## Ranked 3-hypothesis queue (proposals only; no lane assigned)

The ranking below is copied from the checkout-scoped register [`followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json). The qualitative order is research priority versus cost—not a predicted score. The proposals use native competition bands, so no new external data product is required. Their native inputs and, especially, the required shared cache are not currently available. Band identities are defined in [`src/gems86/io.py`](../src/gems86/io.py). “Not found in this checkout” is not a claim of worldwide novelty.

| Rank | Candidate; layers | Signature and reason it could find an uncatalogued structure | Difference from implemented methods | Named non-fault mimic | Qualitative potential / cost |
|---|---|---|---|---|---|
| **1** | **BMR — basement-interface gravity mass-balance residual**; Band 13 `iso_grav_anom`, Band 15 `depth_to_base_surf` | Fit a frozen, fold-safe forward gravity response from basement relief, then test for a localized, persistent cross-strike residual. A buried basement displacement can lack a mapped surface scarp. | Existing H86E-SPBT pairs gravity/depth steps and H86H-PSTD uses gravity tensors; the proposal is an explicit forward-response residual test. Band 15 is gravity-derived, not an independent sensor, so circularity is a central falsifier. | Lateral sediment-density change, errors/smoothing in the gravity-derived basement surface, edge ringing. | Highest qualitative priority, moderate confidence; **high** implementation cost (units/sign, fold-safe model, density/boundary sensitivity, matched controls). |
| **2** | **GSST — gravity step-versus-compact-source shape test**; Bands 13 `iso_grav_anom`, 5 `iso_grav_anom_slope`, 11 `iso_grav_anom_vg`, 18 `iso_grav_anom_hg` | Compare scale-matched horizontal derivative width and signed east/south gradients with extended-step versus compact-source responses. A buried extended discontinuity may be missed by a single gradient maximum. | No explicit competing-source response/likelihood model was found in this checkout; gravity derivative/tensor and Hessian methods are different. Band 11 is a signed southward directional derivative and Band 18 a signed eastward derivative—not conventional vertical gravity gradients. | Elongated intrusive contact, basin-margin facies change, overlapping sources. | Low-to-medium qualitative priority; **medium** cost (scale-matched forward templates and source-depth sensitivity). |
| **3** | **CNT — conductivity-neck topology conditioned on dilatation**; Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate` | Track narrow conductive connections through a frozen threshold-persistence range, then test co-location with positive dilatation/coherent shear. A buried pathway need not have a surface scarp. | Existing methods use conductivity gradients, margins, or halos; no exact persistent-neck topology test was found. An H86K-CNT reserve was proposed earlier but has no execution/run card. Band 17 is surface conductance, not depth-resolved MT and not proof of geothermal fluid. | Saline playa sediments, clay-rich paleochannels, gridding/interpolation bottlenecks. | Lowest qualitative priority due to nonspecific conductivity; **medium** cost (multi-threshold topology, width controls, randomized nulls). |

Each future feature needs its own leakage canary before combination. A feature-alone AUC above `0.90` is a leakage signal until explained. If a proper lane is ever assigned, preserve whole-segment buffered hide-and-recover, derive catalogue features only from visible segments, mask visible fault pixels exactly, and report pooled DTI with its evaluator, withheld positives and 95% CI. Stop within the stated three-experiment/two-hour budget. None of those experiments was run in this review.

## Three passes

### Pass 1 — inspect and reconcile the request

Read `AGENTS.md`, `PROMPT.md`, the full `research/REQUEST_20261025.md`, README, current run cards, input manifests, site renderer, audit scripts, tests, and the latest follow-up review. Confirmed that:

- no single method paragraph is actually assigned;
- the checkout has only the small protocol rasters, not `training_features.tif` or the required shared feature cache;
- old preparation receipts do not establish current array presence;
- the pinned literal witness blocks every nonempty allowed prediction, and existing files are not substitutes for a new candidate;
- the H33 score claim is not accompanied by an organizer receipt; and
- current site prose had a defect: it described the old “all native bands restored and prepared” receipt in a live-sounding status paragraph, despite the actual feature TIFF and prepared arrays being absent in this checkout.

The root-grid copies and registry witness were restored from integrity-pinned owner mirrors to permit the local protocol audit. Their SHA matches establish mirror-byte identity, **not** organizer authentication. No DrivenData portal was accessed or scraped.

### Pass 2 — fix the identified defect

Implemented a reproducible live-input status path:

1. `scripts/audit_workspace_inputs.py --write-report` atomically writes `docs/evidence/current-workspace-inputs.json`; `--require-native` still returns nonzero when required native input is absent. The report explicitly keeps input integrity separate from training, scientific readiness, and upload authorization.
2. `scripts/build_site.py` now reads the live input report and renders timestamped per-input, prepared-array and shared-cache status on the homepage and executive summary. It no longer presents the historical preparation receipt as current input availability.
3. `make audit` and the scheduled/manual Pages workflow refresh the live-input report before rendering. The report is retained with workflow audit artifacts.
4. Added regression tests for atomic report writing, the site’s live-status display, workflow refresh and fail-closed state.
5. Fixed a stale-test assumption that equated an archived session card's historical measurement timestamps with later live remeasurements. The test now checks that the historical timestamps are parseable while binding the immutable witness hash and measured blocker facts. It does not rewrite the historical card.

No feature stack was privately rebuilt. No model, candidate surface, placement, TIFF writer, evaluator, threshold, registry entry, or submission slot was altered or used.

### Pass 3 — re-run and verify the result

| Check / evidence class | Result and scope |
|---|---|
| `scripts/restore_data.py --protocol-only --include-registry` | PASS. Restored/verified sample grid, existing-fault mask and pinned witness from owner mirrors. Not organizer-authenticated; did not restore the 419 MB feature TIFF. |
| `scripts/protocol_preflight.py` — **REGISTRY-MEASUREMENT**, `2026-10-25T16:10:44.320398Z` | `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. Witness SHA-256 `ab0a0a62…`; `5,167,373` positive pixels and `5,106,385` allowed pixels, with `0` uncovered. Every nonempty allowed candidate has literal forward overlap `1.0` versus `0.70`. This is one-witness scope only; no candidate correlation or final-dot overlap was measured. |
| `scripts/audit_release.py --measure-registry` — **REGISTRY-MEASUREMENT**, `2026-10-25T16:10:46.238930Z` | Audit consistency PASS; 31/31 existing published research TIFFs passed local format/integrity checks. Re-measurement against one witness only; registry is explicitly incomplete; decision remains DO NOT SUBMIT. These are inherited files, not a new candidate. |
| `scripts/audit_workspace_inputs.py --write-report` — **INPUT-INTEGRITY-MEASUREMENT**, `2026-10-25T16:21:06.886434Z` | `training_features.tif` missing in both `data/` and `data/bridge/`; existing-fault and sample-grid copies hash-verified; 0/21 recorded prepared-array paths currently hash-verified; shared cache `SHARED_CACHE_NOT_ESTABLISHED`; safe-to-submit false. |
| Site: `build_site.py`, `build_site.py --check`, `check_site.py` | PASS. Homepage and executive summary show the current input report and preserve the negative submission state; link and page checks pass. |
| `audit_downloads.py` | PASS: all 31 inherited research TIFFs and receipts revalidated for local format/integrity. This is not scientific clearance or authorization. |
| Targeted tests | PASS: 53 tests covering input auditing, current review/request and prior follow-up; site-link and download audits pass separately. |
| Full `pytest -q` | PASS: **1,004 passed, 24 skipped, 58 subtests passed** in 366.40 seconds. 48 Rasterio affine deprecation warnings remain; no failures. Skips are not model validation. |
| `compileall` / `git diff --check` | PASS. |

The full session card is [`session-live-input-review-run-card.json`](../docs/evidence/session-live-input-review-run-card.json). **HOLDOUT-DTI:** NOT RUN (`gems57-pooled-hide-v2`; withheld positives/value/95% CI are null because there was no candidate or experiment). **ORGANIZER-CONFIRMED:** no score; no submission-page receipt was accessed.

## Official references and verification limits

The following review links were already catalogued in the repository; this session did not freshly fetch the non-GitHub official pages. They are links for source review, not new claims of current portal state:

- [DrivenData GEMS problem and submission description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — portal/data access requires authenticated user access; automated scraping is prohibited by project policy.
- [DOE/NLR submission guidance PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [DrivenData reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [USGS DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ).
- [DOE Geothermal Data Repository — INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391).
- [EPSG:32611](https://epsg.io/32611).
- [Repository source-observation register](../docs/sources.html) and [H33 forensic analysis](H33_ANALYSIS.md).

## Limitations and next work

1. The new unique TIFF requirement is unmet. Do not rename, repackage, or promote an inherited TIFF to claim otherwise.
2. Obtain the actual shared-template cache and its source-code/input/visible-mask identity contract. The native competition TIFF, if later restored, is not itself that cache.
3. Supply an explicit single method paragraph and resolve the literal witness conflict through an authorized shared protocol decision; do not change thresholds or create a local bypass.
4. Restore a complete, accessible registry and agree a transparent policy for incompatible grids before any claim of like-for-like uniqueness.
5. Only after those blockers are resolved, preregister one lane, run the feature-alone canaries and required segment hide/recover evaluator with matched controls, and perform surface then final-dot uniqueness checks.
6. Keep actual submission selection outside the model builder. No organizer quota, live leaderboard score, upload acceptance, or `ORGANIZER-CONFIRMED` result was inspected or established.
7. Current data restoration scripts fetch pinned owner mirrors; the DrivenData data portal remains the authoritative source but is not available to this automation without authenticated user access. No new private scientific-data access was used.

## Run card

See [`docs/evidence/session-live-input-review-run-card.json`](../docs/evidence/session-live-input-review-run-card.json) for the machine-readable card. Its verdict is **negative**: the request's candidate generation, holdout, uniqueness and submission-authorization requirements were not satisfied.


## Post-review integration addendum — main advanced during PR review

After the three-pass review and its original verification, `main` advanced to `b49a373` with the separate H86L-FMC negative/audit-only TIFF and exposed an existing registration gap (IR-H). This branch now registers that TIFF and run card in the inventory/card map without granting it a validated HOLDOUT-DTI score or upload status. The refreshed local release/download audits report **32/32** format/integrity checks passing; the current decision is still **DO NOT SUBMIT**. This is accounting and publication-gate repair only. H86L-FMC's leakage-suspect holdout diagnostic (0.0000) and duplicate-overlap failure (0.886) remain negative evidence from upstream, not an experiment or candidate produced by this review.

The live-input audit was refreshed at `2026-10-25T16:54:42Z`: the native training TIFF remains absent, 0/21 prepared-array paths are hash-verified, and the shared feature cache remains unestablished. The protocol preflight still blocks every nonempty candidate under the unchanged witness overlap rule. The original review's test counts and registry measurement remain historical to its pre-integration run; post-integration checks are recorded in the PR and current generated evidence.
