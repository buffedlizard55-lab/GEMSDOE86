# H86J-LSI — Live-Score Inversion: review, H33 explanation, ranked hypotheses, three-pass audit

Date: 2026-10-25 (UTC). Lane: **H86J-LSI** (one lane, 3 experiments, ≤ 2 h).
Frozen preregistration: [`H86J_LSI_PREREGISTRATION.md`](H86J_LSI_PREREGISTRATION.md)
(commit `5259f66`, made before any fit, field or dot was computed).
Machine-readable run card: [`docs/evidence/h86j-lsi-run-card.json`](../docs/evidence/h86j-lsi-run-card.json).

## Bottom line — is a file OK to submit? **NO. DO NOT SUBMIT.**

* Verdict **`negative`** (2 of 7 preregistered gates fail). A unique, format-valid raster
  was generated (`gems86-h86j-lsi-30000dots-20261025T052444Z-924195f3-DO-NOT-SUBMIT-zeros`,
  SHA-256 `29c9b2bb…c75276ae`, 15/15 validator checks PASS). Because it is negative it is
  **not published** as a download. `safe_to_submit=false`, `approved_for_weekly_slot=false`,
  0 slots used.
* **New positive finding:** the live-score inversion instrument predicts *held-out sites'*
  OWNER-REPORTED live scores with leave-one-site-out Spearman **0.900** (MAE 0.027). The constant
  model gets 0.310 and the SGMC proxy gets 0.300. This is the first instrument in the repo that
  tracks the live board, but its fitted field is **non-physical** (see §3, E2/E3). Fix that
  before the next candidate.

Evidence classes used below (never mixed):

* `OWNER-REPORTED` — live leaderboard numbers typed in by the owner (`registry/prior_scores.csv`). **No organizer receipt exists for any of them.**
* `HOLDOUT-DTI` — shared evaluator `gems57-pooled-hide-v2`, catalogue-hide folds (seed 20, 11,321 withheld positive pixels), 95 % spatial-block bootstrap CI.
* `SGMC-PROXY-DTI` — the same evaluator scored against the off-catalogue SGMC proxy; **a selection instrument, not a score** (AGENTS rule 12).
* `LSI-PROJECTION` — a number produced by the fitted H86J model. **A model number, never a score.**
* `DERIVED` — algebra applied to owner-reported scores and pixel-exact raster edits.

## 1. Why H33 (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, 0.2778 OWNER-REPORTED) led

Pixel forensics (`docs/evidence/h86f-h33-forensics.json`, repo-verified):
H33 has 37,654 dots and is *exactly* the GEMSDOE28 parent (40,199 dots, 0.2708)
minus 2,545 dots at catalogue distance √2–2 px; that parent is GEMSDOE25 d2.8
(44,090 dots, 0.2600) minus 3,891 dots at d_cat = 1 px. The lineage starts at
the H19-5 surface (0.1922) thinned to ≥ 2.828 px spacing. H33 has no dot on, or
within 2 px of, a mapped trace; 34 % of its dots are ≥ 32 px from the catalogue.
**H33 added no new geology; it removed redundant mass.**

### Mechanism (official metric, α = 0.2, β = 0.8, 300 m triangular kernel)

Write `T` = recovered truth credit, `D = n − M` = dot mass not explained by the
truth, `G` = total (hidden, off-catalogue) truth mass. Then
`DTI = T / (0.2·T + 0.2·D + 0.8·G)`. Deleting `b` dots that each carry truth
credit `k` changes the denominator by `−0.2·b` (FP mass) and the numerator by
`−b·k`. The deletion helps iff `k < α·DTI ≈ 0.2 × 0.27 ≈ 0.056`, i.e. iff the
dot almost never sits within 300 m of a *scored* fault. Because the organizers
score only truth that is **not** in the visible USGS/INGENIOUS catalogue (thread
11516; the hidden truth excludes mapped traces), dots hugging mapped traces earn
almost nothing and only cost precision. Each pruning step is a pure
emission-economics gain.

### What the two pixel-exact edits imply about the hidden truth (DERIVED)

If `b` dots with zero credit are removed, `1/DTI0 − 1/DTI1 = 0.2·b/T` exactly,
so `T ≥ 0.2·b / (1/DTI0 − 1/DTI1)` (equality when the removed dots earned
nothing). [`docs/evidence/h86j-live-algebra.json`](../docs/evidence/h86j-live-algebra.json):

| Edit (pixel-exact) | b | T lower bound | 4-dp rounding interval | implied G (FP = 0) | implied G (M = T/3) |
|---|---:|---:|---|---:|---:|
| d2.8 → GEMSDOE28 (delete d_cat = 1) | 3,891 | 5,073 | [5,027, 5,121] | 22,150 | 12,523 |
| GEMSDOE28 → H33 (delete 1 < d_cat ≤ 2) | 2,545 | 5,470 | [5,393, 5,549] | 23,246 | 14,289 |

So H33 already recovers ≳ 5.5 k truth-credit units, and the hidden truth mass is
≈ 12–23 k pixel-units (two independent edits agree). The independently fitted LSI model (E2, all 74 rasters) puts the hidden truth mass at **G ≈ 18,430**, inside that range. This is a MODEL number.

### Can we beat it?

At fixed `n`, `D` and `G`, beating 0.3195 (OWNER-REPORTED "highest") needs
≈ +15 % `T`; beating the leaderboard 0.4413 (OWNER-REPORTED) needs ≈ +55 % `T`
at the same dot mass (or a matching cut of false-positive mass). Pruning
alone saturates: H33 has no dots left at d_cat ≤ 2, and the next shell (2–3 px)
already earns `k` near the 0.056 break-even. A further gain therefore has to come
from **moving mass to where unmapped truth is dense**, which needs an instrument
that tracks the live metric. That is what this lane tested.

## 2. Instrument audit (new irregularity)

Every earlier lane picked surfaces with catalogue-hide HOLDOUT-DTI (documented to
anti-correlate with live ordering) or the SGMC proxy (claimed to reproduce the
live ordering on 8 rasters, H86G basis). E1 measured both, as-is, on **74 distinct
owner-scored rasters from 55 sites** (`data/work/h86j/e1.json`, not committed;
summary in the run card):

| Instrument (as-is) | Spearman vs OWNER-REPORTED live, n = 74 |
|---|---:|
| SGMC-PROXY-DTI | **0.300** |
| catalogue-hide HOLDOUT-DTI (`gems57-pooled-hide-v2`) | **0.051** |

**IR-86-H86J-01:** the SGMC proxy's 8-raster agreement does not generalise. Large
counter-examples: GEMSDOE44 h46 (SGMC 0.3081 vs live 0.0715), r13 lattice
(0.2499 vs 0.0904), pindrop-v4-ridge (0.3024 vs 0.1152); H33 itself scores only
0.0954 on SGMC. The H86G-EDTI promotion (SGMC paired Δ vs H33 +0.0269) is therefore
weak evidence about the live board. This does not change H86G's card; it changes
how much weight any SGMC-selected file deserves.

## 3. Experiments (budget: 3, all used)

**E1: measurement set, canaries and baselines.** There are 74 distinct decoded rasters from 55 sites
(35 rows had no restorable raster; 1 ambiguous row was excluded). The operators were sampled on 1,275,852 of
5,106,385 active pixels (25 %, seed 861025). LEAKAGE-CANARY: all 15 features pass, with a maximum
discriminative AUC of 0.6174 (`dcat_3_6`, threshold 0.90). As-is baselines are in §2.

**E2: instrument validation (leave-one-site-out, 55 refits).**

| Model (Spearman / MAE vs OWNER-REPORTED live, n = 74) | Spearman | MAE |
|---|---:|---:|
| LSI, in-sample | 0.933 | 0.022 |
| **LSI, LOSO** | **0.900** | **0.027** |
| constant-λ, LOSO | 0.310 | 0.076 |
| SGMC-PROXY-DTI, as-is | 0.300 | — |
| LSI LOSO within the top cluster (live ≥ 0.20, n = 14) | 0.407 | — |
| SGMC within the top cluster | 0.103 | — |

Gate 2 passes. Caveat: inside the top cluster, where H33 lives, ranking is much weaker (0.41).

**E3: candidate.** λ̂ → E[k] → spacing-greedy (≥ 2.8 px, collar > 3 px). The budget was picked by
LSI-PROJECTION over {30k, 37,654, 44,090, 55k}, and 30,000 won.

| Number | Class | Candidate | H33 | H86G-EDTI |
|---|---|---:|---:|---:|
| LSI-PROJECTION (all-data fit) | MODEL, not a score | 0.547 | 0.235 | 0.032 |
| LOSO refits where the candidate projects higher | MODEL | — | 55/55 | 55/55 |
| SGMC-PROXY-DTI (62,122 proxy positives) | selection only | 0.0629 [0.0412, 0.0898] | 0.0954 [0.0848, 0.1068] | 0.1223 [0.0988, 0.1480] |
| paired Δ candidate − control (SGMC) | selection only | — | −0.0325 [−0.0588, −0.0045] | −0.0593 (CI upper < 0) |
| HOLDOUT-DTI `gems57-pooled-hide-v2`, 11,321 withheld, visible construction | HOLDOUT-DTI | 0.0346 [0.0229, 0.0453] | 0.0311 [0.0109, 0.0512] (visible-collar control) | — |
| paired Δ vs H33 visible collar | HOLDOUT-DTI | +0.0035 [−0.0169, +0.0240] | — | — |

**Why the projection is not credible:** the log-linear field exceeds λ = 1 (a probability) on 2,552
active pixels. Those pixels hold 63.5 % of its mass, with a maximum of 96.9. The fit buys accuracy on
fleet scores by piling impossible truth mass into a few hundred hot spots. The 30k-dot candidate goes to
those hot spots, so its projection of 0.547 is an artefact of the same pathology. The two independent
instruments (SGMC proxy, catalogue-hide holdout) do not confirm it.

Registry (final dots, 694 rasters including all 655 inventory rasters and local extras):
max Spearman **0.1833**, 0 rho firings, 0 byte-identical. The highest 3-px forward overlap against a
non-space-filling dot field is **0.6974** (`88976dc5…`, 13GEMSDOE `13gems-toporef-holdoutref`, 246,469
positives), just under 0.70. Forward overlap is 1.0 against 65 continuous or space-filling rasters
(the literal reading, PA-86-01). Pre-placement surface check: max Spearman 0.1833, 0 firings.

## 4. Gates and verdict

| # | Gate (frozen) | Result |
|---:|---|---|
| 1 | Canary AUC ≤ 0.90 | PASS (0.6174) |
| 2 | LOSO ρ ≥ 0.60, > constant, ≥ SGMC | PASS (0.900 / 0.310 / 0.300) |
| 3 | SGMC paired vs H33: CI lower > 0 | **FAIL** (−0.0325 [−0.0588, −0.0045]) |
| 4 | SGMC paired vs H86G: CI upper > 0 | **FAIL** (−0.0593, CI upper < 0) |
| 5 | LSI-PROJECTION beats H33 and H86G in ≥ 90 % of LOSO refits | PASS (55/55), but the field is non-physical |
| 6 | HOLDOUT-DTI ≥ H33 visible-collar control | PASS (0.0346 vs 0.0311; Δ CI spans 0) |
| 7 | Uniqueness (surface and final dots) | PASS in-runner (ρ ≤ 0.1833; non-space-filling dot-field overlap ≤ 0.6974 after the PA-86-02 halo rule). The shared `check_h86e_registry.py` reports `final_dots_gate_pass=false`: the registry is incomplete (2 grid-incompatible rows, 14GEMSDOE `ccbe1de0` and 7GEMSDOE `qfaults_prior_u8`), and there are 17 unadjusted space-filling dot-field firings (worst: lattice-s5, 0.9889). `pa86_chance_overlap.py` fails closed on an incomplete report |
| 8 | Format (writer + independent validator) | PASS (15/15) |

**Verdict: `negative`. Decision: DO NOT SUBMIT.** Even if every lane gate had passed, AGENTS rule 13
and the literal full-support witness (PA-86-01) would keep `safe_to_submit=false`. Upload
authorization is an owner decision, separate from research promotion.

## 5. Ranked untried hypotheses (expected DTI gain per cost)

Ranking is a qualitative judgement, **not a predicted DTI**. Scoped `grep` of
`src/`, `scripts/` and `registry/*.json` found no NDVI/phreatophyte, no NWIS, and
no live-score likelihood; InSAR terms appear only in `gems86_fvmb` and must be
checked before implementing #3.

| Rank | Hypothesis | Layers / physical signature | Why it finds faults missing from USGS/INGENIOUS | Difference from repo | Cost |
|---:|---|---|---|---|---|
| 1 | **LSI + new fleet measurements** (this lane, continued) | Owner-scored rasters as measurement operators | The live score only counts unmapped truth, so every fitted coefficient is about unmapped faults | First lane that fits the live metric's algebra rather than a proxy | Low per added raster; needs more diverse scored rasters |
| 2 | Catalogue-strike-gated oriented scarps (H86J-SCO) | lidar step/cross, DEM gradient, RTP gradient gated by the visible catalogue's local 5 km strike tensor | Unmapped strands of a fault population share the set strike; Lahontan shorelines and flow fronts do not | Prior tensor lanes used data-only orientation | Low |
| 3 | InSAR groundwater-barrier discontinuities | NASA OPERA DISP-S1 Sentinel-1 LOS velocity (ASF DAAC, free with Earthdata login) | Faults act as aquifer barriers: pumping-driven subsidence steps sharply across buried faults with no scarp | No line-of-sight velocity step detector in executable code (verify `gems86_fvmb`) | High (not reachable from this sandbox) |
| 4 | Dry-season phreatophyte alignments | Landsat 8/9 Collection 2 surface-reflectance NDVI (USGS EarthExplorer, free) | Spring lines and phreatophyte belts follow permeable fault zones under alluvium | No NDVI in the repo | Medium; needs new external data |

Official sources: competition page
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> (not
fetched by automation, AGENTS rule 9); OPERA DISP-S1
<https://www.jpl.nasa.gov/go/opera/products/disp-product-suite/>;
ASF DAAC <https://asf.alaska.edu/>; Landsat Collection 2
<https://www.usgs.gov/landsat-missions/landsat-collection-2>;
USGS 3DEP <https://www.usgs.gov/3d-elevation-program>.

## 6. Three-pass audit

* **Pass 1 (implement/verify):** the prereg was frozen before any fit (commit `5259f66`). There are 9 unit tests
  (kernel vs metric, expected-T vs the shared `dti_binary`, analytic gradient vs finite differences,
  synthetic recovery, decode clipping, preflight order, exact 3-px lookup vs EDT). E1 to E3 ran end to end.
  All 655 inventory rasters were restored with hash verification (receipt
  `docs/evidence/h86j-registry-inventory-restore.json`).
* **Pass 2 (bug review):**
  * Fixed an OOM (now lazy decoding).
  * Fixed per-call CSR row slicing, which was 3.5× slower (now CSC sliced once; results are exact).
  * Fixed the uniqueness gate ignoring error rows (it now fails closed).
  * Added the PA-86-02 space-filling rule to the in-runner check, identical to `pa86_chance_overlap.py`.
  * Changed `safe_to_submit` from "lane gates pass" to always false, per rule 13.
  * Found the λ > 1 pathology.
  * Found that the surface byte-identical flag is an artefact (an empty set vs an empty raster).
* **Pass 3 (recheck vs request):**
  * One lane, 3 experiments. The 2 h budget was overrun by ~8 min (E3 ended 05:24 UTC); this is disclosed.
  * Every number is labelled.
  * The canary was run per feature.
  * Surface and final dots were checked before writing.
  * The run card is JSON.
  * The name has a unique digest and the note is ≤ 140 chars (98).
  * Values are in {0, 1} ⊂ [0, 1].
  * No slot was picked and nothing was scraped.

## 7. Irregularities flagged

* **IR-86-H86J-01** — SGMC proxy ρ = 0.30 vs live on 74 rasters (above).
* **IR-86-H86J-02** — registry row `ccbe1de0…` (14GEMSDOE r5-geom-horse-ensemble) has
  the competition shape but a shifted transform (origin 500000, 4500000 instead of
  243350, 4508550). Its OWNER-REPORTED score is 0.0020, consistent with a mis-registered
  file. H86J compares it index-wise (never skips it) and records that it did.
* **IR-86-H86J-03** — one measurement row is ambiguous (GEMSDOE40 `h8-euler-lineament`:
  `-hard.tif` and plain `.tif` decode differently) and was excluded as preregistered;
  35 rows have no restorable raster.
* All live numbers remain OWNER-REPORTED; no DrivenData receipt exists in the repo.

## 8. Limitations and next work

* **Do next (highest P(win) per hour):** refit LSI with a bounded link, λ = σ(θ·f) ≤ 1, plus a
  smoothness prior. Preregister it as amendment A1. Then rerun E2/E3 unchanged. E2 shows the live board
  is learnable from the fleet (ρ = 0.90 held-out). What failed is the physics of the field, not the
  signal.
* **Re-rank the promoted lane:** the LSI model (non-physical, so treat it with caution) projects H86G-EDTI
  far below H33. Combined with IR-86-H86J-01, H86G's SGMC promotion should not be used to pick a slot.
* **Add measurements:** each new owner-scored raster with a recorded name tightens the inversion. The
  most informative ones are deliberate probes, e.g. H33 with one distance shell restored.
* **Limitations:** all live scores are OWNER-REPORTED (none has an organizer receipt). The fleet is
  co-linear (H19-5 lineage), so many directions of θ are unidentified. LOSO by site does not remove
  shared-lineage leakage between sites. The top-cluster ranking is weak (0.41). The shared
  `check_h86e_registry.py` run on the final dots is recorded in `data/work/h86j/out/` only if it finished
  (it is not needed for a negative verdict). The 2 h budget was overrun by ~8 min.
