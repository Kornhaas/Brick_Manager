"""Exit status contracts for the optional legacy analysis command."""

import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize("blocking_check", [None, "bandit", "tests", "black", "isort"])
def test_analysis_warnings_do_not_mask_blocking_failures(monkeypatch, blocking_check):
    script = Path(__file__).resolve().parents[2] / "scripts/pre_commit_analysis.py"
    spec = importlib.util.spec_from_file_location("pre_commit_analysis", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    analyzer = module.PreCommitAnalyzer(str(script.parent.parent))

    def warn():
        analyzer.warnings.append("Advisory finding")
        return False

    monkeypatch.setattr(analyzer, "fix_common_issues", lambda: None)
    for method in ("run_flake8", "run_pylint", "check_dependencies"):
        monkeypatch.setattr(analyzer, method, warn)
    for check, method in {
        "bandit": "run_bandit_security_check",
        "tests": "run_tests",
        "black": "format_with_black",
        "isort": "sort_imports_with_isort",
    }.items():
        monkeypatch.setattr(
            analyzer, method, lambda check=check: check != blocking_check
        )

    assert analyzer.run_all_checks() is (blocking_check is None)
    assert analyzer.warnings
