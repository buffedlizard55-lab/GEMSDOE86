# Mechanism cards — SNAP axis on R0, gain-gated build (2026-10-23)

> **Reconciliation note.** A concurrent session (PR #31) built and merged the same axis
> first (`SNAP-r1p000/r2p000/r2p000-grav`, `evidence/snap_axis_20261023.json`, cards in
> `ledger/variant-cards.md`). Cards 1–2 below describe this session's independent
> replications of those same two values — they are **WITHDRAWN duplicate pairs with no
> raster released** (IR-86-SNAP-05) and are kept because their SGMC dose-response is
> evidence. Card 3 (`snapr2g10`) is the one released file from this build.

Parent **R0** = `h33-h33-2-b2` (GEMSDOE32): 37,654 unit-mass dots, sha256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, live 0.2778 =
**CLAIM** (no receipt in `ledger/`). R0 was rebuilt in-session from the pinned
40,199-dot solo-d2.8 base (delete dots ≤ 2 px from the catalogue) and matched the
published file **byte for byte** (219,065 B) before any variant was written.

**Shared SNAP rule (the only change from R0).** Edge surface = mean of the
footprint-percentiles of two provided gradient bands of the pinned 19-band stack
(sha256 `4371c82e…3bc5`): `tmi_hg` (total-magnetic-intensity horizontal gradient,
already a magnitude ≥ 0) and `|iso_grav_anom_hg|` (a signed band, taken absolute).
Each dot may move to the highest-edge cell inside its Euclidean window. Count is
preserved exactly (37,654); destinations must lie in the footprint, off the
catalogue, > 2 px from it (R0's own exclusion; see IR-86-SNAP-04) and on a valid
edge cell. Collisions are resolved gain-first with origin reservation
(`src/gems86/snap.py`). 16 dots sit on missing edge values and stay.

**Shared hypothesis.** R0's dots were thinned from a smooth multi-line field at
2.8 px, so their within-window positions are partly an artefact of thinning
order, while a fault that juxtaposes magnetically or densimetrically different
rocks produces a *crest* in the horizontal-gradient magnitude along its trace.
GeoDAWN Area 2 was flown at 400 m line spacing, so a lineament's mapped position
is uncertain by roughly the 300 m kernel radius — a ≤ 2 px relocation onto the
gradient crest is exactly the scale of that misregistration. If the true trace
follows the crest, a snapped dot gains triangular-kernel credit (1/3 per pixel
of approach) at zero mass cost.

**Shared non-fault mimics / confounders, stated up front.**
(i) Gradient crests also mark non-fault edges: lithologic contacts, lava-flow and
pluton margins, dikes, basin-fill thickness steps, and cultural ferrous sources
(pipelines, wells, power lines). (ii) For a *dipping* contact the gradient maximum
is displaced from the surface trace (source depth and dip shift the anomaly
crest downdip), so "on the crest" is not generally "on the fault" for ~60° Basin
and Range normal faults — this alone can flip the sign. (iii) `iso_grav_anom_hg`
is signed, i.e. a directional derivative; its absolute value is most sensitive to
structures striking across that direction. (iv) SNAP also erodes the parent's
spacing (dots with a neighbour < 2.8 px go from 0 % in R0 to 28.4 % / 40.1 % /
13.0 % in the three variants) and drifts the 2–3 px collar count by −209 / −82 /
−27 dots, so a live change is attributable to "snap + its spacing side-effect",
not to crest position alone.

Report-only local controls (never gates, never scores): the catalogue
hide-and-recover PROXY is at its structural floor for this parent (R0 0.00436;
deltas −0.0010 / +0.00005 / +0.00001, IR-86-PRUNE-03). The SGMC off-catalogue
control (62,122 truth px > 3 px from the catalogue) is *negative with a clean
dose-response*: R0 0.09539, r2g10 −0.0021, r1 −0.0032, r2 −0.0089. Single-band
catalogue AUCs are 0.527 / 0.529 (combined 0.541) — no leakage canary triggered.

| variant | moved | mean disp. (all / moved) | median gain (moved) | mean edge pct | predicted Δ live (MODEL) |
|---|---:|---:|---:|---:|---:|
| `snapr1` | 36,483 (96.9 %) | 0.97 / 1.00 px | 0.025 | 0.545 → 0.581 | **−0.002** [−0.008, +0.003] |
| `snapr2` | 37,055 (98.4 %) | 1.77 / 1.80 px | 0.042 | 0.545 → 0.605 | **−0.006** [−0.018, +0.006] |
| `snapr2g10` | 6,579 (17.5 %) | 0.34 / 1.95 px | 0.142 | 0.545 → 0.573 | **−0.001** [−0.007, +0.008] |

A live change under 0.01 is no evidence (brief §5), so all three predictions are
formally "inconclusive if submitted"; the centres rank the variants by expected
value, nothing more.

---

### 1. `snapr1` — every dot hill-climbs 1 px
- **Hypothesis.** The misregistration is one pixel: R0's thinning left dots one
  cell off the lineament they were thinned from.
- **Mechanism.** Unconditional argmax in the 5-cell (≤1 px) window. 96.9 % of
  dots take the step, but the median realised gain is 0.025 percentile — in
  most windows the "crest" is barely stronger than the origin, so this variant
  mostly exchanges one near-equal cell for another while still paying the
  spacing side-effect (28.4 % sub-2.8 px neighbours).
- **Non-fault mimic.** Pixel-scale gradient noise from flight-line levelling and
  gridding (400 m lines interpolated to a 100 m grid): adjacent-cell maxima are
  as likely acquisition texture as geology.
- **Predicted sign and size.** −0.002 (MODEL, band −0.008…+0.003).
- **Falsifier.** A receipt ≥ +0.010 vs R0 would say 100 m misregistration is
  real and common — then r2/r2g10 must be re-centred positive. A receipt
  ≤ −0.010 kills the 1 px story outright.

### 2. `snapr2` — every dot to the strongest cell within 2 px
- **Hypothesis.** The crest can be a full kernel-radius-minus-one away: dots sit
  up to 200 m off the trace, the scale of GeoDAWN positional uncertainty.
- **Mechanism.** Unconditional argmax in the 13-cell (≤2 px) window: 98.4 %
  move, mean 1.80 px among movers, mean candidate edge 0.605. It is the
  strongest, cleanest dose of the crest idea — and the noisiest: windows this
  size almost always contain a "stronger" cell, so the variant doubles as a
  within-window noise maximiser, and neighbouring dots converge on shared
  crests (40.1 % sub-2.8 px neighbours) where the max-kernel makes them
  redundant. The SGMC control is worst at this dose (−0.0089).
- **Non-fault mimic.** Dipping-contact crest offset plus lithologic edges, as
  above; at 2 px the window also reaches *adjacent* lineaments, so a dot can
  snap from its own structure onto a parallel contact.
- **Predicted sign and size.** −0.006 (MODEL, band −0.018…+0.006), the widest
  band of the three.
- **Falsifier.** This is the dose-escalation instrument, not a slot candidate.
  It earns a slot only if `snapr2g10` first receipts ≥ +0.010; then r2 ≤ r2g10
  would prove the gain gate, not the crest, is what helps.

### 3. `snapr2g10` — 2 px window, move only on a decisive edge (gain ≥ 0.10)
- **Hypothesis.** Only a minority of R0 dots are genuinely mis-registered, and
  they announce themselves: their window contains a cell at least 0.10
  edge-percentile stronger than the cell they sit on.
- **Mechanism.** Same 13-cell window as r2 with a realised-gain floor. 6,579
  dots (17.5 %) move, mean 1.95 px, median gain 0.142; 82.5 % of the parent —
  including most of its spacing structure — is untouched. If any SNAP form
  carries crest signal, the signal-to-noise is highest here by construction.
- **Non-fault mimic.** A decisive local gradient high is also what a shallow
  cultural source or a volcanic margin looks like; the gate selects for
  *contrast*, not for faulting. And the SGMC control still scores this form
  slightly below R0 (−0.0021), which is why the centre is ~zero, not positive.
- **Predicted sign and size.** −0.001 (MODEL, band −0.007…+0.008).
- **Falsifier.** Receipt ≥ +0.010: crest capture is real at decisive contrasts →
  escalate to `snapr2` (built) and consider combining with the PRUNE winner.
  Receipt ≤ −0.010: even decisive crests mislead at 100–200 m (dip offset /
  cultural edges dominate) → close the SNAP axis for Phase 1. Anything between
  is no evidence, and SNAP must not consume another slot on that outcome.

**Reproduction.** `.venv/bin/python scripts/build_r0_snap.py --build`
(releases only `snapr2g10`, identical sha256; inputs pinned in `registry/data_manifest.json`,
seed 20261023). Full receipts: `evidence/snap_gated_axis_20261023.json`,
`ledger/variants_snap_gated.json`, `releases/*-snapr2g10*-zeros.json`.
