# Follow-up repository review — 2026-10-25

## Decision first

**DO NOT SUBMIT. The requested new, unique TIFF was not generated.** This is an unmet deliverable, not an implied promotion. No new method lane was assigned in `research/REQUEST_20261025.md`; the actual shared feature cache is absent; and the unchanged literal overlap rule is blocked by the pinned, full-support witness. No model experiment, candidate surface, point placement, new raster, or weekly slot was used. The H86K file discussed below is an older negative result, not a substitute deliverable.

## Fresh evidence and what it means

The small protocol inputs were restored with `scripts/restore_protocol_data.py --include-registry` from pinned GitHub owner mirrors. The restore receipt explicitly says `organizer_authenticated=false`. This did **not** restore `data/bridge/training_features.tif` or any shared feature cache; the native feature TIFF and `.cache/work_h86g/` stack remain absent. No private reconstruction was attempted.

`REGISTRY-MEASUREMENT`, `scripts/protocol_preflight.py`, measured at `2026-10-25T13:58:53.694642+00:00`:

- Pinned witness SHA-256: `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`.
- Witness positive support: **5,167,373** pixels; allowed non-catalogue footprint: **5,106,385** pixels; uncovered allowed pixels: **0**. The difference is the measured 60,988 catalogue pixels, not a conflicting footprint count.
- Thus any nonempty prediction restricted to allowed cells has **100% forward overlap** against this witness, over the unchanged **70%** limit. The certifying status is `STOP_LITERAL_OVERLAP_UNSATISFIABLE`.
- Scope is **one pinned witness**, not a complete registry or uniqueness clearance. No candidate surface or final dots existed, so candidate rank-correlation and final-dot overlap are unmeasured (not zero).

`REGISTRY-MEASUREMENT`, `scripts/audit_release.py --measure-registry`, rechecked all **28/28** inherited published TIFFs against that one witness and preserved the negative global decision. Its registry receipt uses the UTC time returned by the fresh preflight certificate (`2026-10-25T14:01:04.838941+00:00`), not a hard-coded historical timestamp. The evidence remains incomplete by design: 1 witness measured, `registry_complete=false`.

The latest request still cannot be completed safely. The rank-correlation/3-pixel overlap and holdout requirements are retained; no private support threshold, PA diagnostic, local format check, or filename change overrides the literal stop. The site and run card make this explicit.

## H33: what is measured, and what is only plausible

The prompt's H33 `0.2778` and parent `0.2708` are **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`; no submission-page receipt was supplied. The prompt also contains conflicting current-leader claims (`0.3195` and `0.4413`), neither of which is authenticated here. They are not valid targets for a current score comparison, and a local holdout is not a leaderboard projection.

Pixel forensics in `docs/evidence/concurrent-artifact-review-20261025.json` establish this exact edit only: the 40,199-dot parent and 37,654-dot H33 raster are identical except for **2,545 removed dots**, **zero added dots**, at catalogue distances `sqrt(2)` or `2` pixels. H33 is the parent minus that two-pixel collar; the removal does not establish that those dots had low or zero credit.

Under the documented shared DTI, truth credit at each truth pixel is the maximum over covering predictions, not the sum. Therefore genuinely redundant mass can increase false-positive cost without increasing truth credit, and thinning can help **if** it preserves coverage. But a dot 1–2 pixels from a mapped trace is not itself a mapped pixel, and its triangular-kernel support can still reach a withheld, unmapped fault. The metric algebra makes collar pruning a plausible mechanism, not a causal explanation of the reported score. No geological mechanism or expected gain can be inferred from the pixel edit alone.

I added a prominent correction to `research/H33_ANALYSIS.md` so its earlier phrase “explained by” no longer overstates the evidence; the exact historical raster identities and owner-reported values remain intact. The separate `research/H33_INTERPRETATION_REVIEW.md` also records the noncausal interpretation.

## Ranked, not-yet-run geological hypotheses

The current, checkout-scoped queue is `registry/followup_hypotheses_20261025.json`; it names actual bands, the physical signature, why a fault could be absent from the catalogue, repository-specific differences, a non-fault mimic, cost, and falsifier. “Not yet run” means the exact method has no execution in this checkout; it does **not** claim scientific novelty or global novelty across the 92-project fleet. The order is qualitative expected information gain versus implementation cost—not a projected score.

| Rank | Hypothesis and actual layers | Why it could reveal an uncatalogued fault; repo-specific difference | Named non-fault mimic | Qualitative potential / cost |
|---|---|---|---|---|
| **1** | **Basement-interface gravity mass-balance residual (BMR)** — Band 13 `iso_grav_anom`; Band 15 `depth_to_base_surf`. | Fit a fold-safe forward gravity response from basement relief, then test for a localized persistent cross-strike residual. A buried basement displacement could remain without a mapped scarp. Earlier reviews proposed this family, but no explicit forward-residual experiment was found. H86E-SPBT pairs Band 13/15 steps and H86H-PSTD uses gravity tensors; neither is this frozen forward-model residual test. Band 15 is gravity-derived, so it is not an independent sensor and circularity must be tested. | Lateral sediment-density change, errors/smoothing in the gravity-derived basement surface, model-edge ringing. | **Highest qualitative priority, moderate confidence**; **high** cost for units, density sensitivity, fold-safe fitting, and matched raw-gravity controls. |
| **2** | **Persistent potential-field saddle connections (PSC)** — Bands 2 `rtp`, 13 `iso_grav_anom`, 15 `depth_to_base_surf`. | Persistence-ranked saddle-to-extremum graphs could connect anomaly bodies missed by peaks, local edges, and surface-scarp methods. The source search found local Hessian ridges, truncations, cross-gradients, and relay features, but not a persistence-ranked saddle graph. Band 15 is context only, not independent corroboration. | Unfaulted intrusive contacts, erosional basement relief/paleovalley necks, or saddles from superposed smooth sources. | **Medium-low** potential; **medium-high** cost for robust topology extraction, scale controls, and randomized-graph tests. Previously proposed, not run. |
| **3** | **Gravity step-versus-compact-source shape test (GSST)** — Bands 13 `iso_grav_anom`, 5 `iso_grav_anom_slope`, 11 `iso_grav_anom_vg`, 18 `iso_grav_anom_hg`. | Compare multiscale derivative patterns to explicit extended-step and compact-source models. The repository has gravity-curvature and tensor/anistropy features, but no explicit competing-source likelihood. Important physics check: Band 11 is a verified signed southward derivative, Band 18 a signed eastward derivative, and Band 5 a horizontal-gradient magnitude—Band 11 is **not** ordinary vertical gravity. | Elongated intrusive contact, basin-margin facies, or overlapping compact sources. | **Low-to-medium** potential; **medium** cost for scale-matched physical templates and sign/depth sensitivity. Previously proposed, not run. |
| **4** | **Conductivity-neck topology under dilatation (CNT)** — Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate`. | Track narrow conductive component necks across a frozen threshold range and test whether they coincide with positive dilatation/coherent shear. This differs from existing conductivity gradients, margins, and halos. Band 17 is a surface-conductance layer, not a depth-resolved MT image and not proof of hydrothermal fluid. | Saline playa sediment, clay-rich paleochannels, or gridding/interpolation bottlenecks. | **Lowest** qualitative potential due to nonspecific conductivity; **medium** cost for threshold persistence, width tests, and randomized controls. Previously proposed, not run. |

All four use native competition bands and require no new external dataset, but none is currently executable under the shared-cache requirement: native raster bytes are not the required shared cached feature stack. Band identities are checked against `src/gems86/io.py:BANDS` and the repository's band-physics verification.

### Earlier ideas excluded from this queue

- The earlier H86G queue's **CSPA** is no longer untried: `scripts/run_h86j_csgd.py` implemented windowed cross-spectral gravity-magnetic admittance. Its run card records a negative current submission verdict.
- The earlier **MPC** proposal is no longer untried: `scripts/run_h86j_mpc.py` implemented and evaluated monogenic phase congruency; its phase-step candidate was falsified by its amplitude control and is negative.
- Directional variogram anisotropy is excluded because `registry/upstream_registry_index.json` lists a GEMSDOE52 H75-DVA variogram-anisotropy artifact. That name is evidence of a prior attempt, not evidence of its score or scientific validity.
- The deferred H86J-MGRD magnetic attenuation/Euler proposal is not included as currently viable: its required `TMI_up150` external raster is absent from this checkout's `.cache/external`. Its documented official source is the [USGS GeoDAWN release (DOI 10.5066/P93LGLVQ)](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), but those bytes were not fetched or re-verified in this pass, so current availability is unconfirmed. The shared cache is absent regardless.
- The deferred H86J-KNKX idea is not listed as distinct because executed H86J-TVHS/MCSP feature families already use 10 m channel/knickzone and LiDAR scarp evidence; a fresh variant would need a sharper distinction.
- H86K-STC was already run; it is not a new lane. Its historical run card labels **HOLDOUT-DTI** with evaluator `gems57-pooled-hide-v2`, **22,641 withheld positives**: STC `0.0427897`, 95% fold-bootstrap CI `[0.0382765, 0.0465859]`, versus `tmi_hg_only` `0.0457682`, CI `[0.0243899, 0.0519314]`. This is a historical negative comparison, not rerun here. The stored uniqueness comparison checked only 53 local rasters; its 0.8414 overlap is against a dense full-support raster, not a like-for-like sparse-raster clearance. The TIFF is in `releases/h86k/`, not `docs/downloads/`, and remains audit-only. The code change below prevents accidental rerun under the current literal stop.

## Three review passes

### Pass 1 — inspect and reconcile

Read `AGENTS.md`, `PROMPT.md`, the complete archived request, the README's current state, the data/cache receipts, H33 analyses, current run cards, registry source index, `scripts/run_h86k.py`, `audit_release.py`, `build_site.py`, and their tests. Confirmed the missing lane paragraph and shared feature cache. Inspected both H86J entrypoints flagged by the earlier AST screen: `run_h86j_lsi.py` and `run_h86j_mpc.py` call `require_like_for_like()` in `main()` before feature work; the AST concern was not an omitted preflight. Confirmed that H86G-CSPA/MPC are historical proposals superseded by later executed H86J lanes, so the stale queue must not be presented as a current untried list.

### Pass 2 — fix and adversarially test

1. Replaced `audit_release.measure_all_registry()`'s fixed `2026-10-25T04:07:18+00:00` timestamp with the UTC time from its freshly measured preflight certificate. Added a mocked regression that asserts the output preserves that exact time.
2. Added `protocol_preflight.require_feasible()` to `scripts/run_h86k.py::main()` as the first runtime action, before grid/features/holdout/placement IO. Added H86K to the builder AST/imported-orchestrator checks and direct-script fail-before-feature test. No candidate code was run.
3. Added a separate current follow-up register rather than mutating the frozen CF73474C queue/card. Updated the site generator to render the current four proposals and label H86G-CSPA/MPC and H75-DVA accurately as previously attempted.
4. Corrected the causal overstatement in `research/H33_ANALYSIS.md` without changing H33 bytes, historical receipts, or owner-reported values.
5. Corrected `docs/submit.html` wording so a fresh registry-only TIFF remeasurement is not misrepresented as a rerun of four older PR-specific forensic investigations. The page now states the scope boundary explicitly.
6. Added a negative JSON review card with null holdout/raster/validator values where nothing was measured; it records the witness stop and zero slots rather than borrowing historical metrics.

The shared evaluator, submission writer, vendor code, thresholds, and all historical TIFF bytes were not modified.

### Pass 3 — full request and publication recheck

Commands/outcomes for this follow-up:

| Check | Outcome / scope |
|---|---|
| `scripts/restore_protocol_data.py --include-registry` | Restored two core grid inputs and the pinned witness from owner mirrors; receipt explicitly says not organizer-authenticated. Did not fetch the 419 MB feature TIFF or rebuild the cache. |
| `scripts/protocol_preflight.py` | **STOP_LITERAL_OVERLAP_UNSATISFIABLE**; 0 uncovered allowed pixels; thresholds unchanged. |
| `scripts/audit_release.py --measure-registry` | **PASS audit consistency**; 28/28 inherited artifacts remeasured; global `DO NOT SUBMIT`; registry scope remains one witness, incomplete. |
| Focused preflight + timestamp tests | **297 passed** (timestamp regression and builder preflight suite). |
| `scripts/review_repository.py --timeout 900` | **PASS all six stages**: release audit, pytest, frozen-card check, deterministic site check, site links, and download audit. The saved report is in ignored `.cache/repository-review.json`. |
| Full pytest | **967 passed, 24 skipped, 58 subtests passed** in 341.71 s; 48 Rasterio affine-operator `PendingDeprecationWarning`s from the pinned dependency. Skips are not model validation. |
| Release / site / download checks | **PASS**: 28/28 inherited artifacts locally valid and remeasured against the one witness; generated site and links pass; all 28 downloads remain audit-only. |
| Compilation and whitespace check | **PASS**: `python -m compileall -q scripts src vendor tests`; `git diff --check` clean. |

No holdout metric for a new hypothesis exists. No surface rho, candidate-dot overlap, candidate hash, candidate validator result, submission name, upload, quota lookup, or weekly-slot decision exists. The run card deliberately leaves these fields null.

## Trusted references and access boundaries

- [Official competition problem/submission description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [official DOE/NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [Pinned DrivenData reference-solution README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md).
- Repository's dated source observations and limits: [`docs/sources.html`](../docs/sources.html).

These links were already catalogued in the repository; non-GitHub source pages were **not freshly fetched in this follow-up**. No DrivenData portal scraping or automated access occurred. The four ranked proposals require no new external product, so no unverified external-data availability claim is needed. A mirrored data hash proves identity with that mirror, not organizer authentication.

## Irregularities / remaining blockers

1. The user's highest-priority new-TIFF requirement remains unsatisfied. A nonempty TIFF cannot satisfy the present literal witness rule; do not substitute H86K or any prior artifact.
2. There is no assigned method paragraph, and the actual shared cached feature stack/visible-mask receipt is absent. No holdout validation is authorized or reproducible from a private rebuild.
3. The refreshed audit proves rejection against one witness only. It is not a complete current registry scan; previously measured grid-incompatible records still need an explicit policy before future like-for-like clearance.
4. The owner-supplied H33 and leaderboard values lack organizer receipts; the H33 pixel edit does not establish score causation.
5. H86K was historically run without the now-mandatory common preflight and reads native features directly. It is now fail-closed, but would still need a properly authorized shared-cache path before any future experiment.
6. The older H86G proposal register is a historical snapshot. Its CSPA and MPC entries are not currently untried; the new queue separates current status without rewriting that archive.
7. No external source was fetched during this pass. Links are provided for manual review, and the known source-observation dates/limits are stated rather than implied current verification.

## Next safe sequence

1. Obtain the required actual shared cache and its preprocessing/visible-mask identity, plus an explicit single-lane assignment.
2. Resolve the literal witness stop through an authorized protocol decision; do not change thresholds or introduce a local bypass. Reconcile incompatible registry records and restore a complete compatible registry.
3. Only if those gates change legitimately, freeze a BMR preregistration and matched controls, test each feature alone for leakage, evaluate buffered whole fault segments with exact visible-fault masking and the shared `evaluate_holdout.py`, report pooled DTI/evaluator/withheld positives/95% CI, then run pre-placement surface and final-dot registry checks.
4. Stop at three experiments or two hours. Keep weekly-slot selection separate. Only an authenticated submission-page receipt can create `ORGANIZER-CONFIRMED` evidence.

## Machine run card

The authoritative follow-up card is [`docs/evidence/session-20261025-followup-run-card.json`](../docs/evidence/session-20261025-followup-run-card.json). It records a negative review, not a candidate result.
