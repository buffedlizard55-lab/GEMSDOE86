# GEMSDOE86 — audited parallel fault-prediction lanes

**Read [`PROMPT.md`](PROMPT.md) first: it is the standing project brief, archived verbatim.**

## NEW UNIQUE TIFF GENERATED — SAFE TO DOWNLOAD, **NOT SAFE TO SUBMIT**

A new single-band competition-grid GeoTIFF was generated from the RMRB-86 model. It is not a copied or renamed prior raster.

- **Research TIFF:** [`gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.tif`](docs/downloads/gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.tif)
- **One-TIFF ZIP:** [`gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.zip`](docs/downloads/gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.zip)
- **SHA-256:** `9ed632445228aad8d9b14d8db75d24687520a092e7e14ca94c3151f96f7aafdd`
- **Submission name:** `RMRB-86 K-Th-U residual boundary + RTP persistence; 37,654 dots`
- **Portal note (107 characters):** `RMRB-86: K~Th+U residual boundaries gated by persistent RTP edges; HGB, 37,654 dots, 2 px catalogue collar.`

The automated format validator passes: one float32 band, all values finite and in `[0,1]`, EPSG:32611, exact shape/transform, zero outside the footprint, and zero on mapped catalogue pixels. The bytes are absent from 1,143 indexed public raster hashes and differ from the decoded stopping witnesses.

**Do not upload it.** The specific engineered transform did not beat its strongest matched raw-radiometric control with a wholly positive paired 95% interval, and the prompt's literal overlap gate is triggered by a continuous registry raster. The negative status is machine-readable in [`docs/evidence/rmrb86-run-card.json`](docs/evidence/rmrb86-run-card.json). No weekly submission slot was used.

### Repository-wide traffic light

Concurrent sessions produced other distinct rasters on `main`. None overrides the literal protocol or authorizes a weekly slot:

| Artifact | Automated evidence | Binding verdict |
|---|---|---|
| **This run: `gems86-rmrb-kthu-rtp-37654-…-DO-NOT-SUBMIT.tif`** | Local format pass; byte-unique in the 1,143-hash index; RMRB versus H33 overlap 0.456; transform delta CI crosses zero; dense-prior overlap 1.0 | **DO NOT SUBMIT** |
| `gems86-h86-rmrb-60000dots-…-zeros.tif` | Own run card is negative; HOLDOUT screen misses incumbent; literal lattice overlap 0.995 | **DO NOT SUBMIT** |
| `gems86-gmc-linepost-…-zeros.tif` | Format pass, but 82% overlap with a prior proximity lane | **DO NOT SUBMIT — duplicate lane** |
| `gems86-gmc-linepost-offcat-…-zeros.tif` | Format pass and low rank correlation, but its audit records literal overlap failures against saturated priors; its own report also records experiment-budget overrun | **DO NOT SUBMIT under the supplied literal rule** |

The earlier site called the last file “OK TO SUBMIT” by exempting continuous/carpet priors. The prompt authorizes no such exemption. This integration corrects the repository-wide decision to fail closed. A future selector may reconsider only after an explicit protocol change and an authenticated quota check.

This run was also checked against the three newly merged parallel rasters on both its continuous surface and final dots. Worst final overlap is 0.484 and worst surface Spearman is 0.093—below the lane thresholds. Those measurements are appended to [`docs/evidence/uniqueness.json`](docs/evidence/uniqueness.json).

[Open the GitHub Pages readiness dashboard](https://buffedlizard55-lab.github.io/GEMSDOE86/) · [Submission guide](https://buffedlizard55-lab.github.io/GEMSDOE86/executive-summary.html) · [Scientific review](research/RMRB86_REVIEW.md)

## Persistent project prompt — read before every session

This section is the repository's standing operational prompt. The original conversation remains the verbatim request and source of truth; this persistent version retains every binding requirement needed to continue safely.

1. **Outcome:** maximize the probability of a top DOE GEMS result and own the end-to-end outcome. Predict missing faults relevant to geothermal exploration without pretending that a fault prediction proves a geothermal vent.
2. **Unique deliverable:** generate a genuinely new competition-format TIFF, never rename/copy an older submission. Put an obvious download and an equally obvious **safe/not-safe to submit** decision at the beginning of the site. Include a unique name and note no longer than 140 characters.
3. **Parallel lane:** stay within one preregistered method. Stop promotion if full-footprint rank correlation with any registry raster exceeds 0.90 or if more than 70% of candidate dots are within three pixels of one registry raster's positive support. Check the surface before placement and final dots. Log negative results.
4. **Shared infrastructure:** reuse the template's cached data where obtainable and use the unmodified `evaluate_holdout.py` and `submission_writer.py`. Catalogue-derived operations must use fold-visible faults only. Mask visible/known faults pixel-exactly. Score pooled distance-tolerant Tversky terms with alpha 0.2, beta 0.8 and a 300 m triangular kernel.
5. **Leakage:** test each feature alone. Symmetric AUC above 0.90 is a stop pending a leakage explanation.
6. **Evidence labels:** performance values may be called only **HOLDOUT-DTI** with evaluator version, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** when bound to an authenticated submission-page receipt. A projection, user report or public-page observation is not a receipt.
7. **Scientific sequence:** before experiments, rank three to five untried hypotheses by expected DTI benefit and cost. Name layers, transform/signature, missing-fault mechanism, non-fault mimic, novelty and data viability. Check any external source before calling it viable. Validate the top candidate on spatially blocked hide-and-recover folds before a weekly slot.
8. **Budget and selection:** stop after three experiments or two hours. Promotion to a real slot is separate and must check the authenticated weekly quota. Never auto-upload from this repository.
9. **Run card:** record hypothesis, mechanism, mimic, HOLDOUT-DTI and CI, registry comparisons, raster SHA-256, validator output, name, note and `promote`/`negative` verdict. Missing evidence is never a pass.
10. **Automation and quality:** no human inspection is accepted as file validation. Reject NaN, Inf, sentinels and values outside `[0,1]`; require exact CRS, shape and transform. Work through implementation, bug/edge-case review and final requirement review. Preserve official/manual-review links, provenance, limitations and irregularities; do not hallucinate.
11. **Project site:** maintain a clean GitHub Pages dashboard, executive submission guide, current evidence and official links. A static site must not claim to be a live feed unless it actually refreshes from an authenticated source.
12. **Repository workflow:** work only on the Arena-assigned branch, open a pull request, merge only through the explicit PR operation, and report remaining work and blockers honestly.

### Core values carried forward

- **Maximize P(Win):** weigh tradeoffs and risk, then choose the evidence-grounded path that maximizes the probability of success rather than the most optimistic narrative.
- **Own the Outcome:** own the end-to-end result; act on failures when possible, and use both failures and successes as signals for improvement.

Here that means a valid TIFF is not called submission-ready merely because creating a download would feel like progress. The scientific and uniqueness outcomes remain binding.

### Current lane

`RMRB-86`: robust K~Th+U mixing residual, broad-background removal, multiscale residual-edge persistence, RTP-edge persistence, absolute cross-gradient alignment and line coherence; fold-proper positive/unlabelled HGB; fixed 37,654-dot placement with two-pixel inhibition/collar.

The prompt referred to a separate single-method paragraph but supplied none. The autonomous lane selection was frozen before execution in [`registry/preregistration.json`](registry/preregistration.json); this is recorded as an irregularity rather than hidden.

## What was measured

All values below are **HOLDOUT-DTI (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, paired physical-block bootstrap 95% CI)**:

| Arm | DTI | 95% CI |
|---|---:|---:|
| Ten-layer core control | 0.06406 | [0.05114, 0.07767] |
| Core + raw K/Th/U | 0.07116 | [0.05723, 0.08591] |
| Full RMRB-86 | 0.07283 | [0.05888, 0.08744] |

The RMRB-minus-core paired difference is **HOLDOUT-DTI delta (`gems57-pooled-hide-v2`, 22,893 withheld positives, 95% CI)** = `0.00877 [0.00296, 0.01434]`. The RMRB-minus-raw-radiometrics paired difference is `0.00167 [-0.00285, 0.00620]` under the same evidence label. Because the stronger interval crosses zero, the preregistered scientific promotion gate fails.

Twenty feature-alone canaries passed; maximum symmetric AUC was 0.58034. This is a leakage diagnostic, not a score.

## Why H33 may have helped—and why that is not enough

The hash-pinned H33 source describes pruning catalogue-adjacent dots from an earlier sparse raster. Under the distance-weighted Tversky objective, redundant prediction mass can increase weighted false positives without improving maximum truth coverage; kernel-scale sparse placement and collar pruning can therefore help. But an unmapped branch or continuation can also lie next to a mapped trace, so pruning is not guaranteed to help.

The historical scalar supplied by the owner has no authenticated submission-page receipt here and is not labelled ORGANIZER-CONFIRMED. RMRB-86 does not copy H33: final full-footprint Spearman correlation is 0.03022, forward three-pixel overlap is 0.45637, and file/decoded hashes differ.

See [`research/RMRB86_REVIEW.md`](research/RMRB86_REVIEW.md) for the five ranked hypotheses, source ledger, exact method, caveats and full interpretation.

## Reproduce

Python 3.11+ and authenticated GitHub CLI access to public owner mirrors are required. No credential belongs in chat or the repository.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_rmrb86_data.py --experiment
.venv/bin/python scripts/run_experiment.py
.venv/bin/python scripts/audit_rmrb86.py
.venv/bin/python -m unittest discover -s tests -v
```

The shared writer refuses to overwrite an existing candidate. Run model regeneration in a fresh checkout/output name; use `scripts/audit_rmrb86.py` to verify the already published artifact.

### Main artifacts

- `src/gems86_rmrb/`: label-blind RMRB features and fold-proper learner/emitter.
- `vendor/gems57/`: shared evaluator/writer, byte-identical to `research/template_pin.json`.
- `docs/evidence/feature-cache.json`: source, builder and cache hashes plus transform receipt.
- `docs/evidence/leakage-canaries.json`: every feature-alone canary.
- `docs/evidence/holdout.json`: pooled components, folds, scores and paired CIs.
- `docs/evidence/uniqueness.json`: surface/final stopping-witness measurements.
- `docs/evidence/rmrb86-run-card.json`: canonical final decision.
- `docs/downloads/`: locally valid negative-research TIFF, ZIP and writer receipt.

## Official/manual-review links and access limits

- [DrivenData problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — authenticated originals were not downloaded here
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)

This sandbox could fetch GitHub sources only. USGS, DrivenData, GDR and EPSG hosts were not freshly reachable. Owner-mirror hashes establish reproducibility, not organizer authentication. No GPU is required for this CPU experiment; no private truth or portal authentication is available.

## Next work

Do not spend a weekly slot on this raster. A future lane should either (a) test raw-radiometric generalization on a genuinely comparable frozen instrument, because that signal was stronger than core, or (b) repair the registry schema so continuous probability surfaces are used for the correlation test and sparse emissions for the dot-overlap test—but only if the owner explicitly changes the current literal rule. The RMRB transform itself is a negative result unless an independently preregistered experiment produces a positive paired interval.
