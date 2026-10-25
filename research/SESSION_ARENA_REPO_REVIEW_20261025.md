# Repository review — 2026-10-25

## Executive decision

**DO NOT SUBMIT. No new TIFF, model experiment, or weekly slot was created or used.** This is a fresh repository and release review, not a new geology lane. The request archive contains no unique assigned method paragraph, the actual shared cached feature stack is absent, and the unchanged literal uniqueness preflight has a hash-pinned full-support counterexample. Generating a candidate despite those stops would contradict the standing protocol and would not establish uniqueness or scientific value.

The requirement for a newly generated unique competition TIFF therefore remains **unmet**. Existing audit-only downloads must not be represented as this session's output or as upload-authorized.

## Three-pass review

### Pass 1 — source, provenance, and pipeline

- Read `PROMPT.md`, `README.md`, `AGENTS.md`, and the entire archived owner request at `research/REQUEST_20261025.md` before evaluating the project state.
- Confirmed the checkout is on `arena/ca001cd4-gemsdoe86`, initially clean and based on `782b4d1` (the checked-out `origin/main`); no open PR was already present for this branch.
- Checked `data/prepared_manifest.json`: the native feature raster's bands had been prepared in a prior run, but `shared_template_feature_stack` is `false`. The native TIFF or its mirrored bytes are not the template's cached derived feature stack required by the reuse protocol.
- The local root copies of `sample_submission.tif` and `existing_faults.tif` were absent. Restored them via the repository's pinned `scripts/restore_protocol_data.py --include-registry`; SHA-256 and byte lengths matched the checked-in manifest. Their receipt explicitly says owner-supplied mirrors and **not organizer-authenticated**. Restoring them did not obtain the missing feature cache or create a prediction.
- The tracked shared evaluator/writer pin checks passed as part of the release audit. No vendor tool or method implementation was changed.

### Pass 2 — stop-gate and scientific review

- Refreshed the hash-pinned protocol measurement and complete local release audit. The current `REGISTRY-MEASUREMENT` reports 5,106,385 allowed cells, zero uncovered by the pinned witness, and a literal support-overlap fraction of 1.0 against the unchanged 0.70 stop. It measures one witness from an incomplete registry snapshot; it is a sufficient negative under the literal rule, **not** a complete uniqueness clearance and not evidence that physical mechanisms are duplicates.
- The current request does not assign one method paragraph. The top previously ranked CSPA candidate (local gravity–magnetic cross-spectral admittance) is a proposal, not an executed or newly validated idea. Since the stop and missing shared cache remain, no holdout, leakage canary, surface comparison, dot placement, or submission serialization was run.
- The repo's latest ranked queue already records four distinct native-layer proposals. They are ranked qualitatively, not scored or proven:

| Rank | Candidate / layers | Target signature and rationale | Main non-fault mimic | Cost / status |
|---|---|---|---|---|
| 1 | **CSPA** — native B13 `iso_grav_anom` + B2 `rtp` | Localized, multiscale gravity–magnetic cross-power/coherence and admittance breaks beneath cover; targets buried density/susceptibility juxtaposition, not another single-layer ridge. | Basalt flow margin or buried lithologic contact; source-depth and survey-resolution changes. | Medium; highest qualitative incremental potential in the archived queue; **not run here**. |
| 2 | **MPC** — B2 `rtp` + B13 gravity | Multiscale monogenic/Riesz phase congruency; seeks weak, covered structural transitions less dependent on amplitude than standard edges. | Remanently magnetized volcanic contacts and flight-line seams. | Medium; prior MPC work exists in the repository, so this is not a clean new lane without a fresh precise method definition. |
| 3 | **PSC** — B2, B13, B15 `depth_to_base_surf` | Persistence of basin/basement saddle-connection topology across smoothing scales; could identify covered relay geometry not expressed as a surface trace. | Paleovalley or erosional basin neck. | Medium-high; no executable persistence method identified in the archived queue; **unrun proposal**. |
| 4 | **CNT** — B17 `cond_surf`, B8 `geod_dilaterate`, B7 `geod_shearrate` | Conductive-neck topology conditioned on dilatation; seeks a concealed permeability corridor rather than a simple conductivity high. | Saline playa or clay-rich channel fill. | Medium, high confounding risk; **unrun proposal**. |

These are inherited candidates listed in the existing repo, not a claim of novelty across every GEMSDOE site. No new external data is proposed as viable; each candidate above uses native bands. The shared-cache requirement remains unmet regardless.

### Pass 3 — adversarial/reproducibility checks

Commands and outcomes:

```text
.venv/bin/python scripts/restore_protocol_data.py --include-registry
  PASS — restored pinned owner mirrors; not organizer-authenticated.

.venv/bin/python scripts/protocol_preflight.py
  PASS as a measurement; STOP_LITERAL_OVERLAP_UNSATISFIABLE.
  One witness measured; registry_complete=false; candidate_generated=false.

.venv/bin/python scripts/audit_release.py --measure-registry
  PASS — audit_ok=true; DO NOT SUBMIT; 28/28 inherited artifacts locally valid;
  experiments_run=0; submission_slots_used=0.

.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
.venv/bin/python scripts/audit_downloads.py
  PASS — generated site consistent; links and historical TIFF/ZIP integrity pass;
  negative-state safety only, not scientific/organizer clearance.

.venv/bin/python -m pytest -q
  957 passed, 24 skipped, 48 warnings, 58 subtests passed (294.65 s).

git diff --check
  PASS.
```

A parallel first attempt to build the site while refreshing the mutable preflight evidence briefly observed a stale hash binding. The prescribed sequential all-artifact audit refreshed dependent hashes; subsequent site, download, and test checks passed. This was caused by concurrent execution in this review, not evidence of a reproducible product defect. The initial audit also stopped because root-grid copies were absent; restoration from the pinned mirror resolved that prerequisite.

## H33 / score interpretation

- The supplied `0.2778` for `GEMSDOE32 h33-h33-2-b2` is **OWNER-REPORTED**, not ORGANIZER-CONFIRMED: no DrivenData submission-page receipt was present or obtained. The other leaderboard numbers in the request are likewise not independently verified here.
- Pixel forensics in existing repository evidence establish an operation, not causation: H33 is the parent dot raster with 2,545 pixels removed at catalogue distances √2–2 pixels and no added dots. The proposed metric mechanism is that, under a 300 m distance-weighted score, redundant near-catalogue predictions can add false-positive cost after truth credit is saturated by a nearby prediction. That is a plausible mechanism, **not proof** that pruning caused the reported private leaderboard result.
- Whether a new candidate can exceed the reported value is **unknown**. No comparison between the archived holdout and a private leaderboard is justified without matched validation and organizer receipts. No leaderboard projection is made.

## Sources for independent verification

The repository's established source index provides these primary/reference links; they were **not freshly fetched in this sandbox review**. DrivenData was not scraped, and no source page is presented as a fresh observation:

- [Competition problem and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE Geothermal Data Repository submission 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)

The above are sources to verify method/data rules, not receipts confirming any claimed score or account status. Owner-provided mirrored bytes remain labelled unauthenticated unless a competition receipt proves otherwise.

## Limitations and handoff

1. Obtain/identify the **actual shared cached feature stack** and its preprocessing/footprint provenance. Do not reconstruct it privately and call it template reuse.
2. Resolve the protocol's full-support uniqueness contradiction through an explicit owner-level rule clarification; do not silently weaken or bypass a gate. Preserve the full-registry scan and report incompatible-grid entries transparently.
3. Assign exactly one distinct method paragraph. Before any experiment, bind every feature to visible-fault-only derivation, withhold buffered whole fault segments, mask visible faults pixel-exactly, and use the shared evaluator/writer.
4. Run each feature's leakage canary first; require a matched spatial holdout with paired uncertainty against the strongest comparable baseline. The three-experiment/two-hour budget and separate slot selector remain binding.
5. Only a submission-page receipt can establish organizer-confirmed score or slot availability. The exact bytes from the earlier `[0,1]` portal rejection are unavailable, so its cause cannot be diagnosed from this repo.
6. Do not scrape DrivenData. A fresh public Pages deployment state or contest acceptance is not inferred from local site tests.

## Run card

```json
{
  "hypothesis": "No candidate hypothesis was assigned or tested in this review; archived CSPA is only a ranked proposal.",
  "mechanism": "None measured; no candidate surface or placement was constructed.",
  "named_non_fault_process": "For the leading archived CSPA proposal: an unfaulted basalt flow margin or buried lithologic contact, source-depth change, or survey-resolution mismatch.",
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
    "candidate_surface": "NOT RUN",
    "candidate_final_dots": "NOT RUN",
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "allowed_pixels": 5106385,
    "uncovered_allowed_pixels": 0,
    "literal_forward_overlap": 1.0,
    "threshold": 0.70,
    "registry_complete": false,
    "interpretation": "Sufficient literal negative; not complete uniqueness clearance."
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": "NOT RUN; no new raster",
    "values_in_0_1": "NOT RUN; no new raster",
    "crs_shape_transform_match": "Inputs pinned and checked; no new raster"
  },
  "submission_name": null,
  "note": "Review only; no new TIFF, no upload authorization, zero experiments and zero slots.",
  "verdict": "negative"
}
```
