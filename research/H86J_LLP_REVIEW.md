# H86J-LLP review: what ~100 live scores say about the hidden truth, and why the protocol holdout cannot see it

**Date:** 2026-10-25 (UTC) · **Lane:** H86J-LLP · **Verdict:** `negative` · **Gate:** `DO NOT SUBMIT`
**Preregistration (frozen 04:34 UTC, amendments A1–A5):** [`H86J_LLP_PREREGISTRATION.md`](H86J_LLP_PREREGISTRATION.md)
**Run card:** [`docs/evidence/h86j-llp-run-card.json`](../docs/evidence/h86j-llp-run-card.json) ·
**Gate result:** [`docs/evidence/submission-gate.json`](../docs/evidence/submission-gate.json)

## Evidence labels

Every number below carries one of these labels:
- **HOLDOUT-DTI**: `gems57-pooled-hide-v2`, 11,321 withheld positives, paired 20-km-block bootstrap 95 % CI.
- **OWNER-REPORTED**: user-supplied scores without an organizer receipt.
- **LLP-EMULATOR**: a fit statistic or a MODEL projection. It is never a score.
- **ANALYTIC**: a closed-form derivation from OWNER-REPORTED inputs.

There is no **ORGANIZER-CONFIRMED** number in this lane. No DrivenData page was fetched, no upload was
made and no weekly slot was used.

## 1. The overlooked data source: the fleet's own scores

Ninety-two sibling projects have uploaded rasters and recorded their live scores. Each score is
a deterministic functional of the hidden new-fault truth G:

`DTI_r = T_r / (0.2 T_r + 0.2 F_r + 0.8 |G|)`, with `T_r = Σ_{g∈G} max_x p_r(x) k(|x−g|)`.

If G is replaced by an intensity λ (truth pixels are independent Bernoulli(λ)), then
`E[T_r] = Σ_g λ(g) c_r(g)` exactly, where `c_r` is raster r's max-kernel coverage map. That makes the
scores *aggregate labels* of the truth, and **learning from label proportions** (LLP) becomes
possible. Fit `λ = exp(b + θ·φ)` over rank-transformed raw-data features so that every raster's
expected DTI matches its reported score. As far as a repository grep shows, no lane had done this;
every earlier lane fitted the catalogue, which the organiser masks, or hand-weighted detectors.

**Data.**
- 109 of 115 OWNER-REPORTED score rows were joined to hash-verified bytes. Sources: 655 registry
  blobs (`data/registry_ext`), 26 local fleet files, and 39 newer files streamed from the owners'
  public repos via codeload (`docs/evidence/scored-ext-receipt.json`).
- Deduplication by in-footprint content left **102 distinct rasters from 59 sites**. Five aliases
  agree exactly on their score.
- Eight rows were dropped: 6 without bytes, plus 2 ambiguous GEMSDOE40 names
  (`docs/evidence/h86j-llp-e0-fleet.json`).

## 2. Results

### E1 — leakage canary and LLP fit (`docs/evidence/h86j-llp-e1.json`)

- **Canary:** 24 features were tested alone on the protocol holdout, with catalogue features built
  from visible faults only. The maximum discriminative AUC is **0.8044**, for the HGB
  catalogue-signature posterior. That is below 0.90, so no feature was dropped.
- **LLP-EMULATOR fit:** leave-one-site-out (LOSO) Spearman between predicted and reported live scores:

  | Model | ρ = 0.3 | ρ = 1 | ρ = 3 | ρ = 10 |
  |---|---:|---:|---:|---:|
  | Full (24 features) | **0.855** (RMSE 0.052) | 0.755 | 0.644 | 0.590 |
  | Distance/density only | 0.541 | 0.555 | 0.585 | 0.563 |

  The preregistered acceptance rule (≥ 0.50 and above the distance-only model) **passes**:
  0.855 vs 0.585. The geophysical and topographic features add real predictive power about
  *live* truth.
- **Fitted catalogue-distance profile.** This is the truth-intensity multiplier relative to >6.4 km
  from any mapped fault. Individual bands are collinear with the density term, so read the shape,
  not the digits:

  | Distance from mapped fault | ≤200 m | 200–400 m | 0.4–0.8 km | 0.8–1.6 km | 1.6–3.2 km | 3.2–6.4 km |
  |---|---:|---:|---:|---:|---:|---:|
  | Multiplier | 0.08 | 0.18 | 0.72 | 3.8 | 1.0 | 21.9 |

  New-fault truth is **depleted roughly 5–12× inside 400 m of mapped faults** and enriched
  kilometres away. Independently, the catalogue-density term is negative (−2.23): relative to the
  model, truth is commoner where mapped faults are sparse.
- **Largest positive weights:**
  - HGB catalogue-signature posterior +4.98: fault-*like* geophysics and topography, but not near the catalogue;
  - DEM gradient (σ = 1.5 px) +2.42;
  - H86G-L multiline corroboration +1.11;
  - gravity gradient +0.97;
  - top-hat L ridge +0.83.

  Conductivity (−1.09), the geodetic 2nd invariant (−0.81) and radiometric total count (−0.71) are
  negative.
- **Known weakness: the top end is compressed.** The model fits H33 at 0.163 (reported 0.2778) and
  the 13GEMSDOE lattice at 0.168 (reported 0.0904). It ranks catastrophes well, but it cannot yet
  separate the H19-5 lineage from uniform coverage. Something in H19-4/H19-5's construction
  (openness/thermal/"pop" layers) carries signal that is missing from the 68 pinned features. This
  is a concrete next feature to rebuild from raw data.

### E2 — protocol holdout, like-for-like (`docs/evidence/h86j-llp-e2.json`)

HOLDOUT-DTI (`gems57-pooled-hide-v2`, seed 20, 11,321 withheld positives, 37,654 dots, E[k]
spacing-greedy ≥2.8 px, visible collar >2 px). Every arm was built from visible faults only.

| Arm | HOLDOUT-DTI | 95 % CI |
|---|---:|---|
| **H86J-LLP (candidate)** | **0.0370** | [0.0249, 0.0498] |
| LLP distance-only ablation | 0.0015 | [0.0001, 0.0034] |
| H86G-L multiline (shipped promote's surface) | 0.0505 | [0.0375, 0.0662] |
| H86G-H HGB catalogue posterior | **0.1373** | [0.1161, 0.1607] |
| random dots | 0.0475 | [0.0417, 0.0534] |
| H86G-H, collar 3 (exact reproduction of the published 0.1689) | 0.1689 | — |
| H33 recipe on visible faults (D2.8 − visible 2-px collar; 38,110 dots) | **0.0286** | — |

Candidate − best in-run comparator (H86G-H): **−0.1003 [−0.1259, −0.0765]**. The published
same-split record is H86F-EWCS at 0.1723. **The promote rule fails, so the verdict is `negative`.**

### E3 — final build and gate (`docs/evidence/h86j-llp-run-card.json`)

- The full-catalogue λ was emitted by E[k] spacing-greedy (≥2.8 px, collar >2 px).
- The budget rule (MODEL projection, never a score) chose **44,090 dots**. The emulator curve is
  flat from 37,654 to 44,090.
- Uniqueness was measured on the surface and the final dots against 734 hash-bound rasters (655
  pinned registry blobs plus local and codeload extras), with PA-86-02 chance correction; the
  results are in the run card.
- The shared writer and validator ran, and then the automated gate. The gate prints **DO NOT
  SUBMIT** because check S3 (protocol holdout) fails. The format and uniqueness results are listed
  in the gate JSON.

## 3. The central scientific finding: the protocol holdout points the wrong way

E2 is the first like-for-like out-of-fold (OOF) measurement that puts the live champion's recipe on
the protocol holdout. **The H33 recipe scores below random (0.0286 vs 0.0475).** The
catalogue-signature HGB model scores 3× random (0.137–0.169), yet the fleet's catalogue-supervised
uploads scored 0.0286 and 0.0424 live (OWNER-REPORTED). The live-calibrated distance profile scores
0.0015.

The mechanism is not subtle:
- **Holdout truth** is withheld *catalogue* components. Fault systems cluster, so those components
  sit a few pixels from visible faults, and the holdout rewards catalogue proximity and catalogue
  signature.
- **Live truth** is organiser-labelled *new* faults. According to the fleet's own scores, they are
  depleted ~5–12× inside 400 m of mapped faults, as GEMSDOE81's 44,090 catalogue-hugging dots
  scoring 0.0041 shows, and they are enriched kilometres away.

The two instruments therefore reward opposite placements. H86G's E1b table had shown the same
anti-correlation with as-is rasters (IR-86-H86G-INSTRUMENT). E2 removes the "as-is leakage"
objection by rebuilding every arm out of fold.

**Consequence for the user's rule** ("do not spend a slot on an idea that hasn't beaten the current
holdout best"): any candidate that respects the live depletion law will lose to catalogue-hugging
arms on this holdout. Any candidate that wins the holdout will tend to hug catalogue tips, the very
placement the live scores punish. Changing that rule is the owner's call, not this lane's. Section 6
gives the concrete options.

## 4. Why GEMSDOE32 `h33-h33-2-b2` led (0.2778 OWNER-REPORTED)

This combines the prior pixel-exact forensics (`H33_ANALYSIS.md`, `h86f-h33-forensics.json`) with
the new LLP evidence.

1. **No new layer.** H33 = the D2.8 parent minus 2,545 dots at catalogue distance √2–2 px. The
   0.2708 → 0.2778 step is pure emission.
2. **The collar works for a measurable reason.** The LLP profile puts truth density at ×0.08 within
   200 m and ×0.18 at 200–400 m. Deleting those dots removes false-positive mass that almost never
   meets truth. The H33 collar is the first rung of a depletion law that extends to ~800 m.
3. **Its dots sit where new faults are.** 49 % of H33's dots are >2 km from a mapped fault and only
   5.8 % are within 300 m. Catalogue-hugging fleet rasters invert that distribution and collapse:
   GEMSDOE81 at 0.0041, GEMSDOE83 at 0.0573.
4. **Coverage-efficient emission.** Spacing of 2.8–3 px matches the 300 m kernel. A non-redundant
   dot pays off iff its kernel credit k > 0.2·DTI, which is ≈0.056 at DTI 0.28 (ANALYTIC). A dot
   placed within one kernel radius of another adds false-positive mass at little truth gain.
5. **Truth mass and budget (ANALYTIC + LLP).**
   - The stride-5 lattice (0.0904) implies |G| ≈ 12.5k truth px per footprint-equivalent. The
     LLP's λ implies ≈30k, but the LLP over-predicts the lattice, so the true value probably lies
     between them.
   - Either way, truth is roughly 0.25–0.6 % of the footprint. The DTI-optimal dot count for a
     surface of H33's quality falls in the 35–45k range where the fleet's ≥0.26 cluster sits.

## 5. Can we beat 0.2778, and reach the cited 0.3195 or 0.4413 (both OWNER-REPORTED, unverified)?

- **What a gain requires.** At DTI ≈ 0.28 and |G| ≈ 12.5–30k, +0.04 needs roughly 1.4× H33's truth
  credit per dot. Reallocating H33's own dots measured |Δ| ≤ 0.007 (SLOT_PLAN), so new localising
  evidence is required.
- **What this lane adds.** It is the first instrument that is *trained on live truth*. It explains
  85 % of the rank order of 102 live scores out of site.
- **The strategy we recommend** (still unvalidated, and none of it a score):
  - (a) Keep the H19-5 surface family. It is the only family the live board rewards.
  - (b) Reweight its dots with the LLP depletion law, extending the collar logic to ~800 m, and
    tilt the mass toward catalogue-sparse terrain.
  - (c) Rebuild the H19-4/H19-5 openness and thermal layers from raw data, so the emulator can see
    what it currently misses.
  - (d) Use the emulator's LOSO-validated ranking, not the catalogue holdout, to choose between
    variants.
- **What we do not claim.** That such a file would score 0.3195 is not established here. Only an
  organizer receipt can confirm any number.

## 6. Decisions the owner must make (stated, not taken)

1. **Holdout rule.** Choose one:
   - keep S3 binding, in which case no live-calibrated idea can ever be promoted (§3);
   - replace S3 with a live-aligned validation (the LLP LOSO-CV emulator, which needs a top-end fix first);
   - require a *detached-truth* holdout: hide only components ≥8 px from any other component, which mimics new faults.
2. **Weekly-slot policy.** Decide whether a single live probe of an H19-5 × LLP-depletion variant is
   worth one of the ≤3 weekly slots. It would directly test §4.2.

## 7. Limitations

- All fleet scores are **OWNER-REPORTED**, and the public leaderboard is computed on undisclosed
  public chunks (organiser statement relayed by https://github.com/munimtechnologies/gems-fault-mapping;
  forum topic 11550 was not fetched, per AGENTS rule 9).
- The emulator's top end is compressed (H33 fit 0.163 and the lattice 0.168, against 0.2778 and
  0.0904 reported). A λ-optimised raster flatters itself: the candidate projects 0.404 against H33's
  0.163. That is why S4 can only veto.
- The 1 m 3DEP LiDAR, the USGS ComCat catalogue and an absolute DEM are free official sources, but
  they are unreachable from this sandbox. That blocked H86J-PLUV and H86J-SEIS.
- The template's cached feature stack is still absent. The pinned 19-band TIFF and the 5 external
  grids were used directly, via the H86G stack builder.

## 8. Sources checked this session (links for manual review)

These were found by web search on 2026-10-25. No DrivenData page was fetched or scraped (AGENTS
rule 9); forum items are quoted only from search-engine snippets and should be re-read by a human.

**Official and primary sources:**

| Topic | What it says | Source |
|---|---|---|
| Prize basics | $300,000 GEMS Prize; two rounds; submissions due 3 Dec 2026 | DOE HGEO, https://www.energy.gov/hgeo/articles/hydrocarbons-and-geothermal-energy-office-announces-300000-help-identify-hidden |
| Official rules record | The rules document itself | NLR research hub, https://research-hub.nlr.gov/en/publications/geologic-enhanced-mapping-system-gems-prize-official-rules/ (PDF linked from the README: https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| Test-set design | Test set = expert-labelled faults in the GeoDAWN region that are *not* in the USGS fault database. The region is chunked into public and private test sets. Phase 2 re-scores against labels expanded by expert review of all submissions; the top five advance | ThinkGeoEnergy report of the DOE announcement, https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/ |
| GeoDAWN magnetic/radiometric data | Glen & Earney (2024); lidar acquired in coordination through 3DEP | USGS data release, DOI https://doi.org/10.5066/P93LGLVQ (https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) |
| Lidar faults and magnetics | Young basin faults recently mapped from lidar near Battle Mountain displace weakly magnetic basin fill and produce subtle magnetic anomalies visible in GeoDAWN data. This supports lidar + high-resolution magnetics as the localising pair for new faults | GRC paper, https://publications.mygeoenergynow.org/grc/1034804.pdf |

**Forum snippets (search engine only; re-read before relying on them):**

| Topic | Snippet | Source |
|---|---|---|
| 11516 | Only new-fault truth is scored; a prediction near a known trace but far from new truth is fully penalised | https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516 |
| 11527 | Staff do not share the data sources, fault types or coverage behind the test faults. Phase 2 uses a test set updated by expert review of all Phase 1 submissions | https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527 |
| 11536 | "New fault" means any fault pixel not already captured by USGS/INGENIOUS, including newly mapped geometry of an existing system | https://community.drivendata.org/t/where-do-you-draw-the-line/11536 |

**Third-party (not official; flagged):** https://github.com/munimtechnologies/gems-fault-mapping
relays two forum points: topic 11524 (3 scored submissions per rolling week) and topic 11550 (scores
pooled over public-test pixels; chunk layout not disclosed).

**Irregularity to flag.** The third-party relay of 11550 says the public leaderboard pools only the
public-test chunks. If true, every OWNER-REPORTED score in this lane measures only those chunks,
which strengthens the case for emulator ranking over raw score chasing.
