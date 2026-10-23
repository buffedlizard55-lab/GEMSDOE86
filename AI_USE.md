# AI_USE — generative-AI disclosure (required by the competition rules)

Rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf (3 scored submissions per week per entity,
one final file, reproducible code, generative-AI disclosure). This file records what the AI
agent wrote and what the human decided, for the 2026-10-23 AXIS session.

## What the AI agent wrote

- `src/gems86_axis/` — the single-axis variant builders (`prune`, `concentration`, `snap`),
  the block-prior and block-density measures, the grid I/O for the two submission encodings,
  and the MUST-pass gates.
- `scripts/build_axis_variants.py` — the pipeline that verifies input pins, builds the
  variants, writes both encodings, runs every gate from the file re-read on disk, and emits
  `evidence/axis_variants.json`.
- `scripts/build_ledger.py` — assembles `ledger/submissions.csv` from the transcribed history
  and this session's builds.
- `scripts/restore_axis_inputs.py` — restores the hash-pinned inputs into the gitignored
  `.cache/`, verifying SHA-256 and byte count before use and aborting on any mismatch.
- `tests/test_axis_variants.py` — the metric-algebra unit test the brief requires
  (`DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)` against the shared template metric, plus the
  isolated-dot break-even `k > α·DTI`), and the variant invariants.
- `research/AXIS_MECHANISM_CARDS.md`, `SLOT_PLAN.md`, `IRREGULARITIES.md`, `docs/SUBMIT.md`,
  this file, and the README `CURRENT STATE` block.

No AI-written code submits anything, logs in anywhere, scrapes a leaderboard, or contacts
drivendata.org or dropbox.com. The only network calls are `gh api` / `api.github.com` blob
fetches of owner-published mirrors and the PyPI install of the pinned requirements.

## What the human decided

- The AXIS set for this session: **PRUNE, CONCENTRATION, SNAP** (chosen from the brief's wk1–2
  default order, over three alternatives offered).
- **TOP_PUBLIC = 0.3195**, taken from this repo's `PROMPT.md` archive and accepted as an
  undated owner CLAIM rather than a receipt.
- **Slots left this rolling week: 3 of 3.**
- **Data scope:** restore the external GeoDAWN/DEM mirror set (~100 MB) but *not* the 419 MB
  feature stack. That single decision is why MASS and RELIEF are unbuilt and why the format
  validator's footprint checks are covered by a direct re-read instead (see
  `IRREGULARITIES.md` items 5 and 7).
- Nothing has been submitted. Promotion to a weekly slot is the human's step, from their own
  registered account.

## Reproducibility

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/restore_axis_inputs.py \
    --ids ext_geodawn_extensions_u8 ext_geodawn_rad_u8 ext_topo_10m_derived_100m_u8 \
          ext_dem10_chi_100m_i16 ext_geodawn_extensions_json ext_geodawn_rad_json \
          ext_derived_sgmc_faults_100m_u8 scored_h19_5 scored_d28_unscored
.venv/bin/python -m pytest tests/test_axis_variants.py -q
.venv/bin/python scripts/build_axis_variants.py
.venv/bin/python scripts/build_ledger.py
```

The builders are deterministic: no RNG is used anywhere in `src/gems86_axis/`, and every
tie is broken by `(row, col)`. Re-running reproduces the same dot sets and the same
dot-set tokens (`e4027684`, `2b883f2d`, `6ec42a92`) — verified this session by rebuilding
PRUNE and SNAP twice after unrelated code changes and getting identical tokens.

Every input carries a SHA-256 pin in `registry/data_manifest.json`; the restore receipt is
`.cache/axis_input_receipt*.json` (gitignored) and the pins are re-verified at build time by
`build_axis_variants.py`, which aborts on mismatch. The build logs the git SHA of the checkout
into each run card (`evidence/axis_variants.json → variants[].git_sha`).

## Limits of this session's evidence

- No live score was produced or observed. Every predicted change is **MODEL**.
- The catalogue hide-and-recover PROXY was **not run**: the shared evaluator scores against
  lidar-covered positives inside held blocks, and the lidar raster is excluded by the brief
  unless the human supplies it. Recorded as NOT RUN, not as a pass.
- The leakage canary was **not run**: it needs a labelled holdout fit, which needs the
  declined feature stack. Recorded as NOT RUN.
- The SGMC control was not re-measured this session.
