# H86-1 results — why 0.2778 happened, whether it can be beaten, and what this lane measured

Session 2026-10-22, branch `arena/4a010211-gemsdoe86`. Every number below is
labelled: **HOLDOUT-DTI** (evaluator `gems57-pooled-hide-v2`), **AUXILIARY-PROXY**
(SGMC off-catalogue proxy, never a score), **REGISTRY-MEASUREMENT**, or
**OWNER-REPORT** (unverified, no organizer receipt in this repo). No number
here is ORGANIZER-CONFIRMED; no weekly slot was used.

## 1. Why `h33-h33-2-b2-…-e5eb6e7e-zeros` got the family's best result

Verified facts about the file: re-fetched this session from
`buffedlizard55-lab/GEMSDOE32@780a5a53`, sha256 `c55bafc4…ab6fa9` matches the
pinned audit (`research/upstream/h33-best-audit.json`); 37,654 binary dots,
0 on-catalogue, all-finite zeros-mode, values in [0,1] (so it cannot trigger
the owner's earlier "Predicted values must be in range [0, 1]" portal error —
that error is consistent with NaN/sentinel/unnormalised values, none present
here). It is the 0.2708-family dotted base **minus every dot ≤2 px (200 m)
from the mapped catalogue** ("B=2 flank prune"). Its pinned audit says
**UNSCORED, projected 0.2747**; the 0.2778 in the brief is therefore
OWNER-REPORT, not an organizer receipt. Irregularity preserved, not papered over.

Mechanism (metric: `vendor/gems57/metric.py`, alpha 0.2, beta 0.8, 300 m
triangular kernel; a non-redundant dot raises DTI iff realised kernel credit
k > alpha·DTI ≈ 0.056 at DTI 0.28):

1. **Dotted emission converts budget into coverage.** TP saturates at 1 per
   truth cell, so contiguous lines pay FP for coverage one dot already
   bought. The family is monotone under thinning (continuous → d1.5 → d2.8 →
   B2-pruned), and this session re-measured the converse: clustered/top-heavy
   placement wastes budget regardless of surface quality.
2. **Flank dots are structurally starved of TP.** Scored truth is *new*
   faults; mapped faults are masked. A dot 100–200 m from a mapped trace
   spends most of its 300 m kernel on the known fault (zero TP value) and
   pays near-full FP. B=2 deletes exactly that mass; the only recall lost is
   genuine splays within 200 m of mapped traces.
3. **Budget ≈37.7k sits at the marginal-credit cliff** for that surface
   (0.73% of the 5,167,373-cell footprint).

New measurement this session — the same file on two local instruments
(fixed raster, identical evaluator):

| instrument | H33-2-B2 | d2.8 base | H32-D | spaced random |
|---|---:|---:|---:|---:|
| catalogue-hidden HOLDOUT-DTI (whole-component hide, n=22,893) | **0.0039** [0.0033, 0.0045] | 0.1009 | 0.1030 | 0.0458 (38k pipeline) |
| SGMC off-catalogue AUXILIARY-PROXY DTI (79,615 proxy px) | 0.0929 | 0.1311 | 0.1338 | 0.0668 (38k full-grid) |

The 0.0039 is *expected arithmetic*, not a bug: B2 was pruned against the
**full** catalogue, so hide-and-recover truths (subsets of that catalogue)
sit ≥2 px from every B2 dot and can only earn the 2–3 px kernel fringe
(credit ≤1/3, mostly ~0). Hide-and-recover therefore **cannot** rank a
flank-pruned candidate fairly, and cross-family it barely ranks live results
at all (upstream Spearman vs owner-reported live: catalogue-hidden +0.087,
drift-corrected +0.510, SGMC +0.498; `research/upstream/h33-hypotheses.md` §0).
This is the single most important structural fact in the project: **the
local instrument and the leaderboard measure different fault populations.**
Catalogue-hidden rewards hugging visible traces; the organizer's new faults
were, by construction, *not* in the catalogue (competition page 967 via
`vendor/gems57/offcatalogue.py` docstring).

## 2. Can 0.2778 be beaten, and can 0.4413 be approached?

In principle yes; by emission tweaks alone, almost certainly not much beyond
0.28. Reasoning:

- The 0.19→0.28 family gains came from (a) one good multiline-corroborated
  ridge **surface**, then (b) emission geometry (dotting) and (c) flank
  pruning — each step smaller (+0.055, +0.012, +0.007 owner-reported).
  Emission is now near its optimum for that surface; B=3-style pruning trades
  the same recall pool and upstream variants plateaued at 0.263–0.271.
- Beating it materially requires a **better surface for the off-catalogue
  population**, validated on an instrument that resembles that population
  (SGMC-style proxy and/or the organizer's identification slots), not only on
  catalogue-hidden. Pure potential-field lineament surfaces have repeatedly
  failed this (H33 A–D below random on catalogue-hidden; H86-1 below random
  on SGMC, §3) because their named mimic — lithologic contacts — is the
  dominant signal in gravity/magnetics/conductivity edges.
- The 0.4413 leaderboard high (OWNER-REPORT in the brief; the brief also
  quotes 0.3195 elsewhere — conflicting, unresolved without a receipt; the
  live page is the only source and was not receipt-captured here) is far
  outside this family's envelope. Closing that gap plausibly needs
  supervised learning that generalises *off* catalogue (e.g. debiased PU,
  H86-3), the 1 m LiDAR scarp chain evidence at native resolution (H33-C
  direction), or identification experiments that spend a few slots to learn
  which local instrument predicts live — none of which can be promised from
  holdout alone, and none of which this session may claim.

Honest answer: this session does **not** produce a candidate with any
evidence of beating 0.2778. It produces a format-perfect, unique-surface
candidate that automated gates **reject**. Submitting it would be spending a
weekly slot on a random-equivalent dot field.

## 3. H86-1 experiment log (3/3 protocol experiments used)

Lane (preregistered, `research/h86-hypotheses.md`): per-physics straight-edge
score (Gaussian-derivative gradient magnitude × structure-tensor coherence)
for `rtp` (2), `det_elev` (12), `iso_grav_anom` (13), `depth_to_base_surf`
(15), `cond_surf` (17); surface = second-highest footprint rank (2-of-5);
greedy 2.8 px-spaced binary dots; no dot ≤2 px from *visible* catalogue
(per-fold in holdout). Non-fault mimic named in advance: lithologic contacts
/ basin-margin edges. That mimic is the most parsimonious explanation of the
result.

**E1 leakage canaries** (HOLDOUT folds, feature-alone AUC; block if >0.90):
rtp 0.547, det_elev 0.603, iso_grav 0.532, depth 0.532, cond 0.521,
surface 0.571. No leakage; note 2-of-5 corroboration *dilutes* the best
single field (DEM edge) — evidence for contacts over buried faults.

**E2 pipeline hide-and-recover** (buffered whole-component hide, seeds 20/21
× 4 quadrants, 12 px domain erosion, 3 px context buffer, visible masked
pixel-exactly, pooled DTI, 22,893 withheld positives, 20 km spatial-block
paired bootstrap), budget 38,000:

| arm | HOLDOUT-DTI [95% CI] |
|---|---:|
| **H86-1 candidate (pipeline)** | **0.0463 [0.0372, 0.0560]** |
| spaced random (pipeline, same budget) | 0.0458 [0.0415, 0.0495] |
| incumbent d2.8 (fixed raster) | 0.1009 [0.0901, 0.1117] |
| incumbent H32-D (fixed raster) | 0.1030 [0.0920, 0.1139] |
| incumbent H33-2-B2 (fixed, structurally handicapped, §1) | 0.0039 [0.0033, 0.0045] |

Candidate − random = **+0.0006 [-0.0082, +0.0103]** (CI includes 0);
candidate − best control = −0.0567 [-0.0685, -0.0439]. Fixed-raster arms
were built with full-catalogue knowledge (labelled in the evidence JSON);
the random arm is the strictly like-for-like pipeline control, and the
candidate does not beat it.

**E3 budget sensitivity** 44,090: candidate 0.0505 [0.0408, 0.0609] vs
random 0.0501 — tracks random exactly as budget rises, confirming coverage,
not discrimination, drives its number.

**Auxiliary SGMC proxy** (79,615 px = derived SGMC 83,593 − 3,978 catalogue
px, pixel-exact; derived file is a ~1 px dilation per vendor IR-57-SGMC-01,
raw SGMC not in the accessible manifest — approximate instrument, never a
score): candidate **0.0544 < random 0.0668** « d2.8 0.1311, H32-D 0.1338,
B2 0.0929. The surface is *worse than random* on the off-catalogue proxy:
straight potential-field edges preferentially avoid where unmapped faults
actually are, consistent with the contact mimic dominating.

## 4. Uniqueness (REGISTRY-MEASUREMENT, accessible scope)

14 hash-verified registry rasters (manifest group=scored + GEMSDOE32 B2/H32-D;
`scripts/fetch_registry.py`). Pre-placement surface: worst Spearman
**0.070** (vs h16-1) « 0.90. Final dots: worst geological dot-field 3 px
overlap **0.292** (vs h28) « 0.70. Literal gate fires only vs the
`r13-lattice-s5` calibration raster: overlap 0.971, but that witness covers
**99.87%** of allowed cells within 3 px (saturation certificate,
`docs/evidence/h86_saturation_lattice.json`), with rho −0.0003 and Jaccard
0.04 — a degenerate near-universal blocker of the same family the vendor
documented for dense surfaces. Reported, not waived; the candidate fails on
science gates long before this matters. Registry is **not complete**
(organizer/cross-team submissions and unfetched siblings absent).

## 5. Candidate file (generated, format-valid, REJECTED by gates)

`gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif`,
sha256 `5d135088…a2f6d5`, 38,000 dots, single-band float32, EPSG:32611,
3730×3292, transform (100, 0, 243350, 0, −100, 4508550), min 0.0 / max 1.0,
n_nan = n_inf = 0 over the full 12,279,160 cells (all-finite zeros policy —
this class of file cannot produce the owner's "[0,1]" portal error),
0 dots on catalogue. Validator: all checks pass (`docs/evidence/h86_validator.json`);
audit re-verifies card↔bytes (`scripts/audit.py`, exit 0). **Verdict:
negative. Do not submit.** Name and ≤140-char note exist only so a future
selector can identify the artifact:
`H86-1 edge2of5 dotted B2 38000dots | HOLDOUT-DTI 0.0463 pooled-hide-v2 n=22893 | UNSCORED`

## 6. Irregularities flagged

1. B2 "0.2778" is OWNER-REPORT; pinned audit says UNSCORED/projected 0.2747.
   Brief quotes leaderboard highs 0.4413 and 0.3195 in different paragraphs.
2. `training_features.tif` finite mask differs from the sample footprint:
   3,061 nonfinite cells inside, 1,540 finite outside (all five used bands).
   Handled by median fill outside per-band finite footprint; ranks computed
   on the sample footprint.
3. Sample submission's 60,988 cells equal to 1 sit exactly on labelled
   faults (upstream note) — it is a grid template, not a prediction.
4. Fixed-raster incumbent arms in hide-and-recover are not pipeline
   like-for-like (full-catalogue construction); B2's 0.0039 is the extreme
   case. Only spaced-random is strictly comparable to the pipeline candidate.
5. Lattice calibration raster is a near-universal literal-overlap blocker
   (99.87% coverage) — the 0.70/3 px gate cannot discriminate against it.
6. SGMC proxy uses the dilated derived raster (raw unavailable in manifest);
   treated as approximate auxiliary evidence only.

## 7. What to do next (selector / next lane, in order)

1. Do **not** spend a slot on H86-1. Spend identification effort (separate
   selector step, live quota check first) on learning which local
   instrument predicts live for *surface* changes, since catalogue-hidden
   demonstrably mis-ranks flank-pruned/off-catalogue methods.
2. Next geological lane by expected value: H86-3 debiased PU or the LiDAR
   en-echelon chain at native resolution — both target the surface, not the
   emission, and both must be screened on SGMC-proxy + catalogue-hidden
   jointly (beat random on both, beat incumbent on at least the proxy,
   before any slot discussion).
3. Obtain raw `sgmc_faults_100m.tif` (and its official SGMC source DOI) so
   the proxy instrument matches the vendor derivation byte-for-byte.
4. Keep emission doctrine fixed (dotted 2.8 px, B=2 flank exclusion,
   ~38–44k budget, all-finite zeros) — it is the family's proven component.

Official sources for manual review: competition
https://www.drivendata.org/competitions/306/competition-doe-gems/ ·
problem/format https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ ·
leaderboard https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ ·
reference solution https://github.com/drivendataorg/gems-prize-reference-solution ·
USGS GeoDAWN (DOI 10.5066/P93LGLVQ) https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
INGENIOUS https://gbcge.org/current-projects/ingenious/ · EPSG:32611 https://epsg.io/32611 ·
Tversky index https://en.wikipedia.org/wiki/Tversky_index
