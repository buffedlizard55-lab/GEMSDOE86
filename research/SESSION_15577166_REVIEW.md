# Repository review — 2026-10-25 — `arena/15577166-gemsdoe86`

## Decision

**DO NOT SUBMIT any file.** No new candidate, geological experiment, or weekly slot was created or used in this review. The request contains no single method paragraph assigning this session a lane, despite the parallel-run protocol requiring one. The existing stop is also decisive: the pinned witness covers every allowed cell, so the literal 3-pixel forward-overlap rule yields 1.0 for every nonempty allowed prediction, exceeding 0.70. A stop cannot be overridden by a locally valid TIFF, a partial-registry uniqueness result, or a score projection.

This review reproduced a publication-integrity defect: an inherited H86M-LT TIFF had a standalone page saying “YES — submit,” although it was absent from the canonical indexes and current release audit. A parallel branch integrated the equivalent fail-closed repair as [PR #166](https://github.com/buffedlizard55-lab/GEMSDOE86/pull/166) during this review; after syncing to current `main`, this branch retains the independent review and ranked research queue rather than duplicating that implementation. The TIFF bytes were not changed. Its historical projection figures remain projections, not HOLDOUT-DTI or ORGANIZER-CONFIRMED scores.

## Pass 1 — reproduce and inspect

- Read `PROMPT.md`, `README.md`, the complete current request archive, `AGENTS.md`, current run cards and input audit code before edits.
- Ran `scripts/review_repository.py --timeout 600`. Initial result: **19 failed, 1,003 passed, 24 skipped, 58 subtests passed**. The primary integration defect was one unregistered H86M-LT TIFF/ZIP and an affirmative submit page; the audit thereby rejected the release inventory and caused multiple downstream tests to fail. Other error messages were consequences of the same inventory mismatch.
- `scripts/audit_workspace_inputs.py` with the pinned environment reports current native features missing, prepared arrays missing, and the required shared feature cache not established. Historical manifest/restore receipts do not change this live availability result.
- The cached shared feature stack is not present. The request gives no lane paragraph. No holdout or model run is permitted or supportable here.

## Pass 2 — reconcile publication and evidence

- The initial branch reproduced the missing inventory/card linkage and the release-audit cascade. The equivalent registration was merged to `main` by concurrent PR #166; the final branch uses that upstream registration and its regression test, avoiding a duplicate fix. The raster remains audit-only and no variant-specific HOLDOUT-DTI claim is inferred.
- Confirmed the current upstream card preserves the historical H86M-LT record while setting current authorization fields false and documenting why the earlier “PROMOTE / YES” publication wording is superseded.
- Confirmed the adjacent writer sidecar and inventory now encode audit-only / no-slot status; no raster pixels were modified.
- Replaced `docs/h86m-lt.html` with a page that states “Download for audit: yes. Submit: no.”
- Restored only hash-pinned protocol mirrors required by the shared audit (`sample_submission.tif`, `existing_faults.tif`, and the pinned historical witness) into ignored local `data/`; no DrivenData portal was accessed, and no training feature raster was restored.
- Remeasured all registered outputs against the pinned witness. **36/36** files pass local format/integrity; current decision remains **DO NOT SUBMIT**. The witness measurement is a negative test, not a full-registry clearance.
- Updated the README's leading summary to align with the current machine decision and point to the standing request and review. Generated pages/reports were rebuilt through their scripts, not edited to hand-transcribe measurements.

## Pass 3 — re-check the whole request and edge cases

- The authoritative DTI evaluator in the vendored template uses a weighted maximum credit per hidden truth location. For a proposed pruning, losing truth credit can outweigh saved false-positive mass; geometric distance from a mapped fault is not itself proof of zero held-out credit. Existing H33 pixel evidence establishes a parent-to-child edit, not causality for an external score change.
- The claimed H33 `0.2778`, and the request's `0.3195` / `0.4413` leaderboard claims, are **OWNER-REPORTED** inputs, not submission-page receipts. No submission score or higher-than-H33 result is claimed.
- Historical H86M-LT reported DTI projections fitted from owner-reported scores and SGMC-PROXY-DTI. Those quantities are not substitute holdout results. Its prior local registry scan of 655 files is narrower than the current strict witness stop; the witness does not prove global uniqueness, but it suffices to reject under the literal threshold.
- Every proposed research direction below is **not run** in this review. All native bands come from the checked-in `src/gems86/io.py:BANDS`; the actual feature TIFF/cache is absent. External ASTER data is explicitly not considered viable until its free official source is obtained and hash-pinned in an allowed environment.
- Final checks are recorded below. No leaderboard portal was scraped. No submission selection or quota inference was made.

## H33 analysis: what is known and what is not

The repository's read-only pixel audit (`docs/evidence/concurrent-artifact-review-20261025.json`) measures parent `D28` at **40,199 dots** and H33 at **37,654 dots**: H33 equals the parent after removing **2,545** collar dots, adding zero. This is a raster measurement. The submitted values `0.2708` and `0.2778` in the owner-provided project history are not organizer-confirmed receipts. The edit is therefore known; a causal explanation for a private score difference is not.

The shared evaluator code and its DTI algebra explain a plausible mechanism: pruning can improve the ratio if it removes prediction mass with little lost hidden-fault credit. But the 2-pixel removed collar is not guaranteed to have zero credit: a nearby prediction can recover a different hidden segment. The correct causal test would compare parent and pruned variants on the same buffered whole-segment hide-and-recover folds, deriving every catalogue feature only from visible segments and masking those pixels exactly. This review did not run that test.

Sources to inspect: [pinned H33 analysis](H33_ANALYSIS.md), [pixel-level comparison receipt](../docs/evidence/concurrent-artifact-review-20261025.json), [shared DTI implementation](../vendor/template66/gems57/metric.py), and [official DrivenData reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution). An OWNER-REPORTED historical number cannot establish that a new method will beat 0.2778.

## Ranked hypotheses for a future, separately assigned lane

Ranks are qualitative research priority, **not score projections**. These methods are unexecuted in this checkout as of this review; this does not establish novelty across all 92 linked projects or the broader literature. The existing H86K queue already recorded the first three as unselected reserves. No candidate is currently authorized for implementation because this session has no assigned method paragraph and the protocol preflight stops before placement.

| Rank | Hypothesis and exact competition bands | Target signature and reason for possible catalogue-missing faults | Difference from methods already implemented here | Named non-fault mimic | Cost / present viability |
|---|---|---|---|---|---|
| 1 | **Steerable quadrature odd/even step–dike discriminator (H86K-CWQA reserve):** Band 2 `rtp`, Band 14 `tmi`, Band 13 `iso_grav_anom`, and signed directional gravity derivatives Bands 11/18. | An 8-azimuth, multi-scale quadrature phase/symmetry response: ask whether a coherent magnetic and gravity anomaly has a step-like odd-symmetry phase rather than an even-symmetry ridge, potentially suppressing volcanic dikes while retaining covered basement steps with no surface scarp. | H86J-MPC/MCSP used orientation-pooled Riesz/phase or other potential-field detectors; this reserve proposes a steerable log-Cauchy phase-symmetry test with a cross-potential-field shape control. No such executable feature is found in `src/` or `scripts/`. | Dike swarms, steep intrusive contacts, magnetic remanence boundaries, or flight-line seams. | Medium-high (filter-bank and sign/scale validation). Uses competition-native inputs, so it requires no new external data, but cannot be validated now: native feature TIFF/shared cache missing and the literal protocol stop forbids placement. “Poisson ratio” should not be called a material property unless units/physics are established; treat any ratio as a proxy and test stability. |
| 2 | **Directional hanging-wall rollover / antithetic-graben curvature (H86K-BFAH reserve):** Bands 12 `det_elev`, 15 `depth_to_base_surf`, 19 `det_elev_slope`, with Band 13 gravity as an independent-shape control. | Test directional second derivative of basin-depth surfaces along frozen range-normal transects, focusing on intrabasin rollover and paired antithetic structures that may have subdued surface relief rather than mapped range-front traces. | H86I-HVFD used isotropic biharmonic curvature; H86K-STDP included a scalar hinge feature. The proposed frozen directional transect/rollover mechanics is not those implementations, though it is not wholly independent of them. | Differential compaction over buried paleotopography, erosional basin margins, and gravity-inversion smoothing artifacts. | Medium (orientation assignment, scale choices, control comparison). Native bands only; no new external data required, but currently untestable due the same missing cache and protocol stop. Band 15 is gravity-derived, so it is not independent corroboration. |
| 3 | **ASTER SWIR steam-heated alteration lineaments (H86K-NVGS reserve):** official USGS ASTER shortwave-infrared mineral-index layers plus native Bands 2 `rtp`, 13 `iso_grav_anom`, and 17 `cond_surf`. | Test persistent Al-OH / hydrated-silica spectral absorption lineaments above covered geothermal systems, aligned with independent basement/structure evidence. A blind, low-scarp alteration corridor could be absent from the existing fault catalogue. This is a remote-sensing hypothesis, not proof that alteration marks faults. | No ASTER SWIR mineral-index layer appears in this checkout's band map or executable features. Existing radiometric total count and potential-field layers are different physical measurements. | Detrital clay-rich washes, altered tuff outcrops, and surface mineralogy unrelated to geothermal faulting. | High; **not presently viable**. The preregistered official source is USGS ScienceBase release / SIM 3476, DOI [10.5066/P9BA3684](https://doi.org/10.5066/P9BA3684). This sandbox's outbound allowlist does not permit direct USGS/ScienceBase requests, and no hash-pinned mirror is verified here. Obtain and hash-verify the actual source first on an allowed host; until then it is deferred, not proposed as ready to validate. |

**Required validation if a future owner-assigned lane clears the stop:** use the pinned template evaluator and writer; hide complete fault components with a buffer; rebuild catalogue-derived features using visible faults only; exact-mask visible fault pixels; report pooled HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI; run one-feature-at-a-time leakage canaries (AUC >0.90 is a stop); compare against matched controls; perform surface uniqueness before placement and final-dot uniqueness before serialization. Stop at three experiments or two hours. A HOLDOUT-DTI win alone does not override a registry uniqueness or submission authorization stop.

## Limitations and handoff

1. **Submission:** none is cleared. The repository's instruction is DO NOT SUBMIT; the H86M-LT binary is retained solely for audit/learning. No unique competition submission was generated by this session.
2. **Lane ambiguity:** the protocol refers to a “single method paragraph below,” but the current request contains no assigned method paragraph. The queued ideas above are proposals, not authorization to pick a lane.
3. **Data:** current workspace inspection finds neither native `training_features.tif` nor prepared arrays nor a verified shared template cache. Hash-pinned `sample_submission.tif`, mapped-fault raster and historical witness are present in ignored local data for read-only audits. A mirrored raw TIFF would not establish cache provenance.
4. **Protocol blocker:** the witness is an owner-repository historical raster, not official label data. It gives a sufficient literal overlap rejection under the rule as currently written; only an authorized shared/upstream clarification can resolve the incompatibility. Do not privately relax thresholds or evade preflight.
5. **External data:** USGS ASTER source is linked above but not obtainable in this sandbox allowlist. Do not claim its current bytes, spectral layers, exact coverage, or usability without an official download receipt and hashes.
6. **Scores/quota:** no leaderboard or organizer page was accessed. All provided historic scores remain user/owner claims; no quota, organizer score, or likelihood of beating 0.2778 is established.
7. **Next work:** clarify/authorize the protocol interpretation and method paragraph; obtain/pin the shared feature cache and native inputs through the approved path; then preregister one lane and run the evaluator and validator. Only after scientific and registry gates pass should the separate slot selector and organizer receipt be used.

## Verification record

- `scripts/audit_release.py --measure-registry`: **PASS**, 36/36 local artifacts audited; verdict DO NOT SUBMIT; zero experiments, zero slots. Latest registry measurement: see `docs/evidence/latest-review-run-card.json`.
- `scripts/audit_downloads.py --write`: **PASS**, 36 TIFF/receipt/ZIP sets validated locally; format validity only.
- `scripts/build_site.py` and `scripts/build_site.py --check`: **PASS**.
- `scripts/check_site.py`: **PASS**, link/inventory/ZIP integrity and negative-state safety.
- Focused regression suite after updates: **94 passed, 39 subtests passed**.
- Final synced-tree suite: **1,029 passed, 24 skipped, 48 warnings, 58 subtests passed** (`pytest -q`, 434.94 s). `scripts/review_repository.py --timeout 900` completed all seven software/evidence checks successfully at 2026-10-25T18:54:07Z; this establishes repository-check completion, not model training readiness or submission authorization.

## Run card — this repository review

```json
{
  "hypothesis": "No assigned geological lane; no new candidate was constructed. Future reserves are ranked H86K-CWQA, H86K-BFAH, then H86K-NVGS, all unrun in this checkout.",
  "mechanism": "Read-only publication and protocol review. The pinned witness has positive support on every allowed cell, so the literal rule rejects every nonempty allowed candidate; no geological mechanism was tested.",
  "named_non_fault_process": "Not tested in this review; leading future-hypothesis mimic is volcanic dike swarms or intrusive contacts for the H86K-CWQA step-versus-dike discriminator.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "NOT_RUN_NO_ASSIGNED_LANE_AND_PROTOCOL_STOP"
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface_spearman": null,
    "candidate_final_dot_overlap_3px": null,
    "inherited_artifacts_checked": 36,
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "witness_forward_overlap_for_nonempty_allowed_prediction": 1.0,
    "stop_threshold": 0.70,
    "registry_complete": false,
    "scope": "Witness-only negative is sufficient to stop; not a full registry uniqueness pass."
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": "NOT_GENERATED",
    "inherited_local_format_integrity": "36/36 PASS",
    "no_nan_inside_footprint": "NOT_APPLICABLE_NO_NEW_RASTER",
    "values_in_0_1": "NOT_APPLICABLE_NO_NEW_RASTER",
    "crs_shape_transform_match": "NOT_APPLICABLE_NO_NEW_RASTER",
    "submission_authorized": false
  },
  "submission_name": null,
  "note": "No new TIFF or experiment. Current decision: DO NOT SUBMIT; H86M-LT is audit-only.",
  "experiments_run": 0,
  "submission_slots_used": 0,
  "safe_to_submit": false,
  "approved_for_weekly_slot": false,
  "verdict": "negative"
}
```
