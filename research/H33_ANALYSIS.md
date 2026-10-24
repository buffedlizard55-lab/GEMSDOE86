# H33 Analysis — Why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored 0.2778 (owner-reported), and whether we can beat it

**Date:** 2026-10-24 (UTC)  
**Status:** OWNER-REPORTED, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained for this result. The prompt's conflicting leaderboard claims (0.3195, 0.4413) are likewise unverified owner claims.

## 1. What changed in H33 — pixel-exact forensic comparison

The pinned `GEMSDOE28` parent (`40,199` dots; owner-reported 0.2708) and `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots; owner-reported 0.2778) rasters differ in **0 cells across all 12,279,160 grid pixels** after deleting the 2,545 dots in the 1.0 < d_cat ≤ 2.0 mapped-fault collar.

In other words, the H33 raster is exactly GEMSDOE28 minus its 2-pixel catalogue collar, with all other dots held identical. The supplied owner-reported values differ by +0.0070, but neither is backed here by an organizer receipt; the raster comparison does not establish what caused a score change. `tests/test_h33_raster_identity.py` now binds this artifact-identity result to the source TIFF hashes.

## 2. Plausible mechanism: coverage-efficient emission, not an established score cause

The official metric is the asymmetric Distance-Weighted Tversky Index (DTI) with α = 0.2 (false-positive weight) and β = 0.8 (false-negative weight), evaluated with a 300 m triangular kernel (3 px radius at 100 m resolution):

```
DTI = T / (0.2·T + 0.2·F + 0.8·|G| + ε)
```

where T = weighted recovered truth credit, F = prediction mass not credited to truth (S - M), and |G| = fixed truth count (since T + FN = |G|, 0.2·T + 0.8·|G| = T + 0.8·FN).

Two algebraic facts explain H33:

**(a) Redundant mass does not increase credit.** At a truth cell, kernel credit is the *maximum* over covering predictions, not the sum. Two dots separated by 3 px (less than one kernel diameter) overlap on the same truth cell; the second dot adds false-positive cost F without adding truth credit T. Thinning redundant dots at the kernel scale lowers F while leaving T unchanged, raising DTI.

**(b) Collar pruning removes low-credit mass.** Dots within 1–2 px of a mapped trace sit on known faults. If the organizer's hidden truth already covers those cells, nearby dots add little T but add F. Deleting them (H33's collar deletion) lowers F with little T loss, raising DTI. Conversely, if a collar dot was the *only* cover of a real unmapped parallel fault, deleting it loses T and hurts.

A plausible mechanism for why such a raster transformation could matter under this metric is **coverage-efficient emission**: retain a high-value lineament field, thin redundant prediction mass at the 300 m kernel scale, and prune mass near mapped faults when it adds little credit. The supplied score is unverified, and this raster-only comparison cannot attribute it to that mechanism. No new layer was discovered by the pixel comparison.

## 3. Can we score higher than 0.2778?

**Not established.** The owner-reported 0.2778 has no organizer receipt. We cannot infer a causal improvement, and holdout results are not leaderboard projections.

Budget arithmetic at 0.2778 with |G| ≈ 40k: T ≈ 10,963, D ≈ 39,464. A +0.01 live DTI gain requires ≈ 418 kernel-credit units ≈ 42 km of fault trace hit squarely. All three prior reallocation sessions (PRUNE, CONCENTRATION, RELIEF) delivered |Δ| ≤ 0.0073 on the most generous instrument — short of the +0.01 evidence floor.

**Conclusion:** Concurrent PR #80 bypassed `protocol_preflight.require_feasible()` to emit a 4,210,938-cell continuous distance halo (`gems86-faulthalo-…-zeros.tif`, revoked under `IR-86-FAULTHALO-01`: `100.0%` 3-px overlap vs `17GEMSDOE`, `99.88%` vs discrete binary `13GEMSDOE`, zero geological bands, `HOLDOUT-DTI = NOT_RUN`). Scoring above 0.2778 requires:
1. A method that passes the literal uniqueness gate (currently blocked by both `17GEMSDOE` and discrete binary `13GEMSDOE`),
2. Holdout-validated improvement over a matched control with a positive paired CI,
3. A submission slot and an organizer receipt.

None of those are established in this checkout.

## 4. What fixes the "[0, 1]" rejection

The rejected file was never supplied, so its exact cause is unknown, though historical fleet inspections identified `-3.4028235e+38` Float32 nodata sentinels (`3,061` in-footprint cells in `training_features.tif`) and unclipped regression outputs as primary causes. The shared writer (`vendor/gems57/submission_writer.py`) rejects nonfinite and out-of-range predictions instead of silently clipping them, then validates the serialized single-band `float32` EPSG:32611 (`3730 × 3292`) GeoTIFF and one-TIFF ZIP on disk (`0` NaN, `0` Inf, values in `[0, 1]`, zeros outside footprint, zeros on mapped faults).

This prevents the class of invalid numerical output that triggers "Predicted values must be in range [0, 1]". Portal acceptance remains unproven without organizer authentication.

## 5. Sources (official, verified where reachable)

- Competition problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules (PDF): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- GEMSDOE32 page (owner-reported 0.2778): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- Current fleet inventory: https://buffedlizard55-lab.github.io/GEMSDOE86/docs/index.html

## Verdict

The H33 raster transformation is exactly reproducible, and coverage-efficient emission is a plausible—but unproven—mechanism for a score change; the supplied `0.2778` remains OWNER-REPORTED. Beating it is not established. Any future claim requires an authorized gate-compliant candidate, spatially blocked holdout evidence, and an organizer receipt—none is available here. The current untried hypotheses and their source limits are in `registry/untried_hypotheses_20261024.json` and `docs/evidence/hypothesis-data-availability-20261024.json`. Concurrent PR #80's protocol-bypassing `faulthalo` binary (`IR-86-FAULTHALO-01`) has been revoked; all preserved historical research TIFFs remain audit-only (`DO NOT SUBMIT`).
