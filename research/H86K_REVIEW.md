# H86K-STC review (2026-10-25) — NEGATIVE, DO NOT SUBMIT

- Hypothesis/mechanism/mimic, 5 ranked candidates: `research/H86K_HYPOTHESES.md`.
- Why prior best (owner-claimed 0.2778, no organizer receipt in repo) scores high:
  sparse dotted binary fields concentrate the 300 m triangular-kernel credit
  (alpha 0.2 / beta 0.8) on off-catalogue fault continuations and avoid paying
  FP on continuous surfaces; continuous/soft rasters waste FP mass. This is an
  inference from repo fleet measurements, NOT an organizer-confirmed explanation.
- H86K-STC: canary AUCs 0.524–0.538 (pass ≤0.90); HOLDOUT-DTI (gems57-pooled-hide-v2,
  22,641 withheld positives) = 0.0428, fold-bootstrap 95% CI [0.0383, 0.0466],
  vs tmi_hg-only control 0.0458 — pre-registered promotion rule FAILED.
- Uniqueness (local 53 rasters): worst sampled Spearman ρ = 0.023 (≤0.90);
  worst 3px dot overlap vs dotted rasters = 0.52 (≤0.70); 0.841 vs the
  4.2M-px full-support `faulthalo` continuous raster is the known literal
  full-support witness blocker, not a dotted-registry duplicate.
- Format: single-band float32, EPSG:32611, 3730×3292, sample transform,
  values exactly {0,1}, no NaN/Inf, 40,000 dots, 0 on catalogue — the
  "Predicted values must be in range [0,1]" portal error class is excluded.
- Verdict: **negative / DO NOT SUBMIT**, 0 slots used. File is downloadable
  for audit only. No claim it beats 0.2778 or 0.4413 (leaderboard, unverified here).

## Independent revalidation (2026-10-25, session `arena/234c24b9`)

Re-read `releases/h86k/gems86-h86k-stc-40000dots-20261025T131720Z-61680c22-zeros.tif`
with rasterio directly (not via the writer receipt): SHA-256
`e4d00084b219e210c10e5ccd539ab1ee1a3c2315ac6188f40b2a256e90f9aa11` matches the run
card; single-band float32; EPSG:32611; 3730×3292; transform identical to
`data/bridge/sample_submission.tif`; all finite; unique values exactly {0.0, 1.0};
40,000 positives; 0 on `existing_faults.tif`. Evidence:
`docs/evidence/h86k-revalidation-20261025.json`. Full test suite: 957 passed,
24 skipped. Irregularities flagged (`IRREGULARITIES.md`): artifact absent from
Pages download inventory (`check_site.py` fail-closed — not bypassed), rerun
blocked by absent restored `data/bridge/training_features.tif`, stale
`docs/downloads/` path inside the releases receipt.
