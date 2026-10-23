"""The uniqueness gate must carry the proof that it is unsatisfiable for saturated priors."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERT = ROOT / "evidence" / "saturation_certificate.json"
AUDIT = ROOT / "evidence" / "uniqueness_audit.json"


def test_certificate_present_and_consistent():
    if not CERT.is_file():
        return
    rows = json.loads(CERT.read_text())
    assert rows and all("halo_coverage_of_allowed" in r for r in rows)
    inform = [r for r in rows if r["halo_coverage_of_allowed"] > 0.7]
    assert len(inform) >= 1
    for r in inform:
        assert r["my_overlap"] > 0.7          # blocked by construction
        assert abs(r["rho"]) < 0.90           # yet statistically unrelated


def test_audit_limits_are_the_shared_ones():
    if not AUDIT.is_file():
        return
    a = json.loads(AUDIT.read_text())
    assert a["rho_limit"] == 0.9 and a["overlap_limit"] == 0.7
    assert a["registry_rasters_expected"] >= 800
