import subprocess

import pytest

from scripts import review_repository as review


def test_plan_reuses_existing_tools():
    commands = review.plan("python")
    assert len(commands) == 6
    assert commands[0][1] == ["python", "scripts/audit_release.py"]
    assert all("--measure-registry" not in command for _, command in commands)
    assert commands[1][1] == ["python", "-m", "pytest", "-q"]


@pytest.mark.parametrize("failure", [False, True])
def test_software_pass_never_authorizes_submission(monkeypatch, tmp_path, failure):
    calls = []

    def check(name, command, root, timeout):
        calls.append(name)
        return dict(name=name, status="FAIL" if failure and len(calls) == 1 else "PASS")

    monkeypatch.setattr(review, "run_check", check)
    card = review.review(tmp_path)
    assert len(calls) == 6  # failures do not skip later review passes
    assert card["software_review_passed"] is not failure
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["holdout_dti"]["value"] is None
    assert card["raster_sha256"] is None
    assert card["verdict"] == "negative"


@pytest.mark.parametrize("mode", ["timeout", "missing", "nonzero"])
def test_subprocess_failures_are_recorded(monkeypatch, tmp_path, mode):
    def run(*args, **kwargs):
        if mode == "timeout":
            raise subprocess.TimeoutExpired(args[0], 1, output=b"partial")
        if mode == "missing":
            raise OSError("unavailable")
        return subprocess.CompletedProcess(args[0], 7, b"out", b"err")

    monkeypatch.setattr(review.subprocess, "run", run)
    result = review.run_check("test", ["tool"], tmp_path, 1)
    assert result["status"] == {"timeout": "TIMEOUT", "missing": "ERROR", "nonzero": "FAIL"}[mode]
    assert len(result["stdout_sha256"]) == 64


def test_report_cannot_overwrite_readme():
    with pytest.raises(SystemExit) as exc:
        review.main(["--output", str(review.ROOT / "README.md")])
    assert exc.value.code == 2


def test_timeout_must_be_positive():
    with pytest.raises(SystemExit) as exc:
        review.main(["--timeout", "0"])
    assert exc.value.code == 2
