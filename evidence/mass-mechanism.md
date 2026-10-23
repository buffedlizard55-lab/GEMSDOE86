# Mechanism cards — MASS axis on R0 (built 2026-10-23)

Parent **R0** = `h33-h33-2-b2`, 37,654 dots, sha256 `c55bafc4…b6fa9`, rebuilt
**byte-exactly** this session (dot set and file bytes). R0's 0.2778 is a **CLAIM**
(no submission-page receipt). Everything below is a **MODEL** prediction, never
a score. A live change with |Δ| < 0.01 is no evidence.

## The ranking both cards use (rebuilt, then validated)

The parent's ranking is not stored anywhere. It was rebuilt from the recorded
recipe: the FIFO-BFS visitation order of `gems27.thinning` (GEMSDOE28 commit
`94b027b`) over the pinned H19-5 field (121,131 binary ridge cells), mirrored by
`scripts/build_r0_prune.original_visit_rank`. The rebuild is *validated*, not
assumed: greedy 2.8 px thinning in ascending visit order reproduces the pinned
`d2.8` dot set **exactly** (44,090 dots, 0 differing cells); a row-major order
does not (14,225 differing cells). Earlier visit = higher priority, because
earlier cells claimed their 2.8 px territory first. The order is
spatial/content-blind — it is a traversal, not a geological probability — and
because components are seeded row-major, it is geographically structured. That
structure is measured for each edit below and is the axis's main confounder.

---

### 1. `h33-h33-2-b2-massminus10-20261023-42b4c5c8` — 33,889 dots (−9.9989 %)

- **Hypothesis.** R0 is slightly over-massed: its lowest-priority 10 % of dots
  (the traversal tail, visit ranks 108,329–121,128) earn less kernel credit
  than the false-positive mass they cost.
- **Mechanism.** Delete those 3,765 dots; nothing else changes. At the claimed
  DTI ≈ 0.28 a dot pays only if its marginal truth credit beats
  `0.2 · DTI ≈ 0.056`. The tail is label-free evidence-poorer than the dots
  that stay (`tmi_hg` percentile 0.491 vs 0.541 for the parent, `tc` 0.437,
  `mag_anom` 0.463), so the saved mass is real — but these dots are also the
  only cover of the small late-visited ridges they sit on, and coverage lost
  there cannot be recovered by the dots that remain (max operator).
- **Non-fault process that could mimic it.** The traversal tail is geographic,
  not geological: the 3,765 dropped dots are **100 % in the southern half**
  (mean row 3,215 vs the parent's 1,273). Small southern ridge fragments —
  range-front scarps and piedmont lineaments that are short because they are
  buried, not because they are absent — are visited last precisely because
  they are small and disconnected. Deleting them could remove genuine
  southern fault cover and read as a "mass" loss.
- **Predicted live change.** **−0.003 (MODEL, band −0.012…+0.006).** Slightly
  negative: near the inclusion bar, with a coverage-loss tilt.
- **Falsifier.** A receipt ≥ +0.010 vs R0 says the tail really was dead mass
  and a further −10 % cut is licensed. A receipt ≤ −0.010 says traversal-tail
  dots carry unique cover — stop cutting mass in rank order.

### 2. `h33-h33-2-b2-massplus10-20261023-a5888761` — 41,419 dots (+9.9989 %)

- **Hypothesis.** R0 is slightly under-massed: the next-ranked H19-5 cells add
  new-fault coverage worth more than their false-positive cost.
- **Mechanism.** Add the 3,765 highest-priority suppressed cells (ascending
  visit rank; footprint, off catalogue, > 2 px from it — R0's own collar;
  minimum added distance 2.236 px). But these cells were suppressed *by* the
  2.8 px rule: **98.59 % lie within 2.8 px of an existing dot** (candidate
  mean nearest-neighbour 3.735 → 3.396 px). Under the metric's max operator,
  most of their truth credit is already claimed by the neighbouring dot,
  while each still pays close to full false-positive mass. Label-free, the
  added set is also evidence-mixed (`tmi_hg` 0.469 vs parent 0.541; `tc`
  0.564). The catalogue hide-and-recover PROXY moved the other way
  (+0.00022, 6/6 folds) — it sits at its floor for this lineage
  (IR-86-PRUNE-03) and is reported, not believed.
- **Non-fault process that could mimic it.** The additions are **100 % in the
  northern strip** (mean row 60.5, 0 % in the southern half): early-visited
  components. Dense northern ridge texture — shoreline terraces, road/track
  lineaments and survey seams in the GeoDAWN bands — supplies fault-like
  cells there, and densifying an already dense area mimics "more coverage"
  without new faults.
- **Predicted live change.** **−0.006 (MODEL, band −0.016…+0.002).** The
  weakest of the session's predictions on mechanism (redundant mass), despite
  the contrary floor-level PROXY.
- **Falsifier.** A receipt ≥ +0.010 vs R0 falsifies the redundancy argument:
  suppressed neighbours would be carrying independent credit, and the 2.8 px
  spacing itself — not the mass — would become the next axis to re-cut.

## What a MASS receipt would and would not teach

Either file, scored, brackets the mass question *as ranked by the recipe*:
if both lose, R0's 37,654 is near a local mass optimum in traversal order and
mass leaves the plan. It would **not** isolate mass from geography (minus
edit) or from spacing/redundancy (plus edit); those confounders are stated
above so a flat or negative result is correctly read as "this ranked edit
did not help", not "mass does not matter".
