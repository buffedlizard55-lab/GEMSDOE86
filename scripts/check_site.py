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
        if entry.get('approved_for_weekly_slot') is not False or entry.get('status') != 'DO NOT SUBMIT':
            raise ValueError('Negative inventory requires exact DO NOT SUBMIT status and false slot approval')
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
    for card_file in (root / 'docs/evidence/run-card.json', root / 'evidence/run_card.json'):
        if not card_file.is_file():
            if card_file == root / 'docs/evidence/run-card.json':
                errors.append('Missing canonical run card')
            continue
        card = json.loads(card_file.read_text())
        if card.get('submission_ready') is not False or card.get('verdict') != 'negative':
            errors.append(f'Run card contradicts negative publication state: {card_file.name}')
        for key in ('approved_for_weekly_slot', 'safe_to_submit'):
            if key in card and card[key] is not False:
                errors.append(f'{card_file.name}: {key} must be false')
    summary_path = root / 'docs/data/summary.json'
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text())
        if any(summary.get(key) is not False for key in ('submission_ready', 'safe_to_submit')):
            errors.append('Summary contradicts negative publication state')
    legacy_page = root / 'docs/submit.html'
    if legacy_page.is_file():
        html = legacy_page.read_text(encoding='utf-8')
        if ('DO NOT SUBMIT' not in html or 'READY TO DOWNLOAD' in html
                or 'raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE86/main/submission/' in html):
            errors.append('Legacy SPT page contains an unsafe release claim or direct upload link')
        card_path = root / 'docs/evidence/spt-run-card.json'
        try:
            card = json.loads(card_path.read_text())
            if (card.get('verdict') != 'negative' or card.get('submission_ready') is not False
                    or card.get('approved_for_weekly_slot') is not False
                    or card.get('safe_to_submit') is not False
                    or card.get('download_url') is not None):
                errors.append('Legacy SPT run card contradicts negative publication state')
        except (OSError, ValueError, TypeError):
            errors.append('Missing or invalid legacy SPT negative run card')
    return errors


if __name__ == '__main__':
    errors = check()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: Pages links, registered TIFF/ZIP integrity and negative-state safety; not scientific clearance')
