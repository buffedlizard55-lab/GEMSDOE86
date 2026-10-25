# Final repository review and verification — 2026-10-25

## Decision

**NEGATIVE / DO NOT SUBMIT.** This recheck produced no experiment, candidate surface, raster, score, or slot selection. It did not upload or merge anything. The highest-priority request for a newly generated unique submission is **not fulfilled**, because the project’s binding preflight and review record prohibit candidate generation under the current unresolved lane/cache/registry conditions. Existing downloadable TIFFs are explicitly audit/research artifacts, not upload-authorized submissions.

This report is an additional environment-and-quality recheck of the detailed [independent repository review](SESSION_20261025_ARENA_REVIEW.md), not a replacement for it and not new scientific evidence.

## Three review passes

### Pass 1 — requirement and safety trace

- Read `PROMPT.md`, `README.md`, `AGENTS.md`, the current request archive, and the current review/evidence state.
- Confirmed the explicit method paragraph needed to bind this parallel run is absent. The four proposed geological hypotheses in `registry/h86g_hypotheses.json` are queued as proposals, not an authorized experiment.
- Confirmed the existing site and README correctly say **DO NOT SUBMIT** / selector pending, and distinguish local format validation and HOLDOUT-DTI from organizer confirmation.
- Confirmed repository policy forbids automated DrivenData portal scraping and requires the shared cache, preflight, holdout, canary, uniqueness, and writer gates. This recheck did not attempt to bypass them.

### Pass 2 — executable checks

The base interpreter initially lacked project dependencies (`numpy` and `pytest`). Installed the exact repository lock into ignored `.venv/`; no tracked dependency or lockfile was changed. Then ran:

- `.venv/bin/pytest -q` — **839 passed, 24 skipped, 41 subtests passed**, with 42 rasterio pending-deprecation warnings; runtime 247.53 s.
- `.venv/bin/python scripts/build_site.py --check` — **PASS**, evidence-generated site; one H86G-EDTI selector-review download, no upload-authorized file.
- `.venv/bin/python scripts/check_site.py` — **PASS**, links / registered TIFF and ZIP integrity / negative-state safety; explicitly not scientific clearance.
- `.venv/bin/python scripts/audit_release.py` — **audit_ok=true**, 21/21 artifacts locally valid and remeasured; zero experiments and zero submission slots used; decision remains **DO NOT SUBMIT**.

The test suite validates implementation and evidence gates, not leaderboard performance or organizer acceptance. The skipped tests and deprecation warnings are retained as review notes; no failed test is being concealed.

### Pass 3 — edge cases, final decision, and follow-up

- Read-only audit results are not treated as full uniqueness clearance: the detailed review records incomplete current registry availability, incompatible grids, a literal full-support witness stop, and failure of the chance-overlap gate.
- No score is asserted here. Historical numeric metrics remain labeled by their evidence classes in the referenced evidence/run cards. No score projection or leaderboard claim is derived from a local test.
- No TIFF was created, rewritten, or represented as safe to submit. This is the compliant outcome under the current repository policy; do not infer that test success authorizes a submission.
- No source code or generated website artifact required a fix in this verification pass. The substantive blockers and prioritized scientific hypotheses remain in the linked detailed review.

## Limitations and next actions

1. Bind one concrete method paragraph/lane before starting a candidate experiment.
2. Restore and verify the actual template-cached feature stack; a raw/mirrored input raster or old prepared manifest is not equivalent.
3. Restore a complete, current, same-grid registry and resolve the incompatible entries through the shared registry tooling; do not privately weaken thresholds.
4. Have the project owner resolve the literal overlap/preflight conflict under the shared protocol; do not add a local bypass.
5. Only after those gates are genuinely resolved, preregister a maximum-three-experiment holdout plan, run feature-alone leakage canaries and whole-segment buffered hide-and-recover evaluation, and report HOLDOUT-DTI with evaluator, withheld-positive count, and 95% CI.
6. A scientific promote verdict still does not authorize a weekly slot. Any organizer confirmation/quota must come from an authorized human-browser receipt. Do not automate access to the DrivenData portal.

## Run card

```json
{
  "hypothesis": "No new geological hypothesis tested in this recheck; the previously ranked H86G-CSPA proposal remains unrun.",
  "mechanism": "Repository verification only: full tests, generated-site consistency, release artifact audit; no feature computation or raster placement.",
  "named_non_fault_process_that_could_mimic_it": "Not applicable; no geophysical candidate was evaluated.",
  "holdout_dti": null,
  "correlation_overlap_vs_registry": "No new candidate exists; no candidate uniqueness claim. Existing detailed review documents incomplete registry coverage and unresolved hard stops.",
  "raster_sha256": null,
  "validator_output": "No candidate raster generated. Existing release audit: 21/21 inherited artifacts locally valid; does not establish scientific/uniqueness clearance. Site checks PASS.",
  "submission_name": null,
  "submission_note": "No new submission. Existing downloads remain audit-only; DO NOT SUBMIT.",
  "verdict": "negative"
}
```
