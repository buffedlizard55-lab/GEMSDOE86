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

8. Historical variant builders and imported model orchestration must call the same
   `protocol_preflight.require_feasible()` before candidate construction, even with
   `--no-write` / `--measure`. Dedicated read-only artifact audits remain usable.
   `audit_release.py --measure-registry` also writes `latest-review-run-card.json`
   with actual UTC measurement time and report/registry hashes; HTML-only rebuilds
   must not manufacture freshness or relabel historical model results.
9. Never fetch or scrape `drivendata.org` via automated tools (DrivenData Terms of
   Use prohibit automated/robot/spider access; only human browser receipts may
   supply `ORGANIZER-CONFIRMED` scores or remaining weekly quota). Verify every
   `training_features.tif` band index against `src/gems86/io.py` (`BANDS`).

10. Historical protocol amendments PA-86-01 / PA-86-02 (2026-10-24) allowed scoped
    like-for-like diagnostics but did not waive or redefine the literal full-support overlap rule.
    Any such diagnostics must still run `scripts/check_h86e_registry.py` on the surface (rho) and
    final dots and `scripts/pa86_chance_overlap.py`; all informative overlap firings are hard stops.
    The current pinned witness proves that every nonempty allowed prediction has literal forward
    overlap 1.0 (> 0.70), so no lane can use a scoped/partial comparison to obtain current clearance.
    Historical builders remain gated by `protocol_preflight.require_feasible()`. See IRREGULARITIES.md.

11. Registry-candidate evidence must bind the source `.npy` hash, shared decoded hash,
    full comparison rows and indexed registry identity. Never grant a gate pass on
    missing/invalid registry rows or implicitly binarize/repair candidate arrays.
    Old unbound H86E reports are archives; rerun them for any future gate decision.
    Surface checks precede placement, final-dot checks precede serialization, and
    a PA diagnostic pass never overrides a failing literal submission gate.

12. H86G-EDTI's 2026-10-25 `promote` is a preserved historical lane verdict under its
    scoped like-for-like interpretation, not current release authorization. The original
    TIFF bytes and scientific run card are retained unchanged; the adjacent identity receipt
    carries a transparent current-disposition addendum. Never rebrand its numbers: the
    `SGMC-PROXY-DTI` is a selection instrument, not a score; the 55k budget came from disclosed
    post-hoc Amendment A4; its `HOLDOUT-DTI` is OOF visible construction and is not a live
    leaderboard result. The present literal full-support proof supersedes the old promote for
    every current decision. `safe_to_submit` and `approved_for_weekly_slot` remain false.
    `audit_release.py` validates the historic card only as an archive and emits
    `DO NOT SUBMIT` for H86G and every other inherited artifact.

13. The current inventory, release report, landing page, executive summary, submission-status
    page, download audit, and README must agree: every inherited TIFF is **DO NOT SUBMIT** and
    audit-only; no weekly slot is authorized. Generated-site checks reject positive/ambiguous
    badges, calls to upload, or any inventory status other than the exact negative state. Never
    treat a local format pass, an archived `promote`, a new byte hash, or an incomplete registry
    scan as submission clearance. Preserve historical cards and explain their scope rather than
    silently rewriting scores or experimental results.
