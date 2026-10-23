# Three-Pass Autonomous Verification Log (`GEMSDOE86` — Session 2, Lane `H86B-GFCO`)

**Current-review correction (2026-10-23):** This is a historical execution log, not a new run.
The current all-file audit is `docs/evidence/release-readiness.json`; all six artifacts fail
the literal registry gate. Its measured GFCO TIFF and ZIP payload are each **145,410 bytes**;
the ZIP archive is **109,484 bytes**. The two different historical byte counts below were
incorrect and have been corrected. No model evidence or TIFF bytes were changed.

**Date:** 2026-10-22 (UTC)
**Branch:** `arena/27952692-gemsdoe86` (branched from `main` at `62ed67084ce2279aaa6cb897bda8e3aa3a12fcf0`)

---

## Pass 1 — End-to-End Implementation, Data Restoration & 3-Experiment Execution

1. **Prior-Session Audit & Cross-Repository Survey:**
   - Inspected all files in `GEMSDOE86` (`main` after PR #6) and surveyed `GEMSDOE32`, `GEMSDOE36`, `GEMSDOE49`, `60GEMSDOE`, `GEMSDOE63`, `GEMSDOE70`, `GEMSDOE73`, `GEMSDOE75`–`GEMSDOE85`, `GEMSDOE87`, and `GEMSDOE88`.
   - Restored and SHA-256-verified all `23` competition, GDR-1391, external proxy, and scored baseline files from `research/upstream/data_manifest.json` plus `15` sibling repository primary candidate GeoTIFFs (`research/upstream/cross_repo_champions_manifest.json`).
   - Verified `vendor/gems57/` SHA-256 pins (`21 / 21` exact matches against `research/template_pin.json`).
2. **Label-Free Multi-Physics + Geothermal Feature Builder (`scripts/h86b_features.py`):**
   - Built `38` `float32` physical, hydrothermal, potential-field contact-offset, basement/strain, 1 m LiDAR scarplet, 100 m DEM hinge/valley, and topographically-deconfounded radiometric planes into `data/cache/h86b_planes/*.npy` (`98.59s`, `catalogue_used = false`, `sgmc_used = false`).
   - Verified all `42` single-feature Leakage Canaries (`38` physical planes + `4` strictly visible-only kinematic components `tip_cone`, `relay_bridge`, `bend_splay`, `m_kin`): `42 / 42 PASS`, `max_disc = 0.8485 <= 0.90`.
3. **3-Experiment LOQO Execution (`scripts/run_lane86b.py`):**
   - Executed strictly within the 3-experiment / 2-hour cap (`16.6 min` CPU, `< 1.8 GB` peak RAM on a `3.8 GB` 0-swap VM):
     - `E1_phys_38k`: `0.0472` (`buffered_comp`), `0.0454` (`all`), `0.0514` (`detached`)
     - `E2_gfco_38k`: `0.0992` (`buffered_comp`), `0.1343` (`all`), `0.1450` (`detached`)
     - `E3_gfco_44k` (**selected**): **`0.1078 [0.0908, 0.1254]`** (`buffered_comp` vs `0.0919` `d2.8` / `0.0961` `H33-2-B2`), **`0.1396 [0.1286, 0.1513]`** (`all` vs `0.1011` `d2.8`, `+38.1%`), **`0.1521 [0.1378, 0.1662]`** (`detached` vs `0.1035` `d2.8`, `+47.0%`).
   - Serialized `docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.{tif,zip,json}` via unmodified `gems57.submission_writer.write_submission` and verified `15 / 15` format checks via `gems57.validate` and `gems57.gates.format_report`.

---

## Pass 2 — Bug Hunt, Hidden Assumptions & Edge Cases Found and Fixed

1. **Bug 1 Caught & Fixed (Pre-Experiment Synthetic Test — `allocate_patient` `1.0 px` Clumping):**
   - *Finding:* Before touching real data, unit-testing `gems57.emit.allocate_patient` on a synthetic 19-ridge grid revealed `min_nn_px = 1.0, skipped = 0` (`DTI = 0.1636`) whenever $k_{\text{self}} = \min(E[k](x), 1.0)$ saturates at `1.0` (`emit.py` line 325 sets marginal FP cost `1 - k_self = 0`), while `emit_decimated(tile_px=3)` left `1.0 px` adjacent pairs across $3 \times 3$ tile seams (`DTI = 0.2361`).
   - *Fix:* Used `gems57.emit.expected_credit` followed by seam-free priority disc thinning at $r_{\text{suppress}} = 2.8\text{ px}$ (`min_nn >= sqrt(8) = 2.828 px`), raising synthetic DTI to `0.2822 (+72.5%)` while keeping `vendor/gems57/emit.py` 100% unmodified.
2. **Bug 2 Caught & Fixed (Holdout Calibration Paradox — Unbuffered Cut Ends vs Buffered Whole Components):**
   - *Finding:* Scoring `d2.8` (`0.1011`) vs `H33-2-B2` (`0.0910`) on unbuffered 12-px cut-branch holdouts inverted their owner-reported live ordering (`0.2600 < 0.2778`) because cut ends sit at `d_vis = 1–2 px`.
   - *Fix:* Added primary evaluation on `gems57.holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)` (whole 8-connected components + 3-px buffer, matching Protocol Rule 2), which restored monotonic ordering `H19-5 (0.0654) < d2.8 (0.0919) < H33-2-B2 (0.0961) < H86B-GFCO (0.1078)`, and reported all three holdout instruments side by side.
3. **Bug 3 Caught & Fixed (`scripts/audit.py` Clobbering `docs/evidence/run-card.json` During `unittest`):**
   - *Finding:* Running `python -m unittest` in Session 1 invoked `audit.run()`, which unconditionally overwrote `docs/evidence/run-card.json` with a `"NOT_RUN"` stub whenever `data/` was absent or mocked.
   - *Fix:* Parameterized `audit.run(..., run_card_out=None)` to be strictly read-only by default and added a byte-equality assertion in `tests/test_audit.py::test_missing_evidence_is_not_ready_and_never_clobbers_runcard`.
4. **Bug 4 Caught & Fixed (`scripts/restore_lane_data.py` Incomplete File Restoration):**
   - *Finding:* `restore_data.py` only restored `existing_faults.tif` and `sample_submission.tif`, skipping `labels.tif`, the GDR-1391 CSVs/rasters, and the `12` scored baselines on a fresh clone.
   - *Fix:* Updated `scripts/restore_lane_data.py` to restore and SHA-256-verify all `22` non-qfaults core manifest files (`ext_gdr_qfaults_traces` excluded by default to prevent label leakage) plus all `15` cross-repo champion rasters via `codeload.github.com` tar streaming with `gh api` fallback.
5. **Bug 5 Caught & Fixed (Stale Temporary Branch Link in `docs/index.html`):**
   - *Finding:* `docs/index.html` line 41 from PR #6 pointed to `blob/arena/d8a21439-gemsdoe86/research/REVIEW.md`.
   - *Fix:* Replaced with `blob/main/research/REVIEW.md` and added an automated link-scanner assertion against stale `arena/` branch URLs.
6. **Bug 6 Caught & Prevented (Low-RAM OOM Hazard on `3.8 GiB` / `0 B` Swap VM):**
   - *Finding:* Keeping `38` `49 MB` `.npy` memmaps open simultaneously with full-grid `two_host_frame` pushed `ru_maxrss` to `3,638 MB` (`95%` of total VM RAM).
   - *Fix:* `gather_lowmem` opens and closes one `.npy` plane at a time (`49 MB` transient) and caches kinematic maps to `data/cache/h86b_kin/*.npz` with immediate `gc.collect()`.

---

## Pass 3 — Full Independent Accuracy, Completeness & Protocol Audit

Executed automated Pass-3 verification + `scripts/audit.py` + `tests/test_audit.py`:
- **`vendor/gems57` pin check:** `21 / 21` files SHA-256 identical (`pins_clean = true`).
- **Strict JSON integrity:** `15 / 15` JSON files in `docs/` and `research/` parsed with `parse_constant` rejecting `NaN`/`Infinity` (`0` non-finite tokens).
- **Standalone `.tif` vs `.zip` byte parity (remeasured/corrected 2026-10-23):** `docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif` and the sole TIFF payload in its ZIP are both **145,410 bytes**, with exact SHA-256 `897ebf7b790efb9b5668934f5929ae766d81d9ec2a4bee3faa7ef2ebaedc1116`. The compressed ZIP file is **109,484 bytes** and `testzip() is None`. Byte equality was rechecked; differing payload lengths cannot imply byte parity.
- **Direct GeoTIFF array verification:** `shape = (3730, 3292)`, `crs = EPSG:32611`, `dtype = float32`, `nodata = None`, `0` NaN, `0` Inf, `min = 0.0`, `max = 1.0`, `arr[~footprint].max() = 0.0`, `arr[catalogue].max() = 0.0`, `(arr > 0).sum() = 44,090`.
- **Link & cross-document number consistency:** Every local link in `README.md`, `docs/index.html`, and `docs/executive-summary.html` resolves on disk; all headline SHA-256, `HOLDOUT-DTI`, leakage canary (`0.8485`), and uniqueness (`0.3012`, `0.6342`, `0.7170`, `0.7656`, `0.9988`) numbers match across `run-card.json`, `lane86b_results.json`, `README.md`, `REVIEW.md`, and `docs/*.html`.
- **Automated unit & integration test suite:** `13 / 13` tests PASS (`2.29s`).
- **Fail-closed protocol compliance:** `experiments_run = 3`, `verdict = "negative"`, `submission_ready = false`, `approved_for_weekly_slot = false` — honoring Protocol Rules 1, 5, and 6 without post-hoc hyperparameter gaming.
