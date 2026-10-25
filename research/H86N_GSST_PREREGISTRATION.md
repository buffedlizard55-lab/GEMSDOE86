# H86N-GSST Preregistration — 2026-10-25

Frozen before any holdout evaluation or dot placement.

## 1. Context & Selection from Queue
In `registry/followup_hypotheses_20261025.json`, three native-band geological hypotheses were queued:
1. `BMR` (basement-interface gravity mass-balance residual) — executed in PR #157 (`H86M-BMR`), falsified (`HOLDOUT-DTI = 0.0220 [0.0086, 0.0384]` vs raw gravity control `0.0364`).
2. `GSST` (gravity step-versus-compact-source shape test) — **unexecuted prior to this session**.
3. `CNT` (conductivity-neck topology conditioned on dilatation) — executed in PR #157 (`H86M-CNT`), falsified (`HOLDOUT-DTI = 0.0408 [0.0257, 0.0575]`, paired CIs cross zero).

We therefore preregister and execute **Lane `H86N-GSST`** (Rank 1 in `registry/h86n_hypotheses.json`).

## 2. Physical Hypothesis & Native Layers
- **Layers (native `training_features.tif`, SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`):**
  - Band 13 (`iso_grav_anom`): Isostatic residual gravity anomaly $g$.
  - Band 5 (`iso_grav_anom_slope`): Unsigned 2-D horizontal gravity gradient magnitude $|\nabla_H g| = \sqrt{g_x^2 + g_y^2}$.
  - Band 11 (`iso_grav_anom_vg`): Pixel-verified signed southward directional gravity derivative $+\partial g / \partial \text{row}_{\text{south}} = -g_y$ (`src/gems86/io.py`).
  - Band 18 (`iso_grav_anom_hg`): Pixel-verified signed eastward directional gravity derivative $+\partial g / \partial x_{\text{east}} = +g_x$ (`src/gems86/io.py`).
- **Physical signature (`GSST`):**
  At frozen scales $\sigma \in \{3.0, 6.0\}\text{ px}$ ($300\text{ m}, 600\text{ m}$):
  1. Let the smoothed horizontal gravity gradient vector be $\mathbf{u}_\sigma = (G_\sigma * \text{Band 18}, G_\sigma * \text{Band 11})$ in $(\text{col}, \text{row})$ pixel coordinates, with magnitude $M_\sigma = \|\mathbf{u}_\sigma\|_2 + \epsilon$ and unit normal $\hat{\mathbf{n}}_\sigma = (n_x, n_y) = \mathbf{u}_\sigma / M_\sigma$, unit strike $\hat{\mathbf{s}}_\sigma = (-n_y, n_x)$.
  2. **Cross-strike step flank persistence ($S_{\text{step},\sigma}$):** Sample the projected normal gradient $\mathbf{u}_\sigma(\mathbf{x} \pm \delta \hat{\mathbf{n}}_\sigma) \cdot \hat{\mathbf{n}}_\sigma(\mathbf{x})$ at cross-strike offset $\delta = \sigma$. Over an extended one-sided step fault, both flanks have positive normal gradient in the same direction as the crest ($\min(g_{n,+\delta}, g_{n,-\delta}) / M_\sigma > 0$), whereas a symmetric bump/dike reverses gradient sign across the crest.
  3. **Along-strike extended coherence vs. compact radial curvature ($C_{\text{ext},\sigma}$):** Compare along-strike gradient persistence $\frac{1}{2}(\mathbf{u}_\sigma(\mathbf{x} + \sigma \hat{\mathbf{s}}_\sigma) + \mathbf{u}_\sigma(\mathbf{x} - \sigma \hat{\mathbf{s}}_\sigma)) \cdot \hat{\mathbf{n}}_\sigma(\mathbf{x}) / M_\sigma$ against the compact-source radial curvature $|\nabla \cdot \hat{\mathbf{n}}_\sigma| = |\partial_x n_x + \partial_y n_y|$.
  4. Combine scales:
     $$\text{GSST} = 0.6 \cdot \text{rank}\!\left(M_3 \cdot \max(S_{\text{step},3}, 0) \cdot \max(C_{\text{ext},3}, 0)\right) + 0.4 \cdot \text{rank}\!\left(M_6 \cdot \max(S_{\text{step},6}, 0) \cdot \max(C_{\text{ext},6}, 0)\right)$$
- **Named non-fault mimic:** Elongated lithologic/intrusive contact or basin-margin alluvial density boundary producing a one-sided density step without brittle fault offset.

## 3. Experimental Arms (Budget = 3 arms, 1 run)
- **`H86N_GSST` (Candidate E1):** Multi-scale step-versus-compact shape score, emitted via greedy $2.8\text{ px}$ Poisson-disc spacing at $37,654$ dots with $>3.0\text{ px}$ off-catalogue collar (visible-only catalogue in holdout folds; full catalogue in final emission).
- **`E0_raw_grav_slope` (Control 1):** Raw horizontal gravity gradient magnitude (`Band 5`, `iso_grav_anom_slope`) at identical $37,654$-dot budget and $2.8\text{ px}$ spacing.
- **`E2_compact_curv` (Control 2):** Compact-source curvature-weighted gradient (`Band 5` weighted by $|\nabla \cdot \hat{\mathbf{n}}_3|$) at identical $37,654$-dot budget and $2.8\text{ px}$ spacing.

## 4. Validation & Promotion Gates (Fail-Closed)
1. **Leakage canary:** Each individual feature tested on withheld positives vs active negatives must have $\text{AUC} \le 0.90$.
2. **Holdout evaluation (`gems57-pooled-hide-v2`):** Buffered whole-component hide-and-recover (`seed=20`, `hide_frac=0.20`, `buffer_px=3`, `boundary_px=12`, `11,321` withheld positives, `1,000` physical $20\text{ km}$ block bootstrap draws). Candidate `H86N_GSST` must beat BOTH `E0_raw_grav_slope` and `E2_compact_curv` with paired 95% CIs strictly above zero (`ci95[0] > 0`), AND beat the repository's same-split strict-LOQO benchmark (`0.1599`) before any promotion or slot recommendation.
3. **Uniqueness:** Surface Spearman $|\rho| \le 0.90$ and final-dot 3-px forward overlap $\le 0.70$ against local dot-field registry rasters (`PA-86-01`), plus mandatory remeasurement against the pinned literal full-support witness (`17GEMSDOE`, `ab0a0a62...`).
4. **Format validation:** Shared `gems57.validate.validate` and `gems57.gates.format_report` (15/15 checks: single-band `float32`, `EPSG:32611`, `3730x3292`, values in `[0, 1]`, 0 NaN/Inf, 0 dots on catalogue, zeros outside footprint).
5. **Slot policy:** `submission_slots_used = 0`, `approved_for_weekly_slot = false`, `safe_to_submit = false`.
