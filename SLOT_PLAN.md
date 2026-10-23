# SLOT PLAN — 2026-10-23 (PRUNE + SNAP + MASS + RELIEF, five axes reconciled)

**No automatic slot use.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); the remaining quota and
`TOP_PUBLIC` are **UNSUPPLIED by the human** — I did not guess them. A live `|Δ| < 0.01`
is no evidence. R0 = `h33-h33-2-b2` (**0.2778 CLAIM**, no receipt in `ledger/`).

Deadline arithmetic: 2026-10-23 → **2026-12-03** is 41 days ≈ 5.9 weeks ⇒ ≈ 17 slots, one of
which is the blind final pick. The date is user-supplied and **UNVERIFIED**.

## What the three axes now say

* **PRUNE** — seven gate-clean artifacts, best predicted +0.004, whole ladder inside ±0.01.
  One slot, no more (three sessions already spent here).
* **SNAP** — three gate-clean artifacts this session, **all predicted ≤ 0**. The instrument is
  decisive and negative: 97–99 % of dots move, but a random-response null control scores the
  same proxy (+0.0001 vs −0.0012) and smoothing makes it worse. Snapping re-centres the field on
  local gradient maxima that the catalogue proxy cannot distinguish from chance, at a measured
  coverage cost (dots < 2 px apart: 0 → 3,448 / 8,341 / 2,085). **Do not spend slot 1 on SNAP.**
  It is worth one slot only as a deliberate probe of the unmeasurable live hypothesis: "new
  faults are at potential-field edges rather than at catalogue-adjacent positions".
* **CONCENTRATION** — **now built** (2026-10-23, PR #37, `arena/95e0ad6b`), on **1 km** blocks
  rather than the 5 km this plan proposed: `gems86-h33-2b2-conc15-20261023-2b883f2d`, 5,648 dots
  (15.00 %) moved out of the lowest-prior 1 km blocks into the highest-prior fifth (10,462
  blocks), count fixed at 37,654, **29.999 % changed**, all placements at the parent's 2.828 px
  spacing. **Block-density CV 0.6235 → 0.7644**, i.e. *away* from the reported 0.51–0.59 band,
  and occupied blocks fall 15,976 → 14,339. Prediction **+0.006 MODEL** (+0.003…+0.010). Its
  placement rule is deliberately geometric (highest-prior block, then largest remaining kernel
  gap) so the axis cannot smuggle in the pixel-scale edge snapping that SNAP already measured as
  negative. Falsifier: ≤ 0 live, which would also vindicate the 0.51–0.59 band as a real
  ceiling and make "spread mass until the CV lands in-band" the next axis.
  **RELIEF / SPACING** — RELIEF is built (above); SPACING remains unbuilt. MASS is built below.

**MASS is now built (2026-10-23, this session).** The parent ranking that blocked it
(IR-86-PRUNE-02) was rebuilt from the recorded recipe (FIFO-BFS visit order of
`gems27.thinning`) and *validated*: greedy 2.8 px thinning in that order reproduces the
pinned `d2.8` set exactly (44,090 dots, 0 differing cells). Two variants, each 9.9989 %
changed, both gate-clean in `releases/mass/`: `…-massminus10-…-42b4c5c8` (33,889 dots,
**−0.003 MODEL**) and `…-massplus10-…-a5888761` (41,419 dots, **−0.006 MODEL**). Both are
predicted to *lose*, so MASS gets **no slot by default** — R0's 37,654 looks near a local
mass optimum in traversal order. Cards: `evidence/mass-mechanism.md`; run card:
`evidence/mass_axis_20261023.json`. Spend a MASS slot only if PRUNE and SNAP/RELIEF both
come back flat and the mass question becomes the binding one; then take `massminus10`
(its falsifier is the sharper of the two) and never both.

## Next three slots, in order

| # | file (upload the `-zeros` twin) | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | the deepest collar rung, unchanged from the last plan; it is the only prediction that is positive *and* has a monotone ladder behind it. Prediction **+0.004 MODEL** (−0.004…+0.013), 35,483 dots, 5.77 % removed | ≥ +0.010 → the collar is not exhausted; next week a 4 px rung. Flat or ≤ −0.010 → PRUNE is finished for Phase 1 |
| 2 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | the only *built* positive prediction outside the collar lineage, and the only one that moves mass instead of deleting it: 5,648 dots (15.00 %) piedmont → range-front, count fixed at 37,654, mean displacement 6.1 km | ≥ +0.010 → the win is spatial allocation, not pruning: build RELIEF-ADD (same selection, count raised 43,302–49,000) and then the combination | ≤ −0.005 → sign confirmed, RELIEF closes for Phase 1 (brief §9 stop rule) | otherwise the axis is alive but below the evidence floor: do not multiply variants, spend slot 3 on the sign flip instead |
| 2b | `releases/gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif` — **CONCENTRATION, 1 km blocks, built** (the slot-2 alternative if the human prefers a move-the-mass cut over a second RELIEF rung) | the axis that changes *where* mass is without needing R0's ranking or a new physical field; 15.00 % of dots moved, count fixed, geometric placement only. Prediction **+0.006 MODEL**. It moves block-density CV 0.6235 → **0.7644**, i.e. away from the reported 0.51–0.59 band, so the result tests that band directly | ≥ +0.010 → the win is spatial allocation, and the final file is a PRUNE+CONCENTRATION combination; next cut is the block size (1 km vs 5 km). Inside ±0.010 → the prior is mapping effort, not geology; retire the catalogue-density term and keep only the TMI term. ≤ −0.010 → the region wants *less* clustering: build the spread-to-CV-in-band variant instead |
| 3 | `…-RELIEF-frontm10-20261023-1b26223e-zeros.tif` **or** `…-SNAP-r2p000-…-e7473403-zeros.tif` | the RELIEF rung is the **sign flip**: paired with slot 2 it is a 25 %-of-mass swing with a predicted separation of ~0.011, the only RELIEF comparison that can clear the floor. SNAP instead if the human would rather test an unmeasured *live* hypothesis (faults at potential-field edges) than a surrogate-measured one | RELIEF pair straddles 0 (slot 2 up, slot 3 down, or the reverse) → relocation is the axis; build RELIEF-ADD, then combine with `le3p000`. Both inside ±0.010 → RELIEF closes, take SNAP next. SNAP ≥ +0.010 → positions are the binding error and SNAP becomes the main lineage |

**Do not spend a slot on:** `SNAP-r1p000` or `SNAP-r2p000-grav` (same axis, weaker dose /
single band; they are the arms that read out *why* slot 3 went the way it did);
`…-prune4-…-de4c2a98` (−0.008) and `…-prune3r-…-8c20bd7e` (−0.003) — rehearsals, not bets;
`…-CONTROL-massctl2171…` (a control); `…-prune3-…-3eb29af5` (withdrawn, IR-86-PRUNE-08);
`RELIEF-frontp10` (a strict 10 % prefix of the 15 % dose, +0.0010 — the fallback, not a third bet);
the other two MASS rungs (−0.003 / −0.006, both predicted negative and never both).

## Calendar to the deadline

- **wk 1 (slot 1).** PRUNE `le3p000`. Single decisive read on the collar.
- **wk 2.** RELIEF `frontp15` (built; upload inside 24 h of any change to the regime map, and
  re-read the `-zeros` bytes through the validator before upload). CONCENTRATION at 5 km blocks only
  if it is built and preregistered first.
- **wk 3.** `RELIEF front−10pct` (paired with week 2) or SNAP `r2p000`, only if the human accepts
  a predicted-negative probe.
- **wk 4.** The better of CONCENTRATION / SNAP / RELIEF, re-cut at a second value on that axis.
- **wk 5.** Combine the two axes with receipt-level effects ≥ 0.01 as **one attributable edit**.
- **wk 6.** Confirm both finalists, re-validate both formats, choose the final file and a
  fallback blind, never multiply accounts.

## Better axes (proposals only; not built this session)

- **Coherent SNAP (structure-tensor, σ = 2–3 px).** The raw gradient bands are smooth but their
  local maxima are still not distinguishable from chance by the proxy; a coherence-weighted
  response is the physically correct "lineament" operator. *Confounder:* coherence peaks on
  any elongated contact. *Falsifier:* no separation from the random control in two independent
  hidden-component draws.
- **Exact-marginal PRUNE.** Remove dots with the most negative exact ΔDTI under the shared
  two-sided metric. *Confounder:* proxy-truth shift. *Falsifier:* no replicated positive sign on
  untouched spatial folds, then no live receipt.
- **Collar-conditional CONCENTRATION.** Only reallocate mass in blocks > 3 px clear of the
  catalogue, so the two axes do not interact. *Confounder:* relief controls both catalogue
  completeness and lineament visibility. *Falsifier:* opposite signs in two relief regimes.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation · any
submission-page receipt (R0's 0.2778 included) · which fill form the portal accepted last time ·
confirmation of the governing uniqueness rule (IR-86-PRUNE-01).

## Addendum — second SNAP session (magnetic edges), 2026-10-23: no slot requested

A second session was assigned SNAP and, because its branch predated PR #28–#31, built the axis
independently before `main` was merged in (IR-86-SNAP-04). It is recorded here so the three files are
not mistaken for untested candidates.

* **Built:** `snap-hg2` (33.9 % of dots moved), `snap-vg2` (39.6 %), `snap-cons2` (45.9 %); mean
  displacement 1.72–1.74 px, count fixed at 37,654, 2.828 px spacing floor held, all format and
  catalogue gates pass. Ledger status **`BUILT-DUPLICATE`**.
* **Verdict: corroborates PR #31, does not reopen the axis.** Under a different rule the result is
  the same: the movement carries no measurable signal. **Do not spend a slot on these three.**
* **What it does add — the proxy is blind (IR-86-SNAP-06).** With one fixed ≥ 3 px collar applied to
  every arm, the hide-and-recover proxy collapses to 0.0000 for the parent, all three variants *and*
  the SGMC control. From now on a proxy comparison is only admissible with the collar held fixed
  across arms; unpinned proxy numbers in earlier cards should be read as collar recovery.
* **Quantified cost of the edit.** The variants put 502 / 564 / 686 dots back inside the 200 m
  catalogue halo (parent: 0) and lift the share of dots within 300 m of a mapped fault from 4.28 % to
  5.4–5.8 %. They also drop the lineage's own ranking evidence from the 98.8th percentile of the
  restored H19-5 field to 69.7–75.1 — an independent, label-free reason to expect no gain.

### Third SNAP build (gain-gated, absolute-gravity) — same verdict, no slot requested

A third concurrent session built SNAP with an unsmoothed `tmi_hg`+`|iso_grav_anom_hg|`
percentile edge and a 0.10 gain gate: `snapr2g10` (17.5 % of dots moved, mean disp. 0.34 px,
**−0.001 MODEL**, status `BUILT-DUPLICATE`); its unconditional r1/r2 arms duplicate PR #31's
pairs and are withdrawn with no raster (IR-86-SNAP-09). Its one new instrument, the SGMC
off-catalogue control, degrades monotonically with snap dose (gated −0.0021, r1 −0.0032,
r2 −0.0089 SGMC-DTI) — a third instrument, same sign. **No slot requested for any of it;**
the plan above is unchanged. Cards: `evidence/r0-snap-mechanism.md`.

### Two axes this session proposes and did not build (neither is in the plan above)

1. **KERNEL-BUDGET (spacing floor at the kernel radius, count held)** — mechanism: 30.3 % of R0's dots
   sit within 3 px of another dot, so part of each dot's unit mass buys credit another dot already
   earns; re-spacing at ≥ 3.0 px at constant count converts wasted α into coverage. Confounder: real
   parallel strands and en-echelon step-overs are exactly 300 m apart, which is why the 2.828 px
   floor was chosen in the first place. Falsifier: live Δ ≤ −0.01, i.e. the deleted neighbour was a
   real second fault.
2. **RE-RANK (positions fixed, ranking changed)** — mechanism: hold every dot's position and re-decide
   which pixels inside the same 2 px neighbourhood enter the top 37,654, using a label-free
   fault-interaction prior (step-over / intersection / tip density from the Faulds inventory). This
   is the one SNAP-adjacent idea the negative result does *not* kill, because it never moves a dot
   away from the lineage's own high-value pixels. Confounder: those interaction zones are also where
   geothermal systems sit, and the target is fault pixels, never vents or heat. Falsifier: live
   Δ ≤ −0.01, which would say the H19-5 ranking is not separable from local geometry at all.

---

# Addendum — SPACING session (branch `arena/c8365759-gemsdoe86`), 2026-10-23

**AXIS: SPACING**, self-assigned from the plan because it is the only brief-§5 axis no earlier
session had built (`MASS`, `CONCENTRATION`, `SNAP`, `PRUNE`, `RELIEF` were all taken; `TRACKB` is
Phase 2). No slot was used or requested, and nothing here authorises an upload.

## What the axis says

Dose, preregistered before any surrogate was read: relocate every R0 dot owning ≤ 16 of the 29 cells
of its radius-3 px kernel disc — **7,228 dots, 19.20 % of the mass, 35.9–37.9 % of cells changed,
count fixed at 37,654**. R0's mean exclusive credit is 20.73 cells, i.e. **28.5 % of its nominal
kernel credit is already written off by overlap**, and 11,415 dots sit at exactly the 2.828 px
thinning floor — *inside* the 300 m kernel radius. Three placement laws, identical selection,
identical objective (largest gap to the nearest retained dot inside 800 m), identical exclusions:

| value | law | coverage bought | surrogate Δ (MODEL) | vs control |
|---|---|---|---|---|
| `pdisk16` | isotropic hard core (Poisson-disk / blue noise) | +113,315 px | **+0.0015** | +0.0013 |
| `lattice16` | hexagonal covering nodes, a = √3·R = 5.196 px (covering verified after rounding) | +107,851 px | **+0.0019** | +0.0017 |
| `strike16` | on the local dot ridge only (±1 px across, ≥2 px along) | +75,136 px | **+0.0020** | +0.0018 |
| `random16` | **null control**, uniform cell in the same window | +74,573 px | +0.0002 | — |

Every band is wide and every number is MODEL; the truth is an independent USGS SGMC off-catalogue
raster, not competition labels.

**The result that changes the plan.** The three laws beat the random control by ~+0.0016, so
*de-overlapping by a rule* pays where *moving at random* does not — the only clean law-vs-chance
separation any axis in this repo has produced. But (a) no arm approaches the 0.01 evidence floor,
(b) under a ±6 px translation of the truth (the 400 m flight-line uncertainty in brief §2) the
control itself rises to +0.0033 and the separation shrinks to ~+0.0016 of the laws' +0.0049, and
(c) 95–98 % of the coverage this axis buys is **off** the H19-5 support surface the lineage was
thinned from (IR-86-SPACING-02), so the surrogate may be paying for area, not for faults. The fold-fair
hide-and-recover PROXY in the same run card reads 0.0122–0.0153 for the arms against 0.0037 for R0,
which looks like corroboration and is not: only the arms got a fold-visible collar, so the instrument
is measuring the absence of the collar (IR-86-SPACING-05). It orders nothing in this plan.

## Slots, revised (one entity, 3 per rolling week; slots left: UNSUPPLIED)

| # | file | why | decision rule |
|---|---|---|---|
| 1 | unchanged: `…-PRUNE-le3p000-…-a438e92b-zeros.tif` (+0.004 MODEL) | the collar is still the only axis with a monotone ladder behind it, and it separates the two things SPACING cannot: mass vs catalogue proximity | as before |
| 2 | **either** `…-RELIEF-frontp15-…-e0e2888f-zeros.tif` (+0.0017) **or** `gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif` (+0.006) | both move mass between regions; the human picks which spatial prior to test first | as before |
| 3 | **replace the SNAP probe with `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif`** (+0.0020 MODEL) | SNAP's verdict is already established by three builds; SPACING `strike` is the one arm that (i) keeps its mass on the trace, (ii) is the only arm whose FP term does not jump (+83.7 vs +140), and (iii) arrives with its own control already built, so one slot buys a law-vs-chance read instead of a third measurement of a known negative | ≥ +0.010 → spacing is the binding error: build the global-dose rung (credit ≤ 20, 44 % of the mass) and pair it with `le3p000`; inside ±0.010 → the arrangement is not a lever and **SPACING closes for Phase 1**; ≤ −0.005 → the surrogate was buying off-fault area, close it and stop building arrangement axes |
| — | `…-sp-random16-…-db4cae83-zeros.tif` | **control, never a slot** — its only job is to make slot 3 interpretable | — |

If the human would rather spend slot 3 on `RELIEF front−10pct` (the sign flip, 25 %-of-mass swing,
predicted separation ~0.011), that comparison still has more power per slot than any single SPACING
arm, and it stays the alternative. Do not build `pdisk10`/`pdisk20` dose rungs this week: a
second dose of a below-floor axis is a repeat, not an experiment.

## What SPACING teaches the *other* axes

`SNAP`'s failure is now explainable without invoking geology: snapping moved 97–99 % of the dots and
**created** 3,448–8,341 sub-2 px pairs, i.e. it moved mass *into* overlap, while SPACING moves the
same mass *out* of it at a mean displacement of 6.8 px. Both are arrangement edits at the same scale,
and the one with a control reads positive-but-tiny. Practical consequence for weeks 4–6: any
combined finalist must hold **sub-kernel pair count** (currently 11,415) as a reported invariant, not
just dot count — a `le3p000 + conc15 + strike16` file that re-clusters would undo its own collar gain.

## New axis proposals (mechanism / confounder / falsifier) — not built this session

1. **DE-OVERLAP UNTIL SATURATED (count fixed, law fixed)** — keep relocating the most redundant dot
   until no dot owns fewer than *k* cells, for k = 20, 24, 29; a dose–response curve on the single
   quantity the metric's max operator actually charges for. *Mechanism:* T rises with union coverage,
   (S−M) falls as M → n. *Confounder:* past ~k = 24 the eligible ground is far from any ridge, so the
   dose and the abandonment of the parent's field are one variable (IR-86-SPACING-02). *Falsifier:* a
   monotone *decrease* in live score with k, which would say overlap is not waste but redundancy for
   mapping error — the physically respectable answer.
2. **PERPENDICULAR-WIDTH** — mirror image of SPACING's along-strike arm: hold the along-trace spacing
   and *widen across* it (2 → 3–4 px), testing whether the score wants a zone, not a line.
   *Mechanism:* new-fault truth is mapped as a zone of damage, one pixel wide in the label but wider
   in the ground. *Confounder:* the catalogue is pixel-exact-masked, so across-trace spreading
   re-enters the collar and interacts with PRUNE. *Falsifier:* live Δ ≤ −0.005 with
   `strike16` flat — the metric is line-shaped and the zone hypothesis dies with it.
3. **Human-supplied lidar DEM SNAP** — brief §5 allows lidar rasters for SNAP only if the human
   supplies them; none has been. The `lidar03` precedent (PROXY pass, live 0.1152) says do not gate on
   it. Not built, and unbuildable here: the pinned lidar mirrors are absent from this checkout.

## Human inputs still missing for this session

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation on the competition page ·
any submission-page receipt (R0's 0.2778 included) · which fill form the portal accepted ·
confirmation of the governing uniqueness rule (IR-86-PRUNE-01) · and, if slot 3 is to be spent on
SPACING, whether the human accepts a **predicted +0.002** probe whose real purpose is a law-vs-chance
test rather than a score improvement.

---

# Addendum — MASS (kernel-budget) session, branch `arena/c6b14099-gemsdoe86`, 2026-10-23

**AXIS: MASS**, self-assigned because the brief's literal MASS arms are already spent and both lost.
No slot was used or requested. Three arms + one control were built on R0, all at the brief's 10 %
dose (9.9989 % of R0's dots changed each), all gate-clean in both encodings:

| file (`releases/mass86/…`) | n | change | MODEL | verdict |
|---|---|---|---|---|
| `…-MASS-minus10pct-marginal-20261023-c3936cfc-zeros.tif` | 33,889 | −3,765 dots by lowest unique kernel credit | −0.0051 | **no slot**: the metric's removal bar (0.0588 × FP charge) is below every dot's unique credit |
| `…-MASS-plus10pct-extend-20261023-3b708da1-zeros.tif` | 41,419 | +3,765 at 3–6 px along the local trace | +0.0066 | **no slot** by itself: equals the instrument's price of generic mass |
| `…-MASS-plus10pct-extend-rand-20261023-37fab392-zeros.tif` | 41,419 | same window, uniform draw | +0.0071 | **CONTROL**, never a slot |

## The result that changes the plan

**The MODEL instrument is monotone in dot count.** A symmetric random add/delete ladder reads
−0.0127 / −0.0068 / −0.0030 / +0.0018 / +0.0040 / +0.0081 for −20/−10/−5/+5/+10/+20 %
(`evidence/mass_instrument_monotonicity.json`). Every MODEL delta published in this repo for a
**mass-changing** artefact is therefore partly a mass reading, and none of them — including this
session's +0.0066 — may be promoted on that instrument. The count-fixed axes (CONCENTRATION,
RELIEF, SPACING) are unaffected: their reads are computed at constant `n`, so the instrument's mass
bias cancels in the comparison.

Cause: the SGMC surrogate credits only 8.4 % of its own truth inventory, while the incumbent's
0.2778 implies 23–48 % coverage for plausible new-fault truth sizes. A map covering a tenth of the
truth has a large marginal appetite for dots; the live one does not.

**MASS is closed in both directions**, and for the second time on stronger grounds:

* *drop* — the metric's own two-sided test forbids it: removal pays only if a dot's unique truth
  credit is under `0.2·DTI/(1 − 0.2·DTI)` = 0.0588 kernel units times its false-positive charge.
  R0's dots have unique credit 1.49–9.38 (mean 6.79; overlap write-off 27.6 %).
* *add* — unimplementable as specified. Only **733 of 121,131** cells of the parent's own field
  support are ≥ 3 px from every dot (99.4 % saturated), so a field-ranked 10 % add is either
  redundant (measured −0.006) or unranked. Non-redundant additions can only come from the parent's
  geometry, and they read like noise (+0.0066 vs +0.0071 for a random twin).

## Slots, revised (one entity, 3 per rolling week; slots left: UNSUPPLIED)

| # | file | why | decision rule |
|---|---|---|---|
| 1 | **`releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif`** (+0.0017 MODEL, count fixed) | after this session's audit, the *only* built artefacts whose predictions survive an instrument that cannot be explained by mass are the count-fixed relocation pair. This is the positive half | ≥ +0.010 → spatial allocation, not pruning, is the lever: next build RELIEF-ADD and the PRUNE combination |
| 2 | **`…-RELIEF-frontm10-20261023-1b26223e-zeros.tif`** (−0.0089 MODEL, count fixed) | the sign flip, and the only built comparison whose predicted separation (~0.011) clears the floor. Slot 1 and 2 together are one experiment with power; either alone is not | the pair straddles 0 → relocation is a real axis; build the 5 km dose. Both inside ±0.010 → RELIEF closes and so does the arrangement family for Phase 1 |
| 3 | **`releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`** (+0.004 MODEL) | the deepest collar rung. Kept third now, not first: its own prediction was measured on a catalogue-truth surrogate while the edit deletes catalogue-adjacent dots, so part of its +0.004 is structural, not geological | ≥ +0.010 → the collar is not exhausted (4 px rung). Flat or worse → PRUNE closed for Phase 1 |

**Do not spend a slot on any of this session's three files**, nor on `massminus10` / `massplus10`
(both now explained by the mass curve), nor on the SNAP builds (three independent negatives), nor on
the SPACING arms (law-vs-chance separation +0.0016, below floor). If the human wants a *single*
informative slot rather than a pair, spend it on slot 1 and expect a reading, not a gain.

## New axis proposals (mechanism / confounder / falsifier) — not built

1. **FRESH-TERRITORY ADD (count up, prior from the trace, judged only by the *difference* against
   its random twin)** — the one surviving question from this session: +3,765 non-redundant dots are
   neutral-to-mildly-positive on an instrument that over-prices mass, and → 0 live if the parent's
   field is exhausted. *Mechanism:* T rises where the map has no mass at all. *Confounder:* the
   instrument's mass monotonicity, which only a paired read can cancel. *Falsifier:* the trace arm
   performing worse than its own random twin on a live pair (would also close the halo question).
2. **COVERAGE-MATCHED PRUNE (count down, *coverage* held)** — delete dots whose disc is covered by
   others *and* whose removal leaves no cell more than R from the retained set. Difference from
   this session's drop arm: it protects `M` as well as `T`, so it is the only deletion rule the
   metric's FP charge cannot punish. *Confounder:* it selects dots at the field's fringe, which is
   where PRUNE already operates. *Falsifier:* live ≤ −0.005 with PRUNE flat.
3. **AMPLITUDE (values below 1 on the least-supported dots) — proposed and analytically dead.** A
   fractional value `v` scales a dot's numerator and denominator contributions alike, so the sign of
   its marginal effect does not depend on `v`; and the max operator makes two half-dots strictly
   worse than one. Do not build it without a new argument.
# Addendum — CONCENTRATION sign experiment (branch `arena/c1df93fc-gemsdoe86`), 2026-10-23

**AXIS: CONCENTRATION**, self-assigned: it is the only brief-§5 axis whose built arm (`conc15`,
PR #37, +0.006 MODEL) is a *spatial-prior* claim, and that arm's own falsifier asks for this exact
build ("≤ −0.010 → build the spread variant instead"). Three gate-clean files, count fixed at
37,654, 5,648 dots (15.00 %) relocated at 1 km blocks, 29.999 % of cells changed, every
placement at the parent's 2.828 px floor, new mass ≥ 3 px off the catalogue, min clearance
2.236 px, 0 dots on catalogue. **No slot used or requested; no new slot is proposed from this
axis this week.** Cards: [evidence/concentration-sign-mechanism.md](evidence/concentration-sign-mechanism.md);
run card: `evidence/concentration_sign_20261023.json`.

| arm | file (`-zeros` twin is the upload) | prediction (MODEL) | role |
|---|---|---|---|
| `spr15` | `releases/sign86/gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif` | **−0.030** (−0.064…+0.011) | candidate: the sign flip |
| `dens15` | `releases/sign86/gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif` | **+0.026** (−0.011…+0.047) | candidate: mirror, band-free prior |
| `rand15` | `releases/sign86/gems86-h33-2b2-concrand15-20261023-fcbae067-zeros.tif` | −0.014 | **CONTROL, never a slot** |

## What this session changes in the plan

1. **The magnitude class changes.** Every axis built so far predicted |Δ| ≤ 0.006. This one's
   truth-model panel spans **−0.064…+0.047** on the same 15 % dose: the concentration *sign* is
   worth up to an order of magnitude more than any arrangement or collar edit. It is also the
   only axis whose predicted sign is set by an *assumption* (where new-fault truth sits) rather
   than by the file, so one slot on it buys a decision, not a tweak.
2. **The instruments cannot settle it, and now we can say why.** Hide-and-recover, the SGMC
   off-catalogue DTI and the H19-5 support surface are all built from the same mapped-fault
   record that the competition *masks* at scoring time. They are structurally biased toward
   "mass near mapped faults" — which is `conc15`'s direction. This session therefore does not use
   them to rank arms; it uses a five-truth-model panel and reports the sign flip explicitly.
3. **The CV band claim is degenerate at 10–20 % dose.** CV is non-monotone in dose (0.5970 at
   5 %, 0.6136 at 15 %, 0.6722 at 30 %) and *every* arm — spread included — concentrates mass
   into fewer blocks, because destinations are a fixed fifth of the occupied blocks. The reported
   0.51–0.59 band is only reachable at ≈5 % dose with mass placed in currently **unoccupied**
   low-prior blocks, which is the placement `GEMSDOE81` `cont-poisson44090` (**0.0041 CLAIM**)
   already shows can collapse the score. Treat the band as a CLAIM that the plan cannot test.

## Next three slots, in order (unchanged slot 1; slots 2–3 re-ordered)

| # | file | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | still the only prediction that is positive **and** sits on a monotone, live-backed ladder: the collar is the one lever in the ledger with a live step behind it (0.2708 → 0.2778 after the ≤ 2 px prune). Prediction **+0.004 MODEL** | ≥ +0.010 → the collar is not exhausted, next week a 4 px rung. Inside ±0.010 → PRUNE closes for Phase 1 with its direction confirmed |
| 2 | `releases/sign86/gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif` | **+0.026 MODEL**, the largest predicted effect available, it replicates `conc15`'s direction with a prior that needs no absent feature stack, and it is the arm all three local instruments agree with — so a receipt here is the first *independent* confirmation of the catalogue prior | ≥ +0.010 → the concentration axis is binding: the final file is `le3p000` + `dens15` as one attributable edit. Inside ±0.010 → the prior is worth nothing measurable; do not spend slot 3 on the mirror, take SPACING `strike16` instead. ≤ −0.005 → the instruments are circular: slot 3 must be `spr15` |
| 3 | `releases/sign86/gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif` **only if** slot 2 lands ≤ −0.005 or inside ±0.010 with the human wanting the sign resolved; otherwise `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif` (+0.0020 MODEL, with its own null control already built) | the pair (slot 2 up, slot 3 down, or the reverse) is the only comparison in this repo that can separate "near mapped faults" from "unmapped ground" with two live numbers, and its predicted separation is ~0.05 | opposite signs → the prior is the lever: build the *mixture* rule (destination prior × kernel-gap) next. Both inside ±0.010 → the catalogue prior is dead for Phase 1; the remaining weeks go to the collar rungs and to one SNAP-style probe, and the final file stays R0-derived |

**Do not spend a slot on** `rand15` (control), `spr30`/`dense30` dose rungs (the CV curve above
shows 15 % is already past the CV minimum), or a second `conc15`-family arm without its mirror.

## Better axes (mechanism / confounder / falsifier) — proposed, not built

1. **SUPPORT-BOUNDED DE-CLUSTER** — relocate only *within* a dot's own 1 km block (largest gap
   inside the same block). Isolates the overlap mechanism from the prior mechanism, so a flat
   result would say block-scale arrangement is not a lever at all, independent of any prior.
   *Confounder:* it cannot change CV at all (block counts are invariant), so it tests the kernel
   budget only. *Falsifier:* live Δ inside ±0.005 with `strike16` also flat → arrangement axes
   close together.
2. **CV-TARGETED SPREAD at 5 % dose into unoccupied blocks** — the only dose/destination pair
   that reaches the reported 0.51–0.59 band. *Confounder:* far-field placement is exactly the
   `cont-poisson44090` collapse (0.0041), so the arm risks a −0.27 tail. *Falsifier:* live
   Δ ≤ −0.01 → the band is a property of the files that scored well, not a cause of it.
3. **PRIOR-MIXTURE** — destination score = z(catalogue prior) − z(distance to the lineage's own
   support), i.e. put mass where *both* the mapped record and the geophysical field agree.
   *Confounder:* the field itself was thinned from the same lineage, so agreement may be
   circular. *Falsifier:* no separation from `rand15`.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation on the competition page
· any submission-page receipt (R0's 0.2778 included) · which fill form the portal accepted ·
confirmation of the governing uniqueness rule (IR-86-PRUNE-01) · **and, before slot 2, whether the
human accepts a predicted +0.026 whose sign rests on "new faults sit near mapped traces"**.
