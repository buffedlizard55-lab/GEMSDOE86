# SPACING axis — mechanism cards (R0 = h33-h33-2-b2)

Session 2026-10-23 (`arena/ee238b91`), AXIS = SPACING. A parallel session landed a different SPACING design (`sp-*c16` arms, evidence/spacing-mechanism.md) on main during this branch; the value keys differ and both stand (IR-86-SPACING-07). Evidence classes: **MODEL** (predictions), **PROXY**
(instruments), **MEASUREMENT** (gates). Nothing here is a score or a receipt; the live
metric's truth is hidden and every number below is either a local measurement or a
projection. Per the brief: a live |delta| < 0.01 is no evidence (public chunks only; the
private score may differ).

## Shared design (all three arms)

Parent R0 (GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, sha256 `c55bafc4…b6fa9`)
carries 37,654 unit-mass dots on the H19-5 lineament support. Its spacing came from a greedy
2.8 px thinning: minimum nearest-neighbour distance 2.828 px, mean 3.735 px. The DTI's
triangular kernel has radius R = 3 px, so **30.3 % of R0's dots (11,415) sit inside the kernel
radius of another dot** — their kernels overlap at positive weight.

**Crowded pool.** Pairs closer than 3.0 px are clustered (4,841 clusters); the member with the
earliest H19-5 visit rank stays — that is the parent's own recipe ranking, rebuilt from the
recorded FIFO-BFS traversal and validated by reproducing the pinned d2.8 set exactly (0
differing cells). The other members (6,574 dots = 17.46 % of R0) are the crowded pool. About
3,050 of them (8.1 % of R0's dots; 16.2 % under the removed+added cells convention) find a
legal destination and move; the rest stay put in saturated corridors (residual crowding,
measured per arm).

**Legality (shared, so the arms differ only in destination geometry).** A moved dot lands on a
parent-support (H19-5) cell, inside the footprint, >= 3.0 px from the catalogue (the >=3 px
rule binds newly emitted mass only — IR-86-RELIEF-02), >= 3.0 px from its cluster's kept dot
(the crowded pair is broken at the kernel radius), and >= 2.828 px (= sqrt(8), the parent's
own floor) from every other dot. The parent's minimum spacing is never tightened. Count is
fixed at 37,654 in every arm.

**Dose-fose confound note.** Median displacement is 1 px, mean 2.1–2.2 px, max 16 px — this is
a spacing repair, not a relocation. The three arms' moved counts differ by < 2 % (occupancy
evolution), so the comparison is effectively paired on the same pool.

**What the metric says about the mechanism.** For a binary dot field,
`DTI = T / (0.2T + 0.2(S − M) + 0.8|G|)` with S = dot count and M = summed self-credits.
A dot whose kernel duplicates its partner's coverage adds almost nothing to T (the max
operator saturates per truth pixel) while still paying `0.2(1 − k)` in the denominator. At
DTI ≈ 0.28 a non-redundant dot pays for itself once its credit exceeds ≈ 0.056; a *redundant*
second dot near the same trace often fails that bar. Breaking the pair at the kernel radius
converts duplicated mass into fresh coverage **if** the freed dot can still sit near truth —
which is what the three placement geometries test.

## Card 1 — SPACING lattice (id `…-SPACING-lattice-20261023-4551582d`)

- **Hypothesis.** The freed dot belongs wherever coverage is thinnest in a *regular* array:
  maximal second-order uniformity is the best way to spend re-spaced mass, regardless of
  structural grain.
- **Mechanism.** The moved dot snaps to the nearest free site of a square lattice of pitch
  3.0 px (the kernel radius) anchored at the raster origin, subject to the shared legality.
  Regular spacing minimises kernel overlap for area-like truth: each dot's triangular kernel
  covers fresh ground.
- **Non-fault process that could mimic it.** Grid-aligned regularity is exactly what survey
  grids, DEM tiling, and processing footprints look like; a lattice can also "win" trivially
  when the real pattern is uniform background. If truth is linear (faults), lattice sites
  pull mass across-strike into inter-strand gaps where fault density is low.
- **Predicted sign and size.** **+0.000 MODEL** (band −0.004 … +0.004). The de-crowding gain
  and the off-lineament placement loss roughly cancel at this dose.
- **Falsifier.** Live delta <= −0.01 would mean the crowded pairs were carrying real second-
  strand coverage (en-echelon pairs at 280 m), i.e. the 2.828 px floor is load-bearing; live
  delta >= +0.01 would promote regularity above lineament-following and retire the
  line-like-truth story.

## Card 2 — SPACING poisson-disk (id `…-SPACING-poissondisk-20261023-d2cf39d5`)

- **Hypothesis.** The effect is the de-crowding itself, not the geometry: any legal placement
  of the freed dots does about as well as any other.
- **Mechanism.** Same pair-breaking at the kernel radius; the destination is a seeded uniform
  draw among legal cells (dart throwing with the spacing floor as the inhibition radius —
  blue noise). This is the *neutral* arm: whatever it shares with the other two is the shared
  mechanism, whatever differs is geometry.
- **Non-fault process that could mimic it.** Random-but-legal placement reproduces ordinary
  thinning noise in mapping effort; if this arm reads best, the "effect" is just jitter off
  the parent's traversal artefacts (IR-86-MASS-01: the parent's ranking is a geographic
  traversal), not a spacing law.
- **Predicted sign and size.** **+0.000 MODEL** (band −0.004 … +0.004).
- **Falsifier.** If poisson-disk beats both structured arms by >= 0.01 live, spacing geometry
  is a red herring and the crowded pairs were traversal artefacts — close SPACING and invest
  in the ranking instead (RE-RANK proposal in SLOT_PLAN.md).

## Card 3 — SPACING along-strike (id `…-SPACING-alongstrike-20261023-4d631f4a`)

- **Hypothesis.** Fault truth is line-like, so the freed dot should stay on its own lineament
  and slide along strike: beads on a string at kernel pitch cover more trace length than any
  isotropic arrangement.
- **Mechanism.** The local ridge tangent at the original cell is the principal axis of the
  H19-5 support within 3 px (PCA), oriented away from the cluster's kept dot; the freed dot
  takes the legal cell on that tangent line, as far along strike as legality allows. The dot
  keeps its self-credit on the same trace and extends coverage of the same structure — the
  DTI's line-like-truth regime rewards exactly this (isolated-truth bar 0.2·DTI ≈ 0.056;
  line-like truth lowers it, and marginal credit along a trace is high).
- **Non-fault process that could mimic it.** Ridge crests, bedding contacts, drainage divides
  and magnetic tonal boundaries are line-like but not faults; the H19-5 lineament field
  follows all of them. A gain here is consistent with "lineaments are where the mass already
  is", not with tectonic fault recovery. The SGMC control (mapped faults off the catalogue)
  is the only instrument here that can separate the two, and it is a PROXY.
- **Predicted sign and size.** **+0.002 MODEL** (band −0.003 … +0.006) — best of the three if
  fault truth follows the ridges at kernel scale; still far below the 0.01 evidence floor.
- **Falsifier.** Along-strike <= poisson-disk live by >= 0.01 falsifies the line-like-truth
  geometry at this scale; parity within ±0.005 with the other arms retires the whole axis.

## Instruments (REPORT ONLY — never gates, never scores)

- **Catalogue hide-and-recover PROXY** (10 whole-component draws, 20 % hidden, seed 306,
  2,000 bootstraps): free reading R0 0.00436 [0.00410, 0.00458]; arms 0.00424–0.00425. With
  the fixed >=3 px collar required by IR-86-SNAP-06 every arm reads **0.0000**. The small free
  drop is consistent with re-spaced mass leaving the catalogue collar; it is not evidence.
- **Leakage canary** (single-feature AUC vs withheld catalogue components): max AUC 0.7937
  (negative distance to visible catalogue), h19_5 binary ≈ 0.49. PASS (threshold 0.90).
- **SGMC control** (official-kernel DTI vs USGS SGMC faults at d_cat > 3 px): R0 0.09539;
  lattice 0.09614 (+0.00076), poisson-disk 0.09621 (+0.00083), along-strike 0.09608
  (+0.00070). All three positive and mutually within 0.00013 — consistent with "de-crowding
  helps a little, geometry is not resolved at this dose". PROXY only.

## Honest summary

Every instrument is flat at the ±0.001 scale and the three arms are nearly identical; the
pre-registered ordering (along-strike > lattice ≈ poisson) is **not** supported by the SGMC
readings, which put poisson-disk marginally first. Manipulation check (MEASUREMENT): the
three geometries place ~78 % of the moved dots on shared destination cells (pairwise Jaccard
0.64–0.65) because the legal sets around crowded clusters are small — the contrast between
arms is real but modest, and this limits what the comparison can resolve. The session's real
product is the closed question: SPACING at this dose, on this support, is not a slot-worthy
lever, and the design limit (IR-86-SPACING-06) says a stronger spacing edit at matched count
is geometrically impossible on R0's support.
