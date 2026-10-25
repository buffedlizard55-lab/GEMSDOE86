# H86J-LLP preregistration: inverting the fleet's live scores into a new-fault truth intensity

**Frozen:** 2026-10-25 04:34 UTC (sandbox clock; JSON twin mtime 04:34:18). Written before any H86J surface was computed, any model
was fitted or any dots were placed. No assigned method paragraph was supplied in the current request
(`research/REQUEST_20261025.md`), so this lane defines its own single paragraph (below) and stays
inside it. Machine-readable twin: `research/H86J_LLP_PREREGISTRATION.json`.

## Lane paragraph

Every scored fleet raster is an *aggregate* measurement of the organiser's hidden new-fault truth:
its owner-reported live DTI is a known nonlinear functional of where its predicted mass sits relative
to truth that nobody can see. Learning from label proportions (LLP) treats ~80 such scores as weak
supervision. Fit a log-linear truth intensity `lambda(x) = exp(b + theta . phi(x))` over rank-transformed
raw-data features `phi` so that each raster's **expected** DTI under `lambda` matches its reported live
DTI. Then place dots where `lambda`'s kernel-expected credit is highest, using H33's proven emission
geometry. No registry raster is ever a feature, a training byte, or a source of dots. Registry rasters
enter only as (prediction, score) pairs in the likelihood, and as comparators in uniqueness checks.

## Why this lane exists (evidence available before freezing; see `docs/evidence/h86j-llp-e0-fleet.json` once written)

Two analytic inversions of OWNER-REPORTED scores motivated the lane. Their inputs are owner claims, so
both are ANALYTIC estimates, not scores:

1. **Truth mass.** 13GEMSDOE's stride-5 lattice (206,895 dots, i.e. one dot per 25 footprint cells)
   reported 0.0904. For a lattice, every truth pixel's expected max-kernel credit is 9.38/25 = 0.375,
   independent of where the truth lies. Solving `0.0904 = 0.375G / (0.851G + 0.2n)` gives
   `G ≈ 12.5k` truth px per full-footprint equivalent (≈0.24 % of footprint). That is about 3× fewer
   than the `|G| ≈ 40k` used in earlier SLOT_PLAN arithmetic.
2. **Depletion beside mapped faults.** GEMSDOE81 `cont-poisson44090-buf2` reported 0.0041. It has
   44,090 dots, 83.6 % of them within 3 px of the catalogue. Under (1), its implied truth credit is
   ≈0.08× that of random dots. New-fault truth is therefore strongly depleted within ~300 m of
   mapped traces. Under this G, the H33 champion's own credit implies ≈7× random enrichment.

Earlier lanes either fitted the catalogue (a population the organiser masks), hand-weighted
lineament detectors, or scored on catalogue-hide holdouts. Their as-is rankings disagree with the
live ordering (`research/H86G_EDTI_REVIEW.md`, E1b). No lane in this repository has used the fleet's
scores as supervision; a grep for LLP/score-regression returned nothing.

## Candidate hypotheses (3–5, not tried before), ranked by expected DTI gain ÷ cost

| Rank | ID | Layers | Physical signature / transform | Why it should catch catalogue-missing faults | Difference from repo | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | **H86J-LLP** | Bands 2 rtp, 3+9 analytic signal, 12 det_elev (gradient), 13 iso-grav (gradient), 15 depth-to-basement, 4 geod 2nd-inv, 10 deq, 17 cond, 6 tc, 19 slope; LiDAR step/cross maxima; 10 m hillshade lineament; profile curvature; H86G-L corroboration; HGB catalogue-signature posterior; catalogue distance bands + density (visible-only in holdout) | Log-linear intensity over rank-transformed edge/ridge magnitudes (plus top-hat ridge enhancement), fitted so kernel max-coverage expected DTI matches live scores | The supervision is the organiser's *new-fault* truth, seen through the scores, not the catalogue. Depletion near mapped traces and signature differences are learned rather than assumed | Every repo lane fits catalogue labels or hand-weights detectors; none inverts live scores | Medium | **Run (E1–E3)** |
| 2 | H86J-BUDGET | Same `lambda` | Truth-mass-calibrated stopping rule: emit while model-expected marginal credit > α·DTI (lattice-inverted G) | Avoids both over-dosing (FP mass, α·F) and under-dosing (β·FN) when truth is ~0.24 % of footprint | Earlier budgets were copied from H33 (37,654) or picked on proxies (55,000) | Low | Run inside E3 |
| 3 | H86J-DEPL | Catalogue distance transform only | Truth-density ratio by catalogue-distance band, estimated from scores; collar = break-even band | Organiser masks catalogue and new faults avoid its halo; the collar width should be measured, not copied | H33 used a 2 px collar by subtraction; no lane measured the profile | Low | Run inside E1 (ablation arm in E2) |
| 4 | H86J-PLUV | Absolute DEM elevation (USGS 3DEP 1/3″) + LiDAR steps | Veto steps that follow Pleistocene Lake Lahontan shoreline elevations (~1,200–1,340 m), the classic fault-scarp mimic | Removes a named FP mimic that LiDAR-scarp lanes reward | No shoreline veto exists in repo | Medium | **Blocked:** `det_elev` is detrended, and 3DEP (https://apps.nationalmap.gov/downloader/) is outside the sandbox allowlist |
| 5 | H86J-SEIS | USGS ComCat relocated hypocentres | Sub-km seismicity alignment (nodal-plane strike agreement) | Blind active faults are seismically lit without scarps | Bands 10/16 are smooth densities (ρ(1 km) ≈ 0.94–0.99) | Medium | **Blocked:** https://earthquake.usgs.gov/fdsnws/event/1/ is outside the allowlist |

## Experiments (budget: ≤3 experiments, ≤2 h wall-clock; no slot picking)

**E1 — fleet assembly, leakage canary, LLP fit.**

*Fleet assembly.* Join scored fleet rasters to `registry/prior_scores.csv` by exact basename. Sources
are the hash-verified registry (`data/registry_ext`) plus `data/scored_fleet`. Deduplicate by
in-footprint content, set predictions on catalogue pixels to 0 (pixel-exact live mask), and clip to
[0, 1] with a log entry.

*Canary.* Compute the single-feature AUC of every feature on the protocol holdout: withheld truth
pixels vs scored background, with catalogue-derived features built from visible faults only.
AUC > 0.90 means leakage: drop the feature and flag it.

*LLP fit.*
- Feature set: the frozen list in the JSON twin.
- Loss: Σ_r (logit ŝ_r − logit s_r)² + ρ‖θ‖², with ρ ∈ {0.3, 1, 3, 10}.
- Expected DTI per raster: `T_r = Σ_g λ(g) c_r(g)`, where `c_r` is the max-kernel coverage; `M_r ≈ T_r / 2.6`; `G = Σ λ`. The integrals are taken on a fixed 25 % uniform subsample S of footprint ∖ catalogue (seed 860310).
- CV: leave-one-site-out.

*Acceptance.* LOSO-CV Spearman(ŝ, s) ≥ 0.50 and > the CV Spearman of a distance-only model. If not,
LLP is uninformative: stop with verdict `negative`.

**E2 — protocol holdout, like-for-like.**
- Split: `holdout.buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3)`, evaluated with `evaluate_holdout` (`gems57-pooled-hide-v2`) and the paired 20 km-block bootstrap (1,000 draws).
- Emission, identical for every arm: E[k] = surface ⊛ kernel, spacing-greedy ≥ 2.8 px, allowed = footprint ∧ d_visible > 2 px, fixed budget 37,654.
- Every arm is constructed from visible faults only:
  - candidate `LLP`;
  - ablation `LLP-dist` (distance/density terms only);
  - comparators `H86G-L` (shipped promote's surface) and `H86G-H` (HGB catalogue-signature posterior, 68 features, visible labels; reported same-design best 0.1689 @37,654);
  - `random` (uniform in allowed).
- **Current holdout best** = the maximum same-design comparator measured in this run.
- **Promote rule:** candidate − best comparator > 0 with the paired 95 % CI lower bound > 0. Otherwise the verdict is `negative`, whatever any proxy says.

**E3 — final build + gates** (only meaningful if E1 is accepted). Full-catalogue features, the same θ, E[k] spacing-greedy emission, allowed = footprint ∧ d_cat > 2 px.
- Budget = argmax of model-expected DTI over {20k, 25k, 30k, 37,654, 44,090, 55k}. This is a MODEL projection, never a score.
- Uniqueness: `scripts/check_h86e_registry.py` on the surface and on the final dots, plus `scripts/pa86_chance_overlap.py`. Thresholds unchanged.
- Shared `submission_writer` + `validate`.
- The SGMC-PROXY-DTI is reported for continuity (selection evidence only).

## Fixed decision outputs

`scripts/submission_gate.py` reads the run card and recomputes the file checks from disk. It prints exactly
one of `OK TO SUBMIT` / `DO NOT SUBMIT`. `OK TO SUBMIT` requires all of the following:
- format/validator pass;
- uniqueness pass (surface + dots, like-for-like with chance correction, literal reading shown);
- canary pass;
- E1 acceptance;
- E2 promote rule;
- file SHA-256 equal to the run-card SHA-256.

A weekly-slot decision remains a separate selector step; the gate never claims a score.

## Named non-fault mimics

Pleistocene Lake Lahontan wave-cut shorelines and beach ridges; alluvial-fan channel and terrace
risers; roads, canals and pipelines; lithologic (non-faulted) contacts in potential fields.

## Amendments (each recorded before the computation it affects)

**A1 (04:38 UTC, before any fit).** The self-credit approximation `M_r ≈ T_r / 2.6` holds for dot
fields only. For a continuous raster T/M ≈ 1/3, and the fleet includes continuous rasters. Replace it
with the line-process expectation `E[M_r] = Σ_x p_r(x)·min(1, 3λ(x))`. That expression is the
two-sided strip integral of the triangular kernel; it yields T/M ≈ 3 for an isolated dot on a line,
and it is exact in the same small-λ limit for both raster types. `p_r` is evaluated on the same
subsample S. Nothing else changes.

**A2 (04:38 UTC, before any fit).** The registry snapshot lacks ~35 scored rasters. The REST API
quota was exhausted by the 655-blob registry restore, so `scripts/fetch_scored_codeload.py` streams
the owner repos' HEAD tarballs from codeload (allowlisted). It keeps only exact scored-name `.tif`
members and records SHA-256 + tarball commit in `docs/evidence/scored-ext-receipt.json`. Those
bytes are likelihood inputs and uniqueness comparators only.

**A3 (04:38 UTC, before any fit).** Compute: an L-BFGS fit on all 25 % S takes minutes. Leave-one-
site-out CV therefore uses a fixed deterministic 1-in-5 thinning of S (every 5th sorted index, i.e. 5 %
of the domain) with warm starts from the full-data fit; the reported final θ is refit on all of S.
The CV statistic stays LOSO Spearman, as preregistered.

**A4 (04:44 UTC, before E1/E2 ran; makes the gate stricter, never looser).** The repo's published
same-split record is **H86F-EWCS HOLDOUT-DTI 0.1723 [0.1530, 0.1898]**
(`gems57-pooled-hide-v2`, seed 20, 11,321 withheld, visible collar 3 px, its own budget;
`docs/evidence/h86f-ewcs-run-card.json`). The request says no slot may go to an idea that has not
beaten the *current holdout best*. The E2 promote rule therefore needs both of the following:
- (i) the paired CI rule against every comparator measured in this run;
- (ii) a candidate pooled HOLDOUT-DTI above 0.1723, the published same-split record.

The emission settings differ, so (ii) is not a like-for-like comparison. It is reported as such and
is used only to tighten the gate.

**A5 (05:04 UTC, after E2 and before E3; stricter only).** Add one binding gate check, **S4**: the
candidate's LLP-EMULATOR expected live DTI (a MODEL projection under the fitted λ, never a score) must
exceed the emulator's projection for H33 (`GEMSDOE32`, the current OWNER-REPORTED live best).
- S4 is necessary but not sufficient. A candidate optimised against λ will flatter itself, so S4
  can only veto; it never grants.
- It is recorded because E2 measured the protocol holdout ranking the H33 recipe *below random*
  (0.0286 vs 0.0475) while live scores put it first. A protocol-holdout pass alone could therefore
  promote a live-weak file.
- S1–S3 are unchanged.
