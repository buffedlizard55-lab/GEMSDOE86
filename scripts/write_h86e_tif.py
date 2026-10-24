"""Serialize H86E final dots with the shared fail-closed writer (gems57.submission_writer)."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from gems57 import grid, submission_writer
NAME = 'gems86-h86e-ridf-hgbthin-37654dots-20261024-zeros'
NOTE = 'H86E RIDF catalogue-blind HGB + 2.8px disc thinning, collar>2px; HOLDOUT NEGATIVE vs R0 foldfair - do not submit'
OUT = ROOT / 'releases/h86e-NEGATIVE-DO-NOT-SUBMIT' / f'{NAME}.tif'
def main():
    # Historical negative artifacts are archived, not permission to regenerate a
    # duplicate. The owner's literal stop still governs any fresh serialization.
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    g = grid.load_grid(ROOT / 'data')
    dots = np.load(ROOT / 'data/work/h86e_final_dots.npy')
    pred = np.where(dots & g.footprint, 1.0, 0.0).astype(np.float32)
    assert len(NOTE) <= 140, len(NOTE)
    rec = submission_writer.write_submission(OUT, pred, ROOT / 'data/sample_submission.tif', g.footprint,
            note=NOTE, name=NAME, catalogue=g.catalogue,
            metadata=dict(lane='H86E-RIDF', verdict='negative', evidence='docs/evidence/h86e-ridf-run-card.json'))
    print(json.dumps({k: rec[k] for k in ('file', 'sha256', 'bytes', 'note_chars', 'zip_sha256', 'approved_for_weekly_slot')}, indent=1))
    print(json.dumps(rec['validator'], indent=1)[:1500])


if __name__ == '__main__':
    main()
