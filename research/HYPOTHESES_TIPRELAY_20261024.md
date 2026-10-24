# 2026-10-24 Ranked Geological Hypotheses — Tip-Relay Hybrid Lane (GEMSDOE86)

**Scope:** Five fresh, unbuilt hypotheses scoped before implementation, ranked by qualitative expected information gain for catalogue-missing fault recovery, data self-sufficiency, and cost. No DTI projections are numerical predictions. Leakage canary threshold 0.90 applies to each feature alone on holdout.

**Data reality:** `training_features.tif` (19 bands, 100 m, EPSG:32611, 3730×3292, sha256 `4371c82e...`) is SHA-pinned and pixel-verified (Band 6 `tc` = GeoDAWN Radiometric TC, r=0.997; Bands 11+18 = signed horizontal gravity vector, IR-86-BAND11-18) but not present in sandbox (`data/prepared_manifest.json` has_features false). All hypotheses below list 100% competition-native layers or already-pinned external mirrors that are obtainable via `scripts/restore_data.py --with-external`. None requires new download to claim viability.

---

### Rank 1 — TIPRELAY-HYBRID (implemented, HOLDOUT-DTI 0.0136, PA-86-02 0 informative firings)

- **Specific layers:** `data/bridge/existing_faults.tif` (catalogue trace, 60,988 px, 3,199 components, 6,747 tips) + `data/bridge/sample_submission.tif` (footprint 5,167,373 px). No geophysics.
- **Physical signature:** For each tip, PCA strike on 7-px window, 6–12 px forward extrapolation (0.6–1.2 km) + 0.5–2.0 km tip-pair straight bridges where strikes collinear <30°; dots 1 px per step, thinned to >2 px off catalogue (collar), distal pool >2 km thinned to 3-px spacing, 18,827+18,827 = 37,654 dots, binary [0,1].
- **Why catches missing vs already mapped:** INGENIOUS/USGS mapping misses sub-seismic relay ramps and blind tip continuations where Quaternary basin fill buries scarps; tip stress fields and en-échelon step patterns predict linkage geometry that surface mapping cannot see. Validated by hiding whole fault components (buffered LOQO) and deriving tips only from visible faults.
- **How differs:** Prior `H86-TIPRELAY` (PR #63) copied 70% of H33 verbatim (IR-86-TIPRELAY-01). GMC/RMRB use potential-field cross-gradients; PRUNE/CONCENTRATION use density caps. This lane is pure catalogue-graph topology, de novo.
- **Expected DTI / cost:** Moderate-low DTI on pooled instrument (0.0136 > H33 0.0044, but < R0 0.096, < H86C 0.124). Low cost: O(10 s) geometry, no ML, CPU-only.
- **Viability:** 100% competition-native, SHA-verified, no external download. Leakage canary: tip proximity is catalogue-derived (dist_to_visible AUC 0.755 in H86E-RIDF) but not a leak when computed from visible only per fold — enforced by holdout builder.
- **Instrument:** `gems57-pooled-hide-v2` buffered whole-component LOQO, 11,321 withheld positives, 300 m triangular kernel, α=0.2 β=0.8.
- **Result:** HOLDOUT-DTI 0.0136 [fold dispersion std 0.0014] vs H33 0.0044 (+0.0092) on same instrument; R0 0.096, H86C 0.124 → negative overall. PA-86-02 informative firings 0/25, max overlap 0.426, max Spearman 0.0009 → passes informative uniqueness, fails literal witness (universal blocker). File `docs/downloads/gems86-tiprelay-hybrid-37654dots-20261024T222630Z-d8ee62a6-zeros.tif` (sha256 `7c1963ea...`, 37,654 dots, [0,1] finite, CRS/shape/transform match, 0 NaN, 0 on catalogue).

---

### Rank 2 — MTCS-RETRO (Magnetic Tilt Continuity Step, not built)

- **Specific layers:** Competition `rtp` (Band 2), `tmi_hg` (Band 3), `tmi_vg` (Band 9), `tc` (Band 6 GeoDAWN TC). All 19 bands available in pinned mirror.
- **Physical signature:** Compute true magnetic tilt `θ = atan2(tmi_vg, tmi_hg)` from Bands 3+9 (correcting IR-86-BAND6 mislabel), track tilt ridge continuity; look for 200–800 m lateral breaks in tilt ridge where `rtp` marker phase shifts but `tc` radiometric stays continuous (filtering lithologic contacts).
- **Why catches missing:** Walker-Lane transfer faults offset buried Miocene volcanic marker horizons without surface scarp; tilt ridge offsets are visible in aeromagnetics where lidar is blind.
- **How differs:** H86B-GFCO compared TMI vs upward-continued TMI at single scale; GMC used gravity-RTP cross-gradient; this uses tilt azimuth continuity, not amplitude.
- **Expected DTI / cost:** Medium-high expected gain (orthogonal to tip geometry), medium cost (multi-scale tilt, seam veto 090°/180°). Leakage canary: tilt AUC ~0.504 (prior holdout), safe.
- **Data needed:** Already pinned in `60GEMSDOE` manifest; no new external.

### Rank 3 — LIDAR-PERSIST (Scarp Persistence, not built)

- **Specific layers:** External `lidar_scarp_features_u8.tif` (SHA `d580bb8b...` pinned in 60GEMSDOE, 36.9 MB, 1-m DEM derived) + competition `det_elev_slope` (Band 19).
- **Physical signature:** Multi-scale scarp crest tortuosity + slope-break persistence across 10–30 m scales; require crest orientation orthogonal to range front and persistence >300 m along strike, veto pluvial shorelines via `det_elev` detrended elevation.
- **Why catches missing:** 100-m competition DEM smooths away <30 m scarps visible in 1-m lidar; blind intrabasin faults have subdued scarps detectable only at lidar resolution.
- **How differs:** GEMSDOE66 used lidar retrain with simple threshold; this uses crest persistence and tortuosity, not amplitude.
- **Expected DTI / cost:** Medium expected, low-medium cost. Leakage canary: lidar scarp alone AUC ~0.6 prior, safe.
- **Data needed:** Already pinned, obtainable via `--with-external --include-registry`.

### Rank 4 — HMDC-VENT-GEODESIC (Hydrothermal Destruction + Vent Triplet, not built)

- **Specific layers:** Competition `rtp` (Band 2), `tmi_vg` (Band 9), `cond_surf` (Band 17), `geod_dilaterate` (Band 8), + GDR `paleo_geothermal_regional.zip` (82 kB, 726 sinter mounds, SHA `faffcf69...` pinned), `ext_gdr_volcanic_vents_in_footprint.csv` (672 B, SHA `f91bafba...` pinned).
- **Physical signature:** Hydrothermal magnetite-destruction trough in `rtp`/`tmi_vg` (negative curvature, opposite to H86D-CTHB positive ridges) + pairwise sinter-vent geodesic co-linearity within 6 km along transtensional azimuths (015°–040° Basin-Range, 310°–335° Walker Lane) where dilation × conductivity high.
- **Why catches missing:** Fossil sinter marks paleo-upflow 1–3 km off active trace; magnetite trough marks alteration halo even where scarp eroded.
- **How differs:** H86D-CTHB used isotropic halos, not geodesics, and positive ridges not troughs.
- **Expected DTI / cost:** Medium-low expected, high cost (multi-source fusion + geodesic search). Leakage safe (point compilations, AUC check).
- **Data needed:** Already pinned (GDR CC-BY-4.0).

### Rank 5 — RADIOMETRIC-KTH-LINEAMENT (Potassic Alteration, not built)

- **Specific layers:** Competition `tc` (Band 6 TC) + external `geodawn_rad_u8.tif` K/Th/U ratios (SHA `c22420f7...` pinned) + competition `depth_to_base_surf` (Band 15) depth gate.
- **Physical signature:** Linear K/Th enrichment (>1.2× background) along 600-m corridors where `tc` low but K high (potassic adularia/illite fault gouge) and depth_to_base >100 m (alluvial cover), filtered for E–W/N–S seam immunity.
- **Why catches missing:** Radiometric K sees chemical alteration halo even where magnetic/topographic scarp is absent; depth gate focuses on covered faults.
- **How differs:** No lane used K/Th ratio; prior radiometric was scalar TC only.
- **Expected DTI / cost:** Low expected (high lithologic mimic rate), medium cost.
- **Leakage canary:** K/Th AUC prior <0.59, safe.
- **Data needed:** Already pinned.

---

## Implementation note

Top candidate (Rank 1) was validated on spatially-blocked holdout before any weekly slot was touched, per protocol rule 2. It did not beat the current holdout best (H86C-KSLB 0.124), so no slot was spent. The remaining four are declared before implementation, not lane assignments. All sources are official, SHA-pinned, and obtainable without new external acquisition; if a mirror is unreachable, viability is marked NOT_READY, not viable.

**Official sources:**
- DOE GDR 1391 (INGENIOUS Regional Dataset, CC-BY-4.0, 116.98 MB): https://gdr.openei.org/submissions/1391
- GeoDAWN (USGS DOI 10.5066/P93LGLVQ, CC0): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- GBCGE INGENIOUS (DOE DE-EE0009254): https://gbcge.org/current-projects/ingenious/
- Competition overview/rules: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ and https://docs.nlr.gov/docs/fy26osti/96647.pdf (§1.1 & §3.4–3.6, $300k prize, 3/week cap, one final pick)
- Tversky index (α=0.2, β=0.8): https://en.wikipedia.org/wiki/Tversky_index
- EPSG:32611 (WGS 84 / UTM zone 11N): https://epsg.io/32611
- GEMSDOE32 H33 page (owner-reported 0.2778): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- GEMSDOE leaderboard (public, portal-auth required for live): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

## Budget

Stop after 3 experiments or 2 hours; do not pick submissions. Promotion to real slot is separate selector step within weekly cap.
