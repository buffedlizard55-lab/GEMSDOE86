"""Restore integrity-pinned owner mirrors; never call them authenticated official data."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def _digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _download(item, destination):
    temporary = destination.with_suffix(destination.suffix + '.partial')
    try:
        with temporary.open('wb') as stream:
            if item.get('blob'):
                endpoints = [f"repos/{item['repo']}/git/blobs/{item['blob']}"]
            else:
                endpoints = [f"repos/{item['repo']}/contents/{part}?ref={item['ref']}"
                             for part in item.get('parts', [item['path']])]
            for endpoint in endpoints:
                subprocess.run(['gh', 'api', endpoint,
                                '-H', 'Accept: application/vnd.github.raw+json'],
                               stdout=stream, check=True)
        if _digest(temporary) != item['sha256']:
            raise ValueError(f"Hash mismatch while restoring {item['id']}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def restore(include_features=False, experiment=False):
    core = json.loads((ROOT / 'research/upstream/data_manifest.json').read_text())['files']
    wanted = {'existing_faults', 'sample_submission'}
    if include_features or experiment:
        wanted.add('training_features')
    items = [item for item in core if item['id'] in wanted]
    if experiment:
        items.extend(json.loads((ROOT / 'registry/experiment_input_pins.json').read_text())['files'])

    receipts = []
    for item in items:
        destination = ROOT / 'data' / item['dest']
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            _download(item, destination)
        digest = _digest(destination)
        if digest != item['sha256'] or destination.stat().st_size != item['bytes']:
            raise ValueError(f"Integrity mismatch: {destination}")
        receipts.append({
            'id': item['id'], 'sha256': digest, 'bytes': destination.stat().st_size,
            'provenance': item['provenance'], 'organizer_authenticated': False,
        })
    (ROOT / 'docs/evidence/data_restore.json').write_text(
        json.dumps(receipts, indent=2, allow_nan=False) + '\n'
    )
    return receipts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-features', action='store_true',
                        help='also fetch the 419 MB mirrored 19-band feature TIFF')
    parser.add_argument('--experiment', action='store_true',
                        help='restore all RMRB experiment inputs, including features and registry witnesses')
    arguments = parser.parse_args()
    print(json.dumps(restore(arguments.include_features, arguments.experiment), indent=2))
