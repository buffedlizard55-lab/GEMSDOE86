# H86N-SHPB Preregistration & Candidate Geological Hypothesis Queue

- **Lane ID:** `H86N-SHPB`
- **Branch:** `arena/fd5fa170-gemsdoe86`
- **Frozen UTC:** `2026-10-25T18:40:00Z`
- **Machine Preregistration:** [`research/H86N_SHPB_PREREGISTRATION.json`](H86N_SHPB_PREREGISTRATION.json)
- **Hypothesis Queue Registry:** [`registry/h86n_hypotheses.json`](../registry/h86n_hypotheses.json)
- **Protocol Budget:** `<= 3` experiments (`E1`, `E2`, `E3`), `<= 2` hours, `0` weekly submission slots spent.

---

## 1. Diagnosis of Prior Repository Bottlenecks (`H86I-KSAD` vs `H86K-STDP` vs `H86M`)

Across the 18 prior lanes in `GEMSDOE86` (`H86A` through `H86M`), two complementary mechanisms achieved the strongest measured results on our two orthogonal evaluation instruments, yet each failed a complementary gate:

1. **`H86I-KSAD` (`HOLDOUT-DTI = 0.1599 [0.1459, 0.1742]` on `E2`, `0.1553 [0.1396, 0.1718]` on `E1`):**
   - Achieved the repository's highest strict Leave-One-Quadrant-Out (`LOQO`) `HOLDOUT-DTI` by training a 2-seed diverse-depth HistGradientBoosting ensemble jointly on static geophysical planes + 6 anisotropic Kostrov-Pollard fracture-mechanics planes with SAR exposure-propensity weights and **Elkan (2001) Bayes subsampling prior-odds recalibration** (preserving the natural fold base-rate difference between fault-dense `SW`/`SE` and sparsely mapped `NE`/`NW`).
   - **Why it failed:** `H86I-KSAD` used a tight `2.6 px` catalogue collar and `2.4 px` dot spacing with weak blind-basin weight, causing **`71.31%`** of its final dots to fall within `3 px` of `GEMSDOE80` (exceeding the `0.70` discrete duplicate threshold by `1.31%`).

2. **`H86K-STDP` (`SGMC-PROXY-DTI = 0.1133` on `E1`, `0.1151` on `E2`; max discrete 3-px overlap `= 0.3711 <= 0.70`):**
   - Introduced multi-altitude 2-D FFT Salem-Fairhead (2007) tilt-zero dip-migration, bilinear hanging-wall-to-footwall up-dip basement pullback (`clip((Z_b/100)*cot(60 deg), 0, 8 px)`), up-hydraulic-head advected DOE GDR #1391 silica/cation geothermometry + 2-m probe thermal walls + paleo-sinter vents, and **Exact 6-Ring Bernoulli Survival Supremum Self-Credit Dinkelbach-CELF** (`d_cat > 3.0 px`, `min_spacing = 2.8 px`, `37,654` dots).
   - **Why it fell short on `HOLDOUT-DTI` (`0.1380 [0.1223, 0.1545]`):**
     1. `calibrate_quadrant_sparse_posterior` forced all four quadrants (`NW`, `NE`, `SW`, `SE`) to have identical median and 90th-percentile logits on *both* `P_blind` and `P_kin`, starving `SW` (`3,781` withheld positive pixels) and `SE` (`3,250` withheld positive pixels) of ~6,500 high-precision tip/relay dots (`SW` dropped from `0.1609` in `KSAD` to `0.1257` in `STDP`).
     2. `H86K-STDP` trained `P_kin` on only 4 isotropic `gems86_ewcs` fracture planes rather than the 6 anisotropic Kostrov-Pollard planes (`collinear_tip_cone_long`, `strike_anisotropic_corridor`) coupled jointly with the static geophysical stack.
     3. `H86K-STDP` did not separate **odd-symmetric basement fault steps** ($\phi = \pm \pi/2$) from **even-symmetric volcanic dikes and paleochannels** ($\phi \in \{0, \pi\}$), nor did it align the **earthquake epicentral lineation tensor** (`Bands 10, 16`) with the **Kostrov transtensional strain-rate tensor** (`Bands 7, 8`).

3. **`H86M-BMR`, `H86M-CNT`, and `H86M-LT`:**
   - `H86M-BMR` (`0.0258` HOLDOUT-DTI) and `H86M-CNT` (`0.0170` HOLDOUT-DTI) tested standalone 2-band gravity-basement residuals and conductivity necks without fracture/geothermal coupling and scored below controls.
   - `H86M-LT` (`PR #165`) synthesized a dot set by tomographically inverting 29 scored sibling rasters without running `vendor/gems57/evaluate_holdout.py` or single-feature leakage canaries; it is quarantined as `verdict = "negative"`, `DO NOT SUBMIT`.

---

## 2. Four Candidate Geological Hypotheses (`H86N` Queue)

| Rank | ID | Candidate Hypothesis | Specific Layers | Physical Signature & Transform | Why Off-Catalogue vs Non-Fault Mimic | Expected DTI Gain / Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **`H86N-SHPB`** | **Steerable Odd-Step vs Even-Dike Quadrature Phase-Asymmetry + Up-Dip Pullback + Seismic-Geodetic Lineation + Cover-Aware Elkan-Bayes 6-Ring Dinkelbach-CELF** | Native Bands `2,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19` + SHA-pinned `.cache/external/` (`geodawn_rad_u8`, `geodawn_extensions_u8`, `acquisition_block_id_100m`, `lidar_scarp_features_u8`, `topo_10m_derived_100m_u8`, `dem10_chi_100m_i16`, GDR #1391 2-m probes, paleo-sinter, wells/vents CSVs with `dist_known_fault_px` banned) | Steerable odd-over-even step asymmetry $\mathcal{A}_{\text{step}} = (\|\nabla_n \phi\| - |\partial_{nn}\phi|)/(\|\nabla_n \phi\| + |\partial_{nn}\phi| + \varepsilon)$ on vector gravity (`B11,B13,B18`) and RTP/`TMI_up150` (`B2`, ext `B4`) pulled back up-dip by $(Z_b/100)\cot 60^\circ$; seismic-lineation structure tensor (`B10,B16`) aligned with Kostrov dilation/shear (`B7,B8`); coupled 30-feature Elkan-Bayes LOQO ensemble + cover-aware blind specialist decoded by 6-ring survival Dinkelbach-CELF (`37,654` dots, `d_cat > 3.0 px`, `d_min = 2.8 px`). | Catches concealed 55–65°-dipping intrabasin fault steps and unmapped range-tip relays while rejecting even-symmetric Miocene Northern Nevada Rift mafic dikes, Lahontan shorelines, and GeoDAWN flight seams. | **Highest** on both `HOLDOUT-DTI` and `SGMC-PROXY-DTI` / **Medium** cost (~18 min CPU, `<900 MiB` RSS) | **SELECTED FOR VALIDATION** |
| **2** | **`H86N-EQLA`** | **Microseismic-Hypocentral Lineation Structure Tensor & Geodetic Coulomb Stress-Rate Coupling** | Native Bands `4 (geod_2ndinv)`, `7 (geod_shearrate)`, `8 (geod_dilaterate)`, `10 (deq_n100a15)`, `15 (depth_to_base_surf)`, `16 (ieq_n100a15)` | 2-D structure-tensor anisotropy $(\lambda_1-\lambda_2)/(\lambda_1+\lambda_2)$ and strike director of $\log(1+\text{B10})$ and $\text{B16}$ projected onto Kostrov dilation $\text{B8}_+\cos^2(\theta-22^\circ)$ and Riedel shear $\text{B7}\sin^2(2(\theta-22^\circ))$. | Catches creeping accommodation-zone and Walker Lane stepover faults hosting linear microseismic streaks without surface scarps; suppresses isotropic swarms/quarry blasts. | **Medium-High** / **Low** cost (core plane incorporated as feature 14 of `H86N-SHPB`) | **QUEUED (SELF-CONTAINED)** |
| **3** | **`H86N-BFAH`** | **Listric Hanging-Wall Rollover Antithetic Fiber-Bending Curvature & Conductive Clay-Cap Termination** | Native Bands `13 (iso_grav_anom)`, `15 (depth_to_base_surf)`, `17 (cond_surf)`, `19 (det_elev_slope)` + `topo_10m_derived_100m_u8.tif` | Directional rollover bending strain $-\partial_{uu}^2 Z_b(x + \Delta s\,\mathbf{u}_{\text{downdip}})$ at 1.5–3.5 km hanging-wall standoff gated by lateral termination of smectite clay-cap conductance (`B17`). | Catches blind antithetic keystone faults 1.5–3.5 km basinward of mapped master range-front scarps; suppresses symmetric playa evaporation pans. | **Medium** / **Low-Medium** cost (core rollover hinge incorporated in `H86N-SHPB`) | **QUEUED (SELF-CONTAINED)** |
| **4** | **`H86N-INSAR`** | **ARIA/COMET Sentinel-1 Ascending+Descending InSAR Vertical Subsidence & Fault-Parallel Creep Step** | Official free public sources: NASA/JPL ARIA GUNW (`https://asf.alaska.edu/data-sets/derived-data-sets/insar/`) & COMET LiCSAR (`https://comet.nerc.ac.uk/COMET-LiCS-portal/`) + native Bands `4,7,8,15` | 100 m high-pass vertical deformation phase-gradient step across blind intrabasin faults acting as hydraulic compartment barriers. | Catches zero-relief playa hydraulic-barrier faults invisible to 10–20 km GPS station interpolations; mimics are agricultural pumping cones. | **High** theoretical potential, but **Blocked** in sandbox (`outbound internet restricted to github/pypi/npmjs`; no pinned InSAR mirror) | **DEFERRED (EGRESS BLOCKED)** |

---

## 3. Preregistered 3-Experiment Budget (`E1`, `E2`, `E3`)

1. **`E1_shpb_coupled_dinkelbach_celf` (Primary Candidate):**
   - Full 24-feature `H86N-SHPB` translation-invariant static stack + 6 fold-visible anisotropic Kostrov-Pollard fracture fields (`30` features total; max single-feature leakage canary $\max(\text{AUC}, 1-\text{AUC}) \le 0.90$).
   - Strict 4-fold Leave-One-Quadrant-Out (`quad != q` eroded 12 px) + nested cross-component PU ensemble calibrated via **Elkan (2001) Bayes subsampling prior-odds recalibration**, fused via **cover-aware Noisy-OR** with the quadrant-sparse blind `H86N-SHPB` conduit specialist, and decoded into `37,654` unit dots (`d_cat > 3.0 px`, `min_spacing = 2.8 px`) via **Exact 6-Ring Bernoulli Survival Supremum Self-Credit Dinkelbach-CELF**.
2. **`E2_shpb_blind_conduit_dinkelbach_celf` (Zero-Catalogue-Feature Blind Conduit Specialist):**
   - Uses only the 24 translation-invariant `H86N-SHPB` static geophysical/geothermal/LiDAR planes + physics corroboration prior (`0` fold-visible elastic features at inference), testing pure blind geothermal/intrabasin conduit discovery on both `HOLDOUT-DTI` and off-catalogue `SGMC-PROXY-DTI`.
3. **`E3_local_unpulled_staticek_ablation` (Preregistered Ablation Control):**
   - Replaces steerable odd-step phase-asymmetry, up-dip basement pullback, multi-altitude Salem dip-migration, seismic-geodetic lineation alignment, and up-hydraulic-head geothermometry with 8 pixel-local unpulled gradient/blur planes + static expected-kernel Poisson-disc thinning (`37,654` dots, `d_cat > 3.0 px`, `min_spacing = 2.8 px`).
