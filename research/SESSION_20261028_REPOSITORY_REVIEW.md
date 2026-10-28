# Repository review — 2026-10-28

## Decision

**NEGATIVE — no candidate is approved for download/submission or for a weekly slot.** This was a three-pass repository and evidence review, not a model experiment. No candidate TIFF was generated, no experiment was run, and no submission slot was used.

This review separates software validity, input readiness, scientific validation, uniqueness, and organizer authorization. Passing any one does not imply the others.

## Executive summary

- The nine-site audit already present in [`docs/nine-sites.html`](../docs/nine-sites.html) identifies GEMSDOE32 H33 as the highest *owner-reported* Focus-9 result at 0.2778. Its source claims are not organizer-confirmed; the repository records no submission-page receipt for them.
- In that audit's measured cohort, all 72 ordered pairs exceed the 0.70 dot-overlap threshold (minimum reported overlap 0.867). Thus none of the nine leading files is unique relative to the other eight. See the site's per-file names, local format audit, and hashes before relying on owner naming.
- Current local validation is strong for software and shipped artifacts: the full test suite passed, the generated site checks passed, and the release audit remeasured all 49 registered TIFFs. These are format/integrity results, **not** score evidence or submission authorization.
- This checkout cannot run the requested like-for-like holdout experiment: `training_features.tif`, all prepared feature arrays, and the verified shared feature cache are absent. The registry input audit found byte coverage for only 74 of 729 indexed raster records, so complete-registry uniqueness cannot be established either.
- A pinned historical dense witness was restored from the repository's already-pinned public GitHub blob and remeasured. Under the repository's **literal** `finite prediction > 0` support reading, it covers every allowed pixel and implies overlap 1.0 for any nonempty candidate. This is a hard stop for that literal reading. The repo also documents a representation-aware interpretation for continuous surfaces, but it does not waive the need to check the candidate surface and final dots against the full registry; that check is not currently possible.

## Pass 1 — request, scope, and repository inventory

Read `README.md`, the complete standing protocol in `PROMPT.md`, `AGENTS.md`, the latest nine-site review, and the existing current-input and release-gate code. The standing request has no assigned method paragraph. Its own rule says not to fit/place a candidate without an assigned lane and to stop on unresolved duplication.

The repository already contains the expected safety components: a holdout/evaluator and writer under the shared vendored template, preregistrations and run cards, a nine-site executive page, a registry ledger, format validators, a release audit, site checks, and a large regression suite. I found no reason to create a private evaluator/writer fork or invent an alternative score estimator.

### Focus-9 leaders (owner-reported estimates; not organizer-confirmed)

| Site | Highest listed file | Reported estimate | Unique vs other eight? |
|---|---|---:|---|
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | No |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | No |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f` | 0.2710 | No |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1` | 0.2708 | No |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | No |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89` | 0.2600 | No |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | No |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1` | 0.2477 | No |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1` | 0.2449 | No |

The values above are copied as **OWNER-REPORTED** in the repository's prior-score ledger; they are not predictions, holdout results, or **ORGANIZER-CONFIRMED** scores. “No” is the measured uniqueness result in the prior nine-site audit, not a statement that these files are byte-identical.

The H33 forensic explanation in the existing report is appropriately framed as hypotheses, not causation: it is a 37,654-dot derivative of a parent with a collar removed; that may affect precision under the competition's catalogue-disjoint objective, but the archived catalogue-hide holdout ranks it poorly and cannot prove a live leaderboard mechanism. The only confirmed live score evidence allowed by project policy would be a submission-page receipt; none was found.

## Pass 2 — automated implementation and artifact checks

Commands and observed outcomes in this checkout:

| Check | Result | Interpretation |
|---|---|---|
| `.venv/bin/pytest -q` | **PASS** — first-pass review: 1,141 passed, 24 skipped, 58 subtests; after merging the independent nine-site truthfulness corrections: 1,143 passed, 24 skipped, 58 subtests; 48 warnings | Regression suite passes on the final merged tree. Warnings are rasterio `PendingDeprecationWarning`s for affine `*` multiplication. |
| `scripts/audit_release.py` | **PASS** — `audit_ok=true`, 49 artifacts remeasured, 49 locally valid, decision `DO NOT SUBMIT` | Local format/integrity only; release audit explicitly does not authorize upload. |
| `scripts/build_site.py --check` | **PASS** | Generated site matches evidence inputs. |
| `scripts/check_site.py` | **PASS** | Link and registered TIFF/ZIP integrity/safety checks pass; not scientific clearance. |
| `scripts/build_review_card.py --check` | **PASS** | Frozen review evidence is internally consistent. |
| `scripts/audit_downloads.py` | **PASS** — 49 research TIFFs and receipts revalidated | Research artifacts only; no selector decision. |
| `git diff --check` | **PASS** | No whitespace errors. |

The clean initial checkout had no system `numpy`/`pytest`; I installed the repository's pinned `requirements-lock.txt` into ignored `.venv/` before testing. No dependency files were changed.

## Pass 3 — blockers, protocol measurement, and final decision

### Live inputs

`audit_workspace_inputs.py` completed inspection but found:

- `training_features.tif`: missing from both `data/` and `data/bridge/`.
- Prepared native feature arrays: missing; no current prepared band stack.
- Shared template feature cache: **not established** (missing cache and no verifiable shared-cache identity receipt).
- `existing_faults.tif` and `sample_submission.tif`: present in `data/bridge/` and hash-verified against repository pins. This does not recover the missing feature raster or shared cache.

Accordingly, no compliant new feature engineering or hide-and-recover HOLDOUT-DTI could be computed in this checkout. The audit also records `safe_to_submit=false` and `approved_for_weekly_slot=false`.

### Registry completeness and uniqueness

- `audit_registry_inputs.py` measured **74 byte-verified raster files out of 729 indexed records**, `byte_coverage_complete=false`; the measured 74 were grid-compatible, but their values were not audited and the measured subset does not establish complete coverage or uniqueness. Command exit status was 1, as expected for incomplete coverage. The time-stamped copy is [`docs/evidence/registry-input-grid-review-20261028.json`](../docs/evidence/registry-input-grid-review-20261028.json). The historical `...20261025.json` report was preserved unchanged.
- The pinned witness was fetched only from its exact Git blob pin and SHA-256/size verified: `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`, 25,065,181 bytes. `protocol_preflight.py` then measured `positive_pixels=5,167,373`, `allowed_pixels=5,106,385`, and `uncovered_allowed_pixels=0`; its literal support result is `universal_overlap_blocker=true` and overlap limit 0. The refreshed measurement is [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json).

Refreshing this proof updates its content hash and temporarily makes [`all-artifacts-registry.json`](../docs/evidence/all-artifacts-registry.json)'s final-dot proof binding stale. The first downstream release/site audit correctly failed closed with `Final-dot measurements have a stale witness/proof binding`. I then ran the required `audit_release.py --measure-registry`, which remeasured all 49 final artifacts against the refreshed proof; the release audit and generated-site checks now pass. This is an important operational order: **if protocol evidence is refreshed, remeasure final-dot registry evidence before rebuilding/checking the site**.
- Scope caveat: this is a continuous probability surface, not necessarily a dot field. The user protocol's dot-overlap test should not be misrepresented as a like-for-like result for a continuous surface. The repository's PA-86-01/AGENTS.md procedure permits representation-aware comparison only when rank-correlation is measured for every registry raster and dot overlap is checked against every dot-field raster on the surface before placement and again on final dots. The full present registry is incomplete, so that alternative path cannot clear a candidate here. No threshold has been changed or exemption granted.

### Why no new hypotheses or TIFF were emitted

The request asks for hypotheses that have not been tried, ranked by expected gain/cost, then for the top one to beat a comparable holdout best before a slot is considered. In this checkout, (1) no method paragraph is assigned, (2) the shared feature stack needed for the specified holdout is absent, (3) the registry inventory is incomplete, and (4) the literal support gate blocks every nonempty output under its current interpretation. Ranking speculative proposals as “untried” or assigning them expected score gains without a complete code/data audit and reproducible holdout would be an unsupported claim. Therefore no candidate was constructed and the experiment budget was not spent. The prior H87-FCB candidate remains the documented negative: its local format pass does not override the previously measured local-uniqueness failures or its unmeasured full-registry clearance.

## Findings and recommended order of work

1. **Do not download or submit any current project TIFF.** GEMSDOE32 H33 is the highest *reported* Focus-9 item but duplicates the others by the repo's measured 3-px test; our latest candidate evidence is also negative. There is no approved file and no organizer-confirmed estimated score.
2. **Restore the exact pinned training feature raster**, verify its SHA/size, and run `scripts/prepare_data.py`. Do not describe raw TIFF restoration or historical manifests as the shared cached feature stack; establish the actual shared-template identity before reusing it.
3. **Restore the missing registry inventory using its pinned source/index**, then rerun the grid/byte audit and representation-aware checks. A partial registry cannot certify uniqueness.
4. **Select and preregister one lane before candidate construction.** First map each proposed layer/transform against existing modules and preregistrations, run each feature alone as a leakage canary, use whole-segment buffered hide-and-recover with visible-only catalogue features and exact masking, and compare against a like-for-like current holdout baseline with paired uncertainty. Respect the three-experiment/two-hour limit.
5. **Only after scientific and uniqueness gates pass**, build with the shared writer, validate single band, CRS, shape, affine transform, finite in-footprint `[0,1]` values, name/note length, and final-dot uniqueness. Weekly-slot selection and organizer confirmation remain separate and cannot be automated without a valid authenticated portal receipt.
6. Keep the executive page's explicit no-download/no-submit status visible. The current repo already provides Focus-9 tables, provenance links, and submission instructions; do not make a research TIFF appear authorized merely because a button can download it.

## Trusted links for manual review

- [Competition overview and problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (login may be required for data/submission pages).
- [DrivenData competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/).
- [Official DOE/NREL GEMS report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [Official USGS GeoDAWN airborne survey data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [INGENIOUS project information](https://gbcge.org/current-projects/ingenious/).
- [Competition reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [Repository Focus-9 site audit](../docs/nine-sites.html), [submission guide](../docs/executive-summary.html), [current release decision](../docs/evidence/release-readiness.json), [input integrity code and evidence](../scripts/audit_workspace_inputs.py), and [irregularity ledger](../IRREGULARITIES.md).

## Three-pass run card

```json
{
  "hypothesis": "No assigned experimental lane; repository/input readiness review only",
  "mechanism": "No candidate mechanism tested",
  "named_non_fault_process_that_could_mimic_it": "Not tested; no candidate or feature surface constructed",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "NOT_RUN_MISSING_NATIVE_FEATURES_AND_SHARED_CACHE"
  },
  "correlation_overlap_vs_registry": {
    "candidate_surface": "NOT_MEASURED",
    "final_dots": "NOT_MEASURED",
    "registry_coverage": "74/729 byte-verified in current audit; incomplete",
    "literal_witness_support_overlap": 1.0,
    "literal_witness_note": "One hash-verified continuous surface covers all allowed pixels under finite-value-greater-than-zero support; this is not a like-for-like dot-field comparison."
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": false,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "note": "Existing release audit: 49/49 locally format/integrity valid; none approved for submission."
  },
  "submission_name": null,
  "submission_note": "No new candidate; no weekly slot used; do not submit an existing audit TIFF.",
  "experiments_run": 0,
  "submission_slots_used": 0,
  "verdict": "negative",
  "safe_to_submit": false,
  "approved_for_weekly_slot": false
}
```
