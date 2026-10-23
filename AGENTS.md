# Agent instructions (GEMSDOE86)

1. Read `PROMPT.md` and `README.md` before any change. The standing rules are the parallel-run
   protocol (lane, reuse, evidence class, leakage canary, run card, budget).
2. Never fork `vendor/template66/gems57/*`. If a shared tool is wrong, fix it upstream and report it.
   The effective pin is `research/template_pin.json`, with both vendored import paths checked.
   FVMB's separate `registry/template_pin.json` describes an amendment absent from the actual
   vendored bytes; it is archived context, not an alternate authorization or effective tool pin.
3. Measured site counts and historical HOLDOUT-DTI come from explicit evidence files in
   `evidence/` or `docs/evidence/`, rendered by `scripts/build_site.py`. Owner score claims are
   separately transcribed in `registry/prior_scores.csv` and must remain unverified claims.
   Never hand-edit generated HTML numbers.
4. Never label a projection as a score. `ORGANIZER-CONFIRMED` requires a submission-page receipt.
5. `data/bridge/*.tif` are hash-pinned; `scripts/restore_data.py` verifies them and aborts on mismatch.
   `.cache/` is ignored; the actual template feature stack is currently absent. A raw mirrored
   feature TIFF is not that shared cache, and must not be described as a restored cache.
6. Before publishing anything: `python scripts/audit_release.py` (all artifacts),
   `python scripts/build_site.py --check`, `python scripts/check_site.py`, and `pytest -q`.
   Recheck the immutable witness with `audit_release.py --measure-registry` after restoring it.
   The literal full-support blocker is binding: do not add a CLI/import bypass or change support
   thresholds privately. A format pass alone must never authorize a weekly slot.
   Never call a maximum across different holdout designs the current holdout best.
7. Report negative results. The GMC hypothesis in this repo is negative and must stay documented as
   such.
