"""Fail closed on broken local links and unsafe publication of candidate files."""
from html.parser import HTMLParser
import hashlib
import json
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
    # Also reject unlinked rasters/ZIPs accidentally staged into the public site.
    for artifact in (root / 'docs').rglob('*'):
        if artifact.suffix.lower() not in {'.tif', '.tiff', '.zip'}:
            continue
        if not card.get('submission_ready') or card.get('verdict') != 'promote':
            errors.append(f'Unapproved downloadable raster/archive: {artifact.relative_to(root)}')
        elif artifact.suffix.lower() in {'.tif', '.tiff'}:
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if digest != card.get('raster_sha256'):
                errors.append(f'Published raster SHA differs from run card: {artifact.name}')
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
    print('PASS: local HTML links and negative-state publication safety (not scientific clearance)')
