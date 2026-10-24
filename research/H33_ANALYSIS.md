# H33 Analysis — Why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored 0.2778 (owner-reported), and whether we can beat it

**Date:** 2026-10-24 (UTC)  
**Status:** OWNER-REPORTED, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained for this result. The prompt's conflicting leaderboard claims (0.3195, 0.4413) are likewise unverified owner claims.

## 1. What changed in H33 — pixel-exact forensic comparison

The pinned `GEMSDOE28` parent (`40,199` dots; owner-reported 0.2708) and `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots; owner-reported 0.2778) rasters differ in **0 cells across all 12,279,160 grid pixels** after deleting the 2,545 dots in the 1.0 < d_cat ≤ 2.0 mapped-fault collar.

In other words, the H33 raster equals the pinned GEMSDOE28 raster after removing that 2-pixel catalogue collar, with all other cells identical. The source records associate this raster change with OWNER-REPORTED scores of 0.2708 and 0.2778 (OWNER-REPORTED delta +0.0070); neither score has an organizer receipt here. This pixel identity does not prove that collar pruning caused the reported score difference or that the removed cells were low-credit under hidden truth.

## 2. Mechanism: coverage-efficient emission, not a new geological discovery

The competition/reference metric is the asymmetric Tversky index (DTI) with α = 0.2 weighting false-positive mass and β = 0.8 weighting false-negative mass, evaluated with a 300 m triangular kernel (approximately a 3 px radius at 100 m resolution). This definition is described in the competition/reference materials; it is not a statement that any reported fleet score was confirmed by the organizer.

```
DTI = T / (0.2·T + 0.2·F + 0.8·N + ε)
```

where T = weighted recovered truth credit, F = weighted false-positive mass, N = fixed truth count.

Two metric properties make coverage-efficient emission a plausible explanation, but do not establish causation for H33:

**(a) Truth-cell credit is a maximum, not a sum.** At each truth cell, the triangular-kernel credit is the maximum over predictions within the kernel. Predictions with overlapping kernels can therefore yield diminishing marginal truth credit. A redundant prediction can still add false-positive mass when it is not itself on a truth cell; its exact marginal effect depends on distance to truth and existing coverage. Thinning may raise DTI only when the reduction in weighted false-positive mass outweighs any lost truth credit.

**(b) Mapped-collar predictions are not automatically useless.** Only mapped pixels are masked; the surrounding 300 m kernel support is not. A collar prediction may cover withheld truth, or it may add false-positive mass with little additional truth credit. Removing it can therefore help or hurt. The archive proves the collar deletion in the raster, not the hidden truth credit of those cells.

Thus H33's owner-reported 0.2778 is *consistent with* more efficient allocation of prediction mass, including possible collar pruning, but this account is not a measured explanation of the private score and is not proof of a new geothermal-vent discovery. No score improvement is established by this analysis.

## 3. Can we score higher than 0.2778?

**Not established.** The owner-reported 0.2778 has no organizer receipt. We cannot infer a causal improvement, and holdout results are not leaderboard projections.

Budget arithmetic at 0.2778 with |G| ≈ 40k: T ≈ 10,963, D ≈ 39,464. A +0.01 live DTI gain requires ≈ 418 kernel-credit units ≈ 42 km of fault trace hit squarely. All three prior reallocation sessions (PRUNE, CONCENTRATION, RELIEF) delivered |Δ| ≤ 0.0073 on the most generous instrument — short of the +0.01 evidence floor.

**Conclusion:** A parallel session generated a format-valid experimental TIFF (`gems86-faulthalo-…-zeros.tif`), but it does **not** satisfy the literal uniqueness gate: the pinned full-support witness forces forward overlap 1.0, above the 0.70 limit. No HOLDOUT-DTI or single-feature canary was run for this candidate. It is explicitly **DO NOT SUBMIT** and is not evidence that a new unique competition TIFF has been cleared. Scoring above the owner-reported 0.2778 is not established; it would require a compliant method, matched buffered holdout improvement with uncertainty, a separate selector decision, and an organizer receipt.

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