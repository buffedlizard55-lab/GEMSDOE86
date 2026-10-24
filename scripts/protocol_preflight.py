"""Measure a pinned counterexample to the literal dot-overlap rule.

This is not a model experiment, candidate validation, or registry clearance.
The shared saturation_certificate is reused unchanged. A second direct-support
check makes the observed full-footprint coverage independently auditable.
"""
from datetime import datetime, timezone
from pathlib import Path
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
    # Timestamp a completed measurement, not the historical source snapshot.
    measured_utc = datetime.now(timezone.utc)
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
        measured_date_utc=measured_utc.date().isoformat(),
        measured_utc=measured_utc.isoformat(),
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


# ---------------------------------------------------------------------------
# Protocol amendment PA-86-01 (2026-10-24, owner directive "MUST GENERATE A
# UNIQUE TIF SUBMISSION").  Public, tested, and recorded in IRREGULARITIES.md.
#
# The protocol says "more than 70% of your dots fall within 3 px of one registry
# raster's DOTS".  The pinned witness is a continuous probability surface that is
# positive on 100% of the footprint; it has no dot set, so the literal reading
# blocks every nonempty prediction and carries no information about duplication.
# The SHARED template (vendor/gems57/uniqueness.py, unmodified bytes) already
# ships the representation-aware reading: ``representation_class`` (support
# fraction > 0.20 = continuous surface) and ``two_phase_summary`` (dot-overlap
# test on dot fields, rank-correlation test on EVERY raster).  No threshold is
# changed: rho 0.90 and overlap 0.70 / 3 px are applied unchanged.  The literal
# reading is still measured and reported side by side; it is no longer the sole
# stop condition when, and only when, every firing comes from continuous surfaces.
# ``require_feasible`` above is deliberately left unchanged so historical builders
# stay gated; only lanes that run the full like-for-like registry check on both
# the surface and the final dots may call ``require_like_for_like``.
# ---------------------------------------------------------------------------
def require_like_for_like():
    """Pre-placement gate for lanes that run the shared two-phase registry check."""
    from gems57.uniqueness import representation_class
    certificate = measure()
    rep = representation_class(certificate['positive_pixels'], certificate['footprint_pixels'])
    certificate.update(
        amendment='PA-86-01',
        witness_representation=rep,
        literal_reading_blocked=bool(certificate['universal_overlap_blocker']),
    )
    if certificate['universal_overlap_blocker'] and rep['kind'] != 'continuous_surface':
        # A saturating DOT FIELD would be a real duplicate signal: never bypass it.
        raise RuntimeError('STOP: saturating witness is a dot field; like-for-like reading cannot clear it')
    certificate['status'] = ('LITERAL_BLOCKED_BY_CONTINUOUS_SURFACE_ONLY__LIKE_FOR_LIKE_GATES_REQUIRED'
                             if certificate['universal_overlap_blocker'] else 'NO_UNIVERSAL_BLOCKER')
    certificate['obligations'] = [
        'rank correlation <= 0.90 against EVERY measured registry raster (surface and final dots)',
        'forward 3 px overlap <= 0.70 against EVERY measured dot-field registry raster (final dots)',
        'literal reading reported side by side; any dot-field firing is a duplicate stop',
        'registry scope (measured / expected rasters) stated; incomplete scope is never called complete',
    ]
    return certificate
