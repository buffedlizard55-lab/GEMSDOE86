# CONCENTRATION dose / block-scale cards — session 2026-10-23

Written for a structural geologist. Parent R0 = `h33-h33-2-b2` (GEMSDOE32), 37,654 unit-mass
dots, sha256 `c55bafc4…b6fa9`, rebuilt **byte-for-byte** this session from the pinned base
`gems28-h27-4-r1-solo-d2-8` (`ab023001…`, 40,199 → 37,654, 0 differing cells).  R0's live 0.2778
is a **CLAIM** (owner-reported); there is no submission-page receipt in `ledger/`.

This session builds three **new** `(CONCENTRATION, value)` pairs.  The axis was already built once
— `(CONCENTRATION, b1km-move15)` (PR #37, `…-conc15-…-2b883f2d`, +0.006 MODEL) — so the three here
are the dose-response rungs and the block-scale cut that the SLOT_PLAN names as the axis's next
experiment.  Every number below is a **MODEL** (local arithmetic on the official metric) unless
labelled otherwise; nothing here is a score, and a live change under 0.01 is no evidence.

Shared mechanism (all three): the prior on where an *unmapped* fault pixel is most likely is
`z(catalogue fault-interaction density, 3×3 km mean) + z(mean Sobel gradient of TMI
upward-continued to 150 m)`, computed per km-block.  Dots are moved out of the lowest-prior blocks
into the highest-prior fifth, count held at 37,654, placement **geometric only** (highest-prior
destination block, then the largest remaining kernel gap).  No pixel-scale response term enters, so
this axis cannot smuggle in the SNAP edit that instrument already measured as negative.

| variant | block | dose | dots moved | % changed | block-CV (occupied) | predicted (MODEL) |
|---|---|---|---:|---:|---|---|
| `b1km-move10` | 1 km | 10 % | 3,765 | 19.998 % | 0.6235 → 0.7289 | +0.004 (+0.002…+0.007) |
| `b1km-move20` | 1 km | 20 % | 7,531 | 40.001 % | 0.6235 → 0.7914 | +0.008 (+0.004…+0.012) |
| `b5km-move15` | 5 km | 15 % | 5,648 | 29.999 % | 0.7442 → 1.0313 | +0.003 (0.000…+0.008) |

The built `b1km-move15` (1 km, 15 %, 5,648 moved, CV 0.6235 → 0.7644, +0.006 MODEL) is the centre
point: with these three it forms a dose-response at 1 km (10/15/20) and a block-size comparison at a
fixed 15 % dose.

---

## 1. `b1km-move10` — dose low

**Hypothesis.** New-fault pixels concentrate where mapped systems interact (step-overs, tips,
intersections, relay ramps), so moving *some* of the dot budget into the highest-prior 1 km blocks
raises truth credit `T` at constant false-positive mass `S`.

**Mechanism.** `DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)`. A relocated dot earns kernel credit only
where its 300 m triangular kernel reaches an *unmasked* new-fault pixel.  The highest-prior blocks
are where interaction-zone strain and detectable magnetic lineaments coincide, so a moved dot there
has a higher expected credit than the low-prior dot it replaced.  Ten percent of the mass is the
brief's lower bound: enough to move 3,765 dots, small enough that the effect should be roughly
linear in dose.

**Non-fault process that could mimic it.** Two. (1) *Mapping effort*: the catalogue is dense near
roads, mine pits and published 1:24,000 quadrangles, so "high interaction density" partly encodes
where a geologist once walked, not where strain localised. (2) *Magnetic edges without faulting*:
lithologic contacts, intrusive margins, propylitic/argillic alteration fronts and survey-line seams
all produce TMI gradients.  GeoDAWN Area 2 was flown at 400 m line spacing 150–200 m above terrain,
so lineament positions carry uncertainty of about one kernel radius.

**Predicted live change.** **+0.004** (range +0.002…+0.007), MODEL. Roughly two-thirds of the built
`b1km-move15` prediction, on a linear-in-dose reading.

**Falsifier.** A live change ≤ 0 falsifies the interaction-prior reading.  Because this is the low
rung, a *flat* result here with a positive `b1km-move15` would instead say the response saturates
faster than linear — which would make `b1km-move20` the informative rung, not this one.

---

## 2. `b1km-move20` — dose high

**Hypothesis.** Same as `b1km-move10`, at the brief's upper bound: the effect is still rising at 20 %
of the mass moved, so the highest dose buys the most truth credit.

**Mechanism.** Identical prior and placement rule; 7,531 dots relocated (20 % of 37,654), count
held.  This is the only one of the three that approaches the 0.01 evidence floor, so it is the rung
that can actually separate "the axis works" from "the axis is below noise".

**Non-fault process that could mimic it.** Same two as `b1km-move10`, plus a dose-specific one: at
20 % the destination blocks are the *same* highest-prior fifth, so the added mass stacks into fewer
blocks and the block-density CV rises to 0.7914.  If the region's real faulting is more dispersed
than the prior says, the extra clustering buys false-positive mass faster than truth credit.

**Predicted live change.** **+0.008** (range +0.004…+0.012), MODEL. The upper rung of the
dose-response; the only variant here predicted to clear 0.01.

**Falsifier.** A live change ≤ 0, *especially* alongside a positive `b1km-move10`, would show the
dose-response turns over — i.e. the prior's high-prior blocks are not systematically richer in new
faults, and the CV rise is buying clustering, not coverage.

---

## 3. `b5km-move15` — block scale

**Hypothesis.** The block size the prior is computed on matters: a 1 km block is finer than the
kernel (300 m) and than the mapping uncertainty, so the "highest-prior" set is noisy; a 5 km block
averages over a real fault-interaction zone and should separate better *if* the mechanism is
block-scale interaction, or worse *if* the mechanism is pixel-scale.

**Mechanism.** Same 15 % dose, same geometric placement, but the prior is computed on 5×5 km blocks
(50×50 px) and the catalogue-interaction term is smoothed over 15 km.  The destination set is the
highest-prior fifth of the 5 km blocks (438 blocks vs 10,462 at 1 km) — far larger and far less
selective.  The parent's own block-CV at 5 km is 0.7442 (not 0.6235, which is the 1 km figure);
this variant takes it to 1.0313.

**Non-fault process that could mimic it.** The 5 km smoothing blurs the catalogue-density term across
distinct terranes, so "high prior" at 5 km can be a broad magmatic/structural domain rather than a
fault-interaction zone.  Conversely the coarser block *reduces* the mapping-effort confounder,
because a 5 km block averages over many survey extents.

**Predicted live change.** **+0.003** (range 0.000…+0.008), MODEL — weaker than `b1km-move15`,
because the destination set is less selective.  This is the SLOT_PLAN's named next cut (block size).

**Falsifier.** A live change ≥ `b1km-move15`'s would say the interaction prior is a *block-scale*
signal and the 1 km cut was under-smoothed — in which case the next cut is 10 km, not another dose.
A live change ≤ 0 while `b1km-move15` is positive would say the mechanism is pixel-scale, not
block-scale, and retire the block-size axis.

---

## Reading order

`b1km-move20` first (only rung that can clear the floor), then `b1km-move10` (dose shape), then
`b5km-move15` (block scale).  None of the three is a slot candidate on prediction alone; they are
built so that the *shape* of the dose-response and the block-scale dependence are measured, not
guessed.

## Provenance of every external input

| input | pin | provenance |
|---|---|---|
| `existing_faults.tif` | `7ba308cc…` | owner mirror of the competition catalogue |
| `sample_submission.tif` | `2176d08e…` | owner mirror of the competition format file |
| parent R0 | `c55bafc4…` | owner mirror, GEMSDOE32 `780a5a53`; rebuilt byte-exactly |
| base `gems28-h27-4-r1-solo-d2-8` | `ab023001…` | owner mirror; R0 = base AND d_cat > 2.0 px |
| `geodawn_extensions_u8.tif` (TMI up-150 m) | `a35a9c6d…` | USGS GeoDAWN, DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), public domain |
| `topo_10m_derived_100m_u8.tif` | `a6398d99…` | USGS 3DEP-derived, owner-computed derivatives |
| `dem10_chi_100m_i16.tif` | `8897ba9c…` | same family |

Lidar-derived rasters were **not** used (brief §5 permits them for SNAP only, and the human supplied
the GeoDAWN/DEM mirror set only).
