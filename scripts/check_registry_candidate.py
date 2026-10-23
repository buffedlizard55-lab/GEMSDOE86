"""Diagnostic registry check of the inherited artifact; no new model or placement.

One measured counterexample is sufficient for a stop, never a uniqueness pass.
The shared checker is reused verbatim with an explicitly incomplete inventory.
"""
import json
from pathlib import Path
import sys

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from scripts.protocol_preflight import measure, verify_file
from gems57.grid import load_grid
from gems57.uniqueness import compare_array_to_registry


def run():
    certificate = measure()  # authenticates mirrored grid and witness hashes
    pin = json.loads((ROOT / 'research/registry_witness_pin.json').read_text())
    card = json.loads((ROOT / 'docs/evidence/run-card.json').read_text())
    tif = ROOT / card['submission_file']
    verify_file(tif, card['raster_sha256'])
    g = load_grid(ROOT / 'data')
    with rasterio.open(tif) as src:
        if (src.count, src.shape, src.crs, src.transform) != (1, g.shape, g.crs, g.transform):
            raise ValueError('Inherited candidate grid differs from authenticated mirror grid')
        prediction = src.read(1)
    records = [dict(repo=pin['repo'], submission=pin['source_path'],
                    file=str(ROOT / 'data' / pin['dest']), sha256=pin['sha256'])]
    result = compare_array_to_registry(prediction, records, g.footprint,
        file_sha256=card['raster_sha256'], expected_grid=(g.shape, g.crs, g.transform))
    # Remove machine-local paths from the otherwise unchanged shared report.
    for row in result['rows']:
        if 'file' in row:
            row['file'] = 'data/' + pin['dest']
    result.update(
        candidate_file=card['submission_file'],
        scope='Inherited negative TIFF vs one immutable dense registry witness. Not a complete scan or pre-placement surface check; no new experiment or artifact.',
        inherited_candidate=True,
        universal_blocker=certificate['universal_overlap_blocker'])
    return result


if __name__ == '__main__':
    result = run()
    (ROOT / 'docs/evidence/inherited-registry-check.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('worst_spearman_full_footprint', 'worst_dot_overlap', 'unique', 'stop_required', 'complete_accessible_scan')}, indent=2))
