# H86I-KSAD Preregistration — Kostrov–Byerlee Azimuthal Tendency, Upward-Continued Depth Persistence & Dinkelbach Submodular $K_3$ Allocation

**Frozen UTC:** `2026-10-25T16:00:00Z` (committed before writing any `H86I` feature extraction, classifier, allocator, or holdout evaluation code).  
**Lane:** `H86I-KSAD` (`H86I-1` from `registry/h86i_ksad_hypotheses.json`).  
**Budget:** Maximum `3` candidate experiment arms (`E1`, `E2`, `E3`), `< 2.0` hours wall-clock, `0` live DrivenData weekly submission slots spent.

## 1. Forensic Motivation & Protocol Continuity

Prior repository lanes leave two simultaneous gaps uncovered by line-by-line code audit:

1. **Physics & Training Gap (`H86C-KSLB` vs `H86F-EWCS`):**
   - `H86C-KSLB` (`HOLDOUT-DTI = 0.1241`, `95% CI [0.1080, 0.1403]`, strict outer Leave-One-Quadrant-Out `quad != q` training) ingested external USGS 3DEP 1-m LiDAR and 10-m DEM layers, **but** misidentified `Band 6 (tc)` as magnetic tilt and `Band 11/18` as vertical gravity tilt (`IR-86-BAND6-TC-MISLABEL-20261024`, `IR-86-BAND11-18-GRAV-VECTOR-20261024`), lacked Pollard–Segall off-axis crack-tip/stepover/stress-shadow fields, and used fixed-spacing decimation.
   - `H86F-EWCS` (`HOLDOUT-DTI = 0.1723`, `95% CI [0.1530, 0.1898]`) repaired the Band 6/11/18 physics and added Pollard–Segall crack-tip fields, **but** (a) omitted all sub-100m 1-m LiDAR scarp polarity, 10-m fluvial $k_{sn}$/$\chi$ knickpoints, 150-m upward-continued magnetic depth persistence, K/Th potassic decoupling, and absolute-elevation Lake Lahontan (`1,180–1,345 m ASL`) contour deconfounding; (b) trained `sample_nested_pu` on all 4 quadrants' visible components rather than strict outer Leave-One-Quadrant-Out (`quad != q` eroded 12 px; documented as `IR-86-H86F-INQUAD-TRAINING-20261025`); (c) omitted Elkan (2001) Bayes subsampling odds calibration; and (d) decoded via fixed `2.8 px` greedy Poisson-disc thinning rather than exact DTI submodular fractional programming.

2. **DTI Fractional-Programming Gap (`Dinkelbach Submodular K3-Supremum Allocation`):**
   Under the official Distance-Weighted Tversky Index ($\alpha = 0.2$, $\beta = 0.8$, $R = 300\text{ m} = 3\text{ px}$, $K_3(d) = \max(1 - d/3, 0)$), for a Bayes-calibrated pixel fault posterior $p(y) \in (0, 1)$, the expected truth-coverage function
   $$F(S) = \sum_{y \in \Omega} p(y) \max_{s \in S} K_3(\|s - y\|)$$
   is **monotone submodular** because for each pixel $y$, $S \mapsto \max_{s \in S} w_{s,y}$ has non-increasing marginal gain $\Delta_y(x \mid S) = \max(0, K_3(\|x-y\|) - C_S(y))$. Under Dinkelbach's (1967) parametric fractional transform at target score $\lambda^* = 0.17$, adding candidate pixel $x$ improves expected DTI iff
   $$\Delta \Phi_{\lambda^*}(x \mid S) = (1 - 0.2\lambda^*)\sum_{\|x-y\|\le 3} p(y)\max\!\big(0, K_3(\|x-y\|) - C_S(y)\big) - 0.2\lambda^*\big(1 - \widehat{M}(x)\big) > 0,$$
   where $\widehat{M}(x) = 1 - \prod_{\|x-y\|\le 3}(1 - K_3(\|x-y\|)\,p(y))$ is the Noisy-OR expected self-credit of dot $x$. Unlike fixed `2.8 px` thinning, Minoux (1978) lazy-greedy maximization of $\Phi_{\lambda^*}$ spaces dots adaptively at `~4.4–5.0 px` along moderate-confidence blind strands while allowing `~2.4–2.8 px` infill only where residual uncovered posterior mass exceeds the marginal bar.

## 2. Frozen Three-Arm Experiment Matrix

- **`E1_ksad_dinkelbach_submod` (Primary Candidate):** 26 quadrant-invariant physical planes + 6 fold-visible anisotropic Kostrov–Pollard elastic planes, strict outer LOQO (`quad != q` eroded 12 px) + nested cross-component SAR cover-propensity PU ensemble (`HistGradientBoostingClassifier` + cover-blind subsurface specialist gated in low-slope basins), Elkan (2001) Bayes prior-odds calibration, and Minoux-exact Dinkelbach Submodular $K_3$-Supremum Allocation (`budget_cap = 37,654`, `min_sep = 2.4 px`, `lambda* = 0.17`, `collar = 2.6 px`).
- **`E2_ksad_pointwise_d28_ablation` (Allocator Ablation):** Exact same fold posteriors as `E1`, decoded via fleet-standard `2.8 px` greedy Poisson-disc thinning at `37,654` dots (`collar = 2.6 px`).
- **`E3_ksad_cover_blind_no_catalogue` (Zero-Catalogue Cover-Blind Control):** Excludes all 6 catalogue-derived elastic features and native 100 m DEM (`Bands 12, 19`), decoded via the same Dinkelbach Submodular $K_3$-Supremum Allocator.

## 3. Binding Pre-Placement, Pre-Serialization & Publication Gates

1. **Single-Feature Leakage Canary:** Every one of the `32` features (`26` static + `6` fold-visible) must satisfy $\max(\text{AUC}, 1 - \text{AUC}) \le 0.90$ on the `11,321` withheld positives before any holdout result is accepted.
2. **Pre-Placement Registry Surface Gate (`Rule 1` & `Rule 11`):** Run `scripts/check_h86e_registry.py --surface` (`v2` SHA-bound) on the full-catalogue bounded `[0, 1]` posterior surface **before** placing final dots. Abort immediately if any valid raster exceeds Spearman $\rho > 0.90$.
3. **Pre-Serialization Final-Dot Registry & Chance-Overlap Gate (`Rule 1` & `Rule 11`):** Run `scripts/check_h86e_registry.py` and `scripts/pa86_chance_overlap.py` on final dots **before** writing any GeoTIFF. Abort without writing a `.tif` if any valid raster has $\rho > 0.90$ or any discrete non-space-filling dot field has forward 3-px overlap $> 0.70$.
4. **Fail-Closed Publication Status (`AGENTS.md` Rules 6, 8, 10, 11):** Because `17GEMSDOE` covers `100%` of allowed pixels (`5,106,385`) and 2 registry rasters (`14GEMSDOE`, `7GEMSDOE`) are grid/band-incompatible (`688/690` compatible), `literal_gate_pass`, `surface_gate_pass`, `final_dots_gate_pass`, and `pa86_02` fail closed; any emitted GeoTIFF is registered strictly as `DO NOT SUBMIT` (`verdict = "negative"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`), and `scripts/run_h86i_ksad.py` is locked behind `protocol_preflight.require_feasible()` upon completion.
