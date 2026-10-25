# H86F-PCC review — 2026-10-25

## Decision

**DO NOT SUBMIT.** A new format-valid GeoTIFF was generated and is safe to download for audit. It is not cleared for a weekly slot. No DrivenData login was used, no organizer receipt exists, and no slot was spent.

- TIFF: `docs/downloads/gems86-h86f-pcc-signed-44090dots-20261025T002755Z-94f74d4e-zeros.tif`
- SHA-256: `7a0dcffb09634de1fb8bf381a358a3fee7508735c9688cd682c1f13a99dec7be`
- Name: `gems86-h86f-pcc-signed-44090dots-20261025T002755Z-94f74d4e-zeros`
- Note (110 characters): `H86F-PCC signed grav-RTP-basement polarity, survey-axis veto; holdout is not a leaderboard score; no slot used`
- Run card: `docs/evidence/h86f-pcc-run-card.json`

## Why the owner-reported 0.2778 is not a target this file beat

`0.2778` is **OWNER-REPORTED** for `h33-h33-2-b2` (GEMSDOE32). This checkout has **no organizer receipt**. The prompt's `0.3195` and `0.4413` are also owner claims. This session did not open the DrivenData leaderboard: automated access is disallowed, and there is no login.

Pixel-exact comparison already in this repository shows what that file is. `GEMSDOE32` `h33-h33-2-b2` (37,654 unit dots) differs from pinned `GEMSDOE28` `d2.8` (40,199 dots; owner-reported `0.2708`) by deletion of the 2,545 dots in the `1 < d_cat ≤ 2` px mapped-fault collar, and by nothing else (0 of 12,279,160 cells differ after that deletion). Owner-reported fleet scores above `0.2600` in the supplied inventory sit in that same `H19-5` / `d2.8` lineage, with 3 px overlap about `93–100%`.

The official-form metric used here is

`DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)`,

with a 300 m triangular kernel. Deleting redundant dots inside that kernel can raise DTI when the deleted mass was mostly false-positive weight. That algebra can explain a small live gain from `0.2708` to `0.2778` if those owner numbers are real. It does not identify a new geological layer, and it is not a projection.

The same parent, rebuilt on this lane's holdout with the visible-fault collar, scores **HOLDOUT-DTI 0.0339**, 95% CI `[0.0160, 0.0497]` (`gems57-pooled-hide-v2`, 11,321 withheld positives). A live claim of `0.2778` and a catalogue-recovery holdout of `0.034` are different instruments. Catalogue recovery is not the private test of faults missing from the catalogue. That gap is why a holdout win would still not be a leaderboard projection, and why a holdout loss forbids spending a slot.

## What this lane tested

Preregistered before the run (`research/H86F_PCC_PREREGISTRATION.json`). Candidate arm `E1_pcc_signed`.

A basement step under cover should make the isostatic-gravity gradient and the RTP gradient point toward the footwall, and the depth-to-basement gradient point the other way. Anti-parallel magnetic-gravity edges score zero. Survey-axis gradients (GeoDAWN flight lines at azimuth 90°, tie lines at azimuth 180°; [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)) are down-weighted. Catalogue pixels are not features. Emission uses the shared 3 px decimated ranker and the shared writer. The feature TIFF has 19 bands; Band 6 is radiometric total count and was not used as tilt. There is one conductivity band, not a stack of MT depth slices, so a depth-migrating MT hypothesis is not viable from this file.

Named non-fault mimic: an unfaulted facies contact or volcanic flow edge, and residual flight-line corrugation.

## Measured result

All of the following are **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, seed 20, 3 px visible collar, 44,090-dot budget. Not organizer scores.

| Arm | DTI | 95% CI |
|---|---:|---|
| E1 signed polarity (candidate) | 0.0327 | [0.0237, 0.0436] |
| E2 cover-weighted control | 0.0275 | [0.0192, 0.0368] |
| E3 unsigned alignment control | 0.0247 | [0.0189, 0.0315] |
| R0 / D2.8 visible-collar control | 0.0339 | [0.0160, 0.0497] |
| H33 visible-collar control | 0.0336 | [0.0157, 0.0496] |
| Historical same-split KSLB comparator (not re-run) | 0.1241 | [0.1080, 0.1403] |

Paired delta of E1 versus R0: **−0.0011**, 95% CI **[−0.0199, +0.0192]**. The interval includes zero. E1 does not beat KSLB. The signed arm beat its own unsigned and cover controls on the point estimate, so the polarity constraint was slightly more specific than generic edge ranking, and still useless for recovering hidden catalogue segments.

**LEAKAGE-CANARY:** maximum discriminative AUC **0.5502** (topographic veto). No feature exceeded 0.90. AUC near 0.5 means the fields are not secretly the catalogue. It also means they do not locate the withheld faults.

**REGISTRY-MEASUREMENT:** 685 of 687 indexed rasters compared; 2 are not on the submission grid (`14GEMSDOE` horse-ensemble CRS/transform; `7GEMSDOE` qfaults prior shape). Worst surface Spearman **0.3406**. Worst final-dot Spearman **0.0285**. Both are below 0.90, so this is not a rank-correlation copy of another lane. Eleven dot-field forward overlaps exceed 70%. A diagnostic using the shared 3 px dilation found all 11 are space-filling (chance coverage 0.73–0.999; excess over chance ≤ +0.001; informative firings **0**). The shared `pa86_chance_overlap.py` script refused to score the incomplete report. That refusal is recorded. The diagnostic is not a gate pass. Literal overlap with the full-support `17GEMSDOE` witness is 1.0, as it is for every nonempty file in this repository.

**LOCAL-FORMAT-VALIDATION:** single-band float32, 3730×3292, EPSG:32611, sample transform, finite values in [0, 1], zero outside the footprint, zero positives on the mapped catalogue, 44,090 positive cells, one-TIFF ZIP. This file would not reproduce the portal error “Predicted values must be in range [0, 1]”. That does not make it submittable.

## Ranked hypotheses considered before the run

1. **H86F-PCC signed basement-step polarity** — run. Expected the best information per cost among ideas not already implemented. Result negative on this holdout.
2. **H86F-RAD K/Th alteration along dilatation** — not run. Needs the pinned radiometric grid. Mimic is rhyolite/basalt lithology. Lower priority after PCC failed to beat even the unsigned edge control by a useful margin.
3. **H86F-MTMIG dipping-conductor updip projection** — not viable. `training_features.tif` has 19 bands and one `cond_surf` band. USGS 3D MT DOI `10.5066/P9TWT2LU` is not mirrored here.
4. **Watershed-crossing chi knickzones and unsigned mag-grav alignment** — already represented by KSLB and H86-WVB. Not a new lane.
5. **Pairwise sinter geodesics** — not run. Point compilations do not recover 11,321 withheld catalogue pixels unless the points lie on those segments. That is a different question from this holdout.

## What remains

A file that can be uploaded has to beat the same-split holdout best (**HOLDOUT-DTI 0.1241**, KSLB, 11,321 withheld positives) with separated intervals, pass a complete same-grid registry scan, and still be selected by a human within the weekly cap. This lane did not do the first of those. Do not upload this TIFF.
