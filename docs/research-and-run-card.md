# Research review, candidate register, and run card

**Status: NEGATIVE / BLOCKED.** This is an evidence report, not a generated prediction. No submission TIF was generated; no holdout experiment was run; no weekly slot is recommended. The repository started with only `README.md`, so there is no stack, registry, holdout evaluator, or writer to execute the required shared workflow.

## Executive finding

The competition target is faults that may indicate geothermal resources—not direct detection of geothermal vents. The official problem page describes an incomplete public fault catalogue and newly expert-labelled faults for evaluation. It scores a probability/confidence raster with a distance-weighted Tversky metric; the official formula assigns `alpha=0.2`, `beta=0.8`, with a 300 m linear triangular distance kernel. Accordingly, simply emitting a high density of lines is not a sound strategy: a candidate must put probability near the hidden targets while controlling unnecessary prediction mass. A local hide-and-recover score against known catalogue faults is only a proxy for the competition's unseen-fault objective.

The data page resolves to DrivenData's login form from this environment. There are no local competition files or tools. It is therefore not possible to reproduce the reference raster, check any raster's uniqueness, calculate a holdout score or confidence interval, or create a trustworthy submission artifact here.

## Source review and evidence boundaries

| Claim or source | What was directly observed | What it does not establish |
|---|---|---|
| [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Describes the fault-discovery objective, supplied geology/geophysics feature families, expert-labelled hidden faults, distance-weighted Tversky formula, and GeoTIFF format. | It does not provide the authenticated data files through this checkout or verify any GEMSDOE team's model or score. |
| [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Fetch redirected to the DrivenData login page. | No download was obtained; this is an access blocker, not proof that the files are unavailable to an authenticated competitor. |
| [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Repository page says to download challenge data into `data/`, offers CPU/GPU environments, and contains a reference notebook. | Its existence does not mean this checkout has the requested cached feature stack or the required shared holdout/writer utilities. It is not an alternate source of competition files. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | USGS describes airborne magnetic and radiometric surveys and airborne lidar, with a linked DOI data release; the page records CC0 1.0 for this release. | It does not by itself establish that any particular external grid is spatially aligned to the competition template or useful for this task. |
| [INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391) | The public page identifies the release, CC BY 4.0 license, DOI `10.15121/1881483`, and lists resources including shallow-temperature, geophysical, and paleogeothermal datasets. | Resource listings are not proof that a downloaded file was inspected, aligned, or validated in this checkout. No such file was downloaded here. |
| [GEMSDOE32 linked page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | The page presents H33-2-B2 as a candidate, gives a model-projected value, and explicitly says no organizer score exists for that artifact. It describes a catalogue-flank deletion and proxy/live-model analyses. | The page is not an organizer submission receipt. Its model and owner-reported analyses do not establish the score of the downloaded bytes. |
| [Live official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Direct read on 2026-10-22 showed the top entry as xiaofanhu with public score **0.4413 — ORGANIZER-CONFIRMED (official public leaderboard read; not a submission-page receipt)**. | A public leaderboard result is not a receipt linking a particular local TIF to a score. It is not a holdout result for this project. |

### H33 score question: what can and cannot be concluded

The request describes `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` as having **0.2778 — USER-REPORTED (not verified from an organizer receipt in this checkout)**. The linked GEMSDOE32 page does not substantiate that number as a score. In the page text retrieved for review, the H33-2-B2 artifact is described as deleting predictions close to the catalogue from a base raster. It reports a proxy/live-mirror result and a **projected 0.2747 — MODEL PROJECTION, NOT A SCORE**, and expressly states that no organizer score exists for that artifact. Its run-card-style site text also marks the candidate `UNSCORED`.

Thus, there is no evidenced causal answer to “why did this TIF score 0.2778?” The strongest answer supported by the source is conditional: if the reported increase came from this candidate, removing pixels close to the known catalogue could reduce prediction mass spent on already-known traces while retaining off-catalogue geometry, which is directionally compatible with a competition focused on unmapped faults and a metric that penalizes false-positive mass less than false-negative mass. That is a plausible mechanism, **not a verified explanation of an organizer score**. The source's own proxy evaluation cannot demonstrate a gain on the hidden fault set; its generative live model is an owner-derived model, not an organizer evaluation.

The user-provided historical list also names **0.3195 — USER-REPORTED (historical leaderboard claim; not verified here as current)** and **0.4413 — USER-REPORTED in the prompt**. The direct live leaderboard read independently shows a current top entry with **0.4413 — ORGANIZER-CONFIRMED (official public leaderboard read; not a submission-page receipt)**. These must not be conflated: the user's first “current high score” value is stale relative to that read, and none of the listed sibling-site scores are receipts for a GEMSDOE86 raster. The official live leaderboard result is the relevant public comparison; the user-supplied `0.2778` remains unverified.

## Candidate hypotheses (proposed only; none tested)

Ranking is by qualitative expected value per implementation cost, not by a predicted numerical DTI. There are no data-backed score projections. The **current branch contains no implementation**, so every candidate differs from what is implemented here. Prior experiment names supplied by the user (for example, topo/geophysics, scarp, strain, and hydro-conduit families) make global novelty uncertain; names alone cannot establish what transforms those files used. Before any promotion, the actual resulting raster must pass the registry similarity and overlap gates.

| Rank | Hypothesis and layers | Physical signature / why it might find an unmapped fault | Named non-fault mimic | Difference from this repository and prior-site uncertainty | Cost / expected value |
|---:|---|---|---|---|---|
| 1 | **Scale-persistent potential-field edge concordance** using provided reduced-to-pole magnetics, TMI vertical/horizontal gradients, and isostatic-gravity anomaly/slope. | Derive edge responses at multiple scales and retain lineaments where independently measured magnetic and gravity edges are spatially and directionally coherent. A buried or poorly exposed structure can perturb multiple potential fields while having no mapped surface trace. Test only residual edge response outside a catalogue buffer; do not feed the held-out catalogue geometry into features. | Lithologic contacts, intrusive bodies, basement composition changes, survey-boundary/flight-line artifacts. | There is no code in this repository. The supplied history contains a generic “topo-geophys baseline” and other geophysical/radiometric names, so distinctness from every sibling cannot be certified from names alone. This hypothesis is specifically cross-scale edge agreement between potential-field observables, not another emission/thinning rule. | **Moderate** coding and validation cost; best qualitative expected value because it tests independent geophysical evidence already in the described feature stack without first requiring new external data. No numeric improvement claimed. |
| 2 | **Strain-localization orientation change** using dilatation rate, shear strain rate, and second strain invariant. | Measure spatial gradients and local directional coherence/change, then test whether persistent narrow strain boundaries associate with withheld fault segments. These deformation-field signatures can reveal unmapped structural corridors, but may be too spatially smooth for individual faults. | Regional strain gradients, interpolation seams, or broad tectonic deformation unrelated to a discrete mapped fault. | No implementation exists in this checkout. The supplied history includes a strain-named model (`sarnnpu`); exact feature construction is unknown, so this may overlap earlier work and must be compared against its raster before considering it novel. | **Low–moderate** cost using supplied layers; expected value below rank one because the provided strain fields may be coarse and its distinctness is uncertain. |
| 3 | **Conductive-base / surface-conductivity boundary agreement** using surface conductivity, depth to conductive base, and magnetic/gravity edges. | Look for coincident lateral conductivity boundaries and independent structural edges. Fault-controlled fluid pathways and alteration can affect conductivity; the independent geophysical agreement may prioritize unmapped structures over isolated conductive anomalies. | Basin-fill thickness changes, clay-rich lithology, saline fluids, and non-fault stratigraphic boundaries. | No implementation exists here. User-supplied history includes a “hydro-conduit” experiment; no raster or source code is available to determine whether this is duplicative. A final correlation/overlap test is mandatory. | **Moderate** cost; expected value medium-low until the stack band definitions and prior hydro-conduit outputs are inspected. |
| 4 | **Depth-coherent magnetotelluric conductance boundary** using the five depth-range conductance maps listed by GDR 1391 (external data), compared with the competition's magnetic/gravity stack. | A depth-consistent conductive boundary may identify fault-controlled fluid pathways or basin structures not represented by surface fault catalogues. Evaluate whether the boundary persists across depth, rather than using a single conductivity map. | Conductive lithology, saline basin fluids, and regional geothermal alteration not tied to an unmapped fault. | No implementation exists here. GDR 1391 lists regional electrical-conductance maps and links the product; the specific files, coverage, CRS, licensing details for redistribution, and alignment have not been checked in this checkout. The GDR page is the source to inspect before download; no external raster is claimed obtained. | **High** data-ingest and alignment cost; potentially valuable independent evidence, but not currently viable to validate without downloading and auditing the official data. No performance estimate. |

### Top-candidate holdout plan (not executable in current checkout)

If the missing shared tools and data become available, test rank one only as the next experiment. First freeze the hypothesis, parameters, masks, and folds. Run each raw feature alone as a leakage canary. For each fold, withhold whole fault segments with the required buffer; build every catalogue-derived feature from visible faults only; mask visible faults pixel-exactly; and score pooled distance-weighted Tversky using the shared evaluator and prescribed parameters/kernel. Report evaluator version, withheld-positive count, paired fold results, and a 95% CI. Compare the final surface to every registry raster before placement and after writing; stop as a duplicate if either threshold is exceeded. Only then may the shared writer create a file, which must be reopened and validated against the actual template. The original protocol limits work to three experiments or two hours; this session used **zero experiments — SESSION COUNT (not HOLDOUT-DTI)** because prerequisites are absent.

## Submission instructions and current blocker

When a candidate eventually passes validation, use the exact generated filename and its short method note in the DrivenData form. The official problem page specifies a single-band float32 GeoTIFF in EPSG:32611 at 100 m resolution, matching the training grid's bounds/transform, predictions in `[0,1]`, and null/NaN outside bounds. The previous portal message “Predicted values must be in range [0, 1]” cannot be diagnosed from this repository because the offending upload and template are absent. Out-of-range finite values and a nodata sentinel outside `[0,1]` are possible causes in general, but neither has been established for that failed upload.

No file is offered for download. No name or note is reserved for a real submission. **Do not submit an artifact from GEMSDOE86 until the blocker is resolved and a receipt can be kept.**

## Specific next work needed

1. Provide authenticated competition data to `data/` on a machine/session that can access it, then record file hashes and the official template metadata. Do not silently substitute an owner mirror for organizer data.
2. Add or connect the shared cached-stack, holdout, writer, and registry artifacts to this template (not a private fork); audit their versions and run the specified baseline once before any experiment.
3. Verify that data availability fits the task, available CPU/RAM/GPU, and the two-hour/three-experiment budget. The official reference repository offers CPU/GPU setups; this session has not run training.
4. Run the top candidate's spatial holdout and feature-level leakage canaries. No submission slot is eligible without beating the registered current holdout best, with uncertainty reported.
5. Implement the front-page download only after a real raster passes byte-level format checks, duplicate checks, and a reproducible manifest. Attach SHA-256, a note no longer than 140 characters, and the submission receipt if scored.

## Run card

```json
{
  "hypothesis": "Scale-persistent concordance of magnetic and isostatic-gravity edges",
  "mechanism": "Independent potential-field boundaries may reveal buried or poorly exposed faults absent from the public fault catalogue.",
  "named_non_fault_mimic": "Lithologic contacts or intrusive bodies producing coincident magnetic and gravity edges.",
  "holdout_dti_and_ci": "NOT MEASURED — no shared evaluator, feature stack, labels, or registry files in this checkout; withheld positives and 95% CI unavailable.",
  "correlation_overlap_vs_registry": "NOT MEASURED — registry rasters absent; no surface placement performed.",
  "raster_sha256": null,
  "validator_output": "NOT RUN — no raster exists; no NaN/range/CRS/shape/transform result can be claimed.",
  "submission_name_and_note": "PROPOSED ONLY, NOT CREATED: GEMSDOE86-multiscale-potential-edge-v1; note: Cross-scale magnetic–gravity edge concordance; blocked-holdout candidate only, not a submission.",
  "verdict": "negative"
}
```

## Manual-review links

- [Official competition overview and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official rules page](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [Official data page (login required here)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [GDR 1391 INGENIOUS compilation](https://gdr.openei.org/submissions/1391)
- [GEMSDOE32 H33 page (owner-maintained, not organizer evidence)](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
- [GEMSDOE32 hypothesis page (owner-maintained)](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/hypotheses.html)
