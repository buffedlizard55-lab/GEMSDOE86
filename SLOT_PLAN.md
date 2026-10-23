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
