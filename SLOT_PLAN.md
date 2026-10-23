# SLOT PLAN — 2026-10-23 (rev. C: RELIEF instrument audit re-ranks the top three)

**No automatic submission.** One entity, ≤ 3 scored submissions per rolling week, 1 blind final pick
([official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Deadline 2026-12-03 (`UNVERIFIED`
portal clock; ~5.9 wk ⇒ ~17 slots max, minus the final pick). Parent **R0 = `h33-h33-2-b2`**
(GEMSDOE32), 37,654 unit-mass dots, `0.2778` is **CLAIM** (0 `RECEIPT` rows in
`ledger/submissions.csv`). `TOP_PUBLIC`, rolling-week quota left and R0's receipt are **UNSUPPLIED**.
Live `|Δ| < 0.01` = no evidence.

## What changed this session (rev. B → rev. C)

**The only instrument that supports RELIEF is a relief-index meter.** Eight deterministic RELIEF
rebuilds (3 shipped + 3 new + 2 displacement-matched nulls) scored on the SGMC-extra surrogate give
`surrogate Δ ≈ 0.0283 · Δ(mean relief index) − 0.0033`, **r = +0.956, R² = 0.9135, n = 8**
(`IR-86-RELIEF-04`, `evidence/relief_source_20261023.json`). `front+15pct`'s `+0.0017` is fully
explained by its `+0.206` index shift (residual **−0.0008**); the zero-index nulls cost `−0.0026` to
`−0.0030`. **Consequence:** RELIEF MODEL numbers are not mechanism evidence, and the shipped RELIEF
row drops from Slot 1 to Slot 3.

**Three new RELIEF arms are built, gated and ledgered, and none is slot-recommended**
(`RELIEF int2front-15pct` `c543e779` `−0.0057`, `int2front-10pct` `4471a74b` `−0.0038`,
`int2pied-15pct` `295eaf92` `−0.0118`; all MODEL, 1/4 quadrants positive, PROXY 0.0037–0.0041 vs
R0 0.0044). The pre-registered sign was **falsified** (`evidence/relief-source-mechanism.md`).
The basin source cannot be tested at all: basin holds 2,014 dots = 5.35 %, below RELIEF's 10 % floor
(`IR-86-RELIEF-05`).

## Next weekly slots (new order — one file per slot, `-zeros` twin unless the portal rejects zeros)

| Slot | Candidate (`releases/<id>`) | Edit vs R0 | Predicted Δ (not a score) | Decision rule on live `RECEIPT` Δ vs 0.2778 |
|---:|---|---|---|---|
| **1** | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | delete 2,171 dots (`5.77 %`) inside the `2.0 < d_cat ≤ 3.0 px` collar | `+0.0040 MODEL` (monotone collar ladder; Δrelief-index ≈ 0, so the bias above cannot manufacture it) | `≥ +0.010`: the collar halo is real drag → test `3.5 px` and combine with Slot 2. `≤ −0.005`: keep R0's collar, close PRUNE. Inside `±0.010`: run Slot 2. |
| **2** | `…-concb5kmdown4-20261023-8aab97b6-zeros.tif` | 1,506 dots (`8.00 %`) shaved from `≥3`-dot 1 km clusters onto sparse-block ancestor ridges (`1 km CV 0.6235 → 0.5162`) | `+0.0015 MODEL` (4/4 quadrants `+`) **and** `+0.0008 PROXY` `[−0.0004, +0.0018]` — two differently-biased instruments agree | `≥ +0.010`: over-clustering was binding → test a 6 % ridge-dispersal dose and combine with Slot 1. `≤ −0.005`: the `0.51–0.59` CV band is falsified, close CONCENTRATION. |
| **3** | `…-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` *(demoted: `+0.0017` MODEL = instrument gradient, `IR-86-RELIEF-04`)* | 5,648 dots (`15.0 %`) piedmont → range-front, count fixed | `+0.0017 MODEL` — **no longer mechanism evidence**; unbiased prior ≈ `0 ± 0.005` | `≥ +0.010`: the front destination beats the instrument's own gradient → restore RELIEF and combine. `≤ −0.005`: close RELIEF entirely. Inside `±0.010`: close as unmeasurable at this effect size. |
| 4 (spare) | `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif` | 7,027 crowded dots re-spaced along strike (`S` fixed) | `+0.0020 MODEL` (`+0.0018` vs random control) | Probe only if Slots 1–3 all land inside `±0.005`. |

**Never upload:** all three new `int2*` RELIEF arms; `conc15` (`−0.0071`), `dens15`/`spr15`
(`−0.0006`/`−0.0013`), `b5km-move10/15/20` (`−0.0066…−0.0150`), `concb5kmup4/8`, all MASS arms, all
SNAP arms, `trackb-cull1dot`, and every `CONTROL` / `BUILT-DUPLICATE` / `withdrawn` row.

## Calendar to 2026-12-03

* **Wk 1:** Slots 1–3, in order, logging each live `RECEIPT` + portal timestamp in
  `ledger/submissions.csv` before the next upload. If Slot 1 clears `+0.010`, spend Wk 2 on the
  `3.5 px` collar rung rather than on Slot 3.
* **Wk 2–3:** second dose on whichever axis cleared `|Δ| ≥ 0.01`; if all are flat, run Slot 4 and
  spend the remaining slots on the best *receipt-verified* pair.
* **Wk 4–5:** single attributable combination of receipt-verified levers only (`> 3.0 px` clearance,
  `≤ 11,415` sub-kernel pairs, no relief edit).
* **Wk 6:** re-validate both finalists on disk (format, hashes, disk re-read), choose 1 blind final
  file + 1 fallback, freeze `AI_USE.md` and the reproducibility pins.

## Unbuilt proposals (mechanism / confounder / falsifier — deliberately not built here)

1. **Collared combination (`le3p000` × `concb5kmdown4`), wk 4.** *Mechanism:* delete the `2–3 px`
   halo **and** disperse `≥3`-dot sub-kernel clusters → two independent drags removed at once.
   *Confounder:* both reduce local mass, so part of the joint gain may be a MASS effect, which is
   closed (`IR-86-MASS-03`). *Falsifier:* combination live Δ ≤ max(single-lever live Δ).
2. **10 km fault-system concentration (`CONCENTRATION-10km`, `IR-86-TRACKB-08`).** *Mechanism:* match
   the 10 km occupied-block CV band (`0.547–0.570`) that every `≥ 0.26` file sits in, instead of the
   1 km/5 km scales already spent. *Confounder:* 10 km blocks co-vary with the two flight regimes
   (400 m vs 200 m line spacing). *Falsifier:* `< +0.001` over `concb5kmdown4` on the SGMC surrogate
   with the relief-index term held fixed (the new control design in `IR-86-RELIEF-04`).
3. **A non-relief instrument for relief.** *Mechanism:* build the RELIEF prior from published
   Quaternary-fault maps (USGS SGMC is already pinned) filtered to *basin-margin* traces only, and
   score candidate arms against that rather than against a raster whose density is itself relief.
   *Confounder:* SGMC and the training catalogue share a provenance lineage. *Falsifier:* the
   instrument's rank correlation with the shipped RELIEF ladder is < 0.5.
4. **Collar-funded `TRACKB` (`IR-86-TRACKB-03/07`), Phase 2 only.** Fund `≥1 km` gap bridges from
   `PRUNE le3p000` collar dots on traces surviving 30° grid rotation + AGC `TMI_up150`.
   *Falsifier:* survival within `±5 %` of random-azimuth lineaments.

**Human inputs still required:** `TOP_PUBLIC` + date · rolling-week slots left · verified deadline ·
R0's `0.2778` portal receipt · accepted outside-footprint encoding (`.tif` NaN vs `-zeros` fallback) ·
organizer uniqueness rule (`IR-86-PRUNE-01`).
