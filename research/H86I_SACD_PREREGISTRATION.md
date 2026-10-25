# H86I-SACD Preregistration (Declared Prior to Holdout Evaluation)

- **Date (UTC):** `2026-10-25`
- **Session branch:** `arena/95a42d60-gemsdoe86`
- **Selected lane:** `H86I-SACD` (*Spin-2 Coulomb-Projected Strike Concordance, Jacobsen Upward-Continuation Depth-Attenuation & Bekker–Davis Alluvial-Burial Propensity Submodular Max-Cover*)
- **Machine-readable specification:** `research/H86I_SACD_PREREGISTRATION.json`
- **Candidate hypothesis queue (4 untried hypotheses):** `registry/h86i_hypotheses.json`

## 1. Physical Hypothesis & Mechanism

Unmapped Quaternary and blind geothermal faults in the Great Basin omit from the USGS QFDB / INGENIOUS compilation primarily where Holocene alluvial-fan aprons, thin pediments, and playa deposits lower geomorphic mapping propensity $c(x) = P(\text{mapped}\mid\text{fault}, x)$. Extending scalar elastic tip halos (`H86F-EWCS`) fails when transverse non-tectonic lineaments (Pleistocene Lake Lahontan shoreline bars around `1,255–1,345 m`, E–W aeromagnetic leveling seams, or cross-strike ephemeral drainages) cross a tip lobe.

`H86I-SACD` introduces three coupled mechanisms not previously tested in `GEMSDOE86`:

1. **Spin-2 Coulomb-Projected Strike Concordance:** Outward unit propagation vectors at fold-visible fault terminations project a 2-D spin-2 failure-strike field $(\cos 2\theta_{\text{stress}}, \sin 2\theta_{\text{stress}})$ across collinear cones, Pollard–Segall tensile wing-crack lobes, and opposing-tip releasing stepover bridges. Signed spin-2 inner products $\cos 2(\theta_m - \theta_{\text{stress}}) \in [-1, +1]$ against (a) Lahontan-deconfounded 1 m USGS 3DEP LiDAR + 10 m 3DEP scarp strike, (b) vector-consistent Laplace $g_{zz} = -(\partial_{\text{col}}\text{B18} + \partial_{\text{row}}\text{B11}) = 0$ density-step strike, and (c) analytical Verduzco magnetic tilt $\arctan2(\text{B9}, \text{B3}) = 0$ contour strike boost strike-compatible fault continuations (`> 0`) while vetoing orthogonal shoreline and survey artifacts (`< 0`).
2. **Jacobsen (1987) Upward-Continuation Attenuation & GeoDAWN K/Th–U/Th Alteration:** Log vertical attenuation between native `Band 14 (tmi)` gradient and `150 m` upward-continued `TMI_up150` gradient isolates shallow brittle Cenozoic fault offsets from deep Mesozoic pluton walls, paired with GeoDAWN `K/Th` potassic adularia-illite and `U/Th` redox alteration plus 10 m fluvial $\Delta\chi$ and $k_{sn}$ knickzones.
3. **Strict Leave-One-Quadrant-Out Bekker–Davis PU Calibration & Minoux 300 m Submodular Max-Cover:** PU `HistGradientBoostingClassifier` models are fit strictly out-of-quadrant (`quad != fold_i`, fixing the trans-quadrant PU sampling noted in `H86F-EWCS`) with label-free inverse-exposure-propensity weights on visible positives, and decoded into `37,654` unit dots via Minoux lazy-greedy submodular maximization of expected `300 m` triangular-kernel `TP_w`.

## 2. Named Non-Fault Mimic

Shallow subvertical Tertiary mafic dike swarms or welded ash-flow tuff cooling joints striking subparallel to regional NNE Basin-and-Range extension beneath thin piedmont veneers, and Pleistocene Lake Lahontan highstand bars (~`1,305 m`) where shoreline strike locally parallels range-front fault strike.

## 3. Frozen Budget & Evaluation Protocol

- **Evaluator:** Unmodified `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`), `buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)` (`11,321` withheld positive pixels), `1,000` paired spatial-block bootstrap draws on `200-px` (`20 km`) physical blocks (`seed=520810`).
- **Arms (`3` total, within `<= 3` experiment / `<= 2` hour cap):**
  1. `E1_sacd_full_submod` (`37,654` dots, `3.0 px` visible collar): Full `H86I-SACD`.
  2. `E2_sacd_scalar_unweighted_thin` (`37,654` dots, `3.0 px` visible collar): Matched-collar ablation removing Spin-2 strike concordance, Bekker–Davis propensity weighting, and submodular kernel allocation (using `disc_thin` at `2.8 px`).
  3. `E3_sacd_cover_blind_subsurface` (`37,654` dots, `3.0 px` visible collar): Pure cover-blind subsurface + hydrothermal + Spin-2 subsurface strike concordance (zero DEM/slope/LiDAR/10 m topo/fluvial $\chi$ inputs).
- **Fail-Closed Governance:** Pre-placement surface registry check (`check_h86e_registry.py --surface`) precedes dot placement; final-dot registry check + `pa86_chance_overlap.py` precede GeoTIFF serialization; because `17GEMSDOE` covers `100.0%` of allowed footprint pixels and `2` upstream registry rows are off-grid, `verdict` remains `"negative"`, `decision` `"DO NOT SUBMIT"`, and `submission_slots_used = 0`.
