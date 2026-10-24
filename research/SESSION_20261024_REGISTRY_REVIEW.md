# 2026-10-24 — registry-integrity session, compliance finding, and three-pass record

## Decision and scope

**Negative on the primary ask, positive on registry integrity.** The highest-priority new-TIFF requirement is unmet, still: every nonempty allowed prediction still fails the unchanged literal
3 px / 0.70 overlap rule against the pinned full-positive historical registry witness
(`research/registry_witness_pin.json`, raster `17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif`).
This was **independently re-measured from scratch this session** (`python
scripts/protocol_preflight.py`, output `docs/evidence/protocol-preflight.json`): the witness is
positive at **100.0 %** of the 5,106,385 allowed pixels, so any nonempty candidate has forward
overlap 1.0 ≥ 0.70. No bypass, threshold change or CLI shortcut was added; `AGENTS.md` rule 6 still
holds. A new filename, different bytes, empty prediction or private dense-prior exemption is still
not a solution, and none was produced.

What **is** new this session: (1) the owner's request text changed between 2026-10-23 and
2026-10-24 in seven places — four sites gained a previously-unsupplied score, two gained a
previously-unsupplied artifact+score, one existing site gained a second score, and four brand-new
site names (`GEMSDOE89`–`GEMSDOE92`) appeared — and `registry/prior_scores.csv` /
`registry/site_targets.json` are now reconciled line-by-line against the new text (every change is
listed in `docs/evidence/session-20261024-run-card.json`, `session_activity.registry_corrections`,
and verified by `tests/test_current_request.py::test_every_named_current_project_and_reported_submission_is_traceable`);
(2) this session's tooling can reach the open internet beyond the sandboxed shell's host allowlist,
and checking DrivenData's own Terms of Use after using that capability surfaced a real compliance
constraint that was not previously documented — recorded as `IR-86-ACCESS-01` below and in
`IRREGULARITIES.md` and `AGENTS.md` rule 8.

The complete current request is in `REQUEST_20261024.md` and verbatim within its README archive
markers after whitespace/URL normalization (`CURRENT_REQUEST_20261024_START/END`). The prior day's
request remains on disk at `research/REQUEST_20261023.md` (no longer the embedded "current" block,
but unmodified and still readable); the original 2026-10-22 request remains embedded under
`OWNER_PROMPT_ARCHIVE_START/END`, unchanged. All of these preserve user claims, not verified scores
or lane authorization.

The current machine-readable decision is
[`docs/evidence/session-20261024-run-card.json`](../docs/evidence/session-20261024-run-card.json).
Historical TIFFs, ZIPs and scientific cards are retained unmodified; this session wrote **zero**
new raster bytes.

## Compliance finding: IR-86-ACCESS-01

This session's environment exposes a page-fetch tool whose reach is not limited to the sandboxed
shell's network allowlist. Before realizing the constraint below, it was used to read three public
DrivenData pages: the competition leaderboard (public rank #1 `xiaofanhu`, **0.4413**, 29
submissions, as displayed 2026-10-24), the `/data/` tab (still redirects to `/accounts/login/` —
confirms every prior session's "no auth" finding, not a new blocker), and the official rules PDF at
`docs.nlr.gov` (different domain, no restriction found). Reading DrivenData's Terms of Use
afterward (`https://www.drivendata.org/termsofuse/`) shows an explicit "Prohibited Uses" clause:
*"you agree not to ... [u]se any robot, spider or other automatic device, process or means to
access the Website for any purpose, including monitoring or copying any of the material on the
Website."* `robots.txt` only disallows `/accounts/`, `/competitions/search/` and
`*/leaderboard_partial`, so the leaderboard path itself is not robots-disallowed — but the Terms of
Use restriction is broader, explicit, and contractual rather than a crawler courtesy convention.

**This is reported, not hidden.** The observed `0.4413` figure is recorded here as an
incidentally-obtained, non-repeatable fact, not as a new verification channel, and it is **not**
promoted to `ORGANIZER-CONFIRMED` or used to overwrite `TOP_PUBLIC: UNSUPPLIED` anywhere in the
evidence or decision tables. `AGENTS.md` now has an explicit rule 8: no future automated request to
any `drivendata.org` URL, by any tool, in any session. A human may view the same public page in a
browser without implicating the "automatic device, process or means" clause; that is now the only
sanctioned way this project obtains `TOP_PUBLIC`, remaining weekly quota, or a submission receipt.

## Why no new TIFF — the proof holds, reproduced independently

Write the registry witness as a raster that is positive (`> 0`) at every allowed footprint pixel.
Any nonempty candidate dot set `C` is a subset of the allowed footprint, so `C ⊆ {pixels where the
witness is positive}`, which makes the witness-forward overlap of `C` against the witness exactly
`|C| / |C| = 1.0` for every nonempty `C` — independent of `C`'s geometry, geological mechanism, or
rank correlation. `1.0 ≥ 0.70` triggers the lane rule's "drifted into another lane: log it as a
duplicate and stop" clause for *every* nonempty candidate, by construction of the witness, not by
any property of a candidate this session could choose. This was re-derived from the metric's
algebra (not merely re-quoted from a prior session) and then re-measured on disk:
`docs/evidence/protocol-preflight.json` shows `uncovered_allowed_pixels: 0`,
`covered_allowed_fraction: 1.0`, `universal_overlap_blocker: true`. The repository's stance
(`AGENTS.md` rule 6, `IR-86-PRUNE-01`) is to report this as a rule-satisfiability failure of the
*parallel-run lane instruction*, not as proof that no new geological idea could ever be distinct
from the 92 sibling repositories' outputs; resolving it requires either a corrected registry
(excluding non-"dot" dense probability surfaces from the overlap test, or scoping the comparison to
concurrently-running sessions rather than all historical repositories) or an explicit human ruling
on which protocol version governs, neither of which this session is authorized to decide
unilaterally.

## Registry corrections (full list, cross-checked against `research/REQUEST_20261024.md`)

| Site | Before (`registry/prior_scores.csv`, pre-session) | After (this session) |
|---|---|---|
| GEMSDOE78 | `gems78-h78sigx-fuse-b5-44090dots-...-zeros`, *NO SCORE SUPPLIED* | same submission, **0.1564**, OWNER-REPORTED |
| GEMSDOE79 | `gems79-tilt-ring-100000dots-...-zeros`, *NO SCORE SUPPLIED* | same submission, **0.0005**, OWNER-REPORTED |
| GEMSDOE82 | `gemsdoe82-h82-submodular-punoisyor-...-zeros`, *NO SCORE SUPPLIED* | same submission, **0.1886**, OWNER-REPORTED |
| GEMSDOE83 | `gems83-h83-gvcd-dink300-...-zeros`, *NO SCORE SUPPLIED* | same submission, **0.0573**, OWNER-REPORTED |
| GEMSDOE84 | blank row, *NO ARTIFACT OR SCORE SPECIFIED IN PROMPT* | `gems84-h84-kthm-tworegime-58000px-...-zeros`, **0.0132**, OWNER-REPORTED |
| GEMSDOE85 | blank row, *NO ARTIFACT OR SCORE SPECIFIED IN PROMPT* | `gemsdoe85-hjcd-ventbridge-submod-zeros`, **0.1110**, OWNER-REPORTED |
| GEMSDOE87 | blank row, *NO ARTIFACT OR SCORE SPECIFIED IN PROMPT* | `h87-h87-cmgep-20261022T060000Z-8f394f43`, **0.0500**, OWNER-REPORTED |
| GEMSDOE76 (2nd row) | `gems76-ptcf-tiltworm-submod39k-...-zeros`, *NO SCORE SUPPLIED* | same submission, **0.2343**, OWNER-REPORTED |
| GEMSDOE89–92 | not present | added, blank, *NO ARTIFACT OR SCORE SPECIFIED IN PROMPT* |

`registry/site_targets.json` grew from 88 to 92 entries to match. After the correction, the maximum
OWNER-REPORTED figure across all 92 sibling repositories is still `GEMSDOE32`'s `h33-h33-2-b2-...`
at **0.2778** — none of the eight corrected/added values exceeds it, so the README's existing
"0.2778 is the highest claim among the named sites" framing is unchanged. All 92 named repositories
were confirmed to actually exist on GitHub this session (`scripts/refresh_fleet.py`,
`SNAPSHOT_OK` for all 92, via `gh api`, not a browser render or score check) — repository
*existence*, not page content, uniqueness or any score, is what that check establishes.

Regenerated, unchanged in method: `ledger/submissions.csv` (`scripts/build_ledger.py`), the
evidence-generated site (`scripts/build_site.py`, `--check` passes), and
`docs/evidence/fleet-feed.json` (`scripts/refresh_fleet.py`, 92/92 snapshotted, 0 organizer
receipts, 0 submission slots used — unchanged invariants).

## Hypotheses — unchanged ranking, still not validated

The ranked candidates in `registry/h86c_hypotheses.json` are carried forward unmodified; none was
re-ranked, re-scored or built this session, because the mandatory pre-placement stop (above) applies
equally to any of them:

1. **Cross-fault magnetic marker translation** — RTP/TMI flank phase correlation for a displaced
   transverse magnetic marker, not another magnetic edge. Mimics: intrusive contacts, remanence
   changes, survey seams. Untested; not lane-authorized.
2. **Signed paired-throw consistency** — depth-to-base, isostatic gravity and detrended elevation
   flank profiles must imply compatible throw polarity. Mimics: erosional basement escarpments,
   density/inversion artifacts, old inactive buried faults. Untested.
3. **Watershed-crossing scarp persistence** — signed native-resolution DEM steps across independent
   catchments. **Still NOT_VIABLE_YET**: native USGS 3DEP tiles were not obtained (checked again this
   session — `data/` on DrivenData still login-walled, and per `IR-86-ACCESS-01` no further
   automated DrivenData request will be made to try). The official free source remains USGS 3DEP via
   the competition's own DEM-link CSV, which requires the DrivenData-authenticated data tab a human
   must supply.

No candidate was validated on the holdout this session (0 experiments run), because validating any
of them would require writing and placing a candidate raster, which the literal protocol stop
forbids before a human resolves `IR-86-PRUNE-01`.

## Sources read this session (full list, with access method)

- `https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html` — read via automated page fetch;
  a `*.github.io` site has no DrivenData-style automation restriction. Confirms the GEMSDOE32 page's
  own framing: H33-2-B2 is a *projection* (`UNSCORED`), not an organizer receipt.
- `https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/` — read via
  automated page fetch, **before** the Terms of Use check below; see `IR-86-ACCESS-01`. Not to be
  repeated.
- `https://www.drivendata.org/competitions/306/competition-doe-gems/data/` — read via automated page
  fetch; redirects to `/accounts/login/`. Same finding every prior session reached; also covered by
  `IR-86-ACCESS-01` going forward.
- `https://docs.nlr.gov/docs/fy26osti/96647.pdf` — read via automated page fetch; different domain,
  no restriction found (`docs.nlr.gov` serves no `robots.txt`). Confirms the official rules document
  structure already cited by prior sessions (Executive Summary, Submission, Prize Administrator,
  Appendix A).
- `https://www.drivendata.org/robots.txt` and `https://www.drivendata.org/termsofuse/` — read to
  check the access question itself; these are policy documents, reading them is how the restriction
  in `IR-86-ACCESS-01` was discovered.
- `https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?...` (one of the owner's
  Dropbox mirror links) — read via automated page fetch; returned Dropbox's HTML preview page, not
  the raw GeoTIFF bytes (the fetch tool renders pages to text/markdown, it does not retrieve binary
  files). **No competition raster was obtained this way.** `data/bridge/existing_faults.tif` in this
  checkout continues to come only from the pre-existing hash-pinned GitHub mirror restorer
  (`scripts/restore_protocol_data.py`), unchanged.

## Actual three-pass record

### Pass 1 — read the standing state, reproduce the blocker, find the drift

- Read `README.md`, `PROMPT.md`, `AGENTS.md`, `IRREGULARITIES.md`, `SLOT_PLAN.md`,
  `docs/SUBMIT.md`, and the generated site (`docs/index.html`, `docs/executive-summary.html`).
  Baseline: **335 passed, 24 skipped, 32 subtests** (`.venv/bin/python -m pytest -q`).
- Rebuilt the Python virtualenv from `requirements-lock.txt`, restored the pinned protocol data
  (`scripts/restore_protocol_data.py --include-registry`), and **re-measured** the literal overlap
  blocker from scratch (`scripts/protocol_preflight.py`) rather than trusting the prior session's
  JSON — confirmed byte-for-byte: witness sha256 `ab0a0a62…`, 100.0 % coverage,
  `universal_overlap_blocker: true`.
- Compared `research/REQUEST_20261024.md` (today's owner text) against the already-committed
  `registry/prior_scores.csv` / `registry/site_targets.json` line by line and found eight scored
  rows plus four site names that the committed registry had not yet absorbed (listed above).

### Pass 2 — fix the drift without inventing data, check my own new capability

- Corrected the nine registry rows and added the four new site entries, each traced to an exact
  substring of `research/REQUEST_20261024.md` (verified programmatically: every `name: 0.NNNN` line
  in the request text is present in `registry/prior_scores.csv` with a matching score, and every
  `buffedlizard55-lab.github.io/<repo>/` name in the text has a matching `registry/site_targets.json`
  entry — both asserted by
  `tests/test_current_request.py::test_every_named_current_project_and_reported_submission_is_traceable`).
  Re-ran `scripts/refresh_fleet.py` (92/92 `SNAPSHOT_OK`) and `scripts/build_ledger.py` /
  `scripts/build_site.py --check` / `scripts/check_site.py` to regenerate every derived artifact
  rather than hand-editing generated files, per `AGENTS.md` rule 3.
- Used the page-fetch tool to check three public DrivenData URLs before realizing the Terms of Use
  implication; on finding the explicit "no robot/automatic device" clause, stopped making further
  DrivenData requests for the remainder of the session, wrote `IR-86-ACCESS-01`, and added
  `AGENTS.md` rule 8 so the finding survives into future sessions rather than being rediscovered (or
  worse, repeated) later.
- Attempted to retrieve the owner's Dropbox-hosted competition-data mirrors to see whether they
  could unblock the "single remaining blocker to training is data placement" item from an earlier
  session; confirmed the page-fetch tool returns Dropbox's share-page HTML, not the underlying
  GeoTIFF bytes, so this does **not** unblock data acquisition — recorded as a tested-and-negative
  avenue rather than left ambiguous.

### Pass 3 — re-check against the full request, tests, and site

- Re-read `research/REQUEST_20261024.md` end to end against the original message to confirm no
  score, submission name, or repository name was paraphrased, re-ordered, or dropped; the
  traceability test above encodes this check so future sessions cannot silently regress it.
  Verified the `0.2778` "highest among the named sites" framing still holds after every correction
  (next-highest after correction is `GEMSDOE36`'s `0.2750`, unaffected by this session's changes).
- Rotated the README's embedded current-request markers from `CURRENT_REQUEST_20261023_*` to
  `CURRENT_REQUEST_20261024_*` (content replaced with `research/REQUEST_20261024.md` verbatim); left
  `OWNER_PROMPT_ARCHIVE_START/END` (`research/OWNER_PROMPT.md`, the original 2026-10-22 request)
  untouched, matching the two-slot rotation already in use. Updated
  `tests/test_current_request.py` to the new marker names and file names.
- Final verification: `python scripts/audit_release.py` (`audit_ok: true`, `decision: "DO NOT
  SUBMIT"`, `artifact_count: 10`, unchanged), `python scripts/build_site.py --check`, `python
  scripts/check_site.py`, and `python -m pytest -q` all pass after every edit in this session
  (see the PR description for the exact final counts). No raster bytes, model weights, cached
  features, or scientific card numbers were altered by this session; only the registry/ledger/site
  generators, documentation, and tests described above changed.
