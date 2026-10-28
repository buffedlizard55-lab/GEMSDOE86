# Checkout review — 2026-10-28

**Branch:** `arena/8238825b-gemsdoe86` · **Base:** `02369c9` · **Disposition:** **DO NOT SUBMIT; no candidate generated; no experiment or slot used.** This is a review of the current checkout, not a new geological lane or a replacement for the historical Focus-9 audit.

## Scope and findings

The repository already contains the requested Focus-9 work: `research/SESSION_20261028_REVIEW.md`, `docs/nine-sites.html`, the generated executive summary, `registry/prior_scores.csv`, dated pairwise-raster evidence, and `registry/focus9_novel_hypotheses_20261028.json`. These identify the reported GEMSDOE32 H33 score (0.2778) and the other listed scores as **OWNER-REPORTED**, not organizer-confirmed; no submission receipt is supplied. They do not establish a current leader-board score, causal improvement from H33's pruning, full-registry uniqueness, or permission to submit. Historical owner TIFFs are for forensic download only. Do not upload them.

The most important fresh checkout finding is that prior blocker evidence is not reproducible from the files currently present:

- `python scripts/protocol_preflight.py` failed before measurement because `data/bridge/registry/dense-witness.tif` is absent. It did not establish a fresh overlap result. The historical `docs/evidence/protocol-preflight.json` and earlier reports remain dated measurements; do not present them as freshly rerun in this checkout.
- `.venv/bin/python scripts/audit_workspace_inputs.py --require-native` exited 1 and reported `NATIVE_INPUTS_MISSING_OR_INVALID`, `NATIVE_PREPARATION_NOT_AVAILABLE`, and `SHARED_FEATURE_CACHE_NOT_ESTABLISHED`. The competition training feature TIFF and cached native band arrays are absent. Existing-fault and sample-submission bridge files pass their recorded hash checks.
- `python scripts/check_site.py` passed: links, registered TIFF/ZIP integrity and negative-state safety. This is a local publication/format check, not scientific clearance, a uniqueness pass, or portal acceptance.
- Focused regression tests passed: `.venv/bin/python -m pytest -q tests/test_focus9_summary.py tests/test_nine_site_truthfulness.py tests/test_protocol.py tests/test_current_review.py` → **45 passed**.

Consequently, the repository's standing instruction remains conservative: no candidate generation, no experiment, no threshold edits, and no weekly slot. The missing witness means the old literal-overlap stop could not be remeasured here; it does **not** nullify the recorded historical stop or authorize bypassing it. Restore the exact pinned witness and the full-registry inputs using the repository's documented, hash-verifying restoration workflow before attempting any measurement. Restore the native competition feature TIFF and establish the pinned shared feature cache before any holdout work. Any data availability or authorization constraint must be resolved without inventing receipt evidence or changing the protocol privately.

## Review against the request

1. **Nine-site summary:** present, with clear owner-claim labeling and forensic-download / do-not-submit status.
2. **H33 explanation:** documented as a plausible collar-pruning mechanism, explicitly not causal proof; do not treat the reported 0.0070 difference as controlled evidence.
3. **Unique candidate TIFF:** intentionally not produced. Current data/protocol prerequisites are unavailable, and current project policy blocks generating one. No file in this review is okay to submit.
4. **Untried hypotheses:** three screened proposals are recorded, with named layers, physical signatures, mimics, distinctions, costs and explicit missing-source availability checks. They are proposed only, not validated or numerically ranked by DTI.
5. **Official-source claims:** the hypothesis registry correctly marks the USGS/ComCat/NGMDB acquisition checks as not performed or not currently obtainable; it does not imply source bytes were fetched.
6. **Submission score estimate:** no defensible score estimate can be calculated from this checkout. The cited historical values are owner-reported; projections are not scores.
7. **User-requested PR and merge:** no PR or merge is attempted by this review. The branch has no new validated candidate or code change to propose, and merging speculative/unverified submission work would contradict the project's fail-closed review policy. If this review itself is accepted as a documentation-only change, it should be proposed through the current Arena branch workflow; it must not be merged to `main` without the normal review/authorization process.

## Three review passes

- **Pass 1 — inventory:** read `PROMPT.md`, `AGENTS.md`, and `README.md`; mapped the current pages, scripts, evidence, and Focus-9 records. Confirmed the user-scoped sites and latest status records.
- **Pass 2 — reproduce gates:** installed the locked Python requirements in the ignored local `.venv`; checked page integrity and focused tests; attempted the required native-input and protocol preflights. The protocol preflight is blocked by the absent pinned witness; the native-input audit fails closed on absent training data/cache.
- **Pass 3 — reconcile and conclude:** separated historical measurement from fresh measurement, score claims from receipts, and download permission from upload authorization. No contradictions were resolved by assumption; candidate/experiment/submission gates remain closed.

## Evidence card (review, not experiment)

```json
{
  "hypothesis": null,
  "mechanism": null,
  "named_non_fault_mimic": null,
  "holdout_dti": {
    "status": "NOT_RUN",
    "evaluator_version": null,
    "withheld_positives": null,
    "ci95": null
  },
  "registry_comparison": {
    "status": "NOT_RERUN",
    "reason": "Pinned dense witness TIFF absent; historical registry evidence is not a fresh measurement."
  },
  "raster_sha256": null,
  "validator_output": {
    "candidate_generated": false,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "site_integrity_check": "PASS; does not validate a new candidate"
  },
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative",
  "safe_to_download": false,
  "safe_to_submit": false,
  "weekly_slot_used": false
}
```

## Limitations / next work

- Restore the exact hash-pinned registry witness and complete registry bytes, then rerun the protocol and registry audits as measurements; do not silently substitute or relax thresholds.
- Obtain the official, login-authorized competition feature TIFF and run the repository preparation workflow; verify its hash/grid and establish the shared-template cache identity.
- Recheck all nine owner-hosted artifacts and their current owner receipts only through permitted sources; keep organizer confirmation absent until an actual submission-page receipt is recorded.
- Once data and protocol gates are legitimately resolved and a lane is explicitly authorized, preregister a bounded holdout test using the required shared evaluator, buffered whole-segment hide-and-recover, visible-only catalogue features and per-feature leakage canaries. Run at most three experiments/two hours, retain negative results, and do not use a submission slot until a separate selector and organizer quota check authorize it.
- A new candidate must pass the complete surface and final-dot registry checks, full-grid/value/finite validator, independent weekly-slot selector, and competition portal format requirements. A local format pass alone is never permission to submit.
