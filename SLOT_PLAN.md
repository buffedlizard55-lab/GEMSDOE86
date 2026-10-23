# SLOT PLAN — one entity, 3 scored submissions per rolling week, final file blind

Deadline **2026-12-03** is the brief's date and is **UNCONFIRMED**: the competition page
cannot be fetched from this sandbox (termsofuse bans automated access), so the human must
confirm it. Today 2026-10-23 ⇒ **≈ 5.9 weeks / ≈ 17 slots** if the weekly quota holds.

`TOP_PUBLIC` is **blank**. The owner prompt quotes two different leaderboard maxima
(0.3195 and 0.4413, undated, no receipt). Neither is a valid target until the human supplies
a dated number from their own leaderboard view. Until then this plan optimises against
**R0 = 0.2778 (CLAIM)**, and every predicted delta below is MODEL, not a score.

## Next three slots, in order

| # | File | Axis · value | Single change vs R0 | Predicted live | What the result changes |
|---|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-3eb29af5-nan.tif` (fallback `…-4bd30478-zeros.tif`) | PRUNE · 3 | drop the 2,171 dots at 2 < d ≤ 3 px (5.77 % of mass) | **−0.003** (MODEL, range −0.010…+0.004) | Is the 3 px collar live or dead? Downside is bounded and small, so this is the cheapest calibration of the only operator that ever raised the lineage (+0.0070 claimed from the 2 px step). |
| 2 | if slot 1 ≥ R0+0.01 → `…prune4…-e198b768-nan`; if slot 1 ≤ R0−0.01 → **hold R0**, do not spend slot 2 on a wider collar | PRUNE · 4 | drop 3,825 dots (10.16 %) | **−0.008** (MODEL) | Confirms or kills monotonicity in collar width. A negative here ends the PRUNE axis and frees the remaining slots for a different axis. |
| 3 | `releases/h33-2-b2-prune3r-20261023-9542efac-nan.tif` — **only** if slots 1–2 are within ±0.01 of each other | PRUNE · 3r | same deletions as slot 1, equal count relocated to 3 < d ≤ 5 px (mean move 1.14 px) | **−0.003** (MODEL) | Separates *mass* from *collar position*. If it differs from slot 1 by ≥ 0.01, mass is not the lever and every later axis must hold count fixed. |

Rule carried from the brief: **a live change under 0.01 is no evidence.** Two of the three
predictions sit under that bar; that is stated up front, not discovered afterwards. The
reason to run slot 1 anyway is that its *falsifier* is decisive for the next four weeks:
it tells us whether to spend the remaining ~14 slots pushing the collar outward or to never
touch it again.

Do **not** re-submit R0 or its `-zeros` twin: at least 8 historical slots already went to
exact repeats (brief §3), and the zeros/NaN twins score identically.

## Weeks to the deadline (default plan, unchanged axis order)

* **wk 1–2 (slots 1–3 above).** PRUNE collar sweep. Exit test: any variant ≥ R0 + 0.01.
* **wk 2–3. MASS and RELIEF.** Blocked this session only because R0's ranking is not stored
  and `gems32` is absent; both become cheap once the ranking is recovered (see below).
  MASS: ±10 % by the parent's own rank, count held. RELIEF: shift 10–15 % of mass between
  basin / piedmont / range-front terciles from `det_elev`, count fixed.
* **wk 4. CONCENTRATION** on km-scale blocks: move 10–20 % of dots from the lowest-prior to
  the highest-prior 5 km blocks; record block-density CV (best files reportedly 0.51–0.59).
* **wk 5. Combine** the two best axes with a single-change ablation so the combination is
  still attributable, plus one SNAP probe (dots to the strongest `tmi_hg`/`iso_grav_anom_hg`
  edge within 2 px, same count, report mean displacement).
* **wk 6. Confirm and freeze.** Re-validate the format of the chosen file and one fallback;
  final submission is chosen blind among the two.

## Better axes proposed (mechanism · confounder · falsifier) — do not build this session

1. **COLLAR-FILL (PRUNE, value 2.5 inward).** *Mechanism:* if the 3 px prune is negative, the
   collar is short of dots and the operator should run the other way — add mass at 2 < d ≤ 3
   by the parent's own rank. *Confounder:* adds false-positive mass that never earns credit
   on masked pixels. *Falsifier:* live drop > 0.01 vs R0 kills the direction.
2. **SPACING-ALONG-STRIKE.** *Mechanism:* the metric credits each truth cell once through
   `max`, so mass is best spent at the 3 px spacing scale along the trace, not across it.
   *Confounder:* near-parallel lithological contacts also reward along-strike spacing.
   *Falsifier:* a Poisson-disk control at the same count scoring the same within ±0.005.
3. **RELIEF-TERCILES.** *Mechanism:* new faults in this basin concentrate at range-front /
   piedmont transitions. *Confounder:* the same terciles host the strongest topographic
   artefacts (alluvial fan edges), which is exactly what a false positive looks like.
   *Falsifier:* a tercile-shuffled control at matched count scoring as well.

## Human inputs still missing

`TOP_PUBLIC` + date · slots used this rolling week · deadline confirmation · one
submission-page receipt for any claimed score (R0's 0.2778 included) · which of the two
fill forms the portal accepted last time (the vendored validator only accepts the
all-finite form).
