# H86 — ranked candidate hypotheses (preregistered before any H86 experiment)

Written 2026-10-22 **before** computing any H86 surface, canary or holdout number.
Band numbers/names below were read from the restored `data/training_features.tif`
band descriptions in this checkout (19 float32 bands, EPSG:32611, 3730×3292,
nodata −3.4028235e38; sha256 `4371c82e…23bc5`, owner mirror, **not**
organizer-authenticated). "Untried" means: not implemented in this repository
and not the method of the inspected shared template (`vendor/gems57`, pin
`60GEMSDOE@b99591ee`) or of the pinned GEMSDOE32 H33 surfaces
(`research/upstream/h33.py`, `h33_holdout.json`). Uniqueness across all ~88
sibling sites cannot be exhaustively proven from here; the accessible pinned
registry (14 hash-verified rasters, `data/registry/index.json`) is the measured
uniqueness scope.

## Why the cited best file scored well — analysis first (mechanism, not folklore)

`h33-h33-2-b2-…-e5eb6e7e-zeros` (37,654 dots; pinned audit in
`research/upstream/h33-best-audit.json`, file sha256 `c55bafc4…ab6fa9`,
re-fetched and hash-verified in this session) is **not a new geological
surface**: it is the 0.2708-family dotted base with every dot within 2 px
(200 m) of the mapped catalogue deleted. Under the official metric
(alpha 0.2, beta 0.8, 300 m triangular kernel — `vendor/gems57/metric.py`)
three effects explain the family ordering
(continuous 121k px → dotted d1.5 60k → d2.8 44k → flank-pruned 37.7k):

1. **Emission geometry dominates.** One binary dot earns kernel-weighted
   credit for every truth cell within 3 px; TP saturates at 1 per truth cell,
   so contiguous lines pay FP mass for coverage a single dot already bought.
   Spaced dots convert the same budget into area coverage. (Measured in the
   pinned H33 holdout: top-N clustered emission of four physics surfaces
   scored *below a uniform-random spread control*, 0.0187–0.0241 vs 0.0344 —
   clustering, not only surface quality, destroys DTI.)
2. **Catalogue-flank dots are structurally likely FPs.** The scored truth is
   *new* faults; mapped faults are masked pixel-exactly. A dot 100–200 m from
   a mapped trace mostly covers (within its 300 m kernel) the already-known
   fault, which cannot earn TP, so its expected marginal credit is low while
   its FP cost (alpha·(1−k)) is near-full. Deleting the ≤2 px flank removes
   low-yield mass; the recall lost is limited to genuine splays within 200 m.
   A non-redundant dot raises DTI iff realised credit k > alpha·DTI
   (≈0.056 at DTI 0.28) — flank dots systematically fail this bar.
3. **Budget sits near the marginal-credit cliff.** 37–44k dots ≈ 0.73–0.85%
   of the 5,167,373-cell footprint; beyond it, surface rank (hence hit
   probability) decays below the alpha·DTI bar.

Irregularity flagged: the pinned audit labels this file **UNSCORED** with a
*projected* 0.2747; the 0.2778 figure is owner-reported, with no
submission-page receipt in this repo, so per protocol it is **not**
ORGANIZER-CONFIRMED here. Any "beat 0.2778" claim can only be made after a
real receipt exists; locally we can only beat comparable HOLDOUT-DTI controls.

## The five candidates

### H86-1 (RANK 1 — this session's single lane) Straight-edge 2-of-5 corroboration, dotted

- **Layers:** `rtp` (2), `iso_grav_anom` (13), `cond_surf` (17),
  `depth_to_base_surf` (15), `det_elev` (12) — one band per independent physics
  (magnetics once, not three times).
- **Signature:** per field, Gaussian-derivative gradient magnitude gated by
  structure-tensor coherence (a *straight step/contact*, not a blob and not a
  ridge crest); rank-normalise inside the footprint; surface = **second-highest**
  of the five ranks (any 2 of 5 physics must independently show a straight
  edge; no cross-physics orientation agreement required, no DEM required).
- **Why it should catch catalogue-missing faults:** faults in potential fields
  appear as offsets/contacts (steps), and under sedimentary cover the surface
  catalogue is empty while gravity/magnetics/MT/basement-depth steps persist.
  Requiring only 2-of-5 lets buried traces (e.g. cond+depth, mag+grav) score
  with zero topographic expression, while exposed faults can use det_elev+1.
- **Non-fault mimic:** lithologic contacts and basin-margin sedimentary edges
  (straight steps in the same fields); survey seams (axis-aligned coherence).
- **Difference from inspected methods:** H33-A required Hessian *line*
  responses in all physics to *agree on strike* (orientation order parameter)
  including DEM/LiDAR, and emitted top-N clusters; H33-D used only the
  cond+depth pair; the h19 family used ridge *crests* with power-law budgets.
  H86-1 is edge/step (not crest), order-statistic 2-of-5 (not product/union/
  order-parameter), with spaced-dot emission and a baked-in ≤2 px
  catalogue-flank exclusion applied from *visible-only* faults per fold.
- **Data/cost:** training_features only; ~minutes CPU. Validatable locally: yes.

### H86-2 (RANK 2) Radiometric mixing-residual boundary

- **Layers:** external GeoDAWN K/Th/U (`data/external/geodawn_rad_u8.tif` in
  the pinned manifest, 26.6 MB, fetchable here) + `rtp` (2).
- **Signature:** spatially cross-fitted robust K~Th+U regression; transverse
  gradient of the residual, gated by magnetic edge persistence.
- **Why off-catalogue:** hydrothermal K redistribution can cross a broad
  lithologic mixing trend with no surface trace.
- **Mimic:** weathering fronts, compositional contacts.
- **Difference:** residuals after unmixing, not raw radiometric consensus.
- **Cost/risk:** moderate; u8 quantisation and band-identity of the external
  product must be verified before use. Not this lane.

### H86-3 (RANK 3) Catalogue-distance-debiased PU classifier

- **Layers:** all 19 bands + derived ridge/edge channels.
- **Signature:** gradient-boosted PU model trained on visible faults with the
  score explicitly orthogonalised against distance-to-visible-catalogue and
  local catalogue density inside each fold.
- **Why off-catalogue:** removes the "emit near known faults" shortcut that
  plain supervised lanes learn (their owner-reported scores are low);
  forces reliance on field evidence far from mapped traces.
- **Mimic:** any field pattern anti-correlated with mapping density itself.
- **Difference:** prior supervised lanes did not debias; risk: orthogonalisation
  may remove genuine fault-clustering signal. Higher cost (per-fold training).

### H86-4 (RANK 4) Displaced-contact offset detection

- **Layers:** `rtp` (2), `iso_grav_anom` (13).
- **Signature:** detect paired, laterally offset terminations of magnetic
  contact ridges; require a transverse gravity-gradient change at the offset.
- **Why off-catalogue:** a concealed cross-fault offsets an older contact; the
  contact is not itself the fault, so contact-following methods miss it.
- **Mimic:** intrusive geometry, survey block seams.
- **Difference:** targets discontinuities *of* lineaments, not lineaments.
  Highest implementation cost of the local options.

### H86-5 (RANK 5, DATA-BLOCKED here) Focal-mechanism nodal-plane lineaments

- **Layers:** would augment `ieq_n100a15` (16) / `deq_n100a15` (10), whose
  100 km support carries no 300 m-scale information (measured upstream).
- **Source (named, free, official):** USGS FDSN event service
  `https://earthquake.usgs.gov/fdsnws/event/1/query` (ComCat moment tensors).
  **Not verified obtainable from this sandbox** (egress allow-list); therefore
  ranked but explicitly **not proposed as viable in this session**.

## Single-lane method paragraph (the lane for this session)

> **H86-1:** From the five one-per-physics bands above, compute per-field
> straight-edge scores (Gaussian-derivative gradient magnitude ×
> structure-tensor coherence at 1–2 px), rank-normalise each within the scored
> footprint, and take the pixelwise second-highest rank as the surface. Emit
> binary dots (value 1.0) by greedy descending-surface placement with minimum
> separation 2.8 px, total budget fixed before scoring (E2: 38,000; optional
> E3 sensitivity: 44,090), forbidding any dot within ≤2 px of the *visible*
> catalogue (per-fold visible set in holdout; full catalogue only for the
> final candidate). No catalogue-derived quantity other than that exclusion
> enters the surface. Serialize all-finite zeros-mode through the unmodified
> shared writer; validate through the unmodified shared validator.

Experiments (protocol budget: ≤3): **E1** per-feature leakage canaries
(AUC > 0.90 blocks) + pre-placement surface uniqueness; **E2** pipeline
hide-and-recover at budget 38,000 vs spaced-random and fixed-incumbent
controls on identical folds; **E3** (only if E2 completes) budget sensitivity
44,090. Promotion requires beating the best comparable control on pooled
HOLDOUT-DTI with a paired spatial-block 95% CI excluding 0, plus literal
uniqueness gates vs the accessible registry. Anything less is a negative
deliverable and must not consume a weekly slot.
