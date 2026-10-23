# Scientific Review, Provenance Audit, Preregistered Hypotheses, and Experimental Results (`GEMSDOE86`)

**Current-review correction (2026-10-23):** The experiments below are archived, not rerun.
All current downloads are **DO NOT SUBMIT**; the current review is
[SESSION_20261023_REVIEW.md](SESSION_20261023_REVIEW.md). Historical canaries and mirror
hashes are not independent organizer authentication, cache input binding, or proof of
universal non-leakage. The upload-cause and catalogue-collar explanations below have been
corrected; no historical metric, card or TIFF was altered.

**Updated:** 2026-10-22 (Session 2 — advancing PR #6 roadmap end-to-end)
**Competition target:** Predict fault locations across the Great Basin / INGENIOUS study area (`EPSG:32611`, `3730 × 3292` pixels at `100 m`, `5,167,373` in-footprint cells, `60,988` mapped catalogue cells, `5,106,385` allowed off-catalogue cells) relevant to geothermal exploration. Predicting fault probability does **not** by itself establish geothermal heat, fluid saturation, open permeability, or an economic vent.

---

## 1. Provenance Audit & Score-Labelling Discipline (Protocol Rule 3)

Per Protocol Rule 3, every quantitative claim in this repository is strictly classified into one of four disjoint categories:

1. **`HOLDOUT-DTI`** — Evaluated locally by unmodified `vendor/gems57/evaluate_holdout.py` (`version = gems57-pooled-hide-v2`, `alpha = 0.2`, `beta = 0.8`, `300 m` / `3 px` triangular distance tolerance, `1,000` 20-km physical spatial-cluster bootstrap draws), always reported with withheld positive count and 95% CI.
2. **`OFF-CATALOGUE-PROXY-DIAGNOSTIC`** — Local diagnostic against USGS State Geologic Map Compilation (`SGMC`) bedrock fault traces strictly > 300 m (`> 3 px`) from the competition catalogue (`derived_sgmc_faults_100m_u8.tif`), with zero SGMC bytes ever used in feature building, training, or calibration. Not `HOLDOUT-DTI` and not a competition score.
3. **`OWNER/USER-REPORTED (unverified in-repo)`** — Historical leaderboard figures cited in the starting prompt or sibling repository prose (`0.1922`, `0.2600`, `0.2708`, `0.2778`, `0.3195`, `0.4413`) for which **no DrivenData submission-page receipt exists in this repository**. Never reproduced as `ORGANIZER-CONFIRMED` scores and never used as training/calibration targets.
4. **`ORGANIZER-CONFIRMED`** — Reserved exclusively for scores backed by an actual DrivenData submission-page receipt. **Count in `GEMSDOE86`: `0`.**

### Resolving Irregularities in the Starting Prompt
- **Missing assigned method paragraph:** The starting prompt instructed *"Stay inside a single method lane — the paragraph in this prompt"* while containing no separate method paragraph. Session 1 logged this irregularity and executed Rank-1 hypothesis `H86-RMRB` (`HOLDOUT-DTI = 0.0420 [0.0369, 0.0467]`, negative result, PR #6), queueing multi-depth magnetic contact-offsets and radiometric–topographic discordance next. Session 2 executes that exact queued next-step synthesis (`H86B-GFCO`) within a single declared 3-experiment budget.
- **Conflicting historical highs in the prompt (`0.2778` vs `0.4413` vs `0.3195`):** None of these three figures has an organizer receipt in this repository. Public inspection of the [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) in Session 1 confirmed external competitors above those figures, while the pinned upstream audit `research/upstream/h33-best-audit.json` explicitly labels `H33-2-B2` as `"UNSCORED"` at file-creation time (`leaderboard_hat = 0.2774` was a regression projection). All live figures from earlier runs are therefore treated strictly as unverified owner reports.
- **DrivenData portal error `"Predicted values must be in range [0, 1]"` (corrected 2026-10-23):** The rejected bytes were not supplied, so its cause is unknown. Out-of-range finite values, infinities and nodata sentinels are numerical risks; the public specification explicitly describes null/NaN outside bounds, so NaN outside is **not** an established cause. The unchanged shared writer rejects nonfinite/out-of-range inputs, exports finite zeros outside the footprint and revalidates serialized output. That local policy prevents those invalid numerical exports but is not organizer-confirmed acceptance.

---

## 2. Archived H33 construction and plausible metric efficiency — not a confirmed score explanation

### 2.1 Exact Physical & Metric Decomposition of `H33-2-B2`
Direct byte inspection of `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`sha256: c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`) and `research/upstream/h33.py` establishes its exact construction:
1. **Base multi-lineament corridor (`H19-5`, `121,131` pixels):** Combines topographic slope/curvature ridges, gravity/magnetic gradients, openness, and thermal spring proximity. Emitting dense 1-px-adjacent ridges wastes precision mass under the official Distance-Tolerant Tversky Index:
   $$\text{DTI} = \frac{\text{TP}}{\text{TP} + 0.2\,\text{FP} + 0.8\,\text{FN}}, \qquad k(d) = \max\!\left(0,\,1 - \frac{d}{300\text{ m}}\right).$$
2. **Archived 2.8 px dot thinning (`d2.8`, `44,090` binary `{0, 1}` dots):** The physical grid makes the corresponding minimum separation about 283 m. This reduces emitted positive mass relative to the archived `121,131`-cell base. It does not by itself prove a proportional reduction in the metric's false-positive term or preservation of truth coverage: both are geometry-dependent. Nearby predictions may be redundant under the maximum triangular-kernel credit, but do not universally pay a full false-positive penalty. The exact tradeoff must be measured on matched folds.
3. **Strict `d_cat > 2.0 px` (`> 200 m`) catalogue-flank collar (`H33-2-B2`, `37,654` binary `{0, 1}` dots):** The archived construction prunes `6,436` dots near the catalogue. This may remove redundant mapped-looking mass, but the official description does **not** establish that a two-pixel collar is masked from private truth or receives near-zero TP credit. Parallel and branching unmapped faults can occur in that collar. The tradeoff depends on lost truth coverage and removed false-positive mass; it cannot be inferred from distance alone.

### 2.2 Two Critical Quantitative Discoveries Established in Session 2

1. **Resolving the Holdout Calibration Paradox (`buffered_component_draw` vs unbuffered cut chunks):**
   When we scored the three historical reference rasters on unbuffered `12 px` branch-chunk holdouts (`holdout.build_holdout`, `mode="all"`, `22,641` positives), `d2.8` (`0.1011`) appeared to beat `H33-2-B2` (`0.0910`) — inverting their owner-reported live ordering (`0.2600 < 0.2778`)! Why? Because slicing continuous fault trees into unbuffered `12 px` chunks leaves cut endpoints at `d_vis = 1–2 px`, artificially rewarding `d2.8`'s `6,436` flank dots right at artificial cut boundaries. When instead evaluated on **`holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)`** (`11,321` withheld positives; **whole 8-connected fault components** withheld with a strict **3-px buffer**, matching Protocol Rule 2), the reference rasters score:
   - `H19-5` (`121,131` px): **`0.0654 [0.0555, 0.0749]`**
   - `d2.8` (`44,090` dots, `d > 0`): **`0.0919 [0.0790, 0.1035]`**
   - `H33-2-B2` fold-fair (`d_vis > 2 px`): **`0.0961 [0.0828, 0.1083]`**
   reproducing the **exact monotonic ordering** (`0.0654 < 0.0919 < 0.0961`) of the owner-reported live progression! Consequently, Session 2 evaluates every candidate across **all three** shared-evaluator views (`buffered_component_draw`, `mode="all"`, and `mode="detached"`).

2. **Submodular `allocate_patient` Saturation Collapse vs Expected-Credit Priority Disc Thinning:**
   Before spending any model experiment, synthetic benchmarking of `vendor/gems57/emit.py` revealed a critical mathematical degeneracy: in `allocate_patient`, `k_self = min(E[k](x), 1.0)` clamps to `1.0` whenever local 3-px integrated probability $E[k](x) \ge 1.0$, setting the marginal FP denominator cost `1 - k_self` to **zero** (`emit.py` line 325) and packing dots **`1.0 px` apart** (`DTI = 0.1636` on synthetic 19-ridge benchmark). Likewise, `emit_decimated(tile_px=3)` allows `1.0 px` adjacent pairs across $3\times 3$ tile seams (`DTI = 0.2361`). Ranking pixels by `emit.expected_credit(surface)` (exact `300 m` triangular kernel expectation) followed by seam-free priority disc suppression at $r_{\text{suppress}} = 2.8\text{ px}$ (`min_nn >= sqrt(8) = 2.828 px`) raised synthetic DTI to **`0.2822` (`+72.5%` over `allocate_patient`, `+19.5%` over `emit_decimated`)** before touching a single real data pixel.

### 2.3 Structural-Geological Weaknesses Remaining in `H33-2-B2`
Despite its strong spacing and collar geometry, `H33-2-B2` remains handicapped by three geological blind spots:
- **Range-front / topographic visibility bias:** Its `H19-5` backbone relies heavily on surface slope ridges, systematically missing **intrabasin blind faults** buried beneath 100–2,000 m of Quaternary playa/alluvial fill where surface slope is near zero.
- **Unused subsurface & hydrothermal fluid tracers:** It ignores chemical geothermometer disequilibrium (`dT_quartz - T_measured`) across the `27,092` INGENIOUS well/spring records, 3D magnetotelluric (`MT`) clay-cap / feeder-root resistivity gradients (`500 m` to `10 km`), multi-depth magnetic attenuation (`TMI` vs `150 m` upward-continued `TMI`), and geodetic strain tensor dilatation/shear.
- **No structural fracture-mechanics coupling:** Unmapped Quaternary/bedrock faults are not isotropic halos around mapped traces; they localize preferentially in **Mode-II/III crack-tip stress-shadow cones**, **en-echelon relay ramps** between sub-parallel stepping strands (Peacock & Sanderson, 1991), and **horsetail / restraining-releasing bend splays** (Curewitz & Karson, 1997).

---

## 3. Five Untried Geological Hypotheses — Preregistration & Obtainability Audit

All external data sources were machine-probed from this workspace on `2026-10-22T23:41:38Z` before treating any hypothesis as viable:
- `https://api.github.com` / `https://codeload.github.com`: **REACHABLE (`HTTP 200`)** — all 23 SHA-256-pinned GDR-1391 & competition files (`research/upstream/data_manifest.json`) and 15 sibling GEMSDOE champion rasters (`research/upstream/cross_repo_champions_manifest.json`) verified byte-for-byte.
- `https://earthquake.usgs.gov/fdsnws/event/1/version`, `https://tnmaccess.nationalmap.gov/api/v1/products?max=1`, `https://data.nbmg.unr.edu/`: **BLOCKED IN SANDBOX (`URLError: TLS/SSL EOF`)** — live external agency downloads are blocked by sandbox egress rules and are explicitly flagged **NOT VIABLE IN THIS SANDBOX** unless mirrored first.

| Rank & ID | Exact Input Layers & Physical Transform | Concealed / Off-Catalogue Discovery Mechanism | Named Non-Fault Mimics & Quantitative Discriminants | Novelty vs `GEMSDOE32..88` & Compute Cost | Obtainability Status |
|---|---|---|---|---|---|
| **Rank 1 (Executed Session 2): `H86B-GFCO`** — *Cover-Adaptive Geothermometer-Disequilibrium & Multi-Depth Contact-Offset × Visible Fracture-Tip/Relay Coupling* | `gdr_wellspring_in_footprint.csv` (`temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c` — `dist_known_fault_px` strictly excluded), `gdr_volcanic_vents_in_footprint.csv`, `training_features.tif` (MT `500 m–10 km`, `TMI`, `TMI_up150m`, `TMI_RTP`, `CBA_grav`, `CBA_HGM`, `basement_depth`, `geodetic_strain`, `det_elev`, `det_slope`), `lidar_scarp_features_u8.tif` (`12` bands), `geodawn_rad_u8.tif` + `geodawn_extensions_u8.tif`; 4-quadrant LOQO dual GBDT (`38`-plane full + `28`-plane cover-blind subsurface head gated by `basement_depth`) × strictly visible-only tip-cone / two-host relay / bend-splay envelope | Deep fault conduits allow rapid adiabatic fluid ascent ($T_{\text{chem}} - T_{\text{meas}} \gg 0$ and quartz–cation equilibration lag; Fournier & Potter 1982; Giggenbach 1988), offset shallow magnetic horizons (`TMI - TMI_up150m`) across basement steps (Grauch & Hudson 2007), and propagate across unmapped relay ramps & tip cones | **Mimics:** Playa evaporite brines, deep plutonic edges, steep range cliffs, alluvial fan K sorting. **Discriminants:** Shallow-vs-150m magnetic attenuation × gravity step; relief-normalized LiDAR scarplet collinearity; Huber topographic residualization of `K` & `U/Th`; PU `d > 4 px` negative sampling | Distinct from PR #6 `H86-RMRB` (label-free radiometric residual), `GEMSDOE73` (no geothermometer disequilibrium or cover-blind dual LOQO head), `GEMSDOE76` (no LiDAR scarplet chains or two-host relay frame), and `GEMSDOE81` (featureless `d_cat` halo). Cost: `~16.6 min` CPU total (`3` experiments) | **VIABLE & VERIFIED** (`22/22` non-qfaults manifest files SHA-256 verified locally) |
| **Rank 2: `H86C-TDPL`** — *Topographically-Deconfounded Multi-Azimuth 1 m LiDAR Piedmont Scarplet & Valley-Deflection Tensor* | `lidar_scarp_features_u8.tif` (`step_max`, `downfacing`, `upfacing`, `relief`, `coherence`) + `det_elev`/`det_slope`; multi-scale (`5, 9, 17 px`) Radon/steerable collinearity tensor with orthogonal stream-incision suppression | Low-slip Holocene intrabasin faults produce subtle (`0.3–1.5 m`) linear scarplets across alluvial fans that vanish in `100 m` DEM slope but align over `0.5–2 km` in `1 m` LiDAR step coherence | **Mimics:** Pleistocene pluvial Lake Lahontan/Bonneville shorelines (contour-parallel!) and incised fan channels. **Discriminants:** Reject zero-elevation-gradient contour-parallel benches (`|∇z · t_scarp| < ε`) and dendritic thalwegs | Untried contour-orthogonality shoreline rejection on `lidar_scarp_features_u8.tif`; ~8 min CPU | **VIABLE** (inputs verified locally; partial component tested inside `H86B-GFCO` Block 4) |
| **Rank 3: `H86D-PFCO`** — *Paired Potential-Field Ridge Dislocation & Transverse Euler-Depth Step Detector* | `TMI_RTP`, `TMI_up150m`, `CBA_grav` (`training_features.tif` bands `1–4, 21, 22`); extract 1D magnetic phase-symmetry ridges, match truncated conjugate ridge tips across `300 m–2.5 km` lateral offsets, score transverse bridge where gravity HGM peaks | Pre-Cenozoic volcanic/plutonic marker beds displaced laterally or vertically by a concealed Basin-and-Range cross-fault reveal the fault along the *truncation corridor* rather than along the magnetic body itself | **Mimics:** Primary caldera ring margins, survey flight-line seams. **Discriminants:** Require conjugate ridge-orientation match (`Δθ < 20°`) + structural index consistency across `TMI` and `TMI_up150m` | Explicit graph matching of truncated conjugate magnetic ridges (untried across `GEMSDOE32..88`); ~12 min CPU | **VIABLE** (inputs verified locally) |
| **Rank 4: `H86E-MTDA`** — *3D Magnetotelluric Depth-Migrating Dipping-Conductor Vector (`500 m → 10 km`)* | `training_features.tif` MT slices (`500 m, 1 km, 2 km, 4 km, 6 km, 10 km`); track lateral migration vector $\vec{v}_z = \arg\max_{\perp}\lvert\nabla\log\sigma(z)\rvert$ across consecutive depths and project dipping plane (`50°–65°` Andersonian normal dip) up to the `z = 0` surface trace | Listric/planar normal faults (`~60°` dip) imaged as conductive fluid/alteration zones at `2–6 km` project `1.2–3.5 km` updip laterally from the deep MT anomaly centroid to the concealed surface rupture | **Mimics:** Flat-lying conductive clay playas (`|v_z| ≈ 0`) and regional 3D inversion smoothness halos. **Discriminants:** Require monotonic lateral shift consistent with `45°–75°` dip (`0.6 <= Δx/Δz <= 2.0`) co-oriented with basement step strike | Explicit updip geometric surface projection of dipping MT gradients (untried); ~6 min CPU | **VIABLE** (6 MT depth slices verified in `training_features.tif`), resolution limited by coarse primary MT station spacing |
| **Rank 5: `H86F-RLSL`** — *Relocated Microseismicity Planar Clustering & Focal-Mechanism Nodal Alignment* | External official free catalogs: [USGS ComCat FDSN API](https://earthquake.usgs.gov/fdsnws/event/1/) + UNR Nevada Seismological Laboratory relocated catalog (`M >= 1.0`, `1980–2026`); 3D RANSAC planar hypocenter fits projected updip to `z = 0` | Seismogenic blind faults and accommodation-zone swarms illuminate active fault planes lacking surface scarps | **Mimics:** Open-pit mine blasts (Carlin/Round Mountain daytime `M 1–2.5` clusters) and geothermal injection swarms. **Discriminants:** Filter `event_type != quarry blast`, require depth `> 2 km` & diurnal uniformity | Tested in `GEMSDOE75` via pre-mirrored CSV, **never** with 3D RANSAC updip plane projection | **NOT VIABLE IN THIS SANDBOX** (`earthquake.usgs.gov` TLS-blocked here; verified 2026-10-22) |

*(Session-1 Rank-1 `H86-RMRB` — global Huber `K ~ Th + U + TC` residual boundary × RTP edge persistence — was already executed in PR #6 and yielded `HOLDOUT-DTI = 0.0420` pre-mask / `0.0038` full-catalogue-masked; see Section 5.)*

---

## 4. Session-2 Declared Lane (`H86B-GFCO`): Method, Leakage Canaries & 3-Experiment Results

### 4.1 Feature Architecture & Zero-Leakage Guarantee (`scripts/h86b_features.py`)
We constructed **38 strictly label-free physical, geothermal, and geomorphic float32 planes** (`data/cache/h86b_planes/*.npy`, `manifest.json` confirming `catalogue_used = false`, `sgmc_used = false`, AST-audited in `tests/test_audit.py` to guarantee `existing_faults.tif`, `labels.tif`, `gdr_qfaults_traces.csv`, `derived_sgmc_faults_100m_u8.tif`, and `dist_known_fault_px` are never accessed):
- **Block 1 — Hydrothermal Upflow & 3D MT Architecture (`8` planes):** Chemical geothermometer disequilibrium $\Delta T_{\text{diseq}} = \max(T_{\text{quartz}}, T_{\text{chalc}}, T_{\text{Na-K-Ca}}) - T_{\text{meas}}$ at `800 m` and `2.5 km` scales (`gt_diseq_s8`, `gt_diseq_s25`; e.g., Beowawe benchmark cell `[189, 2915]` exhibits $T_{\text{quartz}} = 209.4^\circ\text{C}$ vs $T_{\text{meas}} = 78.0^\circ\text{C}$), silica–cation equilibration lag $|T_{\text{quartz}} - T_{\text{Na-K-Ca}}|$ (`gt_kinlag_s15`), surface thermal excess (`gt_thermal_s12`), Quaternary volcanic vent density (`vent_density_s30`), shallow MT clay-cap gradient (`mt_shallow_grad`), deep MT feeder gradient (`mt_deep_grad`), and shallow-to-deep MT vertical contrast (`mt_conduit_couple`).
- **Block 2 — Multi-Depth Potential-Field Contact-Offsets (`12` planes):** `TMI_RTP` fine/regional horizontal gradients & symmetric Hessian ridges, `TMI` vs `150 m` upward-continued `TMI` shallow fault-source attenuation (`mag_up150_atten_s1`, `mag_up150_atten_s3`), magnetic structure-tensor director disruption (`1 - coherence`) gated by medium-scale gradient (`mag_contact_trunc`, `mag_strike_jump`), Complete Bouguer Anomaly (`CBA`) horizontal gradients & curvature ridges, and cross-field `∇TMI_RTP × ∇CBA` concordance (`grav_mag_concord`).
- **Block 3 — Basement Geometry & Geodetic Strain (`6` planes):** Depth-to-basement z-score (`base_depth_z`), basement-step gradient & Hessian ridge (`base_step_grad`, `base_step_ridge`), GPS 2nd invariant shear rate (`strain_2ndinv_z`), dilatation rate (`strain_dilat_z`), and transtensional coupling (`strain_transtension`).
- **Block 4 — 1 m LiDAR Piedmont Scarplets, 100 m DEM Hinges & Topographically-Deconfounded Radiometrics (`12` planes):** Relief-normalized 1 m LiDAR scarp height & face asymmetry (`lidar_step_z`, `lidar_ex_z`, `lidar_face_asym`, `lidar_piedmont_scarp`), 8-azimuth axial collinearity vote (`lidar_chain_vote`), 100 m DEM piedmont slope-break hinge & aligned valley chains (`dem_piedmont_hinge`, `dem_valley_chain`), and Huber-regressed topographic residuals of GeoDAWN `K` and `0.6 U/Th - 0.4 Th/K` (`rad_topo_discord_K`, `rad_topo_discord_UTh`).

**Protocol Rule 4 Single-Feature Leakage Canaries (`42 / 42 PASS`):**
Every single one of the `38` physical planes AND all `4` visible-only kinematic components (`tip_cone`, `relay_bridge`, `bend_splay`, `m_kin`, derived strictly from each fold's `visible` fault mask) was tested individually on `buffered_component_draw` (`11,321` withheld positives):
- Maximum discriminative AUC across all `38` physical planes: **`0.6486`** (`dem_valley_chain`), followed by `lidar_face_asym` (`0.5958`), `lidar_step_z` (`0.5815`), `lidar_ex_z` (`0.5714`), `dem_slope_z` (`0.5693`), `lidar_piedmont_scarp` (`0.5454`), `lidar_chain_vote` (`0.5452`), `dem_piedmont_hinge` (`0.5426`), `base_step_grad` (`0.5352`), `rad_topo_discord_K` (`0.5269`).
- Maximum discriminative AUC across all `4` visible-only kinematic components: **`0.8485 <= 0.90`** (`m_kin = 0.8081` mean / `0.8485` max fold; `tip_cone = 0.8039`; `bend_splay = 0.7883`; `relay_bridge = 0.6084`). **Zero leakage flags (`0 / 42`).**

### 4.2 Spatially Blocked LOQO Training & Pre-Declared 3-Experiment Progression
To prevent any spatial or holdout-draw leakage, `P_phys` was trained via **4-quadrant Leave-One-Quadrant-Out (`NW, NE, SW, SE`)** with `1.2 km` (`12 px`) boundary erosion and positive labels restricted to `strictly_visible = catalogue & ~union_of_all_holdout_hidden_masks`. Each fold combines a 38-feature GBDT (`m_all`) and a 28-feature cover-blind subsurface/geothermal GBDT (`m_sub`, all 10 DEM/LiDAR relief/slope columns removed) weighted by sedimentary cover thickness $w_{\text{cov}}(x) = \text{clip}(0.25 + 0.20\,z_{\text{basement}}(x), 0.15, 0.65)$.

All **3 experiments** (`Protocol Rule 6` cap = 3) were scored by unmodified `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, `1,000` 20-km cluster bootstrap draws):

| Arm / Benchmark | Description & Emitted Dots | Primary Holdout A: Whole-Component 3-px Buffered LOQO (`11,321` pos) | Primary Holdout B: Segment-Hide `all` (`22,641` pos) | Primary Holdout C: Segment-Hide `detached` (`22,619` pos) | Aux Diagnostic: Off-Catalogue `SGMC` (`d_cat > 3 px`, `51,389` px)* |
|---|---:|---:|---:|---:|---:|
| **`E1_phys_38k`** (Exp 1) | Cover-adaptive LOQO `P_phys` only (`0` catalogue features at inference), `37,654` dots (`d_vis > 2 px`) | `0.0472` `[0.0343, 0.0592]` | `0.0454` `[0.0362, 0.0542]` | `0.0514` `[0.0411, 0.0604]` | `0.0830` |
| **`E2_gfco_38k`** (Exp 2) | Coupled `P_phys^0.65 × (0.12 + 0.88 M_kin)` + `expected_credit` `r=2.8 px`, `37,654` dots (`d_vis > 2 px`) | **`0.0992`** `[0.0828, 0.1168]` | **`0.1343`** `[0.1223, 0.1465]` | **`0.1450`** `[0.1298, 0.1592]` | `0.0822` |
| **`E3_gfco_44k`** (Exp 3, **Selected**) | Coupled `P_phys^0.65 × (0.12 + 0.88 M_kin)` + `expected_credit` `r=2.8 px`, `44,090` dots (`d_vis > 2 px`) | **`0.1078`** `[0.0908, 0.1254]` | **`0.1396`** `[0.1286, 0.1513]` | **`0.1521`** `[0.1378, 0.1662]` | `0.0914` |
| `h33_b2_foldfair` (Control) | `GEMSDOE32` `H33-2-B2` mechanism (`d2.8` with fold-fair `d_vis > 2 px`, `~37.7k` dots) | `0.0961` `[0.0828, 0.1083]` | `0.0910` `[0.0807, 0.1001]` | `0.0948` `[0.0839, 0.1050]` | `0.0954` |
| `d28_incumbent` (Control) | Pinned `d2.8` incumbent (`44,090` dots) | `0.0919` `[0.0790, 0.1035]` | `0.1011` `[0.0907, 0.1103]` | `0.1035` `[0.0921, 0.1138]` | `0.0954` |
| `h19_5_ridge` (Control) | Unthinned `H19-5` multi-lineament corridor (`121,131` px) | `0.0654` `[0.0555, 0.0749]` | `0.0712` `[0.0629, 0.0783]` | `0.0727` `[0.0637, 0.0816]` | — |
| `h86_rmrb_pr6` (Session 1) | PR #6 `H86-RMRB` radiometric residual × RTP (`60,000` dots, full-cat masked) | `0.0037` `[0.0029, 0.0045]` | `0.0038` `[0.0031, 0.0044]` (`0.0420` pre-mask) | `0.0039` `[0.0032, 0.0046]` | `0.1069` |

*\*Labelled `OFF-CATALOGUE-PROXY-DIAGNOSTIC` (NOT `HOLDOUT-DTI`, NOT an organizer score).*

**Paired Spatial-Cluster Bootstrap Differences for Selected Arm `E3_gfco_44k`:**
- **Holdout B (`segment_all`, `22,641` positives):** $\Delta\text{DTI vs } d2.8 = \mathbf{+0.0385\;[+0.0269, +0.0524]}$ (`+38.1%`, 95% CI strictly `> 0`); $\Delta\text{DTI vs } \text{H33-2-B2} = \mathbf{+0.0486\;[+0.0376, +0.0616]}$ (`+53.5%`, 95% CI strictly `> 0`).
- **Holdout C (`segment_detached`, `22,619` positives):** $\Delta\text{DTI vs } d2.8 = \mathbf{+0.0486\;[+0.0343, +0.0627]}$ (`+47.0%`, 95% CI strictly `> 0`); $\Delta\text{DTI vs } \text{H33-2-B2} = \mathbf{+0.0573\;[+0.0439, +0.0706]}$ (`+60.4%`, 95% CI strictly `> 0`).
- **Holdout A (`buffered_whole_components`, `11,321` positives):** $\Delta\text{DTI vs } d2.8 = \mathbf{+0.0159\;[-0.0007, +0.0343]}$ (`+17.3%` point gain; lower 95% CI bound `-0.0007` narrowly straddles zero across 4 quadrants); $\Delta\text{DTI vs } \text{H33-2-B2} = \mathbf{+0.0117\;[-0.0052, +0.0303]}$ (`+12.1%` point gain). Per-quadrant `E3_gfco_44k` scores: `NW = 0.0725`, `NE = 0.1302`, `SW = 0.0793`, `SE = 0.0884`.

---

## 5. Cross-Repository Uniqueness Analysis (28 Hash-Verified Rasters Across 16 Repos) & Fail-Closed Verdict

We checked **both** the pre-placement continuous surface and the final `44,090` binary dots of `gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif` (`sha256: 897ebf7b790efb9b5668934f5929ae766d81d9ec2a4bee3faa7ef2ebaedc1116`) via unmodified `vendor/gems57/uniqueness.py` against **28 SHA-256-verified rasters across 16 `buffedlizard55-lab` repositories** (`12` pinned local rasters in `data/scored/`, Session-1 PR #6 `H86-RMRB`, plus `15` primary champion rasters from `GEMSDOE32`, `GEMSDOE36`, `GEMSDOE49`, `60GEMSDOE`, `GEMSDOE70` ×2, `GEMSDOE73`, `GEMSDOE75`, `GEMSDOE76`, `GEMSDOE78` ×2, `GEMSDOE80`, `GEMSDOE81`, `GEMSDOE82`, `GEMSDOE83`):

1. **Pre-placement continuous surface Spearman $|\rho|$:** Worst $|\rho| = \mathbf{0.1366 \le 0.90}$ across all 28 rasters (`PASS`).
2. **Final binary dot Spearman $|\rho|$ & Jaccard:** Worst $|\rho| = \mathbf{0.0530 \le 0.90}$ (`GEMSDOE82`), worst Jaccard $= \mathbf{0.0311 \le 0.50}$ (`PASS`).
3. **3-px forward dot overlap against ALL 25 comparable/modern candidates (`12,000–61,328` dots):** **100% `<= 0.70` (`0 / 25` duplicates!)**:
   - vs `GEMSDOE32` `H33-2-B2` (`37,654` dots): **`0.3012`** (`rho = 0.0131`, `jaccard = 0.0105`)
   - vs `d2.8` incumbent (`44,090` dots): **`0.3352`** (`rho = 0.0108`, `jaccard = 0.0097`)
   - vs `GEMSDOE70` dual-submod (`37,654` dots): **`0.2598`**
   - vs `GEMSDOE49` ortho-gate (`40,000` dots): **`0.2602`**
   - vs `GEMSDOE36` Anderson-PINN (`38,854` dots): **`0.3077`**
   - vs `GEMSDOE76` geotherm-tilt (`37,654` dots): **`0.3495`**
   - vs `GEMSDOE73` vent-bridge (`37,654` dots): **`0.4149`**
   - vs `GEMSDOE82` PU-noisyOR (`37,654` dots): **`0.5108`**
   - vs `GEMSDOE80` Choquet (`51,667` dots): **`0.5309`**
   - vs `GEMSDOE78-GFV` (`37,654` dots): **`0.5483`**
   - vs `GEMSDOE75` ComCat3D (`29,953` dots): **`0.5746`**
   - vs `GEMSDOE81` CONT (`44,090` dots): **`0.5966`**
   - vs `GEMSDOE78-GSC` (`40,000` dots): **`0.6025`**
   - vs `GEMSDOE83` GVCD (`37,654` dots): **`0.6342`** (highest among all 25 comparable rasters; strictly `< 0.70`!)
4. **Why Our Fail-Closed Gate Reports `verdict = "negative"` / `approved_for_weekly_slot = false`:**
   Under Protocol Rule 1's strict literal `> 0.70` forward 3-px dot-overlap rule (`uniqueness.two_phase_summary`), **3 high-density legacy rasters from `GEMSDOE24` exceed `0.70`**:
   - `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (`206,895` dots on a regular 5-px calibration grid covering `99.8724%` of all allowed footprint cells within $\sqrt{8} = 2.828 \le 3.0\text{ px}$: `overlap = 0.9988`, `rho = -0.0004`, `jaccard = 0.0069`);
   - `gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif` (`174,232` dots blanketing `25.58%` of the entire study area and `52.28%` of the `d <= 15 px` catalogue corridor: `overlap = 0.7656`, `rho = 0.0398`, `jaccard = 0.0230`);
   - `gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif` (`69,281` dots covering `26.52%` of the study area and `50.81%` of the `d <= 15 px` corridor: `overlap = 0.7170`, `rho = 0.0207`, `jaccard = 0.0154`).
   Combined with the whole-component 3-px buffered LOQO paired 95% CI narrowly straddling zero (`[-0.0007, +0.0343]`) and our strict adherence to the **3-experiment stop rule** (`Protocol Rule 6` — refusing to run a 4th post-hoc experiment to game `0.7170 -> 0.69`), we record **`verdict = "negative"`** and **`approved_for_weekly_slot = false`**.

---

## 6. Official Trusted Sources & Primary Scientific Literature

1. **DrivenData Competition 306 — DOE GEMS Problem Description, Metric (`alpha=0.2, beta=0.8`, 300 m kernel) & GeoTIFF Specification:** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
2. **DrivenData Official Public Leaderboard:** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
3. **DrivenData Official Reference Solution Repository:** <https://github.com/drivendataorg/gems-prize-reference-solution> (snapshot in `research/upstream/official-reference-README.md`)
4. **DOE Geothermal Data Repository — INGENIOUS Great Basin Dataset (GDR Submission 1391, CC BY 4.0, DOI `10.15121/1887495`):** <https://gdr.openei.org/submissions/1391>
5. **USGS GeoDAWN Airborne Magnetic, Radiometric & LiDAR Compilation (DOI `10.5066/P93LGLVQ`, CC0 1.0):** <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
6. **USGS Quaternary Fault and Fold Database of the United States:** <https://www.usgs.gov/programs/earthquake-hazards/faults>
7. **USGS State Geologic Map Compilation (SGMC, Horton et al. 2017, DS 1052, DOI `10.3133/ds1052`):** <https://pubs.usgs.gov/ds/1052/>
8. **EPSG:32611 (`WGS 84 / UTM zone 11N`) Coordinate Reference System:** <https://epsg.io/32611>
9. **Peer-Reviewed Structural & Geochemical Methodology References:**
   - Fournier, R. O., & Potter, R. W. (1982). *A revised and expanded silica (quartz) geothermometer.* Geothermal Resources Council Bulletin, 11(10), 3–12.
   - Giggenbach, W. F. (1988). *Geothermal solute equilibria: Derivation of Na-K-Mg-Ca geoindicators.* Geochimica et Cosmochimica Acta, 52(12), 2749–2765. <https://doi.org/10.1016/0016-7037(88)90143-3>
   - Grauch, V. J. S., & Hudson, M. R. (2007). *Guides to understanding the aeromagnetic expression of faults in sedimentary basins.* Integrated Investigations of Structure and Tectonics, USGS Professional Paper 1707 / Geophysics, 72(5). <https://doi.org/10.1190/1.2750381>
   - Peacock, D. C. P., & Sanderson, D. J. (1991). *Displacements, segment linkage and relay ramps in normal fault zones.* Journal of Structural Geology, 13(6), 721–733. <https://doi.org/10.1016/0191-8141(91)90033-F>
   - Curewitz, D., & Karson, J. A. (1997). *Structural settings of hydrothermal outflow: Fracture permeability maintained by fault propagation and interaction.* Journal of Volcanology and Geothermal Research, 79(3–4), 149–168. <https://doi.org/10.1016/S0377-0273(97)00027-9>
