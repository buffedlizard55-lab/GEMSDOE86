# Repository review — 2026-10-29 — `arena/19aee8ac-gemsdoe86`

## Decision

**DO NOT SUBMIT. No new TIFF was generated, no model experiment was run, and no weekly slot was used.** This is a repository and evidence review, not a candidate experiment. The requested optimization cannot responsibly proceed in this checkout: the native training feature raster and prepared arrays are absent, the declared shared feature cache is absent, and the pinned witness required by the protocol preflight is absent. A preflight attempt therefore failed closed before candidate construction. Do not interpret a prior owner's leaderboard claim, format-valid historical raster, or successful test suite as a new score or upload approval.

## Review scope and facts checked

- Read `PROMPT.md`, `README.md`, and `AGENTS.md`; preserved the lane, cached-feature-stack, holdout, leakage, registry uniqueness, evidence labeling, and three-experiment/two-hour rules.
- `python scripts/audit_workspace_inputs.py` (measured 2026-10-29T17:57:16Z) reported `native_inputs_available: false`. `data/bridge/existing_faults.tif` and `sample_submission.tif` matched their pins; `training_features.tif` was missing. All 21 prepared arrays were missing, and `.cache/h86_features/static60_fp.f16` was missing / not provenance-established. It reports no scientific or registry gate evaluation.
- `python scripts/protocol_preflight.py` did **not** produce a new measurement: it stopped with `FileNotFoundError` for `data/bridge/registry/dense-witness.tif`. The previously recorded witness audit in the repository remains historical evidence, not a substitute for the missing current bytes. This failure is fail-closed, not a pass, and does not justify relaxing the protocol.
- `python scripts/audit_release.py` passed the local release audit for 50/50 registered research TIFFs and returned `DO NOT SUBMIT`; this confirms local artifact integrity/format checks only, not new performance, full-registry uniqueness, or organizer approval.
- `python scripts/build_site.py --check`, `python scripts/check_site.py`, and `git diff --check` passed. The published content marks the nine-site files as audit-only and scores as owner-reported; it does not authorize submission.
- `.venv/bin/python -m pytest -q`: **1,189 passed, 24 skipped, 48 warnings, 58 subtests passed** in 516.58 seconds. Tests exercise repository behavior; they do not supply missing evidence or establish scientific validity.

## Nine-site executive finding

The generated [`docs/nine-sites.html`](../docs/nine-sites.html) table covers the nine requested projects. Based on the supplied/project-ledger claims, GEMSDOE32 H33 is the highest of the listed entries at **0.2778 OWNER-REPORTED**, followed by GEMSDOE36 at 0.2750, GEMSDOE28 at 0.2710, GEMSDOE31 at 0.2708, GEMSDOE33 at 0.2632, GEMSDOE25 and GEMSDOE30 at 0.2600, GEMSDOE24 at 0.2477, and GEMSDOE27 at 0.2449. These are not organizer receipts and must not be called confirmed leaderboard scores. The higher leaderboard values in the owner's prompt (0.3195 and 0.4413) conflict and were not independently verified.

The newest archived nine-site byte forensics (review dated 2026-10-29, `docs/evidence/nine-site-lineage-20261029.json`) reports all 72 directed pairwise overlaps above the 0.70 threshold (range 0.8672–1.0000). Therefore none is unique within the selected cohort; this is still not a full-registry uniqueness test. Historical files are for audit only.

The best-supported mechanism explanation for H33 is limited and noncausal: pixel forensics show the 37,654-dot H33 field is a strict subset of GEMSDOE31's 40,199-dot field. It removes 2,545 dots (1,201 at 1.4142 px and 1,344 at 2.0 px catalogue distance) and adds none. A smaller prediction set can lower false-positive cost if removed dots earned no useful truth credit, but the truth distribution needed to confirm that mechanism is unavailable here. The owner-claimed difference is +0.0070, without an organizer receipt or controlled same-split ablation. This is a plausible interpretation, **not causal attribution or a score forecast**. The uploaded-file range error cannot be diagnosed without the exact rejected file and validator output.

## Hypothesis queue and blockers

The repo already contains three screened, genuinely proposed-but-unrun hypotheses in [`registry/focus9_novel_hypotheses_20261028.json`](../registry/focus9_novel_hypotheses_20261028.json): (1) age/level-matched displacement of dated Lahontan shoreline benches using raw USGS 3DEP elevation and mapped shoreline geometry; (2) migration of quality-filtered, time-ordered USGS ComCat earthquake sequences; (3) an age-tagged graph of displaced/terminated geologic-unit contacts with native potential-field context. Their rank order is qualitative, not projected DTI. They each name specific layers, physical signature, fault-discovery rationale, repository distinction, non-fault mimics, and official sources. No candidate can currently be called data-viable: raw 1 m AOI DEM/shoreline geometry, AOI ComCat time series, and suitable attributed unit polygons are not present or freshly verified. Official starting links and availability caveats are in that registry entry.

A lane is unassigned and execution is prohibited by the current project rules. Even if input files are restored, a candidate still needs the actual pinned shared cache, a preregistered lane, per-feature holdout leakage canaries, buffered whole-segment hide-and-recover using the pinned evaluator, same-design paired uncertainty against a comparable baseline, pre-placement and final-dot full-registry checks, and the exact submission writer/validator. No predicted leaderboard score should be written. Slot selection remains separate and should not occur until all gates pass.

## Irregularities / follow-up

1. **Current evidence availability differs from archived receipts:** native features/cache and pinned dense witness are absent in this checkout. Restore via pinned, verified inputs, then rerun current audits; do not use historical receipts as proof of present bytes.
2. **Preflight diagnostics:** missing witness currently surfaces as a Python `FileNotFoundError`, although it safely aborts. This is not a bypass or gate pass. A future change may improve the error message, with tests, without changing any threshold or failure semantics.
3. **Reported-score provenance:** keep all owner-hosted claims visibly distinct from organizer receipts. Never extrapolate their values to this untested candidate.
4. **Metric documentation discrepancy:** the shared evaluator's docstring limitation and prior failed upstream correction attempt are recorded in `PROMPT.md` / review archive. Do not alter vendored shared bytes locally; resolve upstream in the template project.

## Run status card

See the machine-readable [review card](run_cards/repo_review_20261029_arena_19aee8ac.json). This card records a negative disposition and no candidate raster. It is not a score card for a new submission.
