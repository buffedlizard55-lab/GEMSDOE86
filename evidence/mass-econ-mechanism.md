# MASS, kernel-budget session (2026-10-23) — mechanism cards and the instrument audit

Parent **R0** = `h33-h33-2-b2` (GEMSDOE32), sha256 `c55bafc4…b6fa9`, 37,654 unit-mass dots,
0 within 2.236 px of the catalogue. Reproduced byte-exactly this session (dot mask re-encoded with
`deflate/predictor=3/zlevel=9/tiled 256` → 219,065 B → `c55bafc4…`); live **0.2778 stays CLAIM**.
Run card: `evidence/mass_econ_axis_20261023.json`. Instrument audit:
`evidence/mass_instrument_monotonicity.json`.

## Why a second MASS session, and what it is *not*

The brief's literal MASS arms were already built and both lost (`massminus10` −0.003,
`massplus10` −0.006, MODEL). The post-mortem (IR-86-MASS-01) is that "the parent's own ranking" is
the FIFO-BFS *traversal* of the thinning recipe — geography, not mass. Brief §2 asks for the other
thing: *rank dots by exact marginal gain from the metric code*. That is what this session ranked.
The axis and the dose stay inside §5 (MASS, ±10 %); only the ranking function changes, and that
deviation is recorded as IR-86-MASS-02.

Two facts measured before any arm was built, both label-free:

1. **The metric's own bar.** With `DTI = T/(T + 0.2·FP + 0.8·(|G|−T))`,
   adding a non-redundant dot pays iff `k > 0.2·DTI`, i.e. iff it lies within `R·(1 − 0.2·DTI)`
   = **2.833 px** of a truth pixel at the incumbent's 0.2778 — which is exactly why the parent's
   2.8 px thinning sits where it does. Removing a dot pays iff its unique truth credit
   `u < 0.0588·f` (`f = 1 − k`, its own false-positive charge), i.e. only for dots with almost no
   unique credit.
2. **R0's unique credit** `u_x` (the exact numerator a removal would delete, averaged over the
   29-cell kernel disc): mean **6.79** of a possible 9.38; write-off from overlap **27.6 %**;
   minimum **1.49**. Not one dot is anywhere near the removal bar.

## Arm cards

### 1. `MASS minus10pct-marginal` — 33,889 dots, 3,765 deleted, 9.9989 % changed, `c3936cfc`

* **Hypothesis.** R0 carries 10 % of dots that are pure false-positive mass: their kernel credit is
  mostly written off by a neighbour, so deleting them costs little numerator and saves 0.2 mass
  each.
* **Mechanism.** Delete the 3,765 dots with the smallest exact unique credit `u_x`, tie-broken by
  nearest-neighbour distance then row-major. Dropped 10 % mean `u` = 4.24; kept minimum 4.78 — the
  ranking is a clean cut (tie class at the cut: 264 dots, so the tie-break does not decide the set).
* **Mimic.** Parallel strands and en-echelon step-overs are exactly 300 m apart by design; if the
  catalogue's own second strands sit at 2.8–3.0 px, the dots the ranking calls "redundant" are the
  second fault. That is the falsifier, not a nuisance.
* **Predicted live change.** **0.000 (MODEL, band −0.008…+0.006)**. The algebra forbids a gain —
  every deletion removes 1.49–9.38 units of unique numerator to save at most 0.2 units of charge —
  so this arm is built as a *ranking test*, not a score play: at identical count it must beat the
  traversal arm (−0.003) for the ranking to mean anything.
* **Falsifier.** A live delta ≥ +0.010 with count down 10 %, which would say the field is
  precision-limited at the dot scale rather than coverage-limited.

### 2. `MASS plus10pct-extend` — 41,419 dots, 3,765 added, 9.9989 % changed, `3b708da1`

* **Hypothesis.** The traversal add lost (−0.006) because 98.6 % of its dots fell inside a
  neighbour's disc: they paid the full false-positive charge and earned almost no credit. New mass
  placed at least one *kernel radius* from every existing dot cannot be redundant.
* **Mechanism.** Candidate cells 3–6 px from the nearest dot, within 1.5 px of that dot's local
  strike (PCA of its 10 nearest dots, coherence ≥ 0.30), ranked by coherence × across-strike fit ×
  distance-to-one-radius, with a 3.0 px floor among the new dots and a 3.0 px catalogue clearance.
  83 % of the 4.18 M eligible cells were rejected by the strike test; placements needed no
  shortfall (3,765/3,765).
* **Mimic.** "Extending the trace" is also what a *mapping halo* looks like: every mapped fault has
  a cloud of nearby non-fault lineaments, and putting dots 300–600 m off the trace buys the halo,
  not the fault.
* **Predicted live change.** **0.000 (MODEL, band −0.010…+0.010)** after the audit below. It is the
  only arm here that can add numerator, and its MODEL read (+0.0066) is *exactly* the instrument's
  price of generic mass.
* **Falsifier.** Live delta ≤ −0.005 while the random-placement twin is flat: the shell around the
  traces is halo, not fault.

### 3. `MASS plus10pct-extend-rand` — 41,419 dots, `37fab392` — **CONTROL, never a slot**

Same window (3–6 px), same spacing floor, uniform draw. MODEL **+0.0071**, i.e. **+0.0006 better
than the trace law**. Read this as the session's sharpest single result: at this dose, *where* the
new mass goes is worth nothing measurable; *that* it is non-redundant is the whole effect — and
that effect is an instrument artefact (below).

## Instrument audit — the SGMC surrogate is monotone in dot count

`scripts/audit_mass_instrument.py` adds and deletes random dots over a symmetric ladder against the
same surrogate the repo uses for MODEL numbers (exact DTI vs off-catalogue USGS SGMC):

| dose | −20 % | −10 % | −5 % | +5 % | +10 % | +20 % |
|---|---|---|---|---|---|---|
| ΔDTI (MODEL) | −0.0127 | −0.0068 | −0.0030 | +0.0018 | +0.0040 | +0.0081 |

Strictly monotone in dot count. Therefore **any mass-changing arm's MODEL delta from this
instrument measures mass, not the axis** — this session's three arms, `massminus10`, `massplus10`,
and any future one. The count-fixed axes (CONCENTRATION, RELIEF, SPACING, PRUNE-with-refill) are not
exposed to it, which is why the repo's habit of reading *them* on this instrument is still defensible.

The reason the surrogate mis-prices mass: it credits only **8.4 %** of its own truth inventory
(`T/|G| = 6,688/79,615`), while the incumbent's claimed 0.2778 implies `T/|G|` between **0.23 and
0.48** for plausible new-fault truth sizes (5k–40k px) using the same identity. A map that covers a
tenth of the truth has a huge marginal appetite for more dots; the live one does not.

## What this session says about the axis

* MASS, **drop** direction: closed. The metric's removal bar is 0.0588 × the dot's own
  false-positive charge; R0's smallest unique credit is 1.49. No ranking can make deletion pay;
  the only question was whether a better ranking loses less, and the surrogate cannot answer it.
* MASS, **add** direction: cannot be run as the brief specifies. The parent's own field has
  121,131 support cells and only **733** of them are ≥ 3 px from every dot (99.4 % saturated), so a
  field-ranked 10 % add is either redundant (measured: −0.006) or outside the field. The add arms
  therefore use the parent's *geometry*; their MODEL read is indistinguishable from generic mass.
* **Consequence for the slot plan.** No MASS artefact should take a slot. The arms that remain worth
  a slot are the count-fixed pairs whose *difference* cancels the instrument's mass bias — in
  practice the RELIEF +15 %/−10 % pair, whose predicted separation (~0.011) is the only one built in
  this repo that can clear the 0.01 evidence floor. See SLOT_PLAN.md.
