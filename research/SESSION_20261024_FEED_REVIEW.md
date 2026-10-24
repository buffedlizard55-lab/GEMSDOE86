# Session review — 2026-10-24 (92-project fleet feed refresh + 8 new owner-reported scores)

## Summary

- **Decision unchanged: `DO NOT SUBMIT`.** No new GeoTIFF was generated (`new_candidate_generated = false`), no model experiment was run (`experiments_run = 0`), and no weekly DrivenData submission slot was used (`submission_slots_used = 0`).
- **92-project fleet synchronized (`GEMSDOE` through `GEMSDOE92`):**
  - Expanded `registry/site_targets.json` from `88` to `92` owner-named repositories (`GEMSDOE89`..`GEMSDOE92` added).
  - Updated `registry/prior_scores.csv` (`119` total rows: `113` scored `OWNER-REPORTED` entries, `6` unscored rows for `GEMSDOE86`, `GEMSDOE88`..`GEMSDOE92`), adding the 8 newly reported owner scores from the 2026-10-24 prompt:
    1. `GEMSDOE76`: `gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros` → `0.2343` (`OWNER-REPORTED`)
    2. `GEMSDOE78`: `gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros` → `0.1564` (`OWNER-REPORTED`)
    3. `GEMSDOE79`: `gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros` → `0.0005` (`OWNER-REPORTED`)
    4. `GEMSDOE82`: `gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros` → `0.1886` (`OWNER-REPORTED`)
    5. `GEMSDOE83`: `gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros` → `0.0573` (`OWNER-REPORTED`)
    6. `GEMSDOE84`: `gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros` → `0.0132` (`OWNER-REPORTED`)
    7. `GEMSDOE85`: `gemsdoe85-hjcd-ventbridge-submod-zeros` → `0.1110` (`OWNER-REPORTED`)
    8. `GEMSDOE87`: `h87-h87-cmgep-20261022T060000Z-8f394f43` → `0.0500` (`OWNER-REPORTED`)
  - Refreshed `docs/evidence/fleet-feed.json` live via `gh api`: `92 / 92` repositories snapshotted (`refresh_complete = true`, `organizer_receipts_obtained = 0`).
- **Empirical lessons from the 8 newly reported owner scores:**
  - Submodular 300 m facility-location decoding near the `~37.6k–39k` dot budget (`GEMSDOE76` `ptcf-tiltworm-submod39k`: `0.2343`; `GEMSDOE70` `dual-submod300-oof38k`: `0.2478`; `GEMSDOE82` `submodular-punoisyor`: `0.1886`) outperforms over-budget ring/continuous emissions (`GEMSDOE79` `100,000` dots: `0.0005`; `GEMSDOE84` `58,000` px: `0.0132`; `GEMSDOE81` `cont-poisson44090`: `0.0041`) by orders of magnitude because DTI's `alpha = 0.2` false-positive weight penalizes every excess off-target kernel support cell.
- **Evidence boundary:** All `113` score scalars remain `OWNER-REPORTED` user claims (`0` `ORGANIZER-CONFIRMED` submission-page receipts in this checkout). Git tree snapshots prove repository and blob metadata, not raster validity or leaderboard scores.
