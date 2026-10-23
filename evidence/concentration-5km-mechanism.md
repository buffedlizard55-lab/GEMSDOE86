# CONCENTRATION (5 km Ridge-Supported & CV-Band Sign Flip) — Mechanism Cards (2026-10-23)

Session branch: `arena/69392a35-gemsdoe86` · Axis: **`CONCENTRATION`** (self-assigned per brief v2 §1 without prompting).
Parent **R0 = `h33-h33-2-b2`** (`GEMSDOE32`), 37,654 unit-mass dots, sha256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, claimed live **0.2778 CLAIM** (no receipt in `ledger/`).
Run card: `evidence/concentration_5km_axis_20261023.json` · Code: `src/gems86/concentration_5km.py`, `scripts/run_concentration_5km.py`, `tests/test_concentration_5km.py`.

## Why this session took `CONCENTRATION` after syncing `origin/main`

After fast-forwarding onto `origin/main` (`a482851`, then syncing concurrent PR #44 `dens15/spr15` and PR #46 `b5km-move10/15/20` at `f35a97d`), forensic audit across all prior `CONCENTRATION` builds uncovered four decision-changing defects (`IR-86-CONC-10`):

1. **Unmeasured `+0.006 MODEL` constant in PR #37 (`conc15`):** `scripts/build_axis_variants.py:57` hard-coded `PREDICTIONS["CONCENTRATION"] = 0.006` without running `dti_binary` on SGMC. Measured here on the exact SGMC off-catalogue surrogate, `b1km-move15` reads **`-0.0071 MODEL`** (`-0.0063` across `±600 m` jitter) — an **0.0131 error**. Likewise, PR #44's `dens15` and `spr15` had no restored `.cache/gems_data/` SGMC or ridge rasters (`IR-86-CONC-06`) and were ranked #1/#2 in `SLOT_PLAN.md` from a synthetic toy model (`+0.026 / -0.030`); measured here on the real USGS SGMC map, **both lose (`dens15 = -0.0006`, `spr15 = -0.0013`)** with **`0.0%` of added dots on ancestor ridges**.
2. **Brief v2 §4.4 clearance breach (`conc15`):** `b1km-move15` placed **2,248 of its 5,648 added dots (`39.8%`) at `<= 3.0 px`** from mapped catalogue faults (`min = 2.2361 px`), violating §4.4 (`>= 3 px` clearance on newly emitted mass unless `AXIS=PRUNE`).
3. **Off-ridge placement across PR #37, #44, and #46:** **99.7%–100.0%** of added dots in `b1km-move15` (`0.3%` on-ridge), `dens15/spr15` (`0.0%`), and `b5km-move10/15/20` (`0.0%` on `H19-5`, `-0.0066..-0.0150 MODEL`) landed off the pinned ancestor lineament fields (`H19-5 | H19-4 | H16-1`) onto empty floor (`IR-86-SPACING-02`). Constraining placements 100% onto ancestor ridges (`concb5kmup4/8`) cuts the off-ridge geometric loss 15x (`-0.0109 -> -0.0007`), proving off-ridge geometry caused most of PR #46's drop while upward clustering itself remains slightly negative.
4. **Resolving `IR-86-CONC-08` (reaching the `0.51–0.59` CV band):** PR #44 concluded the `0.51–0.59` 1 km CV band was unreachable because pouring into a fixed 1/5 block bucket re-concentrated dots (`CV = 0.6136`). Shaving `>= 3`-dot 1 km sub-kernel clusters (`k -> k-1` so occupied blocks never empty) onto sparse-block ancestor ridges (`b5km-cvband-down4`) reaches **`1 km CV = 0.5162` inside `[0.51, 0.59]` at `8.00%` changed** and is the **only `CONCENTRATION` arm across all 10 ledger rows positive on both SGMC `MODEL` (`+0.0015`, 4/4 quads `+`) and symmetric fold-fair `PROXY` (`+0.0008`)**.

## Summary of all measured arms (`n = 37,654` fixed on every arm)

| Variant / Control | Dots moved (`% chg`) | 1 km CV | 5 km CV | On-ridge % | Min cat clear | SGMC `MODEL` $\Delta$ (4 quads) | `±6 px` jitter mean | Symmetric fold-fair `PROXY` $\Delta$ (`n=11,321`, 95% CI) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`b5km-cvband-down4`** (`concb5kmdown4-…-8aab97b6`) | `1,506` (`8.00%`) | **`0.5162`** | `0.7096` | **`100.0%`** | `3.162 px` | **`+0.0015` (`4/4` `+`)** | **`+0.0020`** | **`+0.0008`** `[-0.0004, +0.0018]` |
| **`b5km-ridge-up4`** (`concb5kmup4-…-493cf242`) | `1,506` (`8.00%`) | `0.6254` | `0.6844` | **`100.0%`** | `3.162 px` | `-0.0005` (`2/4` `+`) | `-0.0004` | `+0.0002` `[-0.0026, +0.0027]` |
| **`b5km-ridge-up8`** (`concb5kmup8-…-b4d36a67`) | `3,012` (`16.00%`) | `0.6265` | `0.6603` | **`100.0%`** | `3.162 px` | `-0.0007` (`2/4` `+`) | `-0.0002` | `-0.0026` `[-0.0083, +0.0018]` |
| `CONTROL-b5km-rand8` (not promoted) | `3,012` (`16.00%`) | `0.6295` | `0.6848` | `100.0%` | `3.162 px` | `-0.0008` (`2/4` `+`) | `+0.0005` | — |
| `AUDIT-b1km-move15-PR37` (`conc15`, PR #37) | `5,648` (`30.00%`) | `0.7644` | `0.9577` | `0.3%` | `2.236 px` | **`-0.0071`** (`2/4` `+`) | **`-0.0063`** | `+0.0060` `[-0.0030, +0.0160]` |
| `AUDIT-dens15-PR44` / `spr15-PR44` (PR #44) | `5,648` (`30.00%`) | `0.6722` / `0.6136` | — | **`0.0%`** | `3.162 px` | **`-0.0006` / `-0.0013`** | — | — |
| `AUDIT-b5km-move10/15/20` (PR #46) | `3,765–7,531` (`20–40%`) | `0.70–0.77` | `0.90–1.08` | **`0.0%`** (`H19-5`) | `3.162 px` | **`-0.0066` / `-0.0109` / `-0.0150`** | — | `+0.0141` (asymmetric) |

Single-feature leakage canary: max ROC-AUC **`0.7222 <= 0.90`** across all constituent features and targets.

---

## Mechanism Cards

### Card 1 — `b5km-cvband-down4` (`h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6`)

* **Hypothesis.** R0 (`1 km CV = 0.6235`) over-concentrates dots inside densely dissected range-front blocks where multiple `d = 2.8 px` dots share overlapping `R = 3.0 px` kernel discs (`mean unique credit = 6.79 / 9.38`); shaving 4% of R0 (`1,506` lowest-unique-credit dots from `>= 3`-dot 1 km blocks) onto unused ancestor lineament ridges (`H19-5 | H19-4 | H16-1`, `> 300 m` off catalogue, `>= 283 m` spacing) in sparse `1–2`-dot blocks brings 1 km occupied block-density CV into the `0.51–0.59` top-scorer band (`0.5162`) and converts redundant overlap into fresh fault-strand coverage.
* **Mechanism.** Under DTI (`alpha = 0.2, beta = 0.8`, `max_x k(d(x, g))`), the 3rd–5th dot inside a `10 x 10 px` block earns reduced marginal numerator `T` because neighboring dots already cover adjacent fault pixels, yet pays full `FP_w` whenever off-fault. Moving that dot onto an unpopulated `H19-4 | H16-1` ridge cell inside a 1-dot block buys a non-overlapping 29-cell kernel disc on corroborated geophysical/topographic lineament structure at strictly constant `S = 37,654`.
* **Non-fault process that could mimic it.** Sparse intrabasin blocks contain tilted Miocene basalt flow margins, Pleistocene pluvial-lake (Lahontan) beach ridges, and alluvial-fan distributary scarps captured by `H19-4` / `H16-1`; dispersing mass into sparse blocks could buy geomorphic mimics if range-front step-overs hold nearly all true unmapped faults.
* **Predicted sign and size.** **`+0.0015 MODEL`** on off-catalogue USGS SGMC (`+0.0020` mean across `±600 m` registration shifts), **sign positive in `4/4` quadrants** (`+0.0001..+0.0024`), corroborated by symmetric fold-fair `d28` hide-and-recover **`+0.0008 PROXY`** (`95% CI [-0.0004, +0.0018]`, `n = 11,321` withheld positives). Below the `0.01` single-submission evidence floor (`|Δ| < 0.01` = no evidence alone), but it is the **only `CONCENTRATION` arm positive on both `MODEL` and `PROXY` with 4/4 quadrant agreement**, beating PR #37's `conc15` by **`+0.0086 MODEL`**.
* **Falsifier.** Live `Δ <= -0.005` vs R0 (or losing a paired comparison against `b5km-ridge-up4`): proves unmapped Basin-and-Range faults cluster more tightly than `CV = 0.6235` and that the `0.51–0.59` historical CV band was an artifact of recipe smoothness rather than optimal spatial allocation.

### Card 2 — `b5km-ridge-up8` (`h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup8-20261023-b4d36a67`)

* **Hypothesis.** Unmapped Great Basin faults preferentially nucleate in 5 km structural interaction zones — mapped-fault terminations, branch/intersection junctions, and high local-RMS-normalized magnetic gradients (Faulds & Hinz 2015 [URL](https://pubs.geoscienceworld.org/gsa/books/edited-volume/872/chapter/107089445/Structural-Controls-of-Geothermal-Activity-in-the)). Reallocating 8% of R0 (`3,012` dots, `16.00%` changed) from the lowest-prior 5 km blocks onto unused ancestor ridges (`H19-5 | H19-4 | H16-1`, `> 300 m` off catalogue) in the top-35% 5 km blocks tests regional concentration without off-ridge desert placement or §4.4 violations.
* **Mechanism.** Skeletonizes both `existing_faults.tif` (6,904 tips, 4,131 junctions; 15 km halo) and `H19-5 | H19-4 | H16-1` (32,852 tips, 40,659 junctions; 5 km halo), combines them with 10.1 km local-RMS AGC `|\nabla TMI_up150|` (USGS GeoDAWN DOI `10.5066/P93LGLVQ`, [URL](https://doi.org/10.5066/P93LGLVQ)) to remove the 2× NW Miocene basalt magnetization bias, and fills the largest remaining kernel gaps on ancestor ridges inside top-35% 5 km blocks.
* **Non-fault process that could mimic it.** Quadrangle mapping effort: 1:24k bedrock mapping is denser in mineralized range blocks than in Playas/Quaternary basins, so even tip/junction density partially tracks geologist mapping effort rather than unmapped fault abundance; caldera ring fractures and intrusive stock contacts also elevate junction + AGC magnetic scores.
* **Predicted sign and size.** **`-0.0007 MODEL`** on off-catalogue SGMC (quadrant range `-0.0065..+0.0074`, `2/4` quadrants positive; `±6 px` jitter mean `-0.0002`), indistinguishable from the matched random-5km-block control `CONTROL-b5km-rand8` (**`-0.0008 MODEL`**), with symmetric fold-fair **`-0.0026 PROXY`** (`95% CI [-0.0083, +0.0018]`, `n = 11,321`). Restricting placements to genuine ridges eliminates 90% of `conc15`'s `-0.0071` loss, but concentrating further into high-prior 5 km blocks still buys zero net gain because R0 already saturates those ridges (`99.4%` of `H19-5` covered within 300 m). **Do not spend a weekly slot on this file.**
* **Falsifier.** If a human probes `b5km-ridge-up8` and observes live `Δ >= +0.010`, then private test labels are strongly concentrated in Faulds-style structural hubs that SGMC 1:500k state compilations under-resolved.

### Card 3 — `b5km-ridge-up4` (`h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup4-20261023-493cf242`)

* **Hypothesis.** Strict nested half-dose prefix (`4%` = `1,506` dots moved, `8.00%` changed) of `b5km-ridge-up8`: if `up8` suffers from exhausting prime `H19-4 | H16-1` ridge gaps inside top-35% blocks after the first ~1,500 placements, the first half of the relocation should outperform the second half.
* **Mechanism.** Programmatically verified exact prefix (`src4 == src8[:1506]` and `dst4 == dst8[:1506]`), matched dot-for-dot in edit size (`1,506` moves = `8.00%` changed) against the sign-flip arm `b5km-cvband-down4` so `up4` vs `down4` forms an exact-magnitude sign straddle around R0.
* **Non-fault process that could mimic it.** Same quadrangle-mapping and volcanic/intrusive contact mimics as `b5km-ridge-up8`, scaled to half amplitude.
* **Predicted sign and size.** **`-0.0005 MODEL`** on off-catalogue SGMC (`-0.0042..+0.0056`, `2/4` quadrants positive; `±6 px` jitter mean `-0.0004`), symmetric fold-fair **`+0.0002 PROXY`** (`95% CI [-0.0026, +0.0027]`, `n = 11,321`). Confirms a flat-to-slightly-negative slope (`0 -> -0.0005 -> -0.0007`) for upward block clustering. **Not recommended for a weekly slot.**
* **Falsifier.** Live `Δ >= +0.005` while `up8` is negative would prove sharp capacity saturation between 1,500 and 3,000 ridge placements.

---

## Three unbuilt proposals discovered by this session (proposals only, per brief v2 §5)

1. **`RELIEF-frontp15` + `PRUNE-le3p000` + `CONC-cvband-down4` Orthogonal Composite (for Week 5 after individual receipts):**
   * *Mechanism:* Combines the three count/collar levers whose mechanisms are geometrically orthogonal — `le3p000` removes masked-halo waste at `2–3 px` from mapped faults, `RELIEF-frontp15` shifts piedmont mass onto range fronts, and `cvband-down4` caps `>= 3`-dot 1 km over-packing onto `H19-4 | H16-1` ridges so relocation does not re-create sub-kernel overlap (`IR-86-SPACING-02`).
   * *Confounder:* Range-front blocks naturally carry higher dot density, so naively applying `cvband-down4` after `frontp15` could shave newly placed range-front dots unless the density cap is conditioned on tectono-geomorphic regime.
   * *Falsifier:* Composite scores below the best single constituent receipt on live feedback (`Δ_combo < max(Δ_single)`), proving non-additive interference.
2. **Sub-Basin Cover-Thickness De-Clustering (`CONCENTRATION` weighted by alluvial depth proxy):**
   * *Mechanism:* Instead of uniform 1 km block-density shaving (`>= 3` dots), weight sparse-block ridge additions toward thin-alluvium pediment windows (`relief_local` 10–40 m, `> 1 km` from range front) where concealed Quaternary faults still leave subtle 3DEP 10 m / GeoDAWN magnetic expressions.
   * *Confounder:* Fluvial terrace risers and pluvial-shoreline scarps occupy the exact same low-relief pediment elevation band.
   * *Falsifier:* No positive separation (`< +0.001`) against `b5km-cvband-down4` across all 4 quadrants on off-catalogue SGMC and symmetric fold-fair `d28` `PROXY`.
3. **Coherence-Filtered `TRACKB` Ridge Bridging (`>= 1.5 km` oblique strands, excluding `000°`/`090°` lattice-aligned runs):**
   * *Mechanism:* PR #41 found 5 of R0's 12 longest Hough strands are `000°` column-aligned discretization artifacts (`IR-86-TRACKB-03`); filtering traces by 30°-rotated survival + `TMI_up150` AGC edge support isolates genuine Basin-and-Range (`N15°–40°E`) and Walker Lane (`N30°–55°W`) strands for Phase-2 geologist review.
   * *Confounder:* Flight-line acquisition direction (E–W vs N–S across GeoDAWN Area 1/2 blocks) can induce residual directional anisotropy even off cardinal axes.
   * *Falsifier:* Rotated-grid survival rate matches a random-azimuth synthetic lineament field within `±5%`.
