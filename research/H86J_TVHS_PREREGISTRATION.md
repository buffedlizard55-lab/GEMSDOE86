# H86J-TVHS Frozen Preregistration & Ranked Geological Hypothesis Queue (2026-10-25)

**Status:** `FROZEN_BEFORE_IMPLEMENTATION` (`2026-10-25T05:02:00Z`)  
**Machine-readable preregistration:** `research/H86J_TVHS_PREREGISTRATION.json`  
**Machine-readable 4-hypothesis queue:** `registry/h86j_hypotheses.json`  
**Assigned lane:** `H86J-TVHS` (*Pedersen–Rasmussen Harmonic Gravity-Gradient Tensor 2-D Sheet-Step Invariants × Faulds–Hinz Geothermal Structural-Complexity Triangulation × Exposure-Propensity Dual-Expert PU Expected-Kernel-Credit Discovery*)  
**Budget cap:** `<= 3` experiments (`E1`, `E2`, `E3`), `<= 2` hours CPU, `0` live weekly DrivenData submission slots consumed.

---

## 1. Four Untried Candidate Geological Hypotheses (Ranked Before Implementation)

All `training_features.tif` band numbers are verified against `src/gems86/io.py` (`BANDS` + `BAND_PHYSICS_VERIFIED`, including pixel-verified `Band 6 = tc` GeoDAWN Total Count, `Band 11 = +dg/drow_south = -dg/dy_north`, and `Band 18 = +dg/dx_east`).

### Rank 1 (Selected for Validation) — `H86J-1_TVHS`: Harmonic Gravity-Gradient Tensor (`GGT`) 2-D Sheet-Step Invariants × Faulds–Hinz Geothermal Structural-Complexity Triangulation × Exposure-Propensity Dual-Expert PU `E[k]` Discovery
- **Specific layers:**
  - Native `training_features.tif`: `Bands 11, 13, 15, 18` (signed horizontal gravity vector, isostatic gravity, basement depth), `Bands 2, 3, 9, 14` (RTP, magnetic horizontal/vertical derivatives, TMI), `Bands 4, 7, 8, 10, 16, 17` (GPS strain second invariant, shear, dilatation, seismic distance/intensity, 2 km MT conductivity), `Bands 6, 12, 19` (GeoDAWN Radiometric Total Count, detrended elevation, slope).
  - Official public-domain SHA-256-pinned external inputs on disk: DOE GDR-1391 (`https://gdr.openei.org/submissions/1391`) `2m_temperature_probe_INGENIOUS_regional_data.zip` (`3,800` 2-m probes), `paleo_geothermal_regional.zip` (`726` Holocene/Pleistocene sinter/travertine/tufa mounds), `gdr_wellspring_in_footprint.csv` (`temp_c`, `geothermquartz_c`, `geothermchalc_c`; **`dist_known_fault_px` strictly banned and audited**); USGS 3DEP `lidar_scarp_features_u8.tif` (`step_max`, `cross_max`, `coh100`, `strike`), `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_u8.tif` (`knick_n`, `raised_n`); USGS GeoDAWN `geodawn_rad_u8.tif` / `geodawn_extensions_u8.tif` (`K, Th, U, ThK, UK, UTh`) + `acquisition_block_id_100m.tif`.
- **Physical signature & mathematical transform:**
  1. **3×3 Harmonic Marussi/Eötvös Gravity Gradient Tensor (`GGT`) & Pedersen–Rasmussen (1990) 2-D Dimensionality Index:** Differentiate verified signed horizontal gravity components `(B18 = +dg/dx_east, -B11 = +dg/dy_north)` to obtain $T_{xx}, T_{yy}, T_{xy}$, Laplace vertical curvature $T_{zz} = -(T_{xx}+T_{yy})$, invariant $I_1 = T_{xx}T_{yy} + T_{yy}T_{zz} + T_{zz}T_{xx} - T_{xy}^2$, Differential Curvature $T_{\Delta} = \sqrt{(T_{xx}-T_{yy})^2 + 4T_{xy}^2}$, and quasi-2D fault-step dimensionality index $\mathcal{D}_{2\text{D}} = T_{\Delta}^2 / (T_{\Delta}^2 + 4|I_1| + \varepsilon)$, plus multi-azimuth GGT × RTP magnetic tilt-zero conjugate intersection density.
  2. **Faulds–Hinz Geothermal Structural-Setting Triangulation:** Combine cover-penetrating hydrothermal upflow (`|grad T_2m|` thermal walls, opaline sinter/tufa mounds, 300 m upslope silica geothermometer excess, MT clay-cap margin gradient `|grad B17|`) with strictly fold-visible nested cross-component Pollard–Segall tensile wing-crack lobes, opposing-tip releasing stepovers, **high-angle conjugate fault-intersection cones**, and mid-segment broadside elastic stress shadows.
  3. **Exposure-Propensity Strict-LOQO Dual-Expert PU + `E[k]` Expected-Kernel-Credit Emission:** Reweight PU training by inverse surficial exposure propensity $1/\hat{c}_{\text{expo}}(x)$ (estimated smoothly from slope `Band 19`, local relief, and alluvial radiometric cover without reading labels), train strictly out-of-quadrant (`quad != q`) **Expert A (`P_coupled`)** and **Expert B (`P_blind`, 100% zero-catalogue)** `HistGradientBoostingClassifier` models, fuse via calibrated Noisy-OR, convolve with the exact 300 m triangular Tversky kernel (`vendor/gems57/emit.py::expected_credit`), and emit `37,654` unit dots at `r = 2.8 px` spacing behind a `d > 3.0 px` collar.
- **Why missing from USGS/INGENIOUS catalogue:** ~78% of blind Great Basin geothermal systems sit at stepovers, horsetail terminations, and conjugate fault intersections concealed beneath young bajada washes and Lahontan/Bonneville lakebeds (Faulds & Hinz 2015). Standard PU classifiers underweight low-slope basin floors and starve distal off-catalogue basins; GGT $\mathcal{D}_{2\text{D}}$ + hydrothermal vents + exposure-propensity Dual-Expert PU directly recovers both proximal unmapped extensions and distal blind conduits.
- **Named non-fault mimic:** Circular 3-D pluton stocks and volcanic plugs ($\mathcal{D}_{2\text{D}} \to 0$ veto), down-gradient lateral alluvial thermal outflow plumes (mitigated by `|grad T_2m|` walls + 300 m upslope advection), Pleistocene Lake Lahontan/Bonneville shorelines (`1270, 1332, 1463, 1552 m`), and GeoDAWN survey-block stitch seams.
- **How it differs from repo:** First implementation in `GEMSDOE86` of Pedersen–Rasmussen GGT invariants $(I_1, T_{\Delta}, \mathcal{D}_{2\text{D}})$, high-angle conjugate intersection triangulation, exposure-propensity-weighted strict-LOQO Dual-Expert PU learning (fixing `H86F-EWCS`'s in-quadrant training limitation `IR-86-EWCS-INQUADRANT-20261025`), and unified GDR-1391 hydrothermal + 3DEP 1-m LiDAR + GGT `E[k]` spacing-greedy emission.

### Rank 2 (Deferred behind Rank 1 under 3-Experiment Budget) — `H86J-2_WTHD`: Multiscale Fourier Upward-Continuation Potential-Field Structural-Index Tomography ($N_{\text{SI}}$)
- **Layers:** `training_features.tif` `Bands 2, 3, 9, 11, 13, 15, 18` (viable now; SHA-verified on disk).
- **Transform:** 5-altitude Fourier upward continuation $e^{-2\pi |\mathbf{k}| z}$ ($z \in \{100, 200, 400, 800, 1600\}\text{ m}$) estimating local Moreau–Hornby homogeneity degree $N_{\text{SI}}(x,y)$ along horizontal-gradient ridges to separate sub-vertical normal-fault steps ($N_{\text{SI}} \approx 0.0\text{–}0.5$) from surficial basalt sheets ($N_{\text{SI}} \approx 1.5\text{–}2.0$) and 3-D dipoles ($N_{\text{SI}} \approx 2.5\text{–}3.0$).
- **Named non-fault mimic:** Steep unfaulted Mesozoic pluton contacts.

### Rank 3 (Deferred behind Rank 1 under 3-Experiment Budget) — `H86J-3_KNIC`: Cross-Bajada Tributary Fluvial $\chi$-Knickzone Collinearity & Radiometric Provenance Continuity
- **Layers:** `dem10_chi_100m_u8.tif`, `topo_10m_derived_100m_u8.tif`, `lidar_scarp_features_u8.tif`, `Bands 6, 11, 12, 18, 19` (viable now; SHA-verified on disk).
- **Transform:** Thalweg $\chi$-knickzone jumps aligned across $\ge 3$ adjacent piedmont washes, gated by cross-knickzone `Band 6` Radiometric Total Count continuity to reject resistant bedrock ledges.
- **Named non-fault mimic:** Resistant welded-tuff ledges and pluvial delta fronts.

### Rank 4 (`NOT_VIABLE_IN_SANDBOX_YET`) — `H86J-4_INSAR`: OPERA Sentinel-1 Ascending/Descending InSAR Hydraulic-Barrier & Poroelastic Geothermal Phase-Gradient Discontinuities
- **Official source & obtainability check:** Free public-domain NASA JPL/Caltech OPERA L3 DISP-S1 (`https://search.asf.alaska.edu/`) and UNR NGL (`http://geodesy.unr.edu/`). Verified unreachable under sandbox outbound allowlist (`github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`); flagged `NOT_VIABLE_IN_SANDBOX_YET` per protocol.

---

## 2. Frozen 3-Arm Single-Lane Experimental Protocol (`H86J-TVHS`)

- **Shared evaluator (unchanged):** `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, `11,321` withheld positives across `NW, NE, SW, SE`, 1,000-draw paired 20 km block bootstrap).
- **Shared writer (unchanged):** `vendor/gems57/submission_writer.py`.
- **Arms (`37,654` dots, `r = 2.8 px`, `d > 3.0 px` collar):**
  1. `E1_tvhs_dual_expert_ek` — Full Exposure-Propensity Strict-LOQO Dual-Expert PU (`P_coupled` + `P_blind`) + `E[k] = S (*) K_300m` spacing-greedy candidate.
  2. `E2_tvhs_blind_geothermal_ggt_ek` — 100% zero-catalogue `P_blind` + `E[k]` spacing-greedy control.
  3. `E3_tvhs_unweighted_rawpixel_ablation` — 19-band native-only unweighted LOQO PU ablation emitted by raw pixel probability (no GGT 2-D invariants, no GDR/3DEP/GeoDAWN externals, no exposure-propensity weights, no Dual-Expert blind floor, no `E[k]` kernel convolution).
