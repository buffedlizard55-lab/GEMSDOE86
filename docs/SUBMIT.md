# SUBMIT — the exact upload sheet for this session's files

Local format pass is **not** organizer acceptance. Nothing below has a leaderboard receipt; every
number in the lane is a CLAIM, a PROXY or a MODEL until `receipt_score` is filled in
`ledger/submissions.csv` from the submission page.

## Which file, which twin

Upload **one** file per slot. Both twins of a variant contain the identical dot set; they differ only
outside the footprint (NaN vs zeros) and are therefore expected to score identically (the ledger
records ≥ 8 such twin pairs).

| Slot order | File to upload | Twin (fallback) | Name = the file's stem | Note (≤ 140 chars) |
|---|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-snap-cons2-20261023-43829550.tif` | `…-43829550-zeros.tif` | `h33-h33-2-b2-snap-cons2-20261023-43829550` | `R0 h33-2-b2; SNAP 2px to tmi_hg+|tmi_vg| consensus peak, 54.7% moved, 37654 dots; MODEL +0.005 (range -0.005..+0.015); UNSCORED` |
| 2 | `releases/h33-h33-2-b2-snap-hg2-20261023-718658bc.tif` | `…-718658bc-zeros.tif` | `h33-h33-2-b2-snap-hg2-20261023-718658bc` | `R0 h33-2-b2; SNAP 2px to tmi_hg peak, 43.4% moved, 37654 dots; MODEL +0.004 (range -0.005..+0.015); UNSCORED` |
| 3 (held) | `releases/h33-h33-2-b2-snap-vg2-20261023-b5776416.tif` | `…-b5776416-zeros.tif` | `h33-h33-2-b2-snap-vg2-20261023-b5776416` | `R0 h33-2-b2; SNAP 2px to |tmi_vg| flank peak, 48.3% moved, 37654 dots; MODEL +0.003 (range -0.008..+0.015); UNSCORED` |

## Format receipt (measured on the files as re-read from disk)

| Check | Parent R0 | snap-hg2 | snap-vg2 | snap-cons2 |
|---|---|---|---|---|
| CRS = EPSG:32611 (matches `sample_submission.tif`) | yes | yes | yes | yes |
| shape 3730 × 3292, transform (100, 0, 243350, 0, −100, 4508550) | yes | yes | yes | yes |
| dtype float32, single band | yes | yes | yes | yes |
| values in [0, 1] | yes | yes | yes | yes |
| no NaN inside the footprint | yes | yes | yes | yes |
| NaN outside footprint (primary) / zeros outside (twin) | zeros | yes / yes | yes / yes | yes / yes |
| positive mass on the catalogue | 0 | 0 | 0 | 0 |
| dot count | 37,654 | 37,654 | 37,654 | 37,654 |
| nearest-neighbour floor preserved | 2.828 px | 2.828 px | 2.828 px | 2.828 px |
| sha256 | `c55bafc4…` | `718658bc…` | `b5776416…` | `43829550…` |

Measured by `scripts/build_snap_variants.py` (`evidence/snap_variants.json`) and repeated by
`tests/test_snap_variants.py`. Re-run both before uploading:
`python scripts/build_snap_variants.py --skip-proxy` then `python -m pytest -q tests/test_snap_variants.py`.

## After uploading

1. Copy the score **from the submission page receipt** into `ledger/submissions.csv`
   (`receipt_score`, `receipt_date`) and change `evidence_class` to `RECEIPT`.
2. Record what the score decides in `SLOT_PLAN.md` before spending the next slot.
3. A live change under 0.01 is no evidence. Do not chain a second SNAP slot on a ±0.005 result
   unless the third slot has nothing better to test.

## Not to be done here

No login, no scrape, no automated upload, no leaderboard fetch by this repository. The account holder
submits from their own registered account.
