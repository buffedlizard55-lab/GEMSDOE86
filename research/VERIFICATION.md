# Three-pass verification record

## Pass 1 — implement and exercise

Inspected the empty checkout, selected related GitHub trees and the official reference solution. Recovered small hash-pinned grid inputs from owner mirrors. Located the shared template; vendored its Python package byte-for-byte with a commit/hash pin. Added a reproducible negative preflight, research report, homepage, executive summary and CI.

## Pass 2 — bugs, assumptions, edge cases

Fixed a test that had mistaken the shared `surface_rho` return object for a scalar. Closed a file handle in mirror restoration. Kept shared metric/writer source unchanged. Tested NaN, Inf, negative/over-one and sentinel values, catalogue support, outside-footprint support, empty truth and duplicates. Added a complete ephemeral full-grid TIFF/ZIP roundtrip and overwrite rejection test. No test fixture was offered as a submission. Added current input hashes to preflight checks.

## Pass 3 — requirements and claim review

Eight tests pass. Python compilation and Git whitespace checks pass. Local HTML links are checked for missing targets. Machine JSON uses null rather than inventing scores or validation results. Unfetched official sources, owner-reported scores, mirrored data authenticity and provisional hypotheses are labelled. The UI uses explicit NOT READY language rather than an actionable TIF download.

**Not fully satisfied:** no unique candidate TIF, no assigned lane, no cached feature stack, no complete registry, no feature canaries, no geological experiment, no comparable best holdout/CI, no confirmed leaderboard score or authenticated quota, no live official-source feed, and no verbatim archive of the entire user prompt (README retains a condensed starting brief). These are not hidden behind an overall success claim. Research novelty across every sibling repository remains unverified. Four hypotheses are provisional, not discoveries. Three model experiments / two-hour budget was not consumed; zero model experiments ran.

Local format tests prove serialization and rejection behavior only; they do not prove a useful or unique prediction. The next scientific task must start by resolving the recorded blockers, not by uploading a template.

## Follow-up review in this checkout — 2026-10-22

The current branch was re-reviewed against the full user brief and the run-card protocol. A fresh Python 3.11 virtual environment was created and the pinned dependencies in `requirements.txt` installed. `scripts/restore_data.py` completed from the hash-pinned owner mirror for `existing_faults.tif` and `sample_submission.tif`; the receipts record the expected hashes and explicitly say `organizer_authenticated: false`. The files remain under ignored `data/` and are not committed. The 419 MB mirrored feature raster was deliberately not downloaded: the request requires the template's cached feature stack, and substituting or rebuilding one is not authorized or equivalent.

Fresh checks: `scripts/audit.py` reports the grid inputs present, mirror hashes matching, and matching raster grids (EPSG:32611; 3730 x 3292; 100 m transform). The audit still correctly returns `verdict: negative`, no candidate SHA, no holdout score, and no submission readiness. `python -m unittest discover -s tests -v` passes all eight tests; `compileall` and `git diff --check` pass. One Rasterio `PendingDeprecationWarning` arises in the synthetic round-trip test and does not fail the test. No model experiments were run, so no number is labeled HOLDOUT-DTI, and no result is ORGANIZER-CONFIRMED.

**Decision:** do not create or expose a downloadable TIFF. The prompt's highest-priority demand for a unique submission conflicts with its own stop conditions: it supplies no identifiable authorized method paragraph, complete registry, shared feature cache, feature canary, or benchmark holdout. A new TIFF under these conditions would be unvalidated, not demonstrably unique, and would misleadingly appear eligible for competition upload. The website therefore remains an explicit NOT READY status; `docs/evidence/run-card.json` is a negative preflight, not a submission artifact. No slot was selected or spent.

This is a repo review and a negative preflight, not completion of the scientific submission goal. Existing limitations remain: no current authenticated quota/receipt, no organizer-authenticated inputs, no fresh official leaderboard capture in this rerun, no complete sibling-site registry, and no documented feature-layer validation. The reported historical scores remain unverified in this evidence set.

## Superseding review — this session (branch arena/00e02bfc-gemsdoe86)

The "do not create or expose a downloadable TIFF" decision above is superseded
by the executed lane H86-RMRB (see REVIEW.md addendum): a candidate TIF now
exists and is downloadable FOR INSPECTION ONLY. Independent re-validation
this session (scripts/validate_download.py, no data/ needed): SHA-256
cf4ab340…5962 matches the run card; single-band float32; EPSG:32611;
3730×3292; pinned transform; all finite; values in [0,1]; 60,000 dots;
ZIP contains only that TIF; note 118/140 chars.

Irregularities found and fixed in this session:
1. scripts/audit.py previously overwrote docs/evidence/run-card.json with a
   stale "no candidate / NOT_RUN" preflight — it is now read-only w.r.t. the
   run card and writes docs/evidence/preflight-audit.json instead; a test
   asserts the run card bytes are unchanged by run().
2. Dashboard/README called the candidate "unique": the shared uniqueness
   checker in fact returns unique=false, duplicate_count=1,
   stop_required=true (literal >0.70 3-px dot-overlap vs the saturating
   13GEMSDOE lattice raster, 206,895 dots; Spearman ρ=0.0003, Jaccard=0.009).
   Wording now reports the checker verbatim: byte/pixel-distinct, NOT
   uniqueness-cleared. Per protocol this is logged as a duplicate-gate
   firing and stopped — no re-emission was attempted (budget: 3 experiments
   already run).
3. Root index.html still said "No candidate TIF is available" — corrected.
4. Dashboard linked research/REVIEW.md via a stale branch URL — now relative.

No new experiment was run and no score is claimed: HOLDOUT-DTI 0.0420
[0.0369–0.0467] (gems57-pooled-hide-v2, 22,641 withheld) vs incumbent
0.1011 [0.0856–0.1167] remains a negative result. Historical brief numbers
(0.2778 / 0.4413 / 0.3195) remain owner-reported without receipts.
