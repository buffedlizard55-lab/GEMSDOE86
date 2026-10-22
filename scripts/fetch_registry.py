"""Fetch hash-pinned registry/incumbent rasters for uniqueness checks only.

Sources: research/upstream/data_manifest.json (group == 'scored') plus the two
GEMSDOE32 downloads whose sha256 are pinned in research/upstream/h33-best-audit.json
and research/upstream/slot_plan.json. Bytes are verified, never modified, and
never used as prediction input -- only compared against.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'registry'
EXTRA = [
 dict(id='gemsdoe32_h33_2_b2_zeros', repo='buffedlizard55-lab/GEMSDOE32',
      ref='780a5a534269c79adfe6d1d7d5aadead161332aa',
      path='docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif',
      sha256='c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'),
 dict(id='gemsdoe32_h32d_46090_zeros', repo='buffedlizard55-lab/GEMSDOE32',
      ref='780a5a534269c79adfe6d1d7d5aadead161332aa',
      path='docs/downloads/gemsdoe32-h32d-submodular-multipysics-46090-20261004T183200Z-4de30601-zeros.tif',
      sha256='f81e26d7712d1a4a9d3d5393037b09849400c3976d1ebd40e2760a586f2adc2f'),
]
def fetch(item):
    dest = OUT / (item['id'] + '.tif')
    if not dest.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix('.partial')
        try:
            with tmp.open('wb') as f:
                subprocess.run(['gh','api',f"repos/{item['repo']}/contents/{item['path']}?ref={item['ref']}",
                                '-H','Accept: application/vnd.github.raw+json'], stdout=f, check=True)
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    ok = digest == item['sha256']
    return dict(id=item['id'], file=str(dest.relative_to(ROOT)), sha256=digest,
                sha_ok=ok, bytes=dest.stat().st_size, repo=item['repo'], path=item['path'], ref=item['ref'])
def main():
    manifest = json.loads((ROOT/'research/upstream/data_manifest.json').read_text())
    items = [dict(id=f['id'], repo=f['repo'], ref=f['ref'], path=f['path'], sha256=f['sha256'])
             for f in manifest['files'] if f.get('group')=='scored'] + EXTRA
    rows=[]
    for it in items:
        try: rows.append(fetch(it)); print(rows[-1]['id'], rows[-1]['sha_ok'], rows[-1]['bytes'], flush=True)
        except Exception as e: rows.append(dict(id=it['id'], error=repr(e))); print(it['id'],'ERROR',e, flush=True)
    (ROOT/'data/registry/index.json').write_text(json.dumps(rows,indent=2)+'\n')
    bad=[r for r in rows if not r.get('sha_ok')]
    print(f"{len(rows)-len(bad)}/{len(rows)} verified")
    return 1 if bad else 0
if __name__=='__main__': sys.exit(main())
