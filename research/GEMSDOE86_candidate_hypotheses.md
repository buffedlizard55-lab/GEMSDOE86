# GEMSDOE86 — Candidate Geological Hypotheses (untried / not yet validated)

**Purpose:** satisfy the standing request for 3–5 candidate hypotheses not yet tried in this repo, each naming the specific layer(s), the physical signature targeted, why it should catch a fault MISSING from the USGS/INGENIOUS catalogue, how it differs from anything already implemented, and a ranking by expected DTI improvement vs implementation cost.

**Status:** none of these has been holdout-validated. The only candidate advanced to a generated TIFF in this session is H-1 (geothermal-prospectivity collar), which is format-valid but NOT authorized for a weekly slot (no HOLDOUT-DTI, no organizer receipt; protocol `require_feasible()` blocked by the pinned full-support witness).

**Official sources used (all free / public-domain / official):**
- USGS GeoDAWN airborne magnetic & radiometric survey: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and  (DOI 10.5066/P93LGLVQ)
- USGS 3DEP (1 m / 10 m DEM, LiDAR): https://www.usgs.gov/3d-elevation-program
- USGS SGMC geologic-map faults: https://www.usgs.gov/ (Great Basin geologic maps)
- USGS ScienceBase Great Basin conductive heat flow: DOI 10.5066/P9BZPVUC (DeAngelo et al. 2022) — https://www.sciencebase.gov/catalog/item/5a809b3be4b0c7f309a8e976
- DOE Geothermal Data Repository submission #1391 (INGENIOUS; wells, springs, vents, qfaults): https://gdr.openei.org/submissions/1391  (DOI 10.15121/1881483)
- EPSG:32611 (UTM 11N, competition grid CRS): https://epsg.io/32611
- Tversky index (competition metric family): https://en.wikipedia.org/wiki/Tversky_index

---

## H-1 (IMPLEMENTED this session) — Geothermal-prospectivity collar emphasis

**Rank / expected DTI gain:** 1 — highest expected gain among low-cost candidates.
**Implementation cost:** Low — implemented and generated in this session (~2 CPU minutes; inputs already restored).

**Specific layers:**
- `training_features.tif` Band 5 `iso_grav_anom_slope` (unsigned 2-D horizontal gravity-gradient magnitude, empirically `r=+0.946995` vs hypot(B11,B18))
- `training_features.tif` Band 6 `tc` (GeoDAWN airborne radiometric Total Count; potassium-bearing hydrothermal alteration proxy, empirically `r=+0.997140` vs `geodawn_rad_u8` TC)
- `data/bridge/existing_faults.tif` (catalogue; = `labels.tif` by SHA-256)
- `data/bridge/sample_submission.tif` (grid/footprint template, EPSG:32611, 3730×3292, 100 m)

**Physical signature:** Product of robust-scaled gravity-gradient magnitude × radiometric Total Count, restricted to the intermediate 2–8 px (200–800 m) collar around catalogue faults, then Poisson-disc placed (2.8 px spacing, 37,654 dots). Targets blind geothermal upflow hosted in relay zones / dilational jogs / stepovers of mapped faults.

**Why it catches catalogue-missing faults:** Blind horst-bounding faults, accommodation stepovers, and piedmont synthetic splays buried under Cenozoic valley fill lack >2 m Quaternary surface scarps in aerial/INGENIOUS mapping. The 200–800 m collar is where relay-zone blind strands concentrate; the grav-grad × TC product isolates structural boundary + hydrothermal alteration jointly, suppressing diffuse apron overestimation.

**Named non-fault mimic:** Isometric volcanic plugs / calderas / unfaulted pluton cupolas (no sharp contact-saddle gravity signature); diffuse down-gradient alluvial thermal outflow plumes (suppressed by requiring co-located gradient and radiometric signal inside the collar).

**Differs from repo:** GEMSDOE32 H33 (0.2778, owner-reported) PRUNES dots at 1–2 px from catalogue faults. H-1 EMPHASIZES the 2–8 px collar — the inverse placement rule — and weights by a geophysical × radiometric product rather than pure catalogue geometry. No lane in this repo had shipped a radiometric-TC × gravity-gradient collar dot field.

**Generated artifact:** `docs/downloads/gems86-geothermal-prospectivity-37654dots-20261027T171746Z-480f1b4f-zeros.tif` (SHA-256 `c80f777c3a7880e9f0054d99a68f4ed1967ffb174e60f3d06c6e2637926c47c1`). Format validation: all local checks pass (values in [0,1], 0 NaN/Inf, CRS/shape/transform match sample_submission.tif, 0 dots on catalogue). Local uniqueness vs 25 scored-fleet rasters: 0 overlap firings (worst 0.6028 ≤ 0.70), 0 Spearman firings (worst 0.0949 ≤ 0.90). NOT authorized to submit: no HOLDOUT-DTI (protocol blocked), no organizer receipt.

---

## H-2 — Heat-flow & volcanic-vent corroborated blind fault sweeps

**Rank / expected DTI gain:** 2.
**Implementation cost:** Low — all inputs are public and already mirrored in the repo's external data manifest.

**Specific layers:**
- USGS ScienceBase Great Basin conductive heat-flow points in footprint (`external/sb_heat_flow_in_footprint.csv`, DOI 10.5066/P9BZPVUC)
- DOE GDR #1391 Quaternary volcanic vents in footprint (`external/gdr_volcanic_vents_in_footprint.csv`, DOI 10.15121/1881483)
- `training_features.tif` Band 6 `tc` (radiometric Total Count) and Band 5 `iso_grav_anom_slope`
- `existing_faults.tif` (catalogue, for collar and exclusion)

**Physical signature:** Distance-to-nearest heat-flow anomaly and distance-to-nearest volcanic vent, combined with gravity-gradient × radiometric prospectivity, gated to the 2–8 px catalogue collar and to cells >3 px from any mapped trace (off-catalogue emphasis). Poisson-disc placement weighted by the product, budget 37,654 dots.

**Why it catches catalogue-missing faults:** Geothermal systems surface as heat-flow anomalies and Quaternary vents precisely where blind faults provide permeability. Many of these vents/anomalies lie off the mapped Quaternary fault catalogue (INGENIOUS maps surface trace, not blind conduit). Targeting heat-flow/vent proximity finds blind geothermal faults the catalogue misses.

**Named non-fault mimic:** Young basaltic volcanism unrelated to fault control; palaeolake shorelines / alluvial-fan toes that mimic heat-flow spatial clustering (rejected by requiring co-located grav-grad × TC structural signal).

**Differs from repo:** No lane uses USGS ScienceBase heat-flow points or DOE GDR volcanic vents as a dot-weighting input. The closest is H86M-PFTE's Peclet barrier (uses GDR probes), but not heat-flow/vent proximity weighting.

**External data check (obtainable):** `sb_heat_flow_in_footprint.csv` is already in `data_manifest.json` (GEMSDOE28 mirror, SHA-256 pinned) and `gdr_volcanic_vents_in_footprint.csv` (GEMSDOE24 mirror). Both are free official sources; no new download required.

---

## H-3 — Multi-scale LiDAR topographic openness / curvature edge on piedmont scarps

**Rank / expected DTI gain:** 3.
**Implementation cost:** Medium — needs USGS 3DEP 1 m LiDAR-derived openness/curvature (already mirrored as `external/lidar_scarp_features_u8.tif` and `external/topo_10m_derived_100m_u8.tif`).

**Specific layers:**
- `external/lidar_scarp_features_u8.tif` (USGS 3DEP 1 m LiDAR scarps, quantile-debiased via 10 m DEM)
- `external/topo_10m_derived_100m_u8.tif` (USGS 3DEP 10 m slope/relief/curvature/aspect-coherence on 100 m grid)
- `external/dem10_chi_100m_i16.tif` (USGS 3DEP fluvial chi / knickpoint counts)
- `existing_faults.tif` (catalogue exclusion)

**Physical signature:** Multi-scale topographic openness (positive = ridge/breach, negative = valley) and profile/plan curvature edges computed at 100–300 m scales, highlighting subtle piedmont fault scarps that lack >2 m aerial expression. Combined with chi-knickline colinearity orthogonal to geodetic extension. Poisson-disc dots weighted by openness×curvature edge strength, off-catalogue (>3 px from mapped trace).

**Why it catches catalogue-missing faults:** Slow (0.1–0.3 mm/yr) distributed pediment/basin-range faults across the northern Great Basin produce subtle scarps below INGENIOUS aerial mapping threshold but recoverable from 1 m LiDAR openness. These are blind to the catalogue but real structural conduits.

**Named non-fault mimic:** Alluvial-fan toes, paleolake (Lahontan/Bonneville) shorelines, and fluvial knickpoints from lithology contrast (rejected by requiring cross-watershed colinearity ≥3 adjacent watersheds and co-located gravity-gradient signal).

**Differs from repo:** H86M-SGRT is a related queued hypothesis (fluvial chi knickline colinearity) but was never implemented as a dot submission. No lane has shipped a LiDAR-openness × curvature edge dot field.

**External data check (obtainable):** `lidar_scarp_features_u8.tif`, `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_i16.tif` are pinned in `data_manifest.json` (60GEMSDOE / GEMSDOE48 / 19GEMSDOE mirrors); all free USGS 3DEP.

---

## H-4 — 3-D Reid–Thompson Euler deconvolution contact-sheet apexes

**Rank / expected DTI gain:** 4.
**Implementation cost:** Medium — vectorized batched 4×4 normal equations over 7×7 windows on the potential-field bands.

**Specific layers:**
- `training_features.tif` Bands 2 (`rtp`), 3 (`tmi_hg`), 9 (`tmi_vg`), 11 (`iso_grav_anom_vg`, signed southward derivative), 13 (`iso_grav_anom`), 17 (`cond_surf`), 18 (`iso_grav_anom_hg`, signed eastward derivative)
- `external/gdr_volcanic_vents_in_footprint.csv` (proximity veto for volcanic feeders)

**Physical signature:** Sliding-window 3-D Euler homogeneity least-squares: `(x−x₀)∂ₓF + (y−y₀)∂ᵧF + (z−z₀)∂zF = −N(F−B)` solved jointly at contact index N=0.5 vs volcanic-pipe/plug index N=2.0; retain tight curvilinear apex clusters (x₀,y₀) with z₀ in [100, 1500 m] and variance ratio Var(N=0.5)/Var(N=2.0) < 0.25, co-located with Band 17 MT conductivity steps. Dots on apex clusters off-catalogue.

**Why it catches catalogue-missing faults:** Recovers 3-D sub-playa fault-contact apexes (x₀,y₀,z₀) directly from potential-field homogeneity without basement-depth inversions (B15) or surface scarps. Blind fault contacts hidden under valley fill still perturb the potential field.

**Named non-fault mimic:** Shallow basaltic cinder-cone feeders and cultural pipelines (rejected by N=2.0 pipe preference and vent-proximity veto).

**Differs from repo:** H86J-MCSP used scalar TMI_up150 amplitude-decay ratios; H86M-HDEC is a related queued hypothesis but never implemented as a dot submission. No lane has solved 3-D Euler linear systems for apex-spray dot placement.

---

## H-5 — Aitchison ilr K–eTh–eU metasomatic roll-fronts above seismogenic ramps

**Rank / expected DTI gain:** 5 (most exploratory).
**Implementation cost:** Medium — needs GeoDAWN K/eTh/eU ratios and hypocenter-depth ramps; compositional (ilr) transform is straightforward.

**Specific layers:**
- `external/geodawn_rad_u8.tif` (GeoDAWN K, eTh, eU, TC; DOI 10.5066/P93LGLVQ)
- `external/geodawn_extensions_u8.tif` (Th/K, U/Th ratios)
- `training_features.tif` Band 10 `deq_n100a15` and Band 16 `ieq_n100a15` (seismicity/hypocenter proxies)
- `existing_faults.tif` (collar)

**Physical signature:** Aitchison isometric log-ratio (ilr) ternary transform of K–eTh–eU to remove compositional closure, highlighting metasomatic roll-fronts (K enrichment, eU depletion) updip of seismogenic hypocenter-depth ramps. Combined with radiometric Total Count. Dots weighted by ilr anomaly × ramp proximity, in the catalogue collar, off-trace.

**Why it catches catalogue-missing faults:** Epithermal alteration (K-metasomatism) halos blind fault saddles and roll-fronts that are geochemically anomalous but structurally subtle — invisible to fault-trace mapping but radiometrically visible.

**Named non-fault mimic:** Detrital K-feldspar sand bodies and unfaulted lithologic contacts (rejected by requiring co-located gravity-gradient structural edge and seismogenic-ramp updip position).

**Differs from repo:** H86M-RMRF is a related queued hypothesis (ilr K–eTh–eU roll-fronts) but never implemented. No lane has shipped a compositional radiometric ilr dot field.

**External data check (obtainable):** `geodawn_rad_u8.tif` and `geodawn_extensions_u8.tif` are pinned in `data_manifest.json` (GEMSDOE24 mirror, derived from USGS GeoDAWN DOI 10.5066/P93LGLVQ).

---

## Summary ranking

| Rank | ID | Expected DTI gain | Cost | Novelty vs repo |
|:---|:---|:---|:---|:---|
| 1 | H-1 Geothermal-prospectivity collar | Highest (implemented) | Low | Implemented this session; inverse of H33 collar-prune |
| 2 | H-2 Heat-flow & volcanic-vent sweeps | High | Low | New inputs (USGS heat flow, DOE GDR vents) |
| 3 | H-3 LiDAR openness × curvature edge | Medium | Medium | LiDAR scarps not yet a dot submission |
| 4 | H-4 3-D Euler contact-sheet apexes | Medium | Medium | 3-D Euler not yet implemented |
| 5 | H-5 ilr K–eTh–eU roll-fronts | Exploratory | Medium | Compositional radiometrics not yet implemented |

**Recommendation:** promote H-2 next — it targets geothermal discovery directly (heat flow + vents), uses already-pinned free official inputs, and is low cost. Validate H-2 on a spatially-blocked holdout before any weekly slot, per the budget rule (≤3 experiments / ≤2 hours).
