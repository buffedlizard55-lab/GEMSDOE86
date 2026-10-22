"""Fail closed on broken local links and unsafe publication of candidate files."""
from html.parser import HTMLParser
import hashlib
import json
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


def check(root=ROOT):
    root = Path(root).resolve()
    card = json.loads((root / 'docs/evidence/run-card.json').read_text())
    errors = []
    htmls = [root / 'index.html', *sorted((root / 'docs').rglob('*.html'))]
    for path in htmls:
        parser = Links(); parser.feed(path.read_text())
        for url in parser.urls:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f'{path.relative_to(root)}: broken or escaping local link {url}')
    inventory_file = root / 'docs/evidence/download-inventory.json'
    if inventory_file.is_file():
        entries = json.loads(inventory_file.read_text())['artifacts']
    elif card.get('submission_file'):
        entries = [dict(file=card['submission_file'], sha256=card['raster_sha256'],
                        status=card.get('download_status', ''), approved_for_weekly_slot=card.get('approved_for_weekly_slot'))]
    else:
        entries = []
    registered = {(root / e['file']).resolve(): e for e in entries}
    for target, entry in registered.items():
        if not target.is_relative_to(root) or not target.is_file():
            errors.append('Missing or escaping registered artifact')
        if entry.get('approved_for_weekly_slot') is not False or 'DO NOT SUBMIT' not in entry.get('status', ''):
            errors.append('Negative artifact inventory lacks explicit DO NOT SUBMIT status')
    for artifact in (root / 'docs').rglob('*'):
        if artifact.suffix.lower() not in {'.tif', '.tiff', '.zip'}:
            continue
        target = artifact.resolve() if artifact.suffix.lower() in {'.tif', '.tiff'} else artifact.with_suffix('.tif').resolve()
        entry = registered.get(target)
        if entry is None:
            errors.append(f'Unregistered downloadable raster/archive: {artifact.relative_to(root)}')
            continue
        if artifact.suffix.lower() in {'.tif', '.tiff'}:
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != entry['sha256']:
                errors.append(f'Published raster SHA differs from inventory: {artifact.name}')
        else:
            try:
                with zipfile.ZipFile(artifact) as z:
                    if z.namelist() != [target.name] or z.read(target.name) != target.read_bytes():
                        errors.append('ZIP must contain exactly the registered TIFF bytes')
            except (OSError, zipfile.BadZipFile, KeyError):
                errors.append('Invalid candidate ZIP')
    primary_card = root / 'evidence/run_card.json'
    if primary_card.is_file():
        primary = json.loads(primary_card.read_text())
        if primary.get('submission_ready') is not False or primary.get('approved_for_weekly_slot') is not False or primary.get('verdict') != 'negative':
            errors.append('Primary pipeline contradicts the mandatory literal stop')
    if card.get('submission_ready'):
        # This repo has no full scientific clearance yet. Do not let a UI boolean
        # invent a release authorization while the negative proof still applies.
        witness = card.get('correlation_overlap_vs_registry', {}).get('universal_witness', {})
        if witness.get('universal_overlap_blocker') or not card.get('raster_sha256'):
            errors.append('Submission readiness contradicts evidence')
    return errors


if __name__ == '__main__':
    errors = check()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: local HTML links and registered-download integrity and negative-state safety (not scientific clearance)')
