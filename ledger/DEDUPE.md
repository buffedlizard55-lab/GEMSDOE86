# Ledger dedupe record

Source: `registry/prior_scores.csv` (119 rows). Collapsed to 112 groups by the rules in `scripts/build_ledger.py`.

| kept | merged rows |
|---|---|
| `gems-submission-20260925T001403Z-7f00890a` | 2 |
| `r7-nms3-dem10-scarp_0c9199f14e62` | 2 |
| `h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan` | 2 |
| `H25-ctx-ridge-20260927T232947704150Z-6452ae1d00` | 2 |
| `h27-4-solo-d28-20261004-8acb75e1-nan` | 2 |
| `h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1` | 2 |
| `gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan` | 2 |

Fill-only twins (`-nan` / `-zeros` / `-allfinite`) collapse because they score
identically (brief §3); exact content digests collapse because they are the same file.
