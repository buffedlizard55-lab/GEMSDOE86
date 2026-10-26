# Executive Summary — Highest-Scoring Submissions Across 9 Requested GEMSDOE Sites

**Date:** 2026-10-26 UTC  
**Branch:** `arena/9182dcd2-gemsdoe86`  
**Lane:** H86O-RFGC (Ridge-Flexure Geothermal Concordance)  
**All scores below are OWNER-REPORTED (no submission-page receipt located) — never ORGANIZER-CONFIRMED — except where noted as HOLDOUT-DTI.**

## Quick Answer — Which File Is Best to Submit?

**For the DrivenData leaderboard (|DTI = Tversky alpha=0.2, beta=0.8, 300m|):**

| Rank | Site | Submission artifact | OWNER-REPORTED score | Verdict for submission |
|------|------|---------------------|----------------------|------------------------|
| **1** | **GEMSDOE32** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (37,654 dots, zeros) | **0.2778** | **Highest in the 9-site set; but OWNER-REPORTED only — no receipt, and forensic analysis shows it is 100% identical to GEMSDOE28 after collar pruning (see below). Use with caution.** |
| 2 | GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` (38,854 dots, zeros) | 0.2750 | Contains 100% of GEMSDOE28 R0 verbatim + 1,200 extra dots (97.40% 3-px overlap with H33). Not independent. |
| 3 | GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` (37,660 dots, nan) / `h38-1-hf-euler-r30-r1` (37,??) | 0.2710 / 0.2707 | Family parent of H33; 40,199-dot R0 is ancestor. |
| 4 | GEMSDOE28 | `h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan` (40,199 dots) | 0.2708 | = GEMSDOE31 `h27-4-solo-d28` (same file, same score) — duplicate across sites |
| 5 | GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` (40,199 dots) | 0.2708 | Duplicate of above |
| 6 | GEMSDOE28 | `h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan` | 0.2649 | Same H19-5/D2.8 lineage |
| 7 | GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` (41,865 dots) | 0.2632 | Same H19-5 lineage, 41k variant |
| 8 | GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` (dotted H19-5, d=2.8) | 0.2600 | = GEMSDOE30 `d28-poisson300m-offcat` (same 0.2600) — same method |
| 9 | GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` (44,090 dots) | 0.2600 | = GEMSDOE25 (same score, different density) |
| — | GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Lower; earlier in same lineage |
| — | GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Topographic gap closure, distinct but lower |

**Bottom line:** GEMSDOE32 H33 is numerically highest (0.2778) in this 9-site cohort, but it is **not an independent model** — pixel-exact forensic comparison of pinned GEMSDOE28 (40,199 dots, 0.2708) and GEMSDOE32 H33 (37,654 dots) shows **0 differing cells across 12,279,160 pixels after deleting the 2,545 dots in 1.0 < d_cat ≤ 2.0 collar** (`docs/evidence/` in prior sessions). All scores >0.26 in this set lie in the **single H19-5/D2.8 Poisson-disc lineage** (92.64%–100% 3-px overlap). No ORGANIZER-CONFIRMED receipt exists for any of these 9.

**If you must submit one of these 9 today:** GEMSDOE32 H33 (`h33-h33-2-b2`) is the best **OWNER-REPORTED** number, but submit the **zeros-encoded twin** (not nan) to avoid portal nodata ambiguity. The file must be re-validated locally first (no NaN inside footprint, values in [0,1]).

## Why Did GEMSDOE32 H33 Get 0.2778?

**PhD-level forensic analysis (see `research/H33_INTERPRETATION_REVIEW.md` and `research/H33_ANALYSIS.md`):**

1. **Metric asymmetry:** Under 300m DTI (alpha=0.2, beta=0.8), TP_w = max over 3-px disk (credit for covering truth), FP_w = sum over all positive pixels (cost per dot). Spacing dots near kernel radius (~2.8 px vs 3 px) reduces redundant FP mass without losing TP — but disks still overlap (separation < 2R = 6 px), so credit is max, not additive.

2. **Lineage:** H19-5 (2019-2020 INGENTRUE/UNR powerlaw-budget multiline openness) was a strong continuous ridge surface (~0.1922). GEMSDOE24/25 dotted it to D1.5/D2.8 Poisson-disc (~0.2477–0.26). GEMSDOE28's R0 (40,199 dots, D2.8) hit 0.2708. GEMSDOE32 **pruned 2,545 near-catalogue collar dots (1 < d_cat ≤ 2.0)** and kept 37,654 — a +0.0070 lift to 0.2778.

3. **Why collar pruning helped (but not proof of zero credit):** Off-catalogue dots within 1-2 px of mapped faults are likely to be near visible traces (penalized as FP if no hidden truth nearby). Removing them reduces FP without much TP loss *if* hidden truth is sparse near mapped faults. However, an off-catalogue dot in a 2-px collar **can still recover a hidden fault** (only mapped pixels are masked, not their 300m kernel), so "0% of removed dots had credit" is false — it's a plausible FP reduction, not proof.

4. **Can we beat 0.2778?** Under same lineage, density alone cannot: GEMSDOE28 40k→37.6k pruning helped, but 44k variants (GEMSDOE30 0.2600) score lower, and 38,854 (GEMSDOE36 0.2750) is 97.4% H33. **Beating H33 requires a new geological signal, not re-spacing the same H19-5 surface.** Our HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld, 155 clusters) for H33-family controls is ~0.10–0.13 with paired CI crossing zero — no validated improvement over the lineage has been established in GEMSDOE86 holdout. A new lane must find **unmapped geology** (see 5 hypotheses below).

5. **Leaderboard context:** Prompt claims conflicting "current high" 0.3195 and 0.4413 — both are **OWNER-REPORTED, unverified here**, not ORGANIZER-CONFIRMED. No projection from holdout to leaderboard is valid.

## 5 Candidate Geological Hypotheses (ranked, not yet all run)

| Rank | ID | Layers | Physical signature (transform) | Why off-catalogue | Differs from repo |
|------|----|--------|-------------------------------|-------------------|-------------------|
| **1** | **H86O-RFGC** | Bands 5 (grav slope) × 19 (det slope) × 15 (depth 0.2–1.2km) × 8 (dilatate) | Normalized coincidence S=norm(B5)×norm(B19) depth-gated, ReLU(B8) modulated, Gaussian curvature filter | Low-throw piedmont scarplets (<1m) buried by alluvium: weak B19 + B5 individually sub-threshold, jointly diagnostic at basin margins | No lane combined B5×B19; prior used B5 alone (GSST) or B19 alone (scarp) |
| 2 | H86O-MDCT | Bands 2 (RTP) + 9 (tmi_vg) + 17 (cond) + 8 (dilatate) | Band-pass negative RTP trough (12px-30px) flanked by cond walls | Hydrothermal demagnetization + smectite clay walls along active conduits, no scarp | Prior used positive magnetic highs; none targeted negative troughs |
| 3 | H86O-CEST | Bands 4/7/8 (geodetic) + 5 (grav) | Finsler metric from strain invariants, Riedel R/R' anisotropic geodesics | Strain transfer via conjugate meshes, no single scarp continuity | Prior pointwise Kostrov at fixed azimuth; this is non-local transport |
| 4 | H86O-LIDM | USGS 3DEP 1-m DEM tiles (external) + B12/19 | Signed 5-25m cross-strike curvature across ≥3 watersheds | 0.3–1.5m scarps smoothed in 30-100m DEMs, clean at 1-m | Zero lanes ingest native 1-m tiles |
| 5 | H86O-OPIS | NASA OPERA InSAR DISP-S1 (external) + B4/8 | 30-m LOS velocity steps + seasonal phase jumps | 15-30km GPS grids cannot resolve 100-m fault hydrology | No lane ingests InSAR |

**Top candidate H86O-RFGC was validated in this session** (below). Ranks 4–5 require external data not in sandbox (egress allowlist: only github.com, pypi.org, etc.; 3DEP/OPERA must be mirrored on unrestricted workstation first).

## This Session's Validation (H86O-RFGC)

- **Leakage canary (4 surfaces, 11,321 withheld, 300k negatives):** max AUC 0.5912 ≤ 0.90 — **PASS** (no catalogue leakage)
- **HOLDOUT-DTI (gems57-pooled-hide-v2, 11321 withheld, 155 spatial clusters, 1000 bootstrap):**
  - H86O-RFGC = **0.0000 [0.0000, 0.0000]** — tpw 0.0, fpw 35421, fnw 11321
  - E1 grav-only = 0.0000, E2 topo-only = 0.0000, E3 nodepth = 0.0000
  - Paired deltas vs all controls = 0.0000 [0.0000,0.0000] — **NEGATIVE** (falsified on this holdout; no better than controls, worse than random 0.044 on single fold)
- **Registry (sample 20 of 41 local TIFFs):** max 3-px overlap <0.70 (to be fully measured via `audit_release.py --measure-registry`)
- **Validator (local format/range preflight):** **15/15 PASS** — single-band float32, 3730×3292, EPSG:32611, exact sample_submission transform, **0 NaN, 0 Inf, min 0.0 max 1.0, 0 outside-footprint mass, 0 dots on catalogue**
- **Fix for portal error "Predicted values must be in range [0, 1]":** This TIFF is all-finite zeros inside footprint, values strictly in [0,1] — the validator that previously failed now passes; the portal class of error is excluded by fail-closed writer (no clipping/repair).

**Verdict:** NEGATIVE — do not submit to weekly slot. The concordance hypothesis is falsified on hide-and-recover; it suppresses too much of the truth (0 TP). Next: relax depth gate, test Band5 or Band19 alone, or try H86O-MDCT. The file is a **research/audit download** proving format compliance, not a promotion.

## Download

- **New unique TIFF (2026-10-26):** `gems86-h86o-rfgc-rfconcord-37654dots-20261026T002649Z-f886cfbe-zeros.tif` — SHA256 `96b0b3fb9c99e967e1cd095a2e4da9bba60d87257400d9798154aae09f4e1d4a`, 37,654 dots at 2.8px, EPSG:32611 3730×3292, 15/15 local checks PASS
- **One-TIFF ZIP:** `gems86-h86o-rfgc-rfconcord-37654dots-20261026T002649Z-f886cfbe-zeros.zip`
- **Writer receipt (SHA/ZIP/note):** `gems86-h86o-rfgc-rfconcord-37654dots-20261026T002649Z-f886cfbe-zeros.json`
- **Run card (HOLDOUT-DTI, canary, validator):** `docs/evidence/h86o-rfgc-run-card.json`
- **Preregistration (frozen before scoring):** `research/H86O_RFGC_PREREGISTRATION.md`
- **Hypothesis queue (5 ranked):** `registry/h86o_rfgc_hypotheses.json`

**Is it OK to download and submit?** Download for **audit only**. It is **format-valid** (fixes the [0,1] portal error), **byte-unique**, but **scientifically negative** on holdout (0.0) and has **not passed full 690-raster registry + selector** — so **DO NOT SUBMIT to DrivenData weekly slot**. Promotion is a separate selector step within weekly cap.

## Submission Procedure (for a future POSITIVE file)

1. **Download:** Get the `*.tif` (not zip) from the executive summary — ensure filename ends in `-zeros.tif` (all-finite, outside-footprint zeros; NaN-encoded portal handling is unproven — IR-57-NAN-02)
2. **Validate locally:** `python -m gems57.validate docs/downloads/<your>.tif` must show `all_checks_passed: true`, `range_0_1_guaranteed: true`, `no_nan_anywhere: true`, `outside_footprint_zero: true`
3. **Check uniqueness:** `python scripts/pa86_chance_overlap.py` and `scripts/check_h86e_registry.py` must show 0 informative firings >0.70 and rho ≤0.90
4. **Submit:** On https://www.drivendata.org/competitions/306/competition-doe-gems/data/ → "New submission" → choose the `.tif` (or its one-TIFF `.zip`), paste **submission name** (filename without extension) and **note** (≤140 chars, e.g., `H86O-RFGC ridge-flexure 37654d HOLDOUT 0.0000 negative`) — but **never submit a NEGATIVE file**; wait for a `promote` verdict.
5. **Ledger:** If you do submit a promote file, log the organizer receipt in `ledger/submissions.csv` (ORGANIZER-CONFIRMED score only).

