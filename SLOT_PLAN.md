# SLOT PLAN — 2026-10-23 (after the CONCENTRATION knob session)

**No automatic slot use.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); remaining quota and `TOP_PUBLIC` are
**UNSUPPLIED by the human** — not guessed. R0 = `h33-h33-2-b2` = **0.2778 CLAIM** (no receipt in
`ledger/`). A live `|Δ| < 0.01` is no evidence. Deadline 2026-12-03 is user-supplied, UNVERIFIED:
41 days ≈ 5.9 weeks ≈ **17 slots**, one of which is the blind final pick.

## What this session settled

**CONCENTRATION is closed for Phase 1, at every knob.** Three new gate-clean arms
(`evidence/concentration-knobs-mechanism.md`), each moving one knob off the spent 1 km/15 %/top-20 %
setting, plus three report-only instruments:

- the hide-and-recover gain (+0.012 / +0.024 / +0.019 holdout DTI) is **circular** — it is entirely
  the catalogue-density term (+0.0149); the only non-circular term, TMI gradient, recovers nothing
  (+0.0008, CI −0.0044…+0.0073), and a shuffled-prior null is flat (−0.0004);
- on the USGS **SGMC** independent map *every* arm, null included, loses 0.012–0.020: relocation
  has a cost-of-moving term and no prior in this family repays it;
- so all three arms are predicted **inside ±0.010** (preregistered +0.004/+0.008/+0.007, revised
  to +0.001/−0.001/+0.002). They are built and gated but **not slot-approved**.

**The general lesson, which now governs the plan:** the only mechanism in this repo whose positive
prediction does not depend on a prior is the catalogue **collar** (R0's 2 px exclusion removes mass
that is masked by definition, worth `+0.2T/D² ≈ +2.75e-6` per dot; the live 0.2708→0.2778 step is
exactly that rate). Everything prior-driven has now measured flat on at least two instruments.

## Next three slots, in order

| # | file (upload the `-zeros` twin) | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/…-PRUNE-le3p000-…-a438e92b-zeros.tif` | the only positive prediction with a monotone ladder behind it and **no prior term**: 35,483 dots, 5.77 % removed, **+0.004 MODEL** (−0.004…+0.013) | ≥ +0.010 → the collar is not exhausted, next week a 4 px rung; flat or ≤ −0.010 → PRUNE is finished for Phase 1 |
| 2 | `releases/…-RELIEF-frontp15-…-e0e2888f-zeros.tif` | the only built candidate that *moves* mass and is not prior-free in the same way as CONCENTRATION; 5,648 dots piedmont → range-front, **+0.0017 MODEL**, in-regime displacement control −0.0010 | ≥ +0.010 → spatial allocation is the win, build RELIEF-ADD then the PRUNE+RELIEF combination; ≤ −0.005 → RELIEF closes; otherwise the axis is alive but under the floor |
| 3 | `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif` | the only arm that moves mass *along* the trace instead of off it, with its paired random-move control already built (`sp-random16`, +0.0002) — one slot buys a law-vs-chance read | ≥ +0.010 → trace continuity is real, go to along-strike extension at 2× dose; flat → SPACING closes with RELIEF |

**Not recommended:** any CONCENTRATION arm (predicted flat, and slot 1/2/3 answer the same question
better); `conc24` specifically, because it is the largest exposure to the one measured negative
term and buys nothing extra; the three SNAP arms (instrument negative); the MASS rungs (predicted
negative, traversal-ranked source); `prune4` (−0.008) and `prune3r` (−0.003) (rehearsals);
RELIEF `frontp10` (a strict prefix of slot 2 — the fallback, not a bet).

**If the human wants to falsify the prior question directly** (rather than maximise P(win)): upload
`gems86-h33-2b2-conc15-t05-20261023-278d9995-zeros.tif`. It is the sharpest test of whether a
catalogue-density prior transfers to new faults, and its result would either reopen the family or
close it for good. It is a **probe, not a bet**.

## Calendar to the deadline

- **wk 1** slot 1 (PRUNE `le3p000`). Single decisive read on the collar.
- **wk 2** slot 2 (RELIEF `frontp15`). Re-read the `-zeros` bytes through the validator before upload.
- **wk 3** slot 3 (`sp-strike16`). Then pick the axis with the only receipt-level effect ≥ 0.01.
- **wk 4–5** one new value on that axis (or the sign flip that pairs with it), as ONE attributable edit.
- **wk 6** combine the two best axes into a single file, re-validate both finalists' formats, and
  choose the final submission and the fallback **blind** (write the choice down before either
  receipt is read). Never multiply accounts.

## Better axes (proposals only; nothing built this session)

- **MASS-credit (rank dots by their own kernel redundancy, not by traversal order).** Mechanism: a
  dot whose 29-cell disc is 90 % owned by neighbours adds little `T` and full cost; delete the
  worst decile of *measured* redundancy. Confounder: redundancy along a true trace is free (both
  dots sit on truth), so the rule must be applied only where coverage is thin. Falsifier: live
  Δ ≤ 0 while `massminus10` (traversal order) also ≤ 0 → mass itself is at its optimum.
- **Coherent SNAP (structure tensor, σ = 2–3 px)** — carried over from the SNAP session unchanged:
  a coherence-weighted response is the physically correct lineament operator; falsifier is no
  separation from the random-response null in two independent folds.
- **TRACKB (Phase 2, not a weekly slot):** strike-consistent traces ≥ 1 km from R0's top-ranked
  dots, GeoJSON + raster, one evidence paragraph per trace. Contingent on the Phase 1 receipt
  telling us whether along-strike continuity (slot 3) pays at all.
