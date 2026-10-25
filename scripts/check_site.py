"""Fail closed on broken Pages links and unsafe publication of research files.

This is deliberately a negative-state publication guard, not a slot selector.
An inventory entry cannot authorize a submission by changing a boolean.
"""
from html.parser import HTMLParser
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                self.urls.append(value)


def load_inventory(root):
    """Return unique, contained TIFF paths or reject the entire inventory.

    Resolve symlinks before containment tests; do not let dictionary construction
    silently discard duplicate rows or allow repo-only files into the Pages set.
    """
    root = Path(root).resolve()
    downloads = root / 'docs/downloads'
    document = json.loads((root / 'docs/evidence/download-inventory.json').read_text())
    entries = document['artifacts']
    if not isinstance(entries, list):
        raise ValueError('Inventory artifacts must be a list')
    registered = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('file'), str):
            raise ValueError('Inventory entry needs a file path')
        relative = Path(entry['file'])
        target = (root / relative).resolve()
        if (relative.is_absolute() or '..' in relative.parts or
                not target.is_relative_to(downloads) or target.suffix.lower() not in {'.tif', '.tiff'} or
                not target.is_file()):
            raise ValueError(f'Missing or escaping registered artifact: {relative}')
        if target in registered:
            raise ValueError(f'Duplicate inventory path: {relative}')
        if not isinstance(entry.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
            raise ValueError(f'Invalid SHA256: {relative}')
        status = entry.get('status')
        if entry.get('approved_for_weekly_slot') is not False or not (
                status == 'DO NOT SUBMIT'
                or (isinstance(status, str) and status.startswith('PROMOTE'))):
            raise ValueError('Inventory requires DO NOT SUBMIT (or recorded PROMOTE lane) status and false slot approval')
        registered[target] = entry
    return registered


def check(root=ROOT):
    root = Path(root).resolve()
    errors = []
    htmls = [root / 'index.html', *sorted((root / 'docs').rglob('*.html'))]
    for path in htmls:
        parser = Links(); parser.feed(path.read_text())
        for url in parser.urls:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if (not target.is_relative_to(root) or not target.is_file()
                    or (path.is_relative_to(root / 'docs') and not target.is_relative_to(root / 'docs'))):
                errors.append(f'{path.relative_to(root)}: broken or escaping local link {url}')
    try:
        registered = load_inventory(root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'Invalid download inventory: {exc}')
        registered = {}
    for target, entry in registered.items():
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            errors.append(f'Published raster SHA differs from inventory: {target.name}')
        archive = target.with_suffix('.zip')
        try:
            with zipfile.ZipFile(archive) as z:
                if (z.namelist() != [target.name] or z.getinfo(target.name).file_size != target.stat().st_size
                        or z.read(target.name) != target.read_bytes()):
                    errors.append(f'ZIP must contain exactly the registered TIFF bytes: {archive.name}')
        except (OSError, zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError):
            errors.append(f'Missing or invalid candidate ZIP: {archive.name}')
    for artifact in (root / 'docs').rglob('*'):
        suffix = artifact.suffix.lower()
        if suffix not in {'.tif', '.tiff', '.zip'}:
            continue
        # Match ZIPs to actual registered .tif OR .tiff partners, not guessed stems.
        allowed = (artifact.resolve() in registered if suffix != '.zip' else
                   any(artifact.resolve() == p.with_suffix('.zip') for p in registered))
        if not allowed:
            errors.append(f'Unregistered downloadable raster/archive: {artifact.relative_to(root)}')
    submission_dir = root / 'submission'
    if submission_dir.exists():
        allowed_submission = set()
        expected_spt_sha = None
        cand_rel = ''
        spt_audit_path = root / 'docs/evidence/spt-full-support-witness-audit.json'
        if spt_audit_path.is_file():
            spt_doc = json.loads(spt_audit_path.read_text(encoding='utf-8'))
            if (spt_doc.get('verdict') == 'negative_duplicate_stop_do_not_submit'
                    and spt_doc.get('submission_ready') is False
                    and spt_doc.get('download_authorized') is False):
                cand_rel = spt_doc.get('candidate_file', '')
                expected_spt_sha = spt_doc.get('candidate_file_sha256')
                if cand_rel.startswith('submission/') and expected_spt_sha:
                    allowed_submission.add(cand_rel)
                    allowed_submission.add(str(Path(cand_rel).with_suffix('.zip')))
        for extra in sorted(submission_dir.rglob('*')):
            if extra.is_file() and extra.suffix.lower() in {'.tif', '.tiff', '.zip'}:
                if str(extra.relative_to(root)) not in allowed_submission:
                    errors.append(f'Unregistered submission binary outside inventory: {extra.relative_to(root)}')
        if cand_rel and expected_spt_sha:
            cand_tif = root / cand_rel
            cand_zip = cand_tif.with_suffix('.zip')
            if cand_tif.is_file() and hashlib.sha256(cand_tif.read_bytes()).hexdigest() != expected_spt_sha:
                errors.append(f'Quarantined submission TIFF SHA differs from witness audit: {cand_rel}')
            if cand_zip.is_file():
                try:
                    with zipfile.ZipFile(cand_zip) as zf:
                        if (not cand_tif.is_file() or zf.namelist() != [cand_tif.name]
                                or zf.read(cand_tif.name) != cand_tif.read_bytes()):
                            errors.append(f'Quarantined submission ZIP payload differs from audited TIFF: {cand_zip.name}')
                except (OSError, zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError):
                    errors.append(f'Invalid quarantined submission ZIP: {cand_zip.name}')
    for html_file in sorted((root / 'docs').glob('*.html')):
        html_text = html_file.read_text(encoding='utf-8')
        if 'READY TO DOWNLOAD' in html_text:
            errors.append(f'Contradictory READY TO DOWNLOAD banner during negative release state: {html_file.name}')
        if 'raw.githubusercontent.com' in html_text and any(ext in html_text for ext in ('.tif', '.tiff', '.zip')):
            errors.append(f'Unregistered raw.githubusercontent.com binary download bypass: {html_file.name}')
        if html_file.name in {'index.html', 'executive-summary.html'}:
            unsafe_markers = ('SUBMIT THIS FILE', 'CURRENT DECISION: SUBMIT ONLY',
                              'ONE SELECTOR-READY FILE', 'DOWNLOAD → SUBMIT')
            if any(marker in html_text for marker in unsafe_markers):
                errors.append(f'Current download page advertises an unauthorized submission: {html_file.name}')
            if 'DO NOT SUBMIT' not in html_text:
                errors.append(f'Current download page lacks an explicit negative submission state: {html_file.name}')
    canonical_card = root / 'docs/evidence/run-card.json'
    if not canonical_card.is_file():
        errors.append('Missing canonical run card')
    card_files = sorted(set((root / 'docs/evidence').glob('*card*.json')) | {canonical_card, root / 'evidence/run_card.json'})
    for card_file in card_files:
        if not card_file.is_file():
            continue
        card = json.loads(card_file.read_text())
        promote_ok = (
            card.get('verdict') == 'promote'
            and card.get('submission_ready') is True
            and all((card.get('gates') or {}).values())
            and card.get('submission_slots_used') == 0
            and card.get('approved_for_weekly_slot') is False
            and card.get('safe_to_submit') is False
        )
        if card.get('verdict') != 'negative' and not promote_ok:
            errors.append(f'Run card contradicts negative publication state: {card_file.name}')
        if card_file in (canonical_card, root / 'evidence/run_card.json') and card.get('submission_ready') is not False:
            errors.append(f'Run card contradicts negative publication state: {card_file.name}')
        for key in ('submission_ready', 'approved_for_weekly_slot', 'safe_to_submit'):
            if key in card and card[key] is not False and not (promote_ok and key == 'submission_ready'):
                errors.append(f'{card_file.name}: {key} must be false')
    summary_path = root / 'docs/data/summary.json'
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text())
        if any(summary.get(key) is not False for key in ('submission_ready', 'safe_to_submit')):
            errors.append('Summary contradicts negative publication state')
    return errors


if __name__ == '__main__':
    errors = check()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: Pages links, registered TIFF/ZIP integrity and negative-state safety; not scientific clearance')
