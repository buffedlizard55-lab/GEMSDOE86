# Three-pass verification and current review record

**Reviewed:** 2026-10-22. This file replaces earlier pass summaries where they conflict with the current evidence. It is a dated snapshot, not a live dashboard.

## Pass 1 — implementation and safe local audit

Inspected the checkout and selected upstream trees; installed the pinned Python dependencies; restored the small grid rasters from the owner mirror; verified their SHA-256 hashes against the checked-in manifest. The mirror is not organizer-authenticated. The shared `gems57` tool bytes are unchanged and still match their pin. The 419 MB mirrored feature raster and ephemeral feature cache were not restored or substituted.

An existing candidate TIF was already in the checkout. It was not created during this review. A fresh local read confirms the expected single-band float32 GeoTIFF grid, finite values in [0,1], 60,000 positive pixels, and a ZIP containing exactly that byte-identical TIFF. This is a file-format result only—not scientific validation, registry clearance, or organizer acceptance.

## Pass 2 — protocol, failure-mode, and evidence review

Re-read the historical runner and its JSON evidence. The earlier H86 run consumed all three experiments before this review. It was not authorized by the missing single-method paragraph; it used a locally assembled stack rather than the required cached template stack; and its stored DTI-like numbers came from a different hide/evaluation path and cell bootstrap. The holdout was not whole-segment buffered, its confidence interval was not the shared spatial-cluster interval, and it did not establish the best comparable incumbent. Those values remain raw diagnostics and are excluded from admissible HOLDOUT-DTI claims.

Independently rechecked the final-dot comparison against the hash-pinned 13GEMSDOE lattice raster. The candidate's forward 3-pixel dot overlap is 0.9950333333, above the literal 0.70 stop threshold; Spearman correlation is 0.0003379482 and Jaccard is 0.0092227062. The OR rule fires on overlap. Low correlation/Jaccard and non-identical file bytes do not override the stop. The full registry and the required pre-placement dot comparison remain unavailable/not recorded.

Changed `scripts/audit.py` to write a separate local preflight report instead of overwriting the run card; it fails readiness closed. Added a gate-interpreter module that treats missing/nonfinite registry metrics, identity, incomplete inventory, and threshold violations as non-clearance. Added a local HTML-link checker. Hardened the historical runner against a consumed budget and nonconformant protocol. **The runner was compiled but not executed.** No new geological experiment, candidate generation, submission, or weekly-slot selection occurred during this review.

## Pass 3 — requirements and claim review

The current run card and audit receipt say **negative / DO NOT SUBMIT**. Its admissible HOLDOUT-DTI value, evaluator, withheld-positive count, and CI are null. The separate preflight records the local TIF checks as passing but keeps registry, holdout, and complete-inventory gates false. No ORGANIZER-CONFIRMED score exists for the file. The exact past portal-rejected file was not available, so its reported range-error cause remains unknown.

The GEMSDOE32 H33-2-B2 page was fetched and says **UNSCORED**; it calls its modeled result a projection and says no organizer score exists. The official DrivenData public leaderboard and task page were also fetched on 2026-10-22. A public leaderboard observation is not a per-file submission receipt; the numeric observation is intentionally not copied into this project's run card. Dated source claims and access limits are in `docs/evidence/source_review_2026-10-22.json`.

The README now contains a detailed persistent project directive, protocol, evidence rules, safety commands, and explicit “read at the start of every session” checklist. It is an operational record, not a verbatim archive of the entire original conversation. The clean Pages site makes audit-only status prominent, provides a future portal guide, and labels all score/slot claims. Its local HTML links are checked automatically in CI.

## Safe verification commands and outcome

- `python scripts/check_docs.py` — all local HTML links resolve.
- `PYTHONPATH=vendor .venv/bin/python -m unittest discover -s tests -v` — 15 unit/safety tests pass. One Rasterio `PendingDeprecationWarning` from the synthetic affine-transform test remains non-fatal.
- `PYTHONPATH=vendor .venv/bin/python -m compileall -q scripts vendor tests` — passes, including the disabled legacy runner.
- `git diff --check` — passes.
- `.venv/bin/python scripts/audit.py` — writes `docs/evidence/preflight.json` and intentionally exits 1 because the scientific/provenance readiness gates are negative. It does not overwrite `docs/evidence/run-card.json`.

The tests include a synthetic full-grid writer/ZIP roundtrip, rejection of invalid values/catalogue/out-of-footprint support, metric-oracle arithmetic, fail-closed registry gate behavior, experiment-cap logic, candidate byte/format checks, shared-tool hash pins, read-only preflight behavior, and local Pages links. They do not constitute geological experiments or competition scores.

## Outstanding limitations and handoff

1. The assigned method paragraph is absent; no new lane is authorized. The historical H86 runner's selection was not authorization.
2. The three-experiment cap is consumed. Zero experiments were run **in this current review**; do not run another, submit the candidate, or spend a slot.
3. The shared cached feature stack and its verifiable hash/receipt are unavailable. Do not privately rebuild it or substitute a mirror raster.
4. The complete cross-repository/organizer registry is unavailable, and pre-placement dot overlap was not recorded. The known final-dot overlap gate already fails.
5. No admissible holdout result, paired spatial-cluster CI, feature-alone leakage canary under the required folds, or best-comparable holdout baseline exists.
6. Only small owner-mirrored grid inputs were hash-checked; no official competition download/authentication, private labels, authenticated weekly quota, upload, or submission-page receipt was obtained.
7. Four next-candidate hypotheses are documented with named layers, mechanisms, mimics, qualitative potential tiers, relative novelty limits, cost, and source availability. They remain untested and unauthorized.
8. The user-provided historical score claims have not been systematically verified across every sibling GEMSDOE site. GEMSDOE32's H33-2-B2 page explicitly marks its artifact unscored. Broader sibling-site novelty, score receipts, and complete historical comparisons remain outstanding.
9. The source review is a dated snapshot, not a live official-source feed. The full original user prompt is not archived verbatim; README records its persistent operational requirements.
10. GitHub PR review and merge status is repository metadata and is not evidence that scientific or submission gates passed.

**Current deliverable status:** repository review and negative preflight, not a scientifically cleared competition submission. The audit TIF is downloadable for inspection only; do not upload it.
