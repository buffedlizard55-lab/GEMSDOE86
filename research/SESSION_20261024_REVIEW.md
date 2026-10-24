# 2026-10-24 — protocol remeasurement and builder bypass repair

## Executive decision

**DO NOT SUBMIT. No new unique submission TIFF was generated.** The highest-priority deliverable remains unmet, not silently replaced by an old file. The literal overlap rule is mathematically incompatible with any nonempty prediction while the pinned full-positive registry prior remains in scope. No rule exception, dense-prior exclusion, changed support threshold, empty candidate, private evaluator, competition submission or slot selection was introduced.

Read the standing request in [PROMPT.md](../PROMPT.md), its complete normalized [README archive](../README.md#complete-current-request-archive--read-at-the-start-of-every-session), and [REQUEST_20261023.md](REQUEST_20261023.md) each session. The repeated request in this session preserves the same objectives and protocol; archived scores and access assertions are user claims, not measurements.

### What was actually measured

- Restored **only** hash-pinned owner-mirrored sample/catalogue and the immutable registry witness using `restore_protocol_data.py --include-registry`. These are not organizer-authenticated originals or the required shared feature cache.
- Reran `protocol_preflight.measure()`, including both vendored tool-path integrity checks. Allowed pixels: **5,106,385**; directly uncovered allowed pixels: **0**. Every nonempty allowed candidate therefore has forward overlap **1.0**, exceeding **0.70**, independently of its rank correlation or physical hypothesis. This is **REGISTRY-MEASUREMENT**, not a performance score.
- Reread all **10** historical published TIFFs, receipts and one-TIFF ZIPs with the unchanged shared validators. All passed local numerical/format/integrity checks: finite values in `[0,1]`, matching grid, valid footprint, zero mapped-fault mass. All **10** final-dot fields still fail the literal overlap gate against the witness. A single counterexample suffices for rejection; the registry is not claimed complete.
- Added a current remeasurement receipt, [latest-review-run-card.json](../docs/evidence/latest-review-run-card.json), distinct from the archived `session-20261023-run-card.json`. The receipt records the actual UTC measurement time and hashes of both the all-artifact measurement and release report. A stale or optimistic receipt stops site rendering. Rebuilding HTML alone cannot invent a fresh audit timestamp.

The homepage still leads with an explicit no-submit decision and real audit-only TIFF/ZIP links. The executive summary describes the eventual upload procedure without selecting a weekly slot. A file's numerical validity is not scientific validation, uniqueness, eligibility, quota or organizer acceptance.

## H33 scientific answer, with evidence boundaries

The freshly retrieved [GEMSDOE32 page at a pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/078f3cea1bc75d15beb81b095ab488a912327a5d/docs/index.html) identifies H33-2-B2 as flank pruning of a dotted parent. Its note explicitly says `projected 0.2747; UNSCORED`; the requested owner-reported **0.2778** does not occur in those page bytes. Neither absence nor an old `UNSCORED` note disproves a later result. No submission-page receipt was obtained, so the reported result remains **OWNER-REPORTED**, never ORGANIZER-CONFIRMED. Conflicting prompt leaderboard maxima are also unverified.

The plausible advantage is **coverage efficiency**: remove redundant prediction mass while retaining useful distance-weighted coverage. This can reduce false-positive penalty without gaining a new physical signal. Pruning may instead lose coverage of an unmapped parallel fault, so it is not intrinsically beneficial. The README's tested pruning inequality formalizes that tradeoff; it is not a prediction of leaderboard improvement. A mechanism cannot be causally attributed from a sequence of aggregate private scores with simultaneous geometry, budget and preprocessing changes.

Can we do better? **It is possible in principle, but no validated improvement has been established by this review.** The defensible target is better independent discrimination of displaced rock from contacts, shorelines and acquisition artifacts, not another renamed ancestor or unconditional increase in dot count. Catalogue hide-and-recover is an imperfect proxy for genuinely new expert-mapped faults and does not confirm geothermal vents or economic resources.

### Ranked candidates before any new implementation

The three still-unimplemented ideas were already preregistered in [h86c_hypotheses.json](../registry/h86c_hypotheses.json); this review does not falsely call them new inventions today. No missing lane was autonomously assigned. Their ranking is **qualitative expected DTI opportunity**, not a numerical score forecast:

| Rank | Specific layers and physical transform | Why potentially off-catalogue; difference from existing implementation | Named non-fault mimic | Cost / viability |
|---|---|---|---|---|
| 1 | RTP/TMI; phase-correlate opposing flanks for along-strike displacement of transverse magnetic markers | Searches image-derived offsets, not catalogue-tip extrapolation or unsigned cross-field edges; contrasts with existing GFCO/GMC/WVB methods | Intrusive contacts, remanence boundaries, survey seams | Medium-high; no new external product required, but the actual shared cache is absent; NOT RUN |
| 2 | Depth-to-base, isostatic gravity, detrended elevation; signed paired-flank throw consistency | Concealed basin faults may leave internally consistent subsurface offsets without a mapped scarp; tests polarity rather than magnitude-only edges | Erosional basement scarps, density changes, inversion artifacts, old inactive structures | Medium; band/sign semantics and shared cache must be recovered; NOT RUN |
| 3 | USGS 3DEP native 1 m bare-earth DEM plus detrended elevation; signed scarp persistence across independent drainage divides | Tests cross-catchment continuity rather than a ridge or isolated scarplet already represented in existing features | Paleolake shorelines, fluvial terraces, road cuts | High; exact free official product needed is USGS 3DEP 1 m tiles referenced by competition `1m_DEM_links.csv`; actual tiles/coverage not obtained, **NOT VIABLE YET** |

The original register contains scoped USGS physical-basis links and explicit obtainability caveats. This restricted session cannot recheck USGS tile downloads, so the third idea is not offered as runnable. No new external-data hypothesis was falsely declared viable. The top candidate was **not validated**: the pre-placement STOP fires before construction, and no current comparable holdout baseline or actual shared cache is available. Feature-alone canaries, pooled HOLDOUT-DTI and paired spatial confidence intervals remain **NOT RUN**, not zero.

## Safety bug found and fixed

The earlier model entrypoints were guarded, but **22 historical variant-builder mains** introduced by later work were not. Some flags named `--measure` or `--no-write` still construct new dot fields in memory, so suppressing disk writes is not sufficient. They now call the same `protocol_preflight.require_feasible()` before parsing arguments, reading inputs, computing a candidate, serializing rebuilt parents or updating a ledger. Root-path setup makes the guard work for direct `python scripts/...py` invocation as well as imports.

Imported orchestration was also an alternate route: `experiment.run`, `run_lane.holdout`, and H86's surface/canary/holdout/SGMC/final stages now guard themselves rather than relying only on `__main__`. Pure numerical helpers, read-only all-artifact audits, source/registry metadata restoration, historical evidence and actual shared evaluator/writer bytes remain unchanged. Existing `--validate-only` builder commands also stop conservatively; use the dedicated `audit_release.py`, `audit_downloads.py` and `validate_download.py` for read-only published-artifact validation instead.

Regression tests exercise all repaired imported entrypoints with both a literal-overlap stop and missing-input error. An invalid CLI argument detects accidental continuation to parsing or later work. AST tests check that the guard is first and has no bypass option. These are orchestration safety tests with a mocked stop, **not scientific experiments**. This does not claim that every arbitrary low-level Python helper is sandboxed against a caller deliberately bypassing orchestration.

## Scoped source verification and limitations

[Machine-readable recheck](../docs/evidence/source-recheck-20261024.json) records Git blob identities, SHA-256 digests, exact excerpts and limits.

- Rechecked the [official reference repository](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) README and inspected relevant notebook cells at their exact Git blob identities. CPU-only and GPU options exist; GPU is not a universal prerequisite. The notebook uses Tversky training-loss coefficients `alpha=0.2`, `beta=0.8`. Its Monte Carlo patch split is not the requested buffered whole-segment validation, and training loss is not the full official distance-weighted scoring implementation.
- The H33 page's suggested note is **177 characters**, above this project's **140-character** rule. That is an irregularity, not evidence that the competition portal has the same limit. No historical receipt or note was edited.
- Outbound access is restricted to allowed GitHub/package hosts. DrivenData leaderboard/submission pages, NLR rules, USGS, GDR and Dropbox were **not newly retrieved**. Their [prior source observations](../docs/evidence/source-review-20261023.json) retain their historical date; no current official score, eligibility determination, account quota or complete literature review is claimed.
- The rejected upload bytes were not supplied; the cause of its range error cannot honestly be determined. Validating a different local artifact is not diagnosis of that failed upload.
- The full feature cache, a method lane and comparable frozen-fold baseline remain missing. The cached stack must not be privately rebuilt to work around the protocol.

## Three-pass verification record

### Pass 1 — inspect, reproduce, repair

Read standing instructions, current state, prior next steps, archived request, shared pins, negative cards and scientific register. Installed the locked dependencies in an isolated ignored `.venv` (system Python correctly rejected global installation). Baseline full suite: **335 passed, 24 skipped, 32 subtests passed**, four dependency pending-deprecation warnings. Restored pinned proof inputs and reproduced the universal overlap stop. All 10 historical artifacts passed fresh format/integrity checks and failed literal uniqueness. Repaired the 22 mains and seven imported orchestration functions; initial guard regression suite: **80 passed**.

### Pass 2 — edge cases and freshness

Reviewed direct invocation import paths, missing evidence, imported-call bypasses, no-write/measure semantics and preservation of read-only audits. Added current UTC receipt/hash binding and negative-state site checks; historical dates and scientific metrics remain unchanged. Rechecked pinned H33/reference bytes. Added regression tests for invalid/missing UTC timestamps, stale report/registry identities, optimistic verdicts and fabricated candidate flags. No source/feature acquisition or new model experiment occurred.

### Pass 3 — final integration

Final full suite: **425 passed, 24 skipped, 32 subtests passed**, with four Rasterio/Affine pending-deprecation warnings. Skipped tests retain their existing missing optional-data conditions; they are not claimed as executed geological validation. The 90 new regression cases passed. Three actual direct CLI checks (`build_axis_variants`, `run_concentration_pediment`, `run_h86`) with `PYTHONPATH` unset stopped with `STOP_LITERAL_OVERLAP_UNSATISFIABLE` before an invalid CLI option could be parsed. The first test-harness attempt incorrectly resolved the virtualenv Python symlink to system Python and failed to import NumPy; preserving the virtualenv executable path corrected the harness, not the application.

`build_site.py --check`, `check_site.py`, `audit_downloads.py`, `audit.py`, `validate_download.py`, `build_ledger.py --check`, compileall and `git diff --check` passed. Shared evaluator/writer hashes and historical raster/ZIP bytes remain unchanged. The 2026-10-24 receipt is derived only from fresh measurements, not HTML build time. GitHub integration/deployment is an independent operational step; it is not a scientific promotion or evidence that an official submission occurred.

## Next-session priorities

1. **Resolve the impossible uniqueness policy through an explicitly authorized shared protocol revision**, not a private exception. A representation-aware distinction between dense surfaces and emitted dots is a proposal only; this patch does not implement it.
2. Recover the actual shared cache with input/mask/band/unit/implementation hashes and a complete current registry. Assign one method lane. Do not repeat the historical ancestor-reallocation work merely because builders exist.
3. Freeze buffered whole-segment folds, visible-only catalogue features, exact visible masks and budgets. Establish the strongest rerunnable matched baseline on those same folds. Run feature-alone canaries and at most three experiments/two hours; report pooled HOLDOUT-DTI, evaluator version, withheld positives, block 95% CI and paired deltas. Only a separate selector may consider a weekly slot after all gates pass.
4. Retain an actual organizer receipt and exact uploaded SHA before using ORGANIZER-CONFIRMED; do not infer live leaderboard or remaining quota from public project pages. Check external product bytes, provenance, license, geography and target independence before proposing them as available data.
5. Verify PR checks, merge and Pages deployment. A local HTML build is not proof of a live site update.

**Own the outcome:** the requested unique validated submission has not been delivered. This review improves the enforceability and auditability of the stop rather than hiding that result behind an attractive download button.


## Concurrent-main integration

While PR #59 checks were queued, main merged PR #57's separate fleet review.
Its refreshed 88-project metadata feed is retained. The incoming same-date review
is preserved without editing as `SESSION_20261024_FEED_REVIEW.md`; this builder
safety review keeps its own file. Generated homepage content was rebuilt from the
merged feed and current hash-bound negative audit, not resolved by choosing stale
HTML. No predictor or raster pixels were changed by resolving these conflicts.

## Concurrent SPT candidate re-audit — duplicate stop

After the safety review began, main also received PR #60, which added an SPT TIFF
and initially labeled it ready using a restricted scored-fleet comparison. I did
not build or alter that candidate. I re-read its committed raster and compared its
final dots against the already pinned dense witness with the shared
`gems57.uniqueness.dot_overlap` function; the raster grid matches the reference.

**REGISTRY-MEASUREMENT:** the SPT candidate's final-dot overlap within three pixels
of the witness is **1.0**, exceeding the unchanged **0.70** limit. The overlap of
candidate dots on the witness's positive support is also **1.0**. This single
witness disproves clearance; it does not establish completeness of the registry.
The earlier `0.5056` value was calculated against only 25 scored-fleet rasters
and omitted the pinned full-support witness. No saved pre-placement surface was
available, so candidate-surface rank correlation remains unmeasured. The final-dot
failure alone requires the duplicate stop.

The SPT run card was amended to negative and the public `docs/submit.html` page
now says **DO NOT SUBMIT** and contains no candidate download link. The candidate
TIFF remains in the repository only as an audit artifact; no weekly slot or
organizer upload occurred. Its inherited holdout result is not accepted as
protocol-compliant HOLDOUT-DTI: the builder used a collar derived from the full
catalogue, did not demonstrate fold-visible-only derivation or exact visible-fault
masking, and provides no 95% CI. We do not use its number as a valid holdout score.

The SPT/XFLEET builders were missing the mandatory preflight at their entrypoints.
They now stop before grid/cache/feature reads. Regression tests cover direct CLI
invocation and ensure the SPT audit/page cannot revert to an optimistic status.

## Final post-merge verification

After resolving the latest-main integration and the SPT duplicate stop, the complete
suite passed: **431 passed, 24 skipped, 32 subtests passed**, with four existing
Rasterio/Affine pending-deprecation warnings. The 24 skips remain conditional on
optional/missing data; they are not geological validation. The release audit
remeasured all 10 registered historical TIFFs and receipts: local integrity is
valid, the decision remains **DO NOT SUBMIT**, and no experiment or weekly slot was
used. The separate SPT final-dot witness audit is preserved in its own JSON card.

`audit_downloads.py --write`, `build_site.py`, `build_site.py --check`,
`check_site.py`, and `git diff --check` passed. The site explicitly withholds a
candidate download link, the candidate card contains no raw-download URL, and the
site generator rejects a mismatched or optimistic candidate receipt. These checks
do not establish a passing holdout, complete registry clearance, an official score,
organizer acceptance, or Pages deployment. This working branch now includes the
latest-main integration; PR checks and PR #58's merge into main remained external
operational gates at that review's close.

## Follow-up on `arena/57b36fc2-gemsdoe86` — 2026-10-24

The session branch had fallen behind `origin/main`; it was fast-forwarded in place (the branch name was not changed) to include the already-merged SPT duplicate-stop work. No SPT prediction was generated or promoted in this follow-up. I reopened the inherited SPT GeoTIFF, verified its SHA and grid against its audit card, and independently reran the pinned shared `dot_overlap` check against the pinned witness. **REGISTRY-MEASUREMENT:** final-dot overlap was **1.0**, above the unchanged **0.70** limit; this is a duplicate-stop result, not a DTI score. The SPT file remains an audit artifact with no download or submission authorization. Its stored holdout is still explicitly rejected as protocol-incomplete; no valid HOLDOUT-DTI was computed for the current H86C-MMT plan.

The owner-repository metadata feed was refreshed from GitHub: **88/88** named repositories were snapshotted; **zero** organizer receipts were obtained. The read-only release audit re-opened all **10** registered `docs/downloads` TIFFs and their ZIP/identity receipts; local format checks pass, but no file is approved. The latest hash-bound run card records the fresh registry-measurement time and still says no candidate, no experiment and no slot used. No DrivenData, USGS, NLR or Dropbox endpoint was newly retrieved under the session egress policy; prior source observations remain dated.

A user-facing traceability defect was fixed: the generated homepage, research queue and irregularities page now link to `latest-review-run-card.json` and the current 2026-10-24 review rather than labeling a dated card as current. README and PROMPT pointers now distinguish the current remeasurement from the dated archive. The final post-fix suite passed **432 tests**, with **24** existing conditional skips, **32** subtests and **4** dependency deprecation warnings. `build_site.py --check`, `check_site.py`, `audit_downloads.py`, `audit.py`, `validate_download.py`, `build_ledger.py --check`, registry reproduction, compileall and whitespace checks passed. These are software/integrity checks, not new geological experiments, a leaderboard result or organizer approval.
