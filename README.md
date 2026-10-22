# GEMSDOE86 — auditable GEMS fault-discovery workbench

> **Submission status: BLOCKED. There is no competition GeoTIFF in this checkout. Do not treat this repository as having a file that is ready to download or submit.** No training rasters, labels, cached feature stack, holdout evaluator, submission writer, or validation receipt are present. Creating a dummy raster would not be a scientifically defensible or demonstrably unique submission.

## Project charter (read before every project session)

The goal is to develop and maintain an auditable, scientifically grounded workflow for detecting faults that may indicate geothermal resources in the DOE GEMS / GeoDAWN challenge, and—only after validation—to provide an obviously named, one-click downloadable GeoTIFF that is safe to submit. The competition is about faults, not direct geothermal-vent detection. The user's strategic aim is to improve leaderboard performance, but no score or improvement may be claimed without evidence.

**Core values:**

- **Maximize P(Win):** protect scarce submission opportunities; test ideas on spatially blocked holdouts before any real submission slot is considered.
- **Own the Outcome:** check the complete path from scientific hypothesis through holdout, file writing, byte-level validation, provenance, and honest presentation. Report negative results and blockers rather than disguising them.

**Non-negotiable experiment protocol:**

1. Work only in the assigned experimental lane. Before placing predictions and again on final predictions, compare against each registry raster: stop and record a duplicate if rank correlation exceeds `0.90` or more than `70%` of candidate dots are within `3 px` of one registry raster's dots. Do not claim uniqueness without these checks.
2. Reuse the shared cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; score pooled DTI with `alpha=0.2`, `beta=0.8`, and a 300 m triangular kernel. Fix a shared tool in its template, not in a private fork. **This checkout currently contains none of these tools.**
3. Label every score as either **HOLDOUT-DTI** (evaluator version, number of withheld positives, and 95% CI) or **ORGANIZER-CONFIRMED** (copied from an organizer submission-page receipt). A projection is never a score. Do not relabel owner reports or leaderboard rows as receipts.
4. Run each feature alone as a leakage canary before trusting it; an AUC above `0.90` is leakage until disproved.
5. Keep a run card with hypothesis, mechanism, named non-fault mimic, holdout result and CI, registry similarity, raster SHA-256, format-validator result, submission name/note (note at most 140 characters), and promote/negative verdict.
6. Stop after three experiments or two hours. Do not choose/promote a real submission here; selection is separate and subject to the weekly cap.

**Submission gate:** only show a download as ready when an actual generated single-band float32 GeoTIFF has been reopened and checked against the official template for CRS, shape, transform, footprint, finiteness/no NaN within the footprint, and values in `[0,1]`. The official competition page requires EPSG:32611, 100 m resolution, matching bounds, null/NaN outside bounds, and one float32 prediction layer in `[0,1]`. Preserve the validated artifact and its SHA-256; do not offer an unvalidated placeholder.

**Research and provenance:** prefer official, freely accessible sources; record exact URLs, access dates, licenses, and whether the source was actually fetched. Separate observed measurements, holdout estimates, projections, owner-reported claims, and organizer results. Review the competition prompt and this charter at the start of each project session. Keep generated rasters and large data out of Git unless required.

## Current review findings

This branch's starting repository had only this README. There is no code or data to run, no cached raster stack, no registry rasters for the duplicate gate, and no shared holdout/evaluator/writer to reuse. DrivenData's competition data URL resolves to a login page from this environment. Therefore this session cannot validate a candidate or create a defensible unique TIF. The correct result is a documented **negative / blocked** outcome, not a fabricated file.

The supplied result list includes several scores and the question about the H33 artifact. Those entries are user-provided claims, not evidence that the linked raster received that score. The linked GEMSDOE32 page itself calls its H33-2-B2 projected value a model rather than a score and says no organizer score exists for that artifact. See [`docs/research-and-run-card.md`](docs/research-and-run-card.md) for the source-by-source review, hypotheses, blockers, and run card.

## Site / executive summary

The repository GitHub Pages entry point is [`index.html`](index.html). It is deliberately explicit that there is currently **no safe file to download**. Submission instructions and scientific evidence status are in [`docs/research-and-run-card.md`](docs/research-and-run-card.md).

## Verified primary sources

- [DrivenData problem description, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login is required in this environment.
- [DrivenData live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS Great Basin Regional Dataset Compilation (GDR 1391)](https://gdr.openei.org/submissions/1391)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)
- [Competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
