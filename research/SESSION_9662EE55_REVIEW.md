# Repository review — session 9662ee55 — 2026-10-25 UTC

## Decision first

**DO NOT SUBMIT. No new TIFF was generated. The requested unique-submission deliverable remains unmet.** No geological experiment or competition slot was used. The existing [TIFF/ZIP downloads and executive submission guide](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/executive-summary.html) remain available for review only. A historical `promote` verdict is not authorization to upload.

Read at entry: AGENTS.md, the entire README.md, PROMPT.md, the complete current request in REQUEST_20261025.md, and the latest safety handoffs. The supplied request is already embedded in README; it is not duplicated again or presented as verified evidence. Work remains on `arena/9662ee55-gemsdoe86`.

## Pass 1 — reproduce the handoff; implement one bounded repair

The actual current release audit covers **21** inherited artifacts, not the **18** described in some older dated reviews. All 21 pass the local integrity audit, whose overall decision remains **DO NOT SUBMIT**. This is LOCAL-FORMAT-AND-INTEGRITY evidence, not HOLDOUT-DTI or organizer acceptance. The preserved [fresh summary](session-9662ee55-evidence/release-audit-summary.json) records that scope.

Found and fixed a concrete gap in `scripts/validate_download.py`, the independent historical-download checker:

- Previously it used permissive `json.loads`, accepted a run-card-selected filesystem path without confinement, and imported grid constants without validating shared-tool pins.
- It now reuses `audit_release.strict_json`, `inside`, and `verify_shared_pins`: duplicate keys/nonfinite JSON tokens fail, TIFF and ZIP must resolve within `docs/downloads`, both vendored trees must match their effective pins, and the actually imported grid module must match the same pin.
- These failures occur before raster opening. Absolute/traversing/private paths, escaping TIFF/ZIP symlinks, and wrong suffixes cannot become a successful standalone validation.
- This is validation hardening, not a new evaluator, writer, feature stack, lane, or scientific result. No shared template bytes or thresholds were changed. The valid inherited artifact produces the same report as before and remains negative.

## Why H33 could improve its lineage — and what is not known

Freshly retrieved two immutable GitHub documents and verified their Git blob identities and exact equality with the archives: the [official reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) and [H33 owner's audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json). [Fresh source-integrity receipt](session-9662ee55-evidence/source-integrity.json). This verifies those documents' bytes, not the truth of performance claims in them. H33's audit contains both `UNSCORED` wording and a projected-score field; neither is an organizer receipt. The official README explicitly supports CPU-only setup: a GPU is not a universal training prerequisite.

The historical pinned-byte [H33 forensic receipt](../docs/evidence/h86f-h33-forensics.json) identifies H33 as an exact subset of its D2.8 parent: 2,545 removed dots, no added dots, leaving 37,654; removed dots are within the two-pixel catalogue collar. These are archived RASTER-MEASUREMENTS, not newly recomputed scientific results here. H33 does not demonstrate a newly discovered geological signal relative to that parent.

Under the shared DTI algebra, let `T` be weighted truth credit, `F` weighted false-positive mass, and `K` truth count. Then `D = 0.2(T+F)+0.8K+epsilon`. If pruning loses credit `a` and saves mass `b`, improvement requires exactly `T*b > a*(F+4*K+5*epsilon)`. Max-kernel credit makes redundant dots expendable, but proximity to visible faults does **not** prove zero credit to hidden faults. Consequently collar pruning is a plausible explanation, not proof of the reported private-score change and not a universal recipe. See the metric counterexamples in `tests/test_scientific_interpretation.py` and the [earlier derivation](SESSION_20261025_CF73474C_REVIEW.md).

The supplied H33 **0.2778**, leaderboard **0.4413**, and **0.3195** are **OWNER-REPORTED, NOT ORGANIZER-CONFIRMED**. Their ordering/date cannot be verified here. There is no justified numeric forecast that a new method will exceed them. This competition predicts fault traces; geothermal vents are a scientific motivation, not interchangeable evaluation labels.

## Ranked hypotheses before any model implementation

Carry forward these four **untried local proposals** from [the existing hypothesis register](../registry/h86g_hypotheses.json). They are not claimed as newly invented in this session or globally novel across all sibling repos. Ranking is qualitative expected incremental information for HOLDOUT-DTI against implementation cost, **not projected score improvement**.

| Rank | Native layers and proposed signature | Why a missing fault; difference from implemented methods | Named non-fault process; cost |
|---|---|---|---|
| 1 — CSPA | B2 RTP magnetics + B13 isostatic gravity; localized cross-spectral admittance/coherence breaks | A covered density/magnetization juxtaposition may lack a mapped scarp. Tests a changing joint response, unlike local curvature dipoles or signed-gradient concordance. | Unfaulted buried lithologic contact, remanent lava margin; medium |
| 2 — MPC | B2 + B13; multiscale log-Gabor/Riesz phase congruency | Weak buried markers might preserve phase despite low amplitude. Differs from amplitude-ranked ridges and marker transport. | Dikes, flight-line seams, interpolation ringing; medium |
| 3 — PSC | B2 + B13 + B15 basement depth; persistent saddle-to-extremum connections | Covered connecting structures might be missed by peak-only ridges. Differs from local Hessian and visible-tip relay geometry. Gravity-derived depth is not independent corroboration. | Erosional basement neck or intrusive contact; medium-high |
| 4 — CNT | B17 conductivity + B7 shear/B8 dilatation; persistent narrow conductive necks | Covered pathways might connect wider conductive regions without a scarp. Tests topology rather than broad conductivity or halo gradients; not depth-resolved MT. | Saline paleochannel, playa clay, interpolation bottleneck; medium |

No additional external data product is required for these proposals, but the native raster is **not** the mandatory cached feature stack. We do not claim a new external product is obtainable without acquired bytes. Central layer identity is `src/gems86/io.py:BANDS`; the earlier band-16 seismicity/band-17 conductivity repair is preserved. The top proposal is **NOT RUN**, not a failed canary or measured negative DTI.

## Binding blockers and next steps

1. The prompt refers to a single method paragraph but contains none. Do not autonomously drift into another parallel lane. The hypothesis register has `lane_assignment=null`.
2. Required shared cached feature stack and visible-mask/preprocessing receipts are absent. Native mirrored TIFFs do not establish cache reuse.
3. Restored the pinned small grid inputs and immutable continuous witness; reran read-only `protocol_preflight.measure()` into this session's [separate receipt](session-9662ee55-evidence/protocol-witness.json), preserving shared historical timestamps. It covers every allowed cell; any nonempty dot set has literal forward overlap 1, above 0.70. This proves the literal stop, **not scientific identity of candidates**. PA-86 diagnostics do not override the release gate. Do not privately change thresholds or silently remove the witness.
4. Resolve incompatible registry rows and establish complete valid registry coverage before granting uniqueness. A single witness suffices for a negative, never for clearance.
5. Once feasible and lane-authorized, freeze preprocessing, buffered whole-segment splits and a rerunnable same-split best control. Run each feature-alone canary first, then shared pooled hide-and-recover and paired spatial CI; no comparison across incompatible holdout designs. Stop at leakage, duplicate, three experiments, or two hours. No slot until the scientific gate passes; separate selector authorization and current quota receipt still required.

## Pass 2 — adversarial checks

Added regression tests for malformed JSON in both evidence files; absolute, traversal, private and escaping-symlink paths; non-TIFF inputs; escaping ZIP symlinks; drift in either vendored tree; and a mismatched actually imported grid module. Existing wrong-ZIP-byte and false-readiness tests remain. Focused run: **9 passed, 22 subtests passed** (software verification only).

The initial full suite completed with **839 passed, 24 skipped, 41 subtests passed**, with 42 third-party pending-deprecation warnings. It began before the new tests were added; it is not the final regression run. Skips are not scientific gate passes.

## Pass 3 — final verification and publication

Final full-suite result is recorded in `session-9662ee55-evidence/verification.txt`. Release audit, frozen review-card check, generated-site check, link/inventory safety check, all-download audit, structural audit, and independent download validation were run. Local format success does not authorize submission. Existing generated HTML and historical TIFF/ZIP/cards remain unchanged. No new artifact is renamed or copied into the download inventory.

Official review links: [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). These non-GitHub pages were **not freshly retrieved**: sandbox egress is restricted to GitHub/package hosts. No automated DrivenData access, login, score receipt, or weekly quota lookup occurred. No credentials are requested.

GitHub Pages API reported the existing site `built`, `build_type=legacy`; that is not proof this PR has deployed. PR/merge outcome is reported separately in the final response. [Final negative run card](session-9662ee55-run-card.json).
