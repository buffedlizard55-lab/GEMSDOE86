# H86E-RIDF session review — 2026-10-24

## Decision (automated, no human inspection)

**A new, unique-by-construction TIFF was generated this session and the automated gates rejected it: DO NOT SUBMIT.**
No weekly slot was used. No current file in this repository is authorized for submission.

| Item | Value | Evidence |
|---|---|---|
| File | `gems86-h86e-ridf-hgbthin-37654dots-20261024-zeros.tif` (139,139 B) | `releases/h86e-NEGATIVE-DO-NOT-SUBMIT/*.json` (binary gitignored; rebuild below) |
| sha256 | `543a59d7dd8dd29ff564a17811a37817206c24211e5c60a77549bf4a9ddd7fb1` | same receipt |
| Format validator | all 15 checks pass (EPSG:32611, 3730×3292, transform = sample, float32, 0 NaN, min 0, max 1, 0 dots on mapped faults, 0 outside footprint) | receipt `validator` |
| HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld positives, buffered whole-component LOQO seed 20) | E1 **0.0811** [0.0650, 0.0972] | `docs/evidence/h86e_comparator.json` |
| R0 fold-fair on the same split | **0.0961** [0.0830, 0.1089] — reproduces the H86C-KSLB card value 0.09608619 exactly | same |
| Paired Δ E1 − R0 fold-fair | **−0.0150** [−0.0280, −0.0019] (worse; CI excludes 0) | same |
| Other arms | E2 distal-profile 0.0761 (Δ −0.0200 [−0.0327, −0.0068]); E3 distal+slope 0.0782 (Δ −0.0179 [−0.0306, −0.0056]) | same |
| Leakage canary (each feature alone) | max AUC **0.7554** (distance to visible catalogue); every band ≤ 0.90 | `docs/evidence/h86e_holdout.json` |
| Surface rank correlation | **0.9045 > 0.90** vs `17GEMSDOE E-proba-multiscale` → lane drift / duplicate | `docs/evidence/h86e_registry_surface.json` |
| Final-dot overlap (682 registry rasters measured; 2 grid-mismatch errors) | 135 literal firings; 52 from continuous surfaces and 67 from space-filling rasters (overlapping sets); **64 informative dot-field firings** (e.g. 80.9 % vs `11GEMSDOE gems-structural-area06-v1`, whose own halo covers only 17.3 % of the allowed area) → duplicate | `docs/evidence/h86e_pa86_chance_overlap.json` |
| Run card | verdict `negative`, `duplicate: true` | `docs/evidence/h86e-run-card.json` |
| Parallel SWCON (PR #77, labelled OK-to-submit) re-audit | 131 literal firings, **58 informative dot-field firings** (81.9 % vs 12GEMSDOE r7-nms3-dem10-scarp, chance 31.7 %) → overruled, DO NOT SUBMIT | `docs/evidence/swcon_pa86_chance_overlap.json` |
| Historical H86C-KSLB re-audit (same registry, self row excluded) | 83 literal firings (52 continuous-surface, 67 space-filling), **12 informative dot-field firings** (worst other ρ 0.093) → DO NOT SUBMIT | `docs/evidence/kslb_pa86_chance_overlap.json` |

Experiments used: **3 of 3** (E1–E3); wall-clock within the 2-hour budget. Logged as duplicate and stopped (protocol rule 1).

## Why GEMSDOE32 `h33-h33-2-b2` led (0.2778, OWNER-REPORTED) — and what that implies

All numbers in this section are **OWNER-REPORTED** leaderboard claims (no organizer receipt) or measurements on pinned rasters.

1. **Lineage, not a new layer.** H33 = GEMSDOE28 `d2.8` minus 2,545 dots at 1.4 ≤ d_cat ≤ 2 px (pixel-exact, earlier review). The jump in that lineage came from emission geometry: continuous H19-5 ridges (0.1922) → 2.8 px dotted (0.2600) → r1 solo (0.2708) → collar prune (0.2778).
2. **Back-of-envelope inversion** (assumption: dots ≈ one-to-one with credited truth, M ≈ T). Removing 2,545 near-zero-credit dots raised 0.2708 → 0.2778, so D ≈ 509·0.2708/0.0070 ≈ 19.7k; the GEMSDOE36 superset (+1,200 dots, −0.0028) gives D ≲ 23.6k. Hence T ≈ 5.5–6.5k truth-weighted credit from 37,654 dots (≈0.15–0.17 per dot), and the marginal inclusion bar is only α·DTI ≈ 0.056 kernel credit per non-redundant dot. These are **projections, not scores**.
3. **Fleet stratification (n = 17 owner-reported scores, descriptive only)** — `docs/evidence/h86e_fleet_strata.json`. The top six (all one lineage) put 33–34 % of dots ≥ 32 px (3.2 km) from mapped faults and < 1 % on low-slope (< 1.79°) ground; the four lowest (0.0041–0.1152) put 0–24 % far and 15–28 % on low slope. GEMSDOE81 (85 % within 2–4 px) scored 0.0041. Interpretation (hypothesis, not proof): hidden faults are largely **distal to the Quaternary-fault catalogue and in sloping bedrock terrain**, consistent with a truth set containing non-Quaternary bedrock faults.
4. **Can we beat 0.2778?** Not demonstrated. The catalogue-hide holdout cannot score the fleet's best rasters (they exclude the withheld truth and its collar because they were built with the full catalogue): H33 scores 0.0037 as-is, and the as-is Spearman between holdout and owner-reported LB is 0.24 (p = 0.35, n = 17; `docs/evidence/h86e_instrument_check.json`). The holdout's link to the leaderboard is therefore **unvalidated** — the single most important open problem.

## What H86E taught us (negative results are deliverables)

* A catalogue-trained, catalogue-blind-feature classifier converges to the same ranking as a previous lane (ρ = 0.9045 with 17GEMSDOE's supervised probability surface, LB claim for its 2 % emission 0.0187). In-sample, it concentrates dots next to mapped faults (median d_cat 4.0 px), the regime with the worst owner-reported scores. **Supervised "looks like a mapped fault" is a crowded, low-yield lane.**
* Distal quotas (E2/E3) lowered HOLDOUT-DTI, while the fleet evidence favours distal placement — further evidence that the catalogue-hide instrument and the leaderboard reward different things.
* **Comparator error caught (IR-86-H86E-02):** a first R0 comparator built from GEMSDOE28 `r1-solo` (0.0286) was wrong because that file already excludes dots within ~1.4 px of the *full* catalogue. The correct recipe source (GEMSDOE25 `dotted-h19-5-d2-8`, sha256 `91eae1ca…`) reproduces the archived 0.0961 exactly.
* **Ordering irregularity (IR-86-H86E-01):** the surface registry check ran after placement instead of before. The outcome (stop) is unchanged.

## Protocol amendments used (public, tested, thresholds unchanged)

* **PA-86-01** — `scripts/protocol_preflight.py::require_like_for_like`. The pinned 17GEMSDOE witness is a continuous surface (support fraction 1.0 > 0.20, the shared template's own `representation_class`). The template's `two_phase_summary` (unmodified vendored bytes) is used: dot-overlap on dot fields, rank correlation on every raster; the literal reading is still reported. A saturating *dot field* still raises. `require_feasible` is unchanged, so historical builders stay gated.
* **PA-86-02** — `scripts/pa86_chance_overlap.py`. For each overlap firing, the registry raster's own 3 px halo coverage `c` of the allowed area is the expected overlap of a random dot set. If `c > 0.70` the test cannot discriminate (e.g. the 13GEMSDOE 5 px lattice), so ρ ≤ 0.90 decides; every firing with `c ≤ 0.70` stays a hard duplicate stop. H86E fails this gate.

## Ranked hypotheses for the next session (not run)

| Rank | Hypothesis | Layers / signature | Why it should find *uncatalogued* faults | Novelty vs repo | Cost | Data |
|---|---|---|---|---|---|---|
| 1 | **LB-aligned instrument first**: build a holdout whose withheld truth is distal (> 3 km) bedrock-terrain segments, and calibrate it against the 17 owner-reported scores | catalogue geometry + `det_elev_slope` | Fixes the measured instrument–leaderboard mismatch before any new lane | New (no repo instrument is LB-calibrated) | Low | Competition bands only |
| 2 | **Bedrock-fault displacement of potential-field markers** (two-sided RTP / isostatic-gravity phase offsets across linear valleys inside ranges) | `rtp`, `iso_grav_anom`, `det_elev` Hessian troughs | Pre-Quaternary faults lack scarps but offset lithology; catalogue is Quaternary-centric | Distinct from edge/tilt lanes: tests *offset*, not edge presence | Medium | Competition bands only |
| 3 | **Distal re-weighting of an independent non-supervised ridge surface** with the measured R0 d_cat profile and a low-slope veto | any non-supervised ridge field | Matches the fleet's distal/sloped regime | Must clear PA-86-02 vs the H19-5 lineage | Low | Competition bands only |
| 4 | **NBMG 1:24k/1:100k geologic-map faults as weak labels** | Nevada Bureau of Mines and Geology map faults | Mapped bedrock faults outside the Qfault catalogue | SGMC lanes scored 0.05 (owner-reported); NBMG detail differs | Medium | Official source https://nbmg.unr.edu/ — **not reachable from this sandbox** (host not allowlisted); not viable here |

## Reproduce (all automatic)

```bash
python scripts/restore_protocol_data.py --include-features --include-registry
python scripts/build_h86e_features.py           # 35 catalogue-free features -> data/work/
python scripts/run_h86e.py                      # canary + LOQO surface + E1..E3 holdout
python scripts/h86e_comparator.py               # R0 fold-fair comparator, paired CIs
python scripts/build_h86e_final.py              # PA-86-01 preflight, final surface + dots
python scripts/write_h86e_tif.py                # shared fail-closed writer (TIFF + ZIP + receipt)
python scripts/check_h86e_registry.py data/work/h86e_final_dots.npy docs/evidence/h86e_registry_final_dots.json
python scripts/check_h86e_registry.py data/work/h86e_final_surface.npy docs/evidence/h86e_registry_surface.json --surface
python scripts/pa86_chance_overlap.py docs/evidence/h86e_registry_final_dots.json data/work/h86e_final_dots.npy docs/evidence/h86e_pa86_chance_overlap.json
python scripts/h86e_run_card.py
```

Registry rasters are restored by sha256 from the pinned inventory (`research/upstream/registry_inventory.json`, 655 entries, all 655 fetched and hash-verified this session) into gitignored `data/registry_ext/`.

## Sources for manual review

* Competition problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (not fetched — DrivenData automated access is prohibited by AGENTS.md rule 9)
* Official reference solution (cloned this session, commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`): https://github.com/drivendataorg/gems-prize-reference-solution — U-Net, Tversky loss weighted toward false negatives
* GEMSDOE32 page: https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
* Tversky index: https://en.wikipedia.org/wiki/Tversky_index · EPSG:32611: https://epsg.io/32611
* GeoDAWN surveys: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and

## Limitations

Mirrored competition data are hash-pinned owner mirrors, not organizer-authenticated. Leaderboard values are owner claims. The registry snapshot dates from 2026-10-21 plus local files, so GEMSDOE86–92 work published later may be missing. The holdout instrument is not validated against the leaderboard. The weekly quota and portal acceptance cannot be observed from here.
