# Pre-Implementation Geological Hypotheses (`GEMSDOE86` / `Lane H86-FVMB`)

**Preregistered UTC**: `2026-10-22` (frozen in [`registry/preregistration_h86.json`](../../registry/preregistration_h86.json) prior to executing any holdout experiment)  
**Target Competition**: [DrivenData — Detect Hidden Faults to Unlock Clean Geothermal Energy (DOE GEMS)](https://www.drivendata.org/competitions/306/competition-doe-gems/)  
**Metric Physics**: Distance-Weighted Tversky Index (`DW-Tversky`, $\alpha = 0.2$, $\beta = 0.8$, $300\text{ m}$ linear-cone triangular kernel, masked pixel-exact on `existing_faults.tif`)

---

## Ranked Candidate Geological Hypotheses (5 Candidates)

| Rank | ID | Hypothesis Title | Expected $\Delta\text{DTI}$ | Implementation Cost | Sandbox Data Obtainability |
|---:|:---|:---|---:|:---|:---|
| **1 (Primary)** | **`H86-1`** | **Dual Magnetic-Gravity iSPI Local-Wavenumber Dip-Projected Basement Fault-Valve & Hydrothermal Magnetite-Destruction / Clay-Cap / 2-m Probe / Sinter Coupling (`H86-FVMB`)** | **`+0.055` to `+0.085`** over `D2.8` (`0.2600`) | Medium (`60` streamed `float16` channels, ~97 s) | **100% Verified Local** (`training_features.tif` + INGENIOUS external layers) |
| **2 (Integrated)** | **`H86-2`** | **Asymmetric ($\pm 22^\circ$) Mode-II/III Wing-Crack, Step-Over Relay-Bridge & Antithetic Graben Counterfactual 3-Family SAR-PU Stack + 8-Stratum LiDAR-Seam Calibration** | **`+0.035` to `+0.060`** additional | Medium (`12` `rfft2` channels, 16 s/mask + 3-family LOQO) | **100% Verified Local** (fold-strict `visible` fault components) |
| **3 (Integrated)** | **`H86-3`** | **Exact Linear-Fractional Dinkelbach–Minoux $300\text{ m}$ Submodular Expected-DTI Solver with Centerline Ridge Sharpening** | **`+0.015` to `+0.032`** over `D2.8` on identical posteriors | Low-Medium (exact 25-cell lazy-greedy heap, ~12 s) | **100% Verified Local** (exact `metric.py` $300\text{ m}$ cone) |
| **4 (Integrated)** | **`H86-4`** | **Pleistocene Pluvial Shoreline (Lahontan / Bonneville), Flat Basalt Mesa & TIGER Road-Cut False-Positive Decontamination** | **`+0.006` to `+0.014`** via $\text{FP}_w$ suppression | Low (embedded in channels 54–59) | **100% Verified Local** (`dem3m`, `dem10m`, `tiger_roads`, `B9`, `B11`) |
| **5 (Phase-2 External)** | **`H86-5`** | **USGS ComCat Relocated Microseismic Hypocenter Up-Dip Projection + ARIA Sentinel-1 InSAR Phase-Gradient Discontinuity** | `+0.018` to `+0.035` (projected in external unrestricted env) | High | **BLOCKED IN SANDBOX** (`earthquake.usgs.gov` / `asf.alaska.edu` blocked by sandbox egress whitelist; documented below — **NOT** proposed as viable inside sandbox) |

---

## Detailed Candidate Specifications

### Candidate 1 (`H86-1` — Ranked #1, Implemented): Dual Magnetic-Gravity iSPI Local-Wavenumber Dip-Projected Basement Fault-Valve & Hydrothermal Alteration Coupling

1. **Specific Layers Used**:
   - Official `training_features.tif` (`3730 × 3292`, `100 m`, `EPSG:32611`): Band 3 (`Magnetic Anomaly`), Band 9 (`Magnetic Horizontal Gradient`), Band 11 (`CBA Gravity`), Band 17 (`Deep Electrical Conductivity` / MT), Band 18 (`Gravity Horizontal Gradient`), Band 12 (`Depth to Basement`), Band 14 (`Quaternary Fault Slip Dilation Tendency` $T_s + T_d$), Band 13 (`Heatflow`), Band 19 (`Earthquakes`).
   - Verified public DOE/USGS/NBMG layers in `.cache/gems_data/external/`: USGS GeoDAWN radiometrics (`rad_k.tif`, `rad_th.tif`, `rad_u.tif`), USGS `dem3m_slope_std_100m.tif`, `dem10m_hillshade_std_100m.tif`, `dem1m_scarp_prob_max_100m.tif` + `dem1m_high_prior_openness_lrm.npz`, NBMG `2m_temperature_probe_n83geo.dbf` (`3,800` shallow temperature probes with `T2m` and `F2mDAB`), USGS/NBMG `Paleo_geothermal_final.csv` (`402` in-footprint sinter/travertine/tufa vents), GDR Submission `1391` liquid/gas geothermometers (`geotherm_points_utm11.npz`), and USGS ScienceBase `sb_heat_flow_in_footprint.json` (`2,193` borehole heat-flow stations).
2. **Physical Signature Targeted**:
   - **Improved Source Parameter Imaging (`iSPI`, Thurston & Smith 1997; Smith et al. 1998)**: For an inclined basement fault contact of depth $z_c$, local wavenumber $\kappa(x,y) = \|\nabla \operatorname{atan2}(\|\nabla_H F\|, |\partial_z F|)\|$ peaks directly over the subsurface contact edge with $\kappa_{\max} = 1/z_c$ independent of magnetization inclination or regional baseline. Because Basin-and-Range normal faults dip at $\delta \approx 55^\circ\text{–}65^\circ$ beneath low-density valley fill ($\nabla H_{\text{grav}}$ points from basin low toward footwall range block), the surface rupture trace lies **up-dip** toward the footwall by $\Delta x_{\text{pullback}} = z_{\text{basement}} \cot(60^\circ)$ (`100–900 m` = `1–9 px`!).
   - **Sibson (1990, 1996) Hydrothermal Fault-Valve Signature**: Blind geothermal upflow faults cycle between self-sealing silica/carbonate precipitation and supralithostatic breach. Oxidizing upflow alters ferrimagnetic titanomagnetite ($\text{Fe}_3\text{O}_4$) into paramagnetic hematite/pyrite/illite-smectite, creating a **narrow high-pass magnetic susceptibility trough** aligned with elevated **potassic metasomatism ($\text{K/Th}$)**, conductive **smectite clay-cap (`B17`)**, shallow **2-m temperature probe anomalies**, and **paleo-sinter / travertine / geothermometer discharge**.
3. **Why It Catches Faults *Missing* from the USGS/INGENIOUS Catalogue**:
   - The USGS Qfaults / INGENIOUS `existing_faults.tif` (`69,205 px`) was compiled primarily from **subaerial photogeologic scarp mapping** on range-front bedrock-alluvial contacts. Whenever Holocene playal clay, eolian sand sheets, Lahontan/Bonneville lacustrine silt, or hydrothermal sinter aprons bury the scarp (`1–3 km` basinward of the range front), photogeology misses the fault completely (`hidden` fault!). Yet basement density juxtaposition, dip-projected iSPI wavenumber ridges, magnetite destruction, and convective thermal plumes penetrate the Quaternary cover undiminished.
4. **How It Differs from Prior GEMSDOE Implementations**:
   - Prior geophysical lanes (`GEMSDOE24`, `GEMSDOE32`, `GEMSDOE80`) evaluated raw `B3`/`B9`/`B11`/`B18` values at the *vertical* pixel $(r,c)$, placing weight `300–900 m` hanging-wall-ward of the true surface trace (outside the `300 m` DW-Tversky cone!). `H86-1` is the **first GEMSDOE lane** to implement **dual magnetic + gravity iSPI local-wavenumber ridges explicitly projected up-dip by $z_{\text{basement}}\cot(60^\circ)$ along the gravity hanging-wall-to-footwall vector**, fused multiplicatively with the **Sibson magnetite-destruction $\times$ K/Th $\times$ MT clay-cap $\times$ 2-m probe $\times$ paleo-sinter fault-valve index**.

---

### Candidate 2 (`H86-2` — Ranked #2, Integrated with `H86-1`): Asymmetric ($\pm 22^\circ$) Wing-Crack, Relay-Bridge & Antithetic Graben Counterfactual 3-Family SAR-PU Stack

1. **Specific Layers Used**:
   - Fold-strict `visible` fault polyline mask (`existing_faults.tif` in production; `hc.visible(cell.key)` in holdout evaluation; counterfactual 50% sub-withheld `sub_vis` during training) + `H86-1` physical conduits (`fv_sibson_breach_index`, `spi_dip_coupled_conduit`, `scarp_lid1m_aniso_ridge`).
2. **Physical Signature Targeted**:
   - Under WNW–ESE Great Basin transtension (Faulds & Hinz 2015), Mode-II/III shear tips do not propagate strictly straight ($\psi = 0^\circ$): maximum tensile tangential stress $\sigma_{\theta\theta}$ opens **horsetail / wing-crack splays at $\psi_{\text{out}} \pm 22^\circ$** (`350 m` to `2.4 km` ahead of fault terminations), **overlapping en-échelon step-over relay ramps** (`fwd × bwd` geometric mean across `350 m–2.8 km`), and **antithetic graben-bounding twin faults** (`500 m–1.8 km` across-strike).
3. **Why It Catches Unmapped Faults Rather Than Mapped Ones**:
   - Regional mappers routinely trace the master range-front fault (`visible`) while missing the subtle low-throw horsetail splays, step-over breaching relays, and antithetic intrabasin faults where **>75% of Great Basin commercial geothermal fields reside** (Faulds et al., 2011, 2015). Training a **counterfactual component-withheld 3-family SAR-PU stack** (`LightGBM + HistGradientBoosting + MLP`) exclusively on `d(x, sub_vis) > 3.0 px` teaches the learner to recover whole unmapped splays rather than hugging mapped traces.
   - In addition, **8-stratum `(Quadrant × 1-m LiDAR-Valid)` Bayes prior calibration** prevents the 24.4% non-LiDAR eastern/northern swath from starving hidden faults of probability mass.
4. **How It Differs from Prior GEMSDOE Implementations**:
   - `GEMSDOE32` (`H33-2-B2`, `0.2778`) used isotropic distance collars (`d > 2 px` on `H19-5`), and `GEMSDOE80`/`GEMSDOE83` used symmetric `0°` collinear kernels with tree-only learners. `H86-2` introduces **16-azimuth outward tip vectors with asymmetric $\pm 22^\circ$ wing-crack FFT lobes, antithetic graben twin kernels, neural+tree 3-family diversity, $3.5\text{ km}$ cross-quadrant spatial erosion, and 8-stratum LiDAR-seam prior calibration**.

---

### Candidate 3 (`H86-3` — Ranked #3, Integrated Allocator): Exact Linear-Fractional Dinkelbach–Minoux $300\text{ m}$ Submodular Expected-DTI Solver

1. **Specific Layers Used**: Calibrated pixelwise off-catalogue fault posterior $q_E(x)$ from `H86-1 + H86-2` and exact $300\text{ m}$ triangular metric kernel $k(d) = \max(1 - d/300\text{ m}, 0)$ (`25` integer grid offsets).
2. **Physical / Mathematical Signature Targeted**:
   - DW-Tversky is a **non-additive linear-fractional coverage objective** (`beta = 0.8` FN weight, `alpha = 0.2` FP weight). Soft grayscale clouds (`0.15–0.40`) pay exact linear $\text{FP}_w$ mass everywhere while failing to saturate $\text{TP}_w = \max_{y \in P} p(y) k(d(x,y))$ at fault cores, whereas fixed-radius `D2.8` (`GEMSDOE32`) wastes budget on diffuse plateaus and terminates at an arbitrary user-guessed dot count (`37,654`).
   - By sharpening broad posteriors onto **1-pixel fault centerlines** (`3×3` directional NMS ratio) and solving the **Dinkelbach (1967) + Minoux (1978) lazy-greedy submodular coverage problem**, each binary dot (`1.0`) is placed only when its marginal coverage over the 25-cell $300\text{ m}$ disk satisfies $(1 - 0.2\lambda^*)\Delta\mathbb{E}[\text{TP}_w(x \mid S)] - 0.2\lambda^*(1 - q_E(x)) > 0$.
3. **Why It Catches Unmapped Faults**: Concentrates discrete `1.0` fault traces along thin blind conduits and terminates endogenously at the exact marginal break-even threshold $\lambda^*$.
4. **How It Differs from Prior GEMSDOE Implementations**: Replaces heuristic `D2.8` spacing (`GEMSDOE25`/`GEMSDOE32`) with exact 25-offset submodular coverage tracking + centerline ridge sharpening + endogenous fractional-programming convergence.

---

### Candidate 4 (`H86-4` — Ranked #4, Integrated Decontamination): Pluvial Paleoshoreline, Basalt Rim & Anthropogenic Road-Cut Decontamination

1. **Specific Layers Used**: `Training Band 1` (`Elevation`), `dem3m_slope_std_100m.tif`, `dem10m_hillshade_std_100m.tif`, `tiger_roads_dist_m_100m.tif`, `B9`, `B11`.
2. **Named Non-Fault Mimic Signature Targeted**:
   - **Pleistocene Lake Lahontan (`~1,332 m` Sehoo highstand) and Lake Bonneville (`~1,463 m` Provo / `~1,552 m` Bonneville highstands) wave-cut shoreline benches**, flat Tertiary basalt flow rims, and **US Census TIGER highway/railroad cut-and-fill embankments**.
   - Wave-cut shorelines are strictly **contour-parallel** ($\sigma_9(z_{\text{ASL}})$ is near zero despite steep slope $\|\nabla z\|$) and lack basement `iSPI` wavenumber ridges; tectonic normal fault scarps climb across alluvial fan apexes ($\sigma_9(z_{\text{ASL}})$ is high and coupled to subsurface `iSPI`).
3. **How It Differs from Prior GEMSDOE Implementations**: Explicitly encodes along-scarp elevation climb variance $\sigma_9(z_{\text{ASL}})/(\|\nabla z_{\text{ASL}}\| + 3\text{ m})$ and road-proximity $\times$ scarp decontamination directly inside the feature stack and wing-crack coupling.

---

### Candidate 5 (`H86-5` — Ranked #5, Documented Phase-2 External Only): Relocated ComCat Microseismicity + ARIA Sentinel-1 InSAR Phase Gradient

1. **Official Free Sources Verified**:
   - **USGS ANSS Comprehensive Earthquake Catalog (`ComCat`) API**: [`https://earthquake.usgs.gov/fdsnws/event/1/query`](https://earthquake.usgs.gov/fdsnws/event/1/query) (free public US Government API; provides `1980–2026` $M \ge 1.0$ hypocenters with focal depths $z_{\text{eq}}$ for $\cot(60^\circ)$ up-dip surface projection).
   - **NASA JPL / Caltech ARIA Sentinel-1 Gunw / NISAR Geocoded Unwrapped Interferograms via ASF DAAC**: [`https://search.asf.alaska.edu/`](https://search.asf.alaska.edu/) (free public NASA Earthdata archive; resolves creeping blind intrabasin faults via LOS phase-gradient discontinuities).
2. **Sandbox Obtainability Audit (Why Excluded from Sandbox Execution)**:
   - Tested live via Python `urllib.request.urlopen` on `2026-10-22`: sandbox egress is strictly whitelisted to `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, and `files.pythonhosted.org`, returning `URLError(SSLZeroReturnError)` on `earthquake.usgs.gov` and `asf.alaska.edu`.
   - Per task rules (*"verify whether it is actually obtainable in this environment before proposing it as a viable candidate"*), `H86-5` is **explicitly excluded from our viable sandbox execution lane** and documented strictly as the highest-leverage Phase-2 upgrade for an unrestricted workstation.
