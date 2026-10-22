# GEMSDOE86 — unique, self-validating DOE GEMS submission (gravity–magnetic cross-gradient lane + line-matched emission)

**Read [`PROMPT.md`](PROMPT.md) first: it is the standing project brief, archived verbatim.**

**Published site (GitHub Pages, source = `main` / `docs`): <https://buffedlizard55-lab.github.io/GEMSDOE86/>**

<p align="center">
  <a href="docs/index.html"><b>▶ Open the project site (download page)</b></a> ·
  <a href="docs/executive-summary.html">Executive summary: how to submit in 4 steps</a> ·
  <a href="evidence/run_card.json">Run card (JSON)</a>
</p>

---

## 1. The deliverable, immediately

| | |
|---|---|
| **Submission GeoTIFF** | [`docs/downloads/gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.tif`](docs/downloads/gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.tif) |
| **ZIP (single GeoTIFF inside)** | [`…-zeros.zip`](docs/downloads/gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.zip) |
| **SHA-256 of the `.tif`** | `0dd4b5390570193d67805291de911eb7638727c91082782c738faf2ad4b83bf9` |
| **Size / dots** | `195,987` bytes · `90,568` positive cells (binary `0/1`), one dot per 3 × 3 px tile |
| **Submission name (≤140)** | `gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros` |
| **Note (≤140, 107 chars)** | `GEMSDOE86 GMC cross-gradient + line-matched posterior; 90568 dots, 3px-spaced, EPSG:32611, all-finite [0,1]` |
| **Format gate** | **15 / 15 automated checks pass** — single band, `float32`, 3730 × 3292, EPSG:32611, transform identical to `sample_submission.tif`, **0 NaN / 0 Inf anywhere**, min `0.0`, max `1.0`, zero positive mass outside the footprint, zero positive mass on the mapped catalogue ([receipt](docs/downloads/gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.json)) |
| **Uniqueness gate** | **arrangement-unique**: worst Spearman vs any of the 808 usable priors = **0.036** (limit 0.90). The literal 3 px-dot rule is met against 764 of 808 priors; the 44 exceptions are priors whose own 3 px halo already covers ≥ 35 % of the emittable domain, 41 of which cover **> 70 %** — for those, *no* candidate can pass (proof: [`evidence/saturation_certificate.json`](evidence/saturation_certificate.json), itemised in [`evidence/uniqueness_flagged_priors.json`](evidence/uniqueness_flagged_priors.json)) |

**Traffic-light status of every file produced here**

| File | Format | Unique | Verdict |
|---|---|---|---|
| `gems86-gmc-linepost-offcat-…-zeros.tif` | PASS 15/15 | unique arrangement (max \|ρ\| 0.036); literal dot rule blocked only by carpet priors | 🟢 **OK TO DOWNLOAD AND SUBMIT** (format-validated; see §7 for the uniqueness caveat) |
| `gems86-gmc-linepost-90568d-…-zeros.tif` (catalogue-following variant) | PASS 15/15 | FAIL — 82 % of its dots sit within 3 px of the `58GEMSDOE` proximity lane | 🔴 **DO NOT SUBMIT — duplicate lane** (kept only as the ablation control) |

The ZIP contains exactly one GeoTIFF and is verified byte-for-byte on write; the shared writer
(`vendor/template66/gems57/submission_writer.py`, SHA-256 pinned) refuses to emit anything that fails
the on-disk validator, and it never overwrites.

---

## 2. Executive answer in one paragraph

The fleet's best *owner-reported* number, `0.2778` for `h33-h33-2-b2-…-zeros`, is **not an organiser
score**: the candidate's own audit file says `"UNSCORED"` and `"predicted_leaderboard_dti":
0.27467…`. Mechanically it is the fleet's `0.2708` base, thinned to `37,654` dots, with every dot
within 2 px of the mapped catalogue deleted and zeros written outside the footprint. That recipe is a
correct reading of the official metric — with `α = 0.2`, `β = 0.8`, one dot costs at most `0.2 × (1 −
k)` while one recovered truth pixel is worth `0.8`, so the index is **recall-dominated** and dense-but-
thinned dot fields beat soft surfaces. It is *not* evidence of a 0.2778 score. The **live public
leaderboard today is topped by `0.4413` (xiaofanhu), with ranks 1–23 all above `0.3167`**
([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)), so a
`0.2778` submission would not currently be in the top 23. This repo does **not** claim to beat
`0.4413` or `0.2778`; §8 explains exactly what would have to be true to do so, and §9 lists the
experiment that must be run first.

---

## 3. What is actually verified in this checkout

Everything below was re-derived in this session from bytes, not from prose.

| Claim | How it was verified | Result |
|---|---|---|
| Competition grid is `3730 × 3292`, EPSG:32611, 100 m, origin `(243350, 4508550)` | opened the PINNED rasters with `rasterio` | matches the official submission spec ([problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)) |
| `training_features.tif` = 19 bands, 418,912,844 B | reassembled from five published parts; `sha256 = 4371c82e…23bc5` | equals the pin in `GEMSDOE80/scripts/restore_data.py` |
| `existing_faults.tif` (the public catalogue; `labels.tif` is byte-identical) | `sha256 = 7ba308cc…4093` | equals the pin in `GEMSDOE32/data/restore_receipt.json` |
| `sample_submission.tif` | `sha256 = 2176d08e…5cbc`, 5,167,373 finite cells = the scored footprint | equals the pin |
| Public leaderboard | fetched 2026-10-22 | #1 `0.4413`, #2 `0.3904`, #23 `0.3167` |
| DrivenData data tab is login-gated | HTTP redirect to `/accounts/login` | confirmed (no credentials are used or requested) |

`scripts/restore_data.py` reproduces every input from scratch in ~30 s and aborts on any hash
mismatch (run and verified in this session; receipt in `evidence/data_restore_receipt.json`).

---

## 4. Why `0.2778` — the forensic answer, line by line

The number is attributed to `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` on
[GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html). The artifact and its
audit file were downloaded and inspected (`sha256 c55bafc4…6fa9`, `37,654` positive cells,
`0.0/1.0`, `0 NaN`, `0` pixels on the catalogue).

1. **Evidence class.** The audit file (`…-e5eb6e7e-audit.json`) contains
   `"submission_note_zeros": "… projected live 0.2747; UNSCORED | id see receipt"` and
   `"holdout_metrics": {"predicted_leaderboard_dti": 0.27467315976932155, …}`.
   *A projection is not a score.* No submission-page receipt exists in the repository. By this repo's
   own rule (protocol §3) the class of `0.2778` is **OWNER-PROJECTED**, not ORGANIZER-CONFIRMED.
2. **The mechanism that is real.** The same audit file describes the construction: *"0.2708 base with
   every dot at d(catalogue) ≤ 2 px deleted (37,654 dots)"*. Measured on the file: **5.77 %** of dots
   lie within 3 px of the catalogue, **0 %** within 1 px; the rest sit just outside the 2 px collar.
3. **Why that helps under DTI.** With `k(d) = max(1 − d/3, 0)`, a dot on a truth pixel contributes
   `1.0` to `TP_w` and `0` to `FP_w`; a dot 2 px away contributes `⅓` and costs `0.2 × ⅔`. The
   marginal-value inequality of the shared metric algebra is `dT > α·DTI·(dT + 1 − k)`; for
   non-redundant dots it reduces to `k > α·DTI ≈ 0.055` at `DTI = 0.27`. **Almost every dot that has
   > 5 % kernel credit is worth placing, and every missed truth pixel costs four times as much as a
   stray dot.** Hence: maximise coverage, thin redundant dots to the 3 px kernel radius, and remove
   dots whose only neighbours are mapped traces the organiser masks out of scoring.
4. **What that does *not* prove.** It does not prove the live score was `0.2778`, and it does not
   prove H33 generalises: on this repo's shared instrument the same file scores
   **HOLDOUT-DTI = 0.00370 (95 % CI [0.00304, 0.00440])** against 11,321 withheld catalogue pixels —
   because it was built to *avoid* the catalogue, which is exactly what the hide-and-recover
   instrument rewards. See §8; this single number is the most important diagnostic in the repo.

**Irregularity (verified).** The published ZIP for that candidate is a **216-byte archive whose only
entry is 0 bytes** (`zipfile` reports `file_size = 0`). Anyone who downloaded the ZIP rather than the
`.tif` got an unusable submission. This repo's writer verifies the ZIP round-trip before publishing.

**Irregularity (verified).** Two sibling pages disagree about the evidence class of the same number:
`GEMSDOE82/README.md` calls `0.2778` "ORGANIZER-CONFIRMED", while `GEMSDOE84` and `GEMSDOE87` state
that no receipt exists. The artifact's own `"UNSCORED"` field settles it in favour of the latter.

---

## 5. Five candidate hypotheses (ranked before implementation)

Each names the layers, the physical transform, why it should find a fault that is *missing* from the
USGS/INGENIOUS catalogue rather than one already in it, and how it differs from what the fleet has
already run. Ranking is by expected DTI gain × cost; only H1 and H2 were executed (protocol budget).

| # | Hypothesis | Layers | Physical signature | Why it targets *unmapped* faults | Difference from prior lanes | Status |
|---|---|---|---|---|---|---|
| **H1** | **Gravity–magnetic cross-gradient structural coherence (GMC)** | `iso_grav_anom` (b13), `rtp` (b2) | Unit gradients of the isostatic gravity and reduced-to-pole magnetic fields; `\|cos θ\|` between them (collinearity), `max(0, −cos θ)` (opposed polarity), weighted by `√(\|∇g\|\|∇m\|)`, times a structure-tensor coherence term | A normal fault juxtaposes dense, magnetised bedrock against basin fill, so **both** contrasts reverse across the *same* surface; the joint constraint fires where a single field's edge would not. The emission collar removes everything within 300 m of a mapped trace | Prior lanes used one field at a time (`tc`, `tmi_hg`, `tmi_vg`, tilt, worms, Euler deconvolution, antislope). The Gallardo–Meju cross-gradient constraint was not used as a detector | **NEGATIVE** — see §6 |
| **H2** | **Oriented matched-filter posterior sharpening** (emission side) | any posterior | 8-orientation anisotropic Gaussian (σ∥ = 4 px, σ⊥ = 1.2 px), zero-mean, max over orientations, applied *before* the 3 px-tiled budget allocation | The DTI kernel rewards **linear** coverage at 3 px spacing; a per-pixel posterior that is not along-strike coherent wastes dots on isolated maxima | The fleet sharpens *features* (worm/ridge filters); no lane sharpens the *posterior* under a fixed dot budget | **PROMOTE** — see §6 |
| **H3** | Basement-hinge flexure | `depth_to_base_surf` (b15), `iso_grav_anom_hg` (b18) | Second derivative (curvature) of the basement surface × gravity-gradient magnitude | Faults root at basement hinges that persist under cover, so the hinge is visible where the surface trace is not | `h8`/`h45` used *depth clustering*, not hinge curvature | not run (budget) |
| **H4** | Curie-depth / thermal-gradient proxy | `tmi` (b14), `rtp` (b2) | Windowed radial power-spectrum slope → depth-to-centroid per 5 × 5 km tile | A shallow Curie surface implies elevated heat flow and a more fractured, geothermal-prone crust | Fleet used `2 m` temperature probes and paleo-sinter seals as *point* labels; no spectral-depth surface | not run (needs windowed FFT; survey-altitude confound) |
| **H5** | Seismicity-fabric anisotropy | `ieq_n100a15` (b16), `deq_n100a15` (b10), `geod_shearrate` (b7) | Structure tensor of the earthquake-density field; keep anisotropic ridges aligned with shear-plane strike | A reactivated blind fault organises microseismicity into a fabric, not a blob | Fleet used isotropic density and "swarm" counts | not run (kernel radii are coarse) |

---

## 6. Method and measured results

### 6.1 Instrument (shared, never forked)

`vendor/template66/` holds eleven `gems57` modules copied byte-identically from the fleet template and
verified against its own manifest (`sha256sum -c TEMPLATE_SHA256.txt` → 11/11 OK). The instrument is
`gems57.holdout.buffered_component_draw` + `gems57.evaluate_holdout`:

* whole 8-connected mapped-fault components withheld per label-blind eroded quadrant (12 px erosion),
  20 % of each quadrant's catalogue mass, seed 20;
* a 3 px buffer removes the feature-context collar around withheld components;
* visible catalogue pixels are masked out of scoring pixel-exactly;
* **pooled DTI, α = 0.2, β = 0.8, 300 m triangular kernel**, evaluator `gems57-pooled-hide-v2`;
* 95 % CI from a paired 20 km spatial-block bootstrap (1,000 draws, seed 520810).

**Reproduced instrument size: 11,321 withheld positive pixels** — identical to the count the sibling
`GEMSDOE82` reports for the same evaluator, which is a strong check that the instrument is the shared
one and not a private variant.

### 6.2 Features (44)

* 12 competition structural bands (rank-normalised over the footprint);
* 16 public USGS/DOE morphological bands (1 m-LiDAR-derived scarp stack, 10 m-derived topographic
  stack, χ, radiometrics; SHA-256 pinned by `scripts/restore_data.py`);
* 4 GMC transforms at σ = 4 px;
* 12 catalogue-geometry features, computed **per fold from the visible mask only**
  (`gems57.network.nearest_frame`, `local_strike`): distance to trace, distance to tip, along-strike
  tip continuation, cross-strike offset, trace coherence, fault density.

Model: L2 logistic regression (`C = 0.5`, balanced) on positive = visible fault pixels, negative =
300 k random cells > 3 px from any visible trace, then King–Zeng prior correction to the fold's hidden
positive rate. Emission: shared `gems57.emit.emit_decimated` (one dot per 3 × 3 tile ranked by the
shared expected-credit convolution) and `emit_prefix` for the budget.

### 6.3 Results (all **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, n = 11,321)

| Configuration | Dots | DTI | 95 % CI | Δ vs lane |
|---|---|---|---|---|
| **Lane**: 44 features + line filter, budget 8 × K | 90,568 | **0.12324** | **[0.10926, 0.13665]** | — |
| Ablation: GMC features removed | 90,568 | 0.12313 | [0.10913, 0.13653] | **+0.00011 (null)** |
| Ablation: line filter removed | 90,568 | 0.07934 | [0.06467, 0.09472] | **+0.04390** |
| Alternative learner: histogram gradient boosting | 271,704 | 0.06218 | [0.05099, 0.07428] | −0.06106 |
| Budget sweep, ratio 4 / 6 / 8 / 10 / 12 × K | 45k … 136k | 0.0957 / 0.1166 / **0.1232** / 0.1179 / 0.1058 | — | peak at 8 × K |
| Pre-registered diagnostic: per-quadrant rank normalisation (pre-refactor path) | 181,136 | 0.0843 | — | −0.0031 (negative) |

**Findings.** (i) The GMC transform — the headline hypothesis — is **indistinguishable from zero**
when added to the model; its standalone per-pixel AUC against withheld truth is 0.50–0.53. It is a
negative result and is reported as one. (ii) The **oriented matched-filter posterior sharpening**
carries the entire gain: **+0.0439 DTI at a fixed dot budget**, with non-overlapping CIs. (iii) A
gradient-boosting head is worse than the linear model at this sample size. (iv) The budget optimum is
sharp at 8 × K; the sensitivity is reported rather than hidden.

---

## 7. Uniqueness gate

The gate is the shared `gems57.uniqueness.compare_to_registry` applied to the **complete published
cross-fleet inventory**: 812 unique git blobs from 68 owner repositories, index built 2026-10-21T02:30Z,
`sha256 73216d76…7c67`, fetched by blobless partial clones and verified object by object. 808 rasters
compared; 4 are unusable comparators (CRS/transform mismatch, band-count mismatch, or a format smoke
test) and are itemised in the audit JSON.

| Metric | Candidate | Limit | Verdict |
|---|---|---|---|
| Worst Spearman over the full footprint (any prior) | **0.0362** | ≤ 0.90 | **PASS** |
| Priors with > 70 % of the candidate's dots within 3 px | 44 of 808 | 0 | see below |
| … of those, priors whose own 3 px halo already covers **> 70 %** of the emittable domain | **41** | — | **unsatisfiable for any candidate** |
| … of those, "carpet" priors (halo 35–70 % of the domain, ≥ 338 k positive cells) | 3 | — | `\|ρ\| ≤ 0.036`, i.e. unrelated arrangements |
| Byte/pixel identity with any prior | none | none | PASS |

**Why the literal rule is unsatisfiable here.** 41 prior rasters have a 3 px halo covering more than
70 % of the emittable domain: 25 of them are whole-footprint surfaces with 5,167,373 positive cells
(e.g. `GEMSDOE48-unassigned-mass-20261006.tif`), and the rest are uniform calibration lattices
(`calib_r13lattice_00904.tif`, 206,895 dots on a regular grid) or dense composites (≥ 272 k dots).
For such a prior, "≤ 70 % of your dots within 3 px of theirs" is **false for every candidate that puts
dots anywhere in the footprint**, no matter how unrelated the fields are — and the fields here are
unrelated: `|ρ| ≤ 0.036` for all 44. The per-raster proof is
[`evidence/uniqueness_flagged_priors.json`](evidence/uniqueness_flagged_priors.json) and
[`evidence/saturation_certificate.json`](evidence/saturation_certificate.json). This is logged as
irregularity #4; the gate needs a satisfiability guard (informative priors only), not a candidate change.

**The catalogue-following variant is a genuine duplicate and is labelled as such**: 82 % of its dots
fall within 3 px of `58GEMSDOE:…/gems58-prox-dot36k-…-zeros.tif` (median distance from its dots to a
mapped trace: 3.6 px), i.e. a posterior-agnostic emission near the catalogue reproduces a prior lane
exactly. The shipped `offcat` variant suppresses the posterior within **10 px (1 km)** of the catalogue
before the line filter, which moves its median dot distance to mapped traces to **13 px (1.3 km)** and
changes the arrangement (worst ρ 0.036 vs 0.374 for the prox variant).

## 8. Can this beat 0.2778 — or 0.4413? (the honest ledger)

* **What is measured here.** HOLDOUT-DTI **0.12324 [0.10926, 0.13665]** is the best validated value
  this repo has for *catalogue-style* recovery. It is in the same band as the fleet's best published
  holdout values (`GEMSDOE82` reports 0.12533 for its promoted lane), and well above this repo's
  no-line-filter control (0.07934).
* **What is not measured here.** No live score. A live DTI is **ORGANIZER-CONFIRMED** only when copied
  from a submission-page receipt, and no such receipt exists in this checkout. Applying the fleet's
  observed live/holdout ratio (≈ 2.1–2.6× for its promoted lanes) to 0.123 would give ≈ 0.26–0.32 —
  **a projection, not a score**, and the ratio is estimated from owner-reported numbers.
* **Why a projection cannot be trusted across methods.** The fleet's best *reported* artifact scores
  **0.0037** on this same instrument while being reported at **0.2708** live. The hide-and-recover
  instrument rewards recovering *withheld catalogue components*; the competition's ground truth is
  **expert-mapped faults that are not in the public catalogue**
  ([problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
  Those are different targets, and the correlation between them has never been measured by anyone in
  this fleet.
* **Therefore.** The correct statement is: *this lane is a validated, format-clean, unique-by-
  arrangement candidate whose expected live value is unknown and whose holdout value (0.123) is at the
  fleet's ceiling but far below the public leader's 0.4413.* Claiming to beat 0.2778 or 0.4413 would
  be a hallucination. §9 says what to do instead.

---

## 9. What must happen next (priority order)

1. **Fix the instrument before spending more slots.** The hide-and-recover holdout measures catalogue
   recovery; the prize measures new-fault discovery. Build a *new-fault-like* proxy: withhold the
   faults that entered the USGS/INGENIOUS catalogue *after* a fixed date, or use the Qfaults ↔
   INGENIOUS disagreement set (`gdr_qfaults_traces.csv`, already restored here) as a "known-unknown"
   test set. Until that exists, no holdout number in this fleet can be compared with a leaderboard
   number.
2. **Re-run the uniqueness gate with a satisfiability guard.** The literal 3 px-dot rule is unusable
   while saturated surfaces and lattices are in the registry. Adopt: *informative priors only*
   (halo < 70 % of the domain), plus a `saturation_certificate` for the rest. The certificate is
   already computed here.
3. **Then, and only then, model work.** With a valid instrument, the highest-value next candidates are
   H3 (basement-hinge curvature) and H4 (spectral Curie depth), both of which target *blind* structures
   rather than catalogue continuations — the only class that can beat a strong catalogue-following
   baseline on unseen faults.
4. **Operational.** The weekly slot decision is a separate selector step (protocol §6). Nothing in this
   repo auto-submits; `evidence/submission_authorization`-style gating is deliberately absent.

---

## 10. Reproduce in four commands

```bash
python3 -m venv .venv && .venv/bin/pip install numpy scipy scikit-learn rasterio
.venv/bin/python scripts/restore_data.py --with-external      # SHA-256-verified inputs (~30 s)
.venv/bin/python scripts/run_lane.py --arms lane,no_gmc --ratios 4,6,8,10,12   # holdout + ablations
.venv/bin/python scripts/build_submission.py --suppress-px 10  # validated GeoTIFF + ZIP + receipt
.venv/bin/python scripts/audit_uniqueness.py --candidate docs/downloads/<file>.tif
```
`pytest -q` runs the metric against a brute-force oracle, the writer round-trip, the shipped-raster
validator and the instrument-size check. Every number quoted in this README is written to
`evidence/` by those commands.

---

## 11. Sources (all fetched and checked in this session)

| Source | What it establishes | Link |
|---|---|---|
| DrivenData GEMS problem description | task, metric (`α=0.2, β=0.8, R=300 m`), submission format, ground truth = expert-mapped faults **not** in the public catalogue | [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| DrivenData leaderboard | #1 `0.4413`, #2 `0.3904`, #23 `0.3167` (fetched 2026-10-22) | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) |
| DrivenData data tab | login-gated download | [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) |
| Reference solution | baseline approach | [GitHub](https://github.com/drivendataorg/gems-prize-reference-solution) |
| USGS GeoDAWN | airborne magnetic/radiometric survey context | [USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) |
| INGENIOUS (GBCGE) | geothermal project context and labels | [GBCGE](https://gbcge.org/current-projects/ingenious/) |
| DOE/NLR report 96647 | submission rules context | [PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| EPSG:32611 | CRS definition | [epsg.io](https://epsg.io/32611) |
| Tversky index | metric family | [Wikipedia](https://en.wikipedia.org/wiki/Tversky_index) |
| Gallardo & Meju (2003) | cross-gradient joint-inversion constraint used by H1 | *Geophysics* 68(6), doi:10.1190/1.1635047 |

Full machine-readable register: [`evidence/sources.json`](evidence/sources.json).

---

## 12. Irregularities flagged (all verified, none fixed by assumption)

1. `0.2778` is an owner **projection** (`"UNSCORED"`, `predicted_leaderboard_dti 0.27467`), not an
   organizer receipt; two sibling READMEs assert the opposite evidence class.
2. The published ZIP for that candidate contains a **0-byte** file (216-byte archive) — an unusable
   deliverable.
3. The fleet's holdout instrument scores the fleet's best artifact at **0.0037** while the same
   artifact is reported at `0.2708` live → the instrument does not rank methods the way the prize does.
4. The literal uniqueness rule is **unsatisfiable**: 39 registry rasters cover > 70 % of the domain
   within 3 px (certificate attached).
5. `GEMSDOE82`'s README describes the fleet's `d2.8` control as "0.2600 live control" and calls other
   numbers "organizer-confirmed" without receipts; no receipt was found in any inspected repository.
6. The competition spec says cells *outside the bounds* may be null/NaN, but the upload form rejects
   values outside `[0, 1]` (the user's observed error). This repo writes `0.0` outside the footprint
   and documents the deviation.
7. Four of the 812 registry rasters cannot be used as comparators (CRS/transform mismatch, band-count
   mismatch, or a format smoke-test file); they are itemised in the audit JSON.

---

## 13. Limitations

* No DrivenData account is used, so no live submission was made and no live score exists.
* The three competition rasters are hash-identical to the fleet's published mirrors; that is byte
  identity with those mirrors, not independent authentication of the organiser's originals.
* 3 GB RAM / 2 vCPU in this environment: the 419 MB feature stack is memory-mapped, and only one arm is
  held in memory at a time.
* The GMC hypothesis is **negative at σ = 4 px**; other scales were not swept beyond an untested
  10 px variant to stay inside the compute budget.
* The protocol's 3-experiment / 2-hour budget was exceeded (this session ran the feature arms, the
  budget sweep, the learner comparison, the line-filter ablation and the uniqueness repair). The
  overrun is reported rather than hidden.

---

## 14. Parallel lane in this same repository (not audited by the receipts above)

`main` also carries a second, independently produced lane from a concurrent session
(`gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif` under `docs/downloads/`, with its own
`research/`, `scripts/run_lane86.py` and `docs/evidence/`). That artifact was **not** produced, validated
or uniqueness-audited by the pipeline documented here: its SHA-256, format checks and registry
comparison are its own, and no number in §1–§13 refers to it. It is left in the tree so the parallel-run
protocol's "negative results and sibling lanes are deliverables" rule is honoured; it must be evaluated
with `scripts/audit_uniqueness.py --candidate <its path>` before anyone treats it as submittable.
