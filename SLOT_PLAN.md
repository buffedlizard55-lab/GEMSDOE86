# SLOT PLAN — 2026-10-23, reconciled across three PRUNE sessions

**No automatic slot use.** One entity, ≤ 3 scored submissions per rolling week
([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)); the remaining quota and
`TOP_PUBLIC` are **UNSUPPLIED by the human** — I did not guess them. A live `|Δ| < 0.01`
is no evidence. R0 = `h33-h33-2-b2` (**0.2778 CLAIM**, no receipt in `ledger/`).

Deadline arithmetic: 2026-10-23 → **2026-12-03** is 41 days ≈ 5.9 weeks ⇒ ≈ 17 slots,
one of which is the blind final pick. The date is user-supplied and **UNVERIFIED**
(DrivenData is not contacted from this sandbox).

Seven gate-clean PRUNE artifacts now exist, from three sessions on one parent. The axis is
**crowded**: everything left in the collar ladder is 2,171 dots = 5.8 % of the mass, and the
best available per-dot rate puts the whole ladder inside ±0.01. So PRUNE gets **one slot**,
not three.

## Next three slots, in order

| # | file (upload the `-zeros` twin) | why this one | decision rule |
|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | the deepest rung of the nested ladder (941 + 670 + 560 = 2,171 dots removed; 35,483 dots; 5.77 % changed). Prediction **+0.004 MODEL** (band −0.004…+0.013). One slot buys a monotone read: R0 → r2.236 → r2.828 → r3.000. | ≥ +0.010 → the collar is not exhausted; next week build a single 4 px rung. Flat or ≤ −0.010 → the prune lineage is finished for Phase 1. |
| 2 | **a new prediction surface, not another prune rung** — the 19-band stack is proven restorable (below) | the prune ladder cannot move the score by more than ~±0.01; beating 0.2778 needs a different axis | SNAP or RELIEF, preregistered with mechanism/confounder/falsifier before building; one axis only |
| 3 | the better of (1) and (2), re-cut at a different value on the axis that moved | one more point on the winning axis | keep the loser as the fallback file |

**Do not spend a slot on:** `…-prune3-…-01d57649` (same `(PRUNE, 3)` pair as slot 1, different
refill; only interesting *after* a rung shows ≥ +0.01, when mass versus proximity decides the
next edit); `…-CONTROL-massctl2171…` (a control, not a candidate); `…-prune3-…-3eb29af5`
(**withdrawn** — its dot set is identical to `le3p000`, IR-86-PRUNE-08).

**Cheap defaults if slot 2 is not ready in time** (both built, gated, and unlike anything on
main): `releases/h33-h33-2-b2-prune4-20261023-de4c2a98[-zeros].tif` (PRUNE ≤ 4 px, 33,829 dots,
−0.008 MODEL) and `releases/refill/h33-h33-2-b2-prune3r-20261023-8c20bd7e[-zeros].tif`
(equal count, collar relocated past 3 px, mean move 1.14 px, −0.003 MODEL). The refill design
sits in `releases/refill/` because a PRUNE release in `releases/` may only delete dots. Neither is predicted to help; they are rehearsals, not bets.

## Why the feature stack is no longer the blocker

PR #29's plan called restoring `training_features.tif` (419 MB) the gate for every remaining
axis. It is **open**: this session ran

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
python scripts/restore_data.py --with-external        # 22 s, sha256-verified
```

and the stack verified against its pin `4371c82e…3bc5`; five external rasters verified too.
Needs ~420 MB of disk (gitignored; the pytest suite copies the tree into `/tmp`, so clear
`/tmp/pytest-of-user` if the disk fills). With the stack present, this session measured
label-free band response per dot set — the collar is **not** evidence-poor (`tmi_hg` percentile
0.528 at the collar vs 0.542 elsewhere; `iso_grav_anom_hg` 0.557 vs 0.514).

## Calendar to the deadline

- **wk 1 (slot 1).** The deepest collar rung. Single decisive read on PRUNE.
- **wk 2–3 (slots 2–3).** SNAP (preregistered: move each dot ≤ 2 px to the strongest
  `tmi_hg`/`iso_grav_anom_hg` edge, same count, report mean displacement; falsifier: mean
  displacement < 0.5 px makes it a no-op) **or** RELIEF (shift 10–15 % of mass between basin /
  piedmont / range-front terciles, count fixed).
- **wk 4.** CONCENTRATION on 5–10 km blocks, only at blocks > 3 px clear of the catalogue
  (the collar result already argues against stacking mass next to mapped traces); record the
  block-density CV.
- **wk 5.** Combine the two axes with receipt-level effects ≥ 0.01 as one attributable edit.
- **wk 6.** Confirm both finalists, revalidate both formats, choose the final file and a
  fallback blind, never multiply accounts.

## Better axes (proposals only; not built this session)

- **Collar fill inward (PRUNE, 2.5).** If slot 1 is negative, the annulus is short of dots.
  *Confounder:* added mass can never earn credit on masked pixels. *Falsifier:* a live drop
  > 0.01 versus R0 kills the direction.
- **Exact-marginal PRUNE.** Remove dots with the most negative exact ΔDTI under the shared
  two-sided metric. *Confounder:* proxy-truth shift. *Falsifier:* no replicated positive sign
  on untouched spatial folds, then no live receipt.
- **Annulus-conditional RELIEF.** Test the 200–300 m annulus per relief tercile.
  *Confounder:* relief controls both catalogue completeness and lineament visibility.
  *Falsifier:* no consistent sign in two relief regimes on held-out physical blocks.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation · any
submission-page receipt (R0's 0.2778 included) · which fill form the portal accepted last time.
