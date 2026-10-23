# SLOT PLAN — 2026-10-23, after the RELIEF axis (AXIS assigned by the human)

**No automatic slot use.** One entity, ≤3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); `TOP_PUBLIC` and the remaining quota are
**UNSUPPLIED** and were not guessed. A live `|Δ| < 0.01` is no evidence. R0 = `h33-h33-2-b2`
(**0.2778 CLAIM**, no receipt anywhere in `ledger/` — 115 rows, `receipt=N` on all of them).
2026-10-23 → 2026-12-03 is 41 days ≈ 5.9 weeks ⇒ ≈17 slots, one of which is the blind final pick.
Deadline date is user-supplied and **UNVERIFIED** (the competition page is not fetched from here).

Every number below is a **MODEL** projection on a USGS SGMC hide-and-recover surrogate
(`evidence/relief_axis_20261023.json`), never a score. The catalogue hide-and-recover PROXY is at
its floor for this lineage and is not in the decision path (IR-86-PRUNE-03).

## Next three slots, in order

| # | file (upload the `-zeros` twin) | what it is | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | 5,648 dots relocated piedmont→range-front, count fixed at 37,654, 15.0 % changed, mean displacement 6.1 km. The max dose the axis contract allows and the only RELIEF rung with a positive surrogate read (+0.0017, 3/4 quadrants). | ≥ +0.010 → the front is unsaturated: next build is RELIEF-ADD (insert, don't move) at 25–30 %. ≤ −0.005 → the front population is already covered; RELIEF closes for Phase 1. Inside ±0.01 → no conclusion, which is the expected outcome and is why slot 3 exists. |
| 2 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | the deepest collar rung (2,171 dots deleted, 5.77 % changed, +0.004 MODEL), already built and gated by PR #29. Kept because it is a *different kind* of edit — deletion, not relocation — so its result is additive to slot 1's, not redundant. | ≥ +0.010 → PRUNE is not exhausted and the front+collar combination becomes the next file. Flat/negative → the prune lineage is finished for Phase 1 and the mass budget moves to RELIEF-ADD. |
| 3 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontm10-20261023-1b26223e-zeros.tif` | the sign flip: 3,765 dots relocated front→piedmont, −0.0089 MODEL, sign negative in 4/4 quadrants (the only replicated sign on this axis). **Only if slots 1–2 both land inside ±0.01.** | Spend it for the *paired* read: +15 vs −10 is a 25 %-of-mass swing whose predicted separation (~0.011) is the only RELIEF comparison that can clear the evidence floor. Skip it if slot 1 already moved ≥0.01 or ≤−0.01 — then the direction is known and a third dose adds nothing. |

`front+10pct` (`b20ef72e`) is the nested middle rung: it is in the ledger and downloadable, but it
is the one file here whose result is implied by the other two, so it is the designated **fallback
substitute** if the human prefers a smaller first edit. The in-regime displacement control
(surrogate −0.0010) was measured, not written: controls never take a slot.

**Do not spend a slot on:** `…-prune3-…-01d57649` (same `(PRUNE,3)` pair as slot 2), `…-prune4…`
and `…-prune3r…` (rehearsals, both predicted negative), `…-PRUNE-le2p236/le2p828` (shallower
rungs of the same ladder), and `…-prune3-…-3eb29af5` (withdrawn, IR-86-PRUNE-08).

## Weeks to the deadline

- **wk 1** (this week, ≤3 slots): slots 1–3 above. Nothing else — four sessions have now built
  seven files on one parent, and each additional unsubmitted file costs review time, not feedback.
- **wk 2**: combine or close. If either of slots 1–2 cleared +0.010, build
  `front+15pct ∧ le3p000` as one attributable edit (both singles exist, so the combination is
  interpretable). If both were flat, switch the week to **RELIEF-ADD** (insert 5,648–11,296 front
  dots, count 43,302–48,950 — crossing the 44k band is itself the test) and preregister it first.
- **wk 3–4**: one more *mechanism* axis, SNAP only if the human assigns it (its inputs —
  `tmi_hg`, `iso_grav_anom_slope`, the pinned 3DEP scarp stack — are restored and verified here;
  the blocker recorded in IR-86-PRUNE-05 is gone). Then re-cut the best axis at a second value.
- **wk 5**: confirm the leader, freeze two finalists, re-run the format gates on the exact bytes to
  be uploaded, and re-check both twins against the ledger for exact-hash repeats.
- **wk 6** (before 2026-12-03): no experiments. The human submits the blind final pick from one
  registered account, writes the receipt into `ledger/submissions.csv` (`receipt_score`, `date`,
  `receipt=Y`, `evidence_class=RECEIPT`) and keeps the fallback file unreproduced.

## Better axes (proposals only; not built this session)

1. **RELIEF-ADD** — insert front dots instead of moving them. *Mechanism:* a max-kernel numerator
   cannot be improved by relocating a dot that already covers its truth pixel, and relocation pays
   a measured ~0.001 displacement cost that insertion does not. *Confounder:* mass is confounded
   with field (brief §3); 43.3k–49.0k dots bracket the best-file band, so keep the first build at
   the low end. *Falsifier:* no gain while `front+15pct` gains ⇒ the front is saturated, not sparse.
2. **Corroboration-ranked insertion** — place new dots by SGMC-extra proximity *and* gradient
   support. *Mechanism:* targets the population the metric actually pays. *Confounder:* it optimises
   against a proxy for the label set, not the label set — the sources are undisclosed
   ([forum 11527](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527)),
   and the mapping-completeness bias in relief would be baked in rather than tested.
   *Falsifier:* a gain here with no gain from plain RELIEF-ADD means the corroboration term, not
   relief, is doing the work — which is a Phase-2 expert-review argument, not a Phase-1 score lever.
3. **Annulus-conditional RELIEF** (carried from the ladder plan): test the 200–300 m annulus per
   relief tercile instead of moving whole populations. *Confounder:* relief controls both catalogue
   completeness and lineament visibility. *Falsifier:* no consistent sign across two relief regimes
   on untouched spatial folds ⇒ no live slot.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used in this rolling week · deadline confirmation on the competition
page · any submission-page receipt (R0's 0.2778 included) · which fill form (`-zeros` or `-nan`)
the portal accepted last · **authorization for any slot** — nothing here is authorised to be uploaded
by an agent, and the agent never submits.
