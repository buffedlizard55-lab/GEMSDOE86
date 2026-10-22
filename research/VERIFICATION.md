# Three-pass verification record

## Pass 1 — implement and exercise

Reviewed the checked-out `arena/6d9cbb33-gemsdoe86` branch, its shared evaluator/writer, research notes, static site, run card, and tests. Restored the two small grid inputs through the pinned owner mirrors; their SHA256 values match the manifest. Checked the current pinned GEMSDOE32 owner-repository audit and submission manifest through GitHub API: the H33-2-B2 artifact is marked `UNSCORED` and has no organizer receipt. Rewrote the site and executive summary so there is no ambiguous or misleading download action, added the H33 method/evidence analysis, and made the run card explicitly record every unrun gate as null/negative.

## Pass 2 — bugs, assumptions, and edge cases

Confirmed that the assigned lane paragraph is absent, the pinned upstream feature-stack receipt points to an ephemeral `/tmp` path, and neither the pinned template tree nor GEMSDOE32 snapshot contains the required committed `.npy`/`.npz` stack. The current checkout also lacks the data-download, data-preparation, training, and inference entry points named in the request. Therefore no hypothesis was selected or tested, no private feature stack was rebuilt, no historical TIFF was downloaded or copied, and no submission slot was used. Preserved the shared tool files byte-for-byte. Extended tests to require a fail-closed run card, including an explicit false downloadable-TIFF flag and unrun validator/registry fields. Existing tests exercise NaN, Inf, sentinel, range, catalogue, footprint, metric-oracle, empty-truth, duplicates, and synthetic full-grid TIFF/ZIP round-trip behavior.

## Pass 3 — requirements and claim review

The final local verification on 2026-10-22 passed: all eight unit tests; Python compilation; `git diff --check`; the run-card contract (negative verdict, no candidate, 98-character note); local-link checks for the root page, dashboard, and executive summary; and SHA256 verification of both restored grid inputs. The run card labels the unrun evaluator as `HOLDOUT-DTI` with null result, withheld positives, and confidence interval, and labels the raster/format checks as not run. No score is reported as HOLDOUT-DTI or ORGANIZER-CONFIRMED. External DrivenData, USGS, GDR, and NLR pages were not re-fetched in this session; links remain available for manual review.

**Remaining blockers:** no unique candidate TIFF, no authorized lane, no shared feature stack, no complete registry, no feature-alone leakage canaries, no comparable current-best spatial holdout/CI, no official score receipt, no live leaderboard/quota access, and no automatically refreshed source feed. Four geological ideas in `research/REVIEW.md` are preregistered hypotheses—not discoveries or authorized experiments. The requested training pipeline is not present in this checkout. The three-experiment/two-hour budget was not consumed; zero model experiments ran.

**Submission verdict: negative / NOT READY.** The site explicitly says that no TIFF is available and that no file from the project should be submitted. Local serialization tests are not evidence of geological performance, uniqueness, organizer acceptance, or a path to the competition's top result. The next session should resolve the lane and cached-stack access before any experiment; it must not start by uploading the sample or a historical raster.
