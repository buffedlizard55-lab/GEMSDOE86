# SLOT_PLAN — one entity, 3 scored slots/week, deadline 2026-12-03

**Status of the paper facts I could not fill myself** (the human owns them, I did not guess):
`TOP_PUBLIC` is blank, `slots left this week` is blank, the weekly reset day is unknown.
Every score below that is not marked RECEIPT is a CLAIM or a MODEL, never a score.

Deadline arithmetic: 2026-10-23 → 2026-12-03 is **41 days ≈ 5.9 weeks**, i.e. about
**17 scored slots** at 3/week, of which **one** is the blind final pick.

## The next three slots, in order

| # | file (upload the `-zeros` twin) | why this one | what the result changes | decision rule |
|---|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-27c5eab6-zeros.tif` | highest predicted Δ (+0.004 MODEL, band −0.004…+0.013); the only rung whose mechanism test is decisive | if ≥ +0.010: the collar is not exhausted, add a 4–5 px rung next week. If flat: the prune lineage is finished for Phase 1 | one slot, no second prune variant in the same week |
| 2 | **new prediction surface**, not another prune rung — see "the blocker" below | all three prune rungs together can only move the score by ~±0.01; that is not how we beat 0.2778 | the axis choice for weeks 3–4 | requires restoring `training_features.tif` (419 MB, pinned, public) |
| 3 | the better of (1) and (2) re-cut on the axis that moved | one more point on the winning axis at a different value | whether week 5–6 is a confirm or a re-think | keep the loser as the fallback |

**Do not** spend a slot on the mass-matched control `…-CONTROL-massctl2171-20261023-99190068`.
It is only worth a slot *after* a variant shows ≥ +0.010, when attributing the mechanism
(mass vs. proximity) becomes the thing that decides the next edit.

## Why the PRUNE axis is a one-slot axis, not a three-slot campaign

R0's surviving dots occupy exactly three distance shells (941 at √5, 670 at √8, 560 at 3.0 px);
the whole remaining ladder is 2,171 dots, 5.8 % of the mass. The best available per-dot rate
(+2.75 × 10⁻⁶ from the one live collar datum) puts the entire ladder inside ±0.01. The
report-only catalogue proxy **anti-correlates with that datum by construction** — it scores
R0 at 0.0044 and every rung at ≤ 0.0004, because after a 3 px prune no dot can earn credit
from the catalogue at all. That is a useful negative result: for this axis the proxy is
structurally invalid, not merely noisy, and must never be used to rank collar edits.

## The blocker, and the only axes worth the remaining 5 weeks

`SNAP`, `RELIEF`, `CONCENTRATION` and `MASS` all need a per-pixel surface. The 19-band feature
stack is **absent from this checkout** (`registry/data_manifest.json` pins
`training_features.tif`, sha256 `4371c82e…`, 419 MB, five GitHub parts in
`buffedlizard55-lab/GEMSDOE` at `c0c06ac8…`; `codeload.github.com` answered HTTP 200 on
2026-10-23, so it is fetchable). Restoring it is the gate for everything below.

1. **SNAP (assign first).** Mechanism: per-dot positional error, not per-dot presence, is the
   binding constraint — at 400 m flight-line spacing the lineament position is uncertain by
   about the kernel radius. Confounder: the edge field (TMI/gravity gradient) marks contacts
   and survey seams as readily as faults. Falsifier: if mean displacement is < 0.5 px the
   edit is a no-op and the axis is dead; if it is ~2 px and the score falls, positional
   refinement at this grid is not the lever.
2. **CONCENTRATION at 10 km blocks.** Mechanism: expert-mapped new faults are extensions of
   known systems, so mass belongs where structure density is high. Confounder: that is also
   where the catalogue is dense, and the collar result says the opposite — so this axis is
   *partly falsified already*; run it only at blocks > 3 px clear of the catalogue.
   Falsifier: no monotone relation between block prior and score change.
3. **MASS at fixed geometry.** Needs the parent's own ranking, which is not stored. Rebuilding
   it means re-running the emission recipe on the restored stack — do that before spending a
   slot, or skip the axis (the ledger's mass confound is unresolvable without it).

Axes I recommend **against**, with the reason (so they are not re-tried blindly): a lattice or
Poisson re-draw at matched count (already 0.0904 for a lattice); uniform exploration of the
low-density field (the d2.8 surface is the only thing that has ever scored > 0.19); further
collar pruning beyond 3 px (no dot can earn credit there, so it is pure mass loss).

## Weeks to the deadline

- **wk 1 (now):** submit slot 1. Restore the feature stack and run SNAP offline.
- **wk 2–3:** slots on SNAP and, if it moves, its value twice (dose–response, one axis).
- **wk 4:** combine the best of SNAP with the winner of PRUNE at fixed other-axis values.
- **wk 5:** confirm the leader, re-validate both the candidate and a fallback raster
  (`docs/SUBMIT.md` procedure), record receipts in `ledger/submissions.csv` (`receipt_score`,
  `receipt_date`).
- **wk 6:** blind final pick from the two validated files. Nothing new after that.
