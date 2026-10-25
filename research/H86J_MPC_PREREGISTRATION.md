# H86J-MPC preregistration — monogenic phase-congruency step lineaments
**Frozen 2026-10-25 (UTC), before any H86J field is computed.**

**Lane (single method paragraph).** H86J-MPC computes, for each of three pinned
competition fields — Band 2 `rtp` (reduced-to-pole magnetics), Band 13
`iso_grav_anom` (isostatic gravity), Band 12 `det_elev` (detrended elevation) —
a **multi-scale monogenic (Riesz-transform) phase-congruency step response**:
log-Gabor radial bandpass filters (wavelengths 4/8/16/32 px for RTP and DEM,
8/16/32/64 px for gravity; `sigmaonf = 0.55`, the Kovesi ~2-octave pairing)
give, per scale, an even response `E_s` and an odd Riesz vector `O_s`; the
cross-scale vector sums `E = ΣE_s`, `O = ΣO_s` yield phase congruency
`PC = sqrt(E²+|O|²)/(Σ_s sqrt(E_s²+|O_s|²)+ε) ∈ [0,1]` and stepness
`|O|/sqrt(E²+|O|²)`, so `PC_step = PC × stepness` is high only where the local
Fourier components agree in phase across scales **and** the feature is
odd-symmetric (a step), not even-symmetric (a ridge/line). Dots are emitted
exactly as in the H86G-EDTI lane (reuse, no fork): rank allowed pixels
(footprint, >3 px from the full catalogue for the shipped raster; >3 px from
the *visible* catalogue for holdout arms) by expected kernel credit
`E[k] = surface ⊛ triangular(300 m)` (vendor `gems57.emit.expected_credit`),
spacing-greedy ≥2.8 px (`gems86_edti.model.spacing_greedy_ranking`), at the
**frozen budget 44,090 dots**. No catalogue-derived feature, no prior
submission raster, and no SGMC byte enters any surface; the catalogue is used
only as (a) holdout labels, (b) emission collar, (c) scoring mask.

## Why 0.2778, and what beating it requires (answer frozen with the lane)

Repo-pinned pixel forensics (`docs/evidence/h86f-h33-forensics.json`,
`research/H86G_EDTI_REVIEW.md`; re-measured line-by-line in this session's E1
before any H86J placement) show `h33-h33-2-b2-…-zeros` (37,654 dots) is an
exact subset of its GEMSDOE28 D2.8 parent (40,199 dots): 0 added, 2,545
removed, every removed dot at catalogue distance √2–2 px. Under the
distance-weighted Tversky index (α=0.2 FP, β=0.8 FN, 300 m triangular kernel;
vendor `gems57/metric.py`, verified against brute force in `tests/test_metric.py`)
truth credit at a pixel is the *maximum* kernel weight over covering dots, so
(i) dots closer than ~2.8 px to each other pay FP mass `0.2·(1−k)` without
adding truth credit, and (ii) dots 1–2 px from a mapped trace mostly cover
organiser-masked catalogue pixels at full FP price. The 0.2708 → 0.2778
owner-reported step is therefore **emission efficiency, not new geology**.
A non-redundant dot raises DTI iff its realised kernel credit `k > α·DTI`
(≈0.056 at 0.2778). Beating 0.2778 requires what reallocation of H33's own
dots cannot supply (|Δ|≤0.0073 measured, `SLOT_PLAN.md`): **dots on real
hidden trace that the H19-5 multiline ancestor surface misses**, emitted at
H33-grade efficiency. H86G-EDTI (this repo, 2026-10-25) already attacks this
with an amplitude-detector multiline surface (SGMC-PROXY-DTI 0.1223 @55,000 vs
H33-as-is 0.0954; HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld)
0.0631 [0.0468, 0.0806]). H86J-MPC is a *different physical measurement* of the
same fields, designed to find trace that amplitude ranking suppresses:

* **Contrast invariance.** Phase congruency is dimensionless in [0,1] and
  independent of signal magnitude (Kovesi). A buried fault offsetting a weak
  magnetic marker (deep source, low susceptibility contrast — precisely why
  it is missing from the USGS/INGENIOUS catalogue) retains cross-scale phase
  alignment while its gradient *amplitude* ranks below shallow volcanic
  noise. Every detector in EDTI's L surface and in the H19-5 lineage is an
  amplitude/derivative magnitude; none normalises by local amplitude.
* **Step-vs-line discrimination.** A fault *offset* is a step (odd symmetry);
  a dike, flow ridge or shoreline crest is a line (even symmetry). Amplitude
  detectors fire on both; `PC_step` fires preferentially on steps via the
  local phase angle (Kovesi feature type: step vs bright/dark line). The
  sign convention is not assumed: unit tests on synthetic step/ridge images
  must pass before any real field is trusted.

**Non-fault mimic (named):** unfaulted lithologic contacts and lava-flow
fronts are also true steps in RTP/gravity/DEM; GeoDAWN flight-line seams and
interpolation ringing are phase-congruent steps with no geology at all.

## Ranked candidate hypotheses (5; only rank 1 runs this session)

| Rank | ID | Layers | Physical signature | Why catalogue-missing | Difference from this repo | Mimic | Cost |
|---:|---|---|---|---|---|---|---|
| 1 (RUN) | H86J-MPC | B2 rtp, B13 iso_grav, B12 det_elev | Monogenic log-Gabor phase congruency × stepness (above) | Weak/deep marker offsets keep phase alignment when amplitude ranking buries them; step-type separates offsets from dikes | No `phase congruency/monogenic/Riesz/log-Gabor` implementation exists in `src/`, `scripts/` or `vendor/` (grep-verified this session); carried only as unrun proposal H86G-MPC in `registry/h86g_hypotheses.json` | Lithologic step contacts, flow fronts, survey seams | Medium (3 FFT filter banks) |
| 2 | H86J-CSPA | B2, B13 | Windowed cross-spectral gravity–magnetic coherence/admittance breaks | Buried juxtaposition changes joint density/magnetisation relation without a scarp | Unrun H86G-CSPA proposal; PCC/GZZD/PSTD are pointwise, not windowed cross-spectra | Unfaulted juxtaposition, source-depth change, remanence | Medium, but ~6 km windows localise trace poorly vs the 300 m kernel — hence rank 2 |
| 3 | H86J-CHI | DEM-χ external, B12/B19 | Cross-drainage alignment of χ/ksn knickpoints | Blind footwall uplift reorganises drainage on pediments with no scarp | Deferred H86G-CHI; KSLB used ksn as a Noisy-OR input, never an alignment statistic | Resistant-bed knickpoints, lake base-level fall | Medium-high |
| 4 | H86J-PSC | B2, B13, B15 | Persistence-ranked Morse saddle-connection graph | Buried connectors between anomaly bodies missed by peak ridges | Unrun H86G-PSC; CTHB ridges are local Hessian, not topology | Intrusive contacts, superposed unfaulted sources | Medium-high |
| 5 | H86J-CNT | B17, B7, B8 | Persistent conductivity-neck topology × dilatation | Narrow buried fluid pathway joining conductive regions | Unrun H86G-CNT; CTHB/FVMB use clay-cap margins/halos, not neck topology | Saline playa sediments, clay paleochannels | Medium; weakest specificity |

Ranking rule: expected HOLDOUT/SGMC-proxy information gain per implementation
hour, penalising poor trace localisation under the 300 m kernel. No new
external data: every input is already SHA-pinned in `registry/data_manifest.json`
/ `scripts/restore_data.py` and hash-verified at restore in this session
(training_features `4371c82e…`, SGMC `643cbe99…` — SGMC is a selection
instrument only, never a feature).

## Experiments (≤3, ≤2 h compute; evaluator `gems57-pooled-hide-v2`)

Holdout: `holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)`
via the EDTI runner's fold construction (reused): whole components withheld,
visible faults masked pixel-exactly, pooled DTI α=0.2 β=0.8 300 m triangular,
200-px spatial-block paired bootstrap (1,000 draws, seed 861025). The EDTI
Amendment-A1/A2 instrument findings are adopted *as measured repo evidence*:
the primary selector is SGMC-PROXY-DTI of the as-emitted raster (truth =
pinned USGS SGMC faults >3 px off catalogue; selection only, never a score),
catalogue-hide HOLDOUT-DTI is the OOF visible-construction floor. Unlike EDTI,
**the budget (44,090) and collar (3 px) are frozen here in advance**; budget
curves {37,654, 44,090, 55,000} are reported as points only and cannot move
the gate (no A4-style post-hoc budget rule).

- **E1 — canaries + controls + H33 re-forensics.** Each MPC feature alone
  (`pc_step`, `pc`, `stepness`, `pc_line`, log amplitude per field): AUC vs
  withheld positives in fold regions (stop if discriminative AUC > 0.90).
  Controls scored as-is: H33, D2.8 parent, H86G-EDTI final (55,000) on
  SGMC-proxy; H33-vs-parent subset anatomy re-measured from pinned bytes.
- **E2 — three arms, identical emission @44,090:**
  A `MPC-MAG` = rank01(PC_step,RTP);
  B `MPC-DUAL` = mean(rank mag, rank grav) × (0.5+0.5·1[both ranks>0.5]-agreement as in EDTI L form: mean rank × (0.5 + 0.5·fraction of the two ranks >0.5));
  C `MPC-TRI` = same corroboration over {mag, grav, dem}.
  Arm selected by SGMC-PROXY-DTI point at 44,090 (ties → fewer fields).
- **E3 — falsifier ablations @44,090, same emission:** (a) amplitude control:
  EDTI-stack gradmag corroboration over the same three fields
  (`gradmag_rtp_s1p5`, `gradmag_grav_s1p5`, `gradmag_dem_s1p5`) — MPC must
  beat it on SGMC-proxy point for the phase claim to survive; (b) line-type
  control: `PC_line` corroboration replacing `PC_step` — step must beat line.

## Gates (all must pass for `promote`; any failure ⇒ `negative`, DO NOT SUBMIT)

1. Canary: no MPC feature discriminative AUC > 0.90.
2. SGMC-proxy: candidate @44,090 > H33-as-is with paired 95% CI strictly
   above 0. Paired comparison vs H86G-EDTI-as-is (55,000 dots; budget caveat
   printed) is reported but is not a gate — EDTI remains separately
   selector-ready; this lane must independently beat the 0.2778 mechanism.
3. OOF catalogue-hide floor: candidate HOLDOUT-DTI point ≥ H33
   visible-collar control point at the same budget (EDTI A2 construction).
4. Falsifiers: candidate SGMC-proxy point > E3 amplitude control and >
   E3 line-type control at 44,090.
5. Uniqueness (PA-86-01 like-for-like, thresholds unchanged): surface
   Spearman ρ ≤ 0.90 vs every pinned local registry raster
   (`data/scored_fleet/`, `docs/downloads/`, `submission/`) before placement,
   and final-dot ρ ≤ 0.90 plus forward 3-px overlap ≤ 0.70 vs every local
   dot-field (vendor `representation_class`). The literal full-support
   reading (continuous 17GEMSDOE witness blocks every nonempty candidate)
   is reported side-by-side, never hidden. `scripts/check_h86e_registry.py`
   (surface + final dots) and `scripts/pa86_chance_overlap.py` are run if the
   full inventory restores; their verbatim outcomes are recorded either way.
6. Format: vendor fail-closed writer + independent disk validator —
   single-band float32, EPSG:32611, 3730×3292, sample transform, no NaN/Inf,
   values exactly {0,1} ⊂ [0,1] (the owner's portal error class), zeros
   outside footprint, 0 dots on catalogue, one-TIFF ZIP byte-identical.
7. No slot is picked. `promote` = eligible for the separate selector step
   within the weekly cap; `safe_to_submit`/`approved_for_weekly_slot` stay
   false until an organizer receipt exists. Every number is labelled
   HOLDOUT-DTI / SGMC-PROXY-DTI / OWNER-REPORTED; none is ORGANIZER-CONFIRMED.

## Official / literature sources (manual review)

- Competition + metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (browser only per AGENTS rule 9; not scraped)
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN: https://doi.org/10.5066/P93LGLVQ · INGENIOUS GDR 1391: https://gdr.openei.org/submissions/1391
- Kovesi, phase congruency (contrast invariance; log-Gabor; monogenic `phasecongmono`, feature type step vs line; defaults nscale 4, minwavelength 3, mult 2.1, sigmaonf 0.55): https://peterkovesi.github.io/ImagePhaseCongruency.jl/dev/ and https://www.peterkovesi.com/papers/Kovesi_Videre_v1n3001.pdf
- Phase congruency for potential-field lineaments (CET grid analysis; improved Euler + phase congruency for lineaments): https://doi.org/10.1093/jge/gxaa072
- EPSG:32611 https://epsg.io/32611 · Tversky index https://en.wikipedia.org/wiki/Tversky_index
