# GAPRES session 2026-10-24 — unique TIF generated; automated verdict 🔴 DO NOT SUBMIT

## Why h33 scored 0.2778 (OWNER-REPORTED, no organizer receipt in repo)
Re-verified from `data/scored_fleet/GEMSDOE32__...h33-h33-2-b2...tif`: 37,654 binary
dots, 0 on-catalogue. Prior forensic work in this repo (H86E report) shows it is the
H19-5 multiline-corroborated ridge ancestor, Poisson-dotted at 2.8 px, then pruned of
dots ≤2 px from the catalogue (B2). Dotting converts saturated ridge coverage into
cheap kernel credit (DTI α=0.2/β=0.8, 300 m triangular kernel); B2 removes mass whose
kernel mostly covers already-known faults. Beating it requires a better *surface*,
not more emission rearrangement (53 prior variants, |Δ|≤0.0073 on surrogates).

## Ranked hypotheses (this lane assignment = #1 only)
1. **GAPRES fleet-gap interpolation** — layers: 26 local dotted fleet rasters as a
   vote field; signature: Gaussian σ=2 px vote-density maxima in pixels >3 px from
   every fleet dot and >2 px from catalogue. Why unmapped: collectively traced but
   unsampled lineament gaps. Novelty: all prior fleet work blended/copied dots
   (XFleet ~100% overlap, duplicate); none emitted *only* the complement gaps.
   Mimic: common-mode lithologic/survey lineaments. Cost: low. **RUN.**
2. H86E-MMT magnetic marker phase translation — requires `training_features.tif`;
   it was in fact restorable via `scripts/restore_data.py` (verified this session,
   sha `4371c82e…`), so viable for a *future* lane, not run (budget/lane).
3. H86E-HMDC hydrothermal magnetite-destruction + vent alignment — needs GDR 1391
   point data pinned; not run.
4. SPBT signed paired-throw — already falsified 2026-10-24 (HOLDOUT-DTI 0.0310).
5. Watershed LiDAR micro-scarps — needs USGS 3DEP tiles pinned; not run.

## Experiment 1 (only experiment)
`scripts/build_gems86_gapres.py` → 37,654 dots, allowed pool 926,448 px.
- HOLDOUT-DTI (gems57-pooled-hide-v2, n=22,641 withheld positives): **0.0000**,
  95% CI [0.0, 0.0] (fold-percentile) vs h33 same-instrument 0.0044. **Fails.**
  Caveat: fleet parents used the full catalogue, so this proxy is conservative —
  but under the protocol a non-beating holdout cannot promote.
- Leakage canary: smoothed vote alone AUC 0.632 (<0.90, no leakage flag).
- Uniqueness vs 26 local dotted fleet rasters: worst 3-px dot overlap **0.000**,
  worst |surface Spearman| (200k sample) **0.141**. Unique under the dotted reading.
- Literal dense-witness reading: 1.0 for any nonempty dots (continuous witness) —
  flagged IR-86-GAPRES-01; the rule as written is unsatisfiable, reported not waived.
- Validator (`gems57.validate`): all checks pass — single-band float32, EPSG:32611,
  3730×3292, transform matches sample, 0 NaN/inf, values exactly {0,1} ⊂ [0,1],
  zeros outside footprint (fixes the user's "Predicted values must be in range [0,1]"
  portal error, caused by NaN-outside exports), 0 dots on catalogue.
- sha256 `0af386ec51f12d74df838a6344e2ce85a5a38efd421a198cb3ecf8be1ee72b1c`

## Deliverable & verdict
File: `docs/downloads/gems86-gapres-fleetgap-37654dots-20261024T192023Z-8e34901f-zeros.tif`
(+ one-TIFF ZIP + JSON receipt beside it, listed on the site Downloads section).
**🔴 DO NOT SUBMIT — it is obvious: this report, the run card, the sidecar, and the
site banner all say so. No weekly slot used; promotion is a separate selector step
and this candidate does not qualify.** Negative result is the deliverable.

Run card: `docs/evidence/gapres-run-card.json`
