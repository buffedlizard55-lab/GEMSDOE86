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

# SNAP axis — 2026-10-23 (parent R0 = `h33-h33-2-b2`, 37,654 dots)

All three variants move dots and nothing else: identical count, identical unit mass, identical
catalogue exclusion (`d_cat > 2 px`, the parent's own rule), no dot created or deleted. The
response surface is the rank-normalised weighted mean of the two pinned gradient bands
(`tmi_hg` = band 3, `iso_grav_anom_hg` = band 18); a dot may land only on the strongest free
cell inside its window. Evidence: `evidence/snap_axis_20261023.json`.

**The instrument result that governs all three.** The response is spatially smooth (lag-1
autocorrelation **0.978**), yet **97–99 % of R0's dots move**, i.e. the incumbent field sits
1–2 px off the strongest potential-field gradient almost everywhere. A **null control** — the
identical snap driven by a *random* response over the same window — moves 91 % of the dots and
scores proxy Δ **−0.0012**; the real response scores **+0.0001**, and a σ=1 smoothing of it
**−0.0018**, σ=2 **−0.0032**. The catalogue hide-and-recover PROXY therefore cannot tell these
snaps apart from a random walk inside the window. Every arm's proxy lies within ±0.003 of the
control, on an instrument whose absolute value (0.0044) is at its floor (IR-86-PRUNE-03).

### 1. `SNAP ≤ 1.0 px`, mixed response (96.9 % of dots moved, mean move 1.00 px)
- **Hypothesis.** R0's dot *positions* — not its dot *density* — are the binding error, and one
  grid step of re-centring on the TMI/gravity edge recovers kernel credit without losing coverage.
- **Mechanism.** DTI credits a dot with `k = max(1−d/3,0)`; a 1 px correction to a dot 1 px off
  the trace raises `k` 0.667→1.0 and lowers `FP_w` by the same amount. The 4-neighbour window is
  the smallest admissible perturbation, so this is the arm with the least coverage cost.
- **Non-fault process that could mimic it.** Pixel-scale specular structure in a 400 m-spaced
  aeromagnetic survey (flight-line corrugation) produces ridges that are *not* geology; snapping
  to them is a random walk with extra clustering. Measured clustering cost: dots closer than
  2 px to a neighbour 0 → **3,448**; mean nearest-neighbour 3.735 → 3.522 px.
- **Predicted sign and size.** **−0.004** (MODEL, band −0.012…+0.004). The optimistic algebra
  bracket (+0.000…+0.086) is reported and *not* used: the null control removes the reason to
  believe the hit rate exceeds chance.
- **Falsifier.** Live Δ > +0.01 with `le3p000` flat → positions were the binding error and the
  2 px arm should confirm with a larger gain. Live within ±0.01 of the null-only expectation
  → the axis is a no-op and no further SNAP slot is spent.

### 2. `SNAP ≤ 2.0 px`, mixed response (98.4 % moved, mean 1.79 px) — the main bet
- **Hypothesis.** The full positional uncertainty implied by the survey geometry
  (400 m line spacing, 150–200 m terrain clearance; GeoDAWN Area 2, USGS data release) is
  ≈1 line spacing ≈ the kernel radius, so a 2 px search window is the geologically motivated one.
- **Mechanism.** As above, with a 12-cell window: a dot 2 px off the trace earns 0.33, centred 1.0.
  This is the arm where the mechanism has the most room to pay.
- **Non-fault process that could mimic it.** Speckle-chasing plus convergence: 2 px moves make
  8,341 dots sit within 2 px of another dot (0 in R0), which raises the mutual redundancy term
  `M` and destroys coverage without adding truth credit. Also, any edge that is a *lithological
  contact* rather than a fault pulls dots onto itself and away from the true trace.
- **Predicted sign and size.** **−0.006** (MODEL, band −0.020…+0.006).
- **Falsifier.** A live gain > +0.01 here (with arm 1 positive) is real positional information;
  a gain only in the smoothing sweep (not built as a raster) would mean coherence, not amplitude,
  is the signal and the next slot should carry a structure-tensor response instead.

### 3. `SNAP ≤ 2.0 px`, `iso_grav_anom_hg` only (99.8 % moved, mean 1.95 px)
- **Hypothesis.** Decomposition of arm 2: if magnetic relief carries the positional information,
  a gravity-only response must lose most of arm 2's (hypothetical) gain.
- **Mechanism.** Isostatic gravity responds to density contrasts at greater depth and is far less
  contaminated by flight-line corrugation than TMI; it is also the band with the higher measured
  percentile at R0's collar (`iso_grav_anom_hg` 0.557 vs 0.514 elsewhere, PR #29's measurement).
- **Non-fault process that could mimic it.** Basin-fill / basement contacts and isostatic
  compensation edges, which are regional and low-frequency: they pull dots onto broad gradients
  rather than lineaments. This arm clusters least (dots < 2 px apart 0 → 2,085).
- **Predicted sign and size.** **−0.004** (MODEL, band −0.016…+0.006).
- **Falsifier.** Arm 3 ≥ arm 2 by > 0.01 live: the magnetic gradient is the confounded band and
  the next SNAP-family build should use gravity only.

### Null control (never a slot, no raster)
Random response, identical window and landing mask, seed 86: 91.3 % moved, mean 1.45 px,
proxy Δ −0.0012 [−0.0013, −0.0011]. It exists so that any SNAP result can be read against the
"the window itself costs coverage" baseline rather than against zero.

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

---

## CONCENTRATION (5 km ridge-supported & CV-band sign flip, 2026-10-23, `arena/69392a35-gemsdoe86`)

Full mechanism cards & PR #37 forensic audit: `evidence/concentration-5km-mechanism.md`; run card: `evidence/concentration_5km_axis_20261023.json`.

### 1. `CONCENTRATION b5km-cvband-down4` — 1,506 dots moved (`7.9992%` changed, `8aab97b6`)
- **Hypothesis & Mechanism.** Shaves 1,506 lowest-unique-credit dots off `>= 3`-dot 1 km clusters onto unused `H19-5 | H19-4 | H16-1` ancestor ridges (`> 3.0 px` off catalogue, `>= 2.828 px` spacing) in sparse `1–2`-dot blocks, bringing occupied 1 km block-density CV from `0.6235` down to **`0.5162`** (inside the `0.51–0.59` historical top-scorer band) at fixed count `37,654`.
- **Non-fault mimic.** Intrabasin pluvial-lake (Lahontan) shorelines, basalt flow margins, and alluvial-fan scarps.
- **Predicted sign and size.** **`+0.0015 MODEL`** on off-catalogue SGMC (`+0.0020` under `±6 px` jitter, **4/4 quadrants positive** `+0.0001..+0.0024`), symmetric fold-fair **`+0.0008 PROXY`** (`95% CI [-0.0004, +0.0018]`, `n = 11,321`). Only `CONCENTRATION` arm positive on both instruments (beats PR #37's `b1km-move15`, which measures `-0.0071 MODEL`, by `+0.0086`).
- **Falsifier.** Live `Δ <= -0.005` vs R0: proves unmapped faults cluster tighter than `CV = 0.6235`.

### 2. `CONCENTRATION b5km-ridge-up8` — 3,012 dots moved (`15.9983%` changed, `b4d36a67`)
- **Hypothesis & Mechanism.** Reallocates 3,012 dots (`8.00%`) from lowest-scoring 5 km Faulds fault-interaction blocks (mapped + ridge skeleton tips/junctions + 10.1 km local-RMS AGC `|\nabla TMI_up150|`) onto unused ancestor ridges (`> 3.0 px` off catalogue) in top-35% 5 km blocks, count fixed at `37,654`.
- **Non-fault mimic.** Quadrangle 1:24k mapping density in mineralized bedrock ranges; caldera/intrusive contacts.
- **Predicted sign and size.** **`-0.0007 MODEL`** (`2/4` quadrants positive; matched random-5km-block control `-0.0008 MODEL`), symmetric fold-fair **`-0.0026 PROXY`** (`95% CI [-0.0083, +0.0018]`). Do not spend a slot.
- **Falsifier.** Live `Δ >= +0.010` vs R0.

### 3. `CONCENTRATION b5km-ridge-up4` — 1,506 dots moved (`7.9992%` changed, `493cf242`)
- **Hypothesis & Mechanism.** Strict nested half-dose prefix (`src4 == src8[:1506]`, `dst4 == dst8[:1506]`) of `b5km-ridge-up8`, paired at identical `1,506`-dot magnitude against `b5km-cvband-down4`.
- **Non-fault mimic.** Same quadrangle mapping and volcanic/intrusive contact mimics at half dose.
- **Predicted sign and size.** **`-0.0005 MODEL`** (`2/4` quadrants positive), symmetric fold-fair **`+0.0002 PROXY`** (`95% CI [-0.0026, +0.0027]`). Do not spend a slot.
- **Falsifier.** Live `Δ >= +0.005` while `b5km-ridge-up8` is negative.


---

## CONCENTRATION (10 km fault-system scale, 2026-10-23, `arena/a681fdaf-gemsdoe86`)

Full cards: `evidence/concentration-10km-mechanism.md`; run card: `evidence/concentration_10km_axis_20261023.json`; pre-registration: `registry/preregistration_conc10.json`. All count-fixed at 37,654, 100 % of new dots on ancestor ridges at > 3.0 px clearance (min 3.162 px), block = 100 px. R0 occupied-density CVs: 1 km 0.6235 · 5 km 0.7442 · 10 km 0.7360 (IR-86-CONC-12 corrects the 0.570 figure in IR-86-TRACKB-08).

### 1. `CONCENTRATION b10km-down8` — 3,012 dots moved (`15.9983%` changed, `780f8509`)
- **Hypothesis & Mechanism.** Disperse the lowest-unique-credit dots of the densest occupied 10 km blocks onto unused ancestor ridges in the sparsest 65 % of occupied 10 km blocks: occupied-10 km CV 0.736 → **0.496** (overshoots the 0.51–0.59 band; 5 km CV 0.666, 1 km CV 0.629). First-coverage of under-sampled fault systems under DTI's max operator.
- **Non-fault mimic.** Lahontan shorelines / beach ridges and fan distributary lineaments dominating the sparse-block ridge pool.
- **Predicted sign and size.** Pre-registered +0.001 (−0.003…+0.005). Measured **`+0.0003 MODEL`** (2/4 quadrants; ±6 px jitter +0.0010, 5/5 shifts positive; random-block control −0.0009), **`+0.0012 PROXY`** (95 % CI [−0.0016, +0.0038], n = 11,321). Below the 0.01 floor; does not displace `concb5kmdown4`.
- **Falsifier.** Live `Δ <= -0.005` vs R0 closes 10 km dispersal.

### 2. `CONCENTRATION b10km-down4` — 1,506 dots moved (`7.9992%` changed, `c4e8ffc9`)
- **Hypothesis & Mechanism.** Strict half-dose prefix of `b10km-down8`; lands occupied-10 km CV at **0.518**, inside the 0.51–0.59 band.
- **Non-fault mimic.** Same shoreline/terrace mimic at half exposure.
- **Predicted sign and size.** Pre-registered +0.001 (−0.002…+0.004). Measured **`-0.0010 MODEL`** (2/4 quadrants) vs **`+0.0005 PROXY`** (CI [−0.0006, +0.0019]): instruments disagree on sign, both cover zero — no evidence at 4 %.
- **Falsifier.** Live down4 beating down8 by ≥ +0.005 would favour the CV-band (do-not-overshoot) reading over first-coverage.

### 3. `CONCENTRATION b10km-ridge-up8` — 3,012 dots moved (`15.9983%` changed, `ef2f3548`)
- **Hypothesis & Mechanism.** Sign control: concentrate toward top-35 % Faulds fault-interaction blocks with the prior recomputed at 100 px (30 km catalogue / 10 km ridge tip-junction halos + AGC TMI). 10 km CV 0.736 → 0.545 (interaction blocks ≠ dot-densest blocks).
- **Non-fault mimic.** Quadrangle mapping density; volcanic-margin TMI texture surviving AGC.
- **Predicted sign and size.** Pre-registered −0.001 (−0.004…+0.002). Measured **`-0.0009 MODEL`** (= random control) and **`-0.0075 PROXY`** (CI [−0.0159, −0.0004], excludes zero). Upward concentration has now lost at 1, 5 and 10 km. Do not spend a slot.
- **Falsifier.** Live `Δ >= +0.010` vs R0 would resurrect interaction zoning.
