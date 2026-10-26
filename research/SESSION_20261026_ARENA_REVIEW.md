# Repository review — Arena session 2026-10-26

## Decision

**No file is authorized for upload. Do not submit H86Q or another TIFF from this checkout.** This review did not run a new scientific experiment or spend a competition slot. The H86Q basin-center distance-ridge raster was already created by the merged H86Q work; this review registers and audits that existing artifact, and corrects its presentation so a local format pass cannot be mistaken for submission clearance.

## H86Q-BASINRIDGE artifact review

- Artifact: `docs/downloads/gems86-h86q-basinridge-37654dots-20261026T044757Z-6d59ba15-zeros.tif`.
- SHA-256: `7afcca44dc4c2411af4cad97ca9beb15117ed94b78b77b13ce1462c4ad49a6f4`.
- The writer receipt reports a one-band float32 GeoTIFF on the template grid (`EPSG:32611`, `3730×3292`, exact sample transform), finite values in `[0,1]`, no NaN/Inf, 37,654 positive pixels, and a 139-character note. These are local format checks only.
- **HOLDOUT-DTI:** `NOT RUN`; no whole-segment buffered hide-and-recover evaluation, withheld-positive count, or confidence interval exists for H86Q. The candidate was built from catalogue geometry, not the shared cached feature stack. No per-feature leakage canary or registered pre-placement surface comparison was run.
- The attached uniqueness sidecar reports `71` locally compared rasters (not a complete registry). A README-era claim of `72` conflicts with that sidecar; the discrepancy is flagged, not reconciled by assumption. The sidecar's local maxima (`rho = 0.3786296`, forward 3-px overlap `0.4279227`) are descriptive of that limited scan, not uniqueness clearance.
- The pinned full-support witness has positive support over every allowed pixel. The all-artifact audit therefore reports literal forward overlap `1.0` for every nonempty candidate. Under the currently enforced literal threshold, H86Q is blocked. No threshold was changed or bypassed.
- The distance-transform-ridge mechanism could be mimicked by unfaulted paleolake shorelines, alluvial-fan toes, or basin-floor depositional margins; the raster alone cannot distinguish these from concealed faults or establish a geothermal vent.

The H86Q artifact is now explicitly registered as an **unvalidated negative archive** in the artifact inventory, with a run card and an all-artifact measurement. It is **safe to download for audit only** and **not approved for submission**. Partial local comparisons do not justify calling it globally unique.

## Focus-9 findings

The generated executive summary now lists the best supplied result for each requested site: GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. These historical values remain **OWNER-REPORTED**, not organizer-confirmed, because no submission-page receipts are present. Within this cohort, the highest supplied claim is GEMSDOE32 H33 (`0.2778`); its reported lead is consistent with the D28 → H27-4 lineage and removal of redundant 1–2 px catalogue-collar dots. That is a plausible DTI precision/coverage mechanism, not a controlled causal result or a recommendation to copy/resubmit the raster. Site-by-site forensic evidence and source links are in `SESSION_20261026_H86P_TCWB_REVIEW.md`.

## Changes and checks

- Fixed the clean-checkout builder-preflight test to accept a missing gitignored witness as a fail-closed outcome; the pinned witness may be restored under `data/registry/` or `data/bridge/registry/`.
- Added H86Q to the download inventory and artifact-card index; added a strict `h86q_basinridge_unvalidated` audit schema that rejects any H86Q card lacking the negative, no-slot, no-HOLDOUT and literal-witness-stop fields.
- Updated the generated executive-summary builder to show the Focus-9 table and the H86Q direct audit-download links with an unmistakable negative authorization state. Reworded procedural steps so they cannot imply a current upload is approved.
- Corrected H86Q source documentation to distinguish partial local similarity measurements from full uniqueness clearance.

Verification performed in the current workspace:

- `python -m pytest -q`: **1083 passed, 24 skipped, 58 subtests passed** on the full suite; 48 existing Rasterio deprecation warnings.
- Targeted post-edit suite (preflight, publication, site, download and generated-page tests): **354 passed, 42 subtests passed**.
- `python -m unittest discover -s tests -v` with the gitignored witness absent (fresh-checkout simulation): **120 tests passed, 1 skipped**.
- `scripts/audit_release.py --measure-registry`: **PASS**, 44/44 registered artifacts locally valid, all final artifacts remeasured, decision remains `DO NOT SUBMIT`; no new experiment or slot.
- `scripts/audit_downloads.py`, `scripts/build_site.py --check`, and `scripts/check_site.py`: **PASS** after regenerated outputs.
- `scripts/audit_workspace_inputs.py --require-native`: expected fail-closed blocker. `training_features.tif`, the actual prepared 19-band stack, and the provenance-verified shared feature cache are absent from this workspace.

## Next steps / blockers

1. Keep all downloads visibly audit-only until the selector and literal registry gates are resolved; the format validator must never be the promotion gate.
2. Recover the organizer-authenticated training feature raster/labels (or establish verified access through the competition's permitted route) and the shared feature cache. Do not infer their presence from old receipts or the smaller bridge rasters.
3. Re-run the assigned preregistered hypothesis with the shared evaluator, whole-segment buffered holdout, per-feature leakage canaries, and paired confidence intervals. H86Q must not be treated as having beaten any holdout baseline.
4. Restore and scan the complete registry before claiming uniqueness. The current literal full-support witness mathematically blocks every nonempty candidate; only a documented, authorized protocol clarification could alter that rule. Do not change the thresholds privately.
5. Obtain organizer receipts and weekly capacity through an authorized human portal workflow. Automated scraping or upload is not performed here.
