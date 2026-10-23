# Agent instructions (GEMSDOE86)

1. Read `PROMPT.md`, the current-status section at the top of `README.md`, and the canonical run cards before any change. The full standing request is archived in `README.md` and `research/OWNER_PROMPT.md`.
2. Stay inside the session's preregistered method lane and experiment/time cap. If the prompt has no assigned method paragraph, log that irregularity; do not silently claim a lane assignment.
3. Never fork `vendor/template66/gems57/*`. Use the pinned shared evaluator, holdout, writer, validator, and uniqueness implementation. If a shared-tool defect is established, fix it once in the template and report it; do not keep a private fork.
4. Current Pages figures and prior-site tables are generated from evidence JSON and `registry/prior_scores.csv`. Edit source evidence/records, then run `python scripts/build_site.py`; do not hand-edit generated numeric HTML.
5. The competition TIFFs under `docs/downloads/` are research artifacts unless an explicit run card and a separate selector authorize submission. Keep `DO NOT SUBMIT` visible whenever a gate fails. `ORGANIZER-CONFIRMED` requires an actual submission-page receipt.
6. `data/bridge/*.tif` are hash-pinned. `.cache/` and restored large owner mirrors are not committed. A matching hash proves mirror integrity, not organizer authentication.
7. Before publishing changes, run `.venv/bin/python -m pytest -q`, `python scripts/audit.py`, `python scripts/audit_h86b.py`, `python scripts/audit_rmrb86.py`, `python scripts/check_site.py`, and `python scripts/build_site.py`. Confirm the shared-template pins and `git diff --check`.
8. Report negative results and limitations. The current H86B-GFCO and RMRB lanes are negative; do not relabel their HOLDOUT-DTI or registry measurements as leaderboard scores.
