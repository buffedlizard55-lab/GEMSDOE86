"""Lane 86 / 86B complete data-restoration & SHA-256 verifier.

Restores and SHA-256-verifies:
  1. All 22 non-qfaults competition, GDR-1391, external-proxy, and scored baseline
     files declared in `research/upstream/data_manifest.json` (`gdr_qfaults_traces`
     is deliberately skipped unless `--include-qfaults` is requested, preventing
     accidental full-catalogue trace leakage).
  2. All 15 cross-repository primary submission GeoTIFFs declared in
     `research/upstream/cross_repo_champions_manifest.json` into `data/registry_ext/`,
     streaming `codeload.github.com` tarballs first (1 request per repo, zero GitHub
     REST API quota) with `gh api` fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_MANIFEST = ROOT / "research" / "upstream" / "data_manifest.json"
EXT_MANIFEST = ROOT / "research" / "upstream" / "cross_repo_champions_manifest.json"

LANE86B_REQUIRED = (
    "existing_faults.tif",
    "labels.tif",
    "sample_submission.tif",
    "training_features.tif",
    "external/lidar_scarp_features_u8.tif",
    "external/geodawn_rad_u8.tif",
    "external/geodawn_extensions_u8.tif",
    "external/gdr_wellspring_in_footprint.csv",
    "external/gdr_volcanic_vents_in_footprint.csv",
    "external/derived_sgmc_faults_100m_u8.tif",
    "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _restore_core_manifest(data_dir: Path, verify_only: bool = False) -> list[dict]:
    entries = json.loads(CORE_MANIFEST.read_text())["files"]
    out = []
    for item in entries:
        if item["id"] == "ext_gdr_qfaults_traces":
            continue
        dest = data_dir / item["dest"]
        if dest.is_file() and dest.stat().st_size == item["bytes"] and _sha256(dest) == item["sha256"]:
            out.append(dict(id=item["id"], dest=item["dest"], status="cached_ok", sha256=item["sha256"]))
            continue
        if verify_only:
            out.append(dict(id=item["id"], dest=item["dest"], status="missing_or_mismatch"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".partial")
        try:
            with tmp.open("wb") as fh:
                for part in item.get("parts", [item.get("path")]):
                    subprocess.run(
                        [
                            "gh",
                            "api",
                            f"repos/{item['repo']}/contents/{part}?ref={item['ref']}",
                            "-H",
                            "Accept: application/vnd.github.raw+json",
                        ],
                        stdout=fh,
                        check=True,
                    )
            got = _sha256(tmp)
            if got != item["sha256"] or tmp.stat().st_size != item["bytes"]:
                raise RuntimeError(f"SHA-256/size mismatch for {item['id']}: got {got}")
            tmp.replace(dest)
            out.append(dict(id=item["id"], dest=item["dest"], status="downloaded", sha256=got))
        finally:
            tmp.unlink(missing_ok=True)
    return out


def _restore_cross_repo_registry(data_dir: Path, verify_only: bool = False) -> list[dict]:
    if not EXT_MANIFEST.is_file():
        return []
    entries = json.loads(EXT_MANIFEST.read_text())["files"]
    by_repo: dict[str, list[dict]] = {}
    results: list[dict] = []

    for e in entries:
        dest = data_dir / e["dest"]
        if dest.is_file() and dest.stat().st_size == e["bytes"] and _sha256(dest) == e["sha256"]:
            results.append(dict(id=e["id"], dest=e["dest"], status="cached_ok", sha256=e["sha256"]))
        elif verify_only:
            results.append(dict(id=e["id"], dest=e["dest"], status="missing_or_mismatch"))
        else:
            by_repo.setdefault(e["repo"], []).append(e)

    for repo, needed in by_repo.items():
        url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/main"
        want = {e["path"]: e for e in needed}
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                raw = resp.read()
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
                for member in tf.getmembers():
                    slash = member.name.find("/")
                    rel = member.name[slash + 1 :] if slash >= 0 else member.name
                    if rel in want:
                        e = want.pop(rel)
                        fobj = tf.extractfile(member)
                        if fobj is None:
                            continue
                        payload = fobj.read()
                        got_sha = hashlib.sha256(payload).hexdigest()
                        if got_sha != e["sha256"]:
                            raise RuntimeError(f"SHA-256 mismatch on {e['id']}: {got_sha} != {e['sha256']}")
                        dest = data_dir / e["dest"]
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(payload)
                        results.append(dict(id=e["id"], dest=e["dest"], status="downloaded_codeload", sha256=got_sha))
        except Exception:
            pass

        for e in want.values():
            dest = data_dir / e["dest"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                ["gh", "api", f"repos/{e['repo']}/contents/{e['path']}", "-H", "Accept: application/vnd.github.raw+json"],
                capture_output=True,
                check=True,
            )
            got_sha = hashlib.sha256(proc.stdout).hexdigest()
            if got_sha != e["sha256"]:
                raise RuntimeError(f"SHA-256 mismatch on {e['id']}: {got_sha} != {e['sha256']}")
            dest.write_bytes(proc.stdout)
            results.append(dict(id=e["id"], dest=e["dest"], status="downloaded_gh_api", sha256=got_sha))

    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--skip-ext-registry", action="store_true")
    ap.add_argument("--json-out", type=Path, default=ROOT / "docs" / "evidence" / "lane_data_restore.json")
    args = ap.parse_args(argv)

    core_rows = _restore_core_manifest(args.data_dir, verify_only=args.verify_only)
    ext_rows = [] if args.skip_ext_registry else _restore_cross_repo_registry(args.data_dir, verify_only=args.verify_only)

    core_bad = [r["id"] for r in core_rows if r["status"] == "missing_or_mismatch"]
    ext_bad = [r["id"] for r in ext_rows if r["status"] == "missing_or_mismatch"]
    missing_req = [rel for rel in LANE86B_REQUIRED if not (args.data_dir / rel).is_file()]

    report = dict(
        lane="H86B-GFCO",
        manifest="research/upstream/data_manifest.json",
        cross_repo_manifest="research/upstream/cross_repo_champions_manifest.json",
        core_verified=len(core_rows) - len(core_bad),
        core_total=len(core_rows),
        cross_repo_verified=len(ext_rows) - len(ext_bad),
        cross_repo_total=len(ext_rows),
        required_present=len(LANE86B_REQUIRED) - len(missing_req),
        required_total=len(LANE86B_REQUIRED),
        missing_required=missing_req,
        core_mismatches=core_bad,
        ext_mismatches=ext_bad,
        qfaults_excluded_by_default=True,
        ok=(len(core_bad) == 0 and len(ext_bad) == 0 and len(missing_req) == 0),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
