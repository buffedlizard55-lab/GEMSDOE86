# TRACKB — mechanism cards and trace evidence (2026-10-23)

Session axis: **TRACKB**, self-assigned. Brief v2 §5 lists seven axes; MASS,
CONCENTRATION, SNAP, PRUNE, RELIEF and SPACING all had builds in this repository
(`ledger/submissions.csv`), TRACKB had none. Parent **R0 = `h33-h33-2-b2`**, 37,654
unit-mass dots, live **0.2778 CLAIM** (no receipt in `ledger/`). No slot is
requested here: brief v2 classes TRACKB as a Phase-2 axis.

Run card with every number below: `evidence/trackb_axis_20261023.json`.
Code: `src/gems86/trackb.py`, `scripts/run_trackb_axis.py`, `tests/test_trackb_axis.py`.
Releases (gitignored, local): `releases/h33-h33-2-b2-20261004-e5eb6e7e-TRACKB-*-20261023-*.tif`
＋ `-zeros` twins, trace geometry in `releases/trackb/*-traces.geojson`.

## What was measured first: does R0 even contain traces?

A Hough-style detector (18 strike bins at 10°, ±0.75 px across-strike corridor,
along-strike chaining with a 3.2 px maximum gap, ≥1 km minimum length — brief §5)
run on R0 and on a **uniform null field of the same 37,654 dots** on the same
footprint:

| corridor | R0 traces ≥1 km | R0 dots on them | longest | null traces ≥1 km | null longest run |
|---|---|---|---|---|---|
| 1.0 px | 190 | 807 (2.1 %) | 1.9 km | 0 | none |
| 1.5 px | 300 | 1,270 (3.4 %) | 2.0 km | 0 | none |
| 2.5 px | 587 | 2,578 (6.8 %) | 2.8 km | 1 | 1 km |

**Reading.** R0's mass is organised into 1–2 km strike-coherent strands that a
random field of the same density does not produce (0 versus 300 traces at 1.5 px).
That is a property of the lineage's lineament model, not of the operator, and it is
the first label-free statement in this repository about *what R0 is*: not confetti,
but short strands. It is also the axis's whole Phase-2 case — those strands are
what a geologist can review and extend.

**Two limits, stated up front.**
1. Trace support carries **no** information about the independent USGS SGMC fault
   inventory (single-feature AUC 0.5006 against SGMC off-catalogue pixels vs 0.5454
   for local dot density; canary panel, threshold 0.90). The strands are internally
   coherent, not preferentially located on mapped faults.
2. The lineage ranking that TRACKB is supposed to use **does not exist**
   (IR-86-TRACKB-01): the only recoverable order is the FIFO-BFS *traversal* of the
   H19-5 field, which the MASS session showed is geography (IR-86-MASS-01), and the
   restored H19-5 mirror is binary. The substitute ranking is trace support itself —
   "how much of the parent's mass already lies on a coherent strand" — and it is
   used only to choose which dots to donate.

## The edit, and why it is small

Count fixed at 37,654. Donors = the least trace-supported dots. Destinations = new
unit dots walked out from trace ends, inside a ±20° cone, one 2.93 px step at a
time, each cell required to be in the footprint, off the catalogue, > 3 px from it,
and ≥ √8 px from **every** parent dot (the parent's own thinning separation).

The step floor is what limits the dose: at 2.93 px per step there is almost no free
room along strike, because R0 already sits at its packing limit. Requesting a 10 %
donation (3,765 dots) yields only 716 / 1,246 / 2,710 placeable continuations at the
three corridors. **Capacity, not the contract, sets the dose.** That is itself a
mechanism result: every "move the mass" axis in this repository is confined to
≤ 7 % of the dots for a geometric reason, which is consistent with all six earlier
axes landing inside ±0.01.

## Mechanism cards

### M1 — `c15len1km` (corridor 1.5 px, planned default)

* **Hypothesis.** R0's strands are real lineaments clipped by the thinning rule at
  ~1.0–2.0 km; continuing 1,246 of them along strike by one step each adds truth
  credit where the strand truly continues, at half the false-positive cost of a
  fresh dot (each new dot is inside an existing strand's kernel footprint).
* **Mechanism.** Triangular kernel R = 3 px: a dot 2.93 px beyond a strand end is
  still inside the kernel of the parent strand's own truth pixels, so its *marginal*
  truth credit is small — but so is the false-positive term it adds, because it sits
  in already-occupied territory. The exact-marginal algebra (brief §2) predicts a
  near-zero-to-slightly-positive move, not a large one.
* **Non-fault process that could mimic it.** Every extensional geomorphic feature in
  the Great Basin — fault-line scarps, faceted range fronts, lake shorelines at the
  Lahontan highstands, eolian streaks — is a lineament. A strand extension that
  follows a shoreline adds mass on a non-fault line.
* **Predicted sign and size.** **+0.0008 (MODEL; quadrant range +0.0004…+0.0020,
  4/4 quadrants agree)** on the SGMC off-catalogue surrogate. Below the 0.01
  evidence floor by an order of magnitude. Displacement-matched random-azimuth
  control: **−0.0001** — so the *law* beats chance by ≈ +0.0009, and the *act of
  moving* is worth nothing.
* **Falsifier.** Live Δ ≤ −0.005 while the control reads flat: the strands do not
  continue, and boundary extrapolation is buying false-positive mass. A second
  falsifier is a live Δ > +0.01: then trace continuity is the main effect and the
  next axis is a longer-minimum-length variant, not a mass change.

### M2 — `c10len1km` (corridor 1.0 px, strict collinearity)

* **Hypothesis.** If chance alignments contaminate the trace set, the strictest
  corridor (a dot may deviate < 0.5 px across strike) should be the cleanest and
  should pay best per dot moved. 716 dots relocated (3.8 % of the field).
* **Mechanism.** Same as M1 but with 2.1 % of the mass on traces instead of 3.4 %:
  fewer, straighter strands, and fewest "relay" or "arc" geometries that a ±1.25 px
  corridor absorbs.
* **Mimic.** As M1; in addition, a strict corridor selects only lines that are
  *axis-aligned to a 10° bin*, so an E–W shoreline or a N–S grid artefact of the
  survey has a better chance of surviving than a true 15° fault.
* **Predicted sign and size.** **+0.0004 (MODEL; +0.0000…+0.0017, 3/4 quadrants)**.
* **Falsifier.** If M2 lands above M1 by more than 0.005 live, chance alignments are
  the dominant term and the detector needs a coherence-weighted operator (see
  SLOT_PLAN proposals), not a length threshold.

### M3 — `c25len1km` (corridor 2.5 px, loose)

* **Hypothesis.** A loose corridor captures relays, step-overs and gentle arcs — the
  Faulds-style geometries the brief flags as the geothermal-relevant ones — at the
  cost of capturing crossing strands. 2,710 dots relocated (14.4 % of the field),
  the only variant that clears 10 % changed.
* **Mechanism.** Largest relocation budget and longest strands (up to 2.8 km), so if
  trace continuity is the effect, this dose should show it most strongly.
* **Mimic.** Crossing strands: two unrelated 1 km lines within 2.5 px of each other
  chain into a single 2.8 km "trace", and its extension walks off into empty ground.
* **Predicted sign and size.** **−0.0007 (MODEL; −0.0051…+0.0054, 3/4 quadrants)** —
  the sign flips relative to M1/M2, i.e. the loose detector's extra traces are not
  carrying truth density. This is the dose-response *inverted*, and it is the
  clearest reading of the session: more trace mass is not better trace mass.
* **Falsifier.** If M3 (not M1) is the one that scores, the effect is mass, not
  geometry, and TRACKB collapses into MASS.

## Trace evidence paragraphs (top strands, corridor 1.5 px)

Each paragraph below is generated deterministically by
`trackb.trace_paragraph` and shipped as the `evidence_paragraph` property of the
corresponding GeoJSON feature; the full table for all 300 traces is in the run card
and the `-zeros.json` receipt.

* **TRK-000** — 2.0 km, azimuth 110°, 7 dots, median 3.0 px (300 m) and at least
  2.83 px from the mapped catalogue. The longest strand in the parent field — and
  because it hugs the catalogue it is the *weakest* new-fault candidate of the top
  three: a reviewer will read it as a redrawing of a known trace, not a new one.
* **TRK-001** — 1.9 km, azimuth 000°, 7 dots, median 16.3 px (1.6 km) outside the
  catalogue. Geologically the most interesting of the top three (no mapped trace
  opposite it) but **exactly north–south**, i.e. aligned with a raster column, which
  is also the signature of a discretisation artefact.
* **TRK-003** — 1.68 km, azimuth 160°, 6 dots, median 35.1 px (3.5 km) outside the
  catalogue. In the recorded top 12 this is the longest **oblique, catalogue-distant**
  strand: north-northwest, the Walker Lane trend, and the one this session would put
  in front of a geologist first.

**A caveat the numbers force.** In the recorded top 12 traces, 5 are exactly
azimuth 000° (north–south, so aligned with the raster's columns) and only 1 falls
between 15° and 165°. With 10° strike bins and a 1 px lattice, axis-aligned chains
are the easiest to form, so part of the trace set is a discretisation effect rather
than a geological one. The GeoJSON contains all 300 traces; the N–S subset should be
reviewed as suspect until a coherence-weighted operator (SLOT_PLAN proposal 1)
separates them from the rest.

The paragraphs are deliberately phrased as *what the geometry is* (length, azimuth,
dot count, catalogue distance, shared dots) plus a falsifier. No probability is
quoted: the GeoJSON is a candidate set for a geologist, not a map.

## What this session does **not** claim

* No receipt, no live score, no slot. Every number is **MODEL** (SGMC surrogate) or
  **PROXY** (catalogue hide-and-recover), and the PROXY reads 0.00423 / 0.00414 / 0.00394 for the three arms against
  **0.00370** for the parent under the same instrument (the parent value is the one the
  SPACING session recorded, IR-86-SPACING-05) — at its floor, exactly as IR-86-SNAP-06 warned.
* The Phase-2 argument (experts expand labels around reviewed faults) is a
  mechanism, not a measurement. It cannot be tested from inside this sandbox, and
  it is the only reason to spend a slot on TRACKB at all.
* The two release rasters are **not** approved for a weekly slot. Uploading one
  would be a deliberate Phase-2 probe, and only after slots 1–3 in `SLOT_PLAN.md`.
