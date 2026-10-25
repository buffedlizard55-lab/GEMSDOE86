# H86F-PCC preregistration

Written before the holdout run. The candidate arm is `E1_pcc_signed`. Arms are not swapped after scores are seen. Three arms are the experiment budget. Two further hypotheses are ranked and not run.

## Why this is not a copy of a previous lane

- `H86-WVB` uses unsigned `cos(2Δθ)` magnetic-gravity alignment, Salem tilt depth, lidar scarps, and geothermometry. This lane requires gravity and RTP to point the **same** way and depth-to-basement to point the **opposite** way. Anti-parallel magnetic-gravity edges score zero.
- `H86E-MMT` tests a non-zero cross-corridor lag. This lane tests polarity at zero lag.
- `H86E-SPBT` / quarantined `SPT` use Laplace `g_zz` paired throw. This lane uses first-derivative polarity of gravity, RTP, and basement depth.
- `KSLB` uses fluvial knickpoints and Blakely filaments. This lane does not.
- Catalogue pixels are not features. They enter only as the visible-fault mask inside the shared holdout and as a hard emission mask.

## Official sources

- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ). Flight lines at azimuth 90°, tie lines at azimuth 180°. Magnetic grids are for subsurface structure. Retrieved 2026-10-25.
- Competition bands and the Band 6 / Band 11 / Band 18 header corrections are the pixel-verified receipt `docs/evidence/band-physics-verification-20261024.json`.
- Metric weights α = 0.2, β = 0.8, 300 m triangular kernel are the shared `vendor/gems57/metric.py` transcription of the competition definition. This preregistration does not change them.

## Named non-fault process

An unfaulted basin-fill facies contact, or a volcanic flow edge, can produce the same density and magnetization polarity as a basement step. Residual GeoDAWN flight-line and tie-line corrugations can do the same along survey axes; those axes are down-weighted, not deleted from the grid.

## What would falsify promotion

Promotion inside this lane requires all of the following, and still does not spend a weekly slot:

- leakage canary discriminative AUC ≤ 0.90 on every component;
- HOLDOUT-DTI (`gems57-pooled-hide-v2`, seed 20, 3 px visible collar) above the same-split historical KSLB comparator with non-overlapping 95% CIs;
- paired delta versus the best preregistered control strictly positive;
- surface Spearman ≤ 0.90 against every measured registry raster before placement;
- final-dot PA-86-02 gate pass (no informative >70% overlap with a non-space-filling dot field).

Anything else is a negative deliverable. No number from this lane is an organizer score.
