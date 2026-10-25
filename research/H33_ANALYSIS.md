# H33 Analysis — forensic interpretation of the owner-reported 0.2778, and what remains unproven

**Date:** 2026-10-24 (UTC)  
**Status:** OWNER-REPORTED, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained for this result. The prompt's conflicting leaderboard claims (0.3195, 0.4413) are likewise unverified owner claims.

## 1. What changed in H33 — pixel-exact forensic comparison

The pinned `GEMSDOE28` parent (`40,199` dots; owner-reported 0.2708) and `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots; owner-reported 0.2778) rasters differ in **0 cells across all 12,279,160 grid pixels** after deleting the 2,545 dots in the 1.0 < d_cat ≤ 2.0 mapped-fault collar.

In other words, H33 = GEMSDOE28 minus its 2-pixel catalogue collar, with all other dots held identical. The supplied values differ by +0.0070, but both are OWNER-REPORTED and no matching organizer receipt binds either score to these exact bytes. If the claims do bind to these rasters, the only file change is deletion of 2,545 dots in the mapped-fault collar. That establishes lineage, not why an organizer score changed or whether the deleted dots had low credit against hidden truth.

## 2. Mechanism: coverage-efficient emission, not a new geological discovery

The official metric is the asymmetric Distance-Weighted Tversky Index (DTI) with α = 0.2 (false-positive weight) and β = 0.8 (false-negative weight), evaluated with a 300 m triangular kernel (3 px radius at 100 m resolution):

```
DTI = T / (0.2·T + 0.2·F + 0.8·|G| + ε)
```

where T = weighted recovered truth credit, F = prediction mass not credited to truth (S - M), and |G| = fixed truth count (since T + FN = |G|, 0.2·T + 0.8·|G| = T + 0.8·FN).

Two algebraic facts explain H33:

**(a) Redundant mass does not increase credit.** At a truth cell, kernel credit is the *maximum* over covering predictions, not the sum. Two dots separated by 3 px (less than one kernel diameter) overlap on the same truth cell; the second dot adds false-positive cost F without adding truth credit T. Thinning redundant dots at the kernel scale lowers F while leaving T unchanged, raising DTI.

**(b) Collar pruning removes low-credit mass.** Dots within 1–2 px of a mapped trace sit on known faults. If the organizer's hidden truth already covers those cells, nearby dots add little T but add F. Deleting them (H33's collar deletion) lowers F with little T loss, raising DTI. Conversely, if a collar dot was the *only* cover of a real unmapped parallel fault, deleting it loses T and hurts.

A plausible mechanism for the reported difference is **coverage-efficient emission**: retain the same lineament field, thin redundant prediction mass at the 300 m kernel scale, and prune mass near mapped faults where it adds little hidden-truth credit. No new layer was added. This is a mechanism hypothesis conditional on the owner-reported scores, not a causal finding; hidden truth is unavailable for the pixel-level comparison.

## 3. Can we score higher than 0.2778?

**Not established.** The owner-reported 0.2778 has no organizer receipt. We cannot infer a causal improvement, and holdout results are not leaderboard projections.

Illustrative algebra only—not a score measurement or forecast: substituting the OWNER-REPORTED 0.2778 and an assumed |G| ≈ 40k into the simplified metric gives approximate T ≈ 10,963 and D ≈ 39,464 under the stated assumptions. A hypothetical +0.01 live DTI change would require ≈ 418 kernel-credit units under that model; converting this into trace length (≈42 km if every cell were hit squarely) is a geometric illustration, not a competition projection. Historical PRUNE, CONCENTRATION and RELIEF instrument deltas are not organizer scores and cannot establish a live +0.01 threshold.

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

The owner-reported H33 value is consistent with a coverage-efficiency explanation (collar pruning + kernel-scale thinning), not evidence of a new geological layer. The pixel lineage does not verify the score or prove the hidden-truth credit mechanism. Beating 0.2778 is not established: a future lane needs a gate-compliant, spatially blocked holdout improvement, and any leaderboard score still requires an organizer receipt. Concurrent PR #80's protocol-bypassing `faulthalo` binary (`IR-86-FAULTHALO-01`) has been revoked; all preserved historical research TIFFs remain audit-only (`DO NOT SUBMIT`).
