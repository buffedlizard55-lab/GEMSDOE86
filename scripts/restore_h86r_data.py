"""Session restore driver (H86R): hash-pinned mirrors via repo restore helpers."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_protocol_data import write_path

WANT = {"training_features", "ext_derived_sgmc_faults_100m_u8", "ext_geodawn_rad_u8",
        "scored_h19_5", "scored_h19_4", "scored_h16_1"}
man = json.loads((ROOT / "research/upstream/data_manifest.json").read_text())
out = []
for e in man["files"]:
    if e["id"] not in WANT:
        continue
    dest = ROOT / "data" / e["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        tmp = dest.with_suffix(dest.suffix + ".partial")
        try:
            with tmp.open("wb") as f:
                for part in e.get("parts") or [e["path"]]:
                    print("fetch", e["id"], part, flush=True)
                    write_path(e["repo"], e["ref"], part, f)
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    h = hashlib.sha256(dest.read_bytes()).hexdigest()
    ok = h == e["sha256"] and dest.stat().st_size == e["bytes"]
    print(e["id"], dest.stat().st_size, h[:16], "OK" if ok else "MISMATCH", flush=True)
    if not ok:
        sys.exit(1)
    out.append(dict(id=e["id"], dest=e["dest"], sha256=h, bytes=dest.stat().st_size))
(ROOT / ".cache_h86r_restore.json").write_text(json.dumps(out, indent=2) + "\n")
print("DONE", len(out))
