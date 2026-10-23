# SLOT_PLAN — one entity, 3 scored submissions per rolling week, one blind final

Session 2026-10-23. Parent **R0 = `h33-2b2`** (GEMSDOE32), `sha256 c55bafc4…`, 37,654 dots,
CLAIM **0.2778** (owner-reported, no submission-page receipt in this repo).
**TOP_PUBLIC = 0.3195** — CLAIM, undated, transcribed from this repo's `PROMPT.md` archive at
the human's instruction. It is a target reference only; nothing here is tuned to it.
Slots left this rolling week: **3 / 3** (human-supplied). Deadline **2026-12-03** — UNVERIFIED
(this session never fetches drivendata.org; the human must confirm it on the competition page).

## Built this session (all gates PASS; none submitted)

| slot | file | axis / value | dots | % changed | predicted (MODEL) |
|---|---|---|---|---|---|
| 1 | `releases/gems86-h33-2b2-prune3-20261023-e4027684.tif` | PRUNE `collar3px` | 37,654 | 11.531 | +0.004 (+0.002…+0.006) |
| 2 | `releases/gems86-h33-2b2-snap2-20261023-6ec42a92.tif` | SNAP `2px` | 37,654 | 179.954 (exempt) | +0.004 (+0.001…+0.008) |
| 3 | `releases/gems86-h33-2b2-conc15-20261023-2b883f2d.tif` | CONCENTRATION `b1km-move15` | 37,654 | 29.999 | +0.006 (+0.003…+0.010) |

Upload one file per slot. `-zeros.tif` twins are byte-different fallbacks with identical
pixel content; the ledger already shows the two encodings score identically. Notes for the
submission form are in `docs/SUBMIT.md` (each ≤ 140 characters).

## Next 3 slots, in order, and what each result changes

**Slot 1 — PRUNE `collar3px`.** Smallest edit, and the only axis with a CLAIMED positive step
already on record (2 px collar: 0.2708 → 0.2778).
- Live ≥ 0.288 → the collar is still paying. Next session builds PRUNE `collar4px` and the
  refill rule becomes the axis to tune, not the radius.
- Live in 0.268–0.288 → **no evidence** (under the 0.01 band). Keep R0 as the parent; do not
  extend the collar; spend the next slot on SNAP.
- Live ≤ 0.268 → the 2–3 px annulus carries real new-fault cover. Retire PRUNE, and treat the
  whole catalogue-distance family as a dead axis in `SLOT_PLAN` history.

**Slot 2 — SNAP `2px`.** Count-, exclusion- and collar-preserving, so its result is a clean
read on positional registration.
- Live ≥ R0 + 0.01 → registration was a real loss. Next: SNAP at 3 px, and SNAP restricted to
  the TMI term alone vs the DEM term alone (two further single-axis builds).
- No evidence → the parent's registration is already at the data's own positional uncertainty
  (GeoDAWN Area 2 flew 400 m line spacing, 150–200 m AGL). Retire sub-kernel repositioning.
- Drop → the attractor is non-tectonic (Lahontan shorelines, fan edges, roads). Retire SNAP and
  record the mimic explicitly.

**Slot 3 — CONCENTRATION `b1km-move15`.** Largest edit and the only one that moves mass
between km blocks; it also tests the block-CV claim, because it moves the CV from R0's
measured 0.6235 to 0.7644 (away from the reported 0.51–0.59 band).
- Live ≥ R0 + 0.01 → the fault-interaction prior is real; next session sweeps `move_fraction`
  (10 % / 20 %) and the block size (1 km vs 2 km), not new priors.
- No evidence → the prior is dominated by mapping effort and survey geometry. Retire the
  catalogue-density prior term; keep only the TMI term in a later session.
- Drop → the region wants *less* clustering. That makes the reported 0.51–0.59 CV band the
  next axis to test directly (spread mass until the CV lands in-band), and it demotes
  CONCENTRATION as defined here.

## Weeks to the deadline

- **wk 1–2** — MASS, CONCENTRATION, SNAP, PRUNE, RELIEF, one axis each, parent always the
  current best RECEIPT-confirmed file. This session spent wk1 slots 1–3 on PRUNE, SNAP,
  CONCENTRATION. MASS and RELIEF are **not built**: MASS needs the parent's own ranking, which
  is not stored (the H19-5 surface is binary — 121,131 px of 0/1 — so there is no continuous
  ranking to take the top/bottom 10 % of), and RELIEF needs a detrended-elevation product that
  was not in the restored set. Both need a decision from the human before they are buildable.
- **wk 3–4** — combine the two axes that produced ≥ +0.01 live, as one build per combination,
  from the best RECEIPT-confirmed parent. If no axis reached +0.01, do not combine; spend the
  slots on the axes still untested (MASS, RELIEF, SPACING) instead.
- **wk 5–6** — confirm the leader on a repeat build, choose the final file and one fallback,
  and re-validate the format of both from disk (`python scripts/build_axis_variants.py` gate
  output plus `.venv/bin/python -m gems.validate_submission` on each). The final choice is
  blind; prefer the file with the best *receipt*, never the best projection.

## Proposed better axes (mechanism, confounder, falsifier) — do NOT build this session

1. **COLLAR-SHAPED ANISOTROPY.** Prune only where the dot is *along-strike* of the mapped trace
   (redundant re-cover) and keep dots *across-strike* (possible splay/antithetic).
   Mechanism: antithetic and hanging-wall splay sets sit 100–400 m off the main trace, exactly
   the annulus PRUNE deletes. Confounder: strike estimated from a 100 m raster of a mapped line
   is noisy at trace ends and step-overs. Falsifier: anisotropic collar ≤ isotropic collar at
   the same count.
2. **MAPPING-EFFORT DECONFOUNDING.** Rebuild the CONCENTRATION prior after regressing out
   distance-to-road and distance-to-published-quadrangle-centre. Mechanism: catalogue density
   partly encodes where geologists walked, not where strain localises. Confounder: roads also
   follow range fronts, so the regression can remove real signal. Falsifier: deconfounded prior
   ≤ raw prior at the same move fraction.
3. **KERNEL-BUDGET EQUALISATION (anti-CONCENTRATION).** Spend the count so that every truth
   pixel inside the footprint has exactly one dot within 300 m, and none has two. Mechanism:
   `T` saturates at one credit per truth pixel, so a second dot inside the same kernel is pure
   `FP`. Confounder: truth is unknown, so equalisation must be driven by a proxy. Falsifier:
   equalised field ≤ the parent at matched count.
4. **RELIEF-TERCILE TRANSFER** (the brief's RELIEF axis, still unbuilt). Mechanism: range-front
   and piedmont positions are where normal faults are both present and unmapped; basin centres
   are mostly covered by post-faulting sediment. Confounder: relief is a proxy for erosion, and
   eroded scarps are also where the catalogue is *already* complete. Falsifier: tercile transfer
   ≤ 0 at fixed count.
5. **TRACKB strike-consistent traces** (Phase 2 only). Mechanism: expert expansion in Phase 2
   rewards mappable geometry, not dot scatter. Confounder: a confident wrong trace is worse than
   a scatter dot, because an expert can reject it wholesale. Falsifier: none available before
   Phase 2 labels exist — which is exactly why it must not consume a weekly slot.
