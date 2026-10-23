# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** TOP_PUBLIC, remaining quota and R0's submission receipt were not supplied. The human alone submits from one registered entity.

- Candidate ID: `h33-h33-2-b2-prune3-20261023-01d57649`
- Primary (NaN outside): `releases/h33-h33-2-b2-prune3-20261023-01d57649.tif`
- SHA-256: `01d57649168d52a0bf2f9aced7aa2280a92b6fd7a0224757d5acc5e925785e96`
- Fallback (zeros outside): `releases/h33-h33-2-b2-prune3-20261023-01d57649-zeros.tif`
- Fallback SHA-256: `4131e37133a3c5a874c42fb7c975ec4ecb7b4be946b794ff9c9852afa575e225`
- Upload **only one file per slot**.
- Submission name: `h33-h33-2-b2-prune3-20261023-01d57649`
- Form note (107 chars): `R0 h33-h33-2-b2; PRUNE<=3px + BFS-ranked H19-5 refill, 37654 dots; predicted delta -0.004 MODEL; no receipt`
- Predicted change: **−0.004 (MODEL)**, not a score.
- Format receipt: `evidence/r0-prune3-run-card.json`; both files re-read from disk, all hard checks passed, 37,654 dots, zero catalogue mass.
- TIFFs are local-only and gitignored because this public repository has unchecked competition data-use terms. Record the actual receipt score/date in `ledger/submissions.csv` after any human submission.

---

## PRUNE ladder — four more candidates (same day, second session)

All four are strict subsets of R0; rebuild them with `scripts/run_prune_ladder.py` (the rasters are
gitignored, the hashes are not). Upload the `-zeros` twin. **Do not upload the control.**

| order | file | dots | sha256 (12) | predicted Δ |
|---|---|---:|---|---|
| after the refilled `(PRUNE,3)` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le2p828-20261023-6ff38618-zeros.tif` | 36,043 | `6ff386184585` | +0.003 MODEL |
| then | `…-PRUNE-le2p236-20261023-82b3f1f4-zeros.tif` | 36,713 | `82b3f1f4024a` | +0.001 MODEL |
| mass experiment, only paired with the refilled `(PRUNE,3)` | `…-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | 35,483 | `a438e92b79df` | +0.004 MODEL |
| never | `…-CONTROL-massctl2171-20261023-a2a8be25-zeros.tif` | 35,483 | `a2a8be25eaab` | 0.000 MODEL |

The `(PRUNE,3)` pair (refilled 37,654 dots vs. this 35,483-dot twin) is the cleanest mass experiment
available: same collar, different mass. Score both only if the week has slots to spare — otherwise the
refilled file alone answers the collar question better.

Verify before uploading:

```
PYTHONPATH=vendor/template66 .venv/bin/python -c "
import json,hashlib,pathlib
for p in sorted(pathlib.Path('releases').glob('*-zeros.json')):
    r=json.loads(p.read_text()); f=p.with_suffix('.tif')
    got=hashlib.sha256(f.read_bytes()).hexdigest()
    print(r['id'][-20:], r['n_dots'], 'OK' if got==r['zeros']['sha256'] else 'SHA MISMATCH')"
```

Every row must print `OK`, and the parent must rebuild to `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`
(byte-identical, asserted by the builder).
