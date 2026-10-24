# Mechanism card — CONCENTRATION surface extension (session 2026-10-23)

**Axis:** CONCENTRATION · **Parent:** `h33-h33-2-b2-20261004-e5eb6e7e` (R0, 37,654 unit-mass dots,
sha256 `c55bafc4…b6fa9`, live 0.2778 = **CLAIM**, no receipt) · **Builder:**
`scripts/run_concentration_surfext.py` · **Run card:** `evidence/concentration_surfext_axis_20261023.json`

Written for a structural geologist. Every number below is a local measurement; none is a score.
`MODEL` = SGMC-extra surrogate, `PROXY` = fold-fair catalogue hide-and-recover. Both are
**report-only** (brief §6).

## Why this axis, and why here

The merged CONCENTRATION arm `b5km-cvband-down4` (+0.0015 MODEL in 4/4 quadrants, +0.0008 PROXY) is
the only arm in the ledger positive on both local instruments. A capacity audit run **before** any
candidate was built shows why it cannot be scaled:

| measurement | value |
|---|---|
| R0 dots on the `H19-5` ancestor surface | **37,654 of 37,654** |
| legal cells left on `H19-5` (>3.0 px from the catalogue, ≥2.8284 px from every R0 dot) | **90** |
| legal cells on `H19-4 \| H16-1` ground that is **not** `H19-5` | **8,671** (35,954 px of surface, zero R0 mass) |
| greedy placeable dots on that unused surface | **6,456** |
| merged arm's within-surface destination capacity | ~2,400 dots |

R0 is `H19-5` sampled at its 2.8–3.0 px dot spacing and then pruned inside 2 px of the catalogue. The
three ancestor surfaces are scored submissions of near-equal owner-reported quality — `H19-5` 0.1922,
`H19-4` 0.1894, `H16-1` 0.1855 (all **CLAIM**) — and the parent lineage uses exactly one of them.
The parent is therefore not under-dense; it is **saturated on one third of its own evidence**.

Reproduction check: the merged file was rebuilt from the restored inputs in this session and matches
byte for byte (`sha256 8aab97b65f70ba6c…`, id `…-concb5kmdown4-20261023-8aab97b6`), so the input
bytes here are the ones the merged arm used.

## The metric fact that shapes all three arms

`DTI = T / (0.2·T + 0.2·(n − M) + 0.8·|G|)`, with `T = Σ_g max_x p(x)·k(d)` **saturating at one per
truth cell** and `M = Σ_x max_g k(d)` saturating per dot. A dot whose truth neighbourhood a neighbour
already covers adds `ΔT = 0` but still costs `0.2·(1 − k)`: redundant mass is a strict drag. Hence the
source rule below is "pop the lowest **unique** kernel credit from the densest occupied 1 km block",
which is the merged arm's rule verbatim (its removal sequence is reproduced exactly; the builder's
unit test pins the two ordering properties, and the byte-exact merged-file reproduction pins the rest).

## Arm 1 — `b5km-surfext-down10` (candidate, `…-CONC-surfext10-20261023-fe814da5`)

* **Hypothesis.** 10% of R0's mass sits on dots whose kernel credit is already covered by a
  3-px-spaced neighbour, while 36k px of the parent's own ancestor evidence carries none.
* **Mechanism.** Move the 3,765 lowest-unique-credit dots of the densest 1 km blocks (9.9992% of the
  parent; **20.00% of cells changed**, inside the brief's 1–50%) onto legal cells of
  `H19-4 | H16-1` minus `H19-5`. Count fixed at 37,654; every added dot is ≥3.1623 px from the
  catalogue (mean 30.7 px, i.e. ~3 km) and ≥2.8284 px from every other dot; 100% of added mass lands
  on the ancestor union. 1 km occupied block-density CV 0.6235 → 0.5015.
* **Non-fault process that could mimic it.** `H19-4`/`H16-1` ridges include Lahontan shoreline
  treads, hogbacks and volcanic-flow margins; a fault-like ridge there is not necessarily a fault.
  The opposite failure is also live: 400 m GeoDAWN line spacing puts lineament positions ±150–200 m
  (1.5–2 px) off, so mass moved 3 km from the mapped catalogue may simply be mass removed from the
  only place the organiser promises new truth can sit (within 300 m of a known trace).
* **Predicted sign and size.** MODEL **+0.0059** (4/4 quadrants positive, ±6 px jitter mean +0.0063);
  PROXY **−0.00003** (95% CI [−0.0025, +0.0023], n = 11,321). These two instruments are biased in
  opposite directions for this arm (see the confound section), so the honest projection is
  **live Δ ≈ 0.000 to +0.003, bracket [−0.002, +0.007] — below the 0.01 evidence floor.**
* **Falsifier.** Live receipt Δ ≤ −0.005 → catalogue-adjacency dominates and the unused part of the
  ancestor union is not new-fault ground; close the surface-extension family. Live Δ ≥ +0.01 with
  `surfext15` also positive → the union headroom is real and the next dose is worth a slot.

## Arm 2 — `b5km-surfext-down15` (candidate, `…-CONC-surfext15-20261023-d3f2ecc7`)

* **Hypothesis / mechanism.** Nested 2× dose of arm 1: 5,648 dots (15.0%; **30.00% of cells
  changed**), same source and destination rules, same clearance and spacing floors. CV 0.6235 → 0.4677.
* **Mimic.** Same as arm 1, plus destination crowding: at 15% the frontier of the unused surface is
  reached, so a positive dose response could reflect the *first* 10% only.
* **Predicted sign and size.** MODEL **+0.0073** (4/4 quadrants), PROXY **−0.0005**
  ([−0.0038, +0.0027]). **Live Δ ≈ +0.000 to +0.003.** Under the linear scaling of the merged
  arm's own dose–response (1,506 → +0.0015), a 2× dose should have read ≈ +0.003; it reads +0.0073
  MODEL, but its matched control reads +0.0047, so most of that is not the lineaments.
* **Falsifier.** MODEL gain that does not exceed its own control by ≥0.001 *and* PROXY ≤ 0 → the
  effect is de-clustering, not evidence extension; do not spend a slot on any surface-extension arm.

## Arm 3 — `b5km-surfext-down10-randdst` (CONTROL, `…-CONC-surfext10ctl-20261023-b204c41b`)

* **Purpose.** Identical source dots and dose; destinations drawn uniformly (seed 86) from legal
  cells **off** the ancestor union inside the same 1 km blocks, so local block occupancy and block
  geometry are matched and only the lineament knowledge is removed.
* **Measured.** MODEL **+0.0047** (4/4 quadrants), PROXY **−0.0008**. Mean distance from the added
  cells to the ancestor union is 4.06 px, so this control still leaks mass into the 3-px kernel of
  ridge cells: it prices *de-clustering*, not *lineament knowledge*, and the ridge-specific increment
  is the difference — **+0.0012 MODEL, +0.0008 PROXY**, both inside instrument noise.
* **Never promoted.** A control is not a slot candidate.

## Instrument confound (measured, and it changes how MODEL deltas are read)

The SGMC surrogate's truth is `SGMC − catalogue`. Pixels on the mapped catalogue and in its immediate
collar can never be SGMC truth, while the organiser states new truth *can* lie within 300 m of a known
trace. R0 is built almost entirely of such collar-adjacent dots, so **any outward-moving
CONCENTRATION arm gains on this instrument partly by construction**. Measured here: the treatment's
added mass sits 21.7 px from SGMC-extra truth versus 22.6 px for the mass it removed — i.e. the arm
moved mass *toward* SGMC truth — while the control moved mass slightly *away* (22.8 vs 22.6 px) and
still scored +0.0047. The fold-fair PROXY is biased the other way: it can only reward mass near
*withheld catalogue* traces, which is exactly what surface extension gives up.

Consequence: **MODEL deltas for this family are not comparable across arms with different
catalogue-distance profiles, and neither instrument can settle the sign.** Every arm above is
therefore read against its control, never against zero, and no arm is called an improvement.

## What +0.01 of live DTI would actually require (MODEL projection, not a measurement)

Inverting the official algebra at the claimed 0.2778 with `|G| ≈ 40k` estimated truth pixels gives
`T ≈ 10,963` and a denominator of ≈39,464. One point of live DTI then needs **≈418 kernel-credit
units** of *new* truth coverage — about **42 km of fault trace hit squarely**, i.e. real new fault
geometry, not a different arrangement of the mass R0 already has. That is the quantitative reason
seven axes of rearrangement all land inside ±0.008, and it is the argument in `SLOT_PLAN.md` for
spending the remaining slots on evidence, not on more reallocation.
