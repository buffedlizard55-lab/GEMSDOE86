# H86K candidate hypotheses (generated 2026-10-25, ranked)

All use only the hash-pinned 19-band `data/bridge/training_features.tif`
(SHA256 in `data/prepared_manifest.json`) — no new external data required.

| Rank | ID | Layers / signature | Why it should catch a catalogue-missing fault | Differs from repo lanes | Cost |
|---|---|---|---|---|---|
| 1 | H86K-STC | Structure-tensor coherence of RTP (band 2) at 5px scale × coincident magnetic HG (3) + gravity HG (5, verified = hypot(11,18)) edges × basement-depth gradient (15) | A buried basement fault step produces a *coherent-strike, coincident* mag+gravity edge even where no scarp/catalogue trace exists; incoherent pluton contacts / playa edges lack multi-km strike coherence | No prior lane used structure-tensor *orientation coherence* of RTP gated by coincident two-field edges; prior lanes used magnitudes/admittance/phase alone | Low |
| 2 | H86K-THK | Radiometric Th/K (band 6 TC proxy unavailable as ratio in native stack; would need GeoDAWN external) edge + DEM slope (19) | Hydrothermal K-metasomatism along blind conduits | Needs external GeoDAWN restore; not run | Medium |
| 3 | H86K-CURIE | Depth-to-basement (15) second derivative (ridge of basement relief) × seismicity (16) | Intrabasin horst-edge faults with seismicity, no mag edge | Partly covered by prior depth lanes; not run | Low |
| 4 | H86K-DIL | Geodetic dilatation (8) sign-change zero-crossing × shear (7) | Active transtensional stepovers | EWCS/CSGD used strain as gate, not zero-crossing locus; not run | Low |
| 5 | H86K-SARX | SAR-debiased version of rank 1 | Buried piedmont faults | CSGD already SAR lane; not run | Medium |

Selected: **H86K-STC** (rank 1). Non-fault mimic: unfaulted pluton
wall-rock contacts and lithologic basement ridges (coherent edges without
fault offset) — mitigated only partially by requiring mag+gravity coincidence.

Verdict rule (pre-registered): promote only if pooled HOLDOUT-DTI (gems57-pooled-hide-v2)
beats the tmi_hg single-feature arm, every single-feature canary AUC ≤ 0.90,
surface Spearman ρ ≤ 0.90 and final-dot 3px overlap ≤ 0.70 vs every locally
available registry raster, and the fail-closed writer + independent validator pass.
Otherwise verdict = negative / DO NOT SUBMIT. 0 weekly slots used regardless in this session.
