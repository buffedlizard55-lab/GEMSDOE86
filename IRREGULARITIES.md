# Decision-changing irregularities — 2026-10-23

<<<<<<< HEAD
Only items that changed what a session did, or that a human must resolve before the next
slot. Two Arena sessions worked the PRUNE axis on the same parent; both are recorded.

## IR-86-PRUNE-01 — the standing protocol forbids every submission; brief v2 forbids the gate
`PROMPT.md` / `AGENTS.md` / `scripts/audit_release.py` apply a **70 % overlap** and **0.90
rank-correlation** uniqueness rule against a pinned registry witness that is positive at every
allowed pixel, so forward overlap is 100 % for any nonempty candidate and nothing is ever
submittable. Brief v2 §6 says the opposite: *"Do NOT apply rank-correlation or dot-overlap
'uniqueness' thresholds."* **Decision:** both sessions followed the brief — no overlap
threshold applied, dedupe on exact sha256 and repeated `(parent, axis, value)` only — and
**no gate script was modified, relaxed or bypassed**. No slot is authorised here. **Cost:** the
human must choose which rule governs before submitting; both cannot hold.

## IR-86-PRUNE-02 — parent rebuild: impossible from the `gems32` recipe, solved another way (corrected)
Brief v2 §5 says rebuild R0 and match its sha256, or stop. My first pass concluded "cannot
rebuild": `research/upstream/run_h33.py` imports `gems32.*`, which is not vendored here.
**That conclusion was too strong and is corrected.** PR #29 reproduced R0 **byte-exactly** by
taking the pinned base raster `gems28-h27-4-r1-solo-d2-8` (sha256 `ab023001…`) and deleting
every dot within 2.0 px of a mapped-fault cell: 40,199 → 37,654 dots, 0 differing pixels,
rebuilt sha256 `c55bafc4…b6fa9` = the published file. So the *lineage step* is reproducible
even though the original H33 model is not.
**Decision:** R0's identity is now established twice — by pinned digest (this branch) and by
byte-exact re-execution (PR #29). **MASS remains unavailable**, because a rebuild gives the
dot *set*, not the parent's ranking of the cells it rejected.

## IR-86-PRUNE-03 — the catalogue hide-and-recover PROXY is at its floor for this lineage
Measured: R0 scores PROXY DTI 0.00436 and every pruned variant 0.00000, because a
catalogue-avoiding field earns almost no credit from withheld catalogue pixels. The published
correlation of this instrument with live scores is sign-unstable (−0.87 … +0.54, n = 12–14).
**Decision:** reported in full (`evidence/prune_axis_20261023.json`), used only as a negative
control; no prediction or gate depends on it. **Cost:** the live slot *is* the measurement.

## IR-86-PRUNE-04 — competition rasters are committed in a public repository
`data/bridge/existing_faults.tif` (byte-identical to `labels.tif`) and
`data/bridge/sample_submission.tif` are tracked here, with 26 derived `.tif` files in
`data/scored_fleet/`; data-use terms are unchecked.
**Decision:** no new competition raster is committed. Release TIFFs stay local and are
gitignored (`/releases/*.tif`); only code, hashes and receipts are published. The restored
418 MB feature stack is gitignored too. **Cost:** the human must confirm the data-use terms and
decide whether the tracked bridge rasters should leave history.

## IR-86-PRUNE-05 — no valid target number exists
`TOP_PUBLIC` is blank; the owner prompt quotes 0.3195 and then 0.4413, undated and without
receipts. DrivenData cannot be fetched from this sandbox (terms ban automated access).
**Decision:** no target was invented and no score comparison was made. Everything is reported
against R0 = 0.2778 (**CLAIM**). **Cost:** "beat TOP_PUBLIC" cannot be evaluated.

## IR-86-PRUNE-06 — the (PRUNE, 3.5) pair is already spent on another parent
`GEMSDOE77` `gems85-h85-edti-collar35-skel-r33` (owner-reported 0.0964) already built a 3.5 px
collar, on a skeleton/`r33` parent whose baseline is unknown.
**Decision:** 3.5 was not rebuilt; values 3, 4, `3`+refill and `3r` were used. The 0.0964 says
nothing about R0 because it is confounded with a much weaker parent. **Cost:** the collar curve
has a gap at 3.5 px.

## IR-86-PRUNE-07 — the brief wants NaN outside the footprint; the repo's validator forbids any NaN
Brief §6 lists "NaN outside the footprint" as a MUST gate; `vendor/gems57/validate.py` runs the
opposite convention (`no_nan_anywhere`, `outside_footprint_zero`) as a conservative local policy
adopted after the portal's "values must be in range [0, 1]" error.
**Decision:** every variant ships both forms under distinct names and digests. The `-nan` twin
satisfies the brief; the `-zeros` twin additionally clears the vendored validator
(`all_checks_passed = True`) and `gates.format_report` (`ok = True`). Upload **one** per slot —
`-zeros` if the portal rejects `-nan` on range. **Cost:** one decision left to the human at
upload time.

## IR-86-PRUNE-08 — three sessions, seven builds, one `(PRUNE, 3)` pair spent twice over
Brief v2: "each (AXIS, value) pair is built once across all sessions". Three concurrent
sessions built the PRUNE axis on the same parent today:

* PR #28 — `(PRUNE, 3)` with a fixed-count H19-5 refill (`…-01d57649`, 37,654 dots);
* PR #29 — a nested ladder `(PRUNE, ≤2.2361)`, `(≤2.8284)`, `(≤3.0000)` plus a mass-matched
  control (`82b3f1f4`, `6ff38618`, `a438e92b`, `a2a8be25`);
* this PR — `(PRUNE, 3)` pure deletion (`3eb29af5`), `(PRUNE, 4)` (`e198b768`) and
  `(PRUNE, 3r)` equal-count relocation (`9542efac`).

`3eb29af5` and `a438e92b` are the **same dot set**: R0 minus the 2,171 dots within 3.0 px of the
catalogue (PR #29 measured the shells as 941 at √5 + 670 at √8 + 560 at 3.0 px; this branch
removed exactly 2,171 = 5.766 %). Only the TIFF encoding differs.

**Decision:** all seven stay in `ledger/submissions.csv` (nothing is deleted), the pair is spent
**once** (`le3p000` in slot 1), and this branch's `3eb29af5` is **withdrawn** from slot
consideration. The redundant local copies of `3eb29af5` are deleted from `releases/` so the
wrong file cannot be uploaded by accident. **Cost:** three sessions burned on one 5.8 %-of-mass
axis; the calendar in `SLOT_PLAN.md` now gives PRUNE one slot and moves the rest to a
feature-based axis.
=======
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
>>>>>>> origin/main
