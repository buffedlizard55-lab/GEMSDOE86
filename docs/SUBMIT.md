# SUBMIT — exact upload procedure for the 2026-10-23 PRUNE candidates

A local format pass is **not** organizer acceptance and **not** uniqueness clearance. You upload
from your own account; nothing here logs in, submits, or reads the leaderboard.

## 1. Pick the file

Upload the **`-zeros` twin**, not the spec-form twin.

| order | file | dots | sha256 (first 12) | bytes |
|---|---:|---:|---|---:|
| 1 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-27c5eab6-zeros.tif` | 35,483 | `27c5eab629ec` | 142,955 |
| 2 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le2p828-20261023-e475963d-zeros.tif` | 36,043 | `e475963d1919` | 144,181 |
| 3 | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le2p236-20261023-444eb3b0-zeros.tif` | 36,713 | `444eb3b01aee` | 145,676 |
| — | `releases/…-CONTROL-massctl2171-20261023-99190068-zeros.tif` | 35,483 | `99190068056b` | 143,401 |

The control is an instrument. **Do not submit it.**

Both twins carry the identical dot set; the ledger records that NaN-outside and zeros-outside
files of the same dots have always scored identically. The spec-form twins
(`…-le3p000-20261023-27c5eab6.tif`, no `-zeros`) put NaN outside the footprint, which the public
description allows but this repo's conservative all-finite policy rejects (two checks fail:
`no_nan_anywhere`, `outside_footprint_zero`). Use them only if a upload ever errors on the zeros
twin — that has never happened for a zeros twin.

## 2. Name and note (both ≤ 140 characters, copy exactly)

- **Name:** the file stem, e.g. `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-27c5eab6`
- **Note:** `R0 h33-h33-2-b2-20261004-e5eb6e7e; PRUNE <=3.0000px; 35483 dots; predicted +0.004 (MODEL)`

The exact note for each file is inside its adjacent receipt
(`…-zeros.json` → `note`), together with `note_chars`, so the 140-character limit is measured,
not guessed.

## 3. Format receipt (re-derive it yourself, do not trust this page)

```
.venv/bin/python - <<'PY'
from pathlib import Path
import numpy as np, rasterio
from gems57.grid import load_grid
from gems57.validate import validate
from gems57.gates import format_report
g = load_grid(Path("data/bridge"))
tif = Path("releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-27c5eab6-zeros.tif")
v = validate(tif, g.footprint, g.catalogue); r = format_report(tif, Path("data/bridge/sample_submission.tif"), footprint=g.footprint)
print(v["all_checks_passed"], r["ok"], v["on_catalogue_positive_pixels"], v["emitted_positive_pixels"], v["sha256"])
PY
```

Expected: `True True 0 35483 27c5eab6…`. `pytest -q tests/test_prune_ladder.py` re-runs the same
gates on every committed release, so CI fails if a raster is edited after the fact.

## 4. After the run scores

Put the number in `ledger/submissions.csv` on that candidate's row: `receipt_score` and
`receipt_date`, copied verbatim from the submission-page receipt. Until then `receipt_score` stays
empty and the 0.2778 incumbent stays a CLAIM. One slot = one file; do not re-upload the same
bytes (at least eight historical slots went to exact repeats).

## 5. Before you click submit

- [ ] `slots left this week` in `README.md` is correct.
- [ ] The sha256 of the file you are about to upload matches the table above
      (`shasum -a 256 <file>`), so you are not uploading a twin by mistake.
- [ ] You have read IR-86-PRUNE-03: the repo's standing literal-overlap stop marks every candidate
      "DO NOT SUBMIT" for a uniqueness-policy reason, not a format reason. Overriding it is your
      decision as the owner, not the agent's.
