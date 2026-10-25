# H86M-LT review — leaderboard tomography, H33 forensics, and a promote candidate

**Session:** `arena/ecc314b3-gemsdoe86`, 2026-10-25 (UTC). Budget used: 3 experiments
(E1 fleet geometry, E2 tomography pilots, E3 emission v1–v3 under disclosed amendments),
0 submission slots. Preregistration + amendments: `research/H86M_LT_PREREGISTRATION.md`.
Pilot scripts preserved in `scripts/h86m_pilots/`; production lane `scripts/run_h86m_lt.py`;
full-registry scan `scripts/check_h86m_full_registry.py`.

## Deliverable

**`gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros.tif`**
SHA-256 `4067382cab05de80e85c22e717a8ea98e569f85933eedd9690651a7755eaebee`, 37,654 binary dots.
Run card: `docs/evidence/h86m-lt-run-card.json`. Verdict **promote** under the lane's
machine gates (below); `approved_for_weekly_slot=false` (selector step is separate).

| Gate | Result |
|---|---|
| Format (vendor `validate`, 15 checks: single-band float32, EPSG:32611, 3730×3292, transform = sample, 0 NaN/Inf, values exactly {0,1} ⊂ [0,1], zeros outside footprint, 0 dots on catalogue) | **PASS 15/15** — fixes the portal error "Predicted values must be in range [0, 1]" (cause class: non-finite/sentinel or out-of-range values; writer refuses to emit them) |
| ZIP | single TIFF, byte-identical payload |
| Geometry self-checks | min distance to mapped catalogue 3.16 px (>3); min NN spacing 2.828 px |
| Uniqueness, local (58 dot-fields) | max forward 3-px overlap **0.640 ≤ 0.70**, max Spearman **0.113 ≤ 0.90** |
| Uniqueness, full restored registry (655 files, 414 dot-fields) | max forward **0.649**, max Pearson dots **0.159**, surface **0.556**; **0 firings** (`docs/evidence/h86m-lt-full-registry-uniqueness.json`) |
| Leakage canary analogue | belief AUC vs SGMC off-catalogue = **0.621 < 0.90** |
| Expected DTI vs h33-model (PROJECTIONS, not scores) | E2e primary **0.3317 vs 0.2660 (Δ +0.0657)**; E2d **0.3515 vs 0.2685 (+0.0831)**; E2b coarse **0.2714 vs 0.2716 (−0.0002, tie within LOO-MAE 0.024)** |
| SGMC-PROXY-DTI (diagnostic) | candidate **0.1136** vs h33 0.0954, p5 0.1126, gate_ortho 0.1334 (62,122 proxy-truth px) |

Nothing here is ORGANIZER-CONFIRMED. Every live input score is OWNER-REPORTED
(`registry/prior_scores.csv`, no submission-page receipts). Whether this file beats
0.2778 live can only be settled by an organizer receipt after a selector spends a slot.

## Why did h33 (owner-reported 0.2778) top the fleet? (PhD-level answer)

Verified pixel-exactly in this checkout (and consistent with `research/H33_ANALYSIS.md`):
`h33` = GEMSDOE28 parent `d28` (40,199 dots, 0.2708) **minus its 2,545 dots with
1 < d_cat ≤ 2 px**, nothing else. Three measured facts explain the fleet ordering:

1. **Emission efficiency dominates geology at the top.** The top-9 owner-reported rasters
   are one lineage (h19-5 surface → dotted d1.5/d2.8 → D28 → h33 and near-clones;
   pairwise 3-px overlaps 0.95–1.00, e.g. h33 ⊂ anderson exactly). Their score spread
   (0.245–0.278) is produced by dot *budget, spacing and collar pruning* on essentially
   one surface — DTI `= T/(0.8K + 0.2(T+n−M))` taxes every non-crediting dot at α=0.2
   while truth credit saturates via the 300 m kernel `max`, so redundant/collar mass is
   pure denominator.
2. **Hidden truth is scarce and far from the catalogue.** The lattice calibration raster
   (206,895 px; 99.9 % of allowed pixels within 3 px; 0.0904) inverts to **K ≈ 12–16k**
   hidden truth px (≈⅕–¼ of the 60,988 catalogue px). At K≈15.5k, h33's 0.2778 implies
   it recovers only ≲40 % of weighted truth (T≈5–6k) with ≈37.7k dots — i.e. headroom is
   precision-weighted coverage, not more dots. `poisson81` (dots ring the catalogue at
   median d_cat 2.2 px; 0.0041) shows the 300 m catalogue collar earns ~nothing, whether
   because the organizer masks it or because hidden faults are defined away from mapped
   traces; every top raster by construction emits `d_cat>2–3`.
3. **Independent families corroborate a real, narrow signal.** Non-lineage methods
   (gate_ortho 0.2376, p5 0.2478, ptcf 0.2343, cvarlw 0.2303) overlap h33 only 43–58 %
   forward yet score 0.23–0.25, while near-random controls score ≈0.004–0.09. Tomography
   (below) shows the live-valuable pixels are where ≥5 such independent submissions
   agree within 300 m on ≥2 independent line supports — a physical fault network seen
   through different sensors (magnetics, gravity, topography), not one model's artifact.

Causality limit (retained from prior reviews): without organizer receipts or truth, the
collar-pruning *mechanism* is the uniquely consistent explanation of the pixel diff +
metric algebra, not a proven cause of the +0.0070 owner-reported delta.

## Method (E2 tomography → E3 emission)

Belief density ρ over pixel groups (A/B/C/D near-votes within 3 px × exact-AB votes ×
collar) fit to 29 owner-reported scores through the exact algebra
`T=Qρ, M=Rρ, K=Aρ, DTI=T/(0.8K+0.2(T+n−M))` (Q = kernel coverage, R = kernel convolution,
reciprocity). Primary fit: additive monotone log-linear ρ (corroboration increments ≥0),
K=15,516, fit RMSE 0.0208, **honest LOO-MAE 0.0190** (generic-start refits). Findings:
A-lineage near-votes add nothing once B≥5 and C≥2 are known (A is an emission of the C
surface); B5 is a step function (×~90 density vs base); exact-AB≥3 multiplies ×3.5;
D-family near-votes *reduce* density (×0.40/level — they mark shared false lineaments);
collar ≈ base rate. Emission: equal-weight model average of three belief fits, sharpened
within-group by the score-weighted kernel-vote surface, greedy CELF on exact marginal
truth credit, spacing ≥2.828 px, `d_cat>3`, fixed 37,654 budget, running-ratio
uniqueness gate ≤0.64 vs the 13 binding fleet tubes. Deterministic: two independent
runs produced byte-identical SHA-256.

Validation honesty: the catalogue hide-and-recover instrument cannot validate this (or
any fleet) lane — all fleet rasters are off-catalogue by construction and the instrument
anti-correlates with live ordering (repo E1b). The lane's validation is instead:
tomography LOO on held-out *raster scores*, three-belief cross-check with LOO materiality,
SGMC-PROXY-DTI diagnostic (its live-rank Spearman is −0.11 among top rasters, hence
diagnostic only), format validator, and full-registry uniqueness. Optimizer's curse
applies to all expected-DTI projections; margins must be read against LOO-MAE ≈0.02.

## Ranked geological hypotheses not yet executed in this repo

(Each: layers → signature → why catalogue-missing → difference from implemented lanes.
"Untried" = no executed lane/run card found in this checkout on 2026-10-25; BMR/GSST/CNT
already queued in `registry/followup_hypotheses_20261025.json`.)

1. **BMR — basement-interface gravity mass-balance residual** (bands 13 `iso_grav_anom`,
   15 `depth_to_base_surf`). Forward-model the gravity of the Band-15 basement surface
   (single frozen density contrast, fitted on spatial training blocks only) and rank the
   *residual* cross-strike step. A buried basement offset under basin fill leaves a
   residual density step with no surface scarp — precisely catalogue-missing geometry.
   Differs from H86E-SPBT (paired raw steps) and H86H-PSTD (tensor invariants): it tests
   a physical forward model, and its mimic (intrabasement density heterogeneity / Band-15
   circularity, since Band 15 is gravity-derived) is separable by requiring residual
   persistence across two upward-continuation heights. Cost: low (FFT forward model).
   Validate on catalogue hide-and-recover (this is a *surface* method, so the instrument
   is valid for ranking it, unlike for off-catalogue emissions).
2. **EQL — earthquake-lineation anisotropy** (bands 10 `deq_n100a15`, 16 `ieq_n100a15`).
   Directional (15°-wedge) seismicity density ratio: unmapped active faults host
   microseismicity lineations even where geophysics is blanketed by young volcanics.
   No lane in this repo uses bands 10/16 as a primary signal (grep: only generic feature
   stacks list them). Mimic: geothermal-field induced seismicity clusters (radial, not
   linear — the anisotropy ratio is the discriminator). Cost: low. External check free:
   USGS ComCat (https://earthquake.usgs.gov/fdsnws/event/1/) for a raw-catalogue rebuild
   if band semantics need verification.
3. **GSST — gravity step-vs-compact-source shape test** (bands 13, 5, 11, 18 with the
   verified directional-derivative semantics of `src/gems86/io.py`). Profile-shape
   classification across candidate edges: a fault is a *step* (anti-symmetric profile),
   a dike/compact body is a *bump* (symmetric). Directly attacks the dike mimic that
   tomography cannot separate. Cost: medium (profile extraction along belief ridges —
   can start from this lane's dot chains). 
4. **CNT — conductivity-neck topology × dilatation** (bands 17 `cond_surf`, 8
   `geod_dilaterate`). Persistent narrow conductive necks (fault-zone fluid/clay
   conduits) that coincide with dilatational strain corridors. GDSC used dilatation
   alone; no lane used conductivity *topology* (neck width persistence) as the primary.
   Mimic: playa/lakebed conductors (broad, low relief — width persistence separates).
   Cost: medium.
5. **FVX — vent-chain flexure extrapolation** (external GDR vents CSV already pinned in
   the data manifest + band 12 `det_elev`). **Deprioritized**: H86I-HVFD implemented a
   vent-flexure variant (negative); listed only to close the queue honestly.

Next experiment recommendation: BMR (rank 1) as a *surface* ranked on catalogue
hide-and-recover vs the tomography belief's B5∩C core mask; if its top decile captures
withheld components the core mask misses, fuse as a fourth belief and re-emit — this is
also the cleanest path to dots that are geological *and* fleet-independent.

## Three-pass log

- **Pass 1:** E1 geometry, E2a hit-rate tomography (degenerate: K→5,055 bound, p∈{0,1} —
  dotted vs thick rasters cannot share one credit-per-hit), E2b belief-density rebuild,
  E3-v1 bar-stopped emission (23,517 dots; uniqueness cap failed at 0.786; binaries deleted).
- **Pass 2:** Model-misspecification fixes (Amendments A/B): fixed 37,654 budget, SGMC
  demoted after measuring live-Spearman −0.11 (top range), running-ratio uniqueness gate,
  model-averaged belief. E3-v2 passed uniqueness+SGMC, failed coarse belief; E3-v3 tied it.
- **Pass 3:** Amendment C materiality restatement (exact deltas kept), deterministic
  re-issue (identical SHA), independent 15/15 format re-validation, full 655-raster
  registry scan (0 firings), surface reconstruction check. Remaining known gaps are listed
  under Limitations, not hidden.

## Limitations & what the owner/selector must still do

1. **No organizer receipt exists for any number in this lane.** Input scores are
   OWNER-REPORTED; if any is mis-transcribed, belief shifts. `poisson81` was excluded for
   exactly this inconsistency (predicted 0.084 vs reported 0.0041 under all fits) — see
   `IRREGULARITIES.md` IR-86-H86M-POISSON81. Its local binary may not be the submitted bytes.
2. **Repo-wide gates not run/updated for this lane:** `audit_release.py` needs a new
   `holdout_kind` branch for tomography-LOO before this artifact can enter
   `docs/evidence/download-inventory.json`, and the literal dense-witness reading in
   `protocol_preflight` still returns DO NOT SUBMIT for *every* nonempty raster
   (documented unsatisfiable; PA-86 like-for-like is the operative reading used here).
   `build_site.py` was therefore not regenerated; the lane page is `docs/h86m-lt.html`.
   Main already fails `check_site`/`pytest` (16) over H86L-FMC's missing inventory entry;
   this session did not repair that upstream lane.
3. **Belief is fleet-feedback, not new geology.** If the whole fleet shares a systematic
   blind spot (e.g. faults under young basalt with no mag/grav/topo expression), this
   candidate inherits it; the ratio gate forces 36 % of dots into second-tier belief,
   which mitigates but does not remove fleet bias. BMR/EQL above are the fleet-independent
   follow-ups.
4. **Slot decision is not automated away:** `approved_for_weekly_slot=false`,
   `submission_slots_used=0`. The selector must confirm the weekly cap on the submission
   page (human browser only, per DrivenData terms) and archive the organizer receipt in
   `ledger/submissions.csv` if submitted; only then can any number become ORGANIZER-CONFIRMED.
5. Data provenance: `training_features.tif` restored this session from the hash-pinned
   GitHub mirror (`4371c82e…`, `scripts/restore_data.py`) — byte-identity with the mirror,
   not independent organizer authentication. DrivenData itself was not scraped (terms).

## Official sources (for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules PDF (NLR 96647): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- GeoDAWN surveys (USGS): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS (GBCGE): https://gbcge.org/current-projects/ingenious/
- GDR submission 1391: https://gdr.openei.org/submissions/1391
- EPSG:32611: https://epsg.io/32611 · Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- GEMSDOE32 (owner-reported 0.2778 source): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

## Postscript (merge-time, 2026-10-25): parallel BMR/CNT results

While this lane ran, a parallel session executed BMR and CNT (from the same followup
queue) and merged to main: BMR HOLDOUT-DTI 0.0220 [0.0086, 0.0384] (11,321 withheld),
beaten by its raw-gravity control; CNT 0.0408 [0.0257, 0.0575], paired CIs vs controls
cross zero — both negative (`registry/artifact_cards.json`, DO NOT SUBMIT). The
"next experiment: BMR" recommendation above is therefore **already answered (negative)**
and should not be re-run unchanged; EQL (earthquake-lineation anisotropy, bands 10/16)
becomes the top untried fleet-independent follow-up. This lane's candidate was additionally
checked against the three new main artifacts at merge time: forward 3-px overlap
**0.0688** (BMR), **0.1066** (CNT), **0.1959** (DAMAGERING) — all far below the 0.70 stop,
confirming the tomography lane is spatially distinct from the parallel geological lanes.
