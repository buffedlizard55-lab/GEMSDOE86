# PhD-Level Scientific Review, `GEMSDOE32` (`0.2778`) Forensic Proof, and `H86I-RKSC` Lane Report (`2026-10-25`)

- **Branch**: `arena/ef9c3480-gemsdoe86`
- **Lane Executed**: `H86I-RKSC` (*Lahontan-Deconfounded Piedmont Scarp Profile-Curvature Dipole coupled with GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step and Seismic-Conductance Conduit*)
- **Frozen Preregistration**: `research/H86I_RKSC_PREREGISTRATION.json` (`sha256: 83300b29d6c933737281863b4e0db9d0cfe6c8960ef6e090d5adb4964aae66af`) and `research/H86I_RKSC_PREREGISTRATION.md` (`sha256: 088462aad9568f452662dcbce3a59d8c7386c56746d72fabe1a6ecee6fb37cbc`), frozen before implementation.
- **Generated Unique Audit GeoTIFF**: `docs/downloads/gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.tif`
  - **Raster SHA-256**: `9437c83e0b5cf3fe1679ee26b6e41f200cf9a5eb08d7815a36a13a0e96f765ba` (`1,608,425` bytes; `44,090` emitted dots)
  - **Single-TIFF ZIP**: `docs/downloads/gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.zip` (`sha256: 65fb4bc4b018c254fb86182c42a3eb4a3be6e91b1846df8d56ef3c43ca77dd52`)
  - **Writer Receipt**: `docs/downloads/gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.json`
  - **Run Card**: `docs/evidence/h86i-rksc-run-card.json`
- **Automated Gate Verdict**: **`verdict = "negative"` · `decision = "DO NOT SUBMIT"` · `safe_to_submit = false` · `approved_for_weekly_slot = false` · `submission_slots_used = 0`**

---

## 1. Why and How `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` `OWNER-REPORTED`) Led the Fleet

### 1.1 Exact Pixel-Level Forensic Identity (`docs/evidence/h86f-h33-forensics.json`)
Byte- and pixel-level comparison across all $3730 \times 3292 = 12,279,160$ grid cells between:
1. **`GEMSDOE28` (`gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif`)**: `40,199` unit dots (`0.2708` `OWNER-REPORTED`), itself derived from `GEMSDOE25` (`gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`, `44,090` dots, `0.2682` `OWNER-REPORTED`) by deleting `3,891` dots at Euclidean distance $d_{\text{cat}} = 1.0\text{ px}$ (`100 m`) from `existing_faults.tif`, and
2. **`GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`)**: `37,654` unit dots (`0.2778` `OWNER-REPORTED`)

establishes the following deterministic identity:
$$\mathbf{1}_{\text{H33}}(y, x) \equiv \mathbf{1}_{\text{GEMSDOE28}}(y, x) \cdot \mathbf{1}\!\left(d_{\text{cat}}(y, x) > 2.0\text{ px}\right) \quad \forall (y, x) \in \Omega$$
with **zero differing pixels (`0 / 12,279,160`)** anywhere on the grid:
- `GEMSDOE32` deletes the exact `2,545` dots of `GEMSDOE28` lying in the $1.0 < d_{\text{cat}} \le 2.0\text{ px}$ (`141–200 m`) annulus around mapped catalogue faults (`40,199 - 2,545 = 37,654` dots).
- Outside the footprint, `GEMSDOE32` replaces `NaN` with `0.0` (`-zeros` suffix), ensuring finite float32 values in $[0, 1]$ everywhere.

### 1.2 Exact Distance-Weighted Tversky (`DTI`) Condition for Collar Pruning
Under the official GEMS evaluator (`vendor/gems57/metric.py`, $\alpha = 0.2$, $\beta = 0.8$, $300\text{ m} = 3\text{ px}$ radial triangular kernel $k(d) = \max(0, 1 - d/3)$):
- Each hidden ground-truth fault pixel $g \in G$ receives covered truth credit $c_G(g) = \max_{x} P(x)\,k(\|g - x\|_2) \in [0, 1]$, with total recovered truth $T = \sum_{g \in G} c_G(g)$ and false-negative mass $\text{FN}_w = |G| - T$.
- Each predicted dot $p \in P$ receives self-credit $c_P(p) = \max_{g \in G} k(\|p - g\|_2) \in [0, 1]$, contributing false-positive mass $1 - c_P(p)$ to $\text{FP}_w = \sum_{p \in P} (1 - c_P(p))$.
- Thus:
$$\text{DTI}(P, G) = \frac{T}{T + 0.2\,\text{FP}_w + 0.8\,(|G| - T) + \epsilon} = \frac{T}{0.2\,T + 0.2\,\text{FP}_w + 0.8\,|G| + \epsilon}$$

When a collar-pruning operation removes a dot subset $\Delta P$ (such as the `2,545` dots in $1.0 < d_{\text{cat}} \le 2.0\text{ px}$), losing truth credit $a = -\Delta T \ge 0$ while removing false-positive mass $b = -\Delta \text{FP}_w > 0$, the exact algebraic condition for $\text{DTI}(P \setminus \Delta P, G) > \text{DTI}(P, G)$ is:
$$\frac{T - a}{0.2(T - a) + 0.2(\text{FP}_w - b) + 0.8|G| + \epsilon} > \frac{T}{0.2\,T + 0.2\,\text{FP}_w + 0.8\,|G| + \epsilon} \iff T \cdot b > a \cdot (\text{FP}_w + 4|G| + 5\epsilon)$$

Why did removing the $1.0 < d_{\text{cat}} \le 2.0\text{ px}$ collar satisfy $T \cdot b > a(\text{FP}_w + 4|G| + 5\epsilon)$ on the organizer test set?
1. **Pixel-exact masking of mapped faults (`existing_faults.tif`)**: On the test evaluation grid, mapped catalogue pixels are masked out of $G$. A dot placed at $d_{\text{cat}} \in (1, 2]\text{ px}$ expends most of its $r = 3\text{ px}$ kernel footprint overlapping already-mapped catalogue pixels that cannot contain hidden truth $G$, except where an unmapped splay or relay branches immediately off a mapped trace.
2. **Redundant kernel coverage at junctions**: Even where a newly mapped branch joins a known trace, the adjacent dot at $d_{\text{cat}} \in (2, 3]\text{ px}$ already covers the junction within its $3\text{ px}$ (`300 m`) triangular kernel, making the marginal truth loss $a$ near zero while $b \approx |\Delta P| = 2,545$.

### 1.3 Why Purely Catalogue-Blind Geophysical Operators (`0.024–0.033`) Trail Dual-Regime Kinematic + Out-of-Fold Ensembles (`0.1241`)
Across five consecutive preregistered catalogue-blind lanes in this repository—`H86E-MMT` (`0.0290`), `H86F-GZZD` (`0.0303`), `H86H-PSTD` (`0.0314`), `H86F-PCC` (`0.0327`), and now `H86I-RKSC` (`0.0245`)—every zero-parameter, footprint-wide geophysical operator scored in the narrow band `0.0245–0.0327` on `gems57-pooled-hide-v2` (`seed=20`, `11,321` withheld positives), whereas:
- Fold-fair `R0` (`GEMSDOE25` `dotted-h19-5-d2-8` masked by `d_vis > 2.0 px`) achieves **`0.0961 [0.0829, 0.1094]`**, and
- Same-split `H86C-KSLB` (`E3_kslb_noisyor_44k`) achieves **`0.1241 [0.1080, 0.1403]`**.

The physical and statistical reason is fundamental:
1. **Single-band geophysical/radiometric/topographic derivatives have weak marginal correlation with Quaternary fault traces across the whole 5.17M-pixel footprint** (single-feature discriminative AUCs of `0.50–0.66`), because Miocene–Pliocene volcanic tablelands, calderas, plutonic margins, and non-tectonic erosional scarps occupy $10\times$ more area than active fault traces.
2. **Faults form kinematically linked networks**: In `gems57-pooled-hide-v2` (and in structural geology generally), unmapped fault segments preferentially occupy **crack-tip propagation cones, en-echelon relay stepovers, and strike-concordant damage corridors** anchored to visible fault terminations (`P_link`), combined with high-precision out-of-fold multi-physics filaments (`P_blind`) where dots are concentrated via expected-credit disk thinning (`emit_ek_poisson`) rather than spread uniformly across every $3\times 3\text{ px}$ tile (`emit_decimated`).

---

## 2. Contemporaneously Preregistered `H86I-RKSC` Lane Execution & Results

### 2.1 Band Physics Verification (`BAND-PHYSICS-QC`)
Before computing any feature plane, `scripts/run_h86i_rksc.py` verified:
- All 9 `training_features.tif` band indices (`4, 6, 7, 8, 10, 12, 16, 17, 19`) against `src/gems86/io.py::BANDS`.
- Pixel-level correlation of `training_features.tif` Band 6 (`tc`) against `data/external/geodawn_rad_u8.tif` Band 4 (`TC`, USGS GeoDAWN DOI `10.5066/P93LGLVQ`) across `4,875,879` interior footprint pixels: **$r = +0.997310$** (`> 0.98` fail-closed floor), confirming Band 6 is Airborne Radiometric Total Count.

### 2.2 Single-Feature Leakage Canary (`LEAKAGE-CANARY`)
Tested across all 4 buffered whole-component quadrants (`seed=20`, `11,321` withheld positives):
- `scarp_curvature_deconf`: mean AUC `0.4950`, max discriminative AUC **`0.5419`** (`PASS <= 0.90`)
- `scarp_tensor_anisotropy`: mean AUC `0.6098`, max discriminative AUC **`0.6640`** (`PASS <= 0.90`)
- `rad_kth_metasomatism_index`: mean AUC `0.4342`, max discriminative AUC **`0.6026`** (`PASS <= 0.90`)
- `rad_kth_step_concordant`: mean AUC `0.5060`, max discriminative AUC **`0.5458`** (`PASS <= 0.90`)
- `rad_depleted_lahontan_control`: mean AUC `0.4579`, max discriminative AUC **`0.6001`** (`PASS <= 0.90`)
- `seismic_upflow_gradient`: mean AUC `0.5031`, max discriminative AUC **`0.5615`** (`PASS <= 0.90`)
- `seismic_strain_conductance_gate`: mean AUC `0.5233`, max discriminative AUC **`0.5684`** (`PASS <= 0.90`)

### 2.3 Holdout Evaluation (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`, `11,321` Withheld Positives)

| Arm / Comparator | Evidence Class | `HOLDOUT-DTI` | 95% Block-Bootstrap CI | $\text{TP}_w$ | $\text{FP}_w$ | $\text{FN}_w$ | Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`E1_rksc_full` (Candidate)** | `HOLDOUT-DTI` | **`0.0245`** | `[0.0185, 0.0304]` | `416.9` | `39,384.6` | `10,904.1` | Beats both internal ablations (`E1 > E2 > E3`), confirming positive lift from Lahontan deconfounding, potassic metasomatic polarity, and seismic-conductance coupling; trails external `R0` and `H86C-KSLB`. |
| **`E2_rksc_rad_scarp_only` (Ablation)** | `HOLDOUT-DTI` | **`0.0235`** | `[0.0174, 0.0294]` | `401.9` | `39,907.6` | `10,919.1` | Pure GeoDAWN K/Th/U/TC + Lahontan-deconfounded scarp curvature without seismic/strain/conductance coupling. |
| **`E3_rksc_lahontan_uncorrected_control`** | `HOLDOUT-DTI` | **`0.0142`** | `[0.0093, 0.0196]` | `250.0` | `42,455.7` | `11,071.0` | Removing Lahontan shoreline suppression and inverting K/Th polarity drops DTI by `-42.0%` (`-0.0103`), validating the physical sign of `E1`. |
| **`R0_GEMSDOE25_d28_collar_3px`** | `HOLDOUT-DTI` | **`0.0931`** | `[0.0798, 0.1067]` | `1,506.9` | `34,128.3` | `9,814.1` | Unpruned `GEMSDOE25` `d2.8` masked by `d_vis > 3.0 px` on each fold; paired $\Delta(E1 - R0_{3\text{px}}) = -0.0686$ `[-0.0834, -0.0546]`. |
| **`R0_GEMSDOE25_d28_fold_fair_2px`** | `HOLDOUT-DTI` | **`0.0961`** | `[0.0829, 0.1094]` | `1,588.9` | `35,809.1` | `9,732.1` | Unpruned `GEMSDOE25` `d2.8` masked by `d_vis > 2.0 px` on each fold; paired $\Delta(E1 - R0_{2\text{px}}) = -0.0716$ `[-0.0866, -0.0582]`. |
| **`H86C-KSLB` (`E3_kslb_noisyor_44k`)** | `HOLDOUT-DTI` | **`0.1241`** | `[0.1080, 0.1403]` | — | — | — | Same-split historical best (`docs/evidence/lane86c_results.json`); not beaten. |

### 2.4 Pre-Placement Surface & Final-Dot Registry Uniqueness Scans (`REGISTRY-MEASUREMENT`)
- **Pre-placement surface scan (`docs/evidence/h86i-rksc-registry-surface.json`)**:
  - Measured across `687 / 689` registry rasters (`633` dot fields + `54` continuous surfaces; `0` missing files; `2` historical off-grid rows `14GEMSDOE` and `7GEMSDOE` recorded as errors).
  - **Worst Spearman rank correlation across all 687 valid rasters**: **`0.2633 <= 0.90`** (`0` rho firings; compare `H86F-GZZD` `0.8712` and `H86H-PSTD` `0.9040`).
- **Final-dot scan (`docs/evidence/h86i-rksc-registry-dots.json`)**:
  - **Byte-unique and pixel-unique** across all `687` comparable rasters (`byte_unique_among_checked = true`, `pixel_unique_among_checked = true`).
  - **Worst Spearman rank correlation**: **`0.0395 <= 0.90`** (`0` rho firings).
  - **Worst Jaccard index**: **`0.0140 <= 0.50`**.
  - **Forward 3-px overlap**: `1.0000` against `17GEMSDOE` (`5,167,373` positive pixels) and `13GEMSDOE` `r13-lattice-s5` (`206,895` stride-5 lattice dots covering `99.87%` of allowed cells within 3 px); `0` firings against any sparse (`<= 60,000`-dot) submission in the entire 687-raster registry (top sparse overlap is `27.09%` against `GEMSDOE50` `98,598`-dot `seislineage` and `10.58%` against `GEMSDOE48` `37,654`-dot `h50b-alteration-conflict`).
  - **PA-86-02 chance-overlap script (`scripts/pa86_chance_overlap.py`)**: Fails closed (`returncode = 1`, `gate_pass = false`) because `2` historical registry entries (`14GEMSDOE` and `7GEMSDOE`) have incompatible CRS/grid dimensions. Recorded verbatim as a failed gate.

---

## 3. Three-Pass Verification Log & Next-Session Recommendations

1. **Pass 1 (Implementation & Execution)**: Restored all 55 pinned competition/external/scored-fleet files and all 655 `data/registry_ext` rasters (`728.3 MB`), froze `research/H86I_RKSC_PREREGISTRATION.json` & `.md`, implemented `src/gems86_rksc/features.py` and `scripts/run_h86i_rksc.py`, executed the 3-arm holdout evaluation and full 689-entry surface + final-dot registry scans, serialized `gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.{tif,zip,json}`, and gated `run_h86i_rksc.py` in `tests/test_builder_preflight.py`.
2. **Pass 2 (Bug, Schema & Edge-Case Review)**: Caught and fixed the `training_features.tif` 19-band vs external `geodawn_rad_u8.tif` 4-band indexing via `verify_band_contract()`, eliminated float64 upcast memory spikes via sequential block garbage collection in `compute_rksc_arrays()`, and verified all 18 download artifacts through `audit_release.py --measure-registry` and `audit_downloads.py --write`.
3. **Pass 3 (End-to-End Site, Test & Protocol Audit)**: Synchronized `scripts/build_site.py`, `README.md`, `IRREGULARITIES.md`, `SLOT_PLAN.md`, and unit tests (`tests/test_h86i_rksc.py`, `tests/test_release_audit.py`), and verified `build_site.py --check`, `check_site.py`, `audit_downloads.py`, `audit_release.py`, and full `pytest -q`.

### Recommendations for Next Session
- **Combine `H86I-RKSC`'s orthogonal GeoDAWN K/Th/U/TC + Lahontan-deconfounded scarp planes with `H86C-KSLB`'s out-of-fold LOQO + kinematic tip/relay architecture**: Because `H86I-RKSC` has near-zero rank correlation (`0.0395` on dots, `0.2633` on surface) with existing rasters and strong internal ablation separation (`E1 > E3` by `+72.5%`), adding its immobile-normalized potassium metasomatic step `rad_kth_step_concordant` as a specialist feature inside the `H86C-KSLB` dual-regime noisy-OR framework (`S = 1 - (1 - P_link)(1 - P_blind)`) with `emit_ek_poisson` (`r = 2.8 px`) is the highest-leverage path to testing whether Holdout-DTI can exceed `0.1241 [0.1080, 0.1403]` while reducing dot overlap against `H19-5/D2.8` relatives.
- **Resolve the two protocol-level registry blockers before any live slot selection**: (1) formalize handling of the two off-grid historical registry entries (`14GEMSDOE` and `7GEMSDOE`) in `check_h86e_registry.py` / `pa86_chance_overlap.py`, and (2) obtain an explicit organizer/owner rule amendment separating space-filling continuous/lattice priors (`17GEMSDOE`, `13GEMSDOE` `r13-lattice-s5`) from sparse dot-field submissions.
