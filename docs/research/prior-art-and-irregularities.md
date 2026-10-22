# Prior-art review and irregularity register

**Review scope:** read-only inspection of the public GEMSDOE32 and GEMSDOE83 GitHub material available in the workspace, the public official leaderboard, official competition pages, and official USGS/GDR source pages. This is not a complete inventory of every sibling project or organizer registry. Missing methods in two repositories are not proof of global novelty.

## Findings that change the plan

1. **Moment tensors are prior art.** GEMSDOE32 H33-E and GEMSDOE83 H84-E both propose ComCat/epicenter lineaments or focal-mechanism planes. They are excluded from the new shortlist, even though the USGS FDSN endpoint is reachable.
2. **Several apparent “new” ideas are already explored.** The inspected predecessor set includes multi-physics lineament consensus, drainage/valley chains, LiDAR scarplets, conductivity/basement edges, thermal-infrared leads, well/spring geochemistry, SGMC fault priors, relay geometry, catalogue-flank pruning, and spatially constrained emitters. Do not relabel these as new.
3. **A different conductance dataset is a conditional lead, not a result.** The official USGS ScienceBase entry describes five MT-conductance layers from 2 km to 200 km depth. The inspected predecessor manifests/methods do not name these `gb_conductance_*` rasters. However, those projects have used surface conductivity and related geophysics; novelty is limited to the depth-resolved source/feature and remains provisional pending a complete registry search.
4. **The required data/evaluator stack is unavailable here.** No authorized competition data, cached feature stack, full registry index, or local scientific Python stack was found in GEMSDOE86. The DrivenData data page redirects to login. No experiment or TIFF can be honestly produced.
5. **Shared-tool protocol must be explicit.** `holdout.py` exposes more than one split protocol. This project’s required plan selects `buffered_component_draw`: whole 8-connected components, label-blind quadrant selection, and a separate feature-context buffer. Do not silently substitute the short-strand `build_holdout` protocol. The inspected evaluator/writer were not executed.

## Score-claim audit

| Claim | Evidence label | Audit conclusion |
|---|---|---|
| Public leaderboard top entry: xiaofanhu, 0.4413 | **ORGANIZER-CONFIRMED — official public leaderboard listing fetched 2026-10-22 UTC; not a GEMSDOE86 result and not an artifact receipt** | Current official board snapshot, superseding the older 0.3195 figure. |
| H33 claim: 0.2778 | **OWNER-REPORTED — UNVERIFIED; not ORGANIZER-CONFIRMED** | One owner article calls the value confirmed, but the GEMSDOE32 public project index says no organizer score exists for any artifact in that repository. No organizer receipt was found in this review. Do not present 0.2778 as confirmed. |
| H33-2-B2 “projected live DTI” 0.2747 | **OWNER-PROJECTED VALUE — NOT A SCORE** | The owner-side validation manifest explicitly describes it as a model/projection and also says “NO ORGANISER SCORE EXISTS.” Do not compare it to an observed leaderboard score. |
| GEMSDOE86 result | **No result** | No holdout was run; there is no score, withheld-positive count, 95% CI, or receipt. |

Source links: [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/); [GEMSDOE32 public index](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html); [GEMSDOE32 owner manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/registry/submission_build.json); [GEMSDOE83 owner article](https://buffedlizard55-lab.github.io/GEMSDOE83/research/why-h33-scored-02778.md).

## Provenance and implementation flags

- The official DrivenData data URL is login-walled in this session. A public mirror is not a substitute for an organizer-authenticated download. The GEMSDOE83 manifest itself states that its feature TIFF is an owner-supplied mirror and **not organizer-authenticated**.
- The GEMSDOE83 `registry/data_manifest.json` records the same SHA-256 and byte count for `labels.tif` and `existing_faults.tif`. This may be intentional in that project’s data model, but it was not independently verified against the organizer files; treat it as an audit question, not a fact about the competition release.
- The shared `registry/template_pin.json` names an upstream commit and notes a local amendment to `uniqueness.py`. The clone’s code and pin were inspected, but the upstream pin and every file digest were not independently reconciled here. Do not claim byte-for-byte template identity until that check is recorded.
- The public registry index is not demonstrated to be organizer-complete. A curated list or a check against only local peer TIFFs cannot pass the required uniqueness gate.
- The owner-reported H83/H84 experiment scores and feature claims in peer repositories are historical leads only. They are not imported into the GEMSDOE86 run card or called current `HOLDOUT-DTI` results, because the required shared evaluator version/withheld count/95% CI have not been independently reproduced here.
- A previous broad earthquake query used an approximate bounding box; its count is not an exact GEMS-AOI coverage count. The USGS conductance catalog bounding box contains the coarse screen window, but valid-pixel coverage of the exact raster footprint remains unchecked.
- **USGS conductance georeferencing flag:** the associated surface-layer `.tfw` file was fetched from the official ScienceBase record and reports pixel spacing `1000, 0, 0, −1000` with origin `−494741.8946, 2297582.2934` in map coordinates. The ScienceBase raster facet declares `EPSG:4269`, whose geographic coordinates do not match the projected-looking world-file origin/spacing. The GeoTIFF itself was not fetched, so the internal tags may resolve this; until then, do not assume the true CRS, ground pixel size, or exact target coverage. If the map units are metres, the nominal grid would be much coarser than the competition’s 300 m kernel, which would restrict the layer to regional context rather than direct dot placement.

## Stop/go decision

**STOP before implementation and before producing a submission file.** The H86-A lead can proceed to source download/coverage audit only after official competition inputs, the shared cache/tools, and a complete registry inventory are made available through authorized channels. If any feature-only AUC exceeds 0.90, quarantine it until leakage is explained. If either uniqueness threshold is exceeded, record the duplicate and stop. No weekly slot is allocated by this review.
