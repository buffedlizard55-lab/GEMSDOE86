# GEMSDOE86 submission-safety review — 2026-10-25

## Decision in brief

**DO NOT SUBMIT any TIFF linked from this project. No new candidate TIFF was generated.** The user request's method paragraph does not assign a lane, the current project policy binds the literal registry-overlap stop, and the pinned witness makes that rule fail for every nonempty prediction. The actual shared cached feature stack required by the protocol is also not present. A format-valid artifact or a historical `promote` label is not authorization.

This review fixes a serious user-facing contradiction: the landing page and executive summary said H86G-EDTI was selector-ready and directed upload, while the current run card and repo policy say `safe_to_submit=false`, `approved_for_weekly_slot=false`, and retain a binding literal stop. The generated site now labels **every download audit-only** and prominently states **DO NOT SUBMIT**. H86G's historical run card and original TIFF are unchanged; only the current UI interpretation is corrected.

## H33 result analysis and limits

The prompt's H33 `0.2778` and leaderboard figures are **OWNER-REPORTED**, not **ORGANIZER-CONFIRMED**: no submission-page receipt is recorded in this checkout. The exact H33 pixel-lineage analysis in `research/H33_INTERPRETATION_REVIEW.md` is a plausible mechanism: the H33 raster matches its D2.8 parent after removing 2,545 predictions in the mapped-fault-distance collar from 1 to 2 pixels. The asymmetric Tversky objective used by this project assigns false positives weight `alpha=0.2` and false negatives weight `beta=0.8`; at a finite prediction budget, pruning low marginal-credit dots can improve precision/coverage efficiency. That explains a plausible advantage without asserting that proximity to a known fault always has zero hidden-truth credit.

This is pixel lineage and a metric-based explanation, **not a causal reconstruction of the private portal score**. It does not establish that the reported number is authentic, compare submissions evaluated on different data, or show that any new candidate can beat it. The H33 number is not a holdout result. No projection is made.

## Candidate hypotheses already in the repo (not experiments)

These four native-layer proposals are reused from `registry/h86g_hypotheses.json`, whose novelty claims are explicitly scoped to this checkout's executable `src/` and `scripts/`, not all other repositories or the literature. Ranking is qualitative expected information gain per implementation cost, **not a numerical DTI forecast**.

| Rank | Hypothesis / layers | Physical signature and catalogue-missing rationale | What is new versus this repo | Non-fault mimic | Expected holdout potential / cost |
|---|---|---|---|---|---|
| 1 | Local cross-spectral gravity–magnetic admittance breaks; Band 2 `rtp`, Band 13 `iso_grav_anom` | Tapered local cross-spectrum, coherence and scale-dependent admittance; a persistent relationship break could mark buried density/magnetization juxtaposition even without a surface scarp. | No existing implementation of windowed cross-spectral admittance; existing GZZD and PCC measure local curvature dipoles or signed gradient alignment, not scale-dependent cross-spectra. | Unfaulted lithologic juxtaposition, source-depth changes, remanent volcanic magnetization, survey-resolution mismatch. | Qualitatively highest; medium cost (windowed FFT and resolution-matched controls). |
| 2 | Magnetic monogenic phase congruency; Bands 2 `rtp`, 13 `iso_grav_anom` | Multi-scale log-Gabor/Riesz phase alignment may retain a weak, low-amplitude marker; independently corroborated gravity and matched-budget amplitude-only controls are required. | No Riesz/log-Gabor or phase-congruency code was identified in this repo; existing marker/ridge methods use amplitudes and derivatives. | Lava-flow margins, dikes, interpolation ringing, survey seams. | Second; medium cost (multi-scale FFT and orientation controls). |
| 3 | Persistent potential-field saddle connections; Bands 2 `rtp`, 13 `iso_grav_anom`, 15 `depth_to_base_surf` | Scale-persistent saddle-to-extremum connectors may expose buried structure missed by peak/ridge-only methods; depth-to-base is derived from gravity and is not independent corroboration. | Existing CTHB code uses local Hessian ridges, truncations, cross-gradients and relay mechanics, not a persistence-ranked saddle graph. | Intrusive contacts, erosional basement relief, superposed unfaulted sources. | Third; medium–high cost (topological extraction, scale and null controls). |
| 4 | Conductivity-neck topology conditioned on dilatation; Band 17 `cond_surf`, Band 7 `geod_shearrate`, Band 8 `geod_dilaterate` | Persistent narrow necks joining conductive regions under a strain condition could prioritize a concealed pathway; do not interpret this as a depth-resolved MT image. | Existing conductance halos and CTHB margins do not extract persistent conductive-component necks. | Saline playa sediment, clay-rich paleochannels, interpolation bottlenecks. | Fourth; medium cost, lower specificity and higher threshold sensitivity. |

**Top candidate validation: NOT RUN.** The repository's run card records `HOLDOUT-DTI` with evaluator `gems57-pooled-hide-v2` as `NOT_RUN_PROTOCOL_STOP`, withheld-positive count/value/CI null. No experiment, leakage canary, candidate surface, final dots, submission writer, or slot selection occurred in this review. This is not a negative model result; it is a protocol-blocked, no-experiment result.

No new external dataset is necessary for these four sketches: their named native layers exist in the hash-pinned native-band preparation. That preparation is not the actual shared template cache, so the hypotheses are **not runnable under the present reuse requirement**. The official starting sources already recorded in the project are the [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/), and [NLR competition report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Links are supplied for review; this safety recheck did not freshly fetch external pages. Automated DrivenData scraping remains prohibited by `AGENTS.md`.

## Protocol, data and registry findings

- `research/REQUEST_20261025.md` says to follow “the single method paragraph below,” but does not name a method paragraph. Existing hypothesis queues are proposals, not authority to pick a lane.
- `data/prepared_manifest.json` distinguishes native-band preparation from the actual shared feature cache; `docs/evidence/session-cf73474c-data.json` records `actual_shared_feature_stack_restored=false`.
- `docs/evidence/protocol-preflight.json` binds witness SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be` and records `positive_pixels=footprint_pixels`, `covered_allowed_fraction=1.0`, `uncovered_allowed_pixels=0`, literal overlap limit `0.70`, and `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. This is a witness-only proof, not candidate surface/final-dot measurements or registry clearance.
- The registry inventory has incompatible snapshots that must not be conflated: `docs/evidence/registry-input-grid-review-20261025.json` records 690/690 byte-verified indexed rasters with two grid-incompatible entries, while the separate read-only snapshot `docs/evidence/session-review-20261025/registry-input-grid-review.json` records 43/698 byte-verified and grid-compatible rasters. These are differently scoped snapshots, neither is complete current-candidate clearance. Preserve both and reconcile provenance before any uniqueness claim.
- `docs/evidence/latest-review-run-card.json` records no new candidate, no holdout, no validator result, and no upload approval. The top-level site now agrees with that negative current decision.
- No **ORGANIZER-CONFIRMED** score or weekly account quota is claimed. Do not scrape DrivenData; a human-accessed submission receipt is required for organizer confirmation.

## Three review passes

1. **Implementation and verification:** corrected `scripts/build_site.py` so the landing page, executive summary, and every download card say audit-only / DO NOT SUBMIT; preserved historical evidence and TIFF bytes. The historical H86G `promote` card is now explicitly identified in current UI as not cleared to submit. Updated `tests/test_site.py` and added fail-closed text checks in `scripts/check_site.py`.
2. **Bug/edge-case review:** removed the obsolete H86G page renderer that created a live “submit this file” CTA despite the current negative decision. Sanitized the inventory-driven artifact badge and executive-summary table so the historical `PROMOTE — OK TO SUBMIT` string cannot be mistaken for current authorization. Checked both the top page and archive/table view.
3. **Request and regression review:** generated HTML from the evidence source, checked for stale site output, reviewed the download inventory/receipt paths, and confirmed that no new TIFF or weekly submission was produced. No scientific experiment was allowed by the protocol stop.

## Verification performed

- `.venv/bin/python scripts/build_site.py`: PASS; `0 files cleared to submit`.
- `.venv/bin/python scripts/build_site.py --check`: PASS.
- `.venv/bin/python scripts/check_site.py`: PASS; checks local links, registered TIFF/ZIP integrity and negative-state safety, not scientific clearance.
- `.venv/bin/python scripts/audit_downloads.py`: PASS; 20 existing research TIFFs/receipts revalidated and none authorized for submission.
- `.venv/bin/python -m pytest -q tests/test_site.py tests/test_builder_preflight.py`: **255 passed** (focused pass).
- `.venv/bin/python -m pytest -q`: **823 passed, 24 skipped, 42 dependency warnings, 41 subtests passed**.
- Candidate generation, holdout, canaries, placement, and slot selection: **NOT RUN** by design.

## Remaining blockers / recommendations

1. Obtain an explicit protocol disposition that makes the uniqueness rule satisfiable without private threshold changes or bypasses; until then do not generate/submit a candidate.
2. Assign one method paragraph/lane in the request. Then preregister one top hypothesis and at most three experiments / two hours.
3. Restore the actual template cached feature stack with identity/preprocessing hashes; native raster availability is not enough.
4. Reconcile the 690/690 and 43/698 registry snapshots and the incompatible-grid historical rows; measure all applicable rasters with source-bound candidate arrays before placement and after dot emission.
5. When authorized, use the shared evaluator/writer and required whole-component buffered hide-and-recover; mask visible faults pixel-exactly; derive catalogue features only from visible faults; run feature-alone leakage canaries; compare paired 95% CI to the matched same-split best.
6. Only after science and uniqueness pass should a separate selector check remaining weekly quota. Keep the download CTA clearly negative until then; collect a submission-page receipt before recording any organizer score.

## Run card

See `evidence/session_20261025_submission_safety.json` for the machine-readable run card and `evidence/session_20261025_submission_safety_preflight.json` for this review's independently rerun witness measurement (current UTC timestamp, same hash-pinned blocker). The canonical `docs/evidence/protocol-preflight.json` was not overwritten because downstream release reports are hash-bound to that canonical snapshot. This review's verdict is negative because candidate execution was blocked; it is not a scientific candidate result.
