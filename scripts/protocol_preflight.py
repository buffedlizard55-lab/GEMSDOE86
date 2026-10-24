"""Measure a pinned counterexample to the literal dot-overlap rule.

This is not a model experiment, candidate validation, or registry clearance.
The shared saturation_certificate is reused unchanged. A second direct-support
check makes the observed full-footprint coverage independently auditable.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from gems57 import grid
from gems57.uniqueness import saturation_certificate


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_file(path, sha256, size=None):
    path = Path(path)
    if size is not None and path.stat().st_size != size:
        raise ValueError(f'Wrong byte length: {path.name}')
    if digest(path) != sha256:
        raise ValueError(f'SHA256 mismatch: {path.name}')


def measure(data_dir=None):
    # Direct callers must not rely on another CLI having checked shared bytes.
    # Use the same two-import-path guard as the release audit, not a private copy.
    from scripts.audit_release import verify_shared_pins
    if not all(verify_shared_pins(ROOT).values()):
        raise ValueError('Shared tool SHA drift; protocol measurement cannot proceed')
    data_dir = Path(data_dir) if data_dir is not None else ROOT / 'data'
    pin = json.loads((ROOT / 'research/registry_witness_pin.json').read_text())
    inventory = ROOT / 'research/upstream/registry_inventory.json'
    verify_file(inventory, pin['registry_sha256'])
    records = json.loads(inventory.read_text())['rasters']
    match = [r for r in records if r['sha256'] == pin['sha256']]
    source_id = pin['repo'].split('/')[-1] + ':' + pin['source_path']
    if len(match) != 1 or source_id not in match[0]['sources'] or match[0]['blob'] != pin['blob']:
        raise ValueError('Witness is not bound to the pinned registry record')
    witness = data_dir / pin['dest']
    for path, sha, size in (
        (data_dir / 'sample_submission.tif', grid.SHA256_SAMPLE_SUBMISSION, None),
        (data_dir / 'existing_faults.tif', grid.SHA256_EXISTING_FAULTS, None),
        (witness, pin['sha256'], pin['bytes']),
    ):
        verify_file(path, sha, size)
    g = grid.load_grid(data_dir)
    with rasterio.open(witness) as src:
        if (src.shape, src.crs, src.transform, src.count) != (g.shape, g.crs, g.transform, 1):
            raise ValueError('Witness grid mismatch')
        if not (src.read_masks(1)[g.footprint] > 0).all():
            raise ValueError('Witness validity mask excludes cells inside the footprint')
        a = src.read(1)
        # Invalid prior values must not be used as a saturation witness.
        inside = a[g.footprint]
        if not np.isfinite(inside).all() or (inside < 0).any() or (inside > 1).any():
            raise ValueError('Witness values inside footprint are not probabilities')
        directly_covered = np.isfinite(a) & (a > 0) & g.footprint
        direct_uncovered = int((g.footprint & ~g.catalogue & ~directly_covered).sum())
        range_inside = [float(inside.min()), float(inside.max())]
    certificate = saturation_certificate(witness, g.footprint, g.catalogue,
                                        expected_grid=(g.shape, g.crs, g.transform))
    if direct_uncovered == 0 and not certificate['universal_overlap_blocker']:
        raise AssertionError('Direct-support oracle contradicts shared certificate')
    # Timestamp the completed measurement, not the historical witness verification.
    measured = datetime.now(timezone.utc)
    certificate.update(
        witness_file='data/' + pin['dest'],
        witness_source=f"https://api.github.com/repos/{pin['repo']}/git/blobs/{pin['blob']}",
        source_path=pin['source_path'],
        registry_source=f"https://github.com/{pin['registry_repository']}/blob/{pin['registry_commit']}/{pin['registry_path']}",
        registry_sha256=pin['registry_sha256'],
        registry_entries_in_snapshot=len(records),
        registry_rasters_measured=1,
        registry_complete=False,
        footprint_pixels=int(g.footprint.sum()),
        catalogue_pixels=int(g.catalogue.sum()),
        direct_support_uncovered_allowed_pixels=direct_uncovered,
        witness_range_inside_footprint=range_inside,
        witness_grid_matches=True,
        witness_validity_mask_covers_footprint=True,
        measured_utc=measured.isoformat(timespec='seconds'),
        measured_date_utc=measured.date().isoformat(),
        witness_verified_date_utc=pin['verified_date_utc'],
        candidate_generated=False,
        thresholds_unchanged=True,
        dense_surface_exemption=False,
        status='STOP_LITERAL_OVERLAP_UNSATISFIABLE' if certificate['universal_overlap_blocker'] else 'NO_UNIVERSAL_BLOCKER_FOUND_NOT_CLEARANCE',
        scope='One hash-verified historical registry witness; sufficient for a negative, never for uniqueness clearance. No candidate surface or dots measured.',
        proof='Every allowed pixel is already positive in the witness if direct_support_uncovered_allowed_pixels=0. Any nonempty subset then has forward 3px overlap 1, exceeding 0.70, regardless of rank correlation or geological mechanism.'
    )
    return certificate


def require_feasible():
    """Mandatory early stop for model entrypoints; never an authorization gate."""
    certificate = measure()  # Missing/untrusted inputs raise; they never pass.
    if certificate['universal_overlap_blocker']:
        raise RuntimeError('STOP_LITERAL_OVERLAP_UNSATISFIABLE: no new model experiment or TIFF placement is permitted by the current rule')
    return certificate


if __name__ == '__main__':
    result = measure()
    output = ROOT / 'docs/evidence/protocol-preflight.json'
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))
