#!/usr/bin/env python3
"""Restore and SHA-256-verify competition and public-external GeoTIFF inputs.

Why mirrors are used instead of the DrivenData data tab
-------------------------------------------------------
``https://www.drivendata.org/competitions/306/competition-doe-gems/data/``
is login-walled (redirects to ``/accounts/login``) and automated portal
scraping is disallowed by ``AGENTS.md``. Cross-repository inspection across all
92 ``buffedlizard55-lab`` repositories located two mirror families carrying the
exact same SHA-256-pinned bytes:

1. **GitHub tarball mirrors (primary, works inside egress-restricted sandboxes):**
   - ``buffedlizard55-lab/GEMSDOE`` commit ``c0c06ac82178f26b94fce3397036ef8f12a2f3a0``
     (``data/bridge/`` parts for ``training_features.tif``, ``existing_faults.tif``,
     and ``example_submission.tif`` = ``sample_submission.tif``).
   - ``buffedlizard55-lab/60GEMSDOE`` commit ``32024716f218d06a94e01464157392119c03cb15``
     (``data/external/`` public-domain USGS 3DEP / GeoDAWN derived grids).

2. **Dropbox convenience shares found in ``buffedlizard55-lab/16GEMSDOE/README.md``
   (optional ``--source dropbox`` fallback on unrestricted workstations only):**
   Personal shares (``dl=1`` direct download), NOT official DOE/NLR/USGS/DrivenData
   hosting and unreachable inside egress-restricted sandboxes. Every byte fetched
   from any mirror is verified against ``PINS`` / ``EXTERNAL_PINS`` via SHA-256 in a
   staged ``.partial`` file before publication; any hash mismatch aborts and
   deletes the staged file.

===========================  ==================================================================
training_features.tif        4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
existing_faults.tif          7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093
sample_submission.tif        2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc
===========================  ==================================================================

A hash match proves byte identity with these published mirrors; it does not
independently authenticate the organizer's original portal bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA_ROOT = ROOT / "data"
DATA = DATA_ROOT / "bridge"
CACHE = ROOT / ".cache"
EXT = CACHE / "external"

FEATURE_REF = "c0c06ac82178f26b94fce3397036ef8f12a2f3a0"   # GEMSDOE, data/bridge parts
EXT_REF = "32024716f218d06a94e01464157392119c03cb15"       # 60GEMSDOE, data/external

PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}

EXTERNAL_PINS = {
    "lidar_scarp_features_u8.tif": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
    "topo_10m_derived_100m_u8.tif": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
    "dem10_chi_100m_i16.tif": "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
    "geodawn_rad_u8.tif": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    "geodawn_extensions_u8.tif": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
}
EXTERNAL = tuple(EXTERNAL_PINS)

# Convenience links recorded in buffedlizard55-lab/16GEMSDOE/README.md (personal shares,
# NOT official DOE/NLR/USGS/DrivenData hosting; converted from dl=0 to dl=1 for direct HTTP).
DROPBOX_MIRRORS = {
    "sample_submission.tif": "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1",
    "existing_faults.tif": "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1",
    "training_features.tif": "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1",
}
DROPBOX_DOC_LINKS = {
    "GEMS_96647.pdf": "https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0",
    "Digital-elevation-model-links-JSON.pdf": "https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def stream_extract(url: str, wanted: dict[str, Path], *,
                   expected_sha256: dict[str, str] | None = None) -> None:
    """Stage a complete selection, verify it, then publish only valid bytes.

    Canonical rasters MUST supply all expected hashes. The sole unhashed caller
    restores scratch feature parts; their concatenation is separately verified
    before it becomes training_features.tif. No tar member is extracted by its
    supplied filesystem path. An absent/duplicate requested member is an error.
    """
    if not wanted:
        return
    if len({Path(p).resolve() for p in wanted.values()}) != len(wanted):
        raise ValueError("Archive targets must have distinct destinations")
    if expected_sha256 is not None and set(expected_sha256) != set(wanted):
        raise ValueError("Expected hashes must cover exactly the requested archive members")
    staged: list[tuple[Path, Path]] = []
    seen = set()
    req = urllib.request.Request(url, headers={"User-Agent": "gems86-restore"})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                for member in tf:
                    rel = member.name.split("/", 1)[-1]
                    if rel not in wanted:
                        continue
                    if rel in seen or not member.isfile():
                        raise ValueError(f"Duplicate or non-file requested archive member: {rel}")
                    seen.add(rel)
                    dst = Path(wanted[rel])
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    # Unique temporary names avoid colliding with another
                    # read-only restoration running from the same prompt.
                    with tempfile.NamedTemporaryFile(dir=dst.parent, prefix=dst.name + ".",
                                                     suffix=".partial", delete=False) as out:
                        tmp = Path(out.name)
                        staged.append((tmp, dst))
                        payload = tf.extractfile(member)
                        if payload is None:
                            raise RuntimeError(f"tar member {rel} had no payload")
                        with payload:
                            shutil.copyfileobj(payload, out)
                    if expected_sha256 is not None and sha256(tmp) != expected_sha256[rel]:
                        raise ValueError(f"SHA-256 mismatch before archive publication: {rel}")
        missing = set(wanted) - seen
        if missing:
            raise ValueError(f"Missing requested archive members: {sorted(missing)}")
        # Every selected member passed before ANY target is replaced. A failed
        # download/hash/selection leaves all pre-existing targets untouched.
        for tmp, dst in staged:
            tmp.replace(dst)
    finally:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)


def download_verified(url: str, dst: Path, expected_sha256: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".partial")
    req = urllib.request.Request(url, headers={"User-Agent": "gems86-restore"})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp, tmp.open("wb") as out:
            shutil.copyfileobj(resp, out)
        got = sha256(tmp)
        if got != expected_sha256:
            raise ValueError(f"SHA-256 mismatch from {url}: {got} != {expected_sha256}")
        tmp.replace(dst)
    finally:
        tmp.unlink(missing_ok=True)


def verify_pin(path: Path, name: str, expected_sha256: str) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing {path}; run without --verify-only")
    got = sha256(path)
    if got != expected_sha256:
        path.unlink(missing_ok=True)
        raise SystemExit(f"SHA-256 mismatch for {name}: {got} != {expected_sha256}")
    return {"sha256": got, "bytes": path.stat().st_size, "verified": True}


def sync_grid_root(bridge_dir: Path, data_root: Path, names: tuple[str, ...]) -> None:
    """Ensure ``data/<name>`` matches ``data/bridge/<name>`` for gems57.grid.load_grid."""
    data_root.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = bridge_dir / name
        dst = data_root / name
        if not src.is_file() or src.resolve() == dst.resolve():
            continue
        if dst.is_file() and sha256(dst) == PINS[name]:
            continue
        tmp = dst.with_suffix(dst.suffix + ".partial")
        try:
            shutil.copyfile(src, tmp)
            if sha256(tmp) != PINS[name]:
                raise ValueError(f"Grid copy integrity mismatch for {name}")
            tmp.replace(dst)
        finally:
            tmp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default=str(DATA), help="Target directory (default: data/bridge)")
    ap.add_argument("--protocol-only", action="store_true",
                    help="Restore only existing_faults.tif and sample_submission.tif (skip 419 MB training_features.tif)")
    ap.add_argument("--include-registry", action="store_true",
                    help="Also restore the pinned historical witness (data/registry/dense-witness.tif)")
    ap.add_argument("--with-external", action="store_true",
                    help="Also restore and SHA-256-verify the 5 external USGS/GeoDAWN derived grids")
    ap.add_argument("--source", choices=("github", "dropbox"), default="github",
                    help="Mirror source for missing core rasters (default: github codeload; dropbox is workstation-only)")
    ap.add_argument("--verify-only", action="store_true",
                    help="Verify existing files on disk against SHA-256 pins without downloading")
    ap.add_argument("--write-receipt", action="store_true",
                    help="Refresh evidence/data_restore_receipt.json after full core+external verification")
    a = ap.parse_args(argv)
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(exist_ok=True)

    active_pins = {k: v for k, v in PINS.items()
                   if not (a.protocol_only and k == "training_features.tif")}
    receipt: dict[str, dict] = {}
    need = {n: p for n, p in active_pins.items()
            if not (dest / n).is_file() or sha256(dest / n) != p}
    if need and not a.verify_only:
        if a.source == "dropbox":
            for name, expected in need.items():
                download_verified(DROPBOX_MIRRORS[name], dest / name, expected)
        else:
            alias = {"sample_submission.tif": "example_submission.tif"}
            small = {f"data/bridge/{alias.get(n, n)}": dest / n
                     for n in need if n != "training_features.tif"}
            if small:
                stream_extract(f"https://codeload.github.com/buffedlizard55-lab/GEMSDOE/tar.gz/{FEATURE_REF}", small,
                               expected_sha256={rel: PINS[path.name] for rel, path in small.items()})
            if "training_features.tif" in need:
                parts = {f"data/bridge/gems-geodawn-numerical-features.tif.part-00{i}":
                         CACHE / f"feat-part-{i}" for i in range(5)}
                tmp_feat = (dest / "training_features.tif").with_suffix(".tif.partial")
                try:
                    stream_extract(f"https://codeload.github.com/buffedlizard55-lab/GEMSDOE/tar.gz/{FEATURE_REF}", parts)
                    with tmp_feat.open("wb") as out:
                        for i in range(5):
                            p = CACHE / f"feat-part-{i}"
                            if not p.is_file():
                                raise RuntimeError(f"missing extracted part {p}")
                            with p.open("rb") as f:
                                shutil.copyfileobj(f, out)
                            p.unlink()
                    if sha256(tmp_feat) != PINS["training_features.tif"]:
                        raise SystemExit("SHA-256 mismatch reassembling training_features.tif")
                    tmp_feat.replace(dest / "training_features.tif")
                finally:
                    tmp_feat.unlink(missing_ok=True)
                    for i in range(5):
                        (CACHE / f"feat-part-{i}").unlink(missing_ok=True)

    for name, pin in active_pins.items():
        receipt[name] = verify_pin(dest / name, name, pin)

    if dest.resolve() == DATA.resolve() and not a.verify_only:
        sync_grid_root(dest, DATA_ROOT, tuple(active_pins))

    if a.include_registry and not a.verify_only:
        from scripts.restore_protocol_data import restore_registry_witness
        witness_path = restore_registry_witness()
        receipt["registry_witness"] = {"path": str(witness_path.relative_to(ROOT)), "verified": True}

    if a.with_external:
        wanted = {f"data/external/{n}": EXT / n for n in EXTERNAL}
        missing = {k: v for k, v in wanted.items()
                   if not v.is_file() or sha256(v) != EXTERNAL_PINS[v.name]}
        if missing and not a.verify_only:
            stream_extract(f"https://codeload.github.com/buffedlizard55-lab/60GEMSDOE/tar.gz/{EXT_REF}", missing,
                           expected_sha256={rel: EXTERNAL_PINS[path.name] for rel, path in missing.items()})
        receipt["external"] = {
            n: verify_pin(EXT / n, n, EXTERNAL_PINS[n]) for n in EXTERNAL
        }

    if a.write_receipt or (not a.protocol_only and a.with_external and not a.include_registry):
        out = ROOT / "evidence" / "data_restore_receipt.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps({
            "evidence_class": "DATA-MEASUREMENT",
            "pins_source": "GEMSDOE80/scripts/restore_data.py CORE_PINS; GEMSDOE32/data/restore_receipt.json",
            "files": {k: v for k, v in receipt.items() if k != "registry_witness"},
        }, indent=2) + "\n")
    print(json.dumps({"status": "OK", "files": list(receipt)}, indent=2))


if __name__ == "__main__":
    main()
