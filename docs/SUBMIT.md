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

## Slot 2 — CONCENTRATION on 5 km blocks (not built yet)

Not built. Preregister block size, direction (low-prior → high-prior) and the block-density CV
target in `SLOT_PLAN.md` before writing the raster, and record the CV before/after. MASS stays
blocked: R0's per-dot ranking cannot be recovered from a rebuild (IR-86-PRUNE-02).

## Slot 3 — SNAP, built and gated, predicted **negative**

| Variant | Primary file (NaN outside) | sha256 (NaN twin) | Fallback (`-zeros`) | sha256 (zeros twin) | Prediction |
|---|---|---|---|---|---|
| `SNAP ≤ 1.0 px` mixed | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r1p000-20261023-0e09c2b7.tif` | `b8f215b3d858ad1efd6737ae19521deb6b700cd974f769d778251edc3b80c3d0` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r1p000-20261023-0e09c2b7-zeros.tif` | `0e09c2b7800c302a7c840f0c38b3b3808f82eca242d7292d547f68a5098404be` | **−0.004 MODEL** (−0.012…+0.004) |
| `SNAP ≤ 2.0 px` mixed | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-20261023-e7473403.tif` | `c9f4042f71add006089f79634468488ed2b08183e0505a4174a688f9ee1e916b` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-20261023-e7473403-zeros.tif` | `e74734031f478edafc55017d0002e72fe1930dd32c237c9341833732028f5743` | **−0.006 MODEL** (−0.020…+0.006) |
| `SNAP ≤ 2.0 px` gravity-only | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-grav-20261023-17fe2f15.tif` | `a9cc8fdadbcb31d7c8f19a2adeed56bf7034ac2633bdf64af7767f8023c23218` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-grav-20261023-17fe2f15-zeros.tif` | `17fe2f1573bb35d557d5a6c79a52df743b211f57be0ed5888fbf0ef5dd1d9823` | **−0.004 MODEL** (−0.016…+0.006) |
| `snapr2g10` gain-gated ≤ 2 px (second session; the cheapest SNAP probe) | `releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869.tif` | `32c1e4e99444abafd35165666e34efc9fda3a15c664dea4e7c809d06ae613f52` | `releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869-zeros.tif` | `8ca1d8690aa835c8e8e823db2965a5ca357c9132452ae5a205403a6380082d2e` | **−0.001 MODEL** (−0.007…+0.008) |

Why they are predicted to lose: 97–99 % of dots move, but the random-response **null control**
scores the same catalogue proxy (+0.0001 vs −0.0012) and smoothing makes it worse. Uploading one
of these buys a test of an unmeasured *live* hypothesis — "new faults sit at potential-field
edges, not where the field put its dots" — not an expected gain. If the human does not want to
spend a weekly slot on a predicted-negative probe, skip slot 3 and go to slot 2.
Notes are 99–106 chars each and are stored inside each `-zeros.json` receipt as `note`
(r2g10: 91 chars, `R0 h33-h33-2-b2 SNAP r2g10: dots <=2px to edge if gain>=0.10, 37654 dots; pred -0.001 MODEL`).
The second session's `snapr1`/`snapr2` duplicate PR #31's pairs and are **withdrawn — no
raster was written** (IR-86-SNAP-05); there is nothing to upload by those names.

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
| SNAP parent-diff | count exact 37,654 → 37,654; only positions changed; catalogue exclusion unchanged (min distance 2.236 px) |

The `-zeros` twins additionally pass `vendor/gems57/validate.py` (`all_checks_passed = True`)
and `gems57.gates.format_report` (`ok = True`). The `-nan` twins fail that vendored validator
**by its all-finite policy** — their NaN cells all lie outside the footprint, which is what the
brief asks for (IR-86-PRUNE-07). The portal previously rejected an upload with *"Predicted
values must be in range [0, 1]"*, so if `-nan` is rejected on range, switch to the `-zeros`
twin within the same slot attempt: the twins carry identical dots.

Release TIFFs are gitignored (public repo, unchecked data-use terms), so the digests above are
the authority. Re-run the checks any time: `python scripts/prune_collar.py --measure` (deterministic, seed
20261023), `python scripts/run_snap_axis.py` (deterministic; rebuilds R0 byte-exactly, then the
three SNAP rasters — the sha8 values are reproducible), `python scripts/build_r0_snap.py --build`
(gain-gated session; releases only `snapr2g10`, identical sha256) and
`python scripts/build_ledger.py --check`.

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`,
`evidence_class=RECEIPT`) and re-read `SLOT_PLAN.md` for what the number licenses. Any live
change under **0.01** is treated as no evidence.
