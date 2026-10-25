# H86N — Deep Valley Conductive-Dilation Corridor (DVDC) Lane Preregistration

**Lane ID:** H86N-DVDC (primary), with 4 companion ranked hypotheses.
**Date frozen:** 2026-10-25T18:20:00Z (before any holdout evaluation on new surface)
**Branch:** arena/4dd6af59-gemsdoe86
**Evaluator:** vendor/gems57/evaluate_holdout.py gems57-pooled-hide-v2 (α=0.2, β=0.8, 300 m triangular kernel, pooled DTI, 20 km physical-block bootstrap, 1000 draws, seed 520810)
**Grid:** EPSG:32611, 3730×3292, 100 m, footprint 5,167,373 px, catalogue 60,988 px

## Parallel-run protocol compliance

1. **LANE:** Single method paragraph below; stay inside it. Surface rank-correlation and final-dot overlap vs registry checked before placement AND on final dots (thresholds 0.90 / 0.70). Duplicate → log and stop.
2. **REUSE:** Uses vendor/gems57 cached feature stack (native 19 bands), evaluate_holdout.py, submission_writer.py. Holdout = hide-and-recover whole fault segments with buffer, every catalogue-derived feature recomputed from visible faults only, visible faults masked pixel-exactly, pooled DTI (α 0.2, β 0.8, 300 m triangular). No private fork.
3. **LABEL:** HOLDOUT-DTI vs ORGANIZER-CONFIRMED; projection never a score.
4. **CANARY:** Single-feature AUC >0.90 = leakage.
5. **RUN CARD:** JSON with all required fields.
6. **BUDGET:** ≤3 experiments or 2 h.

---

## Why H33 scored 0.2778 (OWNER-REPORTED, no receipt) — PhD synthesis

- **Forensic raster change (RASTER-MEASUREMENT):** GEMSDOE32 h33-h33-2-b2 (37,654 dots) = GEMSDOE28 D28 (40,199 dots) minus exactly 2,545 dots where 1.0 < d_cat ≤ 2.0 px from existing_faults.tif. Zero dots added. All other pixels identical. Owner-reported delta +0.0070 (0.2708 → 0.2778) is not causally proven; no organizer receipt exists for either number.

- **DTI mechanism (not a forecast):**
  DTI = T / (0.2·T + 0.2·F + 0.8·|G|), where T = max-kernel truth credit (max over covering predictions, not sum), F = false-positive mass (prediction mass not credited), |G| = truth count. At 300 m (3 px) kernel, a second dot within 3 px of truth may add F without adding T (redundant). Collar dots near mapped faults have low marginal T (truth near catalogue is masked in holdout/live scoring) but contribute F, so pruning can raise DTI if dots are redundant/misplaced, and hurt if they were sole cover of a blind relay tip. The raster edit alone does not measure lost T vs saved F.

- **Why it plausibly helped:** Coverage-efficient thinning at kernel scale + catalogue-collar hygiene. DTI penalizes FP at 0.2 and FN at 0.8; H33 removed FP-heavy, low-marginal-T dots while preserving H19-5 ancestor ridge field (derived from mag/gravity/scarp). The H33 holdout on gems57-pooled-hide-v2 is only 0.0961 [0.0830,0.1089] (11,321 withheld), well below later lanes (H86F-EWCS 0.1723), confirming holdout ≠ live.

- **Can we beat 0.2778?** Not established from H33 alone. Requires: (1) new independent evidence of blind faults (not reshuffling H19-5 field), (2) literal format gates, (3) uniqueness ≤0.90/≤0.70, (4) holdout-validated paired positive CI, (5) organizer receipt. Leaderboard 0.4413 claim is OWNER-REPORTED without receipt.

**Official sources:**
- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf (§3.4–3.6, 3 submissions/week, 1 final pick)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- EPSG:32611: https://epsg.io/32611
- USGS GeoDAWN release (magnetic/radiometric): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and / DOI https://doi.org/10.5066/P93LGLVQ
- USGS Geothermal/INGENIOUS: https://gbcge.org/current-projects/ingenious/ / https://gdr.openei.org/submissions/1391 (CC-BY-4.0)
- GEMSDOE32 page: https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

---

## 3–5 Candidate Geological Hypotheses Not Yet Tried in This Repo

All use only the 19 native competition bands (no new external download required; availability verified via `scripts/audit_workspace_inputs.py` HASH_VERIFIED). Each lists: layers, physical signature (edge/curvature transform), why it catches catalogue-missing faults, how it differs from repo.

### Rank 1 — H86N-DVDC: Deep Valley Conductive-Dilation Corridor (PRIMARY, this lane)
- **Layers:** B15 depth_to_base_surf, B17 cond_surf, B8 geod_dilaterate, B7 geod_shearrate, B4 geod_2ndinv, B13 iso_grav_anom, B12 det_elev
- **Physical signature:** Joint detection of (a) thick alluvial cover (Zb > 150 m, low detrended relief), (b) active crustal dilation (geod_dilaterate > 0 + positive 2nd invariant), (c) conductive anomaly (cond_surf high) restricted to dilating domains (vetoed against playa-only conductivity), and (d) gravity gradient lineament (Laplacian of B13) marking buried basin-bounding normal-fault step. Transform: normalized product P = sigmoid(Zb)·sigmoid(dilaterate)·sigmoid(cond|dilating)·sigmoid(|∇²B13|), then oriented ridge extraction (Hessian eigenvectors) filtered for N–S to NNE (015°–035°) Basin-and-Range strike, length-weighted.
- **Why catalogue-missing:** USGS Quaternary fault catalogue is dominated by bedrock scarps (airphoto-mapped). Blind intrabasin and range-front faults beneath >100 m Quaternary alluvium have no scarp but retain dilational strain + conductive clay/brine + gravity step from offset bedrock. These are INGENIOUS's target "blind geothermal" faults.
- **Differs from repo:** No prior lane combines basin thickness × dilation × conductivity with gravity curvature. H86F-EWCS used edge-weighted corridors but not Zb depth gating; H86D-CTHB used cond_surf halos but not dilation-gated; prior concentration/relief axes only reshuffled H19-5 dots.
- **Expected DTI / cost:** Highest expected. Direct blind-fault physics with orthogonal evidence to H19-5 magnetic ridges. Cost LOW (numpy gradient/Laplacian + Hessian, CPU <30 min).
- **Non-fault mimic:** Closed-basin evaporite playas (high cond_surf + thick fill) without active dilation; mitigated by dilation gate and detrended-elevation flat veto.
- **Official basis:** USGS depth-to-basement derived from gravity/magnetics (Band 15 semantics per https://gdr.openei.org/submissions/1617), USGS GeoDAWN for B13/B14 validation (DOI 10.5066/P93LGLVQ), GBCGE INGENIOUS blind-fault concept (https://gbcge.org/current-projects/ingenious/)

### Rank 2 — H86N-TMOR: Tilt-Modulated Analytic-Signal Ridge (SECONDARY)
- **Layers:** B2 rtp, B13 iso_grav_anom, B5 iso_grav_anom_slope, B3 tmi_hg, B9 tmi_vg, B6 tc
- **Physical signature:** Compute 2-D analytic signal amplitude ASA = sqrt((dB/dx)²+(dB/dy)²+(dB/dz)²) for RTP and gravity, then tilt angle θ = atan(dz/|∇h|). Fault produces paired curvature couplet: Laplacian(ASA) positive on upthrown shoulder, negative on downthrown, with θ zero-crossing between them. Detect via LoG (Laplacian of Gaussian, σ=1.5 px) on ASA × |∇θ| sharpness, corroborated across mag+grav.
- **Why catalogue-missing:** Subtle offset of magnetized Tertiary volcanics beneath thin cover creates weak ASA curvature not flagged as ridge in airphoto scarp maps; gravity ASA catches density step even under alluvium.
- **Differs:** No lane implements ASA curvature or tilt-modulated LoG. GMC used cross-gradient angle but not ASA curvature; MPC (planned) would use phase-congruency not amplitude curvature.
- **Expected / cost:** High/medium. Complementary to DVDC; targets magnetite-rich terranes. Cost MEDIUM (FFT gradients, LoG).
- **Mimic:** Volcanic flow fronts, intrusive contacts; falsified by requiring dual-field (mag+grav) coincidence.

### Rank 3 — H86N-RIEDEL: Riedel Shear Mesh from Geodetic Strain Tensor
- **Layers:** B7 geod_shearrate, B8 geod_dilaterate, B4 geod_2ndinv, B18 iso_grav_anom_hg, B11 iso_grav_anom_vg, B17 cond_surf
- **Physical signature:** From horizontal strain tensor (invert shearrate+ dilaterate), compute principal extension azimuth. Detect secondary shears at φ_R = 15°±5° and φ_R' = 75°±7° to P-axis via oriented Gabor filter banks (4 scales, 12 orientations), keeping only responses oblique to main mapped fault strike. Rank by shear-dilatation product.
- **Why catalogue-missing:** Walker Lane transtensional faults (NW-SE, 310°–335°) develop antithetic Riedel mesh of N-S to NNE secondary normal faults at relay zones; these short (<2 km) segments are below airphoto mapping resolution but critical for geothermal permeability.
- **Differs:** No lane extracts Riedel orientations. H86I-RLMS used Riedel listric templates but with scarp+chi, not geodetic tensor; prior cross-gradient used orthogonality not angular Gabor.
- **Expected / cost:** Medium expected (narrow Walker Lane domain reduces |G| hit rate). Cost MEDIUM-HIGH (Gabor bank + tensor).
- **Mimic:** Agricultural lineaments, road grids; vetoed by requiring positive 2nd invariant and no plateau flat.

### Rank 4 — H86N-CHI: Fluvial Chi-Slope-Break × Detrended-Elev Gap Corridor
- **Layers:** B12 det_elev, B19 det_elev_slope, B15 depth_to_base_surf, B13 iso_grav_anom, B5 iso_grav_anom_slope
- **Physical signature:** Compute fluvial chi proxy from competition-native det_elev (valley fill) gradient: chi-slope = local concavity anomaly via second directional derivative along steepest descent (not requiring external 10 m DEM downloads). Fault throw creates paired det_elev slope polarity reversal (scarp) co-located with chi slope-break (knickzone) and gravity slope lineament bridging across divide.
- **Why catalogue-missing:** Low-slip (<1.5 m) late Quaternary piedmont scarps are smoothed at 100 m but drainage network retains tectonic concavity signal; wind gaps across divides mark relay breaching.
- **Differs:** H86E-WCS proposed watershed-crossing with raw 1 m LiDAR tiles (not available/efficient); this uses only native 100 m bands, no external download.
- **Expected / cost:** Lower expected (100 m limits sensitivity). Cost LOW-MEDIUM.
- **Mimic:** Lahontan shorelines (constant elevation, not slope-break paired); vetoed by cross-divide polarity test.

### Rank 5 — H86N-SINTER: Radiometric Silica-Cap Depletion Corridor
- **Layers:** B6 tc (GeoDAWN TC verified r=0.997140), B17 cond_surf, B2 rtp, B8 geod_dilaterate, B12 det_elev
- **Physical signature:** Hydrothermal leaching precipitates opal-A sinter (low K/U, low TC) capping fault vent; detect TC depletion trough (negative Laplacian of B6) flanked by mild potassic halo, coincident with conductive alteration (B17 high) and dilating corridor (B8>0). Transform: signed valley curvature on TC (Hessian negative eigenvalue) × conductivity dilation gate.
- **Why catalogue-missing:** Paleo-sinter caps (726 GDR 1391 sites) mark blind upflow faults that never breached surface as scarps; modern radiometric depletion persists even where sinter eroded.
- **Differs:** H86E-HMDC proposed pairwise vent bridges + magnetite trough, not TC valley curvature itself; no lane uses TC curvature as primary detector.
- **Expected / cost:** Lowest (TC is noisy, playa evaporites mimic). Cost LOW.
- **Mimic:** Saline playa leaching, felsic tuffs (low TC); mitigated by requiring dilation + conductivity coincidence.

**Ranking rationale (expected DTI improvement per cost):**
1. DVDC — highest orthogonal information to H19-5 (basin physics vs ridge physics), directly targets INGENIOUS blind concept, cheapest.
2. TMOR — strong where magnetism strong, moderate cost.
3. RIEDEL — niche but geologically sharp, higher cost.
4. CHI — limited by 100 m resolution.
5. SINTER — most mimic-prone.

**Validation plan for top candidate (DVDC):**
1. Prepare native bands (.cache/gems_work/bands/*.npy) — DONE (prepare_data.py).
2. Run single-feature leakage canaries on DVDC sub-features (B15, B17|dilating, dilaterate, gravity Laplacian) — require max(AUC,1-AUC) ≤0.90.
3. Build DVDC surface S (normalized product + Hessian ridge), then hide-and-recover holdout: whole fault components with 12 px buffer, recompute every catalogue-derived feature from visible faults only, mask visible faults pixel-exactly, pooled DTI (α0.2 β0.8 300 m) with 1000×20 km block bootstrap.
4. Compare vs strongest control: H33-as-is (37,654 dots) and raw edge control (iso_grav_slope ridge alone) at same dot budget via paired CI.
5. If positive paired Δ with CI entirely >0, proceed to spacing-aware dot emission (Poisson disc 2.8 px, d_cat>3 px) and like-for-like uniqueness (rho≤0.90, overlap≤0.70 vs restored 655-raster registry).

If DVDC fails, promote TMOR as next experiment (budget allows 2 more).

## Lane method paragraph (frozen)

H86N-DVDC computes normalized deep-valley conductive-dilation corridors: Zb-depth-normalized (B15 log-depth sigmoid), dilution-gated conductivity (B17 high only where B8>0 and B7/B4 indicate active transtensional shear), active dilation (B8 geod_dilaterate positive anomaly), and gravity second-vertical-derivative proxy (Laplacian of B13 iso_grav_anom via B18/B11 directional derivatives). The product P = S(Zb)·S(dilaterate)·S(cond|dilate)·S(|∇²B13|) is ridge-filtered via Hessian eigenvalues (|λ1| large, |λ2| small, λ1<0 valley for gravity edge) at 2 scales (σ=1.0,1.5 px) and strike-filtered to N015°–035° ±20° (Basin-and-Range normal) retaining length>10 px segments, with closed-basin flat veto (det_elev detrended elevation range <5 m per 500 m window) and survey-seam azimuth veto (E-W/N-S 90°/0° striping). Dots are ranked by expected kernel self-credit and emitted behind 3 px catalogue collar via Poisson-disc spacing 2.8 px to 37,654 dots (H33 budget).

