# Independent review — 2026-10-25 — current submission-status reconciliation

## Decision

**DO NOT SUBMIT. No current file is authorized for upload or a weekly slot.** The repository had a genuine release-pipeline contradiction: the top-level report said no file was authorized, while H86G-EDTI's inventory row, per-file audit and generated site displayed a positive selector/submit verdict. This review corrected the current-status path without rewriting H86G's historical scientific card or changing its TIFF/ZIP bytes.

The pinned `17GEMSDOE` witness is positive over all **5,106,385** allowed cells (100%). Under the unchanged literal overlap rule, any nonempty prediction has forward overlap **1.0**, above the **0.70** limit. `protocol_preflight.py` reports `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. This is **REGISTRY-MEASUREMENT** sufficient to reject any nonempty candidate, not a complete registry scan and not proof that all geology hypotheses are identical.

No candidate TIFF was generated, no geological experiment or holdout was run, no selector action occurred, and no weekly slot was used. The highest-priority new-TIFF requirement remains unmet. The single-method lane is unassigned and the actual shared cached feature stack is absent; the preflight stops before candidate placement. The original request's urgent TIFF instruction does not waive these standing gates.

## Pass 1 — evidence, protocol, H33 and strategy review

### H33 score: claim versus measurable lineage

The supplied **0.2778 is OWNER-REPORTED, not ORGANIZER-CONFIRMED**; no matching portal receipt binds that value to the TIFF. The current pixel audit verifies that H33 is a strict subset of its 40,199-dot parent: it deletes exactly 2,545 dots at catalogue distance √2–2 px and adds none. If both supplied score values bind to those exact rasters, that is the sole raster change. It is consistent with a coverage-efficiency explanation—removing redundant or low-credit prediction mass near mapped faults under asymmetric DTI (α=0.2, β=0.8, 300 m triangular kernel)—but does **not** prove that those removed dots lacked hidden-truth credit or explain an organizer result. The conflicting prompt values 0.3195 and 0.4413 are also unverified claims. No local HOLDOUT-DTI or proxy is a leaderboard projection. See [H33 analysis](H33_ANALYSIS.md), [pixel-forensics receipt](../docs/evidence/h86f-h33-forensics.json), and [interpretation limits](H33_INTERPRETATION_REVIEW.md).

### Four distinct, ranked geological hypotheses

The existing preregistered queue is retained at [`registry/h86g_hypotheses.json`](../registry/h86g_hypotheses.json). The ranking is **qualitative expected information beyond executable edge/coverage methods per implementation cost**, not a DTI estimate. Every proposal names layers, a physical signature, why a buried/unmapped fault might be expressed, a specific non-fault mimic, implementation cost and falsifier. All are `NOT_RUN_PROTOCOL_STOP`; `lane_assignment` is `null`.

| Rank | Hypothesis / layers | Target signature and unmapped-fault rationale | Principal non-fault mimic | Cost |
|---:|---|---|---|---|
| 1 | **H86G-CSPA — local cross-spectral gravity–magnetic admittance breaks**; B2 `rtp`, B13 `iso_grav_anom`. | A localized, scale-persistent change in gravity–magnetic cross-spectrum/coherence may reveal buried density–susceptibility juxtaposition without a surface scarp; compare to phase-scrambled controls. | Unfaulted lithologic contact, source-depth change, remanent volcanic magnetization, survey-resolution mismatch. | Medium; windowed FFT and resolution-matched controls. |
| 2 | **H86G-MPC — magnetic monogenic phase-congruency lineaments**; B2 `rtp`, corroborated by B13 `iso_grav_anom`. | Multi-scale log-Gabor/Riesz phase alignment can preserve a weak covered marker whose amplitude is low; compare to amplitude-only edges at fixed budget. | Lava-flow boundary, dike, interpolation ringing or survey seam. | Medium; multi-scale filtering and orientation controls. |
| 3 | **H86G-PSC — persistent potential-field saddle connections**; B2 `rtp`, B13 `iso_grav_anom`, B15 `depth_to_base_surf`. | A scale-persistent connector between anomaly bodies could mark a covered relay missed by peak/ridge detection; gravity-derived basement depth is not independent corroboration. | Intrusive contact, erosional basement relief or superposed sources. | Medium-high; topology extraction and randomization controls. |
| 4 | **H86G-CNT — conductivity-neck topology conditioned on dilatation**; B17 `cond_surf`, B8 `geod_dilaterate`, B7 `geod_shearrate`. | Persistent narrow conductive necks under positive dilatation may suggest a buried pathway without exposed scarp; one surface-conductivity band does not provide MT depth migration. | Saline playa, clay-rich paleochannel or interpolation bottleneck. | Medium; multi-threshold topology and width/strain controls. |

The queue uses native pinned layers; it does not propose a hypothesis requiring a new external grid. The mirror is not organizer-authenticated and is not the actual shared derived cache. Before any future experiment, the queue requires an assigned method lane, real cache bytes/receipt, a satisfiable protocol disposition, and a complete valid same-grid registry that explicitly handles the two incompatible rows. Therefore the top candidate was **not** tested on holdout. Testing it now would violate the protocol stop and the no-lane rule; no slot will be touched without those prerequisites and a frozen spatially blocked validation showing a genuine paired improvement.

### Source and obtainability limits

Manual review links: [official DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS MT DOI](https://doi.org/10.5066/P9TWT2LU), [USGS heat-flow DOI](https://doi.org/10.5066/P9BZPVUC), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), and [UNR INGENIOUS](https://gbcge.org/current-projects/ingenious/). The repository's source-observation receipt is dated 2026-10-23; non-GitHub pages and the authenticated portal were not freshly fetched in this review. The official data page is login-walled in the dated observation. No DrivenData scraping or quota lookup occurred, and no external product was called obtainable based solely on a URL. These four proposals use only existing native bands; obtaining the actual shared cache remains a hard blocker.

## Pass 2 — current-state corrections

- Changed the live `docs/evidence/download-inventory.json` H86G row to exact `DO NOT SUBMIT`; renamed its mapping in `registry/artifact_cards.json` to identify the prior promote as historical and superseded.
- Changed `scripts/audit_release.py` so every artifact status/verdict is negative and inventory status must be exactly `DO NOT SUBMIT`. H86G's earlier card is validated only as an archived record; its scoped lane outcome no longer produces a current positive release badge. The adjacent H86G writer sidecar carries a transparent current-disposition addendum while preserving its original decision/verdict in explicit historical fields. The original H86G scientific run card and raster/ZIP bytes remain unchanged.
- Changed `scripts/check_site.py` to reject any inventory status other than exact `DO NOT SUBMIT` and to fail if a current safety page omits the negative decision or contains positive upload copy.
- Reworked `scripts/build_site.py`: the homepage, executive summary and submission-status page now lead with **zero files authorized**; every artifact button says audit-only / DO NOT SUBMIT; the H86G panel distinguishes the old scoped promote from the current literal stop and includes direct audit-only links, a labelled historic HOLDOUT-DTI, and the current witness measurement. No upload instructions are presented as current advice.
- Corrected the README and standing-status summaries in `PROMPT.md`, `AGENTS.md`, and `SLOT_PLAN.md`; added a superseding notice to the historical H86G review; clarified the H33 causality limits; and logged `IR-86-H86G-CURRENT-STATUS-CONFLICT-20261025` in `IRREGULARITIES.md`.
- Added regression checks for positive inventory status, positive upload copy, H86G historical/current disposition, release outputs, and site messaging.

## Pass 3 — rebuild and verification

The pinned witness was restored from the public `17GEMSDOE` mirror after the configured GitHub API hit a rate limit. Its Git blob was verified as `374c88b1da2b803e2ed160de467fd71ae114010d`, its SHA-256 as `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`, and its byte length as 25,065,181. `scripts/protocol_preflight.py` remeasured the stop at 2026-10-25T04:06:05Z. This was data restoration for a negative audit only; no model or candidate code ran.

| Check | Outcome |
|---|---|
| `scripts/audit_release.py --measure-registry` | **PASS:** 20/20 local artifact integrity checks; every per-file status `DO NOT SUBMIT`; global decision negative; 0 experiments and 0 slots. H86G final-dot overlap versus pinned witness = **REGISTRY-MEASUREMENT 1.0**. |
| `scripts/audit_downloads.py --write` | **PASS:** 20 TIFF/ZIP/sidecar records revalidated; none authorized. |
| `scripts/build_site.py` | **PASS:** generated current negative pages. |
| `scripts/build_site.py --check` | **PASS:** generated pages match their evidence-driven source. |
| `scripts/check_site.py` | **PASS:** local links, registered raster/ZIP hashes, and negative-state publication safety. |
| Focused regression suite | **PASS:** 77 tests and 13 subtests. The initial stale H33 assertion and missing review-document link were corrected; the final focused run passed. |
| Full repository suite: `python -m pytest -q` | **PASS:** 825 passed, 24 skipped, 41 subtests passed; 42 `rasterio` `PendingDeprecationWarning`s. No test failures. |
| Chromium UI smoke: `scripts/browser_smoke.cjs` | **PASS:** [`ui-smoke-20261025.json`](../docs/evidence/ui-smoke-20261025.json); 11 pages at 1440 px and 390 px, no horizontal overflow, all 20 TIFF and 20 ZIP links counted in the registered list, browser-downloaded TIFF hash matched, filter/copy controls worked, zero browser errors, and the negative decision/downloads remained available without JavaScript. This is local UI verification only. |
| `git diff --check`, Python compilation, JSON parsing | **PASS** at the earlier edit checkpoint; final diff review is recorded below. |

All three review passes are complete. Scientific, release and UI checks pass only at their stated scope; they do **not** satisfy the literal uniqueness constraint or authorize submission. The current decision remains **DO NOT SUBMIT**. No inherited file may be promoted or uploaded.

## Current handoff

1. Keep **DO NOT SUBMIT**; the literal witness proves every nonempty allowed candidate fails the current overlap rule.
2. Obtain a protocol-owner disposition that genuinely resolves the literal/full-support contradiction without a private threshold bypass; repair the two off-grid registry records by an explicit upstream policy.
3. Assign one lane and restore the actual shared feature cache with its preprocessing, footprint and implementation identity.
4. Only after those prerequisites, freeze buffered whole-segment spatial folds, derive catalogue features from visible faults only, mask visible faults pixel-exactly, run every feature-alone leakage canary (AUC >0.90 is leakage pending explanation), and evaluate CSPA or another assigned hypothesis with the unchanged pooled DTI α=0.2, β=0.8, 300 m triangular kernel and 95% physical-block CI against matched controls.
5. Stop at three experiments or two hours; do not select a submission or spend a weekly slot. Only a separate authenticated selector and organizer receipt can create slot approval or ORGANIZER-CONFIRMED evidence.
