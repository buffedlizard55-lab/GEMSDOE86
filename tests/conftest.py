import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "vendor" / "template66")]

BRIDGE = ROOT / "data" / "bridge"
FEATURES = ROOT / ".cache" / "data" / "training_features.tif"
