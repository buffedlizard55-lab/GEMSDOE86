# SLOT_PLAN — 3 scored submissions/week, one entity, deadline 2026-12-03

Plan only. No file here has a receipt: every score in `ledger/submissions.csv` marked `CLAIM`
stays a claim until a line copied from the submission page is pasted into `receipt_score`.

## What the SNAP session established (before any slot is spent)

| Item | Value |
|---|---|
| Parent R0 `h33-h33-2-b2` | 37,654 dots, sha `c55bafc…`, 0 catalogue mass, **CLAIM 0.2778** |
| R0 rebuilt from its recorded recipe | dot-set symdiff **0 px** (`evidence/snap_variants.json`) |
| SNAP variants built and gated | `snap-hg2` 43.4 % moved, `snap-vg2` 48.3 %, `snap-cons2` 54.7 %; mean displacement 2.31–2.36 px; spacing floor held at 2.828 px; all format/catalogue/count checks pass |
| Hide-and-recover PROXY (n = 45,260 withheld positives) | parent 0.0047 → variants 0.0150 / 0.0169 / 0.0190 |
| **Same proxy with a fixed ≥3 px collar on every candidate** | **0.0000 for all four**, and 0.0000 for the SGMC control that scores 0.0877 without the collar |
| H19-5 rank readout | parent dots sit at the 98.8th percentile of the lineage's own ranking field; the variants drop to 69.7–75.1 |

Two consequences, both of which change the plan:

1. **The free proxy is blind here.** Its entire signal is catalogue-collar recovery. Any edit that
   puts mass back beside a known trace "improves" it, which is exactly what the live metric
   penalises. It is still recorded as a PROXY and never used as a gate.
2. **SNAP spends real lineage evidence to buy an unproven edge.** Every variant trades the parent's
   own top-1 % ranking for a magnetic-gradient peak 2.3 px away, and puts 1.3–1.8 % of the dots
   back inside the 200 m collar whose removal is the only controlled edit with a live-claimed gain
   (+0.007, 0.2708 → 0.2778). Predicted live change is therefore stated as a range that straddles
   zero, and the honest expectation is "no evidence" (|Δ| < 0.01) rather than a win.

## The next three slots, in order

| # | File | One thing it decides | If it lands | If it does not |
|---|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-snap-cons2-20261023-43829550.tif` | Does a ≤ 2 px re-centring on a magnetic edge move the live score at all? (widest field, most robust to one band's artefacts) | Δ ≥ +0.01 ⇒ kernel-scale position, not field choice, was the binding constraint; commission the SNAP+PRUNE combination (destinations forced outside the collar) | Δ within ±0.01 ⇒ position is already optimal at kernel scale; retire SNAP and spend the rest of the quota on mass/geometry axes |
| 2 | `releases/h33-h33-2-b2-snap-hg2-20261023-718658bc.tif` | Is the single horizontal-gradient field enough, i.e. did the consensus add anything? (cleanest mechanistic attribution) | hg2 ≈ cons2 ⇒ use the simpler field for the combination; hg2 > cons2 by ≥ 0.01 ⇒ sharpness/consensus was diluting | hg2 < cons2 − 0.01 ⇒ keep consensus; both flat ⇒ SNAP closed as a lane |
| 3 | Hold | Reserved for the week's best MASS or CONCENTRATION variant, or for `snap-cons2` re-cut with every destination forced to ≥ 3 px from the catalogue | keeps one slot responsive to whichever axis the first two results point at | if both SNAP slots are flat, this slot goes to the collar dose-response below |

Do **not** spend a slot on an exact re-submission of R0: the ledger already records ≥ 8 slots lost to
exact repeats, and a repeat cannot separate "no change" from "no effect".

## Weeks to the deadline (today 2026-10-23 → 2026-12-03)

* **wk 1 (now)** — SNAP trio above; 2 slots consumed, 1 held.
* **wk 2** — MASS (drop lowest-ranked 10 % / add next-ranked 10 %, ranking rebuilt from the restored
  H19-5 field, not from another lane) and CONCENTRATION (10–20 % of dots between 1 km blocks,
  block-density CV reported against the 0.51–0.59 band). Third slot: whichever of wk 1 pointed at.
* **wk 3** — the two best axes combined in one controlled edit; 2 slots plus 1 for a replication.
* **wk 4–5** — confirm the winner against a second draw of the same axis value; freeze the choice.
* **wk 6** — re-validate format of the final file **and** its zeros twin, re-read both from disk,
  pick the final submission and the fallback blind, leave one slot unused rather than guess.

## Axes proposed for later sessions (none built here)

1. **COLLAR (dose–response, held count)** — mechanism: mass inside the mapped-fault halo earns no
   truth credit but still pays α per dot, so widening the exclusion from 2 to 3 px and refilling the
   removed dots elsewhere should raise DTI if the halo is net-negative. Confounder: a genuine
   parallel new fault within 300 m of a known trace is deleted, and the forum answer says new-fault
   truth *can* lie that close. Falsifier: live Δ ≤ −0.01 at 3 px while the count is held. This is the
   only mechanism with a live-measured precedent, and B = 3 has never been tested with the count
   held (the historical B = 3 lost 2,171 dots, which confounds mass with geometry).
2. **KERNEL-BUDGET (spacing floor at the kernel radius)** — mechanism: at a 2.828 px floor, 30.3 % of
   parent dots sit within 3 px of another dot, so part of the unit mass is spent on credit another dot
   already earns. Re-spacing at ≥ 3.0 px at constant count should convert wasted α into coverage.
   Confounder: real parallel strands and en-echelon step-overs are exactly 300 m apart. Falsifier:
   live coverage loss exceeds the credit gain, i.e. Δ ≤ −0.01.
3. **RE-RANK (position fixed, ranking changed)** — mechanism: the lineage's edge is its ranking, not
   its dot geometry. Hold every dot's position and only re-decide *which* pixels within the same 2 px
   neighbourhood enter the top 37,654 by a strictly label-free, prospectivity-style prior of fault
   interaction zones (step-over / intersection / tip density). Confounder: those zones are also where
   geothermal systems sit, and the target is fault pixels, never vents. Falsifier: live Δ ≤ −0.01,
   which would say the H19-5 ranking is not separable from the local geometry at all.

Rejected as not worth a slot: SPACING (lattice vs Poisson at matched count, already swept), RELIEF
(relief terciles are a proxy for the same piedmont signal the radon/hydro lanes already lost with),
TRACKB (Phase-2 deliverable, needs a geologist's read of each trace).
