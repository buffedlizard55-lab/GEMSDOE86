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

12. H86G-EDTI (PR #107, 2026-10-25) is **REVOKED (`verdict = "negative"`, `DO NOT SUBMIT`)**
    under `IR-86-H86G-LOCAL-ONLY-DUP-20261025`: PR #107 promoted
    `gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros` (`ba8b731f...`)
    after checking only 43 local files (`max = 0.6850`), but restoring all 655
    external Git blobs (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`)
    proved **44 dot-field overlap firings (> 0.70) and 25 informative
    (`halo_coverage <= 0.70`) firings** (`GEMSDOE46:r11f` `0.7602` at 44,090 dots,
    `GEMSDOE41:h42` `0.7399` at 40,000 dots, `GEMSDOE46:r12` `0.7224` at 37,654 dots).
    Never claim uniqueness clearance on a local-only subset without restoring
    `data/registry_ext/` via `scripts/restore_registry_inventory.py` (which now
    includes zero-REST-quota `codeload.github.com` + git-pack fallback).
    H86J-CSGD (`gems86-h86j-csgd-sar-admit-37654dots-20261025T055033Z-35faffb4-zeros`,
    `079914e3...`) is the first candidate in repo history to achieve **0 / 636
    informative dot-field firings** on the full 690-raster restored scan (`E2`
    ablation `HOLDOUT-DTI = 0.1577`; `E1` SAR-debiased `0.0613`), and stays
    explicitly `negative` (`DO NOT SUBMIT`, 0 slots used) under fail-closed
    gates. All 21 published research TIFFs are `DO NOT SUBMIT`.
