# Final repository review — 2026-10-24 (Arena session)

## Decision

**Negative / DO NOT SUBMIT. The requested new unique competition TIFF was not generated.** No holdout experiment was run, no candidate was selected, and no competition slot was used. The highest-priority failure is an unsatisfiable literal duplicate gate, not a missing file-writing feature. Existing TIFFs are audit-only and must not be uploaded.

This review reread `PROMPT.md`, `README.md`, `research/REQUEST_20261024.md`, and the previous 2026-10-24 session records before acting. The user-provided scores in the request are not organizer receipts. No automated access to DrivenData was attempted.

## Three review passes

### Pass 1 — understand the request and establish stop conditions

- The request says “single method paragraph below” but no such method paragraph/lane is present in the supplied request. The lane cannot be inferred from a previous session or from the hypothesis queue.
- `scripts/restore_protocol_data.py --include-registry` restored the SHA-pinned sample grid, fault mask, and historical registry witness. The receipt explicitly says competition mirrors are owner-supplied and **not organizer-authenticated**. The raw training-feature cache referenced by the protocol is not present; this restore does not create it.
- `scripts/session_preflight.py` then reported `STOP_LITERAL_OVERLAP_UNSATISFIABLE`. In the pinned witness measurement, all allowed off-catalogue support cells are covered under the inherited `finite prediction > 0` support definition. Consequently, every nonempty candidate support has forward overlap `1.0`, exceeding the configured `0.70` limit. This is a **REGISTRY-MEASUREMENT**, not a score. The witness is sufficient to reject under the literal rule but the scan is incomplete and cannot certify uniqueness.
- No candidate surface was built. Thus pre-placement rank-correlation, final-dot overlap for a new candidate, leakage AUC, and candidate holdout DTI are **not measured**; they are not passes.

### Pass 2 — inspect scientific and publication claims

- The existing five-hypothesis queue is retained in [`registry/h86c_hypotheses.json`](../registry/h86c_hypotheses.json). The qualitative top candidate remains **H86E-SPBT**, signed paired basement-depth/gravity flank polarity under low-relief basin cover. It is untested and cannot be run while the stop is active. The full set names source layers, physical signature, catalogue-missing rationale, differences from prior repo methods, and non-fault mimics. Its ordering is a research-priority judgment, **not a numerical DTI projection**.
- For external-data hypotheses H86E-MTCS and H86E-WCS, the repository names USGS DOI `10.5066/P9TWT2LU` / `10.5066/P9BZPVUC` and official USGS 3DEP 1 m DEM products respectively. Their raw grids/tiles are not available in this workspace; they are explicitly not viable for execution until bytes, metadata, coverage, license/provenance, and hashes are obtained. The MTCS DOIs are linked for review at [USGS MT conductance](https://doi.org/10.5066/P9TWT2LU) and [USGS heat flow](https://doi.org/10.5066/P9BZPVUC). These are source references, not claims of a fresh fetch in this session.
- The repository's H33 analysis explains the reported `0.2778` through exact raster forensics: the H33 dots match the archived R0 parent after removing a near-catalogue collar. Sparse mass outside already mapped fault pixels can plausibly reduce false-positive cost while preserving some triangular-kernel coverage of hidden traces. This is a mechanism-based interpretation, **not a causal demonstration of leaderboard performance**. The reported `0.2778`, `0.3195`, and `0.4413` remain `OWNER-REPORTED`, not `ORGANIZER-CONFIRMED`; there is no submission-page receipt in this checkout. See [`research/SESSION_20261024_REVIEW.md`](SESSION_20261024_REVIEW.md) for the pixel-level comparison and its caveats.
- `scripts/audit_release.py --measure-registry` revalidated all ten published release TIFFs locally. They pass local file/format checks but remain negative against the literal registry gate; local validity does not imply uniqueness, scientific merit, or organizer acceptance. `scripts/audit_downloads.py` independently reported the historical research downloads as not authorized. No old raster was repurposed as a “new” submission.

### Pass 3 — regenerate, test, and cross-check

- The evidence audit refreshed measurement timestamps and evidence hashes. The first `build_site.py --check` and simultaneous initial test pass correctly caught stale generated `docs/index.html` / `docs/submit.html` pages. I regenerated those pages and reran the checks; this is recorded as a fixed generated-artifact drift, not hidden.
- Final checks passed:
  - `scripts/audit_release.py --measure-registry`: audit OK; 10/10 published release TIFFs locally valid; decision remains `DO NOT SUBMIT`; zero experiments and zero slots.
  - `scripts/audit.py`, `scripts/validate_download.py`, `scripts/audit_downloads.py`, and `scripts/build_ledger.py --check`: passed. The independent download audit still says no artifact is authorized.
  - `scripts/build_site.py --check`, `scripts/check_site.py`, `compileall`, and `git diff --check`: passed. The generated site continues to label all research downloads `DO NOT SUBMIT`.
  - `.venv/bin/python -m pytest -q`: **491 passed, 24 skipped, 4 pending-deprecation warnings, and 41 subtests passed**. Skipped tests are not scientific validation; the raw cache-dependent experiment was not run.
- `docs/evidence/latest-review-run-card.json` is the machine-readable negative card. It contains no candidate SHA/name, no HOLDOUT-DTI estimate, and no validator pass for a new raster because none exists. It records the incomplete registry scope and the witness stop.

## PhD-level answer and limits

The archived H33 analysis is plausible because its improved reported score is consistent with reallocating fixed prediction mass away from the mapped-fault collar while retaining support whose 300 m triangular-kernel footprints may still overlap withheld fault traces. It does **not** establish that the collar alone caused the reported score, that H33 detected more geothermal vents, or that any new TIFF will score better. Kernel footprints are not disjoint merely because dot centers are spaced apart; this is why the site treats the explanation as a hypothesis rather than proof.

No defensible claim that a new method beats `0.2778` (or the request's other claimed leaderboard figures) is available without a comparable spatially blocked, whole-segment buffered holdout, feature-alone leakage canaries, and an organizer receipt for live performance. This session could not perform the requested holdout because the protocol stops before feature construction or placement. The shared evaluator/writer pins were not changed, and no private fork or threshold exception was made.

## Next work, in order

1. Obtain an explicit method-lane assignment and an authorized upstream resolution of the saturation contradiction. Do not silently alter the 0.70 threshold or exclude the witness in this checkout.
2. Recover the actual pinned template feature cache plus a complete, current accessible raster registry; verify their hashes and provenance. The current raw-data mirrors alone do not satisfy this requirement.
3. Once the shared gate permits it, preregister H86E-SPBT, derive catalogue-based inputs using only fold-visible faults, withhold whole segments plus buffer, run each feature's leakage canary, and compare paired physical-block confidence intervals against a matched baseline through the shared evaluator.
4. Only after a positive comparable holdout and pre-placement/final uniqueness passes should the separate selector inspect the authenticated weekly quota, nominate an exact SHA, and obtain a submission-page receipt. Never upload audit-only artifacts.
5. Obtain official-source raw data for external candidates before calling them viable; no raw MT grids or 1 m DEM tiles were present in this workspace.

## Sources for manual review

- [Official competition description / format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — no portal scraping was performed.
- [Official competition rules/report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [Official reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [DOE GDR 1391](https://gdr.openei.org/submissions/1391).
- [INGENIOUS project overview](https://gbcge.org/current-projects/ingenious/).

These links identify review sources; this report does not claim each page was freshly verified in this session.

## Concurrent-main integration and SWCON safety correction

After the initial review, `origin/main` advanced with a concurrent SWCON TIFF and a public “OK TO DOWNLOAD AND SUBMIT” page. I preserved the result and audited it rather than treating the parallel session's dotted-only gate as permission to override the shared literal rule.

- The TIFF is SHA-256 `5576b15c1c66dd5353c515201c06572d6e7a854aaa130bd95d167435f6f9374f`. Its local float32/range/grid validator passes, but the candidate consists only of allowed-support dots. The pinned continuous witness is positive throughout allowed support; therefore forward overlap is mathematically 1.0 against it, above 0.70. This is **REGISTRY-MEASUREMENT / deterministic implication**, not HOLDOUT-DTI.
- The SWCON **HOLDOUT-DTI** is 0.0074586 using its stated `gems57 dti_binary`, alpha 0.2, beta 0.8, 300 m triangular kernel, pooled four-quadrant whole-component folds, and 60,988 withheld positives; **95% CI is absent**. The experiment note classifies it as a comparative proxy and records a full-catalogue-derived placement caveat; it is not live-score evidence. The canary is one aggregate-surface AUC, not the required per-feature-alone canary set.
- The source run card's initial `promote` flag applied only to its dotted local subset. I retained that history as `verdict_before_full_registry_review`, changed the current card decision to negative, added [`swcon-protocol-review.json`](../docs/evidence/swcon-protocol-review.json), removed the candidate TIFF/ZIP from public downloads, and quarantined the single TIFF at `evidence/rejected-swcon-e3-37654dots-20261024-zeros.tif`. The page [`docs/swcon-submission.html`](../docs/swcon-submission.html) now clearly says DO NOT SUBMIT and has no TIFF/ZIP download link.
- The SWCON builder now invokes the mandatory shared `require_feasible()` before grid loading or placement. `check_site.py` rejects both “READY TO DOWNLOAD” and “OK TO DOWNLOAD AND SUBMIT” banners in the negative publication state. Added regressions for the builder's pre-placement stop and the SWCON page's negative state.
- Latest release measurement at `2026-10-24T18:34:05Z` still covers the ten registered published legacy TIFFs only and says `DO NOT SUBMIT`; the quarantined SWCON artifact is deliberately outside the downloadable inventory. The public registry scan remains incomplete.
- A first integrated audit/test run was executed concurrently and raced on generated proof timestamps; one site-render assertion consequently saw a stale run card, and a new publication test initially lacked its `Links` import. Both were fixed: the audit/site chain was rerun serially and the missing import added. Final suite: **500 passed, 24 skipped, 4 pending-deprecation warnings, and 41 subtests passed**. `audit_release.py --measure-registry`, generated-site checks, `check_site.py`, `audit.py`, `validate_download.py`, `audit_downloads.py`, ledger, preflight-reproduction checks, registry reproduction, compileall, and `git diff --check` passed. These results verify gates and software, not SWCON's scientific merit or organizer acceptance.
