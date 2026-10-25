# H86M-BMR preregistration (frozen before scoring, 2026-10-25)

Lane (single method paragraph): Basement-interface gravity mass-balance residual.
From native band 13 (`iso_grav_anom`) and band 15 (`depth_to_base_surf`) only:
smooth depth at sigma 3 and 8 px, fit an unsupervised robust linear slab model
`grav ~= a*depth_smooth + b` on footprint pixels (no catalogue/label input at any
stage), residual = observed − forward. Surface = footprint rank-percentile blend
0.6·|∇residual(σ3)| + 0.4·|∇residual(σ8)|. Emit exactly 37,654 unit dots,
spacing ≥2.8 px, catalogue collar >3 px, via the shared greedy used by H86L.
Controls (same budget/emission): E0 |∇ band13|, E1 |∇ band15|.
Evaluation: shared `gems57` hide-and-recover (`buffered_component_draw`, seed 20,
hide 0.20, buffer 3, boundary 12), pooled DTI α=0.2 β=0.8 300 m triangular kernel,
evaluator `gems57-pooled-hide-v2`; paired block-bootstrap CI vs both controls.
Canary: each single feature AUC ≤0.90 required. Uniqueness (PA-86-01 like-for-like):
surface Spearman ≤0.90 vs every locally measured registry raster (300k footprint
sample, disclosed) and final-dot Spearman + forward 3 px overlap ≤0.70 vs every
dot field in `data/scored_fleet/` + `docs/downloads/`. Literal full-support-witness
reading reported side-by-side, never hidden.
Named non-fault mimic: lateral sediment-density change / smoothing error in the
gravity-derived basement surface (band 15 is gravity-derived → circularity risk
is the falsifier: BMR must beat BOTH raw-gravity and depth-gradient controls).
Verdict `promote` only if: paired CI low >0 vs both controls, canary pass,
uniqueness pass, writer/validator pass. Otherwise `negative` = DO NOT SUBMIT.
No weekly slot is picked by this lane (protocol rule 6). Budget: 1 experiment.
