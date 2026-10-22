# GEMSDOE86 — auditable fault-prediction research

## 🔴 Current submission status: DO NOT SUBMIT

A TIF is available for **audit/research inspection only**; it is not a cleared competition submission. Its local GeoTIFF/range checks pass, but the literal registry-overlap stop rule fired and the historical holdout is not protocol-conformant. Do not spend a weekly submission slot on it.

- [Open the readiness dashboard](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/)
- [Read the exact portal steps](docs/executive-summary.html) — no file is currently marked **OK TO SUBMIT**
- [Audit-only GeoTIFF](docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif) · SHA-256 `cf4ab3403d28b085018b01221487e58e20fe2697cf17e96be739bd87a91a5962`
- [Current run card](docs/evidence/run-card.json) · [raw historical diagnostics and correction](docs/evidence/lane86_results.json) · [dated source review](docs/evidence/source_review_2026-10-22.json)

The current artifact is **not a new TIF generated in this review**. It was already present in the checkout. I revalidated its bytes and format, independently reproduced the lattice overlap, corrected the misleading readiness claims, and disabled repeat experimentation after the three-experiment cap.

## Persistent task directive — read at the start of every session

This section records the project's working brief and experiment contract. Before making changes, read this file, [`research/REVIEW.md`](research/REVIEW.md), [`research/NEXT_CANDIDATES.md`](research/NEXT_CANDIDATES.md), [`research/VERIFICATION.md`](research/VERIFICATION.md), and [`docs/evidence/run-card.json`](docs/evidence/run-card.json). These sources maintain the ongoing research record; they do not replace the full user request or authorize work outside its constraints.

### Objective and values

- Build an auditable, useful research and submission-preparation project for the DOE GEMS fault-prediction competition. The benchmark target is **faults indicative of geothermal resources**, not direct geothermal-vent confirmation.
- **Maximize P(Win):** choose work by evidence, risk, and expected value; a weekly submission slot is an experiment, not a lottery ticket.
- **Own the Outcome:** make end-to-end claims only when evidence supports them, expose defects and negative results, and fix unsafe workflows rather than hiding them.
- Keep the research grounded in official, free/public data with source links, licenses, hashes, grid checks, and explicit access limitations. A source listing is not proof a file was downloaded or matched to the grid.
- Aim to reduce manual checking with repeatable audits and a dated source feed. A static source snapshot is not a live feed; report its retrieval date and do not imply it is automatically current.

### Submission file and download policy

- The eventual product should be one **unique, single-band GeoTIFF** with an obvious download and an unmistakable status at the top of the site. Provide a distinct submission name and a short note no longer than 140 characters.
- Never copy an earlier submission as a candidate (except for clearly marked education/reproduction). Check content and lane overlap against the full available registry.
- **Local format PASS is not permission to upload.** The official format is EPSG:32611, 100 m, matching bounds/shape/transform, one float32 band, predictions in [0,1], and allowed nodata behavior outside bounds. Reopen the serialized TIFF and check all values, NaN/Inf/sentinels, footprint, checksum, and ZIP contents.
- The site must make it obvious whether a file is safe to submit. The current file is red-status and audit-only. Do not submit it, and do not spend a weekly slot on a candidate that fails a scientific or uniqueness gate.
- Explain the portal workflow on the executive-summary page. Validation should be automated; actual portal authentication, weekly-cap selection, submission, and organizer receipt remain separate steps. No automatic upload or unverified human-inspection claim is made here.

### Parallel-run and experiment contract

- Work only in the explicitly assigned method lane. The prompt referenced a “single method paragraph” that was not supplied. The earlier agent self-selected H86-RMRB; that was not valid lane authorization. Resolve the lane before any new scientific experiment.
- **Reuse, do not privately rebuild:** use the template's hash-pinned cached feature stack, shared hide-and-recover evaluator, and shared submission writer. If a shared tool is wrong, fix it once upstream and report the change; do not keep a private fork. The upstream cache receipt in this checkout names an ephemeral path and lacks a usable cache hash, so the requested stack is currently unavailable.
- A valid holdout must withhold whole fault segments/components with a buffer, derive catalogue-based features only from visible faults, and mask visible faults pixel-exactly. Use the shared pooled distance-weighted Tversky metric (alpha 0.2, beta 0.8, 300 m triangular kernel). Report the evaluator version, withheld-positive count, and a spatially appropriate 95% CI; compare against the best comparable holdout on identical folds.
- Test every feature alone on the holdout. AUC above 0.90 is suspected leakage until investigated; a low AUC does not prove geological validity.
- Before placement, compare the surface with every pinned registry raster; check dot overlap before and after final masking. Spearman correlation above 0.90 **or** more than 70% of dots within 3 px of any registry raster means duplicate/lane collision: log it and stop. Do not add exceptions for dense lattices or low Jaccard.
- Rank 3–5 untried hypotheses before a new experiment, each with layers, physical signature, missing-fault mechanism, named mimic, novelty against this repo, expected-potential tier, cost, and external-source availability check. Qualitative rankings are not score projections.
- Stop at three experiments or two hours. Negative results are deliverables. Promotion to a real weekly slot is a separate selector decision within the authenticated weekly cap.

### Evidence and score policy

- Label a score only as **HOLDOUT-DTI** with evaluator version, withheld positives, and 95% CI, or **ORGANIZER-CONFIRMED** with a copied submission-page receipt. A public leaderboard snapshot, projection, owner claim, test metric, or file name is not an organizer receipt.
- Keep source facts, measured findings, hypotheses, user/owner reports, and inaccessible/unverified inputs distinct. If a page says “unscored,” do not convert its projection into a score.
- Explain unknown causes honestly. The former portal message “Predicted values must be in range [0, 1]” cannot be diagnosed without the exact rejected file. The current TIF passes local numerical checks; that does not identify the old error or guarantee organizer acceptance.
- End each research run with one JSON run card containing hypothesis, mechanism, named non-fault mimic, valid holdout DTI+CI (or null if not established), registry correlation/overlap, raster SHA-256, validator output, submission name/note, and promote/negative verdict.

### Review of the H33-2-B2 claim

The linked [GEMSDOE32 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) describes a dotted raster pruned near the catalogue. The page marks the file **UNSCORED**, presents a model projection, and says that no organizer score exists. A possible metric-geometric explanation for a genuinely receipted score is that removing weak/redundant prediction mass lowers false-positive cost, but that is not proof of a confirmed result or new geological discovery. The checked-in owner manifest and historical artifacts also carry numerical annotations; they are preserved as owner-maintained provenance, not receipts or score labels. The live [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was fetched in the latest review and is above the maximum quoted in the prompt; its numeric value is not copied into this project's score card without the required per-submission receipt.

## Current evidence and blockers

1. **The existing TIF format is locally valid.** It is a one-band float32 raster in EPSG:32611 with the expected grid and values in [0,1]. This was independently checked with owner-mirrored sample/fault rasters whose hashes match the local manifest; they are not organizer-authenticated.
2. **The literal duplicate stop fired.** The final dots have more than 70% forward 3-pixel overlap with the pinned 13GEMSDOE lattice raster. They are not an exact byte/pixel copy, but the prompt defines overlap as an independent OR stop. Pre-placement dot overlap was not recorded, and the registry is incomplete.
3. **There is no admissible holdout result.** The historical runner imported but did not use `evaluate_holdout.py` for scoring, did not apply the required whole-segment context buffer, used a cell bootstrap rather than the shared spatial-cluster interval, and compared only one selected baseline. Raw diagnostics remain in evidence but are excluded from the run card.
4. **The lane is unresolved and the three-experiment cap is consumed.** No new geological experiment is authorized in this session. The legacy runner fails closed.
5. **No upload or slot check occurred.** There is no ORGANIZER-CONFIRMED result for this artifact.

The linked H33 page and public board are owner/organizer sources respectively, but neither substitutes for a submission receipt for this project's file. Current source facts and limits are in [`docs/evidence/source_review_2026-10-22.json`](docs/evidence/source_review_2026-10-22.json). Future hypotheses and official-data availability checks are in [`research/NEXT_CANDIDATES.md`](research/NEXT_CANDIDATES.md).

## Reproduce only the safe local audit

Python 3.11+ and the pinned packages in `requirements.txt` are used. GitHub CLI access is needed to restore small owner-mirror grid inputs; this does **not** authenticate with DrivenData.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/check_docs.py
.venv/bin/python scripts/audit.py  # expected exit 1 while readiness is negative; writes the report
.venv/bin/python -m unittest discover -s tests -v
```

The audit writes `docs/evidence/preflight.json`; it never overwrites the scientific run card. `data/` and `.venv/` are ignored by Git. The legacy `scripts/run_lane86.py` is fail-closed after the experiment cap and protocol review; do not run it to generate another candidate.

## Official review links

- [DrivenData competition overview and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS Great Basin conductance maps, DOI 10.5066/P9TWT2LU](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b)
- [USGS ComCat/FDSN query service](https://earthquake.usgs.gov/fdsnws/event/1/query)
- [GDR INGENIOUS compilation 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)
