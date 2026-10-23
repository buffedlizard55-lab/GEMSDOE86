#!/usr/bin/env python3
"""Restore the hash-pinned inputs this AXIS session needs, into ``.cache/gems_data``.

Everything fetched here is listed in ``registry/data_manifest.json`` with a SHA-256 pin;
a digest mismatch aborts and the partial file is deleted.  Provenance stays exactly what
the manifest says: owner-published mirrors of DrivenData/USGS products, NOT organiser
authenticated bytes.  The competition data tab itself is never contacted.

Only two host families are used: ``api.github.com`` (through ``gh api``) and, for the
tarball fallback, ``codeload.github.com``.

Usage::

    .venv/bin/python scripts/restore_axis_inputs.py --ids ext_geodawn_extensions_json ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"
DEST_ROOT = ROOT / ".cache" / "gems_data"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _blob_sha(repo: str, ref: str, remote: str) -> str:
    """Resolve a path to its immutable Git blob SHA via the contents metadata endpoint."""
    out = subprocess.run(["gh", "api", f"repos/{repo}/contents/{remote}?ref={ref}",
                          "--jq", ".sha"], capture_output=True, check=True)
    return out.stdout.decode().strip()


def _stream_blob(repo: str, blob: str, tmp: Path) -> None:
    """Stream raw blob bytes.  The token is read from ``gh`` and never printed or stored."""
    token = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           check=True).stdout.decode().strip()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/git/blobs/{blob}",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github.raw",
                 "User-Agent": "gems86-axis-restore"})
    with urllib.request.urlopen(req, timeout=1800) as resp, tmp.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def fetch(entry: dict, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    repo, ref, remote = entry["repo"], entry["ref"], entry["path"]
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        _stream_blob(repo, _blob_sha(repo, ref, remote), tmp)
        got = sha256_file(tmp)
        if got != entry["sha256"]:
            raise SystemExit(f"SHA-256 MISMATCH {entry['id']}: {got} != {entry['sha256']}")
        if tmp.stat().st_size != entry["bytes"]:
            raise SystemExit(f"SIZE MISMATCH {entry['id']}: {tmp.stat().st_size} != {entry['bytes']}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return {"id": entry["id"], "sha256": got, "bytes": dest.stat().st_size,
            "repo": repo, "ref": ref, "remote_path": remote, "dest": str(dest.relative_to(ROOT))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="+", required=True)
    ap.add_argument("--receipt", default=".cache/axis_input_receipt.json")
    a = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    by_id = {f["id"]: f for f in manifest["files"]}
    receipts = []
    for ident in a.ids:
        if ident not in by_id:
            raise SystemExit(f"{ident} is not pinned in registry/data_manifest.json")
        entry = by_id[ident]
        dest = DEST_ROOT / entry["dest"]
        if dest.is_file() and sha256_file(dest) == entry["sha256"]:
            receipts.append({"id": ident, "sha256": entry["sha256"], "bytes": entry["bytes"],
                             "status": "already-present-verified"})
            print(f"  = {ident} verified in place", flush=True)
            continue
        receipts.append({**fetch(entry, dest), "status": "fetched-verified"})
        print(f"  + {ident} {entry['bytes']} bytes verified", flush=True)
    out = ROOT / a.receipt
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"evidence_class": "DATA-MEASUREMENT",
                               "pin_source": "registry/data_manifest.json",
                               "organizer_authenticated": False,
                               "files": receipts}, indent=2) + "\n")
    print(json.dumps({"status": "OK", "n": len(receipts), "receipt": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
