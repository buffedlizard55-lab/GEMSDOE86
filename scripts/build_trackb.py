#!/usr/bin/env python3
"""GEMSDOE86 session, AXIS = TRACKB (self-assigned; the only unbuilt brief-5 axis).

1. Pins verified against registry/data_manifest.json before any read.
2. R0 rebuilt from the pinned base and required byte-exact (c55bafc4...), else stop.
3. Three trace sets differing ONLY in turning-angle ceiling (20/30/40 deg):
   strike-consistent chains >= 1 km from R0's dots (src/gems86/trackb.py).
   Each emits GeoJSON (the Phase-2 review object, one evidence paragraph per
   trace) + a raster pair (NaN/zeros twins) rendered under brief 4.4.
4. MUST gates re-read from disk; SGMC off-catalogue surrogate + leakage canary
   are REPORT-ONLY (MODEL / canary), never gates, never slot arguments.
TRACKB is Phase 2: no slot is used or requested.  Nothing submits, logs in,
scrapes, or contacts DrivenData/dropbox.
Usage: .venv/bin/python scripts/build_trackb.py
"""
from __future__ import annotations

import csv, hashlib, json, subprocess, sys, time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems57 import metric  # noqa: E402
from gems86 import trackb as TB  # noqa: E402
from gems86_axis import gates, grid_io  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

DATE_TAG = "20261023"
SEED = 20261023
PARENT_LABEL = "h33-h33-2-b2"
ARMS = {"s20": 20.0, "s30": 30.0, "s40": 40.0}   # value -> max turning angle (deg)
PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "sgmc": ROOT / ".cache/gems_data/external/derived_sgmc_faults_100m_u8.tif",
}
MANIFEST_IDS = {"parent": "scored_h33_2_b2_zeros", "catalogue": "existing_faults",
                "sample": "sample_submission", "sgmc": "ext_derived_sgmc_faults_100m_u8"}
LITERAL_PINS = {"parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
                "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"}


def sha256(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:
        return "unknown"


def verify_inputs() -> dict:
    man = {f["id"]: f for f in json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]}
    files = {}
    for name, path in PATHS.items():
        if not path.is_file():
            raise SystemExit(f"pinned input absent: {name} {path.relative_to(ROOT)} "
                             "(restore via scripts/restore_axis_inputs.py; never approximate)")
        got = sha256(path)
        exp = LITERAL_PINS.get(name) or (man[MANIFEST_IDS[name]]["sha256"] if name in MANIFEST_IDS else None)
        if exp and got != exp:
            raise SystemExit(f"PIN MISMATCH {name}: {got} != {exp}")
        files[name] = {"path": str(path.relative_to(ROOT)), "sha256": got,
                       "bytes": path.stat().st_size, "verified": bool(exp),
                       "organizer_authenticated": False}
    return {"files": files, "note": "GitHub mirrors integrity-pinned, NOT organizer-authenticated"}


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def rebuild_parent(foot, cat) -> dict:
    base = read(PATHS["base"])
    bm = (np.nan_to_num(base, nan=0.0) > 0) & foot
    rebuilt = bm & (ndi.distance_transform_edt(~cat) > 2.0)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    if int((rebuilt != parent).sum()):
        raise SystemExit("R0 REBUILD MISMATCH; stopping (brief 5)")
    out = ROOT / "tmp_session/rebuild_parent_zeros.tif"
    out.parent.mkdir(exist_ok=True)
    with rasterio.open(PATHS["parent"]) as src:
        crs, transform = src.crs, src.transform
    prof = dict(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                zlevel=9, tiled=True, blockxsize=256, blockysize=256, interleave="band",
                nodata=None, height=foot.shape[0], width=foot.shape[1], crs=crs, transform=transform)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(np.where(foot, rebuilt, 0.0).astype(np.float32), 1)
    digest = sha256(out)
    if digest != LITERAL_PINS["parent"]:
        raise SystemExit(f"R0 REBUILD NOT BYTE-EXACT: {digest}")
    return {"base_dots": int(bm.sum()), "rebuilt_dots": int(rebuilt.sum()),
            "differing_cells_vs_parent": 0, "rebuild_sha256": digest, "byte_exact": True,
            "recipe": "gems28-h27-4-r1-solo-d2-8 AND distance-to-catalogue > 2.0 px"}


def known_hashes() -> set[str]:
    out = set()
    led = ROOT / "ledger/submissions.csv"
    if led.is_file():
        with led.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    v = (row.get(col) or "").strip()
                    if len(v) == 64:
                        out.add(v)
    for f in (ROOT / "data/scored_fleet").glob("*.tif"):
        out.add(sha256(f))
    return out


def surrogate(parent, arms, foot, cat) -> dict:
    """Exact DTI vs SGMC off-catalogue faults (MODEL, report-only; RELIEF convention)."""
    sgmc = read(PATHS["sgmc"]) > 0
    off = sgmc & foot & ~cat

    def score(m):
        r = metric.dti_binary(m, off, valid=foot, known=cat)
        return {k: (round(float(r[k]), 6) if k in ("dti", "coverage") else float(r[k]))
                for k in ("dti", "tp", "fp", "fn", "coverage", "n_truth", "n_emitted")}
    base = score(parent)
    out = {"evidence_class": "MODEL", "truth_pixels": int(off.sum()), "parent": base, "arms": {}}
    for name, m in arms.items():
        c = score(m)
        out["arms"][name] = {"dti": c["dti"], "delta_vs_r0": round(c["dti"] - base["dti"], 6),
                             "delta_tp": round(c["tp"] - base["tp"], 2),
                             "delta_fp": round(c["fp"] - base["fp"], 2),
                             "n_emitted": c["n_emitted"]}
    out["note"] = ("trace rasters emit far fewer pixels than R0, so a negative delta is the "
                   "expected mass effect, not a verdict on the traces; TRACKB's product is the "
                   "GeoJSON for expert review (Phase 2), not a Phase-1 score")
    return out


def canary(arms, foot, cat) -> dict:
    from sklearn.metrics import roc_auc_score
    sgmc = read(PATHS["sgmc"]) > 0
    truth = sgmc & foot & ~cat
    rows = []
    for name, m in arms.items():
        vals = m.astype(float)[foot & ~cat]
        lab = truth[foot & ~cat]
        if lab.sum() and np.unique(vals).size > 1:
            rows.append({"arm": name, "feature": "is_trace_pixel",
                         "auc": round(float(roc_auc_score(lab, vals)), 4)})
    mx = max((r["auc"] for r in rows), default=0.0)
    return {"status": "PASS" if mx <= 0.90 else "STOP_INVESTIGATE", "threshold": 0.90,
            "max_auc": mx, "rows": rows}


def main() -> int:
    t0 = time.time()
    pins = verify_inputs()
    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]
    rebuild = rebuild_parent(foot, cat)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    points = TB.dot_points(parent)
    cat_edt = ndi.distance_transform_edt(~cat)
    with rasterio.open(PATHS["sample"]) as src:
        transform = src.transform
    print(f"[parent] {rebuild['rebuilt_dots']} dots BYTE-EXACT {rebuild['rebuild_sha256'][:12]}...", flush=True)

    known = known_hashes()
    cards, masks, geojson_paths = {}, {}, {}
    outdir = ROOT / "releases/trackb"
    for value, turn in ARMS.items():
        traces, st = TB.extract_traces(parent, turn)
        mask, rstats = TB.rasterize(traces, points, foot.shape, cat_edt, foot)
        masks[value] = mask
        # per-trace catalogue distance + GeoJSON (EPSG:32611 coordinates)
        feats = []
        for t in traces:
            pts = points[t["dot_indices"]]
            d = cat_edt[[int(r) for r in pts[:, 0]], [int(c) for c in pts[:, 1]]]
            dist = {"min": round(float(d.min()), 3), "median": round(float(np.median(d)), 3)}
            coords = [[float(transform.c + c * transform.a), float(transform.f + r * transform.e)]
                      for r, c in pts]
            feats.append({"type": "Feature",
                          "geometry": {"type": "LineString", "coordinates": coords},
                          "properties": {**t, "parent": PARENT_LABEL, "axis": "TRACKB",
                                         "value": value, "catalogue_distance_px": dist,
                                         "evidence": TB.evidence_paragraph(t, dist)}})
        token = dot8(mask)
        stem = f"h33-h33-2-b2-trackb{value}-{DATE_TAG}-{token}"
        gj = outdir / f"{stem}.geojson"
        gj.parent.mkdir(parents=True, exist_ok=True)
        gj.write_text(json.dumps({"type": "FeatureCollection", "crs": {
            "type": "name", "properties": {"name": "EPSG:32611"}},
            "properties": {"parent": PARENT_LABEL, "axis": "TRACKB", "value": value,
                           "max_turn_deg": turn, "min_length_km": 1.0, "seed": SEED,
                           "git_sha": git_sha()}, "features": feats}, indent=1) + "\n")
        geojson_paths[value] = gj
        note = (f"{PARENT_LABEL} TRACKB/{value}: {st['n_traces']} strike-consistent traces >=1km "
                f"(turn<={turn:.0f}deg) from R0 dots; Phase2 review, not a slot")[:140]
        pair = grid_io.write_pair(mask, ctx, outdir, stem, name=stem, note=note)
        g = {m: gates.run_all(pair[m]["path"], ctx, known, grid_io.PARENT_CAT_CLEARANCE_PX)
             for m in ("nan", "zeros")}
        for m in ("nan", "zeros"):
            known.add(pair[m]["sha256"])
        shared = int((mask & parent).sum())
        diff = {"parent_dots": int(parent.sum()), "variant_dots": int(mask.sum()),
                "shared_dots": shared, "dropped": int(parent.sum() - shared),
                "added": int(mask.sum() - shared),
                "pct_changed_of_parent": round(100.0 * (int(parent.sum() - shared) + int(mask.sum() - shared)) / int(parent.sum()), 4),
                "jaccard": round(shared / int((mask | parent).sum()), 6)}
        ok = all(g[m]["passed"] for m in g)
        cards[value] = {"id": stem, "axis": "TRACKB", "value": value, "token": token,
                        "role": "phase2_trace_product", "slot_candidate": False,
                        "parent": {"id": PARENT_LABEL, "sha256": LITERAL_PINS["parent"], "rebuild": rebuild},
                        "chain_stats": st, "raster_stats": rstats, "parent_diff": diff,
                        "gates": g, "artifacts": pair, "geojson": str(gj.relative_to(ROOT)),
                        "geojson_sha256": sha256(gj), "note": note, "git_sha": git_sha()}
        print(f"[{value}] traces={st['n_traces']} traced={st['n_traced_dots']} "
              f"({st['pct_parent_dots_traced']}%) raster_px={int(mask.sum())} gates={'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            raise SystemExit(f"gate failure {value}: {json.dumps(g)[:800]}")

    instr = {"sgmc_offcatalogue_surrogate": surrogate(parent, masks, foot, cat),
             "leakage_canary": canary(masks, foot, cat),
             "catalogue_hide_recover_proxy": {"status": "NOT_RUN",
                "reason": "trace rasters are Phase-2 renderings, not dot variants; the proxy is "
                          "documented collar-recovery for this lineage (IR-86-SNAP-06) and would rank nothing"}}
    for v in cards.values():
        v["predicted_change_model"] = instr["sgmc_offcatalogue_surrogate"]["arms"][
            v["value"]]["delta_vs_r0"]
        rp = Path(v["artifacts"]["zeros"]["path"]).with_suffix(".json")
        rec = json.loads(json.dumps(v, default=str)); rec["evidence_class"] = "MODEL"
        rp.write_text(json.dumps(rec, indent=2) + "\n")

    out = {"schema_version": 1, "session_axis": "TRACKB", "generated_utc":
           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git_sha": git_sha(),
           "seed": SEED, "elapsed_s": round(time.time() - t0, 1),
           "parent": {"id": PARENT_LABEL, "sha256": LITERAL_PINS["parent"],
                      "live_claim": "0.2778 CLAIM (no receipt in ledger/)", "rebuild": rebuild},
           "inputs_verified": pins,
           "constants": {"max_step_px": TB.MAX_STEP_PX, "min_length_px": TB.MIN_LENGTH_PX,
                         "min_dots": TB.MIN_DOTS, "new_mass_clearance_px": TB.NEW_MASS_CLEARANCE_PX,
                         "arms_deg": ARMS},
           "top_public": "UNSUPPLIED", "slots": "UNSUPPLIED; TRACKB requests no slot",
           "variants": cards, "instruments": instr,
           "evidence_labels": {"predicted_change": "MODEL", "traces": "MODEL (geometry only)"}}
    ev = ROOT / f"evidence/trackb_axis_{DATE_TAG}.json"
    ev.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"[out] {ev.relative_to(ROOT)} ({out['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
