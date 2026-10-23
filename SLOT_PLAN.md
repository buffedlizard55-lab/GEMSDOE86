# SLOT PLAN — 2026-10-23 (session 3: CONCENTRATION surface extension; budget argument added)

**No automatic submission.** One entity, `<= 3` scored submissions/rolling week, 1 blind final pick
scored in Phase 1 (DTI, $50k) and Phase 2 ($250k geologist review)
([official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Deadline `2026-12-03` (portal clock
`UNVERIFIED`; ~5.9 wk ⇒ ~17 remaining slots, minus the final pick). `TOP_PUBLIC`, rolling-week quota
remaining and R0's live receipt are **UNSUPPLIED**. Parent **R0 = `h33-h33-2-b2`**
(`37,654` unit-mass dots, sha256 `c55bafc4…b6fa9`, `0.2778` = **CLAIM**, 0 `RECEIPT` rows). Live
`|Δ| < 0.01` = no evidence.

## This session in one paragraph

`AXIS = CONCENTRATION`, new `(parent, axis, value)` keys only. Before building, a capacity audit found
the reason every reallocation arm lands inside ±0.008: **R0 is the `H19-5` ancestor surface dotted at
2.8–3.0 px and it is saturated there — 90 legal free slots remain on `H19-5` — while `H19-4 | H16-1`
ground not on `H19-5` (35,954 px, a surface of near-equal owner-reported quality: 0.1894 / 0.1855 vs
0.1922, all CLAIM) carries **zero** parent mass and 8,671 legal slots.** Three gate-clean files were
built on that unused surface (`surfext10`, `surfext15`) plus a matched random-destination control.
The merged `concb5kmdown4` file was rebuilt byte-exactly (`8aab97b6…`) as the input-integrity check.

**Read the two instruments as brackets, not as evidence.** SGMC-extra MODEL: `+0.0059` (surfext10,
4/4 quadrants), `+0.0073` (surfext15), but the **control at the same dose scores `+0.0047`** — and the
control moves mass *away* from SGMC truth on average, so the instrument's reward is de-clustering, not
lineament knowledge; the ridge-specific increment is `+0.0012 MODEL`. Fold-fair PROXY: `−0.00003`
[−0.0025, +0.0023], `−0.0005` [−0.0038, +0.0027], control `−0.0008` — flat, and biased against this
arm because it can only reward mass near withheld catalogue traces. **Predicted live Δ ≈ 0.000 to
+0.003. Nothing here clears the 0.01 floor; none of the three is slot-approved.**

## Budget arithmetic that governs the rest of the plan (MODEL, not a measurement)

Inverting `DTI = T/(0.2T + 0.2(n−M) + 0.8|G|)` at 0.2778 with `|G| ≈ 40k`: `T ≈ 10,963`, `D ≈ 39,464`.
**+0.01 of live DTI needs ≈418 kernel-credit units ≈ 42 km of fault trace hit squarely** (`|G|` 20k–80k:
24–78 km). Rearranging 2–6k existing dots cannot manufacture that. With 3 slots/week until 2026-12-03,
the only route to a materially higher score is *new fault-line evidence*, so the plan below spends two
slots on the two remaining receipt-worthy reallocations and reserves the rest for evidence work.

## Next weekly slots (upload one file per slot; `-zeros.tif` fallback or `.tif` NaN twin)

| Slot | Candidate | Edit vs R0 | Predicted Δ (not a score) | Decision rule on live `RECEIPT` Δ vs 0.2778 |
|---:|---|---|---|---|
| **1** | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | 5,648 dots (15.0%) piedmont → range front, `S` fixed | **+0.0017 MODEL** (3/4 quads) | `≥ +0.010`: range-front allocation is real → combine with Slot 2 winner. `≤ −0.005`: close RELIEF. Inside ±0.010: run Slot 2 unchanged. |
| **2** | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6-zeros.tif` | 1,506 dots (8.00% chg) shaved from ≥3-dot 1 km clusters onto sparse-block ancestor ridges; 1 km CV 0.6235 → 0.5162 | **+0.0015 MODEL (4/4 quads), +0.0008 PROXY** | `≥ +0.010`: over-clustering was binding → test the surface-extension dose below. `≤ −0.005`: close the whole CONCENTRATION family (this session's arms then never fly). |
| **3** | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | delete 2,171 dots in the 2–3 px catalogue collar (35,483 dots) | **+0.0040 MODEL** (monotone collar ladder; partly mass-confounded) | `≥ +0.010`: collar halo is drag → test a 3.5 px rung. Flat / `≤ −0.005`: keep the 2 px collar; close PRUNE. |
| 4 (spare) | `…-CONC-surfext10-20261023-fe814da5-zeros.tif` **(probe only)** | 3,765 dots off saturated `H19-5` onto `H19-4\|H16-1` (20.0% chg, 3.16 px min clearance) | **+0.000…+0.003**, bracket [−0.002, +0.007] | `≥ +0.010`: the ancestor union is real new-fault ground → escalate to `surfext15`. `≤ −0.005`: catalogue adjacency dominates; retire the family. **Never** upload `surfext10ctl` (control). |

**Retired / never upload:** `conc15` (−0.0071), `dens15`/`spr15`, `b5km-move10/15/20`
(−0.0066…−0.0150), `concb5kmup4/8`, all MASS arms, all SNAP arms, `trackb-cull1dot`, and every
CONTROL / DUPLICATE / withdrawn row.

## Calendar to 2026-12-03

* **Wk 1:** Slots 1–3 as written; log each live `RECEIPT` (score + portal timestamp) in
  `ledger/submissions.csv` before the next upload.
* **Wk 2–3:** One re-dose on whichever axis clears `|Δ| ≥ 0.01`, one `surfext10` probe if a slot is
  spare, otherwise **stop spending slots on reallocation** — the budget arithmetic says it is capped.
* **Wk 4–5:** Fund one new-evidence axis (proposals below); require a positive fold-fair PROXY **and**
  a MODEL gain over a matched control before it ever reaches the portal.
* **Wk 6:** Re-validate both finalists from disk, then lock one blind final file (prefer the highest
  `RECEIPT`-verified score; if none clears the floor, prefer the conservative `concb5kmdown4` +
  `le3p000` lineage over an unvalidated evidence lane).

## Proposed axes for later sessions (mechanism / confounder / falsifier — not built here)

1. **`EVIDENCE-LIDAR` — sub-kernel scarp relocation on the pinned lidar band** (`lidar_scarp_features_u8`,
   already hash-pinned). *Mechanism:* the 400 m flight-line geometry limits *airborne* lineament
   position to ±150–200 m, but 1 m lidar scarps are positioned to ~1 px; move each dot ≤2 px onto the
   lidar scarp crest and the kernel credit rises without changing mass. *Confounder:* pluvial-shoreline
   treads and hogbacks have the same scarp expression; the earlier `SNAP` family failed because it
   used *airborne* gradients, which share the flight-line error it was meant to fix. *Falsifier:* live
   Δ ≤ −0.005, or no displacement-conditioned gain over a matched random-2 px SNAP control.
2. **`EVIDENCE-OFFSURFACE` — a fourth independent evidence surface.** *Mechanism:* the three ancestor
   surfaces agree on 78% of their pixels; the residual 22% (35,954 px) is where a *new* lineament
   family would have to live, and this session shows the parent uses none of it. *Confounder:* surface
   disagreement may be mapped-quadrangle bias, not geology. *Falsifier:* < +0.001 over `surfext10` on
   both instruments with a matched control.
3. **`MASS-CEILING` — how many dots before the FP term dominates.** *Mechanism:* `0.2(n−M)` is the only
   term mass moves; measuring `dDTI/dn` on the live metric (via a receipt on a ±10% file) calibrates
   the budget arithmetic above, which is currently a MODEL. *Confounder:* mass and field are
   confounded in file names (`IR-86-MASS-03`), so it needs a matched random-placement control.
   *Falsifier:* live Δ within ±0.003 of the random control → mass is irrelevant at this operating
   point, and every remaining slot should go to evidence.

**Human inputs still required:** `TOP_PUBLIC` + date · rolling-week slots left · verified deadline ·
R0's `0.2778` portal receipt · accepted outside-footprint encoding · organizer uniqueness rule
(`IR-86-PRUNE-01`).
