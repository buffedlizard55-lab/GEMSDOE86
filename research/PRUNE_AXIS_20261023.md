# PRUNE axis, session 2026-10-23 — mechanism cards for a structural geologist

Axis: **PRUNE** (catalogue collar width). Parent: **R0** = `h33-h33-2-b2` from GEMSDOE32
(37,654 unit-mass dots; owner-reported live **0.2778**, evidence class **CLAIM**: no
submission-page receipt exists in this checkout).

Evidence classes follow the brief: **RECEIPT** (none here) | **CLAIM** (owner-reported) |
**PROXY** (local holdout) | **MODEL** (projection). No number in this file is a score.

---

## 1. What was actually verified before anything was built

| Check | Result |
|---|---|
| `data/bridge/sample_submission.tif` sha256 | `2176d08e…d35cbc` = pin in `registry/data_manifest.json` ✔ |
| `data/bridge/existing_faults.tif` sha256 | `7ba308cc…4093` = pin ✔ (byte-identical to the `labels.tif` pin) |
| R0 raster sha256 | `c55bafc4…b6fa9` = pin in `scripts/fetch_registry.py` `EXTRA[0]` (repo `buffedlizard55-lab/GEMSDOE32`, ref `780a5a53…`) ✔ |
| R0 measured content | 37,654 finite cells, all exactly 1.0, none outside the footprint; **0 dots within 2 px** of the catalogue; minimum catalogue distance **2.236 px** (= √5, one diagonal step) |
| Rebuild of R0 from its own recipe | **Impossible in this checkout.** `research/upstream/run_h33.py` imports `gems32.*` (holdout, h33, bo, paths), which is not vendored here. Parent identity therefore rests on the pinned digest, not on a re-execution. No approximation of the parent was made (brief §5). |

Consequence: the parent's **dot ranking is not stored and cannot be rebuilt**, so the
MASS axis (add/drop by the parent's own ranking) was not attempted — any "refill" here
is a geometric rule, labelled as such.

## 2. Label-free measurements that drive the prediction

**(a) Ring occupancy.** Enrichment = (share of dots) ÷ (share of scored footprint) at a
given distance to the mapped catalogue. R0 deliberately hugs the traces:

| ring (px) | footprint px | dots | enrichment |
|---|---:|---:|---:|
| (0, 2] | 243,560 | 0 | 0.00 |
| **(2, 3]** | 140,246 | **2,171** | **2.12** |
| (3, 4] | 119,588 | 1,654 | 1.90 |
| (4, 5] | 149,596 | 1,812 | 1.66 |
| (5, 6] | 113,774 | 1,164 | 1.40 |
| (6, 10] | 481,406 | 4,559 | 1.30 |
| (10, 20] | 1,009,170 | 7,770 | 1.05 |
| (20, 30] | 765,981 | 5,037 | 0.90 |
| (30, 50] | 1,016,593 | 5,986 | 0.81 |
| > 50 | 1,066,471 | 7,501 | 0.97 |

**(b) Per-dot redundancy.** Median nearest-neighbour distance among R0's dots is 3.00 px.
In the 2–3 px collar, **1,648 of 2,171 dots (76 %) have no other dot within 3 px** — they
are not duplicates; each carries a unique piece of kernel coverage.

**(c) Is the collar evidence-poor?** Rank-normalised |band − median| percentile over the
footprint (0.5 = background), measured on the pinned 19-band stack
(sha256 `4371c82e…3bc5`):

| band | collar dots | rest of R0 | random footprint |
|---|---:|---:|---:|
| `tmi_hg` | 0.528 | 0.542 | 0.495 |
| `tc` | 0.515 | 0.518 | 0.497 |
| `det_elev_slope` | 0.499 | 0.505 | 0.504 |
| `iso_grav_anom_hg` | **0.557** | 0.514 | 0.501 |
| `rtp` | 0.507 | 0.523 | 0.498 |
| `mag_anom` | 0.507 | 0.520 | 0.499 |

The collar is **not** an evidence desert: it is within ±0.02 of the rest of the field on
five of six bands and 0.043 *above* it on the isostatic-gravity horizontal gradient. All
dots sit only marginally above background, consistent with the brief's AUC ≈ 0.57.

**(d) The algebra bar.** With `DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)` and unit mass, removing
one dot with self-credit `k` raises DTI **iff**

```
dT  <  0.2·DTI·(dT + 1 − k)        ⇒   dT < 0.0588·(1 − k)   at DTI = 0.2778.
```

For a collar dot at 2.24 px (`k = 0.25`): removal helps only if that dot's truth credit is
**below 0.044**. A dot whose kernel holds even a fifth of one truth cell at k ≈ 0.4 already
earns ≈ 0.08 and pays for itself.

Why the 2 px prune *did* work: at ≤ 2 px the dot's kernel is dominated by **mapped pixels,
which the organiser masks pixel-exactly** — credit there is structurally zero, while the
mass still counts as false positive. That argument stops at 2 px. Beyond it the kernel
opens onto unmasked terrain where a newly mapped strand adjacent to a known trace can sit.

## 3. Mechanism cards

### Card A — `prune3`: collar > 3 px
* **Hypothesis.** The 2171 dots in the 2–3 px ring are mass without credit: their kernels
  are mostly consumed by masked mapped pixels.
* **Mechanism.** For a dot at distance d ∈ (2, 3], a substantial share of its 3 px kernel
  falls on the mapped corridor; that share earns nothing because those pixels are masked,
  while the whole dot still adds `0.2·(1 − M)` to the denominator.
* **Non-fault process that could mimic it.** Acquisition geometry: at 400 m line spacing the
  mapped trace's *position* is uncertain at the 1–3 px level, so a real new strand parallel
  to a known one is systematically pushed into the same 2–3 px annulus. Pruning then deletes
  the very dots that catch step-overs and splays.
* **Predicted live change (MODEL).** **−0.003** (range −0.010 … +0.004). Small negative:
  76 % of the removed dots are non-redundant and the collar is evidence-rich.
* **Falsifier.** If the live delta is **≤ −0.01**, the collar carries real new-fault coverage
  and no wider collar should ever be built on this lineage. If **≥ +0.01**, masked-pixel
  waste dominates and the collar should be pushed to 4–6 px in one step.

### Card B — `prune4`: collar > 4 px
* **Hypothesis.** Extending A to the 3–4 px ring captures the rest of the masked-pixel waste.
* **Mechanism.** Same, but the 3–4 px dots sit fully in unmasked terrain; there is no masking
  argument left, only the 1.90× geometric clustering near traces.
* **Non-fault process.** Basin-margin topographic grain parallel to range-front faults
  produces exactly a 3–5 px annulus of lineament-like response and no fault.
* **Predicted live change (MODEL).** **−0.008** (range −0.025 … +0.003). It removes 3,825
  dots (10.16 % of the mass) — 1,654 of them from the 3–4 px ring — with no masking argument
  left to justify the loss, and 1.90× geometric clustering as the only thing that says those
  dots were about something real.
* **Falsifier.** A live delta ≥ +0.005 while `prune3` is flat would mean the effect is
  monotone in collar width, not a masked-pixel artefact — then test 6 px.

### Card C — `prune3r`: same count, collar pushed out
* **Hypothesis.** Any `prune3` effect is *mass*, not collar position.
* **Mechanism.** Delete the identical 2,171 dots, then place 2,171 dots on free cells with
  3 < d ≤ 5 px, nearest to the dot they replace (mean move **1.14 px**, max 9.06 px, no
  shortfall). Count, footprint and catalogue exclusions are identical to R0.
* **Non-fault process.** Relocation can drift dots onto unrelated lineaments (drainage,
  roads, playa margins) that happen to sit just outside the collar.
* **Predicted live change (MODEL).** **−0.003** (range −0.012 … +0.006).
* **Falsifier.** If `prune3r − prune3 ≥ +0.010` at equal count, the collar width itself is
  the lever and mass is irrelevant; if `prune3r ≈ prune3`, mass dominates and future work
  should hold count fixed in every axis.

## 4. Negative result: the catalogue hide-and-recover proxy cannot rank this axis

Design used: withhold 20 % of 8-connected catalogue components per draw (6 draws, seed
20261023, 11,771 withheld positive px per draw), treat the visible catalogue as
pixel-exactly known, score the exact α = 0.2 / β = 0.8 / R = 3 px DTI
(`gems57.metric.dti_exact`).

| candidate | PROXY DTI | Δ vs R0 [95 % CI] |
|---|---:|---|
| R0 | 0.00436 | — |
| prune3 | 0.00000 | −0.00436 [−0.00502, −0.00370] |
| prune4 | 0.00000 | −0.00436 [−0.00502, −0.00370] |
| prune3r | 0.00000 | −0.00436 [−0.00502, −0.00370] |

This is not a ranking, it is a **floor effect**: a field pruned to stay > 2 px from the
catalogue earns almost no kernel credit from withheld catalogue pixels, and pruning the
collar removes the last of it. The instrument rewards catalogue-following while the scored
metric punishes it once the catalogue is masked — the likely reason this proxy has shown
sign-unstable correlation with live scores (−0.87 … +0.54, n = 12–14; brief §3). Reported,
never used as a gate or as a prediction.

## 5. Files

| id | dots | Δ vs R0 | min catalogue distance | sha256 (nan) | sha256 (zeros) |
|---|---:|---:|---:|---|---|
| `h33-2-b2-prune3-20261023-3eb29af5-nan` | 35,483 | 5.766 % | 3.16 px | `3eb29af5…f0501` | `4bd30478…e4838b` |
| `h33-2-b2-prune4-20261023-e198b768-nan` | 33,829 | 10.158 % | 4.12 px | `e198b768…715cd` | `de4c2a98…4ebc5` |
| `h33-2-b2-prune3r-20261023-9542efac-nan` | 37,654 | 11.531 % | 3.16 px | `9542efac…06682` | `8c20bd7e…52c2e` |

All six rasters pass every MUST gate in brief §6 (single band, float32, EPSG:32611, 3730×3292,
template transform, values in [0,1], no NaN inside the footprint, NaN outside for `-nan` /
zeros outside for `-zeros`, zero catalogue mass, unit mass where emitted), were re-read from
disk after writing, and duplicate no existing digest on disk. Full receipts:
`evidence/prune_axis_20261023.json`.

Cross-check with the repo's own tooling: the three `-zeros` twins pass **both**
`vendor/gems57/validate.py` (`all_checks_passed = True`) and
`gems57.gates.format_report` against `sample_submission.tif` (`ok = True`). The three `-nan`
twins fail the vendored validator by its own all-finite policy (7,111,787 NaN cells, all
outside the footprint, exactly as brief §6 asks) — a policy difference, not a defect
(IR-86-PRUNE-07).

## 6. What this session does *not* claim

* No live score, no leaderboard comparison, no "beats R0". The predictions above are MODEL.
* The parent's ranking was not rebuilt, so nothing here re-derives R0's own choice of dots.
* The label sources, fault types and public/private chunk split remain undisclosed
  (<https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527>).
