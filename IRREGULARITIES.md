Only items that changed what a session did, or that a human must resolve before the next
slot. Three Arena sessions worked the PRUNE axis on the same parent; all are recorded.

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
## IR-86-LADDER-01 — the fixed-count refill confounder (PR #28's design)
The ≤ 3 px prune removes 2,171 dots, but only 475 same-field refills preserve the parent's 2.8 px
spacing; the mandated 2,171-dot refill therefore changes spacing as well as collar membership
(measured: mean nearest-neighbour 3.735 → 3.550 px). A live result from `…-01d57649` cannot be
attributed to collar width alone. **Decision:** that design is not slot 1; the pure-deletion rung
is. This branch's `prune3r` (relocate 1.14 px, spacing nearly intact) is the clean version.

## IR-86-LADDER-02 — byte identity IS achievable, and my first pass said otherwise
PR #29 found that `existing_faults.tif`'s own writer profile (deflate, `predictor=3`, `zlevel=9`,
tiled 256, `nodata=None`) re-encodes R0 to exactly 219,065 bytes and sha256 `c55bafc4…`. My first
pass declared file bytes unreproducible after a smaller profile sweep; that was wrong and is
retracted here. **Decision:** the brief's parent gate is satisfiable as "dot set + file bytes", and
every rung is written with that profile. **Cost:** this branch's own releases use a different
profile, so their digests differ from PR #29's even where the dot sets agree — the dot-set digest
is the identity that survives an encoder change, and both are recorded.

## IR-86-LADDER-03 — the ledger had three writers for one day
Three sessions seeded `ledger/submissions.csv` independently (PR #28's builder, PR #29's
`merge_prune_ledger.py`, this branch's `build_ledger.py`). **Decision:** this branch's
`scripts/build_ledger.py` is the single generator; it reproduces PR #29's schema and rebuilds the
other sessions' rows from `ledger/variants.json` + `ledger/variants_external.json`, so
`build_ledger.py --check` proves the file is current. The other two scripts are left untouched and
remain valid for building rasters, not for regenerating the ledger.

## IR-86-RELIEF-01 — the report-only instruments caught two defects in my own first build
The first RELIEF pass built the same three doses with two faults: (a) sources were selected as the
dots *nearest* a legal destination, which moved every dot only 3–4 px (300–400 m) — a class-label
flip, not a change of terrain setting; and (b) eligibility was tested against the *parent* dot set
only, so two relocated dots could be placed 1 px apart. The children therefore had minimum
nearest-neighbour 1.0 px against the parent's 2.828 px, i.e. each variant silently contained a
clustering edit — precisely the confound IR-86-LADDER-01 records for PR #28's refill. The parent-diff
statistics (`nn_dist_px`) and the surrogate instrument are what exposed it: the first pass read
−0.003 / −0.002 / −0.010, and after fixing selection ("deepest-in-regime" first) and blocking the
spacing disc around every accepted cell, the same three doses read +0.0017 / +0.0010 / −0.0089 —
the sign of the axis flipped because the clustering cost disappeared.
**Decision:** the defective files were never released and never entered the ledger (their local
rasters were deleted, `ledger/` reverted, and the build re-run once); both fixes are unit-tested
(`tests/test_relief_axis.py::test_relocation_preserves_the_parents_min_spacing`,
`test_deepest_selection_picks_dots_further_inside_the_regime`), and the gate now refuses a child
whose spacing contract is broken. **Cost:** ~25 min of one session, and a rule for future axes:
*report-only* statistics have to be read before a file is called a variant, because they are the
only thing here that can see a self-inflicted confound.
Related trap, same session: bands 12/19 of the pinned stack carry `-3.4028234663852886e+38`
nodata **inside** the footprint (3,061 cells). A reader that scrubs only non-finite values lets
those spikes dominate the standardisation, and the regime classification then puts 100 % of R0's
dots in "basin". `src/gems86/io.read_band` is the only sanctioned reader; the driver now asserts
`max|band| < 1e6` on the inputs it classifies with.

## IR-86-RELIEF-02 — brief §4.4's ">=3 px from the catalogue" contradicts the parent's own geometry
R0 keeps 2,171 dots at 2–3 px from a mapped fault (its rule was "off the trace, >2 px"). Brief §4.4
demands ≥3 px for every emitted mass, but §5's axis contracts demand that a variant change *only*
its own axis, and clearing that band **is** `(PRUNE, 3.0)` — already built, already slot-1, spent
three times over (IR-86-PRUNE-08).
**Decision:** the ≥3 px rule binds **newly emitted** mass — every cell any RELIEF variant inserted
is ≥3 px from the catalogue — while the parent's inherited 2–3 px dots are left exactly as they
are; relocation shrinks that band incidentally (2,171 → 1,925–2,039), which is reported per variant
rather than optimised away. **Cost:** the variants are not fully §4.4-compliant, and the residual
difference (1,925–2,039 dots) is a known, quantified gap that any reader must attribute to PRUNE,
not RELIEF.

## IR-86-RELIEF-03 — MASS is not blocked the way IR-86-PRUNE-02 says, but the recovered rank is not geology
Brief §5 MASS allows "rebuild the ranking from the recorded recipe if it is not stored", and PR
#28 did reconstruct one: `scripts/build_r0_prune.py::original_visit_rank` reproduces the
deterministic FIFO-BFS visitation order of the `gems27.thinning` recipe (GEMSDOE28 94b027b) that
produced the parent's dot set. So a "lowest-ranked 10 %" cut is buildable here today.
**Decision:** not built. That rank is *traversal order over connected ridge pixels*, explicitly
content-blind — the same script says so — so a MASS drop by it measures "cut the tail of a
breadth-first scan", not "cut the least-probable dots", and a live result would be uninterpretable
in exactly the way the ledger's mass-versus-field confound already is (brief §3). **Cost:** MASS
stays unbuilt until either the parent's *probability* field is recovered (H19-5 is pinned in the
manifest but its values, not just its dot mask, would be needed) or a session is explicitly
authorised to define the ranking itself and say so on the card.
