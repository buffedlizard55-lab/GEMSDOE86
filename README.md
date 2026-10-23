# GEMSDOE86 — Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach Relay Mechanics (`H86-CTHB`)

## 🟢 READY TO DOWNLOAD & SUBMIT — VERDICT: `PROMOTE` (`safe_to_submit = true`)

- **Unique GeoTIFF Candidate:** [`docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.tif`](docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.tif) (`140,584` bytes, `37,654` dots)
- **Single-TIF ZIP Archive:** [`docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.zip`](docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.zip)
- **GeoTIFF SHA-256:** `e382e638d248e9d638182eb5c2e875eee7d819f859d9753c27005e652a0cd425`
- **ZIP SHA-256:** `a0ebdcf1af01bfa3e760af35c2d84c63d5fb69d4d69f13f151b5cf8692d73427`
- **Unique Submission Name:** `gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.tif`
- **DrivenData Note (`98 / 140` chars):** `GEMS86 H86-CTHB LOQO contact-trunc+2mDAB/sinter+relay submod 37654d HOLDOUT-DTI=0.2506 [0,1] zeros`
- **Dashboard & Submission Guide:** [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html) · [`docs/evidence/run-card.json`](docs/evidence/run-card.json) · [`docs/evidence/lane86_results.json`](docs/evidence/lane86_results.json)

### Gate Summary (All Scores Explicitly Classified)

| Gate | Status | Quantitative Result |
|---|---|---|
| **1. Portal Format & `[0, 1]` Fix** | **PASS (`15/15`)** | Single-band `float32`, `EPSG:32611`, `3730×3292` (100 m), `nodata=None`, `0` NaN, `0` Inf, `min=0.0, max=1.0`, `0` outside-footprint positives, `0` mapped-catalogue positives |
| **2. Single-Feature Leakage Canary** | **PASS (`35/35`)** | Max discriminative AUC = `0.8663 <= 0.90` (`shuffled = 0.4986`); `dist_known_fault_px.tif` never read |
| **3. `HOLDOUT-DTI` (`gems57-pooled-hide-v2`)** | **PASS (`3/3` modes)** | **`all` (`22,641` px):** `0.2506 [0.2351, 0.2669]` vs `D2.8 = 0.1011` (`Δ = +0.1495 [+0.1353, +0.1644]`) & fold-fair `H33-2-B2 = 0.0910` (`Δ = +0.1596 [+0.1453, +0.1742]`)<br>**`detached` (`22,619` isolated px):** `0.2588 [0.2402, 0.2779]` (`Δ_D28 = +0.1553 [+0.1389, +0.1730]`, `Δ_H33 = +0.1640 [+0.1474, +0.1814]`)<br>**`buf300m` (`22,893` whole-comp px):** `0.1133 [0.0965, 0.1297]` vs `D2.8 = 0.1009` (`+0.0124`) & `H33-2-B2 = 0.1056` (`+0.0076`) |
| **4. 38-Raster Cross-Repo Uniqueness** | **PASS** | Pre-placement surface `max |ρ| = 0.2008 <= 0.90`; final dots `max |ρ| = 0.0576 <= 0.90`; discriminating 3-px dot overlap `max = 0.6852 <= 0.70` (`<= 0.4878` vs all modern `~36.5k–51.7k` sibling dot rasters) |
| **5. Budget & Selector Discipline** | **READY FOR SELECTOR** | `3/3` budgeted experiments completed in `607.3 s` (`< 7,200 s` cap); zero live weekly slots consumed in sandbox |

---

## Starting brief — read at the beginning of every session

The following is a **condensed operational record** of the owner's long request, not a verbatim transcript. Read this AND `research/REVIEW.md` before any new session work.

- Review previous work first; maximize probability of winning through evidence (`Maximize P(Win)`), and own the outcome end to end (`Own the Outcome`). Do not trade scientific integrity for an optimistic claim.
- Generate a UNIQUE competition-format single-band GeoTIFF, never copy an earlier submission except for education. Make download and readiness status obvious at the beginning of the site. Supply a distinct name and note of at most 140 characters.
- Work autonomously through 3 passes: Pass 1 (implement & verify), Pass 2 (review & fix bugs/missing requirements/edge cases), and Pass 3 (final re-check against full request & polish). Research official free data, preserve provenance and links, flag irregularities, distinguish verified facts from hypotheses. Explain access limits and next steps honestly.
- Parallel-run lane: stay inside one single declared method lane. Check BOTH continuous surface (before placement) and final dots against registry rasters — stop if Spearman rank correlation `> 0.90` or `> 70%` of candidate dots fall within 3 px of any discriminating registered raster.
- Reuse shared `vendor/gems57/` tools (`evaluate_holdout.py`, `submission_writer.py`, `uniqueness.py`, `gates.py`, `validate.py`) byte-identically without private forks. Hide complete fault segments with buffers. Derive catalogue features strictly from visible faults only and mask visible faults pixel-exactly. Pool distance-tolerant Tversky components: `alpha = 0.2`, `beta = 0.8`, `R = 300 m` triangular kernel.
- Test each feature alone on holdout; discriminative AUC `> 0.90` means suspected leakage until disproven. Generate and rank 3–5 candidate geological hypotheses with named layers, physical signatures, missing-fault mechanism, non-fault mimics, novelty vs repo, expected DTI gain, and cost before implementing. Confirm external data availability before treating an external-data idea as viable.
- Benchmark against the best comparable spatial holdout before touching a weekly slot. Stop after 3 experiments or 2 hours. Selection/promotion into a real weekly slot is a separate step respecting the 3/week team quota.
- Report scores ONLY as `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (actual submission receipt). User-reported values (`0.2778`, etc.) and projections are never reported as confirmed scores.
- End with one JSON run card (`docs/evidence/run-card.json`): hypothesis, mechanism, named non-fault mimic, holdout result + CI, registry comparisons, SHA256, serialized raster validation, submission name, `<= 140`-char note, `promote` / `negative`. Negative results are valid deliverables (PR #6's negative `H86-RMRB` candidate is preserved in `docs/downloads/archive_negative_pr6/`).
- Build a clean GitHub Pages site (`docs/index.html`) with an executive summary (`docs/executive-summary.html`) explaining exactly how to submit. Reject NaN/Inf/sentinels and values outside `[0, 1]`, matching `sample_submission.tif` CRS/shape/transform via automated validation (no human-in-the-loop format checks).
- Open and merge a PR onto `main`, then list remaining work and limitations.

---

## Reproduce End-to-End

Requires Python 3.11+ and authenticated `gh` CLI (used only to pull SHA-256-pinned mirrors into git-ignored `data/`):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_lane_data.py     # Restores & SHA-256-verifies 55 input + fleet files
.venv/bin/python scripts/run_lane86.py            # Runs Canary + E1 + E2 + E3 + 38-raster audit + GeoTIFF writer
.venv/bin/python scripts/audit.py                 # Automated zero-HITL verification of .tif, .zip, run-card, & HTML
.venv/bin/python -m unittest discover -s tests -v # 11 safety, pin, leakage, submodular, & artifact unit tests
```

### Repository Architecture

- `vendor/gems57/`: Read-only shared upstream tools (`23/23` files SHA-256-verified by `scripts/audit.py` against `research/template_pin.json`).
- `scripts/restore_lane_data.py` & `research/h86_extended_manifest.json`: SHA-256-pinned restoration of core GeoTIFFs, 10 official external USGS/DOE GDR layers, 12 local registry rasters, and 25 cross-repo sibling rasters.
- `scripts/h86_features.py`: 28 static zero-catalogue geophysical/geothermal/3DEP planes + 7 strictly fold-visible anisotropic crack-tip, bend-splay, and two-host relay-breach fields.
- `scripts/run_lane86.py`: 4-quadrant LOQO trainer (`E1`, `E2`, `E3`), Two-Stage Quota-Split Minoux `R=300 m` submodular kernel allocator, 38-raster uniqueness gate, and `submission_writer` export.
- `scripts/audit.py` & `tests/test_audit.py`: Automated format, `[0, 1]` range, SHA-256, uniqueness, holdout, and HTML synchronization checks executed in GitHub Actions CI (`.github/workflows/verify.yml`).
- `research/REVIEW.md` & `research/VERIFICATION.md`: Preregistered forensic audit, `GEMSDOE32` autopsy, 5 ranked hypotheses, post-run ablation results, and 3-pass verification log.
- `docs/`: GitHub Pages readiness dashboard (`index.html`), step-by-step upload guide (`executive-summary.html`), promoted `.tif`/`.zip`/`.json` artifacts (`downloads/`), and archived negative PR #6 baseline (`downloads/archive_negative_pr6/`).
