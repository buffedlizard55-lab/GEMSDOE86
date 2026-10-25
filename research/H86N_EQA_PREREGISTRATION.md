# H86N-EQL preregistration — earthquake-lineation anisotropy

**Date:** 2026-10-25 (UTC), session `arena/92f9e0e8-gemsdoe86`. Frozen **before** any holdout
scoring or dot placement for this lane. Hypothesis queue: `registry/h86n_hypotheses.json`
(rank 1 of 5). One unsupervised pilot is disclosed: band-distribution inspection of the
prepared arrays (min/percentiles/NaN fraction of bands 10/16, no labels, no holdout), used
only to choose rank/log transforms.

## Hypothesis (single lane)

Where the seismicity fields of `training_features.tif` — Band 10 `deq_n100a15` and Band 16
`ieq_n100a15` (indices verified against `src/gems86/io.py` `BANDS`) — are both **present**
and **linearly organized at ~600 m scale**, they trace active fault segments, including
segments missing from the surface-mapped USGS/INGENIOUS catalogue. The discriminator is
structure-tensor **coherence**: fault-hosted microseismicity is anisotropic (line-like),
whereas geothermal induced-seismicity clusters and background seismicity are isotropic
(cloud-like) at the same scale.

**Band-semantics honesty:** this repo glosses B10 as an earthquake proximity field and B16
as an intensity/density field (`research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md`); the
organizer's exact definitions are not independently verified here. The lane therefore uses
only `log1p` + rank-percentile transforms, so any monotone redefinition of either band
leaves the surface unchanged. A free official rebuild source exists if semantics must be
settled later: USGS ComCat FDSN event service, https://earthquake.usgs.gov/fdsnws/event/1/
(not required for this lane).

**Mechanism.** DTI (α=0.2, β=0.8, 300 m triangular kernel, shared `vendor/gems57` metric)
pays for precision-weighted coverage near hidden truth and taxes every non-crediting dot.
A coherence-gated seismicity surface concentrates the fixed dot budget on line-like
seismicity instead of cloud-like seismicity, which — if lineations are fault-hosted —
raises expected truth credit per dot relative to isotropic density at the same budget.

**Named non-fault mimics.** (1) Geothermal-field induced seismicity (radial clusters —
rejected by coherence in principle, residual risk retained); (2) quarry/blast and
catalogue-location artifacts aligned along network geometry; (3) smoothed-field ridges
where two isotropic clusters happen to bridge. Control C0 (below) is the direct falsifier
for "anisotropy adds nothing beyond density".

## Frozen surface and emission

- Density: `d = rank_pct(log1p(B16))` averaged with `rank_pct(log1p(B10))` inside the
  footprint (NaN→footprint median before ranking; outside footprint excluded).
- Structure tensor of `s = gaussian(d, 1.5px)` gradients, integrated at `6px`;
  coherence `c = (λ1−λ2)/(λ1+λ2+ε)`; energy `E = λ1+λ2`.
- Candidate surface: `rank_pct( c * sqrt(E) * (0.25 + 0.75*d) )`.
- Controls (same emission rule): **C0_iso_density** `= d` (anisotropy falsifier);
  **C1_rtp_grad** = rank_pct |∇ Band 2 `rtp`| (generic potential-field edge baseline).
- Emission: fixed **37,654 dots**, minimum spacing **2.8 px**, eligible = footprint &
  `d_cat > 3 px` (per-fold visible catalogue inside holdout folds, full catalogue for the
  shipped raster), greedy by surface with deterministic tie-break (row, col).
- No catalogue-derived feature exists in any surface, so surfaces are fold-safe by
  construction; the catalogue enters only via the shared evaluator's truth/masking and
  the standard >3 px collar.

## Validation (all machine-checked; labels kept separate)

- `HOLDOUT-DTI`: shared `gems57-pooled-hide-v2` hide-and-recover
  (`buffered_component_draw`, seed 20, hide 0.20, buffer 3 px, boundary 12 px; pooled
  20 km physical-block bootstrap, 1000 draws) for candidate and both controls, with
  paired differences. Reported with evaluator version, withheld-positive count, 95 % CI.
  Never compared across different holdout designs; never a leaderboard projection.
- `LEAKAGE-CANARY`: single-feature AUC of each input/derived feature vs withheld truth;
  any AUC > 0.90 (symmetric) stops the lane as leakage.
- Uniqueness (PA-86-01/02 like-for-like, thresholds unchanged): surface Spearman and
  final-dot phi ≤ 0.90, forward 3-px overlap ≤ 0.70 vs every locally measured discrete
  dot-field in `data/scored_fleet/` + `docs/downloads/`; the literal full-support-witness
  reading is reported side-by-side (it blocks every nonempty raster and is not hidden).
  Registry scope actually measured is stated; incomplete scope is never called complete.
- Format: shared `submission_writer.write_submission` + `validate.validate` (single-band
  float32, EPSG:32611, 3730×3292, sample transform, values exactly {0,1} ⊂ [0,1], 0 NaN/Inf,
  zeros outside footprint, 0 dots on catalogue) — the portal "[0, 1]" error class is
  excluded by construction.

## Gates

`promote` requires **all** of: paired 95 % CI lower bound > 0 vs **both** controls;
canary pass; uniqueness pass (surface + final dots); exact 37,654-dot budget;
zero dots on catalogue; format validator all-pass. Anything else is `negative`
(DO NOT SUBMIT) and is still published as an audit deliverable. Regardless of verdict,
`safe_to_submit=false` and `approved_for_weekly_slot=false` in the run card (repo
publication guard, AGENTS.md rule 14): this session uses **0** weekly slots and picks no
submission. Budget: ≤ 3 experiments (E1 canary+surfaces, E2 holdout, E3 emission+registry),
≤ 2 h.
