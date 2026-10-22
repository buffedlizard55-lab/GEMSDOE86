# Three-pass verification record

## Pass 1 — implement and exercise

Inspected the empty checkout, selected related GitHub trees and the official reference solution. Recovered small hash-pinned grid inputs from owner mirrors. Located the shared template; vendored its Python package byte-for-byte with a commit/hash pin. Added a reproducible negative preflight, research report, homepage, executive summary and CI.

## Pass 2 — bugs, assumptions, edge cases

Fixed a test that had mistaken the shared `surface_rho` return object for a scalar. Closed a file handle in mirror restoration. Kept shared metric/writer source unchanged. Tested NaN, Inf, negative/over-one and sentinel values, catalogue support, outside-footprint support, empty truth and duplicates. Added a complete ephemeral full-grid TIFF/ZIP roundtrip and overwrite rejection test. No test fixture was offered as a submission. Added current input hashes to preflight checks.

## Pass 3 — requirements and claim review

Eight tests pass. Python compilation and Git whitespace checks pass. Local HTML links are checked for missing targets. Machine JSON uses null rather than inventing scores or validation results. Unfetched official sources, owner-reported scores, mirrored data authenticity and provisional hypotheses are labelled. The UI uses explicit NOT READY language rather than an actionable TIF download.

**Not fully satisfied:** no unique candidate TIF, no assigned lane, no cached feature stack, no complete registry, no feature canaries, no geological experiment, no comparable best holdout/CI, no confirmed leaderboard score or authenticated quota, no live official-source feed, and no verbatim archive of the entire user prompt (README retains a condensed starting brief). These are not hidden behind an overall success claim. Research novelty across every sibling repository remains unverified. Four hypotheses are provisional, not discoveries. Three model experiments / two-hour budget was not consumed; zero model experiments ran.

Local format tests prove serialization and rejection behavior only; they do not prove a useful or unique prediction. The next scientific task must start by resolving the recorded blockers, not by uploading a template.

---

# Session 2 (2026-10-22) — H86-1 lane, three passes

## Pass 1 — implement and exercise
Restored hash-pinned rasters incl. the 419 MB 19-band feature raster and a
14-raster registry (`scripts/restore_data.py --include-features`,
`scripts/fetch_registry.py`, all SHA-verified). Preregistered 5 ranked
hypotheses and one lane paragraph (`research/h86-hypotheses.md`). Built the
H86-1 surface/emission/holdout pipeline (`scripts/run_h86.py`) on the
unmodified vendor metric/evaluator/writer/validator/uniqueness code.
Ran E1 canaries (no AUC > 0.90), E2/E3 pipeline hide-and-recover
(candidate ≈ spaced random on HOLDOUT-DTI at both budgets; far below fixed
incumbents), an auxiliary SGMC-proxy screen (candidate below random),
surface+dot uniqueness vs 14 rasters, and serialized a 38,000-dot candidate
through the shared writer (validator: all checks pass).

## Pass 2 — bugs, assumptions, edge cases
Caught and documented, not hidden: fixed-incumbent arms in hide-and-recover
are not pipeline like-for-like (B2's 0.0039 is structural); the literal
dot-overlap gate fires only against a lattice raster covering 99.87% of
allowed cells (saturation certificate added); feature-raster finite mask
differs from sample footprint (3,061/1,540 cells); SGMC derived raster is a
~1 px dilation (proxy kept auxiliary/approximate). Rewrote `scripts/audit.py`
to re-verify the run card against TIF bytes (a concurrent-tool race with the
old audit briefly clobbered the card during editing; regenerated and
re-verified). All 8 unit tests pass; shared vendor bytes unchanged (pin check).

## Pass 3 — requirements and claim review
Every number labelled HOLDOUT-DTI / AUXILIARY-PROXY / REGISTRY-MEASUREMENT /
OWNER-REPORT; none presented as an organizer score. Site banner, run card
(`verdict: negative`, `submission_ready: false`) and README agree: the TIF is
downloadable for inspection and must not be submitted. Local doc links all
resolve; evidence JSON parses without NaN/Inf literals; card SHA matches TIF
bytes. Remaining unfulfilled by design of the result: no organizer-confirmed
score, no slot use, registry limited to 14 accessible rasters, raw SGMC
unavailable in the manifest, no live quota verification. Full record:
`research/H86_RESULTS.md`.
