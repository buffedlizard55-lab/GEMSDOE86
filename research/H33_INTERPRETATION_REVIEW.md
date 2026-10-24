# H33 interpretation review — 2026-10-24

## Decision and scope

**DO NOT SUBMIT. No new unique TIFF was generated.** Fresh automated measurement of the pinned registry witness still blocks every nonempty allowed prediction under the literal overlap rule. This review corrects scientific interpretation; it does not relax that rule or change the shared evaluator. No method paragraph was assigned in the request, so the existing ranked hypotheses remain provisional, not permission to enter another lane.

## What the H33 evidence does and does not establish

The user-reported H33 result is **OWNER-REPORTED 0.2778**, not ORGANIZER-CONFIRMED. The prompt also gives conflicting current leaderboard claims (OWNER-REPORTED 0.3195 and 0.4413). Neither is a verified target here. The archived pixel identity explains *what changed* between the parent and H33, not *why hidden organizer truth rewarded it*. An organizer receipt and controlled same-support evaluation would be needed for the stronger conclusion.

Corrections applied to the generated homepage and earlier session report:

- Dot separation near one kernel radius does **not** make kernel supports disjoint. Two radius-R disks overlap for separation below 2R. On the pixel grid, dots separated by three pixels can both cover the same truth cell under the shared triangular kernel. Credit at that truth cell is the maximum, not the sum.
- An off-catalogue dot in a two-pixel catalogue collar can still recover an unmasked hidden fault. Only mapped pixels are masked exactly; the entire surrounding kernel is not removed. Thus collar pruning is a plausible reduction of low-credit prediction mass, **not proof that all removed dots had zero credit**.
- Increasing dot count can improve recovery if the added dots cover previously missed truth. Adding redundant, imperfectly matched dots can instead increase false-positive cost without improving truth credit. Density alone does not determine DTI.
- Cross-project comparisons change geology features, geographic support, decoder, and density simultaneously. They cannot establish density as the cause of their owner-reported score differences.

`tests/test_scientific_interpretation.py` checks all four statements with synthetic arrays and the unchanged shared `gems57.metric` implementation. These are **SYNTHETIC-METRIC-CHECKS**, not HOLDOUT-DTI, model experiments, projections, or organizer results. No synthetic scalar is presented as a competition score.

## Ranked research plan (unchanged; not run)

The previously registered candidates in `registry/h86c_hypotheses.json` remain the plan, ranked qualitatively by plausible upside and implementation cost, **not numerical expected score gain**:

1. Signed basement-depth / isostatic-gravity paired throw beneath low-relief cover. Low–medium cost; paleovalley margins are the non-fault mimic.
2. Two-sided magnetic-marker phase translation. Medium–high cost; survey seams and primary volcanic boundaries are mimics.
3. MT conductance × geodetic dilatancy. Not viable in this sandbox until official grids are obtainable and pinned; saline playas are a mimic.
4. Watershed-crossing native LiDAR micro-scarps. Not viable until official tiles are obtainable and pinned; shoreline benches and terrace risers are mimics. The earlier multi-hour estimate must not override the two-hour session budget.

Specific layers, physical signatures, catalogue-missing rationale and repository novelty are documented in `SESSION_20261024_REVIEW.md`. These are hypotheses, not established fault-discovery facts. The top candidate was **not** run: the mandatory preflight stops before fitting or placement. Existing historical holdout outcomes must not be relabeled as validation of these hypotheses.

## Sources and access boundaries

- Official reference repository: https://github.com/drivendataorg/gems-prize-reference-solution
- Immutable archived official README: https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md
- Official competition problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules URL supplied by the user: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Prospective official regional data: https://gdr.openei.org/submissions/1391
- Prospective official MT release: https://doi.org/10.5066/P9TWT2LU

Only permitted GitHub source bytes were rechecked in this session using `scripts/review_sources.py`. Direct portal, PDF, DOI and GDR verification was **not performed this session** because those hosts are outside the sandbox allowlist. Earlier verification assertions are dated historical evidence, not a fresh independent source check. Mirrored competition rasters are hash-pinned owner mirrors, not organizer-authenticated data. The official reference README explicitly supports CPU-only execution; GPU access is not universally required.

## Three-pass record

1. **Implement and verify:** Read standing prompt, full README and prior-session review; restored hash-pinned proof inputs; remeasured every published historical artifact against the witness. Added synthetic regression tests and corrected causal and geometry overstatements. No model experiment or weekly slot used.
2. **Review edge cases:** Tests explicitly cover shared truth credit, useful collar predictions, helpful additional dots, and harmful redundant dots. This prevents replacing one blanket density claim with its opposite. Shared tool bytes and protocol thresholds are unchanged.
3. **Final recheck:** Full test suite: 448 passed, 24 skipped, 32 subtests passed; skips remain explicit and are not fresh model validation. Release audit, read-only site build check, site link check and download audit are required before merge. The machine-readable final decision is `docs/evidence/latest-review-run-card.json`; fresh audit receipts do not refresh historical holdout claims.

## Remaining work

A protocol amendment distinguishing dense probability rasters from sparse dot sets is necessary before a nonempty candidate can comply; it cannot be invented by this agent. Once authorized, restore the actual shared feature cache, run isolated-feature canaries and whole-segment buffered holdout, compare on an identical split with paired confidence intervals, and perform surface and final-dot registry checks. Promotion stays a separate selector step. Live quota and organizer confirmation remain unknown. No leaderboard improvement or submission readiness is claimed.
