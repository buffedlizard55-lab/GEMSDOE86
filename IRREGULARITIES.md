# IRREGULARITIES — items that changed a decision in this session

Only entries that altered what was built or what the human should do. Everything else is in the
session documents.

## IR-86-SNAP-01 — the free holdout proxy is blind on this parent lineage (finding, not a bug)

The catalogue hide-and-recover PROXY returned 0.0047 for the parent and 0.0150 / 0.0169 / 0.0190 for
the three SNAP variants, which reads like a 3× improvement. Re-scoring every candidate with an
identical ≥ 3 px catalogue collar collapses **all four to 0.0000**, and collapses the SGMC control
from 0.0877 to 0.0000 as well (`evidence/snap_fixed_collar.json`).

Decision changed: the proxy is no longer reported as a headline comparison for this lineage, and it
does not rank the SNAP variants. The entire signal is recovery of withheld catalogue traces inside
the halo that the live metric masks out and penalises. This is consistent with the ledger's own note
that proxy-to-live correlation spans −0.87 to +0.54 over 12–14 files, i.e. it is not informative here.
Reported as PROXY, never as a score, never a gate.

## IR-86-SNAP-02 — raw-field snapping is jitter, so the rule had to be fixed in advance

A diagnostic run made **before** the variants were built showed that snapping each dot to the raw
100 m magnetic bands moves 99 % of dots with a mean gain barely above a random-offset null
(0.000 σ against a null 90th percentile of +0.288 σ; only 43 % of dots beat that). The 100 m bands
carry interpolation structure between the 400 m GeoDAWN flight lines, so "strongest edge in the
window" is dominated by survey geometry, not geology.

Decision changed: the pre-registered rule smooths at 1 px and requires a ≥ 0.25 σ gain before a dot
may move; both are recorded in `registry/preregistration_snap.json` as fixed before scoring. Without
that gate the experiment would have been "displace 99 % of the parent's dots by 2.4 px", which
cannot be attributed to an edge at all.

## IR-86-SNAP-03 — SNAP moves mass back inside the catalogue collar

The parent has 0 dots within 2 px of the catalogue (that exclusion is the only edit with a
live-claimed gain, +0.007 at 0.2708 → 0.2778). The variants put 502 / 564 / 686 dots back inside that
200 m halo, and raise the share of dots within 300 m of a mapped fault from 4.28 % to 5.37 / 5.53 /
5.78 % (`evidence/snap_variants.json`, collar table in `SLOT_PLAN.md`).

Decision changed: the predicted live change for all three variants is stated as a range that includes
zero (central +0.003 to +0.005, i.e. below the 0.01 evidence floor), and the follow-up axis proposed
for week 2 is a held-count collar dose–response rather than a second SNAP round. A SNAP variant that
forces every destination outside the collar is named in `SLOT_PLAN.md` as the slot-3 reserve.

## IR-86-SNAP-04 — this workspace does not persist `.venv` or `.cache` (operational)

Both directories are excluded from workspace snapshots, so the interpreter and the hash-verified
inputs are gone at the start of every session. Order used and required:
`python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt`, then
`.venv/bin/python scripts/restore_data.py --dest .cache/bridge --with-external`, plus the H19-5
field from manifest entry `scored_h19_5` (used only for the ranking readout and, later, MASS).
A restore run rewrites `evidence/data_restore_receipt.json`; restore the committed copy afterwards
(`git checkout -- evidence/data_restore_receipt.json`) or CI's site check will see a diff.

## IR-86-SNAP-05 — R0 is reproducible as a dot set, not as bytes

`c55bafc…` is reproduced exactly at the level that matters (37,654 dots, symdiff 0 px, from the
0.2708 base minus every dot at d(catalogue) ≤ 2 px, verified in `scripts/build_snap_variants.py`).
The container bytes are **not** byte-reproducible: 90 combinations of compression, predictor, zlevel
and block shape were tried and none reproduces 219,065 bytes / `c55bafc…`
(nearest 153,363 bytes, tiled 512). The parent is therefore carried as the pinned file, and the
variants are compared against its dot set, never against re-derived bytes.
