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

## IR-86-CONC-05 — partial 5 km edge blocks were almost treated as the lowest-prior source

**Observed.** A 50×50 px tiling of the 3,730×3,292 grid leaves 30 rows and 42 columns in
partial edge blocks. `block_to_pixels` marks those cells `-inf` because they have no complete
block prior. The first 5 km build therefore put their dots at the front of the ascending-prior
source draw; `prior_separation` stopped the run before any candidate raster, receipt or ledger
row was written. This is not evidence that edge-strip geology is low priority.

**Decision.** Unclassified dots are excluded from the low-prior draw (`source_priority=+inf` for
non-finite block values), and the 5 km builder fails if one is dropped anyway. Density CV remains
explicitly a **complete-block** measurement; it is not silently extended with a different partial-
block normalization. The 10/15/20% doses and low→high direction were not changed after the first
SGMC read. A synthetic 110×110 regression grid now exercises the remainder strips. **Cost:** one
205 s stopped build, zero releases and zero slots. The same guard also corrects the latent two-
column remainder issue in the older 1 km implementation; no historical 1 km artifact was rebuilt
or relabelled here.

## IR-86-CONC-09 — positive catalogue-recovery PROXY conflicts with support and independent control

**Observed.** All three 5 km arms place **0% of their added cells** on pinned `gems19-h19-5`, the
support surface from which R0's lineage was thinned; all source cells are on it. Meanwhile pooled
hide-and-recover rises from parent `0.0286 [0.0240,0.0333]` to `0.0408 / 0.0427 / 0.0441` for
10/15/20% (`n=11,321` withheld positive pixels; the paired 15% Δ is `+0.0141 [0.0072,0.0234]`,
**PROXY only**). The independent SGMC MODEL read instead changes by `−0.0066 / −0.0109 / −0.0150`,
and occupied complete-5 km-block CV rises `0.7442 → 0.9006 / 1.0113 / 1.0798`.

**Decision.** None of these three files is slot-recommended. The positive PROXY is not a score or
a gate and cannot overrule either the support-surface abandonment or the negative independent
control. Its catalogue-interaction term is also part of the placement prior, so the instrument
and mechanism are not independent. A future **support-constrained** block-allocation axis is only
a proposal for a later session; no fourth variant or retuned value was built here.

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

## IR-86-MASS-02 — brief §5's MASS ranking is a traversal; the axis was re-ranked, and the brief's own §2 requires it

**Decision changed:** yes — the ranking function this session used, and the rejection of all three
artefacts for slots.

Brief §5 defines MASS as "drop the lowest-ranked 10 % / add the next-ranked 10 %, **by the parent's
own ranking**". That pair was built by an earlier session and both arms lost (IR-86-MASS-01: the
recorded ranking is the FIFO-BFS traversal of the thinning recipe). Brief §2 then says, in the same
document, "rank dots by exact marginal gain from the metric code, not the shortcut". The two
sentences cannot both govern a MASS experiment, because the recorded ranking *is* the shortcut.

Resolution taken: the axis (MASS), the dose (±10 %) and the change rule (1–50 % of dots) stay
exactly as §5 specifies; the **ranking function** is the metric's own marginal credit
(`gems86.mass_econ.marginal_credit`), which is computable from the parent's dot mask alone with no
label, no band and no surrogate. Both predictions (preregistered, then revised) are in the run card.
If the human reads §5 as binding on the ranking function, this session's arms are off-brief and
should be treated as instrument audit only — which is exactly how SLOT_PLAN now treats them.

## IR-86-MASS-03 — the SGMC MODEL instrument is monotone in dot count, so it cannot rank mass

**Decision changed:** yes — it demotes every mass-changing artefact in the ledger, including this
session's own, and it re-orders the slot plan.

`evidence/mass_instrument_monotonicity.json`: a symmetric random add/delete ladder on the SGMC
off-catalogue surrogate reads −0.0127 / −0.0068 / −0.0030 / +0.0018 / +0.0040 / +0.0081 for
−20 / −10 / −5 / +5 / +10 / +20 % of R0's dots. Any arm that changes the dot count therefore has a
MODEL delta that is at least partly the instrument's mass response, so no such delta may be used to
promote an arm. Count-fixed arms (CONCENTRATION, RELIEF, SPACING, PRUNE-with-refill) are unaffected
at constant `n`; their *card* numbers are not withdrawn.

Numbers already published elsewhere in this repository that this affects: `massminus10` (−0.003) and
`massplus10` (−0.006) — their "selection is bad" reading is not separable from "fewer/more dots" —
and any future count-changing arm. It does **not** affect `le3p000` (+0.004) as a *number*, but see
IR-86-MASS-04.

## IR-86-MASS-04 — PRUNE's positive prediction shares a structural bias with its own edit

**Decision changed:** yes — PRUNE moves from slot 1 to slot 3 in SLOT_PLAN.md.

The PRUNE ladder's predictions were computed against a catalogue-derived truth (the
hide-and-recover construction), while the edit deletes dots near the catalogue. Any instrument whose
truth is (or contains) the catalogue will reward that deletion by construction, so part of
`le3p000`'s +0.004 is structural rather than geological. This is not a claim that PRUNE is wrong —
it is the only axis with a monotone ladder behind it — but it is no longer the best use of slot 1
when a count-fixed pair with an above-floor predicted separation exists.

## IR-86-MASS-05 — a re-run of the same pinned recipe reproduces the same sha256; the §6 hash gate needed a self-exemption

**Decision changed:** no — the gate is unchanged in substance; its implementation now says what it
means.

Brief §6 requires "sha256 not already in the ledger". This session's script rewrites its own rows
through `scripts/build_ledger.py`, so a second identical run reproduces the same bytes and would trip
its own gate. The check now passes only when every matching ledger row is one of *this run's own ids*
and carries no receipt; any other match (a prior session's artefact, or anything with a
`receipt_score`) fails. Recorded so that "reproducible" is never mistaken for "repeat submission"
(the ledger's real target: 8 slots on exact repeats).

## IR-86-MASS-06 — `src/gems86/mass_econ.py` had three bugs; the unit tests caught all three before any artefact was written

**Decision changed:** no (caught pre-release), but the numbers in the first two drafts of the run
card were wrong and are superseded.

1. the kernel offset set excluded the dot's own cell, so every dot lost its `k = 1` self-credit
   (disc weight 8.3803 instead of 9.3803);
2. the second-best surface was updated as `max(second, where(v >= best, v, second))`, which discards
   `v` whenever `v < best` — the asymmetry showed up as two symmetrical dots receiving 7.91 and 5.23
   units of unique credit instead of 5.23 each;
3. the docstring asserted `sum_x u_x = sum_g best`, which is false: with a max operator the marginals
   sum to `sum_g (best − second)`. Corrected in the module and asserted against brute force in
   `tests/test_mass_econ.py` (6 tests).

The stale artefacts from the first two drafts were deleted from `releases/mass86/`; only the three
hashes in `ledger/variants_mass_econ.json` exist on disk.
## IR-86-TRACKB-01 — the ranking TRACKB is specified to use does not exist in this checkout

**Observed.** Brief v2 §5 defines TRACKB as traces "built from R0's top-ranked dots". R0's only
recorded order is the FIFO-BFS *visitation* order of the `gems27.thinning` recipe, which the MASS
session showed reproduces the d2.8 set but is a geographic traversal (IR-86-MASS-01); the restored
H19-5 mirror is **binary** (every positive cell is exactly 1.0, measured on the pinned file), so it
carries no per-dot score either.
**Decision.** The substitute ranking is the parent's own *trace support* (longest ≥−1 px collinear run
containing the dot), computed from R0's geometry alone, and it is used only to choose donors. Stated
on the mechanism card and in the run card; no ranking is invented and no provenance order is implied.
**Cost:** transport of a MASS confound into TRACKB is impossible (no dot is added or removed for its
position in the traversal), but TRACKB cannot be described as "top-ranked dots" in any provenance sense.

## IR-86-TRACKB-02 — two build defects, one caught by a gate and one by the tests; both fixed before release

**Observed.** (a) `trace_runs` first stored indices into the dot *list* rather than flat raster cells,
so the support field landed on empty cells (7,462 cells, of which 46 were dots) while every shape
check still passed; the 1 km trace count was therefore wrong by construction. (b) `select_donors` used
`support >= 0` as its dot mask, which is true for every raster cell, so the "donors" were mostly empty
cells and deletion was short of the addition — the fixed-count gate in `run_trackb_axis.py` fired
(`37654 -> 38870`) before any file was written.
**Decision.** Both fixed (`flat[order]` decode; explicit `dots` argument, `ValueError` on over-donation),
both regression-tested in `tests/test_trackb_axis.py`. The gate, not the test suite, caught (b).
**Cost:** none released; one re-run.

## IR-86-TRACKB-03 — the 1–50 % change contract binds at the *bottom* for this axis

**Observed.** Every new trace continuation must clear the catalogue (3 px) and the parent's own √8 px
dot separation, so the relocation budget is capacity-limited: a requested 10 % donation yields 716
(3.8 % changed), 1,246 (6.6 %) and 2,710 (14.4 %) at corridors 1.0 / 1.5 / 2.5 px. Only the loosest
corridor clears 10 % changed, and it is the one whose surrogate sign is negative.
**Decision.** The three variants are reported as *corridor* values with the realised dose measured and
recorded, never as dose values that were not achieved. A future TRACKB build that wants a larger dose
must relax the spacing floor, which would fold SPACING into the axis — not permitted this session.
**Cost:** the axis is confined to ≤ 7.2 % of the dot set; the ≥ 10 % changed rung exists only at the
loose corridor.

## IR-86-TRACKB-04 — the GeoJSON trace set is a candidate prediction and stays out of Git

**Observed.** The brief asks for TRACKB as "GeoJSON + raster". This repository already keeps candidate
rasters out of Git because the data-use terms are unchecked (IR-86-PRUNE-04).
**Decision.** `releases/trackb/*.geojson` is gitignored exactly like `releases/*.tif`; the committed
record is the per-file `-zeros.json` receipt (trace table, length/azimuth/catalogue-distance statistics
and the 12 strongest traces) plus `evidence/trackb_axis_20261023.json`.
**Cost:** the full 300-trace geometry lives only in the workspace; CI cannot regenerate it without the
pinned parent (which is itself local-only).

## IR-86-CONC-06 — the CONCENTRATION prior is band-free this session, so `dens15` is not a replication of `conc15`
`variants.block_prior()` needs two terms: catalogue fault-interaction density **and** the mean Sobel
gradient of upward-continued TMI. The second comes from `training_features.tif` (419 MB), which is
absent from this checkout (`.cache/gems_data` does not exist), so this session's prior is the
catalogue term only. **Decision:** build the prior that the data support, add a matched
same-dose arm in *both* prior directions under that prior (`concdens15`, `concspr15`) plus a
random-block control, and log that `concdens15` is a **paired calibration**, not a replication of
`conc15`'s `+0.006 MODEL`; the difference between the two arms is the only quantity that isolates
the prior's sign from the missing band. The absent SGMC raster also means no SGMC control gate
this session. **Cost to the next session:** if `dens15` and `conc15` disagree, the TMI term is the
first suspect and cannot be tested until the feature stack is restored.

## IR-86-CONC-07 — this axis's sign is not measurable with any instrument in this repo, only with a live receipt
The five-truth-model panel puts `spr15`/`dens15` at −0.064/+0.047 under catalogue-adjacent truth
and +0.011/−0.011 under uniform far-field truth. Hide-and-recover, the SGMC off-catalogue DTI and
the H19-5 support surface are *all* built from the mapped-fault record that the organiser masks at
scoring time, so all three favour "mass near mapped faults" by construction and cannot rank these
arms. **Decision:** the plan treats one live slot as the only admissible test and spends at most
one slot per direction; no local instrument is reported as evidence for either sign. **Cost:**
every prediction for this axis is MODEL-class and its band crosses zero from either side.

## IR-86-CONC-08 — the block-density CV band is not reachable at the doses brief §5 allows
CV is non-monotone in dose (0.5970 at 5 %, 0.6136 at 15 %, 0.6722 at 30 %; parent 0.6235) and
*every* arm — spread included — reduces the number of occupied 1 km blocks (15,976 → 13,297), because
destinations are confined to a fixed prior fifth of the occupied blocks. **Decision:** the
0.51–0.59 band is recorded as an unverified CLAIM and is not used to choose a dose; the reported CV
is accompanied by the occupied-block count so the two cannot be read as one variable. **Cost:**
a future arm that wants to test the band must place mass in *unoccupied* low-prior blocks, which is
exactly the placement `GEMSDOE81 cont-poisson44090` scores 0.0041 with (CLAIM).

## IR-86-SPACING-06 — kernel-disjoint re-spacing at matched count is locally infeasible on R0's support

**Observed.** The natural strong form of this session's crowded-pool design — re-space the pool
so *every* final pair is >= 3.0 px (the DTI kernel radius) at the parent's count 37,654 — has
almost no legal destinations. R0 is a saturated 2.828 px packing of the H19-5 support: cells
>= 3 px from all 37,654 dots number in the hundreds (7,024 free support cells at the parent's
own floor before any placement), and the fallback displaced dots by kilometres (up to 3.8 km —
the CONCENTRATION-scale confound IR-86-RELIEF-01 warns about). 64 % of the pool could not be
placed within 24 px in the first design pass.
**Decision.** The shipped arms break each crowded pair at >= 3.0 px from its cluster's kept dot
(the kernel-overlap waste the axis targets) while holding the parent's own 2.828 px floor
everywhere else, destinations <= 16 px away; pool members with no legal cell stay put and are
counted as residual crowding (3,488-3,538 of 6,574). This also retires the KERNEL-BUDGET
proposal in SLOT_PLAN.md as literally stated ("re-spacing at >= 3.0 px at constant count"): at
37,654 dots the support cannot host it. Complements IR-86-SPACING-04 (the parallel session's
1-50 % reading): that entry rules out the global form by dose, this one rules out the strong
spacing floor by geometry. **Cost:** the arms are a partial repair (~8 % of R0's dots moved),
so the experiment speaks about the crowded pool only; the three geometries additionally share
~78 % of destinations (Jaccard 0.64) because legal sets are small.

## IR-86-SPACING-07 — two sessions built SPACING in parallel; distinct value keys both stand

**Observed.** This branch's ledger check (start of session) found no SPACING pair; PRs #44/#46
(`arena/c1df93fc`, `arena/146307ee`) landed `sp-lattice16 / sp-pdisk16 / sp-strike16 /
sp-random16` on main while this branch was building `lattice / poisson-disk / along-strike`.
Both designs answer the same axis with different scopes (their dose ~36-38 % of cells, the
"written-off mass" selection; this one ~8 % of dots, the kernel-crowded pool). The
`(parent, axis, value)` keys differ, so brief §6's dedupe does not fire and both builds stand.
The colliding file names were resolved without deleting either session's evidence: the later
branch's artifacts were renamed (`evidence/spacing-crowdedpool-mechanism.md`,
`evidence/spacing_axis_crowdedpool_20261023.json`, `tests/test_spacing_crowdedpool.py`), the
two `ledger/variants_spacing.json` lists were concatenated, and `tests/test_prune_ladder.py`
now carries both the TRACKB and the SPACING contract branches.
**Decision.** No withdrawal and no BUILT-DUPLICATE status (the keys are distinct); every card
cross-references the other session's arms so a reader cannot mistake the two designs. Slots:
neither SPACING family is a default bet (all predictions inside +/- 0.01). **Cost:** one merge
conflict round and a rename; the recurring rule (cf. IR-86-CONC-01) is that a ledger check at
session start is not a reservation.

## IR-86-TRACKB-05 — raw global `|∇TMI_up150|` concentrates 82 % of top-100 geologist traces in NW flood basalts

**Observed.** Ranking R0's `2,801` `H19-5`-supported `>= 1 km` traces by un-normalised global
`|∇TMI_up150|` + 3DEP scarp placed `82/100` (`82 %`) of the top traces in the NW quadrant (`47.4 %` of
footprint, `47.9 %` of R0 dots) over high-susceptibility Miocene–Pliocene flood basalts, leaving SE/SW
tuffs and metasediments under-represented (`1 %` in SE).
**Decision.** Replaced raw global magnetic gradient in the trace ranking composite with 5 km (`50 px`)
local-RMS automatic-gain-control normalisation `|∇TMI_up150| / sqrt(mean_5km(|∇TMI_up150|²) + 1e-3)`
paired equally with 3DEP 10 m scarp, restoring footprint-matched balance across the 120 geologist
dossier traces (`NW 63 / NE 27 / SW 13 / SE 17` = `52.5 % / 22.5 % / 10.8 % / 14.2 %`).
**Cost:** none; raw `|∇TMI_up150|` percentile is reported alongside AGC percentile per trace so
volcanic-margin mimics stay visible to a reviewing geologist.

## IR-86-TRACKB-06 — pure trace-only rasters fail both brief §5 (`1–50 %` diff) and `NLR-RULES`'s single-final-file constraint

**Observed.** Under official challenge rules (`https://docs.nlr.gov/docs/fy26osti/96647.pdf`), ONE
blind final GeoTIFF is scored in both Phase 1 ($50k automated `DTI`) and Phase 2 ($250k expert
geologist trace review + expanded ground truth). Emitting *only* the `2,237` connected pixels of the
top-120 `>= 1 km` traces changes `96.31 %` of R0 (outside brief §5's `1–50 %` invariant) and collapses
off-catalogue SGMC `MODEL` DTI from `0.092893` to `0.002429` (`Δ = −0.090464`, `−97.4 %`) because DTI
weights recall `4:1` (`β = 0.8` vs `α = 0.2`).
**Decision.** Kept pure-trace emission strictly as an in-memory diagnostic (`diagnostic_pure_top120_only`)
and implemented `rendertop120` as a count-fixed (`37,654` dots, `8.1957 %` changed) hybrid that
rasterises all 120 `>= 1 km` traces continuously at 100 m while preserving `95.9 %` of R0's background
(`SGMC Δ = −0.004335`, inside the `0.01` live evidence floor).

## IR-86-TRACKB-07 — R0's 3,349 isolated 1-dot singletons carry 4.1× the live DTI inclusion bar due to collar truncation

**Observed.** Deleting R0's `3,349` isolated 1-dot singletons (`0` R0 neighbours within `550 m`,
`cull1dot`) lowered off-catalogue SGMC `T` by `−758.25` (`0.2264 T`/dot — `12.2×` above SGMC's
`0.2 × 0.0929 = 0.0186` isolated-dot bar and `4.1×` above R0's live `0.2 × 0.2778 = 0.0556` bar),
giving `SGMC Δ = −0.009644`. Inspection shows `551` of those singletons sit in `(2.0, 3.0] px` where
R0's `<= 2 px` pruning severed real fault splays into 1-dot islands, and others sample narrow bedrock
windows across alluvial fans. Relocating them onto `>= 1 km` trace gap-bridges and collinear tips
(`bridge1km`) recovered `+444.54 T` (`+0.005352` over `cull1dot` and `+0.000842` over random relocation;
`Δ = −0.001747` on `> 3 px` SGMC truth).
**Decision.** Pre-registered rules and rasters were NOT post-hoc retuned on the surrogate; all three
`TRACKB` variants remain `slot_candidate: false`, and `SLOT_PLAN.md` logs `COLLAR-TO-TRACE` (fund trace
bridges from `PRUNE le3p000` collar dots, conditional on a non-negative Slot 3 receipt).

## IR-86-TRACKB-08 — full-footprint occupied 10 km (`100 px`) blocks match brief §4.2's `0.51–0.59` CV band across historical leaders

**Observed.** Measuring occupied block-density CV across `1, 2, 5, 10 km` scales on 10 tracked
historical scored rasters (`data/scored_fleet/`) showed that while `1 km` gives `0.6235` on R0
(`IR-86-CONC-02/08`) and `5 km` complete blocks give `0.7442`, at **`10 km` (`100 px`, fault-system
scale)** every top-scoring file (`0.2632–0.2778`) sits inside **`0.547–0.570`** (`R0 = 0.570`,
`H27-4 d2.8 = 0.547`, `H19-5 = 0.575`) whereas `gems66-lidar03` (`0.1152`) sits at **`0.960`**.
**Decision.** Logged in `SLOT_PLAN.md` as the unbuilt proposal `CONCENTRATION-10km` so any future
scale-matched concentration test targets `10 km` blocks rather than `1 km` or `5 km`.

## IR-86-CONC-10 — forensic audit retires all off-ridge `CONCENTRATION` slot claims (`conc15`, `dens15`, `spr15`) and resolves `IR-86-CONC-06`/`08`

**Observed.** Restoring all 15 SHA-256-pinned manifest inputs (`training_features.tif`, `derived_sgmc_faults_100m_u8.tif`, `H19-5`, `H19-4`, `H16-1`) enabled direct measurement of the prior `CONCENTRATION` builds (`evidence/concentration_5km_axis_20261023.json`):
1. PR #37's `conc15` (`b1km-move15`) carried an unmeasured constant (`PREDICTIONS["CONCENTRATION"] = 0.006` in `scripts/build_axis_variants.py:57`), placed 2,248 of 5,648 added dots (`39.8%`) at `<= 3.0 px` (`min = 2.236 px`, breaching brief §4.4) with `99.7%` off ancestor ridges, and actually reads **`-0.0071 MODEL`** (`-0.0063` under `±6 px` jitter) on SGMC.
2. PR #44's `dens15` and `spr15` (`IR-86-CONC-06`, built without `.cache/gems_data/` and ranked #1/#2 in `SLOT_PLAN.md` from a synthetic five-truth-model mean) place **`0.0%` of added dots on `H19-5 | H19-4 | H16-1`** and **both lose on SGMC** (`dens15 = -0.0006 MODEL`, `spr15 = -0.0013 MODEL`, matching PR #46's off-ridge `b5km-move10/15/20` at `-0.0066..-0.0150`).
3. Constraining 5 km upward relocations 100% onto ancestor ridges (`concb5kmup4 = -0.0005`, `concb5kmup8 = -0.0007`) eliminates ~95% of PR #46's off-ridge geometric penalty while confirming upward concentration still loses. Conversely, shaving `>= 3`-dot 1 km sub-kernel clusters (`k -> k-1` so occupied blocks never empty) onto sparse-block ancestor ridges (`b5km-cvband-down4` / `concb5kmdown4`, `1,506` dots moved / `8.00%` changed) reaches **`1 km occupied CV = 0.5162` inside `[0.51, 0.59]`** (resolving `IR-86-CONC-08` without desert-floor Poisson scatter) and scores **`+0.0015 MODEL` (`4/4` quadrants `+`, `+0.0020` under `±6 px` jitter) and `+0.0008 PROXY`**.

**Decision.** Retire `conc15`, `dens15`, `spr15`, and `b5km-move10/15/20` from weekly slot consideration; promote `concb5kmdown4` (`8aab97b6`) as the sole count-fixed `CONCENTRATION` slot candidate alongside `RELIEF-frontp15`. **Cost:** historical JSONs remain untouched for reproducibility; human plan updated.

## IR-86-CONC-11 — symmetric fold-fair `d28` rebuild rehabilitates catalogue hide-and-recover `PROXY` (`IR-86-SPACING-05` resolved)

**Observed.** Earlier sessions (`IR-86-SPACING-05`, `IR-86-CONC-09`) saw artificial `+0.014` `PROXY` inflation because static `R0` was already masked at `d_cat > 2.0 px` around held-out faults while relocated dots stepped back inside `2..3 px` of withheld traces. Using unmasked `scored_d28_unscored` (`ab023001...`), `R0 == d28 & footprint & (edt_cat > 2.0)` holds pixel-for-pixel (`0` differing cells). Rebuilding fold-fair `R0_f = d28 & footprint & (edt(f.visible) > 2.0)` and recomputing priors/clearances strictly from `f.visible` inside each buffered whole-component fold (`n = 11,321` withheld positives, `141` 20 km spatial clusters) restores symmetric fold-fair `R0 = 0.0961` and puts `concb5kmdown4` positive (`+0.0008`, `95% CI [-0.0004, +0.0018]`) while `concb5kmup8` is negative (`-0.0026`), matching SGMC's sign. **Decision:** record symmetric `d28` `PROXY` as `REPORT-ONLY` (`evidence_class = PROXY`), never a gate or score.


## IR-86-CONC-12 — the pre-registered 8 % and 2 km arms do not exist; the axis is capacity-capped
Two of the three builds pre-registered in `evidence/concentration-dose-mechanism.md` turned out to be
**geometrically impossible on this parent**, discovered on the first execution and before any score
was computed:

* 1 km `cvband-down8` needs 3,012 destinations; the sparse-ridge 1 km pool at `> 3.0 px` clearance
  and `>= sqrt(8) px` spacing exhausts after **2,399** placements (max feasible dose ≈ 6.37 % of R0);
* 2 km `cvband-2km-down4` needs 1,506; the 2 km pool exhausts after **920**.

**Decision:** the ladder was re-cut to 3 % / 5 % / 6 % on the unchanged 1 km rule, and the matched
ordering control was moved to the 6 % dose so it matches the strongest arm. The amendment is recorded
in the run card (`preregistration.predictions.*.amended_from`) and in the mechanism card; the
original predictions for `down5`/`down6` were **not** revised after seeing the CV values. **Cost:** the
dose curve has no point above 6.4 %, so "more dose" is not an open direction without changing a second
variable (spacing or ridge support). A 2 km block-scale replication is unavailable at the dose that
would make it comparable.

## IR-86-CONC-13 — the CV-band mechanism is falsified as stated; dispersal dose is the live variable
Measured against the pre-registration, the registered **inverted-U** shape is wrong. SGMC `MODEL` and
the fold-fair `PROXY` both rise monotonically with dose (`+0.0013 → +0.0018 → +0.0022` MODEL;
`+0.0004 → +0.0010 → +0.0013` PROXY for 3 % → 5 % → 6 %) while 1 km occupied CV falls
`0.5377 → 0.4998 → 0.4840`, i.e. the best arm lands **outside** the `0.51–0.59` band that PR #47's
card called the target. Separately, the matched ordering control (same source blocks, random dot,
random destination, same count, same gates) captures ≈ 67 % of the ranked arm's MODEL gain and ≈ 62 %
of its PROXY gain.

**Decision:** the `0.51–0.59` CV band is retired as a *mechanism* and demoted to a descriptive
correlate; future CONCENTRATION cards must state a dose, not a CV target. The credit ranking is
retained only as a `≈ +0.0007 MODEL` refinement, explicitly below instrument resolution — no ledger
row or slot note may credit the ranking with the whole gain. `conc6` still dominates PR #47's `down4`
on both report-only instruments, so it is the CONCENTRATION candidate of record, placed in slot 3
behind the two larger predicted levers. **Cost:** a clean price on the ranking needs a paired live
A/B (two slots), which the 3-per-week budget makes expensive; until then the honest prior for this
axis is the control's `+0.0015 MODEL`.

## IR-86-CONC-14 — the leakage canary initially flagged AUC 1.0000 because the canary itself leaked
On the first execution the canary returned `max_auc = 1.0000`, which trips the brief's stop rule. The
cause was in my own feature dict: `catalogue_px` is the scoring target verbatim, so its AUC is 1.0 by
construction. It was replaced by `block_density_1km_parent` (a feature the rule actually uses), and no
result was read before that fix.

**Decision:** the stop rule was honoured literally (the run aborted and no raster was written), and
the canary now reports only features that enter the edit: against the catalogue target
`ridge_union_px` 0.5154, `unique_credit_parent` 0.5037, `block_density_1km_parent` 0.5094, and
against the SGMC off-catalogue target 0.5086 / 0.5023 / 0.5467 respectively — worst case 0.5467,
far below 0.90. **Cost:** none, but the episode is a reminder that a "leakage canary" can pass or
fail on the choice of feature, so the feature list must be printed with the number.

## IR-86-RELIEF-04 — the only instrument that supports RELIEF is a relief-index meter (R² = 0.9135, n = 8)

**Observed.** Eight deterministic RELIEF rebuilds of R0 (the three shipped ladder arms, this
session's three arms, and two displacement-matched random nulls) were scored on the SGMC-extra
surrogate and regressed on the one quantity that varies across all of them, the change in mean
`relief_index` at the dots (`evidence/relief_source_20261023.json`, `instrument_diagnostic`):

| arm | Δ mean relief index | surrogate Δ (MODEL) | residual vs the fit |
|---|---:|---:|---:|
| `front+15pct` (reconstruction of the ledger row) | +0.2058 | **+0.00171** | −0.0008 |
| `front+10pct` (reconstruction) | +0.1370 | +0.00100 | −0.0009 |
| `front-10pct` (reconstruction) | −0.1163 | −0.00885 | −0.0023 |
| `int2front-15pct` (new) | −0.0587 | −0.00569 | −0.0007 |
| `int2front-10pct` (new) | −0.0565 | −0.00379 | +0.0011 |
| `int2pied-15pct` (new) | −0.2987 | −0.01179 | +0.0000 |
| null, random destination (interior source) | −0.0677 | −0.00298 | +0.0020 |
| null, random destination (piedmont source) | +0.0170 | −0.00256 | −0.0008 |

Pearson **r = +0.9558, R² = 0.9135, slope +0.0283 DTI per index unit**, intercept −0.0033 (the
"displacement tax": an arm that does not change mean relief index is predicted to lose 0.0033).
The surrogate's single-feature AUC for `relief_index → SGMC-extra` is `0.7281`, so this is not a
coincidence of the arms: to first order the instrument is a monotone function of exactly the
quantity every RELIEF variant manipulates. The reconstruction of `front+15pct` reproduces the
ledger's delta to three decimals (`+0.001711` vs `+0.0017`), so the regression is on the shipped
recipe, not a look-alike.

**Decision (changes the slot order).** No RELIEF MODEL number may be cited as *mechanism*
evidence. `front+15pct`'s `+0.0017` is what the instrument reports for a `+0.206` shift in mean
relief index, and its residual is **−0.0008** — i.e. after the gradient is removed it is
indistinguishable from (slightly below) the instrument's own line. `RELIEF-frontp15` is therefore
**demoted from Slot 1 to Slot 3**; `PRUNE-le3p000` takes Slot 1 (its relief-index change is
near zero, so this bias cannot manufacture its `+0.0040`), and `CONC-concb5kmdown4`
(`+0.0015 MODEL` **and** `+0.0008 PROXY`, two differently-biased instruments agreeing, `1 km`
CV inside `0.51–0.59`) takes Slot 2. **Cost:** the RELIEF family keeps its rows and rasters, but
its published support is reclassified as instrument-shaped; a live receipt is now the only thing
that can restore it, and at `+0.0017` a single slot could never clear the §"|Δ| < 0.01 = no
evidence" floor anyway.
**Not claimed:** that RELIEF is wrong. `relief_index` tracks real basin-margin structure; the
claim is that this instrument cannot separate that from its own gradient.
**Limit:** n = 8 deterministic rebuilds of one parent, not independent experiments, and seven of
the eight sit on two source classes of a single grid. It prices the instrument; it does not
re-score the competition.

## IR-86-RELIEF-05 — the basin source cannot be tested inside the axis contract (2,014 dots = 5.35 %)

**Observed.** Regime census of R0 this session: piedmont 20,280 dots (53.86 %), range-front 6,045
(16.05 %), range-interior 9,315 (24.74 %), **basin 2,014 (5.35 %)**. Brief v2 §5 fixes the RELIEF
dose at 10–15 % of the parent's dots, i.e. 3,765–5,648 dots. The basin holds fewer dots than the
*floor* of that window, so "does leaving the alluvium pay?" — the cleanest geological version of the
question — cannot be asked as a RELIEF variant at any legal dose.
**Decision:** the source was varied over the range interior (the only remaining class with enough
mass) and the basin question is recorded as **unbuildable on this parent**; it would need a
different axis (a mass-controlled test at ≤ 5.35 %, which is a MASS edit, and MASS is closed per
`IR-86-MASS-01..03`). **Cost:** one of the three arms that looked most promising on mechanism
grounds was never built, and the factorial is therefore 4-cell (interior/piedmont × front/piedmont)
rather than the 6-cell design with basin.

## IR-86-CONC-15 — the SGMC-extra instrument rewards *outward movement* for CONCENTRATION arms, not lineaments

**Observed.** The SGMC surrogate's truth is `SGMC − catalogue`, so a dot in the mapped-fault collar can
never earn credit there, while the organiser states new truth *can* lie within 300 m of a known trace —
and R0 is built almost entirely of such dots. Measured on this session's three arms
(`evidence/concentration_surfext_axis_20261023.json` → `instrument_confound`): `surfext10`'s added mass
sits **21.7 px** from SGMC-extra truth versus **22.6 px** for the mass it removed (the treatment moved
mass *toward* SGMC truth) yet beats its matched control by only **+0.0012 MODEL**; the control moved
mass *away* (22.8 px) and still scored **+0.0047 MODEL** in 4/4 quadrants. The fold-fair PROXY is biased
the opposite way, since it can only reward mass near *withheld catalogue* traces — exactly what surface
extension gives up (`−0.00003` treatment vs `−0.0008` control).
**Decision.** CONCENTRATION MODEL deltas are not compared across arms with different
catalogue-distance profiles; every arm is read against a matched control, never against zero, and a
positive SGMC delta alone is not evidence of lineament knowledge. This is the same instrument failure
mode already recorded for RELIEF (`IR-86-RELIEF-04`) and for the CV band (`IR-86-CONC-13`).

## IR-86-CONC-16 — R0 is saturated on its own evidence surface; the headroom is *off* that surface

**Observed.** Confirms and localises `IR-86-CONC-12`'s ≈6.4 % capacity cap. Measured on the pinned
inputs before any candidate was built: all 37,654 R0 dots lie on the `H19-5` ancestor surface, and under
the parent's own constraints (`> 3.0 px` from the catalogue, `>= 2.8284 px` from every dot) only **90**
legal free cells remain on that surface — the merged cvband rule's within-surface destination capacity
is ~2,400 dots. `H19-4 | H16-1` minus `H19-5` is 35,954 px of near-equal owner-reported quality
(`0.1894` / `0.1855` vs `0.1922`, all CLAIM) carrying **zero** parent mass, with 8,671 legal free cells
(6,456 placeable greedily).
**Decision.** Future CONCENTRATION/SPACING sessions must state the free-slot count before building;
within-surface reallocation is treated as closed, and the open headroom is surface extension
(`H19-4 | H16-1` ground, or a new evidence surface) — carried in `SLOT_PLAN.md` as
`EVIDENCE-OFFSURFACE` and tested at probe strength by `b5km-surfext-down10` (predicted live Δ ≈
0.000…+0.003, below the evidence floor).

## IR-86-CONC-18 — the pediment refinement of the dispersal rule FAILS its SGMC falsifier; instruments split; no slot change

**Observed** (session `arena/f29e1689`, `evidence/concentration_pediment_axis_20261023.json`; R0 rebuilt
byte-exactly first). The pre-rev-E SLOT_PLAN's pediment proposal (former proposal 2, `IR-86-TRACKB-08`
line) was built as three destination-regime splits of the `concb5kmdown4` shave: `concb5kmpeddown2p5`
(941 dots, 5.00 % chg, 100 % in-window), `concb5kmnonpeddown2p5` (941 dots, 100 % out-window,
attribution control), `concb5kmpeddown5` (1,882 dots, 10.00 % chg, 55.6 % in-window). The truth-free
pediment window (3DEP `relief_local` 10–40 m, > 1 km from the RELIEF regime front; 18.8 % of the
footprint) **caps at 1,045 moved dots** under the > 3 px / √8 px rules — a *window-specific* capacity
beside `IR-86-CONC-12`/`16`'s within-surface caps — so the pair is dose-matched at 2.5 % of R0.

1. **SGMC MODEL falsifier fired:** at the identical dose the non-pediment complement beats the
   pediment arm (+0.0013 vs +0.0007; REF `concb5kmdown4` +0.0015 replicates the recorded value
   exactly). As far as mapped-fault truth can tell, the dispersal gain is **generic sparse-ridge
   coverage**, not the thin-alluvium concealed-fault prior.
2. **Displacement is matched** (mean 1,612.7 vs 1,630.8 px; median 1,597.3 vs 1,582.3), so
   `IR-86-CONC-15`'s outward-movement bias is common-mode across the pair and cannot explain the
   ped/nonped gap — but it inflates both vs R0, which is why the quoted read is arm-vs-arm, not
   arm-vs-zero.
3. **The symmetric fold-fair d28 `PROXY` orders the arms oppositely** (+0.0012 in-window vs +0.0004
   out-window, CIs straddling/near zero): the attribution is *split*, not resolved. No arm clears the
   0.01 live-evidence floor (max |Δ| = 0.0017).
4. **Dose** is near-linear on SGMC (+0.0007 → +0.0017 at 2×) but the 2× dose pushes the 1 km CV to
   0.5013, below the (already demoted, `IR-86-CONC-13`) CV-band's lower edge.

**Decision.** No slot change: slots stay exactly as rev E ranks them (`le3p000`, `conc6`/`concb5kmdown6`,
`frontp15`). The three pediment arms are recorded `BUILT` audit artifacts and are **never upload
candidates**. Any future pediment-restricted CONCENTRATION design is capped at ~2.8 % of R0's dots by
destination capacity. The 10 km CV definition was pinned to `IR-86-TRACKB-08` (fully-covered 100 px
blocks: R0 = 0.5699 vs 0.736 unfiltered — both now reported by
`gems86.concentration_pediment.cv_report`).
## IR-86-CONC-17 — concurrent-session collision: two independent sessions built the same down-dose ladder; one build is byte-identical

**Observed.** This session (`arena/4822aa3b-gemsdoe86`, PR #55) and the concurrent PR #50 session
(`arena/60ecf1c8`) both self-assigned CONCENTRATION, both extended the `b5km-cvband-down4` dose
curve, and both named their artifacts `run_concentration_dose.py` / `variants_concentration_dose.json`.
PR #50 merged first (with `cvband-down3` `ffb47d4b`, `cvband-down5` `a2f8aaad`, `cvband-down6`
`1ed78e0f`, and a `CONTROL-cvband-down6-randcredit` `a6838dc2`). On merging origin/main for PR #55,
this session's `b5km-cvband-down6` proved **byte-identical** to PR #50's `conc6` (same zeros sha256
`1ed78e0f…`) — the same deterministic pipeline and dose from two independent runs, which is itself
a reproducibility datum. This session's other two rungs are new: `b5km-cvband-down2` (`f0ee647f`,
753 moves — a point below PR #50's lowest rung) and `b5km-cvband-downmax` (`d4a42664`, 2,381 moves —
the exact binary-searched sparse-ridge destination-pool ceiling), which confirm `IR-86-CONC-12`'s
"≈ 6.4 % of R0" capacity cap with the precise number (2,381 = 6.32 %) and show the marginal 122
moves past `conc6` cost more than they bought (`+0.0020` vs `+0.0022` MODEL, both 4/4 quadrants).
This item was first drafted as "IR-86-CONC-12" before main's numbering was known; 12/13/14 are
taken (`IR-86-CONC-14` is PR #50's own canary item), so it is renumbered here.

**Decision.** This session's `down6` is recorded `BUILT-DUPLICATE` (house pattern:
`gems86-h33-2b2-prune3` `collar3px`), pointing at PR #50's `conc6` BUILT row; files renamed to
`scripts/run_concentration_dose_rungs.py`, `tests/test_concentration_dose_rungs.py`,
`ledger/variants_concentration_dose_rungs.json`, `evidence/concentration_dose_axis_20261023.json`;
`down2`/`downmax` recorded `BUILT` as curve brackets, not slot candidates (Slot 2 stays `conc6`
per rev. D). No slot was spent; the exact-hash duplicate is kept in the ledger rather than deleted,
because two independent byte-identical builds is evidence the down-mechanism dose ladder is
reproducible, and the brief's dedupe rule is "exact hash and repeated (parent, axis, value)".

## IR-86-CONC-19 — IR-86-TRACKB-08's "R0 10 km CV = 0.570, inside 0.51–0.59" does not reproduce under the canonical block-density definition

**Observed.** `IR-86-TRACKB-08` and `SLOT_PLAN.md` proposal 2 state that at 10 km (100 px) every top-scoring file sits inside CV `0.547–0.570` with `R0 = 0.570`. Measuring R0 this session with the repo's canonical `gems86.concentration_5km.block_density_stats` (occupied blocks; density = dots / footprint cells per block) gives **0.7360** (complete blocks, 538 occupied) and **0.7331** (padded blocks, 547 occupied); count-CV variants give 0.6434 / 0.6422. No variant of the canonical definition reproduces 0.570, so the TRACKB session's 10 km numbers must come from a different (unrecorded) block accounting — e.g. a different occupied/valid rule or density normalisation.
**Decision.** Treat the *qualitative* TRACKB-08 observation (leaders cluster tightly at 10 km; the 0.1152 lidar file is an outlier) as unreplicated until re-measured under one stated definition, and do not quote `0.547–0.570` as a target band at 10 km. This session's 10 km builds therefore report CVs under the canonical definition only (R0 0.7360 → down4 0.5182, down8 0.4956, up8 0.5450) and the slot argument for dispersal rests on the two instruments, not on band membership. **Cost:** the "10 km CV law" cannot currently justify a slot by itself; re-measuring the 10 historical fleet files under the canonical definition is a zero-slot task for a future session.

## IR-86-SPT-01 — 2026-10-24 SPT candidate vs the negative-only release audit (SUPERSEDED BY `IR-86-SPT-02`)
`scripts/audit_release.py` only certifies the 10 registered historical artifacts as DO NOT SUBMIT and fails closed on any other TIFF under `docs/`. The new SPT candidate (sha256 `26cf2d39…`) therefore lived in `submission/` (linked from `docs/submit.html`), not `docs/downloads/` — **revoked and removed in `IR-86-SPT-02` below**.

## 2026-10-24 review — builder entrypoint bypass and freshness

- **IR-86-20261024-01 (repaired):** 22 later historical variant-builder mains (now **25**, adding `build_spt`, `build_xfleet`, and `gen_tip_final`) did
  not enforce the literal registry preflight; seven imported orchestration routes
  could also avoid CLI-only guards. Guarded before candidate work; missing evidence
  remains an error and `--no-write` does not authorize construction in memory.
  Shared evaluator/writer bytes and historical scientific evidence are unchanged.
- **IR-86-20261024-02 (repaired):** automated re-audits still rendered a dated
  2026-10-23 session card as "this session". Preserve that archive and additionally
  issue a current UTC, report/registry-hash-bound negative receipt only after fresh
  registry measurement; site builds reject stale or optimistic receipts.
- **IR-86-20261024-03 (open):** H33 page recommends a 177-character note, above
  this project's 140-character rule. Its HTML says projected/UNSCORED, not an
  organizer receipt for the owner-reported result. No current leaderboard or
  organizer acceptance was obtainable from the allowed-host network in this run.
- **IR-86-SPT-02 (repaired):** Commit `2538214` (PR #60) bypassed `protocol_preflight.require_feasible()` at module import in `scripts/build_spt.py` and `scripts/build_xfleet.py`, placed unregistered binaries `submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.{tif,zip,json}` (`sha256: 26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342`) outside `docs/downloads/`, published `docs/evidence/spt-run-card.json` (`verdict: "promote-candidate"`, `submission_ready: true`) and a hand-edited `docs/submit.html` (`READY TO DOWNLOAD`) contradicting `docs/index.html` (`DO NOT SUBMIT`), masked `dist_cat > 2.0` using the **full** `existing_faults.tif` catalogue (leaking withheld test-fold fault locations with zero split buffer), promoted a coin-flip surface (`canary_score_auc = 0.4947 < 0.50`) with `100%` literal witness overlap (`my_dots_within_3px_of_theirs = 1.0` against `17GEMSDOE`), and claimed signed paired-throw on `training_features.tif` bands 15/13/12 in `research/SPT_20261024.md` while `build_spt.py` never opened `training_features.tif` and ran with `SPT_PENALTY=0`. Remedied by removing the `submission/` binaries, gating `build_spt.py` and `build_xfleet.py` behind `require_feasible()`, revoking `spt-run-card.json` / `xfleet-run-card.json` / `spt-independent-validation.json` / `docs/submit.html` to `verdict: "negative"` (`DO NOT SUBMIT`), and hardening `audit_release.py` + `check_site.py` against `submission/` binaries and non-negative sidecar cards.
- **IR-86-TIPRELAY-01 (repaired):** Concurrent PR #63 (`502fc14`, `H86-TIPRELAY`) committed an unregistered GeoTIFF/ZIP (`docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.{tif,zip,json}`, `sha256: c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3`), inserted a `tiprelay` filename exclusion backdoor into `scripts/audit_release.py`, added `scripts/gen_tip_final.py` executing at import time without `protocol_preflight.require_feasible()`, wrote `"verdict": "promote"`, `"submission_ready": true`, `"holdout_dti": {"status": "PROJECTION_NOT_HOLDOUT"}` in `docs/evidence/h86-tiprelay-run-card.json` with zero spatially-blocked holdout evaluation, and hand-edited `docs/index.html` and `docs/executive-summary.html` with escaping `../research/` links that broke `build_site.py --check`, `check_site.py`, and `audit_downloads.py`. Read-only measurement via `gems57.uniqueness.compare_to_registry` proved `my_dots_within_3px_of_theirs = 0.8508 > 0.70` even against sparse `GEMSDOE32` `h33-h33-2-b2` (`0.8510 > 0.70` vs `GEMSDOE28`, plus `1.0 > 0.70` vs `17GEMSDOE`). Remedied by removing the unregistered `docs/downloads/gems86-h86-tiprelay-*` files and `audit_release.py` backdoor, gating `scripts/gen_tip_final.py` behind `require_feasible()`, revoking `docs/evidence/h86-tiprelay-run-card.json` to `verdict: "negative"`, and regenerating `docs/*.html` from `scripts/build_site.py`.
- **IR-86-PROMPT-CONFLICT-20261024 (flagged):** The 2026-10-24 request states both `Current competition leaderboard GEMSDOE high score: 0.4413` and `0.3195 is the highest score right now`, and lists 92 sites (`GEMSDOE`..`GEMSDOE92`) of which 6 (`GEMSDOE86`, `GEMSDOE88`..`GEMSDOE92`) have empty `:` lines. Preserved verbatim in `research/REQUEST_20261024.md` as unverified `OWNER-REPORTED` input; missing entries stay blank (`None`), never `0.0`.
- **IR-86-USGS-504-20261024 (flagged):** `https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and` returned `HTTP 504 Gateway Time-out` during live recheck on 2026-10-24; official GeoDAWN DOI `https://doi.org/10.5066/P93LGLVQ` (Glen & Earney 2024) was verified directly in `https://docs.nlr.gov/docs/fy26osti/96647.pdf`.

See `research/SESSION_20261024_REVIEW.md` and
`docs/evidence/source-recheck-20261024.json` for exact scope and unresolved blockers.
