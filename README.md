# GEMSDOE86 — audited fault-prediction research

## 🔴 NOT READY TO SUBMIT — candidate generated, automated gates REJECTED it

**H86-1 candidate (inspection only — do not upload):**
`docs/downloads/gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif`
SHA256 `5d135088eb703e6d6f74f28b66b531145b290eac4fb542d6b5d5893ebba2f6d5` · 38,000 dots · format: ALL CHECKS PASS · science: FAIL
(HOLDOUT-DTI 0.0463 [0.0372, 0.0560], `gems57-pooled-hide-v2`, 22,893 withheld
positives — indistinguishable from spaced random; below random on the SGMC
off-catalogue proxy. Verdict `negative`, `submission_ready: false` in
`docs/evidence/run-card.json`. See `research/H86_RESULTS.md`.)

[Executive summary and submission instructions](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/executive-summary.html) · [Research and source review](research/REVIEW.md) · [Machine-readable run card](docs/evidence/run-card.json)

History: the previous session ended as a negative *preflight* (no data, no lane).
This session (2026-10-22) restored the hash-pinned competition rasters
(including the 419 MB 19-band feature raster) and a 14-raster hash-verified
uniqueness registry from owner mirrors (integrity only, not organizer
authentication), preregistered five hypotheses (`research/h86-hypotheses.md`),
ran the top lane **H86-1** through leakage canaries and buffered
hide-and-recover with the unmodified shared evaluator/writer, and generated a
unique, format-valid candidate TIF. Automated gates rejected it: its surface
has no measurable skill beyond random dot coverage. **Do not submit it, the
sample TIFF, or any upstream historical raster.** No weekly slot was used.

## Starting brief — read at the beginning of every session

The following is a **condensed operational record** of the owner's long request, not a verbatim transcript. The original conversation remains the complete prompt. Read this AND research/REVIEW.md before work. Unfulfilled requirements remain explicit blockers rather than completed checkboxes.

- Review previous work first; maximize probability of winning through evidence, and own the outcome end to end. Do not trade scientific integrity for an optimistic claim.
- Generate a UNIQUE competition-format single-band GeoTIFF, never copy an earlier submission except for education. Make download and readiness status obvious at the beginning of the site. Supply a distinct name and note of at most 140 characters.
- Work autonomously through implementation, bug/edge-case review and final requirements review. Research official free data, preserve provenance and links, flag irregularities, distinguish verified facts from hypotheses. Explain access limits and next steps honestly.
- Parallel-run lane: no single method paragraph was present in the supplied request; this session resolved that explicitly by preregistering five ranked hypotheses and assigning itself the top one as the single lane paragraph (`research/h86-hypotheses.md`). Future sessions must not quietly inherit H86-1: it is falsified. Pick one new lane, in writing, before experiments. Surface and final-dot checks must stop on rank correlation >0.90 or >70% dots within 3 px of any registered raster.
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
.venv/bin/python scripts/restore_data.py --include-features
.venv/bin/python scripts/fetch_registry.py
.venv/bin/python scripts/run_h86.py surface
.venv/bin/python scripts/run_h86.py canary
.venv/bin/python scripts/run_h86.py holdout 38000 e2_b38000
.venv/bin/python scripts/run_h86.py holdout 44090 e3_b44090
.venv/bin/python scripts/run_h86.py final 38000 e2_b38000   # refuses overwrite; new timestamped name
.venv/bin/python scripts/run_h86.py sgmc
.venv/bin/python scripts/run_h86.py card e2_b38000 e3_b44090
.venv/bin/python scripts/audit.py
.venv/bin/python -m unittest discover -s tests -v
```
(SGMC stage also needs the manifest's `ext_derived_sgmc_faults_100m_u8` under
`data/external/`; see `research/H86_RESULTS.md` §6 for its dilation caveat.)

`restore_data.py --include-features` can also recover the hash-pinned raw mirrored feature TIFF. This is NOT the required shared cached stack; the option does not unblock experimentation. Large inputs are ignored in Git. No GPU is required for the audit. Official reference training supports CPU; GPU improves speed.

### What exists

- `vendor/gems57/`: shared upstream tools, byte-identical to the pin in `research/template_pin.json`.
- `research/upstream/`: owner-repository audit snapshots and official reference README; historical metrics are not fresh evaluations.
- `scripts/restore_data.py`: pinned mirror restoration with SHA and byte-length verification.
- `scripts/audit.py`: negative run card with real grid checks, separate from unrun candidate validation.
- `tests/`: safety tests, not geological validation or score estimates.
- `docs/`: Pages site, executive summary and downloadable evidence, not a fake submission button.

### Next session, in order

1. Do not resurrect H86-1 (falsified on two instruments). Preregister one new
   lane attacking the *surface*: H86-3 catalogue-distance-debiased PU or
   native-resolution LiDAR en-echelon scarplet chains are the ranked options
   in `research/h86-hypotheses.md` §7 of `research/H86_RESULTS.md`.
2. Screen any new surface on catalogue-hidden **and** SGMC off-catalogue
   proxy jointly (must beat spaced random on both) before any slot talk;
   obtain raw `sgmc_faults_100m.tif` with its official source so the proxy
   matches the vendor derivation byte-for-byte.
3. Keep the proven emission doctrine (2.8 px dotted spacing, ≤2 px
   catalogue-flank exclusion from visible faults, ~38–44k dots, all-finite
   zeros through the shared writer). Expand the uniqueness registry beyond
   the accessible 14 rasters before claiming completeness.
4. Only after gates pass: separate selector checks the live weekly quota;
   bind any organizer receipt to the file SHA before using the words
   ORGANIZER-CONFIRMED.
