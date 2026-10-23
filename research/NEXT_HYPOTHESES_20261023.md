# Ranked next hypotheses (reviewed 2026-10-23)

## Decision and evidence boundary

**No hypothesis was run in this review.** The pinned dense-witness certificate makes every nonempty support in the allowed domain fail the current literal three-pixel overlap gate. The H86B lane has already consumed its three declared experiments; this review does not select or spend a weekly slot.

Ranks below are a **qualitative ordering of scientific priority and implementation feasibility**, not a forecast of DTI or leaderboard performance. No numerical gain is predicted. All candidates need a new preregistration and a fixed spatially blocked holdout before implementation. The repository's reusable shared feature cache is absent, and restored data mirrors are not independently organizer-authenticated.

## Novelty audit: do not relabel existing work

The retained H86B feature list already includes geothermal well disequilibrium, surface MT conductivity gradient/ridge, multi-scale magnetic ridges, a 150 m upward-continuation attenuation gradient, magnetic director disruption, gravity tilt/gradient, magnetic–gravity contact offset, basement step gradient/ridge, geodetic strain, LiDAR scarplet-chain vote, DEM valley/hinge fields, and radiometric–topography discordance. Those primitives are not called untried here.

Earlier H33 work also proposed oriented multi-physics lineaments, drainage/LiDAR chains, long straight conductive/basement boundaries, and an event-density/focal-plane seismicity hypothesis. Some were tested and some were blocked; none is repeated as a new hypothesis below. The H86B 38-feature inventory and earlier hypothesis archive are the basis for this novelty screen.

## Ranking

| Rank | Distinct hypothesis | Qualitative potential | Cost | Input availability in this checkout | Status |
|---:|---|---|---|---|---|
| 1 | Multi-scale basement-curvature / gravity-curvature coherence | Moderate, mechanistically targeted | Medium | Relevant bands exist in the owner-supplied feature mirror; reusable shared cache is absent | Not tested; blocked by protocol |
| 2 | Windowed magnetic spectral source-depth transition | Low-to-moderate, high uncertainty | High | TMI/RTP bands are referenced by the local feature stack; validated source metadata and reusable cache are absent | Not tested; blocked by protocol |
| 3 | Magnitude-frequency and recurrence anomalies in raw earthquakes | Potentially moderate only if event coverage/completeness is adequate | High; external data, completeness modeling, and spatial analysis | Only very broad smoothed seismic bands appear in the existing stack; no raw event catalog was restored | Not viable now; obtainability not checked this session |
| 4 | Depth-migrating MT conductivity boundary | Unknown-to-moderate if depth-resolved inversions are available and well constrained | Very high; new data and inversion-resolution audit | Local H86B has only scalar surface conductivity derivatives; no depth stack is in the manifest | Not viable now; data availability not verified |

## 1. Multi-scale basement-curvature / gravity-curvature coherence

**Mechanism.** A buried fault or fault-controlled basin margin can produce a change in basement-surface curvature together with a laterally aligned density boundary. Derive scale-normalized Hessian eigenvalues and axial directions from the basement-depth surface at several preregistered scales; independently derive gravity curvature from the gravity high-gradient layer. Score only spatially persistent, orientation-consistent curvature structures, and retain polarity as a tested factor rather than choosing the favorable sign after viewing holdout results.

**Non-fault mimic.** Basin edge, intrusive contact, basement lithology boundary, survey seam, or inversion/gridding edge can produce the same basement–gravity alignment.

**What is genuinely new.** H86B already has basement step/ridge and gravity tilt/gradient plus a magnetic–gravity contact-offset feature. This proposal is not “add basement curvature” in isolation: the distinct object is a preregistered multi-scale, signed/oriented **second-derivative cross-physics coherence and persistence** measure. A source-code audit should explicitly confirm that no equivalent shared feature is already cached before implementation.

**Data and validation.** The bands are part of the local owner-supplied feature mirror, but that mirror does not independently authenticate organizer provenance. The required shared feature cache is missing. If later made eligible, build the feature without catalogue-derived inputs; run the feature-alone leakage canary first; then use the shared spatially blocked whole-segment holdout, with visible faults masked pixel-exactly and all catalogue-derived fields generated from visible faults only. No holdout result exists for this hypothesis.

**Official review link.** [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) for task and feature context. Not freshly fetched during this review.

## 2. Windowed magnetic spectral source-depth transition

**Mechanism.** Estimate radial power-spectrum slopes from overlapping windows of the TMI/RTP field at a fixed, preregistered window scale; compare nested windows or spectral bands to form a *relative source-depth-transition proxy*. Test whether coherent depth-regime boundaries align with independent structural evidence. This is not a direct Curie-depth or geothermal-temperature measurement: those interpretations require restrictive assumptions about magnetization, source geometry, survey altitude, and spectral stationarity.

**Non-fault mimic.** Lithologic/remanent-magnetization changes, survey-line leveling, gridding artifacts, and variable flight height can all shift spectral slopes without a fault or heat source.

**What is genuinely new.** H86B already has multi-scale magnetic ridges, a magnetic Hessian, tilt/director disruption, and one 150 m upward-continuation attenuation gradient. It does not include a windowed radial-spectrum estimate or a scale-persistent source-depth transition. A single upward-continuation difference must not be presented as a spectral-depth inversion.

**Data and validation.** TMI/RTP are represented in the local feature inventory, but the shared cache and independently authenticated raw feature source are absent. Implementation cost is high because window edges, anisotropic survey sampling, and scale choice need locked controls. A feature-alone canary and spatially blocked holdout are mandatory; no score is available or predicted.

**Official review link.** [USGS GeoDAWN survey page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Not freshly fetched during this review.

## 3. Magnitude-frequency and recurrence anomalies from raw earthquakes

**Mechanism.** Replace broad smoothed seismic density with event-level, spatially blocked estimates of magnitude-frequency slope (Gutenberg–Richter *b*-value) and recurrence/swarm residuals. Estimate local magnitude of completeness first and suppress unstable cells; only then test whether persistent anomalies align with independent structural evidence. Signs are not assumed: the expected relationship between *b*-value, stress, fracturing, and hydrothermal fluid is context-dependent.

**Non-fault mimic.** Quarry blasts, induced seismicity, aftershock clusters, station-coverage changes, magnitude-completeness drift, and event-location uncertainty can create apparent anomalies.

**What is genuinely new.** The earlier H33-E idea was epicenter density plus focal-plane/nodal-plane orientation. This is deliberately different: magnitude-frequency and temporal recurrence **conditioned on completeness**, not an event-density ridge or a focal-plane lineament. H86B uses no raw event catalog; its available seismic bands are broad smoothed covariates.

**Data and validation.** The [USGS ComCat FDSN event service](https://earthquake.usgs.gov/fdsnws/event/1/) is the named official source to check. It was not queried during this review, no raw event file exists in the local manifest, and network obtainability is not established here. Until a bounded event extract, completeness diagnostics, and licensing/provenance receipt are saved, this candidate is **not viable to execute**. No focal mechanism or event coverage is assumed.

## 4. Depth-migrating MT conductivity boundary

**Mechanism.** If the INGENIOUS MT inversion provides uncertainty-qualified conductivity/resistivity slices at several depths, trace a lateral boundary through depth and test whether it migrates consistently with a steep fault plane. The response would be a cross-depth boundary track, not merely a surface conductivity gradient.

**Non-fault mimic.** Basin fill, lithologic contacts, inversion smoothing/regularization, and edge artifacts can produce apparent depth migration.

**What is genuinely new.** H86B contains `mt_cond_z`, `mt_cond_grad`, and `mt_cond_ridge` from a scalar surface conductivity layer. The distinct candidate requires a depth stack and an explicit inversion-resolution/uncertainty model; neither is in the present feature manifest. It is not a repackaging of those existing surface derivatives.

**Data and validation.** The [DOE Geothermal Data Repository record 1391](https://gdr.openei.org/submissions/1391) is the source to inspect, but its live availability, depth-slice contents, and license were not verified this session. The repository does not contain the required depth-resolved slices or uncertainty products. Therefore this is **not currently obtainable/validated from this checkout** and is not proposed as ready-to-run.

## Common preregistration if a future protocol permits work

1. Stay within the declared single method lane and use the pinned shared feature cache, evaluator, and submission writer; do not fork shared tools.
2. Freeze the transform and scale choices before holdout evaluation. Derive any catalogue feature only from visible faults; mask visible faults pixel-exactly.
3. Run a feature-alone leakage canary; AUC above 0.90 is a stop until explained.
4. Report only **HOLDOUT-DTI** with evaluator version, withheld-positive count, and paired 95% CI. No projection is a score.
5. Compare the pre-placement surface and final dots against every available hash-pinned registry raster under the literal `rho > 0.90` or forward 3-pixel overlap `> 0.70` stop. A partial registry cannot clear uniqueness.
6. Do not run any experiment or emit a TIFF while the current universal witness remains binding. At most three experiments or two hours; no weekly slot is selected by the experiment runner.
