# H86J-MPC review — why 0.2778, whether phase congruency beats it (no), and what to test next

**Date:** 2026-10-25 (UTC) · **Lane:** H86J-MPC · **Verdict: `negative` — DO NOT SUBMIT**
**Candidate (audit only):** `docs/downloads/gems86-h86j-mpctri-mpcstep-44090dots-20261025T041719Z-014b24c0-zeros.tif`
SHA-256 `e3035cd59620b8ee442c8ec8c0232f474d15d245411000bd8cd057739b559c3d` · 44,090 dots
**Run card:** [`docs/evidence/h86j-mpc-run-card.json`](../docs/evidence/h86j-mpc-run-card.json) ·
**Preregistration (frozen before implementation):** [`H86J_MPC_PREREGISTRATION.md`](H86J_MPC_PREREGISTRATION.md)

Every number is labelled `HOLDOUT-DTI`, `SGMC-PROXY-DTI`, or `OWNER-REPORTED`.
No DrivenData login, upload, selector decision, or weekly slot was used
(`submission_slots_used = 0`); there is no `ORGANIZER-CONFIRMED` number here.
Validation was fully automated (vendor fail-closed writer + independent
on-disk validator + release audit 21/21) — no human inspection gate.

## Bottom line

* A **unique** new TIFF **was** generated and machine-validated: surface
  Spearman max 0.053 and final-dot forward 3-px overlap max 53.8% vs the 46
  local registry rasters (only 18.7% of its dots within 3 px of H86G-EDTI) —
  it is a genuinely different predicted trace, not a copy or rebrand.
* It is **not OK to submit**: the preregistered hypothesis was falsified by
  its own frozen controls. Pure phase-congruency step ranking scores
  SGMC-PROXY-DTI 0.0658 @44,090 vs H33-as-is 0.0954 (paired Δ −0.0296,
  95% CI [−0.0427, −0.0156]) and vs its own amplitude control 0.1089.
  Spending a weekly slot on it would predictably waste the slot.
* The file that **is** OK to submit remains **H86G-EDTI** (previous session,
  green panel on the site). This session's deliverable is the negative
  result + the diagnosis + a sharper follow-up queue (below).

## Q1 — Why and how did `h33-h33-2-b2-…-zeros` reach 0.2778 (OWNER-REPORTED)?

Re-measured line-by-line in this session's E1 from the pinned bytes in this
checkout (`data/scored_fleet/…e5eb6e7e-zeros.tif`, sha256 `c55bafc4…`, and its
GEMSDOE28 parent `ab023001…`; full block in the run card's `h33_forensics`):

* H33 (37,654 dots) is an **exact subset** of the D2.8 parent (40,199 dots):
  **0 added, 2,545 removed**, and the removed dots sit at catalogue distance
  exactly {√2, 2.0} px. Minimum nearest-neighbour spacing 2.828 px; 0 dots on
  the catalogue; 0 outside the footprint. Nothing else differs.
* The parent is a ≥2.828 px-thinned dotted emission of the H19-5
  "multiline-corroborated" lineament surface.

Mechanism under the competition metric (distance-weighted Tversky,
α = 0.2 FP, β = 0.8 FN, 300 m triangular kernel; vendor `gems57/metric.py`,
unit-verified against brute force): truth credit at a pixel is the **maximum**
kernel weight over covering dots, while every dot pays FP weight
`0.2·(1 − k_self)`. Therefore (1) a second dot inside one kernel diameter
adds cost without adding credit (spacing ≥ ~2.8 px removes that waste), and
(2) dots 1–2 px from a mapped trace mostly cover organiser-masked catalogue
pixels — near-zero marginal credit at full price (the collar deletion is the
entire 0.2708 → 0.2778 difference). The exact marginal bar for a
non-redundant dot is `k > α·DTI` (≈ 0.056 at DTI 0.2778).

**PhD judgement:** 0.2778 is an *emission-efficiency* optimum on one ancestor
surface, not evidence of a better geological model. The fleet table in the
owner prompt supports this: every entry ≥ 0.2600 belongs to the H19-5/D2.8
lineage (0.2600–0.2778), while methodologically independent surfaces
(supervised HGB 0.0286/0.0424, Euler/worm/gravity novelties 0.03–0.16) sit
far below. Two readings remain open and are *not* resolved by owner reports
without receipts: (a) the hidden truth genuinely lies mostly on the same
multiline habitat the H19-5 surface traces, so lineage refinements win; or
(b) the truth was mapped with the same data/habits, so the lineage partially
matches the *mapping* process. Either way, beating 0.2778 needs **new trace
on real hidden faults at H33-grade emission efficiency** — budget arithmetic
(`SLOT_PLAN.md`): +0.01 DTI at 0.2778 ≈ 418 kernel-credit units ≈ 42 km of
trace hit squarely; reallocations of H33's own dots measure |Δ| ≤ 0.0073.

## Q2 — Can we generate a submission that scores higher than 0.2778?

Possibly — H86G-EDTI (historical amended-gate promote; not currently authorized on main) is the repo's designed attempt
(independent multiline surface, SGMC-PROXY-DTI 0.1223 vs H33 0.0954, only 26%
dot overlap with H33), but **no number in this repo is a live score** and the
0.3195/0.4413 "leaderboard high" claims in the prompt are OWNER-REPORTED and
mutually inconsistent. What this session adds is a *tested elimination*:
one more physically distinct way of reading the same fields — contrast-
invariant phase — does **not** supply the missing trace in pure form.

## What was built (3 experiments, frozen in advance)

Inputs: SHA-pinned restored bytes only (training_features `4371c82e…`;
SGMC proxy `643cbe99…`, selection-only). Emission/evaluation/writing are the
shared vendor + EDTI tools, unmodified (template pins re-verified by the
release audit). The template's *cached feature stack* remains absent; the
pinned 19-band TIFF was used directly and never relabelled as that cache.

* **E1 — canaries + controls + H33 re-forensics.** 18 single features,
  max discriminative AUC 0.5749 (< 0.90 stop; gradmag_dem strongest, MPC
  features 0.49–0.52). Controls reproduce EDTI's instrument table **exactly**
  (H33 SGMC-proxy 0.0954 / cat-hide 0.0037; EDTI 0.1223 / 0.0000), verifying
  the measurement chain end-to-end in this session.
* **E2 — three MPC arms, identical frozen emission (44,090 dots).**
  Surface registry check ran *before* placement (max ρ ≤ 0.053, all arms
  eligible). SGMC-PROXY-DTI @44,090: MPC-TRI 0.0658 > MPC-MAG 0.0655 >
  MPC-DUAL 0.0603 — all far below H33-as-is 0.0954.
* **E3 — falsifiers @44,090.** Amplitude control (same 3 fields, Gaussian
  gradmag corroboration — a 3-of-8-detector subset of EDTI-L): **0.1089**.
  Line-type control (PC_line): 0.0640. So amplitude ≫ phase, and step ≈ line:
  both halves of the frozen hypothesis fail (contrast invariance does not
  rescue weak markers here; odd/even symmetry does not separate fault steps
  from ridges at these wavelengths in these smooth fields).

Final gates (run card): canary PASS; SGMC-vs-H33 **FAIL** (Δ CI entirely
negative); OOF catalogue-hide floor PASS (HOLDOUT-DTI
(`gems57-pooled-hide-v2`, 11,321 withheld) 0.0453 [0.0379, 0.0528] vs floor
0.0349 — a sanity floor only); falsifiers **FAIL**; local uniqueness PASS;
format PASS (independent disk validation: binary {0,1}, EPSG:32611,
3730×3292, min spacing 2.828 px, min catalogue distance 3.16 px, ZIP
byte-identical; SGMC value reproduced by direct `dti_binary`).

## Why pure phase congruency underperforms here (diagnosis, measured)

1. **PC saturation in harmonic fields.** Mean PC is 0.79–0.90 across the
   footprint. Potential fields are solutions of Laplace's equation —
   upward-continued by physics — so local phase is intrinsically coherent
   across the wide (~2-octave, `sigmaonf 0.55`) log-Gabor scales almost
   everywhere. The ranking therefore spends dots where amplitude is negligible
   but phase is tidy (smooth basin interiors, gridding fabric), not on source
   edges. Contrast invariance, PC's virtue in optical images, is a liability
   when amplitude itself carries the source-depth/contrast information.
2. **No noise compensation.** Kovesi's production form subtracts a noise
   threshold `T` from local energy and weights by frequency spread; the
   frozen simplified form omits both, so flat-area congruency is not
   suppressed. (Preregistered simplification — now measured, hence fixable
   in a *new* preregistration, not by post-hoc tuning here.)
3. **Step/line degeneracy at source depth.** A basement offset at 0.5–2 km
   depth produces a magnetic/gravity transition spread over ~5–20 px, not a
   pixel step; odd/even decomposition at 4–64 px wavelengths then separates
   poorly (STEP 0.0658 vs LINE 0.0640). The DEM step signal is real but
   weakest exactly where faults are buried (no scarp), which is the target
   population.
4. MPC is **not noise**: 0.0658 ≫ the catalogue-hugging poisson raster's
   SGMC 0.0405 and ≈ 2/3 of H33. It carries independent signal (rank corr
   with gradmag only 0.17–0.38; 81% of dots >3 px from EDTI dots) — as a
   *precision filter on* an amplitude ranking it remains plausible, which is
   follow-up #1 below, not a rescue of this lane.

## Ranked follow-ups (next sessions; each needs its own preregistration)

| Rank | Idea | Why it could beat 0.2778 where MPC failed | Cost |
|---:|---|---|---|
| 1 | **H86K-AMPC hybrid**: EDTI-L-class amplitude multiline ranking reweighted by `PC_step` rank (phase as precision gate, amplitude as recall), frozen budget sweep | Uses MPC's independent signal (81% disjoint dots at 2/3 strength) to *remove* amplitude false positives (dikes, flow fronts — line-type, high amplitude, low stepness) instead of replacing the ranking | Low (surfaces cached) |
| 2 | **Phase symmetry (CET-style)** instead of congruency | The potential-field CET literature reports symmetry outperforming congruency for fault/lineament detection and being less noise-prone; a *ridge-of-step* (symmetric) response matches the smoothed-step physics in §3 better than odd-symmetry stepness | Medium (same FFT bank, different functional) |
| 3 | **Noise-compensated PC** (Kovesi `T` + spread weighting, `sigmaonf 0.75`, mult 1.6) | Directly fixes measured failure mode #1/#2; falsifiable against this lane's saved terms | Low-medium |
| 4 | H86J-CSPA windowed cross-spectral admittance (prereg rank 2, still unrun) | Joint density/magnetisation *relationship* breaks are amplitude-independent in a different way; localisation risk remains | Medium |
| 5 | Selector decision on H86G-EDTI itself | The only gate-passing candidate; one organizer receipt would calibrate every proxy in this repo (SGMC vs cat-hide vs live) and is worth more information than another unsubmitted lane | Owner action only |

Budget/protocol notes: exactly 3 experiments ran; no post-hoc arm, budget,
or threshold was introduced after seeing E2/E3 (the frozen 44,090 gate is
what makes this negative clean — contrast EDTI's disclosed A4). The upstream
registry v2 scan measured 330/694 rasters this session (362 blobs not
restored; 2 known off-grid rows), PA-86-02 failed closed verbatim, and the
literal continuous-witness reading remains blocked for every nonempty
candidate — all reported, none hidden. Irregularity flagged for the owner:
none new in shared tools (template pins verify); the standing limitation
that *no* score in the fleet table (incl. 0.2778/0.3195/0.4413) has an
organizer receipt in this repo remains the largest epistemic risk.
