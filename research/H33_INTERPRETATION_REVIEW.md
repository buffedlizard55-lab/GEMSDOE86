# H33 interpretation review — 2026-10-24

## Decision and scope

**DO NOT SUBMIT. No new unique TIFF was generated.** Fresh automated measurement of the pinned registry witness still blocks every nonempty allowed prediction under the literal overlap rule. This review corrects scientific interpretation; it does not relax that rule or change the shared evaluator. No method paragraph was assigned in the request, so the existing ranked hypotheses remain provisional, not permission to enter another lane.

## What the H33 evidence does and does not establish

**2026-10-27 correction:** The remeasured [pinned pixel audit](../docs/evidence/h33-identity-20261027.json) proves the 2,545-dot deletion only within the footprint. All 7,111,787 outside-footprint cells differ in encoding (parent NaN versus H33 zero). Earlier historical reviews claiming full-grid numerical identity or claiming that the deleted points had zero hidden-truth credit are superseded by this correction.

The user-reported H33 result is **OWNER-REPORTED 0.2778**, not ORGANIZER-CONFIRMED. The prompt also gives conflicting current leaderboard claims (OWNER-REPORTED 0.3195 and 0.4413). Neither is a verified target here. The archived pixel identity explains *what changed* between the parent and H33, not *why hidden organizer truth rewarded it*. An organizer receipt and controlled same-support evaluation would be needed for the stronger conclusion.

Corrections applied to the generated homepage and earlier session report:

- Dot separation near one kernel radius does **not** make kernel supports disjoint. Two radius-R disks overlap for separation below 2R. On the pixel grid, dots separated by three pixels can both cover the same truth cell under the shared triangular kernel. Credit at that truth cell is the maximum, not the sum.
- An off-catalogue dot in a two-pixel catalogue collar can still recover an unmasked hidden fault. Only mapped pixels are masked exactly; the entire surrounding kernel is not removed. Thus collar pruning is a plausible reduction of low-credit prediction mass, **not proof that all removed dots had zero credit**.
- Increasing dot count can improve recovery if the added dots cover previously missed truth. Adding redundant, imperfectly matched dots can instead increase false-positive cost without improving truth credit. Density alone does not determine DTI.
- Cross-project comparisons change geology features, geographic support, decoder, and density simultaneously. They cannot establish density as the cause of their owner-reported score differences.

`tests/test_scientific_interpretation.py` checks all four statements with synthetic arrays and the unchanged shared `gems57.metric` implementation. These are **SYNTHETIC-METRIC-CHECKS**, not HOLDOUT-DTI, model experiments, projections, or organizer results. No synthetic scalar is presented as a competition score.

## Ranked research plan (5 scoped hypotheses; not run)

The five pre-registered candidates in `registry/h86c_hypotheses.json` (`H86E-SPBT`, `H86E-MMT`, `H86E-HMDC`, `H86E-MTCS`, `H86E-WCS`) remain the plan, ranked qualitatively by competition-data self-sufficiency, verified band physics (`docs/evidence/band-physics-verification-20261024.json`), and implementation cost — **never by unmeasured numeric score projections**:

1. **`H86E-SPBT` — Signed paired-throw basement–Laplace-gravity concordance beneath low-relief cover:** Pairs antiparallel cross-strike steps in `depth_to_base_surf` (Band 15) and `iso_grav_anom` (Band 13) with the exact Laplace vertical gravity curvature zero-crossing $g_{zz} = -(\partial_x\text{B18} - \partial_y\text{B11})$ reconstructed from the pixel-verified signed horizontal gravity vector `(Band 18, -Band 11)` inside low-slope (`det_elev_slope` Band 19) basin interiors. Low cost; paleovalley margins and caldera rings are non-fault mimics.
2. **`H86E-MMT` — Cross-fault magnetic marker translation & competition-native radiometric `TC` contact decoupling:** Two-sided cross-corridor profile phase-lag on `rtp` (Band 2) and analytical magnetic tilt $\theta_{\text{mag}} = \arctan2(\text{Band 9},\, \text{Band 3})$, using competition-native `tc` (Band 6, pixel-verified GeoDAWN Airborne Radiometric Total Count `TC`, `r = +0.997140`) to reject surficial alluvial-fan gamma-ray wash boundaries. Medium cost; flight-line drape seams and basalt flow margins are mimics.
3. **`H86E-HMDC` — Hydrothermal magnetite-destruction & conductive clay-cap dilational corridor:** Pairs narrow linear magnetic-susceptibility troughs (`rtp` Band 2, `tmi_vg` Band 9) with elevated `cond_surf` (Band 17), radiometric `tc` (Band 6) alteration contrast, and active transtensional strain (`geod_dilaterate` Band 8, `geod_shearrate` Band 7), optionally enriched by CC-BY-4.0 GDR-1391 sinter/2-m temperature probe compilations. Low–medium cost; saline playa pans are mimics.
4. **`H86E-MTCS` — Multi-depth 3D MT conductance × convective heat-flow residual sharpened onto analytical magnetic tilt zero-crossings:** Uses USGS `10.5066/P9TWT2LU` + `10.5066/P9BZPVUC` sharpened onto $\theta_{\text{mag}} = \arctan2(\text{Band 9},\, \text{Band 3}) = 0$ (correcting the invalid Band 6 zero-crossing operator flagged in `IR-86-BAND6-TC-MISLABEL-20261024`). Not viable inside this sandbox until external ScienceBase grids are mirrored and pinned; graphitic shales are mimics.
5. **`H86E-WCS` — Multi-azimuth wavelet micro-scarp continuity on native 1-m USGS 3DEP LiDAR:** Tracks sub-meter scarps across `>= 3` drainage interfluves on native 1-m 3DEP DEM tiles. Not viable inside this sandbox until external 3DEP tiles are mirrored within the two-hour session budget; Lake Lahontan shorelines and terrace risers are mimics.

Specific layers, physical signatures, catalogue-missing rationale, cross-fleet novelty (including newly merged `GEMSDOE89`..`GEMSDOE92`), and repository novelty are documented in `SESSION_20261024_REVIEW.md` and `GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md`. The top candidate was **not** run: the mandatory preflight stops before fitting or placement. Existing historical holdout outcomes must not be relabeled as validation of these hypotheses.

## Sources and access boundaries

- Official reference repository: https://github.com/drivendataorg/gems-prize-reference-solution
- Immutable archived official README: https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md
- Official competition problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules PDF (DOE/NLR September 2026): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Official USGS GeoDAWN data release (`DOI 10.5066/P93LGLVQ`): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and *(note: legacy prompt link `https://www.usgs.gov/centers/gggsc/science/geodawn-geoscience-data-acquisition-western-nevada` returns USGS HTTP 404)*
- Official UNR GBCGE INGENIOUS project page: https://gbcge.org/current-projects/ingenious/
- Official DOE GDR Submission 1391 (`DOI 10.15121/1881483`, CC-BY-4.0): https://gdr.openei.org/submissions/1391
- Prospective official MT & Heat Flow releases: https://doi.org/10.5066/P9TWT2LU and https://doi.org/10.5066/P9BZPVUC

Permitted GitHub source bytes were rechecked via `scripts/review_sources.py`, and non-DrivenData official reference pages (`docs.nlr.gov`, `usgs.gov`, `doi.org/10.5066/P93LGLVQ`, `gbcge.org`, `gdr.openei.org`, `epsg.io`, `en.wikipedia.org`) were re-verified on `2026-10-24` in `docs/evidence/source-recheck-20261024.json` (never scraping `drivendata.org` per `AGENTS.md` Rule 9). Mirrored competition rasters remain hash-pinned owner mirrors, not organizer-authenticated data. The official reference README explicitly supports CPU-only execution; GPU access is not universally required.

## Three-pass record

1. **Implement and verify:** Read standing prompt, full README and prior-session review; restored hash-pinned proof inputs; remeasured every published historical artifact against the witness. Added synthetic regression tests and corrected causal and geometry overstatements. No model experiment or weekly slot used.
2. **Review edge cases:** Tests explicitly cover shared truth credit, useful collar predictions, helpful additional dots, and harmful redundant dots. This prevents replacing one blanket density claim with its opposite. Shared tool bytes and protocol thresholds are unchanged.
3. **Final recheck:** Full test suite: 448 passed, 24 skipped, 32 subtests passed; skips remain explicit and are not fresh model validation. Release audit, read-only site build check, site link check and download audit are required before merge. The machine-readable final decision is `docs/evidence/latest-review-run-card.json`; fresh audit receipts do not refresh historical holdout claims.

## Remaining work

A protocol amendment distinguishing dense probability rasters from sparse dot sets is necessary before a nonempty candidate can comply; it cannot be invented by this agent. Once authorized, restore the actual shared feature cache, run isolated-feature canaries and whole-segment buffered holdout, compare on an identical split with paired confidence intervals, and perform surface and final-dot registry checks. Promotion stays a separate selector step. Live quota and organizer confirmation remain unknown. No leaderboard improvement or submission readiness is claimed.
