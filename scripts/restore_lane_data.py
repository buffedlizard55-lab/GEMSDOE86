#!/usr/bin/env python3
"""Restore and SHA-256-verify all GEMSDOE86 lane inputs + cross-repo registry rasters.

Restores:
  1. Core + baseline external + 12 baseline registry rasters from `research/upstream/data_manifest.json`
  2. Extended official public-domain / CC-BY-4.0 layers (USGS 3DEP 1 m LiDAR, 10 m DEM curvature &
     fluvial chi, DOE GDR 1391 2m shallow temperature probes, paleo-geothermal sinter/tufa,
     well/spring geothermometry, volcanic vents, GeoDAWN acquisition blocks) and 25 cross-repo
     GEMSDOE sibling submission rasters from `research/h86_extended_manifest.json`.

Every file is verified against its pinned byte length and SHA-256 digest before use.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = ROOT / "research" / "upstream" / "data_manifest.json"
EXT_MANIFEST = ROOT / "research" / "h86_extended_manifest.json"
DATA_DIR = ROOT / "data"
RECEIPT_PATH = ROOT / "docs" / "evidence" / "lane_data_restore.json"

BASE_REQUIRED_IDS = {
    "core_training_features",
    "core_existing_faults",
    "core_sample_submission",
    "ext_geodawn_rad_u8",
    "ext_geodawn_ext_u8",
    "ext_sgmc_faults_u8",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_token() -> str:
    proc = subprocess.run(
        ["gh", "auth", "token"],
        check=True,
        capture_output=True,
        text=True,
    )
    tok = proc.stdout.strip()
    if not tok:
        raise RuntimeError("`gh auth token` returned empty token.")
    return tok


def fetch_entry(entry: dict, dest: Path, token: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    url = entry.get("raw_url")
    if url:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {token}",
                "User-Agent": "GEMSDOE86-lane-restore",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as resp, tmp.open("wb") as out:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
    else:
        parts = entry.get("parts", [entry.get("path")])
        with tmp.open("wb") as out:
            for part in parts:
                api = f"repos/{entry['repo']}/contents/{part}?ref={entry['ref']}"
                subprocess.run(
                    ["gh", "api", api, "-H", "Accept: application/vnd.github.raw+json"],
                    check=True,
                    stdout=out,
                )

    actual_bytes = tmp.stat().st_size
    actual_sha = sha256_file(tmp)
    if actual_bytes != entry["bytes"] or actual_sha != entry["sha256"]:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Integrity mismatch for {entry['id']}: "
            f"bytes {actual_bytes}!={entry['bytes']} or sha256 {actual_sha}!={entry['sha256']}"
        )
    tmp.replace(dest)


def collect_entries(include_fleet: bool = True) -> list[dict]:
    base = json.loads(BASE_MANIFEST.read_text())["files"]
    seen_dest: set[str] = set()
    selected: list[dict] = []
    for e in base:
        if e["dest"] not in seen_dest:
            seen_dest.add(e["dest"])
            selected.append(e)
    if EXT_MANIFEST.exists():
        ext_doc = json.loads(EXT_MANIFEST.read_text())
        for e in ext_doc.get("external_files", []):
            if e["dest"] not in seen_dest:
                seen_dest.add(e["dest"])
                selected.append(e)
        if include_fleet:
            for e in ext_doc.get("fleet_registry_files", []):
                if e["dest"] not in seen_dest:
                    seen_dest.add(e["dest"])
                    selected.append(e)
    return selected


def main(include_fleet: bool = True) -> int:
    selected = collect_entries(include_fleet=include_fleet)
    token: str | None = None
    records = []
    for entry in selected:
        dest = DATA_DIR / entry["dest"]
        status = "cached_verified"
        if not dest.exists() or dest.stat().st_size != entry["bytes"] or sha256_file(dest) != entry["sha256"]:
            if token is None:
                token = gh_token()
            print(f"[fetch] {entry['id']} -> {entry['dest']} ({entry['bytes']:,} B)")
            fetch_entry(entry, dest, token)
            status = "downloaded_verified"
        else:
            print(f"[ok]    {entry['id']} ({entry['sha256'][:12]})")
        records.append(
            {
                "id": entry["id"],
                "group": entry["group"],
                "dest": entry["dest"],
                "repo": entry["repo"],
                "ref": entry["ref"],
                "bytes": entry["bytes"],
                "sha256": entry["sha256"],
                "status": status,
            }
        )

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "base_manifest_sha256": sha256_file(BASE_MANIFEST),
                "extended_manifest_sha256": sha256_file(EXT_MANIFEST) if EXT_MANIFEST.exists() else None,
                "restored_count": len(records),
                "files": records,
                "provenance_warning": (
                    "Upstream blobs are restored from commit-pinned public/sibling mirrors and verified "
                    "against SHA-256 digests. Mirror hash verification proves byte reproducibility, "
                    "not DrivenData organizer authentication."
                ),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Verified {len(records)} SHA-256-pinned files; receipt at {RECEIPT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
