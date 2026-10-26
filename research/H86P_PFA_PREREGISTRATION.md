# H86P-PFA Frozen Preregistration — 2026-10-26 (session `arena/5620a35f-gemsdoe86`)

Declared **before any H86P feature, model or allocator code runs**, and before
any H86P holdout number is looked at. Machine-readable twin:
`research/H86P_PFA_PREREGISTRATION.json`. Ranked queue:
`registry/h86p_pfa_hypotheses.json` (5 hypotheses; this lane is Rank 1).

## Lane (single method paragraph — stay inside it)

Paired-flank multi-physics cross-strike asymmetry: for native Bands 6 (`tc`,
verified GeoDAWN Total Count), 17 (`cond_surf`), 15 (`depth_to_base_surf`),
13 (`iso_grav_anom`) and 2 (`rtp`), sample each sigma=1.5 px-smoothed field at
±4 px and ±7 px along 4 cross-strike axes, form the dispersion-normalised
flank contrast, weight it by a centre-intermediate **step-purity** factor
(step/contact scores high, dike/ridge scores low), and summarise per field
plus multi-physics axis concordance. These 8 PFA planes join a frozen
12-plane label-free baseline (gradient/Hessian/strain/seismicity derivatives,
no raw regional levels) and the shared EWCS fold-visible elastic fields
(visible catalogue only) in a strict footprint-median 4-fold LOQO
HistGradientBoosting PU stack, calibrated per quadrant with the shared SLCQ
logit-quantile calibrator and decoded at exactly **37,654 dots, 2.8 px
spacing, >3.0 px catalogue collar** by the shared STDP Dinkelbach-CELF
allocator. Shared `gems57` evaluator/writer bytes are used unmodified.

## Why this should catch catalogue-missing faults

The USGS/INGENIOUS catalogue is trace/scarp-based. A piedmont fault buried by
its own alluvium keeps a **signed sediment-thickness step** — Total Count
dilution, higher near-surface conductivity, deeper basement and lower
gravity on the hanging-wall side — with no scarp. Gradient magnitude (every
high-holdout lane so far) is side- and sign-blind and cannot distinguish that
step from a dike, flow margin or hogback ridge. Paired-flank sampling +
step purity encodes exactly that distinction.

**Named non-fault mimic:** alluvial fan-toe progradation fronts, Lake
Lahontan shoreline benches against conductive playas, buried
paleochannel/fanglomerate facies changes, Miocene basaltic-andesite flow
margins and other lithologic contacts.

## Frozen protocol (3 arms = the whole experiment budget)

- Instrument: `gems57-pooled-hide-v2` via `vendor/gems57/evaluate_holdout.py`
  — `holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3,
  boundary_px=12)`, pooled 200-px (20 km) physical-block paired bootstrap,
  1,000 draws, alpha 0.2 / beta 0.8 / 300 m triangular kernel. Visible
  faults masked pixel-exactly; every catalogue-derived feature from the
  visible mask only.
- Training: 4-fold LOQO on true footprint-median quadrants
  (`gems57.holdout.quadrant_ids`), training domain `quad != q` eroded 12 px.
  Positives = visible catalogue in the training domain (capped 60k, seed
  fixed). Negatives = 160k uniform training-domain cells with distance to
  visible > 8 px (PU unlabelled, not asserted fault-free). HGB:
  `max_iter=250, learning_rate=0.06, max_leaf_nodes=31,
  min_samples_leaf=40, l2_regularization=0.1, early_stopping=False`.
- Arms (identical allocator/budget/spacing/collar in all three):
  1. `E1_pfa_candidate` — baseline 12 + PFA 8 + elastic 5.
  2. `E2_pfa_blind` — baseline 12 + PFA 8, **no elastic/catalogue features**.
  3. `E3_baseline_ablation` — baseline 12 + elastic 5, **no PFA** (control).
- Comparators (context only, not arms): GEMSDOE32 H33 and GEMSDOE28 R0 dot
  fields masked to the fold-visible collar, where locally present.
- Leakage canary: every static/PFA/elastic plane alone, discriminative AUC
  `max(AUC,1-AUC)` on withheld positives vs region negatives; **>0.90 stops**.
- Registry (PA-86-01/02 obligations, thresholds unchanged): surface Spearman
  check BEFORE placement and final-dot check BEFORE serialisation via
  `scripts/check_h86e_registry.py` + `scripts/pa86_chance_overlap.py`;
  rho > 0.90 anywhere or any informative (dot-field, halo coverage ≤ 0.70)
  forward overlap > 0.70 = duplicate stop, log and do not retune.
- Comparable holdout best to beat (same evaluator, strict LOQO, 37,654 dots):
  H86I-KSAD `0.1553` HOLDOUT-DTI and H86M-SLCQ `0.1527 [0.1364, 0.1679]`
  HOLDOUT-DTI (both `gems57-pooled-hide-v2`, 11,321 withheld). H86F-EWCS
  `0.1723` is **not** comparable (in-quadrant training, logged
  `IR-86-EWCS-INQUADRANT-20261025`). Beating a number from a different design
  will not be claimed.
- Verdict rule (frozen): `promote` requires ALL of — canary pass; E1 > E3
  paired 95% CI strictly > 0; E1 point estimate above the strict-LOQO best
  above; surface rho ≤ 0.90 and zero informative dot firings on the full
  restored registry; fail-closed writer/validator pass. Otherwise
  `negative / DO NOT SUBMIT`, `safe_to_submit=false`,
  `approved_for_weekly_slot=false`, `submission_slots_used=0` regardless —
  promotion to a slot is a separate selector step (protocol rule 6), and the
  literal full-support witness reading remains reported side by side.
- Final file (if not stopped before serialisation): LOQO-OOF surface retrained
  with the full catalogue visible, 37,654 binary {0,1} dots via shared
  `submission_writer.write_submission` (`-zeros` policy: finite everywhere,
  0 outside footprint — the class that removes the portal
  "Predicted values must be in range [0, 1]" rejection), unique stem
  `gems86-h86p-pfa-37654dots-<UTC>-<sha8>-zeros`, note ≤ 140 chars.

## Amendment A1 (2026-10-26, before any real-data feature/model run)

A synthetic step-vs-ridge oracle unit test (`tests/test_h86p_pfa.py`)
falsified the naive `max` over offsets: a 3-px dike's *edges* mimic a step at
the 4-px diagonal offset (one flank lands on the crest, purity-weighted
score 2.20 vs the true step's 2.05). The operator was corrected to
cross-offset persistence `min(score_4px, score_7px)` per axis (dike edge
0.24 at 7 px), and the oracle now passes. No competition-band data had been
read by H86P code at the time of this amendment; no holdout number exists.

## Budget

≤ 3 experiments (the 3 arms above), ≤ 2 h. No hyperparameter retuning after
seeing holdout results. No weekly slot is spent or picked in this session.
