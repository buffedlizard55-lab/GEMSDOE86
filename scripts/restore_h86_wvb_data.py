#!/usr/bin/env python3
"""Fetch and SHA-256 verify official external public-domain layers + sibling registry rasters for GEMSDOE86.

Provenance:
- Base 7 external layers come directly from `research/upstream/data_manifest.json`
  (`buffedlizard55-lab/GEMSDOE24@07345ea0604953d7efb858d9cfbc21e20c7aca0b`: USGS GeoDAWN
  doi:10.5066/P93LGLVQ, USGS 3DEP 1 m LiDAR, USGS SGMC, and DOE GDR #1391 doi:10.15121/1881483).
- 3 supplemental official public-domain layers come from `buffedlizard55-lab/60GEMSDOE`
  (`b99591eede63c6d45c8a896255b8cd34824fa00b`): seamless USGS 3DEP 10 m DEM morphometrics
  (`topo_10m_derived_100m_u8.tif`), DOE GDR #1391 INGENIOUS paleo-geothermal sinter/travertine
  inventory (`paleo_geothermal_regional.zip`), and INGENIOUS slip-sense segments
  (`trace_segments_utm11.csv`, strictly masked to fold-visible pixels).
- `--include-siblings` verifies/restores the 30 deduplicated sibling champion `.tif` rasters
  pinned in `research/sibling_champions_manifest.json` into `data/scored_ext/` for extended
  cross-repo uniqueness auditing.

Data Integrity Guard:
- `derived_sgmc_faults_100m_u8.tif` is used ONLY as a read-only post-hoc off-catalogue structural
  diagnostic (`SGMC \\ INGENIOUS`) and NEVER enters any feature vector or model fit.
- `dist_known_fault_px` in GDR CSV tables is label-derived and NEVER enters any feature vector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = ROOT / "research" / "upstream" / "data_manifest.json"
SIBLING_MANIFEST = ROOT / "research" / "sibling_champions_manifest.json"

SUPPLEMENTAL_EXTERNAL = [
    {
        "id": "ext_topo_10m_derived_100m_u8",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "b99591eede63c6d45c8a896255b8cd34824fa00b",
        "remote_path": "data/external/topo_10m_derived_100m_u8.tif",
        "dest": "external/topo_10m_derived_100m_u8.tif",
        "bytes": 32523329,
        "sha256": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
        "provenance": "USGS 3DEP 1/3 arc-second (~10 m) seamless DEM sub-100m morphometric stack (9 bands; public domain)",
    },
    {
        "id": "ext_paleo_geothermal_regional",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "b99591eede63c6d45c8a896255b8cd34824fa00b",
        "remote_path": "data/external/paleo_geothermal_regional.zip",
        "dest": "external/paleo_geothermal_regional.zip",
        "bytes": 84008,
        "sha256": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
        "provenance": "DOE GDR #1391 INGENIOUS Paleo_geothermal_final.csv (DOI 10.15121/1881483, CC BY 4.0; sinter/travertine/tufa)",
    },
    {
        "id": "ext_trace_segments_utm11",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "ref": "b99591eede63c6d45c8a896255b8cd34824fa00b",
        "remote_path": "data/external/trace_segments_utm11.csv",
        "dest": "external/trace_segments_utm11.csv",
        "bytes": 5283577,
        "sha256": "c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513",
        "provenance": "DOE GDR #1391 INGENIOUS fault trace slip-sense segments (strictly masked to fold-visible pixels)",
    },
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_one(repo: str, ref: str, remote_path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    endpoint = f"repos/{repo}/contents/{remote_path}?ref={ref}"
    with tmp.open("wb") as out:
        proc = subprocess.run(
            ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
            stdout=out,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"gh api failed for {endpoint}: {proc.stderr.decode(errors='replace').strip()}")
    tmp.replace(dest)


def restore_items(items: list[dict], data_root: Path) -> tuple[list[dict], list[dict]]:
    verified: list[dict] = []
    mismatches: list[dict] = []
    for item in items:
        dest = data_root / item["dest"]
        remote_path = item.get("remote_path") or item["path"]
        if not (dest.exists() and dest.stat().st_size == item["bytes"] and _sha256(dest) == item["sha256"]):
            _fetch_one(item["repo"], item["ref"], remote_path, dest)
        actual_sha = _sha256(dest)
        actual_bytes = dest.stat().st_size
        ok = (actual_sha == item["sha256"]) and (actual_bytes == item["bytes"])
        rec = {
            "dest": item["dest"],
            "repo": item["repo"],
            "ref": item["ref"],
            "remote_path": remote_path,
            "bytes": item["bytes"],
            "sha256": item["sha256"],
            "actual_bytes": actual_bytes,
            "actual_sha256": actual_sha,
            "ok": ok,
        }
        verified.append(rec)
        if not ok:
            mismatches.append(rec)
    return verified, mismatches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=ROOT / "data")
    ap.add_argument("--include-siblings", action="store_true", help="Also verify/restore research/sibling_champions_manifest.json")
    ap.add_argument("--receipt", type=Path, default=ROOT / "docs" / "evidence" / "h86_wvb_data_restore.json")
    args = ap.parse_args(argv)

    t0 = time.time()
    base_ext = [x for x in json.loads(BASE_MANIFEST.read_text())["files"] if x["group"] == "external"]
    ext_verified, ext_bad = restore_items(base_ext + SUPPLEMENTAL_EXTERNAL, args.data_root)
    sib_verified: list[dict] = []
    sib_bad: list[dict] = []
    if args.include_siblings and SIBLING_MANIFEST.exists():
        sib_items = json.loads(SIBLING_MANIFEST.read_text())["files"]
        sib_verified, sib_bad = restore_items(sib_items, args.data_root)

    all_bad = ext_bad + sib_bad
    receipt = {
        "restored_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 2),
        "external_files": len(ext_verified),
        "sibling_champion_files": len(sib_verified),
        "mismatch_count": len(all_bad),
        "files": ext_verified,
        "sibling_files": sib_verified,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("external_files", "sibling_champion_files", "mismatch_count", "elapsed_s")}, indent=2))
    return 0 if not all_bad else 2


if __name__ == "__main__":
    sys.exit(main())
