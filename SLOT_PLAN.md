# SLOT PLAN — 2026-10-23 (PRUNE ladder + SNAP ×2, reconciled)

**No automatic slot use.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); the remaining quota and
`TOP_PUBLIC` are **UNSUPPLIED by the human** — I did not guess them. A live `|Δ| < 0.01`
is no evidence. R0 = `h33-h33-2-b2` (**0.2778 CLAIM**, no receipt in `ledger/`).

Deadline arithmetic: 2026-10-23 → **2026-12-03** is 41 days ≈ 5.9 weeks ⇒ ≈ 17 slots, one of
which is the blind final pick. The date is user-supplied and **UNVERIFIED**.

## What the three axes now say

* **PRUNE** — seven gate-clean artifacts, best predicted +0.004, whole ladder inside ±0.01.
  One slot, no more (three sessions already spent here).
* **SNAP** — built **twice concurrently** (PR #31 unconditional `r1p000/r2p000/r2p000-grav`;
  this session's absolute-gravity build, whose r1/r2 duplicate those pairs and are withdrawn,
  IR-86-SNAP-05), **every artifact predicted ≤ 0**. Two independent instruments agree: PR #31's
  random-response null control scores the same catalogue proxy as the real snap (+0.0001 vs
  −0.0012), and this session's SGMC off-catalogue control degrades monotonically with dose
  (gated −0.0021 → r2 −0.0089). Coverage cost is measured (dots < 2 px apart: 0 → up to 8,341).
  **Do not spend slot 1 or 2 on SNAP.** At most one slot, only as a deliberate probe of the
  live hypothesis "new faults sit at potential-field edges" — and the cheapest such probe is
  the gain-gated `snapr2g10` (17.5 % of dots move, **−0.001 MODEL**), not a 98 %-moved file.
* **MASS / CONCENTRATION / RELIEF / SPACING** — unbuilt. MASS stays blocked (R0's per-dot
  ranking is not recoverable from a rebuild, IR-86-PRUNE-02). RELIEF and CONCENTRATION need no
  ranking and no new data.

## Next three slots, in order

| # | file (upload the `-zeros` twin) | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | the deepest collar rung, unchanged from the last plan; it is the only prediction that is positive *and* has a monotone ladder behind it. Prediction **+0.004 MODEL** (−0.004…+0.013), 35,483 dots, 5.77 % removed | ≥ +0.010 → the collar is not exhausted; next week a 4 px rung. Flat or ≤ −0.010 → PRUNE is finished for Phase 1 |
| 2 | **CONCENTRATION on 5 km blocks** — not built yet | the only remaining axis that changes *where* mass is without needing R0's ranking or a new physical field; the best files reportedly sit at block-density CV 0.51–0.59 | preregister block size, direction and CV target before writing; ≥ +0.010 → the win is spatial allocation, and the final file is a PRUNE+CONCENTRATION combination |
| 3 | SNAP probe **only on explicit human choice**: `releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869-zeros.tif` (gated, −0.001) or `…-SNAP-r2p000-…-e7473403-zeros.tif` (full dose, −0.006) — **or** a RELIEF variant instead | SNAP tests an unmeasured live hypothesis (faults at geophysical edges) at a predicted-negative price; the gated file buys nearly the same read for the least expected cost | probe ≥ +0.010 → positions *are* the binding error; escalate dose (the other file). Probe ≤ −0.010 → SNAP closed. Within ±0.010 → no evidence; SNAP gets no further slot |

**Do not spend a slot on:** `SNAP-r1p000` or `SNAP-r2p000-grav` (same axis, weaker dose /
single band; they are the arms that read out *why* slot 3 went the way it did);
`snapr1-…-withdrawn` / `snapr2-…-withdrawn` (duplicate pairs, **no raster exists**);
`…-prune4-…-de4c2a98` (−0.008) and `…-prune3r-…-8c20bd7e` (−0.003) — rehearsals, not bets;
`…-CONTROL-massctl2171…` (a control); `…-prune3-…-3eb29af5` (withdrawn, IR-86-PRUNE-08).

## Calendar to the deadline

- **wk 1 (slot 1).** PRUNE `le3p000`. Single decisive read on the collar.
- **wk 2.** CONCENTRATION at 5 km blocks, preregistered; record block-density CV before/after.
- **wk 3.** SNAP probe (gated `snapr2g10` preferred; only if the human accepts a predicted-negative probe) or RELIEF.
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
confirmation of the governing uniqueness rule (IR-86-PRUNE-01) · **an explicit AXIS
assignment for the next session** (blank again today — SNAP was built twice concurrently
because two sessions both followed this plan's slot-2 line, IR-86-SNAP-05).
