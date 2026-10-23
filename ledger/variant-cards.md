# Variant cards — PRUNE axis on R0 (built 2026-10-23)

Parent **R0** = `h33-h33-2-b2-20261004-e5eb6e7e` (GEMSDOE32), 37,654 dots,
sha256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`,
parent dot-set digest `905cee9d4383de23d6ee6366da4627fe19a78e4f49ce3a2462a8736e9b66a027`.
R0's 0.2778 is a **CLAIM** (owner report, no submission-page receipt). Nothing below is a score.

The parent's support is reproduced **pixel for pixel** from pinned bytes: take the
0.2708 field's 40,199 dots and delete every dot whose Euclidean distance to a mapped-fault
cell is ≤ 2.0 px → 37,654 dots, **0 differing pixels**. The parent's *file bytes* are not
reproducible (see IRREGULARITIES.md IR-86-PRUNE-01), so every candidate carries a dot-set
digest as well as a sha256.

R0's surviving dots sit in exactly three distance shells, so the whole axis has three
remaining rungs: **941 dots at d = √5 ≈ 2.236**, **670 at d = √8 ≈ 2.828**, **560 at d = 3.0**.
There are no dots at d ≤ 2 (removed in R0) and none at d = 1 or √2 in the base field at all.

All four rasters: EPSG:32611, 3730×3292, transform (100, 0, 243350, 0, −100, 4508550),
float32, one band, values in {0, 1}, zero mass on the catalogue, re-read from disk after
writing, and `gems57.validate` + `gems57.gates.format_report` pass on every `-zeros` twin.

| id | dots | removed vs R0 | predicted Δ live (MODEL) | zeros sha256 |
|---|---:|---:|---|---|
| `…-PRUNE-le2p236-20261023-444eb3b0` | 36,713 | 941 (2.50 %) | **+0.001** [−0.003, +0.003] | `444eb3b0…` |
| `…-PRUNE-le2p828-20261023-e475963d` | 36,043 | 1,611 (4.28 %) | **+0.003** [−0.003, +0.008] | `e475963d…` |
| `…-PRUNE-le3p000-20261023-27c5eab6` | 35,483 | 2,171 (5.77 %) | **+0.004** [−0.004, +0.013] | `27c5eab6…` |
| `…-CONTROL-massctl2171-20261023-99190068` | 35,483 | 2,171 far-field (5.77 %) | **0.000** [−0.004, +0.003] | `99190068…` |

How the MODEL number is built, stated so it can be attacked: the only live datum on this
axis is 0.2708 → 0.2778 for deleting 2,545 collar dots, i.e. **+2.75 × 10⁻⁶ per dot**, which
is one order of magnitude *above* the metric's own zero-credit estimate (≈ 0.2·DTI/D ≈ 10⁻⁶
per dot at DTI ≈ 0.28) and therefore partly a coverage effect, not a pure false-positive
effect. Linear extrapolation of that rate gives +0.0026 / +0.0044 / +0.0060. The central
figures above halve it for expected saturation; the linear end is the top of each band.
Both inputs to the rate are CLAIMs, so the whole prediction is a MODEL.

---

### 1. `PRUNE ≤ √5` — remove the knight-move shell (941 dots)

- **Hypothesis.** The 941 dots at exactly (2,1) offsets are residue of an emission that put mass on the mapped trace and had it deleted; they are close enough to the catalogue to be collateral, far enough to earn almost no credit.
- **Mechanism.** These dots are the innermost survivors of R0's collar. If the useful boundary is set by geometry (a 100 m grid artefact of deleting on-catalogue pixels) rather than by geology, deleting one more shell lowers the false-positive mass without touching new-fault coverage.
- **Non-fault process that would mimic it.** A genuine unmapped parallel strand 200 m from a mapped trace: the 400 m GeoDAWN flight-line spacing makes a 100–200 m offset indistinguishable from a digitising offset, so the same 941 dots could be the only cover of real truth. This is the mimic with the highest prior — the organizer has confirmed new-fault truth may lie within 300 m of known traces.
- **Predicted sign and size.** +0.001 (MODEL, 90 % band −0.003…+0.003); below the 0.01 evidence floor either way.
- **Falsifier.** A live change below −0.003 says the knight shell was real cover and the collar optimum is *inside* 2 px — then stop pruning and test R0's complement (add back the ≤2 px ring) instead. A change above +0.006 says the 2 px prune was not a fluke and the ladder should jump two rungs.

### 2. `PRUNE ≤ √8` — remove √5 and √8 shells (1,611 dots)

- **Hypothesis.** The collar effect is graded, not a step at 2 px: the dots at 2–2.83 px are the next most redundant.
- **Mechanism.** Same as (1), one shell further out. At 2.83 px a dot still earns kernel credit 0.06 against a truth pixel 3 px away — the marginal-inclusion bar (`credit > 0.2·DTI ≈ 0.056`) — so this is the *last* shell that can pay for itself at all. Anything beyond 3 px cannot earn credit from a fault known only within 300 m of the catalogue.
- **Non-fault process that would mimic it.** Same parallel-strand mimic, but the expected loss is smaller because kernel credit at 2.83 px is already near the bar.
- **Predicted sign and size.** +0.003 (MODEL, band −0.003…+0.008).
- **Falsifier.** If this and `≤3.0` score *below* `≤√5`, the effect is monotone-negative beyond √5 and the collar optimum is proven to be 2–2.83 px; if all three are flat within ±0.003, the axis is saturated and no further slot belongs to it.

### 3. `PRUNE ≤ 3.0` — clear the entire kernel radius (2,171 dots)

- **Hypothesis.** New-fault truth in the scored chunks is not hugging the masked catalogue, so every dot within the 3 px kernel radius is dead weight.
- **Mechanism.** The strongest version of the collar argument: after this edit the nearest dot to any mapped fault is 3.16 px away, so no dot's credit can come from a fault the catalogue already contains. It is also the sharpest test of the organizer's statement that new-fault truth *can* be within 300 m of known traces — if that statement describes the scored chunks, this variant must lose.
- **Non-fault process that would mimic it.** Expert-mapped extensions of known systems (step-overs, splays, tip damage zones) that the catalogue truncates: those are exactly the truth pixels a 3 px clearance deletes cover for. Also, the *mass* drops 5.8 % at the same time, so a gain here is not automatically a collar gain — that is what the control is for.
- **Predicted sign and size.** +0.004 (MODEL, band −0.004…+0.013). Highest variance of the three.
- **Falsifier.** Live ≤ R0: the collar is exhausted at 2 px, and the prune lineage stops. Live ≥ +0.010: the per-dot rate is *not* saturating and a 4–5 px prune is the next slot. If this and the control move by the same amount, the mechanism is mass, not proximity to the catalogue.

### 4. `CONTROL` — same mass, no collar (not for submission)

2,171 dots drawn uniformly at random (seed 86) from R0's dots **more than 3 px** from the
catalogue. It answers the one question that would otherwise be unresolvable: does deleting
5.8 % of the mass move the live score by itself? Predicted 0.000 (band ±0.004). It is a
measuring instrument, never a slot: it is labelled `BUILT-CONTROL` in the ledger.

---

# RELIEF axis, 2026-10-23 (this session; AXIS assigned by the human)

Parent `h33-h33-2-b2` (R0, 37,654 unit dots, **0.2778 CLAIM**, rebuilt byte-exactly here:
`c55bafc4…b6fa9`, 0 differing pixels). One signed edit on one axis: **relocate** a stated
fraction of R0's dots between relief regimes, count and unit mass fixed. Regimes are terciles of
`z(smoothed det_elev) + z(smoothed |det_elev_slope|)` over the footprint (bands 12 and 19 of the
pinned 19-band stack, 3.1 km box smoothing); the top class is then split by proximity to a basin
cell, because a *range front* is a basin-margin scarp — high-index cells farther than 5 km from
any basin are range interior and are excluded from both the source and the destination sets.

Measured on R0, before any edit: piedmont **53.86 %** of the mass, range-front **16.05 %**,
range-interior 24.74 %, basin **5.35 %**. Independent corroboration (USGS SGMC fault pixels that
are *not* in the training catalogue, 79,615 of them) is distributed almost the other way:
34,565 px/Mpx at the front and 27,886 in the interior against 12,944 in the piedmont and 2,704
in the basin; 29.6 % of front dots sit within one kernel radius of such a pixel against 15.5 % of
piedmont dots. That contrast is the whole reason this axis was built — the parent's mass sits
where the middle-ground mapping is densest, not where an independent inventory says the
un-mapped population is thickest.

All three files: same count (37,654), zero mass on catalogue pixels, every new cell ≥ 3 px from
the catalogue **and** ≥ 2.83 px from every other dot (the parent's own minimum), min nearest-
neighbour preserved at 2.8284 px, deterministic (seed-free; ties by flat index).

### 1. `RELIEF front+15pct` — 5,648 dots moved piedmont → range-front (e0e2888f)

- **Hypothesis.** R0 under-weights the basin-margin range front; pushing 15 % of the mass from
  the deep middle tercile onto the front raises the live score, because the front band carries
  2.7× the per-pixel density of independently-mapped, catalogue-absent faults.
- **Mechanism.** In the Basin and Range, Quaternary strain localises on range-bounding
  structures. Their master traces are in the catalogue and are masked pixel-exactly, so they can
  earn nothing — but the splay, tip-zone and step-over population around them is exactly what
  "new fault" means here (forum 11536). R0 was thinned *away* from the trace by the 2 px collar
  and then spread by a field that favours the open piedmont, leaving the escarpment band at 16 %
  of the mass. Relocation keeps the count, so nothing else in the DTI denominator moves: only the
  regime that each relocated dot's 300 m kernel now samples changes. Sources are the dots
  *deepest inside* the piedmont (median 17 px from their own regime boundary), so a moved dot
  genuinely changes terrain setting — mean displacement 61 px (6.1 km), median 46 px.
- **Non-fault process that could mimic it.** Range-front magnetic and gravity lineaments are
  frequently lithologic contacts and fan-edge/alluvial-apron boundaries rather than faults. Worse,
  the SGMC density gradient used to pick the direction partly measures where a geologist can see
  bedrock: mapping completeness rises with relief, so a front gain could be a *mapping-bias* gain
  and not a truth gain. At the 400 m GeoDAWN line spacing the position uncertainty is of the same
  order as the kernel radius, i.e. as the whole effect.
- **Predicted sign and size.** **+0.0017 (MODEL)** on the SGMC-extra surrogate, quadrant range
  −0.0022…+0.0112, sign positive in 3/4 quadrants. Below the 0.01 evidence floor: this file buys
  a *direction*, not a result. The displacement-matched in-regime control costs −0.0010 on the
  same surrogate, so the net regime effect is ~1.7× the cost of moving at all — thin.
- **Falsifier.** Live ≤ −0.005 against R0: the front population is already covered (saturation,
  not sparsity), and the relocation pays only its displacement cost — then RELIEF closes for
  Phase 1 and the front idea survives only as an *insertion* test (proposal 1 below). Live
  ≥ +0.010: the curve is unsaturated and the next dose is 25–30 %.

### 2. `RELIEF front+10pct` — 3,765 dots, a strict prefix of rungs above (b20ef72e)

- **Hypothesis.** Same direction at two thirds the dose; the point is the **slope**, not the file.
- **Mechanism.** Selection is dose-ordered by boundary depth, so this dot set is exactly the first
  3,765 of `front+15pct` (asserted in the run card: `ladder_nesting.front5_is_prefix_of_front10`,
  nesting verified programmatically). Two nested rungs on one signed axis are what turn a single
  number into a curve.
- **Non-fault process that could mimic it.** Identical to (1); additionally, mean displacement here
  is *larger* than in (1) (67 px vs 61 px) because the extra 5 % of the big dose comes from
  shallower, nearer-boundary piedmont dots — a lower dose is the more aggressive edit. Any reader
  comparing the two files must not interpret the displacement difference as a mechanism.
- **Predicted sign and size.** **+0.0010 (MODEL)**, quadrant range −0.0009…+0.0068, 3/4 quadrants
  positive. Predicted *smaller* than (1): surrogate Δ scales with dose (0.0010 → 0.0017 ≈ 0.67
  ratio for a 0.67 dose ratio), which is what a linear, unsaturated response looks like.
- **Falsifier.** If this beats `front+15pct` live by ≥ 0.005, the response is sub-linear in dose —
  saturation below 15 % — and no larger front dose should be built.

### 3. `RELIEF front-10pct` — 3,765 dots moved range-front → piedmont, the sign flip (1b26223e)

- **Hypothesis.** The null of this axis: the same magnitude of change with the sign reversed. If
  regime membership matters, removing front mass must cost roughly what adding it gains.
- **Mechanism.** Sources are the deepest front dots (median depth 6.4 px), placed on the nearest
  legal piedmont cells (mean displacement 13 px — much smaller than (1), because the front band is
  narrow and wedged between piedmont on one side and interior on the other). Front share
  16.05 % → 6.06 %, piedmont 53.86 % → 63.86 %.
- **Non-fault process that could mimic it.** A *reduction* in false-positive mass, since the front
  is where a dot's kernel most often lands on masked catalogue pixels; the variant could gain for
  a reason that has nothing to do with relief (it drops 246 dots from the 2–3 px collar band as a
  side effect of relocating front mass — 2,171 → 1,925).
- **Predicted sign and size.** **−0.0089 (MODEL)**, quadrant range −0.0160…−0.0009, sign negative
  in 4/4 quadrants — the only variant on this axis whose surrogate sign replicates everywhere.
  Paired against (1) it is a 25 %-of-mass swing with a predicted separation of ~0.011, i.e. the
  one comparison on this axis that could clear the 0.01 floor.
- **Falsifier.** A live *gain* here means the piedmont is over-weighted in the parent and the
  front mass is redundant — then the next edit is a *deletion* of front mass (a PRUNE-shaped edit
  on the front, already a spent pair, so it must be a new value such as "front−25 %"), not a
  relocation.

**Not built, deliberately:** `front+5pct` (sub-noise by projection: half of +10 %), the 4 px/
20 %+ rungs (outside the 10-15 % the axis contract allows), and any regime shift that also edits
the 2–3 px collar (that is PRUNE, spent three times over — IR-86-PRUNE-08).

## Better axes this session found (proposals only, per brief §5; not built)

1. **RELIEF-ADD.** *Insert* 5,648 front dots (37,654 → 43,302) instead of relocating them.
   *Mechanism:* with a max-kernel numerator, a dot that already covers a truth pixel cannot be
   improved by moving it, only by adding a new one — so relocation structurally pays a
   ~0.001 displacement cost (measured control) that insertion does not. 43,302 stays inside the
   37–44k band the best files occupy, bounding the mass confound. *Confounder:* mass versus field
   (brief §3). *Falsifier:* no gain while `front+15pct` gains ⇒ the front is saturated, not sparse.
2. **Combine-front-collar.** `front+15pct` ∧ `le3p000` as one file: the only two single-edit files
   on the incumbent whose parents' effects are separable, because both singles exist.
   *Confounder:* the two edits touch the same pixels (2,171 → 1,925 overlap). *Falsifier:* combine
   gains less than the better single ⇒ the effects are not additive and Phase 2 needs one lever.
3. **Annulus-conditional RELIEF** (from the earlier ladder plan, unchanged): test the 200–300 m
   annulus per relief tercile rather than moving whole populations. *Confounder:* relief controls
   both catalogue completeness and lineament visibility. *Falsifier:* no consistent sign across two
   relief regimes on untouched spatial folds ⇒ no live slot.
