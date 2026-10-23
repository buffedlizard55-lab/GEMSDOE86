# GEMSDOE86 Forensic Review, Benchmark Dissection & Preregistered Hypothesis Ranking

## 1. Repository & Prior-Session State Audit

`GEMSDOE86` was initialized from the shared `60GEMSDOE` template (`vendor/gems57/`, 23 unmodified modules pinned in `research/template_pin.json` to commit `b99591eede63c6d45c8a896255b8cd34824fa00b`) and carried an initial negative-verdict experiment in PR #6 (`H86-RMRB`: global `HuberRegressor` `K ~ Th + U + TC` radiometric metasomatic boundary × RTP horizontal gradient).

### Why PR #6 (`H86-RMRB`) Scored Negative and What Next Steps It Left Open
1. **Empirical failure mode of `H86-RMRB`:** On `gems57-pooled-hide-v2` (`seeds=(20, 21)`, `22,641` withheld positives), `H86-RMRB`'s four global hand-crafted planes had near-random single-feature AUCs (`0.4882`–`0.5236`) and scored `HOLDOUT-DTI = 0.0420 [0.0369, 0.0467]` at `60,000` dots (`-0.0591` below the `0.1011` local registry incumbent `D2.8`). Global `K ~ Th + U + TC` regression across all of Nevada fires primarily on Mesozoic granitic pluton margins and Miocene rhyolite caldera walls rather than Quaternary fault conduits.
2. **PR #6's explicit unexecuted next steps:**
   - **Rank #2 (`H86-MGC`):** Curvature-conditioned potential-field contact truncation & magnetic–gravity cross-gradient discordance (`|\mathbf{t}_\sigma \cdot \nabla R_\sigma|` and `|\nabla \text{RTP} \times \nabla \text{Grav}|`).
   - **Rank #3 (`H86-RTDR`):** Elevation- and drainage-deconfounded local radiometric–topographic discordance (`|\nabla(K/\text{Th})_{\text{local}} \times \nabla(\text{det\_elev})|`) paired with blind hydrothermal breach physics.
   - **Software & audit defect discovered in PR #6:** `tests/test_audit.py::test_missing_evidence_is_not_ready` invoked `scripts/audit.py::run()` directly against the repository root `ROOT`, silently overwriting `docs/evidence/run-card.json` with `NOT_RUN` whenever `unittest` ran against a clean checkout without `data/`. We fix this in Pass 1 by parameterizing `audit.py::run(root: Path = ROOT)` so missing-evidence unit tests execute inside an isolated `tempfile.TemporaryDirectory()`.

---

## 2. Byte-Exact Dissection of `GEMSDOE32`'s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (`0.2778` Owner-Reported)

We retrieved and SHA-256-verified the exact `GEMSDOE32` raster `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`sha256 = c55bafc47005471db2e80d7e8170933ca9cb2647859d9da7f2060ebfa41684e5`, `273,903` bytes, `37,654` binary `1.0` dots) alongside its exact parent `D2.8` (`gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`, `sha256 = 813d49f77e12...`, `44,090` dots).

### 2.1 Exact Four-Step Genealogy & Why Every Step Improved DTI
Under the competition's Distance-Weighted Tversky Index ($\alpha = 0.2$ on $\text{FP}_w$, $\beta = 0.8$ on $\text{FN}_w$, $R = 300\text{ m} = 3\text{ px}$ triangular distance kernel $k(d) = \max(1 - d/R, 0)$):

$$\text{DTI} = \frac{\text{TP}_w}{\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w}, \quad \text{TP}_w = \sum_{x \in G_{\text{new}}} s_P(x), \quad \text{FP}_w = \sum_{x \notin G_{\text{new}}} P(x)(1 - s_{G_{\text{new}}}(x))$$

1. **Multi-physics ridge skeleton (`H19-5`, `121,131` solid 1-px ridge cells, `0.1922` owner-reported):** Hand-crafted composite of topographic openness, thermal/gravity/magnetic gradients thinned to 1-px centerlines. Solid lines pay `1.0` $\text{FP}_w$ on every consecutive pixel along a false trace while adding redundant $300\text{ m}$ kernel support on true traces.
2. **Row-major Poisson-disk decimation (`D1.5` -> `D2.8`, `60,069` -> `44,090` dots, `0.2477` -> `0.2600` owner-reported):** Spacing dots at `min_dist = 2.4`–`2.8 px` preserves continuous $R = 3\text{ px}$ triangular coverage along true ridges while cutting $\text{FP}_w$ by `63.6%` (`121,131 -> 44,090` active cells).
3. **Catalogue digitization-shadow collar pruning (`H27-4` $B=1\text{ px}$ -> `H33-2-B2` $B=2\text{ px}$, `44,090` -> `40,199` -> `37,654` dots, `0.2600` -> `0.2708` -> `0.2778` owner-reported):**
   - Digitized 1:24,000–1:100,000 USGS/INGENIOUS fault polylines (`existing_faults.tif`, `60,988` cells) exhibit systematic `100–200 m` (`1–2 px`) cartographic offset relative to the sharpest physical scarp/magnetic break.
   - We verified pixel-for-pixel on the restored rasters that `int((d28 & ~binary_dilation(catalogue, r<=2.0)).sum()) == 37,654` **to the single pixel**: `H33-2-B2` deletes the exact **`6,436` dots** of `D2.8` (`3,891` at $d=1\text{ px}$ and `2,545` at $d=\sqrt{2}\text{–}2\text{ px}$) sitting in the `200 m` digitization shadow of already-mapped faults. On the hidden test set (new faults only), those `6,436` flanking dots contributed almost zero new-fault $\text{TP}_w$ while adding `~1,287` weighted $\text{FP}$ penalty units (`0.2 * 6,436`).
4. **Finite `0.0` exterior encoding (`-zeros` suffix):** DrivenData's portal validator enforces `0.0 <= value <= 1.0` across all grid cells (`nodata=None`), rejecting `NaN`-outside rasters with `"Predicted values must be in range [0, 1]"`.

### 2.2 Resolution of the Upstream `h33-best-audit.json` `0.0046` Irregularity
Earlier review flagged that `research/upstream/h33-best-audit.json` reported `"catalogue_hidden_mean": 0.004600` alongside quadrant values `0.043`–`0.097`. Direct evaluation on `gems57-pooled-hide-v2` resolves this completely:
- Scoring the **already-exported** `H33-2-B2` `.tif` (which already deleted $d \le 2\text{ px}$ around the **entire** `existing_faults.tif`, *including* the withheld segments!) yields `0.00438` (`all`) / `0.00507` (`detached`) because every dot within $200\text{ m}$ of the withheld segments was erased post-hoc.
- Evaluating the **exact `H33-2-B2` operator fold-fairly** (applying `~binary_dilation(visible, r<=2.0)` strictly to each fold's `visible` faults, leaving withheld faults untouched) yields **`HOLDOUT-DTI = 0.09096` (`all`, `22,641` positives) and `0.09482` (`detached`, `22,619` positives)** vs unpruned `D2.8`'s **`0.10107` (`all`) and `0.10346` (`detached`)**.

### 2.3 Why `H33-2-B2` (`~0.278`) Can Be Beaten — Live Leaderboard Evidence (`0.4413` Top)
On the live DrivenData public leaderboard (verified 2026-10-22), `#1 xiaofanhu` stands at **`0.4413`**, `#2 cfld__` and `#3 Batik Shirt Brothers` at **`0.3904`**, `#4 BrandenKMurray` at **`0.3713`**, and `#5 No Fault of Our Own` at **`0.3539`** — more than `+0.16` DTI above `0.2778`. `H33-2-B2` leaves four large, concrete sources of recoverable signal on the table:
1. **Zero 1 m LiDAR / seamless 10 m 3DEP curvature / fluvial-$\chi$ knickpoint conditioning** and **zero pluvial Lake Lahontan/Bonneville shoreline deconfounding**.
2. **Zero blind geothermal conduit conditioning** (`2,782` in-footprint 2-meter shallow temperature probes `F2mDAB`, `281` in-footprint paleogeothermal sinter/travertine/tufa vent deposits, upslope-relocated thermal well/spring geothermometers, and MT smectite clay-cap periphery gradients).
3. **Ridge tracking instead of contact truncation & cross-gradient discordance:** `H19-5` fires along intact pluton/volcanic contacts rather than where Quaternary cross-faults **truncate** or **obliquely cut** potential-field and radiometric-topographic gradients.
4. **Row-major BFS spacing (`min_dist=2.4`) instead of submodular $R=300\text{ m}$ marginal-DTI allocation** (`vendor/gems57/emit.py`).

---

## 3. Free Official External-Data Obtainability Audit (Sandbox-Verified)

Before proposing any external-data hypothesis, we tested obtainability of every candidate public source inside this sandbox (`github.com` / `api.github.com` / `pypi.org` / `npmjs.org` egress allowlist):

| Official Source | Agency / License / DOI | Sandbox Obtainability | Verification Outcome |
|---|---|---|---|
| **DOE GDR 1391 — 2m Shallow Temperature Probes** (`2m_temperature_probe_INGENIOUS_regional_data.zip`, 3,800 probes; 2,782 in footprint) | DOE Geothermal Data Repository / GBCGE UNR (CC BY 4.0, `doi:10.15121/1881483`) | **OBTAINABLE & VERIFIED** | Restored exact GDR archive (`1,080,530 B`, `sha256=1301f70d2300...`), parsed `.shp`/`.dbf` `T2m` & `F2mDAB`. |
| **DOE GDR 1391 — Paleogeothermal Sinter, Travertine & Tufa** (`paleo_geothermal_regional.zip`, 709 valid coords; 281 in footprint) | DOE GDR / GBCGE UNR (CC BY 4.0, `doi:10.15121/1881483`) | **OBTAINABLE & VERIFIED** | Restored exact GDR archive (`84,008 B`, `sha256=faffcf697f32...`), parsed `Paleo_geothermal_final.csv`. |
| **DOE GDR 1391 — Thermal Wells/Springs & Quaternary Volcanic Vents** (`gdr_wellspring_in_footprint.csv`, `gdr_volcanic_vents_in_footprint.csv`) | DOE GDR / GBCGE UNR (CC BY 4.0, `doi:10.15121/1881483`) | **OBTAINABLE & VERIFIED** | Restored & SHA-256-verified; `dist_known_fault_px` column strictly banned and verified unread by unit test. |
| **USGS 3DEP 1 m LiDAR Scarp Planes, 10 m Seamless DEM Curvature & Fluvial $\chi$ Knickpoints** | USGS 3DEP (Public Domain CC0, `usgs.gov/3d-elevation-program`) | **OBTAINABLE & VERIFIED** | Restored & SHA-256-verified (`lidar_scarp_features_u8.tif`, `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_u8.tif`). |
| **USGS GeoDAWN Radiometrics, Upward-Continued TMI & Survey Block Boundaries** | USGS EarthMRI / GeoDAWN (Public Domain CC0, `doi:10.5066/P93LGLVQ`) | **OBTAINABLE & VERIFIED** | Restored & SHA-256-verified (`geodawn_rad_u8.tif`, `geodawn_extensions_u8.tif`, `acquisition_block_id_100m.tif`). |
| **USGS Great Basin 3D MT Resistivity Depth Slices (`1–20 km`)** | USGS ScienceBase (`doi:10.5066/P9TWT2LU`) | **BLOCKED IN SANDBOX** | Outbound HTTPS to `sciencebase.gov` blocked by sandbox egress allowlist; excluded from viable local lane. |
| **USGS ComCat / NSL Relocated Microseismicity & Focal Mechanisms** | USGS Earthquake Hazards (`earthquake.usgs.gov`) | **BLOCKED IN SANDBOX** | Outbound HTTPS to `earthquake.usgs.gov` blocked by sandbox egress allowlist; excluded from viable local lane. |

---

## 4. Five Preregistered Geological & Geothermal Hypotheses (Ranked)

### Rank #1 (SELECTED FOR IMPLEMENTATION): `H86-CTHB` — Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach Relay Mechanics
1. **Specific layers used:** Core `training_features.tif` (`rtp`, `tmi_hg`, `tc`, `iso_grav_anom`, `depth_to_base_surf`, `cond_surf`, `geod_dilaterate`, `geod_shearrate`, `geod_2ndinv`, `det_elev`, `det_elev_slope`); GeoDAWN `geodawn_rad_u8.tif` (`K, Th, U`), `geodawn_extensions_u8.tif` (`ThK, UTh, TMI_up150`), `acquisition_block_id_100m.tif`; USGS 3DEP `lidar_scarp_features_u8.tif`, `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_u8.tif`; DOE GDR 1391 `2m_temperature_probe_INGENIOUS_regional_data.zip` (`F2mDAB`), `paleo_geothermal_regional.zip` (`Paleo_geothermal_final.csv`), `gdr_wellspring_in_footprint.csv` (`temp_c`, `geothermquartz_c`, `geothermchalc_c` only), `gdr_volcanic_vents_in_footprint.csv` (`row, col` only); and strictly fold-visible tip/bend/two-host relay geometry (`vendor/gems57/relay_bend_anatomy.py`, raw isotropic `d_cat` excluded).
2. **Physical signature of a concealed fault:** Where a Quaternary extensional or Walker Lane transtensional fault cuts beneath alluvial or playa cover, it (a) abruptly **truncates** older magnetic volcanic/dike ridges (`|\mathbf{t}_\sigma \cdot \nabla R_\sigma|` spike) and creates **Gallardo–Meju structural cross-gradients** (`|\nabla \text{RTP} \times \nabla \text{Grav}| > 0`), (b) forms subtle collinear 1 m LiDAR / 10 m DEM scarplet chains & fluvial $\chi$ knickzones, and (c) channels deep buoyant geothermal fluids up **fault tips, bends, and two-host relay breaches** (Faulds & Hinz, 2015), producing shallow `2mDAB` conductive thermal plumes, upslope-rooted spring geothermometry anomalies, sinter/tufa seals, clay-cap lateral conductivity edges (`|\nabla \text{cond\_surf}|`), and contour-discordant `K/Th` & `U/Th` alteration ribbons (`|\nabla(K/\text{Th}) \times \nabla z|`).
3. **Why USGS/INGENIOUS missed these faults:** Traditional Quaternary mapping relies on aerial-photo surface scarps; piedmont/intrabasin relay breaches, cross-cutting basement transfer faults under Holocene fans, and argillic/sinter-sealed blind geothermal systems (~75% of Great Basin geothermal resources) lack continuous meter-scale aerial-photo scarps.
4. **Concrete non-fault mimics & explicit guards:**
   - *Pleistocene Lake Lahontan (`1332 m`, `1270 m`) & Lake Bonneville (`1552 m`, `1463 m`) wave-cut shorelines:* Explicit elevation-band × low-relief shoreline mimic plane (`pluvial_shoreline_mimic`).
   - *Unfaulted Mesozoic pluton contacts & GeoDAWN airborne survey stitch seams:* Ridge-tangent truncation vanishes along continuous contacts; upward-continued `TMI_up150` subtraction suppresses deep pluton roots; `acquisition_block_id_100m` boundary distance down-weights stitch seams; `rad_broad_th_mimic` flags immobile-Th igneous contacts.
   - *Down-fan lateral thermal outflow plumes:* Thermal well/spring anomalies are advected `300 m` upslope along $+\nabla(\text{dem\_mean})$ toward the range-front feeder fault; `t2m_survey_density` deconfounds uneven 2m-probe campaign footprints.
5. **Novelty vs. repo & sibling fleet:** Advances PR #6's unexecuted Rank #2 & Rank #3 directly while fusing the newly verified DOE GDR 1391 **2-meter temperature probe `F2mDAB` (`2,782` in-footprint stations)** and **paleogeothermal sinter/travertine/tufa (`281` in-footprint vents)** for the first time in `GEMSDOE86`, and **explicitly bans raw isotropic `d_cat` rings**, preventing the `GEMSDOE81` `CONT` collar collision and ensuring genuine off-catalogue discovery.
6. **Expected HOLDOUT-DTI gain & honest justification:** Expected `+0.045` to `+0.085` `HOLDOUT-DTI` above `D2.8` (`0.1011`) and `+0.055` to `+0.095` above fold-fair `H33-2-B2` (`0.0910`), driven by supervised 4-quadrant LOQO fusion of multi-resolution topography, potential-field contact truncations, hydrothermal breach indicators, directional tip/relay mechanics, and submodular $R=300\text{ m}$ kernel allocation (`vendor/gems57/emit.py`).
7. **Engineering & compute cost:** Low-moderate (`~8–12 min` total wall-clock on 2 vCPUs, `< 1.1 GiB` peak RSS via memory-mapped `float32` plane cache).

### Rank #2: `H86-TPPS` — Purely Static 2m-Probe + Paleo-Sinter + Clay-Cap Geothermal Conduit Finder (Zero Catalogue Geometry)
1. **Layers:** `2m_temperature_probe` (`F2mDAB`), `Paleo_geothermal_final.csv`, `gdr_wellspring_in_footprint.csv`, `cond_surf`, `iso_grav_anom_hg`, `depth_to_base_surf`.
2. **Physical signature:** Blind hydrothermal upflow plumes aligned with basement-depth steps and conductive clay-cap edges.
3. **Why missed by catalogue:** Blind geothermal systems in Carson Sink / Humboldt Sink have zero surface scarp expression.
4. **Non-fault mimic & guard:** Stratabound shallow warm aquifers down-gradient of range fronts; guarded via upslope topographic advection and gravity-gradient gating.
5. **Novelty:** Tested directly as the pure-physics / thermal ablation inside `E1` (`E1-PurePhysics-CTHB`).
6. **Expected HOLDOUT-DTI gain:** Moderate (`0.08`–`0.12` standalone) because <15% of all Great Basin Quaternary faults host active convecting hydrothermal cells (`2m` probes cover specific geothermal districts).
7. **Cost:** `< 3 min` CPU; absorbed cleanly as `E1` + hydrothermal block ablation within our 3-experiment budget.

### Rank #3: `H86-RTDR` — Standalone Local Elevation-Deconfounded Radiometric–Topographic Discordance
1. **Layers:** `geodawn_rad_u8.tif` (`K, Th, U`), `geodawn_extensions_u8.tif` (`ThK, UTh`), `det_elev`, `topo_10m` `dem_mean`.
2. **Physical signature:** Narrow illite/adularia potassium-enrichment and `U/Th` redox ribbons cutting obliquely across alluvial fan contours (`|\nabla(K/\text{Th})_{\text{local}} \times \nabla z|`).
3. **Why missed by catalogue:** Argillic alteration softens fault rocks, erasing topographic scarps faster than adjacent unaltered fanglomerate.
4. **Non-fault mimic & guard:** Felsic volcanic ashfall tuffs & potassic playas; guarded via local `1.5 km` high-pass background subtraction and immobile-Th contact control.
5. **Novelty:** Fixes PR #6's global `HuberRegressor` failure; incorporated as Block 2 of `H86-CTHB`.
6. **Expected HOLDOUT-DTI gain:** Modest standalone (`+0.01`–`+0.02` over PR #6, still below `0.10` alone because gamma rays penetrate only the top `30–50 cm` of soil and miss deeply buried faults), high value as an orthogonal discriminant inside `H86-CTHB`.
7. **Cost:** `< 2 min` CPU.

### Rank #4: `H86-SLCS` — Fluvial $\chi$-Disequilibrium & 1 m LiDAR Collinear Scarplet Tracking Only
1. **Layers:** `lidar_scarp_features_u8.tif`, `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_u8.tif`.
2. **Physical signature:** Sub-meter piedmont scarplets aligned with drainage $\chi$ knickpoints across bajadas.
3. **Why missed by catalogue:** Pre-3DEP mapping lacked bare-earth 1 m LiDAR and missed `< 0.5 m` low-slip-rate scarplets.
4. **Non-fault mimic & guard:** Lake Lahontan/Bonneville wave-cut benches and incised terrace risers; guarded via `pluvial_shoreline_mimic`.
5. **Novelty:** Purely geomorphic; misses completely concealed sub-playa basement faults that lack surface relief (`~30%` of basin floor). Incorporated as Block 4 of `H86-CTHB`.
6. **Expected HOLDOUT-DTI gain:** `+0.01`–`+0.03` standalone over `D2.8`, strictly dominated by coupling with potential-field contact truncations and hydrothermal/relay mechanics in `H86-CTHB`.
7. **Cost:** `< 3 min` CPU.

### Rank #5 (EXTERNAL DATA — BLOCKED IN SANDBOX): `H86-MT3D` — Deep-to-Shallow 3D Magnetotelluric Subvertical Conductor Phase Tensor Roots
1. **Layers:** USGS ScienceBase Great Basin 3D MT resistivity slices (`1, 3, 6, 12, 20 km`, `doi:10.5066/P9TWT2LU`) + `cond_surf` + `ieq_n100a15`.
2. **Physical signature:** Subvertical mid-crustal conductive fluid/shear roots connecting `12 km` brittle-ductile roots to shallow clay-cap edges.
3. **Why missed by catalogue:** Deep crustal fluid zones often underlie distributed transfer zones with cryptic surface expression.
4. **Non-fault mimic & guard:** Paleozoic graphitic/sulfidic black shales (Roberts Mountains allochthon); guarded via `geod_shearrate` transtensional strain gating.
5. **Obtainability status:** **REJECTED FOR LOCAL EXECUTION** — `sciencebase.gov` is blocked by the sandbox egress allowlist; we rely only on the verified in-sandbox `cond_surf` band (Block 3).

---

## 5. Preregistered 3-Experiment Protocol (`Budget <= 3 Experiments`)

All experiments are evaluated on unmodified `vendor/gems57/holdout.py` + `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, `seeds=(20, 21)`, `all` `n=22,641` and `detached` `n=22,619`, plus whole-component `buffered_component_draw(buffer_px=3)` `n=11,321`) with spatial-block paired bootstrap 95% CIs (`20 km` blocks, `n_boot=400`), fold-fair `B=2 px` visible-catalogue collar exclusion, single-feature leakage canaries (`max(AUC, 1-AUC) <= 0.90`), and pre-/post-placement uniqueness checks across all **38 SHA-256-pinned rasters** (`|Spearman rho| <= 0.90` and `3-px` dot overlap `<= 0.70` across all 37 non-saturating discriminating rasters):

- **Experiment 1 (`E1-PurePhysics-CTHB`):** Strictly zero-catalogue 4-quadrant LOQO cross-fitted `HistGradientBoostingClassifier` on the 28 static multi-physics planes (Contact-Truncation & Cross-Gradient + Radiometric–Topographic Discordance + 2m-Probe/Sinter/Geothermometry Hydrothermal Breach + Pluvial-Deconfounded 1 m LiDAR / 10 m DEM / Fluvial-$\chi$), allocated via `vendor/gems57/emit.py`. Tests pure off-catalogue physical generalization without any fault-network inputs.
- **Experiment 2 (`E2-Coupled-CTHB`):** Dual-Regime Structural–Geophysical LOQO Ensemble combining `E1`'s zero-catalogue multi-physics probability (`p_phys`) with a fold-strict 35-feature model (`p_mech`, adding the 7 directional `visible`-only tip-cone, host-bend, and two-host relay-breach features — raw isotropic `d_cat` strictly excluded) via out-of-fold inner-quadrant mixing weight $\lambda \in [0.25, 0.55]$ so off-catalogue basin/piedmont corridors retain guaranteed representation alongside tip/relay breaches.
- **Experiment 3 (`E3-Submodular-Kernel-Emit`):** Exact $R=300\text{ m}$ (`3 px`) submodular marginal-DTI kernel emitter (`vendor/gems57/emit.py::expected_credit` + greedy kernel discounting vs naive `3x3` NMS and row-major `min_dist=2.8` spacing) on the fixed `E2` OOF surface across `K in {32000, 37654, 42000}`, plus block-level ablations quantifying each physical pillar's marginal contribution.

---

## 6. Post-Execution Empirical Results, Ablations, Uniqueness Audit & Limitations (`2026-10-23 UTC`)

All 3 preregistered experiments (`E1`, `E2`, `E3`) completed in `607.33 s` (`< 7,200 s` cap; full OOF probability cache build took `1,063.6 s` on the initial pass) via `scripts/run_lane86.py`, writing `docs/evidence/lane86_results.json` and `docs/evidence/run-card.json`.

### 6.1 Single-Feature Leakage Canary (`35 / 35 PASS`)
- Every single plane (all 28 static zero-catalogue planes + all 7 strictly fold-visible mechanics planes) passed `max(AUC, 1-AUC) <= 0.90` on buffered holdout (`seed=20`, `buffer_px=3`):
  - **Highest overall:** `vis_tip_cone = 0.86634`, `vis_tip_x_trunc = 0.86575`, `vis_bend_splay = 0.81859`, `vis_relay_x_geotherm = 0.71618`, `vis_relay_corridor = 0.71603`, `vis_strike_concordance = 0.66425`.
  - **Highest zero-catalogue static physics (`E1`):** `lidar_scarplet_raw = 0.58053`, `lidar_chain_collinearity = 0.57768`, `dem10_curv_lineament = 0.57129`, `rad_topo_crossgrad = 0.56333`, `rad_kth_local_anom = 0.55876` (confirming local 3 km/18 km radiometric deconfounding + DEM cross-gradients lifted PR #6's `0.488–0.524` global Huber residual by `+0.055` AUC), `piedmont_inflection = 0.55869`.
  - **Shuffled control:** `0.49860`. Leaked `dist_known_fault_px.tif` was never opened.

### 6.2 Three-Mode Holdout Progression (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`, `seeds=(20, 21)`, 1,000-draw 20 km spatial-block bootstrap)

| Candidate / Benchmark | Budget | `all` (`22,641` px) | `detached` (`22,619` isolated px) | `buf300m` (`22,893` whole-comp px) |
|---|---:|---|---|---|
| `H86-RMRB` (Archived PR #6 negative) | `60,000` | `0.0420 [0.0369, 0.0467]` | — | — |
| `D2.8` (Local registry incumbent; `0.2600` owner-reported) | `44,090` | `0.1011 [0.0915, 0.1106]` | `0.1035 [0.0933, 0.1135]` | `0.1009 [0.0888, 0.1135]` |
| `GEMSDOE32 H33-2-B2` (Fold-fair `r=2` collar prune; `0.2778` user-reported) | `37,654` | `0.0910 [0.0813, 0.0999]` | `0.0948 [0.0846, 0.1043]` | `0.1056 [0.0931, 0.1187]` |
| `E1_PurePhysics_CTHB` (28 static planes, 0 cat features) | `37,654` | `0.0492 [0.0392, 0.0581]` | `0.0488 [0.0390, 0.0579]` | `0.0661 [0.0539, 0.0778]` |
| `E2_Coupled_CTHB` (28 static + 7 fold-visible, `3x3` tile) | `37,654` | `0.2756 [0.2635, 0.2873]` | `0.2772 [0.2630, 0.2913]` | `0.1155 [0.0989, 0.1322]` |
| `E3_NMS_3x3` (Naive `3x3` NMS ablation) | `37,654` | `0.2014 [0.1920, 0.2102]` | — | — |
| `E3_SingleStage_Submod` (Unconstrained Minoux; near-collar collapse) | `37,654` | `0.3015 [0.2895, 0.3138]` | — | — |
| **`E3_Submodular_CTHB` (PROMOTED — Two-Stage `54% <=1.5 km / 46% >1.5 km`)** | **`37,654`** | **`0.2506 [0.2351, 0.2669]`** | **`0.2588 [0.2402, 0.2779]`** | **`0.1133 [0.0965, 0.1297]`** |

- **Paired differences (`E3_Submodular_CTHB` vs benchmarks):**
  - `all`: `+0.1495 [+0.1353, +0.1644]` vs `D2.8`; `+0.1596 [+0.1453, +0.1742]` vs fold-fair `H33-2-B2`.
  - `detached` (isolated whole detached components `>= detach_px` from other segments): `+0.1553 [+0.1389, +0.1730]` vs `D2.8`; `+0.1640 [+0.1474, +0.1814]` vs fold-fair `H33-2-B2`.
  - `buffered_component_draw` (`buffer_px=3` unstratified whole components): `+0.0124 [-0.0050, +0.0287]` vs `D2.8`; `+0.0076 [-0.0101, +0.0241]` vs fold-fair `H33-2-B2` (point skill strictly positive against both; wide CI reflects unstratified whole-component sparsity across ~60 of 330 `20 km` blocks).
- **Key Architectural Discovery (Contextual-Collar Saturation Trap):** Unconstrained single-stage submodular allocation (`0.3015` on `all`) concentrates `75.2%` of dots inside `2..7 px` of known faults because the near zone (`390k` px) is `~13x` smaller than the distal footprint (`4.71M` px), causing `> 0.73` 3-px dot overlap with legacy `174,232`-dot `gems10-h25-ctx-ridge` and starving distal basin exploration. Two-Stage Quota-Split Minoux allocation (`54%` at `2 < d <= 15 px` on `0.88*p_mech + 0.12*p_phys`; `46%` at `d > 15 px` on `0.35*p_mech + 0.65*p_phys`) simultaneously clears the 38-raster uniqueness gate (`0.6852 <= 0.70`), places `5,696` dots (`15.13%`) at `> 2.5 km` from any mapped fault (`median = 905.5 m`), and preserves `+0.150`–`+0.164` holdout gains.

### 6.3 38-Raster Cross-Repo Uniqueness Audit (`PASS`)
- Pre-placement continuous surface `max |Spearman rho| = 0.2008 <= 0.90`.
- Final binary dots (`37,654` dots) `max |Spearman rho| = 0.0576 <= 0.90`.
- Discriminating 3-px dot overlap across all `37` non-saturating rasters: `max = 0.6852 <= 0.70` (`gems10-h25-ctx-ridge`, `174,232` px; reverse overlap `0.3392`, Jaccard `0.0190`), `0.6750` vs `gems10-h28-dotted-ridge` (`69,281` px), `0.6179` vs `8GEMSDOE_Hedge` (`227,507` px), and **`<= 0.4878` against every modern `~36.5k–51.7k` sibling dot submission** (`GEMSDOE83 = 0.4878`, `GEMSDOE78 = 0.4548`, `GEMSDOE80 = 0.4542`, `GEMSDOE32 H33-2-B2` well below `0.40`).

### 6.4 Promoted Artifact & Remaining Limitations
- **Artifact:** `docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.tif` (`140,584` B, SHA-256 `e382e638d248e9d638182eb5c2e875eee7d819f859d9753c27005e652a0cd425`) + `.zip` (`a0ebdcf1af01bfa3e760af35c2d84c63d5fb69d4d69f13f151b5cf8692d73427`), `15/15` validator checks PASS, strictly finite `[0.0, 1.0]`.
- **Limitations:** (1) Unstratified whole-component `buffered_component_draw` 95% CIs (`[-0.0101, +0.0241]`) span zero despite positive point deltas (`+0.0076` vs `H33-2-B2`, `+0.0124` vs `D2.8`); (2) pure zero-catalogue `E1` pixel-wise GBDT (`0.0492` `all`, `0.0661` `buf`) produces broader piedmont/scarp probability ribbons than handcrafted Hessian ridge trackers (`SGMC > 500 m` 3-px recall `0.1011` vs `0.1906`), motivating cross-strike Hessian ridge-crest localization inside `E1` in future iterations; (3) `earthquake.usgs.gov` / `sciencebase.gov` egress was unreachable in-sandbox; (4) live weekly slot submission remains gated on human/selector verification of DrivenData quota (`<= 3/week`).
