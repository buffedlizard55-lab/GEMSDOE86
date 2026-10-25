# Frozen Preregistration — Lane `H86J-MCSP` (`2026-10-25`)

- **Machine-readable pin:** `research/H86J_MCSP_PREREGISTRATION.json`
- **Frozen before feature/model implementation:** `2026-10-25T04:08:00Z`
- **Protocol compliance:** `AGENTS.md` Rules 1–12, Parallel-Run Protocol Rules 1–6 (`max_experiments = 3`, `max_hours = 2`, fixed dot budget `37,654`, `min_spacing_px = 2.8`, `collar_px = 3.0`, zero post-hoc budget snooping).

## 1. Scientific Diagnosis Motivating `H86J-MCSP`

Across all prior lanes in `GEMSDOE86`, two disjoint failure modes separated catalogue-hide holdout performance from off-catalogue structural generalization:
1. **`H86G-EDTI` (`promote`, 55,000 dots)**: Unsupervised 8-detector scalar edge rank (`L_lineament`) achieved `SGMC-PROXY-DTI = 0.1223` at `55,000` dots (`0.0947` at `37,654` dots), but only `HOLDOUT-DTI = 0.0631` (`0.0097` in NE) because scalar gradient amplitudes weight strongly magnetized Miocene–Pliocene basalt flow margins 10x–50x higher than weakly contrasted intra-basin Quaternary faults; conversely, its `H_hgb` arm (`HOLDOUT-DTI = 0.1689` @ `37,654`) included raw regional elevation/gravity/magnetic background levels (`b01, b02, b12, b13, b14, b15`) without Leave-One-Quadrant-Out (`LOQO`) spatial cross-fitting, memorizing mountain-range habitats and dropping to `SGMC-PROXY-DTI = 0.0680`.
2. **`H86F-EWCS` (`HOLDOUT-DTI = 0.1723`, 37,654 dots)**: Demonstrated the power of Pollard–Segall elastic crack-tip & broadside stress-shadow mechanics (`+0.0131` paired lift over isotropic tip control), but used only 18 native bands (omitting pinned public-domain 3DEP LiDAR scarps, GeoDAWN `K/Th/U/TMI_up150`, and fluvial $\chi$-knickzones), trained across all 4 quadrants simultaneously rather than spatial `LOQO`, and emitted dots via static disk thinning rather than exact submodular marginal DTI-numerator optimization.

## 2. Four Ranked Untried Geological Hypotheses (Frozen Pre-Implementation)

1. **Rank 1 (`H86J-MCSP` — Selected for Validation)**: *Monogenic Cross-Spectral Phase-Congruent Structural Conduit + Out-of-Quadrant Geothermal Fault-Intersection Specialist with Exact Submodular CELF Kernel Allocation*.
   - **Layers**: Native `training_features.tif` Bands `2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19` (`src/gems86/io.py:BANDS` verified) + pinned public-domain externals `geodawn_extensions_u8.tif` (`ThK, UK, UTh, TMI_up150`), `geodawn_rad_u8.tif` (`K, Th, U, TC`), `lidar_scarp_features_u8.tif` (excluding `valid` and `strike`), `topo_10m_derived_100m_u8.tif`, and `dem10_chi_100m_i16.tif`.
   - **Physical signature**: Multi-scale 2-D Riesz monogenic phase congruency ($\sigma \in \{1.5, 3.0, 6.0\}\text{ px}$, strictly contrast-amplitude invariant), `TMI` vs `TMI_up150` vertical structural attenuation, hydrothermal magnetite-destruction troughs inside gravity phase steps, Hessian-eccentricity linear `cond_surf` conduits, Lahontan-deconfounded `K/Th` & `U/Th` epithermal metasomatism, structure-tensor fault-intersection determinant ($\det J / \operatorname{tr} J$, targeting blind Great Basin geothermal stepovers/intersections per Faulds & Hinz 2015), 3DEP LiDAR/fluvial-$\chi$ scarps, and strictly fold-visible Pollard–Segall fracture-tip lobes — trained strictly with **4-fold Leave-One-Quadrant-Out (`LOQO`)** on **translation-invariant operators only** (zero raw regional background levels) and allocated via **exact `heapq` CELF submodular marginal kernel credit**.
   - **Named non-fault mimic**: Buried Tertiary caldera ring-fracture walls or welded tuff cooling-unit pinch-outs altered by fossil Miocene epithermal systems, and Pleistocene Lake Lahontan (~1,330 m) wave-cut benches adjacent to conductive playas.
2. **Rank 2 (`H86J-WCA` — Reserve)**: *Upward-Continuation Wavenumber Attenuation Structural Index (`TMI` vs `TMI_up150`) for Intra-Graben Faults* (mimic: Miocene mafic feeder dikes).
3. **Rank 3 (`H86J-KCSN` — Reserve)**: *Anisotropic Drainage-Divide $\chi$-Asymmetry Coupled with Crustal Transtensional Strain-Rate Alignment* (mimic: differential granite–tuff erodibility).
4. **Rank 4 (`H86J-ECFN` — Reserve)**: *Hessian-Eccentricity Conductive Fault-Gouge Necking Deconfounded from Isotropic Evaporite Playas* (mimic: clay-filled axial paleochannels).

## 3. Three Frozen Experimental Arms (`max_experiments = 3`, `37,654` Dots)

- **`E1_mcsp_dual_celf`**: Dual-regime Noisy-OR $S = 1 - (1 - 0.50 P_{\text{blind}})(1 - 0.65 P_{\text{kin}})$ with 4-fold spatial `LOQO` cross-fitting + exact `CELF` submodular marginal credit (`min_spacing = 2.8 px`, `collar > 3.0 px`, `37,654` dots).
- **`E2_mcsp_blind_celf`**: Pure catalogue-blind specialist $P_{\text{blind}}$ (`0` catalogue-geometry inputs) + exact `CELF` (`37,654` dots).
- **`E3_mcsp_amp_staticek_ablation`**: Standard scalar amplitude gradients + isotropic tip halo + static `E[k]` spacing-greedy (no monogenic phase, no geothermal intersection/conductance/metasomatism, no CELF residual-credit updates) at identical `37,654` dots and `3.0 px` collar.

## 4. Binding Fail-Closed Gate Rules

Per `AGENTS.md` Rules 6, 10, 11, and 12:
1. Every feature must pass single-feature `LEAKAGE-CANARY` (`max(AUC, 1 - AUC) <= 0.90`).
2. `scripts/check_h86e_registry.py --surface` runs before full-catalogue placement; `scripts/check_h86e_registry.py` and `scripts/pa86_chance_overlap.py` run on final dots before serialization.
3. Because `research/upstream/registry_inventory.json` retains 2 incompatible historical rasters (`14GEMSDOE`, `7GEMSDOE`) and literal `17GEMSDOE` full-footprint support (`1.0 > 0.70`), any candidate evaluated under the strict v2 690-file gate fails closed to `verdict = "negative"`, `decision = "DO NOT SUBMIT"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`, preserving `H86G-EDTI` as the sole PA-86-01 `promote` card per Rule 12 while publishing complete `HOLDOUT-DTI`, `SGMC-PROXY-DTI`, and registry measurements for audit and future selector review.
