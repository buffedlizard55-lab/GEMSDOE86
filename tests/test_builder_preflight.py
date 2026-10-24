"""Historical variant commands cannot bypass the current literal protocol stop.

These are orchestration safety tests, not geological experiments. No surface,
fit, placement, cache or TIFF is constructed. Pure numerical helpers stay usable.
"""
import ast
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import protocol_preflight

ROOT = Path(__file__).resolve().parents[1]
BUILDERS = """
build_axis_variants build_concentration5_axis build_concentration_sign
build_mass_axis build_mass_econ build_r0_prune build_r0_snap build_r0_spacing
build_r0_trackb build_snap_variants build_spt build_submission build_xfleet
gen_tip_final h86b_features h86c_features h86d_features prepare_h86_fvmb_data
prune_collar run_concentration_10km run_concentration_5km
run_concentration_dose run_concentration_dose_rungs run_concentration_pediment
run_concentration_surfext run_h86_fvmb_pipeline run_h86_wvb run_lane86
run_lane86b run_lane86c run_lane86d run_prune_ladder run_relief_axis
run_relief_source run_snap_axis run_spacing_axis run_trackb_axis
""".split()
IMPORTED_ORCHESTRATORS = [
    ("experiment", "run", ("full",)),
    ("run_experiment", "run", ()),
    ("run_lane", "holdout", ()),
    ("run_h86", "build_surface", ()),
    ("run_h86", "stage_canary", ()),
    ("run_h86", "run_holdout", (38000, "test")),
    ("run_h86", "stage_sgmc", ()),
    ("run_h86", "stage_final", (38000, "test")),
]


@pytest.mark.parametrize("module_name,function,args", [
    *[(name, "main", ()) for name in BUILDERS], *IMPORTED_ORCHESTRATORS,
])
@pytest.mark.parametrize("failure", ["literal_overlap", "missing_input"])
def test_stops_before_first_work_even_when_imported(monkeypatch, module_name, function, args, failure):
    module = importlib.import_module("scripts." + module_name)
    calls = []

    def stop():
        calls.append("preflight")
        if failure == "missing_input":
            raise FileNotFoundError("missing pinned witness")
        raise RuntimeError("STOP_LITERAL_OVERLAP_UNSATISFIABLE")

    monkeypatch.setattr(protocol_preflight, "require_feasible", stop)
    expected = FileNotFoundError if failure == "missing_input" else RuntimeError
    # An invalid CLI prevents accidental continuation to argparse or IO from passing.
    monkeypatch.setattr("sys.argv", [module_name, "--not-a-real-option"])
    with pytest.raises(expected, match="missing pinned witness|STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
        getattr(module, function)(*args)
    assert calls == ["preflight"]


@pytest.mark.parametrize("name", BUILDERS)
def test_root_import_and_guard_precede_parser_io_and_placement(name):
    """Direct `python scripts/foo.py` must also find the scripts package."""
    tree = ast.parse((ROOT / "scripts" / (name + ".py")).read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    body = main.body
    if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    assert ast.unparse(body[0]) == "sys.path.insert(0, str(ROOT))"
    assert isinstance(body[1], ast.ImportFrom)
    assert body[1].module == "scripts.protocol_preflight"
    assert ast.unparse(body[2]) == "require_feasible()"
    assert not any(a.arg in {"skip_literal_preflight", "force", "bypass"}
                   for a in main.args.args + main.args.kwonlyargs)


@pytest.mark.parametrize("name", ["build_spt.py", "build_xfleet.py"])
def test_concurrent_candidate_builders_fail_before_any_feature_load(name):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT, env=env,
        text=True, capture_output=True, timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "training_features.tif" not in output
    assert "STOP_LITERAL_OVERLAP_UNSATISFIABLE" in output or "sample_submission.tif" in output
