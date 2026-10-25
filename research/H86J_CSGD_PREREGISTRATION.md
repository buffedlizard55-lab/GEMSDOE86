# Preregistration — Lane `H86J-CSGD` (2026-10-25)

- **Branch**: `arena/0bec8252-gemsdoe86`
- **Frozen JSON spec**: `research/H86J_CSGD_PREREGISTRATION.json`
- **Ranked 4-hypothesis queue**: `registry/h86j_hypotheses.json`
- **Budget**: Single lane (`H86J-CSGD`), strictly $\le 3$ experiments (`E1`, `E2`, `E3`) plus 0-fit geometry control `R0_D28_visible_collar`, $< 2\text{ hours}$ wall-clock, **0 weekly submission slots consumed**.

---

## 1. Scientific Diagnosis Motivating `H86J-CSGD`

Full-registry (`692` SHA-pinned rasters; `690` grid-compatible) and dual-instrument diagnostics on `GEMSDOE86` revealed two coupled structural failures in prior lanes:

1. **Full-registry audit revokes `H86G-EDTI` (`ba8b731f...`)**:
   PR #107 checked `H86G-EDTI` against only `43` local rasters (`docs/evidence/h86g-edti-registry.json`). Against the restored `655`-blob upstream registry (`692` unique rasters), `H86G-EDTI` triggers **`44` total dot-field overlap firings** (`forward_overlap_3px > 0.70`) and **`25` informative firings** (`halo_coverage <= 0.70`), including sparse `37k–44k`-dot fleet submissions (`GEMSDOE46:r11f` `0.7602` at `44,090` dots, live `0.1589`; `GEMSDOE41:h42` `0.7399` at `40,000` dots, live `0.0245`; `GEMSDOE46:r12` `0.7224` at `37,654` dots, live `0.0843`), while scoring `HOLDOUT-DTI = 0.0631 < R0 (0.0961)`.
2. **Why `H86F-EWCS` (`HOLDOUT-DTI = 0.1723`) collided with range-front priors (`20` informative firings) and trailed `H33` on off-catalogue `SGMC-PROXY-DTI` (`0.0819 < 0.0954`)**:
   Standard Positive-Unlabeled (PU) classifiers trained directly on mapped Quaternary faults $S=1$ with topographic slope (`Band 19`) in the feature matrix learn:
   $$P(S = 1 \mid X_{\text{deep}}, X_{\text{vis}}) \;=\; P(Y = 1 \mid X_{\text{deep}}) \cdot e(X_{\text{vis}}),$$
   where $e(X_{\text{vis}}) = P(S=1 \mid Y=1, X_{\text{vis}})$ is the **surficial scarp mappability propensity**. Steep exposed range fronts (`slope >= 6 deg`) have high $e(X_{\text{vis}})$ and are already mapped in `existing_faults.tif` AND saturated to **94.8%** 3-px halo coverage by `GEMSDOE3:coverage-v3-wide` (`92.6%` by `13GEMSDOE:r6-ensemble`). Conversely, on low-slope alluvial aprons, pediments, stepovers, and basin floors (`slope < 4 deg`, `d_cat > 10 px`), where ~75% of blind Great Basin geothermal conduits reside (Faulds et al., 2015, 2021), `GEMSDOE3` covers only **24.5%** of pixels!

---

## 2. Four Candidate Geological Hypotheses (Ranked Before Execution)

| Rank | ID | Candidate Hypothesis | Verified Layers (`src/gems86/io.py` & Pinned Externals) | Physical Mechanism & Why Missing from Catalogue | Named Non-Fault Mimic | Cost / Status |
|---:|---|---|---|---|---|---|
| **1** | **`H86J-CSGD`** | **SAR Geomorphically De-Biased Cross-Spectral Potential-Field Admittance & Geothermal Upflow Conduit PU** | `B2, B3, B9, B11, B13, B15, B18` (cross-spectral grav-mag + Laplace $g_{zz}$); `B4, B7, B8, B10, B16, B17` (strain/EQ/smectite); `geodawn_extensions` (`TMI_up150`, `ThK`, `UTh`), `geodawn_rad` (`K, Th, U`); `gdr_wellspring` (`temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c`; **`dist_known_fault_px` forbidden**) + `gdr_volcanic_vents` veto; `B6, B12, B15, B19` + `topo_10m dem_mean` **only** in SAR propensity $\hat{e}(X_{\text{vis}})$ | Windowed cross-spectral admittance residuals $|\nabla(\Delta g_{\text{iso}} - H_{\text{GM}}\Delta\text{RTP})|$, hydrothermal magnetite-destruction troughs (`TMI_up150` attenuation on $g_{zz}$ steps), and silica-geothermometer thermal upflow plumes persist across Holocene alluvial aprons where $\hat{e}(X_{\text{vis}}) \ll 1$; SAR odds $((1-\hat{e})/(\hat{e}+\tau))^\gamma$ remove range-front scarp selection bias before 300 m kernel-credit thinning | Pluton-wallrock roof contacts, closed-basin playa lateral outflow plumes, Quaternary volcanic plugs (vetoed via `gdr_volcanic_vents` + curl-vetoed $g_{zz}$) | Medium (~4 min CPU) — **SELECTED** |
| 2 | `H86J-MGRD` | Upward-Continued Magnetic Wavenumber Attenuation (`RTP` vs `TMI_up150`) & Euler $N=0.5$ Depth Staircase | `B2, B3, B9, B14` + `geodawn_extensions` Band 4 (`TMI_up150`) | Vertical harmonic decay $\frac{1}{150\,\text{m}}\ln(\|\nabla\text{TMI}\|/\|\nabla\text{TMI}_{\text{up150}}\|)$ isolates intrabasin magnetic-basement fault steps under non-magnetic Cenozoic fill | Basaltic boulder talus aprons & Miocene ash-flow cooling margins | Low — Deferred (1-lane cap) |
| 3 | `H86J-KNKX` | 10 m 3DEP Stream-Power $k_{sn}$ Transient Knickzone Alignment & 1 m LiDAR Scarp Projection | `dem10_chi_100m_i16` (`ksn_max_m0.9`, `step_max_x1000`), `lidar_scarp_features_u8` (`coh100`, `valid`), `B15`, `geodawn` `ThK` | Active normal slip sends transient $k_{sn}$ knickzones into footwall catchments that survive fan-head debris-flow burial of the canyon-mouth scarp | Resistant quartzite / welded-tuff ledges & heterogeneous 1 m LiDAR tile edges | Medium — Deferred (1-lane cap) |
| 4 | `H86J-MT3D` | EarthScope USArray 3D Magnetotelluric Phase-Tensor Skew ($|\beta| > 3^\circ$) & Subvertical Conductor Ramps | External IRIS/EarthScope SPUD 3D MT impedance models + `B17` (`cond_surf`) + `B8` (`geod_dilaterate`) | Distinguishes subvertical brittle-ductile hydrothermal upflow ramps (3–15 km) from flat-lying saline playas | Paleozoic Roberts Mountains graphitic thrust shales | High — **`NOT_VIABLE_IN_SANDBOX_YET`** (host allowlist) |

---

## 3. Three Preregistered Experiment Arms (`<= 3` Experiments)

1. **`E1_csgd_sar_debiased` (Primary)**: Cover-blind `P_deep` (zero DEM/slope features) + strictly fold-visible Pollard-Segall crack-tip/stepover fields, multiplied by SAR geomorphic censoring odds $((1-\hat{e}(X_{\text{vis}}))/(\hat{e}(X_{\text{vis}})+0.12))^{0.85}$, convolved with `vendor/gems57/emit.py::expected_credit` (`300 m` triangular kernel), Poisson-disc thinned at `d = 2.8 px`, `37,654` dots (`d_vis > 3.0 px`).
2. **`E2_csgd_unweighted_pu_ablation` (SAR Censoring Ablation)**: Identical `P_deep` + fold-visible elastic fields + `300 m` expected-credit emitter with $\gamma = 0.0$ (no SAR burial reweighting).
3. **`E3_csgd_autonomous_blind_conduit` (Elastic-Free Autonomous Conduit Ablation)**: Cover-blind `P_deep` with **zero** fold-visible elastic/catalogue features + SAR burial reweighting ($\gamma = 0.85$) + `300 m` expected-credit emitter (`37,654` dots, `d_vis > 3.0 px`).

All outputs are audited fail-closed under `AGENTS.md` Rules 2–11 (`check_h86e_registry.py --surface`, `check_h86e_registry.py`, `pa86_chance_overlap.py`, `validate.py`, `submission_writer.py`).
