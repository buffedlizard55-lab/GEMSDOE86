"""Restore integrity-pinned owner mirrors; never describe these as authenticated official data."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _is_rest_rate_limited(exc: subprocess.CalledProcessError) -> bool:
    return bool(exc.stderr and b"API rate limit exceeded" in exc.stderr)


def _git_fetch_blob(repo: str, blob: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gems86_gitblob_") as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        subprocess.run(
            ["git", "-C", td, "fetch", "-q", "--depth=1", f"https://github.com/{repo}.git", blob],
            check=True,
            timeout=900,
        )
        raw = subprocess.check_output(["git", "-C", td, "cat-file", "blob", blob], timeout=600)
    identity = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if identity != blob:
        raise ValueError("Git smart-HTTP blob object identity mismatch")
    return raw


def _git_fetch_path(repo: str, ref: str, path: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="gems86_gitpath_") as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        subprocess.run(
            ["git", "-C", td, "fetch", "-q", "--filter=blob:none", "--depth=1", f"https://github.com/{repo}.git", ref],
            check=True,
            timeout=900,
        )
        raw = subprocess.check_output(["git", "-C", td, "show", f"FETCH_HEAD:{path}"], timeout=600)
    return raw


def write_blob(repo, blob, stream):
    """Decode the JSON Git Data API, avoiding gh's binary stdout transformer.

    Raw TIFF streaming works in some gh builds but fails with "transform:
    short source buffer" on the hosted runner. JSON/base64 is portable; Git
    object identity plus the final SHA256/size pins still authenticate bytes.
    When concurrent org sessions exhaust GitHub's 5,000 req/hr REST API quota,
    fall back strictly on ``API rate limit exceeded`` to Git smart-HTTP blob
    transport verified against the identical Git SHA-1 object identity.
    """
    try:
        response = subprocess.run(['gh', 'api', f'repos/{repo}/git/blobs/{blob}',
                                   '-H', 'Accept: application/vnd.github+json'],
                                  capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:
        if not _is_rest_rate_limited(exc):
            raise
        raw = _git_fetch_blob(repo, blob)
        stream.write(raw)
        return
    obj = json.loads(response.stdout)
    if obj.get('encoding') != 'base64' or obj.get('sha') != blob:
        raise ValueError('Unexpected Git blob identity or encoding')
    raw = base64.b64decode(''.join(obj['content'].split()), validate=True)
    identity = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if identity != blob or obj.get('size') != len(raw):
        raise ValueError('Git object identity/size mismatch')
    stream.write(raw)


def write_path(repo, ref, path, stream):
    try:
        blob = subprocess.check_output(['gh', 'api',
            f'repos/{repo}/contents/{path}?ref={ref}', '--jq', '.sha'],
            stderr=subprocess.PIPE).decode().strip()
    except subprocess.CalledProcessError as exc:
        if not _is_rest_rate_limited(exc):
            raise
        stream.write(_git_fetch_path(repo, ref, path))
        return
    write_blob(repo, blob, stream)


def restore(include_features=False, include_registry=False):
    manifest = json.loads((ROOT / 'research/upstream/data_manifest.json').read_text())
    receipts = []
    for item in manifest['files']:
        if item['id'] not in {'existing_faults', 'sample_submission'} | ({'training_features'} if include_features else set()):
            continue
        dest = ROOT / 'data' / item['dest']
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            tmp = dest.with_suffix('.partial')
            try:
                with tmp.open('wb') as f:
                    for part in item.get('parts', [item.get('path')]):
                        write_path(item['repo'], item['ref'], part, f)
                with tmp.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if digest != item['sha256'] or tmp.stat().st_size != item['bytes']:
                    raise ValueError(f"Integrity mismatch before publication: {item['id']}")
                tmp.replace(dest)
            finally:
                tmp.unlink(missing_ok=True)
        with dest.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if digest != item['sha256'] or dest.stat().st_size != item['bytes']:
            raise ValueError(f"Integrity mismatch: {dest}")
        receipts.append(dict(id=item['id'], sha256=digest, bytes=dest.stat().st_size,
                             provenance=item['provenance'], organizer_authenticated=False))
    if include_registry:
        restore_registry_witness()
    (ROOT / 'docs/evidence/protocol-data-restore.json').write_text(json.dumps(receipts, indent=2) + '\n')
    return receipts


def restore_registry_witness():
    from scripts.protocol_preflight import verify_file
    pin = json.loads((ROOT / 'research/registry_witness_pin.json').read_text())
    dest = ROOT / 'data' / pin['dest']
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        verify_file(dest, pin['sha256'], pin['bytes'])
        return dest
    tmp = dest.with_suffix('.partial')
    try:
        with tmp.open('wb') as stream:
            write_blob(pin['repo'], pin['blob'], stream)
        verify_file(tmp, pin['sha256'], pin['bytes'])
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-features', action='store_true', help='also fetch the 419 MB mirrored feature raster; not the shared cached stack')
    parser.add_argument('--include-registry', action='store_true', help='restore the immutable historical saturation witness, NOT a candidate')
    args = parser.parse_args()
    print(json.dumps(restore(args.include_features, args.include_registry), indent=2))
