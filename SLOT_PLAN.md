# Slot plan — 2026-10-23

**No automatic submission.** R0 is `h33-h33-2-b2`, 37,654 unit-mass dots, rebuilt byte-for-byte (`c55bafc4…b6fa9`). Its reported `0.2778` remains a **CLAIM**; no submission receipt, `TOP_PUBLIC`, or rolling-week quota was supplied. The brief states a 2026-12-03 deadline, but it is **UNVERIFIED** here because competition pages must not be fetched. From 2026-10-23 that is about 5.9 weeks. A live change with `|Δ| < 0.01` is no evidence.

## Next three weekly slots (conditional; human submits one file per slot)

| Order | Candidate | Why this order / decision rule |
|---|---|---|
| 1 | **CONCENTRATION `b5km-cvband-down4`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6-zeros.tif` | Count fixed; 8.00% changed; `1 km` occupied-block CV `0.6235 → 0.5162`; **+0.0015 MODEL** and **+0.0008 PROXY** (95% CI `[-0.0004,+0.0018]`). Both are below evidence threshold. A live `Δ ≥ +0.01` justifies a conservative confirmation; `Δ ≤ -0.01` closes this concentration mechanism. |
| 2 | **RELIEF `front+15pct`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | Count fixed, 15.00% moved piedmont→range-front; **+0.0017 MODEL**, 3/4 quadrants positive. `Δ ≥ +0.01` supports a small-dose confirmation; `Δ ≤ -0.01` closes the front-allocation hypothesis. |
| 3 | **PRUNE `le3p000`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | Removes the 2–3 px collar at fixed count; **+0.004 MODEL**, confounded by mass/halo alignment. `Δ ≥ +0.01` would justify testing a farther collar; a flat or negative receipt retains R0's 2 px clearance. |

The new R0 **PRUNE `3.75px`** build (`h33-h33-2-b2-PRUNE3p75-20261023-a90d5477`) is **not in the default slot queue**: `-0.002 MODEL`, report-only SGMC delta `-0.0040`, and a contaminated catalogue PROXY of zero. It exists to test the farther-collar mechanism reproducibly, not because it is expected to win. Consider it only if `le3p000` first yields a same-entity live receipt `≥ +0.01`. Do not upload both NaN and zeros twins.

## Calendar and controls

- **Weeks 1–2:** at most three scored submissions in any rolling week; log the portal receipt score and date before the next upload. Verify the actual quota, `TOP_PUBLIC`, and R0 receipt with the human.
- **Weeks 3–4:** repeat/confirm only a receipt-backed axis with `Δ ≥ +0.01`; make one attributable combination only if its single levers are receipt-verified.
- **Weeks 5–6:** blind final selection from receipt-verified candidates; keep one fallback and re-run format checks on both. Never treat MODEL or PROXY values as scores.
- **Before any upload:** check the official deadline, entity quota, accepted outside-footprint encoding, and organizer uniqueness rule. Candidate rasters remain local-only while public-repository data-use terms are unchecked.

## Better future axes (proposals only; not built this session)

1. **Rotation-stable multi-signal lineament persistence.** Mechanism: prioritize strike-like edges that persist across TMI/gravity gradients and modest grid rotations, reducing single-band and flight-direction artefacts. Confounder: E–W acquisition lineaments and basin-margin scarps. Falsifier: persistence is no better than randomized azimuths, or the independent SGMC surrogate has no positive quadrant-consistent change.
2. **Cover-window-conditioned fault expression.** Mechanism: condition ridge/edge priors on thin-cover or pediment windows where buried structures can be expressed without basin-wide clutter. Confounder: pluvial shorelines, channels, roads, and alluvial contacts. Falsifier: no incremental independent-map performance over the matched ridge baseline or geologist review rejects the predicted traces.

**Human must supply:** `TOP_PUBLIC` and date; remaining rolling-week slots; confirmed deadline; R0 portal receipt; accepted null encoding; and authorization for any one manual upload. No submission has been made by this agent.
