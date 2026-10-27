"""Focus-9 executive summary must use score and registry evidence, not stale prose."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_site import focus9_summary  # noqa: E402


def test_focus9_highest_score_per_site_and_measured_uniqueness():
    html = focus9_summary()
    # H36-1 (0.2710) is the highest GEMSDOE28 claim; the previous renderer
    # incorrectly surfaced H27-4 (0.2708) in the per-site table.
    assert "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan" in html
    assert "0.2710</strong> OWNER-REPORTED" in html
    assert "0.2708</strong> OWNER-REPORTED" in html  # GEMSDOE31 remains H27-4
    assert "95.5% within 3 px of GEMSDOE32 H33" in html
    assert "Unique under 70% rule?" in html
    assert html.count("<strong>NO</strong> — exceeds the 70% overlap stop") == 9
    assert "ORGANIZER-CONFIRMED" not in html
    assert "DO NOT RESUBMIT" in html
