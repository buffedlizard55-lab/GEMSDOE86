# H86L-VFGR preregistration (frozen before scores)

Session `arena/95120ff2-gemsdoe86`, 2026-10-25. This file is the lane assignment for
this run. It was written before `scripts/run_h86l_vfgr.py` was executed. No
coefficient, threshold, budget, or seed below may be changed after the first
holdout number is printed.

## Why this lane

The standing request says to stay inside one method. No coordinator paragraph
was inserted. The previous checkout's next unrun method was basement
mass-balance (BMR). This request also says to rank new hypotheses by expected
spatially blocked HOLDOUT-DTI improvement per cost and to validate only the
top one. Mapped-segment recovery is what that holdout measures, so the top
candidate is the visible-fault explained-edge residual (VFGR), not BMR. BMR is
arm E3 inside the same three-experiment budget so the previous next step is
measured, not silently dropped.

## Frozen arms

| Arm | Role | Layers | Operation |
|---|---|---|---|
| E1_vfgr | candidate | Band 3 `tmi_hg`, Band 5 `iso_grav_anom_slope`, visible-fault distance | Fit `edge ≈ a * exp(-d²/2σ²)` on the training quadrant only, `σ = 2.0` px, `a ≥ 0`. Residual = relu(edge − a w). Surface = training-percentile unit of `sqrt(res_mag * res_grav) * mean(coherence)`. |
| E2_raw_edge | control | Same bands, subtraction forced off | Same coherence, same emitter, same budget. |
| E3_bmr | control / previous next-step | Band 13 `iso_grav_anom`, Band 15 `depth_to_base_surf` | Training-only OLS `g ≈ a + b * Gaussian(depth, σ=8 px)`. Surface = coherent gradient magnitude of the residual. |

Emitter, frozen: `static_ek_spacing_allocate`, budget 37,654, minimum spacing
2.8 px, catalogue collar `distance > 2.0` px, candidate cap 450,000. Holdout
coefficients use only the complement of the scored quadrant. The deployment
raster refits on the full footprint; its as-is holdout number is reported
separately and is not the promotion number.

## Holdout and gates

- Split: `gems57.holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)`.
- Score: `evaluate_holdout.evaluate` + `pooled_summary` (1,000 paired 20 km block draws, seed 520810).
- Evaluator: `gems57-pooled-hide-v2`. Alpha 0.2, beta 0.8, 300 m triangular kernel.
- Visible faults masked pixel-exactly by the shared evaluator.
- Leakage canary: each arm surface alone, ROC-AUC vs withheld truth on a deterministic 400,000-pixel sample (seed 86). AUC > 0.90 stops the lane before placement.
- Same-split comparator: pinned GEMSDOE32 H33 raster scored as-is on these folds. Not a refit. Not an organizer score.
- Promotion (scientific only) requires canary pass, E1 paired 95% CI versus E2, versus E3, and versus H33-as-is all strictly above 0, and no informative (halo coverage ≤ 0.70) 3 px overlap above 0.70 and no Spearman above 0.90 on the measured registry. Incomplete registry cannot promote.
- `safe_to_submit` and `approved_for_weekly_slot` stay false. This run does not pick a weekly slot. Literal full-support witness overlap is reported and is not treated as clearance.

## Named non-fault mimic

A lithologic contact or flight-line residual that is linear, off the mapped
catalogue, and coherent in both magnetic horizontal gradient and gravity slope.
BMR's separate mimic is a lateral sediment-density change or an error in the
gravity-derived basement surface.

## Data boundary

Native competition bands only. No new external product. The template cached
feature stack is absent; this lane reads the hash-pinned native TIFF and says
so. That is not a claim that the shared cache was restored.
