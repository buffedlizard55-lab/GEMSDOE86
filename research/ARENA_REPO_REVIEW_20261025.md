# GEMSDOE86 repository review — 2026-10-25

## Executive decision

**NO — do not submit any current file.** This pass made no candidate TIFF, did not train a model, did not consume a competition slot, and did not modify thresholds, evaluator code, or writer code. The project contains research/audit TIFFs, but the current release audit explicitly marks all as **DO NOT SUBMIT**. A local-format pass is not uniqueness clearance, organizer acceptance, or slot authorization.

This review follows the current request archive (`research/REQUEST_20261025.md`), `PROMPT.md`, and `AGENTS.md`. The archived request is owner input, not verified competition evidence. In particular, the supplied H33 value `0.2778` and the competing `0.3195` / `0.4413` leaderboard claims are **OWNER-REPORTED**, not organizer-confirmed receipts in this repository. No claim that a new method exceeds any of those values is made.

## Three-pass review

### Pass 1 — provenance and codebase review

- The repository is a mature, guarded research pipeline, not a single model: it contains the shared vendored `gems57` evaluator/writer, more than twenty lane-specific feature/model packages, numerous frozen preregistrations, receipts, audits, and a generated GitHub Pages site.
- Read the current request archive and standing rules. The current prompt does **not** assign a single method paragraph. The previous ranked queue in `registry/h86g_hypotheses.json` is a historical proposal list, not current permission to experiment.
- The template’s actual derived feature cache is not available. `data/prepared_manifest.json` is a historical/native-band preparation receipt, explicitly says `shared_template_feature_stack: false`, and does not prove that its listed prepared arrays are present now. In this checkout, `data/training_features.tif` and the prepared arrays under `.cache/gems_work/bands/` are absent. The upstream receipt names an ephemeral `/tmp/gems32/work/feature_stack.npy`, but those cache bytes are not in this checkout. The native training TIFF, even when restored, is not a substitute for the template cache.
- Hash-verified protocol rasters and the historical registry witness were restored from the pinned mirrors solely to run the required read-only integrity checks. Mirror byte identity does not independently authenticate the competition’s original portal bytes.
- The shared evaluator/writer check and release reports remain unchanged; no private metric, writer, or feature-cache fork was introduced.

### Pass 2 — automated verification and scientific stop conditions

Commands run from the repository root:

```text
.venv/bin/python scripts/restore_data.py --protocol-only --include-registry
  PASS: restored hash-pinned sample_submission, existing_faults, and registry witness
.venv/bin/python scripts/audit_release.py
  PASS: audit_ok=true; FORMAT/INTEGRITY-VALIDATION 28/28; decision DO NOT SUBMIT;
        0 experiments and 0 slots
.venv/bin/python scripts/audit_release.py --measure-registry
  PASS: all inherited final artifacts remeasured; decision DO NOT SUBMIT;
        0 experiments and 0 slots
.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
  PASS: generated Pages consistency, links, registered TIFF/ZIP integrity,
        and negative-state safety (not scientific clearance)
.venv/bin/python scripts/audit_downloads.py
  PASS: 28 research TIFFs and receipts revalidated; no authorization inferred
.venv/bin/python scripts/build_review_card.py --check
  PASS: frozen review evidence consistent
.venv/bin/python -m pytest -q
  PASS: 957 passed, 24 skipped, 58 subtests passed; 48 Rasterio deprecation warnings
```

`python scripts/verify_band_physics.py` was also attempted and **could not run** because `data/training_features.tif` is absent (`FileNotFoundError`). This is not a failed scientific result; it confirms a missing input. The protocol-only restore intentionally does not download the 419 MB feature raster, and even restoring that raster would not provide the required shared derived cache.

**REGISTRY-MEASUREMENT — unchanged literal rule:** `docs/evidence/protocol-preflight.json` records the pinned `17GEMSDOE` witness SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`. It directly covers all 5,106,385 allowed cells (zero uncovered), so any nonempty candidate restricted to allowed cells has 100% forward overlap with this witness, greater than the unchanged 70% stop. This proves a literal-rule stop; it does not prove that all geologic mechanisms are duplicates. The input-grid audit has 690 byte-verified registry rasters, of which 688 are grid-compatible and two are incompatible/invalid; the inventory is not complete. A partial inventory can reject but cannot certify uniqueness. No candidate surface or final dots were constructed in this review.

### Pass 3 — edge cases, stale evidence, and safe next actions

- The missing-cache distinction matters: a manifest that says native bands were prepared cannot substitute for the actual template feature stack or prove the cache exists. This review refuses to infer presence from the historical manifest.
- Historical proposal status is stale in places. `registry/h86g_hypotheses.json` said its magnetic phase-congruency lane was not implemented, but later H86J-MPC and H86J-MCSP work exists in this repository. Similarly, a gravity–magnetic cross-spectral idea must be compared with the later H86J-CSGD implementation before being called untried. The frozen proposal file is preserved; do not rewrite history or rerun those same ideas under new names.
- The immutable full-support witness and missing explicit lane assignment prevent a scientifically valid experiment under the current written rules. Do not weaken the 0.70 stop, treat dot uniqueness as a substitute for the literal surface rule, or publish an audit TIFF as a competition-ready download.
- The current site’s “safe to download” wording means **safe for research/audit only**. A human-free automated integrity gate exists, but it correctly reports **no file authorized to submit**. The site must not present the research downloads as upload-ready.

## Ranked research queue (proposals only; no experiments authorized)

Ranking is qualitative expected information beyond existing methods versus implementation cost. It is not an expected score, DTI projection, or promise of novelty across the external project fleet. Bands below follow `src/gems86/io.py:BANDS`.

| Rank | Candidate and specific layers | Signature and why it could find an uncatalogued structure | Difference from this checkout | Main non-fault mimic | Potential / cost |
|---|---|---|---|---|---|
| 1 | **Persistent potential-field saddle connections** — Band 2 `rtp`, Band 13 `iso_grav_anom`, Band 15 `depth_to_base_surf` | Track scale-persistent saddle-to-extremum connectors between potential-field anomaly bodies; a buried connecting structure can lack a surface scarp and may not rank as an isolated edge or peak. Gravity-derived depth is not independent corroboration. | A different representation—persistence-ranked graph topology—rather than the local Hessian ridges, truncations, cross-gradients, and visible-fault relays in CTHB. | Intrusive contacts, erosional basement relief, and saddles created by superposed sources. | Medium qualitative potential; medium-high cost; needs graph/persistence controls. Existing preregistration entry H86G-PSC; NOT RUN under current stop. |
| 2 | **Conductivity-neck topology conditioned on strain** — Band 17 `cond_surf`, Band 7 `geod_shearrate`, Band 8 `geod_dilaterate` | Identify narrow, threshold-persistent connections between conductive components specifically in positive dilatation; a buried fluid-pathway hypothesis does not require a visible scarp. One surface-conductance band cannot establish depth or geothermal origin. | Persistent component-neck geometry, rather than raw conductivity highs, conductive margins, or a generic conductivity/strain fusion. | Saline playa deposits, clay-rich paleochannels, and gridding bottlenecks. | Low-to-medium qualitative potential because conductivity is nonspecific; medium cost. Existing preregistration entry H86G-CNT; NOT RUN under current stop. |
| 3 | **Local multiband directional-semivariogram break** — Band 2 `rtp`, Band 13 `iso_grav_anom`, optionally Band 17 `cond_surf` and Band 8 `geod_dilaterate` as independent context | Look for a spatially localized change in directional correlation length / anisotropy that persists across windows and is compatible with a basement discontinuity. It may detect a covered fault corridor where isolated gradients are weak, without using catalogue proximity to nominate it. | Second-order spatial-statistics change-point test rather than a ridge/edge detector, phase-congruency score, or classifier over pointwise pixels. A source-code search found no directional-semivariogram implementation, but this is only checkout-scoped novelty. | Lithologic boundaries, volcanic flow fabrics, interpolation/tie-line seams, and basin-fill texture changes. | Low and speculative qualitative potential; medium-high cost due to resolution/window controls and spatially blocked nulls. **New proposal for review only; not preregistered or implemented.** |

Do not start any of these until the single lane is explicitly assigned, cache provenance is resolved, the registry stop is addressed through a shared/upstream protocol disposition (not a private threshold change), and incompatible registry rows have an auditable policy. Every feature would require a feature-alone leakage canary and whole-segment hide-and-recover evaluation with visible-catalogue-only features, pixel-exact masking, pooled DTI, and physical-block confidence intervals.

## H33 interpretation and current scientific limits

The independent H33 forensic review in `research/SESSION_20261025_CF73474C_REVIEW.md` reports that the H33 raster is the parent 40,199-dot GEMSDOE28 raster after removing 2,545 dots inside the two-pixel catalogue collar, with no added dots. That is a raster-measurement result, not causal proof of the owner-reported score change. The metric can reward pruning redundant false-positive mass if lost truth-kernel credit is sufficiently small, but the exact change in an organizer score cannot be inferred from that operation alone. Holdout scores from differing folds, buffers, feature availability, and bootstrap designs cannot be compared as a single “current best.” No projection is a score.

Fault-likelihood prediction is also not confirmation of a geothermal vent, heat supply, permeability, or commercial viability. Even an eventual organizer-confirmed leaderboard result would evaluate the competition target—not establish a geothermal resource without independent geologic and field evidence.

## Verified-source links for follow-up

These are official or standards references already registered in the repository; they are supplied for review, not asserted as newly fetched in this pass.

- [DrivenData GEMS problem statement and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — do not automate portal access; organizer confirmation requires a user-visible receipt.
- [DrivenData competition entry and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [USGS DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [DOE/NREL Geothermal Data Repository — INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611 / WGS 84 UTM zone 11N](https://epsg.io/32611)

## Limitations and next work

1. Obtain the actual template-derived cache and its generating-code/input hashes from the shared upstream template; do not privately rebuild and mislabel it.
2. Resolve the literal witness blocker in shared/upstream tooling or document an owner-approved interpretation before any candidate generation. This review does not authorize a threshold change.
3. Restore a complete, current accessible registry and explicitly adjudicate the two incompatible grids without silently warping or dropping rows.
4. Assign one method paragraph, preregister a single lane, test each feature alone, and evaluate against matched current controls on the pinned shared evaluator. Stop after three experiments or two hours.
5. Keep upload selection separate. The weekly cap, organizer leaderboard state, and organizer-confirmed score are not available from this audit; no submission page was accessed.
6. Keep the site’s release state as **DO NOT SUBMIT** unless scientific gates, full-registry uniqueness, format checks, and the separate slot selector all pass. Record an organizer receipt before labeling any result ORGANIZER-CONFIRMED.

## Run card — this review only

```json
{
  "hypothesis": "No candidate lane selected or tested; the three ranked items above are proposals only.",
  "mechanism": "No new mechanism measured. Existing H33 pixel-operation interpretation is archived forensic evidence, not a causal score explanation.",
  "named_non_fault_process": "No candidate mimic tested; proposal-specific mimics are enumerated in the table.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "NOT_RUN_NO_LANE_ASSIGNED"
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface": null,
    "candidate_final_dots": null,
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "allowed_cells": 5106385,
    "uncovered_allowed_cells": 0,
    "literal_forward_overlap_for_any_nonempty_allowed_candidate": 1.0,
    "overlap_limit": 0.7,
    "registry_scope": "690 byte-verified registry files; 688 grid-compatible and 2 incompatible/invalid; inventory incomplete; no candidate uniqueness clearance"
  },
  "raster_sha256": null,
  "validator_output": {
    "status": "NO_NEW_RASTER",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "inherited_artifacts": "FORMAT/INTEGRITY-VALIDATION 28/28; audit decision DO NOT SUBMIT"
  },
  "submission_name": null,
  "note": "Repository review only; no new TIFF, experiment, or competition slot.",
  "verdict": "negative"
}
```
