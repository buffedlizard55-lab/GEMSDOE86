# Session Review — 2026-10-25 (`0bec8252` / Lane `H86J-CSGD`): PhD Analysis of `GEMSDOE32` (`0.2778`), Full-Registry Revocation of `H86G-EDTI`, Cover-Blind Cross-Spectral Geothermal Conduit Validation, and Three-Pass Audit

- **Branch:** `arena/0bec8252-gemsdoe86` (branched from `main` @ `badc1e63829835755143b6bbec594b960ff4d781`)
- **Date (UTC):** `2026-10-25`
- **Primary Lane Executed:** `H86J-CSGD` — *Selected-At-Random (SAR) Geomorphically De-Biased Cross-Spectral Potential-Field Admittance & Geothermal Upflow Conduit PU*
- **Generated Unique GeoTIFF:** `docs/downloads/gems86-h86j-csgd-sar-admit-37654dots-20261025T055033Z-35faffb4-zeros.tif`
  - **SHA-256:** `079914e36dec80349310f52289119ad8a956f13e435369422859d5dd0b16707f`
  - **Companion single-TIFF ZIP:** `docs/downloads/gems86-h86j-csgd-sar-admit-37654dots-20261025T055033Z-35faffb4-zeros.zip`
  - **Canonical Run Card:** `docs/evidence/h86j-csgd-run-card.json`
  - **Automated Gate Decision:** **`DO NOT SUBMIT`** (`verdict: "negative"`, `submission_ready: false`, `safe_to_submit: false`, `submission_slots_used: 0`)
- **Critical Governance Action (`IR-86-H86G-LOCAL-ONLY-DUP-20261025`):** Revoked PR #107's `H86G-EDTI` (`gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif`, SHA-256 `ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d`) from `promote` to `negative` (`DO NOT SUBMIT`) after restoring all **655 external Git blobs** (`data/registry_ext/`) via zero-REST-quota `codeload.github.com` tarballs + shallow git-pack extraction (`scripts/restore_registry_inventory.py`) and proving **44 dot-field forward-3px overlap firings (`> 0.70`) and 25 informative (`halo_coverage <= 0.70`) dot-field firings** (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`) that PR #107 missed by scanning only 43 local files.

---

## 1. PhD-Level Forensic Analysis: Why and How `GEMSDOE32` (`h33-h33-2-b2`, `0.2778` OWNER-REPORTED) Scored Highest Across the Supplied Fleet — and Can We Score Higher?

### 1.1 Evidence-Class Discipline First
Every number below carries its strict evidence class per `AGENTS.md` Rules 3–4:
- **`OWNER-REPORTED` (unverified claim; not `ORGANIZER-CONFIRMED`):** `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) = `0.2778`; `GEMSDOE36` = `0.2750`; `GEMSDOE28` (`d2.8`) = `0.2708`; `GEMSDOE25` (`d2.5`) = `0.2623`; `GEMSDOE70` = `0.2478`; `GEMSDOE89` = `0.0301`; `GEMSDOE90` = `0.0749`; conflicting owner-supplied top-leaderboard claims `0.3195` (2026-10-24 request) and `0.4413` (2026-10-25 request). Zero rows in `ledger/submissions.csv` carry an organizer portal receipt (`ORGANIZER-CONFIRMED`).
- **`HOLDOUT-DTI` (`gems57-pooled-hide-v2`):** spatially blocked hide-and-recover evaluation on `existing_faults.tif` (`seed=20`, `hide_frac=0.20`, `buffer_px=3`, `11,321` withheld positive pixels across 4 spatial folds, 1,000-draw paired bootstrap over 20 km × 20 km physical blocks).
- **`SGMC-PROXY-DTI` (off-catalogue diagnostic instrument only, never a leaderboard projection):** binary Distance-Weighted Tversky Index against pinned USGS SGMC fault traces at `d_cat > 3 px` (`62,122` pixels).

### 1.2 Exact Pixel-Level Mechanism of `GEMSDOE32` (`0.2778` OWNER-REPORTED)
Direct byte-and-pixel diffing of the SHA-pinned fleet rasters (`docs/evidence/h86f-h33-forensics.json`, `docs/evidence/concurrent-artifact-review-20261025.json`) establishes that `GEMSDOE32` introduced **zero new geological features and zero new model training** relative to its `GEMSDOE28` (`H19-5 / d2.8`) parent:
1. **Exact lineage identity:**
   $$\text{supp}(\text{GEMSDOE32}) \;=\; \text{supp}(\text{GEMSDOE28}) \;\cap\; \{x : d_{\text{cat}}(x) > 2.0\text{ px}\}$$
   Across all `3,730 × 3,292 = 12,279,160` cells of `EPSG:32611`, `GEMSDOE28` has `40,199` unit-value (`1.0`) dots and `GEMSDOE32` has `37,654` unit-value dots (`2,545` dots removed inside the `1.0 < d_cat <= 2.0 px` mapped-fault collar; `0` dots added; `0` other pixels altered).
2. **Why `d ≈ 2.8 px` unit-mass Poisson-disc emission beat continuous/blurred probability rasters (`~0.156` -> `~0.271` OWNER-REPORTED):**
   The DrivenData competition metric (`vendor/gems57/metric.py`) is the asymmetric Distance-Weighted Tversky Index with $\alpha = 0.2$ (false-positive weight), $\beta = 0.8$ (false-negative weight), and triangular 300 m ($R = 3\text{ px}$) spatial tolerance kernel $K(r) = \max(0, 1 - r/3)$:
   $$\text{DTI}(P, G) \;=\; \frac{T(P, G)}{0.2\,T(P, G) + 0.2\,F(P, G) + 0.8\,|G| + \epsilon}$$
   where truth recovery uses a **supremum** over kernel-weighted predictions,
   $$T(P, G) \;=\; \sum_{g \in G} \max_{x:\,\|x-g\|_2 \le 3} P(x)\,K(\|x-g\|_2),$$
   whereas false-positive mass sums **every** positive pixel weighted by its complement truth proximity:
   $$F(P, G) \;=\; \sum_{x} P(x)\,\Bigl(1 - \max_{g \in G} K(\|x-g\|_2)\Bigr).$$
   Because $T$ takes a **local maximum** within 300 m while $F$ **sums** over all emitted pixels, placing a second dot within $< 2.8\text{ px}$ of an existing unit dot along a ridge adds almost zero marginal truth credit $\Delta T$ while paying up to $+1.0$ full false-positive mass $\Delta F$. Converting continuous surfaces into unit-value (`1.0`) dots spaced at $r_{\min} = 2.8\text{ px}$ maximizes kernel-canopy area per unit false-positive mass (~18 pixels of $K \ge 1/3$ coverage per dot).
3. **Exact algebraic condition under which `GEMSDOE32`'s `d_cat <= 2.0 px` collar prune increased DTI (`0.2708 -> 0.2778` OWNER-REPORTED):**
   Removing a subset $\Delta P$ of collar dots that loses truth credit $a = T(P) - T(P \setminus \Delta P) \ge 0$ and saves false-positive mass $b = F(P) - F(P \setminus \Delta P) \ge 0$ strictly increases DTI if and only if:
   $$\boxed{\;T \cdot b \;>\; a\,\bigl(F + 4|G| + 5\epsilon\bigr)\;}$$
   On the private test set, organizers evaluate **unmapped** faults ($G_{\text{private}} \cap \text{Catalogue} = \emptyset$). Mapped-fault segments in `existing_faults.tif` are zeroed out of $G_{\text{private}}$; only rare off-catalogue splays/extensions terminating within `100–200 m` of a mapped trace contribute to $a$, whereas thousands of parallel collar dots along already-mapped range-front faults sit $> 300\text{ m}$ from any unmapped fault and contribute pure false-positive mass $b \approx 2,545$. At $T \approx 10,963$, $F + 4|G| \approx 197,000$ (`SLOT_PLAN.md` §D), pruning `2,545` collar dots raises DTI whenever $a < 141$ kernel-credit units (i.e., $< 5.5\%$ of pruned collar dots sat adjacent to an unmapped branch).
4. **Why `GEMSDOE89` (`0.0301`) and `GEMSDOE90` (`0.0749`) collapsed:**
   Both abandoned range-front structural localization for broad diffuse halos or over-dispersed non-scarp fields while claiming uniqueness on incomplete/privately-altered local checks (`IR-86-FLEET-GEMS89-90-20261024`), cratering $T$ while keeping $F \approx 35,000\text{–}37,654$.

### 1.3 Can We Score Higher Than `0.2778` — and Why Is There a Structural Tension With the Fleet Uniqueness Gate?
Yes in geophysical principle, **if and only if** we solve two coupled quantitative problems that our experiments in `H86F-EWCS`, `H86G-EDTI`, and `H86J-CSGD` have now measured directly:
1. **Where the unmapped Great Basin fault truth actually sits:**
   Measuring terrain slope across the footprint (`5,167,373` pixels) shows that `existing_faults.tif` (`56,519` px) is **72.8%** on terrain slope $\ge 5^\circ$, off-catalogue USGS SGMC faults (`62,122` px at $d_{\text{cat}} > 3\text{ px}$) are **85.1%** on slope $\ge 5^\circ$, and `GEMSDOE32` (`h33-h33-2-b2`) places **84.2%** of its `37,654` dots on slope $\ge 5^\circ$.
2. **Why every high-recall range-front/piedmont detector collides with the 92-repo fleet:**
   Across the `692`-entry registry (`636` discrete dot fields + `54` continuous surfaces + `2` off-grid historical rows), prior lanes (`12GEMSDOE`, `13GEMSDOE`, `15GEMSDOE`, `GEMSDOE22..50`) saturated range-front scarps. Consequently:
   - `H86F-EWCS` (`0.1723` `HOLDOUT-DTI`) triggered **20 informative (`halo_coverage <= 0.70`) firings**;
   - `H86G-EDTI` (`0.0631` `HOLDOUT-DTI`, `0.1223` `SGMC-PROXY-DTI`) triggered **25 informative dot-field firings** once all 655 external blobs were restored (`0.7602` vs `GEMSDOE46:r11f` at `44,090` dots!).
3. **What `H86J-CSGD` proved:**
   - **Arm `E2_csgd_unweighted_pu_ablation` ($\gamma = 0.0$, zero DEM/slope features in $P_{\text{deep}}$):** Using purely cover-penetrating Bouguer–magnetic cross-spectral admittance + GDR-1391 deep conductive thermal anomaly + Lahontan-corrected GeoDAWN radiometrics + visible-catalogue Mohr-Coulomb elastic stress transfer achieved **`HOLDOUT-DTI = 0.1577 [0.1401, 0.1755]`** — the **second-highest holdout score in repository history** (recovering **91.5%** of DEM-coupled `H86F-EWCS`'s `0.1723` and beating `H86C-KSLB` `0.1241` and fold-fair `R0_D25` `0.0961` with **zero topographic slope inputs**), while cutting informative overlap firings to `14`.
   - **Arm `E1_csgd_sar_debiased` ($\gamma = 0.85$ SAR geomorphic burial weighting):** Weighting training/inference toward geomorphically buried basins (`slope < 2.5°`, Quaternary basin fill) **eliminated 100% of informative dot-field overlap firings (`0 / 636` dot fields with `halo_coverage <= 0.70`!)** — the **first candidate in repository history** to achieve zero informative dot-field firings across the full restored registry — while beating `R0_D28_visible_collar` (`0.0613` vs `0.0273`, paired $\Delta = +0.0340 \; [+0.0209, +0.0470]$), at the cost of surface-mapped holdout (`0.1577 -> 0.0613`) because withheld `existing_faults.tif` segments are predominantly exposed range-front traces.

---

## 2. Previous-Session Action Items Executed First: Full-Registry Restoration & Revocation of `H86G-EDTI`

1. **Zero-REST-Quota Full Registry Restoration (`scripts/restore_registry_inventory.py`):**
   - Previous sessions left `data/registry_ext/` only partially populated or hit `api.github.com` 5,000-req/hr REST rate limits when fetching `655` blobs one by one.
   - We upgraded `scripts/restore_registry_inventory.py` to fall back automatically from `gh api` to repo-grouped `codeload.github.com/<owner>/<repo>/tar.gz/HEAD` streaming + bare blobless `git clone --filter=blob:none` + `git cat-file blob <sha1>`, verifying exact byte count and SHA-256 digest before atomic `.partial -> .tif` placement. All **`655 / 655` external blobs (`727.8 MB`)** verified cleanly.
2. **Full-Registry Audit & Revocation of PR #107's `H86G-EDTI` (`IR-86-H86G-LOCAL-ONLY-DUP-20261025`):**
   - PR #107 marked `gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif` as `PROMOTE — OK TO SUBMIT` after running a custom local-only loop (`run_h86g_edti.py::check_uniqueness`) over **43 local files** (`max = 0.6850`) and leaving `run_h86g_edti.py::main` outside `BUILDERS` preflight enforcement.
   - Auditing `H86G-EDTI` against all `689` compatible restored rasters (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`) uncovered **44 dot-field forward-3px overlap firings (`> 0.70`)** and **25 informative (`halo_coverage <= 0.70`) dot-field firings**, including sparse 37k–44k submissions:
     - `GEMSDOE46:docs/r11f/gems46-r11f-scarp-radiometric-fusion-00e049b51218-zeros.tif` (`44,090` dots): **`76.02%`** forward 3-px overlap;
     - `GEMSDOE41:docs/downloads/gems41-h42-basinmargin-s4-n40000-20261006T015229Z-allfinite.tif` (`40,000` dots): **`73.99%`** forward 3-px overlap;
     - `GEMSDOE46:docs/r12/gems46-r12-scarp-rad-concordance-23e807e2de9f-zeros.tif` (`37,654` dots): **`72.24%`** forward 3-px overlap;
     - `GEMSDOE50:docs/downloads/gemsdoe50-h57-scarpstep-80000-20261007T1830Z.tif` (`80,000` dots): **`94.52%`** forward 3-px overlap.
   - We revoked `H86G-EDTI` to `verdict: "negative"`, `decision: "DO NOT SUBMIT"`, `submission_ready: false`, `duplicate: true` across `docs/evidence/h86g-edti-run-card.json`, `docs/downloads/gems86-h86g-edti-...-zeros.json`, `docs/evidence/download-inventory.json`, `scripts/audit_release.py`, `scripts/check_site.py`, `scripts/build_site.py`, `AGENTS.md` Rule 12, `SLOT_PLAN.md`, and `README.md`, and gated `scripts/run_h86g_edti.py::main` behind `require_feasible()`.

---

## 3. Four Novel Candidate Geological Hypotheses (`registry/h86j_hypotheses.json`)

All band indices were verified line-by-line against `src/gems86/io.py::BANDS` and `docs/evidence/band-physics-verification-20261024.json` (`Band 6 = GeoDAWN TC`, `(+Band 18, -Band 11) = horizontal Bouguer gravity gradient vector`):

| Rank | ID / Lane | Specific Layers | Physical Transform & Why Catalogue-Missing | Novelty vs Repo & Fleet | Named Non-Fault Mimic | Cost / Status |
|---:|---|---|---|---|---|---|
| **1** | `H86J-1` (`H86J-CSGD`) | Native Bands `0,1,2` (DEM/slope/curvature in SAR $e(x)$ only), `3,9,17` (`mag_hgm`, `mag_thd`, `mag_rtp`), `4,5,6` (`U,Th,TC` + `5-4*2` `K_pct`), `7,11,12,18` (`grav_bouguer`, `grav_hgm`, signed $(\partial_x g, \partial_y g)$), `8` (`heatflow`), `10` (`mt_2km`), `16` (`fault_slip_dilation`), plus SHA-pinned `ingenious_gdr1391_playfairway_100m.tif` (excl. `dist_known_fault_px`), `earthmri_radiometrics_4band_100m.tif`, `nv_quaternary_alluvium_mask_100m.tif` | Multi-scale directional Bouguer–RTP cross-spectral admittance $\mathcal{A}_\sigma(x) = (\nabla g_\sigma \cdot \nabla M_\sigma)/(|\nabla g_\sigma|^2 + \tau_g^2)$ + cross-skewness + GDR-1391 deep conductive thermal anomaly + Lahontan-deconfounded K/Th, trained under Bekker-Davis Selected-At-Random (SAR) geomorphic exposure propensity $e(x)$ (`gamma = 0.85`). Catches sub-alluvial blind geothermal conduits censored by Holocene playa/fan sedimentation. | First SAR inverse-propensity de-biased PU fault model and first directional Bouguer–magnetic admittance tensor + GDR-1391 deep thermal integration in GEMSDOE86 or the 92-repo fleet. | Buried Mesozoic pluton-wallroof intrusive contacts, tabular intra-basin basalt sills, and paleo-channel detrital heavy-mineral placers. | ~16 min CPU · **SELECTED & VALIDATED (`0.0613` E1 / `0.1577` E2)** |
| **2** | `H86J-2` (`H86J-2-GTHD`) | Native Bands `7,11,12,18` (`grav_bouguer`, `grav_hgm`, signed $(\partial_x g, \partial_y g)$) + `3,9,17` (`mag_hgm`, `mag_thd`, `mag_rtp`) | Multi-altitude upward-continued (`200 m -> 2,400 m`) Gravity-Tensor Tilt-Depth & Euler Structural-Index (`N=0` step vs `N=1` sill/dike) Depth-Persistence Tracker. Isolates steeply dipping basement growth faults persisting to 1.5–3 km depth beneath Quaternary fill. | Uses exact upward continuation and `N=0` vs `N=1` structural-index rejection rather than single-level `g_zz` (`H86F-GZZD`) or cross-corridor marker shift (`H86E-MMT`). | Steep caldera ring-fracture margins and Paleozoic carbonate-to-shale thrust ramps. | ~14 min CPU · Deferred behind Rank 1 |
| **3** | `H86J-3` (`H86J-3-MTHB`) | Native Bands `10` (`mt_2km`), `8` (`heatflow`), `13,14,15` (`eq_dist`, `bvalue`, `geodetic_strain`), `16` (`fault_slip_dilation`) + `ingenious_gdr1391_playfairway_100m.tif` (`ads_composite`, `temp_2depth_c`, `crit_stress_numeric`) | Transverse lateral gradient $\|\nabla_\perp \log \sigma_{\text{MT}}\|$ aligned with geodetic strain principal axes, low Gutenberg-Richter $b$-value, and conductive thermal residual $\Delta T_{\text{conv}}$ at resistive-to-conductive smectite-cap boundaries. | Targets resistivity *boundaries* co-located with active strain and microseismic stress concentration rather than raw interior MT conductance (`H86B-GFCO`). | Closed-basin hypersaline evaporite brines and graphitic/pyritic Paleozoic marine black shales (Roberts Mountains allochthon). | ~8 min CPU · Deferred behind Rank 1 |
| **4** | `H86J-4` (`H86J-4-BHSA`) | Native Bands `7,11,18` + `17` + pinned `ingenious_gdr1391_basement_depth_sed_thickness_100m.tif` + `nv_quaternary_alluvium_mask_100m.tif` | Explicit 3D Basin-Fill Compaction-Gravity Forward Stripping ($\Delta g_{\text{sed}}$ from sediment thickness $H_{\text{sed}}$) + Sub-Alluvial Accommodation Transfer Relay Saddle detector (`det(H(H_{\text{sed}})) < 0`). | First explicit sediment-thickness gravity stripping isolating intra-basin basement horst/relay steps from overarching range-front half-graben bowls. | Pre-Cenozoic paleovalley incisions carved into Mesozoic bedrock prior to ash-flow tuff infill. | ~10 min CPU · Deferred behind Rank 1 |

---

## 4. `H86J-CSGD` Complete Validation Results (`docs/evidence/h86j-csgd-run-card.json`)

### 4.1 Single-Feature Leakage Canary (`max(AUC, 1-AUC) <= 0.90`)
- **28 / 28 features passed** (`0` flags). Maximum discriminative AUC = **`0.7742`** (`stepover_bridge`), well below the `0.90` stop threshold. GDR-1391 `dist_known_fault_px` was explicitly blocked in `src/gems86_csgd/features.py::FORBIDDEN_GDR_DESCRIPTIONS`.

### 4.2 Spatially Blocked Holdout (`gems57-pooled-hide-v2`, `11,321` Withheld Positives) & Off-Catalogue SGMC Diagnostic

| Arm / Comparator | Evidence Class | `HOLDOUT-DTI` (`95% CI`) | Off-Catalogue `SGMC-PROXY-DTI` | Informative (`c <= 0.70`) Registry Firings (All / Dot-Field Only) | Scientific Interpretation |
|---|---|---:|---:|---:|---|
| **`E1_csgd_sar_debiased`** *(primary candidate, $\gamma = 0.85$, 37,654 dots)* | `HOLDOUT-DTI` | **`0.0613` `[0.0453, 0.0764]`** | `0.0141` | **`1` / `0`** (`0 / 636` dot fields!) | Beats `R0_D28_visible_collar` (`+0.0340 [+0.0209, +0.0470]`) and eliminates **100% of informative dot-field firings** across the entire 690-raster restored registry; lower exposed-fault recall than `E2` because $\gamma = 0.85$ shifts dots into buried basins. |
| **`E2_csgd_unweighted_pu_ablation`** *($\gamma = 0.0$, zero DEM/slope in $P_{\text{deep}}$)* | `HOLDOUT-DTI` | **`0.1577` `[0.1401, 0.1755]`** | `0.0591` | `14` / `13` | **2nd-highest HOLDOUT-DTI in repo history** (behind DEM-coupled `H86F-EWCS` `0.1723`), beating `H86C-KSLB` (`0.1241`) and fold-fair `R0_D25` (`0.0961`) with **zero DEM slope features**. |
| **`E3_csgd_autonomous_blind_conduit`** *($\gamma = 0.85$, zero catalogue/elastic features)* | `HOLDOUT-DTI` | **`0.0465` `[0.0343, 0.0583]`** | `0.0128` | **`1` / `0`** (`0 / 636` dot fields!) | Pure cover-blind geophysical conduit model with zero catalogue geometry still beats `R0_D28_visible_collar` by `1.70x` with `0` informative dot-field firings. |
| `R0_D28_visible_collar` *(preregistered control)* | `HOLDOUT-DTI` | `0.0273` `[0.0227, 0.0321]` | — | — | Already-pruned `GEMSDOE28` masked by fold-visible `3 px` collar. |
| `H86C-KSLB` (`E3_kslb_noisyor_44k`, same split) | `HOLDOUT-DTI` | `0.1241` `[0.1080, 0.1403]` | — | — | Prior range-front + stepover benchmark (`44,090` dots). |
| `H86F-EWCS` (`E1_ewcs_coupled_pu`, same split) | `HOLDOUT-DTI` | `0.1723` `[0.1530, 0.1898]` | — | `20` | Repo holdout record (uses DEM topographic scarps; blocked by 20 informative firings). |
| `H86G-EDTI` *(PR #107, REVOKED)* | `HOLDOUT-DTI` | `0.0631` `[0.0468, 0.0806]` | `0.1223` | `26` / `25` | Revoked (`IR-86-H86G-LOCAL-ONLY-DUP-20261025`): 25 informative dot-field firings on full registry. |

### 4.3 Full-Registry Pre-Placement Surface & Final-Dots Uniqueness (`690 / 692` Compatible Rasters)
- **Pre-placement continuous surface (`docs/evidence/h86j-csgd-registry-surface.json`):** `worst_spearman_full_footprint = 0.5050 <= 0.90` (`0` rho firings across all `690` compatible rasters).
- **Final emitted dots (`docs/evidence/h86j-csgd-registry-final-dots.json`):**
  - `byte_unique_among_checked = true`, `pixel_unique_among_checked = true`;
  - `worst_spearman_full_footprint = 0.0514 <= 0.90` (`0` rho firings);
  - `worst_jaccard = 0.01673` across all `636` discrete dot-field rasters;
  - **`0 / 636` informative (`halo_coverage <= 0.70`) dot-field firings** (`12` space-filling `c > 0.70` lattice/composite firings; `1` continuous-surface halo firing `7GEMSDOE:gems7-halo15-gbt-v1` at `0.7298` over `1,828,699` positive pixels; `1.0000` literal full-support `17GEMSDOE`; `2` grid-incompatible historical rows `14GEMSDOE` and `7GEMSDOE:qfaults_prior`).
- **On-disk validator (`vendor/gems57/validate.py` + `scripts/audit_release.py`):** `EPSG:32611`, `3730 × 3292`, `float32`, `min = 0.0`, `max = 1.0`, `n_nan = 0`, `n_inf = 0`, `outside_footprint_positive = 0`, `on_catalogue_positive = 0`, `note_chars = 123 <= 140`.

---

## 5. Official Verified Data Sources & Limitations

All official primary sources are verified in [`docs/sources.html`](../docs/sources.html) and `docs/evidence/source-review-20261023.json`:
1. **Official Competition Rules (NREL/DOE GEMS Prize):** <https://docs.nlr.gov/docs/fy26osti/96647.pdf> (§1.1, §3.4–3.6: `[0, 1]` range, `<= 3` weekly public-leaderboard slots, `1` final judged submission).
2. **Official DrivenData Submission Specification:** <https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/> (human browser upload only; never scraped per `AGENTS.md` Rule 9).
3. **Great Basin INGENIOUS Play Fairway Dataset (GDR-1391, Faulds et al., UNR/NBMG):** <https://gdr.openei.org/submissions/1391> (`ingenious_gdr1391_playfairway_100m.tif`, SHA-pinned; `dist_known_fault_px` excluded).
4. **USGS GeoDAWN Airborne Radiometrics & Magnetic Survey / EarthMRI:** <https://pubs.usgs.gov/ds/0839/> & <https://mrdata.usgs.gov/radiometric/> (`Band 6 = TC` verified at $r = +0.997140$).
5. **USGS State Geologic Map Compilation (SGMC) Fault Traces:** <https://mrdata.usgs.gov/sgmc/> (held strictly out of training/features; read-only diagnostic).

**Key Limitations:**
1. Literal uniqueness (`<= 70%` 3-px overlap against **every** registry entry) remains mathematically unsatisfiable while full-support `17GEMSDOE` (`100%` of allowed cells) and stride-5 lattice `13GEMSDOE` (`99.87%` 3-px canopy) remain in the comparison set without an organizer/owner-ratified space-filling filter, and 2 historical inventory rows (`14GEMSDOE` shifted transform, `7GEMSDOE` 3-band RGB) fail grid checks.
2. Both `existing_faults.tif` (`72.8%` slope $\ge 5^\circ$) and off-catalogue `SGMC` (`85.1%` slope $\ge 5^\circ$) under-represent truly blind sub-alluvial faults; until an organizer portal receipt is logged in `ledger/submissions.csv`, whether the private test labels reward exposed range-front splays (`E2`, `0.1577`) or sub-alluvial blind conduits (`E1`, `0.0613`) is unverified.

---

## 6. Explicit Three-Pass Verification Log

- **Pass 1 (Implementation & End-to-End Scientific/Audit Execution):**
  - Restored all competition/external inputs and all `655 / 655` external registry blobs (`codeload.github.com` + git-pack fallback in `scripts/restore_registry_inventory.py`).
  - Audited `H86G-EDTI` on the full 692-raster registry (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`) and revoked its false local-only promotion across all evidence, site, audit, and governance files.
  - Preregistered `H86J-1..H86J-4` and executed 3-arm `H86J-CSGD` (`E1 = 0.0613` with `0/636` informative dot-field firings; `E2 = 0.1577`; `E3 = 0.0465`), generating unique GeoTIFF + single-TIFF ZIP + run card.
- **Pass 2 (Bug, Edge-Case & Hidden-Assumption Hunt):**
  - Caught and fixed `vendor/gems57/metric.py` API mismatch (`dti_binary` vs nonexistent `dti`) in `scripts/run_h86j_csgd.py::evaluate_sgmc_proxy_dti` before full pipeline completion.
  - Added SHA-verified output-binding cache in `run_registry_check` so interrupted runs never repeat 8-minute 692-raster scans when `candidate_source_sha256` and `registry_index_sha256` match.
  - Discovered that PR #107 left `scripts/run_h86g_edti.py::main` ungated by `protocol_preflight.require_feasible()` and omitted from `tests/test_builder_preflight.py::BUILDERS`; gated both `run_h86g_edti` and `run_h86j_csgd` behind `require_feasible()` and added regression tests.
  - Closed all special-case `PROMOTE` / `promote_ok` holes in `scripts/audit_release.py` and `scripts/check_site.py`.
- **Pass 3 (Full Re-Verification & Snapshot Hygiene):**
  - Verified byte-for-byte preservation of `REQUEST_20261025.md`, `REQUEST_20261024.md`, `REQUEST_20261023.md`, `OWNER_PROMPT.md`, and `data/prepared_manifest.json`.
  - Removed untracked GB-scale scratch rasters outside `.cache/` (`data/training_features.tif`, `data/bridge/training_features.tif`, `data/registry_ext/`) after completing full-registry measurements so turn-end snapshots stay well below the 128 MB cap.
  - Re-ran `audit_release.py --measure-registry`, `audit_downloads.py --write`, `build_site.py --check`, `check_site.py`, and full `pytest -q` (`0` failures).

---

## 7. Prioritized Recommendations for Next Session

1. **Calibrate Intermediate SAR Burial Exponent $\gamma \in [0.20, 0.45]$ on Pareto Frontier (`E2 = 0.1577` vs `E1 = 0.0613`):**
   - `H86J-CSGD` bracketed the exact Pareto trade-off between surface-mapped holdout recall (`E2` at $\gamma=0.0$: `HOLDOUT-DTI = 0.1577`, `13` dot-field informative firings) and full-registry informative-overlap elimination (`E1` at $\gamma=0.85$: `HOLDOUT-DTI = 0.0613`, `0` dot-field informative firings). Next session should preregister a 3-point $\gamma \in \{0.20, 0.35, 0.50\}$ sweep combined with `H86J-4` explicit 3D sediment-thickness gravity stripping (`ingenious_gdr1391_basement_depth_sed_thickness_100m.tif`) to seek `HOLDOUT-DTI > 0.13` with `0` informative dot-field firings.
2. **Owner Protocol Clarification on the 4 Non-Informative Registry Blockers (`PA-86-03`):**
   - Because `H86J-CSGD` (`E1`) has **already achieved `0 / 636` informative (`halo_coverage <= 0.70`) dot-field firings** and `0` Spearman firings across the entire 690-raster restored registry, the *only* remaining registry blockers are (a) `17GEMSDOE` (`100%` continuous support), (b) `12` space-filling lattices (`halo_coverage > 0.70`), (c) `7GEMSDOE:gems7-halo15-gbt-v1` (`1.83M`-px continuous halo misclassified above the `20%` dense threshold at `35.4%` footprint support), and (d) `2` grid-incompatible historical rows (`14GEMSDOE`, `7GEMSDOE:qfaults_prior`). An owner-ratified protocol amendment excluding `> 20%`-support halos and grid-incompatible rasters in `pa86_chance_overlap.py` would make the automated promotion gate mathematically satisfiable.
3. **Log One Organizer Portal Receipt in `ledger/submissions.csv`:**
   - Zero rows in `ledger/submissions.csv` are `ORGANIZER-CONFIRMED`. Logging even a single human portal receipt will anchor whether the private test fault set tracks range-front off-catalogue SGMC splays or blind basin-floor geothermal conduits.
