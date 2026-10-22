# GEMSDOE86 — reproducible GEMS fault-prediction workspace

> **Current release gate: BLOCKED — no authorized competition data or validated submission TIFF is present. Do not download or submit a raster from this repository.**
>
> This branch has produced **no experiment, no HOLDOUT-DTI result, no validation receipt, and no submission file**. The download control on the public site is intentionally disabled until the full evidence gate passes.

## Aim and standing project prompt

Build and maintain a reproducible, auditable workflow for the DOE GEMS Prize: identify *previously unmapped faults with geothermal significance*, create a unique probability GeoTIFF only when the evidence supports it, and make the valid artifact and executive submission instructions obvious. Optimize for the Arena Core Values **“Maximize P(Win)”** and **“Own the Outcome”** without trading away scientific integrity, data provenance, or competition rules.

Before implementation, review prior art and rank **3–5 genuinely distinct hypotheses**. Verify that each proposed source can be obtained and covers the competition area; do not call a candidate viable until that check is complete. Select at most one candidate for the spatially blocked hide-and-recover holdout. Use the shared feature cache, evaluator, and writer unchanged; do not copy a registry submission into this repository or use one as a candidate. Withhold whole fault components/segments, keep a spatial buffer between hidden truth and visible fault-derived features, derive every catalogue feature from visible faults only, and mask visible faults pixel-exactly. Use pooled DTI with **α=0.2, β=0.8, and the 300 m triangular kernel**. Test each feature alone for leakage; **AUC >0.90 is a leakage alarm** until investigated and resolved.

A performance result must be labelled **HOLDOUT-DTI** with evaluator version, withheld-positive count, and 95% confidence interval, or **ORGANIZER-CONFIRMED** with an organizer receipt. Keep owner-reported claims separate. Stop and record the candidate as a duplicate if either its unthresholded surface or final raster has rank correlation **>0.90** with a registry raster, or if **>70%** of its dots lie within 3 px of one registry raster. Enforce validator checks and the shared writer’s checks; never repair an invalid raster by hand. Generate a unique, submission-ready TIFF only after every gate passes. Do not spend more than **3 experiments or 2 hours** on a run. Weekly-slot promotion is a separate selector decision, never an automatic side effect of holdout performance.

Keep the site current, highlight download/submission readiness (or the reason it is blocked), and put concise executive submission instructions beside the download state. Perform three review passes, record irregularities and limitations, use official sources where possible, and finish every run with the JSON card at [`docs/data/run-card.json`](docs/data/run-card.json). The complete workflow and review log are in [`docs/`](docs/).

## Current verified state

- The public DrivenData data page redirects to login in this session. Competition data were **not** downloaded. The public GDR INGENIOUS page is accessible, but its resource files were **not** downloaded.
- The inspected shared implementation is `gems57-pooled-hide-v2` in the read-only GEMSDOE83 reference clone. It was **not executed** here. No cached feature stack, complete registry index, or verified training raster is present in this checkout.
- A public USGS ScienceBase record lists five Great Basin MT-conductance GeoTIFFs and a catalog bounding box that contains the coarse screening window, but an associated world file reports 1000/−1000 map-unit pixels and a projected-looking origin while the raster facet declares EPSG:4269. The GeoTIFF bytes/internal tags and exact valid-data coverage have not been checked. This unresolved source-metadata discrepancy makes the lead conditional, not an experiment.
- The official public leaderboard snapshot fetched **2026-10-22 UTC** lists xiaofanhu at **0.4413** (**ORGANIZER-CONFIRMED public-board entry**; not a GEMSDOE86 result or an artifact receipt). The H33 **0.2778** assertion remains owner-reported and unverified; another owner-controlled page explicitly says no organizer score exists for artifacts in that repository.
- No TIFF/ZIP has been generated. **No candidate is safe to submit.** See the [live project status](https://buffedlizard55-lab.github.io/GEMSDOE86/) after Pages is deployed.

## Reproducibility and data policy

This repository deliberately does not vendor or fork the shared evaluator/writer, contain public registry TIFFs, or fabricate a placeholder submission. Use a separately prepared, pinned shared-tool checkout and an authorized data/cache location; point the preflight at them with environment variables. The preflight only checks that prerequisites exist. It does **not** validate rasters, run the evaluator, certify uniqueness, or approve a submission.

```bash
python scripts/preflight.py
python -m unittest discover -s tests -v
python scripts/check_site.py
```

Preflight inputs (set only after preparing the authorized materials):

- `GEMS_DATA_DIR` — directory containing `training_features.tif`, `labels.tif`, `existing_faults.tif`, and `sample_submission.tif`.
- `GEMS_FEATURE_STACK` — exact cached feature-stack file to reuse.
- `GEMS_SHARED_TEMPLATE` — separately checked-out shared template containing `vendor/gems57/evaluate_holdout.py` and `vendor/gems57/submission_writer.py`.
- `GEMS_REGISTRY_INDEX` — complete, hash-verified registry index required by the shared uniqueness gate.

See [`docs/executive-summary.html`](docs/executive-summary.html), [`docs/research/hypotheses.md`](docs/research/hypotheses.md), [`docs/research/prior-art-and-irregularities.md`](docs/research/prior-art-and-irregularities.md), [`docs/sources.md`](docs/sources.md), and [`docs/data/run-card.json`](docs/data/run-card.json).
