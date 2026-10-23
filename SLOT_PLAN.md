# SLOT PLAN — 2026-10-23 (PRUNE + SNAP + MASS, four axes reconciled)

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
* **CONCENTRATION / RELIEF / SPACING** — unbuilt. They need no ranking and no new data.
  MASS is built (next paragraph).

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
| 2 | **CONCENTRATION on 5 km blocks** — not built yet | the only remaining axis that changes *where* mass is without needing R0's ranking or a new physical field; the best files reportedly sit at block-density CV 0.51–0.59 | preregister block size, direction and CV target before writing; ≥ +0.010 → the win is spatial allocation, and the final file is a PRUNE+CONCENTRATION combination |
| 3 | `…-SNAP-r2p000-…-e7473403-zeros.tif` **or** a RELIEF variant | SNAP is the one built artifact that tests an unmeasured live hypothesis (faults at geophysical edges); RELIEF is the cheap alternative if the human prefers not to spend a slot on a predicted-negative file | SNAP ≥ +0.010 → positions *are* the binding error and SNAP becomes the main lineage. SNAP within ±0.010 → the axis is retired in one slot, as PRUNE was |

**Do not spend a slot on:** `SNAP-r1p000` or `SNAP-r2p000-grav` (same axis, weaker dose /
single band; they are the arms that read out *why* slot 3 went the way it did);
`…-prune4-…-de4c2a98` (−0.008) and `…-prune3r-…-8c20bd7e` (−0.003) — rehearsals, not bets;
`…-CONTROL-massctl2171…` (a control); `…-prune3-…-3eb29af5` (withdrawn, IR-86-PRUNE-08).

## Calendar to the deadline

- **wk 1 (slot 1).** PRUNE `le3p000`. Single decisive read on the collar.
- **wk 2.** CONCENTRATION at 5 km blocks, preregistered; record block-density CV before/after.
- **wk 3.** SNAP `r2p000` (only if the human accepts a predicted-negative probe) or RELIEF.
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
