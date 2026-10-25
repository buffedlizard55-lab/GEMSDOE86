# H33 analysis — forensic raster change and the unverified owner-reported 0.2778

**Date:** 2026-10-24 (UTC)  
**Status:** OWNER-REPORTED, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained for this result. The prompt's conflicting leaderboard claims (0.3195, 0.4413) are likewise unverified owner claims.

> **Correction / interpretation limit (2026-10-25):** The exact raster comparison below establishes only the pixel edit. It does **not** establish that the removed dots were low-credit, that their deletion caused the reported score change, or that collar pruning will generalize. The claims in the earlier wording that the score is "explained" by pruning are hypotheses, not findings. See the [interpretation review](H33_INTERPRETATION_REVIEW.md) and the current [follow-up repository review](ARENA_REPO_REVIEW_20261025_FOLLOWUP.md).

## 1. What changed in H33 — pixel-exact forensic comparison

The pinned `GEMSDOE28` parent (`40,199` dots; owner-reported 0.2708) and `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots; owner-reported 0.2778) rasters differ in **0 cells across all 12,279,160 grid pixels** after deleting the 2,545 dots in the 1.0 < d_cat ≤ 2.0 mapped-fault collar.

In other words, H33 = GEMSDOE28 minus its 2-pixel catalogue collar, with all other dots held identical. The owner-reported values differ by +0.0070, but the absence of an organizer receipt or a controlled replay means the raster edit cannot be causally assigned the score change. The 2,545 removed dots were outside the exact mapped pixels and could still have covered hidden faults.

## 2. Mechanism: coverage-efficient emission, not a new geological discovery

The official metric is the asymmetric Distance-Weighted Tversky Index (DTI) with α = 0.2 (false-positive weight) and β = 0.8 (false-negative weight), evaluated with a 300 m triangular kernel (3 px radius at 100 m resolution):

```
DTI = T / (0.2·T + 0.2·F + 0.8·|G| + ε)
```

where T = weighted recovered truth credit, F = prediction mass not credited to truth (S - M), and |G| = fixed truth count (since T + FN = |G|, 0.2·T + 0.8·|G| = T + 0.8·FN).

Two metric properties make coverage-efficient pruning plausible, but do not explain H33's reported score:

**(a) Redundant mass need not increase credit.** At a truth cell, kernel credit is the *maximum* over covering predictions, not the sum. Two dots separated by 3 px can both cover the same truth cell under the 300 m triangular kernel; a second dot may therefore add false-positive cost F without adding truth credit T. If it is redundant across all relevant truth cells, removing it can lower F while leaving T unchanged. That conditional statement is not evidence that H33's other dots were redundant.

**(b) Collar distance is not a truth mask.** H33's removed dots lie 1.0 < d_cat <= 2.0 px from mapped traces but are outside the exact mapped pixels. A nearby dot can still cover a withheld, unmapped fault. If hidden truth already supplies the relevant coverage, a removed dot may have contributed little T while adding F; if it was the only useful cover, its removal loses T and can lower DTI. The raster comparison alone cannot distinguish these cases.

Thus **coverage-efficient emission is one plausible, unverified mechanism** for the owner-reported difference. The measured deletion does not show that the removed points had low credit, that thinning caused the score change, or that a different method will score higher. No new geological layer was added in the pixel edit.

## 3. Can we score higher than 0.2778?

**Not established.** The owner-reported 0.2778 has no organizer receipt. We cannot infer a causal improvement, and holdout results are not leaderboard projections.

A previous back-of-envelope conversion from 0.2778 to implied truth credit and false-positive mass depends on an owner-reported value and an unverified hidden-truth count. It is not repeated as a score, a projection, or a required live-DTI gain here. Without organizer truth or a controlled same-split evaluation, the number of useful prediction cells or fault-trace kilometres needed for a live improvement is unknown.

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

The owner-reported H33 0.2778 is consistent with, but does not establish, coverage-efficient emission (collar pruning + kernel-scale thinning); the exact pixel edit proves no causal score mechanism. Beating that unverified value is not established. A new result would require a gate-compliant, holdout-validated method and an organizer receipt. Concurrent PR #80's protocol-bypassing `faulthalo` binary (`IR-86-FAULTHALO-01`) has been revoked; all preserved historical research TIFFs remain audit-only (`DO NOT SUBMIT`).
