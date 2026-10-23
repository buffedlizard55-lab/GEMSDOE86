# SLOT PLAN — 2026-10-23 (SNAP built; centres ~zero-to-negative, so PRUNE keeps slot 1)

**No automatic slot use.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); remaining quota and
`TOP_PUBLIC` remain **UNSUPPLIED**. R0 = `h33-h33-2-b2` (**0.2778 CLAIM**, no receipt).
A live `|Δ| < 0.01` is no evidence. 2026-10-23 → 2026-12-03 (user-supplied,
**UNVERIFIED**) is 41 days ≈ 17 slots, one of them the blind final pick.

**What SNAP taught us (no slot spent).** Three gate-clean crest relocations of R0
exist (`snapr1/r2/r2g10`; cards in `evidence/r0-snap-mechanism.md`). The dose is
real (up to 98.4 % of dots moved, mean disp. 1.77 px) but both report-only
controls are flat-to-negative: hide-and-recover PROXY ≈ 0 (floored,
IR-86-PRUNE-03) and the SGMC off-catalogue control is negative with a clean
dose-response (r2g10 −0.0021, r1 −0.0032, r2 −0.0089). MODEL centres were set
accordingly (−0.002 / −0.006 / −0.001): **gradient crests at 100–200 m do not
look like free score**, plausibly because a dipping contact's gradient crest is
offset from its surface trace. PRUNE — the only axis with a positive centre —
keeps the first slot.

## Next three slots, in order

| # | file (upload the `-zeros` twin; see docs/SUBMIT.md) | decision rule |
|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` (35,483 dots, **+0.004 MODEL**) | ≥ +0.010 → collar not exhausted, single 4 px rung next week. Flat or ≤ −0.010 → PRUNE lineage finished for Phase 1. |
| 2 | **RELIEF, to be built next session** (shift 10–15 % of mass between basin/piedmont/range-front terciles from the detrended-elevation bands, count fixed; preregister classes before building). If a slot must be filled before it exists: `releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869-zeros.tif` (37,654 dots, 17.5 % moved, **−0.001 MODEL**) — a crest-hypothesis test, not a score bet. | SNAP receipt ≥ +0.010 → escalate to built `snapr2`; ≤ −0.010 → close SNAP; between → no evidence, SNAP gets no further slot. RELIEF receipt ≥ +0.010 → re-cut its dose; ≤ −0.010 → close RELIEF. |
| 3 | The better of slots 1–2, re-cut on the axis that receipted ≥ 0.01 (or the two winners combined as one attributable edit, only if both did). | Keep the loser as the named fallback for the final pick. If neither moved, slot 3 goes to CONCENTRATION (below), not to a re-roll of a flat axis. |

**Do not spend a slot on:** `snapr1` (dominated by r2g10: more churn, weaker
gains), `snapr2` (dose instrument; only after an r2g10 receipt ≥ +0.010),
`…-CONTROL-massctl2171…` (a control), `…-prune3-…-01d57649` (same `(PRUNE,3)`
pair as slot 1, refill variant), or the withdrawn `3eb29af5` (IR-86-PRUNE-08).

## Calendar to the deadline

- **wk 1:** slot 1 (PRUNE `le3p000`). Build RELIEF in parallel (no slot needed to build).
- **wk 2–3:** slot 2 (RELIEF, or SNAP r2g10 if RELIEF missed) and slot 3 per the table.
- **wk 4:** CONCENTRATION on 5–10 km blocks (record block-density CV before/after; brief
  reports the best files at 0.51–0.59), unless a winner from wk 1–3 asks for a dose re-cut.
- **wk 5:** combine the two axes with receipt effects ≥ 0.01 as one attributable edit.
- **wk 6:** re-validate finalist + fallback byte-for-byte, choose the final file blind.

## Better axes (proposals only — not built this session)

- **Isotropic SNAP (SNAP-iso).** Re-run r2g10 with the gravity edge from
  `iso_grav_anom_slope` (a non-negative gradient *magnitude*) instead of the
  signed `iso_grav_anom_hg`. *Mechanism:* removes the directional-derivative
  bias in the current pair. *Confounder:* any difference is then "which band",
  not "crest or not". *Falsifier:* build only if r2g10 receipts — a flat/negative
  r2g10 kills the whole crest family, isotropy included.
- **Dip-aware offset (SNAP-dip).** Move dots to the gradient crest *shifted*
  updip by a depth-proportional offset instead of onto the crest. *Mechanism:*
  dipping-contact anomaly crests sit downdip of the trace. *Confounder:* needs a
  dip/depth field the stack only proxies (`depth_to_base_surf`). *Falsifier:* if
  r2g10 is flat, the crest itself carries no positional information to shift.
- **Exact-marginal PRUNE / collar-fill-inward** (carried from the previous plan):
  prune by exact ΔDTI under the two-sided metric, or — if slot 1 receipts
  negative — *add* mass in the 2–3 px annulus. *Confounder:* proxy-truth shift /
  masked pixels earn nothing. *Falsifier:* no replicated sign on held-out folds,
  then no live gain ≥ 0.01.
- **Annulus-conditional RELIEF.** RELIEF applied separately inside the 200–300 m
  catalogue annulus. *Confounder:* relief drives both catalogue completeness and
  lineament visibility. *Falsifier:* no consistent sign in two relief regimes.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation · any
submission-page receipt (R0's 0.2778 included) · which fill form the portal
accepted last time · **the AXIS for the next session** (left blank again this
session; SNAP was taken from this plan's own preregistration, IR-86-SNAP-02).
