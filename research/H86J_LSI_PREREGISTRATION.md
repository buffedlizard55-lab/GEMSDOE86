# H86J-LSI preregistration — Live-Score Inversion of hidden-truth density

**Frozen:** 2026-10-25 (UTC), before any LSI field, fit, candidate or dot was computed.
Machine-readable twin: [`H86J_LSI_PREREGISTRATION.json`](H86J_LSI_PREREGISTRATION.json).
The SHA-256 of both files is recorded in the run card; any later change is an
amendment and must be listed below with the measurement that forced it.

## 0. Why a new lane (one paragraph)

Every lane in this repository so far chose surfaces with an instrument that is
*not* the live metric: catalogue-hide HOLDOUT-DTI (measured to **anti-correlate**
with the owner-reported live ordering, `research/H86G_EDTI_REVIEW.md` E1b) or the
SGMC proxy (reproduces the ordering on 8 rasters). Yet the repository already
holds ~70 distinct rasters that were each scored *on the hidden live truth*
(owner-reported, `registry/prior_scores.csv`). Under the official DTI each score
is a known non-linear function of three **linear functionals of the unknown
truth field** — so the fleet is a set of measurements of that field. No lane has
used them. H86J-LSI inverts them.

## 1. Candidate hypotheses (ranked; only #1 is run in this session)

| Rank | ID | Layers | Physical / statistical signature | Why it targets *uncatalogued* faults | Difference from repo | Expected ΔDTI / cost |
|---:|---|---|---|---|---|---|
| 1 | **H86J-LSI** | Owner-scored fleet rasters (as *measurement operators* only) + 9 pinned stack layers + catalogue-distance shells + 3DEP lidar-coverage fraction | Truth-density field λ(x) = exp(θ·f(x)) fitted so that the official DTI algebra reproduces the reported live scores | The live score only counts organiser-masked, off-catalogue truth, so every fitted coefficient is *about unmapped faults by construction* | No lane used live scores as a likelihood; all used catalogue-hide or SGMC | Highest (direct target); medium cost |
| 2 | H86J-SCO | lidar step/cross, DEM gradient, RTP gradient + local strike field of the *visible* catalogue (5 km structure tensor) | Oriented-filter response gated by alignment with the local fault-set strike | Fault populations are strongly oriented sets; parallel unmapped strands share the set strike while Lahontan shorelines / flow fronts do not | Prior tensor lanes (55GEMSDOE, 59GEMSDOE) used data-only orientation, never catalogue-set strike | Medium; low cost |
| 3 | H86J-MEC | lidar `valid` coverage + lidar scarp bands | Mapping-effort covariate: newly mapped faults are where high-resolution lidar exists | The hidden truth is *newly mapped*; mapping effort is a first-order control on where it can exist | H86G excluded `valid` deliberately (catalogue-hide leak); it was never tested as a live covariate | Folded into #1 as one feature; low cost |
| 4 | H86J-PJX | `b12_det_elev`, `topo_relief_local`, `topo_curv_prof_absmax` | Piedmont-junction (range-front base) curvature transition | Low-relief fronts are under-mapped relative to high-relief range fronts | Overlaps the closed RELIEF axis (SLOT_PLAN) | Low; low cost |
| 5 | H86J-1M | USGS 3DEP 1 m lidar (`1m_DEM_links.csv`) | Metre-scale scarp detection | Sub-100 m scarps invisible in the 10 m DEM | Needs new external data; `prd-tnm.s3.amazonaws.com` / `rockyweb.usgs.gov` are **not reachable** from this sandbox (egress allow-list), so NOT VIABLE here | Unknown; high cost |

Official sources for the layers: competition page
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> (not
fetched by automation, AGENTS rule 9), GeoDAWN radiometric/magnetic
<https://doi.org/10.5066/P93LGLVQ>, INGENIOUS / GBCGE
<https://gbcge.org/current-projects/ingenious/>, GDR submission
<https://gdr.openei.org/submissions/1391>, USGS 3DEP
<https://www.usgs.gov/3d-elevation-program>, EPSG:32611 <https://epsg.io/32611>,
Tversky index <https://en.wikipedia.org/wiki/Tversky_index>.

## 2. H86J-LSI model (frozen)

**Measurement set.** Every `registry/prior_scores.csv` row with a numeric score
whose submission name matches a locally restored, hash-pinned raster on the
competition grid (`data/scored_fleet`, `data/scored`, `data/registry_ext`).
A row whose name matches several *different* decoded arrays is excluded
(ambiguous). Decoded arrays (NaN → 0, catalogue pixels → 0, outside footprint
→ 0) that are identical are merged; their scores are averaged. All scores are
`OWNER-REPORTED`; none is an organizer receipt.

**Operators.** Active domain `A = footprint ∧ ¬catalogue`. For raster `i` with
values `p_i`: `c_i(x) = max_x' p_i(x')·k(|x−x'|)` (truth-credit operator) and
`s_i(x) = Σ_x' p_i(x')·k(|x−x'|)` (dot-credit operator), `k` = official 300 m
triangular kernel, `n_i = Σ_A p_i`.

**Expected-metric algebra** (derivation in the review): with truth probability
`λ(x)`, `T_i = ⟨λ, c_i⟩`, `M_i = ⟨λ, s_i⟩ / 3` (line-geometry constant: the
kernel summed along a line through its centre is 3), `G = ⟨λ, 1_A⟩`,
`DTI_i = T_i / (0.2·T_i + 0.2·(n_i − M_i) + 0.8·G)`.

**Field.** `log λ(x) = θ0 + Σ_j θj·fj(x)` over 15 frozen features:
footprint ranks of `lidar_step_max`, `lidar_cross_max`, `topo_hs_lineament`,
`gradmag_dem_s1p5`, `topo_relief_local`, `b12_det_elev`, `gradmag_rtp_s1p5`,
`gradmag_grav_s1p5`, `b04_geod_2ndinv`; lidar coverage fraction (`valid`
band of the pinned lidar raster); catalogue-distance shells
`1[0<d≤3]`, `1[3<d≤6]`, `1[6<d≤12]`, `1[12<d≤25]`, `1[25<d≤50]` (baseline
`d>50`; distances from the catalogue in force — full for live/SGMC, visible for
the holdout). **No SGMC byte and no registry raster pixel enters any feature.**

**Fit.** Weighted least squares on DTI with ridge `1e-3·‖θ1:‖²` on standardised
features, L-BFGS, analytic gradient, operators evaluated on a fixed uniform 25 %
pixel sample of `A` (seed 861025), rescaled to the full domain.

## 3. Experiments (max 3)

* **E1** measurement set + operators; leakage canary for all 15 features on the
  catalogue-hide folds (`gems57-pooled-hide-v2`, seed 20); as-is instrument
  baselines (SGMC-proxy and catalogue-hide Spearman vs live on the same set).
* **E2** instrument validation: leave-one-*site*-out (LOSO) refits; Spearman,
  MAE of predicted vs reported live score; compared with the constant-λ model
  and the SGMC-proxy baseline.
* **E3** candidate: λ̂ (all-data fit) → `E[k] = λ̂ ⊛ k` → spacing-greedy ≥ 2.8 px,
  collar > 3 px, budget = argmax of LSI-predicted DTI over
  {30,000; 37,654; 44,090; 55,000}. Gates evaluated, TIFF written by the fail-closed
  vendor writer only if all pass.

## 4. Promotion gates (all must pass; otherwise verdict `negative`)

1. **Canary:** every feature's discriminative AUC ≤ 0.90.
2. **Instrument validity:** LOSO Spearman(pred, live) ≥ 0.60 **and** > constant-λ
   LOSO Spearman **and** ≥ SGMC-proxy Spearman on the same rasters.
3. **SGMC-PROXY-DTI vs H33-as-is:** paired 95 % CI lower bound > 0.
4. **SGMC-PROXY-DTI vs H86G-EDTI (current promoted lane):** paired 95 % CI upper
   bound > 0 (not significantly worse) at its shipped 55,000-dot raster.
5. **LSI-PROJECTION** (a MODEL number, never a score): candidate > H33 and >
   H86G-EDTI in ≥ 90 % of LOSO refits.
6. **HOLDOUT-DTI floor:** visible-construction candidate ≥ H33 visible-collar
   control (`gems57-pooled-hide-v2`, 11,321 withheld).
7. **Uniqueness:** max Spearman ≤ 0.90 (surface before placement and final dots)
   and max forward 3 px dot overlap ≤ 70 % against every restored registry
   dot-field (including H86G-EDTI and every `docs/downloads` TIFF).
8. **Format:** vendor writer + independent disk validator (single band float32,
   EPSG:32611, 3730×3292, geotransform match, finite, values in {0,1} ⊂ [0,1],
   0 dots on catalogue).

## 5. Named confounders

* Owner-reported scores are unverified; a transcription error moves the fit.
* Fleet rasters are strongly co-linear (H19-5 lineage), so coefficients
  orthogonal to the fleet's span are unidentified (ridge shrinks them to 0).
* Non-fault mimics in the evidence layers: Lahontan shorelines, volcanic
  flow fronts, unfaulted lithologic contacts; the lidar-coverage feature is a
  *mapping-effort* proxy, not geology.

## Amendments

None at freeze.
