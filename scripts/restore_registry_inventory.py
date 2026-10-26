#!/usr/bin/env python3
"""Restore the hash-pinned cross-repository registry for uniqueness audits.

The registry is comparison-only: its rasters are never prediction inputs.  The
inventory records immutable Git blob IDs, byte lengths, and SHA-256 digests.
This command downloads each missing blob into the ignored ``data/registry_ext/``
cache — attempting ``gh api`` first and automatically falling back to
zero-REST-quota ``codeload.github.com`` tarballs + shallow ``git cat-file blob``
when ``api.github.com`` is rate-limited — verifies byte count and SHA-256
digest before atomic placement, and writes a receipt.  An incomplete receipt is
never a uniqueness pass.

The public owner inventory is not an organizer registry and its bytes do not
authenticate the competition's private labels.  The distinction is deliberate.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research/upstream/registry_inventory.json"
DEFAULT_OUT = ROOT / "data/registry_ext"
DEFAULT_RECEIPT = ROOT / "docs/evidence/registry-inventory-restore.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _github_token() -> str | None:
    try:
        res = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        tok = res.stdout.strip()
        return tok or None
    except Exception:
        return None


def fetch_one_rest(record: dict, out_dir: Path, owner: str) -> dict:
    expected = record["sha256"]
    repo = f"{owner}/{record['repo_first']}"
    dest = out_dir / f"{expected}.tif"
    if dest.is_file():
        got = sha256(dest)
        if got == expected and dest.stat().st_size == record["bytes"]:
            return {"sha256": expected, "bytes": record["bytes"], "status": "cached_ok", "repo": repo}
        dest.unlink()
    partial = dest.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    endpoint = f"repos/{repo}/git/blobs/{record['blob']}"
    try:
        with partial.open("wb") as stream:
            subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
                stdout=stream,
                stderr=subprocess.PIPE,
                check=True,
                timeout=900,
            )
        got = sha256(partial)
        size = partial.stat().st_size
        if got != expected or size != record["bytes"]:
            raise RuntimeError(
                f"integrity mismatch {record['repo_first']}:{record['blob']}: "
                f"sha={got} bytes={size}; expected {expected}/{record['bytes']}"
            )
        partial.replace(dest)
        return {"sha256": expected, "bytes": size, "status": "downloaded_rest"}
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def restore_repo_codeload_and_git(
    repo_name: str,
    records: list[dict],
    out_dir: Path,
    owner: str,
    token: str | None,
) -> tuple[list[dict], list[dict]]:
    """Fallback that uses zero api.github.com REST quota via codeload + git pack."""
    restored: list[dict] = []
    still_missing: list[dict] = []
    by_relpath: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        prefix = f"{repo_name}:"
        matched = False
        for src in rec.get("sources", []):
            if src.startswith(prefix):
                by_relpath[src[len(prefix):]].append(rec)
                matched = True
        if not matched:
            still_missing.append(rec)

    headers = {"Authorization": f"token {token}"} if token else {}
    tar_url = f"https://codeload.github.com/{owner}/{repo_name}/tar.gz/HEAD"
    found_shas: set[str] = set()
    try:
        req = urllib.request.Request(tar_url, headers=headers)
        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp_tar:
            with urllib.request.urlopen(req, timeout=180) as resp:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    tmp_tar.write(chunk)
            tmp_tar.flush()
            with tarfile.open(tmp_tar.name, "r:gz") as tf:
                for member in tf.getmembers():
                    if not member.isfile() or "/" not in member.name:
                        continue
                    rel = member.name.split("/", 1)[1]
                    if rel not in by_relpath:
                        continue
                    fobj = tf.extractfile(member)
                    if fobj is None:
                        continue
                    data = fobj.read()
                    got = hashlib.sha256(data).hexdigest()
                    for rec in by_relpath[rel]:
                        if rec["sha256"] == got and len(data) == rec["bytes"] and got not in found_shas:
                            dest = out_dir / f"{got}.tif"
                            part = dest.with_suffix(".partial")
                            part.write_bytes(data)
                            part.replace(dest)
                            found_shas.add(got)
                            restored.append({
                                "sha256": got,
                                "bytes": len(data),
                                "status": "downloaded_codeload",
                                "repo": rec["repo_first"],
                                "blob": rec["blob"],
                                "sources": rec["sources"],
                            })
    except Exception:
        pass

    remaining = [r for r in records if r["sha256"] not in found_shas]
    if not remaining:
        return restored, []

    # Historical non-HEAD blobs: shallow git clone/fetch + git cat-file blob
    clone_errors: list[dict] = []
    with tempfile.TemporaryDirectory() as git_tmp:
        try:
            subprocess.run(
                ["git", "clone", "--bare", "--filter=blob:none",
                 f"https://github.com/{owner}/{repo_name}.git", git_tmp],
                capture_output=True,
                check=True,
                timeout=300,
            )
            for rec in remaining:
                expected = rec["sha256"]
                dest = out_dir / f"{expected}.tif"
                part = dest.with_suffix(".partial")
                try:
                    proc = subprocess.run(
                        ["git", "--git-dir", git_tmp, "cat-file", "blob", rec["blob"]],
                        capture_output=True,
                        check=True,
                        timeout=180,
                    )
                    data = proc.stdout
                    got = hashlib.sha256(data).hexdigest()
                    if got != expected or len(data) != rec["bytes"]:
                        raise RuntimeError(f"blob sha/size mismatch for {rec['blob']}")
                    part.write_bytes(data)
                    part.replace(dest)
                    restored.append({
                        "sha256": expected,
                        "bytes": len(data),
                        "status": "downloaded_git_pack",
                        "repo": rec["repo_first"],
                        "blob": rec["blob"],
                        "sources": rec["sources"],
                    })
                except Exception as exc:
                    part.unlink(missing_ok=True)
                    clone_errors.append({
                        "repo": rec["repo_first"],
                        "blob": rec["blob"],
                        "sources": rec["sources"],
                        "error": repr(exc),
                    })
        except Exception as exc:
            for rec in remaining:
                clone_errors.append({
                    "repo": rec["repo_first"],
                    "blob": rec["blob"],
                    "sources": rec["sources"],
                    "error": repr(exc),
                })
    return restored, clone_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be positive")

    inventory = json.loads(INVENTORY.read_text())
    owner = inventory["owner"]
    records = inventory["rasters"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    need_fetch: list[dict] = []

    for r in records:
        dest = args.out_dir / f"{r['sha256']}.tif"
        if dest.is_file() and dest.stat().st_size == r["bytes"] and sha256(dest) == r["sha256"]:
            rows.append({
                "sha256": r["sha256"],
                "bytes": r["bytes"],
                "status": "cached_ok",
                "repo": r["repo_first"],
                "blob": r["blob"],
                "sources": r["sources"],
            })
        else:
            need_fetch.append(r)

    rest_failed: list[dict] = []
    if need_fetch:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(fetch_one_rest, r, args.out_dir, owner): r for r in need_fetch}
            for future in as_completed(futures):
                record = futures[future]
                try:
                    result = future.result()
                    rows.append({
                        **result,
                        "repo": record["repo_first"],
                        "blob": record["blob"],
                        "sources": record["sources"],
                    })
                except Exception:
                    rest_failed.append(record)

    errors: list[dict] = []
    if rest_failed:
        token = _github_token()
        by_repo: dict[str, list[dict]] = defaultdict(list)
        for rec in rest_failed:
            by_repo[rec["repo_first"]].append(rec)
        with ThreadPoolExecutor(max_workers=min(4, args.workers)) as pool:
            futs = {
                pool.submit(restore_repo_codeload_and_git, repo_n, recs, args.out_dir, owner, token): repo_n
                for repo_n, recs in by_repo.items()
            }
            for fut in as_completed(futs):
                ok_rows, err_rows = fut.result()
                rows.extend(ok_rows)
                errors.extend(err_rows)

    rows.sort(key=lambda row: row["sha256"])
    errors.sort(key=lambda row: (row["repo"], row["blob"]))
    complete = not errors and len(rows) == len(records)
    receipt = {
        "schema": "gems86.registry-restore.v1",
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "inventory_entries": len(records),
        "verified_entries": len(rows),
        "errors": errors,
        "complete_accessible_scan": complete,
        "organizer_authenticated": False,
        "comparison_only": True,
        "bytes_verified": sum(row["bytes"] for row in rows),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: receipt[k] for k in (
        "inventory_entries", "verified_entries", "complete_accessible_scan", "bytes_verified")}, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
