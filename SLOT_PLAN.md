# SLOT PLAN — current, 2026-10-23 (merged through CONCENTRATION sign/5 km + TRACKB hybrid dossier)

**No automatic upload, score claim or final submission.** R0 is `h33-h33-2-b2` / GEMSDOE32
`h33-h33-2-b2-20261004-e5eb6e7e`, 37,654 dots; `0.2778` is a **CLAIM**, not a receipt. `TOP_PUBLIC`,
slots left and deadline confirmation are **UNSUPPLIED**; 2026-12-03 (~5.9 weeks / ~18 slots at 3/wk
for ONE entity + ONE blind final) remains **UNVERIFIED**. R0 was rebuilt byte-exactly (`219,065` B,
`c55bafc4…b6fa9`). A live `|Δ| < 0.01` is no evidence.

## Next three Phase 1 slots — ranked proposals, none auto-approved

| Order | Candidate / zeros-outside file | MODEL read and purpose | Decision |
|---|---|---|---|
| 1 | **CONCENTRATION `dens15`** — `releases/sign86/gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif` | `+0.026` (`−0.011…+0.047`), count fixed; positive half of the sign experiment | Largest positive magnitude, uncalibrated; read paired with slot 2 |
| 2 | **CONCENTRATION `spr15`** — `releases/sign86/gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif` | `−0.030` (`−0.064…+0.011`), count fixed; paired separation ≈`0.056` | Most informative sign test; if both land flat, close catalogue-prior concentration |
| 3 | **PRUNE `le3p000`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | `+0.004` (`−0.004…+0.013`); historical `0.2708→0.2778` direction is CLAIM only | Orthogonal near-catalogue collar test; mass-changing MODEL is confounded |

`RELIEF` `frontp15/frontm10` (`+0.0017 / −0.0089` MODEL) is the fallback pair; `SPACING` `strike16`
(`+0.0020`) is a later probe. `rand15` is a control, never a slot. `CONCENTRATION` 5 km (`−0.0066 /
−0.0109 / −0.0150` MODEL), `MASS` (closed), and `SNAP` (`−0.0017…−0.0445` MODEL) earn no slots.

## This session — TRACKB (Phase 2) geologist dossier + hybrid R0 variants (not weekly-slot candidates)

Traced R0 along pinned `H19-5` (`h19_buf1 >= 0.75`), yielding **2,801** strike-consistent `>= 1.0 km`
traces (`12,549` R0 dots, max `7.21 km`, all `> 300 m` off catalogue). Exported top **120**
susceptibility-normalised (5 km AGC `|∇TMI_up150|` + 3DEP 10 m scarp; `IR-86-TRACKB-05`) traces to
`releases/trackb/gems86-h33-2b2-trackb-top120-20261023.geojson` with **120 per-trace geologist
evidence paragraphs** in `evidence/trackb-geologist-dossier.md`. All 3 dual-encoded R0 variants pass
every gate (`> 3 px` new-mass clearance, unseen SHA-256, disk re-read; leakage canary max AUC `0.7670 <= 0.90`):

| Value | Dots / % parent changed | Pre-reg → SGMC `MODEL` Δ (`>3 px` collar) | 4-fold `PROXY` (`n=11,321`) | Phase 1 slot |
|---|---:|---|---|---|
| `cull1dot` | `34,305` / `8.894%` (`−3,349 / +0`) | `+0.0010` → **`−0.0096`** (`−0.0081`) | `0.00303 [0.00240, 0.00379]` | **NO** |
| `bridge1km` | `37,654` / `17.778%` (`−3,347 / +3,347`) | `+0.0020` → **`−0.0043`** (`−0.0017`; `+0.0008` vs rand) | `0.00291 [0.00230, 0.00364]` | **NO** |
| `rendertop120` | `37,654` / `8.196%` (`−1,543 / +1,543`) | `−0.0005` → **`−0.0043`** (`−0.0033`) | `0.00321 [0.00256, 0.00392]` | **NO** (Phase 2 hybrid) |

**Decision-changing findings (`evidence/trackb_hybrid_20261023.json`):**
1. **Pure trace-only rasters collapse DTI (`IR-86-TRACKB-06`):** emitting *only* the `2,237` pixels of
   the top-120 `>= 1 km` traces changes `96.31%` of R0 and drops SGMC `MODEL` DTI `−97.4%`
   (`0.0929 → 0.0024`). Because `NLR-RULES` scores ONE blind final GeoTIFF across Phase 1 and Phase 2,
   Phase 2 trace continuity must be embedded *inside* R0 (`rendertop120`), never emitted alone.
2. **Collar-truncated singletons are real splays (`IR-86-TRACKB-07`):** R0's `3,349` isolated 1-dot
   singletons earn `0.2264` SGMC `T`/dot (`4.1×` above `0.2 × 0.2778 = 0.0556`) because `<= 2 px`
   pruning severs real splays (`551` in `(2,3] px`) into 1-dot islands; `bridge1km` recovers `+58.6%`
   of that loss (`+0.0054` over `cull1dot`). Combined with PR #44's corridor `TRACKB` (`c10/c15/c25len1km`:
   `+0.0004 / +0.0008 / −0.0007` MODEL), `TRACKB` asks for **0** Phase 1 slots unless the human wants a
   Week 5 blind-final verification read on `rendertop120` or `bridge1km`.

## Calendar and better unbuilt axes (proposals only, not built)

- **Wk1–2:** `dens15` + `spr15` sign pair + `PRUNE le3p000` (only with human quota/receipt confirmation).
  **Wk3–4:** `RELIEF` fallback pair (`frontp15/frontm10`) or combine >=0.01 receipt winners.
  **Wk5–6:** confirm encoding (`NaN` vs `-zeros`) and lock ONE blind final choice (`R0` / live winner,
  or hybrid `rendertop120` if prioritizing Phase 2 `$250k` geologist trace review).
- **`CONCENTRATION-10km` (fault-system scale, `IR-86-TRACKB-08`):** full-footprint occupied `10 km`
  (`100 px`) block CV puts all 10 top historical files (`0.2632–0.2778`) inside **`0.547–0.570`**
  (`R0 = 0.570`, `lidar03 = 0.960`). Confounder: range/basin area ratio; falsifier: live `|Δ| < 0.01`.
- **`COLLAR-TO-TRACE` (collar-funded `>= 1 km` bridging):** fund `bridge1km` gap-bridges from
  `PRUNE le3p000`'s `2,171` `(2, 3] px` collar dots instead of off-collar singletons (build only if
  Slot 3 `le3p000` is non-negative). Confounder: unmapped parallel strands at `200–300 m`; falsifier:
  live DTI worse than `le3p000` alone.
- **Support-bounded de-cluster / coverage-matched PRUNE:** relocate strictly inside `H19-5` support
  within each block, or delete only `100%` kernel-redundant dots (`marginal T = 0`).

**Human inputs still needed:** current `TOP_PUBLIC`, remaining rolling-week slots, actual receipts
for R0 and any newly tested file, and the verified final deadline. No axis choice is requested.
