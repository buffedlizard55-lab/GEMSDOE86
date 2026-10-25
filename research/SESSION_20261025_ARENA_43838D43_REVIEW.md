# Independent repository review — 2026-10-25 — Arena branch `arena/43838d43-gemsdoe86`

## Decision

**NEGATIVE — no new TIFF was generated, and no file is authorized for upload.** I did not spend a model experiment or a weekly slot. This is an intentional protocol stop, not a claim that the unique-TIFF request was satisfied. Existing H86G/H86I downloads are earlier artifacts; none was copied, renamed, or presented as new work.

The literal registry gate is unsatisfiable for any non-empty prediction under the currently pinned support definition: the hash-verified `17GEMSDOE` witness has positive support on every allowed cell. Thus every candidate dot would be within 3 pixels of a positive witness cell, giving forward overlap `1.0`, above the fixed `0.70` limit. This is a **REGISTRY-MEASUREMENT**, not a model score or a complete uniqueness scan. The recorded report itself says only one historical witness was measured and the registry is incomplete for promotion. I did not reinterpret the gate or delete the witness.

The current source tree also confirms that the actual shared template cached feature stack is absent. A native 19-band input manifest and prepared-band receipts do not constitute that cache. The local prepared outputs are not present in the checkout's `data/` tree. The current owner request does not identify a single executable method paragraph beyond requiring new hypotheses; selecting one and computing anyway would violate the standing lane rule. The maximum-three-experiment budget is not permission to bypass these prerequisites.

## H33 (`h33-h33-2-b2`) — evidence and interpretation

- The supplied **0.2778** and conflicting leaderboard maxima **0.3195 / 0.4413** are **OWNER-REPORTED**, not organizer-confirmed. No submission-page receipt is present; no DrivenData page was fetched or scraped.
- The pinned pixel-forensics record reports that H33 is the H28 parent with 2,545 dots removed in the mapped-catalogue distance band `sqrt(2)..2 px`, with zero dots added and unchanged parent dots outside that collar. This is a **RASTER-MEASUREMENT** and supports the interpretation that the score difference is associated with collar pruning, not a new geological signal. It does **not** prove that pruning caused the private leaderboard difference: the organizer score receipt and controlled scoring context are absent.
- Mechanistically, the shared metric grants each hidden truth pixel its maximum nearby triangular-kernel credit, while false-positive mass accumulates over predictions. Removing a low-incremental-credit dot can help, but only if saved false-positive cost exceeds lost truth credit; a mapped-fault collar is not proof of zero credit for an unmapped nearby fault.
- Therefore we cannot honestly claim this repository can beat the reported `0.2778`, nor turn a local holdout result into a leaderboard projection. Historical H86I-HVFD `HOLDOUT-DTI` evidence is `0.101327` (evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, 95% CI `[0.088559, 0.113897]`); this is a spatial hide-and-recover measurement, not an organizer score and not comparable to an unreceipted leaderboard score.

## Candidate hypotheses not yet implemented in this checkout

Ranking is qualitative expected information gain per implementation cost, not a predicted score. “New” means no implementation was found in this checkout's `src/` and `scripts/`; novelty across all external GEMSDOE sites or the scientific literature is **not certified**. Competition band meanings were checked against `src/gems86/io.py:BANDS`.

| Rank | Candidate and layers | Physical signature and reason it might recover an unmapped fault | Difference from code here | Named non-fault mimic | Cost / status |
|---|---|---|---|---|---|
| 1 | **Local cross-spectral gravity–magnetic admittance break** — Band 2 `rtp`, Band 13 `iso_grav_anom` | Measure windowed cross-power/coherence and a scale-dependent gravity–magnetic admittance; seek a persistent local relationship break beneath cover rather than another single-channel ridge. Buried displacement or juxtaposition could alter the relationship without a surface scarp. | No windowed cross-spectral/admittance implementation was found; existing GZZD/PCC lanes use local gravity curvature or signed gradient alignment, not this spectral residual. | Unfaulted lithologic contact, source-depth change, remanent volcanic magnetization, or resolution mismatch. | **Medium; rank 1. NOT RUN.** Requires frozen windows, scales, regularization and phase-scrambled controls before any holdout. |
| 2 | **Monogenic magnetic phase congruency** — Bands 2 `rtp` and 13 `iso_grav_anom` | Multi-scale log-Gabor/Riesz phase alignment may retain weak covered lineament continuity when amplitude ridges are weak; gravity is a corroboration channel, not a fault label. | No monogenic/Riesz/log-Gabor phase implementation found; current magnetic methods emphasize amplitudes, derivatives, or translations. | Lava-flow/dike boundaries, interpolation ringing, or acquisition seams. | **Medium; rank 2. NOT RUN.** Compare to amplitude-only controls at identical budget. |
| 3 | **Persistent potential-field saddle connections** — Bands 2 `rtp`, 13 `iso_grav_anom`, 15 `depth_to_base_surf` | Rank saddle-to-extremum connectors by persistence across smoothing scales; buried connectors could bridge anomaly bodies without a surface fault trace. Band 15 is gravity-derived and must not be presented as independent confirmation. | No persistence-ranked saddle graph found; current local topology is ridge/relay oriented. | Erosional paleovalley or superposed unfaulted source fields. | **Medium-high; rank 3. NOT RUN.** Needs graph randomization and ridge baselines. |
| 4 | **Conductivity-neck topology conditioned on dilatation** — Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate` | Look for narrow, threshold-persistent conductive necks spatially associated with extension; this could express a concealed fluid-permeability corridor. Scalar conductivity alone does not establish hydrothermal fluids or depth. | No persistent conductive-neck extraction found; differs from broad conductivity halos and clay-cap margins. | Saline playa brines, clay-rich paleochannels, interpolation bottlenecks. | **Medium; rank 4. NOT RUN.** Require broad-conductivity and strain-only controls. |

### Why rank 1 was not validated

No new external dataset is required for the first three candidates: they use competition feature bands. But that does not remove the mandatory **shared-cache** requirement. The pinned reference implementation describes downloading competition data from its official competition page; the repository has hash-pinned native-input receipts, but the actual derived template cache and its preprocessing/footprint identity are not available here. Rebuilding a private stack from the native TIFF would violate “reuse, don't rebuild.” Separately, the literal uniqueness preflight stops every nonempty candidate before surface construction. Thus CSPA is a proposal only: no isolated-feature AUC, HOLDOUT-DTI, CI, surface correlation, final-dot overlap, or candidate raster exists.

## Three-pass review and verification

### Pass 1 — inspect requirements and the working tree

- Read `AGENTS.md`, `PROMPT.md`, the complete `research/REQUEST_20261025.md`, README's decision section, and the latest repository handoffs.
- Confirmed the branch is `arena/43838d43-gemsdoe86`; the request archive and generated project status already exist. No unregistered candidate was found or added.
- Rechecked `src/gems86/io.py:BANDS`, `registry/h86g_hypotheses.json`, the native preparation manifest and the protocol-preflight witness. `grep` found no CSPA, monogenic/Riesz, saddle-connection, or conductivity-neck implementation in `src/` or `scripts/`.

### Pass 2 — run local integrity checks and inspect edge cases

- Installed only the locked test dependencies into ignored `.venv/`.
- `.venv/bin/python scripts/audit_release.py`: `audit_ok=true`, **21/21** inherited artifacts locally valid, decision **DO NOT SUBMIT**, 0 experiments and 0 slots in that audit. Local format checks do not grant scientific or upload authorization.
- `.venv/bin/python scripts/build_site.py --check`: PASS; evidence-generated site current, one historical artifact promoted for selector review only, no upload-authorized file.
- `.venv/bin/python scripts/check_site.py`: PASS; local links, registered TIFF/ZIP integrity and negative-state safety. This is not scientific clearance or proof of remote Pages deployment.
- `.venv/bin/python -m pytest -q`: **839 passed, 24 skipped, 41 subtests passed**; 42 Rasterio `PendingDeprecationWarning`s. No model experiment was run by the tests.

### Pass 3 — recheck against the full request

- The requested unique new TIFF cannot be produced honestly while the literal gate rejects every nonempty candidate, the shared cache is missing, and no single lane is assigned. We leave the stop conditions unchanged.
- The registered H86I-HVFD TIFF is not a substitute: its previous `HOLDOUT-DTI` is below the same-split historical H86C-KSLB comparator, and its literal registry report remains negative. Its TIFF/ZIP are explicitly audit-only and **DO NOT SUBMIT**.
- The top candidate is ranked but not tested. No score, holdout CI, AUC, uniqueness result, or organizer confirmation is fabricated.

## Trusted-source links for review

Only the official GitHub reference README was fetched during this session. The sandbox's outbound allowlist prevented a fresh automated fetch of DrivenData, USGS, GDR, the rules PDF, or Dropbox; those links are provided for manual review and were not newly verified here. No DrivenData page was scraped.

- Official DrivenData reference-solution repository at pinned commit (describes the benchmark and directs users to download data from the competition site): https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md
- Official DOE GDR Submission 1391 (not used by the ranked CSPA candidate): https://gdr.openei.org/submissions/1391
- Official USGS GeoDAWN data landing page: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Official USGS 3DEP landing page (relevant to the prior H86I lane, not required for CSPA): https://www.usgs.gov/3d-elevation-program
- Competition data page (browser review only; no automated access in this session): https://www.drivendata.org/competitions/306/competition-doe-gems/data/

## Remaining work, ordered by blocker

1. Obtain an explicit protocol-owner disposition for the full-support witness contradiction. Do not privately revise support semantics or thresholds.
2. Restore and hash-bind the actual shared feature cache and its preprocessing, footprint, and visible-mask identity; native bands are insufficient.
3. Resolve the two incompatible inventory rows under a written policy, then establish a complete same-grid registry snapshot.
4. Assign one lane paragraph. Freeze a <=3-experiment / <=2-hour plan; use the shared evaluator/writer; derive catalogue features only from visible faults, mask them pixel-exactly, and run every feature-alone leakage canary first.
5. Only after same-split paired HOLDOUT-DTI improves against the strongest rerunnable control and both surface and final-dot registry gates pass should a file be considered for a separate selector. Organizer-confirmed scores require an actual submission-page receipt.

## Run card

See [`docs/evidence/arena-43838d43-run-card.json`](../docs/evidence/arena-43838d43-run-card.json). This review's verdict is **negative**; no TIFF identity exists for this session.
