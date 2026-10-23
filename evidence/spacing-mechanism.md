# SPACING — mechanism cards (session of 2026-10-23, parent R0 `h33-h33-2-b2`)

AXIS: **SPACING** — the one axis in brief §5 that no earlier session had built. Every arm is a
single relocation of R0's own mass: the count stays 37,654, the exclusions stay R0's, the *dose* is
a threshold on a geometric quantity rather than a percentage, and only the admissible *shape* of a
destination changes between arms. All numbers below are MODEL or PROXY; none is a score.

## What is shared by all four builds

**Selection.** Each dot owns some of the 29 cells of its radius-3 px kernel disc — the cells for
which it, and not a neighbour, is the first dot within reach. Under the official max kernel
(`TP_w = Σ_g max_x p(x)·k(d)`, `vendor/gems57/metric.py`) that exclusive set *is* the part of a dot's
credit no neighbour can take away. R0's mean exclusive credit is 20.73 of 29 cells, i.e. **28.5 % of
its nominal kernel credit is already written off by overlap**; 11,415 dots (30.3 %) have a nearest
neighbour at exactly 2.828 px, the d2.8 thinning floor, which is *inside* the kernel radius. Every
dot owning ≤ 16 cells — **7,228 dots, 19.20 % of R0, 37.5–37.9 % of its cells changed** — is picked
up and put down by one of the laws below. A threshold was used instead of a count because the credit
distribution is quantised: a count-based cut lands inside the tie class at credit 17 (3,411 dots)
and the pixel-scan tie-break would then be the experiment, which is the failure mode that made the
MASS session's ranking a traversal (IR-86-MASS-01).

**Objective (identical in all arms).** Inside an 800 m window, take the free cell farthest from the
nearest retained dot — fill the largest local kernel gap — subject to a hard core of 3.0 px (the
kernel radius) against every dot that will be present, and to ≥ 3.0 px off the catalogue for the new
mass (brief 4.4, applied as IR-86-RELIEF-02 requires). No band, label, or probability field enters a
placement, so unlike SNAP this axis cannot be a hidden edge detector.

**Non-fault process that could mimic the whole axis.** The metric pays for *area within 300 m of a
prediction*, not for geology. Any arrangement that spreads discs over unclaimed ground raises the
score without saying anything about a fault — fluvial terraces, paleoshorelines, curvilinear
drainages, survey lines and road cuts all have the same local geometry as a scarp, and a
max-over-discs score cannot tell them apart. This is why the arms are read against a random-move
control rather than against zero.

---

## 1. `SPACING / pdisk16` — isotropic hard core (blue noise)

`releases/axis86/gems86-h33-2b2-sp-pdisk16-20261023-0d2f135e-zeros.tif`

- **Hypothesis.** R0's score is limited by disc overlap, not by where its mass sits: give the
  redundant 19 % of the mass its own uncovered neighbourhood and the same 37,654 unit masses buy
  strictly more truth coverage.
- **Mechanism.** De-clustered emission. Union of kernel discs over the eligible domain grows by
  +113,315 px (+14.5 % of R0's own covered area off the catalogue); dots below the kernel radius
  fall from 11,415 to 3,754; mean NN spacing 3.735 → 4.288 px; mean displacement 6.77 px (677 m).
  Under `DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)` at fixed S, T and M both rise with fewer shared
  truth pixels, so the same mass is asked to cover more of the trace field.
- **What a geologist should distrust.** A Poisson-disk hard core is *anti-geological* along a
  fault: real strands en-echelon at 200–600 m spacing, step-overs and splays are exactly the
  sub-kernel clustering this rule removes. The arm pays for that if the metric's extra coverage is
  not on a fault.
- **Predicted live change.** **+0.0015 MODEL** (band +0.0015…+0.0072 from the translated-ensemble
  bracket; surrogate relative gain +1.6 %). Below the 0.01 evidence floor: a single live read here
  cannot prove or disprove the mechanism, it can only fail to.
- **Falsifier.** Live Δ ≤ −0.005 → the coverage bought is off-fault mass; the axis closes for
  Phase 1 and spacing is removed from the plan. Δ inside ±0.010 and the same as the random control
  → the law does not exist as far as the score is concerned, which is the *expected* outcome of
  this design.

## 2. `SPACING / lattice16` — ordered even placement

`releases/axis86/gems86-h33-2b2-sp-lattice16-20261023-63c4c56f-zeros.tif`

- **Hypothesis.** At fixed mass the metric rewards *evenness*, not merely separation: the sparsest
  ordered arrangement that still leaves no point of the region more than 300 m from a dot is the
  optimum of this axis.
- **Mechanism.** Same selection, same objective, destinations restricted to the nodes of a
  hexagonal lattice with spacing √3·R. The ideal covering spacing is 5.196 px; because nodes must
  land on a 100 m grid, the spacing is searched downward and the *measured* interior covering
  radius is reported (3.162 px <= 3.0 + 0.5 px tolerance), so "covering" is a checked property, not
  an assertion. Coverage gain +107,851 px; 480 dots needed the widened 1.6 km window and 8 could
  not be placed at all and kept their parent cells (so their count, not their position, changed). Mean displacement 6.29 px.
- **What a geologist should distrust.** This is the arm most likely to be pure cartography: a
  regular grid of prediction points over a landscape that is not regularly faulted. The fleet has
  one warning — the historic `13GEMSDOE r13-lattice-s5` file, a lattice emission, scored 0.0904
  (CLAIM). That file replaced the field with a lattice rather than re-spacing R0's 19 %, so it does
  not falsify this arm, but it should stop anyone from calling lattice placement safe.
- **Predicted live change.** **+0.0019 MODEL** (band +0.0019…+0.0072; +2.0 % relative on the
  surrogate) — the largest surrogate read of the three.
- **Falsifier.** Live Δ ≤ −0.005, or block-density CV (the reported 0.51–0.59 band for the best
  files, which R0 itself sits outside at 0.6235, IR-86-CONC-02) moving further out than
  CONCENTRATION's 0.7644 while the score falls: that would say the region wants *less* order, and
  both this arm and CONCENTRATION retire together.

## 3. `SPACING / strike16` — extend the trace, never leave it

`releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif`

- **Hypothesis.** Redundant mass should be spent *along the same lineament*, because a fault is a
  line: the coverage a duplicated dot wastes is exactly the coverage an along-strike gap lacks.
  Isotropic spreading (arms 1–2) buys area the metric cannot attribute to a fault.
- **Mechanism.** The local strike is the leading eigenvector of the parent dot cloud's k-nearest
  neighbourhood (PCA of R0's own geometry — no geophysical band, so this is not SNAP by another
  name); coherence `(λ1−λ2)/(λ1+λ2)` decides whether the neighbourhood is line-like, and the 10th
  percentile is 0.21, so **1,808 of 7,228 selected dots sit on blobs, not lines, and fall back to
  the isotropic law; that is reported, not hidden**. Destinations must lie within 1 px across the
  ridge and ≥ 2 px along it. Coverage gain +75,136 px — the smallest of the three, by construction:
  a trace has less free length than the neighbourhood around it. Mean displacement 6.88 px;
  **its false-positive term rises by only +83.7 against +140 for the other arms**, the one
  signature that says the moved mass stayed on something real.
- **What a geologist should distrust.** A line fitted to the dots is a line fitted to the
  *prediction*, so the arm is self-confirming: it cannot discover a fault the lineage's own field
  missed, and where the ridge is an artefact of the thinning (a straight run of 2.83 px steps) the
  "strike" is an artefact of the algorithm, not of stress.
- **Predicted live change.** **+0.0020 MODEL** (band +0.0020…+0.0050, 3/4 quadrants positive) —
  nominally the best of the three and the only one whose FP cost is nearly zero.
- **Falsifier.** Live Δ ≤ −0.005 while pdisk/lattice stay flat → trace continuity buys nothing; the
  kernel is isotropic and so should the arrangement be. Positive on this arm and negative on
  `strike`'s own dose-reduction rung (a 10 % threshold rung, unbuilt) → the effect is dose, not law.

## 4. `SPACING / random16` — the null control (**not** a slot candidate)

`releases/axis86/gems86-h33-2b2-sp-random16-20261023-db4cae83-zeros.tif`

Same 7,228 dots, same window, same floor, same exclusions, destination drawn uniformly at random.
Surrogate Δ **+0.0002** (+0.2 % relative), so every arm above beats chance by ~+0.0015 — but under
the ±6 px translation ensemble the control rises to +0.0033 and the separation from the laws
shrinks to ~+0.0016. **The honest summary of this session: the surrogate rewards de-overlap far
more strongly than it rewards any particular spacing law, and no arm here is predicted to clear the
0.01 evidence floor.** Recorded so the next session does not dress a displacement artifact up as a
mechanism.

## Cross-arm confounds, stated

1. **The gained coverage is mostly off the lineage's own evidence.** 100 % of the relocated dots
   start on the H19-5 support surface; only 1.8 % (pdisk), 3.0 % (lattice) and 5.2 % (strike) of
   their destinations are on it. The surrogate rewards the new coverage because the SGMC map extends
   past the H19-5 ridge; the live truth may not. This is the axis's largest single risk and the
   reason all three bands are wide.
2. **Spacing and collar are entangled by the eligibility rule**: raising the hard core to 3.0 px
   pushes mass away from *other dots*, and the catalogue clearance pushes it away from *the
   catalogue*, so a positive read cannot be assigned to spacing alone. PRUNE's `le3p000` is the arm
   that separates the two, which is why slot 1 in `SLOT_PLAN.md` stays there.
3. **The hide-and-recover PROXY cannot rank this axis, in either direction.** With the collar held
   fixed, every new cell is ≥ 3 px off a visible fault and the whole lineage reads ~0
   (IR-86-PRUNE-03, IR-86-SNAP-06). Re-derived *fairly per fold* it does move — pooled PROXY DTI
   0.00370 [0.00297, 0.00441] for R0 versus 0.01534 (`pdisk16`), 0.01359 (`lattice16`), 0.01217
   (`strike16`) — but that is an artefact of who got a collar: an arm built from the fold's *visible*
   catalogue is free to sit on the withheld trace, while R0 was built against the full catalogue and
   avoids exactly those pixels. The instrument then measures the absence of the collar, which is
   PRUNE's quantity (IR-86-SPACING-05). Reported, never used to order the arms, never a gate; every
   prediction in the ledger comes from the SGMC off-catalogue surrogate instead.
4. **Every number here is a projection against an independent map**, not a score, and 0 receipts
   exist in `ledger/submissions.csv` — including for R0's 0.2778.
