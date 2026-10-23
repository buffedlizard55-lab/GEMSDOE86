# Agent instructions (GEMSDOE86)

1. Read `PROMPT.md`, the current-status section at the top of `README.md`, and the canonical run cards before any change. The full standing request is archived in `README.md` and `research/OWNER_PROMPT.md`.
2. Stay inside the session's preregistered method lane and experiment/time cap. If the prompt has no assigned method paragraph, log that irregularity; do not silently claim a lane assignment.
3. Never fork `vendor/template66/gems57/*`. Use the pinned shared evaluator, holdout, writer, validator, and uniqueness implementation. If a shared-tool defect is established, fix it once in the template and report it; do not keep a private fork.
4. Current Pages figures and prior-site tables are generated from evidence JSON and `registry/prior_scores.csv`. Edit source evidence/records, then run `python scripts/build_site.py`; do not hand-edit generated numeric HTML.
5. `scripts/audit_downloads.py` reopens every registered TIFF with the pinned shared validators and verifies its ZIP/receipt. `make verify-downloads` must pass before publication. `docs/download-status.html` and its report are audit-only; format PASS is not submission approval.
6. The competition TIFFs under `docs/downloads/` are research artifacts unless an explicit run card and a separate selector authorize submission. Keep `DO NOT SUBMIT` visible whenever a gate fails. `ORGANIZER-CONFIRMED` requires an actual submission-page receipt.
7. `data/bridge/*.tif` are hash-pinned. `.cache/` and restored large owner mirrors are not committed. A matching hash proves mirror integrity, not organizer authentication.
8. Before publishing changes, run `.venv/bin/python -m pytest -q`, `.venv/bin/python scripts/audit.py`, `.venv/bin/python scripts/audit_h86b.py`, `.venv/bin/python scripts/audit_rmrb86.py`, `make verify-downloads`, `.venv/bin/python scripts/build_site.py`, and `git diff --check`. Confirm shared-template pins.
9. Report negative results and limitations. The current H86B-GFCO and RMRB lanes are negative; do not relabel their HOLDOUT-DTI or registry measurements as leaderboard scores.
