# Preregistration: Lane `H86M-PFTE` & Ranked `H86M` Hypothesis Queue (2026-10-25)

- **Branch:** `arena/2ea5b025-gemsdoe86`
- **Frozen UTC (before model/feature code):** `2026-10-25T16:28:00Z`
- **Machine-readable queue:** `registry/h86m_hypotheses.json`
- **Selected single-method lane:** `H86M-PFTE` (*3-D Cordell–Parker Spectral Compaction-Stripped Marussi Gravity Tensor Eigensystem, Baranov Pseudogravity Decoupling & Strike-Guided Peclét Dispersion with Comonotonic Tube-Survival Dinkelbach-CELF*)

## 1. Verified Band Physics & Official Data Provenance

All native bands obey `BAND_PHYSICS_VERIFIED` in `src/gems86/io.py` (audited empirically against `training_features.tif`, SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`):
- **Band 6 (`tc`)** is **GeoDAWN Airborne Radiometric Total Count** (`min = +2.9534`, `r = +0.997140` vs `geodawn_rad_u8` TC), **never** magnetic tilt.
- **Band 18 (`iso_grav_anom_hg`)** is the **signed Eastward** gravity derivative $+\partial(\text{Band 13})/\partial x_{\text{east}}$ (`r = +0.948186`), **not** an unsigned gradient magnitude.
- **Band 11 (`iso_grav_anom_vg`)** is the **signed Southward** gravity derivative $+\partial(\text{Band 13})/\partial y_{\text{south}} = -\partial(\text{Band 13})/\partial y_{\text{north}}$ (`r = +0.938102`), **not** a vertical derivative.
- **Band 5 (`iso_grav_anom_slope`)** is the unsigned 2-D horizontal gravity slope $\operatorname{hypot}(\text{Band 11}, \text{Band 18})$ (`r = +0.946995`).
- All external public-domain layers are SHA-256-verified from official USGS GeoDAWN (`https://doi.org/10.5066/P93LGLVQ`), USGS 3DEP (`https://www.usgs.gov/3d-elevation-program`), and DOE GDR `#1391` INGENIOUS (`https://gdr.openei.org/submissions/1391`); `dist_known_fault_px` in `gdr_wellspring_in_footprint.csv` is strictly banned and never read.

## 2. Ranked `H86M` Untried Geological Hypotheses

| Rank | ID | Specific Layers | Physical Signature & Transform | Why Missing from USGS/INGENIOUS Catalogue & Differentiation |
| :--- | :--- | :--- | :--- | :--- |
| **1 (Selected)** | **`H86M-PFTE`** | Native Bands `2,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19`; GeoDAWN `geodawn_rad_u8`, `geodawn_extensions_u8`, `acquisition_block_id_100m`; 3DEP `lidar_scarp_features_u8`, `topo_10m_derived_100m_u8`, `dem10_chi_100m_i16`; DOE GDR `#1391` `2m_temperature_probe`, `paleo_geothermal`, `gdr_wellspring` (`temp_c`, `geotherm*` only), `gdr_volcanic_vents` | **3-D Cordell–Parker Spectral Compaction-Stripped Marussi Gravity Tensor + Baranov Pseudogravity Decoupling + Strike-Guided Peclét Thermal Barrier + Comonotonic Tube-Survival Dinkelbach-CELF:** Strips 3-D multi-shell attenuated sedimentary compaction bowls ($e^{-\|\mathbf{k}\|z_m - z_m/1500\text{ m}}$) from `(B13, +B18, -B11)`, decomposes the 2×2 symmetric horizontal Marussi tensor into $(\lambda_1-\lambda_2)$, hyperbolic contact saddle $\sqrt{\max(0,-\lambda_1\lambda_2)}$, Beiki curvature-tilt, strike $\theta_{\text{grav}}$, and conservative curl seam veto $\|\partial_y g_x - \partial_x g_y\|$; pairs with Baranov FFT pseudogravity vector decoupling, across-vs-along-strike Peclét thermal/geochemical barrier sharpness, LOQO Noisy-OR, and 1-D Fréchet–comonotonic fault-tube survival self-credit | Sub-alluvial intrabasin horsts, accommodation zones, and piedmont synthetic stepovers lack >2 m Quaternary scarps while smooth 3-D basin bowls mask Band 5 gravity slope. Distinct from all prior lanes (`H86L-FMC` ensemble, `H86K-STDP` Salem pullback + independent-Bernoulli rings, unrun 1-D Bouguer `BMR`) |
| **2** | **`H86M-HDEC`** | Native Bands `2,3,9,11,13,17,18`; GeoDAWN `TMI_up150`; GDR-1391 `gdr_volcanic_vents` | **3-D Reid–Thompson Euler Deconvolution ($N=0.5$ Contact Sheet vs $N=2.0$ Pipe Rejection) + MT Skin-Depth Upflow Corridors** | Recovers 3-D sub-playa fault-contact apexes $(x_0,y_0,z_0)$ directly from potential-field homogeneity without basement depth `B15`; never implemented in GEMSDOE86 |
| **3** | **`H86M-SGRT`** | Native Bands `4,7,8,12,19`; 3DEP `dem10_chi_100m_i16`, `topo_10m_derived_100m_u8`, `lidar_scarp_features_u8` | **Multi-Watershed Cross-Divide Fluvial $\chi$ Knickline Colinearity Orthogonal to Principal Geodetic Extension** | Detects slow (`0.1–0.3 mm/yr`) E/NE Nevada distributed pediment faults across >=3 adjacent watersheds without discrete aerial scarps |
| **4** | **`H86M-RMRF`** | Native Bands `6,10,16,17`; GeoDAWN `geodawn_rad_u8`, `acquisition_block_id_100m`; GDR-1391 `paleo_geothermal` | **Aitchison Isometric Log-Ratio (`ilr`) Ternary K–eTh–eU Metasomatic Roll-Fronts Above Seismogenic Hypocenter-Depth (`B10`) Ramps** | Isolates recessive epithermal altered fault saddles updip of active dipping microseismic ramps while removing compositional closure |

## 3. Preregistered 3-Arm Validation Budget (`<= 3` Experiments)

1. **`E1_pfte_comonotonic_dcelf`:** Full PFTE 4-fold LOQO dual-regime Noisy-OR + 1-D Fréchet–comonotonic fault-tube survival Dinkelbach-CELF (`37,654` unit dots, `d_min = 2.8 px`, `d_cat > 3.0 px`).
2. **`E2_pfte_blind_comonotonic_dcelf`:** Pure catalogue-blind PFTE 4-fold LOQO specialist + comonotonic tube-survival Dinkelbach-CELF (`37,654` unit dots, zero fold-visible catalogue features).
3. **`E3_unstripped_scalar_indep_ablation`:** Controlled falsifier replacing Cordell–Parker stripping, Marussi tensor invariants, Baranov decoupling, strike-guided Peclét dispersion, and comonotonic tube survival with unstripped scalar slopes + isotropic thermal blur + static-$E[k]$ Poisson-disc spacing (`37,654` unit dots).
