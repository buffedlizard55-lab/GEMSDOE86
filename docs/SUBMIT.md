# SUBMIT — what to upload, in what order, and the receipt to paste back

Nothing in this repository submits anything. The human uploads from their own registered
DrivenData account. One entity gets **3 scored submissions per rolling week** plus one final
file chosen blind.

Submission form: a single-band GeoTIFF (`.tif`) or a `.zip` containing one GeoTIFF, matching
the submission format's CRS, shape and geotransform, plus an optional note.

## Order

Spend the slots in this order, and paste each receipt score back into
`ledger/submissions.csv` (`receipt_score`, `receipt_date`). `SLOT_PLAN.md` says what each
outcome changes.

### Slot 1 — PRUNE `collar3px`

- **File:** `releases/gems86-h33-2b2-prune3-20261023-e4027684.tif`
  (fallback twin: `gems86-h33-2b2-prune3-20261023-e4027684-zeros.tif` — identical pixels,
  zeros instead of NaN outside the footprint)
- **Name:** `gems86-h33-2b2-prune3-20261023-e4027684`
- **Note (97 chars):**
  `GEMSDOE86 h33-2b2 PRUNE collar3px | 37654 dots, 11.531% changed vs R0 | token e4027684 | UNSCORED`
- **Format receipt:** PASS — single band, float32, EPSG:32611, 3730×3292, transform
  `|100, 0, 243350| |0, −100, 4508550|`, all values in [0, 1], no NaN inside the footprint,
  NaN outside, 0 dots on catalogue pixels, minimum catalogue clearance 3.162 px,
  37,654 emitted cells.
- **SHA-256 (nan form):** `6286ebe52628a80ceefdbbb88d307376854c65c842b2c6b0551578999880a296`
- **SHA-256 (zeros form):** `f0f3d620144478038a53b8fa40ba10b39aba80f82f5a4c5614f35b2de2b097d2`

### Slot 2 — SNAP `2px`

- **File:** `releases/gems86-h33-2b2-snap2-20261023-6ec42a92.tif`
  (fallback twin: `gems86-h33-2b2-snap2-20261023-6ec42a92-zeros.tif`)
- **Name:** `gems86-h33-2b2-snap2-20261023-6ec42a92`
- **Note (91 chars):**
  `GEMSDOE86 h33-2b2 SNAP 2px | 37654 dots, 179.954% changed vs R0 | token 6ec42a92 | UNSCORED`
- **Format receipt:** PASS — same grid/dtype/range checks; 37,654 emitted cells; 0 dots on
  catalogue pixels; minimum catalogue clearance 2.236 px (unchanged from the parent);
  mean dot displacement 1.4349 px (143 m), max 2.0 px.
- **SHA-256 (nan form):** `23cc396355bc5a0f4761f685f18dc0817361985c67c4067b23ab8242c666c0aa`
- **SHA-256 (zeros form):** `accdb5754a85d720b3eb9d9ad2f8c5c3936113c86cdfad8bde94cb3090d88ae9`
- **Read the note before uploading:** 179.954 % "changed" counts *pixels*, not distance. Every
  dot moved at most 200 m; the pixel-set overlap with the parent is low only because dots are
  sparse. SNAP is the one axis the brief exempts from the 1–50 % change rule.

### Slot 3 — CONCENTRATION `b1km-move15`

- **File:** `releases/gems86-h33-2b2-conc15-20261023-2b883f2d.tif`
  (fallback twin: `gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif`)
- **Name:** `gems86-h33-2b2-conc15-20261023-2b883f2d`
- **Note (107 chars):**
  `GEMSDOE86 h33-2b2 CONCENTRATION b1km-move15 | 37654 dots, 29.999% changed vs R0 | token 2b883f2d | UNSCORED`
- **Format receipt:** PASS — same grid/dtype/range checks; 37,654 emitted cells; 0 dots on
  catalogue pixels; minimum catalogue clearance 2.236 px; 5,648 dots relocated between 1 km
  blocks; block-density CV 0.6235 → 0.7644.
- **SHA-256 (nan form):** `cf54e7578a9ecd5202a02c464e1142ca911eb88039af0a9f9db5e47d8915000e`
- **SHA-256 (zeros form):** `09aaa696e1f0fce6ea010a0c125e64bf6df9a1dff18bcf547dffae94b928e6f5`

## Which encoding to upload

Either. The two forms differ only outside the footprint (NaN vs 0) and the ledger shows the
encodings scoring identically. Upload **one** file per slot, never both. The `-zeros` twin
exists because a previous submission attempt returned
`Predicted values must be in range [0, 1]`; both forms here are inside [0, 1] by measurement,
so the twin is a fallback, not a fix.

## Before you upload

1. Confirm on the competition page: the weekly slots remaining, the deadline, and the current
   public leader. This session verified none of them (it never fetches drivendata.org).
2. Re-run the gate from disk, so you are uploading what was measured:
   `.venv/bin/python -c "import sys; sys.path[:0]=['src','vendor/template66']; from gems.validate_submission import validate; import json; print(json.dumps(validate('releases/gems86-h33-2b2-prune3-20261023-e4027684.tif', reference_path='data/bridge/sample_submission.tif'), indent=1))"`
3. Paste the receipt back into `ledger/submissions.csv`. A score without a receipt stays a
   CLAIM.

## What this session did not check

No live score exists for any of these files. The catalogue hide-and-recover PROXY, the
leakage canary and the SGMC control were all **NOT RUN** this session — the first needs a
lidar coverage mask the brief withholds, the second and third need the 419 MB feature stack the
human declined to restore. None of that is a pass; it is an explicit gap. See
`AI_USE.md` and `IRREGULARITIES.md`.
