# Frozen Preregistration: Lane `H86K-STDP` (2026-10-25)

- **Branch:** `arena/8114f7b4-gemsdoe86`
- **Frozen timestamp (prior to implementation):** `2026-10-25T13:56:00Z`
- **Machine-readable preregistration:** [`research/H86K_STDP_PREREGISTRATION.json`](H86K_STDP_PREREGISTRATION.json)
- **4-Hypothesis Queue:** [`registry/h86k_hypotheses.json`](../registry/h86k_hypotheses.json) (`H86K-STDP` Rank 1, `H86K-CWQA` Rank 2, `H86K-BFAH` Rank 3, `H86K-NVGS` Rank 4 egress-blocked USGS ScienceBase `10.5066/P9BA3684`)

## 1. Single-Lane Method Paragraph (Protocol Rule 1)

`H86K-STDP` computes multi-altitude 2-D FFT harmonic upward-continued Salem–Fairhead (2007) tilt-angle zero-contour sharpness and lateral dip-migration ($z_0 = 100\text{ m}$ vs. $z_1 = 400\text{ m}$) on reduced-to-pole magnetics (`B2 rtp`) and isostatic gravity (`B13 iso_grav_anom`, vector horizontal gradient `+B18, +B11`), then bilinearly pulls back buried gravity, RTP, 2-D Riesz monogenic step, and narrow MT conductive-gouge neck (`B17 cond_surf`) planes up-dip along the footwall-directed basin-thickness vector ($-\nabla Z_b$) by $\Delta s = \operatorname{clip}((Z_b/100)\cot 60^\circ, 0, 8\text{ px})$ onto near-surface fault emergence. Simultaneously, it extracts intrabasin rollover keystone curvature, aseismic geodetic-minus-seismic creep deficit (`B4, B7, B8` minus `B16`), GeoDAWN survey-seam-vetoed (`acquisition_block_id_100m.tif`) and Lahontan-deconfounded `K/eTh` and `U/eTh` alteration steps, 10 m DEM quantile-debiased 3DEP 1 m LiDAR scarps + fluvial $\chi$ knickzones, and up-hydraulic-head advected DOE GDR `#1391` Fournier silica/cation thermal disequilibrium ($\max(T_{\text{qtz}}, T_{\text{chalc}}, T_{\text{cat}}) - T_{\text{meas}}$), 2-m probe thermal walls (`3,800` probes), and paleo-sinter travertine vents (`726` sites; `dist_known_fault_px` strictly banned). Using zero raw regional levels, quadrant-IQR calibrated convex fault posteriors across strict 4-fold Leave-One-Quadrant-Out (`LOQO`) spatial cross-fitting fused via Noisy-OR with cross-component Pollard–Segall fracture lobes, `H86K-STDP` allocates `37,654` unit dots (`d_min = 2.8 px`, `d_cat > 3.0 px`) via **Exact 6-Ring Bernoulli Survival Supremum Self-Credit Dinkelbach Fractional-Programming CELF**.

## 2. Mathematical Formulation Frozen Prior to Coding

1. **Multi-Altitude Salem–Fairhead Tilt & Up-Dip Pullback:**
   $$\theta(x; z) = \arctan\!\left(\frac{\partial_z \Phi(x; z)}{\|\nabla_H \Phi(x; z)\|_2 + \varepsilon}\right), \qquad S_{\text{Salem}}(x) = \operatorname{sech}^2\!\left(\frac{\theta(x; z_0)}{0.35}\right)\|\nabla_H \theta(x; z_0)\|_2,$$
   $$\Delta\theta_{\uparrow}(x) = \bigl|\theta(x; z_1) - \theta(x; z_0)\bigr|\,\operatorname{sech}^2\!\left(\frac{\theta(x; z_0)}{0.50}\right), \qquad \mathcal{P}_{\text{updip}}[F](\mathbf{x}) = F\!\bigl(\mathbf{x} + \Delta s(\mathbf{x})\,\hat{\mathbf{u}}_{\text{downdip}}(\mathbf{x})\bigr).$$

2. **Exact 6-Ring Bernoulli Survival Supremum Self-Credit & Submodular Dinkelbach-CELF:**
   Let $1 = w_1 > w_2 > \dots > w_6 > w_7 := 0$ be the 6 distinct nonzero radial weights of the official $300\text{ m}$ ($3\text{ px}$) triangular kernel `OFF_K`. Under $G(x) \sim \operatorname{Bernoulli}(p(x))$:
   $$k_{\text{self}}^{\star}(y) = \mathbb{E}\!\left[\max_{j:\,\|\delta_j\|_2 \le 3} G(y + \delta_j)\,K(\delta_j)\right] = \sum_{r=1}^{6} (w_r - w_{r+1})\!\left(1 - \prod_{j:\,K(\delta_j) \ge w_r} \bigl(1 - p(y + \delta_j)\bigr)\right).$$
   At Dinkelbach ratio $\lambda^{(t)} \in (0, 1)$, lazy-greedy CELF maximizes the exact submodular Lagrangian gain:
   $$g_\lambda(y \mid S) = (1 - 0.2\,\lambda)\,\Delta T(y \mid S) - 0.2\,\lambda\,\bigl(1 - k_{\text{self}}^{\star}(y)\bigr).$$

## 3. Preregistered 3-Experiment Budget & Fail-Closed Gates

- **Arms (`3` total, `<= 2` hours):** `E1_stdp_dinkelbach_celf` (primary candidate), `E2_stdp_blind_dinkelbach_celf` (100% zero-catalogue blind specialist), `E3_pixel_local_staticek_ablation` (pixel-local un-pulled-back + isotropic thermal + static `E[k]` ablation).
- **Leakage Canary (Rule 4):** Single-feature `max(AUC, 1 - AUC) <= 0.90` across all 24 static, 1 analytical corroboration, 8 ablation, and 5 fold-visible planes before trusting any holdout result.
- **Uniqueness & Fail-Closed Publication Gate (Rules 1, 5, 6 & `AGENTS.md` Rules 10–15):** Pre-placement surface and final-dot checks run on the full restored registry (`655` upstream blobs + local fleet/downloads). Any literal or completeness failure forces `verdict = "negative"`, `decision = "DO NOT SUBMIT"`, `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`.
