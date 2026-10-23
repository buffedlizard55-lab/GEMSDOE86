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

## IR-86-SNAP-01 — the axis was unassigned for a fourth session
Brief v2 §1 says the human assigns the AXIS; nothing arrived again, and the clarification question
was skipped. **Decision:** SNAP was chosen because it is named in `SLOT_PLAN.md` slot 2, every input
it needs is pinned **and** restored (the 419 MB stack verifies against `4371c82e…`), and PRUNE is
already exhausted (7 builds). PRUNE, MASS (no ranking) and RELIEF were rejected for the reasons in
IR-86-PRUNE-02/08 and because CONCENTRATION's "prior" definition is not pinned in this repo.
**Cost:** a fourth axis was picked by the agent, so the three weekly slots are again aimed at a
question the human did not choose. **This is the single thing that most needs a human decision.**

## IR-86-SNAP-02 — the literal SNAP rule is degenerate; the built files add two gates
Brief §5 defines SNAP as "move each dot <= 2 px to the strongest edge/scarp response in its
window". Measured on R0 with the pinned bands: that rule moves **97–99 % of dots by a mean 1.8 px**,
because the argmax of a smooth surface over a 5×5 window sits at the window boundary for almost
every dot. Every dot lands on the window edge, so the result is a re-labelling of the parent field,
not a correction of individual dots — and it destroys the parent's calibrated spacing (mean
nearest-neighbour 3.735 → 3.30 px). **Decision:** the built variants add two *declared* gates to the
rule — target response ≥ 0.75 rank (top quartile) and gain > 0.02 — applied identically to all three
surfaces, which brings the moved fraction to 34 % / 7.7 % / 23.3 %. The rule is fixed in
`scripts/run_snap.py`, written into the mechanism cards before the rasters, and the ungated numbers
are recorded. **Cost:** these are not the literal brief form; if the human wants the ungated form,
`snap_dots(..., min_gain=0.0, min_response=-inf)` reproduces it in one run and it is predicted worse.

## IR-86-SNAP-03 — the strongest in-window edge is usually the masked catalogue, so SNAP cannot pay
For **20,235 / 27,480 / 23,081** of R0's 37,654 dots (tmihg / gravhg / combo) the highest-response
cell inside the 2 px window lies **inside the 3 px masked collar**, i.e. it is the mapped fault
trace itself. Those cells score nothing (organizer: known pixels are masked pixel-exactly), so the
rule must be forced outward, away from the very feature the geophysics is detecting. **Decision:**
the collar exclusion is kept (constraint 4), the effect is reported per variant, and the predicted
sign is negative for all three. **Cost:** this closes the "snap onto the mapped trace" idea by
construction — it can only be revisited under AXIS=PRUNE, where collar mass is the manipulated
variable rather than an accident.

## IR-86-SNAP-04 — the report-only instruments cannot order these files
Catalogue hide-and-recover PROXY: R0 0.00436 [0.00410, 0.00458] vs 0.00366 / 0.00418 / 0.00386 for
the variants — all at the floor, because a catalogue-avoiding field earns almost nothing on
withheld catalogue pixels (IR-86-PRUNE-03). The SGMC control was not computed: the pinned
`derived_sgmc_faults_100m_u8.tif` is not in the restored external subset. **Decision:** neither is
used for a prediction or a gate; predictions come from the algebra plus the measured AUC/percentile
evidence. **Cost:** the live slot is the only measurement that can settle SNAP.

## IR-86-SNAP-05 — the brief's block-density CV band cannot be compared with a local CV
Brief §1 quotes CONCENTRATION's best files at block-density CV 0.51–0.59 without stating block size,
minimum-footprint rule or definition. Measured here on 5 km blocks (≥ 25 % footprint), R0 sits at
**0.904** and no SNAP variant moves it (0.903–0.904) — the statistic is dominated by the footprint
shape, not by the dots. **Decision:** the 0.51–0.59 band is treated as **unusable as a target** until
the human supplies the definition; CONCENTRATION's next-session gate must therefore be a *relative*
CV change with the block definition frozen in the script, not an absolute attempt to hit 0.55.
**Cost:** one of the few quantitative targets in the brief is unavailable.
