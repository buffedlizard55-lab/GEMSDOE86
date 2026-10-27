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


def test_table_explicitly_separates_estimates_from_historical_claims():
    html = focus9_summary()
    assert "Estimated leaderboard score" in html
    assert "File to download for submission" in html
    assert html.count("Not estimated — no organizer-calibrated estimate") == 9
    assert html.count("NONE approved;") == 9


def _isolated_inputs(tmp_path, monkeypatch):
    import csv
    import shutil
    import scripts.build_site as builder
    (tmp_path / "registry").mkdir()
    (tmp_path / "docs/evidence").mkdir(parents=True)
    for rel in ("registry/prior_scores.csv", "docs/evidence/focus9-forensics-20261026-rev2.json"):
        shutil.copyfile(ROOT / rel, tmp_path / rel)
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    path = tmp_path / "registry/prior_scores.csv"
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    return builder, path, rows


def test_changed_champion_cannot_inherit_old_overlap(tmp_path, monkeypatch):
    import csv
    import pytest
    builder, path, rows = _isolated_inputs(tmp_path, monkeypatch)
    row = next(r for r in rows if r["site"] == "GEMSDOE24")
    row["submission"] = "new-unmeasured-geological-method"
    row["score"] = "0.9999"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="champion changed"):
        builder.focus9_summary()


def test_same_method_different_identity_cannot_inherit_overlap(tmp_path, monkeypatch):
    import csv
    import pytest
    builder, path, rows = _isolated_inputs(tmp_path, monkeypatch)
    row = next(r for r in rows if r["site"] == "GEMSDOE32")
    row["submission"] = row["submission"].replace("e5eb6e7e", "deadbeef")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="overlap is missing or ambiguous"):
        builder.focus9_summary()
