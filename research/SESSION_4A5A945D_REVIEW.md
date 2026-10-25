# Repository review — 2026-10-25 — session 4a5a945d

## Executive decision

**DO NOT SUBMIT. No new TIFF was generated; the unique-submission requirement remains unmet.** No model experiment or weekly slot was used. Existing audit-only downloads and the executive submission guide remain at [the project site](https://buffedlizard55-lab.github.io/GEMSDOE86/). A format-valid file is not an approved competition entry.

The full supplied request is already in [README](../README.md) and [the request archive](REQUEST_20261025.md); it was read along with PROMPT.md, AGENTS.md and prior handoffs. No historical score, card, request or candidate bytes were rewritten for this review.

## Pass 1 — inspect, reproduce and correct

- Found a concrete semantic input bug in `scripts/build_unique_submission.py`: `ieq_n100a15` used band 17, whereas the central physical map `src/gems86/io.py` assigns seismicity to band 16 and conductivity to band 17. The prototype now resolves all names through the central `BY_NAME` map. This repairs future identity, not any historical result.
- Found invalid assurance that deterministic/no-training features imply no leakage. Removed it: data-derived and catalogue-derived deterministic features still need feature-alone canaries.
- Found unsafe ordering in that historical prototype: it serialized before registry measurement, lacked surface-before-placement checking, and evaluated fixed dots already masked using the complete catalogue. Such dots cannot test visible-only recovery of withheld catalogue segments. **The CLI is explicitly archived and disabled**, even if the literal-overlap stop is later resolved. The unchanged literal gate still executes first. There is no new bypass, threshold change, replacement evaluator or alternate writer.
- Restored the two small pinned grid rasters and immutable witness using `restore_protocol_data.py --include-registry`. This is mirror integrity verification, not organizer authentication or restoration of the shared feature cache. Recomputed the witness proof and reproduced the existing universal stop. The new read-only measurement is in the session run card; the shared historical proof remains byte-preserved.

## H33: what the evidence supports

The existing pinned-byte forensic receipt [h86f-h33-forensics.json](../docs/evidence/h86f-h33-forensics.json) establishes an exact subset of the D2.8 parent: H33 removes near-catalogue dots rather than discovering a new corridor. Those are historical raster measurements, not newly recomputed model performance. Max-kernel credit can make some dots redundant, so pruning can save false-positive mass while preserving truth credit. It can also remove useful recovery dots. The exact conditional pruning inequality and counterexamples are in [the prior scientific review](SESSION_20261025_CF73474C_REVIEW.md) and `tests/test_scientific_interpretation.py`.

The reported H33 **0.2778**, parent **0.2708**, and inconsistent leaderboard maxima **0.3195 / 0.4413** are **OWNER-REPORTED**, not ORGANIZER-CONFIRMED. No submission-page receipt is available here. A higher private score is possible in principle but is not demonstrated or forecast by this review. Fault-trace prediction is the competition task; geothermal vents are not interchangeable with fault ground truth.

## Ranked geological testing queue (before any new model implementation)

The four detailed hypotheses already in [h86g_hypotheses.json](../registry/h86g_hypotheses.json) remain unimplemented proposals. Ranking is qualitative information gain per cost, **not predicted DTI improvement**:

| Rank | Layers / targeted transform | Missing-fault rationale; distinction | Confounder / cost |
|---|---|---|---|
| 1 | RTP magnetic band 2 + gravity band 13; windowed cross-spectral admittance breaks | Buried juxtaposition may change joint density/magnetization relationships without a scarp; differs from existing curvature dipoles and signed gradient concordance | Lithologic contacts, remanence, mismatched resolution; medium |
| 2 | Bands 2/13; monogenic log-Gabor/Riesz phase congruency | Weak covered markers may retain cross-scale phase despite low amplitude; differs from amplitude-ranked ridge persistence | Lava margins, dikes, ringing and survey seams; medium |
| 3 | Bands 2/13/15; persistent saddle-to-extremum connections | Tests connecting buried structures missed by local maxima; differs from local Hessian/relay graphs; gravity-derived depth is not independent corroboration | Intrusive contacts and superposed sources; medium-high |
| 4 | Conductivity band 17 + strain bands 7/8; persistent conductive necks conditioned on dilatation | Tests covered narrow pathways rather than broad conductance/halo gradients | Saline paleochannels, clay and interpolation bottlenecks; medium |

No new external data are required for these native-layer proposals, but native raster availability is not availability of the mandatory shared cache. No new official external-data product is asserted obtainable. The top candidate was **NOT RUN**: no explicit method paragraph, absent actual shared cache, binding literal stop and incompatible registry entries prevent a compliant experiment. No cross-split historical maximum is used as a current best.

## Pass 2 — edge cases and regressions

Added three tests: every selected band matches the semantic map; resolving the literal blocker still cannot reach construction/serialization in the unsafe archive; and the literal stop retains precedence. No synthetic arrays were submitted as scientific evidence. All shared template files retain their pinned hashes.

An initial test run after refreshing the shared proof timestamp exposed its hash-bound dependency chain (12 failures). The historical proof bytes were restored rather than stamping old measurements with a new time. The completed full rerun passed: **805 tests passed, 24 skipped, 41 subtests passed** (software verification, not HOLDOUT-DTI); 42 third-party pending-deprecation warnings remain. Skips are not scientific passes. This session's new proof is isolated in its own card.

## Pass 3 — requirements, publication and limitations

`audit_release.py` passes integrity checks for all **18 inherited format-valid artifacts**, with decision **DO NOT SUBMIT**. `build_site.py --check` and `check_site.py` pass. These are software/format audits, not candidate uniqueness clearance or organizer acceptance. Pages API reports the existing Pages site built, with legacy build configuration; this does not verify future deployment after merge.

Freshly read the official [reference README at pinned commit](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) using GitHub API. It explicitly supports CPU-only setup; GPU is helpful, not a universal training prerequisite. That README alone does not verify our DTI implementation, band physics or private leaderboard. Band identity above is based on the repository's central map and existing physical-verification evidence, not a claim of new official source authentication.

Official review links (not freshly fetched in this session): [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Egress is limited to GitHub/package hosts; no portal scraping, credentials or quota receipt was used.

### Next-session work, in order

1. Resolve literal continuous-surface overlap semantics explicitly, without privately changing thresholds; resolve incompatible registry rows without silently dropping or warping them.
2. Obtain the actual pinned shared cache and visible-mask/preprocessing receipts; assign the single permitted method lane. Native band preparation alone does not satisfy template reuse.
3. Run feature-alone canaries and frozen buffered whole-segment hide-and-recover using the shared evaluator; test top-ranked CSPA against a rerunnable same-split best and paired spatial CI. Stop for leakage or duplicate gates. Budget remains at most three experiments/two hours.
4. Only after all gates pass, serialize using the shared writer and verify on-disk finite footprint, [0,1], CRS/shape/affine and exact hash. Keep slot promotion separate and require a current quota receipt. The archived prototype is not a supported route.

PR/merge outcome is reported in the session response; no claim of a new approved TIFF is made.
