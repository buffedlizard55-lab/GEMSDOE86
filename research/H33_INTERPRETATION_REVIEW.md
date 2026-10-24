# H33 interpretation review — 2026-10-24

## Decision and scope

**DO NOT SUBMIT. The requested new unique TIFF remains unmet.** Fresh measurement shows the pinned registry witness covers every allowed pixel, so the unchanged literal overlap rule blocks every nonempty candidate before feature construction. This review does not relax that rule or change the shared evaluator. Current untried priorities are in `registry/untried_hypotheses_20261024.json`; H86E-MMT is top-ranked but not validated. No method result is authorized by this report.

## What the H33 evidence does and does not establish

The user-reported H33 result is **OWNER-REPORTED 0.2778**, not ORGANIZER-CONFIRMED. The prompt also gives conflicting current leaderboard claims (OWNER-REPORTED 0.3195 and 0.4413). Neither is a verified target here. The archived pixel identity explains *what changed* between the parent and H33, not *why hidden organizer truth rewarded it*. An organizer receipt and controlled same-support evaluation would be needed for the stronger conclusion.

Corrections applied to the generated homepage and earlier session report:

- Dot separation near one kernel radius does **not** make kernel supports disjoint. Two radius-R disks overlap for separation below 2R. On the pixel grid, dots separated by three pixels can both cover the same truth cell under the shared triangular kernel. Credit at that truth cell is the maximum, not the sum.
- An off-catalogue dot in a two-pixel catalogue collar can still recover an unmasked hidden fault. Only mapped pixels are masked exactly; the entire surrounding kernel is not removed. Thus collar pruning is a plausible reduction of low-credit prediction mass, **not proof that all removed dots had zero credit**.
- Increasing dot count can improve recovery if the added dots cover previously missed truth. Adding redundant, imperfectly matched dots can instead increase false-positive cost without improving truth credit. Density alone does not determine DTI.
- Cross-project comparisons change geology features, geographic support, decoder, and density simultaneously. They cannot establish density as the cause of their owner-reported score differences.

`tests/test_scientific_interpretation.py` checks all four statements with synthetic arrays and the unchanged shared `gems57.metric` implementation. These are **SYNTHETIC-METRIC-CHECKS**, not HOLDOUT-DTI, model experiments, projections, or organizer results. No synthetic scalar is presented as a competition score.

## Current ranked research plan and tested-method boundary

The live plan is `registry/untried_hypotheses_20261024.json`; it contains five untested hypotheses, no measured candidate scores, and a separate list of prior experiments. The original `registry/h86c_hypotheses.json` remains an archived preregistration snapshot, not current experiment history. This review ranks qualitatively by fault-mechanism fit, current evidence, data readiness, and implementation cost—never by numeric score projections.

**Previously tested:** The standalone signed paired-throw SPBT E1-E2 implementation used basement/gravity flank concordance but did not include Laplace-gravity-curvature `g_zz`. It was reported negative against controls: weighted **HOLDOUT-DTI `0.0280`**, 95% CI `[0.0143, 0.0435]`, `gems57-pooled-hide-v2`, `11,321` withheld positives; polarity-scrambled control `0.0314 [0.0202, 0.0438]`; spaced random `0.0333 [0.0284, 0.0377]`. This does not test the distinct SPBT-Laplace extension. H86E-CCTX was also run and not promoted; its archived HOLDOUT-DTI was `0.1037`, 95% CI `[0.0854, 0.1216]`, same evaluator and withheld-positive count. Both are prior results, not current validation.

1. **`H86E-MMT` — Cross-corridor magnetic-marker translation (priority 1).** Bands 2 (`rtp`), 3 (`tmi_hg`), 9 (`tmi_vg`), and 6 (`tc`, radiometric Total Count only as a surficial-contact control). Detect coherent two-sided lateral translation of a marker across adjacent strike windows; compare with zero-shift and phase-scrambled controls. Buried transfer faults may offset markers without a prominent scarp. Mimics: intrusive contacts, volcanic-flow terminations, remanence, and survey seams. Medium-high, unbenchmarked cost; competition feature data/cache are absent locally. The mechanism is the most directly fault-aligned of this current queue, but remains low-confidence and untested.
2. **`H86E-SPBT-LAPLACE` — Paired throw plus Laplace-gravity-curvature extension.** Bands 15, 13, 18, 11, 12, 19, and 3. Adds a masked/regularized `g_zz = -(d_x Band18 - d_y Band11)` constraint to signed basement/gravity steps. This is not the standalone SPBT already tested. Gravity quantities share source ancestry and are not independent observations. The negative standalone result lowers the extension's qualitative prior; mimics include paleovalley/caldera boundaries, inversion artifacts, and resampling noise. Medium-high, unbenchmarked cost; untested and blocked.
3. **`H86E-HMDC` — Hydrothermal magnetic-trough / paleo-sinter corridors.** Combine RTP/magnetic-trough geometry, shallow conductivity/strain, and GDR 1391 sinter plus 2 m temperature locations. Concealed conduits might be fault-associated, but the target is faults, not vents; point-location controls and per-layer leakage canaries are mandatory. Mimics: low-susceptibility tuffs, remanence, saline playas, and survey lines. The official GDR page was previously retrieved, and pinned GitHub API metadata lists two archive entries; their raw bytes were not restored or SHA-checked here, so this is not viable now.
4. **`H86E-MTCS` — Multi-depth MT conductance × conductive heat flow.** Candidate official sources are USGS DOIs `10.5066/P9TWT2LU` and `10.5066/P9BZPVUC`; verify binary data, license, coverage, depth intervals, and native resolution before any use. Possible blind-fluid signature; graphitic/sulfidic units and basin brines mimic it. Not viable yet.
5. **`H86E-WCS` — Native 1 m 3DEP watershed-crossing scarps.** Test signed micro-scarp persistence across drainage divides against 100 m terrain controls. It targets surface-expressed, not blind, faults. Mimics: shorelines, terraces, channels, and roads. The competition tile-link CSV and raw tiles are absent; the mirrored derived feature is not a native tile. Not viable yet.

Official source links and data-access evidence are attached to each row of the current queue. The source audit at `docs/evidence/hypothesis-data-availability-20261024.json` distinguishes dated official-page observations, GitHub API metadata, expected manifest hashes, and locally restored bytes. It confirms no candidate is data-ready in this checkout. The reviewed repository/fleet scope does not prove global novelty.

The top candidate was **not run**. The witness blocks every nonempty allowed output before surface construction. Whole-segment buffered holdout recovery of known catalogue faults is itself an imperfect proxy for genuinely uncatalogued expert faults. No candidate score or private leaderboard improvement is inferred.

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
