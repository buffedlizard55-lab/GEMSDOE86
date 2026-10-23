"""Lane H86C-KSLB complete SHA-256 data-restoration & cross-fleet verifier.

Restores and SHA-256-verifies into `--data-dir` (default `.cache/gems86_data` so
large rasters never bloat Git commits or workspace snapshots):
  1. All 22 non-qfaults competition, GDR-1391, external-proxy, and scored baseline
     files declared in `research/upstream/data_manifest.json` (`gdr_qfaults_traces`
     excluded by default to prevent full-catalogue trace leakage).
  2. Both seamless USGS 3DEP 10 m morphological & fluvial-chi/ksn rasters
     (`topo_10m_derived_100m_u8.tif` and `dem10_chi_100m_i16.tif`) declared in
     `research/upstream/cross_repo_champions_ext88_manifest.json`.
  3. All 19 cross-repository primary submission GeoTIFFs across `GEMSDOE32..88`
     (`cross_repo_champions_manifest.json` + `cross_repo_champions_ext88_manifest.json`).
  4. The immutable 100%-support dense historical registry witness declared in
     `research/registry_witness_pin.json`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.restore_h86b_data import _restore_core_manifest, _restore_cross_repo_registry, _sha256
from scripts.restore_protocol_data import write_blob

EXT88_MANIFEST = ROOT / "research" / "upstream" / "cross_repo_champions_ext88_manifest.json"
WITNESS_PIN = ROOT / "research" / "registry_witness_pin.json"

DEFAULT_DATA_DIR = ROOT / ".cache" / "gems86_data"

LANE86C_REQUIRED = (
    "existing_faults.tif",
    "labels.tif",
    "sample_submission.tif",
    "training_features.tif",
    "external/lidar_scarp_features_u8.tif",
    "external/topo_10m_derived_100m_u8.tif",
    "external/dem10_chi_100m_i16.tif",
    "external/geodawn_rad_u8.tif",
    "external/geodawn_extensions_u8.tif",
    "external/gdr_wellspring_in_footprint.csv",
    "external/gdr_volcanic_vents_in_footprint.csv",
    "external/derived_sgmc_faults_100m_u8.tif",
    "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "registry/dense-witness.tif",
)


def _stream_extract(url: str, wanted: dict[str, Path]) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "gems86c-restore"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for m in tf:
                if not m.isfile():
                    continue
                rel = m.name.split("/", 1)[-1]
                if rel in wanted:
                    dst = wanted[rel]
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    fh = tf.extractfile(m)
                    if fh is not None:
                        with dst.open("wb") as out:
                            shutil.copyfileobj(fh, out)


def _restore_ext10m(data_dir: Path, verify_only: bool = False) -> list[dict]:
    items = json.loads(EXT88_MANIFEST.read_text())["external_10m"]
    rows = []
    need_by_ref: dict[tuple[str, str], dict[str, tuple[dict, Path]]] = {}
    for item in items:
        dest = data_dir / item["dest"]
        if dest.is_file() and dest.stat().st_size == item["bytes"] and _sha256(dest) == item["sha256"]:
            rows.append(dict(id=item["id"], dest=item["dest"], status="cached_ok", sha256=item["sha256"]))
        elif verify_only:
            rows.append(dict(id=item["id"], dest=item["dest"], status="missing_or_mismatch"))
        else:
            need_by_ref.setdefault((item["repo"], item["ref"]), {})[item["path"]] = (item, dest)

    for (repo, ref), mapping in need_by_ref.items():
        _stream_extract(
            f"https://codeload.github.com/{repo}/tar.gz/{ref}",
            {rel: dst for rel, (_, dst) in mapping.items()},
        )
        for item, dst in mapping.values():
            got = _sha256(dst) if dst.is_file() else ""
            if not dst.is_file() or dst.stat().st_size != item["bytes"] or got != item["sha256"]:
                raise RuntimeError(f"SHA-256/size mismatch for {item['id']}: got {got}")
            rows.append(dict(id=item["id"], dest=item["dest"], status="downloaded", sha256=got))
    return rows


def _restore_ext88_champions(data_dir: Path, verify_only: bool = False) -> list[dict]:
    import subprocess

    items = json.loads(EXT88_MANIFEST.read_text())["files"]
    rows = []
    for item in items:
        dest = data_dir / item["dest"]
        if dest.is_file() and dest.stat().st_size == item["bytes"] and _sha256(dest) == item["sha256"]:
            rows.append(dict(id=item["id"], dest=item["dest"], status="cached_ok", sha256=item["sha256"]))
            continue
        if verify_only:
            rows.append(dict(id=item["id"], dest=item["dest"], status="missing_or_mismatch"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["gh", "api", f"repos/{item['repo']}/contents/{item['path']}", "-H", "Accept: application/vnd.github.raw+json"],
            capture_output=True,
            check=True,
        )
        got = hashlib.sha256(proc.stdout).hexdigest()
        if got != item["sha256"] or len(proc.stdout) != item["bytes"]:
            raise RuntimeError(f"SHA-256/size mismatch on {item['id']}: {got}")
        dest.write_bytes(proc.stdout)
        rows.append(dict(id=item["id"], dest=item["dest"], status="downloaded_gh_api", sha256=got))
    return rows


def _restore_witness(data_dir: Path, verify_only: bool = False) -> dict:
    pin = json.loads(WITNESS_PIN.read_text())
    dest = data_dir / pin["dest"]
    if dest.is_file() and dest.stat().st_size == pin["bytes"] and _sha256(dest) == pin["sha256"]:
        return dict(id="dense_witness", dest=pin["dest"], status="cached_ok", sha256=pin["sha256"])
    if verify_only:
        return dict(id="dense_witness", dest=pin["dest"], status="missing_or_mismatch")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".partial")
    try:
        with tmp.open("wb") as stream:
            write_blob(pin["repo"], pin["blob"], stream)
        got = _sha256(tmp)
        if got != pin["sha256"] or tmp.stat().st_size != pin["bytes"]:
            raise RuntimeError(f"Witness SHA-256/size mismatch: {got}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dict(id="dense_witness", dest=pin["dest"], status="downloaded", sha256=pin["sha256"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--json-out", type=Path, default=ROOT / "docs" / "evidence" / "h86c_data_restore.json")
    args = ap.parse_args(argv)

    core_rows = _restore_core_manifest(args.data_dir, verify_only=args.verify_only)
    ext10m_rows = _restore_ext10m(args.data_dir, verify_only=args.verify_only)
    ext_rows = _restore_cross_repo_registry(args.data_dir, verify_only=args.verify_only)
    ext88_rows = _restore_ext88_champions(args.data_dir, verify_only=args.verify_only)
    wit_row = _restore_witness(args.data_dir, verify_only=args.verify_only)

    core_bad = [r["id"] for r in [*core_rows, *ext10m_rows] if r["status"] == "missing_or_mismatch"]
    ext_bad = [r["id"] for r in [*ext_rows, *ext88_rows] if r["status"] == "missing_or_mismatch"]
    wit_bad = [] if wit_row["status"] != "missing_or_mismatch" else ["dense_witness"]
    missing_req = [rel for rel in LANE86C_REQUIRED if not (args.data_dir / rel).is_file()]

    report = dict(
        lane="H86C-KSLB",
        manifests=[
            "research/upstream/data_manifest.json",
            "research/upstream/cross_repo_champions_manifest.json",
            "research/upstream/cross_repo_champions_ext88_manifest.json",
            "research/registry_witness_pin.json",
        ],
        core_and_10m_verified=len(core_rows) + len(ext10m_rows) - len(core_bad),
        core_and_10m_total=len(core_rows) + len(ext10m_rows),
        cross_repo_verified=len(ext_rows) + len(ext88_rows) - len(ext_bad),
        cross_repo_total=len(ext_rows) + len(ext88_rows),
        dense_witness_verified=(len(wit_bad) == 0),
        required_present=len(LANE86C_REQUIRED) - len(missing_req),
        required_total=len(LANE86C_REQUIRED),
        missing_required=missing_req,
        mismatches=core_bad + ext_bad + wit_bad,
        qfaults_excluded_by_default=True,
        ok=(len(core_bad) == 0 and len(ext_bad) == 0 and len(wit_bad) == 0 and len(missing_req) == 0),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
