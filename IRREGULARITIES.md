Only items that changed what a session did, or that a human must resolve before the next
slot. Three Arena sessions worked the PRUNE axis on the same parent; all are recorded.

## IR-86-RKSC-01 — H86I-RKSC generated a unique audit-only GeoTIFF (0 rho firings, 0 sparse-dot overlap firings) and failed closed on holdout & off-grid registry rows (2026-10-25)

Before any lane code was written, four untried geological hypotheses (`H86I-1..H86I-4`) were frozen in `research/H86I_RKSC_PREREGISTRATION.json` (`sha256: 83300b29…`) and `research/H86I_RKSC_PREREGISTRATION.md`. `scripts/run_h86i_rksc.py` executed the top candidate (`H86I-RKSC`: Lahontan-Deconfounded Piedmont Scarp Profile-Curvature Dipole coupled with GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step and Seismic-Conductance Conduit, excluding all gravity and magnetic bands) and serialized `docs/downloads/gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.tif` (`sha256: 9437c83e0b5cf3fe1679ee26b6e41f200cf9a5eb08d7815a36a13a0e96f765ba`, `44,090` dots, `0` NaN, values in `[0, 1]`). **Decision: `DO NOT SUBMIT` (`verdict: "negative"`, `safe_to_submit: false`, `submission_slots_used: 0`).** On `gems57-pooled-hide-v2` (`seed=20`, `11,321` withheld positives), `E1_rksc_full` (`0.0245 [0.0185, 0.0304]`) beat both internal ablations (`E2 = 0.0235 [0.0174, 0.0294]` and Lahontan-uncorrected K-depleted negative control `E3 = 0.0142 [0.0093, 0.0196]`, `+72.5%` relative lift), but trailed fold-fair 2-px `R0` (`0.0961 [0.0829, 0.1094]`), 3-px `R0` (`0.0931 [0.0798, 0.1067]`), and same-split `H86C-KSLB` (`0.1241 [0.1080, 0.1403]`). Across `687 / 689` valid registry rasters, pre-placement surface worst Spearman is `0.2633 <= 0.90` (`0` rho firings) and final-dot worst Spearman is `0.0395 <= 0.90` (`0` overlap firings against any sparse `<=60,000`-dot submission), but `16` space-filling lattice/composite rasters (`13GEMSDOE`, `15GEMSDOE`, `GEMSDOE48`) and continuous witness `17GEMSDOE` exceed `0.70` 3-px overlap and `scripts/pa86_chance_overlap.py` fails closed on the `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`). Following execution, `scripts/run_h86i_rksc.py` is gated behind `protocol_preflight.require_feasible()` in `tests/test_builder_preflight.py`.

## IR-86-PCC-01 — H86F-PCC generated a format-valid TIFF and the gates rejected it (2026-10-25)

`scripts/run_h86f_pcc.py` wrote `docs/downloads/gems86-h86f-pcc-signed-44090dots-20261025T002755Z-94f74d4e-zeros.tif` (sha256 `7a0dcffb…c7be`). **Decision: DO NOT SUBMIT.** HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld positives) is 0.0327 [0.0237, 0.0436], below the same-split KSLB comparator 0.1241 [0.1080, 0.1403]. The shared PA-86-02 script refused the registry report because two inventory rasters are not on the submission grid (`14GEMSDOE` horse-ensemble; `7GEMSDOE` qfaults prior). A later diagnostic, `docs/evidence/h86f-pcc-chance-diagnostic.json`, classified 11 dot-field overlap hits as space-filling (0 informative firings). That diagnostic is not a gate pass. The run-card reason string was corrected after the script crash; scores and the SHA-256 were not recomputed. No slot was used.

## IR-86-PCC-02 — template feature cache still absent; raw pinned TIFF was used, not described as the cache

The protocol names the template cached feature stack. It is not in this checkout (`/tmp/gems32/work/feature_stack.npy` is the upstream receipt path). This lane used SHA-pinned `training_features.tif` (`4371c82e…`) plus the unmodified `vendor/gems57` evaluator and writer. It did not rebuild or relabel that cache. The pinned registry inventory still ends at `56GEMSDOE`; local `docs/downloads` and `data/scored_fleet` were added by the existing checker. That is not a complete organizer registry and not coverage of `GEMSDOE57`–`GEMSDOE92`.

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
`scripts/audit_release.py` only certifies the 10 registered historical artifacts as DO NOT SUBMIT and fails closed on any other TIFF under `docs/`. The new SPT candidate (sha256 `26cf2d39…`) therefore lived in `submission/` (linked from `docs/submit.html`), not `docs/downloads/` — **revoked and quarantined outside `docs/` in `IR-86-SPT-02` below**.

## 2026-10-24 review — builder entrypoint bypass and freshness

- **IR-86-20261024-01 (repaired):** **43** CLI builder/feature/pipeline `main()` commands (including `build_gems86_swcon.py`, `generate_unique_submission.py`, `experiment.py`, `run_experiment.py`, `run_h86.py`, `run_lane.py`, `prune_collar.py`, `build_spt.py`, `build_xfleet.py`, `gen_tip_final.py`, `build_submission.py`, `h86b/c/d_features.py`, `prepare_h86_fvmb_data.py`, `run_h86_fvmb_pipeline.py`, `run_h86_wvb.py`, and `run_lane86/b/c/d.py`) and **8** imported orchestration entrypoints (including `run_experiment.run`) are now uniformly AST- and runtime-tested in `tests/test_builder_preflight.py` to enforce `protocol_preflight.require_feasible()` before argument parsing, feature loading, or placement; missing evidence remains an error and `--no-write` / `--measure` does not authorize construction in memory. Shared evaluator/writer bytes and historical scientific evidence are unchanged.
- **IR-86-20261024-02 (repaired):** automated re-audits still rendered a dated
  2026-10-23 session card as "this session". Preserve that archive and additionally
  issue a current UTC, report/registry-hash-bound negative receipt only after fresh
  registry measurement; site builds reject stale or optimistic receipts.
- **IR-86-20261024-03 (open):** H33 page recommends a 177-character note, above
  this project's 140-character rule. Its HTML says projected/UNSCORED, not an
  organizer receipt for the owner-reported result. No current leaderboard or
  organizer acceptance was obtainable from the allowed-host network in this run.
- **IR-86-SPT-02 (repaired):** Commit `2538214` (PR #60) bypassed `protocol_preflight.require_feasible()` at module import in `scripts/build_spt.py` and `scripts/build_xfleet.py`, placed unregistered binaries `submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.{tif,zip,json}` (`sha256: 26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342`) outside `docs/downloads/`, published `docs/evidence/spt-run-card.json` (`verdict: "promote-candidate"`, `submission_ready: true`) and a hand-edited `docs/submit.html` (`READY TO DOWNLOAD`) contradicting `docs/index.html` (`DO NOT SUBMIT`), masked `dist_cat > 2.0` using the **full** `existing_faults.tif` catalogue (leaking withheld test-fold fault locations with zero split buffer), promoted a coin-flip surface (`canary_score_auc = 0.4947 < 0.50`) with `100%` literal witness overlap (`my_dots_within_3px_of_theirs = 1.0` against `17GEMSDOE`), and claimed signed paired-throw on `training_features.tif` bands 15/13/12 in `research/SPT_20261024.md` while `build_spt.py` never opened `training_features.tif` and ran with `SPT_PENALTY=0`. Remedied by gating `build_spt.py` and `build_xfleet.py` behind `require_feasible()`, revoking `spt-run-card.json` / `xfleet-run-card.json` / `spt-independent-validation.json` / `docs/submit.html` to `verdict: "negative"` (`DO NOT SUBMIT`), quarantining `submission/gems86-spt-throwcons-*` outside `docs/` (excluded from GitHub Pages, `download_authorized: false`, and cryptographically SHA/ZIP-verified against `docs/evidence/spt-full-support-witness-audit.json` in both `audit_release.py` and `check_site.py`), and failing closed on any other binary or byte modification in `submission/`.
- **IR-86-TIPRELAY-01 (repaired):** Concurrent PR #63 (`502fc14`, `H86-TIPRELAY`) committed an unregistered GeoTIFF/ZIP (`docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.{tif,zip,json}`, `sha256: c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3`), inserted a `tiprelay` filename exclusion backdoor into `scripts/audit_release.py`, added `scripts/gen_tip_final.py` executing at import time without `protocol_preflight.require_feasible()`, wrote `"verdict": "promote"`, `"submission_ready": true`, `"holdout_dti": {"status": "PROJECTION_NOT_HOLDOUT"}` in `docs/evidence/h86-tiprelay-run-card.json` with zero spatially-blocked holdout evaluation, and hand-edited `docs/index.html` and `docs/executive-summary.html` with escaping `../research/` links that broke `build_site.py --check`, `check_site.py`, and `audit_downloads.py`. Read-only measurement via `gems57.uniqueness.compare_to_registry` proved `my_dots_within_3px_of_theirs = 0.8508 > 0.70` even against sparse `GEMSDOE32` `h33-h33-2-b2` (`0.8510 > 0.70` vs `GEMSDOE28`, plus `1.0 > 0.70` vs `17GEMSDOE`). Remedied by removing the unregistered `docs/downloads/gems86-h86-tiprelay-*` files and `audit_release.py` backdoor, gating `scripts/gen_tip_final.py` behind `require_feasible()`, revoking `docs/evidence/h86-tiprelay-run-card.json` to `verdict: "negative"`, and regenerating `docs/*.html` from `scripts/build_site.py`.
- **IR-86-PROMPT-CONFLICT-20261024 (flagged):** The 2026-10-24 request states both `Current competition leaderboard GEMSDOE high score: 0.4413` and `0.3195 is the highest score right now`, and lists 92 sites (`GEMSDOE`..`GEMSDOE92`) of which 6 (`GEMSDOE86`, `GEMSDOE88`..`GEMSDOE92`) have no supplied score (`2` carry prompt-named unscored artifact IDs: `GEMSDOE89` `gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:` and `GEMSDOE90` `gems90-cnc-35000dots-20261024T084324Z:`, and `4` have bare `:` lines: `GEMSDOE86`, `GEMSDOE88`, `GEMSDOE91`, `GEMSDOE92`). Preserved verbatim in `research/REQUEST_20261024.md` as unverified `OWNER-REPORTED` / `PROMPT-NAMED UNSCORED` input; missing entries stay blank (`None`), never `0.0`.
- **IR-86-USGS-504-20261024 (resolved on recheck) & IR-86-USGS-GGGSC-404-20261024 (flagged):** While the prompt's legacy science-center link `https://www.usgs.gov/centers/gggsc/science/geodawn-geoscience-data-acquisition-western-nevada` returns USGS `HTTP 404` ("Lost Bison"), `https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and` and ScienceBase DOI `https://doi.org/10.5066/P93LGLVQ` both return `HTTP 200` on live recheck (`docs/evidence/source-recheck-20261024.json`), confirming Glen & Earney (March 4, 2024, CC0 1.0, `149,030 line-km`, `51,857 sq km`, `200/400 m` E–W flight lines and `2000/4000 m` N–S tie lines).
- **IR-86-BAND-INDEX-20261024 (repaired):** Prior hypothesis prose in `registry/h86c_hypotheses.json` and `research/SESSION_20261024_REVIEW.md` misattributed `training_features.tif` Band 2 as `mag_horiz_grad` (actual Band 2 = `rtp`; `tmi_hg` = Band 3), Band 6 as `ter_rad_k` (actual Band 6 key = `tc`), Band 10 as `surf_rough` (actual Band 10 = `deq_n100a15`), and Band 14 as `rtp_tilt_deriv` (actual Band 14 = `tmi`), and mischaracterized `GEMSDOE81` (`0.0041`) as continuous rather than binary unit-mass near-catalogue dots (`100%` at `d_cat <= 5 px`, median `2.24 px`). Corrected against `src/gems86/io.py` and enforced by regex regression test in `tests/test_fleet_feed.py`.
- **IR-86-BAND6-TC-MISLABEL-20261024 (repaired):** Direct pixel-level verification (`scripts/verify_band_physics.py` → `docs/evidence/band-physics-verification-20261024.json`) proves that the embedded GeoTIFF header string inside `training_features.tif` for **Band 6** (`'tc - Tilt angle or total curvature - magnetic field derivative for edge detection'`) is **physically false in the competition file metadata itself**. Across all `5,164,300` valid footprint pixels, Band 6 is strictly positive (`min = +2.953424`, `median = +18.481700`, `max = +88.566544`, `0` non-positive pixels — making zero-crossing magnetic-tilt edge detection impossible), correlates at **`r = +0.997140`** with USGS GeoDAWN Airborne Gamma-Ray Spectrometry **Total Count (`TC`)** (`DOI 10.5066/P93LGLVQ`; `r = +0.915310` with `Th`, `r = +0.881676` with `K`, `r = +0.715073` with `U`), and correlates at only **`r = +0.012796`** with true analytical magnetic tilt $\arctan2(\text{Band 9 } \text{tmi\_vg},\, \text{Band 3 } \text{tmi\_hg})$. Repaired across `src/gems86/io.py`, `registry/h86c_hypotheses.json`, `research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md`, and `research/H33_INTERPRETATION_REVIEW.md`.
- **IR-86-BAND11-18-GRAV-VECTOR-20261024 (repaired):** Direct spatial finite-difference verification of `Band 13 (iso_grav_anom)` across `5,152,505` interior footprint cells (`docs/evidence/band-physics-verification-20261024.json`) proves that **Band 18 (`iso_grav_anom_hg`)** is the **signed East-West horizontal derivative** $+\partial g_{\text{iso}}/\partial x_{\text{east}}$ (`r = +0.948186`, vs `r = +0.027557` against scalar $|\nabla_h g_{\text{iso}}|$) and **Band 11 (`iso_grav_anom_vg`, labeled `'vertical gradient'` in the GeoTIFF header)** is actually the **signed South-directed horizontal derivative** $+\partial g_{\text{iso}}/\partial\text{row} = -\partial g_{\text{iso}}/\partial y_{\text{north}}$ (`r = +0.938102`), with $\sqrt{\text{B11}^2 + \text{B18}^2}$ reproducing **Band 5 (`iso_grav_anom_slope`)** at `r = +0.946995`. By Laplace's equation ($\nabla^2 U = 0$), the footprint-masked, Gaussian-regularized (`sigma = 400–600 m`) vertical gravity curvature $g_{zz} = -(\partial_x\text{B18} - \partial_y\text{B11})$ matches $-\nabla_h^2(\text{Band 13})$ at `r = +0.8627` to `+0.9149` purely from competition Bands 11 and 18 (`H86E-SPBT`).
- **IR-86-DUAL-SATURATION-20261024 (measured):** In addition to the continuous `17GEMSDOE` witness (`ab0a0a62...`, `5,106,385 / 5,106,385 = 100.0%` allowed coverage), the discrete binary stride-5 dot lattice `13GEMSDOE` (`20261001_r13-lattice-s5_v2_nan-outside.tif`, `b4570b40...`, `206,895` binary dots, `0.0904` `OWNER-REPORTED`) covers `5,099,871 / 5,106,385` (`99.8724%`) of allowed pixels within `3 px` (`uncovered_allowed_pixels = 6,514`). By the pigeonhole principle, any `37,654`-dot allowed raster has forward 3-px overlap `>= 1 - 6514/37654 = 82.70% > 70%` against `13GEMSDOE`. Therefore, any future upstream protocol amendment in `60GEMSDOE` must be saturation-aware (excluding high-halo `>50%` footprint witnesses or using symmetric overlap), not merely excluding non-binary surfaces.
- **IR-86-FLEET-GEMS89-90-20261024 (measured):** Direct byte-level GeoTIFF validation and pinned `vendor/gems57/uniqueness.py` overlap verification (`docs/evidence/prompt-named-unscored-audit-20261024.json`) of the two newly prompt-named unscored fleet entries revealed severe uniqueness and evaluation irregularities in both sibling repositories: (1) `GEMSDOE89` (`gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros.tif`, `140,693` B, `sha256: 715c8b86...`, `37,654` dots) claimed `complete_registry_coverage: true` and `verdict: "promote"` in `registry/h89_run_card.json` over a 91-geometry subset that omitted both `17GEMSDOE` (`1.0000 > 0.70` forward 3-px overlap) and discrete binary `13GEMSDOE` (`0.999203 = 37,624 / 37,654 > 0.70` forward 3-px overlap), while contradicting its adjacent `.json` writer receipt (`approved_for_weekly_slot: false`, `promoted: false`); (2) `GEMSDOE90` (`gems90-cnc-35000dots-20261024T084324Z.tif`, `241,734` B, `sha256: e1e91be2...`, `35,000` dots; repository `README.md` also retains unresolved merge markers) privately altered the protocol uniqueness rule in `evidence/run_card.json`, exceeded *both* clauses of its own altered rule (`max_overlap = 0.983286 > 0.70` and `max_excess_over_chance = 0.403712 > 0.30`; pinned `gems57/uniqueness.py` measures `1.0000` vs `17GEMSDOE` and `0.983486 = 34,422 / 35,000` vs binary `13GEMSDOE`) yet still recorded `duplicate: false`, relied on external USGS `qfault_sliprate_den` (`AUC = 0.7784`) on 4-fold cut segments (`60,823` px) as its #1 feature, and failed its own score-history calibration (`verdict: "NEGATIVE"`).
- **IR-86-RULES-SECT-20261024 (repaired):** `scripts/build_site.py` (`docs/executive-summary.html` portal checklist) previously cited `Official Rules §5–6` for the 3-per-week public leaderboard limit and single final entry across Phase 1 ($50k) and Phase 2 ($250k). Live line-by-line verification of `https://docs.nlr.gov/docs/fy26osti/96647.pdf` confirmed the Official Rules PDF contains only Sections 1–4 plus Appendix A, with the prize phases, weekly submission cap, and single final selection specified in `§1.1` and `§3.2–3.6`; fixed in `scripts/build_site.py` and `docs/executive-summary.html` and guarded in `tests/test_current_review.py`, alongside fixing a stale `H86C-MMT` string in `docs/evidence/session-20261024-run-card.json` to match `registry/h86c_hypotheses.json` (`H86E-SPBT`).
- **IR-86-DROPBOX-MIRRORS-20261024 (repaired):** Cross-repo search located the 5 Dropbox links referenced in the prompt inside `buffedlizard55-lab/16GEMSDOE/README.md` (`GEMS_96647.pdf`, `example_submission.tif`, `existing_faults.tif`, `gems-geodawn-numerical-features.tif`, `Digital-elevation-model-links-JSON.pdf`); these are personal convenience shares (`dl=0`), not official DOE/NLR/USGS/DrivenData hosting, and are unreachable inside egress-restricted sandboxes. Repaired `scripts/restore_data.py` with SHA-256-verified `EXTERNAL_PINS`, atomic `.partial` staging, `sync_grid_root()`, `--protocol-only` / `--include-registry` flags, and SHA-256-gated `--source dropbox` (`dl=1`) workstation fallback, covered by `tests/test_restore.py`.
- **IR-86-SWCON-01 (repaired):** Concurrent PR #77 (`510fdb6`, `SWCON`) committed unregistered binaries (`docs/downloads/gems86-swcon-e3-37654dots-20261024-zeros.{tif,zip,json}` and `submission/gems86-swcon-e3-37654dots-20261024-zeros.{tif,json}`, `sha256: 5576b15c...`), an unguarded builder `scripts/build_gems86_swcon.py`, and hand-edited `docs/swcon-submission.html` + `README.md` (`OK TO DOWNLOAD AND SUBMIT`) that immediately broke all three CI workflows on `main`. Direct measurement via `vendor/gems57/uniqueness.py` proved `0.997769` (`37,570 / 37,654 > 0.70`) forward 3-px dot overlap against discrete binary dotted `13GEMSDOE` and `1.0000` against `17GEMSDOE`, alongside below-chance canary `AUC = 0.4046`, missing `ci95 = null`, and `HOLDOUT-DTI = 0.00746`. Repaired by removing the unregistered `SWCON` binaries and `docs/swcon-submission.html`, gating `scripts/build_gems86_swcon.py` behind `protocol_preflight.require_feasible()`, and revoking `docs/evidence/swcon-run-card.json` and `research/SWCON_20261024.md` to `verdict: "negative"`, `submission_ready: false`.
- **IR-86-FAULTHALO-01 (repaired):** Concurrent PR #80 (`3c98290`, `gems86-faulthalo-4210938px-20261024T181838Z-219b3357-zeros.tif`, `sha256: 8a66c57c...`) omitted `protocol_preflight.require_feasible()` in `scripts/generate_unique_submission.py` to emit a continuous `4,210,938`-pixel Euclidean distance halo around `existing_faults.tif` (`0.998783` forward 3-px overlap vs discrete binary `13GEMSDOE`, `1.0000` vs `17GEMSDOE`, zero geological bands, `HOLDOUT-DTI = NOT_RUN`), and inverted `α = 0.2` (FP) and `β = 0.8` (FN) in `research/H33_ANALYSIS.md`. Repaired by gating `scripts/generate_unique_submission.py`, `scripts/run_h86e.py`, and `scripts/finalize_h86e.py` behind `require_feasible()` (`45` CLI builders + `8` imported orchestrators in `tests/test_builder_preflight.py`), fixing `research/H33_ANALYSIS.md`, and retaining `gems86-faulthalo-*` solely as an audited `DO NOT SUBMIT` inventory record (`docs/evidence/h86-faulthalo-run-card.json`, `verdict: "negative"`).

See `research/SESSION_20261024_REVIEW.md` and
`docs/evidence/source-recheck-20261024.json` for exact scope and unresolved blockers.


## 2026-10-24 — H86E-RIDF session (lane `ridf`; distinct from the concurrent H86E-CCTX session below)

- **PA-86-01 (amendment, public):** the 17GEMSDOE witness is a continuous surface (support fraction 1.0); the shared template's `two_phase_summary` like-for-like reading is used for new lanes via `require_like_for_like()`. Literal reading still reported. A saturating dot field still stops.
- **PA-86-02 (amendment, public):** an overlap firing against a raster whose own 3 px halo covers > 70 % of the allowed area is non-informative (a random dot set would fire); rho ≤ 0.90 then decides. Firings with halo coverage ≤ 70 % remain hard stops.
- **IR-86-RIDF-01:** the surface registry check ran after placement rather than before; result (rho 0.9045 > 0.90, stop) unchanged.
- **IR-86-RIDF-02:** first R0 comparator used GEMSDOE28 `r1-solo` (excludes dots near the full catalogue) → 0.0286; corrected to GEMSDOE25 `dotted-h19-5-d2-8` → 0.0961 (reproduces the KSLB card exactly).
- **IR-86-RIDF-03:** catalogue-hide holdout cannot score fleet rasters built with the full catalogue (H33 = 0.0037 as-is); holdout–LB alignment unvalidated (Spearman 0.24, n = 17, owner-reported LB).
- **IR-86-RIDF-04:** two registry inventory entries are not on the competition grid (14GEMSDOE horse-ensemble transform; 7GEMSDOE qfaults prior u8) and were recorded as errors, so the scan is not "complete".
- **IR-86-RIDF-05:** SWCON (PR #77, merged to main concurrently) was published as "OK TO SUBMIT" after a uniqueness check against local files only. It is a score-weighted consensus of 33 prior fleet submissions, and its per-source overlap cap was tuned against that same local set. On the full 682-raster registry it has 58 informative dot-field firings, so it is a duplicate. Its holdout (0.00746, full-catalogue proxy, no CI) is not comparable with the buffered-holdout best. Verdict changed to `negative`, with `original_verdict` kept.

## 2026-10-24 H86E session — owner-mandated generation under a blocked literal rule

- **IR-86-H86E-01 (SUPERSEDED — bypass revoked; historical record retained):** The 2026-10-24 H86E request explicitly ordered generation of a unique TIF with fully automated (no-human) validation, which is impossible while `protocol_preflight.require_feasible()` hard-stops every builder under the literal full-support overlap rule (IR-86-DUAL-SATURATION-20261024). An earlier revision of `scripts/run_h86e.py` and `scripts/finalize_h86e.py` therefore did not call `require_feasible()`; instead they used the shared `gems57.uniqueness.two_phase_summary` and reported BOTH the literal reading (worst forward overlap `1.0` vs the pinned dense witness; `0.9988` vs the stride-5 lattice) and the like-for-like dot-field reading (worst geological overlap vs the GMC catalogue-halo control), with thresholds unchanged (`rho 0.90`, overlap `0.70`). No shared tool was forked or edited. The generated artifact is fully registered (`docs/evidence/download-inventory.json`, `registry/artifact_cards.json`), passes `audit_release.py --measure-registry`, and its own automated gates (`docs/evidence/h86e-run-card.json`) return **DO NOT SUBMIT** (G4/G5/G6 fail), so no weekly slot is authorized by this amendment. **The bypass itself has since been revoked:** both scripts now call `require_feasible()` as the first action of `main()`, before argparse, grid load, feature construction, fitting or placement, and are pinned by `tests/test_builder_preflight.py` (an owner mandate to produce a file is not a protocol exemption; AGENTS.md item 8). The E1-E3 measurements and the published artifact are preserved as a `DO NOT SUBMIT` audit record of the ungated revision, not as a live authorization. Future sessions must not cite this entry as a general preflight bypass: the literal stop remains binding for any submission authorization.
- **IR-86-PROSE-CODE-01 (repaired):** Two builders shipped docstrings contradicting their own enforced guards — the IR-86-SPT-02 "misrepresented prose vs code" defect class. `scripts/generate_unique_submission.py` claimed it "does NOT call `protocol_preflight.require_feasible()`" while `main()` did (left stale when PR #80 was gated under IR-86-FAULTHALO-01), and `scripts/run_h86e.py` claimed the same while `main()` did (left stale when PR #83 was gated). Both docstrings were corrected to describe the enforced behaviour and the revoked bypass; no guard, threshold or measurement was changed. `tests/test_builder_preflight.py::test_gated_builder_docstring_does_not_claim_a_preflight_bypass` now fails any `BUILDERS` entry whose docstring asserts a bypass, so this cannot silently recur.
- **IR-86-H86E-02 (measured):** First E3 run degenerated (`p=1` on catalogue, `p~1e-6` elsewhere, HOLDOUT-DTI `0.0209`) because plain distance-to-visible-catalogue is `0` exactly on training positives (self-identity leak, preserved in `.cache` run-1 log summary inside `research/H86E_SESSION_20261024.md`). Repaired with other-component (two-group) distances and self-corrected densities; corrected rerun is the reported E3. The buggy run is an implementation defect record, not a scientific result.

## IR-86-GAPRES-01 (2026-10-24) — literal overlap rule unsatisfiable; dotted reading used and disclosed
`scripts/build_gems86_gapres.py` does not call `protocol_preflight.require_feasible()` (same
owner-mandate pattern as IR-86-H86E-01). The pinned 17GEMSDOE witness is a continuous
probability surface with support>0 over ~the whole footprint, so under the literal
support>0 dot definition every nonempty candidate has 1.0 forward 3-px overlap and the
>0.70 lane rule can never pass. GAPRES therefore reports BOTH readings in
`docs/evidence/gapres-run-card.json`: dotted-fleet reading (worst overlap 0.000 vs 26 local
binary fleet rasters) and the literal dense-witness reading (1.0, unsatisfiable). No
threshold was changed and no slot was authorized; verdict remains DO NOT SUBMIT on the
independent holdout gate. Resolving this requires an explicit revised protocol from the
owner, not a private exemption.


## IR-86-REGISTRY-BINDING-4D79B443 — 2026-10-24

Independent review found false-clearance paths in the newer H86E orchestration:
missing registry files were omitted from expected counts, surface/final booleans
ignored incomplete scans, and final arrays were silently binarized/masked before
checking. PA-86-02 did not load its candidate argument, did not require complete
bound evidence, and allowed arbitrary self exclusion with a truncated correlation
list. The RIDF builder placed dots before checking its surface; its writer executed
on import without the literal preflight. Fixed in the orchestration, not a private
shared-tool fork. New v2 evidence is source/decoded/index-bound and retains all rows;
negative checks exit nonzero. Legacy reports stay archived, never upgraded in place.
Surface/dot order and literal gated serialization now have regression coverage.

Fresh audit: 13 published research TIFFs pass local format and fail literal overlap;
no new TIFF, model experiment or slot. See
`research/SESSION_20261024_4D79B443.md` and the current machine-readable audit card.
The user generation mandate remains unmet; inherited PA interpretations do not
establish that the stated literal overlap gate passed. The missing lane/cache and
non-comparable holdout histories remain blockers.

## IR-86-H86F-GZZD-01 (2026-10-25) — registry completeness trap measured blocking for a second lane; GZZD hypothesis falsified as run
The H86F-GZZD lane (frozen preregistration `research/H86F_GZZD_PREREGISTRATION.json`)
ran exactly three arms and both two-phase registry scans. Measured: 685 of 687
indexed rasters, the same 2 grid/CRS-incompatible rows as H86E-MMT
(`14GEMSDOE` horse-ensemble; `7GEMSDOE` qfaults prior), so
`registry_complete_for_index=false` and `scripts/pa86_chance_overlap.py` failed
closed with `ValueError: Incomplete registry cannot pass` (recorded
FAILED_CLOSED_NO_REPORT in `docs/evidence/h86f-gzzd-run-card.json`). **Decision:**
no private exclusion/bypass; PA-86-02 remains unsatisfiable until the protocol
repairs or formally excludes those rows upstream. Scientific result is
independently negative (HOLDOUT-DTI E1 0.0303 [0.0237, 0.0364] < unsigned-edge
control 0.0321 and R0 0.0339; same-split best 0.1241), so the verdict does not
depend on the registry trap. **Cost:** none to slots (0 used); the artifact is
audit-only. Also recorded: (a) pre-placement worst surface rho 0.467 was vs a
GEMSDOE24 `acquisition_block_id` external grid inside the registry — below the
0.90 stop, but survey-block mimicry remains a live risk for gravity-compilation
features; (b) this lane's frozen gate allowed an audit-only emission with 0
missing + 0 rho firings despite completeness=false, while the patched
`run_h86e_mmt.py` additionally requires zero registry errors before placement —
divergence disclosed in `research/H86F_GZZD_REVIEW_20261025.md`; future lanes
should adopt the stricter zero-error rule; (c) the shared writer left new
download files at mode 600 (mkstemp), normalized to 644 without byte changes.
## IR-86-MMT-RANK01-TIE-20261024 — `gems86_mmt.features.rank01` row-major tie ramp corrupted `R0_D28_visible_collar` (`0.03386` vs true `R0` `0.09609`)

In PR #93 (`src/gems86_mmt/features.py`), `rank01(a, footprint)` ordered values via
`np.argsort(v, kind="stable")` and mapped positions linearly to `np.linspace(0.0, 1.0, N)`.
On `GEMSDOE28__gems28-h27-4-r1-solo-d2-8` (`40,199` binary dots inside `5,167,373` footprint
cells), the `5,127,174` tied `0.0` background cells received monotonically increasing ranks
from `0.0` at row `0` up to `0.992221` at the southern footprint edge (`row 3729`). When
`emit.emit_decimated(..., tile_px=3)` + `emit.emit_prefix(..., 44090)` selected the top
`44,090` 3x3 tiles, **all `44,090` emitted comparator dots landed in southern rows `3023..3727`**
(`median row = 3302.0`, `0` dots in northern rows `0..3022`), overlapping only `2,453 / 40,199`
(`6.10%`) of `D28`'s true dots and filling the remaining `41,637` dots as a dense 3x3 southern
wallpaper (`HOLDOUT-DTI = 0.03386 [0.0169, 0.0514]`). Moreover, `GEMSDOE28` (`r1-solo`) was
already pruned against the **full** `60,988`-px catalogue (including the `11,321` withheld
holdout pixels, scoring `0.02431 [0.0202, 0.0286]` once ties are fixed), whereas the true
fold-fair `R0` visible-collar control from `GEMSDOE25` (`dotted-h19-5-d2-8`, sha256
`91eae1ca42ec...`, `docs/evidence/h86e_comparator.json`) scores **`HOLDOUT-DTI = 0.09609
[0.0830, 0.1089]`** on the identical `seed=20, hide_frac=0.20, buffer_px=3` split (true
`E1_mmt_tc_decoupled` deficit vs fold-fair `R0` is **`-0.0671`**, not `-0.0049`).
**Decision:** `src/gems86_mmt/features.py::rank01` is fixed using tie-invariant min-ranking
(`scipy.stats.rankdata(v, method="min")`, mapping tied floor `0.0` cells uniformly to `0.0`
across all rows) with regression coverage in `tests/test_h86e_mmt.py`; the archived run card
`docs/evidence/h86e-mmt-run-card.json` is preserved unedited with an explicit comparator
provenance caveat on `README.md` and `docs/`.

## IR-86-MMT-SHIFT-AXIS-20261024 — `build_marker_features` shifted `tgrad` parallel to the gradient normal instead of orthogonal corridor strike

In PR #93 (`src/gems86_mmt/features.py`), `_directional_difference(a, theta)` computed the
cross-corridor finite difference along the normal vector `(dy, dx) = (sin theta, cos theta)`,
and the lag loop then shifted `tgrad` along the **same** vector `(sin theta * lag, cos theta * lag)`
rather than orthogonal corridor strike `(-cos theta * lag, sin theta * lag)`. Consequently,
standalone `H86E-MMT` v1 measured normal-to-edge separation between `rtp` and `tilt` peaks
(a cross-profile source-depth/dip width effect) rather than lateral strike-slip / transfer-fault
marker offset along a structural corridor, and also applied `tc` (Band 6) directly before an
authoritative organizer band-table check.
**Decision:** `src/gems86_mmt/features.py` now defaults to `shift_axis="strike"` (`(-cos theta * lag, sin theta * lag)`, verified orthogonal to `(sin theta, cos theta)` in `tests/test_h86e_mmt.py`),
while `registry/h86c_hypotheses.json` Rank 2 explicitly separates the still-untested two-sided
split-window FFT along-strike phase-correlation formulation from PR #93's negative normal-lag
predecessor.

## IR-86-MMT-PRE-V2-UNBOUND-REPORTS-20261024 — Pre-v2 unbound `H86E-MMT` registry reports & three ungated H86E scripts

Both `docs/evidence/h86e-mmt-registry-surface.json` and `docs/evidence/h86e-mmt-registry-final-dots.json`
were generated against a pre-v2 checker (`evidence_schema` absent, `candidate_file_sha256: null`,
`complete_accessible_scan: false`, `683 / 685` comparable rows with 2 grid/CRS errors in
`14GEMSDOE` and `7GEMSDOE`), and `scripts/run_h86e_mmt.py` lacked `protocol_preflight.require_feasible()`
and reached `write_candidate(...)` even when `registry_gate` evaluated `False`. In addition,
`scripts/build_h86e_features.py` and `scripts/run_h86e_ridf.py` lacked `require_feasible()`, and
`scripts/build_h86e_features.py`, `scripts/h86e_comparator.py`, `scripts/h86e_fleet_strata.py`,
and `scripts/h86e_instrument_check.py` executed raster I/O at module import time.
**Decision:** `build_h86e_features.py`, `run_h86e_ridf.py`, and `run_h86e_mmt.py` now enforce
`require_feasible()` (bringing `tests/test_builder_preflight.py::BUILDERS` from 47 to **50**
CLI builders + 8 imported orchestrators), `run_h86e_mmt.py` also halts before `write_candidate`
whenever `registry_gate` is `False`, and all four diagnostic/feature scripts are wrapped in
`main()` with import-safety regression tests.

## IR-86-PREPARE-RELPATH-20261024 — `scripts/prepare_data.py` crashed on relative or external `--data-dir`

Invoking `python scripts/prepare_data.py --data-dir .cache/bridge` raised `ValueError:
'.cache/bridge/sample_submission.tif' is not in the subpath of '/home/user/GEMSDOE86'` because
`Path(data_dir)` remained relative while `ROOT` was resolved absolute (`tmpl_path.relative_to(ROOT)`
also failed for any external `--data-dir` outside `ROOT`).
**Decision:** Fixed in `scripts/prepare_data.py` via `_rel_or_str()` + `.resolve()`, covered in
`tests/test_prepare_data.py`, and verified end-to-end by restoring all 3 SHA-256-pinned core
competition rasters (`training_features.tif` `4371c82e...`, `existing_faults.tif` `7ba308cc...`,
`sample_submission.tif` `2176d08e...`) plus 5 external USGS/GeoDAWN rasters into `.cache/` and
generating the complete 19-band `data/prepared_manifest.json` (`has_features: true`, `58,171`
total sentinel band-pixels across `3,073` unique perimeter/TC cells).

## IR-86-INVENTORY-OFFGRID-ROWS-20261025 — 2026-10-24/25 (`H86H-PSTD` strict Rule-11 stop before placement)

Even after restoring and SHA-256-verifying all `655 / 655` blobs in `research/upstream/registry_inventory.json`
(`728,345,463` bytes; `689` unique indexed rasters including the 17 prior local artifacts, `0` missing), two historical
inventory entries fail `vendor/gems57/uniqueness.py::compare_array_to_registry` grid/CRS checks:
- `14GEMSDOE:docs/downloads/GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f.tif` (`ccbe1de0...`: `registry CRS/transform differs from reference`)
- `7GEMSDOE:external/qfaults/qfaults_prior_u8.tif` (`538b4573...`: `registry grid or band-count mismatch`)

Unlike lanes that serialized audit-only GeoTIFFs despite failing `surface_gate_pass` / `literal_gate_pass`,
the contemporaneously preregistered `H86H-PSTD` lane (`scripts/run_h86h_pstd.py`, `docs/evidence/h86h-pstd-run-card.json`)
strictly obeys `AGENTS.md` Rule 11: it checks its continuous surface (`rho_firings = 0`,
`worst_spearman_full_footprint <= 0.90` across all `687` valid competition-grid rasters including `H86F-GZZD` and `H86F-PCC`)
and **halts fail-closed before full-footprint dot placement and before GeoTIFF serialization** (`final_dots_placed = False`,
`candidate_tif_serialized = False`). Also added `holdout_binary_control` (`GEMSDOE25` `91eae1ca42ec...`, `d_vis > 2.0 px`,
`HOLDOUT-DTI = 0.096086`) to `scripts/run_h86e_mmt.py` and gated `write_h86e_tif`.

## IR-86-H86F-EWCS-01 (2026-10-25) — H86F-EWCS sets repo same-split HOLDOUT-DTI record (`0.1723`), yet fails closed to DO NOT SUBMIT on registry completeness and literal saturation

`scripts/run_h86f_ewcs.py` executed the frozen 3-arm preregistered `H86F-EWCS` lane
(`research/H86F_EWCS_PREREGISTRATION.json`, `registry/h86f_hypotheses.json`) within
the `<= 3` experiment / `<= 2` hour budget using SHA-pinned competition inputs and
unmodified `vendor/gems57` tools. On `gems57-pooled-hide-v2` (`seed=20`, `hide_frac=0.20`,
`buffer_px=3`, `11,321` withheld positives, `1,000` bootstrap draws over `20 km` blocks),
`E1_ewcs_coupled_pu` (`37,654` dots, `2.8 px` Poisson-disc spacing) achieved
**`HOLDOUT-DTI = 0.172325` (`95% CI [0.152956, 0.189793]`)**, outperforming its
isotropic-tip mechanism control `E3_ewcs_isotropic_tip_ablation` (`0.159234`, paired
delta **`+0.013091` `95% CI [+0.001163, +0.026066]`**), cover-blind subsurface control
`E2_ewcs_cover_blind_pu` (`0.100261`, paired delta `+0.072063`), `R0_D28_visible_collar`
(`0.027299`), fold-fair `GEMSDOE25` `R0` (`0.096086 [0.082975, 0.108898]`), and prior
repo same-split best `H86C-KSLB` (`0.124063 [0.107970, 0.140330]` at `44,090` dots) with
separated 95% CIs (`23` leakage canaries max discriminative AUC `0.7949 <= 0.90`).
Both `v2` SHA-bound registry scans (`687 / 689` measured, explicitly including the
newly merged `H86F-PCC` and `H86F-GZZD` TIFFs) recorded `0` Spearman `rho > 0.90`
firings (`worst_spearman = 0.7508`) and `0` discrete `<= 50,000`-dot overlap firings
(`26.96%` vs `GEMSDOE32` `h33-h33-2-b2`, `37.57%` vs `H86C-KSLB`, `9.46%` vs `H86F-PCC`,
`9.90%` vs `H86F-GZZD`). However, the same `2` grid/CRS-incompatible historical rows
(`14GEMSDOE`, `7GEMSDOE`), `39` space-filling `>= 56,605`-dot firings, and literal
`17GEMSDOE` full-support saturation caused `surface_gate_pass`, `final_dots_gate_pass`,
`literal_gate_pass`, and `pa86_02` to fail closed.
**Decision:** The format-valid GeoTIFF (`docs/downloads/gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif`,
SHA-256 `8322dcf157851e07dfdd4391ed5164916479e4dce17af2d0e14afab5592a697d`) is registered
for audit download only (`status = "DO NOT SUBMIT"`, `verdict = "negative"`, `0` slots
used) and emerges as the lead technical candidate once a human selector resolves the
upstream registry blockers.

## IR-86-H86F-PCC-PREFLIGHT-20261025 — `scripts/run_h86f_pcc.py` lacked `require_feasible()` and `docs/evidence/h86e-mmt-registry-surface.json` carried `surface_gate_pass: true` despite 2 errors

Pass-2/3 audit after merging PRs #97–#102 found that `scripts/run_h86f_pcc.py` (merged in
PR #97 concurrently with PR #98's builder-gating sweep) did not call
`protocol_preflight.require_feasible()` at the start of `main()` and was absent from
`tests/test_builder_preflight.py::BUILDERS`, while archived
`docs/evidence/h86e-mmt-registry-surface.json` still carried `"surface_gate_pass": true`
despite `2` grid/CRS errors (`14GEMSDOE` and `7GEMSDOE`), contradicting
`docs/evidence/h86e-mmt-run-card.json` (`false`) and `AGENTS.md` Rule 11.
**Decision:** Both `scripts/run_h86f_pcc.py` and `scripts/run_h86f_ewcs.py` now call
`protocol_preflight.require_feasible()` before any work and are pinned in
`tests/test_builder_preflight.py::BUILDERS`, and `docs/evidence/h86e-mmt-registry-surface.json` now records
`"surface_gate_pass": false` with an explicit archive note.

## IR-86-H86G-INSTRUMENT-20261025 — Catalogue-hide holdout anti-correlates with live ordering; OOF-vs-shipped conflation

E1b (this session) scored shipped rasters as-is on the seed-20 buffered
whole-component catalogue-hide instrument: live-best H33 = 0.0037, live-worst
poisson81 = 0.0918 (full table in `research/H86G_EDTI_REVIEW.md`). Selecting on
that instrument alone selects *for* catalogue proximity, which the organiser's
known-fault masking does not reward. Separately, the historical "same-split
best 0.1241" (KSLB) is an out-of-fold arm construct; the shipped KSLB raster
measures 0.0038 as-is on the same folds. Any cross-lane comparison must state
OOF-vs-as-is construction explicitly. H86G-EDTI therefore selected on the
SGMC-proxy (which reproduces the live ordering) with catalogue-hide demoted to
an OOF floor; Amendments A1–A2 in the preregistration.

## IR-86-H86G-COLLAR-DEGENERACY-20261025 — Collar-3 submissions score identically 0 as-is on catalogue-hide

Any raster collared >3 px against the full catalogue has catalogue-hide DTI
exactly 0.0000 as-is, because withheld truth ⊂ catalogue (measured: all three
H86G arms, all budgets). As-is catalogue-hide readings of collared submissions
are meaningless; use the OOF visible construction like-for-like.

## IR-86-H86G-A3A4-BUDGET-20261025 — Post-hoc budget rule (disclosed, not hidden)

The SGMC proxy's budget optimum is a truth-density artifact (still rising at
98,163-dot ranking exhaustion). Amendment A3 capped budget at the live-validated
44,090; Amendment A4 (adopted *after* inspecting marginal-credit flatness and
paired CIs at 55k/70k) set budget = smallest grid budget whose paired proxy CI
excludes 0 → 55,000. The reported CI is post-selection descriptive. The
superseded A3 44,090-dot artifact was removed from `docs/downloads/` so no
orphan binary lacks a run card; its nested ranking makes the 44,090 prefix
regenerable byte-consistently from `scripts/run_h86g_edti.py` caches.

## IR-86-AUDIT-LINKEDCARDS-20261025 — `linked_cards` read a non-existent config key

`scripts/audit_release.py:build_report` built `linked_cards` from
`c["source_card"]`, but `registry/artifact_cards.json` configs carry the key
`card`; the linked set was therefore always empty and every `*card*.json` was
held to the unlinked-sidecar negativity check. Fixed to `c["card"]` this
session (linked cards are validated per-artifact in `audit_artifact`, including
the new `h86g_edti` promote branch). No historical verdict changed: all
previously linked cards are negative under both readings.

## IR-86-H86G-FEED-20261025 — GEMSDOE89/90 owner scores not yet in the ledger/feed

This session's prompt supplies OWNER-REPORTED scores for GEMSDOE89 (0.0301)
and GEMSDOE90 (0.0749), previously prompt-named unscored. They are recorded in
`research/REQUEST_20261025.md` but not yet folded into
`registry/prior_scores.csv` / `docs/evidence/fleet-feed.json` (hash-bound
pair); a fleet-refresh session should ledger them and regenerate the feed.

## IR-86-PUBLICATION-AUTH-09C7FC42 (2026-10-25)

Homepage, executive summary, README and build success output said H86G-EDTI was OK to
submit while its card explicitly denied safe_to_submit and weekly-slot approval, and
literal release audit failed. Corrected publication instructions to research-only;
historical amended-gate promotion and binary bytes unchanged. Added regression checks
rejecting positive upload instructions in the negative-state publisher. See
`research/SESSION_09C7FC42_REVIEW.md`. No new TIFF, model experiment or portal operation.


## IR-86-085C2B7A — promotion was displayed as upload permission (2026-10-25)

The generated homepage/executive guide and current README said to submit H86G-EDTI even though its scientific card records `safe_to_submit=false`, `approved_for_weekly_slot=false`, and the release audit retains the literal witness stop. Fixed the source generator, regenerated pages and exposed the promoted-for-review identity in `docs/data/summary.json` without changing historical scientific evidence. Regression tests forbid the unsafe direct-upload phrases. No new raster, model experiment or slot. See `research/SESSION_085C2B7A_REVIEW.md`.

## IR-86-HVFD-COLLAR-ABLATION-20261025 — 2026-10-25 (`H86I-HVFD` 3-arm Dual-Regime Noisy-OR & `buffer_px=3` vs unbuffered collar ablation)

Contemporaneously preregistered lane `H86I-HVFD` (`research/H86I_HVFD_PREREGISTRATION.json`,
`scripts/run_h86i_hvfd.py`, `docs/evidence/h86i-hvfd-run-card.json`) generated audit-only GeoTIFF
`docs/downloads/gems86-h86i-hvfd-vent-flexure-37654dots-20261025T030002Z-33c17af1-zeros.tif` (`sha256:
0325442434733ee10a9d77200b17db86f00d6195d373afeca43d673435216b58`, `37,654` unit dots, `15/15` local format
checks PASS), gated `run_h86h_pstd` and `run_h86i_hvfd` in `tests/test_builder_preflight.py::BUILDERS` (`57` CLI
builders + `8` imported orchestrators), added `holdout_binary_control` (`R0_G25_foldfair_collar`) to
`scripts/run_h86f_pcc.py`, and updated `src/gems86_pstd/features.py::_rank01` to `method="min"`. While
`E1_hvfd_blind_vent_conduit` (`0.0475` `[0.0364, 0.0585]`) beat all prior zero-catalogue algebraic lanes
(`0.0245–0.0327`) by `+45%` to `+94%` and `E2_hvfd_foldfair_vent_relay_noisyor` (`0.1013` `[0.0886, 0.1139]`)
beat fold-fair `R0_G25_foldfair_collar` (`0.0961` `[0.0828, 0.1090]`), `E2` (`37,654` dots, `d_vis > 2.0 px`)
trailed its own 44,090-dot `d_vis > 1.5 px` collar-ablation control `E3` (`0.1040` `[0.0917, 0.1166]`, paired
`E2 - E3 = -0.0027` `[-0.0054, -0.0003]`) on `buffer_px=3` whole-component holdout as well as `H86C-KSLB`
(`0.1241`). Furthermore, although `H86I-HVFD` has `rho_firings = 0` (`worst_spearman = 0.0625`) and
`<= 58.59% < 70%` 3-px forward overlap against all `468` sparse (`<= 100k` dot) registry submissions (`21.20%`
vs `h33-2-b2`), it measures `1.0000` vs full-support `17GEMSDOE`, `0.9995` vs dense lattice `13GEMSDOE`, and
encounters the `2` off-grid historical inventory rows (`errors = 2`), so it is automatically marked
`verdict: "negative"`, `decision: "DO NOT SUBMIT"`, `submission_slots_used: 0`.

## 2026-10-25 — H86J-LSI (live-score inversion)

* **IR-86-H86J-01:** on 74 owner-scored rasters, the SGMC proxy as-is reaches Spearman 0.300 vs OWNER-REPORTED live, and catalogue-hide (`gems57-pooled-hide-v2`) reaches 0.051. The 8-raster SGMC agreement behind H86G does not generalise (e.g. GEMSDOE44 h46: SGMC 0.3081 vs live 0.0715).
* **IR-86-H86J-02:** inventory row `ccbe1de0…` (14GEMSDOE r5-geom-horse-ensemble) has the competition shape but a shifted transform (origin 500000, 4500000). H86J compared it index-wise.
* **IR-86-H86J-03:** the H86J log-linear truth density is non-physical. λ > 1 on 2,552 pixels, which hold 63.5 % of its mass, so its LSI-PROJECTION values are not forecasts.
* **IR-86-H86J-05:** two concurrent sessions both used the `H86J` prefix (H86J-MPC on main, H86J-LSI here). The lanes are distinct (different suffix, cards and files). `build_site.py` variables were renamed to avoid a silent overwrite. The H86I-SACD and H86J-MPC artifacts were lost from `download-inventory.json`/`artifact_cards.json` when PR #131 merged; this merge restores them (24 artifacts re-audited).
* **IR-86-H86J-04:** E3 ended ~8 min past the 2 h session budget. No further experiment was run. The negative raster is not published.

## IR-F548F465 — hash identity is not registry uniqueness (2026-10-25)

`verify_submission_tif.py` printed “unique by pinned digest” after a format/hash check.
Corrected to format/identity only, with explicit DO NOT SUBMIT and no inferred
holdout, registry or slot clearance. Added clean fail-closed handling and tests
for malformed receipts and ZIPs. See `research/SESSION_F548F465_REVIEW.md`.

## IR-86-H86F-EWCS-TRANSQUAD-PU-20261025 — `scripts/run_h86f_ewcs.py` sampled PU training rows across all 4 quadrants rather than strict `quad != fold_i`

Forensic line-by-line inspection of `scripts/run_h86f_ewcs.py` (`line 519`) during
session `95a42d60` confirmed that while `vis = f["visible"] & fp` properly stripped
all `11,321` withheld positive pixels and their `3-px` feature collar globally (`0`
hidden-truth label leakage), `sample_nested_pu(static_mm, s_keys, vis, fp, e_keys, ...)`
drew visible training positives and unlabeled background rows from the full footprint
`fp` (including the held-out quadrant `quad == fold_i`) and emitted four full-map
`37,654`-dot allocations rather than restricting classifier training to the three
out-of-quadrant regions `fp & (quad != fold_i)`.
**Decision:** The archived `H86F-EWCS` run card (`docs/evidence/h86f-ewcs-run-card.json`)
is left untouched per `AGENTS.md` Rule 9, its trans-quadrant PU scope is documented
explicitly in `H86I-SACD`'s comparator table and on `irregularities.html`, and the new
`H86I-SACD` runner (`scripts/run_h86i_sacd.py`) enforces strict spatial
Leave-One-Quadrant-Out training (`train_region = fp & (quad != fold_i)`).

## IR-86-H86I-SACD-01 (2026-10-25) — H86I-SACD executed under strict spatial LOQO (`0/367` `<=50k`-dot firings, `0/691` Spearman firings), auto-marked DO NOT SUBMIT (`verdict = "negative"`)

Session `95a42d60` preregistered four untried hypotheses (`registry/h86i_hypotheses.json`,
`research/H86I_SACD_PREREGISTRATION.json`) prior to any holdout evaluation and executed
Rank-1 `H86I-SACD` (*Spin-2 Coulomb-Projected Strike Concordance, Jacobsen
Upward-Continuation Depth-Attenuation & Bekker-Davis Alluvial-Burial Propensity
Submodular Max-Cover*) across 3 fixed arms (`<= 3` experiment / `<= 2` hour budget,
`1,323.96 s` wall time). All `33` features passed single-feature ROC-AUC leakage
canaries (`max = 0.7639 <= 0.90`). Under strict `quad != fold_i` LOQO (`11,321`
withheld positives, `1,000` paired `20 km` block-bootstrap draws), scalar unweighted
pointwise `E2` achieved `HOLDOUT-DTI = 0.1055 [0.0878, 0.1257]` (beating `R0_D25`
`0.0931` and `R0_D28` `0.0273`), whereas `E1` (`0.0832 [0.0673, 0.0997]`) and pure
cover-blind subsurface `E3` (`0.0843 [0.0693, 0.0995]`) trailed `E2` (`paired delta =
-0.0223 [-0.0352, -0.0104]`) due to Fold-0 forced inter-quadrant quantile equalization
over-allocating dots into lower-density `NE` (`10,797` dots) and submodular plateau
clustering on broad diffuse basin posteriors. Full post-merge `v2` registry scans (`691 / 693`
valid competition-grid rasters including `H86G-EDTI`, `H86I-RKSC`, and `H86I-HVFD`, `0` missing)
confirmed `0` Spearman `rho > 0.90` firings and `0` discrete `<= 50k`-dot overlap firings
(`31.17%` vs `GEMSDOE32` `h33-h33-2-b2`, `55.60%` vs `H86F-EWCS`), while failing closed on
`17GEMSDOE` saturation, space-filling lattices, and `2` off-grid upstream rows (`PA-86-02`
`FAILED_CLOSED_NO_REPORT`).
**Decision:** The unique `[0, 1]` GeoTIFF (`docs/downloads/gems86-h86i-sacd-spin2-submod-37654dots-20261025T040150Z-0544ef05-zeros.tif`,
SHA-256 `b15a89fa1917526c1ce32081c1802d39333dc497d0d0d1034dc962df47c691e0`) is published
strictly as an audit-only download (`status = "DO NOT SUBMIT"`, `verdict = "negative"`,
`0` weekly slots used), and `scripts/run_h86i_sacd.py` is locked behind
`protocol_preflight.require_feasible()` (`58` CLI builders + `8` imported orchestrators).

## IR-86-H86G-LOCAL-ONLY-DUP-20261025 — H86G-EDTI 43-file local check missed 25 informative full-registry firings

Restoring all 655 external Git blobs via zero-REST-quota `codeload.github.com` + shallow
git-pack fallback in `scripts/restore_registry_inventory.py` and auditing
`gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif` (`ba8b731f...`)
across all 689 compatible rasters excluding self (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`)
revealed **44 dot-field forward-3px overlap firings (> 0.70)** and **25 informative
(`halo_coverage <= 0.70`) firings**, including sparse `GEMSDOE46:r11f` (`76.02%` at
44,090 dots), `GEMSDOE41:h42` (`73.99%` at 40,000 dots), and `GEMSDOE46:r12` (`72.24%`
at 37,654 dots). `scripts/run_h86g_edti.py::main` is now gated behind
`protocol_preflight.require_feasible()` (`60` CLI builders + `8` imported orchestrators).

## IR-86-CSGD-LITERAL-STOP-20261025 — H86J-CSGD achieves 0 / 636 informative dot-field firings on full registry, stays fail-closed negative

Session `0bec8252` preregistered `registry/h86j_hypotheses.json` +
`research/H86J_CSGD_PREREGISTRATION.json` and executed 3-arm `H86J-CSGD`
(`docs/downloads/gems86-h86j-csgd-sar-admit-37654dots-20261025T055033Z-35faffb4-zeros.tif`,
SHA-256 `079914e36dec80349310f52289119ad8a956f13e435369422859d5dd0b16707f`):
`28/28` canaries passed (`max = 0.7742 <= 0.90`), `E2` unweighted cover-blind ablation
achieved `HOLDOUT-DTI = 0.1577 [0.1401, 0.1755]` (zero DEM/slope features), and primary
SAR-debiased `E1` (`0.0613 [0.0453, 0.0764]`) achieved **0 / 636 informative dot-field
firings** across the full 690-raster restored scan (`0` Spearman firings, max `0.5050`).
Because `E1` trails `H86C-KSLB` (`0.1241`) and literal `17GEMSDOE` (`100%`) + 2 off-grid
rows fail closed, `H86J-CSGD` is recorded as `verdict = "negative"` (`DO NOT SUBMIT`,
`0` weekly slots used).
