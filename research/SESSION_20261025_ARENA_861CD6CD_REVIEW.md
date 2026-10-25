# Three-pass repository review — 2026-10-25

**Branch:** `arena/861cd6cd-gemsdoe86`

**Decision:** **DO NOT SUBMIT. No new TIFF, model experiment, or weekly slot was created in this review.**

**Scope:** Requirement and evidence review, repair of an existing artifact-registration/site defect, read-only audits, and the existing proposal queue. No model fitting, raster generation, candidate placement, or DrivenData access was performed.

This review supplements—not rewrites—the full request embedded in [`README.md`](../README.md) and archived at [`REQUEST_20261025.md`](REQUEST_20261025.md). The earlier request archives remain historical. The older, detailed `research/SESSION_20261025_ARENA_REVIEW.md` remains byte-for-byte preserved; this branch-specific review is kept separately so its earlier evidence is not overwritten.

## Executive answer: what H33's 0.2778 does and does not show

`GEMSDOE32`'s `h33-h33-2-b2` value **0.2778 is OWNER-REPORTED, not ORGANIZER-CONFIRMED** in this repository. The prompt's additional `0.3195` and `0.4413` claims are also user/owner-reported without submission-page receipts here. The current official leaderboard, submission identity behind those two values, and ordering among them were not independently verified; this environment does not scrape DrivenData.

The repository's pixel-lineage review says H33 contains 37,654 positive dots versus 40,199 in the D28 parent: it removes 2,545 dots in the mapped-catalogue collar and adds none. That establishes the pixel edit, **not** why the private score changed. Under the project's distance-weighted Tversky interpretation, a removed dot may reduce false-positive cost, but a nearby dot can still receive credit for an unmasked hidden fault through the kernel. The removed collar is therefore a plausible precision/false-positive-mass hypothesis—not proof of zero lost truth credit or a causal explanation. Cross-site score differences also change geology, support, decoder and density together. See [`H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md) for the pixel audit and counterexamples.

**Can this checkout honestly claim it can beat H33 or the reported leaderboard values? No.** Improvement may be possible in principle, but no comparable clean experiment in this review supports that claim. H86L-FMC's archived result is not a valid promotion result, the current candidate gates are unsatisfiable under the literal rule, and the user-supplied headline values lack organizer receipts.

## Current evidence and blockers

### Protocol stop — `REGISTRY-MEASUREMENT`

Fresh `scripts/protocol_preflight.py` measurement binds the immutable 17GEMSDOE witness to SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`:

- 5,106,385 allowed pixels; 0 uncovered; witness support covers 100% of the allowed domain.
- The unchanged literal forward 3-pixel overlap limit is 0.70. Under the inherited `prediction > 0` support definition, every nonempty allowed dot set has overlap 1.0 with this witness and fails.
- The certificate covers one witness raster from a 655-entry registry snapshot; `registry_complete=false`. It is a sufficient negative, **not** a full-registry uniqueness clearance and not evidence that different geological mechanisms are identical.
- No new candidate surface, rank correlation, final-dot set, or candidate validator result exists in this review. Do not infer any candidate measurement from the inherited-artifact audit.

The all-artifact audit remeasured 32 existing TIFFs against that same single witness. Each has 1.0 forward overlap, but this only reaffirms the negative protocol stop. It does not claim a complete registry scan.

### Live data and lane readiness — `INPUT-INTEGRITY-MEASUREMENT`

`python scripts/audit_workspace_inputs.py` found:

- `training_features.tif`: missing from both `data/` and `data/bridge/`.
- `existing_faults.tif` and `sample_submission.tif`: hash-verified owner mirrors exist in `data/bridge/`; mirror integrity is not organizer authentication.
- The prepared native-band arrays are missing, and the preparation receipt is stale/incomplete.
- The shared-template feature cache is not established; the recorded lane cache is absent. Rebuilding a private feature stack from a raw TIFF would not satisfy the request to reuse the shared cache.
- The current request contains no assigned single method paragraph. Therefore no scientific lane was selected.

These are separate blockers. Restoring a native TIFF alone would not repair shared-cache provenance, assign a lane, or cure the literal protocol stop. No DrivenData download or scraping was attempted.

### Existing H86L-FMC artifact — negative, not a new submission

The repository already contained `gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros.tif`; this review did not create it. The artifact-registration gap was a software defect: the TIFF/ZIP/receipt existed under `docs/downloads/`, but the inventory and artifact-card index omitted them, causing the release audit and generated site checks to fail. The artifact and its scientific card are now registered and the site generator renders an explicit negative/audit-only card on the homepage, executive guide and submission-status page.

Its preserved run card reports:

- **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, 11,321 withheld positives, 95% CI `[0.0000, 0.0000]`): `0.0000`, **explicitly leakage-suspect** because the fleet was built with the full fault catalogue. It is not a clean hide-and-recover promotion result.
- **Paired HOLDOUT-DTI Δ vs H33:** `-0.0037`, 95% CI `[-0.0044, -0.0030]` on the same archived design; this is not an organizer score.
- **LEAKAGE-CANARY:** `fleet_support_count` AUC `0.4361` (below 0.90); the numeric canary does not repair the full-catalogue provenance leak.
- Earlier local scan: 0.8864 forward 3-px overlap versus GEMSDOE63, already above 0.70. Fresh inherited-artifact comparison to the pinned full-support witness is 1.0.
- Local GeoTIFF/ZIP/receipt checks pass. **Format validity does not make it unique or safe to submit.** Its verdict, safety and weekly-slot flags remain negative/false.

The shared release audit now validates all **32/32** registered TIFFs/receipts/ZIPs for local integrity and format. It separately retains `safe_to_submit=false`, `approved_for_weekly_slot=false`, 0 experiments, and 0 slots.

## Ranked untried hypotheses — proposals only

The existing [`registry/followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json) contains three exact methods not found as executed candidate experiments in this checkout. “Untried” is scoped to this checkout, not a claim of global novelty. Ranking is qualitative; **no numeric improvement projection is made**.

| Rank | Layers and targeted signature | Why it might find uncatalogued faults; difference from implemented methods | Named non-fault mimic | Qualitative potential / cost |
|---|---|---|---|---|
| 1 — BMR | Band 13 `iso_grav_anom` plus Band 15 `depth_to_base_surf`; fit a frozen basement-interface forward gravity response on training blocks, then test a persistent localized cross-strike residual. | A buried basement displacement under basin fill could remain after the broad basement response is modeled. This is a physical forward-residual test, not the existing H86E step pairing, H86H tensor derivatives, or H86K Hessian-saddle topology. Band 15 is gravity-derived, so independence/circularity must be tested. | Lateral sediment-density changes; gravity-derived basement-depth error/smoothing; model-edge ringing. | Highest qualitative priority but only moderate confidence; **high** implementation cost (units/signs, fold-safe forward model, boundary and density sensitivity, matched controls). |
| 2 — GSST | Bands 13, 5 `iso_grav_anom_slope`, 11 signed southward gravity derivative, and 18 signed eastward gravity derivative; compare scale-matched extended-step and compact-source shapes. | A coherent extended cross-strike response may survive when single gradient maxima do not. Unlike existing gravity derivative/tensor or Hessian-topology features, this explicitly compares competing source-shape models; Bands 11/18 are not conventional vertical-gravity derivatives. | Elongated intrusive/contact response, basin-margin facies change, or overlapping compact sources. | Low-to-medium qualitative potential; **medium** cost (forward templates, sign/coordinate checks, scale/depth sensitivity). |
| 3 — CNT | Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate`; threshold-persistent narrow conductive connections conditioned on positive dilatation/coherent shear. | A concealed permeability pathway could connect broader conductive zones without a surface scarp. This is a topology/strain test, not the existing conductivity-gradient/margin/halo methods. It was reserved—not executed—in an earlier preregistration. Band 17 is a single surface-conductance layer, not depth-resolved MT. | Saline playa/clay-rich paleochannels; gridding/interpolation bottlenecks. | Lowest qualitative priority; **medium** cost (frozen thresholds, width controls, randomized-neck nulls). |

All three use competition-native bands and need no additional external product, but the native TIFF and the required shared cache are absent here. **Top-candidate validation was not run**: no lane was assigned, and this review cannot bypass the protocol stop. Thus there is no HOLDOUT-DTI for BMR, no per-feature leakage canary, no surface-rank comparison, no final-dot overlap, no new raster SHA, and no validator result for a new candidate. H86L's archived number must not be substituted for BMR validation.

## Three-pass review record

### Pass 1 — requirements, provenance and scientific evidence

- Read `AGENTS.md`, `PROMPT.md`, the full current README request, current lane/history and the shared-tool pins.
- Re-ran live input inspection and protocol preflight. They confirmed missing native/shared inputs, no assigned method paragraph, and the immutable literal-overlap blocker.
- Separated owner/user score claims from organizer-confirmed evidence. No submission-page receipt was supplied or obtained.
- Reviewed the existing untried queue; no candidate was selected or fitted.

### Pass 2 — implementation and adversarial software checks

- Added a strict `h86l_fmc` archived-evidence normalizer that preserves the leakage-suspect label, evaluator, withheld-positive count, confidence interval and paired comparison; it rejects a card that hides its full-catalogue provenance or malformed canary state.
- Registered the existing H86L TIFF/receipt/card as negative; added tests for the correct HOLDOUT-DTI label, leakage caveat, paired interval and witness overlap.
- Updated the generated site to show the existing H86L artifact as audit-only/DO NOT SUBMIT. Shared evaluator, writer, validator, uniqueness thresholds and raster bytes were not changed.
- Targeted review checks: **3 passed** after correcting the current README count/status line. The current follow-up run card's witness/registry timestamps and artifact counts were refreshed to match the latest measured evidence (32 artifacts), fixing the sole full-suite regression.
- Final full suite via `scripts/review_repository.py --timeout 900`: **1,006 passed, 24 skipped, 48 warnings, 58 subtests passed**; the test process completed in 345.02 seconds. All seven review checks passed (release, full tests, frozen evidence, generated site, site links, downloads and live inputs). The 24 skips and 48 warnings are reported, not suppressed.

### Pass 3 — release, website and feed

- `scripts/audit_release.py --measure-registry`: PASS; 32/32 artifacts locally valid; all inherited dots measured against one witness; 0 experiments and 0 slots; decision remains DO NOT SUBMIT.
- `scripts/audit_downloads.py --write`: PASS; 32 TIFFs/receipts/ZIPs checked; no submission decision inferred from format.
- `scripts/build_site.py --check` and `scripts/check_site.py`: PASS; all published download links resolve and the negative status is explicit.
- GitHub metadata feed: 92/92 named repositories snapshotted; 0 organizer receipts, 0 slots; this is not a live leaderboard/quota feed.
- No official external pages were fetched during this review. Existing official references are linked from the site and [`sources.html`](../docs/sources.html); automated DrivenData scraping remains prohibited.

## Limitations and required follow-up

1. A valid new TIFF cannot be produced under the current evidence: the request supplies no single-method lane, the actual shared feature cache is missing, and the literal registry rule fails every nonempty candidate. Do not weaken the threshold or force an empty raster.
2. Before any experiment: obtain/establish the authorized shared feature cache and visible-mask identity contract; assign one method paragraph; resolve the protocol satisfiability conflict through an explicit authorized rule change; make the comparable registry treatment explicit. Then freeze whole-segment buffered holdouts, derive catalogue features from visible faults only, mask visible pixels exactly, run every single-feature leakage canary, reuse the shared evaluator/writer, and score pooled DTI with α=0.2, β=0.8, and the 300 m triangular kernel.
3. A future candidate requires both pre-placement surface and final-dot registry checks, a complete candidate run card, and a separate promotion/slot selector. Do not infer a leaderboard result from HOLDOUT-DTI.
4. Current user-cited `0.3195`/`0.4413`, H33 `0.2778`, organizer quota, and all current leaderboard ordering remain unverified absent submission-page evidence.
5. Fault predictions do not establish geothermal heat, fluid supply, open permeability, a confirmed vent, or economic viability.

## Source links preserved for manual review

- Official competition and leaderboard: [GEMS Prize competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) *(not queried by automation)*.
- Official rules: [DOE/NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- Reference implementation: [DrivenData GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- Official survey release: [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ).
- Regional context: [UNR GBCGE INGENIOUS](https://gbcge.org/current-projects/ingenious/).
- Official geothermal references: [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391), [rules and datasets index](../docs/sources.html).
