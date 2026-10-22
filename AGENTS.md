# Agent instructions (GEMSDOE86)

1. Read `PROMPT.md` and `README.md` before any change. The standing rules are the parallel-run
   protocol (lane, reuse, evidence class, leakage canary, run card, budget).
2. Never fork `vendor/template66/gems57/*`. If a shared tool is wrong, fix it upstream and report it.
3. Every number on the site comes from a file in `evidence/` produced by a script in `scripts/`.
   Run `python scripts/build_site.py` after regenerating evidence — never hand-edit HTML numbers.
4. Never label a projection as a score. `ORGANIZER-CONFIRMED` requires a submission-page receipt.
5. `data/bridge/*.tif` are hash-pinned; `scripts/restore_data.py` verifies them and aborts on mismatch.
   `.cache/` holds the 419 MB feature stack and is never committed.
6. Before publishing a candidate: `pytest -q`, `scripts/audit_uniqueness.py`, and confirm the
   saturation certificate is current. A file that fails the format gate must never be linked as
   submittable.
7. Report negative results. The GMC hypothesis in this repo is negative and must stay documented as
   such.
