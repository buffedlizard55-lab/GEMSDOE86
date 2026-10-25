# H86F-WARP Preregistration — Broad-warp detrended-elevation curvature persistence

**Frozen:** 2026-10-25T02:15:00Z  
**Lane:** H86F-WARP  
**Budget:** 3 arms / 2 hours / 44,090 dots  
**Holdout:** buffered whole-component LOQO v2, hide 0.20, buffer 3 px, pooled DTI α=0.2 β=0.8 R=300 m  
**Status:** frozen_before_lane_computation

## Lane resolution
The supplied prompt contains no separate single method paragraph assigning this session a lane. Exactly one lane is selected and frozen here before any H86F-WARP surface, fit, canary, holdout or placement computation. This follows PA-86-01/02 (AGENTS.md rule 10): new lanes may call `require_like_for_like()` instead of `require_feasible()` ONLY if they run the full two-phase registry checker on surface and final dots and `pa86_chance_overlap.py`. All thresholds unchanged (ρ>0.90, overlap>0.70, 3 px). Read-only H33 forensics and band-physics spot checks before this freeze are audits, not lane experiments.

## Ranked hypotheses (5 — before implementation, per prompt)

### Rank 1 — H86F-WARP (THIS LANE): Broad-warp detrended-elevation profile-curvature sign-flip persistence
- **Layers:** `training_features.tif` Band 12 `det_elev` (USGS DOI 10.5066/P9MQRCBY, detrended elevation = topography with regional trends removed) and Band 19 `det_elev_slope` (gradient of detrended elevation). Both verified against pinned SHA 4371c82e… No external data.
- **Physical signature:** Second directional derivative of Band 12 at two broad scales σ=3 px (300 m) and σ=6 px (600 m): Gaussian Laplacian `LoG = gaussian_laplace(Band12, sigma)` (positive where valley, negative where ridge, zero at inflection). For 8 strike azimuths (0°,22.5°…157.5°), compute flank means at +2..4 px and −2..4 px along the unit normal (ny,nx) = (sinθ, cosθ) rotated to image row/col, then dipole pairing `sqrt(clip(plus * -minus,0))` (max of forward/reverse polarity) requiring opposite-sign curvature lobes with zero-crossing over the hinge. Strike-smooth over 9 px (≥900 m continuity) and take max over azimuths and scales. Weighted higher where `det_elev_slope` muted (rank-normalized inverse slope) to emphasize degraded scarps under alluvial cover — but weight is multiplicative and never masks the primary curvature test.
- **Why catch missing vs mapped:** Pre-Quaternary bedrock faults can retain a 300–600 m broad flexural warp after the discrete Holocene scarp (throw <1 m) has degraded below USGS/INGENIOUS Quaternary photo/DEM mapping thresholds and been reworked by alluvial fans. The catalogue is Quaternary/surface-expression based (Qfaults). A broad-warp curvature zero-crossing is blind to that selection: it detects the inherited monocline, not the surviving scarp step. Mapped faults are dominated by high-relief range-front scarps already scored in Band 19 slope magnitude; broad warp is orthogonal to that selector.
- **How differs from repo:** Prior topographic lanes use **slope magnitude** (Band 19 scalar, `r=+0.9506` vs ‖∇B12‖), relief, or 1-m lidar sharp scarps (SNAP family, retired for using airborne gradients that share flight-line error). No executed lane tests **signed broad-warp curvature sign flip** on Band 12 as standalone surface at dual 300/600 m scales with strike persistence and dipole pairing. H86C-KSLB used fluvial Ksn and Blakely Noisy-OR; H86D-CTHB used contact truncation; H86-FVMB used dip pullback; none use LoG curvature pairing.
- **Non-fault mimic:** Hogback dip slopes, Lake Lahontan paleoshorelines/pluvial treads, lithologic dip-slope breaks, and bedding-plane flexures. These produce curvature but lack multi-scale persistence and orientation coherence; fluvial Ksn control and orientation dispersion filter mitigate.
- **Expected DTI / cost:** Ranked highest qualitative priority: historic topographic signals are strongest in fleet (H19 lineage 0.1922 OWNER-REPORTED) and warp targets degraded-scarp gap directly. Expected HOLDOUT-DTI modest (+0.005 to +0.015 over slope-magnitude control) — no numerical projection — but low-medium implementation cost (deterministic, no fitting, no external bytes, ~20 min CPU, within 2-hr cap). **Must be validated on spatially-blocked holdout before slot consideration; cannot be projected to leaderboard.**
- **Official basis:** USGS 3DEP detrended elevation via competition bundle (DOI 10.5066/P9MQRCBY), EPSG:32611, 100 m grid; Official Rules PDF https://docs.nlr.gov/docs/fy26osti/96647.pdf §1; GeoDAWN DOI 10.5066/P93LGLVQ for acquisition geometry context; Tversky https://en.wikipedia.org/wiki/Tversky_index.

### Rank 2 — H86F-SLB: Geodetic strain-localization boundary (tensor-gradient ridge)
- **Layers:** `geod_2ndinv` Band 4, `geod_shearrate` Band 7, `geod_dilaterate` Band 8 (INGENIOUS strain compilation, DOI 10.1785/0220220153 via https://gbcge.org/current-projects/ingenious/).
- **Signature:** Gradient-magnitude ridge of the strain-rate second invariant with orientation coherence — boundary between straining and rigid blocks, not scalar strain value.
- **Why missing:** Interseismic strain concentrates on locked faults whether or not they have a mappable Quaternary trace.
- **Differs:** Bands 4/7/8 entered GFCO/KSLB/WVB/blind-geothermal only as scalar values or rank averages; no lane uses tensor-gradient localization ridge as standalone statistic.
- **Mimic:** GPS/InSAR interpolation smoothing artifacts; volcanic/anthropogenic deformation.
- **Expected / cost:** Lowest incremental HOLDOUT-DTI priority: geodetic grids are smooth at multi-km scale vs 300 m kernel, so per-dot credit diffuse. Low cost but ranked 2 for novelty, not DTI. Not run this session.

### Rank 3 — H86F-HMDC-LITE: Hydrothermal magnetite-destruction trough with vent collinearity (competition-native subset)
- **Layers:** `rtp` Band 2, `tmi_vg` Band 9, `cond_surf` Band 17, `tc` Band 6 (pixel-verified radiometric Total Count, r=+0.997140, NOT magnetic tilt), plus GDR 1391 `paleo_geothermal_regional.zip` (726 sinter/tufa, sha256 faffcf69…) and `2m_temperature_probe` (3,800 probes, sha256 1301f70d…).
- **Signature:** Strike-continuous RTP minima with positive cross-strike second derivative and magnetic shoulders, co-located with Band 17 conductance and pairwise ≤6 km collinear geodesics connecting sinter/vent points inside dilatant crust (Band 8 >0), vs phase/point-scrambled controls.
- **Why missing:** Hydrothermal upflow along blind fault destroys magnetite and deposits sinter without building a mappable scarp.
- **Differs:** H86D-CTHB extracted only positive magnetic Hessian ridges (`mag_ridge_s15`) and radial halos; no lane extracts negative troughs or pairwise collineations.
- **Mimic:** Remanent reversed-polarity flows, felsic tuffs with primary low susceptibility, playa clay pans, survey seams.
- **Expected / cost:** Geothermally most specific, but point compilations sparse inside footprint. Medium-high cost (pairwise geometry + scrambled controls). **NOT VIABLE YET** in this sandbox: paled sinter/2m probe archives not re-obtained and hash-verified here; need free official source https://gdr.openei.org/submissions/1391 (CC BY 4.0) — not in allowlist via pip, must be mirrored via GitHub. Ranked 3, not run.

### Rank 4 — H86F-GVCD-STILL: Single-scale g_zz dipole without basement gate (ablation)
- **Layers:** `iso_grav_anom_hg` Band 18, `iso_grav_anom_vg` Band 11, `iso_grav_anom` Band 13.
- **Signature:** Regularized `gzz = -(d_x B18 + d_row B11)` dipole pairing alone, no Band 15 basement polarity gate.
- **Why missing:** Subsurface density step under basin fill.
- **Differs:** GZZD tested with polarity gate; this isolates gzz contribution.
- **Mimic:** Paleovalley margins, inversion artifacts.
- **Expected / cost:** Very low: prior GZZD candidate 0.0303 vs edge control 0.0321 (negative). Low cost but ranked 4 (redundant with executed negative lane).

### Rank 5 — H86F-ASIG: Analytic signal amplitude vs RTP decoupling
- **Layers:** `tmi` Band 14, `tmi_hg` Band 3, `tmi_vg` Band 9, `tc` Band 6.
- **Signature:** Analytic signal amplitude `ASA = hypot(B3,B9)` vs RTP decoupling via TC contrast.
- **Why missing:** Lithologic contacts vs fault offsets.
- **Differs:** Not yet tried, but heavily overlaps prior magnetic-edge fleet (HEDGE, WVB, GFCO).
- **Mimic:** Intrusive contacts, lava-flow edges.
- **Expected / cost:** Low HOLDOUT-DTI (magnetic edges already saturated in fleet), low cost but ranked last. Not run.

**Ranking basis:** Qualitative expected information gain per implementation cost (not projected DTI). WARP is the only candidate whose statistic is specific to degraded-scarp *warp* (paired opposite-sign curvature lobes at broad scale) rather than any edge, needs no external bytes, and has full-footprint coverage. HMDC-LITE is geothermally specific but sparse; SLB is cheap but diffuse; GVCD is ablation of already-negative lane; ASIG is saturated family.

**Validation gate:** Top candidate (WARP) must beat its own slope-magnitude control and historical best on the identical spatially-blocked holdout with separated 95% CI before any slot consideration. If a candidate requires external data, the specific free official source must be obtainable — checked above.

## Arms (3 fixed, 44,090 dots each, 3 px catalogue buffer, 3 px decimated emission)
- **E1_warp_persistent (candidate):** `LoG(Band12, sigma=3)` and `LoG(Band12, sigma=6)` dipole pairing (8 azimuths, ±2..4 px flanks, 9-px strike smoothing) max over azimuths and scales, multiplied by inverse-slope weight (rank-normalized `1 - rank01(det_elev_slope)` infootprint), then `rank01`.
- **E2_warp_single (ablation):** Identical but sigma=3 only, no multi-scale max.
- **E3_slope_control (negative control):** Unsigned `det_elev_slope` Band 19 Gaussian-smoothed sigma=2 px, rank01 — the historical slope-magnitude selector that WARP must beat to claim warp-specific credit.

All three share: footprint-masked median fill outside footprint, no catalogue pixels read, catalogue entering only via holdout/emit masks recomputed from visible faults per fold, 3 px decimated emission (`emit_decimated` tile_px=3), budget 44,090.

## Checks (fail-closed, thresholds unchanged)
1. Preflight `require_like_for_like()` (PA-86-01) — continuous-surface witness is not a dot-field duplicate.
2. Band-physics QC: Band 12/19 finite median fill, LoG interior check.
3. Leakage canary: feature-alone AUC >0.90 stops.
4. Buffered whole-component holdout (hide 0.20, buffer 3 px, pooled DTI α0.2 β0.8 R300m, 200-px blocks, 1000 draws).
5. Pre-placement surface registry check (ρ≤0.90) — firing stops before placement.
6. Final dots + submission_writer validation (single-band float32 EPSG:32611 3730×3292, [0,1], 0 NaN, zeros outside footprint, zero on mapped faults).
7. Final-dot registry check + PA-86-02 chance-overlap attempt (fail-closed recording, not bypass).
8. Run card with hypothesis, mechanism, mimic, HOLDOUT-DTI+CI, correlation/overlap vs registry, raster sha256, validator output, name+note ≤140 chars, verdict promote/negative.

No weekly slot is selected here; promote means eligible for separate human selector step.

## Outcome 2026-10-25 (2 experiments, 400s)

**E1_warp_persistent (full inverse-slope weight):** HOLDOUT-DTI 0.0358409 [0.0274462, 0.0449846] (11321 withheld positives) vs E3_slope_control 0.013290 [0.00757,0.02040]; delta +0.0225 pooled, CI vs control does not cross zero — warp beats its own slope control on same-split holdout. However candidate trails same-split historical best 0.1241 (H86C-KSLB) so HOLDOUT gate negative (DO NOT SUBMIT). Leakage canary max 0.55 <0.90 pass. Surface registry like-for-like 0 firings (worst 0.47 <0.70); final-dot like-for-like 0 firings (worst 0.689 <0.70 vs GEMSDOE85 geopb-crest 90k) — unique under dot-field gate. Literal continuous-surface firing 1 vs faulthalo (expected, not counted per require_like_for_like). First mild-weight variant (020558Z) had 0.765 overlap (duplicate) and was removed; second full-weight variant (022520Z c0f71390) is the registered audit artifact (18 total).

**Interpretation vs H33 (0.2778 OWNER-REPORTED):** Like GEMSDOE32 H33-2-B2, warp uses coverage-efficient dotted emission (44,090 dots, d>2px, tile3 decimation, median spacing ~2.8 px) to avoid redundant kernel mass under R300m, but unlike H33's collar-subsetting (2545 dots in 1<dcat<=2), warp creates a new geological surface (LoG curvature dipole) under low-relief cover where catalogue is blind. H33's leaderboard lead is thus not new geology but sampling efficiency; warp's modest holdout lift over slope control suggests broad-warp signal exists but is not yet leaderboard-competitive. No organizer-confirmed score projection is made.

**Evidence:** docs/evidence/h86f-warp-run-card.json, docs/downloads/gems86-h86f-warp-broadwarp-44090dots-20261025T022520Z-c0f71390-zeros.tif (sha fddcc0aa, 146KB, 44,090 dots, pass [0,1] CRS 32611).
