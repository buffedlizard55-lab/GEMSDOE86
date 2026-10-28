# Session review — 2026-10-27, branch `arena/fb68389e-gemsdoe86`: nine-site audit, H87-FCB candidate, decision

**Decision: DO NOT SUBMIT.** `safe_to_submit = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0`. No organizer receipt exists for any file in this session.

Evidence labels used below: **MEASURED** (computed from bytes in this session), **HOLDOUT-DTI** (gems57-pooled-hide-v2, withheld positives, cell-bootstrap 95% CI), **OWNER-REPORTED** (from `registry/prior_scores.csv`, unverified), **ORGANIZER-CONFIRMED** (none exists).

## 1. Executive summary (per site)

Full table and per-site rows: [`docs/nine-sites.html`](../docs/nine-sites.html) (rendered by `scripts/build_site.py` from `docs/evidence/nine-site-audit-20261027.json`).

| Site | Best owner-published file (highest OWNER-REPORTED score) | Owner score | Dots | Unique vs the other eight? |
|---|---|---|---|---|
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (H33) | 0.2778 | 37,654 | No (max overlap 1.0000 vs GEMSDOE36) |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 | 38,854 | No (0.9758 vs GEMSDOE27) |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` (owner name ends `-nan`) | 0.2710 | 37,660 | No (1.0000 vs GEMSDOE30) |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | 0.2708 | 40,199 | No (1.0000 vs GEMSDOE30) |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | 41,865 | No (0.9971 vs GEMSDOE27) |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | 0.2600 | 44,090 | No (1.0000 vs GEMSDOE30) |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 | 44,090 | No (1.0000 vs GEMSDOE27) |
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` (owner name ends `-nan`) | 0.2477 | 60,069 | No (1.0000 vs GEMSDOE30) |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | 0.2449 | 61,328 | No (0.9802 vs GEMSDOE24) |

MEASURED: all nine files are finite (0 NaN, 0 Inf), have values in [0,1], shape 3730×3292, the pinned transform, EPSG:32611, and zero dots on the mapped catalogue. Across all 72 ordered pairs the 3-px dot overlap is ≥0.867, and every pair exceeds the 0.70 threshold. **None of the nine is unique relative to the others.** For each site with a NaN-outside twin, the twin has an identical dot set (symmetric difference 0).

Best submission overall, by owner score alone: **GEMSDOE32 H33** (0.2778, OWNER-REPORTED). It is not unique (see §3), and it has no organizer receipt.

## 2. Estimate table — candidate files

"Estimated score" means the owner-reported score. No independent live-score estimate exists for these files. The unique column is the measured result against the other eight best files.

| File | Estimated score | Source of estimate | Unique vs listed sites? |
|---|---|---|---|
| GEMSDOE32 H33 (`…h33-h33-2-b2…-zeros.tif`) | 0.2778 | OWNER-REPORTED | No |
| GEMSDOE36 anderson-geothermal (`…9b9ea4e6-zeros.tif`) | 0.2750 | OWNER-REPORTED | No |
| GEMSDOE28 H36-1 (`…b531dae0a36f-allfinite.tif`) | 0.2710 | OWNER-REPORTED | No |
| GEMSDOE31 H27-4 (`…8acb75e1-allfinite.tif`) | 0.2708 | OWNER-REPORTED | No |
| GEMSDOE33 H33d (`…cb490425926e.tif`) | 0.2632 | OWNER-REPORTED | No |
| GEMSDOE25 dotted-H19-5 (`…e56ea318af89-zeros.tif`) | 0.2600 | OWNER-REPORTED | No |
| GEMSDOE30 d28-poisson (`…91eae1ca.tif`) | 0.2600 | OWNER-REPORTED | No |
| GEMSDOE24 H25-1 (`…989f59505db1-allfinite.tif`) | 0.2477 | OWNER-REPORTED | No |
| GEMSDOE27 topo-gap (`…5512495c6bd1-allfinite.tif`) | 0.2449 | OWNER-REPORTED | No |
| **Our H87-FCB B3 3–5 px (`gems86-h87-fcb-b3-3to5px-37654dots-20261027-zeros-out.tif`, workspace `releases/`)** | **No live estimate.** HOLDOUT-DTI 0.2197 [0.2105, 0.2277] | HOLDOUT-DTI (catalogue-derived holdout; see §4) | **FAIL**: 14 of 502 local references ≥0.70 overlap; 81 exceed 0.30 excess over chance |

Our candidate: SHA-256 `ddce5c07…8245d`, 37,654 dots, 825,650 B, format gate PASS (MEASURED). Its literal full-support witness gate is not re-measured here (the witness raster is not in the workspace); the repo record says the literal overlap is 1.0000 for any dot field.

## 3. Why H33 scored highest, and whether it can be beaten (analysis)

**What is measured about H33** (MEASURED, `docs/evidence` and README): H33 is the GEMSDOE28 parent (owner-reported 0.2708) with 2,545 dots deleted from the 1 < d_cat ≤ 2.0 px collar, leaving 37,654 dots (from 40,199). The local copy is byte-identical to the owner's file (`identical_to_repo_local_copy: true`). The H33 change is a tiny edit to a parent. The owner-reported gain is 0.0070.

**Why it probably scored highest (candidate explanations, not established):**
1. *Collar removal.* The deleted dots sat 1–2 px from mapped traces, where a catalogue-disjoint live truth would not have fault positives. Removing them raises precision with no recall cost on live faults.
2. *Budget.* 37,654 dots is the repo's budget figure. Of the nine best files, only H33 and GEMSDOE28 (37,660) are near it; the others range 38,854–61,328. The count alone does not explain the ranking, and this is not tested.
3. *Noise.* The whole top group spans 0.2449–0.2778 (0.033) on single owner-reported numbers with no receipts. Differences of 0.007 cannot be attributed to a mechanism without repeated organizer receipts.

**Can H33 be beaten?** Possibly, but nothing measured here shows it. Two facts constrain the answer:
- The local catalogue-hide holdout ranks H33 **last** (L arm 0.0047 [0.0043, 0.0052], vs the uniform null 0.0441). The holdout's truth is catalogue-derived (withheld catalogue segments), whereas the live truth is catalogue-disjoint new faults. This is consistent with AGENTS.md rule 12: a catalogue-hide instrument can anti-correlate with owner-reported live ordering. Alternative explanations are untested.
- Our H87 band-3–5 px candidate scores 0.2197 on that holdout, roughly 5× the null. But the band is near visible traces, which is the same catalogue-proximity the holdout rewards. So the holdout score is not evidence of a live gain, and the owner-reported live ordering does not support it.

Conclusion: **there is no measured route to beating 0.2778 that the repo can certify.** A beat needs (a) a file that passes the uniqueness gate, and (b) an organizer receipt. Neither exists yet.

## 4. Hypotheses (ranked; H87 is tested, the others are NOT RUN)

1. **H87-FCB — fair visible-trace band (TESTED on holdout; blocked on uniqueness).** Mechanism: damage-zone and en-echelon strands sit 3–5 px (≈300–500 m) from mapped traces but beyond the 3 px kernel. Uses catalogue geometry only, no native bands. Preregistration: `research/H87_FAIR_CATALOGUE_BAND_PREREGISTRATION.json`. Result: B3 0.2197 [0.2105, 0.2277] vs N0 0.0441; paired Δ +0.1756 [+0.1679, +0.1820]. Caveats: holdout is catalogue-derived; canary AUC (distance to visible trace) 0.8835 is under the 0.90 leakage rule but close; the candidate fails local uniqueness (14 references ≥0.70).
2. **Magnetic horizontal-gradient lineaments far from the catalogue (NOT RUN).** Layers: Band 2 `rtp` (reduced-to-pole) and Band 1 `mag_anom`. Physical signature: horizontal-gradient maxima from lithology contrast juxtaposed across faults, >1 km from mapped traces (the catalogue is silent there). Why catalogue-missing: no mapped trace where the survey signal is strong but unmapped. Difference from repo: NOT CHECKED. Must be compared against the prior lane records (`research/`, `registry/`) before any preregistration.
3. **Isostatic-gravity gradient lineaments (NOT RUN).** Layers: Band 13 `iso_grav_anom`, Band 18 `iso_grav_anom_hg` and Band 11 `iso_grav_anom_vg`. Physical signature: density contrast across buried faults, with a sign-consistent gradient ridge. Difference from repo: NOT CHECKED. The candidate element is a sign-consistent ridge rule; prior use of these gravity bands must be checked before any preregistration.

Neither NOT-RUN hypothesis may spend a slot until it passes a spatially blocked holdout and the uniqueness gate.

## 5. Verification log (this session)

- `scripts/nine_site_audit.py` → `docs/evidence/nine-site-audit-20261027.json` (9 files, MEASURED; NaN written as null).
- `scripts/run_h87_fcb.py` experiment 1 (`O,L,canary,N0,B1`) and experiment 2 (`N0,B2,B3`) → `docs/evidence/h87-fcb-experiment{1,2}-20261027.json`.
- `scripts/h87_build_candidate.py` → `releases/gems86-h87-fcb-b3-3to5px-37654dots-20261027-zeros-out.tif` (git-ignored) and receipt `docs/evidence/h87-fcb-candidate-receipt-20261027.json`. Rebuilt once after moving out of `docs/downloads/`; identical SHA `ddce5c07…8245d`, 502 references, 14 ≥0.70, 81 excess >0.30.
- `scripts/build_site.py` → `docs/nine-sites.html` and the nav link. `scripts/check_site.py`: PASS (links, registered TIFF/ZIP integrity, negative-state safety).
- Full pytest run: see the PR description (result recorded there, not claimed here before it finished).

## 6. Remaining work and limitations

- **Owner decision needed** on whether a continuous full-support raster can count as a dot-registry member (the literal witness gate). Until then no candidate can be uploaded, and the H87 candidate's download/submit answer stays NOT OK.
- **Full-registry uniqueness** for the candidate was measured against the 502 locally available rasters (docs/downloads, data/scored_fleet, and the nine owner archives). It was NOT measured against the full 690-raster registry, which is not in the workspace. This is not a claim of absence.
- **Publishing** the candidate under `docs/downloads/` would require the full artifact-registration pipeline (download inventory, artifact cards, ZIP companion, all-artifacts measurement). Not done; the file stays in git-ignored `releases/`.
- **The "Predicted values must be in range [0, 1]" rejection** is still not reproduced. All nine best files are all-finite with values in [0,1], so NaN-outside cannot explain it for those files. The rejected file was not in this checkout.
- **Leaderboard figures 0.3195 and 0.4413** are not in the registry and have no receipts. They are not cited as scores anywhere on the new page.
- **Holdout validity**: the gems57-pooled-hide-v2 holdout is catalogue-derived and does not reproduce owner-reported live ordering. Holdout numbers are not live scores.
- **Experiment 1 canary** AUC 0.8835 is below the 0.90 rule but close, and is a suspected catalogue-proximity confound.
- **Dense-reference saturation.** Overlap against dense references (for example faulthalo 4.2 M dots) is inflated by chance; the excess-over-chance column is reported for that reason.
