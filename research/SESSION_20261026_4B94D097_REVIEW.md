# Independent repository review — session `4b94d097` (2026-10-26)

## Decision at this checkout

**DO NOT SUBMIT any file from this repository to a live DrivenData slot.** This is a governance and registry decision, not a claim that the GeoTIFF is malformed. No experiment or submission slot was used in this review. The current checkout contains the prior H86Q-BFRA research TIFF, but does not contain the source inputs or the shared feature cache needed to reproduce its scientific experiment.

- Prior research artifact: [`gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif`](../docs/downloads/gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif); SHA-256 `b9cd35e51880fa0f9b4c47962b4544e93b7c2929e269a8d7595bfbbd444c54a9`.
- Its recorded local format checks pass (single band; EPSG:32611; 3730×3292; sample geotransform; finite values in [0,1]). This addresses the portal's stated range/format rejection class, **not** permission to submit.
- Its saved H86Q-BFRA `HOLDOUT-DTI` is `0.0734 [0.0604, 0.0865]` on `gems57-pooled-hide-v2`, 11,321 withheld positives. This is not an organizer score or a projection of leaderboard performance. See the [run card](../docs/evidence/h86q-bfra-run-card.json).
- The saved Focus-9 report marks historical submission scores as owner-reported, not organizer receipts. Its analysis attributes H33's reported lead plausibly to reducing redundant near-catalogue dots while preserving far-field coverage; this is a mechanism-based explanation, not causal proof. See the [Focus-9 report](SESSION_20261026_H86Q_BFRA_REVIEW.md#1-executive-summary-across-all-9-focus-9-sites-gemsdoe24-25-27-28-30-31-32-33-36) and [executive summary page](../docs/executive-summary.html#focus9-summary).
- The current fail-closed release audit remeasured 45 published research TIFFs and returned `DO NOT SUBMIT`; the inherited full-support witness has a recorded forward overlap of `1.0`, above the `0.70` stop. See [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json) and `python scripts/audit_release.py` output. This witness is a literal gate stop; local comparisons against discrete dot rasters do not override it.

## Current-checkout input audit

`python scripts/audit_workspace_inputs.py` completed read-only inspection at `2026-10-26T16:07:39Z`:

| Input/capability | Current observation | Consequence |
|---|---|---|
| `data/bridge/existing_faults.tif` | Present; SHA-256 matches pin `7ba308cc…` | Available locally |
| `data/bridge/sample_submission.tif` | Present; SHA-256 matches pin `2176d08e…` | Available locally |
| `training_features.tif` | Missing from both `data/` and `data/bridge/` | Cannot reproduce feature extraction or training |
| Prepared arrays listed by `data/prepared_manifest.json` | Missing under ignored `.cache/gems_work/bands/` | Historical preparation manifest is stale/incomplete in this checkout |
| Shared template feature cache | Not established; `.cache/` lane mmap is missing and receipt lacks the shared-cache identity contract | Do not claim template cache reuse or run scientific candidate generation |
| Readiness flags | `safe_to_submit=false`, `approved_for_weekly_slot=false` | No upload authorization |

The prior `data/prepared_manifest.json` is a historical receipt, not evidence that those current files exist. The local integrity pins authenticate mirrored bytes, not organizer origin. Automated access to DrivenData must remain disabled per `AGENTS.md`; missing source data must be restored only by the documented, hash-checked route and must not be represented as freshly available before the audit passes.

## Review of the requested Focus-9 and H33 analysis

The existing Rev-2 Focus-9 work already covers all nine requested sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`), ranks their reported best entries, marks the score claims as `OWNER-REPORTED`, and distinguishes the historical leader from an upload recommendation. H33 (`GEMSDOE32`, `0.2778` in the supplied claim set) is therefore the best **reported historical result in this cohort**, not an approved file or a guaranteed path to a higher score. The user-supplied `0.3195` and `0.4413` marks are conflicting external claims without a receipt in this checkout and are not adopted as verified leaderboard facts.

The repository already includes the prior session's four preregistered hypotheses, candidate ranking, H86Q-BFRA holdout evaluation, leakage-canary measurements, registry checks, run card, site pages, TIFF writer validation, and a three-pass review. These are audited as historical evidence; this review does not rerun the lane or choose a weekly slot. The reported H86Q-BFRA pure-blind `SGMC-PROXY-DTI` diagnostic is not a competition score and must not be compared as one.

## Three-pass review performed

1. **Requirement/evidence pass:** Read `AGENTS.md`, `PROMPT.md`, `README.md`, the Rev-2 owner request, the H86Q-BFRA session review, executive summary, and run card. Confirmed the Focus-9 table and H33 forensic discussion exist and that the top-level status says `DO NOT SUBMIT`.
2. **Operational/format pass:** Installed the pinned test environment into ignored `.venv/`; ran `scripts/audit_workspace_inputs.py`, `scripts/audit_release.py`, `scripts/build_site.py --check`, and `scripts/check_site.py`. Release audit: `audit_ok=true`, 45/45 registered artifacts locally valid, final artifacts remeasured, decision `DO NOT SUBMIT`. Site/evidence checks pass. Workspace audit reveals absent native feature raster, absent prepared cache arrays, and no established shared feature cache.
3. **Regression pass:** Ran the complete test suite: **1,091 passed, 24 skipped, 48 warnings, 58 subtests passed**. Warnings were Rasterio `PendingDeprecationWarning` about Affine matrix `*` multiplication; no test failures. Verified no tracked code or generated-site drift from the checks.

## Recommended next work (not performed in this review)

1. Restore the missing pinned `training_features.tif` via the repository's approved hash-verified process, then rerun `audit_workspace_inputs.py --require-native`; do not rely on the historical preparation receipt.
2. Restore and authenticate the shared template cache/identity contract. If that cannot be proven, stop rather than privately rebuild or fork the required shared stack.
3. Only after inputs/cache are valid, let the next explicitly assigned lane preregister up to the three-experiment budget, use the pinned holdout/evaluator/writer, run each-feature leakage canaries, then check surface and final dots against the full registry. Keep the immutable full-support witness as a hard stop unless governance resolves it through the approved shared process.
4. Preserve the site-wide and repository-wide `DO NOT SUBMIT` state until the full scientific, registry, format, and separate weekly-slot authorization gates pass. A local TIFF format pass alone never authorizes upload.

## Reproduction commands

From the repo root, in a virtual environment with the pinned requirements:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/audit_workspace_inputs.py
.venv/bin/python scripts/audit_release.py
.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
.venv/bin/pytest -q
```
