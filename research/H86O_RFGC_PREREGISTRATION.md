# H86O-RFGC Preregistration — Ridge-Flexure Geothermal Concordance

**Frozen:** 2026-10-26T00:30:00Z UTC (before any scoring)  
**Lane:** `H86O-RFGC` — single method paragraph below (Parallel-Run Protocol Lane 1)  
**Branch:** `arena/9182dcd2-gemsdoe86`  
**Evaluator:** `vendor/template66/gems57/evaluate_holdout.py` (gems57-pooled-hide-v2) — hide-and-recover whole fault segments with buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel)  
**Writer:** `vendor/template66/gems57/submission_writer.py` (fail-closed: no clipping/repair, on-disk validation before publish)  
**Budget:** 3 experiments or 2 hours, whichever first  
**Leakage canary limit:** max feature-alone AUC > 0.90 means leakage until proven otherwise  
**Uniqueness:** Spearman rho > 0.90 or >70% dots within 3px of registry raster => drift into another lane, log as duplicate and stop (checked on surface before placement AND final dots)

## Method Paragraph (single lane)

**Hypothesis H86O-RFGC:** Low-throw (0.3–1.5 m) blind relay-ramp and piedmont faults at shallow (0.2–1.2 km) basin margins create coincident weak topographic slope breaks (Band 19 `det_elev_slope`) and basement density steps (Band 5 `iso_grav_anom_slope`) under active crustal dilatation (Band 8 `geod_dilaterate`), individually below USGS QFaults photogeologic mapping thresholds but jointly diagnostic when depth-gated and dilatation-modulated. Physical signature is normalized coincidence S = z(Band5) × z(Band19) inside Band15 depth window 200–1200 m, weighted by ReLU(Band8), shape-filtered by along-strike vs cross-strike curvature to suppress compact volcanic plugs (high radial curvature) vs fault steps (low along-strike curvature), then Poisson-disc sampled at 2.8 px to 37,654 dots.

## Layers Involved (verified band physics, 2026-10-24 receipt)

- **Band 5 `iso_grav_anom_slope`:** Scalar 2-D horizontal isostatic gravity gradient magnitude (pixel-verified r=+0.946995 vs hypot(B11,B18); `docs/evidence/band-physics-verification-20261024.json`)
- **Band 19 `det_elev_slope`:** Scalar detrended topographic slope magnitude (r=+0.950603 vs |grad(B12)|)
- **Band 15 `depth_to_base_surf`:** Depth to pre-Tertiary basement / basin-fill thickness
- **Band 8 `geod_dilaterate`:** Geodetic dilatation rate — crustal extension / fracture-opening rate (Kreemer & Young 2022, DOI 10.1785/0220220153)
- **Band 12 `det_elev`:** Detrended elevation — local scarp relief (for Lake Lahontan veto)
- **No external data:** All 5 bands are in hash-pinned `training_features.tif` (SHA 4371c82e...), verified in `data/prepared_manifest.json`

## Why This Should Catch Faults Missing From Catalogue Rather Than Already In It

Existing `existing_faults.tif` (60,988 footprint pixels) is dominated by high-relief range-front scarps (>50 m) imaged in aerial photos and 10-30 m DEMs. Piedmont/horsetail relay faults have <1 m throw, buried by Quaternary alluvium, invisible to photogeology, but retain:
- **Band19:** 2–5° slope break at 100 m (weak but above 7.4 mean + 8.3 std background)
- **Band5:** 0.12 mean, 0.08 std gravity gradient from 0.2–1.2 km basement offset (smoothed by fill elsewhere)
Individually sub-threshold; coincidence at shallow basin margins (Band15 window) under active extension (Band8>0) is diagnostic. Deep basins and bedrock highs are vetoed by depth gate.

## How It Differs From Anything Already Implemented In This Repo

| Prior lane | Its signature | RFGC difference |
|---|---|---|
| H86N-GSST (gravity step-vs-compact) | Band 5/11/13/18 gravity morphology only | Adds Band19 topography coincidence + depth + dilatation |
| H86K-PSC (saddle-ridge Hessian) | Hessian topology on Bands 12/13 | Pointwise Hessian vs normalized coincidence product |
| H86M-BMGS (BMR+GSST+CNT) | BMR gravity residual + RTP magnetics + conductance necks | No magnetics/conductance; pure topo-gravity concordance |
| GDSC (dilatational) | Band8 dilatation magnitude alone | Dilatation is modulator, not sole signal |
| FVMB (tri-regime) | Tri-regime thresholds on multiple bands | No thresholds; continuous coincidence surface |
| H86I-RKSC (rad scarp) | Radiometric + magnetic gradients | No radiometrics/magnetics |

Checked via `registry/*.json` and `docs/hypotheses.html` — no lane combines Band5×Band19 with Band15 depth gating and Band8 dilatation.

## Named Non-Fault Process That Could Mimic It

**Pleistocene Lake Lahontan shoreline terraces (~1330 m Bonneville-level, ~1205 m Sehoo cycle)** and fluvial terrace risers produce coincident topographic slope + density contrast (alluvial fan vs lacustrine fines) without brittle offset. Mitigated by: (1) Band8 dilatation gating (terraces are aseismic, low strain), (2) Band12 detrended elevation window excluding lacustrine highstands, (3) along-strike curvature test (terraces are perfectly contour-parallel, high along-strike continuity vs fault steps with en echelon segmentation). Tertiary volcanic flow margins (Band5 without Band19) are second mimic.

## Falsifier

Paired pooled HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld positives, 1000-draw physical-block bootstrap) vs three preregistered controls:

- **E1 = Band5 alone** (gravity ridge only)
- **E2 = Band19 alone** (topographic slope only)
- **E3 = uniform depth window** (RFGC without depth gating)

If RFGC paired delta vs all controls includes zero in 95% CI, the concordance/depth hypothesis is falsified (negative result). Also: any single-feature AUC >0.90 triggers leakage stop.

## Implementation Cost & Expected Value

- **Cost:** Low (~5 min CPU, O(N) Gaussian/gradient operators, no ML fitting, <1 GB RAM)
- **Expected DTI:** Medium — suppresses deep-basin and high-range false positives that dominate prior continuous submissions; no numeric projection, to be measured on holdout
- **Data viability:** 100% SHA-pinned native bands restored in sandbox (`python scripts/restore_data.py` verified), no external download needed
- **Verification:** Band physics re-checked in `docs/evidence/band-physics-verification-20261024.json`; 1-m DEM and OPERA InSAR deferred to H86O-LIDM/H86O-OPIS (missing_data, not viable now)

## Sources (verified, official, free)

- DOE/NLR GEMS Prize Rules (Sep 2026): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GBCGE INGENIOUS DE-EE0009254: https://gbcge.org/current-projects/ingenious/
- USGS GeoDAWN Release DOI 10.5066/P93LGLVQ: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Competition reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Kreemer & Young 2022 horizontal strain: https://doi.org/10.1785/0220220153
- EPSG:32611 (WGS84/UTM Zone 11N): https://epsg.io/32611
- Tversky index (DTI alpha 0.2/beta 0.8): https://en.wikipedia.org/wiki/Tversky_index
- Band physics verification: `docs/evidence/band-physics-verification-20261024.json` (r values above)

No drivendata.org scraping; all scores labeled HOLDOUT-DTI or OWNER-REPORTED; projection never written as score.

