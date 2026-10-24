"""Build the catalogue-blind H86E feature memmap (data/work/h86e_features.npy)."""
import sys,time; sys.path[:0]=['vendor','.','src']
from pathlib import Path
from gems57 import grid
from gems86_ridf import features
t=time.time(); g=grid.load_grid('data')
n=features.build(Path('data/training_features.tif'), g.footprint, Path('data/work/h86e_features.npy'))
print(len(n), n, time.time()-t)
