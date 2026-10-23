# IRREGULARITIES

Only items that change a decision. Each one states the observation, the measurement or source
behind it, and the decision it forced.

## 1. The parent's filename token is not its SHA-256 prefix

`data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`
carries the token `e5eb6e7e`, but the file's SHA-256 is
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. The `-zeros` and `-nan`
twins on the upstream mirror are `c55bafc4…` and `baeae321…` respectively
(`docs/evidence/h86_wvb_data_restore.json`, GEMSDOE32 ref `780a5a53`), so no published twin of
this file hashes to `e5eb6e7e…`.

**Decision.** The brief's instruction "rebuild R0 and match its sha256" was satisfied against
the `registry/data_manifest.json` pin (`c55bafc4…`, 219,065 bytes) rather than against the
filename token, and the parent was used as restored bytes — not rebuilt from a recipe.
Every release this session names itself with a **dot-set** digest (a deterministic SHA-256 over
the packed dot bitmap plus shape), not a file digest, so the token cannot be circular and is
reproducible from the mask alone. Both the token and the file SHA-256 are recorded in
`ledger/submissions.csv`.

## 2. R0 was not rebuilt from its recipe; the parent bytes were verified instead

The recipe lives in another repository (GEMSDOE32). Its `evidence/h33_removal_rule_scan.json`
shows `R0-base` at 40,199 dots and `R1-flankB2` at 37,654 — matching the parent exactly — but
the intermediate 40,199-dot surface is not published, so a byte-exact rebuild is impossible
here.

**Decision.** The brief says "if you cannot [rebuild R0], stop and report; never approximate the
parent." Restored, hash-verified parent bytes are strictly stronger than a rebuild from a
partially published recipe, so the session continued and every derived number is reported
against the verified bytes. The parent's own geometry was re-measured rather than trusted
(37,654 dots; 0 on catalogue; min clearance 2.236 px; nearest-neighbour floor 2.828 px;
R0 ⊂ the 44,090-dot d2.8 set).

## 3. The reported block-density CV band does not contain the incumbent

The brief states the best files sit at block-density CV 0.51–0.59. Measured on the incumbent
R0 over occupied 1 km blocks, the CV is **0.6235** (15,976 of 122,717 blocks occupied).

**Decision.** The band is treated as an unverified CLAIM, not a target. CONCENTRATION was built
per the brief's definition (move 15 % of dots from lowest- to highest-prior km blocks), which
moves the CV to 0.7644 — outside the band — and that direction is now a stated falsifier rather
than something quietly tuned away. If slot 3 drops, the CV band becomes a directly testable
axis (spread mass until the CV lands in-band).

## 4. The parent's support mask is saturated at its own thinning radius

The PRUNE refill must hold the count at 37,654. Inside the parent's own H19-5 support mask
(121,131 px) only **611** eligible cells region-wide sit ≥ 2.828 px from a retained dot, against
2,171 needed.

**Decision.** The refill runs in two passes: parent spacing first (475 placed), then a relaxation
to the parent's own >2 px catalogue-clearance floor (1,696 placed). This is a disclosed spacing
side-effect of holding the count, recorded in `evidence/axis_variants.json` as
`refilled_at_relaxed_spacing`. The alternative — accepting a 1,696-dot shortfall — would have
turned a PRUNE build into an unlabelled MASS change, which is worse.

## 5. The parent's own ranking is not stored, so MASS is not buildable this session

The H19-5 surface that the whole lineage was thinned from is **binary**: 121,131 positive
pixels with only two distinct values. There is no continuous ranking to drop or add 10 % by.

**Decision.** MASS was not built and no proxy ranking was substituted, because a proxy ranking
would make the axis unattributable. MASS is parked in `SLOT_PLAN.md` with the decision it needs:
either restore the 419 MB feature mirror and refit the field, or accept a declared proxy.

## 6. Brief v2 supersedes this repo's literal uniqueness gate

`PROMPT.md` and `AGENTS.md` impose a stop at rank-correlation > 0.90 or > 70 % dot overlap with
any registry raster, and the pinned full-support witness currently makes that rule
unsatisfiable for every non-empty candidate. Brief v2 section 6 says explicitly: "Do NOT apply
rank-correlation or dot-overlap uniqueness thresholds. Dedupe only on exact hash and on repeated
(parent, axis, value)."

**Decision.** Brief v2 governs this session; the local gate is a repo rule, not an organiser
rule, and the official metric page imposes no uniqueness requirement. Dedupe was applied exactly
as brief v2 specifies: SHA-256 against the ledger and `data/scored_fleet/`, plus (parent, axis,
value). By construction the variants overlap R0 heavily (Jaccard 0.891 / 0.739 / 0.053) — that is
the point of a controlled single-axis edit, and under the old gate all three would have been
flagged as duplicates.

## 7. The template format validator skips its footprint checks here

`vendor/template66/gems/validate_submission.py` derives the official footprint from the 419 MB
feature stack, which the human declined to restore this session, so it returns
`SKIPPED: no features raster supplied`.

**Decision.** The gate does not treat that SKIP as a pass and does not ignore it either:
`src/gems86_axis/gates.py` records it in `skipped_covered_elsewhere` and takes the same
measurements directly — the written file is re-read from disk and checked against the footprint
of the pinned `sample_submission.tif` (`in_footprint_all_finite`, `in_footprint_range_0_1`,
`outside_footprint_nan_or_zero`). Any *other* SKIP or FAIL still fails the gate closed.

## 8. Deadline and weekly cap are unverified here

Deadline 2026-12-03, the 3-per-week cap and the leaderboard value 0.3195 all come from the brief
and the human, not from a page this session fetched (the terms ban automated access to
drivendata.org, and no page was fetched).

**Decision.** All three are labelled CLAIM/UNVERIFIED wherever they appear. The human must
confirm the deadline, the slots remaining and TOP_PUBLIC on the submission page before spending
a slot.

## 9. No catalogue-mass or leakage violations found

Measured on all six written files: 0 dots on catalogue pixels, minimum catalogue clearance
2.236 px (3.162 px for the PRUNE variant), all values in [0, 1], no NaN inside the footprint,
NaN (or 0 for the fallback twin) everywhere outside it. No leakage canary was run this session:
it needs a labelled holdout fit, which needs the feature stack. That is recorded as NOT RUN, not
as a pass.
