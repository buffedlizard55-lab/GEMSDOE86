# Current-workspace review — 2026-10-25 — 679d92e7

## Submission answer

**DO NOT SUBMIT. No new TIFF was generated in this session. The highest-priority requirement for a new, unique, submission-cleared TIFF remains unmet.** No old raster was renamed or copied as a new submission. No model experiment, placement, organizer upload, or weekly-slot selection occurred.

The inherited downloads remain accessible through the [homepage](https://buffedlizard55-lab.github.io/GEMSDOE86/#downloads) and [executive guide](https://buffedlizard55-lab.github.io/GEMSDOE86/executive-summary.html). Their format validity does **not** override the negative submission decision. This limitation is machine-enforced, not a request for a human to inspect a raster.

## What was implemented

`scripts/audit_workspace_inputs.py` inspects **current bytes** rather than assuming an old preparation receipt means data are present. It:

- Checks both native TIFF locations against the existing canonical mirror hashes; a corrupt shadow copy fails rather than being silently ignored.
- Checks every native prepared-array record for existence, SHA-256 and length, and requires the exact native band/footprint/label filename set. Detects stale receipts and duplicate records.
- Rejects paths escaping the checkout, including symlinks, and reports malformed receipts explicitly.
- Distinguishes a lane-specific size-only mmap receipt from a verified shared-template cache contract. Even present bytes cannot establish shared feature-code/visible-mask provenance from that receipt alone.
- Has no network, preparation, fitting, TIFF-writing, or upload side effect. Default exit status describes inspection completion only. `--require-native` exits nonzero for missing/invalid native TIFFs; it is **not** a training or submission authorization command.

The existing three-pass reviewer includes this inspection and explicitly records that training readiness is not established. Tests cover stale/partial manifests, hash corruption, shadow copies, malformed JSON/schema, duplicate records, grid-only preparation, unpinned lane caches, path traversal and symlink escape. Shared evaluator and submission-writer bytes are unchanged.

```bash
.venv/bin/python scripts/audit_workspace_inputs.py
.venv/bin/python scripts/audit_workspace_inputs.py --require-native
.venv/bin/python scripts/review_repository.py
```

## Measured blockers, not assumptions

[Input snapshot](session-679d92e7-inputs.json) is a timestamped **INPUT-INTEGRITY-MEASUREMENT**, not a training result:

- Native `training_features.tif` is absent in both searched locations. Both small grid/fault mirrors are hash-verified.
- All **21** arrays named in the tracked native preparation manifest are absent. The manifest's historical `has_features=true` does not establish current availability. No preparation was run to replace that historical receipt with a grid-only result.
- `.cache/h86_features/static60_fp.f16` is absent. Its historical lane receipt is not an authenticated shared-template feature cache even if the file were restored.
- [Fresh witness measurement](session-679d92e7-witness.json): all **5,106,385** allowed pixels are directly positive in the pinned historical continuous witness. Every nonempty allowed dot set therefore has **REGISTRY-MEASUREMENT overlap = 1.0**, exceeding the unchanged **0.70** literal stop. This is a mathematical rule-satisfiability failure, not proof that all geological mechanisms are duplicates. The PA representation-aware diagnostics do not override the literal final submission gate.
- The prior full inventory review records incompatible historical rows. This session restored only the immutable negative witness, not a full current registry; no complete uniqueness pass is claimed.
- No single method paragraph was assigned. No comparable current-best result was established on a frozen common split. No organizer score receipt or live quota is available.

The statement in the owner prompt that data placement is the **single remaining blocker** is not supported by this checkout. GPU access is also not universally necessary: the freshly rechecked official reference README explicitly supports CPU-only execution.

## What H33 actually proves

[Fresh support comparison](session-679d92e7-h33-lineage.json) found **RASTER-LINEAGE-MEASUREMENT**:

| Quantity | Measured result |
|---|---:|
| D28 parent positive support | 40,199 pixels |
| H33 positive support | 37,654 pixels |
| Removed parent pixels | 2,545 |
| Added pixels | 0 |
| Difference from `parent AND NOT (1 < d_catalogue <= 2 px)` | 0 cells |

These are full-grid **positive-support** counts, not a claim that every cell was inside the feature footprint. No model or submission was constructed by this comparison.

The user-reported **0.2778** for H33 and **0.2708** for its parent are **OWNER-REPORTED**, not ORGANIZER-CONFIRMED. The immutable H33 audit document still says `UNSCORED` in its note and contains a projected leaderboard field; it is not an organizer receipt. [Fresh source byte check](session-679d92e7-sources.json) binds the precise GitHub documents and confirms that caveat.

Under the pinned metric, let `T` be weighted true-positive credit, `F` weighted false-positive mass, and `N` truth count. Then

`DTI = T / (0.2*T + 0.2*F + 0.8*N + eps)`.

Deleting dots reduces `T` by `a` and `F` by `b`. Cross-multiplication shows the deletion improves DTI exactly when

`T*b > a*(F + 4*N + 5*eps)`.

Here **`b` is the reduction of weighted false-positive mass, not the raw deleted-dot count**. Maximum kernel credit at a truth pixel saturates; false-positive mass is summed. Pruning can therefore help when it removes redundant, low-credit mass. It can hurt when a deleted collar dot recovers a genuine unmapped segment. Separation near the kernel radius does not make two kernel disks disjoint. These facts invalidate a blanket claim that binary sparse dots always dominate continuous fields or that collar proximity proves zero truth credit.

**Can a new candidate beat OWNER-REPORTED 0.2778?** It is possible, but no new result in this review establishes that. Neither the hidden truth nor a verified score receipt is available. The conflicting **OWNER-REPORTED 0.3195 and 0.4413** cannot serve as verified current leaderboard targets. No numerical leaderboard projection is made.

## Three prospective hypotheses, ranked before implementation

**None is selected, implemented, or experimentally validated here.** Ranking is qualitative expected information gain for paired HOLDOUT-DTI per cost, not a predicted score. These are narrowly scoped extensions, not claims of new geology or novelty across all projects. A keyword/operator review of executable `src/` and `scripts/` found no explicit bispectrum, wavelet-leader or entropic optimal-transport implementation; absence of keywords does not prove conceptual novelty. Native layer names/indexes are from `src/gems86/io.py`.

| Rank / proposed method | Specific layers and physical transform | Why possibly off-catalogue; difference from existing code | Non-fault mimic / falsifier | Cost and viability |
|---|---|---|---|---|
| 1 — **Bispectral phase closure of buried contacts** | RTP (band 2) and isostatic gravity (band 13); tapered local third-order Fourier phase coupling `X(k1) X(k2) conj(X(k1+k2))`, with amplitude-matched phase-scrambled controls. | A coherent buried displacement could retain localized nonlinear phase coupling without a surface scarp. Existing MPC/MCSP phase congruency and CSGD cross-spectral admittance are not themselves a third-order phase-closure statistic. | Intrusive contacts, finite-window leakage and survey interpolation can yield the same coupling. Reject if matched controls or a second-order amplitude baseline perform as well on paired buffered holdout. | Medium-high; sampling variance is a major risk. No new external source needed, but native data/shared-cache and protocol blockers prevent execution now. |
| 2 — **Two-sided joint-distribution restoration** | RTP (2), total-count radiometrics (6), gravity (13); regularized optimal transport between multivariate profile distributions on opposite sides of a proposed corridor, comparing local affine restoration with translation-only and shuffled controls. | An offset marker assemblage beneath cover might be restored jointly when scalar edges fail. This extends MMT's translation/profile matching; it is not claimed as an unrelated mechanism. | Smooth facies variation, alluvial sorting and unrelated volcanic units. Reject unless a restoration constraint adds paired holdout recovery beyond MMT and identity/translation controls. | High; non-unique inversion and tuning cost. Native-only proposal, currently blocked; no claim that a transport match proves displacement. |
| 3 — **Cross-scale intermittency break at a buried basin margin** | Basement depth (15) and gravity (13), with elevation slope (19) as a nuisance control; wavelet-leader scaling breaks across a corridor, requiring persistence under spatial resampling and detrending. | A buried structural boundary might change multi-scale roughness without a detectable scarp. Existing curvature/flexure/ridge methods test local derivatives, not this explicit scaling statistic. Basement depth and gravity are not independent evidence if one was derived from the other. | Depositional paleochannels, rough basement lithology, inversion smoothing and grid seams. Reject if an edge baseline or shuffled scaling fields match its paired holdout result. | Medium; geological specificity is weak, so ranked last. Native-only proposal, currently blocked. |

No new external product is called obtainable or viable. Official sources below describe the competition/data context; they do **not** endorse these untested operators or establish that any identified fault is an active geothermal vent. The competition target is fault prediction; vent discovery requires additional physical evidence.

## Verified-source and access ledger

| Source | What was verified in this session | Boundary |
|---|---|---|
| [Official DrivenData reference README, immutable commit](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) | GitHub bytes match the archived document; CPU-only support is explicit. | Reference solution, not proof of competition data origin or a score receipt. |
| [H33 owner audit, immutable commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) | GitHub bytes match archive; unscored wording/projection field found. | Owner source, **not official organizer confirmation**. |
| [Official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Links retained for browser review. | Not fetched or scraped; no authenticated receipt or quota check. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Existing official-source link retained. | Host not in this sandbox's outbound allowlist; **not newly verified**. |
| [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Existing official/project links retained. | Not newly downloaded or checked; no fresh external-data viability claim. |

Scientific literature research outside the allowed GitHub hosts was not performed. No line-by-line verification of all 92 live sites, the PDF, the live leaderboard, or hidden organizer evaluation is claimed.

## Three passes and next-session handoff

1. **Implement and verify:** read standing instructions/request, audited all inherited releases, restored and measured the pinned negative witness, freshly compared H33 positive support and official/owner source bytes. Added live input inventory and integrated it into the three-pass reviewer. Initial full suite: **957 passed, 24 skipped, 58 subtests passed** (SOFTWARE-TEST-MEASUREMENT; not HOLDOUT-DTI).
2. **Review bugs/edge cases:** checked actual preparation schema (`prepared_arrays`, exact indexed BANDS), corrupt shadows, malformed manifests, duplicate/symlink/path escape, grid-only caches and missing/size-only lane receipts. Focused review: **26 passed** before final added regression tests. Corrected two current README causal/metric overclaims; immutable prompt/source archives were left unchanged.
3. **Final requirements check:** the seven-check reviewer passed: release audit, full suite (**975 passed, 24 skipped, 58 subtests passed**), frozen evidence, generated site, links, downloads and live inputs. A final symlink-cycle reporting fix and its regression were added after full-suite collection; the final focused supplement passed **32 tests**. `--require-native` correctly exited **1** for the absent feature TIFF. Exact evidence is in [the negative run card](session-679d92e7-run-card.json). These are SOFTWARE-TEST-MEASUREMENTS, not scientific validation; skips are not passed model experiments. No new TIFF was generated to conceal the unresolved gates.

Next steps, in order:

- Resolve the literal/full-registry protocol conflict through a documented shared decision; do not silently change thresholds or exempt rows. A representation-aware diagnostic already exists but is not current upload authorization.
- Restore the actual shared feature cache with content/code/visible-mask provenance. Native TIFF restoration and `prepare_data.py` alone do not fulfill the reuse requirement. The new live checker can verify current native bytes without altering their old receipt.
- Assign exactly one lane and freeze feature definitions, controls, buffer, whole-segment split, emission budget and paired spatial CI. Test feature-alone canaries before trusting results. Compare only identical holdout instruments and establish a common-split best.
- Restore and validate the complete applicable registry; resolve incompatible inputs explicitly, then run pre-placement surface and final-dot checks. Stop/log any duplicate before serialization.
- Only after every gate passes, use the existing shared writer, re-read the actual TIFF/ZIP, verify finite `[0,1]` values and exact template metadata, and expose a clearly authorized download. Keep weekly-slot selection separate and bounded by a real organizer receipt/quota. No score or quota can be invented by automation.
