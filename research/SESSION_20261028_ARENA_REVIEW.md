# Repository review and next-step decision — 2026-10-28

**Branch:** `arena/785b85a2-gemsdoe86` · **Disposition:** **DO NOT SUBMIT; no candidate generated; no experiment run; no weekly slot used.** This is a repository/readiness review, not a new scientific result.

## Executive finding

The repository already contains the requested Focus-9 executive material, historical submission instructions, evidence ledgers, a machine-readable feed, candidate research register, TIFF format auditing, and fail-closed publication checks. No current artifact is cleared for upload. In particular, do not interpret an owner-reported leaderboard figure, local TIFF validation, or an audit-download link as organizer confirmation or submission approval.

### Focus-9 reported champions (not organizer-confirmed)

The scores below are `OWNER-REPORTED` claims recorded in the repo, not `ORGANIZER-CONFIRMED` receipts. The byte-level site comparison found each champion over the unchanged 70% directed 3-px overlap stop against at least one of the other eight. These links are historical forensic files and must not be submitted.

| Site | Best reported artifact | Reported score | Uniqueness result within nine-site comparison | Decision |
|---|---|---:|---|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5 | 0.2477 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE25 | dotted-h19-5-d2-8 | 0.2600 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5 | 0.2449 OWNER-REPORTED | Fail, max directed overlap 98.02% | Do not submit |
| GEMSDOE28 | h36-1-rung30-blind-r1 | 0.2710 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE30 | d28-poisson300m-offcat-44090 | 0.2600 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE31 | h27-4-solo-d28 | 0.2708 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE32 | h33-h33-2-b2 | 0.2778 OWNER-REPORTED | Fail, max directed overlap 100.00% | Do not submit |
| GEMSDOE33 | h33d-analog-tip-stepover-r30 | 0.2632 OWNER-REPORTED | Fail, max directed overlap 99.71% | Do not submit |
| GEMSDOE36 | anderson-geothermal-pinn-38854 | 0.2750 OWNER-REPORTED | Fail, max directed overlap 97.58% | Do not submit |

Source of exact audited paths, aliases, method, and pairwise measurements: [`docs/evidence/nine-site-audit-20261027.json`](../docs/evidence/nine-site-audit-20261027.json) and [`research/SESSION_20261028_REVIEW.md`](SESSION_20261028_REVIEW.md). The nine-site audit does not establish uniqueness against the full registry.

### H33 claim: what can and cannot be inferred

GEMSDOE32 H33 is the highest Focus-9 owner-reported claim at 0.2778. Repo forensics describe it as a pruned H19-5-family field: it removes 2,545 near-catalogue collar dots from its parent while retaining much of the far-field pattern. This is consistent with a plausible precision/coverage trade-off under an asymmetric DTI objective, but does not demonstrate that pruning caused the claimed score increase. There is no organizer receipt or controlled rerun establishing causality; the score cannot be projected from these file comparisons.

## Gate evidence and why requested experiments cannot be run

- The pinned protocol witness hash is `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`. The recorded preflight reports 5,106,385 allowed pixels and zero uncovered allowed pixels. Under the frozen literal rule (finite prediction `>0` support), every non-empty candidate has forward overlap 1.0, exceeding the unchanged 0.70 stop. Machine state: `STOP_LITERAL_OVERLAP_UNSATISFIABLE`; see [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json). This is a blocking result, not uniqueness clearance.
- A separate registry-input audit has byte coverage for 74/729 indexed rasters; the measured records were grid-compatible, but values/candidate similarity were not audited. Registry completeness and full-registry uniqueness are not established.
- Competition `training_features.tif`, prepared native feature arrays, and the pinned shared feature cache are absent in this checkout. Thus the requested shared-stack buffered hide-and-recover HOLDOUT-DTI, feature-alone leakage canaries, and candidate validation cannot be honestly recomputed here.
- Current owner-reported scores and historical model figures are not freshly re-scored. The claim 0.3195, 0.4413, and other leaderboard totals cited in the prompt were not authenticated from organizer receipts in this run.
- These constraints make it inappropriate to choose a purported best submission, fabricate a score estimate, or generate a TIFF that would be misleadingly represented as safe to upload.

## Candidate research queue (proposal only; none validated)

The repository's [`registry/focus9_novel_hypotheses_20261028.json`](../registry/focus9_novel_hypotheses_20261028.json) records three screened, unexecuted proposals. Cost/gain are qualitative hypotheses only, not score projections.

| Rank | Hypothesis and layers | Signature / rationale | Key mimic | Cost and data status | Decision |
|---|---|---|---|---|---|
| 1 | Dated Lake Lahontan shoreline displacement; age-tagged shoreline geometry plus native elevation/slope and optional gravity/depth context | Repeated cross-bench step or tilt of a same-age paleoshoreline, potentially exposing displacement where a modern scarp is subdued | Wave-cut bench/facies changes, age miscorrelation, compaction, erosion, volcanic margins | High; exact official NGMDB map/coverage and raw 1 m DEM tiles are absent, and USGS access was outside sandbox egress | Not viable now |
| 2 | Time-ordered earthquake-sequence migration; official USGS ComCat event time/depth/location/magnitude with native strain/geophysics context | Quality-filtered hypocenter migration along a coherent buried plane, not static event density | Geothermal injection swarms, mining/blasts, volcanic swarms, mapped-fault aftershocks, catalog completeness changes | Very high; no local time series and official endpoint could not be queried | Not viable now |
| 3 | Age-tagged stratigraphic-contact displacement graph; attributed geologic-unit contacts plus native gravity, RTP, basement-depth and conductivity | Several matched contacts terminate/step consistently across a corridor with independent subsurface support | Intrusive/volcanic contacts, facies boundaries, alluvial cover, map joins, georeferencing error | High; exact free map product, polygons, scale, and coverage are not verified or present | Not viable now |

The novelty statements are repository-screen results, not proof that no one has ever tried the ideas. No external-data hypothesis is promoted as viable until the exact public source, AOI coverage, bytes, metadata, and reproducible retrieval are checked. There is no assigned method lane. The requested “top candidate” therefore has not been validated against holdout.

## Three-pass review performed

1. **Scope and evidence review:** checked the standing brief, active stop state, site comparison, hypothesis register, current Pages status, and submission instruction page. Confirmed the website emphasizes DO NOT SUBMIT and labels research downloads as audit only.
2. **Implementation/regression review:** installed the pinned lockfile into ignored `.venv`; ran `.venv/bin/pytest -q` → **1,147 passed, 24 skipped, 58 subtests passed**, 48 rasterio affine deprecation warnings. Ran `build_review_card.py --check`, `build_site.py --check`, `check_site.py`, and `audit_downloads.py` → all PASS. These establish reproducibility/integrity checks, not scientific clearance or portal acceptance.
3. **Requirement/edge-case review:** verified no new experiment or TIFF was created, no submission slot was used, no score was relabeled organizer-confirmed, and missing inputs plus incomplete registry prevent a valid high-score comparison. `git diff --check` passed. The appropriate result is a negative release decision.

## Next work, ordered to maximize value

1. Restore the exact competition feature file through the authenticated competition download path or a verifiable permitted mirror; validate hash/metadata and prepare it using repository scripts. Do not claim the shared cache exists until its identity receipt is established.
2. Resolve the literal full-support stop via an authorized protocol interpretation/registry audit; do not silently change the 0.70 threshold or ignore the witness. Obtain complete registry raster bytes, then re-run representation-aware correlation and dot overlap both before placement and on final dots.
3. Assign one method lane and preregister it; only then run the common hide-and-recover evaluator, feature-alone AUC leakage canaries, paired confidence intervals, and capped experiment plan using visible-only catalogue-derived features and exact masking.
4. Promote only after holdout beats the matched best with positive paired uncertainty and all uniqueness gates pass. Generate with the shared writer, validate CRS/shape/transform, `[0,1]`, footprint NaN policy, hash, name/note, and only then separately consider an authorized weekly slot.
5. Preserve clear “NO FILE AUTHORIZED — DO NOT SUBMIT” status until a valid candidate and independent slot selection exist. Organizer receipts alone can upgrade an entry to `ORGANIZER-CONFIRMED`.

## Run card

```json
{
  "hypothesis": "Readiness review only; no lane assigned",
  "mechanism": "No candidate mechanism tested",
  "named_non_fault_process_that_could_mimic_it": "Not applicable; no predictor or surface constructed",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positive_pixels": null,
    "value": null,
    "ci95": null,
    "status": "NOT_RUN: native features and shared feature cache missing"
  },
  "correlation_overlap_vs_registry": {
    "candidate_surface": "NOT_MEASURED",
    "final_dots": "NOT_MEASURED",
    "registry_input_coverage": "74/729 bytes; incomplete; values not audited",
    "pinned_witness_literal_forward_overlap": 1.0,
    "status": "BLOCKED: unchanged 0.70 literal support gate"
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": false,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "existing_release_audit": "49/49 historical research TIFFs format/integrity valid; none approved"
  },
  "submission_name": null,
  "submission_note": "No candidate; audit only; DO NOT SUBMIT",
  "experiments_run": 0,
  "submission_slots_used": 0,
  "verdict": "negative"
}
```
