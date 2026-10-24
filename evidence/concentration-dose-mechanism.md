# CONCENTRATION — CV-band dose ladder (mechanism cards, PRE-REGISTERED 2026-10-23)

Session branch `arena/60ecf1c8-gemsdoe86`. Axis **`CONCENTRATION`**, self-assigned under brief v2 §1
("pick your own session"; no prompt to the human).

Parent **R0 = `h33-h33-2-b2`** (`GEMSDOE32`), 37,654 unit-mass dots, sha256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. Live **0.2778 is a CLAIM**
(0 `RECEIPT` rows in `ledger/submissions.csv`). TOP_PUBLIC unsupplied.

## Why this axis and these values

`b5km-cvband-down4` (PR #47, `concb5kmdown4-…-8aab97b6`) is the only arm across 47 ledger rows that
is positive on **both** report-only instruments (SGMC `MODEL` `+0.0015`, 4/4 quadrants; symmetric
fold-fair `PROXY` `+0.0008`) at fixed count. A single dose cannot distinguish a mechanism from a
lucky magnitude, so this session spends its three builds on the **dose–response and the block
scale** of that one rule, plus a matched ordering control:

| build | value | rule | dots moved | % of R0 changed |
|---|---|---|---:|---:|
| V1 | `cvband-down6` | shave `>=3`-dot **1 km** blocks → `1–2`-dot ancestor-ridge blocks | 2,259 (6 % of R0) | 12.00 % |
| V2 | `cvband-down8` | same rule, double the dose | 3,012 (8 % of R0) | 16.00 % |
| V3 | `cvband-2km-down4` | same rule, dose of `down4`, **2 km** blocks | 1,506 (4 % of R0) | 8.00 % |
| C | `CONTROL-cvband-down8-randcredit` | V2's block selection, **random dot within block** and **random destination order** | 3,012 | 16.00 % |

Every arm: count fixed at 37,654, zero catalogue mass, newly emitted mass `> 3.0 px` from the
catalogue, `>= sqrt(8) px` inter-dot spacing (R0's own floor, not tightened), 100 % of new dots on
the pinned ancestor ridge union `H19-5 | H19-4 | H16-1`.

## Pre-registered predictions (MODEL, written before the builds ran)

Anchor: `down4` measured `+0.0015 MODEL` / `+0.0008 PROXY` at 1 km CV `0.6235 → 0.5162`.

* **V1 `cvband-down6` — `+0.0015 ± 0.004` MODEL.** Predicted 1 km CV lands at or just below the
  bottom of the historical `0.51–0.59` band; the extra 753 moves therefore buy little new unique
  kernel credit and the arm should not beat `down4` by more than noise.
* **V2 `cvband-down8` — `+0.0008 ± 0.005` MODEL.** Over-dispersal: CV well under 0.51, destinations
  start to be second-choice ridge cells. Predicted *below* V1 despite the larger dose.
* **V3 `cvband-2km-down4` — `+0.0004 ± 0.004` MODEL.** A 2 km block holds ~7 kernel diameters, so
  "over-concentration" at that scale is not the same construct the 1 km rule targets; predicted
  positive but weaker than the 1 km arm at the same dose.
* **C control — `0.0000 ± 0.004` MODEL.** With the credit ranking and the gap ranking replaced by
  random choice, the arm should lose the `down4` gain; if the control matches the ranked arms the
  effect is "any dispersal", not "credit-ranked dispersal into sparse blocks".

Shape prediction: **inverted-U in dose**, peaking near 1 km CV ≈ 0.52 and falling on both sides.
A monotone rise through V2 would falsify the CV-band reading of the mechanism and replace it with a
plain "disperse low-credit dots" reading.

## Falsifier for the whole session

Live `RECEIPT` Δ vs 0.2778 (public chunks only; private chunks may differ):

* V1 and V2 both `<= -0.005`: the 1 km CV-band mechanism is dead; close `CONCENTRATION`.
* V1 `>= V2` by `>= 0.005`: confirms the inverted-U, i.e. 1 km CV ≈ 0.52 is a real optimum →
  next dose should sit between 4 % and 6 %.
* Control `>= max(V1, V2)`: the ranking is irrelevant, only the count of displaced dots matters →
  retire all prior "credit-ranked" CONCENTRATION claims.
* Any single live Δ `>= +0.010`: first evidence above the brief's floor on this axis → that file
  becomes the new incumbent candidate and the next slot goes to the winning dose.

## Mechanism (for a structural geologist)

R0's dots are the surviving output of a 121k-pixel continuous field thinned to unit-mass points.
Inside densely dissected range-front blocks a `10 x 10 px` 1 km cell can hold 4–8 dots whose
`R = 3 px` triangular kernels overlap almost completely: the 4th–8th dots re-credit fault pixels
already covered, so they add little numerator `T`, while each off-truth dot still pays the full
`0.2(S-M)` mass term and inflates the `0.8|G|` dilation term. Shaving the lowest unique-kernel-credit
dot of each over-dense block and re-emitting it on an *unused* ridge cell in a sparse block
converts redundant overlap into fresh along-strike coverage at constant `S`, which is exactly what
the metric's denominator rewards.

**Non-fault process that could mimic it.** Great Basin sparse blocks contain tilted Miocene basalt
flow margins, Lahontan pluvial shoreline scarps, and alluvial-fan distributary ridges that
topographic/tilt-derivative ridge fields (`H19-4`, `H16-1`) also light up. Dispersal into those
blocks could buy geomorphic mimics rather than faults; the `CONTROL` and the 2 km arm bound how
much of any live gain is generic dispersal rather than ridge-selective placement.

**Supporting algebra.** `DTI = T / (0.2T + 0.2(S-M) + 0.8|G|)`; at fixed `S = 37,654` the numerator
only grows via `T`, and a dot whose credit is already covered contributes ~0 to `T` while still
adding dilation — so the marginal value of the nth dot in a dense block is negative long before the
block runs out of dots. This is the same algebra brief v2 §2 states ("rank dots by exact marginal
gain from the metric code").

## Evidence classes

Predictions above are `MODEL`. The `PROXY` (catalogue hide-and-recover, fold-fair) and the SGMC
control are **report-only**, never gates, and never called a score. No submission is made here.

---

# RESULTS (measured after the pre-registration above)

Built by `scripts/run_concentration_dose.py` (git SHA logged in the receipt). Every arm: 37,654
dots, zero catalogue mass, new mass `min 3.162 px` from the catalogue, `min 2.828 px` inter-dot
spacing (= R0's own floor), 100 % of new dots on the ancestor ridge union. Twins on disk, re-read,
shared validator + format report pass. Leakage canary max single-feature AUC **0.5467**.

| build | dots moved (% chg) | 1 km CV | SGMC `MODEL` Δ (quadrants) | ±6 px jitter | fold-fair `PROXY` Δ (95 % CI, n = 11,321) |
|---|---:|---:|---:|---:|---:|
| `cvband-down3` (`conc3-…-ffb47d4b`) | 1,130 (6.00 %) | 0.5377 | **+0.0013** (4/4 +) | +0.0017 | +0.0004 [−0.0006, +0.0013] |
| `cvband-down5` (`conc5dose-…-a2f8aaad`) | 1,883 (10.00 %) | 0.4998 | **+0.0018** (4/4 +) | +0.0024 | +0.0010 [−0.0003, +0.0023] |
| `cvband-down6` (`conc6-…-1ed78e0f`) | 2,259 (12.00 %) | 0.4840 | **+0.0022** (4/4 +) | +0.0028 | **+0.0013** [−0.0004, +0.0028] |
| `CONTROL-cvband-down6-randcredit` (`conc6rand-…-a6838dc2`) | 2,259 (12.00 %) | 0.4855 | +0.0015 (4/4 +) | +0.0021 | +0.0008 [−0.0014, +0.0026] |
| *anchor* PR #47 `b5km-cvband-down4` | 1,506 (8.00 %) | 0.5162 | +0.0015 (4/4 +) | +0.0020 | +0.0008 [−0.0004, +0.0018] |

## What the measurements say (and where the pre-registration was wrong)

1. **The inverted-U was falsified; the dose–response is monotone.** I predicted the peak at
   1 km CV ≈ 0.52 and a fall at higher dose. Measured: Δ rises 3 % → 5 % → 6 % on both instruments
   (`+0.0013 → +0.0018 → +0.0022` MODEL; `+0.0004 → +0.0010 → +0.0013` PROXY) while CV falls
   `0.5377 → 0.4998 → 0.4840`, i.e. the highest dose lands **outside** the historical `0.51–0.59`
   band and still wins. **The `0.51–0.59` CV band is therefore not the causal variable** — it was a
   descriptive correlate of archived submissions (`IR-86-CONC-13`). The disciplined reading is
   "disperse low-unique-credit dots", not "hit CV 0.55".
2. **Most of the effect is generic dispersal, not the credit ranking.** The matched ordering
   control — same source blocks, random dot within block, random destination order — captures
   `+0.0015` of the ranked arm's `+0.0022` MODEL (≈ 67 %) and `+0.0008` of `+0.0013` PROXY (≈ 62 %).
   So the ranked arm's edge over "any dispersal" is only **+0.0007 MODEL / +0.0005 PROXY**, well
   inside the instrument's own uncertainty. Any live win from this axis cannot be credited to the
   marginal-credit ranking without a paired live A/B (two slots), which the brief's 3-slot budget
   makes expensive.
3. **The ladder is capacity-limited, not dose-limited.** The pre-registered 8 % arm is impossible:
   the 1 km sparse-ridge destination pool exhausts after **2,399** placements (< 3,012), and the
   2 km pool after **920** (< 1,506). Both are recorded as `IR-86-CONC-12`; the 2 km arm was
   replaced by `down3` to bracket the band from below. The ceiling (~6.4 % of R0) is a property of
   this parent's ridge support and `>= sqrt(8)` spacing, so "more dose" is not an open direction —
   the next step at higher dose would require loosening spacing or leaving the ridge union, i.e.
   changing a second thing at once.
4. **All four arms are `|Δ| < 0.005`.** By brief v2 §5 that is **no evidence**; the live slot is the
   measurement. `conc6` is the best CONCENTRATION file built to date on both report-only
   instruments and dominates PR #47's `down4` on both, at a cost of 753 more moved dots.

## Ranking for a slot

`conc6` > `conc5dose` > `conc3` > `conc6rand` (control, never upload). But the honest expected live
gain is ≈ `+0.0007` above generic dispersal, so this file belongs in a slot only **after** the
larger predicted levers (`PRUNE le3p000` +0.0040 MODEL, `RELIEF frontp15` +0.0017 MODEL), and it
should not be combined with them until one of them returns |Δ| ≥ 0.01 live.
