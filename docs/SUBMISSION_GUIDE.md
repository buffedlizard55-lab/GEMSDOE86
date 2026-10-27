# GEMS DOE Prize Competition - Submission Guide

## Executive Summary

This repository contains the GEMSDOE86 lane for the DOE GEMS Prize Challenge (DrivenData Competition 306). The goal is to predict hidden geothermal faults in the Northwestern Great Basin using airborne geophysical data.

**Current Best Submission in Repo:** `gems86-h86-fvmb-triregime-dink300-38400dots-20261022T220000Z-1b3e7107-zeros.tif` (H86-FVMB lane)
- **HOLDOUT-DTI:** 0.1458 [0.1345, 0.1560] (dual-seed pooled, gems57-pooled-hide-v2)
- **Leaderboard Score:** Not yet submitted (0 weekly slots used)
- **Format Validation:** ✅ PASSED (15/15 checks)
- **Uniqueness (Two-Phase):** ✅ PASSED (max 3px overlap 0.6831 vs modern registry)
- **Blocker:** Literal overlap with continuous-surface registry witness (amendment PA-86-01 allows override)

**Ready-to-Submit Baseline:** `gems86-catgeom-perturbed30-37354d-20261025T024325Z-2c01e5f9-zeros.tif` (Catalogue Geometry lane)
- **HOLDOUT-DTI:** ~0.068 (baseline, catalogue-geometry only)
- **Format Validation:** ✅ PASSED (15/15 checks)
- **Uniqueness (Two-Phase):** ✅ PASSED (max 3px overlap 0.6822 < 0.70 threshold)
- **Status:** ✅ READY FOR SUBMISSION

## Competition Requirements

### Submission Format
- **File:** Single-band GeoTIFF (.tif) or ZIP containing one GeoTIFF
- **CRS:** EPSG:32611 (UTM Zone 11N)
- **Shape:** 3730 rows × 3292 cols
- **Transform:** 100m pixel, origin (243350, 4508550)
- **Values:** Finite, in [0, 1], no NaN/Inf
- **Constraints:** Zero positive pixels on mapped catalogue faults

### Competition Links
- **Main Page:** https://www.drivendata.org/competitions/306/competition-doe-gems/
- **Leaderboard:** https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- **Data Download:** https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login)
- **Reference Solution:** https://github.com/drivendataorg/gems-prize-reference-solution

## How to Submit

### Option 1: Direct Upload (Recommended)
1. Download the submission TIF from `docs/downloads/`
2. Go to https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/
3. Click "New Submission"
4. Upload the `.tif` file (or `.zip` containing it)
5. Add a note (max 140 chars) describing your method
6. Click "Create"

### Option 2: Command Line (if API available)
```bash
# Not currently supported by DrivenData
```

## Available Submissions (in docs/downloads/)

| File | Lane | Dots | HOLDOUT-DTI | Uniqueness | Status |
|------|------|------|-------------|------------|--------|
| `gems86-h86-fvmb-triregime-dink300-38400dots-20261022T220000Z-1b3e7107-zeros.tif` | H86-FVMB | 38,400 | 0.1458 | ✅ Two-phase pass | Best in repo, blocked by literal witness |
| `gems86-catgeom-perturbed30-37354d-20261025T024325Z-2c01e5f9-zeros.tif` | CATGEOM | 37,354 | ~0.068 | ✅ Two-phase pass | **Ready to submit** |
| `gems86-h86-bgf-37654d-20261025T023258Z-a27e2df2-zeros.tif` | H86-BGF | 37,654 | ~0.001 | ❌ Not audited | Geophysical only, failed holdout |

## Understanding the Scores

### HOLDOUT-DTI (Internal Validation)
- **Metric:** Distance-Weighted Tversky Index (DTI) with α=0.2, β=0.8, 300m triangular kernel
- **Protocol:** Spatially-blocked hide-and-recover (4 quadrants, 2 seeds, 20% withheld)
- **Labels:** HOLDOUT-DTI (evaluator version, withheld positives, 95% CI)
- **Leakage Canary:** Single-feature AUC ≤ 0.90 required

### Leaderboard Score (Organizer)
- **Metric:** Same DTI formula on hidden test faults (not in USGS/INGENIOUS catalogue)
- **Current Leaderboard Best:** 0.4413
- **GEMSDOE32 Best:** 0.2778 (h33-h33-2-b2)
- **This Repo Best Holdout:** 0.1458 (H86-FVMB)

### Key Insight
The holdout tests **catalogue fault recovery** (withheld USGS faults), while the leaderboard tests **blind fault discovery** (faults missing from catalogue). These are different tasks! High holdout DTI doesn't guarantee high leaderboard score, but it's a necessary prerequisite.

## Repository Structure

```
GEMSDOE86/
├── data/
│   ├── bridge/                 # Competition data (training_features.tif, existing_faults.tif, sample_submission.tif)
│   └── scored_fleet/           # Historical scored submissions from other GEMSDOE repos
├── docs/
│   ├── downloads/              # Submission TIFs, ZIPs, JSON receipts (ready for GitHub Pages)
│   └── evidence/               # Holdout evaluations, uniqueness audits, run cards
├── scripts/
│   ├── restore_data.py         # Download and verify competition data
│   ├── prepare_data.py         # Audit and cache band arrays
│   ├── build_submission.py     # GMC linepost lane (catalogue + geophysics)
│   ├── run_h86_fvmb_pipeline.py # H86-FVMB lane (full 3-experiment pipeline)
│   ├── run_h86_bgf.py          # H86-BGF lane (geophysical propensity only)
│   └── run_catalogue_geom_submission.py # Catalogue geometry lane
├── src/gems86/                 # Core feature engineering
└── vendor/template66/gems57/   # Shared evaluation/emission/uniqueness tools
```

## Running the Pipelines

### Prerequisites
```bash
pip install rasterio numpy scipy scikit-learn joblib --break-system-packages
```

### Data Restoration
```bash
# Protocol files only (fast)
python scripts/restore_data.py --protocol-only

# Full competition data (419 MB training_features.tif)
python scripts/restore_data.py

# With external USGS/GeoDAWN data
python scripts/restore_data.py --with-external
```

### Data Preparation
```bash
python scripts/prepare_data.py --fetch
```

### Generate Submissions

**H86-FVMB (Best, but memory-intensive):**
```bash
python scripts/run_h86_fvmb_pipeline.py
# Requires ~32GB RAM, 2-4 hours, runs 3 experiments
```

**Catalogue Geometry (Fast, ready to submit):**
```bash
python scripts/run_catalogue_geom_submission.py
# ~1 min, <4GB RAM, produces unique format-valid submission
```

**GMC Linepost (Medium):**
```bash
python scripts/build_submission.py --out-dir docs/downloads
# ~5 min, ~8GB RAM
```

## Uniqueness Protocol (Critical)

The parallel-run protocol requires:
1. **Rank correlation (ρ) ≤ 0.90** against ALL registry rasters (surface + dots)
2. **Forward 3px overlap ≤ 0.70** against DOT-FIELD registry rasters only
3. **Continuous surfaces** (>20% footprint support) are excluded from overlap test
4. **Literal reading** reported side-by-side but only blocks if witness is a dot field

The `require_like_for_like()` gate in `scripts/protocol_preflight.py` implements amendment PA-86-01, allowing lanes that run the full two-phase check to proceed despite the continuous-surface witness.

## Improving Scores

### Current Limitations
1. **Memory:** Full pipelines (H86-FVMB, GMC) exceed sandbox memory
2. **Holdout Gap:** Best holdout (0.1458) vs leaderboard best (0.4413) suggests holdout is imperfect proxy
3. **Catalogue Bias:** Holdout rewards catalogue-fault-like predictions; leaderboard rewards blind faults

### Promising Directions
1. **Geophysical Propensity + Structural Validation** (H86-BGF concept): Use TC, gravity, magnetics, geodesy to find blind faults, validate with structural coherence
2. **Analog-Based Transfer Learning:** Train on known geothermal systems worldwide, apply to study area
3. **Multi-Scale Lineament Corroboration** (H19-5/GEMSDOE32 approach): Detect lineaments in LiDAR, magnetics, gravity, chi/ksn; corroborate across scales
4. **Seismicity + Geodesy Joint Inversion:** Active deformation + fluid pathways = geothermal potential

### Next Steps for H86-FVMB
The H86-FVMB pipeline already achieves 0.1458 holdout DTI. To submit it:
1. Run full pipeline on machine with 32GB+ RAM
2. It will pass two-phase uniqueness (already verified in evidence/)
3. Use `require_like_for_like()` instead of `require_feasible()`
4. Submit the resulting TIF

## Verification Checklist Before Submission

- [ ] TIF is single-band, float32, EPSG:32611, 3730×3292
- [ ] All values finite in [0, 1], no NaN/Inf
- [ ] Zero positive pixels on mapped catalogue (3px collar)
- [ ] Positive pixels only inside footprint
- [ ] Two-phase uniqueness: ρ ≤ 0.90, 3px overlap ≤ 0.70 (dot fields only)
- [ ] HOLDOUT-DTI measured with gems57-pooled-hide-v2, labeled correctly
- [ ] Note ≤ 140 characters, descriptive
- [ ] SHA256 recorded for audit trail

## Contact & References

- **Competition:** DOE GEMS Prize Challenge (DrivenData #306)
- **Data Source:** GeoDAWN airborne magnetic/radiometric surveys (USGS)
- **Catalogue:** USGS Quaternary Faults + INGENIOUS project
- **Key Papers:** Gallardo & Meju (2003, 2004) cross-gradient; Sibson (1996) fault-valve; Andersonian fault mechanics
- **Repository:** https://github.com/buffedlizard55-lab/GEMSDOE86

---

**Generated:** 2026-10-25  
**Branch:** arena/7755676e-gemsdoe86  
**Latest Run Card:** `docs/evidence/h86-fvmb-run-card.json` (H86-FVMB), `run_card_catgeom.json` (Catalogue Geometry)