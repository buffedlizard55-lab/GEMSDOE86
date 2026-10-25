# GEMSDOE86 independent recheck — 2026-10-25

## Decision

**DO NOT SUBMIT any repository TIFF. No new TIFF was generated.** I did not run an experiment, train a model, select a slot, or access the competition portal. The current run-card remains negative: the pinned historical full-support raster blocks every nonempty candidate under the literal 70% overlap stop, the current request assigns no single method paragraph, and the required shared derived-feature cache is absent. Creating a downloadable TIFF anyway would violate the stated uniqueness gate; existing TIFFs remain research/audit files only.

This is a fresh read-only review and remeasurement, not a new scientific result. The top-level user claims that H33 scored `0.2778` and the leaderboard is at `0.3195` or `0.4413` are **OWNER-REPORTED**. The repository has no submission-page receipt for any of these values; none is **ORGANIZER-CONFIRMED**.

## Three-pass review

### Pass 1 — current requirements, provenance, and H33 forensics

- Read `PROMPT.md`, `README.md`, `AGENTS.md`, and `research/REQUEST_20261025.md`. The long-term request to make an upload-ready unique TIFF conflicts with the same request's literal overlap rule and the current verified stop. It does not supply one lane-specific method paragraph. The latter is a binding prerequisite; old preregistrations are not a new lane assignment.
- Rechecked H33 lineage from the hash-pinned raster comparison in `docs/evidence/concurrent-artifact-review-20261025.json`: the parent raster has 40,199 dots; H33 has 37,654; H33 is exactly the parent after 2,545 catalogue-collar dots are removed (zero additions). This is a **RASTER-MEASUREMENT**, not a score measurement or causal experiment.
- The plausible metric mechanism is precision/mass control: with a distance-weighted Tversky score (shared pinned `vendor/gems57/metric.py`; `alpha=0.2`, `beta=0.8`, 300 m triangular kernel), a removed prediction that had little marginal hidden-truth credit can reduce false-positive mass more than it reduces true-positive credit. Because mapped fault pixels are masked but surrounding kernel cells are not, collar dots may still recover nearby unmapped faults; therefore collar removal is not guaranteed to help. The raster edit explains *what changed*. It does not establish that the edit caused the owner-reported score increase.
- The auditable answer is therefore: H33's observed edit is a targeted catalogue-collar pruning of an existing sparse prediction, not evidence for a new geothermal mechanism. Its reported `0.2778` is plausible under the metric if the pruned dots were mostly low-incremental-credit predictions. A higher score is possible in principle, but **no result in this checkout establishes that we can beat it**. Whether it is actually the top result cannot be established from owner-provided scores, especially given the request's conflicting `0.3195` and `0.4413` claims.

### Pass 2 — run gates, detect regressions, repair, and verify

Environment was prepared from the committed `requirements-lock.txt`. The native feature TIFF and actual shared derived-feature cache are absent; no feature generation or model evaluation was attempted.

Read-only measurement commands and outcomes:

```text
.venv/bin/python scripts/restore_data.py --protocol-only --include-registry
  PASS: restored hash-pinned sample grid, mapped-fault mask, and dense witness.
.venv/bin/python scripts/protocol_preflight.py
  STOP_LITERAL_OVERLAP_UNSATISFIABLE: witness SHA-256 ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be;
  all 5,106,385 allowed cells covered, zero uncovered, measured overlap 1.0 > 0.70.
.venv/bin/python scripts/restore_registry_inventory.py --workers 8
  PASS: 655/655 immutable external inventory entries byte-verified (728,345,463 bytes).
.venv/bin/python scripts/audit_registry_inputs.py
  PASS: 700/700 current indexed raster entries byte-verified; 698 grid-compatible, 2 incompatible/invalid; uniqueness clearance false.
.venv/bin/python scripts/audit_release.py --measure-registry
  PASS integrity audit: 28/28 inherited outputs locally format-valid; decision DO NOT SUBMIT; 0 experiments / 0 slots.
.venv/bin/python scripts/build_site.py
  PASS: regenerated the executive summary and homepage from current evidence (research downloads remain explicitly non-submittable).
```

The first audit attempt was correctly rejected because the inherited final-dot proof was bound to the previous preflight report. After restoring the pinned registry inputs, `audit_release.py --measure-registry` refreshed the witness binding and passed. The fresh input audit found 700 rather than the previously hard-coded 690 entries: the current indexed set includes the 655 external inventory blobs plus 45 local files. This is complete byte coverage of that **indexed snapshot**, not proof that the public project fleet or organizer registry is complete. Two known incompatible grids remain: `14GEMSDOE` has a shifted affine origin; the `7GEMSDOE`/`GEMSDOE22` record is three-band. Neither was silently dropped, warped, or repaired.

The first full test run found two stale assumptions in `tests/test_current_session_cf73474c.py` (fixed registry size `690` and matching display string). Updated them to assert the measured audit counts and generated-page count dynamically. The tests now enforce that the inventory totals agree, both incompatible records remain blocking, and the UI publishes the byte-verification count. This is a repository regression fix, not a change to the protocol threshold or science.

After this recheck, `origin/main` advanced and integrated a separate GDSC research TIFF (PR #145). It was not generated in this review. I re-audited the merged release: **29/29** artifacts are locally format-valid, but all remain `DO NOT SUBMIT`; the GDSC card is negative and the same literal witness blocks it. The current base also introduced a live input audit; `scripts/audit_workspace_inputs.py --require-native` independently confirms that `training_features.tif`, all 21 prepared arrays, and the lane cache are missing, then fails closed with exit code 1 (the read-only form without `--require-native` exits 0 but records these blockers). The merged registry input audit is now 701/701 indexed rasters byte-verified, 699 compatible and 2 incompatible; this is snapshot coverage, not public-fleet completeness. This remeasurement supersedes the pre-integration 28-artifact/700-input counts below without changing this review's no-candidate/no-slot result.

The merged GDSC sidecar uses a path-qualified ZIP name and carries its non-promotion decision in a linked run card rather than in the writer receipt's legacy fields. The shared `audit_downloads.py` previously rejected that valid local sidecar shape; extended the common audit to verify the exact inventory ZIP path/hash and the linked run card's negative/no-slot fields. No TIFF or receipt bytes were rewritten. A regression test now covers the schema. Also fixed a hard-coded historical timestamp in `audit_release.measure_all_registry()` so a `--measure-registry` run records actual UTC time; its synthetic-clock regression passes.

Automated checks before the base-branch integration (28-artifact snapshot):

```text
.venv/bin/python -m pytest -q
  PASS: 957 passed, 24 skipped, 58 subtests passed; 48 Rasterio pending-deprecation warnings.
.venv/bin/python scripts/build_site.py --check
  PASS: generated pages match current evidence.
.venv/bin/python scripts/check_site.py
  PASS: links, registered artifacts, and DO NOT SUBMIT state.
.venv/bin/python scripts/audit_downloads.py
  PASS: 28 TIFFs/receipts locally revalidated; no authorization inferred.
.venv/bin/python scripts/build_review_card.py --check
  PASS: frozen historical review remains unchanged.
git diff --check
  PASS.
```

Post-merge, the first three-pass CI replay found one additional stale assertion (`tests/test_publication_gate.py` still expected 28 artifacts). It was changed to compare the measured artifact count to the inventory length; this is the same evidence-driven fix as the two earlier 690-to-700 test corrections. The corrected final one-command review passed:

```text
.venv/bin/python scripts/review_repository.py --timeout 600
  PASS: software_review_passed=true; all 7 release/test/frozen/site/link/download/live-input checks passed.
  pytest: 978 passed, 24 skipped, 58 subtests passed; 48 Rasterio pending-deprecation warnings.
  release audit: 29/29 local format/integrity checks; verdict DO NOT SUBMIT; 0 experiments and 0 slots.
  downloads audit: 29/29 TIFFs/receipts passed; no upload authorization inferred.
  live-input audit: software inspection passed, while native input/readiness remains false; feature TIFF, prepared arrays and shared cache are absent.
```

The separate `scripts/audit_workspace_inputs.py --require-native` check is expected to exit 1 because the pinned `training_features.tif` is missing. This is an availability blocker, not a model result. `scripts/audit_release.py --measure-registry` now records its actual UTC remeasurement time rather than replaying the historical `04:07` timestamp; the timestamp regression test and the fresh page timestamp both pass.

### Pass 3 — scientific proposals, external data, and edge cases

The three candidates below are **proposal-only** and ranked qualitatively by expected information not covered by current methods versus implementation cost. They are not score projections. The earlier repo review documents checkout-scoped searches and band names; external-fleet novelty is not claimed. All three use competition-native bands; no new external dataset is required merely to evaluate them. However, the required shared feature cache is absent and no lane was assigned, so none was run. Their main physical mimics and essential controls are stated rather than hidden.

| Rank | Hypothesis and competition layers | Target signature; why it may find an uncatalogued fault | Difference from implemented checkout methods | Named non-fault mimic | Expected information / cost |
|---|---|---|---|---|---|
| 1 | **Persistent potential-field saddle connections** — Band 2 `rtp`, Band 13 `iso_grav_anom`, Band 15 `depth_to_base_surf` | Track scale-persistent saddle-to-extremum connectors between anomaly bodies. A buried structural link may lack an exposed scarp and need not appear as an isolated local peak or ridge. | Persistence-ranked graph topology, rather than current local Hessian ridges, truncation/cross-gradient detectors, or visible-fault relay rules. | Intrusive contacts, erosional basement relief, or saddles from superposed sources. | Medium qualitative potential; medium-high implementation/control cost. Existing H86G-PSC preregistration exists; **not run here**. |
| 2 | **Conductivity-neck topology conditioned on strain** — Band 17 `cond_surf`, Band 7 `geod_shearrate`, Band 8 `geod_dilaterate` | Find narrow, threshold-persistent conductive connections preferentially in positive dilatation. A buried fluid pathway need not have surface expression. | Persistent component-neck geometry; distinct from raw conductivity highs, edge-only margins, and generic conductivity/strain fusion. | Saline playa, clay-rich paleochannel, or gridding bottleneck. | Low-to-medium qualitative potential; medium cost. Existing H86G-CNT preregistration exists; **not run here**. |
| 3 | **Directional-semivariogram change point** — Band 2 `rtp`, Band 13 `iso_grav_anom`, optionally Bands 17 `cond_surf` and 8 `geod_dilaterate` for context | Detect spatially localized shifts in directional correlation length/anisotropy persisting across windows; may reveal covered basement discontinuities without using catalogue proximity to nominate them. | Second-order spatial-statistics change point rather than pointwise classifier, edge/ridge transform, or monogenic phase score. Checkout search found no implementation; that is not evidence of fleet-wide novelty. | Lithologic boundaries, volcanic-flow fabric, tie-line/interpolation seams, and basin-fill texture. | Low/speculative potential; medium-high cost due to window selection and spatial-block nulls. Not preregistered/implemented. |

No proposal can be called “viable to validate now”: the repo's current stop prevents candidate placement and the shared feature cache is missing. All specified layers are in the competition-native stack, so no external data acquisition is necessary for the first test. For independent geologic corroboration later, the official USGS GeoDAWN release (DOI `10.5066/P93LGLVQ`) and DOE Geothermal Data Repository INGENIOUS submission 1391 are useful sources already linked in the repo; they are not substitutes for a valid blind holdout. Automated DrivenData portal access remains prohibited by `AGENTS.md` Rule 9; no portal or score page was scraped in this pass.

## Limitations and safe next steps

1. Keep the current state **DO NOT SUBMIT**. A locally valid TIFF is not a unique, scientifically validated, organizer-accepted file. No new file/hash/name exists.
2. Resolve the literal full-support witness through an authorized shared/upstream protocol disposition. Do not privately loosen the `0.70` gate, re-label audit files, or bypass a preflight.
3. Obtain and hash-pin the actual template-derived feature cache; raw/native TIFF layers or preparation manifests are not that cache.
4. Assign one method paragraph, preregister exactly one lane, and then use the shared `evaluate_holdout.py`/`submission_writer.py` pipeline: hide whole fault segments with buffer, derive catalogue features from visible segments only, exact-mask visible fault pixels, compute pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular kernel), include withheld-positive count and block-bootstrap 95% CI, and test each feature alone (AUC >0.90 is leakage pending proof). Cap work at three experiments or two hours.
5. Run full-registry surface uniqueness before placement and final-dot uniqueness before serialization; define an explicit fail-closed policy for incompatible registry grids. A partial scan may reject, never certify uniqueness.
6. A separate authenticated selector and organizer submission-page receipt are required for slot authorization and an `ORGANIZER-CONFIRMED` result. No quota or organizer score was established here.
7. Use the linked official sources below for manual review. Competition-hosted data pages were not accessed or scraped; access and leaderboard numbers are not represented as newly verified.

## Official/standards sources retained for review

- [DrivenData GEMS problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — official task description; not accessed automatically here.
- [DrivenData competition rules/entry](https://www.drivendata.org/competitions/306/competition-doe-gems/) — official competition page; no portal scraping.
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) — official reference implementation repository.
- [DOE/NLR GEMS solicitation PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — competition document linked by the project.
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ).
- [DOE Geothermal Data Repository, INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391).
- [EPSG:32611](https://epsg.io/32611) — grid CRS reference.
- H33 lineage and score caveat: [pixel-measurement receipt](../docs/evidence/concurrent-artifact-review-20261025.json), [H33 analysis](H33_ANALYSIS.md), [interpretation review](H33_INTERPRETATION_REVIEW.md), and [GEMSDOE32 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) (the page's score is an owner-reported claim for this project, not a receipt).

## Run card — this review

```json
{
  "hypothesis": "No lane assigned or candidate tested; three ranked proposals are unrun.",
  "mechanism": "H33's measured edit removes 2,545 catalogue-collar dots from the parent; the plausible DTI mechanism is reduced low-credit prediction mass, but causation of the owner-reported score change is unproven.",
  "named_non_fault_process": "For the leading potential-field topology proposal: intrusive contacts, erosional basement relief, or superposed-source saddles.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "status": "NOT_RUN_NO_LANE_ASSIGNED_AND_PROTOCOL_STOP",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface_spearman": null,
    "candidate_final_dot_overlap_3px": null,
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "witness_allowed_cells": 5106385,
    "uncovered_allowed_cells": 0,
    "literal_forward_overlap_for_any_nonempty_allowed_candidate": 1.0,
    "stop_threshold": 0.70,
    "registry_input_snapshot": "700 indexed entries byte-verified; 698 grid-compatible; 2 incompatible; snapshot completeness is not public-registry completeness",
    "candidate_unique": null
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": "NOT_GENERATED",
    "inherited_local_format_validation": "28/28 pass",
    "no_nan_inside_footprint": "NOT_APPLICABLE_NO_NEW_RASTER",
    "values_in_0_1": "NOT_APPLICABLE_NO_NEW_RASTER",
    "crs_shape_transform_match": "NOT_APPLICABLE_NO_NEW_RASTER",
    "submission_authorized": false
  },
  "submission_name": null,
  "note": "Review/negative result only; no TIFF generated and no slot used.",
  "verdict": "negative"
}
```
