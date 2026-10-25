# H86N-EQL preregistration — pure earthquake-lineation anisotropy

**Date:** 2026-10-25 UTC
**Status:** `PROPOSAL_ONLY_NOT_RUN_SHARED_CACHE_BLOCKER`
**Lane isolation:** pure native earthquake-field transform; no DEM, potential-field, conductance, fault-distance, or label-derived feature is used in the candidate surface.

This document freezes the top candidate before implementation. It does **not** authorize a weekly submission slot, claim a score, or override the repository's shared-cache and registry stops.

## Scientific hypothesis

A catalogue-missing active fault can organize the supplied earthquake-intensity field into a persistent narrow lineation even where the public fault catalogue and surface geophysics have weak expression. A compact geothermal injection swarm or volcanic swarm can also be intense, but should be less line-like or less persistent across Gaussian scales. The candidate therefore targets **multi-scale lineation anisotropy**, not raw earthquake intensity.

The nominated non-fault mimic is an induced geothermal injection swarm or volcanic dike swarm with an elongated event cloud. A positive result would not identify a fault or geothermal vent by itself; it would only justify an independent spatially blocked test against controls.

## Frozen inputs and feature design

| Input | Use | Leakage rule |
|---|---|---|
| Native Band 16 `ieq_n100a15` | log1p intensity/density; 2 px and 4 px Hessian line-ridge response | Read from the shared pinned stack only; no labels or fault mask in the full surface |
| Native Band 10 `deq_n100a15` | distance/closeness control and descriptive ablation | It is not multiplied into the EQL mechanism; if it is used in a fold, recompute from visible catalogue faults only or keep it as the supplied non-label seismic transform exactly as the shared stack specifies |
| Footprint | output mask | Values outside the footprint are zero in the local conservative export policy |

For each scale, compute the Hessian eigenvalues of the smoothed log-intensity field. The bright-ridge response is the positive part of the negative smaller eigenvalue; anisotropy is the clipped difference between the absolute eigenvalues divided by their sum. Rank the ridge and anisotropy only inside the footprint. The frozen candidate is:

```text
lineation = sqrt(rank(ridge_sigma_2) * rank(ridge_sigma_4))
EQL = lineation * (0.35 + 0.65 * rank(anisotropy_sigma_4))
      * (0.50 + 0.50 * rank(log1p(ieq)))
```

The preregistered controls are: `E0_IEQ_intensity` (intensity only), `E1_DEQ_closeness` (distance/closeness only), `E2_catalogue_edge` (smoothed intensity gradient), and `E3_single_scale_ridge` (one-scale ridge). These are controls/ablations, not additional unregistered experiments. Do not tune coefficients after seeing holdout results.

## Required gates before any TIFF

1. **Shared cache:** use the hash-pinned shared template feature cache, not merely `.cache/gems_work/bands/` prepared from the native TIFF. If the cache receipt is absent or fails, stop and record `NOT_RUN_SHARED_CACHE_BLOCKER`.
2. **Preflight:** verify `PROMPT.md`, shared tool hashes, native input hashes, sample grid, existing-fault mask, registry inventory, and a frozen run card before feature work.
3. **Holdout:** use `gems57.holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)` with whole fault components and a context buffer. Derive catalogue-based features from visible faults only; mask visible faults pixel-exactly; use the unchanged `gems57-pooled-hide-v2` evaluator with alpha 0.2, beta 0.8, 300 m triangular kernel, pooled physical-block bootstrap, 95% CI, and a recorded withheld-positive count.
4. **Canary:** score every individual feature on the holdout. Any discriminative AUC above 0.90 is leakage until proven otherwise and stops the lane.
5. **Baseline:** compare the candidate on the same split against the current comparable `HOLDOUT-DTI` baseline and fold-fair controls. No different-fold maximum is called a baseline.
6. **Uniqueness:** run the unchanged shared registry comparator on the continuous surface before dot placement and on final dots after placement. Stop on Spearman greater than 0.90 or forward 3-pixel overlap greater than 0.70. Use the complete compatible registry; local subset measurements are not clearance.
7. **Writer/format:** only after all scientific and uniqueness gates pass, use the shared `submission_writer.py` to emit one single-band float32 GeoTIFF, validate finite `[0,1]`, CRS/shape/transform, exact footprint policy, ZIP, SHA-256, unique name, and note no longer than 140 characters. Keep slot selection separate.

## Budget and decision rule

At most three arms/experiments and two hours. The lane can produce a negative audit artifact; a negative result is a deliverable. The candidate may be marked `promote` only if it beats the same-split current best with the preregistered CI rule **and** every canary, registry, format, and source gate passes. Otherwise the run card must say `verdict: negative`, `decision: DO NOT SUBMIT`, `safe_to_submit: false`, `approved_for_weekly_slot: false`, and `submission_slots_used: 0`.

Every numeric result must be labeled `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` from a saved organizer receipt. Projections, expected DTI, SGMC diagnostics, and local format/registry measurements are not scores.

## Current blocker

The native `training_features.tif` has been restored and its SHA-256 is pinned, but `docs/evidence/feature-cache.json` names a shared cache that is not present. Native prepared arrays are explicitly not accepted as proof of the shared cache. The pure H86N-EQL lane is therefore specified but **not run**; no H86N TIFF, holdout score, or submission receipt exists.
