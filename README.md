# GEMSDOE86 — audited fault-prediction research

## 🔴 TWO CANDIDATES GENERATED — DO NOT SUBMIT EITHER (both failed the holdout gate)

**Download (inspection only):** [`docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif`](docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif) · SHA-256 `cf4ab3403d28b085018b01221487e58e20fe2697cf17e96be739bd87a91a5962` · [Site / readiness dashboard](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/) · [Executive summary: exactly how to submit](docs/executive-summary.html) · [Run card](docs/evidence/run-card.json)

Lane **H86-RMRB** (declared this session — see irregularity note in the run card): GeoDAWN radiometric mixing-residual boundaries × RTP magnetic-edge persistence. The file is **byte/pixel-distinct and format-valid** (shared writer + validator PASS: finite [0,1], EPSG:32611, 3730×3292, 0 on-catalogue dots; surface ρ ≤0.0004 vs the 12-raster local registry) — but the shared uniqueness checker returns **unique=false / stop_required=true** (literal >70% 3-px dot-overlap gate fires vs the saturating 13GEMSDOE lattice raster; ρ=0.0003, Jaccard=0.009), so it is **not uniqueness-cleared** but **HOLDOUT-DTI 0.0420 [0.0369–0.0467]** (gems57-pooled-hide-v2, 22,641 withheld positives) **does not beat the same-instrument incumbent benchmark 0.1011 [0.0856–0.1167]**. Per protocol, **no weekly slot may be spent on it**; verdict **negative** (a deliverable). No ORGANIZER-CONFIRMED score exists. Historical numbers in the brief (0.2778/0.4413/0.3195) are unverified owner reports without receipts — see `research/REVIEW.md`. Reproduce: `.venv/bin/python scripts/restore_lane_data.py && .venv/bin/python scripts/run_lane86.py`.

**Lane H86-1 (parallel session, PR #9):** straight-edge 2-of-5 corroboration
(RTP/gravity/conductivity/basement-depth/DEM), 2.8 px-spaced dotted emission,
200 m catalogue-flank exclusion. Also format-valid and distinct (surface
ρ ≤0.070 vs 14 registry rasters; vs H86-RMRB ρ 0.013 — see
`docs/evidence/h86_crosslane_vs_rmrb.json`) but **HOLDOUT-DTI 0.0463
[0.0372–0.0560]** (gems57-pooled-hide-v2, 22,893 withheld positives) vs
spaced-random 0.0458 — no skill beyond coverage; below random on the SGMC
auxiliary proxy. **Do not submit:** [`docs/downloads/gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif`](docs/downloads/gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif) · SHA-256 `5d135088eb703e6d6f74f28b66b531145b290eac4fb542d6b5d5893ebba2f6d5` · run card `docs/evidence/h86_run_card.json` (embedded in `run-card.json`). Analysis incl. why the 0.2778-family file worked: `research/H86_RESULTS.md`; preregistration: `research/h86-hypotheses.md`. Reproduce: `.venv/bin/python scripts/restore_data.py --include-features && .venv/bin/python scripts/fetch_registry.py && .venv/bin/python scripts/run_h86.py {surface,canary,holdout,final,sgmc,card}` (stages documented in the script).

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
