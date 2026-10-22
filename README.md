# GEMSDOE86 — audited fault-prediction research

## NOT READY TO SUBMIT — no candidate TIF generated

[Executive summary and submission instructions](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/executive-summary.html) · [Research and source review](research/REVIEW.md) · [Machine-readable run card](docs/evidence/run-card.json)

This session began with only a README. It recovered integrity-pinned mirrored grid inputs and unmodified shared evaluator/writer code, not a trained model or proven winning submission. **Do not submit the sample TIFF or any upstream historical raster as a new submission.** No weekly slot was used. A downloadable candidate is deliberately absent rather than misrepresented as validated or unique.

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
- `scripts/audit.py`: negative run card with real grid checks, separate from unrun candidate validation.
- `tests/`: safety tests, not geological validation or score estimates.
- `docs/`: Pages site, executive summary and downloadable evidence, not a fake submission button.

### Next session, in order

Resolve the lane, obtain/pin the shared feature cache and complete registry, validate layer identities, establish a comparable current-best holdout, run leakage canaries, then test only the authorized hypothesis. After improvement and uniqueness checks, export through the shared writer, validate the serialized file, and have the separate selector verify the live weekly quota. Until then this is a **negative preflight**, not a successful submission generator.
