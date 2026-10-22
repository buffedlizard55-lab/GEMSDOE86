# GEMSDOE86 — audited fault-prediction research

## 🔴 CANDIDATE GENERATED — DO NOT SUBMIT (failed the holdout gate)

**Download (inspection only):** [`docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif`](docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif) · SHA-256 `cf4ab3403d28b085018b01221487e58e20fe2697cf17e96be739bd87a91a5962` · [Site / readiness dashboard](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/) · [Executive summary: exactly how to submit](docs/executive-summary.html) · [Run card](docs/evidence/run-card.json)

The H86-RMRB GeoDAWN radiometric mixing-residual × RTP magnetic-edge candidate was produced by a prior parallel run and is already present on `main`; this follow-up did **not** generate, rerun the experiment, retest the science or serialized format, submit, or promote it. The merge verification only checked the existing run-card/file SHA consistency. It is locally format-valid and byte/pixel-distinct from the 12 checked rasters, but the shared uniqueness checker returns **unique=false / stop_required=true** (literal >70% 3-px dot-overlap gate fires vs the saturating 13GEMSDOE lattice raster; final-dot overlap 99.5%). The local registry is incomplete, so uniqueness is not established. The run card reports diagnostic **HOLDOUT-DTI** using label `gems57-pooled-hide-v2` with 22,641 withheld positives: candidate 0.0420 with cell-bootstrap 95% CI [0.0369–0.0467], below the same-instrument incumbent HOLDOUT-DTI benchmark 0.1011 [0.0856–0.1167]. Protocol review also found that the run rebuilt a lane-specific cache instead of using the required shared feature stack, used the older holdout/scoring entry points, and calculated a cell-bootstrap rather than the shared spatial-block interval. These values are **diagnostic, not protocol-complete promotion evidence**. Per the literal duplicate stop and negative holdout, **do not submit and do not rerun**; no weekly slot was used. No ORGANIZER-CONFIRMED score exists. Historical H33 figures in the brief are unverified owner reports; the owner manifest has no receipt and its page says UNSCORED. See `research/REVIEW.md` and the protocol caveats in the run card. Do not execute `scripts/run_lane86.py`.

## H33-2-B2: verified method and score status

At pinned GEMSDOE32 commit `780a5a534269c79adfe6d1d7d5aadead161332aa`, the [owner audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) describes deleting every dot within two grid cells (200 m on the 100 m grid) of the mapped catalogue, leaving 37,654 dots. The [owner manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/submissions_manifest.json) has `receipt:null`, and the [owner site snapshot](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/index.html) labels it UNSCORED. Thus the user-quoted H33 figure is not independently verified as ORGANIZER-CONFIRMED, nor is the legacy audit a protocol-complete HOLDOUT-DTI result (it omits evaluator version, withheld-positive count and spatial 95% CI). Pruning could reduce false-positive mass under distance-tolerant DTI, but that is a metric-geometry hypothesis, not proof of improved geology; it could also delete true parallel faults. This session did not copy or rescore the H33 raster.

## Starting brief — read at the beginning of every session

The following is a **condensed operational record** of the owner's long request, not a verbatim transcript. The original conversation remains the complete prompt. Read this AND research/REVIEW.md before work. Unfulfilled requirements remain explicit blockers rather than completed checkboxes.

- Review previous work first; maximize probability of winning through evidence, and own the outcome end to end. Do not trade scientific integrity for an optimistic claim.
- Generate a UNIQUE competition-format single-band GeoTIFF, never copy an earlier submission except for education. Make download and readiness status obvious at the beginning of the site. Supply a distinct name and note of at most 140 characters.
- Work autonomously through implementation, bug/edge-case review and final requirements review. Research official free data, preserve provenance and links, flag irregularities, distinguish verified facts from hypotheses. Explain access limits and next steps honestly.
- Parallel-run lane is the single assigned method paragraph. **None was present in the supplied request.** Do not guess authorization or drift into another lane. Surface and final-dot checks must stop on rank correlation >0.90 or >70% dots within 3 px of any registered raster.
- Reuse cached features, evaluate_holdout.py and submission_writer.py; do not privately fork shared tools. Hide complete fault segments with buffers. Derive catalogue features from visible faults only and mask visible faults exactly. Pool distance-tolerant Tversky components: alpha 0.2, beta 0.8, 300 m triangular kernel.
- Test each feature alone; holdout AUC >0.90 means suspected leakage until disproven. Generate/rank three to five untested geological hypotheses with named layers, signatures, missing-fault mechanism, mimics, novelty and cost before experiments. Confirm external data availability before treating an external-data idea as viable.
- Benchmark against the best comparable spatial holdout before touching a weekly slot. Stop after three experiments or two hours. Selection/promotion into a real slot is separate and must respect the authenticated weekly cap.
- Report scores ONLY as HOLDOUT-DTI (version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (actual submission receipt). User-reported values and projections are not confirmed scores. The request contains conflicting leaderboard highs; resolve against official evidence, not repetition.
- End with one JSON run card: hypothesis, mechanism, named non-fault mimic, holdout result+CI, registry comparisons, SHA256, serialized raster validation, submission name, short note, promote/negative. Negative results are deliverables.
- Build a clean GitHub Pages site with an executive summary explaining exactly how to submit. Reject NaN/Inf/sentinels and values outside [0,1], and match the template's CRS/shape/transform. Automated inspection must replace unsupported “human inspected” claims.
- Preserve source knowledge for future projects. Target fault prediction relevant to geothermal exploration; do not pretend a prediction proves a geothermal vent. Open and merge a PR, then list remaining limitations.

## Reproduce the audit

Python 3.11+ and authenticated `gh` are needed for mirror restoration. No credentials belong in chat or Git.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/audit.py
.venv/bin/python -m unittest discover -s tests -v
```

`restore_data.py --include-features` can also recover the hash-pinned raw mirrored feature TIFF. This is NOT the required shared cached stack; the option does not unblock experimentation. Large inputs are ignored in Git. No GPU is required for the audit. Official reference training supports CPU; GPU improves speed.

### What exists

- `vendor/gems57/`: shared upstream tools, byte-identical to the pin in `research/template_pin.json`.
- `research/upstream/`: owner-repository audit snapshots and official reference README; historical metrics are not fresh evaluations.
- `scripts/restore_data.py`: pinned mirror restoration with SHA and byte-length verification.
- `scripts/audit.py`: read-only consistency check for the current run card and published TIF; writes a separate preflight receipt and never overwrites the run card.
- `scripts/run_lane86.py`: prior H86 experiment implementation. **Do not rerun**: its three-experiment budget is consumed, the literal duplicate stop fired, and this review found cache/holdout protocol deviations.
- `tests/`: safety tests, not geological validation or score estimates.
- `docs/`: Pages site, executive submission guide, inspection-only TIF and linked evidence; no portal submission is implemented.
- H33 source review: pinned owner audit/manifest/page show catalogue-proximity pruning, `receipt:null`, and `UNSCORED`; see `research/REVIEW.md`. No H33 artifact was copied as a new candidate.

### Next session, in order

Do **not** rerun H86-RMRB or upload the existing TIF. Its three-experiment budget is consumed, the literal duplicate stop fired, and the review found that it did not reuse the required shared cache or exact shared spatial-block holdout path. Before any new geological experiment, obtain the actual assigned method paragraph, pin the shared cached feature stack and a complete registry, verify layer identities and authorized data access, then freeze the whole-component buffered holdout and shared evaluator. A new authorized lane must pass feature leakage canaries, same-instrument HOLDOUT-DTI with the correct spatial-block CI, full-registry surface and dot uniqueness gates, and serialized writer validation. Only a separate selector may check the live authenticated weekly cap. Until then this repository is a **negative, inspection-only research record**, not a submission-ready generator.
