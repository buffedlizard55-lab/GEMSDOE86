# Session 2026-10-27 — Focus-9 Executive Summary, H86S-DWPU (Falsified), Three-Pass Audit

- **Branch:** `arena/df922739-gemsdoe86`
- **Lane executed (1 selected of 5 ranked hypotheses, 3 preregistered arms):** `H86S-DWPU` — Detectability-Weighted PU Learning, the Rank-2 untried candidate carried in `registry/h86r_hypotheses_20261026.json` and re-ranked Rank 1 here. Queue: [`registry/h86s_hypotheses_20261027.json`](../registry/h86s_hypotheses_20261027.json) · Preregistration: [`research/H86S_DWPU_PREREGISTRATION.json`](H86S_DWPU_PREREGISTRATION.json) · Run card: [`docs/evidence/h86s-dwpu-run-card.json`](../docs/evidence/h86s-dwpu-run-card.json)
- **Generated unique GeoTIFF (audit download only):** `gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros.tif` (sha256 `123938217b733a959124578a5218c0d513e0842f2bbb4025f023ae2b829c70c9`, 37,654 dots, format/range checks PASS, values in [0,1], 0 NaN/Inf)
- **Upload status: ⛔ DO NOT SUBMIT** (`verdict="negative"`, `safe_to_submit=false`, `approved_for_weekly_slot=false`, `submission_slots_used=0`) — frozen gates G3/G4 FAIL. No slot was spent; promotion remains a separate owner/selector step.
- **Verification note (2026-10-27):** the GEMSDOE32 page was re-fetched this session: it lists the best scored file as **0.2778 OWNER-REPORT** ("no submission-page receipt linking this raster hash to the score is present in this repository") and currently marks every file DO NOT SUBMIT. This matches `registry/prior_scores.csv` (all rows OWNER-REPORTED; nothing ORGANIZER-CONFIRMED anywhere in this repo). The prompt's 0.3195 / 0.4413 / leaderboard-0.4413 marks remain unverified owner claims — DrivenData Terms prohibit automated access, so no leaderboard number here is organizer-confirmed.

---

## 1. Executive summary — Focus-9 (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`): the best submission per site, obviously

All scores are **OWNER-REPORTED** (no receipts). Local pixel geometry was re-measured in the merged H86R session (`docs/evidence/h86r-selector-table-20261026.json`) and not re-scored live here.

| Rank | Site | Best scored submission (audit download only) | Score | Overlap vs H33 · %>1 km | Resubmission status |
|---:|---|---|---:|---|---|
| **#1** | GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | 1.000 (self) · 69.8% | Already submitted — **exact duplicate if re-uploaded** |
| #2 | GEMSDOE36 | `anderson-geothermal-pinn-38854-...-zeros` | 0.2750 | 0.974 · 69.7% | Duplicate-lane (>0.70); already submitted |
| #3 | GEMSDOE28 | `h36-1-rung30-blind-r1-...-nan` | 0.2710 | 0.955 · 65.7% | Duplicate-lane; `-nan` twin has outside-footprint NaNs |
| #4 | GEMSDOE31 | `h27-4-solo-d28-...-nan` | 0.2708 | pixel-clone of GEMSDOE28 H27-4 | Exact clone across sites |
| #5 | GEMSDOE33 | `h33d-analog-tip-stepover-r30` | 0.2632 | 0.926 · 63.4% | Duplicate-lane; already submitted |
| #6t | GEMSDOE25 | `dotted-h19-5-d2-8` (D28) | 0.2600 | 0.882 · 59.6% | Duplicate-lane; already submitted |
| #6t | GEMSDOE30 | `d28-poisson300m-offcat-44090` | 0.2600 | same D28 family | Duplicate |
| #8 | GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-...-nan` | 0.2477 | 0.885 · 59.3% | Duplicate-lane; `-nan` twin |
| #9 | GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-...-nan` | 0.2449 | 0.867 · 58.4% | Duplicate-lane; best non-lineage run on that site is `gems27-h29` 0.2190 (overlap 0.561) |

**Obvious answer:** GEMSDOE32's H33 at 0.2778 is the single best scored file in the cohort. Every other Focus-9 "best" is a 0.87–1.00 3-px overlap near-clone of it and was already submitted. **None is a legal new upload.**

## 2. Why 0.2778 happened (PhD-level, bounded — not causal proof), and whether >0.2778 is reachable

DTI (alpha 0.2, beta 0.8, 300 m = 3 px triangular kernel; `vendor/gems57/metric.py`) rewards max kernel credit per truth pixel and penalises summed false-positive mass. Three measured lineage facts explain the ordering D28 0.2600 → H27-4 0.2708 → H33 0.2778:

1. **Dotting beats ribbons.** Replacing continuous ridge ribbons with 2.8 px Poisson-spaced unit dots cuts ~3.4× of redundant false-positive mass at near-identical truth coverage (one dot saturates a truth pixel's kernel; neighbours add denominator only).
2. **Collar pruning is pure denominator reduction.** H33 = H27-4's 40,199 dots minus 2,545 dots at 1.41–2.0 px from the catalogue (min d_cat 1.41→2.24 px, then 37,654 dots). Dots that close to *mapped* faults can only earn credit if a *hidden* fault lies within 300 m — on the organiser's hidden-truth set they mostly did not, so removing them raised DTI without losing coverage.
3. **Far-field mass is where the score lives.** 69.8% of H33's dots sit >1 km from the catalogue. Live score across the fleet is dominated by overlap with H33 (Focus-9 Pearson r≈0.97 in the H86R fleet regression, n=23 strict-matched, LOO-RMSE 0.038): `live ≈ −0.039 + 0.156·ovH33 + 0.115·SGMC + 0.215·frac>1km`.

**Can a unique file beat 0.2778?** Not by construction from history: any raster obeying the owner's uniqueness rule (ovH33 ≤ 0.70, surface ρ ≤ 0.90) projects ≤ ~0.24 under the fitted fleet history, and the best unique file ever scored live is 0.2478 (GEMSDOE70 P5, OWNER-REPORTED). Beating 0.2778 uniquely requires genuinely new hidden-fault mass that H33 misses — which no instrument in this repo (catalogue-hide holdout, SGMC proxy with its measured 0.0754 chance floor and ≤3 px collar blindness) can verify before the fact. Any claim of a projected >0.2778 unique file would be fabrication; none is made here. The correct programme is falsifiable lanes with frozen gates (below), not score promises.

## 3. Download-decision table (file, estimated score, uniqueness) — this session

| File to download (audit) | Evidence class | Estimated live score | Unique vs locally measured registry? | OK to submit? |
|---|---|---:|---|---|
| GEMSDOE32 `h33-h33-2-b2-...-zeros.tif` (`data/scored_fleet/`, best scored overall) | 0.2778 OWNER-REPORTED past submission | 0.2778 reported (not a projection) | No — lineage reference; already submitted | **NO — exact duplicate** |
| Best prior unique candidate: `gems86-h86m-pfte-blind-...-zeros.tif` (H86R selector, SGMC 0.1210) | SGMC-PROXY-DTI + fleet projection | 0.167 [0.093, 0.241] projection (v2, n=23) | Yes (scoped, ovH33 0.301) | **NO — governance negative** |
| **New today:** `gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros.tif` | HOLDOUT-DTI 0.0870 [0.071, 0.104] (gems57-pooled-hide-v2, 11,321 withheld) | **0.130 [0.050, 0.211] FLEET-REGRESSION-PROJECTION (n=20, LOO-RMSE 0.041) — never a score** | Yes (scoped, 74 rasters): ovH33 0.270, worst discrete 0.521 ≤0.70, worst surface ρ 0.121 ≤0.90 | **NO — DO NOT SUBMIT (G3/G4 FAIL)** |

All files pass the automated format/range validation that prevents the user-reported *"Predicted values must be in range [0, 1]"* rejection (single-band float32, EPSG:32611, 3730×3292, exact sample transform, 0 NaN/Inf, min 0.0 / max 1.0, zeros outside footprint, 0 dots on catalogue). Submission identity for the new file: name `gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros`, note (≤140 chars, in the writer receipt) `H86S-DWPU detect-weighted PU 37654d HOLD 0.0870 SGMC 0.0559 ovH33 0.270; audit, selector decides`. How-to-submit steps are on `docs/executive-summary.html`; no file is authorised until a separate selector decision plus an organiser receipt exists.

## 4. H86S-DWPU experiment (3 arms, preregistered, no post-hoc retuning)

**Hypothesis.** Standard PU learning treats deep covered basins as trusted negative evidence, suppressing exactly the unmapped faults the competition rewards. Weighting negatives by mapping completeness `c(x)=0.6·(1−rank(B15))+0.4·rank(B19)` (`w_neg=0.05+0.95c`) should recover covered-basin fault signal on 11 catalogue-free native geophysics features (HGB, 200 iters).

**Named non-fault mimic:** genuinely fault-free deep playa basins are up-weighted once their negative evidence is discounted; saline playa response mimics hydrothermal alteration.

**Results (all HOLDOUT-DTI = gems57-pooled-hide-v2, 11,321 withheld, 1,000 paired 20 km-block bootstrap):**
- E1 weighted: **0.0870 [0.0707, 0.1037]** — SGMC-PROXY-DTI 0.0559
- E2 unweighted ablation: **0.1039 [0.0877, 0.1217]** — paired Δ(E1−E2) = **−0.0169 [−0.0278, −0.0062]** (CI excludes 0, wrong direction)
- E3 weighted, no B15/B19 features: 0.0705 [0.0557, 0.0869]
- Comparators same split: H33 visible-collar 0.0036, H27-4 0.0273; SGMC H33 0.0937, random null 0.0754 (E1 below both)

**Interpretation:** detectability weighting as frozen *hurts* on catalogue-like hidden truth in every quadrant pattern that matters — consistent with the preregistered warning that holdout truth favours propensity learning, but the SGMC far-field instrument agrees (E1 0.0559 < E2 0.0816 < null-adjusted expectations), so the honest reading is falsification, not instrument artefact. **Verdict: negative.** Budget spent: 3/3 experiments. No retuning.

**Gates:** G1 format PASS · G2 canary PASS (worst discriminative AUC 0.695 ≤ 0.90, 15 planes) · G3 holdout FAIL · G4 SGMC FAIL · G5 uniqueness (scoped) PASS · G6 fingerprint PASS.

## 5. Three-pass audit

- **Pass 1 (implement + verify):** data restored hash-verified (training_features 4371c82e…, SGMC 643cbe99…, bridge pins); SGMC path bug found (`run_h86k_stdp` expects `.cache/external/`, fixed by symlink to the pinned `data/external/` file — shared tool not forked, IR flagged below); lane run end-to-end; writer validation 15/15.
- **Pass 2 (bugs/edge cases):** re-ran after the SGMC fix — holdout numbers reproduced bit-identically (0.0870/0.1039/0.0705), confirming the first run's holdout was unaffected; negative-sample dilation, footprint-chunk prediction, and tie-order emission reviewed; canary hard-stop wired before placement; uniqueness checked on the surface (pre-serialization data available in evidence) and on final dots.
- **Pass 3 (requirement recheck):** every requested artefact exists — Focus-9 per-site best table (§1), PhD H33 analysis (§2), unique TIF + obvious DO/DON'T-SUBMIT labelling (§3, site banner, README), score estimator labelled as projection (§3), hypothesis queue with layers/signature/why-unmapped/difference/cost + obtainability (registry file; Rank-5 InSAR/MT explicitly BLOCKED_SANDBOX_EGRESS, not proposed as viable), holdout-before-slot validation, run card (§6 JSON in the run-card file), tests + release audit.

## 6. Run card (summary; full JSON in `docs/evidence/h86s-dwpu-run-card.json`)

```json
{
  "hypothesis": "Detectability-weighted PU (w_neg = 0.05+0.95*c, c from B15/B19) recovers covered-basin faults vs uniform PU",
  "mechanism": "HGB (200 iters) on 11 catalogue-free native bands; positives=catalogue, 250k sampled negatives weighted by completeness",
  "named_non_fault_mimic": "Unfaulted deep playa basins up-weighted once negative evidence is discounted",
  "holdout_dti": {"class": "HOLDOUT-DTI", "evaluator": "gems57-pooled-hide-v2", "withheld": 11321, "E1": "0.0870 [0.0707, 0.1037]", "E2_ablation": "0.1039 [0.0877, 0.1217]", "paired_E1_minus_E2": "-0.0169 [-0.0278, -0.0062]"},
  "correlation_overlap_vs_registry": {"scoped_rasters": 74, "worst_surface_rho": 0.1213, "worst_discrete_overlap_3px": 0.5213, "overlap_vs_H33": 0.2703, "literal_witness": 1.0},
  "raster_sha256": "123938217b733a959124578a5218c0d513e0842f2bbb4025f023ae2b829c70c9",
  "validator": "15/15 PASS: no NaN/Inf, values in [0,1], EPSG:32611, 3730x3292, exact sample transform, 0 catalogue dots",
  "submission_name": "gems86-h86s-dwpu-37654dots-20261027T172648Z-ae0c897b-zeros",
  "verdict": "negative — DO NOT SUBMIT; 0 slots used"
}
```

## 7. Irregularities flagged

- **IR-86S-SGMC-PATH-20261027:** `scripts/run_h86k_stdp.evaluate_sgmc_proxy` silently returns `SGMC_NOT_PRESENT` when `.cache/external/derived_sgmc_faults_100m_u8.tif` is absent, even though the pinned file lives at `data/external/`. First H86S run crashed on the missing `scores` key *after* holdout (holdout reproduced identically on re-run). Workaround is a symlink; the shared helper should resolve the pinned `data/external/` location or fail loudly. Not privately forked.
- **Surface-check timing:** per protocol the surface ρ check should precede placement; in this runner the sampled surface scan is computed after final training but before serialization (dots are emitted in memory only; the TIFF is written only if G5 passes). Recorded honestly; no gate was bypassed.
- **Estimator refit n=20** (vs H86R v2 n=23): strict matching over the 74 locally present rasters only; coefficients differ slightly (−0.038, 0.147, 0.093, 0.225). Projections remain fleet-history regressions, never scores.

## 8. Next steps (no slot without beating holdout best + selector step)

1. Execute queued **H86S-2_KNDS** iso-chi back-projection (pin `dem10_chi` 8897ba9c… first) — the only queued mechanism that relocates signal *to* the fault instead of reweighting pixels.
2. Fix the SGMC path resolution upstream in `run_h86k_stdp` (or a shared helper) so future lanes cannot silently lose the SGMC instrument.
3. Selector step (owner): if any existing unique file is ever slot-tested, PFTE-blind remains the SGMC-best candidate; log the organiser receipt in `ledger/submissions.csv` before any further slot.
