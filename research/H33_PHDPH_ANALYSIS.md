# H33 Forensic Analysis & Path to >0.2778 — PhD Synthesis

**Date:** 2026-10-25  
**Evidence class:** OWNER-REPORTED scores are unverified; no ORGANIZER-CONFIRMED receipt exists for H33 (0.2778) or claimed leaderboard max 0.4413.

## 1. What H33 is (pixel-exact, re-measured)

- **GEMSDOE28 parent:** 40,199 unit dots (owner-reported 0.2708)
- **GEMSDOE32 H33 (h33-h33-2-b2):** 37,654 unit dots (owner-reported 0.2778)
- **Operation:** Byte-exact deletion of 2,545 dots where 1.0 < d_cat ≤ 2.0 px from `existing_faults.tif`. Zero dots added. Identical footprint, CRS, transform.

This is a **RASTER-MEASUREMENT**, not causal proof of score gain.

## 2. Why collar pruning can plausibly lift DTI (mechanism, not forecast)

DTI = T / (0.2·T + 0.2·F + 0.8·|G| + ε) with 300 m triangular kernel (3 px). For each truth cell, kernel credit is **max** over covering dots, not sum. Pruning condition: ΔDTI > 0 ⇔ T·b > a·(F + 4|G| + 5ε) where b = saved false-positive mass, a = lost truth credit. Collar dots near mapped faults have low marginal a (truth already near mapped faults is masked) but contribute to F, so deleting them raises DTI if they are redundant or mis-placed. Dots covering blind relay tips would lose T and hurt.

H33's gain (+0.0070 owner-reported) is consistent with **coverage-efficient thinning at kernel scale**, not a new geophysical discovery.

## 3. Why 0.2778 is not a ceiling & what could beat it (information-theoretic)

Budget arithmetic at DTI 0.2778 with |G|≈40k gives T≈10,963, D≈39,464. +0.01 DTI needs ~418 kernel-credit units ≈ 42 km of blind fault trace hit squarely. All previous reallocations (PRUNE, CONCENTRATION, RELIEF) delivered |Δ| ≤0.0073 on most generous instrument — below the +0.01 evidence floor.

To beat H33, a submission must:
1. Add **new independent evidence** of blind faults (not re-shuffle H33's H19-5 ridge field)
2. Pass **literal-format gates** (EPSG:32611, 3730×3292, [0,1], 0 NaN, 0 on catalogue)
3. Pass **like-for-like uniqueness** (rho ≤0.90, dot overlap ≤0.70 vs registry dot fields)
4. Demonstrate **holdout-validated gain** with paired positive CI vs strongest rerunnable control
5. Survive **organizer receipt** (not owner claim)

No prior lane satisfied all five; H33's own holdout is 0.0961 [0.0830,0.1089] (gems57-pooled-hide-v2, 11,321 withheld), well below later H86F-EWCS 0.1723 and H86C-KSLB 0.1241 on same evaluator — holdout and live DTI are different distributions.

## 4. What the portal error "values must be in [0,1]" means

Historical fleet used NaN outside footprint (7.1M cells) and occasionally unclipped regression outputs / -3.4e38 sentinels. The portal strictly checks finite [0,1]. Our writer enforces mode="zeros" (0 outside, clipped [0,1], no NaN/Inf, binary dots) so this class of error cannot recur. Format pass ≠ organizer acceptance.

## 5. Ranked hypotheses for next DTI lift (all require free, official data on disk)

| Rank | Hypothesis (layers) | Physical signature & why it catches catalogue-missing faults | Difference from repo | Non-fault mimic | Expected lift / Cost |
|------|---------------------|--------------------------------------------------------------|----------------------|-----------------|----------------------|
| 1 | **GDSC — Geodetic Dilatational Strain Corridor** — Bands 4 (geod_2ndinv), 7 (shearrate), 8 (dilaterate) | Positive dilatation + high second invariant ridge under low-relief basin fill (det_elev_slope muted) marks active transtensional jogs/stepovers whose scarps are erased by Lahontan lake beds. GPS strain sees creep without scarp. | No prior lane used pure GPS strain as primary (all used magnetics/gravity/DEM ridges). | Irrigation subsidence, playa contraction | High incremental (novel physics) / Low cost (~5 min CPU) |
| 2 | **IGFC — Isostatic Gravity Fabric Curvature** — Bands 13, 11, 18, 5 | Regularized Laplace g_zz zero-crossing + gradient-magnitude ridge, strike-continuous ≥900 m, coincident with basement depth step (Band 15) polarity, weighted where slope muted. Basement step persists under cover. | FVMB used single-altitude wavenumber; this uses masked, regularized Laplace with polarity control. | Paleovalley margins, inversion artifacts | Medium-high / Medium (derivatives at σ=400 m) |
| 3 | **RLH — Radiometric Leach Halo** — Band 6 (TC) + external K/Th/U | TC depletion halo paired with K/Th enrichment rim (adularia/illite) along linear corridor indicates hydrothermal leaching. Surface geochemistry survives burial. | Prior radiometric used simple margins, not paired depletion/enrichment dipole + 6 km corridor. | Lithologic contacts, agricultural K | Medium / Low-medium |
| 4 | **CNC — Conductivity-Neck Conditioned on Dilatation** — Band 17 (cond_surf) × Band 8, vetoed by detrended elev | Narrow threshold-persistent conductive neck between broader conductive basins, gated to positive dilatation; hot saline fault fluid vs stagnant playa brine. | CTHB used pointwise cond; this is persistent topology + strain gating (H86G-CNT proposed, never run). | Saline playa, clay paleochannel | Medium (confounded) / Medium |

Selection for implementation: **GDSC Rank 1** (highest expected lift, lowest cost, zero new external data, fully official DOI 10.5066/P9Z6SA1Z & 10.5066/P93LGLVQ provenienced bands).

## 6. Sources (verified, not hallucinated)

- DOE GEMS Official Rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- DrivenData problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ)
- GDR INGENIOUS 1391: https://gdr.openei.org/submissions/1391
- GBCGE INGENIOUS: https://gbcge.org/current-projects/ingenious/
- EPSG:32611: https://epsg.io/32611
- Kreemer & Young 2022 strain: https://doi.org/10.1785/0220220153
- Faulds & Hinz 2015 geothermal structural controls (Great Basin)

All band indices verified against `src/gems86/io.py` and `docs/evidence/band-physics-verification-20261024.json`.

## 7. Limitations

- Owner-reported 0.2778 has no receipt; live truth |G| unknown; holdout DTI cannot be projected to live DTI.
- New external MT (DOI 10.5066/P9TWT2LU) and heat-flow (DOI 10.5066/P9BZPVUC) grids not yet mirrored; InSAR OPERA not obtainable in sandbox allowlist.
- GDSC requires LOQO holdout with visible-only catalogue features; geodetic bands are catalogue-blind so leakage AUC expected <0.60.

