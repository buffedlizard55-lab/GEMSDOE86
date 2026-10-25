# H86L-VFGR three-pass review — 2026-10-25

Decision: **DO NOT SUBMIT. No TIFF was written.** `safe_to_submit` is false. No weekly slot was used.

## What was asked

A unique competition GeoTIFF, values in [0, 1], matching the sample grid, with a machine-readable yes/no for download and submission. Before writing it: unused geological hypotheses, one validated on a spatially blocked holdout. Explain the owner-reported H33 value 0.2778 and whether a higher score is possible. Put the standing prompt in the README. Publish the decision on GitHub Pages.

## Hypotheses, frozen before the score

Ranked in `registry/h86l_vfgr_hypotheses.json` and `research/H86L_VFGR_PREREGISTRATION.md` before any holdout print. The shared filename `registry/h86l_hypotheses.json` belongs to the concurrent H86L-FMC lane.

1. **H86L-VFGR** — subtract the expected magnetic and gravity edge of the *visible* faults, then keep the residual edge. Selected.
2. **H86L-BMR** — residual gravity after a training-only basement-depth regression. Run as the third arm.
3. **H86L-GSST** — gravity-stress shear. Not run. The three-experiment budget was spent.
4. **H86L-CNT** — contact-versus-fault shape. Not run.
5. **H86L-FLOR** — flight-line orientation residual. Not viable here: this checkout has no flight-line azimuth raster, and the USGS DOI was not fetched.

## Pass 1 — implement and verify

`scripts/run_h86l_vfgr.py` used the shared evaluator `gems57-pooled-hide-v2`, the shared writer path, and the hash-pinned native bands (`4371c82e…`). The template cached feature stack was not present. That absence is stated on the run card; the native bands were not relabeled as the cache.

Leakage canary, 400,000 pixels, seed 86: E1 0.4823, E2 0.5343, E3 0.4918. All below 0.90.

Same-split HOLDOUT-DTI, 11,321 withheld positives, 1,000 physical-block draws, seed 520810:

| Arm | HOLDOUT-DTI | 95% CI |
| --- | ---: | --- |
| E1 visible-fault residual | 0.0313 | [0.0230, 0.0395] |
| E2 raw edge, subtraction off | 0.0367 | [0.0272, 0.0457] |
| E3 basement-mass residual | 0.0285 | [0.0196, 0.0370] |
| H33-as-is, same folds | 0.0037 | [0.0030, 0.0044] |

Paired E1 minus E2: **−0.0054 [−0.0082, −0.0026]**, entirely below zero. The subtraction made the holdout worse. E1 minus E3 crosses zero. E1 beats H33-as-is on this catalogue-hide split only because H33 avoids the mapped catalogue; that 0.0037 is not H33’s live score.

Surface worst Spearman against 701 local rasters: 0.3706, with 0 firings above 0.90. Final 37,654 dots: 6 informative overlap firings. The substantive one is `GEMSDOE46` `SUBMISSION-GEMSDOE46-dfa-corroborated.tif` and its twin: overlap 0.7013, their halo coverage 0.1965, their dot count 37,654. That is a lane collision, not a space-filling lattice. The writer stopped. No TIFF, no ZIP, no SHA-256.

## Pass 2 — bugs, assumptions, edges

- The unit test first required the visible-fault residual to fall below 0.05. A two-pixel Gaussian cannot erase a one-pixel spike under least squares. The test now checks relative suppression, which is what the operator actually does. The holdout, not the synthetic test, decided the hypothesis.
- `registry_complete` is false even though 0 of 655 inventory files were missing. Some measured rows failed the grid check, including known off-grid historical files. Missing files and invalid files are both fail-closed. This did not create the duplicate stop; the measured GEMSDOE46 overlap did.
- `depth_to_base_surf` ranges from −14.84 to 7135.31 on the footprint. A negative depth-to-basement is a data irregularity. The basement regression still fit (training R² 0.383 on the canary mask) and still lost.
- H33-as-is emitted 7,074 to 10,184 dots inside each quadrant because the file already exists. It was not refit. Its tiny holdout is the expected cost of a collar around the catalogue when the hidden positives are catalogue segments.
- The 13GEMSDOE archive hits (overlap 0.701–0.710, halo coverage 0.646–0.680, 246k–344k dots) are threshold firings against dense archives. They are reported. They are not the reason this lane is a copy. GEMSDOE46 is.

## Pass 3 — full request

| Request | Result |
| --- | --- |
| Unique TIFF in [0, 1] | Not written. A duplicate file would violate the uniqueness rule. |
| Obvious download/submit status | Homepage and executive summary say NO, with the measured reason. Historical downloads stay audit-only. |
| Why H33 is 0.2778 | Still an owner report, not an organizer receipt. This repo has 0 receipt rows. The pixel audit in `research/ARENA_REPO_REVIEW_20261025_FOLLOWUP.md` stands: one finite positive edit on a zeros file. |
| Can a higher score be produced here? | Not from this lane. E1 lost to E2. No organizer-confirmed score was created. |
| Standing prompt in README | Already present; this session’s decision is now the lead. |
| Portal [0, 1] error | No new file was offered to the portal. The rejected upload is not in this checkout, so its exact cause remains unknown. The shared writer still refuses nonfinite and out-of-range values. |
| Three review passes | This file. |
| Pull request and merge | Done only after this review is in the commit. |
| Run card | `docs/evidence/h86l-vfgr-run-card.json`. |

No claim in this review is an ORGANIZER-CONFIRMED score.
