"""Restore integrity-pinned owner mirrors; never describe these as authenticated official data."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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
                        subprocess.run(['gh', 'api', f"repos/{item['repo']}/contents/{part}?ref={item['ref']}",
                                        '-H', 'Accept: application/vnd.github.raw+json'], stdout=f, check=True)
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
    (ROOT / 'docs/evidence/data_restore.json').write_text(json.dumps(receipts, indent=2) + '\n')
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
            subprocess.run(['gh', 'api', f"repos/{pin['repo']}/git/blobs/{pin['blob']}",
                            '-H', 'Accept: application/vnd.github.raw+json'],
                           stdout=stream, check=True)
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
