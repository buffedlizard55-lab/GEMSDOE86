"""Revalidate EVERY published research TIFF using the unchanged shared validators.

No training, new raster, metric estimate, clipping, or slot authorization occurs.
`--write` refreshes the deterministic report and its HTML view only after all
checks pass. Default mode verifies the committed report/page without writing.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from gems57 import grid, gates
from gems57.validate import validate
from scripts.check_site import check, load_inventory
from scripts.session_preflight import check_pins

REPORT = 'docs/evidence/download-validation.json'
PAGE = 'docs/download-status.html'
CARD = 'docs/evidence/session-review-run-card.json'


def review_card(report):
    """A no-new-candidate run card; do not recycle an inherited raster identity."""
    proof = json.loads((ROOT / 'docs/evidence/protocol-preflight.json').read_text())
    if (proof.get('status') != 'STOP_LITERAL_OVERLAP_UNSATISFIABLE'
            or proof.get('universal_overlap_blocker') is not True
            or proof.get('covered_allowed_fraction') != 1.0):
        raise ValueError('Protocol proof changed; review the no-new-candidate card rather than inventing clearance')
    return dict(
        hypothesis='Deferred basement mass-balance residual; no assigned method lane',
        mechanism='Remove a forward basement gravity response and test persistent residual gradients.',
        non_fault_mimic='Lateral sediment-density changes and basement-model error',
        holdout_dti=dict(evidence_class='HOLDOUT-DTI', evaluator_version='gems57-pooled-hide-v2',
                         status='NOT_RUN_PROTOCOL_STOP', withheld_positives=None, value=None, ci95=None),
        correlation_overlap_vs_registry=dict(status=proof['status'], complete=False, surface=None, final_dots=None,
            witness_sha256=proof['witness_sha256'], covered_allowed_fraction=proof['covered_allowed_fraction'],
            implication='Every nonempty allowed dot set fails the literal overlap rule; not a measured candidate comparison.'),
        raster_sha256=None,
        validator=dict(status='NOT_RUN_NO_NEW_CANDIDATE', no_nan_inside_footprint=None,
                       values_in_0_1=None, crs_shape_transform_match=None,
                       inherited_artifacts_local_format_pass=report['all_checks_passed'], report=REPORT),
        submission_name=None,
        note='No new TIFF: protocol stop reproduced. H86G PROMOTE is historical; current upload authorization is DO NOT SUBMIT.',
        verdict='negative', safe_to_submit=False, experiments_run=0, submission_slots_used=0,
        scope='Format/integrity audit only. No new model, surface or dots. H86G-EDTI retains a historical PA-86-01 PROMOTE verdict, but the current literal registry rule blocks upload; no selector action or weekly slot was recorded.')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def gdsc_zip_filename_matches(receipt_value, expected_zip_ref):
    """Accept only the receipt basename or the exact inventory-relative ZIP path."""
    expected = Path(expected_zip_ref).as_posix()
    actual = Path(str(receipt_value or '')).as_posix()
    return actual in {expected, Path(expected).name}


def audit_artifact(path, entry, sample, footprint, catalogue):
    """Inspect bytes directly; the adjacent JSON may be a writer receipt or archived run card."""
    receipt = json.loads(path.with_suffix('.json').read_text())
    sha = digest(path)
    local = validate(path, footprint, catalogue)
    template = gates.format_report(path, sample, footprint=footprint)
    with rasterio.open(path) as src:
        # Project's conservative all-finite export has no nodata tag/masked cells.
        unmasked = bool((src.read_masks(1)[footprint] > 0).all())
        no_nodata = src.nodata is None
    is_run_card = (receipt.get('evidence_class') == 'RUN-CARD'
                   and path.name.startswith('gems86-blindgeothermal-dilation-'))
    is_gdsc_sidecar = receipt.get('metadata', {}).get('lane') == 'GDSC'
    gdsc_card = None
    if is_gdsc_sidecar:
        card_path = ROOT / 'docs/evidence/gdsc-run-card.json'
        if not card_path.is_file():
            raise ValueError(f'{path.name}: linked GDSC run card is missing')
        gdsc_card = json.loads(card_path.read_text())
    zip_path = path.with_suffix('.zip')
    with zipfile.ZipFile(zip_path) as bundle:
        zip_one_exact_tif = bundle.namelist() == [path.name]
        zip_payload_matches = zip_one_exact_tif and bundle.read(path.name) == path.read_bytes()
        zip_crc_passed = bundle.testzip() is None
    checks = dict(local['checks'])
    checks.update(
        shared_template_format_pass=template['ok'],
        in_footprint_valid_mask=unmasked,
        no_nodata_tag=no_nodata,
        hash_matches_inventory=sha == entry['sha256'],
        receipt_hash_matches=receipt.get('sha256') == sha,
        receipt_filename_matches=receipt.get('file') == path.name,
        receipt_byte_count_matches=receipt.get('bytes') == path.stat().st_size,
        zip_one_exact_tif=zip_one_exact_tif,
        zip_payload_equals_tif=zip_payload_matches,
        zip_crc_passed=zip_crc_passed,
    )
    if is_run_card:
        checks.update(
            run_card_sidecar_schema_recognized=True,
            run_card_no_unverified_zip_hash_claim='zip_sha256' not in receipt and 'zip_file' not in receipt,
            receipt_not_promoted=receipt.get('verdict') == 'format-valid; not organizer-confirmed; weekly slot not used',
            receipt_no_slot_approval=receipt.get('submission_slots_used') == 0,
        )
    elif is_gdsc_sidecar:
        expected_zip_ref = Path(entry['file']).with_suffix('.zip').as_posix()
        checks.update(
            gdsc_run_card_sidecar_schema_recognized=True,
            receipt_zip_filename_matches=gdsc_zip_filename_matches(receipt.get('zip_file'), expected_zip_ref),
            receipt_zip_hash_matches=receipt.get('zip_sha256') == digest(zip_path),
            receipt_not_promoted=(gdsc_card.get('verdict') == 'negative'
                                  and gdsc_card.get('safe_to_submit') is False),
            receipt_no_slot_approval=(gdsc_card.get('approved_for_weekly_slot') is False
                                      and gdsc_card.get('submission_slots_used') == 0),
        )
    else:
        checks.update(
            receipt_zip_filename_matches=receipt.get('zip_file') == zip_path.name,
            receipt_zip_hash_matches=receipt.get('zip_sha256') == digest(zip_path),
            receipt_not_promoted=receipt.get('promoted') is False,
            receipt_no_slot_approval=receipt.get('approved_for_weekly_slot') is False,
        )
    for key in ('submission_name', 'note'):
        text = receipt.get(key)
        checks[key + '_valid_length'] = isinstance(text, str) and bool(text.strip()) and len(text) <= 140
    checks['receipt_note_length_matches'] = receipt.get('note_chars') == len(receipt.get('note', ''))
    failed = [key for key, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f'{path.name}: failed checks: {failed}')
    return dict(file=entry['file'], sha256=sha, bytes=path.stat().st_size,
                zip_file=str(Path(entry['file']).with_suffix('.zip')),
                zip_sha256=digest(zip_path),
                submission_name=receipt['submission_name'], note=receipt['note'],
                note_chars=len(receipt['note']), positive_pixels=local['emitted_positive_pixels'],
                min=local['min'], max=local['max'], n_nan=local['n_nan'], n_infinite=local['n_infinite'],
                grid=local['meta'], checks=checks, all_checks_passed=True,
                safe_to_submit=False, status='NOT_ASSESSED_BY_FORMAT_AUDIT',
                sidecar_kind=('archived run-card sidecar' if is_run_card else
                              'GDSC run-card-linked writer receipt' if is_gdsc_sidecar else
                              'writer receipt'))


def audit(root=ROOT):
    root = Path(root).resolve()
    # Always pin the actual imported shared code, not a privately patched validator.
    if not check_pins():
        raise ValueError('Shared template hash mismatch')
    pins = json.loads((ROOT / 'research/template_pin.json').read_text())['files']
    tool_hashes = {}
    for module in (grid, gates, sys.modules[validate.__module__]):
        expected = pins['vendor/gems57/' + module.__name__.rsplit('.', 1)[-1] + '.py']
        actual = digest(module.__file__)
        if actual != expected:
            raise ValueError(f'Imported shared tool drift: {module.__name__}')
        tool_hashes[module.__name__] = actual
    errors = check(root)
    if errors:
        raise ValueError('\n'.join(errors))
    bridge = root / 'data/bridge'
    for name, expected in (('sample_submission.tif', grid.SHA256_SAMPLE_SUBMISSION),
                           ('existing_faults.tif', grid.SHA256_EXISTING_FAULTS)):
        if digest(bridge / name) != expected:
            raise ValueError(f'Bridge mirror SHA256 mismatch: {name}')
    with rasterio.open(bridge / 'sample_submission.tif') as sample, rasterio.open(bridge / 'existing_faults.tif') as faults:
        if (sample.shape, sample.crs, sample.transform, sample.count) != (grid.SHAPE, rasterio.crs.CRS.from_epsg(grid.EPSG), grid.TRANSFORM, 1):
            raise ValueError('Pinned sample grid mismatch')
        if (faults.shape, faults.crs, faults.transform, faults.count) != (sample.shape, sample.crs, sample.transform, 1):
            raise ValueError('Pinned catalogue grid mismatch')
        footprint = np.isfinite(sample.read(1)) & (sample.read_masks(1) > 0)
        catalogue = faults.read(1) > 0
    artifacts = [audit_artifact(path, entry, bridge / 'sample_submission.tif', footprint, catalogue)
                 for path, entry in load_inventory(root).items()]
    if not artifacts:
        raise ValueError('No registered research artifacts to validate')
    return dict(schema_version=1, evidence_class='LOCAL-FORMAT-AND-INTEGRITY',
                scope='All registered published research TIFFs, ZIPs and identity sidecars (writer receipts or archived run cards); not holdout, uniqueness or organizer acceptance.',
                organizer_authenticated=False, safe_to_submit=False, verdict='negative',
                all_checks_passed=True, artifact_count=len(artifacts), shared_tool_hashes=tool_hashes,
                inputs={name: digest(bridge / name) for name in ('sample_submission.tif', 'existing_faults.tif')},
                artifacts=artifacts)


def render(report):
    sections = []
    for row in report['artifacts']:
        name = Path(row['file']).name
        href = 'downloads/' + name
        sections.append(f'''<section class="card"><h2 class="mono">{escape(name)}</h2>
<p><span class="badge neutral">FORMAT AUDIT ONLY · DECISION NOT MADE HERE</span> <span class="badge ok">Local format / integrity PASS</span></p>
<p><a class="btn ghost" href="{escape(href)}" download>Download TIFF — format audit</a>
<a class="btn ghost" href="{escape(str(Path(href).with_suffix('.zip')))}" download>Single-TIFF ZIP</a>
<a href="{escape(str(Path(href).with_suffix('.json')))}">{escape(row['sidecar_kind'])}</a></p>
<dl><dt>SHA-256</dt><dd class="mono">{row['sha256']}</dd>
<dt>File bytes</dt><dd>{row['bytes']:,}</dd>
<dt>Submission name (identity only, not authorization)</dt><dd>{escape(row['submission_name'])}</dd>
<dt>Recorded note ({row['note_chars']} characters; historical wording preserved)</dt><dd>{escape(row['note'])}</dd>
<dt>Raster checks</dt><dd>{len(row['checks'])}/{len(row['checks'])} pass; range [{row['min']}, {row['max']}]; NaN {row['n_nan']}; infinity {row['n_infinite']}; positive cells {row['positive_pixels']:,}.</dd></dl></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verified research downloads · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header><nav><b>GEMSDOE86</b><a href="index.html">Decision</a><a href="executive-summary.html">How to submit</a><a href="evidence.html">Evidence</a></nav></header><main>
<h1>Verified research downloads — format audit, not a slot decision</h1>
<p>This page checks file bytes, GeoTIFF format and ZIP integrity; it does not authorize a weekly slot. The current repository decision is <strong>DO NOT SUBMIT any file</strong>. H86G-EDTI retains a historical PA-86-01 PROMOTE verdict under a like-for-like reading, but does not pass the current literal registry rule; it is available for audit/reproducibility only. No slot was picked here. Local format checks alone do not establish geological skill, uniqueness, eligibility or organizer acceptance.</p>
<p>This page is generated from actual TIFF bytes and adjacent writer receipts or archived run-card sidecars, not manually transcribed sizes or note lengths. The conservative export policy requires finite [0,1] values everywhere, exact sample geometry, valid in-footprint masks, no nodata tag, zero outside the footprint and zero on mapped faults. Inputs are hash-pinned owner mirrors, not authenticated organizer downloads.</p>
<p><a href="index.html">Current per-file decision and H86G-EDTI download</a> · <a href="executive-summary.html">Submission steps</a> · <a href="evidence/download-validation.json">Full automated validation report</a> · <a href="evidence/protocol-preflight.json">Literal registry blocker proof</a> · <a href="evidence/session-review-run-card.json">This audit's negative no-slot run card</a></p>
<p>Regenerate with <code>python scripts/audit_downloads.py --write</code>; verify without writes with <code>python scripts/audit_downloads.py</code>. CI reruns the byte checks before Pages publication. This is not a live leaderboard feed.</p>
''' + '\n'.join(sections) + '\n</main><footer>Format PASS ≠ submission authorization or organizer acceptance. Current repository decision: DO NOT SUBMIT any file.</footer></body></html>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='refresh the report and HTML after successful validation')
    args = parser.parse_args()
    report = audit()
    outputs = {REPORT: json.dumps(report, indent=2, allow_nan=False) + '\n', PAGE: render(report),
               CARD: json.dumps(review_card(report), indent=2, allow_nan=False) + '\n'}
    for relative, content in outputs.items():
        path = ROOT / relative
        if args.write:
            path.write_text(content, encoding='utf-8')
        elif not path.is_file() or path.read_text(encoding='utf-8') != content:
            raise SystemExit(f'Stale or missing generated output: {relative}; run --write')
    print(f"PASS: {report['artifact_count']} research TIFFs and receipts revalidated; current repository decision remains DO NOT SUBMIT (format audit made no selector decision)")


if __name__ == '__main__':
    main()
