# Frozen Preregistration — Lane `H86Q-BFRA` (2026-10-26)

- **Lane ID:** `H86Q-BFRA`
- **Branch:** `arena/6ac94866-gemsdoe86`
- **Hypothesis Queue Reference:** [`registry/h86q_hypotheses_20261026.json`](../registry/h86q_hypotheses_20261026.json)
- **Selected Candidate:** `H86Q-1_BFRA` (Rank 1 of 4 untried hypotheses; directly executes queued next steps `H86P-2_BCSF` and `H86P-3_RCSD` from `SESSION_20261026_H86P_TCWB_REVIEW.md` plus `Bands 1/2/14` TMI-vs-RTP remanence dislocation, repairs `IR-86Q-TCWB-SWAPPED-ARGS-20261026`, and introduces 1-D fault-strand tangent-sharp two-regime radial Dinkelbach-CELF)
- **Frozen JSON Contract:** [`research/H86Q_BFRA_PREREGISTRATION.json`](H86Q_BFRA_PREREGISTRATION.json)

## 1. Parallel-Run Protocol Binding Constraints

1. **Single Method Lane (`<= 3` Experiments, `< 2` Hours, `0` Live Slots Spent):**
   - `E1_bfra_coupled_tworegime_dcelf` (Primary coupled + blind two-regime candidate, `37,654` dots, `d_min = 2.8 px`, `d_cat > 3.0 px`)
   - `E2_bfra_blind_subsurface_piedmont_dcelf` (100% zero-catalogue-feature blind subsurface/piedmont/remanence specialist, `37,654` dots)
   - `E3_local_unpulled_staticek_ablation` (`8` pixel-local unpulled gradients + isotropic tip halo decoded via static `E[k]` thinning, `37,654` dots)
2. **Reuse Shared Template Infrastructure Unmodified:**
   - `vendor/gems57/evaluate_holdout.py`, `vendor/gems57/metric.py`, `vendor/gems57/holdout.py`, `vendor/gems57/submission_writer.py`, `vendor/gems57/validate.py`, `vendor/gems57/uniqueness.py` verified via SHA-256 pin guard (`verify_shared_pins`).
3. **Single-Feature Leakage Canary (`AUC <= 0.90`):**
   - Every static (`32`), corroboration/cover (`2`), ablation (`8`), and fold-visible elastic (`7`) feature plane (`49` planes total) is audited individually on withheld `gems57-pooled-hide-v2` positives (`11,321` withheld positive pixels) prior to trusting any model output; any `discriminative_auc > 0.90` halts fail-closed.
4. **Two-Stage Full-Registry Uniqueness Gate (`655` Restored Accessible Upstream Rasters + Focus-9 + Local Archive):**
   - Checked on BOTH pre-placement continuous surface (`|Spearman rho| <= 0.90`) AND final discrete dots (`|Spearman rho| <= 0.90` and `<= 70%` 3-px dot overlap across comparable discrete dot fields; literal `17GEMSDOE` full-support witness audited fail-closed so `safe_to_submit` and `approved_for_weekly_slot` remain `false` unless all literal gates clear).

## 2. Mathematical & Physical Specification of New `H86Q-BFRA` Operators

1. **Broken-Plate Elastic Basement Flexural Shear (`-\partial^3_{nnn} Z_b`) & Antithetic Listric Rollover Concavity (`-\partial^2_{nn} Z_b`):**
   - Let $\hat{\mathbf{n}}_{\text{basin}} = (n_r, n_c)$ denote the smoothed unit basinward horizontal vector defined by downward Bouguer gravity gradient (`-Band 11`, `-Band 18`) corroborated by `Band 15` (`depth_to_base_surf`) thickening.
   - Along $\hat{\mathbf{n}}_{\text{basin}}$, first derivative $\partial_n Z_b$ peaks mid-ramp (`400-1,400 m` hanging-wall-ward of the fault subcrop) and $+\partial^2_{nn} Z_b > 0$ marks the convex footwall shoulder, whereas elastic broken-plate flexure across a normal fault plane produces a **vertical shear inflection break $-\partial^3_{nnn} Z_b > 0$ at the buried fault plane**, paired down-dip with **hanging-wall rollover concavity $-\partial^2_{nn} Z_b > 0$**. Both are migrated up-dip by Salem et al. (2007) vector tilt-contact `cot(dip)` (`bfra_flexural_shear_d3zb`, `bfra_flexural_shear_pullback`, `bfra_rollover_concavity_pullback`).
2. **Two-Endmember Piedmont Regolith & Hydrothermal Metasomatic Log-Ratio Unmixing:**
   - From verified `Band 6` (`TC`) and USGS GeoDAWN `geodawn_rad_u8.tif` (`K, Th, U`), compute the scale-invariant felsic-detritus vs mature-playette-clay isometric log-ratio $\psi_{\text{prov}} = \frac{1}{\sqrt{6}}\ln\!\bigl(\frac{K \cdot U}{Th^2}\bigr)$ and evaluate its signed cross-contour jump $|\nabla \psi_{\text{prov}} \cdot \hat{\mathbf{u}}_{\text{down}}|$ weighted toward low-slope (`Band 19`) piedmont aprons outside Pleistocene Lake Lahontan (`1,330 m / 1,205 m`) (`bfra_regolith_felsic_unmix_jump`).
   - Separately, isolate potassium metasomatism (adularia-sericite/illite hydrothermal upflow) via positive local residual $\max\bigl(0, \ln(K/Th) - G_{\sigma=14}(\ln(K/Th))\bigr)$ gated by shallow `Band 17` (`cond_surf`) conductivity (`bfra_hydro_k_over_th_metasom`).
3. **Oblique Vector-TMI-vs-RTP Remanence Phase Dislocation (`Bands 1, 2, 14`):**
   - Standard `RTP` (`Band 2`) assumes magnetization parallel to the modern geomagnetic dipole and phase-inverts Reverse-Polarity Oligo-Miocene tuffs and Neogene basalts in NW/NE Nevada. Normalize `Band 14` (`tmi`), `Band 2` (`rtp`), and `Band 1` (`mag_anom`) by local robust MAD and evaluate the GeoDAWN-seam-masked cross-strike phase dislocation $|\partial_n \tilde{B}_{14} - \partial_n \tilde{B}_2| \cdot \sqrt{|\nabla \tilde{B}_1| \cdot |\nabla \tilde{B}_{14}|}$, migrated up-dip by Salem `cot(dip)` (`bfra_tmi_rtp_remanence_disloc`).
4. **1-D Fault-Strand Tangent-Sharp Survival & Quadrant-Repaired Two-Regime Dinkelbach-CELF:**
   - Repair `IR-86Q-TCWB-SWAPPED-ARGS-20261026` by passing `(blind_blend, eval_union, quad_ids)` in exact signature order to `calibrate_quadrant_sparse_posterior`, restoring `NW` and `NE` blind calibration.
   - Apply cross-strike Hessian ridge sharpening (attenuating off-crest flank concavity $\partial^2_{nn} S > 0$ while preserving 1-D continuity along the Spin-2 fault tangent) prior to `exact_six_ring_self_credit` and 2-pass Dinkelbach-CELF, paired with stronger far-field (`d_vis > 10 px`) blind weight to align with the `r = +0.994` Focus-9 radial leaderboard law while keeping comparable discrete `<=90k`-dot 3-px overlap well below `0.70`.
