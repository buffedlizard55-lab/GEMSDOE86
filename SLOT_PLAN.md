# SLOT PLAN — 2026-10-23 (SNAP session, branch `arena/1f6f5dc8-gemsdoe86`)

**No slot is used or authorised here.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)), one blind final choice. `TOP_PUBLIC`
(+date) and the remaining rolling-week quota are **UNSUPPLIED by the human** and were not guessed.
A live `|Δ| < 0.01` is **no evidence**. R0 = `h33-h33-2-b2`, **0.2778 CLAIM**, no receipt in
`ledger/`. Deadline 2026-12-03 is user-supplied and **UNVERIFIED** (DrivenData is not contacted
from this sandbox): 41 days ≈ 5.9 weeks ⇒ ≈ 17 slots including the final pick.

## What this session added (three files, one axis)

SNAP on R0: three variants, identical rule and exclusions, different physical surface. Full cards:
[ledger/variant-cards.md](ledger/variant-cards.md); measurements: `evidence/snap_axis.json`;
rerun: `python scripts/run_snap.py --build`.

| id (upload the `-zeros` twin in `releases/snap/`) | change | predicted Δ live |
|---|---|---|
| `…-SNAP-combo-20261023-dba98049` | 23.3 % of dots (8,770) moved ≤ 2 px onto shared magnetic + gravity crests | **−0.004** MODEL [−0.018, +0.011] |
| `…-SNAP-gravhg-20261023-701aada8` | 7.7 % (2,915) moved onto isostatic-gravity crests | **−0.002** MODEL [−0.014, +0.010] |
| `…-SNAP-tmihg-20261023-ede24e24` | 34.0 % (12,809) moved onto TMI-gradient crests | **−0.006** MODEL [−0.022, +0.012] |

All three keep the dot count at 37,654, add no collar mass, and pass every format gate. **None is
predicted to beat R0.** The axis is worth at most **one** slot, and only to close the hypothesis.

Why the prior is negative, in one line: for 54–73 % of dots the strongest edge inside their own
2 px window is the **masked catalogue trace itself** (20,235 / 27,480 / 23,081 dots), and the
surfaces separate catalogue from background at AUC 0.500–0.527 — the edge is where the *known*
fault is, which pays nothing, and it barely marks the rest.

## Next three slots, in order

| # | file | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | still the only built file whose sign comes from a **live** datum (+2.75 × 10⁻⁶ per pruned collar dot), prediction **+0.004** [−0.004, +0.013] | ≥ +0.010 → collar not exhausted, build a single 4 px rung; flat/≤ −0.010 → PRUNE is finished for Phase 1 |
| 2 | **CONCENTRATION**, to be built next session (5 km blocks, dots moved from the lowest-prior to the highest-prior blocks, 10–20 % of mass, block CV before/after recorded) | the only untried axis with a mechanism the ledger actually supports: R0's dot field is strongly clumped at km scale (CV 0.904 on 5 km blocks) while the brief reports best files at 0.51–0.59 | this is the first file since R0 that can plausibly clear ±0.01; preregister mechanism/confounder/falsifier before writing |
| 3 | `…-SNAP-combo-…-dba98049` **or** the better of slots 1–2 re-cut | closes SNAP with the moderate edit if the human wants the question answered; otherwise a second point on the winning axis | SNAP ≥ +0.010 → magnetic/gravity edges carry sub-kernel information, licence a *selective* snap; ≤ −0.010 → SNAP closed for Phase 1 |

**Do not spend a slot on:** `SNAP-tmihg` (largest edit, worst prediction, same information as
`combo`), `SNAP-gravhg` alone (a chance-level surface — it is the control, not a bet),
`…-prune3-…-3eb29af5` (withdrawn, same dot set as `le3p000`, IR-86-PRUNE-08), or any PRUNE twin
already in the ledger.

## Calendar to the deadline

- **wk 1.** Slot 1 = `le3p000`. One decisive read on the collar.
- **wk 2.** Build **CONCENTRATION** (5 km and 10 km blocks, two values) and spend slot 2 on the
  better one; keep the loser as the fallback.
- **wk 3.** Slot 3 = `SNAP-combo` *or* a second CONCENTRATION point, whichever the wk-1/2 receipts
  make informative. Then stop spending and re-read this file.
- **wk 4–5.** Combine the two axes with receipt-level effects ≥ 0.01 as one attributable edit
  (e.g. prune the collar *and* concentrate km-scale mass), re-validating format each time.
- **wk 6.** Confirm both finalists, re-run `scripts/run_snap.py`/`prune_collar.py` to prove
  reproducibility, choose the final file and a fallback **blind**, never multiply accounts.

## Better axes (proposals only — not built this session)

- **CONCENTRATION at 5 km vs 10 km.** *Mechanism:* geothermal systems and fault step-overs cluster
  at km scale; the metric's max-cover term rewards clustering where truth is dense. *Confounder:*
  the catalogue's own completeness varies by block, so "prior" and "known faults" are entangled.
  *Falsifier:* block CV drops toward 0.55 with no live gain, or CV falls below 0.45 and the score
  drops — then clustering is not the axis.
- **RELIEF terciles (basin / piedmont / range-front).** *Mechanism:* range-front faults are better
  imaged than basin-floor ones. *Confounder:* relief also controls catalogue completeness and
  lineament visibility. *Falsifier:* no consistent sign in two relief regimes on held-out blocks.
- **Selective magnetic snap.** Only if `SNAP-combo` returns ≥ +0.010: move only dots whose own
  surface percentile is below 0.4, and only onto a crest ≥ 0.90. *Falsifier:* the moved fraction
  collapses below 1 % (measured: a 0.85/0.05 gate already leaves 12 % on `tmi_hg`, 6 % on `combo`).
- **Exact-marginal PRUNE.** Remove the dots with the most negative exact ΔDTI under the shared
  two-sided metric. *Confounder:* proxy-truth shift; *falsifier:* no replicated positive sign on
  untouched spatial folds.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation · any submission-page
receipt (R0's 0.2778 included) · which fill form the portal accepted last time · confirmation that
the data-use terms permit keeping competition rasters out of this public repo (release TIFFs stay
gitignored, IR-86-PRUNE-04).
