# Session review 2026-10-25 — `arena/92f9e0e8-gemsdoe86`

Three passes: (1) implement + verify, (2) review own work for bugs/edge cases and fix,
(3) recheck against the full request. Budget: 3 experiments (E1 surfaces+canary,
E2 holdout, E3 emission+registry — all inside one preregistered lane run), 0 submission
slots. Request archive: `research/REQUEST_20261025_92F9E0E8.md`.

## Bottom line (obvious submission status)

**DO NOT SUBMIT ANY FILE.** This session generated one new unique GeoTIFF
(`gems86-h86n-eql-seislineation-37654dots-20261025T181759Z-zeros.tif`, SHA-256
`5b355275dfbc6774b3f113a1ec85e4becab6b8235f78386f3de1e098da27895a`) and its preregistered
hypothesis was **not supported** on the spatially blocked holdout, so the file is an
audit-only negative deliverable. Separately, the repo's publication state was repaired:
H86M-LT is now registered and consistently labelled (scientific PA-86 PROMOTE preserved;
`safe_to_submit=false`, no slot authorized), and `check_site.py` passes again.
`approved_for_weekly_slot=false` everywhere; 0 slots used.

## Why did h33 score 0.2778 (owner-reported), and can we beat it?

Re-verified pixel-exactly in this checkout this session (not copied from prior prose):
`h33-h33-2-b2` (37,654 dots) = its GEMSDOE28 parent `d28` (40,199 dots) **minus exactly
2,545 dots, all with 1 < d_cat ≤ 2 px (measured min √2, max 2.0), plus 0 added dots**;
h33's nearest dot to the catalogue is 2.236 px. Under the pinned DTI
(α=0.2, β=0.8, 300 m triangular kernel; `DTI = T/(0.8K + 0.2(T+n−M))` in the shared
`vendor/gems57/metric.py` algebra), every emitted dot that earns no truth credit still
adds α-weighted false-positive mass to the denominator, while truth credit saturates
through the kernel `max`. Dots hugging mapped traces (1–2 px) are precisely the mass most
likely to earn nothing — hidden truth is defined off the mapped network, and the fleet's
own near-catalogue control (`poisson81`, owner-reported 0.0041) shows the collar earns
~nothing. So h33's lead is an **emission-efficiency** result (2.8 px dotted spacing +
collar pruning on the H19-5 multiline surface), not new geology: the top of the fleet is
one lineage whose spread (0.245–0.278, all owner-reported) is produced by budget/spacing/
collar choices on essentially one surface, while independent families (gate_ortho 0.2376,
p5 0.2478, ptcf 0.2343, cvarlw 0.2303) corroborate that a real, narrow off-catalogue
signal exists. Causality limit: with no organizer receipt and no hidden truth, collar
pruning is the uniquely consistent mechanism for the pixel diff + metric algebra, not a
proven cause of the +0.0070 owner-reported delta over d28.

**Can a submission score higher than 0.2778?** Plausibly yes in expectation —
tomography in the H86M-LT lane estimates h33 recovers only ≲40 % of weighted hidden truth
(K≈15.5k px), leaving precision-weighted-coverage headroom, and H86M-LT's fitted-belief
projections (never scores) put its candidate above the h33 model under two of three
beliefs and tied under the coarsest. But no file in this repo has an organizer-confirmed
score, the catalogue hide-and-recover instrument anti-correlates with the live ordering
for off-catalogue emissions (measured in H86G E1b), and this session's new geological
lane (below) did not beat its own controls. The honest statement is: **beating 0.2778 is
unproven until an organizer receipt exists**; spending a weekly slot is a separate owner
selector decision this session does not make.

## Ranked hypotheses and the lane run

Five untried hypotheses were frozen in `registry/h86n_hypotheses.json` before
implementation (layers / signature / why catalogue-missing / difference / mimic / cost /
falsifier each): **1) H86N-EQL** earthquake-lineation anisotropy (bands 10/16),
2) H86N-GSST gravity step-vs-compact shape, 3) H86N-MTCS seismic→conductance down-dip
phase offset, 4) H86N-SPBT spin-2 seismic×conductance alignment, 5) H86N-CHTD
transtensional regime-angle gating. All use only hash-pinned native bands (no new
external data needed; optional free official check named: USGS ComCat FDSN,
https://earthquake.usgs.gov/fdsnws/event/1/). Rank 1 was preregistered
(`research/H86N_EQA_PREREGISTRATION.md`) and run with shared tools only
(`scripts/run_h86n_eql.py`).

**Result (all numbers HOLDOUT-DTI, evaluator `gems57-pooled-hide-v2`, 11,321 withheld
positives, 1000-draw 20 km block bootstrap):** candidate **0.0306 [0.0175, 0.0455]**;
C0 isotropic-density control 0.0356 [0.0139, 0.0595]; C1 RTP-gradient control 0.0429
[0.0300, 0.0566]; paired Δ −0.0050 [−0.0301, +0.0200] (vs C0) and −0.0123
[−0.0311, +0.0074] (vs C1). Leakage canary PASS (max single-feature AUC 0.543 ≤ 0.90).
Uniqueness vs 61 locally measured rasters: max surface Spearman 0.069, max dot phi 0.140,
max forward 3-px overlap 0.579 (≤ 0.70) — the TIFF is unique in the measured local scope
(complete-registry restoration was not run this session and is not claimed). Format
validator: all checks pass (values exactly {0,1}, 0 NaN/Inf, EPSG:32611, 3730×3292,
sample transform, 0 dots on catalogue) — the "[0, 1]" portal error class is excluded on
these bytes. **Verdict: negative.** Interpretation: at 100 m grid, the seismicity fields
are too smooth/sparse for 600 m tensor coherence to rank mapped-fault proximity better
than density alone; anisotropy may still be useful as a *gate* on a proven surface, but
that is a new hypothesis requiring fresh preregistration — do not re-run EQL unchanged.

## Repo review findings repaired (Pass 1–2)

1. **Publication contradiction (IR-86-92F9E0E8-H86M-PUBLICATION).** On `main`:
   `check_site.py` failed (exit 1) — H86M-LT TIFF/ZIP unregistered; lane page said
   "OK TO SUBMIT? YES"; run card `safe_to_submit=true`; README headline contradicted the
   generated index. Registered LT + EQL (37 artifacts), added reviewed `h86m_lt` /
   `h86n_eql` branches to `scripts/audit_release.py`, added a dated publication addendum
   to the LT card (scientific content untouched), aligned lane page + README.
   `audit_release --measure-registry`, `audit_downloads --write`, `build_site`,
   `check_site` all PASS after repair.
2. **`scripts/verify_submission_tif.py` ignores its CLI argument** and always verifies
   the pinned H86G-EDTI file (by design as a pinned-byte guard, but the interface is a
   footgun: passing another TIFF silently verifies H86G instead). Flagged here; not
   changed this session because tests pin its behaviour — recommend renaming to
   `verify_h86g_pinned_tif.py` or making the argument mandatory-and-checked.
3. **New owner claims not yet in the fleet ledger** (IR-86-92F9E0E8-PRIOR-SCORES):
   GEMSDOE91/92 scores from this request are archived in the request file;
   `registry/prior_scores.csv` needs a deliberate feed re-pin before transcription.
4. Pass-2 self-fix: first registration edit reformatted two JSON files wholesale;
   redone with original indentation so diffs stay line-auditable (+34/−4 lines).

## Limitations and next steps (prioritized)

1. **No organizer-confirmed score exists for anything.** The single highest-value action
   is an owner selector decision on H86M-LT (the only PA-86 PROMOTE) with the receipt
   archived in `ledger/submissions.csv`; until then every live number is owner-reported
   and every expected-DTI figure is a projection.
2. **Complete-registry uniqueness for EQL not restored** (61-raster local scope only);
   run `scripts/restore_registry_inventory.py` before any future uniqueness claim
   (AGENTS.md rule 15 lesson from H86G).
3. **Next geological lane:** H86N-GSST (rank 2) as a surface ranked on catalogue
   hide-and-recover; or fuse EQL coherence as a *gate* under a fresh preregistration.
   Do not re-run pure EQL, BMR or CNT unchanged (all measured negatives).
4. Transcribe GEMSDOE91/92 owner claims into `registry/prior_scores.csv` with the fleet
   feed re-pin; rename/guard `verify_submission_tif.py`.
5. The literal full-support-witness rule still blocks every nonempty raster; only an
   owner protocol decision (not an agent edit) can retire PA-86's like-for-like reading
   or the witness itself.

## Sources (manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ ·
  problem description page/967 · reference solution
  https://github.com/drivendataorg/gems-prize-reference-solution (not scraped this
  session per AGENTS.md rule 9; links for human browser review).
- Metric: Tversky index, https://en.wikipedia.org/wiki/Tversky_index ; pinned local
  implementation `vendor/gems57/metric.py` (α=0.2, β=0.8, R=300 m).
- CRS: https://epsg.io/32611 · GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
  INGENIOUS: https://gbcge.org/current-projects/ingenious/ · GDR 1391:
  https://gdr.openei.org/submissions/1391 · USGS ComCat:
  https://earthquake.usgs.gov/fdsnws/event/1/

## Run card (session)

```json
{
  "lane": "H86N-EQL earthquake-lineation anisotropy",
  "hypothesis": "Line-like organization of seismicity fields (bands 10/16) at ~600 m traces active, incl. catalogue-missing, faults; isotropic clouds do not.",
  "mechanism": "Structure-tensor coherence x energy x density, rank surface; 37,654 dots @2.8px, dcat>3; shared gems57 evaluator/writer only.",
  "named_non_fault_process": "Geothermal induced-seismicity radial clusters; quarry/blast and network-geometry location artifacts.",
  "holdout_dti": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": "gems57-pooled-hide-v2", "withheld_positives": 11321, "value": 0.0306, "ci95": [0.0175, 0.0455], "paired_vs_C0_iso_density": [-0.0301, 0.0200], "paired_vs_C1_rtp_grad": [-0.0311, 0.0074]},
  "correlation_overlap_vs_registry": {"scope": "61 locally measured rasters (incomplete; complete registry not restored)", "max_surface_spearman_abs": 0.069, "max_dot_phi_abs": 0.140, "max_forward_overlap_3px": 0.579, "limits": [0.90, 0.70]},
  "raster_sha256": "5b355275dfbc6774b3f113a1ec85e4becab6b8235f78386f3de1e098da27895a",
  "validator_output": {"no_nan_inside_footprint": true, "values_in_0_1": true, "values_exactly_0_1": true, "crs_shape_transform_match": true, "zero_dots_on_catalogue": true},
  "submission_name": "gems86-h86n-eql-seislineation-37654dots-20261025T181759Z-zeros",
  "note": "H86N-EQL seismicity lineation anisotropy dotted 37654; HOLDOUT-DTI in run card; DO NOT SUBMIT",
  "verdict": "negative",
  "safe_to_submit": false,
  "approved_for_weekly_slot": false,
  "submission_slots_used": 0,
  "machine_run_card": "docs/evidence/h86n-eql-run-card.json"
}
```
