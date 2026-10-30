import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[2] / "run_tests.py"
SPEC = importlib.util.spec_from_file_location("repository_run_tests", SCRIPT_PATH)
assert SPEC and SPEC.loader
run_tests = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_tests)


def test_coverage_command_uses_active_python_interpreter(monkeypatch):
    captured = {}

    def capture(command, description):
        captured["command"] = command
        captured["description"] = description
        return True

    monkeypatch.setattr(sys, "argv", ["run_tests.py", "coverage"])
    monkeypatch.setattr(run_tests, "run_command", capture)

    assert run_tests.main()
    assert captured == {
        "command": [sys.executable, "-m", "coverage", "report"],
        "description": "Coverage Report",
    }


def test_pytest_command_uses_only_validated_cli_options(monkeypatch):
    commands = []
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_tests.py", "quick", "--verbose", "--fail-fast", "--no-coverage"],
    )
    monkeypatch.setattr(
        run_tests,
        "run_command",
        lambda command, description: commands.append((command, description)) or True,
    )

    run_tests.main()

    assert commands == [
        (
            [
                sys.executable,
                "-m",
                "pytest",
                "-v",
                "-x",
                "-m",
                "not slow",
                "brick_manager/tests/",
            ],
            "Running quick tests",
        )
    ]
