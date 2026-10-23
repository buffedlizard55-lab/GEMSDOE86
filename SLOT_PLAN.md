# SLOT PLAN — 2026-10-23 (PRUNE ladder + SNAP, three axes reconciled)

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
* **MASS / CONCENTRATION / RELIEF / SPACING** — unbuilt. MASS stays blocked (R0's per-dot
  ranking is not recoverable from a rebuild, IR-86-PRUNE-02). RELIEF and CONCENTRATION need no
  ranking and no new data.

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
