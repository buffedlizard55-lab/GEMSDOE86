# GEMSDOE86 independent recheck — 2026-10-25

## Decision

**DO NOT SUBMIT any repository TIFF. This recheck generated no TIFF and ran no experiment.** The latest merged base now includes the upstream H86K-PSC research artifact (not produced by this review): HOLDOUT-DTI 0.0467 [0.0380, 0.0550], `gems57-pooled-hide-v2`, 11,321 withheld positives. Its paired difference versus the ridge control crosses zero, so the preregistered promotion rule failed; its run card explicitly records `safe_to_submit=false`, `approved_for_weekly_slot=false`, and 0 slots. Current release audit reports 30/30 local format/integrity checks, still **DO NOT SUBMIT**. The current workspace also retains a pinned full-support witness that blocks every nonempty candidate under the literal 70% overlap stop; no new lane was assigned for this recheck and the shared feature cache is absent. Existing TIFFs remain research/audit files only.

This is a fresh read-only review and remeasurement, not a new scientific result. The top-level user claims that H33 scored `0.2778` and the leaderboard is at `0.3195` or `0.4413` are **OWNER-REPORTED**. The repository has no submission-page receipt for any of these values; none is **ORGANIZER-CONFIRMED**.

## Three-pass review

### Pass 1 — current requirements, provenance, and H33 forensics

- Read `PROMPT.md`, `README.md`, `AGENTS.md`, and `research/REQUEST_20261025.md`. The long-term request to make an upload-ready unique TIFF conflicts with the same request's literal overlap rule and the current verified stop. It does not supply one lane-specific method paragraph. The latter is a binding prerequisite; old preregistrations are not a new lane assignment.
- Rechecked H33 lineage from the hash-pinned raster comparison in `docs/evidence/concurrent-artifact-review-20261025.json`: the parent raster has 40,199 dots; H33 has 37,654; H33 is exactly the parent after 2,545 catalogue-collar dots are removed (zero additions). This is a **RASTER-MEASUREMENT**, not a score measurement or causal experiment.
- The plausible metric mechanism is precision/mass control: with a distance-weighted Tversky score (shared pinned `vendor/gems57/metric.py`; `alpha=0.2`, `beta=0.8`, 300 m triangular kernel), a removed prediction that had little marginal hidden-truth credit can reduce false-positive mass more than it reduces true-positive credit. Because mapped fault pixels are masked but surrounding kernel cells are not, collar dots may still recover nearby unmapped faults; therefore collar removal is not guaranteed to help. The raster edit explains *what changed*. It does not establish that the edit caused the owner-reported score increase.
- The auditable answer is therefore: H33's observed edit is a targeted catalogue-collar pruning of an existing sparse prediction, not evidence for a new geothermal mechanism. Its reported `0.2778` is plausible under the metric if the pruned dots were mostly low-incremental-credit predictions. A higher score is possible in principle, but **no result in this checkout establishes that we can beat it**. Whether it is actually the top result cannot be established from owner-provided scores, especially given the request's conflicting `0.3195` and `0.4413` claims.

### Pass 2 — run gates, detect regressions, repair, and verify

Environment was prepared from the committed `requirements-lock.txt`. In this recheck workspace the native feature TIFF and actual shared derived-feature cache are absent; no feature generation, new model evaluation, or experiment was attempted. This does not erase the separate H86K-PSC run already present on the merged base.

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

After this recheck, `origin/main` advanced and integrated a separate GDSC research TIFF (PR #145), then an H86K-PSC research run (PR #147). Neither was generated in this review. The current merged release has **30/30** locally format-valid artifacts, all still `DO NOT SUBMIT`; both GDSC and H86K-PSC run cards deny submission authorization. H86K-PSC reports 699/701 comparable registry rasters, discloses two incompatible entries, and does not override the literal full-support witness stop. The current base also introduced a live input audit; `scripts/audit_workspace_inputs.py --require-native` independently confirms that `training_features.tif`, all 21 prepared arrays, and the lane cache are missing, then fails closed with exit code 1 (the read-only form without `--require-native` exits 0 but records these blockers). The merged registry input audit is now 701/701 indexed rasters byte-verified, 699 compatible and 2 incompatible; this is snapshot coverage, not public-fleet completeness. The current remeasurement supersedes prior 28/29-artifact and 700-input counts; this review itself still generated no candidate and used no slot.

The merged GDSC sidecar uses a path-qualified ZIP name and carries its non-promotion decision in a linked run card rather than in the writer receipt's legacy fields. The shared `audit_downloads.py` previously rejected that valid local sidecar shape; extended the common audit to verify the exact inventory ZIP path/hash and the linked run card's negative/no-slot fields. No TIFF or receipt bytes were rewritten. A regression test now covers the schema. Also fixed a hard-coded historical timestamp in `audit_release.measure_all_registry()` so a `--measure-registry` run records actual UTC time; its synthetic-clock regression passes.

Automated checks before the H86K-PSC base integration (29-artifact snapshot):

```text
.venv/bin/python -m pytest -q
  PASS: 957 passed, 24 skipped, 58 subtests passed; 48 Rasterio pending-deprecation warnings.
.venv/bin/python scripts/build_site.py --check
  PASS: generated pages match current evidence.
.venv/bin/python scripts/check_site.py
  PASS: links, registered artifacts, and DO NOT SUBMIT state.
.venv/bin/python scripts/audit_downloads.py
  PASS: 29 TIFFs/receipts locally revalidated; no authorization inferred.
.venv/bin/python scripts/build_review_card.py --check
  PASS: frozen historical review remains unchanged.
git diff --check
  PASS.
```

The first post-GDSC replay found a stale literal (`tests/test_publication_gate.py` expected 28 artifacts); it was made inventory-relative. That 29-artifact replay passed with 978 tests, but it preceded the subsequent H86K-PSC integration from PR #147. After integrating PR #147, the three-pass runner caught a missing current count phrase in the README: the inventory test requires the current `**30** published research TIFFs` label. The README summary was corrected without changing the audit or scientific state.

The final replay on the 30-artifact tree passed:

```text
.venv/bin/python scripts/review_repository.py --timeout 600
  Measured UTC: 2026-10-25T15:07:53.356247+00:00
  PASS: software_review_passed=true; all 7 release/test/frozen/site/link/download/live-input checks passed.
  pytest: 980 passed, 24 skipped, 58 subtests passed; 48 Rasterio pending-deprecation warnings.
  release audit: 30/30 local format/integrity checks; DO NOT SUBMIT; 0 experiments and 0 slots recorded for this review.
  downloads audit: 30/30 TIFFs/receipts revalidated; no upload authorization inferred.
  live-input audit: software inspection passed, but training readiness is false; native feature TIFF, prepared arrays, and shared cache are absent.
```

A fresh protocol preflight and registry remeasurement immediately before this final replay was recorded at `2026-10-25T14:54:13.425113+00:00`; the one-hash-pinned dense witness still covers all 5,106,385 allowed pixels and makes the inherited literal 0.70 overlap rule unsatisfiable for every nonempty candidate. The separate `scripts/audit_workspace_inputs.py --require-native` check is expected to exit 1 because `training_features.tif` is missing. This is an availability blocker, not a model result. `scripts/audit_release.py --measure-registry` records actual UTC rather than replaying the old historical timestamp; its regression test and generated-page check pass.

### Pass 3 — scientific proposals, external data, and edge cases

H86K-PSC is now an **already-run upstream lane**, not a proposal: its HOLDOUT-DTI result and paired-control uncertainty are recorded above and in `docs/evidence/h86k-psc-run-card.json`. The two remaining ideas below are unrun, ranked qualitatively by expected information not covered by current methods versus implementation/control cost, and are not score projections. The earlier repo review documents checkout-scoped searches and bands; external-fleet novelty is not claimed. Both use competition-native bands, but the required shared feature cache is absent and no new lane was assigned here. Their principal physical mimics and controls are stated explicitly.

| Rank | Hypothesis and competition layers | Target signature; why it may find an uncatalogued fault | Difference from implemented checkout methods | Named non-fault mimic | Expected information / cost |
|---|---|---|---|---|---|
| 1 | **Conductivity-neck topology conditioned on strain** — Band 17 `cond_surf`, Band 7 `geod_shearrate`, Band 8 `geod_dilaterate` | Find narrow, threshold-persistent conductive connections preferentially in positive dilatation. A buried fluid pathway need not have surface expression. | Persistent component-neck geometry; distinct from raw conductivity highs, edge-only margins, and generic conductivity/strain fusion. | Saline playa, clay-rich paleochannel, or gridding bottleneck. | Low-to-medium qualitative potential; medium cost. Existing H86G-CNT preregistration exists; **not run here**. |
| 2 | **Directional-semivariogram change point** — Band 2 `rtp`, Band 13 `iso_grav_anom`, optionally Bands 17 `cond_surf` and 8 `geod_dilaterate` for context | Detect spatially localized shifts in directional correlation length/anisotropy persisting across windows; may reveal covered basement discontinuities without using catalogue proximity to nominate them. | Second-order spatial-statistics change point rather than pointwise classifier, edge/ridge transform, or monogenic phase score. Checkout search found no implementation; that is not evidence of fleet-wide novelty. | Lithologic boundaries, volcanic-flow fabric, tie-line/interpolation seams, and basin-fill texture. | Low/speculative potential; medium-high cost due to window selection and spatial-block nulls. Not preregistered/implemented. |

Neither unrun proposal can be called “viable to validate now”: the repo's current stop prevents candidate placement and the shared feature cache is missing. All specified layers are in the competition-native stack, so no external data acquisition is necessary for an eventual first test. For independent geologic corroboration later, the official USGS GeoDAWN release (DOI `10.5066/P93LGLVQ`) and DOE Geothermal Data Repository INGENIOUS submission 1391 are useful sources already linked in the repo; they are not substitutes for a valid blind holdout. Automated DrivenData portal access remains prohibited by `AGENTS.md` Rule 9; no portal or score page was scraped in this pass.

## Limitations and safe next steps

1. Keep the current state **DO NOT SUBMIT**. A locally valid TIFF is not an upload authorization or organizer-accepted file. This recheck created no file/hash/name; the inherited H86K-PSC file remains an audit artifact with a negative run card.
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
  "hypothesis": "No new lane assigned in this recheck; H86K-PSC is an upstream measured lane with a negative promotion verdict; two remaining ideas are unrun.",
  "mechanism": "H33's measured edit removes 2,545 catalogue-collar dots from the parent; the plausible DTI mechanism is reduced low-credit prediction mass, but causation of the owner-reported score change is unproven.",
  "named_non_fault_process": "For the highest-ranked remaining conductivity-neck idea: saline playa, clay-rich paleochannel, or gridding bottleneck.",
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
    "registry_input_snapshot": "701 indexed entries byte-verified; 699 grid-compatible; 2 incompatible; snapshot completeness is not public-registry completeness",
    "candidate_unique": null
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": "NOT_GENERATED",
    "inherited_local_format_validation": "30/30 pass",
    "no_nan_inside_footprint": "NOT_APPLICABLE_NO_NEW_RASTER",
    "values_in_0_1": "NOT_APPLICABLE_NO_NEW_RASTER",
    "crs_shape_transform_match": "NOT_APPLICABLE_NO_NEW_RASTER",
    "submission_authorized": false
  },
  "submission_name": null,
  "note": "This review generated no TIFF and selected no slot. Integrated upstream H86K-PSC is HOLDOUT-DTI 0.0467 [0.0380, 0.0550], n=11,321, negative paired promotion verdict; it is not organizer-confirmed.",
  "verdict": "negative"
}
```
