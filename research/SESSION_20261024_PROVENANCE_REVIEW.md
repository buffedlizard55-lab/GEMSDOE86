# 2026-10-24 follow-up: reproducible stop and measurement provenance

## Outcome

**DO NOT SUBMIT. No new unique TIFF was generated.** This remains an unmet requirement, not a success claimed through a renamed historical file. No model experiment, lane assignment, private shared-tool fork, rule exemption or weekly-slot use occurred.

The repeated request is preserved in the README's complete request archive and the standing `PROMPT.md`. The prior [review](SESSION_20261024_REVIEW.md) and [three ranked, unimplemented hypotheses](../registry/h86c_hypotheses.json) remain applicable. They are not new inventions in this follow-up. The prompt still does not supply its promised single-method lane. Proposing additional untestable variants would not resolve the earlier next-step blockers.

## Pass 1 — restore and reproduce

Installed locked dependencies into ignored `.venv` after system Python reported missing NumPy. Restored the hash-pinned sample/catalogue mirrors and historical registry witness, not a cached feature stack or a new submission. Fresh measurement confirms every allowed pixel is positive in the witness: **5,106,385 allowed pixels; zero directly uncovered**. These are REGISTRY-MEASUREMENT counts, not DTI. Any nonempty allowed dot set has forward overlap **1.0**, exceeding the unchanged **0.70** gate. This is a sufficient rejection witness, not a complete-registry uniqueness clearance.

All **10 inherited TIFFs** were reread: local format/integrity checks pass; literal final-dot uniqueness fails for every artifact. The site continues to distinguish audit-only downloads from permission to submit. No new-candidate validator result, feature canary, withheld-positive count, HOLDOUT-DTI or CI exists for this session.

## Pass 2 — provenance bug and edge cases

Found `protocol_preflight.measure()` hard-coded `measured_date_utc='2026-10-22'` even on fresh execution. It now stamps completed measurements with timezone-aware UTC and derives the date from that same instant. Historical witness verification is separately retained as `witness_verified_date_utc`. Shared evaluator, writer and uniqueness code remain byte-unchanged.

Synthetic regression tests cover both sides of UTC midnight and corrupt witness input. Corruption stops before a completion timestamp can be issued. These tests exercise orchestration/provenance, not model performance.

Refreshing the proof invalidates downstream hash-bound receipts as intended. An initial local command sequence refreshed the proof *after* the artifact audit; site rendering correctly rejected that stale binding. Correct order is now explicit in Pages deployment: restore → preflight proof → all-artifact measurement → site build. Added a regression check for that order and retention of both current run card and proof in workflow artifacts.

## Pass 3 — integration and evidence limits

Full suite before the final workflow-order test: **428 passed, 24 skipped, 32 subtests passed**, with four Rasterio/Affine pending-deprecation warnings. After adding that test, targeted provenance/current-review/protocol suite: **29 passed**. Read-only release audit, download audit, ledger generator check, generated-site check, site-link/integrity checks and `git diff --check` pass. Skipped optional-data tests are not executed scientific validation.

Freshly rechecked two immutable sources through GitHub, with blob and SHA-256 checks in [review-source-checks.json](../docs/evidence/review-source-checks.json):

- [Official reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md): includes CPU-only support; the prompt's universal GPU prerequisite is not supported.
- [H33 owner audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json): includes UNSCORED wording and a projected leaderboard field; this is not a submission-page receipt. The user-reported result is not independently confirmed here.

H33's plausible advantage remains reduced redundant prediction mass while preserving distance-weighted coverage, not demonstrated discovery of a new geothermal mechanism. Neither causal attribution of its reported score nor a promised improvement is justified by these artifacts. The competing leaderboard figures in the prompt remain unverified. This follow-up does not claim to have re-researched every sibling site or fetched official portal/USGS/NLR/Dropbox content beyond the allowed network hosts.

## Next steps, in dependency order

1. Obtain an explicitly authorized **shared** distinction between dense prediction surfaces and emitted dots if the literal rule is to change. No private threshold change is implemented here.
2. Supply one method lane; recover the actual hash-pinned shared cache and current registry. A raw feature mirror is not the cache.
3. Freeze a comparable buffered whole-segment baseline, visible-only catalogue features, exact masks and dot budgets. Run feature-alone canaries, then the top magnetic-marker hypothesis within the experiment/time cap. Report paired spatial uncertainty and pooled HOLDOUT-DTI before any selector decision.
4. Preserve an organizer receipt, exact uploaded hash and verified quota before describing any result as ORGANIZER-CONFIRMED or authorizing a slot.

Current negative run card: [latest-review-run-card.json](../docs/evidence/latest-review-run-card.json). PR merge/deployment, if completed, is operational delivery only, not scientific promotion.

### Final workflow review

Found a second consequence during pre-merge review: the proof-reproduction CI job compared entire JSON files byte-for-byte, including the now-correct variable measurement timestamp. Added `check_preflight_reproduction.py` to validate explicit UTC and date consistency, then compare all other fields exactly (including historical verification date, hashes, thresholds and verdicts). Only those two proof files are excluded from the generic Git diff; the dedicated comparator checks both. Added regression coverage for midnight, missing/non-UTC offsets, mismatched dates, changed verdicts and historical dates. This does not relax any scientific gate.

Final full-suite recheck after all code changes: **430 passed, 24 skipped, 32 subtests passed**, four dependency pending-deprecation warnings. Site generation/check, link/integrity checks and all ten download audits passed again. GitHub checks were queued without runners at the first watch timeout; queued is not passed.
