# CONCENTRATION knob session — mechanism cards (2026-10-23)

Parent **R0** = `h33-h33-2-b2` (GEMSDOE32), 37,654 unit-mass dots,
sha256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`.
R0's live 0.2778 is a **CLAIM** (owner report, no submission-page receipt). Everything below is
**MODEL** or **PROXY**; nothing is a score. Parent rebuilt byte-exactly at the start of this
session (`scripts/verify_r0_rebuild.py`, `evidence/r0_rebuild_20261023.json`: 40,199 → 37,654
dots, 0 differing cells, re-encoded with `deflate/predictor=3/zlevel=9/tiled 256` = 219,065 B =
`c55bafc4…`).

## Why this axis, stated so it can be attacked

The metric is `DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)`. Calibrating on the only live difference in
the ledger (solo-d28 40,199 dots = 0.2708 CLAIM → R0 37,654 = 0.2778 CLAIM, the removed 2,545 dots
being the ≥2 px catalogue collar) gives **D ≈ 20,200, T ≈ 5,610** for the scored chunks. Two
consequences:

* Deleting a dot that earns no credit is worth `+0.2T/D² = +2.75e-6`; deleting one that covers
  truth is worth about `−1.0e-5`. An unguided MASS cut is therefore a coin flip weighted against
  you (which is what `massminus10` / `massplus10` measured).
* **Relocating** a dot costs no mass. It pays exactly when the destination cell's credit exceeds
  the source cell's, i.e. when the destination prior knows more than the incumbent field's own
  placement does. That is the whole CONCENTRATION hypothesis, and it is falsifiable offline.

One setting was already spent on this axis (`b1km-move15`, PR #37: block 10 px, 15 % of dots
moved, destinations = top fifth of blocks). Each variant here moves **exactly one knob** off that
setting, so a live difference between two arms is attributable to that knob.

Prior (identical in all mixed arms): `z(catalogue fault-interaction density)` + `z(mean |∇TMI|)`,
both aggregated per block, z-scored over footprint blocks. Sources: lowest-prior blocks first.
Placement: geometric only (highest-prior destination block, then the largest remaining kernel
gap), so this axis cannot smuggle in the pixel-scale edge snapping that SNAP measured as negative.

---

## 1. `b5km-move15` — block scale 1 km → 5 km

* **Hypothesis.** The catalogue-density prior is only as good as the scale at which mapping
  effort varies, and that scale is quadrangle/1:24k compilation, i.e. kilometres to tens of km,
  not 1 km.
* **Mechanism.** At 1 km a block holds ~100 cells, so the density estimate is dominated by the
  digitising noise of individual traces; at 5 km it averages 25× more catalogue length and
  approaches the region where new faults are actually being found. Coarser destinations damp
  the prior's *breadth* (438 destination blocks instead of 10,462) and should raise the prior's
  *quality* per block.
* **Non-fault process that could mimic it.** Compilation effort is a property of *maps*, not of
  rock: a 5 km block with dense catalogue traces is one a geologist walked. Where the modern
  catalogue is complete, dense blocks hold no new faults, and the prior then concentrates mass on
  already-mapped ground — the exact failure mode R0's collar prune was built to avoid.
* **Predicted sign and size.** **+0.001 (MODEL, band −0.008…+0.008)** — preregistered +0.004,
  revised down after the instruments (below). 5,648 dots (15.00 %) moved, 29.999 % of cells
  changed, count fixed at 37,654, every placement at the parent's 2.828 px spacing.
  Block-density CV 0.7442 → 1.0313 at 5 km; at 1 km 0.6235 → 0.7555.
* **Falsifier.** Live Δ ≥ +0.010 at 5 km while the 1 km arms are flat would say the prior is real
  but mis-scaled — the strongest possible positive result for this axis. Live Δ ≤ −0.010 says
  concentration is anti-informative and the axis is finished for Phase 1.

## 2. `b1km-move24` — dose 15 % → 24 %

* **Hypothesis.** If the prior carries information, the gain grows with dose until the source pool
  stops being credit-free or destinations saturate. The slope is what decides whether a third,
  larger dose is worth a slot.
* **Mechanism.** Same rule, 1.6× the moved mass: the *sources* are now dots in even lower-prior
  blocks (cheaper to lose); the destinations are unchanged in definition, so each added moved dot
  carries the same expected prior advantage.
* **Non-fault process that could mimic it.** Every arm on this axis looks better at larger dose in
  a catalogue-truth instrument, by construction. The genuinely dose-sensitive confound is
  *coverage*: 9,037 dots leave blocks that then hold nothing, and a fault that was covered by one
  of them is now uncovered at weight β = 0.8.
* **Predicted sign and size.** **−0.001 (MODEL, band −0.012…+0.008)** — preregistered +0.008.
  9,037 dots (24.00 %) moved, **48.0 % of cells changed** (inside the brief's 1–50 % band by 2
  points), count fixed, all at 2.828 px spacing, no shortfall. Block-density CV 0.6235 → 0.8077.
* **Falsifier.** A live *gain* that is roughly 1.6× the 15 % arm's gain would confirm a real prior;
  a live loss that scales with dose would confirm the cost-of-moving term; both arms inside ±0.010
  retires the axis rather than the dose.

## 3. `b1km-move15-t05` — destination selectivity, top fifth → top 5 %

* **Hypothesis.** The prior's *ranking* is more reliable at the top than its breadth: the top 5 %
  of blocks (2,615 instead of 10,462) should hold the highest-prior ground, and the same 5,648
  moved dots should therefore buy more expected truth credit each.
* **Mechanism.** Same dose and block size, five times fewer destination blocks. Consequences to
  state before the result: mean dots per destination block rises ~4×, so the geometric placement
  rule works harder, and any error in the top of the ranking is now paid five times over.
* **Non-fault process that could mimic it.** The top 5 % of the catalogue-density term is
  dominated by a handful of densely mapped corridors (the step-over/intersection zones of the
  Faulds inventory). New faults there may be genuinely absent precisely because the corridor is
  already mapped at high density.
* **Predicted sign and size.** **+0.002 (MODEL, band −0.007…+0.009)** — preregistered +0.007.
  5,648 dots (15.00 %) moved, 29.999 % changed, count fixed, all at 2.828 px spacing.
  Block-density CV 0.6235 → 0.7425.
* **Falsifier.** This arm beating the 15 %/top-fifth arm on the *live* score, with the TMI-only
  readout flat, would say the catalogue-density term carries real (non-circular) information
  about new faults — the one finding that would reopen the axis. Both flat: the prior's sharpness
  is not the problem, its information content is.

---

## Report-only instruments (never gates) and what they changed

Full numbers: `evidence/concentration_instruments_20261023.json`. Design: four spatial folds,
whole catalogue components withheld, every collar **and the whole block prior** rebuilt from that
fold's visible catalogue only, TMI band label-free, 20 km pooled blocks, paired bootstrap.

| arm | holdout DTI (R0 = 0.02861) | Δ vs R0 | 95 % CI | SGMC control Δ vs R0 |
|---|---|---|---|---|
| `b5km-move15` | 0.04082 | +0.0122 | +0.0029…+0.0254 | −0.0126 |
| `b1km-move24` | 0.05275 | +0.0241 | +0.0121…+0.0372 | −0.0200 |
| `b1km-move15-t05` | 0.04811 | +0.0195 | +0.0093…+0.0315 | −0.0139 |
| **shuffled-prior null** | 0.02826 | **−0.0004** | −0.0028…+0.0027 | −0.0120 |
| **TMI-only prior** | 0.02945 | **+0.0008** | −0.0044…+0.0073 | −0.0160 |
| **catalogue-only prior** | 0.04346 | **+0.0149** | +0.0064…+0.0257 | −0.0097 |

Three readings, in order of importance:

1. **The holdout gain is the instrument's circularity, not information.** The hide-and-recover
   truth *is* the withheld catalogue, so a catalogue-density prior is rewarded by construction;
   decompose the prior and the entire gain sits in the catalogue term (+0.0149) while the only
   non-circular, physical term recovers nothing (+0.0008, CI crossing zero). The shuffled-prior
   null confirms the instrument is not simply rewarding movement (−0.0004).
2. **An independent map disagrees.** Against USGS SGMC faults that are not in the competition
   catalogue, *every* arm — including the null — loses 0.012–0.020. Relocation has a real
   cost-of-moving term, and no prior in this family earns it back. (SGMC is itself a
   catalogue-like map, so this control is biased the same way as the first and still comes out
   negative; that makes the negative the stronger half of the evidence.)
3. **Therefore the axis is predicted flat.** Both prior predictions were revised down after these
   instruments ran; the preregistered numbers stay visible in `ledger/submissions.csv`
   (`preregistered_change`) so the revision cannot be mistaken for the original bet.

**What would change the decision:** a live CONCENTRATION Δ ≥ +0.010 would prove the
catalogue-density prior transfers to *new* faults and would justify the CONCENTRATION field as a
first-class feature; it would also mean the TMI term is dispensable. Anything inside ±0.010
retires the axis for Phase 1 and moves the remaining slots to the collar lineage, whose
mechanism (masked slivers) does not depend on any prior at all.

## Leakage canary

Not re-run for this axis: both prior terms are block aggregations of (a) the catalogue itself and
(b) a public potential-field band, and the instrument above is *by design* catalogue-derived —
a single-feature AUC computed against withheld catalogue would be ~1.0 for the catalogue term
for trivial reasons and would not identify leakage. The honest statement is that no label-free
feature here is claimed to be independent of the catalogue; the SGMC control is the guard, and it
is reported above with its own bias stated.
