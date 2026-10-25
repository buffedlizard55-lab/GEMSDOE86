# H86F-EWCS Contemporaneous Preregistration (2026-10-24)

**Status:** Frozen prior to feature extraction, PU fitting, holdout evaluation, and registry comparison.
**Machine-readable specification:** `research/H86F_EWCS_PREREGISTRATION.json`
**Candidate hypothesis queue:** `registry/h86f_hypotheses.json` (`H86F-EWCS`, `H86F-GDFB`, `H86F-PFSB`, `H86F-USGS-3DGF`)

## 1. Scientific Hypothesis & Physical Mechanism

Mapped Quaternary faults in the USGS Qfaults and Great Basin INGENIOUS compilations routinely terminate at range-front canyon mouths or step across alluvial relay basins where Holocene debris-flow aggradation obscures surface scarps (`Band 19 det_elev_slope`). Previous `GEMSDOE86` lanes suffered from two structural limitations identified in repository forensics:

1. **Band-header physics mislabels (`IR-86-BAND6-TC-MISLABEL-20261024`, `IR-86-BAND11-18-GRAV-VECTOR-20261024`):** Supervised lanes (`H86C-KSLB`, `H86D-CTHB`) ingested `Band 6` (`tc`) as magnetic tilt (`mag_tc_z`) and `Band 11` as vertical gravity gradient, whereas pixel-level verification proved `Band 6` is Airborne Radiometric Total Count (`r = +0.997140`) and `(+Band 18, -Band 11)` is the signed 2-D horizontal gravity gradient vector `(+dg/dx_east, +dg/dy_north)`. Meanwhile, `H86E-MMT` used true analytical magnetic tilt `atan2(Band 9, Band 3)` only inside an unsupervised 4-feature lag heuristic (`HOLDOUT-DTI = 0.0290`).
2. **Unsigned tip halos without broadside stress-shadow physics:** Under linear elastic fracture mechanics (Pollard & Segall, 1987; King, Stein & Lin, 1994), slip along an interior fault segment casts a broadside **elastic stress-release shadow** perpendicular to mid-segment strike (`0.3–2.0 km`), while concentrating tensile hoop stress in forward off-axis **wing-crack lobes** (`~15–42 deg` off outward tip propagation vectors) and **opposing-tip releasing stepover bridges**.

**`H86F-EWCS`** tests whether combining:
- **Verduzco et al. (2004) harmonic magnetic tilt-depth contact sharpness** $|\nabla \theta_{\text{mag}}| \exp(-(\theta_{\text{mag}}/0.35)^2)$ with $\theta_{\text{mag}} = \arctan2(\text{B9}, \text{B3})$ (inverse burial depth $h^{-1}$ to truncated magnetic basement),
- **Source-free Laplace vertical gravity curvature** $g_{zz} = -(\partial_{\text{col}} \text{B18} + \partial_{\text{row}} \text{B11}) = -(\partial_{x_{\text{east}}} g_x + \partial_{y_{\text{north}}} g_y)$ zero-crossing steepness at $\sigma \in \{300\text{ m}, 600\text{ m}\}$,
- **Garland–Poisson gravity–magnetic Hessian principal-axis misalignment** $\sin^2(\psi_{\text{grav}} - \psi_{\text{mag}})$ and radiometric `Band 6 tc` surficial decoupling, and
- **Strictly fold-visible Pollard–Segall wing-crack lobes + opposing-tip stepover bridges minus broadside mid-segment stress-shadow zones**

improves hidden whole-segment fault recovery over matched subsurface-only (`E2`), isotropic-tip (`E3`), and `R0_D28_visible_collar` controls on the pinned `gems57-pooled-hide-v2` split (`seed=20, hide_frac=0.20, buffer_px=3`, `11,321` withheld positives).

## 2. Named Non-Fault Mimic Process

Steep unfaulted Mesozoic pluton margins or Tertiary caldera-wall ring-dike contacts situated down-strike of mapped range-front terminations produce sharp shallow tilt-depth contacts and Laplace $g_{zz}$ zero-crossings; Pleistocene Lake Lahontan wave-cut benches underlain by shallow volcanic flows can mimic piedmont slope breaks unless decoupled by subsurface potential-field continuity.

## 3. Preregistered Experimental Budget (`<= 3` Arms) & Fail-Closed Gates

1. **`E1_ewcs_coupled_pu`** (primary candidate): Full pixel-verified harmonic potential-field + crustal-fluid + geomorphic + fold-visible elastic wing-crack/stress-shadow PU `HistGradientBoostingClassifier`, `2.8 px` Poisson-disc thinning outside `3.0 px` visible-fault collar, `37,654` dots.
2. **`E2_ewcs_cover_blind_pu`** (ablation 1): Cover-blind subsurface-only PU model (removes `Bands 12, 19` and all fold-visible fault geometry features).
3. **`E3_ewcs_isotropic_tip_ablation`** (ablation 2): Replaces Verduzco tilt-depth, Laplace $g_{zz}$, Poisson misalignment, wing-crack lobes, stepover bridges, and broadside stress shadows with an isotropic tip-distance decay + unsigned raw gradients.
4. **Mandatory fail-closed sequence (`AGENTS.md` Rules 6, 10, 11; `PA-86-01/02`):** Run `scripts/check_h86e_registry.py --surface` (`gems86.registry-candidate.v2`) on the bounded `[0, 1]` surface **before** full-catalogue dot placement. If `rho_firings != 0` (`worst_spearman_full_footprint > 0.90`), halt before placement with no GeoTIFF written. When `rho_firings == 0`, place `37,654` Poisson-disc dots (`spacing = 2.8 px`, `collar = 3.0 px`), run `scripts/check_h86e_registry.py` on final dots plus `scripts/pa86_chance_overlap.py`, serialize an audit-only format-valid GeoTIFF via shared `vendor/gems57/submission_writer.py`, and fail closed to `verdict = "negative"` / `DO NOT SUBMIT` (`0` weekly slots used) unless `HOLDOUT-DTI` beats controls + `H86C-KSLB = 0.1241` with separated 95% CIs **and** `surface_gate_pass`, `final_dots_gate_pass`, `literal_gate_pass`, and `pa86_02.gate_pass` are all `true`.
