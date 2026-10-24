#!/usr/bin/env python3
"""TRACKB (Phase 2) axis on R0 (``h33-h33-2-b2``): >= 1 km strike traces, GeoJSON dossier, and 3 R0 variants.

Pipeline (strictly ordered per brief v2)
----------------------------------------
1. Hash-verify all pinned manifest inputs (``registry/data_manifest.json`` + ``research/template_pin.json``).
2. Rebuild parent R0 (``h33-h33-2-b2``) from pinned ``base`` + ``existing_faults.tif`` (``d_cat > 2.0 px``)
   and verify byte-for-byte SHA-256 identity ``c55bafc4...b6fa9`` (stop immediately on mismatch).
3. Lock pre-registered mechanism cards and live-change predictions BEFORE running any surrogate.
4. Extract all non-branching >= 1.0 km strike-consistent traces from R0's dots along the pinned
   ``H19-5`` ridge network using susceptibility-invariant multi-physics corroboration (5 km AGC
   GeoDAWN ``TMI_up150`` gradient + USGS 3DEP 10 m scarp composite).
5. Build the 3 controlled ``TRACKB`` variants of R0 (``cull1dot``, ``bridge1km``, ``rendertop120``),
   write NaN-outside and zeros-outside GeoTIFF pairs in ``releases/axis86/``, re-read every raster
   from disk, and enforce all MUST-pass gates.
6. Export RFC 7946 GeoJSON (``releases/trackb/gems86-h33-2b2-trackb-top120-20261023.geojson``,
   gitignored per ``IR-86-TRACKB-04``) + geologist dossier and mechanism cards
   (``evidence/trackb-geologist-dossier.md``) with one evidence paragraph per trace.
7. Run report-only instruments (SGMC off-catalogue control + quadrant & +/-6 px translation splits
   + random-relocation null control + pure-top120 diagnostic; 4-fold buffered-component catalogue
   hide-and-recover PROXY with 95 % block-bootstrap CI; single-feature leakage canary with
   AUC > 0.90 stop check) and emit ``evidence/trackb_hybrid_20261023.json``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

from gems57 import metric  # noqa: E402
from gems86 import instrument  # noqa: E402
from gems86 import trackb_hybrid as tb  # noqa: E402
from gems86_axis import bands as axis_bands  # noqa: E402
from gems86_axis import gates, grid_io  # noqa: E402

DATE = "20261023"
SEED = 20261023
PARENT_ID = "h33-h33-2-b2"
PARENT_PREFIX = "gems86-h33-2b2"
PARENT_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
BASE_REL = "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
BASE_SHA256 = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
PARENT_REL = "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
CACHE = ROOT / ".cache" / "gems_data"
OUT_DIR = ROOT / "releases" / "axis86"
GEOJSON_OUT = ROOT / "releases" / "trackb" / f"gems86-h33-2b2-trackb-top120-{DATE}.geojson"
DOSSIER_OUT = ROOT / "evidence" / "trackb-geologist-dossier.md"
CARD_OUT = ROOT / "evidence" / f"trackb_hybrid_{DATE}.json"
TOP_K_DOSSIER = 120

REQUIRED_MANIFEST_IDS = (
    "sample_submission",
    "existing_faults",
    "scored_h33_2_b2_zeros",
    "scored_h19_5",
    "ext_derived_sgmc_faults_100m_u8",
    "ext_geodawn_extensions_u8",
    "ext_geodawn_extensions_json",
    "ext_geodawn_rad_u8",
    "ext_geodawn_rad_json",
    "ext_topo_10m_derived_100m_u8",
    "ext_dem10_chi_100m_i16",
    "ext_tiger_road_distance_m",
)

# Pre-registered mechanism cards & live-change predictions (locked BEFORE running any surrogate)
PREREGISTERED_CARDS: dict[str, dict[str, Any]] = {
    "cull1dot": {
        "title": "TRACKB / cull1dot — pure deletion of isolated 1-dot singletons (<550 m)",
        "slot_candidate": False,
        "hypothesis": (
            "R0's 3,349 isolated 1-dot singletons (8.894% of R0; zero R0 neighbours within 550 m) "
            "cannot form >= 1 km Phase 2 fault traces and represent localized geophysical/topographic "
            "speckles whose expected truth coverage sits below the DTI isolated-dot inclusion bar "
            "c = 0.2 * DTI (~0.0556); deleting them while keeping 100% of multi-dot chains and "
            ">= 1 km traces trims false-positive denominator weight without eroding trace recall."
        ),
        "mechanism": (
            "Surface-rupturing and range-bounding normal/oblique faults in the Great Basin scale at "
            "L >> 500 m across 100 m GeoDAWN pixels. An unlinked 1-dot island in a d=2.83 px "
            "ridge-thinned network marks a sub-550 m local gradient spike rather than a continuous "
            "fault plane. Under DTI = T / (0.2T + 0.2(S - M) + 0.8|G|), setting delta_S = -3,349 "
            "reduces 0.2*(S - M) while preserving 100% of R0's >= 1 km traces."
        ),
        "mimicking_non_fault_process": (
            "Small volcanic plugs/cones, isolated mafic erosional knobs, talus aprons, stock-pond "
            "berms, or single-line airborne survey tie-line levelling spikes (which make cull1dot "
            "help); conversely, short bedrock windows of real buried range-front faults peeking "
            "through thick piedmont alluvium (which make cull1dot hurt)."
        ),
        "predicted_live_change": "+0.0010 MODEL (band -0.0040..+0.0040; |delta|<0.01 = no single-slot evidence)",
        "predicted_sign": "near-zero / slightly positive (+0.0010 MODEL; below 0.01 evidence floor)",
        "falsifier": (
            "Live delta <= -0.010 falsifies singleton noise-dominance and proves R0's isolated dots "
            "capture real segmented or alluvium-masked fault windows above the 0.2*DTI bar."
        ),
        "form_note_template": "R0 TRACKB cull1dot: drop {removed} isolated 1-dot speckles (<550m); keep 100% >=1km traces",
    },
    "bridge1km": {
        "title": "TRACKB / bridge1km — count-fixed kernel-spaced gap bridging & tip extension on >= 1 km traces",
        "slot_candidate": False,
        "hypothesis": (
            "Reallocating R0's 3,349 isolated 1-dot singletons (17.788% of R0 cells changed, total "
            "mass fixed at 37,654) into internal > 300 m kernel blind spots and 320 m collinear "
            "tip steps along R0's strike-consistent >= 1 km traces converts sub-bar isolated mass "
            "into contiguous along-strike fault coverage without paying sub-kernel overlap tax."
        ),
        "mechanism": (
            "Along R0's 2,808 >= 1 km strike-consistent traces, vertex spacings of 566-750 m leave "
            "triangular-kernel saddle blind spots (k(d)=0 at 300 m), while range-front fault tips "
            "step beneath young fan alluvium just past R0's thinning cutoff. Inserting relocated "
            "dots at internal gap midpoints first and 320 m/640 m collinear tip steps second "
            "strictly preserves R0's 2.8284 px spacing floor and > 300 m catalogue clearance, "
            "raising T and M along coherent fault zones at fixed S = 37,654."
        ),
        "mimicking_non_fault_process": (
            "Resistant welded ash-flow tuff hogbacks, linear Miocene basalt flow margins, "
            "Pleistocene Lake Lahontan wave-cut shorelines (<1,360 m), and straight piedmont "
            "road/canal grades form multi-kilometre colinear ridges; bridging and extending them "
            "concentrates mass onto linear non-fault landforms."
        ),
        "predicted_live_change": "+0.0020 MODEL (band -0.0030..+0.0070; <0.01 Phase 1 floor; Phase 2 trace-completion arm)",
        "predicted_sign": "small positive (+0.0020 MODEL; primary Track B count-fixed hybrid candidate)",
        "falsifier": (
            "Live delta <= -0.010, or live delta worse than cull1dot on the identical singleton "
            "pool, falsifies >= 1 km trace bridging/tip-extension and shows relocated mass walked "
            "onto linear volcanic/shoreline/erosional mimics."
        ),
        "form_note_template": "R0 TRACKB bridge1km: move {removed} 1-dot speckles to >=1km trace gaps/tips; S=37654",
    },
    "rendertop120": {
        "title": "TRACKB / rendertop120 — continuous 100 m polyline rasterisation of top-120 GeoJSON traces",
        "slot_candidate": False,
        "hypothesis": (
            "Rasterising the top-120 multi-physics-corroborated >= 1 km GeoJSON geologist traces as "
            "unbroken 8-connected 100 m polylines (+1,518 Bresenham connector pixels funded 1-for-1 "
            "by removing 1,518 weakest isolated singletons; 8.063% of R0 changed, S = 37,654) "
            "delivers unmistakable continuous fault traces for Phase 2 expert review while keeping "
            "the Phase 1 DTI sub-kernel overlap tax inside +/-0.005."
        ),
        "mechanism": (
            "Under NLR-RULES, ONE blind final GeoTIFF is scored in both Phase 1 (automated DTI) and "
            "Phase 2 (expert geologist trace review + expanded reference labels). Pure trace-only "
            "rasters fail Phase 1 recall, whereas d=2.83 px dot chains appear discontinuous at 100 m "
            "pixel scale. Continuous Bresenham rendering on only the top-120 >= 1 km traces (4.03% "
            "of R0's mass budget) synchronises the raster pixel-for-pixel with the GeoJSON geologist "
            "dossier while preserving 96.0% of R0's kernel-spaced background coverage."
        ),
        "mimicking_non_fault_process": (
            "Adjacent 100 m pixels along rendered traces share 67-83% of their R=300 m triangular "
            "kernel discs (deliberate Phase 1 overlap tax), and any strike-parallel volcanic dike, "
            "tuff cliff, or pluvial shoreline inside the top-120 receives 2.2x denser unit mass "
            "per km than background R0 chains."
        ),
        "predicted_live_change": "-0.0005 MODEL (band -0.0050..+0.0030; Phase 1 neutral, Phase 2 geologist-legibility arm)",
        "predicted_sign": "Phase 1 neutral / slight overlap tax (-0.0005 MODEL; Phase 2 review arm)",
        "falsifier": (
            "Phase 1 live delta <= -0.010 falsifies continuous 100 m trace rendering even at a 4% "
            "mass budget; Phase 2 geologist audit rejecting > 50% of the 120 GeoJSON traces as "
            "volcanic flow margins, hogbacks, or pluvial shorelines falsifies the ranking composite."
        ),
        "form_note_template": "R0 TRACKB rendertop120: render 120 >=1km GeoJSON traces continuously (-{removed} 1-dot); S=37654",
    },
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_all_inputs() -> dict[str, Any]:
    """Verify SHA-256 of every required manifest input, base raster, and template pin."""
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in manifest["files"]}
    verified: dict[str, Any] = {}

    for fid in REQUIRED_MANIFEST_IDS:
        entry = by_id[fid]
        p_name = Path(entry["path"]).name
        candidates = [
            ROOT / entry["path"],
            CACHE / entry["path"],
            CACHE / "scored" / p_name,
            CACHE / "external" / p_name,
        ]
        if entry.get("local_cache_relpath"):
            candidates.append(ROOT / entry["local_cache_relpath"])
        if fid == "scored_h33_2_b2_zeros":
            candidates.append(ROOT / PARENT_REL)
        found = next((p for p in candidates if p.is_file()), None)
        if found is None:
            raise FileNotFoundError(
                f"Missing pinned input {fid} ({entry['path']}); run scripts/restore_axis_inputs.py first."
            )
        actual = _sha256(found)
        if actual != entry["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch on {fid}: expected {entry['sha256']}, got {actual}")
        verified[fid] = {
            "path": str(found.relative_to(ROOT)),
            "bytes": found.stat().st_size,
            "sha256": actual,
            "status": "VERIFIED",
        }

    base_path = ROOT / BASE_REL
    base_sha = _sha256(base_path)
    if base_sha != BASE_SHA256:
        raise RuntimeError(f"SHA-256 mismatch on R0 base {BASE_REL}: expected {BASE_SHA256}, got {base_sha}")
    verified["r0_unpruned_base_d28"] = {
        "path": BASE_REL,
        "bytes": base_path.stat().st_size,
        "sha256": base_sha,
        "status": "VERIFIED",
    }

    tpin = json.loads((ROOT / "research" / "template_pin.json").read_text(encoding="utf-8"))
    tpin_checked = 0
    for rel, expected in tpin["files"].items():
        p = ROOT / rel if (ROOT / rel).is_file() else ROOT / "vendor" / "template66" / rel.removeprefix("vendor/")
        if not p.is_file() or _sha256(p) != expected:
            raise RuntimeError(f"Template pin mismatch on {rel}")
        tpin_checked += 1
    verified["template66_pinned_files"] = {"count": tpin_checked, "status": "VERIFIED"}
    return verified


def rebuild_and_verify_r0(ctx: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    """Rebuild R0 from pinned base + catalogue (d > 2.0 px) and assert byte-exact SHA-256 match."""
    foot = ctx["footprint"]
    cat = ctx["catalogue"]
    shape = ctx["grid"]["shape"]

    base_path = ROOT / BASE_REL
    parent_path = ROOT / PARENT_REL
    with rasterio.open(base_path) as src:
        base_raw = src.read(1)
    base_dots = foot & np.isfinite(base_raw) & (base_raw > 0.5)
    edt_cat = ndi.distance_transform_edt(~cat)
    rebuilt_dots = base_dots & (edt_cat > 2.0)

    with rasterio.open(parent_path) as src:
        p_raw = src.read(1)
        crs, transform = src.crs, src.transform
    stored_dots = foot & np.isfinite(p_raw) & (p_raw > 0.5)
    if not np.array_equal(rebuilt_dots, stored_dots):
        raise RuntimeError("STOP: Rebuilt R0 dot mask does not match stored R0 dot mask.")

    # Re-encode with the documented R0 writer profile in memory for byte-for-byte SHA-256 check
    prof = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "compress": "deflate",
        "predictor": 3,
        "zlevel": 9,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "interleave": "band",
        "nodata": None,
        "height": shape[0],
        "width": shape[1],
        "crs": crs,
        "transform": transform,
    }
    arr = np.where(foot, rebuilt_dots, 0.0).astype(np.float32)
    with MemoryFile() as mem:
        with mem.open(**prof) as dst:
            dst.write(arr, 1)
        rebuilt_bytes = mem.read()
    rebuilt_sha = hashlib.sha256(rebuilt_bytes).hexdigest()
    disk_sha = _sha256(parent_path)
    if disk_sha != PARENT_SHA256 or rebuilt_sha != PARENT_SHA256:
        raise RuntimeError(
            f"STOP: R0 byte-exact rebuild gate failed (rebuilt={rebuilt_sha}, disk={disk_sha}, "
            f"expected={PARENT_SHA256})."
        )
    return rebuilt_dots, {
        "parent_id": PARENT_ID,
        "parent_path": PARENT_REL,
        "base_dots": int(base_dots.sum()),
        "pruned_le2px": int((base_dots & ~rebuilt_dots).sum()),
        "r0_dots": int(rebuilt_dots.sum()),
        "rebuilt_bytes": len(rebuilt_bytes),
        "stored_bytes": parent_path.stat().st_size,
        "rebuilt_sha256": rebuilt_sha,
        "expected_sha256": PARENT_SHA256,
        "byte_exact_match": True,
        "dot8": grid_io.dot8(rebuilt_dots),
    }


def load_trackb_external_pack(footprint: np.ndarray) -> dict[str, Any]:
    """Load verified USGS GeoDAWN, 3DEP 10 m, fluvial chi/ksn, SGMC, TIGER, and H19-5 rasters."""
    bd = axis_bands.load_bands()
    with rasterio.open(CACHE / "scored" /
                       "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as src:
        h19_raw = src.read(1)
    h19_mask = footprint & np.isfinite(h19_raw) & (h19_raw > 0.5)

    topo_extra: dict[str, np.ndarray] = {}
    with rasterio.open(CACHE / "external" / "topo_10m_derived_100m_u8.tif") as src:
        descs = list(src.descriptions)
        for want in ("relief_local", "aspect_coherence", "dem_mean"):
            b_idx = descs.index(want) + 1
            raw = src.read(b_idx)
            tags = src.tags(b_idx)
            lo, hi = float(tags["q_lo"]), float(tags["q_hi"])
            arr = np.full(raw.shape, np.nan, dtype=np.float32)
            valid = raw > 0
            arr[valid] = lo + (raw[valid].astype(np.float32) - 1.0) * ((hi - lo) / 254.0)
            topo_extra[want] = arr

    with rasterio.open(CACHE / "external" / "dem10_chi_100m_i16.tif") as src:
        descs_c = list(src.descriptions)
        ksn_raw = src.read(descs_c.index("ksn_max_m0.9") + 1)
        z_raw = src.read(descs_c.index("zmean_m") + 1)
        ksn = np.where(ksn_raw == -32768, np.nan, ksn_raw.astype(np.float32))
        zmean_m = np.where(z_raw == -32768, np.nan, z_raw.astype(np.float32))

    with rasterio.open(CACHE / "external" / "geodawn_rad_u8.tif") as src:
        rad_k_u8 = src.read(1)
    with rasterio.open(CACHE / "external" / "geodawn_extensions_u8.tif") as src:
        thk_u8 = src.read(1)
    with rasterio.open(CACHE / "external" / "tiger_road_distance_m.tif") as src:
        road_dist_m = src.read(1).astype(np.float32)
    with rasterio.open(CACHE / "external" / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc_u8 = src.read(1)

    return {
        "tmi_up150": bd["tmi_up150"],
        "scarp": bd["scarp"],
        "topo_extra": topo_extra,
        "h19_mask": h19_mask,
        "ksn_m09": ksn,
        "zmean_m": zmean_m,
        "rad_k_u8": rad_k_u8,
        "thk_u8": thk_u8,
        "road_dist_m": road_dist_m,
        "sgmc_mask": footprint & (sgmc_u8 > 0),
    }


def _known_ledger_hashes_excluding_self() -> set[str]:
    hashes: set[str] = set()
    csv_path = ROOT / "ledger" / "submissions.csv"
    if not csv_path.is_file():
        return hashes
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("axis") == "TRACKB" and row.get("value") in PREREGISTERED_CARDS:
                continue
            sha = (row.get("sha256") or "").strip().lower()
            if len(sha) == 64:
                hashes.add(sha)
    return hashes


def _new_mass_gate(disk_dots: np.ndarray, parent: np.ndarray, cat: np.ndarray, clearance_px: float = 3.0) -> dict[str, Any]:
    """Brief section 4.4 on newly emitted cells re-read from disk (IR-86-RELIEF-02)."""
    edt = ndi.distance_transform_edt(~cat)
    new = disk_dots & ~parent
    passed = bool(
        (new & cat).sum() == 0
        and ((edt[new] > clearance_px - 1e-9).all() if new.any() else True)
    )
    return {
        "gate": "new_mass_clearance",
        "passed": passed,
        "n_new": int(new.sum()),
        "on_catalogue": int((new & cat).sum()),
        "min_cat_distance_px": round(float(edt[new].min()), 4) if new.any() else None,
        "required_px": clearance_px,
    }


def _sgmc_surrogate_suite(
    variants_dots: dict[str, np.ndarray],
    r0_dots: np.ndarray,
    sgmc_mask: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
) -> dict[str, Any]:
    """Report-only off-catalogue USGS SGMC surrogate (house RELIEF/SPACING convention + >3 px check)."""
    truth_off = sgmc_mask & footprint & ~catalogue
    edt_cat = ndi.distance_transform_edt(~catalogue)
    truth_gt3 = sgmc_mask & footprint & (edt_cat > 3.0)

    h, w = footprint.shape
    rmid, cmid = h // 2, w // 2
    quads = {
        "NW": (slice(0, rmid), slice(0, cmid)),
        "NE": (slice(0, rmid), slice(cmid, w)),
        "SW": (slice(rmid, h), slice(0, cmid)),
        "SE": (slice(rmid, h), slice(cmid, w)),
    }
    rng = np.random.default_rng(SEED)
    shifts = [(0, 0)] + [tuple(int(v) for v in rng.integers(-6, 7, 2)) for _ in range(11)]

    def _eval_mask(dmask: np.ndarray) -> dict[str, Any]:
        full = tb.dti_algebra_terms(dmask.astype(np.float32), truth_off, valid=footprint, known=catalogue)
        gt3 = metric.dti_binary(dmask, truth_gt3, valid=footprint, known=catalogue)
        q_out: dict[str, float] = {}
        for qn, (rs, cs) in quads.items():
            qr = metric.dti_binary(dmask[rs, cs], truth_off[rs, cs],
                                   valid=footprint[rs, cs], known=catalogue[rs, cs])
            q_out[qn] = round(float(qr["dti"]), 6)
        sh_vals: list[float] = []
        for dy, dx in shifts:
            rolled = np.roll(np.roll(truth_off, dy, axis=0), dx, axis=1) & footprint & ~catalogue
            sr = metric.dti_binary(dmask, rolled, valid=footprint, known=catalogue)
            sh_vals.append(float(sr["dti"]))
        return {
            "dti": round(full["dti_metric"], 6),
            "dti_gt3px_collar": round(float(gt3["dti"]), 6),
            "T": round(full["T"], 2),
            "S": int(round(full["S"])),
            "M": round(full["M"], 2),
            "FP_w": round(full["F"], 2),
            "n_truth_px": int(round(full["G"])),
            "quadrant_dti": q_out,
            "shift_pm6px_mean_dti": round(float(np.mean(sh_vals)), 6),
            "shift_pm6px_min_dti": round(float(np.min(sh_vals)), 6),
            "shift_pm6px_max_dti": round(float(np.max(sh_vals)), 6),
        }

    r0_res = _eval_mask(r0_dots)
    out: dict[str, Any] = {
        "evidence_class": "MODEL",
        "note": ("Report-only independent USGS SGMC 1:500k mapped-fault surrogate off the competition "
                 "catalogue (known=catalogue); NOT a competition score and never a gate."),
        "source_url": "https://pubs.usgs.gov/ds/1052/",
        "r0": r0_res,
        "arms": {},
    }
    for name, dmask in variants_dots.items():
        res = _eval_mask(dmask)
        res["delta_vs_r0"] = round(res["dti"] - r0_res["dti"], 6)
        res["delta_gt3px_vs_r0"] = round(res["dti_gt3px_collar"] - r0_res["dti_gt3px_collar"], 6)
        res["delta_shift_pm6px_mean_vs_r0"] = round(
            res["shift_pm6px_mean_dti"] - r0_res["shift_pm6px_mean_dti"], 6
        )
        res["quadrants_beating_r0"] = int(sum(
            1 for qn in quads if res["quadrant_dti"][qn] > r0_res["quadrant_dti"][qn]
        ))
        out["arms"][name] = res
    return out


def _catalogue_proxy_suite(
    variants_dots: dict[str, np.ndarray],
    r0_dots: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
) -> dict[str, Any]:
    """Official shared whole-component buffered 4-fold catalogue hide-and-recover PROXY (report-only)."""
    folds = instrument.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    terms_by_arm: dict[str, np.ndarray] = {"r0": instrument.terms(r0_dots.astype(np.float32), folds)}
    for k, v in variants_dots.items():
        terms_by_arm[k] = instrument.terms(v.astype(np.float32), folds)

    pooled = instrument.summarize(terms_by_arm, candidate="bridge1km")
    scores_clean = {
        arm: {
            "evidence_class": "PROXY",
            "pooled_proxy_dti": round(float(pooled["scores"][arm]["dti"]), 6),
            "bootstrap_95ci": [round(float(x), 6) for x in pooled["scores"][arm]["ci95"]],
            "n_withheld_catalogue_positives": int(pooled["scores"][arm]["withheld_positive_pixels"]),
            "tpw": round(float(pooled["scores"][arm]["tpw"]), 2),
            "fpw": round(float(pooled["scores"][arm]["fpw"]), 2),
        }
        for arm in terms_by_arm
    }
    return {
        "evidence_class": "PROXY",
        "status": "REPORT-ONLY (never a gate)",
        "evaluator_version": pooled["evaluator_version"],
        "clusters_20km": pooled["bootstrap"]["clusters"],
        "folds": [
            {"fold": f.name, "withheld_positive_pixels": int(f.truth.sum())}
            for f in folds
        ],
        "warning": (
            "Catalogue hide-and-recover PROXY sits near the ~0.00436 floor across all R0 descendants "
            "because R0 already zeroes all mass within <=2 px of the full catalogue (IR-86-PRUNE-03, "
            "IR-86-SPACING-05). Reported with n withheld positives and 95% CI; never called a score."
        ),
        "r0": scores_clean["r0"],
        "variants": {k: scores_clean[k] for k in variants_dots},
    }


def _leakage_canary_suite(
    features: dict[str, np.ndarray],
    variants_dots: dict[str, np.ndarray],
    footprint: np.ndarray,
    catalogue: np.ndarray,
    sgmc_mask: np.ndarray,
) -> dict[str, Any]:
    """Single-feature ROC AUC leakage canary (brief section 6: stop and investigate if AUC > 0.90)."""
    edt_cat = ndi.distance_transform_edt(~catalogue)
    off_mask = footprint & (edt_cat > 3.0)
    y_cat = catalogue[footprint].astype(np.uint8)
    y_sgmc = sgmc_mask[off_mask].astype(np.uint8)

    # Subsample 250k deterministic pixels for exact, fast ROC AUC across 5.17M cells
    idx_foot = np.linspace(0, int(footprint.sum()) - 1, 250_000, dtype=int)
    idx_off = np.linspace(0, int(off_mask.sum()) - 1, 250_000, dtype=int)

    rows: list[dict[str, Any]] = []
    all_surfaces: list[tuple[str, np.ndarray]] = list(features.items())
    for name, dmask in variants_dots.items():
        all_surfaces.append((f"neg_dist_to_{name}", -ndi.distance_transform_edt(~dmask).astype(np.float32)))

    for fname, surf in all_surfaces:
        s_foot = surf[footprint][idx_foot]
        yc = y_cat[idx_foot]
        fin_c = np.isfinite(s_foot)
        auc_c = float(roc_auc_score(yc[fin_c], s_foot[fin_c])) if fin_c.sum() > 100 and 0 < yc[fin_c].sum() < fin_c.sum() else 0.5
        auc_c_sym = max(auc_c, 1.0 - auc_c)

        s_off = surf[off_mask][idx_off]
        ys = y_sgmc[idx_off]
        fin_s = np.isfinite(s_off)
        auc_s = float(roc_auc_score(ys[fin_s], s_off[fin_s])) if fin_s.sum() > 100 and 0 < ys[fin_s].sum() < fin_s.sum() else 0.5
        auc_s_sym = max(auc_s, 1.0 - auc_s)

        rows.append({
            "feature": fname,
            "auc_vs_catalogue_raw": round(auc_c, 4),
            "auc_vs_catalogue_symmetric": round(auc_c_sym, 4),
            "auc_vs_sgmc_off_cat_raw": round(auc_s, 4),
            "auc_vs_sgmc_off_cat_symmetric": round(auc_s_sym, 4),
        })

    max_cat = max(r["auc_vs_catalogue_symmetric"] for r in rows)
    max_sgmc = max(r["auc_vs_sgmc_off_cat_symmetric"] for r in rows)
    stop = bool(max_cat > 0.90 or max_sgmc > 0.90)
    return {
        "threshold": 0.90,
        "max_symmetric_auc_vs_catalogue": round(max_cat, 4),
        "max_symmetric_auc_vs_sgmc_off_catalogue": round(max_sgmc, 4),
        "stop": stop,
        "features": rows,
    }


def _write_geologist_dossier(
    geojson_fc: dict[str, Any],
    trace_stats: dict[str, Any],
    built_records: dict[str, dict[str, Any]],
    sgmc_suite: dict[str, Any],
    proxy_suite: dict[str, Any],
    canary: dict[str, Any],
) -> None:
    """Write ``evidence/trackb-geologist-dossier.md``: mechanism cards + 120 trace paragraphs."""
    lines: list[str] = [
        "# TRACKB (Phase 2) — Mechanism Cards & Structural-Geologist Trace Dossier (`2026-10-23`)",
        "",
        "- **Parent:** `R0 = h33-h33-2-b2` (`37,654` unit-mass dots, `> 2.0 px` off catalogue, `0.2778` `CLAIM`, sha256 `c55bafc4...b6fa9` reproduced byte-for-byte).",
        "- **Axis:** `TRACKB` — Phase 2 expert-geologist fault-trace synthesis (`>= 1.0 km` strike-consistent traces from R0's dots, exported as GeoJSON + 3 controlled R0 raster variants). **Not a weekly Phase 1 slot candidate unless the human decides.**",
        f"- **Full R0 `>= 1.0 km` trace inventory:** `{trace_stats['n_traces']}` non-branching strike-consistent polylines linking `{trace_stats['n_dots_in_traces']}` R0 dots (mean `{trace_stats['mean_length_km']:.2f} km`, max `{trace_stats['max_length_km']:.2f} km`, minimum catalogue clearance `{trace_stats['min_cat_edt_px_all_traces'] * 100:.0f} m > 300 m`).",
        f"- **Geologist review set (`{GEOJSON_OUT.relative_to(ROOT)}`, local/gitignored per `IR-86-TRACKB-04`):** Top `{len(geojson_fc['features'])}` multi-physics-corroborated traces (`CRS84` lon/lat + native `EPSG:32611` UTM metadata), rendered as unbroken 100 m polylines in `rendertop120`.",
        "- **Evidence discipline:** Every surrogate number below is `MODEL` or `PROXY` — **never** a live competition score.",
        "",
        "---",
        "",
        "## Part 1 — Pre-Registered Structural-Geologist Mechanism Cards",
        "",
    ]

    for idx, val in enumerate(("cull1dot", "bridge1km", "rendertop120"), start=1):
        card = PREREGISTERED_CARDS[val]
        rec = built_records[val]
        sg = sgmc_suite["arms"][val]
        pr = proxy_suite["variants"][val]
        lines.extend([
            f"### {idx}. `{card['title']}`",
            "",
            f"- **Primary file (NaN outside):** `{rec['nan_path']}` (`{rec['nan_bytes']:,}` B, sha256 `{rec['nan_sha256'][:16]}…`)",
            f"- **Fallback file (`-zeros`):** `{rec['zeros_path']}` (`{rec['zeros_bytes']:,}` B, sha256 `{rec['zeros_sha256'][:16]}…`)",
            f"- **Parent diff vs R0:** `{rec['diff']['n_dots_variant']:,}` dots (`-{rec['diff']['removed']:,} / +{rec['diff']['added']:,}`, **`{rec['diff']['pct_changed']:.4f}%` of R0 changed**), weekly-slot candidate: **`False` (Phase 2 / Track B)**.",
            f"- **Hypothesis:** {card['hypothesis']}",
            f"- **Mechanism:** {card['mechanism']}",
            f"- **Mimicking non-fault process:** {card['mimicking_non_fault_process']}",
            f"- **Pre-registered live prediction:** **{card['predicted_live_change']}**.",
            f"- **Post-build report-only readouts (never gates):** SGMC off-catalogue `MODEL` DTI `{sg['dti']:.6f}` (`Δ = {sg['delta_vs_r0']:+.6f}` vs R0 `{sgmc_suite['r0']['dti']:.6f}`; `>3 px` collar `Δ = {sg['delta_gt3px_vs_r0']:+.6f}`; `±6 px` shift mean `Δ = {sg['delta_shift_pm6px_mean_vs_r0']:+.6f}`; `{sg['quadrants_beating_r0']}/4` quadrants > R0); 4-fold buffered-component catalogue `PROXY` `{pr['pooled_proxy_dti']:.6f}` (95% CI `[{pr['bootstrap_95ci'][0]:.6f}, {pr['bootstrap_95ci'][1]:.6f}]`, `n = {pr['n_withheld_catalogue_positives']:,}`).",
            f"- **Falsifier:** {card['falsifier']}",
            "",
        ])

    ctrl = sgmc_suite["arms"]["control_random1dot"]
    pure = sgmc_suite["arms"]["diagnostic_pure_top120_only"]
    lines.extend([
        "### Diagnostic Controls (in-memory only; not emitted as submission rasters)",
        "",
        f"- **`control_random1dot` (null relocation control):** Relocating the exact same `{built_records['bridge1km']['diff']['removed']:,}` isolated singletons to uniform random eligible (`> 3 px` off-catalogue, `>= 2.83 px` spaced) footprint cells yields SGMC `MODEL` `Δ = {ctrl['delta_vs_r0']:+.6f}` (`{ctrl['dti']:.6f}` vs `bridge1km`'s `{sgmc_suite['arms']['bridge1km']['delta_vs_r0']:+.6f}`), isolating true along-strike fault bridging from random de-clustering.",
        f"- **`diagnostic_pure_top120_only` (why pure trace-only rasters are NOT viable under `NLR-RULES`):** Emitting *only* the `{pure['S']:,}` pixels of the top-120 `>= 1 km` traces (changing `96.31%` of R0, outside brief §5's `1–50%` invariant) collapses SGMC `MODEL` DTI from `{sgmc_suite['r0']['dti']:.6f}` to `{pure['dti']:.6f}` (`Δ = {pure['delta_vs_r0']:+.6f}`) because DTI weights recall `4:1` (`β = 0.8` vs `α = 0.2`) and `NLR-RULES` scores a **single** blind final GeoTIFF across both Phase 1 and Phase 2 (`IR-86-TRACKB-06`).",
        f"- **Leakage canary (`AUC <= 0.90`):** Max symmetric `AUC` across all `{len(canary['features'])}` single features + variant distance fields is `{canary['max_symmetric_auc_vs_catalogue']:.4f}` against `existing_faults` and `{canary['max_symmetric_auc_vs_sgmc_off_catalogue']:.4f}` against off-catalogue SGMC (`stop = {canary['stop']}`).",
        "",
        "---",
        "",
        f"## Part 2 — Per-Trace Structural-Geologist Evidence Paragraphs (`Top {len(geojson_fc['features'])}` Traces)",
        "",
        f"Every trace below corresponds 1-for-1 to its `Feature` in `{GEOJSON_OUT.relative_to(ROOT)}` and is continuously rasterised in `rendertop120`.",
        "",
    ])

    for feat in geojson_fc["features"]:
        p = feat["properties"]
        lines.append(
            f"1. **`{p['trace_id']}` (`{p['arc_length_km']:.2f} km`, `{p['quadrant']}`, `{p['strike_label']}`):** "
            f"{p['evidence_paragraph']}"
        )
    lines.append("")
    DOSSIER_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    print("[1/7] Verifying SHA-256 of all pinned manifest inputs and template66 tools ...")
    verified_inputs = verify_all_inputs()

    print("[2/7] Rebuilding parent R0 (h33-h33-2-b2) and checking byte-exact SHA-256 ...")
    ctx = grid_io.load_context()
    foot = ctx["footprint"]
    cat = ctx["catalogue"]
    shape = ctx["grid"]["shape"]
    r0_dots, r0_rebuild = rebuild_and_verify_r0(ctx)
    print(f"      R0 verified: {r0_rebuild['r0_dots']:,} dots, {r0_rebuild['rebuilt_bytes']:,} B, sha256={r0_rebuild['rebuilt_sha256'][:16]}...")

    print("[3/7] Extracting label-free >= 1.0 km strike-consistent traces from R0 along H19-5 ...")
    ext_pack = load_trackb_external_pack(foot)
    ev_pack = tb.build_evidence_surface(ext_pack["tmi_up150"], ext_pack["scarp"], foot, agc_window_px=50)
    traces, trace_stats = tb.extract_strike_traces(
        r0_dots,
        foot,
        cat,
        support_mask=ext_pack["h19_mask"],
        evidence_field=ev_pack["composite"],
    )
    print(f"      Extracted {trace_stats['n_traces']:,} traces >= 1.0 km ({trace_stats['n_dots_in_traces']:,} R0 dots, max {trace_stats['max_length_km']:.2f} km).")

    print("[4/7] Building 3 controlled TRACKB variants of R0 (cull1dot, bridge1km, rendertop120) ...")
    cull_dots, cull_stats = tb.build_cull_singletons(r0_dots, foot, cat)
    bridge_dots, bridge_stats = tb.build_bridge_traces(
        r0_dots, foot, cat, traces, ev_pack["composite"],
        support_mask=ext_pack["h19_mask"],
    )
    render_dots, render_stats = tb.build_render_top_traces(
        r0_dots, foot, cat, traces, ev_pack["composite"],
        top_k=TOP_K_DOSSIER,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    known_hashes = _known_ledger_hashes_excluding_self()
    built_records: dict[str, dict[str, Any]] = {}

    for value, v_dots, v_stats in (
        ("cull1dot", cull_dots, cull_stats),
        ("bridge1km", bridge_dots, bridge_stats),
        ("rendertop120", render_dots, render_stats),
    ):
        d8 = grid_io.dot8(v_dots)
        variant_id = f"{PARENT_PREFIX}-trackb-{value}-{DATE}-{d8}"
        form_note = PREREGISTERED_CARDS[value]["form_note_template"].format(
            removed=v_stats["removed"], added=v_stats["added"]
        )
        assert len(form_note) <= 140, f"form_note exceeds 140 chars: {len(form_note)}"

        pair = grid_io.write_pair(v_dots, ctx, OUT_DIR, variant_id, name=variant_id, note=form_note)
        nan_path = Path(pair["nan"]["path"])
        zeros_path = Path(pair["zeros"]["path"])
        nan_sha = pair["nan"]["sha256"]
        zeros_sha = pair["zeros"]["sha256"]

        # Re-read BOTH written GeoTIFFs from disk and run ALL MUST-pass gates
        gate_nan = gates.run_all(nan_path, ctx, known_hashes, clearance_px=grid_io.PARENT_CAT_CLEARANCE_PX)
        gate_zeros = gates.run_all(zeros_path, ctx, known_hashes, clearance_px=grid_io.PARENT_CAT_CLEARANCE_PX)
        disk_nan_dots = grid_io.load_dots(nan_path, foot)
        disk_zeros_dots = grid_io.load_dots(zeros_path, foot)
        new_gate_nan = _new_mass_gate(disk_nan_dots, r0_dots, cat, clearance_px=3.0)
        new_gate_zeros = _new_mass_gate(disk_zeros_dots, r0_dots, cat, clearance_px=3.0)

        pct = float(v_stats["pct_changed"])
        pct_in_1_50 = 1.0 <= pct <= 50.0
        twins_identical = bool(np.array_equal(disk_nan_dots, disk_zeros_dots))
        disk_matches_memory = bool(np.array_equal(v_dots, disk_zeros_dots))
        outside_nan_ok = gate_nan["values"]["mode"] == "nan"
        outside_zeros_ok = gate_zeros["values"]["mode"] == "zeros"

        if not (gate_nan["passed"] and gate_zeros["passed"]
                and new_gate_nan["passed"] and new_gate_zeros["passed"]
                and pct_in_1_50 and twins_identical and disk_matches_memory
                and outside_nan_ok and outside_zeros_ok):
            raise RuntimeError(
                f"MUST-pass gate failure on {variant_id}: nan={gate_nan['passed']}, "
                f"zeros={gate_zeros['passed']}, new_nan={new_gate_nan['passed']}, "
                f"pct={pct}, twins={twins_identical}"
            )
        known_hashes.add(zeros_sha)
        known_hashes.add(nan_sha)

        receipt_payload = {
            "variant_id": variant_id,
            "parent": PARENT_ID,
            "parent_sha256": PARENT_SHA256,
            "axis": "TRACKB",
            "value": value,
            "date": DATE,
            "dot8": d8,
            "slot_candidate": False,
            "form_note": form_note,
            "nan_path": str(nan_path.relative_to(ROOT)),
            "nan_sha256": nan_sha,
            "nan_bytes": nan_path.stat().st_size,
            "zeros_path": str(zeros_path.relative_to(ROOT)),
            "zeros_sha256": zeros_sha,
            "zeros_bytes": zeros_path.stat().st_size,
            "diff": v_stats,
            "gates_nan": {**gate_nan, "new_mass_clearance": new_gate_nan},
            "gates_zeros": {**gate_zeros, "new_mass_clearance": new_gate_zeros},
            "pct_changed_in_1_to_50": pct_in_1_50,
            "twins_identical_on_footprint": twins_identical,
            "disk_reread_matches_memory": disk_matches_memory,
        }
        (OUT_DIR / f"{variant_id}-zeros.json").write_text(
            json.dumps(receipt_payload, indent=2) + "\n", encoding="utf-8"
        )
        built_records[value] = receipt_payload
        print(f"      PASS {variant_id}: dots={v_stats['n_dots_variant']:,}, pct_changed={pct:.4f}%, dot8={d8}, zeros_sha8={zeros_sha[:8]}")

    print("[5/7] Writing RFC 7946 GeoJSON trace collection for geologist review ...")
    geojson_fc = tb.annotate_traces_for_geologist(
        traces[:TOP_K_DOSSIER],
        ctx["grid"]["transform"],
        foot,
        cat,
        ev_pack,
        ext_pack["scarp"],
        ext_pack["zmean_m"],
        ext_pack["ksn_m09"],
        ext_pack["rad_k_u8"],
        ext_pack["thk_u8"],
        ext_pack["road_dist_m"],
        rendered_variant_id=built_records["rendertop120"]["variant_id"],
    )
    GEOJSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    GEOJSON_OUT.write_text(json.dumps(geojson_fc, indent=2) + "\n", encoding="utf-8")

    print("[6/7] Running report-only instruments (SGMC control, 4-fold PROXY, leakage canary) ...")
    ctrl_dots, ctrl_stats = tb.build_random_singleton_control(
        r0_dots, foot, cat, ev_pack["composite"],
        n_relocate=bridge_stats["removed"],
    )
    pure_top120 = np.zeros_like(r0_dots)
    for tr in traces[:TOP_K_DOSSIER]:
        px = tr["pixels_rc"]
        pure_top120[px[:, 0], px[:, 1]] = True

    sgmc_suite = _sgmc_surrogate_suite(
        {
            "cull1dot": cull_dots,
            "bridge1km": bridge_dots,
            "rendertop120": render_dots,
            "control_random1dot": ctrl_dots,
            "diagnostic_pure_top120_only": pure_top120,
        },
        r0_dots,
        ext_pack["sgmc_mask"],
        foot,
        cat,
    )
    proxy_suite = _catalogue_proxy_suite(
        {"cull1dot": cull_dots, "bridge1km": bridge_dots, "rendertop120": render_dots},
        r0_dots,
        foot,
        cat,
    )

    canary_features = {
        "TMI_up150": ext_pack["tmi_up150"],
        "tmi_raw_grad": ev_pack["tmi_raw_grad"],
        "tmi_agc_grad": ev_pack["tmi_agc_grad"],
        "scarp_composite_z": ev_pack["z_scarp"],
        "curv_prof_absmax": ext_pack["scarp"]["curv_prof_absmax"],
        "slope_max": ext_pack["scarp"]["slope_max"],
        "hs_lineament": ext_pack["scarp"]["hs_lineament"],
        "relief_local": ext_pack["topo_extra"]["relief_local"],
        "aspect_coherence": ext_pack["topo_extra"]["aspect_coherence"],
        "dem_mean": ext_pack["topo_extra"]["dem_mean"],
        "ksn_max_m0.9": ext_pack["ksn_m09"],
        "rad_K_rank": np.where(ext_pack["rad_k_u8"] > 0, ext_pack["rad_k_u8"].astype(np.float32), np.nan),
        "ext_ThK_rank": np.where(ext_pack["thk_u8"] > 0, ext_pack["thk_u8"].astype(np.float32), np.nan),
        "tiger_road_distance_m": ext_pack["road_dist_m"],
        "trackb_multi_physics_composite": ev_pack["composite"],
    }
    canary = _leakage_canary_suite(
        canary_features,
        {"cull1dot": cull_dots, "bridge1km": bridge_dots, "rendertop120": render_dots},
        foot,
        cat,
        ext_pack["sgmc_mask"],
    )
    if canary["stop"]:
        raise RuntimeError(f"STOP: Single-feature leakage canary exceeded 0.90! {canary}")

    print("[7/7] Writing geologist dossier and session evidence receipt ...")
    _write_geologist_dossier(geojson_fc, trace_stats, built_records, sgmc_suite, proxy_suite, canary)

    card_json = {
        "session_date": "2026-10-23",
        "axis": "TRACKB",
        "axis_selection_rationale": (
            "Unassigned by user prompt; self-assigned TRACKB because ledger/submissions.csv already "
            "contains R0 variants on PRUNE, RELIEF, MASS, SNAP, CONCENTRATION, and SPACING, leaving "
            "TRACKB as the sole brief-section-5 axis with zero built variants in the ledger."
        ),
        "phase_note": "Phase 2 / Track B geologist trace synthesis; slot_candidate=false on all 3 variants unless human decides.",
        "verified_inputs": verified_inputs,
        "r0_rebuild": r0_rebuild,
        "trace_inventory": {
            **trace_stats,
            "dossier_top_k": TOP_K_DOSSIER,
            "geojson_path": str(GEOJSON_OUT.relative_to(ROOT)),
            "geojson_sha256": _sha256(GEOJSON_OUT),
            "dossier_markdown_path": str(DOSSIER_OUT.relative_to(ROOT)),
            "quadrant_counts_all_traces": {
                q: int(sum(1 for t in traces if (
                    ("NW" if t["pixels_rc"][:, 0].mean() < shape[0] / 2 and t["pixels_rc"][:, 1].mean() < shape[1] / 2 else
                     "NE" if t["pixels_rc"][:, 0].mean() < shape[0] / 2 else
                     "SW" if t["pixels_rc"][:, 1].mean() < shape[1] / 2 else "SE") == q
                )))
                for q in ("NW", "NE", "SW", "SE")
            },
            "quadrant_counts_top120": {
                q: int(sum(1 for f in geojson_fc["features"] if f["properties"]["quadrant"] == q))
                for q in ("NW", "NE", "SW", "SE")
            },
        },
        "preregistered_mechanism_cards": PREREGISTERED_CARDS,
        "variants": built_records,
        "controls_in_memory": {
            "control_random1dot": ctrl_stats,
            "diagnostic_pure_top120_only": {
                "n_pixels": int(pure_top120.sum()),
                "pct_of_r0_changed": round(100.0 * int((r0_dots ^ pure_top120).sum()) / int(r0_dots.sum()), 4),
            },
        },
        "report_only_instruments": {
            "sgmc_off_catalogue_model": sgmc_suite,
            "catalogue_hide_and_recover_proxy": proxy_suite,
            "leakage_canary": canary,
        },
    }
    CARD_OUT.write_text(json.dumps(card_json, indent=2) + "\n", encoding="utf-8")
    print(f"Done: wrote {GEOJSON_OUT.relative_to(ROOT)}, {DOSSIER_OUT.relative_to(ROOT)}, and {CARD_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
