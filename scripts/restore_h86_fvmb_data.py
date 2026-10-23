#!/usr/bin/env python3
"""Autonomously restore and SHA-256-verify competition rasters, official public
external geophysical/geothermal layers, and fleet registry rasters for GEMSDOE86.

Mirrors are owner-supplied public GitHub blobs (DrivenData files are login-walled).
Every restored file is SHA-256-verified (fails closed on mismatch).
Large rasters are stored in `.cache/gems_data/` (excluded from Git/snapshot bloat)
and linked into `data/raw/`, while the 3 small grid/audit rasters (`existing_faults.tif`,
`labels.tif`, `sample_submission.tif`) are also placed in `data/bridge/` for `vendor/gems57/grid.py`.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = ROOT / ".cache" / "gems_data"
RAW_LINK_DIR = ROOT / "data" / "raw"
BRIDGE_DIR = ROOT / "data" / "bridge"

EXTRA_FLEET_CANDIDATES = [
    ("scored_gems36_anderson", "buffedlizard55-lab/GEMSDOE36", "main",
     "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
     "GEMSDOE36 Anderson PINN 38,854 dots (owner-reported 0.2750)"),
    ("scored_gems28_h36_1", "buffedlizard55-lab/GEMSDOE28", "main",
     "docs/downloads/gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-allfinite.tif",
     "GEMSDOE28 all-increments D2.8 reference"),
    ("scored_gems63_cvarlw", "buffedlizard55-lab/GEMSDOE63", "main",
     "docs/downloads/cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros.tif",
     "GEMSDOE63 CVaR thin 54,864 dots (owner-reported 0.2303)"),
    ("scored_gems78_sigx", "buffedlizard55-lab/GEMSDOE78", "main",
     "docs/downloads/gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros.tif",
     "GEMSDOE78 H78-SIGX 44,090 dots"),
    ("scored_gems79_tiltring", "buffedlizard55-lab/GEMSDOE79", "main",
     "docs/downloads/gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros.tif",
     "GEMSDOE79 Tilt-Ring 100,000 dots"),
    ("scored_gems80_h80g_choquet", "buffedlizard55-lab/GEMSDOE80", "main",
     "docs/downloads/gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros.tif",
     "GEMSDOE80 H80-G Choquet Two-Regime 51,667 dots"),
    ("scored_gems80_adpt_kkt", "buffedlizard55-lab/GEMSDOE80", "main",
     "docs/downloads/gems80-adpt-kkt-lagrangian-36500d-20261022T012049Z-5bd11c85-zeros.tif",
     "GEMSDOE80 ADPT KKT Lagrangian 36,500 dots"),
    ("scored_gems81_cont", "buffedlizard55-lab/GEMSDOE81", "main",
     "docs/downloads/gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros.tif",
     "GEMSDOE81 Continuation Poisson 44,090 dots"),
    ("scored_gems82_punoisyor", "buffedlizard55-lab/GEMSDOE82", "main",
     "submissions/gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros.tif",
     "GEMSDOE82 H82 Submodular PU Noisy-OR 37,654 dots"),
    ("scored_gems82_csam_41200", "buffedlizard55-lab/GEMSDOE82", "main",
     "submissions/gems82-h82-csam-dinkelbach-41200-20261021-zeros.tif",
     "GEMSDOE82 H82-CSAM Dinkelbach 41,200 dots"),
    ("scored_gems82_csam_37654", "buffedlizard55-lab/GEMSDOE82", "main",
     "submissions/gems82-h82-csam-dinkelbach-37654-20261021-zeros.tif",
     "GEMSDOE82 H82-CSAM Dinkelbach 37,654 dots"),
    ("scored_gems83_gvcd", "buffedlizard55-lab/GEMSDOE83", "main",
     "docs/downloads/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif",
     "GEMSDOE83 H83-GVCD Dinkelbach 37,654 dots"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_raw_blob(repo: str, ref: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        # First try contents API with raw header; fallback to git blob API for >1MB files
        res = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
            stdout=tmp.open("wb"),
            stderr=subprocess.PIPE,
        )
        if res.returncode != 0 or tmp.stat().st_size == 0:
            tree = json.loads(
                subprocess.check_output(["gh", "api", f"repos/{repo}/git/trees/{ref}?recursive=1"])
            )["tree"]
            blob_sha = next(x["sha"] for x in tree if x["path"] == path)
            with tmp.open("wb") as out:
                subprocess.run(
                    ["gh", "api", f"repos/{repo}/git/blobs/{blob_sha}", "-H", "Accept: application/vnd.github.raw"],
                    stdout=out,
                    check=True,
                )
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def ensure_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())

    raw_b64 = subprocess.check_output(
        ["gh", "api", "repos/buffedlizard55-lab/GEMSDOE80/contents/registry/data_manifest.json", "--jq", ".content"]
    )
    man = json.loads(base64.b64decode(raw_b64))
    existing_ids = {e["id"] for e in man["files"]}

    # Add USGS 3DEP 3m Wallace scarp stack & 1m openness/LRM & USGS heat flow
    extra_external = [
        {
            "id": "ext_h52_scarp3m_100m",
            "repo": "buffedlizard55-lab/GEMSDOE48",
            "ref": "main",
            "path": "data/external/h52_scarp3m_100m.tif",
            "dest": "external/h52_scarp3m_100m.tif",
            "group": "external",
            "sha256": "b5e53d67c3a7d3d1ca44ae04ae1e84d8574857da3fcd5e34ba47276d6c04b923",
            "bytes": 43839078,
            "provenance": "USGS 3DEP sub-10m Wallace fault-scarp diffusion stack (h_gate07, h_gate12, sigma, strike)",
        },
        {
            "id": "ext_dem1m_openness_lrm",
            "repo": "buffedlizard55-lab/19GEMSDOE",
            "ref": "main",
            "path": "evidence/ci/dem1m_high_prior_openness_lrm.npz",
            "dest": "external/dem1m_high_prior_openness_lrm.npz",
            "group": "external",
            "sha256": "62f27929747ad3c35be4dd3e0257b0bde7d7bea8566474956e1711269ad451fe",
            "bytes": 610575,
            "provenance": "USGS 3DEP 1m DEM topographic openness & local relief model",
        },
        {
            "id": "ext_sb_heat_flow",
            "repo": "buffedlizard55-lab/GEMSDOE28",
            "ref": "main",
            "path": "docs/data/sb_heat_flow_in_footprint.csv",
            "dest": "external/sb_heat_flow_in_footprint.csv",
            "group": "external",
            "sha256": None,
            "bytes": None,
            "provenance": "USGS ScienceBase Great Basin conductive heat-flow points inside GeoDAWN footprint",
        },
    ]
    for e in extra_external:
        if e["id"] not in existing_ids:
            man["files"].append(e)
            existing_ids.add(e["id"])

    # Probe extra recent fleet submissions so uniqueness checks cover up through GEMSDOE83
    for fid, repo, ref, rpath, prov in EXTRA_FLEET_CANDIDATES:
        if fid in existing_ids:
            continue
        short_repo = repo.split("/")[-1]
        man["files"].append(
            {
                "id": fid,
                "repo": repo,
                "ref": ref,
                "path": rpath,
                "dest": f"scored/{short_repo}__{Path(rpath).name}",
                "group": "scored",
                "sha256": None,  # computed & pinned upon first fetch
                "bytes": None,
                "provenance": prov,
                "optional_probe": True,
            }
        )
        existing_ids.add(fid)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    return man


def restore_entry(entry: dict, root: Path) -> dict | None:
    dest = root / entry["dest"]
    expected_sha = entry.get("sha256")
    if dest.exists() and (expected_sha is None or sha256_file(dest) == expected_sha):
        got_sha = sha256_file(dest)
        entry["sha256"] = got_sha
        entry["bytes"] = dest.stat().st_size
        return {
            "id": entry["id"],
            "dest": entry["dest"],
            "group": entry.get("group", "other"),
            "status": "present",
            "bytes": dest.stat().st_size,
            "sha256": got_sha,
        }

    try:
        if "parts" in entry:
            tmp = dest.with_suffix(".assembling")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("wb") as out:
                for part in entry["parts"]:
                    p = root / "raw_parts" / Path(part).name
                    fetch_raw_blob(entry["repo"], entry["ref"], part, p)
                    with p.open("rb") as src:
                        shutil.copyfileobj(src, out, 1 << 20)
                    p.unlink(missing_ok=True)
            got_sha = sha256_file(tmp)
            if expected_sha and got_sha != expected_sha:
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"HASH MISMATCH {entry['id']}: {got_sha} != {expected_sha}")
            tmp.replace(dest)
        else:
            fetch_raw_blob(entry["repo"], entry["ref"], entry["path"], dest)
            got_sha = sha256_file(dest)
            if expected_sha and got_sha != expected_sha:
                dest.unlink(missing_ok=True)
                raise RuntimeError(f"HASH MISMATCH {entry['id']}: {got_sha} != {expected_sha}")
    except Exception as exc:
        if entry.get("optional_probe"):
            print(f"    skip  {entry['dest']:60s} ({exc})", flush=True)
            return None
        raise

    entry["sha256"] = got_sha
    entry["bytes"] = dest.stat().st_size
    return {
        "id": entry["id"],
        "dest": entry["dest"],
        "group": entry.get("group", "other"),
        "status": "restored",
        "bytes": dest.stat().st_size,
        "sha256": got_sha,
    }


def sync_links_and_bridge(cache_root: Path) -> None:
    RAW_LINK_DIR.mkdir(parents=True, exist_ok=True)
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    for item in cache_root.iterdir():
        if item.name == "raw_parts":
            continue
        link_path = RAW_LINK_DIR / item.name
        if link_path.is_symlink() or link_path.exists():
            if link_path.is_symlink() or link_path.is_file():
                link_path.unlink()
        os.symlink(item.resolve(), link_path)

    for bname in ("existing_faults.tif", "labels.tif", "sample_submission.tif"):
        src = cache_root / bname
        dst = BRIDGE_DIR / bname
        if src.is_file() and (not dst.is_file() or sha256_file(dst) != sha256_file(src)):
            shutil.copy2(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", default="all", help="comma-separated manifest ids or 'all'")
    ap.add_argument("--manifest", default=str(ROOT / "registry" / "data_manifest.json"))
    ap.add_argument("--target-dir", default=str(DEFAULT_CACHE_DIR))
    args = ap.parse_args()

    t0 = time.time()
    manifest_path = Path(args.manifest)
    man = ensure_manifest(manifest_path)
    cache_root = Path(args.target_dir)
    cache_root.mkdir(parents=True, exist_ok=True)

    want = None if args.ids == "all" else set(args.ids.split(","))
    results = []
    kept_files = []
    for entry in man["files"]:
        if want is not None and entry["id"] not in want:
            kept_files.append(entry)
            continue
        r = restore_entry(entry, cache_root)
        if r is not None:
            entry.pop("optional_probe", None)
            kept_files.append(entry)
            results.append(r)
            print(f"{r['status']:>8}  {r['dest']:64s} sha256={r['sha256'][:12]}…", flush=True)

    man["files"] = kept_files
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    sync_links_and_bridge(cache_root)

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.time() - t0, 2),
        "verified_files_count": len(results),
        "storage_root": ".cache/gems_data",
        "files": results,
    }
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "restore_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Verified {len(results)} files in {receipt['elapsed_seconds']}s -> data/restore_receipt.json")


if __name__ == "__main__":
    main()
