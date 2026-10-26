# Session `9c9712ca` — Focus-9 Executive Summary, Fleet Score Estimator, `H86R-SFG` Strike-Field Gate (Falsified), and Three-Pass Audit (`2026-10-26`)

- **Branch:** `arena/9c9712ca-gemsdoe86`
- **Lane executed (1 of 5 ranked hypotheses, 3 preregistered arms):** `H86R-SFG` — *Catalogue Strike-Field Gated Blind Potential-Field Edge Fusion*, executing the queued-but-never-implemented `H86J-SCO` proposal (`research/H86J_LSI_PREREGISTRATION.md`, rank 2) at full-footprint scale. Queue: [`registry/h86r_hypotheses_20261026.json`](../registry/h86r_hypotheses_20261026.json) · Preregistration: [`research/H86R_SFG_PREREGISTRATION.json`](H86R_SFG_PREREGISTRATION.json) · Run card: [`docs/evidence/h86r-sfg-run-card.json`](../docs/evidence/h86r-sfg-run-card.json)
- **Generated unique GeoTIFF (audit download only):** [`gems86-h86r-sfg-strikegate-37654dots-20261026T162637Z-ee3f1551-zeros.tif`](../docs/downloads/gems86-h86r-sfg-strikegate-37654dots-20261026T162637Z-ee3f1551-zeros.tif) (`sha256 b4e985310bd4b5a7ac73e56b376d4d62ea1692f8512a2f15a6d489469171c158`, 37,654 dots, 15/15 format checks PASS, `[0,1]`, 0 NaN/Inf, note ≤140 chars in writer receipt)
- **Upload status: ⛔ `DO NOT SUBMIT`** (`verdict="negative"`, `safe_to_submit=false`, `approved_for_weekly_slot=false`, `submission_slots_used=0`, `scoped_download_candidate=false` — gates G3/G4 failed, §4)
- **Prior-session next steps disposition:** H86Q-BFRA's queued `H86Q-2_PCPD` (Baranov pseudogravity) is **rejected as already implemented** by `H86M-PFTE` (`src/gems86_pfte/features.py:394`; `IR-86R-PCPD-ALREADY-IMPLEMENTED-20261026`). BFRA's prior-weighted quadrant calibration repair was reviewed and not selected (BFRA-internal, duplicate-stopped lineage); `H86Q-3_KNDS` carried forward un-run (its `dem10_chi` input is not yet hash-pinned in this repo's manifest).

---

## 1. Executive summary — Focus-9 sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`): which scored file is best, per site

Scores are `OWNER-REPORTED` rows of [`registry/prior_scores.csv`](../registry/prior_scores.csv) (no submission-page receipts exist in this repo, so nothing is `ORGANIZER-CONFIRMED`). Pixel geometry for locally held rasters was **re-measured this session** ([`docs/evidence/h86r-selector-table-20261026.json`](../docs/evidence/h86r-selector-table-20261026.json)); site `HEAD`/gate status is from the merged 2026-10-26 rev-2 forensic audit ([`SESSION_20261026_H86Q_BFRA_REVIEW.md`](SESSION_20261026_H86Q_BFRA_REVIEW.md)); all nine repos show `pushed_at` on 2026-10-26 (GitHub API, checked this session), so newer *unscored* candidates may exist that cannot be live-ranked.

| Rank | Site | Best scored submission to download (for audit) | Score (`OWNER-REPORTED`) | Locally re-measured this session (dots · overlap vs H33 · %>1 km · SGMC-PROXY-DTI) | Resubmission status |
|---:|---|---|---:|---|---|
| **#1** | GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **0.2778** | 37,654 · 1.000 (self) · 69.8% · 0.0937 | Already submitted; resubmitting the identical file would be an exact duplicate — **do not** |
| #2 | GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-...-zeros.tif` | 0.2750 | 38,854 · 0.974 · 69.7% · 0.0951 | Duplicate-lane vs H33 (>0.70); already submitted |
| #3 | GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 | 37,660 · 0.955 · 65.7% · 0.0915 | Duplicate-lane; `-nan` twin has outside-footprint NaNs |
| #4 | GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-...-nan.tif` | 0.2708 | pixel-clone of GEMSDOE28 H27-4 (40,199 · 0.954) | Exact clone of a GEMSDOE28 file |
| #5 | GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | 41,865 · 0.926 · 63.4% · 0.0945 | Duplicate-lane; already submitted |
| #6t | GEMSDOE25 | `gems25-dotted-h19-5-d2-8-...` (D28) | 0.2600 | 44,090 · 0.882 · 59.6% · 0.0937 | Duplicate-lane; already submitted |
| #6t | GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-...` (same D28 dots) | 0.2600 | same raster family as GEMSDOE25 row | Duplicate |
| #8 | GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-...-nan.tif` | 0.2477 | 60,069 · 0.885 · 59.3% · 0.1007 | Duplicate-lane; `-nan` twin |
| #9 | GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-...-nan.tif` | 0.2449 | 61,328 · 0.867 · 58.4% · 0.1020 | Duplicate-lane; best *non-lineage* Focus-9 run is `gems27-h29` = 0.2190 (overlap 0.561) |

**Obvious answer, per site and overall:** the single best *scored* file in the Focus-9 cohort (and #1 of all 124 OWNER-REPORTED claims fleet-wide) is GEMSDOE32's `h33-h33-2-b2-...-zeros` at 0.2778. Every other Focus-9 "best" is a 0.87–1.00-overlap near-clone of it. **None of these files is a legal new submission** — they were already submitted, and re-uploading any of them (or a >0.70-overlap twin) violates the uniqueness rule the owner set for this programme.

## 2. Why 0.2778 happened, and whether >0.2778 is reachable (updated proof, this session's additions)

The full DTI algebra proof is in the merged rev-2 review (§2 of `SESSION_20261026_H86Q_BFRA_REVIEW.md`): 2.8 px Poisson dotting removes ~3.4× of ribbon false-positive mass at identical kernel coverage, and pruning the 1.41–2.0 px catalogue collar (40,199→37,654 dots, min d_cat 1.41→2.24 px) removed 6.3% of pure-denominator dots, walking the lineage 0.2600 → 0.2708 → 0.2778. This session adds three measured corollaries (`IR-86R-INSTRUMENT-FLOORS-20261026`):

1. **The winning edits are invisible to our best local proxy.** H33/H27-4/D28 give bit-identical SGMC-PROXY terms because the instrument masks ≤3 px around the catalogue and each winner is the previous raster minus dots inside that shell. Any future collar/budget improvement likewise cannot be selected on SGMC.
2. **SGMC-PROXY has a 0.0754 chance floor** at this budget (seeded uniform null, measured here). Historical "SGMC wins" of +0.01–0.03 over H33 are partly spatial-spread effects.
3. **Fleet regression (n=23 strict-matched, LOO-RMSE 0.038)** — live ≈ −0.039 + 0.156·ovH33 + 0.115·SGMC + 0.215·frac>1km. Live score is dominated by overlap with H33 (Focus-9 Pearson r=0.97): deviation from H33's dots has historically *cost* score almost linearly. A candidate obeying the uniqueness rule (ovH33 ≤ 0.70) is therefore projected ≤ ~0.24 by construction of the fitted history; the best such file ever scored live is 0.2478 (GEMSDOE70 P5, OWNER-REPORTED) and the best Focus-9 one is `gems27-h29` at 0.2190. **Beating 0.2778 with a unique raster requires genuinely new hidden-fault mass that H33 misses — which no instrument in this repo can currently verify before the fact.** Claims of a projected >0.2778 unique file would be fabrication; none is made here.
4. Leaderboard context: 0.3195 and 0.4413 remain **unverified external marks quoted in owner prompts** (the PR #182 attribution of 0.3195 to GEMSDOE87 was retracted with evidence in `IR-86Q-HALLUCINATION-AND-LEDGER-REPAIR-20261026`). This session did not access DrivenData (its Terms prohibit automated access), so no leaderboard number here is ORGANIZER-CONFIRMED.

## 3. The download-decision table (the file to download, its estimated score, and uniqueness)

Repository governance: **no file is approved to upload** (`safe_to_submit=false` everywhere; slot-spending is the owner's separate DrivenData action). Within that constraint, the automated, human-inspection-free ranking of *existing downloadable candidates* by this session's frozen instruments is:

| File to download (audit) | Evidence | Estimated live score | Unique vs every locally measured discrete registry raster? | OK to submit? |
|---|---|---:|---|---|
| **Best already-scored file overall:** GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (in `data/scored_fleet/`) | 0.2778 OWNER-REPORTED (actual past submission) | 0.2778 (reported, not a projection) | No — it *is* the lineage reference; already submitted | **NO — exact duplicate if re-uploaded** |
| **Best new unique candidate in GEMSDOE86 downloads (37,654-dot class, in-support):** `gems86-h86m-pfte-blind-comonodcelf-37654dots-20261025T175515Z-04d0022f-zeros.tif` | SGMC-PROXY-DTI 0.1210 (repo-best at this budget, re-measured) | **Projection 0.167 [0.093, 0.241]** (fleet regression v2; not a score) | Yes (scoped): ovH33 0.301 ≤ 0.70; its card records 0/464 discrete firings | **NO — DO NOT SUBMIT under governance** (verdict negative; literal witness gate; selector step outstanding) |
| Runner-up unique: `gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif` | SGMC 0.0967; HOLDOUT-DTI 0.0734 (blind arm, its card) | Projection 0.172 [0.098, 0.247] | Yes (scoped): ovH33 0.339 | NO — DO NOT SUBMIT |
| **New today:** `gems86-h86r-sfg-strikegate-37654dots-20261026T162637Z-ee3f1551-zeros.tif` | HOLDOUT-DTI 0.0450 [0.034, 0.057] (n=11,321); SGMC 0.0596 | **Projection 0.162 [0.087, 0.236]** (v2) | Yes (scoped local, 76 rasters): worst discrete overlap 0.670 ≤ 0.70, ovH33 0.239, worst sampled surface ρ 0.072 ≤ 0.90 | **NO — hypothesis falsified (G3/G4 FAIL); audit only** |

Full 77-raster measurements: [`docs/evidence/h86r-selector-table-20261026.json`](../docs/evidence/h86r-selector-table-20261026.json). Estimator: [`docs/evidence/h86r-fleet-estimator-20261026-v2.json`](../docs/evidence/h86r-fleet-estimator-20261026-v2.json) (v1 superseded — 5/28 false filename matches, `IR-86R-ESTIMATOR-MISMATCH-20261026`).

## 4. H86R-SFG experiment (3 arms, preregistered, zero post-hoc retuning)

**Hypothesis.** Blind potential-field edge detectors waste most of a 37,654-dot budget on strike-discordant non-fault edges (caldera rings, shorelines, dikes, seams). Gating a 5-plane multiline-corroborated edge fusion `E` (B5 gravity slope, B3 magnetic HG, RTP gradient, B15 basement gradient, B19 slope; `E = 0.5·mean + 0.5·2nd-highest` of ranks) by spin-2 alignment `A = cos²(θ_E − θ_C)` with a 5 km-smoothed double-angle catalogue strike field (`S = E·(0.35+0.65A)`, edge strike from the verified B18/B11 gravity-gradient vector) should retain far-field parallel strands (the >1 km live-scoring population) while suppressing discordant mimics. *Named mimic:* strike-parallel unfaulted lithologic contacts/strike valleys (pass the gate); genuine perpendicular transfer faults (down-weighted to the 0.35 floor).

**Results** (`gems57-pooled-hide-v2`, 11,321 withheld positives; input hashes verified; canary worst 0.564 ≤ 0.90 PASS):

| Arm / comparator | HOLDOUT-DTI | SGMC-PROXY-DTI |
|---|---:|---:|
| E1 gated fusion (candidate) | 0.0450 [0.034, 0.057] | 0.0596 |
| E2 ungated ablation | **0.0512** [0.039, 0.063] | 0.0757 |
| E3 gated gravity-only | 0.0361 [0.026, 0.049] | 0.0204 |
| H33 visible-collar (replication check) | 0.0036 ✓ matches prior sessions | 0.0937 ✓ |
| H27-4 visible-collar | 0.0273 ✓ | 0.0937 ✓ |
| BFRA blind as-shipped | 0.0000 (artifact: min d_cat 3.16 px > kernel ⇒ TP≡0 as-is; not evidence about BFRA) | 0.0967 ✓ |
| Uniform-random null (seeded) | — | 0.0754 |

Paired E1−E2 = −0.0062 [−0.0167, +0.0041]. **Frozen gates:** G1 format PASS (15/15) · G2 canary PASS · **G3 holdout FAIL** (E1 < E2) · **G4 SGMC FAIL** (0.0596 < 0.0937, and below random) · G5 scoped uniqueness PASS (worst discrete 0.670 vs GEMSDOE85 90k crest; surface ρ sampled) · G6 fingerprint PASS (37,654 dots, min d_cat 3.16 px, 72.7% >1 km). **Verdict: negative. The orientation prior, at 5 km smoothing with a soft floor, removes real fault signal along with mimics — plausible cause: at 100 m pixels the catalogue strike field is dominated by the nearest range front, while hidden intrabasinal/accommodation strands are systematically oblique to it, and the gravity-gradient strike is noisy where B13 is smooth.** No 4th experiment was run (protocol budget).

## 5. Hypotheses queue (ranked; full text in the registry JSON)

| Rank | ID | Mechanism (layers) | Why it could catch unmapped faults | Status |
|---:|---|---|---|---|
| 1 | H86R-1_SFG | Catalogue strike-field gate × 5-plane edge fusion (B2,3,5,11,15,18,19) | Far-field parallel strands share population strike | **Executed — falsified (§4)** |
| 2 | H86R-2_DWPU | Detectability-weighted PU-HGB (negatives trusted only where B15/B19 say mapping is complete) | Stops PU from learning survey-exposure propensity | Queued; viable now (all inputs restored) |
| 3 | H86R-3_KNDS | Iso-χ knickzone back-projection (3DEP χ + B12/15/19) | Footwall χ outlives erased scarps by >0.5 Myr | Queued; needs `dem10_chi` manifest pin first |
| 4 | H86R-4_VENT_RANSAC | RANSAC alignments of GDR #1391 springs/wells/vents × B17 | Blind geothermal upflow traces buried permeable strands | Queued; low recall standalone |
| 5 | H86R-5_PCPD_REJECTED | Baranov pseudogravity cross-product | — | **Rejected: already implemented (PFTE)** |

## 6. Three-pass log, limitations, next steps

- **Pass 1 (implement + verify):** restored hash-pinned inputs (`training_features.tif 4371c82e…`, SGMC, ancestors) via the repo's own restore helpers; froze hypotheses + preregistration; implemented `src/gems86_sfg/` + `scripts/run_h86r_sfg.py` on the shared vendor evaluator/writer (no forks); ran 3 arms; serialized the unique TIFF.
- **Pass 2 (bugs/assumptions/edge cases):** caught and fixed (a) the loose filename→score matcher contaminating the estimator (v2 + IR + regression tests), (b) a parallel-edit race that silently reverted two file edits (re-applied sequentially, verified by grep + unit checks), (c) float32 soft-floor test tolerance; explained the BFRA as-is 0.0000 and the identical H33/H27-4/D28 SGMC values as instrument arithmetic, not bugs (both replicated from independent prior measurements). Registered artifact #46 (inventory, cards, auditor branch), restored the registry witness, rebuilt the site.
- **Pass 3 (full re-check):** re-ran `audit_release.py --measure-registry`, `build_site.py --check`, `check_site.py`, targeted + full `pytest`; re-read the standing prompt requirement-by-requirement (unique TIFF ✓ generated; obvious download decision ✓ §3 + site gate table; score estimate ✓ labelled projection with interval; per-site Focus-9 summary ✓ §1; no slot spent ✓).

**Limitations (explicit).** (1) No ORGANIZER-CONFIRMED score exists for anything here; DrivenData was not accessed (ToS). (2) Uniqueness is *scoped* to 76 locally restored rasters; the full ~713-raster upstream registry was not restored this session, and the literal full-support witness (17GEMSDOE) makes the unscoped gate unsatisfiable for any nonempty raster — a protocol conflict only the owner can resolve. (3) The estimator is OLS on 23 OWNER-REPORTED points with collinear predictors; its interval is a LOO-RMSE approximation, not a leaderboard interval. (4) Surface Spearman is a 400k-pixel seeded sample, not full-footprint. (5) The 419 MB feature mirror is owner-supplied and hash-pinned, not organizer-authenticated. (6) Focus-9 repos moved today; unscored new candidates there are unranked here.

**Next steps (H86S queue).** 1) Run H86R-2_DWPU (detectability-weighted PU) — all inputs already restored. 2) Pin `dem10_chi_100m_i16.tif` into the manifest, then H86R-3_KNDS. 3) Selector decision remains outstanding: if the owner ever spends a slot from this repo, §3's table is the measured ranking to start from — and the receipt must be logged before any number here is called a score.

**Official sources for manual review:** Competition & rules: https://www.drivendata.org/competitions/306/competition-doe-gems/ · Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf · Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution · USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · INGENIOUS: https://gbcge.org/current-projects/ingenious/ · EPSG:32611: https://epsg.io/32611 · GDR #1391: https://gdr.openei.org/submissions/1391 · DTI/Tversky background: https://en.wikipedia.org/wiki/Tversky_index
