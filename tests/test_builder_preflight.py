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
build_gems86_gapres build_gems86_swcon build_h86e_features build_mass_axis build_mass_econ build_r0_prune build_r0_snap build_r0_spacing
build_r0_trackb build_snap_variants build_spt build_submission build_xfleet
experiment finalize_h86e gen_tip_final generate_unique_submission build_unique_submission h86b_features h86c_features h86d_features
prepare_h86_fvmb_data prune_collar run_concentration_10km run_concentration_5km
run_concentration_dose run_concentration_dose_rungs run_concentration_pediment run_h86k
run_concentration_surfext run_experiment run_h86 run_h86_fvmb_pipeline
run_h86_wvb run_h86e run_h86e_mmt run_h86e_ridf run_h86f_ewcs run_h86f_gzzd run_h86f_pcc run_h86g_edti run_h86h_pstd run_h86i_hvfd run_h86i_ksad run_h86i_rksc run_h86i_rlms run_h86i_sacd run_h86j_csgd run_h86j_mcsp run_h86j_tvhs run_h86k_stdp run_h86l_fmc run_h86m_bmgs run_h86m_pfte run_lane run_lane86 run_lane86b run_lane86c run_lane86d
run_prune_ladder run_relief_axis run_relief_source run_snap_axis
run_spacing_axis run_trackb_axis write_h86e_tif
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


BYPASS_CLAIMS = (
    "does not call protocol_preflight",
    "does not call require_feasible",
    "do not call require_feasible",
    "no preflight",
    "without preflight",
    "skips preflight",
    "bypasses preflight",
    "is not gated",
    "stays ungated",
)

# A sentence carrying one of these markers documents a *revoked* bypass rather
# than asserting a live one, so it must not trip the test. Without this the test
# would forbid the very history that makes the guard auditable.
REVOCATION_MARKERS = (
    "revoked", "superseded", "no longer", "earlier revision", "an earlier",
    "has since", "was removed", "now calls", "now call", "not a protocol exemption",
)


def _sentences(text: str) -> list[str]:
    """Split prose on sentence boundaries, keeping the delimiter out."""
    import re
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


@pytest.mark.parametrize("name", BUILDERS)
def test_gated_builder_docstring_does_not_claim_a_preflight_bypass(name):
    """Prose must not contradict the enforced guard (IR-86-SPT-02 defect class).

    ``generate_unique_submission.py`` and ``run_h86e.py`` each shipped a
    docstring asserting the script "does NOT call
    protocol_preflight.require_feasible()" while ``main()`` did call it -- the
    misrepresented-prose-vs-code defect that revoked PR #60's SPT candidate
    (IR-86-SPT-02) and PR #80's FAULTHALO (IR-86-FAULTHALO-01). Every builder in
    BUILDERS is pinned by the tests above to call ``require_feasible()``, so a
    docstring *asserting* a live bypass is always stale.

    Sentence-scoped, skipping sentences that mark the bypass as revoked, so
    documenting the history stays possible (IR-86-PROSE-CODE-01).
    """
    text = (ROOT / "scripts" / (name + ".py")).read_text()
    docstring = ast.get_docstring(ast.parse(text)) or ""
    offending = []
    for sentence in _sentences(docstring):
        lowered = sentence.lower()
        if any(marker in lowered for marker in REVOCATION_MARKERS):
            continue
        claims = [c for c in BYPASS_CLAIMS if c in lowered]
        if claims:
            offending.append((sentence[:120], claims))
    assert not offending, (
        f"{name}.py docstring asserts a live preflight bypass {offending} but main() "
        f"is required to call require_feasible(); fix the prose, never the guard. "
        f"If the sentence documents a revoked bypass, mark it with one of "
        f"{REVOCATION_MARKERS}."
    )


@pytest.mark.parametrize("name", [
    "build_spt.py",
    "build_xfleet.py",
    "build_gems86_swcon.py",
    "generate_unique_submission.py",
    "build_gems86_gapres.py",
    "build_unique_submission.py",
    "build_h86e_features.py",
    "run_h86e_ridf.py",
    "run_h86e_mmt.py",
    "run_h86f_pcc.py",
    "run_h86f_gzzd.py",
    "run_h86f_ewcs.py",
    "run_h86i_ksad.py",
    "run_h86j_tvhs.py",
    "run_h86j_mcsp.py",
    "run_h86k.py",
    "run_h86k_stdp.py",
])
def test_concurrent_candidate_builders_fail_before_any_feature_load(name):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    args = [sys.executable, str(ROOT / "scripts" / name)]
    if name == "build_unique_submission.py":
        args.extend(["--skip-holdout", "--skip-registry"])
    result = subprocess.run(
        args, cwd=ROOT, env=env, text=True, capture_output=True, timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "training_features.tif" not in output
    assert "STOP_LITERAL_OVERLAP_UNSATISFIABLE" in output or "sample_submission.tif" in output


@pytest.mark.parametrize("module_name", [
    "h86e_comparator",
    "h86e_fleet_strata",
    "h86e_instrument_check",
    "h86f_forensics",
])
def test_diagnostic_scripts_do_not_execute_io_on_import(module_name):
    module = importlib.import_module("scripts." + module_name)
    assert callable(getattr(module, "main", None))

