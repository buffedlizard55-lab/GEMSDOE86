# GEMSDOE86 — standing project runbook (reviewed 2026-10-26)

## Read at the start of every session

1. [`AGENTS.md`](AGENTS.md) — repository workflow, mandatory preflights and publication rules.
2. [`README.md`](README.md) — current status, evidence links and the complete owner request preserved verbatim under **“Complete current owner prompt archive — 2026-10-26.”**
3. [`research/REQUEST_20261026.md`](research/REQUEST_20261026.md) — companion owner-input archive. Its leaderboard figures and external-project claims are requests/claims, not verified evidence.
4. The latest relevant preregistration, run card and review. For the inherited H86P lane these are [`research/H86P_TCWB_PREREGISTRATION.md`](research/H86P_TCWB_PREREGISTRATION.md), [`docs/evidence/h86p-tcwb-run-card.json`](docs/evidence/h86p-tcwb-run-card.json), and [`research/SESSION_20261026_H86P_TCWB_REVIEW.md`](research/SESSION_20261026_H86P_TCWB_REVIEW.md).

## Current release and download state

**No file in this checkout is authorized for a competition upload or weekly slot.** The previously generated H86P-TCWB TIFF is a valid research/audit download only; its existence, format pass, pixel uniqueness or historical holdout result does not clear it for submission. This review has generated no new candidate TIFF and used no slot. The current release and protocol audits are fail-closed.

- H86P-TCWB historical evidence: **HOLDOUT-DTI = 0.1727007956**, 95% CI **[0.1560010, 0.1893807]**, evaluator `gems57-pooled-hide-v2`, **11,321 withheld positives**. Its paired change against the preregistered E3 ablation is **+0.0161572**, 95% CI **[+0.0040447, +0.0286042]**. These are spatial-holdout measurements, not leaderboard results, and were not rerun in this review.
- GEMSDOE32 H33 **0.2778 is OWNER-REPORTED**, not organizer-confirmed. The raster lineage describes which pixels changed; it does not establish why private organizer truth rewarded the change. Other leaderboard figures in request archives are also unverified unless supported by a submission-page receipt.
- The pinned historical `17GEMSDOE` full-support witness measures positive at every allowed footprint cell. Under the unchanged literal overlap rule, every nonempty allowed candidate has 100% direct overlap with that witness, exceeding the 70% stop. Do not bypass, amend, or reinterpret this gate.
- The current local input audit found `training_features.tif`, prepared native feature arrays and a verifiable shared feature cache missing. A small integrity-pinned bridge pair and the separately pinned registry witness do not supply the scientific stack. Therefore no new holdout experiment is reproducible from the current checkout.

## Binding scientific and submission protocol

- Read the full owner request in `README.md`; follow the one-assigned-method-lane rule. Do not silently choose a lane or use a private copy of shared tools.
- Reuse the shared cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue features only from visible faults; mask visible faults pixel-exactly; evaluate pooled DTI with `alpha=0.2`, `beta=0.8` and the 300 m triangular kernel. Test each feature alone; AUC above 0.90 is a stop until explained.
- Check rank-correlation before placement and dot overlap after placement against the registry. Stop and log a duplicate for correlation above 0.90 or more than 70% of dots within 3 px of a registry raster. Missing or incomplete registry evidence is not a pass.
- Label measured scores as **HOLDOUT-DTI** with evaluator, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** with a submission receipt. State explicitly when a number is a preregistered projection; projections are not scores and must not be presented as leaderboard results.
- Finish an authorized experiment with its required JSON card, including hypothesis, mechanism, named non-fault mimic, holdout result and interval, registry measurements, raster SHA-256, validator output, submission name/note and verdict. Negative results count. Stop after three experiments or two hours. Never select a live submission slot; promotion is a separate selector step.
- Before proposing a new lane, rank 3–5 distinct geological hypotheses by evidence, expected holdout change and implementation cost; name layers, the target physical signature, why the target could reveal faults missing from the catalogue, how it differs from prior repo work, and whether necessary free official data is obtainable. Validate a viable top hypothesis on the spatial holdout before any slot.

## Work ethic and limitations

Keep **Maximize P(Win)** and **Own the Outcome** central: verify claims, preserve negative results, correct stale or overstated interpretations, and make download safety and submission readiness unmistakable. Do not automate DrivenData scraping. A mirror hash establishes byte identity, not organizer provenance; a local format audit establishes neither geological validity nor a live score. Current limitations are the literal registry-overlap stop, missing native feature stack/shared cache, and lack of organizer submission receipts. No weekly slot has been selected.
