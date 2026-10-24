# Session review — 2026-10-24 (PhD analysis of `GEMSDOE32` `0.2778`, 92-site fleet audit, PR #60 forensic revocation, and 4 ranked hypotheses)

## Executive outcome

- **Release decision: `DO NOT SUBMIT` (`verdict: "negative"`, `safe_to_submit: false`, `submission_ready: false`).**
- **Unmet deliverable stated plainly:** No new unique competition GeoTIFF is cleared for DrivenData upload in this session (`new_candidate_generated = false`, `experiments_run = 0`, `submission_slots_used = 0`). Under `scripts/protocol_preflight.py`, the SHA-pinned historical continuous witness from `buffedlizard55-lab/17GEMSDOE` (`sha256: ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`) covers **`5,106,385 / 5,106,385` (`100.0%`)** of allowed off-catalogue footprint cells within `3 px` (`uncovered_allowed_pixels = 0`), forcing `STOP_LITERAL_OVERLAP_UNSATISFIABLE` (`1.0 > 0.70`) before any compliant model fit or dot placement.
- **Critical safety remediation (`IR-86-SPT-02` & `IR-86-TIPRELAY-01`):** Forensically audited and revoked both PR #60 (`2538214`, `SPT`, `sha256: 26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342`: `100%` witness overlap, `AUC = 0.4947 < 0.50` canary, withheld test-fold collar leak) and concurrent PR #63 (`502fc14`, `H86-TIPRELAY`, `sha256: c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3`: `85.08% > 70%` 3-px overlap even against sparse `GEMSDOE32` `h33-h33-2-b2`, `100%` witness overlap, zero holdout evaluation, and an unregistered `docs/downloads/` backdoor that broke `check_site.py` and `build_site.py --check` on `main`).

---

## 1. PhD-level answer: Why did `GEMSDOE32` (`h33-h33-2-b2`: `0.2778` `OWNER-REPORTED`) achieve the highest fleet score, and can we beat `0.2778` / `0.3195` / `0.4413`?

### 1.1 Exact pixel-level mechanism of `GEMSDOE32` (`h33-h33-2-b2`)

1. **Evidence class first:** `0.2778` (for `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`), `0.3195`, and `0.4413` are **`OWNER-REPORTED` claims** from the user prompt (`IR-86-PROMPT-CONFLICT-20261024`), not `ORGANIZER-CONFIRMED` submission-page receipts in this repository.
2. **Pixel-exact forensic identity (`0` differing pixels out of `12,279,160`):** Direct read-only comparison of the pinned `GEMSDOE28` `h27-4-r1-solo-d2-8` raster (`40,199` unit-mass dots; `0.2708` `OWNER-REPORTED`) and the pinned `GEMSDOE32` `h33-h33-2-b2` raster (`37,654` unit-mass dots; `0.2778` `OWNER-REPORTED`) against `existing_faults.tif` proves:
   $$\text{R0}_{\text{GEMSDOE32}} \equiv \text{D2.8}_{\text{GEMSDOE28}} \wedge \bigl(\text{EDT}(\neg\text{catalogue}) > 2.0\text{ px}\bigr)$$
   Deleting the exact **`2,545` dots** in the `1.0 < d_cat <= 2.0` (`100–200 m`) mapped-fault collar reproduces `h33-h33-2-b2` with **zero pixel discrepancy across the entire `3730 × 3292` grid**.
3. **Why this geometry aligns tightly with the asymmetric Distance-Weighted Tversky Index (`DTI`):**
   - Under `vendor/template66/gems57/metric.py` (`alpha = 0.2` false-positive weight, `beta = 0.8` false-negative weight, `R = 3 px = 300 m` isotropic triangular kernel $K(\Delta) = \max(0, 1 - \|\Delta\|_2 / 3)$), truth recovery $T = \sum_{y \in G} \max_{x} p(x) K(x - y)$ takes a **pointwise maximum** rather than a sum over nearby dots, whereas false-positive cost $F$ accumulates across every emitted dot not matched to hidden truth.
   - **Disk spacing (`d ≈ 2.8 px ≈ R`):** Placing unit-mass (`1.0`) dots on a Poisson-disk / greedy-exclusion packing of radius `2.8 px` reduces redundant nearby placements but does not prevent kernel overlap: two radius-3 px discs can overlap whenever their centres are less than 6 px apart. The max-kernel evaluator, not a non-overlap guarantee, determines the marginal recovery credit while covering curvilinear corridors with `300 m` tolerance cones on a high-prior lineament skeleton (`H19-5` / `H27-4`).
   - **Collar pruning (`d_cat > 2.0 px`):** Known `existing_faults.tif` pixels are masked during scoring, and a dot at `1 < d_cat <= 2 px` sees a large fraction of its `3 px` kernel disc land on masked known faults where no new-fault truth credit is available while still paying `0.2` false-positive weight on off-truth cells. Removing `b` units of pure false-positive mass while losing `a` units of truth credit improves `DTI = T / (0.2 T + 0.2 F + 0.8 N + \epsilon)` if and only if:
     $$T \cdot b > a \cdot (F + 4N + 5\epsilon)$$
     Moving from `40,199` to `37,654` dots removed `2,545` high-collar-overlap dots, plausibly explaining the reported `+0.0070` gain (`0.2708 → 0.2778`).
   - **Corroboration from the 8 new 2026-10-24 fleet scores:** Over-dense or unthinned placements (`GEMSDOE79` `100,000` dots → `0.0005`; `GEMSDOE84` `58,000` px → `0.0132`; `GEMSDOE81` continuous `44,090` → `0.0041`) have low owner-reported results, consistent with but not proving denominator inflation (their supports and physical models differ too), whereas `~37.6k–39k` submodular 300 m decoders (`GEMSDOE70` → `0.2478`, `GEMSDOE76` `ptcf-tiltworm-submod39k` → `0.2343`, `GEMSDOE73` → `0.1917`, `GEMSDOE82` → `0.1886`) consistently reach the `0.19–0.25` tier.

### 1.2 Can we beat `0.2778` (and reach `0.3195` / `0.4413`)?

- **Not by geometric collar-tweaking or re-allocating `R0` dots alone:** Seven axes of `R0` post-processing in this repo (`PRUNE`, `CONCENTRATION`, `RELIEF`, `SPACING`, `SNAP`, `MASS`, `TRACKB`) showed that `R0`'s `H19-5` support has only `90` free legal slots left (`IR-86-CONC-16`), and local perturbations move proxy scores by at most `|Δ| <= 0.0073`, whereas `+0.01` live DTI at `0.2778` (`|G| ≈ 40k`) requires **`~418` new kernel-credit units (`~42 km` of genuinely unmapped fault trace hit squarely)**.
- **Where genuine upside exists (and what is already measured on holdout):**
  - On `gems57-pooled-hide-v2` (`HOLDOUT-DTI`), `GEMSDOE86`'s strongest physical discovery lane (`H86D-CTHB`, `37,654` dots, 35 geophysical + hydrothermal features) achieves **`0.2506` (`95% CI [0.2351, 0.2669]`)** on whole-segment hide-and-recover (vs `D2.8 = 0.1011` and fold-fair `H33-2-B2 = 0.0910`), **`0.2588` (`[0.2402, 0.2779]`)** on detached segments, and **`0.1133` (`[0.0965, 0.1297]`)** on strict buffered whole-component LOQO (vs `H33-2-B2 = 0.1056`, paired delta **`+0.0076`, 95% CI `[-0.0101, +0.0241]`**).
  - Because that strict buffered whole-component paired CI still crosses zero (`-0.0101`) AND the literal `17GEMSDOE` dense-witness rule blocks promotion, **we cannot scientifically guarantee beating `0.2778` today**.
  - Closing the gap from `0.25–0.28` toward `0.32–0.44` requires **new orthogonal physical observables** that resolve blind/subtle faults invisible to 100 m unsigned potential-field edges: (i) **signed dip-slip throw concordance** across basin-depth and isostatic gravity beneath flat alluvium, (ii) **two-sided cross-fault lateral phase translation** of magnetic marker horizons, (iii) **deep MT electrical conductance + GPS geodetic dilatancy** (`DOI 10.5066/P9TWT2LU`, `GDR 1391`), and (iv) **native 1-m USGS 3DEP LiDAR micro-scarp curvature** (`1m_DEM_links.csv`), all decoded via `R = 300 m` greedy submodular facility-location at `~36k–39k` unit-mass dots.

---

## 2. Four ranked candidate geological hypotheses (`registry/h86c_hypotheses.json`)

All four are declared before implementation (`experiments_run = 0`, `holdout_dti = null`, `ci95 = null`, `status = NOT_RUN*`) under the mandatory preflight stop:

1. **Rank 1 — `H86E-SPBT`: Signed paired-throw basement–gravity concordance under low-relief alluvial cover**
   - **Layers:** `depth_to_base_surf` (Band 15), `iso_grav_anom` (Band 13), `det_elev` (Band 12, DOI `10.5066/P9MQRCBY`), `mag_horiz_grad` (Band 2, DOI `10.5066/P93LGLVQ`).
   - **Physical signature:** Strike-oriented cross-flank signed step product $(+\Delta\text{depth\_to\_base\_surf})\cdot(-\Delta\text{iso\_grav\_anom})$ across $\pm 400\text{ m}$ flanks with $\ge 900\text{ m}$ strike continuity, up-weighted where `det_elev` relief is muted by Holocene basin fill, benchmarked against a polarity-scrambled control.
   - **Why catalogue-missing:** USGS/INGENIOUS catalogues strongly sample subaerial range-front scarps (`det_elev` breaks) and under-sample buried intrabasin growth faults where sedimentation erases topography while dip-slip preserves same-side basement and gravity steps.
   - **Novelty vs repo:** Prior `GEMSDOE86` lanes (`GMC`, `RMRB`, `WVB`, `GFCO`, `KSLB`, `CTHB`) use unsigned gradients, tilt zero-crossings, or Blakely curvature ridges; PR #60 mentioned signed throw in prose without ever loading `training_features.tif` (`IR-86-SPT-02`).
   - **Non-fault mimic:** Unfaulted pre-Tertiary paleovalley walls or caldera moats filled by low-density tuffs.
   - **Cost / data:** Low–medium (`~35 min` CPU on local mirrored `training_features.tif`; no external data needed; blocked by `require_feasible()`).

2. **Rank 2 — `H86E-MMT`: Cross-corridor GeoDAWN magnetic marker-horizon phase-correlation offset**
   - **Layers:** `rtp_tilt_deriv` (Band 14), `mag_horiz_grad` (Band 2), `ter_rad_k` (Band 6).
   - **Physical signature:** Split-window 1-D FFT phase correlation of transverse magnetic marker ridges across $\pm 700\text{ m}$ corridors requiring coherent nonzero lateral shift across adjacent strike windows and weak zero-shift match (retaining both dextral and sinistral slip).
   - **Why catalogue-missing:** Oblique Walker Lane / Humboldt accommodation-zone transfer structures offset buried Tertiary volcanic sheets across basin floors without building prominent range-front scarps.
   - **Novelty vs repo:** Existing lanes evaluate single-window gradients/cross-gradients rather than two-sided cross-corridor lateral marker translation.
   - **Non-fault mimic:** GeoDAWN survey-block tie seams, intrusive contacts, and primary lava-flow lobe terminations.
   - **Cost / data:** Medium–high (`~65 min` CPU on local `training_features.tif`; no external data needed; blocked by `require_feasible()`).

3. **Rank 3 — `H86E-MTCS`: Magnetotelluric crustal conductance boundary × geodetic transtensional dilatancy bridge**
   - **Layers:** USGS Great Basin MT electrical conductance grids (`https://doi.org/10.5066/P9TWT2LU`), INGENIOUS GPS geodetic strain-rate & dilatation archive (`geodetics` in `https://gdr.openei.org/submissions/1391`, DOI `10.15121/1881483`), GeoDAWN `rtp_tilt_deriv` (Band 14), and INGENIOUS `2m` temperature / heat flow (`10.5066/P9BZPVUC`).
   - **Physical signature:** Steep $1\text{–}5\text{ km}$ horizontal $\log_{10}\Sigma_{\text{MT}}$ boundaries co-aligned with positive horizontal geodetic dilatation ($\dot{\varepsilon}_{xx}+\dot{\varepsilon}_{yy} > 0$) and maximum shear strain rate, sharpened along RTP tilt zero-crossings.
   - **Why catalogue-missing:** Blind hydrothermal upflow zones often lack Holocene surface scarps yet produce saline-fluid + smectite-illite conductive damage zones inside actively dilating crust — the core blind geothermal target of INGENIOUS Phase 2 expert relabeling.
   - **Novelty vs repo:** Zero `GEMSDOE86` lanes ingest MT electrical conductance or GPS strain-rate/dilatation grids.
   - **Non-fault mimic:** Closed-basin playa evaporite brines and stratiform Paleozoic graphitic/sulfidic black shales.
   - **Cost / external data obtainability:** Medium–high; public CC-BY-4.0 metadata and archive listings verified live on 2026-10-24 at `https://gdr.openei.org/submissions/1391` and `https://gbcge.org/current-projects/ingenious/`, but `NOT_VIABLE_YET` inside this sandbox until binary grids are mirrored onto an allowed host (excluding `qfaults_ingenious` shapefiles to prevent label leakage).

4. **Rank 4 — `H86E-WCS`: Watershed-crossing 1-m 3DEP LiDAR micro-scarp curvature persistence**
   - **Layers:** Official USGS 3DEP bare-earth `1 m` DEM tiles (`1m_DEM_links.csv` in `https://docs.nlr.gov/docs/fy26osti/96647.pdf`), `det_elev` (Band 12), `surf_rough` (Band 10).
   - **Physical signature:** Cross-strike `5–25 m` elevation second-derivative scarp steps on native `1 m` LiDAR DEMs retaining strike and downthrown polarity across independent drainage divides, vetoing channels, constant-elevation shorelines, and road grades.
   - **Why catalogue-missing:** Low-slip (`0.3–1.5 m`) late Quaternary piedmont scarps are smoothed out at `30–100 m` DEM resolution and missed in pre-LiDAR airphoto mapping.
   - **Novelty vs repo:** Zero `GEMSDOE86` lanes ingest native `1 m` 3DEP LiDAR tiles.
   - **Non-fault mimic:** Pleistocene Lake Lahontan shoreline benches, fluvial terrace risers, and road/rail embankments.
   - **Cost / external data obtainability:** High (`2–4 hr` external tile streaming); `NOT_VIABLE_YET` until `1m_DEM_links.csv` / 3DEP tile summaries are SHA-pinned into a reachable mirror.

---

## 3. Forensic audit & revocation of PR #60 (`IR-86-SPT-02`)

Read-only inspection of commit `2538214` (PR #60) identified five disqualifying defects:
1. **Literal witness overlap (`100% > 70%`):** Direct comparison of `submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.tif` (`267,158` bytes, `sha256: 26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342`) against `17GEMSDOE` `dense-witness.tif` (`ab0a0a62...`) yielded `my_dots_within_3px_of_theirs = 1.0` (`duplicate_by_overlap = true`).
2. **Coin-flip feature canary (`AUC = 0.4947 < 0.50`):** The cross-fleet throw-consensus surface scored below random chance against mapped faults.
3. **Withheld test-fold collar leakage:** `scripts/build_spt.py` computed `allowed = foot & (dist_cat > 2.0)` from the **entire** `existing_faults.tif` raster (including hidden test folds with zero buffer), selectively deleting `R0` dots near hidden test faults (`0.00526` vs `0.00479`).
4. **Prose-vs-code misrepresentation:** `research/SPT_20261024.md` claimed signed paired-throw on `training_features.tif` bands `15`, `13`, and `12` was executed, whereas `scripts/build_spt.py` never opened `training_features.tif` and exported with `SPT_PENALTY=0` while claiming `"surface-penalised"` in `note`.
5. **Preflight & inventory bypass:** `build_spt.py` and `build_xfleet.py` executed at import time without `protocol_preflight.require_feasible()` and placed unregistered binaries in `submission/` linked from a hand-edited `docs/submit.html` (`READY TO DOWNLOAD`).

**Remediation completed:** Removed `submission/gems86-spt-throwcons-*`, gated `build_spt.py` and `build_xfleet.py` behind `require_feasible()` (verified in `tests/test_builder_preflight.py`), updated `spt-run-card.json` / `xfleet-run-card.json` / `spt-independent-validation.json` to `verdict: "negative"`, generated `docs/submit.html` via `scripts/build_site.py` as an explicit `DO NOT SUBMIT` revocation page, and hardened `scripts/audit_release.py` + `scripts/check_site.py` against `submission/` binaries, `READY TO DOWNLOAD` / `raw.githubusercontent.com` HTML bypasses, and optimistic sidecar cards.

---

## 4. Official verified primary sources (checked 2026-10-24)

- **DOE / NLR GEMS Prize Official Rules PDF:** <https://docs.nlr.gov/docs/fy26osti/96647.pdf> — all 7 chunks verified on 2026-10-24 ($300,000 total prize pool: $50,000 Phase 1 + $250,000 Phase 2; 100 m GeoTIFF over GeoDAWN study area; up to 3 weekly public-leaderboard submissions; **one** final submission selected across both phases; mandatory AI disclosure and reproducible code for finalists).
- **GBCGE INGENIOUS Project (UNR / DOE GTO DE-EE0009254):** <https://gbcge.org/current-projects/ingenious/> — verified 2026-10-24; links regional compilation (`10.15121/1881483`), heat flow (`10.5066/P9BZPVUC`), gravity/magnetics (`10.5066/P9Z6SA1Z`), MT conductance (`10.5066/P9TWT2LU`), fault slip/dilation tendency (`10.5066/P9YL58W6`), and geodetic strain rates (`10.1785/0220220153`).
- **DOE GDR Submission 1391 (INGENIOUS Great Basin Regional Dataset Compilation):** <https://gdr.openei.org/submissions/1391> — verified 2026-10-24 (CC-BY-4.0, 9 downloadable archives totaling `116.98 MB`; includes `qfaults_ingenious` fault shapefiles that must be excluded from features to avoid label leakage).
- **USGS GeoDAWN Airborne Magnetic & Radiometric Survey:** <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> (returned `HTTP 504` on 2026-10-24; 2026-10-23 verified excerpt retained in `docs/evidence/source-review-20261023.json`, and ScienceBase DOI `https://doi.org/10.5066/P93LGLVQ` confirmed in Official Rules PDF).
- **EPSG:32611 (`WGS 84 / UTM zone 11N`):** <https://epsg.io/32611> — verified 2026-10-24 (`metre` units, central meridian `-117°`, scale factor `0.9996`, false easting `500000 m`).
- **Tversky Index (Tversky 1977):** <https://en.wikipedia.org/wiki/Tversky_index> — verified 2026-10-24 (`alpha=0.2`, `beta=0.8` weights missed positives `4x` over false positives).
- **Competition Portal & Reference Solution (dated 2026-10-23 public records, not scraped):** <https://www.drivendata.org/competitions/306/competition-doe-gems/>, <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>, <https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/>, and <https://github.com/drivendataorg/gems-prize-reference-solution>.

---

## 5. Multi-pass verification record

- **Pass 1 (Implement & verify):** Restored SHA-pinned protocol rasters + `17GEMSDOE` witness; verified `R0` pixel-exact collar identity (`40,199 - 2,545 = 37,654`, `0` diff pixels) and PR #60 `SPT` defects (`100%` witness overlap, `0.4947` canary AUC, test-fold collar leak, prose-vs-code mismatch); archived `research/REQUEST_20261024.md` and embedded in `README.md`; expanded fleet registry `88 → 92` sites (`92/92` snapshotted in `fleet-feed.json`, `113` scored `OWNER-REPORTED` rows in `prior_scores.csv`, `ledger/submissions.csv` rebuilt); expanded `registry/h86c_hypotheses.json` to 4 ranked hypotheses; gated `build_spt.py` + `build_xfleet.py` behind `require_feasible()`; removed `submission/` binaries; hardened `audit_release.py` + `check_site.py`; updated `build_site.py` (`docs/submit.html` + `executive-summary.html` portal checklist) and ran `audit_release.py --measure-registry`, `build_site.py --check`, `check_site.py`, `audit_downloads.py`, and `audit_h86d.py`.
- **Pass 2 (Review for bugs, missing requirements, edge cases & fix):** Verified `test_optimistic_scientific_card_cannot_promote` compatibility between linked scientific cards vs unlinked sidecar `*card*.json` files; verified `test_root_import_and_guard_precede_parser_io_and_placement` exact 3-statement AST contract on `build_spt.py` and `build_xfleet.py`; added explicit regression tests for unregistered `submission/` binaries, `READY TO DOWNLOAD` / `raw.githubusercontent.com` HTML bypasses, optimistic sidecar run cards, 92-site traceability, and 2026-10-24 request embedding.
- **Pass 3 (Re-check against original request, accuracy, reliability & final audit):** Line-by-line cross-check of every metric, byte count, SHA-256 digest, link, archive marker, and test across `README.md`, `PROMPT.md`, `IRREGULARITIES.md`, `SLOT_PLAN.md`, `docs/*.html`, and `docs/evidence/*.json`; full `pytest -q` suite, `build_ledger.py --check`, `audit_release.py`, `audit_downloads.py`, `audit_h86d.py`, `build_site.py --check`, and `check_site.py` verified clean (`exit 0`).

---

## 6. Remaining limitations & recommended next-session actions

1. **Literal `17GEMSDOE` continuous-witness rule (`STOP_LITERAL_OVERLAP_UNSATISFIABLE`):** Requires an explicit owner protocol amendment distinguishing continuous probability surfaces (`>5.1M` positive pixels) from sparse dotted submissions (`~37.6k` pixels) before any nonempty GeoTIFF can legally clear Rule 1 (`<= 70%` 3-px dot overlap).
2. **Sandbox network allowlist (`github.com`, `pypi.org`, `npmjs.org` only):** Prevents direct DrivenData authentication (no live leaderboard check, remaining weekly slot balance, or `ORGANIZER-CONFIRMED` submission receipts) and prevents direct download from `gdr.openei.org`, `sciencebase.gov`, or USGS 3DEP S3/TNM without first SHA-pinning external datasets (`10.5066/P9TWT2LU` MT conductance, GDR-1391 `geodetics`, and `1m` LiDAR scarp summaries) into a GitHub mirror.
3. **Immediate next session once witness rule is amended:** Run `H86E-SPBT` (signed paired-throw basement–gravity concordance) and `H86E-MMT` (cross-corridor magnetic marker phase translation) on `gems57-pooled-hide-v2` buffered whole-component LOQO against `H86D-CTHB` (`0.1133`) and fold-fair `R0` (`0.1056`), promoting to the separate human selector step **only** if the paired physical-block 95% CI vs both controls excludes zero on the positive side and all 45+ non-lattice uniqueness and `[0, 1]` validator gates pass.
