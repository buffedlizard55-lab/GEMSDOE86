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
