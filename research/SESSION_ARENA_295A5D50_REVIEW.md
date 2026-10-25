# Repository review — 2026-10-25 — `arena/295a5d50-gemsdoe86`

## Executive decision

**DO NOT SUBMIT. No new TIFF was generated. No experiment or weekly slot was used.** The request contains no single assigned method paragraph for this parallel-run lane, which is a protocol stop. The current workspace also lacks `training_features.tif` and the shared cached feature stack. The initial release audit exposed an unregistered published H86M-LT TIFF/ZIP and an unsafe historical `safe_to_submit=true` flag. I reconciled that artifact as audit-only, preserved its historical scientific result, and made the shared full-artifact audit pass. The resulting global release decision remains `DO NOT SUBMIT`.

This review deliberately does not copy, relabel, or manufacture a raster to satisfy the urgent request. The H86M-LT binary remains available in the repository as an existing artifact, but **is not authorized for upload based on this checkout's current fail-closed state**. The exact required deliverable—a new, uniquely validated, submission-cleared TIFF—was not produced.

## Pass 1 — read and inspect

Read `AGENTS.md`, `README.md`, and `PROMPT.md` before making changes. The complete standing request is already preserved in `PROMPT.md` and the README points readers there. The prompt's score claims conflict (`0.3195`, `0.4413`, and H33 `0.2778`) and are not accompanied by a DrivenData submission-page receipt in this checkout. They therefore remain owner-provided/unverified claims, not `ORGANIZER-CONFIRMED` scores.

Repository facts verified locally:

- `vendor/gems57/metric.py` implements the 300 m / 3-pixel triangular kernel and `alpha=0.2`, `beta=0.8`. `research/H33_ANALYSIS.md` and `docs/evidence/h86f-h33-forensics.json` report an exact pixel comparison: H33 is the GEMSDOE28 parent with 2,545 dots removed from the 1–2 pixel mapped-fault collar; no other raster cells changed. The score change is **not causally established** by this edit, and it is not an organizer receipt.
- The most defensible explanation for H33's owner-reported advantage is more efficient emission under the score's asymmetric false-positive penalty and distance-kernel saturation: redundant or low-credit collar predictions can add false-positive cost without adding much new truth credit. This is a mechanism consistent with the pixel diff and metric—not proof of why a private leaderboard score changed.
- `src/gems86/io.py` identifies the native 19 bands. Prior method cards and queues show extensive testing of magnetic/gravity edges, derivatives, fault geometry, conductivity, topography, cross-spectral approaches, topology, and catalogue-informed emission. Candidates below are deliberately distinct from the methods actually run, but not claims of global novelty across other repositories or all literature.
- Current local workspace audit (`.venv/bin/python scripts/audit_workspace_inputs.py`): `training_features.tif` is missing from root and bridge paths; `existing_faults.tif` and `sample_submission.tif` have pinned, SHA-verified root copies after authorized mirror restoration; prepared `.cache/gems_work/bands/*.npy` arrays are missing; `shared_template_feature_stack=false`; `safe_to_submit=false`; `approved_for_weekly_slot=false`.
- The hashes establish byte identity against repository pins, **not organizer provenance**. The prepared manifest is a historical receipt and does not prove that its ignored `.cache` files exist now.

## Pass 2 — adversarial checks and ranked hypotheses

No hypothesis below was run. Ranking is qualitative expected *information value per cost*, not a projected DTI increase. “Untried here” means no matching executable candidate method/run card was found in this checkout; close adjacent methods are named. All three use native competition bands, so no new external product is needed in principle. That does not remove the missing-data/shared-cache or protocol blockers.

| Rank / qualitative potential / cost | Specific layers and targeted signature | Why it might recover a catalogue-missing structure | Difference from executed repo methods | Named non-fault mimic |
|---|---|---|---|---|
| 1 · medium potential · medium cost — **PFSB, alluvial-fan burial/censoring propensity** | Band 6 `tc` (radiometric total count), Band 12 `det_elev`, Band 19 `det_elev_slope`, Band 15 `depth_to_base_surf`, Bands 11/18 signed gravity derivatives, Band 17 `cond_surf`, and Bands 10/16 seismicity proxies. Freeze a fan-apron propensity field using piedmont concavity/low slope and smooth high-TC detrital plumes; use it to model where a fault catalogue may be censored, not as direct fault evidence. | Buried faults may lack mapped scarps where fans conceal the surface expression. Explicitly modeling mapping/visibility bias could recover omitted strands rather than rewarding the already well-exposed scarps preferentially labeled in the catalogue. | PFSB appears as an unexecuted proposal in `registry/h86f_hypotheses.json`; no matching PFSB executable was found in `scripts/` or `src/`. It differs from existing ridge/edge ranks by modeling observation/censoring propensity. | Non-tectonic pediment ledges, fan channels, and radiometric contrasts caused by lithology or alteration. |
| 2 · low-to-medium potential · medium cost — **GDFB, gravity–magnetic tensor misalignment with seam veto** | Bands 13/11/18 (gravity scalar and signed horizontal derivatives), Bands 2/3/9 (RTP and magnetic derivatives), Bands 7/8 (geodetic shear/dilatation), and Band 17 (surface conductance). Target spatially persistent angular misalignment between gravity and magnetic gradient/tensor orientations, conditionally weighted by dilatation/conductive alteration; include derivative-curl and survey-seam controls. | A fault-related density boundary can persist while hydrothermal alteration destroys or rotates magnetic susceptibility, producing cross-field discordance even when no surface trace is mapped. | GDFB is an unexecuted proposal in `registry/h86f_hypotheses.json`; no GDFB executable/run card was found. This is not the already-tested windowed gravity–magnetic cross-spectral admittance (H86J-CSGD), magnetic phase-congruency (H86J-MPC), or single-field derivative/ridge ranking. | Reversed-polarity basalt, an unfaulted intrusive/lithologic contact, or levelling/tie-line seams. |
| 3 · low-to-medium potential · medium-high cost — **GSST, gravity extended-step versus compact-source model comparison** | Band 13 `iso_grav_anom`, Band 5 horizontal gravity-gradient magnitude, and Bands 11/18 signed south/east derivatives. Compare preregistered scale-normalized responses for an extended basement step against compact-source and elongated-contact alternatives; use spatially held-out forward-template calibration. | A buried fault-related basement step may have a broad, coherent cross-strike signature that pointwise edge maxima miss, while explicit compact-source competition may reject isolated anomalies. | GSST is listed as unrun in `registry/followup_hypotheses_20261025.json`; no explicit step-versus-compact likelihood executable/run card was found. It differs from H86F-GZZD gravity curvature, H86H-PSTD tensor invariants, and H86K-PSC saddle/ridge topology. | Elongated intrusive contact, basin-margin facies change, or overlapping compact sources. |

**External-data exclusion:** The USGS Great Basin 3-D hydrogeologic framework (USGS Scientific Investigations Report 2010-5193 / corresponding ScienceBase grids) could potentially provide borehole-constrained basin-fill thickness independent of gravity-derived Band 15. This is **not viable in this run**: no bytes are pinned in the checkout and the current outbound allowlist does not include USGS/ScienceBase hosts, so obtainability could not be verified. It is not ranked as an executable candidate. The official USGS GeoDAWN record is linked below for manual review, but no claim is made that it supplies the framework grids.

### Why the top hypothesis was not validated

The user requested a holdout test before any slot action. No slot was used, but the top proposal could not be validated: the method lane is not assigned, `training_features.tif` and the shared cache are absent, and the run-time preflight cannot proceed from the historical manifest. In addition, the registered publication audit currently fails on an inventory mismatch. Running a private feature reconstruction, an alternate evaluator, or an unregistered TIFF would violate the standing reuse/audit rules. Consequently there is **no new HOLDOUT-DTI**, withheld-positive count, CI, leakage-canary result, pre-placement surface comparison, or final-dot uniqueness result to report.

## Pass 3 — cross-checks, release integrity, and limitations

After installing the pinned `requirements-lock.txt` into ignored `.venv/` and reconciling the inherited H86M-LT publication metadata:

```text
.venv/bin/python scripts/restore_protocol_data.py --include-registry
  PASS — restored hash-pinned owner mirrors and the historical witness; none is
  represented as organizer-authenticated training data.

.venv/bin/python scripts/audit_workspace_inputs.py
  PASS as read-only inspection; training_features.tif and prepared .cache arrays
  are missing, shared cache absent, safe_to_submit=false, slot approval=false.

.venv/bin/python scripts/protocol_preflight.py
  PASS as a measurement; STOP_LITERAL_OVERLAP_UNSATISFIABLE. Witness covers 100%
  (5,106,385 / 5,106,385) allowed cells; registry completeness=false; no candidate.

.venv/bin/python scripts/audit_release.py --measure-registry
  PASS integrity audit; decision DO NOT SUBMIT; 36/36 artifact formats locally valid;
  all 36 final TIFFs remeasured against the single witness; 0 experiments, 0 slots.
  This is a sufficient negative, not a complete-registry uniqueness clearance.

.venv/bin/python scripts/audit_downloads.py --write
  PASS — refreshed deterministic download report for 36 artifacts.

.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
  PASS; all downloads are explicitly audit-only and no file is authorized for upload.

.venv/bin/python -m pytest -q tests/test_release_audit.py tests/test_site.py tests/test_current_review.py tests/test_publication_gate.py
  66 passed, 17 subtests passed.

.venv/bin/python -m pytest -q
  1023 passed, 24 skipped, 48 warnings, 58 subtests passed in 453.20 seconds.

Final repeated release/download/site audits and `git diff --check`: PASS.
```

The first release audit correctly failed because H86M-LT was published but unregistered; the first site checker also found the old H86M-LT page claiming “YES” and an unsafe `safe_to_submit=true` card flag. I corrected the underlying metadata/page (not raster pixels), added a fail-closed archived-card branch and regression assertions, and then ran the complete artifact audit. The historical TIFF now remains downloadable only as an explicitly registered audit artifact. Its hash and historical research metrics were not changed. The current one-witness remeasurement for its final dots is Spearman 0.06914945298 and literal 3-px forward overlap 1.0; the latter exceeds 0.70 and is sufficient for a negative, while the registry scan is incomplete.

No automated fetch of DrivenData was attempted; repository policy expressly forbids scraping it. Thus the live leaderboard, current weekly quota, account eligibility, and the exact cause of the user's earlier `[0,1]` portal error remain unverified. A local format validator cannot establish organizer acceptance.

### Items needing follow-up

1. Resolve the publication mismatch through the shared inventory/audit implementation: either register H86M-LT with an explicit current negative/no-authorization interpretation, or remove it from public downloads via the repository's normal release process. Do not simply relabel it safe to submit.
2. Restore the exact shared feature cache and source provenance, including preprocessing and visible-mask identity. Native-band TIFFs or historical manifests alone do not satisfy template-cache reuse.
3. Assign one precise method paragraph, then freeze buffered whole-segment folds and controls, derive catalogue-based features from visible faults only, mask visible fault pixels exactly, run per-feature AUC canaries, and use the pinned evaluator/writer. Stop if canary AUC exceeds 0.90 pending leakage resolution.
4. Reconcile the literal full-support uniqueness witness under an explicit protocol amendment; never privately change the threshold or bypass a failing stop. Run surface correlation before placement and final-dot 3-pixel overlap against the complete, valid registry.
5. Re-run the complete release, site, link and test audits on the final tree. A passing format/range check is only one gate and must not be labelled upload authorization.
6. Keep any future leaderboard result as `ORGANIZER-CONFIRMED` only when copied from a submission-page receipt. Keep all projections, proxy metrics, and holdout results labelled separately.

## Official / primary links for manual review

These are links to primary resources already referenced by the project. They are offered for review; they were **not freshly fetched** in this session. The exact DrivenData pages were not accessed because of the repository no-scraping rule.

- Competition problem and format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Competition rules: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Official reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Official USGS GeoDAWN data record: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DOE/NREL GDR INGENIOUS source record: https://gdr.openei.org/submissions/1391
- Coordinate reference system (EPSG:32611): https://epsg.io/32611
- Official GEMS submission/rules PDF linked by the project: https://docs.nlr.gov/docs/fy26osti/96647.pdf

## Run card

See machine-readable companion: `research/session-arena-295a5d50-run-card.json`. The current result is a review-only **negative**; no TIFF, score, or upload name is claimed.
