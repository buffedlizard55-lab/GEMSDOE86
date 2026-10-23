# CONCENTRATION — the sign experiment (2026-10-23, branch `arena/c1df93fc-gemsdoe86`)

**AXIS: CONCENTRATION.** Parent **R0 = `h33-h33-2-b2`** (GEMSDOE32), sha256
`c55bafc4…b6fa9`, 37,654 unit-mass dots, 0 within 2 px of the catalogue, live **0.2778 CLAIM**
(no receipt in `ledger/`). R0 was rebuilt byte-exactly this session from the pinned base
`ab023001…` (40,199 dots) **AND** distance-to-catalogue > 2.0 px; 0 differing cells, re-encoded
`deflate/predictor=3/zlevel=9/tiled 256` to 219,065 B = `c55bafc4…`.

**No slot is requested by this document.** Nothing below is a score; every number is MODEL.

## Why this value

`CONCENTRATION` was the only brief-§5 axis whose built arm (`conc15`, PR #37) is a
*spatial-prior* claim rather than a geometry claim, and that arm's own falsifier asks for
exactly this build: "≤ −0.010 → the region wants *less* clustering: build the spread variant
instead". `conc15` moved 15 % of the dots **into** the highest-prior 1 km blocks and predicted
**+0.006 MODEL**. This session builds the mirror (**`spr15`**), the same-direction arm under a
*band-free* prior (**`dens15`**, the paired calibration — PR #37's prior needed an
upward-continued-TMI gradient from the 419 MB feature stack, absent here), and the null
(**`rand15`**) that makes the pair interpretable.

## The three files

| arm | role | dots | % changed | block-density CV | occupied 1 km blocks | mean move to nearest dropped dot |
|---|---|---:|---:|---|---:|---:|
| `…-concspr15-20261023-6d452f96` | candidate | 37,654 | **29.999** | 0.6235 → **0.6136** | 15,976 → 13,297 | 7.2 km |
| `…-concdens15-20261023-f8e7ae42` | candidate | 37,654 | **29.999** | 0.6235 → 0.6174 | 15,976 → 13,623 | 90.1 km |
| `…-concrand15-20261023-fcbae067` | **CONTROL** | 37,654 | 29.622 | 0.6235 → 0.6600 | 15,976 → 13,774 | 2.4 km |

"% changed" is cells changed = dots removed **+** dots added, so a 15 % dose reports ≈ 30 %
(the brief's own `conc15` reports 29.999 % for the same reason). **5,648 dots (15.00 %) are
relocated in every arm; all 5,648 were re-placed at the parent's 2.828 px spacing floor
(0 at the relaxed 2.0 px pass); count is fixed at 37,654 and no arm has a shortfall.** Minimum
catalogue clearance stays 2.236 px (inherited dots), 0 dots on catalogue pixels, new mass
≥ 3 px off the catalogue.

## Mechanism card — `spr15` (spread)

* **Hypothesis.** R0's mass is over-weighted toward blocks with a dense mapped-fault record, and
  part of that record is *mapping effort*, not fault density. Because the organiser masks known
  fault pixels and scores only **new** faults, the unmapped ground of low-catalogue-prior blocks
  carries a larger share of the scored truth than its mapped-fault density suggests.
* **Mechanism.** 5,648 dots leave the highest-prior occupied 1 km blocks and are re-placed, by
  largest kernel gap only, in the lowest-prior occupied blocks. The relocated dots keep the
  lineage's support surface; nothing is dropped and no response band enters the placement.
* **Non-fault process that could mimic it.** Ridge/valley contrast in the geophysical field is
  confounded with basin fill and Quaternary cover: low-catalogue-prior ground in this region is
  largely basin and alluvium, where lineaments are both *less mapped* and *less real*. That
  confound points the same way as the hypothesis, which is why this arm cannot be read as
  evidence about faults alone.
* **Predicted sign and size.** **−0.030 MODEL** (mean over five truth models, range
  −0.064…+0.011). Negative because two *non-circular* priors agree with the catalogue: R0's own
  geophysical field puts 1.66× background mass in the 300–1200 m annulus around mapped traces
  (measured this session: 1.209 % dot density at 3–6 px vs 0.729 % footprint mean), and the
  damage-zone/branch-splay scale is exactly that annulus. Those models are **not calibrated**:
  the parent scores DTI 0.050–0.107 on them versus 0.2778 live, so the magnitudes are upper
  bounds under stated assumptions, not forecasts.
* **Falsifier.** Live Δ ≥ +0.010 → the catalogue is not a fault-density proxy for this target
  and every catalogue-derived local instrument in this repo (hide-and-recover, SGMC off-catalogue
  DTI, H19-5 support) is biased toward "near mapped faults"; the final file should then be
  built to *maximise distance from mapped ground* subject to staying on the lineage's support.

## Mechanism card — `dens15` (dense; paired calibration)

* **Hypothesis.** New faults are mostly *newly mapped geometry of existing systems* (organiser
  thread 11536), so fault-interaction zones — step-overs, splays, terminations — concentrate near
  already-mapped traces, and mass should be denser there.
* **Mechanism.** Mirror of `spr15`: 5,648 dots from the lowest-prior occupied blocks are
  re-placed in the highest-prior occupied blocks under the same geometric rule and exclusions.
* **Non-fault process that could mimic it.** Mapped-fault density is *mapping effort*: USGS and
  INGENIOUS coverage is uneven, so "high prior" partly means "was surveyed". The
  hide-and-recover proxy and the SGMC surrogate are both built from that same record and
  therefore cannot distinguish effort from geology — this arm exists to price that substitution,
  and it is a new `(CONCENTRATION, value)` because its prior is band-free.
* **Predicted sign and size.** **+0.026 MODEL** (mean over five models, range −0.011…+0.047),
  against `conc15`'s **+0.006** on the SGMC surrogate. Same direction, ~4× the magnitude, and the
  two magnitudes disagree because the truth models here over-cover the truth.
* **Falsifier.** Live Δ ≤ −0.005 → the local instruments' preference for catalogue-adjacent mass
  is circular, `conc15`'s +0.006 was an artefact of its surrogate, and the concentration axis is
  closed in the negative direction for Phase 1.

## Mechanism card — `rand15` (control, never a slot)

Same source dots as `spr15`, destination blocks drawn uniformly from the same occupied set
(seed 20261023). Its job is to say how much of `spr15`'s movement is caused by the *destination
prior* rather than by *moving mass at all*: under the three catalogue-adjacent truth models it
recovers about half of `spr15`'s loss (−0.033 vs −0.064 on `annulus_2_4px`), so roughly half of
the spread penalty is the prior and half is displacement itself.

## What the block-density CV says (the brief's 0.51–0.59 claim)

Measured CV-vs-dose on the same rule (`evidence/concentration_sign_20261023.json`,
`cv_vs_dose`):

| dose | spread CV | dense CV |
|---|---|---|
| 0.05 | **0.5970** | **0.5978** |
| 0.15 | 0.6136 | 0.6174 |
| 0.30 | 0.6722 | 0.6875 |
| 0.50 | 0.7057 | 0.7573 |

Parent 0.6235. The curve is **non-monotone**: only the 5 % dose lands at the top of the
reported 0.51–0.59 band, and every larger dose — in *either* prior direction — moves CV away from
it. The reason is structural: both arms confine destinations to a fixed **fifth** of the occupied
blocks (3,195 of 15,976), so mass is *concentrated into fewer blocks* (occupied blocks fall
15,976 → 13,297–13,774) in every arm including the "spread" one. **The axis's CV framing and its
prior framing therefore pull in opposite directions at 10–20 % dose**, and any future arm that
wants to test the band must place mass in currently *unoccupied* low-prior blocks — at the risk
measured by `GEMSDOE81` `cont-poisson44090` (**0.0041 CLAIM** for a near-uniform far-field dot
set, against R0's 0.2778).

## Instrument status (why there is no PROXY here)

* The catalogue hide-and-recover PROXY is at its floor for every R0-derived arm: with one fixed
  ≥ 3 px collar applied to all arms it reads 0.0000 for parent, variants and the SGMC control
  (IR-86-SNAP-06). It is not run as a gate and does not rank these files.
* The SGMC off-catalogue control raster (`ext_derived_sgmc_faults_100m_u8`) is **absent from
  this checkout**; the 419 MB feature stack is absent too, so `variants.block_prior()` cannot be
  called and the prior is catalogue-only (IR-86-CONC-06).
* What replaces them is a **five-truth-model panel** (exact DTI, collar-masked): `annulus_2_4px`,
  `annulus_3_8px`, `uniform_far_0p8pct`, `uniform_all_0p8pct`, `catalogue_shift_6px` (600 m
  translation, the brief's flight-line uncertainty). The panel's job is to expose that the sign
  of this axis is decided by truth geometry, not by the file.

## Gates (all MUST-pass, re-read from disk after writing)

`format` (template validator, sample_submission as reference) · `values` (float32, one band,
EPSG:32611, [0,1], no NaN inside footprint, NaN/0 outside) · `catalogue_clearance` at the
parent's own 2.0 px rule · `new_mass_clearance` ≥ 3 px for the 5,648 emitted dots · `sha256 not
in ledger` · re-read from disk equals the built mask. **All three files pass.**

**Re-reading the gates after the ledger rows exist.** `gates.run_all` includes a *newness*
check (`sha256 not already in the ledger`). Once `scripts/build_ledger.py` has written these
`-zeros` digests into `ledger/submissions.csv`, that one check necessarily reads False on the
`-zeros` twins — as it does for every previously released candidate. Re-measured just now:
`format`, `values` and `catalogue_clearance` are **True** on all three `-zeros` files and on all
three NaN twins. A False here is bookkeeping, not a format failure; at build time (before the
rows existed) all four checks were True.
