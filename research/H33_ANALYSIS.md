# H33 Analysis — Why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored 0.2778 (owner-reported), and whether we can beat it

**Date:** 2026-10-24 (UTC)  
**Status:** OWNER-REPORTED, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained for this result. The prompt's conflicting leaderboard claims (0.3195, 0.4413) are likewise unverified owner claims.

## 1. What changed in H33 — pixel-exact forensic comparison

The pinned `GEMSDOE28` parent (`40,199` dots; owner-reported 0.2708) and `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots; owner-reported 0.2778) rasters differ in **0 cells across all 12,279,160 grid pixels** after deleting the 2,545 dots in the 1.0 < d_cat ≤ 2.0 mapped-fault collar.

In other words, H33 = GEMSDOE28 minus its 2-pixel catalogue collar, with all other dots held identical. The score moved from 0.2708 to 0.2778 (+0.0070 owner-reported) purely by removing 2,545 low-credit dots from the mapped-fault collar.

## 2. Mechanism: coverage-efficient emission, not a new geological discovery

The official metric is the asymmetric Tversky index (DTI) with α = 0.2 (false-negative cost) and β = 0.8 (false-positive cost), evaluated with a 300 m triangular kernel (≈ 3 px radius at 100 m resolution):

```
DTI = T / (0.2·T + 0.2·F + 0.8·N + ε)
```

where T = weighted recovered truth credit, F = weighted false-positive mass, N = fixed truth count.

Two algebraic facts explain H33:

**(a) Redundant mass does not increase credit.** At a truth cell, kernel credit is the *maximum* over covering predictions, not the sum. Two dots separated by 3 px (less than one kernel diameter) overlap on the same truth cell; the second dot adds false-positive cost F without adding truth credit T. Thinning redundant dots at the kernel scale lowers F while leaving T unchanged, raising DTI.

**(b) Collar pruning removes low-credit mass.** Dots within 1–2 px of a mapped trace sit on known faults. If the organizer's hidden truth already covers those cells, nearby dots add little T but add F. Deleting them (H33's collar deletion) lowers F with little T loss, raising DTI. Conversely, if a collar dot was the *only* cover of a real unmapped parallel fault, deleting it loses T and hurts.

So H33's 0.2778 is explained by **coverage-efficient emission**: retain high-value lineament field, thin redundant prediction mass at the 300 m kernel scale, prune mass near mapped faults when it adds little credit. No new layer was discovered.

## 3. Can we score higher than 0.2778?

**Not established.** The owner-reported 0.2778 has no organizer receipt. We cannot infer a causal improvement, and holdout results are not leaderboard projections.

Budget arithmetic at 0.2778 with |G| ≈ 40k: T ≈ 10,963, D ≈ 39,464. A +0.01 live DTI gain requires ≈ 418 kernel-credit units ≈ 42 km of fault trace hit squarely. All three prior reallocation sessions (PRUNE, CONCENTRATION, RELIEF) delivered |Δ| ≤ 0.0073 on the most generous instrument — short of the +0.01 evidence floor.

**Conclusion:** We *can* generate a unique submission TIF (done: `gems86-faulthalo-…-zeros.tif`, format-valid, values in [0,1]), but scoring above 0.2778 requires:
1. A method that passes the literal uniqueness gate (currently blocked by the full-support 17GEMSDOE witness),
2. Holdout-validated improvement over a matched control with a positive paired CI,
3. A submission slot and an organizer receipt.

None of those are established in this checkout. The generated TIF is **format-valid for the portal** (fixes the "[0,1]" rejection) but **not authorized for submission** under the current protocol stop.

## 4. What fixes the "[0, 1]" rejection

The rejected file was never supplied, so its cause is unknown. The shared writer in this repo rejects nonfinite and out-of-range predictions instead of silently clipping them, then validates the serialized TIFF and ZIP. The generated TIF here has:
- 0 NaN, 0 Inf
- min = 0.0, max = 0.93 (inside [0,1])
- single-band float32, EPSG:32611, 3730 × 3292, pinned transform
- zeros outside the footprint, zeros on mapped faults

This prevents the class of invalid numerical output that triggers "Predicted values must be in range [0, 1]". Portal acceptance remains unproven.

## 5. Sources (official, verified where reachable)

- Competition problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules (PDF): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- GEMSDOE32 page (owner-reported 0.2778): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- Current fleet inventory: https://buffedlizard55-lab.github.io/GEMSDOE86/docs/index.html

## Verdict

H33's 0.2778 is plausibly explained by coverage-efficient emission (collar pruning + kernel-scale thinning), not by a new geological layer. Beating it requires a gate-compliant, holdout-validated method plus an organizer receipt — none established here. The unique TIF generated in this session is **safe to download for audit** but **NOT authorized for submission** under the current literal overlap stop.