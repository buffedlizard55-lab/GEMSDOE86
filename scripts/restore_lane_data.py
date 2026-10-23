"""Restore hash-pinned mirror files needed by lane H86 (see data_manifest.json). Mirror integrity != organizer authentication."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WANT={'training_features','existing_faults','sample_submission','ext_geodawn_rad_u8','ext_geodawn_extensions_u8','ext_derived_sgmc_faults_100m_u8'}
WANT |= {e['id'] for e in json.loads((ROOT/'research/upstream/data_manifest.json').read_text())['files'] if e['group']=='scored'}
def main():
    man=json.loads((ROOT/'research/upstream/data_manifest.json').read_text())
    out=[]
    for e in man['files']:
        if e['id'] not in WANT: continue
        dest=ROOT/'data'/e['dest']; dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            tmp=dest.with_suffix(dest.suffix+'.partial')
            try:
                with tmp.open('wb') as f:
                    for part in e.get('parts') or [e['path']]:
                        subprocess.run(['gh','api',f"repos/{e['repo']}/contents/{part}?ref={e['ref']}",'-H','Accept: application/vnd.github.raw+json'],stdout=f,check=True)
                tmp.replace(dest)
            finally: tmp.unlink(missing_ok=True)
        h=hashlib.sha256(dest.read_bytes()).hexdigest()
        ok = h==e['sha256'] and dest.stat().st_size==e['bytes']
        print(e['id'], dest.stat().st_size, h[:12], 'OK' if ok else 'MISMATCH', flush=True)
        if not ok: sys.exit(1)
        out.append(dict(id=e['id'],sha256=h,bytes=dest.stat().st_size,organizer_authenticated=False))
    (ROOT/'docs/evidence/lane_data_restore.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__': main()
