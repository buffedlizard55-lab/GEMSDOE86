"""Verify the published candidate and evidence without regenerating the model."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from gems57 import grid  # noqa: E402


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_pins():
    pin = json.loads((ROOT / 'research/template_pin.json').read_text())
    return all((ROOT / p).is_file() and digest(ROOT / p) == expected
               for p, expected in pin['files'].items())


def run():
    if not check_pins():
        raise AssertionError('shared evaluator/writer bytes drifted from template pin')
    card_path = ROOT / 'docs/evidence/rmrb86-run-card.json'
    card = json.loads(card_path.read_text())
    tif = ROOT / 'docs' / card['download_file']
    archive = ROOT / 'docs' / card['zip_file']
    if digest(tif) != card['raster_sha256']:
        raise AssertionError('published TIFF hash differs from run card')
    with rasterio.open(tif) as src:
        values = src.read(1)
        if src.count != 1 or src.dtypes[0] != 'float32':
            raise AssertionError('candidate is not a single float32 band')
        if src.shape != grid.SHAPE or src.crs.to_epsg() != grid.EPSG or src.transform != grid.TRANSFORM:
            raise AssertionError('candidate grid differs from competition template constants')
        if src.nodata is not None:
            raise AssertionError('all-finite candidate must not carry a nodata sentinel')
    if not np.isfinite(values).all() or values.min() < 0 or values.max() > 1:
        raise AssertionError('candidate contains nonfinite or out-of-range values')
    if int((values > 0).sum()) != 37_654:
        raise AssertionError('candidate dot budget drifted')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.namelist() != [tif.name] or bundle.read(tif.name) != tif.read_bytes():
            raise AssertionError('ZIP is not a byte-identical one-TIFF bundle')
    if len(card['note']) > 140:
        raise AssertionError('submission note exceeds 140 characters')
    if card['verdict'] == 'negative' and card['safe_to_submit']:
        raise AssertionError('negative result cannot be marked safe to submit')
    if card['validator_output']['status'] != 'PASS_LOCAL_FORMAT_ONLY':
        raise AssertionError('published local format validation is not a pass')
    return card


if __name__ == '__main__':
    result = run()
    print(json.dumps({
        'raster_sha256': result['raster_sha256'],
        'verdict': result['verdict'],
        'safe_to_download': result['safe_to_download'],
        'safe_to_submit': result['safe_to_submit'],
        'validator_output': result['validator_output'],
    }, indent=2, allow_nan=False))
