import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

BRIDGE = ROOT / "data" / "bridge"
FEATURES = ROOT / ".cache" / "data" / "training_features.tif"
