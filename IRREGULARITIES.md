# Decision-changing irregularities — 2026-10-23

1. **Axis and collar conflict.** No explicit AXIS assignment was supplied. R0 has 1,611 dots at `2 < d_cat < 3` px, while the new brief requires ≥3 px except for PRUNE. Any non-PRUNE variant would need a second collar edit. This session therefore builds only PRUNE≤3/refill; no other axis is silently combined.
2. **Fixed-count confounder.** The ≤3 px prune removes 2,171 dots, but only 475 same-field refills preserve the parent's 2.8 px spacing. The mandated 2,171-dot refill changes spacing as well as collar membership. This is measured in the run card and prevents a clean geological interpretation of a live change.
3. **No submission authorization inputs.** R0's 0.2778 is CLAIM, not RECEIPT. TOP_PUBLIC, remaining rolling-week quota, and an explicit human axis assignment are absent. No file is called a winner or automatically approved. The 2026-12-03 deadline is user-supplied and UNVERIFIED because DrivenData was not contacted.
4. **Ledger substitute.** `ledger/submissions.csv` and `ledger/raw_paste.txt` were absent. The builder seeds the ledger from `registry/prior_scores.csv`, collapses repeated `(name, score)` rows, and marks every historical score CLAIM/receipt=N. Missing hashes or dot counts remain blank rather than inferred.
5. **Public-raster data use.** This GitHub repository is public and already contains competition-derived TIFFs; data-use terms are unchecked. New candidate TIFFs are written locally under `releases/` but gitignored, so the PR contains code and SHA-bound receipts, not new public raster copies. A human must resolve the existing-data terms question before mirroring or releasing more rasters.

---

## IR-86-PRUNE-01 (corrected) — byte identity IS achievable; the collar ladder does not need a dot-set-only ledger

My first pass concluded "bytes not reproducible" after a 30-profile sweep (best match 147,697 B vs. the
published 219,065 B) and I was about to key the ledger on a dot-set digest alone. That conclusion was
**wrong**, and the correction comes from the sibling session in PR #28: the profile carried by
`existing_faults.tif`, updated to `deflate / predictor=3 / zlevel=9 / tiled 256 / nodata=None`,
re-encodes R0 to **219,065 B and sha256 `c55bafc47005…` exactly**. I verified this independently in
this checkout, and `scripts/run_prune_ladder.py` now refuses to continue unless its rebuild is
byte-identical.

Decision changed twice: (a) the parent gate in the brief is now fully satisfiable — "dot set + file
bytes" rather than dot set only; (b) every rung is written with that profile, so all four releases are
byte-reproducible from pinned inputs. The dot-set digest is kept as a secondary identity because it is
the only identity that survives a different GDAL build.

## IR-86-PRUNE-06 — two sessions built `(PRUNE, 3)` on the same day (decision: one belongs in a slot, and it is not mine)

PR #28 (branch `arena/06524e4a-gemsdoe86`, merged first) shipped `h33-h33-2-b2-prune3-20261023-01d57649`:
prune ≤3 px **plus a 2,171-dot refill at fixed count**, 37,654 dots, predicted −0.004 MODEL. The brief's
PRUNE spec asks for exactly that refill, so that file is the spec-compliant `(PRUNE, 3)` and mine
(`…-PRUNE-le3p000-…-a438e92b`, 35,483 dots, no refill) is **not a second `(PRUNE,3)` experiment** — it is
the mass-reduced counterpart of it (same collar edit, 5.8 % less mass). I left both in the ledger with
distinct ids and labelled mine "no refill" in `SLOT_PLAN.md`, because sending two collar edits to the same
week's slots without knowing which one differs would waste one. **Do not submit both.**

What is *not* duplicated and is new here: the `(PRUNE, √5)` and `(PRUNE, √8)` rungs (PR #28 built only
value 3), the mass-matched control, and the byte-identity verification above. The two sessions' R0
rebuilds agree exactly (40,199 − 2,545 = 37,654, sha `c55bafc4…`), which is the strongest cross-check
either session has.

## IR-86-PRUNE-07 — releases are gitignored (decision: the PR carries code, receipts and hashes, not rasters)

PR #28 established that `/releases/*.tif` stays out of the public repository because the data-use terms
for competition-derived rasters are unchecked. I adopted that: the four rasters exist only in the working
tree after `scripts/run_prune_ladder.py` runs, and the committed evidence is the adjacent receipt
(sha256, bytes, validator output) plus the ledger rows. Anyone can rebuild them byte-for-byte from pinned
inputs and check the hashes.
