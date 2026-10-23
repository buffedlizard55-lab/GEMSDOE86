# Mechanism cards — CONCENTRATION at 10 km (fault-system scale) on R0, built 2026-10-23

Parent **R0** = `h33-h33-2-b2-20261004-e5eb6e7e`, 37,654 unit-mass dots, sha256 `c55bafc4…b6fa9`,
rebuilt **byte-exactly** this session (0 differing pixels). R0's 0.2778 is a **CLAIM** (no receipt).
All deltas below are **MODEL** (USGS SGMC off-catalogue surrogate, 79,615 truth px) or **PROXY**
(symmetric fold-fair catalogue hide-and-recover, n = 11,321 withheld px) — never scores.
A live change with |Δ| < 0.01 is no evidence. Arms were pre-registered in
`registry/preregistration_conc10.json` before any instrument ran. Raw numbers:
`evidence/concentration_10km_axis_20261023.json`.

Shared construction (identical to the audited 5 km session, block = 100 px = 10 km): every new dot
sits on a pinned ancestor ridge cell (`H19-5|H19-4|H16-1`), > 3.0 px from the catalogue
(measured min 3.162 px), ≥ √8 px from every other dot; donors are chosen by ascending exact
unique kernel credit within their block class; count fixed at 37,654. R0's occupied block-density
CV (canonical `block_density_stats`): **1 km 0.6235 · 5 km 0.7442 · 10 km 0.7360**. The 10 km
figure corrects IR-86-TRACKB-08's 0.570 (see IR-86-CONC-12): under the repo's canonical
definition R0 sits *above* the 0.51–0.59 band at 10 km, so dispersal is the band-ward direction
at this scale as well.

---

### 1. `…-concb10kmdown8-20261023-780f8509` — `b10km-down8`, 3,012 dots moved (15.9983 % changed)

- **Hypothesis.** R0 over-concentrates at the fault-system scale: a few 10 km blocks (dense
  range-front clusters) hold dots whose kernel credit is largely redundant, while entire
  neighbouring fault systems carry one or two dots per 10 km block. Moving the lowest-unique-
  credit dots out of the densest occupied 10 km blocks onto unused ancestor ridges in the
  sparsest occupied 10 km blocks buys first-coverage of under-sampled systems at near-zero
  numerator cost.
- **Mechanism.** Occupied-10 km density CV 0.736 → **0.496** (5 km 0.744 → 0.666; 1 km
  0.624 → 0.629, essentially untouched — the edit is purely inter-system). Destinations are the
  sparsest 65 % of the 537 valid occupied blocks (capacity ladder; only 8,761 free ridge cells
  exist anywhere ≥ √8 px from R0). Under DTI's max operator a dot that first-covers a new
  system's lineament can earn up to ~9.4 units of unique credit; a fifth dot on an already
  covered 1 km cluster earns a fraction of that and pays the same 0.2 false-positive charge.
- **Non-fault process that could mimic it.** Sparse occupied 10 km blocks are disproportionately
  basin/piedmont blocks where the ancestor ridges are pluvial Lake Lahontan shorelines, beach
  ridges and alluvial-fan distributary lineaments — linear, ridge-like, and not faults. If the
  sparse-block ridge pool is mostly shoreline, dispersal spends real range-front coverage on
  lacustrine terraces and the live score falls even though both local instruments (whose truth
  sets are themselves mapped-fault-like) stay quiet.
- **Predicted live change.** Pre-registered +0.001 (band −0.003…+0.005). Measured: **+0.0003
  MODEL** (2/4 quadrants, range −0.0040…+0.0107; ±6 px jitter mean **+0.0010**, 5/5 shifts
  positive) and **+0.0012 PROXY** (95 % CI [−0.0016, +0.0038]) vs matched random-block control
  −0.0009 MODEL. Sign-consistent with `concb5kmdown4` but weaker and quadrant-split; far below
  the 0.01 floor.
- **Falsifier.** Live Δ ≤ −0.005 vs R0 closes 10 km dispersal; live down8 ≤ down4 − 0.005 would
  additionally show the sparse-block ridge pool saturates at 4 %.

### 2. `…-concb10kmdown4-20261023-c4e8ffc9` — `b10km-down4`, 1,506 dots moved (7.9992 % changed)

- **Hypothesis / mechanism.** Strict half-dose prefix of `b10km-down8` (identical source and
  destination orderings; verified pixel-for-pixel). It lands the occupied-10 km CV at **0.518**,
  inside the 0.51–0.59 band, where the 8 % dose overshoots to 0.496 — so if the band itself is
  the causal object, this is the better-aimed file.
- **Mimic.** Same shoreline/terrace mimic as down8, at half exposure.
- **Predicted live change.** Pre-registered +0.001 (band −0.002…+0.004). Measured:
  **−0.0010 MODEL** (2/4 quadrants; jitter −0.0005) but **+0.0005 PROXY** (CI [−0.0006,
  +0.0019]). The two instruments disagree on sign at this dose and both intervals cover zero:
  the honest read is *no evidence either way at 4 %*, with the dose–response non-monotone on
  MODEL (8 % > 4 %) and monotone on PROXY. This is why neither down arm displaces
  `concb5kmdown4` (+0.0015 MODEL, 4/4 quadrants, +0.0008 PROXY) in the slot order.
- **Falsifier.** If down4 were ever scored and beat down8 by ≥ +0.005 live, the CV-band
  interpretation (aim at 0.51–0.59, do not overshoot) beats the first-coverage interpretation.

### 3. `…-concb10kmup8-20261023-ef2f3548` — `b10km-ridge-up8`, 3,012 dots moved (15.9983 % changed)

- **Hypothesis.** The sign control: unmapped faults cluster where mapped faults interact —
  step-overs, splays, terminations (Faulds inventory as a *prior on interaction zones* only) —
  so concentrating mass into the top-35 % fault-interaction blocks, with the prior recomputed at
  fault-system scale (30 km catalogue tip/junction halo, 10 km ridge halo, AGC-normalised TMI),
  should win if interaction zoning is the active lever at 10 km.
- **Mechanism.** Donors leave low-prior blocks; destinations fill unused ridges in high-prior
  blocks. Note this also *lowers* the 10 km density CV (0.736 → 0.545), because high-interaction
  blocks are not the dot-densest blocks — so the arm separates "where the geology says
  interactions are" from "where R0 already piled up dots".
- **Non-fault mimic.** Catalogue tip/junction density is partly a *mapping* density:
  quadrangles mapped at larger scale contribute more tips, and Miocene volcanic margins
  contribute TMI texture that survives AGC. Concentrating there can chase cartography.
- **Predicted live change.** Pre-registered −0.001 (band −0.004…+0.002). Measured:
  **−0.0009 MODEL** (2/4 quadrants; indistinguishable from the random-block control −0.0009)
  and **−0.0075 PROXY** (95 % CI [−0.0159, −0.0004] — the only interval in this session that
  excludes zero). Upward concentration has now lost at 1 km, 5 km and 10 km, on-ridge and off.
- **Falsifier.** A live Δ ≥ +0.010 would resurrect interaction-zoning and falsify the dispersal
  preference. Short of that, this arm's job is done: do not spend a slot on it.

## What this session changes

Nothing here clears the 0.01 live evidence floor, and no b10km arm displaces the current slot
order (RELIEF `frontp15`, CONCENTRATION `concb5kmdown4`, PRUNE `le3p000`). What it retires is
the *up* direction at the last unbuilt scale, and what it adds is a second, independent
dispersal dose–response (PROXY +0.0005 → +0.0012 across 4 % → 8 %) consistent with the 1 km
CV-band result. If Slots 1–3 all return inside ±0.005, `b10km-down8` is the cheapest remaining
probe of whether *any* concentration sign survives contact with live truth; `b10km-down4` is
its in-band fallback. (The `displacement_px` field in the receipts pairs sources and
destinations by sort order, not by transport; do not read it as a physical move distance.)
