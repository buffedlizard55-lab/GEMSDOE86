# H86L-FMC review — 2026-10-25 (3 passes)

## Answer: why did H33 (`h33-h33-2-b2`, GEMSDOE32) reach 0.2778 (OWNER-REPORTED, 0 organizer receipts in `ledger/submissions.csv`)?
Verified in-repo (prior sessions, re-cited not rerun): H33 = its D28 parent (40,199 dots, 0.2708 owner-reported) minus 2,545 dots in the `1 < d_cat ≤ 2 px` collar (`research/session-679d92e7-h33-lineage.json`). Under DTI (α=0.2, β=0.8, 300 m triangular kernel; `vendor/gems57/metric.py`), a dot farther than 3 px from any hidden-fault pixel earns zero truth credit but pays FP mass; a redundant dot near an already-covered truth pixel earns ~0 marginal `dT` yet pays `α(1−k)`. Pruning low-marginal-credit collar dots therefore *can* raise DTI. It does **not** prove 2 px is optimal, nor explain the private score causally: hidden faults near pruned dots would be hurt. The same algebra bounds ambition: at DTI 0.2778, +0.01 needs ≈418 kernel-credit units ≈ 42 km of newly hit fault trace (SLOT_PLAN §D) — reallocation of existing dots cannot plausibly beat 0.4413 (current leaderboard claim in prompt, unverified); only new fault evidence can.

## This session's lane (preregistered `registry/h86l_hypotheses.json`)
Ranked candidates: (1) **H86L-FMC** fleet minority-consensus 2–8/25 (only lane executable here); (2) H86L-SOLO anti-consensus (not run, budget); (3) BMR basement gravity residual and (4) GSST step-vs-compact — both **blocked**: `training_features.tif`/`.cache` feature stack absent in this checkout (IR-86L-01, flagged below). Free official source to unblock: DrivenData data tab (login-gated, https://www.drivendata.org/competitions/306/competition-doe-gems/data/) or the Dropbox mirror pinned in `scripts/restore_data.py`; obtainable only with DrivenData auth — not obtainable autonomously here.

## Result (experiment 1 of ≤3; stopped per lane rule 1)
- Script `scripts/run_h86l_fmc.py` (shared template only). 37,654 dots, greedy 2.8 px, >3 px off-catalogue.
- **HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld positives) = 0.0000 [0.0000, 0.0000]**, paired Δ vs H33 control −0.0037 [−0.0044, −0.0030]. Two independent falsifiers: (a) support-surface canary AUC 0.436 (<0.5, anti-predictive); (b) by construction dots >3 px from all catalogue can receive no kernel credit on catalogue-hide truth — the *surface* check (AUC, pre-placement, per protocol) already condemned it.
- **Uniqueness:** max |Spearman| 0.787 (<0.90 pass) but **3-px dot overlap 0.886 > 0.70 vs GEMSDOE63** → duplicate gate fires; logged as duplicate, lane stopped.
- **Validator:** 15/15 PASS (EPSG:32611, 3730×3292, float32, {0,1}, 0 NaN, 0 on catalogue). Format-valid ≠ submit-worthy.
- Verdict **negative, DO NOT SUBMIT**, 0 slots. SHA-256 `5bacedbe67a8000dd8bcb5f375c089cef71aba7172f482ff05a76363a04a502a`.

## Pass 2/3 checks
Writer receipt + ZIP verified; note 92 ≤140 chars; site banner states DO NOT SUBMIT at top visibility; no score labelled organizer-confirmed (0.2778/0.4413 remain owner/user-reported).

## Irregularities flagged
- **IR-86L-01:** shared cached feature stack absent (`.cache` excluded from snapshot); all native-band geological lanes (incl. queued BMR/GSST) irreproducible in this checkout until `scripts/restore_data.py` is run with DrivenData/Dropbox access.
- **IR-86L-02:** fleet-minority cells are anti-predictive of withheld catalogue faults (AUC 0.436) — fleet corroboration concentrates on/near catalogue ancestry, not on hidden faults.
