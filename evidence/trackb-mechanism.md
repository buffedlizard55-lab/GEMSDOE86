# TRACKB mechanism cards — written for a structural geologist

Parent R0 = `h33-h33-2-b2` (37,654 unit-mass dots, 0.2778 CLAIM, no receipt).
Axis self-assigned: TRACKB is the only brief-§5 axis no earlier session built,
and the only one aimed at Phase 2 (expert-expanded labels after reviewing
submitted faults). **No slot is requested.** All predictions are MODEL.

Common construction (all three arms): greedy two-sided chaining of R0's own
dots, step ≤ 4.5 px, chain kept iff ≥ 4 dots and ≥ 10 px (1 km) long; seeds in
descending neighbour count. Arms differ **only** in the turning-angle ceiling.
No band, label or probability field is read (`src/gems86/trackb.py`).

## Card 1 — `trackbs20` (turn ≤ 20°): the strict strand set
- **Hypothesis.** The most defensible Phase-2 objects are near-straight
  strands: a real fault trace mapped at 100 m should not kink more than ~20°
  per 300–450 m step except at intersections and step-overs.
- **Mechanism.** Strict chaining keeps only dots whose neighbours continue the
  local strike; 1,327 traces, 6,839 dots (18.2 % of R0), 1,831 km total.
  These are the traces to put in front of an expert first.
- **Non-fault mimic.** Chance alignments of field maxima at 2.8–4.5 px spacing,
  and cultural lineaments (roads, drainages) the parent field may have followed.
- **Predicted sign/size.** Raster rendering −0.069 MODEL vs R0 on the SGMC
  surrogate — expected on mass alone (20,603 vs 37,654 px) and **not** a
  prediction about Phase-2 value, which no local instrument measures.
- **Falsifier.** An expert rejects these strands at the same rate as the s40
  additions, i.e. strictness bought nothing; or s20 traces dissolve under a
  ±1 px dot jitter (not run — proposed, not built).

## Card 2 — `trackbs30` (turn ≤ 30°): the base set
- **Hypothesis.** 30° admits genuine fault curvature and en-échelon jogs while
  still excluding random walks.
- **Mechanism.** 1,830 traces, 10,229 dots (27.2 % of R0). The increment over
  s20 (+503 traces) is exactly the population of curved/stepped strands.
- **Non-fault mimic.** As card 1, plus drainage bends, which turn smoothly at
  exactly this scale.
- **Predicted sign/size.** −0.059 MODEL (raster, mass effect as above).
- **Falsifier.** Expert acceptance of the s30-only traces is no better than
  acceptance of s40-only traces — then curvature was noise, and s20 is the set.

## Card 3 — `trackbs40` (turn ≤ 40°): the permissive bound
- **Hypothesis.** An upper bound, not a recommendation: how much of R0 is
  chainable at all before the rule stops discriminating?
- **Mechanism.** 2,137 traces, 12,722 dots (33.8 % of R0); even permissively,
  **two-thirds of R0's dots lie on no ≥1 km strike-consistent chain** — the
  axis's headline measurement, independent of any surrogate.
- **Non-fault mimic.** At 40° the chain can follow arcuate non-fault features
  (shorelines of playas, road grids turning at junctions).
- **Predicted sign/size.** −0.051 MODEL (raster; it emits the most pixels).
- **Falsifier.** If experts accept s40-only traces as often as s20 traces, the
  coherence ceiling is not the discriminating variable and TRACKB's ranking
  premise fails — the dots' value is not in their collinearity.

## What would change the plan
Expert review (the human's Phase-2 act, not a weekly slot) is the only
instrument that can score these. If review accepts strict traces preferentially,
the final-file lineage gains a trace-ranked re-selection axis (proposed in
SLOT_PLAN.md, not built). If review is flat across arms, collinearity is not
evidence and TRACKB closes.
