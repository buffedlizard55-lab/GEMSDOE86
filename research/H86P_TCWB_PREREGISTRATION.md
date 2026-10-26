# H86P-TCWB Preregistration & Candidate Geological Hypothesis Queue

- **Lane ID:** `H86P-TCWB`
- **Branch:** `arena/1595e23f-gemsdoe86`
- **Frozen UTC:** `2026-10-26T01:10:00Z`
- **Machine Preregistration:** [`research/H86P_TCWB_PREREGISTRATION.json`](H86P_TCWB_PREREGISTRATION.json)
- **Hypothesis Queue Registry:** [`registry/h86p_hypotheses_20261026.json`](../registry/h86p_hypotheses_20261026.json)
- **Protocol Budget:** `<= 3` experiments (`E1`, `E2`, `E3`), `<= 2` hours, `0` weekly submission slots spent.

---

## 1. Structural & Radial Allocation Motivation Across Focus Sites (`GEMSDOE24`–`36`) and `GEMSDOE86`

Direct pixel-level audits across all 27 GeoTIFFs from the 9 focus sites (`GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, `36`) and prior `GEMSDOE86` lanes reveal two complementary bottlenecks:

1. **Unused Native Physical Modalities & Untried Buried-Piedmont / Basement-Hinge / Clay-Cap Operators:**
   - `Band 6 (tc)` is verified in `src/gems86/io.py` (`BAND_PHYSICS_VERIFIED[6]`) as strictly positive **GeoDAWN Airborne Radiometric Total Count** (`r = +0.99714` vs `geodawn_rad_u8` TC, *not* magnetic tilt), yet was unused in `H86K-STDP`, `H86M-SLCQ`, and open sibling PR #179 (`H86N-SHPB`). Active piedmont faults buried under Holocene sheetwash juxtapose U/Th/K-bearing footwall fanhead detritus against fine distal hanging-wall wash (`tc_downslope_wash_asym`, `tc_crossbreak_contrast`).
   - `Band 15 (depth_to_base_surf)` kinks sharply at buried half-graben footwall crests ($\mathbf{n}_b^\top \mathbf{H}(Z_b)\mathbf{n}_b > 0$) concordantly with horizontal Bouguer gravity drops ($-\mathbf{n}_b \cdot (\text{B18}, \text{B11}) > 0$), yet `H86O-3_DBK` (`registry/h86o_hypotheses_20261025.json`) had never been implemented.
   - `Band 17 (cond_surf)` forms hanging-wall smectite/illite hydrothermal clay caps in blind Great Basin geothermal systems (Bradys, Desert Peak, Dixie Valley, McGinness Hills) that **terminate laterally against sealing fault planes** (`claycap_fault_seal_term`) where boiling fluids destroy titanomagnetite (`Band 2 rtp`), rather than forming only narrow symmetric ridges.
2. **Near-Catalogue Stress-Shadow Crowding vs Far-Field (`> 1 km`) Blind-Fault Budget:**
   - Across live owner-reported submissions, top performers (`GEMSDOE32` `0.2778` at `69.8% > 1 km`, `GEMSDOE28 h36-1` `0.2710` at `65.7% > 1 km`, `GEMSDOE27 h29` `0.2190` at `61.8% > 1 km`, `GEMSDOE70` `0.2478` at `55.1% > 1 km`) allocate `55–70%` of their `37,654` dots beyond `1 km` from mapped faults, whereas `H86M-SLCQ` (`0.1527` `HOLDOUT-DTI`) placed `59.0%` inside `300 m–1 km`.
   - Sampling coupled PU negatives down to `4.5 px` (`450 m`, inside broadside Coulomb stress shadows rather than excluding `3.0–8.0 px`) plus radial-and-cover-aware Noisy-OR fusion with the blind `TCWB` specialist suppresses broadside halo clutter while boosting far-field blind fault discovery.

---

## 2. Four Ranked Candidate Geological Hypotheses (`H86P` Queue)

| Rank | ID | Candidate Hypothesis | Specific Layers | Targeted Physical Signature & Transform | Off-Catalogue Rationale & Named Mimics | Expected Gain / Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **`H86P-1_TCWB`** | **Downslope TC Wash-Blanket Asymmetry $\times$ Gravity-Signed Basement Hinge Kink $\times$ Clay-Cap Fault-Seal Termination + Radial-Cover Elkan-Bayes 6-Ring Dinkelbach-CELF** | Native Bands `2,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19` + SHA-pinned `.cache/external/` (`acquisition_block_id_100m`, `geodawn_rad_u8`, `geodawn_extensions_u8`, `lidar_scarp_features_u8`, `topo_10m_derived_100m_u8`, `dem10_chi_100m_i16`, GDR `#1391` wells/2m-probes/sinter/vents with `dist_known_fault_px` banned) | One-sided downslope `Band 6 (tc)` wash depletion (`±450 m` along $-\nabla G_5(\text{B12})$, seam-vetoed & Lahontan-suppressed); vector-gravity-signed `Band 15` footwall hinge kink pulled back up-dip by adaptive Salem $\cot\delta$; one-sided `Band 17` smectite clay-cap lateral seal termination; `Bands 7,8 x 10,16` seismo-dilatancy gate; Aitchison CLR radiometric Jacobian; 4.5 px de-crowded 4-fold LOQO Elkan-Bayes PU + radial-cover Noisy-OR + 6-ring survival Dinkelbach-CELF (`37,654` dots). | Catches sheetflood-beveled piedmont faults, buried half-graben master hinges, and blind hydrothermal clay-cap sealing faults; suppresses Lahontan benches, fan toes, GeoDAWN seams, NNR mafic dikes, paleovalleys, and injection swarms. | **Highest** / **Medium** (~15 min CPU) | **SELECTED FOR VALIDATION** |
| **2** | **`H86P-2_BCSF`** | **Thin-Plate Elastic Basement Flexural Shear Force ($-\partial_{nnn}^3 Z_b$) & Footwall-Uplift Couple** | Native Bands `15 (depth_to_base_surf)`, `12 (det_elev)`, `18 (+dg/dx_east)`, `11 (+dg/drow_south)` | Signed cross-strike third derivative $-\partial_{nnn}^3 Z_b$ ($\sigma = 4\text{–}8\text{ px}$) gated by upslope residual `Band 12` footwall uplift and basinward gravity moat. | Catches range-front step-out faults where cumulative elastic flexure outlasts scarp burial; mimics are caldera ring margins and pluton roofs. | **Medium-High** / **Low** (~3 min CPU) | **QUEUED** |
| **3** | **`H86P-3_RCSD`** | **Full Aitchison Compositional Radiometric Tensor Decomposition (Provenance vs Constant-Th Epithermal Metasomatism)** | Native Bands `6 (tc)`, `2 (rtp)` + GeoDAWN `K, eTh, eU` & `acquisition_block_id_100m` | $2\times 2$ structure-tensor eigen-separation of $\operatorname{clr}(\text{K, eTh, eU})$ into lithologic provenance steps vs constant-$\text{eTh}$ potassic/redox fault-conduit alteration. | Catches eroded Walker Lane / Humboldt epithermal bedrock faults lacking Quaternary scarps; mimics are ash-flow cooling units and alkali playa crusts. | **Moderate** / **Low-Medium** (~4 min CPU) | **QUEUED** |
| **4** | **`H86P-4_USMT`** | **EarthScope USArray 3-D Magnetotelluric Mid-Crustal Sub-Vertical Conductive Fault-Root Curtain** | Official free public NSF EarthScope / IRIS SPUD EMTF & USGS ScienceBase 3-D MT models (`3–15 km`) + native Bands `17, 15, 10, 8` | Lateral log-conductivity gradient & phase-tensor skew of mid-crustal conductive fault roots aligned with shallow `Band 17` terminations and `Band 10` seismicity. | Catches deep crustal fluid conduits beneath thick basin fill; mimics are Paleozoic graphitic black-shale thrusts. | **Moderate-High** / **Deferred** (sandbox egress restricted to `github/pypi/npmjs`; unmirrored) | **DEFERRED (EGRESS)** |

---

## 3. Preregistered 3-Experiment Budget (`E1`, `E2`, `E3`)

1. **`E1_tcwb_coupled_radial_dcelf` (Primary Candidate):** 26 static `TCWB` planes + 6 fold-visible Kostrov–Pollard planes, 4-fold eroded-LOQO (`quad != q` eroded 12 px) + nested cross-component PU (`coupled_neg_buffer_px = 4.5`) with Elkan (2001) Bayes prior-odds recalibration, radial-and-cover-aware Noisy-OR fusion with blind `TCWB` specialist, Exact 6-Ring Bernoulli Survival Dinkelbach-CELF (`37,654` dots, `d_min = 2.8 px`, `d_cat > 3.0 px`).
2. **`E2_tcwb_blind_piedmont_basement_dcelf` (Pure Zero-Catalogue Blind Specialist):** 26 translation-invariant `TCWB` static planes + `TCWB` physics corroboration prior (`0` fold-visible elastic features at inference), Exact 6-Ring Dinkelbach-CELF (`37,654` dots).
3. **`E3_local_unpulled_staticek_ablation` (Preregistered Ablation Control):** 8 pixel-local unpulled gradient/blur planes + isotropic tip halo without `TCWB` physics, up-dip pullback, Elkan-Bayes recalibration, or Dinkelbach-CELF, decoded via static expected-kernel Poisson-disc thinning (`37,654` dots).
