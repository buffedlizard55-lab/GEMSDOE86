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
    # Preserve a concurrent, explicitly negative research artifact, but never
    # let an unknown/modified TIFF or ZIP silently become a download.
    registered = (root / card['submission_file']).resolve() if card.get('submission_file') else None
    for artifact in (root / 'docs').rglob('*'):
        if artifact.suffix.lower() not in {'.tif', '.tiff', '.zip'}:
            continue
        is_tif = artifact.suffix.lower() in {'.tif', '.tiff'}
        expected = registered if is_tif else registered.with_suffix('.zip') if registered else None
        if registered is None or artifact.resolve() != expected:
            errors.append(f'Unregistered downloadable raster/archive: {artifact.relative_to(root)}')
            continue
        if not card.get('submission_ready'):
            if (card.get('verdict') != 'negative' or card.get('approved_for_weekly_slot') is not False
                    or 'DO NOT SUBMIT' not in card.get('download_status', '')):
                errors.append('Negative artifact lacks explicit DO NOT SUBMIT status')
        if is_tif:
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if digest != card.get('raster_sha256'):
                errors.append(f'Published raster SHA differs from run card: {artifact.name}')
        else:
            try:
                with zipfile.ZipFile(artifact) as z:
                    if z.namelist() != [registered.name] or z.read(registered.name) != registered.read_bytes():
                        errors.append('ZIP must contain exactly the registered TIFF bytes')
            except (OSError, zipfile.BadZipFile, KeyError):
                errors.append('Invalid candidate ZIP')
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
