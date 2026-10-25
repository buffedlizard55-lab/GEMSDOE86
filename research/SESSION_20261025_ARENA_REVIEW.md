# Independent repository review — 2026-10-25

## Decision

**NEGATIVE / DO NOT SUBMIT.** This review generated no TIFF, ran no model experiment, selected no weekly slot, and made no upload. The requested new, unique submission is **not delivered**. Existing TIFF downloads remain research/audit files; a format pass is not submission approval.

This is a three-pass review of the checked-out tree, not an organizer score receipt or a claim that no future method can work. The request's single assigned method paragraph is absent. The literal uniqueness preflight has a full-support witness; the shared cached feature stack is not present in this checkout; and the current locally obtainable registry inventory is incomplete. Running a candidate under those conditions would either break lane isolation or produce unverifiable novelty. I stopped before feature engineering, placement, or serialization.

## Pass 1 — trace evidence, identify what the H33 result does and does not say

### H33's claimed lead

The supplied **OWNER-REPORTED** H33 value is 0.2778, and the supplied parent value is 0.2708; neither is **ORGANIZER-CONFIRMED** because no submission-page receipt is in this repository. The supplied leaderboard values 0.3195 and 0.4413 are also conflicting owner-provided claims, not verified receipts. They must not be treated as scores established by this review.

Pinned-pixel forensics in [`docs/evidence/h86f-h33-forensics.json`](../docs/evidence/h86f-h33-forensics.json), independently rerun by `scripts/audit_concurrent_artifacts.py`, establish the operation—not its claimed score effect:

- H33 (SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`) is an exact subset of its parent D2.8 raster (SHA-256 `ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73`).
- It removed 2,545 dots at catalogue distances √2 to 2.0 pixels and added none. The remaining field has 37,654 dots, no dots on the mapped catalogue, and a median nearest-neighbour spacing of 3 pixels.
- The DTI code pinned in [`vendor/gems57/metric.py`](../vendor/gems57/metric.py) defines a 300 m (3-pixel) triangular kernel and asymmetric weights α=0.2, β=0.8. Per truth pixel, weighted TP is capped by the best nearby prediction; a prediction also contributes a distance-dependent FP term. Consequently, removing nearby *redundant* predictions can reduce FP penalty with little or no loss of already-saturated TP. But the removed dots were near mapped faults and could also have contributed TP; whether their removal improved DTI depends on their marginal coverage in the complete prediction set. The observed pixel edit is therefore consistent with a coverage-efficient thinning explanation, not proof of it.
- H33 did not add a new geological data layer relative to its parent. Its apparent lead in the supplied list is best explained as a small emission/spacing/near-catalogue pruning change in an existing dotted lineage—not a demonstrated new geothermal discovery mechanism. A separate geologic mechanism or causal effect has not been established.

The strongest warranted answer to “why did it score 0.2778?” is therefore: the score is unverified; the raster diff shows a 2,545-pixel collar-pruning operation that could plausibly improve this asymmetric metric by reducing redundant prediction mass. It is not possible to infer that explanation as causal without rerunning both rasters under the same exact evaluator/holdout or obtaining the competition receipt. Nor is it possible to infer from this one reported result that the model would beat the supplied 0.3195/0.4413 leaderboard claims.

### Current constraints measured in this checkout

- **REGISTRY-MEASUREMENT:** the pinned witness SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be` is positive on all 5,106,385 allowed pixels (0 uncovered). It is a historical continuous raster, not a candidate dot field; the literal support test therefore blocks any nonempty allowed prediction. This is a negative preflight, not a candidate correlation/overlap result.
- The checked-out registry-index restoration is incomplete: the current read-only byte/grid audit found 43 of 698 indexed rasters locally available and hash-verifiable. The prior pinned audit, [`docs/evidence/registry-input-grid-review-20261025.json`](../docs/evidence/registry-input-grid-review-20261025.json), records a different earlier snapshot with 690/690 bytes verified, 688 compatible grids, and 2 incompatible grids. These are differently scoped, differently timed workspace measurements; do not overwrite one with the other or infer the two incompatible rows were corrected. The new partial audit is preserved separately at [`docs/evidence/session-review-20261025/registry-input-grid-review.json`](../docs/evidence/session-review-20261025/registry-input-grid-review.json).
- **DATA-MEASUREMENT:** hash-pinned protocol grid files and the witness were restored for this review. The native training-feature TIFF and actual shared template cached feature stack are absent. `data/prepared_manifest.json` is a prior preparation manifest and explicitly says its arrays are not the shared feature stack; ignored `.cache/` arrays were not present. No candidate feature or prediction was computed.
- **REGISTRY-MEASUREMENT (limited pairwise recheck):** inherited H86F-PCC and H86F-GZZD final-dot rasters had Spearman ρ=0.0203 in either direction, and forward 3-pixel overlaps of 0.1705 and 0.1658 respectively. This is only a pairwise comparison; the registry completeness and full uniqueness clearance are false. It cannot clear any candidate.
- A fresh read-only release audit revalidated all 18 inherited TIFF artifacts locally. Every one remains **DO NOT SUBMIT**. No organizer receipt or slot selection was accessed.

## Pass 2 — ranked research options and validation feasibility

The repository's maintained queue is [`registry/h86g_hypotheses.json`](../registry/h86g_hypotheses.json). Its ranking is qualitative research triage, not a numeric DTI forecast. These four proposals use competition-native bands, so they do not require new external layers in principle. None is assigned as this session's lane or validated here.

| Rank (qualitative) | Hypothesis / layers | Physical signature and rationale for catalogue-missing faults | Difference from implementations recorded in this repo | Main named non-fault mimic | Cost / viability now |
|---|---|---|---|---|---|
| 1 | Local cross-spectral gravity–magnetic admittance breaks — Band 2 `rtp`, Band 13 `iso_grav_anom` | Windowed cross-spectrum/coherence and scale-dependent admittance break; a buried displacement or juxtaposition might change the joint density/magnetization response without a mapped surface scarp. | Not the gravity-curvature dipoles (GZZD) or signed gradient alignment (PCC); the windowed cross-spectral relationship is not implemented in `src/` or `scripts/` per the queue audit. | Unfaulted lithologic juxtaposition, source-depth change, remanent magnetization, or survey-resolution mismatch. | Medium. Native inputs suffice in principle; **not runnable now** without assigned lane, actual shared stack, complete valid comparator scope, and a permitted preflight. |
| 2 | Magnetic monogenic phase-congruency lineaments — Band 2 `rtp`, Band 13 `iso_grav_anom` | Multi-scale phase alignment may retain a weak marker whose amplitude is low; compare against gravity corroboration and amplitude-only matched-budget controls. | MMT shifts magnetic-marker responses; existing ridge/persistence methods use amplitude/derivative responses, not Riesz/log-Gabor phase congruency. | Lava-flow boundaries, dikes, interpolation ringing, or survey seams. | Medium. Same blockers as Rank 1; native layers only. |
| 3 | Persistent potential-field saddle connections — Bands 2 `rtp`, 13 `iso_grav_anom`, 15 `depth_to_base_surf` | Scale-persistent saddle-to-extremum connectors could expose buried connections missed by peak/ridge-only methods; gravity-derived depth must not be treated as independent corroboration. | Existing CTHB uses local Hessian ridges, truncations, cross-gradients and relay mechanics, not a persistence-ranked saddle-connection graph. | Intrusive contacts, erosional basement relief, or superposed unfaulted sources. | Medium–high. Same blockers; more complex extraction and controls. |
| 4 | Conductivity-neck topology conditioned on dilatation — Band 17 `cond_surf`, Band 7 `geod_shearrate`, Band 8 `geod_dilaterate` | Persistent narrow necks joining conductive regions under a strain condition could prioritize a concealed pathway without claiming a depth-resolved MT image. | Prior conductance halos and CTHB margins do not extract persistent conductive-component necks. | Saline playa sediment, clay-rich paleochannels, or interpolation bottlenecks. | Medium. Same blockers; lowest specificity and more threshold sensitivity. |

### Why the top proposal was not validated

The request says to stay within “the single method paragraph below,” but no such method paragraph identifies the lane. `AGENTS.md` makes the shared feature cache and full registry gates binding; the request's explicit lane/canary/holdout protocol also precludes selecting a different method implicitly. A fresh protocol preflight measured the universal literal overlap stop, while a complete accessible registry and the true shared cache were unavailable. The correct outcome is **not run**, not a fabricated HOLDOUT-DTI, not a new lane, and not a private override.

The four candidates do not require external data as formulated. The missing item is not a new official third-party dataset; it is the project's actual shared cached feature stack and complete compatible registry inventory, plus a lane assignment and valid protocol disposition. The user-supplied official starting points remain available for manual review: [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), and [NLR report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). These links were not freshly fetched in this review. Automated DrivenData scraping is disallowed by this repo's `AGENTS.md`; a human-accessed portal receipt is the only accepted source for an organizer score or remaining slot quota.

## Pass 3 — full request and regression check

| Requirement | Result |
|---|---|
| Read the standing prompt and repository instructions; review prior work | Met; see `PROMPT.md`, `README.md`, `AGENTS.md`, prior review reports and evidence links above. |
| Analyze H33 rather than copy it | Met as pixel forensics and metric-based plausible explanation; claimed score remains OWNER-REPORTED and causality is not established. |
| Propose 3–5 distinct hypotheses, layers/signatures/mimics/novelty/cost | Met as four queued, qualitatively ranked hypotheses; no leaderboard projection. |
| Validate top hypothesis before slot | Not met: **blocked/not run** for missing assigned lane, shared cache, and complete valid registry/protocol gate. No holdout number exists. |
| Generate a new, unique, clearly submit-approved TIFF | Not met. No TIFF was created or authorized. Existing page labels remain **DO NOT SUBMIT**. |
| Check the earlier `[0,1]` submission error | Existing releases are locally revalidated for range and grid; the exact rejected file bytes are not available, so the original portal failure cannot be diagnosed or claimed fixed at organizer level. |
| Current feed and verified sourcing | The project feed and evidence site already exist. Current 43/698 local registry availability differs from the prior 690/690 dated measurement; this irregularity is explicitly preserved for review rather than silently overwritten. No portal score/quota was scraped. |

### Verification run record

- `.venv/bin/python scripts/restore_data.py --protocol-only --include-registry`: **PASS**; restored and hash-verified the two protocol rasters and witness from pinned GitHub mirrors. This does not authenticate organizer-origin bytes or restore the 419 MB native feature TIFF/shared cache.
- `.venv/bin/python scripts/protocol_preflight.py`: **PASS as a negative stop measurement**; zero uncovered allowed cells in the pinned witness; no candidate measured.
- `.venv/bin/python scripts/audit_registry_inputs.py --output docs/evidence/session-review-20261025/registry-input-grid-review.json`: **expected nonzero (exit 1)**; 43/698 locally indexed files available and byte-verified; not complete, no candidate comparison, no uniqueness clearance.
- `.venv/bin/python scripts/audit_concurrent_artifacts.py`: **PASS for scoped inherited pair/H33 forensics only**; not full registry clearance.
- `.venv/bin/python scripts/audit_release.py --measure-registry`: **PASS audit consistency**; 18/18 inherited artifacts locally format-valid and all negative; zero experiment, zero slot.
- The current audit receipts and standalone [JSON run card](../docs/evidence/session-review-20261025/run-card.json) are retained in [`docs/evidence/session-review-20261025/`](../docs/evidence/session-review-20261025/). Historical full-inventory evidence is not overwritten.
- `.venv/bin/python scripts/build_site.py --check`, `.venv/bin/python scripts/check_site.py`, and `.venv/bin/python scripts/audit_downloads.py`: **PASS**; the pages/links and all 18 registered downloads remain negative and locally valid.
- `.venv/bin/python -m pytest -q -rs`: **802 passed, 24 skipped, 41 subtests passed** in 178.46 s. The 42 warnings are pinned Rasterio affine-operator deprecations. Skips are release-fixture/input-dependent tests and do not count as model validation.
- `git -c core.whitespace=cr-at-eol diff --check`: run before publication; preserves the ledger's CRLF convention.
- **Not run in this report:** no model fit, holdout, feature-alone leakage canary, candidate surface/dot comparison, or writer call. Those are not implied by the checks above.

## Handoff

1. Keep the download UI's **DO NOT SUBMIT** state. Do not select a slot or pass an inherited artifact off as this session's unique TIFF.
2. Resolve the missing single-lane assignment and obtain the actual shared cached feature stack with provenance/content receipt; native TIFF restoration alone does not satisfy that requirement.
3. Reconcile the registry snapshot discrepancy and incompatible-grid records without silently dropping/warping them, and obtain an explicit protocol disposition for the literal witness.
4. Only then preregister one method, whole-segment buffered folds, visible-fault-only features and exact masking; run single-feature AUC canaries first; compare paired HOLDOUT-DTI with CI to a same-split best; stop by three experiments/two hours.
5. Require full surface and final-dot registry checks using the shared comparator, shared writer, and on-disk finite/[0,1]/CRS/shape/transform validator. A separate authorized selector/portal receipt is still required before any real slot or organizer-confirmed score.
6. Check remote Pages source/deployment independently; local files and browser smoke do not prove what GitHub Pages serves.

## Run card

```json
{
  "hypothesis": "No assigned lane; top queued proposal is H86G-CSPA local cross-spectral gravity-magnetic admittance breaks, not run",
  "mechanism": "A windowed gravity-magnetic cross-spectrum/coherence and scale-dependent admittance break could flag concealed density/magnetization relationships; this session computed no such feature.",
  "named_non_fault_process": "Unfaulted lithologic juxtaposition, source-depth change, remanent magnetization, and survey-resolution mismatch",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "status": "NOT_RUN_PROTOCOL_STOP",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface_rho": null,
    "candidate_final_dot_overlap_3px": null,
    "candidate_status": "NOT_RUN_NO_CANDIDATE",
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "witness_positive_fraction_of_allowed_domain": 1.0,
    "literal_overlap_limit": 0.70,
    "complete_registry": false
  },
  "raster_sha256": null,
  "validator_output": {
    "status": "NOT_RUN_NO_NEW_RASTER",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null
  },
  "submission_name": null,
  "note": "No new TIFF; preflight stopped before experiment/placement. Existing artifacts remain audit-only; DO NOT SUBMIT.",
  "verdict": "negative",
  "new_candidate_generated": false,
  "submission_slots_used": 0
}
```
