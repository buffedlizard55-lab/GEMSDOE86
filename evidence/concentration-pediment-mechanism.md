# Pediment-window CONCENTRATION — mechanism card (2026-10-23, session 15)

**Parent.** R0 = `h33-h33-2-b2` (GEMSDOE32 `h33-h33-2-b2-20261004-e5eb6e7e`), 37,654 unit-mass
dots, sha256 `c55bafc4…b6fa9`, rebuilt **byte-exactly** this session before any arm was built.
Live 0.2778 is **CLAIM** (no receipt in `ledger/submissions.csv`).

**This is SLOT_PLAN proposal 2** (`IR-86-TRACKB-08` → `evidence/concentration-5km-mechanism.md`),
pre-registered before this session and built here unchanged in mechanism, with one measured
design change: the pediment-restricted destination pool **saturates at 1,045 moved dots**
(> 3.0 px catalogue clearance, ≥ √8 px spacing, sparse-block ancestor-ridge cells only), so the
attribution pair is dose-matched at **941 dots (2.5 % of R0, 5.00 % changed)** instead of
`concb5kmdown4`'s 1,506. Both pre-registered arms stay below that cap; the dose arm doubles it.

## Arms (all count-fixed 37,654, 100 % ancestor-ridge, min added clearance 3.162 px)

| id (sha8) | edit vs R0 | mechanism being tested |
|---|---|---|
| `…concb5kmpeddown2p5-20261023-9fb6bfc9` | 941 dots moved (5.00 % chg), destinations 100 % inside the pediment window | Concealed Quaternary faults under 10–40 m alluvium, > 1 km from a range front, are under-represented in the mapped catalogue → a relocated lineament dot there pays more often against *new-fault* truth |
| `…concb5kmnonpeddown2p5-20261023-57cc867c` | 941 dots moved, destinations 100 % outside the window | Attribution control: identical shave, generic sparse-ridge coverage only |
| `…concb5kmpeddown5-20261023-161b002e` | 1,882 dots moved (10.00 % chg), destinations pediment-first (55.6 % in-window, 44.4 % spill) | Dose-response of the pediment-prioritised rule |

The window itself is **truth-free** (USGS 3DEP-derived `relief_local` band + the RELIEF axis's
detrended-elevation regime map): 970,734 px = 18.8 % of the footprint; 17,790 R0 dots (47.2 %)
already sit inside it. No catalogue, SGMC, or scored-truth byte enters the mask, so it is
fold-fair by construction. Sources are the exact `relocate_cvband_down` shave
(≥ 3-dot 1 km clusters, lowest unique-credit dot first) — identical across all arms and identical
to the slot-2 arm's.

## Predictions written before measuring (MODEL, not scores)

* ped-down2p5 ≥ nonped-down2p5 on SGMC MODEL if the pediment prior is real;
* ped-down5 ≈ 2 × ped-down2p5 if the dose-response is linear;
* pre-registered falsifier (SLOT_PLAN proposal 2): pediment upgrade fails if it reads
  < +0.001 over `concb5kmdown4` on SGMC MODEL and the symmetric d28 PROXY.

## Measured (report-only instruments; brief §6 — none is a gate or a score)

| arm | SGMC MODEL Δ (quads, ±6 px jitter) | fold-fair d28 PROXY Δ (CI95, n=11,321) | 1 km CV | 10 km full-cover CV |
|---|---|---|---|---|
| ped-down2p5 | **+0.0007** (3/4, [−0.0005, +0.0021]; +0.0007) | **+0.0012** ([+0.00005, +0.0023]) | 0.6235 → 0.5542 | 0.5699 → 0.5594 |
| nonped-down2p5 | **+0.0013** (4/4, [+0.0009, +0.0017]; +0.0016) | +0.0004 ([−0.0004, +0.0013]) | → 0.5489 | → 0.5566 |
| ped-down5 | +0.0017 (4/4, [+0.0003, +0.0041]; +0.0022) | +0.0014 ([+0.00007, +0.0026]) | → 0.5013 (below the 0.51 band edge) | → 0.5506 |
| REF `concb5kmdown4` | +0.0015 (4/4) — **replicates the recorded +0.0015 exactly** | — | → 0.5162 | → 0.5516 |

Leakage canary max single-feature AUC 0.7606 (`relief_local_m`, SGMC-beyond-3 px target) — under
the 0.90 stop. Zero fold fallbacks. The 10 km column uses the fully-covered-block definition that
reproduces `IR-86-TRACKB-08`'s R0 = 0.570 (measured 0.5699; the unfiltered-occupied definition
gives 0.736 — both are now in `cv_report` so the scales cannot be mixed again).

## Verdict

1. **The pre-registered falsifier fired on the SGMC MODEL instrument**: at the identical dose the
   non-pediment complement beats the pediment arm (+0.0013 vs +0.0007; per-moved-dot efficiency
   1.3e-6 vs 0.7e-6), i.e. the slot-2 arm's gain is **generic sparse-ridge coverage**, not the
   thin-alluvium pediment prior, as far as mapped-fault truth can tell.
2. **The d28 PROXY orders the arms the opposite way** (+0.0012 vs +0.0004). The two instruments
   disagree in sign of the attribution, so the mechanism question is *split*, not resolved.
3. **Dose** is roughly linear on SGMC (+0.0007 → +0.0017 at 2×) with no pediment saturation in
   range, but the double dose pushes the 1 km CV below the empirical 0.51–0.59 band edge (0.5013).
4. **Decision consequence: no slot change.** `concb5kmdown4` (8aab97b6) remains the CONCENTRATION
   slot candidate exactly as ranked in SLOT_PLAN slot 2. None of the three pediment arms is a
   slot candidate: every predicted |Δ| ≤ 0.002 is far under the 0.01 live-evidence floor, and the
   only arm that beats the parent on SGMC per dot (nonped) is an attribution control.

## Non-fault processes that could mimic each arm (for a structural geologist)

* *Pediment window:* fluvial terrace risers and pluvial (Lahontan) shoreline scarps live in the
  exact same 10–40 m local-relief band — the pre-registered confounder, unchanged.
* *Non-pediment complement:* bedrock lineaments follow lithologic contacts and foliation, not
  only faults; the ancestor ridges already price much of that in, so the complement's SGMC gain
  may still be non-fault geology that SGMC happens to map.
* *Dose arm:* pushing 1 km CV to 0.5013 approaches the over-dispersed regime where the metric's
  triangular kernel stops paying for neighbours — the PROXY's plateau at 2× dose is consistent
  with that.

*Evidence class: MODEL (SGMC-extra surrogate) and PROXY (fold-fair d28 hide-and-recover). Neither
is a score. Master run card: `evidence/concentration_pediment_axis_20261023.json`; ledger rows in
`ledger/submissions.csv` via `ledger/variants_concentration_pediment.json`; builder
`src/gems86/concentration_pediment.py`; runner `scripts/run_concentration_pediment.py`.*
