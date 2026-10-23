# Three-Pass Verification Record — GEMSDOE86 (`H86-CTHB`)

## Session `arena/4908895b-gemsdoe86` (2026-10-22 / 2026-10-23 UTC)

### Pass 1 — Implement & Verify End-to-End
1. **Prior-Session Review & Fleet Forensics:**
   - Audited `README.md`, `research/REVIEW.md`, PR #6's negative `H86-RMRB` run (`HOLDOUT-DTI = 0.0420 [0.0369, 0.0467]`), `GEMSDOE32`'s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`37,654` dots, `0.2778` user/owner-reported; exact `r=2 px` collar prune + `NaN->0` conversion of `D2.8`), and 25 sibling repositories (`GEMSDOE24`–`88`).
   - Verified official competition specification (`drivendata.org/competitions/306/competition-doe-gems/page/967/`), live public leaderboard (`#1 0.4413`, `#5 0.3539`, `#50 0.2817`), Sept 2026 DOE/NLR Official Rules (`docs.nlr.gov/docs/fy26osti/96647.pdf`), and DOE GDR #1391 (`gdr.openei.org/submissions/1391`).
   - Archived PR #6's negative candidate in `docs/downloads/archive_negative_pr6/` and built `research/h86_extended_manifest.json` + `scripts/restore_lane_data.py` (55 SHA-256-pinned inputs & cross-repo sibling rasters).
2. **Preregistered Hypotheses & `H86-CTHB` Implementation (`scripts/h86_features.py`, `scripts/run_lane86.py`):**
   - Ranked 5 candidate geological/geothermal hypotheses in `research/REVIEW.md` prior to coding, selecting `H86-CTHB` (Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach Relay Mechanics).
   - Built 28 static zero-catalogue planes (RTP & gravity ridge-tangent contact truncations, Gallardo–Meju magnetic–gravity cross-gradients, locally deconfounded K/Th × DEM cross-gradients, GDR 1391 2 m probe `F2mDAB` plumes, paleo-sinter/tufa vents, 300 m upslope spring geothermometers, MT clay-cap edges, and shoreline-deconfounded 1 m LiDAR / 10 m DEM scarplets & fluvial `χ`) + 7 strictly fold-visible crack-tip, bend-splay, and two-host relay-breach fields.
   - Executed 35-feature leakage canary (`max_disc_auc = 0.86634 <= 0.90`, `shuffled = 0.4986`), 3-experiment LOQO progression (`E1`, `E2`, `E3`), 38-raster uniqueness check, and `vendor/gems57/submission_writer.py` export.

### Pass 2 — Review & Fix Bugs, Edge Cases & Missing Requirements
1. **Fixed `SW.write_submission` API Contract:** Removed unsupported `outside`/`zip_output` keyword arguments and matched exact `vendor/gems57/submission_writer.py` signature `(path, prediction, sample, footprint, *, note, name, catalogue, metadata)`.
2. **Resolved Contextual-Collar Saturation Trap (`0.7351 -> 0.6852 <= 0.70`):**
   - Diagnosed why single-stage submodular allocation (`0.3015` on `all`) and narrow `d <= 10 px` splits (`0.7351` overlap) exceeded the `0.70` 3-px dot-overlap cap against `174,232`-dot `gems10-h25-ctx-ridge`.
   - Implemented Two-Stage Quota-Split Minoux `R = 300 m` Submodular Allocation (`NEAR_SPLIT_PX = 15.0`, `NEAR_QUOTA_FRAC = 0.54`, `surf_far = 0.35*p_mech + 0.65*p_phys`), reducing max discriminating 3-px overlap across all 37 rasters to `0.6852 <= 0.70` (`<= 0.4878` vs all modern `~36.5k–51.7k` sibling dot rasters) while placing `5,696` dots (`15.13%`) at `> 2.5 km` from mapped faults.
3. **Pooled Whole-Component Buffered Holdout & Memory Ceiling:**
   - Pooled `buffered_component_draw` across `seeds=(20, 21)` (`22,893` withheld pixels) to match `gems57-pooled-hide-v2` and added explicit `del` + `gc.collect()` before 38-raster scanning to keep RSS safely under the `3.8 GiB` sandbox limit (`3,390.1 MB`).
4. **Fixed `scripts/restore_lane_data.py`, `requirements.txt`, and `scripts/audit.py`:**
   - Added multi-part GitHub blob assembly (`parts`) and full 23-entry base manifest coverage in `scripts/restore_lane_data.py` (`55/55` files verified).
   - Added `pandas>=2.2,<3.0` to `requirements.txt`.
   - Upgraded `scripts/audit.py::run(root: Path = ROOT)` so missing-evidence tests run isolated in `tempfile.TemporaryDirectory()` without clobbering `docs/evidence/run-card.json`, while `python scripts/audit.py` runs 24 automated format, `[0, 1]` range, SHA-256, uniqueness, holdout, and HTML sync checks in CI.
   - Removed duplicate `ZIP SHA-256` draft text in `docs/executive-summary.html`.

### Pass 3 — Final Re-Check Against Full User Request & Polish
- Let's verify every deliverable and check:
  - **Shared `vendor/gems57/` integrity:** `23/23` files byte-identical to `research/template_pin.json` (`check_pins(ROOT) == True`).
  - **Unique `.tif` + `.zip` generated & validated:** `docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.{tif,zip,json}` (`sha256 = e382e638d248e9d638182eb5c2e875eee7d819f859d9753c27005e652a0cd425`), `15/15` validator checks PASS, `min = 0.0, max = 1.0`, `n_nan = 0`, `n_infinite = 0`, `EPSG:32611`, `3730×3292`, `0` catalogue overlap.
  - **Submission note length:** `98 <= 140` characters (`GEMS86 H86-CTHB LOQO contact-trunc+2mDAB/sinter+relay submod 37654d HOLDOUT-DTI=0.2506 [0,1] zeros`).
  - **Automated audit & unit tests:** `python scripts/audit.py` (`24/24` checks `True`), `python -m unittest discover -s tests -v` (`11/11` tests `OK`), `python -m compileall -q scripts vendor tests` (`exit 0`), `git diff --check` (`clean`), and local HTML link/target check (`all links resolve`).
  - **GitHub Pages UI & Executive Summary:** Top-of-page `🟢 OK TO DOWNLOAD & SUBMIT` banner on both `docs/index.html` and `docs/executive-summary.html`, step-by-step upload guide, `GEMSDOE32` autopsy, 5 ranked hypotheses, 3-experiment ablation ledger, verified official source table, and honest risk/limitation disclosures.

---

## Historical Preflight Record (Prior Sessions — Preserved for Provenance)

Earlier preflight sessions (`2026-10-22`) established the `vendor/gems57/` pin (`research/template_pin.json`), safety unit tests, and negative `H86-RMRB` baseline (`docs/downloads/archive_negative_pr6/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif`, `HOLDOUT-DTI = 0.0420`). All earlier blockers (missing extended feature stack, 12-only local registry, weak global radiometric regression) were resolved in `H86-CTHB` above.
