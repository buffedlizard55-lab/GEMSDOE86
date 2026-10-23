# SUBMIT — exact instructions for the three PRUNE rasters

**Read first:** nothing in this repository is approved for a slot. This page gives the
human the file, the name, the note and the format receipt so the upload takes one minute.
Promotion to a slot is the human's decision (3 scored submissions per rolling week, one
final file). `TOP_PUBLIC` is still unset, so "beat the public leaderboard" cannot be
evaluated yet.

## 1. File

Upload **one** of the two twins of one variant. They contain exactly the same dots; only the
out-of-footprint fill differs.

| Slot order | Variant | Upload this file | sha256 |
|---|---|---|---|
| 1 (default) | `prune3` | `releases/h33-2-b2-prune3-20261023-3eb29af5-nan.tif` | `3eb29af50244daada65c70d433be9c0507fd4422b358c54c7e7eebc4485f0501` |
| 1 fallback | `prune3` | `releases/h33-2-b2-prune3-20261023-4bd30478-zeros.tif` | `4bd3047844fcff384245af58b76906caf9acd48ba356ff37f145225359e4838b` |
| 2 (conditional) | `prune4` | `releases/h33-2-b2-prune4-20261023-e198b768-nan.tif` | `e198b768b5a19d7e08e33de14ad1ec03425154db1acd81fad5db3b4b7e9715cd` |
| 2 fallback | `prune4` | `releases/h33-2-b2-prune4-20261023-de4c2a98-zeros.tif` | `de4c2a98bd13c518697442655c0a3980ba51d6712216c2ea0e330dc01924ebc5` |
| 3 (conditional) | `prune3r` | `releases/h33-2-b2-prune3r-20261023-9542efac-nan.tif` | `9542efacb60a4e8c9155b1e9c000ce7e33f43f7e413ad2a5883304b413906682` |
| 3 fallback | `prune3r` | `releases/h33-2-b2-prune3r-20261023-8c20bd7e-zeros.tif` | `8c20bd7eeaf1a1518b7d7f4711613169bd1ab00c4a4b3d74c87bf2b70d552c2e` |

Use only **one** file per slot. Do not upload both twins of the same variant: they score
identically and would burn two slots (≥ 8 historical slots were lost that way).

## 2. Name (≤ 140 characters)

```
h33-2-b2-prune3-20261023-3eb29af5-nan
h33-2-b2-prune4-20261023-e198b768-nan
h33-2-b2-prune3r-20261023-9542efac-nan
```

## 3. Note (≤ 140 characters, form note: parent; change; predicted change)

```
prune3 — parent h33-2-b2 (0.2778); drop 2171 dots at 2<d<=3px from catalogue; predicted -0.003 (MODEL, +-0.007)
```

```
prune4 — parent h33-2-b2 (0.2778); drop 3825 dots at 2<d<=4px from catalogue; predicted -0.008 (MODEL, +-0.014)
```

```
prune3r — parent h33-2-b2 (0.2778); same count, collar moved past 3px, mean move 1.14px; predicted -0.003 (MODEL)
```

## 4. Format receipt (measured on disk, brief §6 MUST gates)

Common to all six files — re-read from disk after writing:

| Gate | Measured |
|---|---|
| Bands / dtype | 1 / `float32` |
| CRS | `EPSG:32611` (= `sample_submission.tif`) |
| Shape | 3730 × 3292 |
| Transform | `(100, 0, 243350, 0, -100, 4508550)` (= template) |
| Values | inside `[0,1]`, unit mass where emitted |
| NaN inside footprint | none |
| Outside footprint | `NaN` for `-nan` files, `0` for `-zeros` files |
| Dots on mapped catalogue | **0** in every file |
| Exact-hash duplicate of any file on disk | none |

Cross-check with the repo's own tooling: the three `-zeros` twins pass
`vendor/gems57/validate.py` and `gems57.gates.format_report` against the template; the three
`-nan` twins fail that validator **by its all-finite policy** (their 7,111,787 NaN cells are
all outside the footprint, which is what the brief asks for). That is IR-86-PRUNE-07, not a
defect — but it is the reason the `-zeros` twin is the safer upload.

Per file: `evidence/prune_axis_20261023.json` → `variants[*].validation_nan` and
`validation_zeros`. Re-run at any time with
`python scripts/prune_collar.py --measure`; the build is deterministic (fixed seed
20261023), so it re-writes byte-identical files and re-checks them from disk.

The portal rejected a previous upload with *"Predicted values must be in range [0, 1]"*.
The vendored validator (`vendor/gems57/validate.py`) only passes the all-finite form, so if
the `-nan` upload is rejected on range, switch to the `-zeros` twin **within the same slot
attempt** — the twins carry identical dots.

## 5. After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `receipt_date`,
`evidence_class=RECEIPT`) and re-read `SLOT_PLAN.md` §"Next three slots" for what the number
licenses. Any live change under **0.01** is treated as no evidence.
