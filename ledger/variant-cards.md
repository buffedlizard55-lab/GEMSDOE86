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

# Variant cards — SNAP axis on R0 (built 2026-10-23, PR #31)

Parent **R0** = `h33-h33-2-b2`, 37,654 dots, sha256 `c55bafc4…b6fa9`, dot-set digest
`905cee9d…`. Re-verified this session: the base raster's 40,199 dots minus every dot at
Euclidean distance ≤ 2.0 px from a mapped-fault cell reproduces R0 with **0 differing pixels**
and, re-encoded with the catalogue's own writer profile (`deflate/predictor=3/zlevel=9/tiled 256`),
**byte-identical** files (219,065 B, `c55bafc4…`). R0's 0.2778 remains a **CLAIM**.

## The rule, fixed before any raster was written

Response surface (identical construction for every variant): rank-normalise the band over the
footprint → Gaussian smooth σ = 1 px (100 m) by normalised convolution → rank-normalise again, so
`0.75` is the 75th percentile of every surface. `combo` is the equal-weight mean of the two
smoothed rank surfaces, ranked a third time for the same reason.

A dot may move at most **2 px**, only if the target cell

1. lies inside the footprint and **≥ 3.0 px** from the catalogue (no new collar mass),
2. is not held by another dot,
3. has response **≥ 0.75** (a decisive crest), and
4. beats the dot's own cell by **> 0.02** rank units.

Count preserved exactly, greedy service by descending gain, ties by row-major index.

**Why the gates exist (measured, not aesthetic).** Without them this rule moves **97–99 % of the
dots by a mean 1.8 px**: with a smooth surface the argmax over a 5×5 window sits at the window
boundary for almost every dot, so "snap to the strongest edge" degenerates into "climb 2 px up the
gradient", i.e. a re-labelling of the whole field rather than a correction of individual dots.
The gate turns it back into a local edit. The ungated numbers are kept in
`evidence/snap_axis.json` (`stats` of a measure-only run) so nobody has to take this on trust.

## Measured pre-test (before any slot)

| variant | surface | dots moved | mean disp. | cells changed | NN spacing | dot percentile before → after | predicted Δ live (MODEL) |
|---|---|---:|---:|---:|---|---|---|
| `…-SNAP-tmihg-…-ede24e24` | `tmi_hg` | 12,809 (34.0 %) | 1.87 px | 68.04 % | 3.735 → 3.544 px | 0.581 → 0.610 | **−0.006** [−0.022, +0.012] |
| `…-SNAP-gravhg-…-701aada8` | `iso_grav_anom_hg` | 2,915 (7.7 %) | 1.97 px | 15.48 % | 3.735 → 3.705 px | 0.487 → 0.491 | **−0.002** [−0.014, +0.010] |
| `…-SNAP-combo-…-dba98049` | mean of both | 8,770 (23.3 %) | 1.90 px | 46.58 % | 3.735 → 3.599 px | 0.548 → 0.564 | **−0.004** [−0.018, +0.011] |

Surface separation of catalogue pixels from background (single-feature AUC, leakage canary):
`tmi_hg` 0.527, `iso_grav_anom_hg` 0.500, `combo` 0.519; worst spatial quadrant 0.578 → **PASS**
(threshold 0.90). Block-density CV on 5 km blocks: 0.9036 before, 0.903–0.904 after — unchanged.

The single most important measurement: for **20,235 / 27,480 / 23,081** dots (tmihg / gravhg /
combo) the strongest in-window edge lies **inside the masked 3 px collar**, i.e. the strongest
magnetic or gravity edge near an R0 dot is usually the *known* fault trace itself, where the
organizer scores nothing. That is the structural reason this axis cannot pay, and it is why the
predicted sign is negative for all three.

## Mechanism cards (for a structural geologist)

### `SNAP-tmihg` — move dots onto TMI horizontal-gradient crests
- **Hypothesis.** A magnetisation contrast across a fault produces a TMI horizontal-gradient
  maximum along the trace; a dot sitting 1–2 px off that crest would collect more kernel credit if
  it climbed onto it.
- **Mechanism.** R0's dots come from a smooth 19-band model sampled on a 2.8 px lattice, so each
  dot's sub-kernel position is a model average. Snapping replaces it with the local maximum of the
  delivered magnetic edge.
- **Mimic.** Pixel-scale dither in the delivered gradient (0 % of horizontal neighbour differences
  are zero) and 400 m flight-line smearing at 150–200 m clearance both put a 100 m crest where no
  100 m fault boundary exists. R0's dots already sit at the 62nd percentile of this surface
  (background 50th), so the parent already used this field.
- **Predicted sign and size.** −0.006 live (95 % range −0.022 … +0.012): the biggest edit of the
  three (34 % of dots, nearest-neighbour spacing down 0.19 px), the smallest expected gain.
- **Falsifier.** A live change ≥ +0.010 means the magnetic edge carries sub-kernel position
  information the parent's model missed; it would license a *selective* magnetic snap next.
  Inside ±0.010 the magnetic-snap form is closed for Phase 1.

### `SNAP-gravhg` — move dots onto isostatic-gravity horizontal-gradient crests
- **Hypothesis.** A density contrast across a fault produces a gravity-gradient crest; gravity is
  not blanked over magnetically quiet volcanic cover, so it is the independent test.
- **Mechanism.** Same rule, different surface. Agreement with the magnetic variant would be
  evidence that the edge geometry is physical rather than a processing artefact.
- **Mimic.** Isostatic correction low-passes the field, displacing a 100 m crest off the trace.
  Measured: R0's dots sit at the **48th** percentile here (background 50th) and catalogue pixels
  separate at AUC **0.500** — chance. This variant is the honest null control of the trio.
- **Predicted sign and size.** −0.002 live (95 % range −0.014 … +0.010): the smallest edit (7.7 %
  of dots), so the smallest expected loss; no mechanism for a gain.
- **Falsifier.** A gain ≥ +0.010 would mean gravity edges localise faults better than the parent's
  model despite chance-level catalogue AUC, which needs an independent explanation before a slot.

### `SNAP-combo` — move dots onto shared magnetic + gravity crests
- **Hypothesis.** Where both horizontal gradients are strong, two independent contrasts share one
  boundary (the cross-gradient argument of Gallardo & Meju 2003); snapping to that conjunction
  should be cleaner than snapping to either field.
- **Mechanism.** Equal-weight mean of the two rank surfaces, ranked again; a cell scores high only
  if both fields are high there, so dots climb the shared boundary rather than one field's
  artefacts.
- **Mimic.** Equal weights are a declared choice, not fitted. A mean is a *soft* conjunction: one
  strong field can carry a cell, and half of any local noise is inherited.
- **Predicted sign and size.** −0.004 live (95 % range −0.018 … +0.011).
- **Falsifier.** The conjunction mechanism requires the combo to beat **both** single-field
  variants by ≥ 0.005 live. Between them = no conjunction, and ±0.010 overall = no evidence.

## Report-only instruments

- **Catalogue hide-and-recover PROXY** (never a gate, never a score): R0 0.00436
  [0.00410, 0.00458]; tmihg 0.00366; gravhg 0.00418; combo 0.00386. All at the floor and
  contaminated by construction — the dot field was emitted from a catalogue-trained surface
  (IR-86-PRUNE-03). This instrument cannot order these files.
- **SGMC control** not computed this session: `derived_sgmc_faults_100m_u8.tif` is pinned in the
  manifest but is not part of the restored external subset used here (five rasters). REPORT ONLY,
  so nothing depends on it.

## Files

`releases/snap/<id>-zeros.tif` (upload-form fallback) and `<id>.tif` (NaN outside the footprint,
brief §6 form); receipts `<id>-zeros.json`. All three pass `gems57.validate`
(`all_checks_passed=True`) and `gems57.gates.format_report` (`ok=True`) on the `-zeros` twin, carry
zero catalogue mass, preserve the 37,654-dot count, were re-read from disk after writing, and
reproduce the same sha256 on a second build (byte-deterministic).
