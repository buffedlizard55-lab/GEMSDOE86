# Decision-changing irregularities — 2026-10-23

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

## IR-86-PRUNE-02 — the parent cannot be rebuilt from its recipe in this checkout
Brief v2 §5 says rebuild R0 and match its sha256, or stop. `research/upstream/run_h33.py`
imports `gems32.*`; that package is not vendored here. The 19-band stack and five external
rasters were restored and hash-verified, but the recipe was not.
**Decision:** parent identity rests on the pinned digest `c55bafc4…b6fa9` (identical to
`scripts/fetch_registry.py` `EXTRA[0]`, repo `buffedlizard55-lab/GEMSDOE32` ref `780a5a53…`),
never on an approximation. **MASS is unavailable** because R0's ranking is neither stored nor
derivable. **Cost:** two axes (MASS, RELIEF-by-rank) stay blocked until the ranking arrives.

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

## IR-86-PRUNE-08 — two builds now share the `(PRUNE, 3)` pair
Brief v2: "each (AXIS, value) pair is built once across all sessions". Two concurrent sessions
built `(PRUNE, 3)` on the same parent: `…-01d57649` (delete ≤3 px, refill the count from the
H19-5 field; PR #28) and `…-3eb29af5` (delete ≤3 px, no refill; this PR). They are different
experiments — count held versus count reduced — with the same nominal value.
**Decision:** both are recorded in `ledger/submissions.csv` and both are gate-clean, but the
plan spends the pair **once** (slot 1 = `01d57649`), and `3eb29af5` is kept only as the local
deletion-side control for `3r`. Nothing is deleted. **Cost:** one `(PRUNE, 3)` build cannot be
scored, and the collar-versus-mass question now needs the `3r` pairing to be answered.
