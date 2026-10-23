"""Refresh narrow source-integrity evidence through permitted GitHub APIs.

This does not fetch the competition portal, authenticate a score or establish
that all sibling methods were inspected. Uses pinned commits and verifies Git
blob identity, then compares against the archived research bytes.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_protocol_data import write_blob

SOURCES = (
    ('drivendataorg/gems-prize-reference-solution', 'aebe92f7c8a990f0e3443451b7a825d9afd6336b',
     'README.md', 'research/upstream/official-reference-README.md', 'OFFICIAL-REFERENCE-CODE'),
    ('buffedlizard55-lab/GEMSDOE32', '780a5a534269c79adfe6d1d7d5aadead161332aa',
     'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json',
     'research/upstream/h33-best-audit.json', 'OWNER-ARTIFACT-NOT-ORGANIZER-RECEIPT'),
)


def run():
    rows = []
    for repo, commit, path, local, classification in SOURCES:
        blob = subprocess.check_output(['gh', 'api', f'repos/{repo}/contents/{path}?ref={commit}', '--jq', '.sha'], text=True).strip()
        stream = io.BytesIO()
        write_blob(repo, blob, stream)
        raw = stream.getvalue()
        archived = (ROOT / local).read_bytes()
        row = dict(url=f'https://github.com/{repo}/blob/{commit}/{path}',
                   source_class=classification, git_blob=blob,
                   retrieved_sha256=hashlib.sha256(raw).hexdigest(),
                   archive_file=local, archived_sha256=hashlib.sha256(archived).hexdigest(),
                   archive_matches_retrieved_bytes=raw == archived)
        if not row['archive_matches_retrieved_bytes']:
            raise ValueError(f'Archived source mismatch: {local}')
        if path.endswith('.json'):
            source = json.loads(raw)
            row['has_unscored_wording_in_submission_note'] = 'UNSCORED' in source['submission_note_zeros']
            row['contains_projected_leaderboard_field'] = 'predicted_leaderboard_dti' in source['holdout_metrics']
            row['is_organizer_receipt'] = False
        else:
            row['cpu_only_explicitly_supported'] = 'CPU-only' in raw.decode()
        rows.append(row)
    return dict(retrieved_utc=datetime.now(timezone.utc).isoformat(), sources=rows,
                scope='Two immutable source documents only; not a full fleet review, live leaderboard or official submission receipt.',
                live_portal_verified=False)


if __name__ == '__main__':
    result = run()
    path = ROOT / 'docs/evidence/review-source-checks.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))
