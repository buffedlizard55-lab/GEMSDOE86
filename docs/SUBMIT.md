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

Nothing is built yet. The 419 MB feature stack restores in ~22 s and verifies against its pin,
so SNAP or RELIEF can be built and gated next session. Build one axis, preregister its
mechanism/confounder/falsifier in `SLOT_PLAN.md` before writing the raster.

## MASS variants — built and gated, **not recommended for a slot** (both predicted negative)

Upload, if the human overrules the default in [SLOT_PLAN.md](../SLOT_PLAN.md), the `-zeros`
twin; the `-nan` twin carries identical dots. TIFFs are local-only and gitignored.

| Variant | Primary file (NaN outside) | sha256 | Fallback (zeros) | sha256 |
|---|---|---|---|---|
| MASS −10 % (drop traversal-tail) | `releases/mass/h33-h33-2-b2-massminus10-20261023-42b4c5c8.tif` | `6614be7425dbbf00403ac8491fb38ab365d8947b26b759245f29197f5ab1abde` | `releases/mass/h33-h33-2-b2-massminus10-20261023-42b4c5c8-zeros.tif` | `42b4c5c8f7087b8699057d888bdd00c775c4812c8ed37b5abf6d1a351aae2779` |
| MASS +10 % (add next-ranked cells) | `releases/mass/h33-h33-2-b2-massplus10-20261023-a5888761.tif` | `45e8ac0aee4ca237552d6c71698b82f87698f566f03c6da7d9228917c58e8347` | `releases/mass/h33-h33-2-b2-massplus10-20261023-a5888761-zeros.tif` | `a5888761dd03239e21d71c125649f7da4bd4480ae1a83106854dd7cd49eef481` |

Form notes (≤140 chars): minus (107): `R0 h33-h33-2-b2 MASS-10%: drop 3765 lowest-priority
traversal-tail dots, 33889 left; predicted -0.003 MODEL`; plus (115): `R0 h33-h33-2-b2
MASS+10%: add 3765 next-ranked H19-5 cells, d>2px off catalogue, 41419 dots; predicted
-0.006 MODEL`. Re-verify any time: `.venv/bin/python scripts/build_mass_axis.py --measure`
(gates re-read from disk) and `.venv/bin/python scripts/build_ledger.py --check`.

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
