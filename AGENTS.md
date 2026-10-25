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

10. Protocol amendments PA-86-01 / PA-86-02 (2026-10-24, owner directive to generate a unique TIFF):
    new lanes may call `protocol_preflight.require_like_for_like()` instead of `require_feasible()`
    ONLY if they then run `scripts/check_h86e_registry.py` on the surface (rho) and final dots and
    `scripts/pa86_chance_overlap.py` (informative overlap firings are hard stops). Thresholds are
    unchanged; `require_feasible()` still gates every historical builder. See IRREGULARITIES.md.

11. Registry-candidate evidence must bind the source `.npy` hash, shared decoded hash,
    full comparison rows and indexed registry identity. Never grant a gate pass on
    missing/invalid registry rows or implicitly binarize/repair candidate arrays.
    Old unbound H86E reports are archives; rerun them for any future gate decision.
    Surface checks precede placement, final-dot checks precede serialization, and
    a PA diagnostic pass never overrides a failing literal submission gate.

12. H86G-EDTI (2026-10-25) is the first `promote` lane: its single candidate
    (`gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros`, sha256
    `ba8b731f...`) passed canary, SGMC-proxy paired-CI (selection only),
    OOF catalogue-hide floor, like-for-like uniqueness vs 43 local registry
    dot-fields, and the fail-closed format writer. Never rebrand its numbers:
    SGMC-PROXY-DTI is not a score, the 55k budget came from disclosed post-hoc
    Amendment A4, `safe_to_submit`/`approved_for_weekly_slot` stay false until
    an organizer receipt is logged in `ledger/submissions.csv`. The catalogue-
    hide whole-component instrument anti-correlates with owner-reported live
    ordering (E1b table in `research/H86G_EDTI_REVIEW.md`); never select a
    live candidate on it alone, and never compare an OOF arm number to a
    shipped raster's as-is number. `audit_release.py` knows this lane via
    `holdout_kind="h86g_edti"`; the literal full-support witness stop and all
    thresholds are unchanged.

13. H86J-MPC (2026-10-25) is a `negative` lane: pure monogenic phase-congruency
    step ranking (`src/gems86_mpc/`, preregistration
    `research/H86J_MPC_PREREGISTRATION.md`, frozen 44,090-dot budget) was
    falsified by its own amplitude control (SGMC-PROXY-DTI 0.1089 vs 0.0658
    @44,090; run card `docs/evidence/h86j-mpc-run-card.json`,
    `holdout_kind="h86j_mpc"` → `CURRENT_LANE_NEGATIVE`). Never rebrand the
    AMP-GRADMAG control as a candidate (it is an EDTI-L-lineage 3-detector
    subset) and never re-run unchanged pure PC; a hybrid amplitude×phase
    gate or phase-symmetry lane needs a fresh preregistration.
