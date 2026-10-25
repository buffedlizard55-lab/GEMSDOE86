# H86F-GZZD preregistration (frozen 2026-10-25T00:10:47Z, before lane computation)

Machine-readable freeze: `research/H86F_GZZD_PREREGISTRATION.json` (the runner refuses to start
without it and checks the 3-arm / 2-hour / DTI-weight fields, as in the H86E-MMT runner).
Base commit `7d7da3f88b98fd75a51534456c9a034608d4029f`. This file is the human-readable companion;
if they differ, the JSON governs and the difference is an irregularity.

**Lane-resolution irregularity (standing):** the supplied prompt contains no separate single
method paragraph assigning this session a lane. Exactly one lane (H86F-GZZD) is selected and frozen
here before any H86F surface/canary/holdout/placement computation. Read-only forensics on pinned
prior artifacts (`scripts/h86f_forensics.py` → `docs/evidence/h86f-h33-forensics.json`) preceded the
freeze; forensics fit nothing and placed no dots.

## Ranked hypotheses (summary; full fields in the JSON)

| Rank | ID | Layers | Signature | Why uncatalogued | Novelty vs this repo | Cost | Data status |
|---:|---|---|---|---|---|---|---|
| 1 | **H86F-GZZD** (run) | B18, B11, B13, B15 (+B5 control) | σ=500 m Laplace `gzz = -(∂x B18 + ∂row B11)` antisymmetric dipole pairing, 8 azimuths, ±200–400 m flanks, 900 m strike smoothing; B15/B13 polarity soft gate | Buried basement step under cover: dipole without a scarp | First executed divergence of the signed gravity vector; prior lanes used B11/B18 under wrong header physics, unsigned edges, or raw steps (SPBT-v1 negative) | Low–med | Competition-native only — **viable now** |
| 2 | H86F-WARP | B12, B19 | Broad-warp (σ=300/600 m) profile-curvature sign flip, ≥900 m persistence | Degraded pre-Quaternary warp after scarp loss | DEM lanes used slope/relief/lidar sharp scarps, not signed broad-warp flips | Low | Native — viable, not run |
| 3 | H86F-HMDC-LITE | B2, B17, B6 + GDR 1391 points | RTP magnetite-destruction trough + conductance + pairwise ≤6 km vent/sinter collinearity | Hydrothermal upflow signature without a scarp | Proposed before (H86E-HMDC), never run; CTHB used radial halos only | Med–high | Official source named (GDR 1391, CC BY 4.0) but sinter/probe archives **not re-obtained+hash-verified in this sandbox → not viable to run here** |
| 4 | H86F-SLB | B4, B7, B8 | Strain-rate tensor-gradient localization ridge | Locked-fault strain concentration | Strain bands used only as scalars/rank averages before | Low | Native — viable, lowest priority (multi-km smoothness vs 300 m kernel) |

Ranking basis is qualitative expected information per implementation cost. **No numerical DTI gain
is projected for any hypothesis.**

## Arms (exactly 3, fixed budget 44,090 dots, shared decimated emission)

- **E1 `E1_gzzd_concordant`** — candidate: dipole pairing × soft polarity gate (1.0 / 0.25).
- **E2 `E2_gzzd_dipole`** — ablation: identical dipole, gate fixed at 1.0.
- **E3 `E3_gravmag_edge_control`** — negative control: σ=2 px Band 5 unsigned edge magnitude.

Controls scored on the identical instrument: `R0_D28_visible_collar` (fold-fair, rebuilt per fold)
and the historical same-split comparator `E3_kslb_noisyor_44k`
(`docs/evidence/lane86c_results.json`, HOLDOUT-DTI, not re-run).

## Frozen gates

- Holdout: `gems57-pooled-hide-v2`, buffered whole components, seed 20, hide 0.20, buffer 3 px,
  α=0.2, β=0.8, 300 m triangular kernel, pooled 200-px physical-block bootstrap (shared code,
  unmodified). Catalogue-derived quantities (only the allowed-mask collar) use visible faults only
  per fold; the GZZD surfaces themselves read no catalogue pixels.
- Leakage canary: every returned field alone; discriminative AUC > 0.90 stops the lane.
- Registry (PA-86-01/02, thresholds unchanged ρ≤0.90, forward 3-px overlap ≤0.70): surface checked
  **before** placement. A surface ρ firing stops before placement (no TIFF). If there is no ρ
  firing but completeness fails (e.g. grid-incompatible registry rows), an audit-only TIFF may be
  written **only** with verdict forced negative — completeness failure is never a pass
  (AGENTS.md rule 11). PA-86-02 informative firings are hard stops; if `pa86_chance_overlap.py`
  itself fails closed on binding/completeness, that exception is recorded verbatim as a failed gate,
  never bypassed with a private computation.
- Format: shared fail-closed writer + independent on-disk re-validation (single-band float32,
  EPSG:32611, 3730×3292, transform match, all values finite in [0,1], zeros outside footprint,
  zero positives on the mapped catalogue, one-TIFF ZIP, SHA-256 receipt). This is the direct fix
  for the portal error *"Predicted values must be in range [0, 1]"*: the writer rejects — never
  clips — non-finite or out-of-range input, so a file that exists has already passed the range test
  on its on-disk bytes. Local validity is not organizer acceptance.
- Promotion: `promote` means only "eligible for the separate human selector". It requires beating
  the same-split best with separated CIs **and** a strictly positive paired Δ vs the best
  preregistered control **and** all registry/format gates. This lane uses **0 weekly slots** in
  every outcome.

## Named non-fault mimic (E1)

Unfaulted pre-Tertiary paleovalley margins or buried caldera moat walls infilled by low-density
sediments; gravity-basement inversion artifacts. Bands 13/15 share inversion ancestry (pre-freeze
audit: interior r = −0.6396), hence polarity is a sign gate only.

## Sign convention (verified, do not "fix" from the headers)

Pixel verification (`docs/evidence/band-physics-verification-20261024.json`, re-spot-checked in the
pre-freeze audit) gives the signed horizontal gravity vector as (∂g/∂x_east, ∂g/∂y_north) =
(+Band 18, −Band 11), with Band 11 = ∂g/∂row_south. In image coordinates (row increases southward)
the horizontal divergence is ∂x(Band 18) + ∂row(Band 11), so
`gzz = −(∂x B18 + ∂row B11)`. The audit measured corr(gzz, −Laplacian B13) = +0.8952 at σ=5 px for
this sign and +0.1501 for the minus-row alternative; the runner recomputes and records this QC
correlation and fails closed below +0.80.
