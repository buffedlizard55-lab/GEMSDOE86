# Scientific Synthesis: Structural Controls & Multi-Physics Signatures of Blind Geothermal Vents in the Great Basin

**Date:** `2026-10-24` (UTC)  
**Scope:** Primary-source scientific reference and auditable data-layer inventory for `GEMSDOE86` and sibling GEMS Prize workflows. Every citation, DOI, survey specification, and raster band index below was verified against the live primary documents retrieved in `docs/evidence/source-recheck-20261024.json` and the SHA-256-verified GeoTIFF headers of `training_features.tif` (`sha256: 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`). No unverified score or untested model claim is made here.

---

## 1. Why Geothermal Vent Discovery Matters for Missing-Fault Prediction in GEMS

Per the [DOE/NLR GEMS Prize Official Rules (September 2026)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) and the [UNR Great Basin Center for Geothermal Energy (GBCGE) INGENIOUS project (`DE-EE0009254`)](https://gbcge.org/current-projects/ingenious/), the overarching scientific goal of the competition is to identify **structures indicative of geothermal resources** across the northwestern Great Basin / Walker Lane (`EPSG:32611`, `100 m` grid, `3730 × 3292` pixels) that are **missing from the published USGS Qfaults / INGENIOUS Quaternary fault compilation** (`existing_faults.tif`, `60,988` positive footprint pixels).

In the Great Basin, hydrothermal upflow rarely occurs along the mid-segments of simple, high-relief planar range-front normal faults — precisely the features *already* well-mapped in `existing_faults.tif` because they build prominent subaerial scarps. Instead, geothermal vents, blind upflow plumes, and paleo-hydrothermal deposits localize in **structurally complex, high-fracture-density dilatant damage zones** where vertical permeability stays open against mineral self-sealing:

1. **Horse-tail fault terminations / tip-splay cones:** Distributed tensile and hybrid shear fractures radiating off the propagating tips of normal or strike-slip faults into basin fill, where individual strand throw is too small (`< 1 m`) to survive Holocene alluvial reworking in 30–100 m DEMs.
2. **Soft-linked normal-fault relay ramps & accommodation zones:** Breached or unbreached stepovers between overlapping echelon normal faults (including Humboldt structural zone and northern Walker Lane transfer zones), where bed rotation and cross-ramp breaching fractures maintain subvertical fluid conduits.
3. **Conjugate / oblique fault intersections & transtensional pull-apart stepovers:** Intersections between NNE-striking Basin-and-Range normal faults and NW-striking Walker Lane dextral strike-slip faults under active horizontal crustal dilatation (`geod_dilaterate > 0`, `geod_shearrate` high; Kreemer & Young 2022, [DOI `10.1785/0220220153`](https://doi.org/10.1785/0220220153)).

---

## 2. Verified 19-Band Competition Feature Stack (`training_features.tif`)

Direct inspection of `training_features.tif` (`sha256: 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, `418,912,844` bytes, `EPSG:32611`, `nodata = -3.4028234663852886e+38`, `src/gems86/io.py`) confirms the exact 19 bands and corrects prior band-index misattributions (`IR-86-BAND-INDEX-20261024`):

| Band | Short key (`io.py`) | Exact embedded GeoTIFF band description | Primary physical observable |
|---:|---|---|---|
| 1 | `mag_anom` | `mag_anom - Magnetic anomaly - deviation from expected Earth's magnetic field` | Residual magnetic intensity |
| 2 | `rtp` | `rtp - Reduced to pole magnetic data - magnetic anomaly corrected for latitude effects` | Magnetization centered over causal bodies |
| 3 | `tmi_hg` | `tmi_hg - Total magnetic intensity horizontal gradient - rate of change in horizontal direction` | Steep shallow magnetic contacts |
| 4 | `geod_2ndinv` | `geod_2ndinv - Geodetic second invariant - measure of strain rate tensor magnitude` | Total active horizontal crustal strain rate |
| 5 | `iso_grav_anom_slope` | `iso_grav_anom_slope - Isostatic gravity anomaly slope - gradient of gravity after isostatic correction` | Basin-margin / basement density-contrast slope |
| 6 | `tc` | `tc - Tilt angle or total curvature - magnetic field derivative for edge detection` | Depth-normalized magnetic edge / zero-crossing |
| 7 | `geod_shearrate` | `geod_shearrate - Geodetic shear rate - rate of angular deformation from GPS/InSAR` | Active strike-slip / oblique shear rate |
| 8 | `geod_dilaterate` | `geod_dilaterate - Geodetic dilatation rate - rate of volumetric strain (expansion/contraction)` | Crustal extension / fracture-opening rate |
| 9 | `tmi_vg` | `tmi_vg - Total magnetic intensity vertical gradient - rate of change in vertical direction` | Shallow short-wavelength magnetic fabric |
| 10 | `deq_n100a15` | `deq_n100a15 - Distance to earthquake (n=100km radius, a=15° azimuth parameters)` | Seismic proximity field |
| 11 | `iso_grav_anom_vg` | `iso_grav_anom_vg - Isostatic gravity anomaly vertical gradient - vertical rate of change` | Upper-crustal density step sharpening |
| 12 | `det_elev` | `det_elev - Detrended elevation - topography with regional trends removed` | Local scarp / range-front relief ([DOI `10.5066/P9MQRCBY`](https://doi.org/10.5066/P9MQRCBY)) |
| 13 | `iso_grav_anom` | `iso_grav_anom - Isostatic gravity anomaly - gravity after compensating for topographic mass` | Basin-fill vs bedrock density integrated column ([DOI `10.5066/P9Z6SA1Z`](https://doi.org/10.5066/P9Z6SA1Z)) |
| 14 | `tmi` | `tmi - Total magnetic intensity - total strength of magnetic field` | Total aeromagnetic field ([DOI `10.5066/P93LGLVQ`](https://doi.org/10.5066/P93LGLVQ)) |
| 15 | `depth_to_base_surf` | `depth_to_base_surf - Depth to basement surface - thickness of sedimentary cover` | Pre-Tertiary basement depth / basin-fill thickness |
| 16 | `ieq_n100a15` | `ieq_n100a15 - Earthquake intensity or density (n=100km radius, a=15° parameters)` | Seismicity spatial density |
| 17 | `cond_surf` | `cond_surf - Conductivity surface - electrical conductivity of subsurface` | Shallow/upper-crustal electrical conductivity ([DOI `10.5066/P9TWT2LU`](https://doi.org/10.5066/P9TWT2LU)) |
| 18 | `iso_grav_anom_hg` | `iso_grav_anom_hg - Isostatic gravity anomaly horizontal gradient - horizontal rate of change` | Steep basement / basin-fill density boundaries |
| 19 | `det_elev_slope` | `det_elev_slope - Detrended elevation slope - gradient of elevation after detrending` | Geomorphic scarp / break-in-slope magnitude |

---

## 3. GeoDAWN Acquisition Geometry & Survey-Artifact Controls (Verified USGS Metadata)

From the live-verified USGS GeoDAWN data release ([Glen & Earney, March 4, 2024, DOI `10.5066/P93LGLVQ`](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), CC0 1.0 Public Domain):

- **Extent & blocks:** `149,030 line-km` across `51,857 km²` in four blocks (north to south: **Winnemucca, Fallon, Hawthorne, Tonopah**), flown Nov 1, 2021 – Nov 20, 2022.
- **Area 1 (Clayton Valley Li-brine/clay focus):** Helicopter survey at `100 m` nominal terrain clearance (`150 m` over mountains), **E–W flight lines (`90°` azimuth) at `200 m` spacing**, **N–S tie lines (`180°` azimuth) at `2,000 m` spacing**.
- **Area 2 (Geothermal focus across remainder of GeoDAWN):** Fixed-wing + helicopter survey at `150 m` nominal terrain clearance (`200 m` over mountains), **E–W flight lines (`90°` azimuth) at `400 m` spacing**, **N–S tie lines (`180°` azimuth) at `4,000 m` spacing**, with a `22°` maximum climb/descent drape.
- **Modeling implication for GEMS:**
  1. Strictly **E–W (`090°`)** features at `200–400 m` spacing and strictly **N–S (`000°/180°`)** features at `2,000–4,000 m` spacing risk tracking residual flight-line or tie-line leveling corrugations, whereas regional **NNE–SSW (`015°–040°`)** Basin-and-Range normal faults and **NW–SE (`310°–335°`)** Walker Lane strike-slip faults cut obliquely across both survey directions.
  2. Over steep (`> 22°`) mountain fronts, aircraft terrain clearance increases above the nominal drape surface, attenuating short-wavelength magnetic (`tmi_vg`, `tmi_hg`) and radiometric (`K/Th/U`) amplitudes relative to flat basin floors.

---

## 4. Overlooked Official Public Datasets for Blind Geothermal Vent & Conduit Discovery

Verified directly on [DOE GDR Submission 1391 (`DOI 10.15121/1881483`, CC-BY-4.0)](https://gdr.openei.org/submissions/1391) and [UNR GBCGE INGENIOUS](https://gbcge.org/current-projects/ingenious/):

| Official public resource | License / Access | Size / Mirror Status in Repo | How it targets unmapped geothermal faults & exact novelty vs `H86D-CTHB` | Leakage audit rule |
|---|---|---|---|---|
| **GDR 1391 `paleo_geothermal_regional.zip`** (`https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip`) | CC-BY-4.0 (public) | `84,008 B` (`82.04 kB`); **SHA-pinned on GitHub** (`60GEMSDOE`, `sha256: faffcf69...` in `research/h86d_extended_manifest.json`) | Maps 726 fossil siliceous sinter (`SiO2·nH2O`, reservoir $T \gtrsim 175^\circ\text{C}$) and travertine/tufa (`CaCO3`) spring mounds. `H86D-CTHB` used only isotropic radial point halos (`paleo_sinter_vent`); pairwise co-linear vent-to-vent strike geodesics coupled to magnetite-destruction troughs (`H86E-HMDC`) remain untested. | Point/deposit compilation; verify zero derived columns from `qfaults_ingenious` and run single-feature canary (`AUC <= 0.90`). |
| **GDR 1391 `2m_temperature_probe_INGENIOUS_regional_data.zip`** (`https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip`) | CC-BY-4.0 (public) | `1,080,530 B` (`1.03 MB`); **SHA-pinned on GitHub** (`60GEMSDOE`, `sha256: 1301f70d...` in `research/h86d_extended_manifest.json`) | 3,800 shallow 2-meter temperature probes (Coolbaugh/Sladek, Kraal et al. 2022) across Great Basin basins. `H86D-CTHB` used smoothed plume/density planes (`t2m_dab_plume`); principal-axis elongation of thermal plumes along demagnetized corridors (`H86E-HMDC`) remains untested. | Independent field temperature measurements; canary check required before fold fitting. |
| **GDR 1391 `great_basin_q_volcanics.zip`** (`ext_gdr_volcanic_vents_in_footprint.csv` pinned in `data_manifest.json`) | CC-BY-4.0 (public) | `672 B` in-footprint CSV (`sha256: f91bafba...`) | Quaternary volcanic vents align along deep crustal diking/extensional fissures and accommodation-zone conduits (`H86D-CTHB` used radial `volcanic_vent_halo` only, not linear vent-chain alignments). | Already SHA-pinned (`f91bafba...`); `dist_known_fault_px` banned. |
| **GDR 1391 `wellspringdata.gdb.zip`** (`ext_gdr_wellspring_in_footprint.csv` pinned in `data_manifest.json`) | CC-BY-4.0 (public) | `2,146,771 B` CSV (`sha256: 122718e6...`) | Thermal wells, springs, and aqueous geothermometry (`SiO2`, `Na-K-Ca`) trace blind upflow zones along concealed intrabasin faults. | **Must drop `dist_known_fault_px`** (enforced in `scripts/h86d_features.py`). |
| **USGS Multi-Depth MT Conductance (`DOI 10.5066/P9TWT2LU`)** (Peacock & Bedrosian 2022) | USGS Public Domain | 5 depth slices (`2–200 km`); **not yet mirrored** | Separates shallow closed-basin evaporitic playa brines (`< 2 km`) from deep (`2–10 km`) subvertical hydrothermal fault-conduit and smectite-illite clay-cap conductance boundaries (unlike single-band `cond_surf` Band 17). | Independent 3D MT inversion; canary check required. |
| **USGS Conductive Heat Flow (`DOI 10.5066/P9BZPVUC`)** (DeAngelo et al. 2022) | USGS Public Domain | Regional grids; **not yet mirrored** | Conductive background heat flow after removing shallow convective overprints, isolating deep crustal thermal anomalies. | Independent USGS thermal release; canary check required. |
| **GDR 1391 `qfaults_ingenious_*.zip` & USGS `DOI 10.5066/P9YL58W6`** | CC-BY-4.0 / Public Domain | Fault shapefiles | **FORBIDDEN AS UNMASKED INPUT FEATURES:** Directly encode INGENIOUS / USGS Quaternary fault traces (`existing_faults.tif` / withheld truth). | **Hard exclusion outside fold-visible mask.** |

---

## 5. Coupled Hydrothermal-Vent Signature for Unmapped Fault Detection (`H86E-HMDC`)

When hot reducing fluids ascend along an unmapped intrabasin or relay-ramp fault beneath alluvial cover, four independent physical observables co-localize along a linear corridor (`>= 600–1,200 m`):

1. **Hydrothermal magnetite destruction (`rtp` Band 2 & `tmi_vg` Band 9 linear trough):** Sulfidation/oxidation of host-rock magnetite ($\text{Fe}_3\text{O}_4 \to \text{FeS}_2$ pyrite / hematite / leucoxene) creates a narrow, strike-persistent **negative magnetic trough** flanked by unaltered magnetic volcanic shoulders — the **opposite curvature sign** from the positive magnetic ridges extracted in `H86D-CTHB` (`mag_ridge_s15`).
2. **Pairwise co-linear vent / sinter / 2-m probe geodesic bridges:** Rather than radial Gaussian halos (`paleo_sinter_vent`, `volcanic_vent_halo` in `H86D-CTHB`), connect co-linear triplets/pairs of sinter/tufa deposits (`paleo_geothermal_regional.zip`), Quaternary volcanic vents, and 2-m temperature probe anomalies within `<= 6 km` along regional Basin-and-Range / Walker Lane transtensional azimuths.
3. **Potassic alteration / sinter-travertine radiometric ratio (`K/Th` & `U/Th` in `geodawn_extensions_u8.tif`, DOI `10.5066/P93LGLVQ`):** Potassium enrichment in adularia/illite clay alteration relative to immobile thorium elevates `K/Th` along shallowly exhumed fault-vent damage zones, while uranium mobilization marks redox fronts.
4. **Dilatant conductive conduit (`cond_surf` Band 17 × `geod_dilaterate` Band 8 × `geod_shearrate` Band 7):** High electrical conductivity from hot saline fluids + smectite clay alteration restricted to actively dilating/shearing transtensional crust (suppressing stagnant non-dilatant playa centers via detrended elevation / closed-basin flat vetoes).
