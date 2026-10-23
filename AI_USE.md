# AI_USE — disclosure of what the AI wrote and what the human decided

Required by the competition rules (reproducible code, generative-AI disclosure). This file covers the
SNAP session of 2026-10-23 only; earlier sessions are described in their own records.

## Human decisions (not made by the AI)

| Decision | Who | Where it is recorded |
|---|---|---|
| AXIS for this session = **SNAP**, response family **magnetic edges (tmi_hg / tc)** | human, from the options put to them | this file; `SLOT_PLAN.md` header |
| Which weekly slots are spent, and the uploads themselves | human, from their own account | human-owned columns of `ledger/submissions.csv` |
| `receipt_score` / `receipt_date` values | human, copied from the submission page | `ledger/submissions.csv` |
| Whether to keep the SNAP lane open after the first two live results | human | `SLOT_PLAN.md` decides-it table |

The AI never logged in, never fetched drivendata.org, never contacted dropbox.com, never submitted,
and never wrote code capable of doing any of those.

## AI-written, in this session

* `scripts/build_snap_variants.py` — input hash verification, R0 recipe re-derivation, response
  fields, the placement engine, the gate set, the report-only proxy/canary readouts, and the writer
  for `releases/` (NaN and zeros twins).
* `scripts/build_ledger.py` — merges the transcribed history with this session's rows, preserving
  human-entered receipt columns on re-run.
* `tests/test_snap_variants.py` — the invariant tests (count, catalogue, spacing, cap, determinism,
  on-disk format).
* `registry/preregistration_snap.json` — the rule, axis values and analysis plan, written before any
  variant was built or scored.
* `SLOT_PLAN.md`, `docs/SUBMIT.md`, `IRREGULARITIES.md`, the README CURRENT STATE block, and the
  mechanism-card prose inside the build script.

## AI-written constants that the human should sanity-check

1. `SMOOTH_SIGMA_PX = 1.0`, `GAIN_GATE = 0.25` σ — chosen after a jitter diagnostic (IR-86-SNAP-02),
   fixed before scoring, not tuned on any score.
2. `SPACING_FLOOR_PX = 2.828` — copied from the parent's own measured nearest-neighbour floor, so the
   edit cannot change emission spacing.
3. The three predicted-change ranges. These are MODEL projections with no receipt behind them and are
   centred below the 0.01 evidence floor on purpose.

## Data and models

No model was trained. No new external data was fetched: every raster used is hash-pinned in
`registry/data_manifest.json` and verified on use. The H19-5 ranking field is owner-mirrored
competition-side output (pinned sha `ec1f9b56…`), used only for a readout here and reserved for the
MASS axis later.
