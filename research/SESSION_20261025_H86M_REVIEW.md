# H86M session review (2026-10-25, branch arena/4add368e-gemsdoe86)

## Answer: why did H33 score 0.2778 (owner-reported), and can we beat it?
H33 = GEMSDOE28 parent minus 2,545 dots in the 1<d_cat<=2px collar, 0 added
(verified pixel-exact in prior sessions; vendored metric alpha=0.2/beta=0.8,
300m kernel pays alpha*FP per dot, so deleting low-credit collar dots can
raise DTI). 0.2778/0.4413/0.3195 are OWNER-REPORTED, no organizer receipt in
repo. Beating it requires a candidate whose paired HOLDOUT-DTI CI vs matched
controls excludes 0 on the positive side. Neither H86M lane did. No
leaderboard projection is made.

## What was done this session
1. Restored hash-pinned competition data in-sandbox via
   `scripts/restore_data.py --with-external --include-registry`
   (training_features.tif 4371c82e..., 5 external grids, dense witness) and
   `scripts/prepare_data.py` (19 bands). This corrects the prior session's
   "data absent" blocker for THIS sandbox.
2. Preregistered H86M-BMR (registry followup queue rank 1) before scoring:
   research/H86M_BMR_PREREGISTRATION.md. Ran it (scripts/run_h86m_bmr.py)
   with the shared gems57 evaluator/writer, PA-86-01 preflight.
   Instrument bug found and fixed in-pass: holdout arms must collar against
   VISIBLE catalogue per fold (EDTI allowed_vis precedent); a full-catalogue
   collar structurally guarantees DTI=0. Reported transparently.
3. H86M-BMR result: HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld)
   0.0220 [0.0086, 0.0384]; paired vs raw-gravity control -0.0144
   [-0.0257, -0.0025] -> hypothesis FALSIFIED (band-15 circularity mimic wins).
4. Experiment 3, H86M-CNT (queue rank 3): HOLDOUT-DTI 0.0408 [0.0257, 0.0575];
   paired CIs vs cond-only and |shear| controls both cross zero -> negative.
5. Both rasters: unique (surface Spearman <=0.067; dot-field 3px overlap
   <=0.57 vs 57-58 measured registry rasters), values exactly {0,1}, 0 NaN,
   validator PASS, zero dots on catalogue. Verdict negative, DO NOT SUBMIT,
   0 slots. Budget (3 experiments) exhausted; no further lanes run.
6. Registered H86L-FMC + both H86M artifacts in download-inventory.json and
   registry/artifact_cards.json (fixes the pre-existing check_site/build_site
   failure from PR #150); added run-card.v1 branch to scripts/audit_release.py;
   audit_downloads --write, audit_release --measure-registry, build_site and
   check_site all PASS. Site banner + executive summary state the download /
   submit decision and the [0,1] (-zeros, never -1/-nan) fix at the top.

## Portal "[0,1]" error
No published -zeros TIFF reproduces it (all revalidated: min 0, max 1,
0 NaN). existing_faults.tif uses -1 outside footprint; a file derived from it
would trigger exactly this error. That is a labelled hypothesis, not a
confirmed cause (the uploaded filename was never supplied).

## Irregularities
- IR-H86M-01: data/prepared_manifest.json regenerates with a new timestamp,
  breaking build_site's historical cf73474c receipt pin; manifest reverted,
  prepared arrays (.cache, ignored) retained. Owner should re-pin deliberately.
- IR-H86M-02: audit_release previously could not normalize any
  gems86.run-card.v1 lane (H86L-FMC included) -> build_site failure predated
  this session; fixed with an explicit negative-only branch.

## Run cards
docs/evidence/h86m-bmr-run-card.json (sha fa7418e8...),
docs/evidence/h86m-cnt-run-card.json (sha ff95ed56...).
- IR-H86M-03: the live registry remeasurement (34 artifacts) refreshed
  all-artifacts-registry.json measured_utc; the frozen followup card's
  registry_measurement_utc pointer was synced to it (negative content
  unchanged) so its binding test stays valid. Flagged for owner review.
