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

## IR-86-MASS-01 — the parent's ranking is a traversal, and it is geographically structured
Brief v2 §5 (MASS) says to rebuild R0's ranking from the recorded recipe. Done and validated:
greedy 2.8 px thinning in FIFO-BFS visit order reproduces the pinned `d2.8` set exactly
(44,090 dots, 0 differing cells; row-major order does not). But the order is seeded
row-major by connected component, so "lowest-ranked 10 %" is not a random or quality tail:
the 3,765 dropped dots are **100 % in the southern half** (mean row 3,215 vs parent 1,273)
and the 3,765 added cells are **100 % in the northern strip** (mean row 60.5), with 98.59 %
of additions within 2.8 px of an existing dot. **Decision:** built literally as briefed,
with the quadrant shares and redundancy measured in `evidence/mass_axis_20261023.json` and
stated on the mechanism cards, and with both variants predicted negative so no slot is
recommended by default. **Cost:** a MASS receipt cannot be attributed to mass alone
(minus = mass × geography; plus = mass × kernel redundancy); it can only bracket whether
*traversal-ranked* mass at 37,654 is near-optimal. This also narrows IR-86-PRUNE-02: a
rebuild supplies no *quality* ranking, but the recipe's actual priority order is recoverable
and checkable.
## IR-86-SNAP-01 — AXIS was again unassigned; SNAP was taken from the slot plan, not from the human
Brief v2 §1 says the AXIS is human-assigned. It arrived blank for the fourth session running.
**Decision:** SNAP was chosen because (a) `SLOT_PLAN.md` (written by the PRUNE sessions) had
already pre-registered "SNAP or RELIEF" as slot 2 and declared PRUNE crowded, and (b) SNAP's two
bands restore from a verified pin, so nothing had to be guessed. No other axis was touched.
**Cost:** if the human wanted MASS, CONCENTRATION or RELIEF, this session's three builds are off-axis.

## IR-86-SNAP-02 — SNAP is a negative axis on the only instrument available
97–99 % of R0's dots move to a stronger gradient cell, so the edit is large; but the catalogue
hide-and-recover PROXY cannot separate any arm from a **random-response null control** (real
+0.00013 vs null −0.00120; σ=1 smoothing −0.00179, σ=2 −0.00316), and it costs coverage
(dots with a neighbour closer than 2 px: 0 → 3,448 / 8,341 / 2,085). The response is smooth
(lag-1 autocorrelation 0.978), so this is not speckle — the incumbent field simply is not on the
TMI/gravity ridge, and "on the ridge" is not demonstrably "on a fault".
**Decision:** all three variants ship as gate-clean artifacts with **negative** MODEL predictions
and are ranked *below* the PRUNE rung in `SLOT_PLAN.md`. SNAP gets at most one slot, and only as a
deliberate probe of the live hypothesis, never as an expected gain. **Cost:** the live hypothesis
("new faults are at potential-field edges") is untestable locally; one slot is the only measurement.

## IR-86-SNAP-03 — a SNAP variant changes ~194 % of R0's cells, which the 1–50 % rule cannot express
A move deletes one cell and adds another, so % of parent *cells* changed is 2×% of dots moved
(193.8 / 196.9 / 199.6 %). Brief §5 exempts SNAP from the 1–50 % contract and asks only that the
exact percentage be recorded.
**Decision:** the ledger's `pct_changed` column reports **% of parent dots that moved**
(96.92 / 98.44 / 99.78 %) because a dot is the unit of mass; the cell-level figure and the
count-preservation proof are in `ledger/variants_snap.json`. **Cost:** anyone comparing the SNAP
rows to the PRUNE rows in that column compares two different denominators.

## IR-86-SNAP-04 — the (R0, SNAP) pair was already spent before this branch saw main

The ledger check the brief asks for could not see the other sessions: this branch was cut from
`27d915f`, and `origin/main` was a single grafted commit, so `git merge-base` returned nothing until
`git fetch --unshallow` (IR-86-SNAP-05). PR #28–#31 landed the PRUNE ladder and an independent SNAP
axis (`a3d584a`, three variants `r1p000` / `r2p000` / `r2p000-grav`) while this session was building.

Decision changed: the three magnetic-edge variants built here are recorded as **`BUILT-DUPLICATE`**
and are **not** proposed for a weekly slot. They are kept because they were built under a different
rule (1 px smoothing, 0.25 σ gain gate, 2.828 px spacing floor, magnetic-band response) and they
corroborate PR #31's negative verdict from an independent geometry. Requesting slots for them would
have spent three of the entity's weekly submissions on an axis already measured negative.

## IR-86-SNAP-05 — depth: shallow checkout hid the common ancestor

`git merge origin/main` failed with *"refusing to merge unrelated histories"* and `git merge-base`
returned nothing, because the checkout carried `origin/main` at depth 1 (one grafted commit). The
repository was **not** diverged; `git fetch --unshallow origin` restored 84 commits on main, after
which the merge base was `27d915f` as expected. Anyone reconciling two sessions here must unshallow
first, or a resolvable content conflict looks like history corruption.

## IR-86-SNAP-06 — the hide-and-recover PROXY measures catalogue-collar recovery and nothing else

Reported by this session, and it changes how every future proxy number in this repo must be read.
The proxy gave 0.0047 for the parent and 0.0150 / 0.0169 / 0.0190 for the three magnetic SNAP
variants — a factor of three. Re-scoring all four with **one fixed ≥ 3 px catalogue collar applied
to every candidate** gives **0.0000 for all four**, and drops the SGMC control from 0.0877 to
0.0000 (`evidence/snap_fixed_collar.json`).

Decision changed: no proxy number in `SLOT_PLAN.md`, the README or any card may be quoted as a
ranking of candidates for this lineage unless the same collar is applied to every arm; the only
quantity the free proxy is measuring is how much mass sits beside a withheld catalogue trace, which
is the zone the live metric masks out and penalises. The proxy stays report-only and never a gate.

## IR-86-SNAP-07 — the SNAP window was Chebyshev, corrected to a 2 px Euclidean radius

The pre-registered window was the 25 cells with `max(|dy|,|dx|) <= 2`. A corner move is 2.828 px,
so the file could claim a "≤ 2 px" rule while displacing dots by 2.83 px, and the repository's own
SNAP rule and release contract (`src/gems86/snap.py`, `tests/test_prune_ladder.py`) both define the
cap as a **Euclidean radius**. The house contract caught it (`assert 2.828 <= 2.0`).

Decision changed: the window is now the 13 cells within a 2.0 px Euclidean radius, the realised
maximum displacement is exactly 2.0 px, and the three builds were regenerated under it — moved
fractions 33.9 / 39.6 / 45.9 %, mean displacement of moved dots 1.72–1.74 px, spacing floor still
2.828 px. The change is a definitional correction, made before any score existed and before any
file left this branch; it is recorded here because it happened after the pre-registration was
written, and the pre-registration text was amended in the same commit rather than quietly.

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

## IR-86-RELIEF-03 — MASS: this session declined it, a concurrent session built it, and both said the same thing
Brief v2 §5 MASS allows "rebuild the ranking from the recorded recipe if it is not stored", and PR
#28 had reconstructed one: `scripts/build_r0_prune.py::original_visit_rank`, the deterministic
FIFO-BFS visitation order of the `gems27.thinning` recipe. So when the human assigned RELIEF, this
session left MASS unbuilt on the grounds that a traversal order is not a quality ranking
(IR-86-PRUNE-02 had gone further and called MASS unavailable).
**Update during merge:** the concurrent `arena/7cf7f98a` session *did* build MASS ±10 % and reached
the same conclusion independently — the reconstructed order reproduces the pinned `d2.8` set
exactly, but it is geographic, so its dropped 10 % is 100 % southern-half dots and its added 10 % is
100 % northern-strip cells, 98.6 % of them within 2.8 px of an existing dot (IR-86-MASS-01).
**Decision:** no conflict to resolve — the two sessions agree that a MASS receipt cannot be
attributed to mass alone. This item stays as the record that the axis was *available*, so nobody has
to re-derive it a third time. **Cost:** none to this branch; the MASS files exist and are
`-0.003 / -0.006 MODEL`.

---

## IR-86-CONC-01 — two sessions built (PRUNE,3) and (SNAP,2) independently; the ledger was stale at branch point

**Observed.** This branch was cut at `27d915f`, before PRs #33/#34/#36 merged. Its
`ledger/submissions.csv` therefore did not contain the parallel sessions' rows, so the brief's
"check the ledger first" step passed locally and this session built `(PRUNE, collar3px)` and
`(SNAP, 2px)` — keys already built on `main` as `(PRUNE,3)` (`…-prune3-…-01d57649`) and
`(SNAP,2)` (`…-SNAP-r2p000-…-e7473403`).

**Decision.** Brief §6 dedupes on repeated `(parent, axis, value)`, so both are recorded
`BUILT-DUPLICATE` in `ledger/variants_concentration.json` and are **not** slot candidates. They
stay on disk for audit only. The one non-colliding build is `(CONCENTRATION, b1km-move15)`, which
was unbuilt on `main`.
**Cost.** Two wasted builds (~400 s of compute), no slot spent.
**Prevention.** Re-`git fetch origin main` and re-read the ledger *after* the axis is chosen and
*before* the build, not only at session start. `tests/test_axis_releases.py::
test_duplicate_arms_are_not_marked_built` now fails if a duplicate is ever recorded as `BUILT`.

## IR-86-CONC-02 — the reported block-density CV band does not contain the incumbent

**Observed.** The brief states the best files sit at block-density CV 0.51–0.59. Measured on R0
over occupied 1 km blocks (10×10 px): **0.6235** (15,976 of 122,717 blocks occupied, mean 2.357
dots per occupied block). The parent is outside the band it is supposed to exemplify.

**Decision.** The band is treated as an unverified CLAIM, not a target and not a gate.
CONCENTRATION was built to the brief's own definition (move 15 % from the lowest-prior blocks to
the highest-prior ones), which moves the CV to **0.7644** — further outside. That direction is
recorded as the axis's falsifier rather than tuned away: if the live result is ≤ 0, the band
becomes the thing to test (spread mass until the CV lands in-band) and CONCENTRATION-as-defined
retires. **Cost:** none; the variant is built either way.

## IR-86-CONC-03 — R0's support mask is saturated at its own thinning radius

**Observed.** A count-preserving PRUNE refill must find 2,171 free cells. Inside the parent's own
H19-5 support mask (121,131 px) only **611** eligible cells region-wide sit ≥ 2.828 px from a
retained dot.

**Decision.** The refill runs in two passes: parent spacing first (475 placed), then a relaxation
to the parent's own >2 px catalogue-clearance floor (1,696 placed), recorded as
`refilled_at_relaxed_spacing`. The alternative — a 1,696-dot shortfall — would have turned a PRUNE
build into an unlabelled MASS change, which is worse. Note this is the same confound PR #28
recorded for its own `(PRUNE,3)+refill` ("PRUNE and spacing are not separable in this design");
two sessions reached it independently. **Cost:** the PRUNE arm cannot be attributed to the collar
alone. It is a duplicate arm here, so it costs no slot.

## IR-86-CONC-04 — the parent's filename token is not a digest of the parent's bytes

**Observed.** The parent's name carries `e5eb6e7e`; its SHA-256 is
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. The upstream `-zeros` and
`-nan` twins hash to `c55bafc4…` and `baeae321…`
(`docs/evidence/h86_wvb_data_restore.json`, GEMSDOE32 ref `780a5a53`), so no published twin of
that file hashes to `e5eb6e7e…`. Other sessions' `h33-h33-2-b2-20261004-e5eb6e7e-…` release names
inherit the same non-digest token.

**Decision.** This session's releases are named with a deterministic **dot-set** digest
(`grid_io.dot8`: SHA-256 over the packed bitmap plus shape), so the token is reproducible from the
mask alone and cannot be circular with the file's own tags. The ledger records the token in
`sha8` and the zeros twin's file digest in `sha256`, per house convention, and
`tests/test_axis_releases.py` re-derives both from disk. **Cost:** none, but any tool that parses
`e5eb6e7e` as a content digest is wrong.

## IR-86-SNAP-08 — brief §4.4 (>=3 px) vs the SNAP spec ("same exclusions") on R0
The same conflict RELIEF logged as IR-86-RELIEF-02, reached independently from SNAP:
enforcing >=3 px inside a SNAP variant re-runs PRUNE's collar. All SNAP builds keep the
parent's >2 px exclusion (min 2.236 px, zero catalogue mass). No new decision; recorded
so the SNAP files' 2-3 px dots are not mistaken for an oversight.

## IR-86-SNAP-09 — a third SNAP build (gain-gated) landed after two were already merged
Its `snapr1`/`snapr2` duplicate PR #31's pairs (36,483 vs 36,494; 37,055 vs 37,066 dots
moved) and are **withdrawn, no raster written**; its novel gated pair `snapr2g10` stands
as `BUILT-DUPLICATE` corroboration (PR #34's convention), not a candidate. **Cost:** SNAP
consumed three sessions/builders for one thrice-measured negative; the next session needs
an explicit human AXIS assignment instead of another slot-plan reading.

## IR-86-SNAP-10 — the SNAP builds treat the signed gravity band differently
`iso_grav_anom_hg` is signed: PR #31 ranks it as-is, PR #34 uses magnetic bands only, the
gated build ranks `|iso_grav_anom_hg|`. Nothing is re-run; cross-build gravity comparisons
are not like-for-like, and any future SNAP-adjacent proposal must state its treatment first.

## IR-86-SPACING-01 — the dedupe gate fires on a session's own rebuild, so the scan was scoped to the ledger

**Observed.** The SPACING builder was re-run once after a defect fix. The second pass aborted on
`sha256_not_in_ledger`, because `known_hashes()` had globbed `releases/**/*.tif` and picked up the
*first pass's own bytes*: a deterministic rebuild of the same `(parent, axis, value)` collides with
itself. Brief §6 dedupes on "exact hash and repeated (parent, axis, value)" — an identical rebuild of
the same key is neither a repeat slot nor a new file, and treating it as one hides nothing but stops
the session.
**Decision.** `scripts/build_r0_spacing.py:known_hashes()` now consults `ledger/submissions.csv`
plus the delivered parents in `data/scored_fleet/`, and no longer scans `releases/`. The gate script
`src/gems86_axis/gates.py` was **not** modified: the dedupe rule is unchanged, only the set it is
compared against. Nothing was promoted by this: the tokens (0d2f135e / 63c4c56f / caffc3f0 /
db4cae83) are identical in both passes, so the rebuild is provably the same experiment.
**Cost:** ~6 minutes and one aborted run. A reusable rule for this repo's axis builders: never seed
the duplicate set from the directory you are about to write into.

## IR-86-SPACING-02 — the axis moves mass off its own evidence surface; the surrogate cannot see the difference

**Observed.** 100 % of the relocated dots start on the H19-5 support surface the lineage was thinned
from; after placement only 1.8 % (pdisk), 3.0 % (lattice) and 5.2 % (strike) of their destinations
are on it. The SGMC off-catalogue surrogate nevertheless reads +0.0015…+0.0020 for all three arms,
while the random-move control in the same window reads +0.0002 — and rises to +0.0033 once the truth
is translated by up to 6 px to represent the ~400 m flight-line position uncertainty in brief 2.
**Decision.** Reported as MODEL only, with the control printed next to every arm, and no SPACING arm
is offered as slot 1 or 2 in `SLOT_PLAN.md`. The law-vs-control separation (~+0.0016) is the axis's
real content; the absolute number is not trustworthy because most of the bought coverage sits on
ground the parent's own field does not rate. A SPACING slot is a mechanism probe, decided by the
human, and `strike` is the only arm whose false-positive term barely rises (+83.7 vs +140).
**Cost:** none this session; it bounds what a SPACING receipt can later be said to have proved.

## IR-86-SPACING-03 — a count-preserving bug found by the axis tests, not by the gates

**Observed.** The first draft of `src/gems86/spacing.py:relocate()` built its output as
`retained ∪ destinations`, so any dot it could not place *disappeared*: on a 12×12 synthetic grid the
"fixed count" arm returned 2 dots for 4. The MUST-pass gates would not have caught it (the file is
valid, the format is valid, the catalogue is clean) — only the axis contract would.
**Decision.** Placement now runs on a single occupancy set that starts as the whole parent, vacates a
source when it is processed and re-fills it if the dot cannot be placed, so the count is fixed **by
construction** and an unplaced dot is reported in `moved_unplaced` (8 lattice, 201 strike, 0 pdisk).
Two side effects are features, not accidents: a destination can no longer land on a cell another
selected dot still occupies, and `destinations_on_vacated_source_cells` (87–260 per arm) is now
reported so `dots_changed = 2·(placed − reuse)` holds as an identity in
`tests/test_spacing_axis.py`. **Cost:** one rewrite; the rule to keep is that a variant which changes
the count is a MASS experiment wearing another name.

## IR-86-SPACING-04 — brief §5's SPACING spec, read literally, is impossible on this parent

**Observed.** Brief §5 asks SPACING for "lattice vs Poisson-disk vs along-strike at matched count",
and §5 also requires a variant to change 1–50 % of the parent's dots. A *global* lattice or
Poisson-disk re-arrangement of 37,654 dots changes ~100 % of them (and the historic full-lattice file
`13GEMSDOE r13-lattice-s5` scored 0.0904 CLAIM). The two instructions cannot both hold on this
parent.
**Decision.** The three laws were kept, the *scope* was reduced: each arm re-lattices only the mass
the metric has already written off (credit ≤ 16 of 29 disc cells), so all three sit at 35.9–37.9 %
changed cells with the count fixed, and every destination stays within 800 m of its source (widened to
1.6 km for 480 lattice / 1,095 strike dots, reported). The literal global forms stay unbuilt and are
recorded here as the reason. **Cost:** none; the reading is logged so a later session does not
"correct" the dose upward.

## IR-86-SPACING-05 — the fold-fair hide-and-recover PROXY is *not* at the floor here, and that is a confound, not a win

**Observed.** The SPACING run card (`evidence/spacing_axis_20261023.json`,
`instruments.catalogue_hide_recover_proxy`) measures pooled PROXY DTI **0.00370 [0.00297, 0.00441]
for R0** and **0.01534 / 0.01359 / 0.01217** for `pdisk16` / `lattice16` / `strike16` (11,321
withheld positives, 4 folds). Unlike the PRUNE and SNAP arms, which read 0.00000 (IR-86-PRUNE-03,
IR-86-SNAP-06), these arms recover withheld catalogue faults four times better than the parent.
The reason is structural: the comparison is fold-fair only for the *arms*. Each arm is re-derived
per fold using that fold's **visible** catalogue for its collar, so its relocated mass is free to sit
on the withheld trace, while R0 was built against the **full** catalogue and therefore avoids exactly
those pixels. The instrument is measuring "you did not apply the 2 px collar here", which is
PRUNE's quantity, not SPACING's.
**Decision.** The proxy is published in the run card and **ranked by nothing**: no arm ordering, no
slot argument, and no README/SLOT_PLAN claim uses it. `SLOT_PLAN.md` and `evidence/spacing-mechanism.md`
carry this entry instead of the earlier "proxy is at the floor" phrasing, and the run card's own
`caveat` string (written before the measurement) is superseded by this entry. A future session that
wants a usable proxy for an arrangement axis must build the parent *in the fold too* — i.e. re-derive
the parent's dot set from the visible catalogue — or hold the collar fixed across every arm, which is
exactly what IR-86-SNAP-06 concluded.
**Cost:** one report-only instrument retired for this lineage, and a rule for future axes. The MODEL
predictions used for the ledger come from the SGMC off-catalogue surrogate, not from this number.

## IR-86-CONC-05 — brief §4.4's ">= 3 px" cannot bind the CONCENTRATION placement rule on R0

**Observed.** Brief §4.4 says "emit zero mass on catalogue pixels and keep >= 3 px from them unless
AXIS=PRUNE". R0 itself keeps 2,171 dots at 2–3 px from a mapped trace (its rule is "off the trace,
>2 px"), so the rule cannot bind the inherited dots: clearing that band **is** `(PRUNE, 3.0)`, a
different axis and a different slot, already spent three times over (IR-86-PRUNE-08). The merged
`(CONCENTRATION, b1km-move15)` arm (PR #37) resolved the same conflict the way the SNAP arm did
(IR-86-SNAP-08): it kept the parent's own >2 px floor, so its newly placed dots sit at 2.236 px.

**Decision.** This session's three CONCENTRATION variants (`b1km-move10`, `b1km-move20`,
`b5km-move15`) follow that same rule — the parent's >2 px catalogue exclusion — so that the only
change against R0 is the block relocation and the axis stays single-variable. The residual is
reported, not hidden. Newly emitted dots inside the 2–3 px band: **1,599** (`b1km-move10`), **2,899**
(`b1km-move20`), **991** (`b5km-move15`); the inherited band is 2,171 in all three. Enforcing the
literal ≥3 px on new mass would *also* tighten the placement spacing floor from the parent's 2.828 px
to 3.0 px (the builder uses one parameter for both), which is a second edit, so it was not done.
**Cost.** The variants are not literally §4.4-compliant for newly emitted mass. The gap is quantified
above and must be attributed to PRUNE, not CONCENTRATION, by any reader; it is a known, logged gap
(IR-86-RELIEF-02, IR-86-SNAP-08), not an oversight.
