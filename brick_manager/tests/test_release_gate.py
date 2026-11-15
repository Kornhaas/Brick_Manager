"""A published container must depend on an actual, blocking test invocation."""

from pathlib import Path

import yaml


def test_docker_publication_is_gated_by_executable_pytest():
    workflow = yaml.safe_load(
        (Path(__file__).parents[2] / ".github/workflows/docker-image.yml").read_text()
    )
    jobs = workflow["jobs"]
    assert "test" in jobs["build-and-push"]["needs"]
    commands = [
        step
        for step in jobs["test"]["steps"]
        if any(
            line.strip().startswith("poetry run pytest ")
            for line in step.get("run", "").splitlines()
        )
    ]
    assert commands, (
        "Docker release test job must execute pytest, not leave it commented out."
    )
    for step in commands:
        assert step.get("continue-on-error", False) is False
        assert not step.get("if"), "Release tests must not be conditionally skipped."
        assert "|| true" not in step["run"]
