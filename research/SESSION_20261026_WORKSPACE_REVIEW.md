# GEMSDOE86 workspace review — 2026-10-26

## Decision

**DO NOT SUBMIT any file from this repository. No new TIFF or experiment was created in this review; no weekly slot was used.** The user-supplied request archive is not a lane assignment. No single method paragraph was designated for this session, and the immutable full-support registry witness trips the literal `>0.70` dot-overlap stop for every nonempty prediction raster. The machine release report therefore remains fail-closed.

- Current release audit: [`docs/evidence/release-readiness.json`](../docs/evidence/release-readiness.json) — 46/46 registered research TIFFs pass local format/integrity validation, but `decision = DO NOT SUBMIT`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `selector_run = false`, and `submission_slots_used = 0`.
- Registry remeasurement: [`docs/evidence/all-artifacts-registry.json`](../docs/evidence/all-artifacts-registry.json) and [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json). The restored historical continuous witness has forward overlap `1.0`, exceeding the literal limit `0.70`. This one witness establishes a negative stop, not uniqueness clearance against the complete upstream registry.
- No candidate surface was made; therefore this review has no new surface-correlation or final-dot statistic, HOLDOUT-DTI, confidence interval, prediction raster SHA-256, or leaderboard-score estimate.

## Focus-9 answer and H33 interpretation

The existing Focus-9 summary already covers GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Its best named result is GEMSDOE32 H33 (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) at **0.2778 OWNER-REPORTED**; no submission-page receipt in this repository makes that score ORGANIZER-CONFIRMED. See the [Focus-9 comparison and H33 forensic analysis](SESSION_20261026_H86R_SFG_REVIEW.md) and the [executive summary page](../docs/executive-summary.html#focus9-summary).

The prior pixel analysis describes H33 as a D28/H27-4 lineage refinement: it retained a sparse far-field dot population while pruning 2,545 low-marginal-credit near-catalogue collar dots. Under the supplied metric description, unnecessary predictions cost false-positive mass, so a collar prune can plausibly improve precision while retaining useful coverage. This is a mechanism-based explanation, **not a causal identification**: the historical submissions are not controlled experiments, and the supplied 0.2778 claim has not been independently confirmed from a DrivenData receipt. The user-supplied 0.3195 and 0.4413 leaderboard marks conflict and are unverified here. Do not present either as current official leaderboard truth or promise that a unique candidate will beat H33.

No Focus-9 historical TIFF should be copied into a new submission. The prior forensic report measures high overlap among the scored leaders and identifies duplicate lineages; its score table is a historical comparison, not an upload recommendation. All files in this repository remain audit-only under the current release decision.

## Current workspace input audit (after restoring via the pinned mirror process)

This review restored available inputs using the repository's integrity-checked GitHub mirror tooling. These checks authenticate bytes against project pins; **they do not independently authenticate the bytes as organizer-originated data**.

| Capability | Measured state in this workspace | What it establishes / does not establish |
|---|---|---|
| `training_features.tif` | Present in `data/` and `data/bridge/`; SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`; 418,912,844 bytes | Mirror-pin identity only; not DrivenData provenance |
| `existing_faults.tif` | Present in both locations; SHA-256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`; 425,830 bytes | Mirror-pin identity only |
| `sample_submission.tif` | Present in both locations; SHA-256 `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc`; 1,599,597 bytes | Mirror-pin identity only |
| Native preparation | `scripts/prepare_data.py --manifest .cache/gems_work/prepared_manifest.json` passed its grid/label checks and prepared 19 bands; reported grid `3730×3292`, EPSG:32611, footprint 5,167,373 cells, catalogue 60,988 cells | Local preparation from pinned mirror inputs; live receipt/arrays are in ignored `.cache/gems_work/` and may not be present in a fresh checkout |
| Shared template cache | `SHARED_CACHE_NOT_ESTABLISHED`; no verified shared-template feature/implementation/visible-mask identity contract; recorded lane mmap missing | **Still blocks a compliant holdout experiment**; local native arrays are not a substitute for the required shared cache |
| External inputs | `restore_lane_data.py` verified required external/scored mirror assets against manifest hashes; `verify_band_physics.py` completed | Input diagnostics only; not a holdout, leaderboard score, candidate, or upload clearance |

The current audit command `python scripts/audit_workspace_inputs.py --require-native` exits successfully and reports `native_inputs_available = true`, `native_bands_available = true`, with `preparation.manifest_file = .cache/gems_work/prepared_manifest.json`; its sole blocker is `SHARED_FEATURE_CACHE_NOT_ESTABLISHED`. The live receipt is preferred when present; a malformed live receipt fails closed instead of falling back to the frozen historical `data/prepared_manifest.json`. This preserves the prior session's manifest hash pin while making current array checks auditable. Do not interpret the historical manifest alone as proof of current arrays; use the live audit.

### Band-physics diagnostic (not a score)

`python scripts/verify_band_physics.py` ran after the pinned external data were staged at the paths used by the verifier. Its read-only result is recorded at [`docs/evidence/band-physics-verification-20261024.json`](../docs/evidence/band-physics-verification-20261024.json). For example, the diagnostic Pearson correlation between feature Band 6 (`tc`) and the GeoDAWN total-count raster was `0.99714`; Band 18 vs east gravity derivative was `0.948186`; Band 11 vs south gravity derivative was `0.938102`. These are **input/physics consistency diagnostics**, not DTI values or evidence of predictive lift. The source dataset's official USGS landing page and DOI are linked from the [sources page](../docs/sources.html) and the [USGS GeoDAWN page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).

## Three-pass review

1. **Pass 1 — requirement and status:** Read the standing prompt and repo instructions; checked the current Focus-9 table, H33 explanation, submission guide, prior run card, and release state. Confirmed all historical scores remain owner-reported absent a receipt; found no assigned single-method paragraph in this request; did not spend a slot or create a candidate.
2. **Pass 2 — input, release, and UI/repository checks:** Restored the pin-verified core and lane assets with repository scripts; ran `prepare_data.py` to an ignored live manifest; audited current inputs; ran `audit_release.py --measure-registry` against the immutable witness; ran `build_site.py --check`, `check_site.py`, and `audit_downloads.py`. The result is 46/46 format-valid artifacts but `DO NOT SUBMIT`; native feature arrays are verified locally while the required shared cache remains unestablished. Code review found that the live-input audit inspected only the frozen manifest; it now prefers the current cache receipt, fails closed on a malformed one, and keeps the historical manifest pin intact.
3. **Pass 3 — regression and scope:** Ran the full suite after preparation: **1,102 passed, 23 skipped, 48 warnings, 58 subtests passed**. The warnings are Rasterio `PendingDeprecationWarning` notices about Affine `*` multiplication. Re-ran `audit_workspace_inputs.py --require-native` after data preparation; it exits 0 but still reports the shared-cache blocker. Verified no private template fork, no new experiment, no TIFF, and no weekly slot.

## Irregularities, limitations, and next work

1. **Live preparation receipt drift (fixed in this review).** The current-input audit previously looked only at tracked `data/prepared_manifest.json`, which is pinned by the generated site as historical evidence. Re-running preparation to that path changes the pinned file hash and makes `build_site.py` fail; reverting it then leaves the fresh ignored array bytes uncheckable from the current audit. The audit now prefers `.cache/gems_work/prepared_manifest.json` when present and fails closed if it is invalid, while preserving the historical receipt. New tests cover live-manifest precedence and invalid-live/no-fallback behavior. Use `python scripts/prepare_data.py --manifest .cache/gems_work/prepared_manifest.json` for a fresh local prep.
2. **Blocking literal uniqueness rule.** The full-support witness is positive on every allowed footprint cell, so direct final-dot overlap is 1.0 for any nonempty candidate and exceeds the 0.70 limit. Do not evade this by changing thresholds, redefining the metric privately, or making an empty/degenerate file. Resolve this governance/protocol contradiction through the shared approved process before generating another candidate.
3. **Shared feature cache provenance is still missing.** Native source and prepared arrays have been hash-verified in this workspace, but the run protocol requires a verifiable shared cache and shared holdout/writer tools. Establish that exact identity contract before any new model experiment; do not relabel locally prepared arrays as the template's cached feature stack.
4. **Competition performance is not verified.** Historical focus-site values are OWNER-REPORTED. The 0.3195 and 0.4413 values conflict; no DrivenData leaderboard or submission-page receipt was used. The portal's login and the repository's no-automated-DrivenData rule preclude claiming organizer confirmation here.
5. **Full external registry scan remains incomplete for promotion.** The pinned witness proves failure of the current literal gate, but it does not establish uniqueness against the full upstream fleet. Full registry inventory restoration is mandatory before any like-for-like uniqueness claim; a pass would still not override the witness or authorize a slot.
6. **Next scientific step:** the H86R review's queued detectability-weighted PU proposal is a *proposal*, not today's assigned lane. First obtain a specific lane paragraph consistent with the parallel-run rules, confirm the shared cache, preregister no more than three arms, test every feature alone for leakage, and evaluate with the pinned whole-segment buffered hide/recover evaluator. Stop if its paired evidence or registry checks fail. Do not use a leaderboard projection as a score.
7. **Submission authorization remains separate.** The repository contains a click-to-download archive for research, not a currently approved competition TIFF. The submission guide should continue to say `DO NOT SUBMIT`; live slot selection/quota and organizer acceptance require a separately authorized DrivenData action and receipt.

## Primary sources for review

- [DrivenData DOE GEMS competition and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login-gated; this review did not automate access.
- [NLR / DOE GEMS Prize description and submission guidance (PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN official data landing page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611 reference](https://epsg.io/32611)
- [Repository source register](../docs/sources.html), with the project's existing verification caveats.

These links are provided for provenance/manual review; they do not imply that DrivenData was accessed during this automated review or that any score was independently confirmed.

## Reproduction

From the repository root with the locked Python environment:

```bash
.venv/bin/python scripts/restore_data.py --with-external --include-registry
.venv/bin/python scripts/prepare_data.py --manifest .cache/gems_work/prepared_manifest.json
.venv/bin/python scripts/restore_lane_data.py
.venv/bin/python scripts/verify_band_physics.py
.venv/bin/python scripts/audit_workspace_inputs.py --require-native
.venv/bin/python scripts/audit_release.py --measure-registry
.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
.venv/bin/python scripts/audit_downloads.py
.venv/bin/pytest -q
```

All commands above are local project tooling. The restore commands retrieve project-mirrored bytes and verify the recorded pins; they do not automate the DrivenData portal, establish organizer provenance, run a new experiment, or grant permission to submit.
