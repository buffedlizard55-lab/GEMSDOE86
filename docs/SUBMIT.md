# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** TOP_PUBLIC, remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Full plan and decision tree: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms); hashes below are the authority.

## Slot 1 — PRUNE ≤ 3.000 px, pure deletion (nested ladder, PR #29)

- Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros`
- Upload: `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
- SHA-256: `a438e92b…` — take the full digest from `releases/…-a438e92b-zeros.json`.
- 35,483 dots (R0 minus all 2,171 dots within 3.0 px of the catalogue), 5.77 % changed.
- Prediction: **+0.004 (MODEL)**, band −0.004 … +0.013. Receipt: `evidence/prune_ladder.json`.
- Nested rungs at ≤ 2.2361 px and ≤ 2.8284 px exist in the same ladder if the human prefers a
  shallower first edit.

## Slot 2 — a new prediction surface (not a prune rung)

**SNAP is now built** (three files, `releases/snap/`); **CONCENTRATION** is the recommended next
build. The 419 MB feature stack restores and verifies against its pin `4371c82e…`, so RELIEF and
CONCENTRATION can be built and gated next session. Build one axis, preregister its
mechanism/confounder/falsifier in `SLOT_PLAN.md` before writing the raster.

### SNAP files, if the human wants the axis closed (none is predicted to beat R0)

| Variant | Primary file (NaN outside) | zeros sha256 | Fallback (zeros) | Dots moved |
|---|---|---|---|---|
| SNAP combo (23.3 %) | `releases/snap/h33-h33-2-b2-SNAP-combo-20261023-dba98049.tif` | `dba98049de46d8092d7a499a09add51c1e9a56ba9b52f012d3bcf9197763e6d7` | same name `-zeros.tif` | 8,770 |
| SNAP gravity (7.7 %) | `releases/snap/h33-h33-2-b2-SNAP-gravhg-20261023-701aada8.tif` | `701aada83513a213bc44bf488b318f01149585b466e0bb2ba3a4eb87d447560c` | same name `-zeros.tif` | 2,915 |
| SNAP magnetic (34.0 %) | `releases/snap/h33-h33-2-b2-SNAP-tmihg-20261023-ede24e24.tif` | `ede24e246056cfef5428682e52bd1df9ba0edd9601aeafa377db2ccd3e25b1c4` | same name `-zeros.tif` | 12,809 |

Submission names are the file names without `.tif`; notes are in each `-zeros.json`
(`note`, ≤ 140 chars). Predictions: **−0.004 / −0.002 / −0.006 MODEL**, bands inside ±0.03 —
upload one only to *measure* the axis, never expecting a gain. Full cards:
[`ledger/variant-cards.md`](../ledger/variant-cards.md); measurements: `evidence/snap_axis.json`.
Truth for all three: 37,654 dots (count preserved), zero catalogue mass, ≥ 3 px collar respected for
every *moved* dot, `gems57.validate` + `format_report` PASS on the `-zeros` twin.

## Cheap defaults, already built and gated (only if slot 2 is not ready)

| Variant | Primary file (NaN outside) | sha256 | Fallback (zeros) | sha256 |
|---|---|---|---|---|
| PRUNE ≤ 4 px | `releases/h33-h33-2-b2-prune4-20261023-de4c2a98.tif` | `e198b768b5a19d7e08e33de14ad1ec03425154db1acd81fad5db3b4b7e9715cd` | `releases/h33-h33-2-b2-prune4-20261023-de4c2a98-zeros.tif` | `de4c2a98bd13c518697442655c0a3980ba51d6712216c2ea0e330dc01924ebc5` |
| PRUNE ≤ 3 px, equal count relocated | `releases/refill/h33-h33-2-b2-prune3r-20261023-8c20bd7e.tif` | `9542efacb60a4e8c9155b1e9c000ce7e33f43f7e413ad2a5883304b413906682` | `releases/refill/h33-h33-2-b2-prune3r-20261023-8c20bd7e-zeros.tif` | `8c20bd7eeaf1a1518b7d7f4711613169bd1ab00c4a4b3d74c87bf2b70d552c2e` |

Predictions: PRUNE ≤ 4 px **−0.008 MODEL** (111-char note: `prune4 — parent h33-2-b2
(0.2778); drop 3825 dots at 2<d<=4px from catalogue; predicted -0.008 (MODEL, +-0.014)`);
relocated-collar **−0.003 MODEL** (113-char note: `prune3r — parent h33-2-b2 (0.2778); same
count, collar moved past 3px, mean move 1.14px; predicted -0.003 (MODEL)`). Neither is
predicted to help; they are rehearsals.

Naming note: the pair is named once — the NaN twin (`…-<zeros8>.tif`) carries the **zeros**
digest, the zeros twin is `…-<zeros8>-zeros.tif`, and the receipt is `…-<zeros8>-zeros.json`.

**Do not upload:** `…-prune3-…-3eb29af5` (withdrawn — identical dot set to slot 1's
`le3p000`, IR-86-PRUNE-08; its local copies are deleted) or `…-prune3-…-01d57649` (same
`(PRUNE, 3)` pair; a control for the mass question, not a candidate).

## Format receipt (measured on disk, brief §6 MUST gates)

Common to every file above — re-read from disk after writing:

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
| Exact-hash duplicate of any file on disk or in the ledger | none |

The `-zeros` twins additionally pass `vendor/gems57/validate.py` (`all_checks_passed = True`)
and `gems57.gates.format_report` (`ok = True`). The `-nan` twins fail that vendored validator
**by its all-finite policy** — their NaN cells all lie outside the footprint, which is what the
brief asks for (IR-86-PRUNE-07). The portal previously rejected an upload with *"Predicted
values must be in range [0, 1]"*, so if `-nan` is rejected on range, switch to the `-zeros`
twin within the same slot attempt: the twins carry identical dots.

Release TIFFs are gitignored (public repo, unchecked data-use terms), so the digests above are
the authority. Re-run the checks any time: `python scripts/prune_collar.py --measure`
(deterministic, seed 20261023) and `python scripts/build_ledger.py --check`.

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`,
`evidence_class=RECEIPT`) and re-read `SLOT_PLAN.md` for what the number licenses. Any live
change under **0.01** is treated as no evidence.
