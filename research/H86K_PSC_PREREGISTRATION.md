# H86K-PSC preregistration (frozen before any holdout score)
Lane: persistent potential-field saddle connectors. Bands verified vs src/gems86/io.py BANDS: 2=rtp, 13=iso_grav_anom, 15=depth_to_base_surf (15 is gravity-derived, NOT independent corroboration — used only as concordance multiplier and disclosed).
Arms (<=3 experiments): E1 PSC surface; C1 gradient-ridge control (gradient magnitude of same two fields); C2 = E1 without depth concordance (ablation). Same allocator (static E[k], spacing 2.8px, catalogue collar >3px), same per-fold budgets.
Holdout: gems57 buffered whole-component LOQO v2 (holdout.buffered_component_draw, seed 20, hide 0.20, buffer 3px), evaluator gems57-pooled-hide-v2, pooled DTI alpha0.2 beta0.8 300m triangular, 1000-draw paired 20km block bootstrap.
Canary: every feature plane alone AUC vs withheld truth on fold-active pixels; >0.90 = leakage stop.
Allocator final: exact CELF (gems86_mcsp.celf), 37,654 dots, spacing 2.8, collar 3.0.
Uniqueness: PA-86-01 like-for-like: Spearman rho<=0.90 all measured rasters, 3px dot overlap<=0.70 dot-fields; literal continuous-witness reading reported separately. Scope = locally available scored_fleet + docs/downloads; incomplete scope disclosed, never called complete.
Mimic: intrusive contacts / erosional basement relief saddles.
Verdict rule: promote only if E1 pooled HOLDOUT-DTI > both controls with paired CI and uniqueness+format pass; else negative. safe_to_submit requires format+uniqueness pass; approved_for_weekly_slot stays false (separate selector).

AMENDMENT A1 (before Exp2 scoring): Exp1 E1=0.0371 < C1 ridge=0.0403 (paired CI includes 0) — pure saddle falsified as standalone. Exp2 tests preregistered refinement within same lane: saddle-ridge junction surface sqrt(E1_psc * C1_ridge), same holdout/allocator/budget. Canary bug in Exp1 (sampling mask excluded hidden catalogue pixels, AUC=NaN) fixed: sample from footprint minus VISIBLE catalogue.
