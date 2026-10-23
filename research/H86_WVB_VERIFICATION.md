# Three-Pass Verification Record (`GEMSDOE86` · Lane `H86-WVB`)

- **Verification Date:** 2026-10-22 UTC
- **Branch:** `arena/7ab8d89e-gemsdoe86`
- **Primary Artifact:** `docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif` (`SHA-256: d0231888c4567816d706cca360c8fe0cd98fc0b673409edb3ffc5649e3d1bdf3`)
- **Automated Verdict:** **`negative` (`🔴 DO NOT SUBMIT TO WEEKLY PORTAL SLOT`)**

---

## Pass 1 — Implement, Restore Pinned Data, and Execute End-to-End Without Human Intervention

1. **Workspace, Sibling Fleet & Upstream Audit:**
   - Inspected all tracked files in `GEMSDOE86`, all 23 SHA-256-pinned modules in `vendor/gems57/` (`60GEMSDOE@b99591eede63c6d45c8a896255b8cd34824fa00b`), `research/upstream/h33.py`, `research/upstream/h33-best-audit.json`, and sibling repositories `GEMSDOE28..GEMSDOE88`.
   - Verified hardware envelope (`2` CPUs, `3.8 GiB` cgroup RAM `memory.max`, `0 B` Swap) and egress policy (GitHub/PyPI/npm allowed; `earthquake.usgs.gov` blocked `HTTP 000`; `drivendata.org` login-walled).
2. **Hash-Verified Data & 43-Raster Registry Restoration (`scripts/restore_lane_data.py`):**
   - Restored and SHA-256-verified all 23 `data_manifest.json` files (`training_features.tif`, `existing_faults.tif`, `sample_submission.tif`, `labels.tif`, 7 external rasters/CSVs, 12 upstream scored rasters), plus 3 supplemental `60GEMSDOE@b99591ee` external files (`Paleo_geothermal_final.csv`, `topo_10m_derived_100m_u8.tif`, `usgs_sgmc_faults_100m.tif`) and **30 deduplicated `3730 x 3292` sibling champion GeoTIFFs** (`GEMSDOE32..GEMSDOE88`) into gitignored `data/`, recording hashes in `research/sibling_champions_manifest.json` and `docs/evidence/lane_data_restore.json` (`mismatch_count: 0`).
3. **Hypothesis Ranking & `H86-WVB` 3-Experiment Execution (`scripts/run_h86_wvb.py`):**
   - Ranked 5 untried geological hypotheses (`H86-WVB`, `H86-CCMO`, `H86-RTDR`, `H86-TSBA`, `H86-SEIS-3D`) prior to model implementation.
   - Executed `scripts/run_h86_wvb.py` cleanly inside the 3.8 GiB RAM cap (`1240.36 s`, `exit_code = 0`):
     - **Gate 2 Leakage Canary (`36 / 36` PASS):** `seed=20` `max_disc_AUC = 0.87047 <= 0.90`; `seed=21` `max_disc_AUC = 0.86697 <= 0.90`; shuffled control `0.51399`.
     - **Gate 3 Buffered Whole-Component `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `22,893` px, `159` 20 km clusters):** `E1_static_physics_nms = 0.07209 [0.05835, 0.08572]`, `E2_coupled_valve_nms = 0.14237 [0.12739, 0.15614]`, **`E3_dual_submod300 = 0.15792 [0.13884, 0.17587]`** vs `d28_incumbent = 0.10093` (`+56.5%`) and `h33_foldfair = 0.10564` (`+49.5%`). Secondary `build_holdout` (`22,641` px): `all = 0.30237`, `detached = 0.12233`.
     - **Gate 1 Zero-Touch GeoTIFF Serialization (`15 / 15` PASS):** Wrote `docs/downloads/gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.{tif,zip,json}` via unmodified `vendor/gems57/submission_writer.py` (`zeros` mode) and verified via `vendor/gems57/validate.py` (`EPSG:32611`, `3730 x 3292`, `100 m`, `0 NaN`, `0 Inf`, exact `{0.0, 1.0}`, `37,654` dots inside footprint, `0` outside, `0` on catalogue, note `94 <= 140` chars).
     - **Gate 4 43-Raster Uniqueness Audit:** Surface `max |rho| = 0.12710 <= 0.90`, dot `max |rho| = 0.09489 <= 0.90`, **30/30 sibling champions (`GEMSDOE32..88`) `< 0.70` 3-px overlap** (`max = 0.63531`; `GEMSDOE32 H33-2-B2 = 0.29280`), blocked by `gems10-h25-ctx-ridge` (`0.78531`) and `gems10-h28-dotted-ridge` (`0.74146`) -> strict `verdict = "negative"`.

---

## Pass 2 — Bugs, Hidden Assumptions, Edge Cases, and Regression Fixes

1. **Fixed `IR-86-AUDIT-CLOBBER-01` in `scripts/audit.py`:**
   - *Bug found:* Earlier `scripts/audit.py:run()` unconditionally overwrote `docs/evidence/run-card.json` with a blank preflight stub whenever `unittest` ran `test_audit.py`.
   - *Fix applied:* Refactored `scripts/audit.py:run(evidence_path=..., write_out=None)` so default verification is strictly read-only, fails closed (`verdict: "negative"`, `ready_to_submit: False`) when evidence is absent, verifies all 23 `vendor/gems57/` template pins, and validates the live `H86-WVB` `.tif` / `.zip` hashes and `15/15` GeoTIFF checks when `run-card.json` is present.
2. **Fixed `IR-86-LIDAR-01` Band-Header Bug:**
   - *Bug found:* Upstream `h33.py` indexed bands `(1, 2, 5)` of `lidar_scarp_features_u8.tif` for `(ex_max, step_max, downface_max)`, whereas actual GeoTIFF band descriptions are `1=ex_max, 2=ex_mean, 3=step_max, 6=downface_max, 7=upface_max, 9=relief, 10=coh100, 12=valid`.
   - *Fix applied:* Verified every band description directly via `rasterio` and bound exact band indices in `scripts/run_h86_wvb.py`.
3. **Fixed `IR-86-PR6-EVAL-01` Holdout Catalogue-Masking Trap & `dist_known_fault_px` Leakage Guard:**
   - *Bug found:* Prior PR #6 masked full `existing_faults.tif` (`B=2 px`) prior to `evaluate_holdout`, wiping out withheld segments near visible splits (`0.04199 -> 0.00376`); additionally, `ing_wells_geotherm_metrics.csv` contained a `dist_known_fault_px` column.
   - *Fix applied:* Masked only fold-visible `d_visible <= 2 px` during holdout and strictly excluded `dist_known_fault_px` from `STATIC_NAMES`.
4. **Fixed 29-px Submodular Blob Bias & 3.8 GiB cgroup Memory Envelope:**
   - Replaced raw diffuse probability kernel allocation with multiplicative physical corroboration $p_{E2}^{0.85}\,p_{E1}^{0.15}$ + `min_dist_px = 2.8 px`, and staged array lifecycles so peak RSS stayed `< 1.5 GiB` inside the `3.8 GiB` container limit with `0 B` swap.
5. **Aligned Run-Card & Generator Mechanism Strings + CI-Safe Tests (`tests/test_audit.py`):**
   - Synchronized `mechanism` and `IR-86-LATTICE-01` text between `scripts/run_h86_wvb.py` and `docs/evidence/run-card.json` to match exact `E3` code and empirical `40/42` non-lattice `<0.70` counts.
   - Ensured `tests/test_audit.py` passes both locally (with `data/` present) and on GitHub Actions CI runners (where `data/` is gitignored and `validate.validate(tif_path)` runs grid/CRS/transform/`[0, 1]` checks standalone).

---

## Pass 3 — Final Line-by-Line Verification Against Every Requirement in the Original Prompt

| Prompt Requirement | Verification Check | Status |
|---|---|---|
| Review previous work first & preserve starting brief in `README.md` | Audited PR #4/#5/#6 history, `GEMSDOE32`, `60GEMSDOE`, and `GEMSDOE28..88`; preserved starting brief in `README.md` and cleared stale preflight claims across `README.md`, `research/REVIEW.md`, and `research/VERIFICATION.md` | **PASS** |
| PhD-level explanation of why `GEMSDOE32` (`h33-h33-2-b2-...-zeros`, `0.2778`) scored highest & how to score higher (`0.3195`–`0.4413`) | Documented exact DTI numerator/denominator asymmetry, `2.8 px` dotting, `B=2 px` collar prune (`-2,545` dots), `zeros` portal fix, and algebraic credit-per-dot inversion in `README.md`, `docs/index.html`, and `research/REVIEW.md` | **PASS** |
| Pre-implementation ranking of 3–5 untried geological hypotheses + external data check | Ranked 5 hypotheses (`H86-WVB`, `H86-CCMO`, `H86-RTDR`, `H86-TSBA`, `H86-SEIS-3D`) with named layers, physical signatures, missing-fault targets, mimics, novelty, cost, and verified `earthquake.usgs.gov` egress block | **PASS** |
| Reuse shared template tools (`vendor/gems57/`) without private forks | `23/23` files in `vendor/gems57/` match SHA-256 pins in `research/template_pin.json` (`template_pin_ok: true`) | **PASS** |
| Single-feature leakage canary (`AUC <= 0.90`) | `36/36` features tested across seeds `20` & `21`; max `disc_AUC = 0.87047 <= 0.90`; shuffled control `0.51399` | **PASS** |
| Budget (`<= 3` experiments / `<= 2` hours) & strict score labelling (`HOLDOUT-DTI` / `ORGANIZER-CONFIRMED`) | `3/3` experiments (`E1`, `E2`, `E3`) completed in `1240.36 s` (`20.7 min`); every holdout figure carries `HOLDOUT-DTI` + evaluator version + withheld count + 95% CI; zero unreceipted numbers tagged `ORGANIZER-CONFIRMED` | **PASS** |
| Unique automated `.tif` in `[0, 1]`, no NaN/Inf/sentinels, matching CRS/shape/transform, unique name & note `<= 140` chars | `gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif` (`d0231888...`) passes `15/15` automated checks (`min=0.0, max=1.0, nan=0, inf=0, EPSG:32611, 3730x3292, 100 m`, note `94 <= 140` chars) | **PASS** |
| Immediate download & unmistakable `DO NOT SUBMIT` vs `OK TO SUBMIT` at top of GitHub Pages + executive summary subpage | `docs/index.html` and `docs/executive-summary.html` open with `🔴 DO NOT SUBMIT TO WEEKLY PORTAL SLOT (verdict: negative)`, direct `.tif`/`.zip`/`.json` buttons, and step-by-step DrivenData submission guide | **PASS** |
| End with one protocol-compliant JSON Run Card & keep large data out of Git | `docs/evidence/run-card.json` + final Run Card block in `README.md`; `data/` and `.venv/` excluded via `.gitignore` | **PASS** |

---

## Historical Chronology (Earlier Sessions Preserved for Auditability)
- **Session 1 (Preflight):** Vendored `vendor/gems57/` (`23` files) from `60GEMSDOE@b99591ee`, restored small grid inputs (`existing_faults.tif`, `sample_submission.tif`), and published a negative preflight scaffold with `0` experiments run.
- **Session 2 (PR #6 · `H86-RMRB`):** Restored GeoDAWN radiometrics + `training_features.tif` and ran unsupervised radiometric mixing-residual boundary `H86-RMRB` (`HOLDOUT-DTI = 0.0420 [0.0369, 0.0467]` vs `0.1011` incumbent -> negative). Artifact preserved in `docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif` and `docs/evidence/lane86_results.json`.
- **Session 3 (Current · `H86-WVB`):** Restored full 26-file input/external stack + 30 sibling champion rasters (`43` total deduplicated registry rasters), ranked 5 geological hypotheses, fixed `IR-86-LIDAR-01`, `IR-86-PR6-EVAL-01`, and `IR-86-AUDIT-CLOBBER-01`, and executed `H86-WVB` (`E1`, `E2`, `E3`), achieving `HOLDOUT-DTI = 0.15792 [0.13884, 0.17587]` (`+56.5%` over `d2.8`) and `30/30` sibling uniqueness clearance while logging `verdict: "negative"` on the `gems10` halo overlap gate.
