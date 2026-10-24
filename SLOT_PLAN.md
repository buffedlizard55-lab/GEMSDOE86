# SLOT PLAN — 2026-10-23 (rev. D: merges the RELIEF instrument audit and the CONCENTRATION dose ladder)

**No automatic submission.** One entity, ≤ 3 scored submissions per rolling week, 1 blind final pick
([official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Deadline 2026-12-03 (`UNVERIFIED`
portal clock; ~5.9 wk ⇒ ~17 slots max, minus the final pick). Parent **R0 = `h33-h33-2-b2`**
(GEMSDOE32), 37,654 unit-mass dots; `0.2778` is **CLAIM** (0 `RECEIPT` rows in
`ledger/submissions.csv`). `TOP_PUBLIC`, rolling-week quota left and R0's receipt are **UNSUPPLIED**.
Live `|Δ| < 0.01` = no evidence.

## What the two 2026-10-23 sessions changed

**A. `CONCENTRATION` is monotone in dose and partly generic dispersal (PR #50).** `conc3` `+0.0013` →
`conc5dose` `+0.0018` → `conc6` `+0.0022 MODEL` (4/4 quadrants; `+0.0013` PROXY) while 1 km occupied
CV falls `0.5377 → 0.4998 → 0.4840`, so the historical `0.51–0.59` band is a correlate, not the cause
(`IR-86-CONC-13`). The matched ordering control (same blocks, same count, random dot, random
destination) gets `+0.0015` / `+0.0008 PROXY`, so **the ranking buys only ≈ `+0.0007`**. The axis is
capacity-capped at ≈ 6.4 % of R0 (`IR-86-CONC-12`) — pinned exactly by the PR #55 rungs session:
the binary-searched sparse-ridge destination-pool ceiling is **2,381 moves** (`b5km-cvband-downmax`,
`d4a42664`, CV 0.4789), and the 122 moves past `conc6` cost more than they bought (`+0.0020` vs
`+0.0022` MODEL, 4/4 quads). The same session added the low rung `b5km-cvband-down2` (`f0ee647f`,
753 moves, CV 0.5611, `+0.0012` MODEL 4/4, `+0.0001` PROXY), so the curve is now measured at
753 / 1,130 / 1,506 / 1,883 / 2,259 / 2,381 moves and is monotone to the pool ceiling
(`IR-86-CONC-15` records that PR #55's `down6` rebuilt PR #50's `conc6` byte-identically).
`conc6` supersedes `concb5kmdown4` on both instruments at 753 extra moved dots.

**B. `RELIEF`'s only instrument is a relief-index meter (PR #51).** Eight RELIEF rebuilds (3 shipped +
3 new + 2 displacement-matched random nulls) score on the SGMC-extra surrogate as
`Δ ≈ 0.0283·Δ(mean relief index) − 0.0033`, **r = +0.956, R² = 0.9135, n = 8**; the `front+15pct`
reconstruction reproduces its ledger `+0.0017` exactly and sits **−0.0008 below the fit**, and the
zero-index nulls cost `−0.0026…−0.0030` (`IR-86-RELIEF-04`). RELIEF MODEL deltas are therefore not
mechanism evidence, and `frontp15` drops to Slot 3. The new source arms are all negative
(`−0.0057 / −0.0038 / −0.0118`) and the pre-registered sign was falsified
(`evidence/relief-source-mechanism.md`). The basin source holds 2,014 dots (5.35 %), below RELIEF's
10 % dose floor, so the alluvium question cannot be asked on this parent (`IR-86-RELIEF-05`).

## Next weekly slots (one file per slot, human uploads; `-zeros` twin unless the portal rejects zeros)

| Slot | Candidate (`releases/<id>`) | Edit vs R0 | Predicted Δ (MODEL, not a score) | Decision rule on live `RECEIPT` Δ vs 0.2778 |
|---:|---|---|---|---|
| **1** | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | delete 2,171 dots (`5.77 %`) in the `2.0 < d_cat ≤ 3.0 px` collar; 35,483 dots | `+0.0040` — largest lever, and its Δrelief-index ≈ 0 so the bias in §B cannot manufacture it (partly mass-confounded, `IR-86-MASS-04`) | `≥ +0.010`: collar halo is real drag → next slot probes `4.0 px` and combines with Slot 2. `≤ −0.005`: keep the 2 px collar, close PRUNE. Flat: run Slot 2. |
| **2** | `h33-h33-2-b2-20261004-e5eb6e7e-conc6-20261023-1ed78e0f-zeros.tif` *(replaces `concb5kmdown4`)* | 2,259 dots (`12.0 %` changed) shaved from `≥3`-dot 1 km clusters onto sparse-block ancestor ridges; 1 km CV `0.6235 → 0.4840`; count fixed | `+0.0022` (4/4 quads, `+0.0007` above its own dispersal control), `+0.0013 PROXY` | `≥ +0.010`: density-cap dispersal is a real lever → 6 % is the ceiling, so combine rather than dose up. `≤ −0.005`: dispersal is neutral-to-negative on private chunks → close CONCENTRATION. |
| **3** | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` *(demoted)* | 5,648 dots (`15.0 %`) piedmont → range-front, count fixed | `+0.0017` headline, but **unbiased prior `0 ± 0.005`**: the headline is the instrument's relief gradient (§B) | `≥ +0.010`: the front destination beats the instrument's own gradient → restore RELIEF and combine. `≤ −0.005`: close RELIEF. Inside `±0.010`: close as unmeasurable at this effect size. |
| 4 (spare) | `…-conc5dose-20261023-a2f8aaad-zeros.tif` | 1,883 dots (`10.0 %`), CV `0.4998` | `+0.0018` MODEL / `+0.0010` PROXY | Paired dose point for Slot 2 only if Slot 2 returns a positive but sub-0.01 Δ. |

**Never upload:** the three new `int2*` RELIEF arms; `conc6rand` (`CONTROL`); `conc15` (`−0.0071`),
`dens15`/`spr15` (`−0.0006`/`−0.0013`), `b5km-move10/15/20` (`−0.0066…−0.0150`), `concb5kmup4/8`
(`−0.0005`/`−0.0007`); all MASS arms; all SNAP arms; `trackb-cull1dot`; every `BUILT-DUPLICATE` /
`withdrawn` row.

## Calendar to 2026-12-03

* **Wk 1:** Slots 1–3 in order, logging each live `RECEIPT` + portal timestamp in
  `ledger/submissions.csv` before the next upload. If Slot 1 clears `+0.010`, spend Wk 2 on the
  `4.0 px` collar rung instead of Slot 3.
* **Wk 2–3:** second dose only on an axis that cleared `|Δ| ≥ 0.01`; otherwise the next-best levers.
  A paired CONCENTRATION A/B (ranked `conc6` vs its own control) is the only clean way to price the
  ranking and costs two slots — not before one lever proves real.
* **Wk 4–5:** one attributable combination of receipt-verified `≥ +0.01` levers (at most two, so the
  result stays attributable), with **no relief edit** in the mix.
* **Wk 6:** re-validate both finalists on disk (format, hashes, disk re-read), lock one blind final
  file plus one fallback, freeze `AI_USE.md` and the reproducibility pins.

## Unbuilt proposals (mechanism / confounder / falsifier — not built here)

0. **Pool-extension `CONCENTRATION` rung beyond the ceiling (`downmax-plus`).** *Mechanism:* the ceiling at 2,381 moves is the 1–2-dot destination pool running dry; extend destinations to 3-dot blocks (or the strict 1-dot-only mirror) past the ceiling and read whether the marginal `−0.0002` (`conc6`→`downmax`) is destination-quality decay or a hard mechanism limit. *Confounder:* 3-dot destinations re-create the sub-kernel overlap the shave removed. *Falsifier:* `MODEL ≤ conc6` again with CV still > 0.47 ⇒ the mechanism, not the pool, is exhausted.

1. **Kernel-credit saturation pruning (`MASS` at fixed count).** *Mechanism:* replace the 1 km-CV rule
   with a direct per-dot marginal-`DTI` ranking from the metric code, delete the lowest-ranked dots
   and refill at the largest kernel gaps, so the edit targets numerator `T` instead of block
   statistics. *Confounder:* the ranking is only as good as the surrogate, and mass is monotone on
   that instrument (`IR-86-MASS-03`). *Falsifier:* `≤ 0` live Δ.
2. **A non-relief instrument for relief (§B fix).** *Mechanism:* build the RELIEF prior from the
   pinned public-domain SGMC inventory filtered to **basin-margin** traces only, and score arms
   against that rather than against a raster whose density is itself relief. *Confounder:* SGMC and
   the training catalogue share a provenance lineage. *Falsifier:* rank correlation with the shipped
   RELIEF ladder `< 0.5`.
3. **10 km fault-system concentration (`IR-86-TRACKB-08`).** *Mechanism:* every `≥ 0.26` historical
   file sits in a 10 km occupied-block CV of `0.547–0.570`; test that scale instead of the 1 km and
   5 km scales already spent. *Confounder:* 10 km blocks co-vary with the two flight regimes (400 m
   vs 200 m line spacing). *Falsifier:* `< +0.001` over `conc6` with the relief-index term held fixed.
4. **Collar-funded `TRACKB`, Phase 2 only (`IR-86-TRACKB-03/07`).** Fund `≥ 1 km` gap bridges from
   `PRUNE le3p000` collar dots on traces surviving 30° grid rotation + AGC `TMI_up150`. *Falsifier:*
   survival within `±5 %` of random-azimuth lineaments.

**Human inputs still required:** `TOP_PUBLIC` + date · rolling-week slots left · verified deadline ·
R0's `0.2778` portal receipt · accepted outside-footprint encoding (`.tif` NaN vs `-zeros` fallback) ·
organizer uniqueness rule (`IR-86-PRUNE-01`).
