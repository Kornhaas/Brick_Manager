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


def test_runtime_security_packages_are_refreshed_on_every_ci_build():
    root = Path(__file__).parents[2]
    dockerfile = (root / "Dockerfile").read_text()
    runtime = dockerfile.split(" AS runtime", 1)[1]
    assert "apk upgrade --no-cache" in runtime
    workflow = yaml.safe_load((root / ".github/workflows/docker-image.yml").read_text())
    builds = [
        step
        for step in workflow["jobs"]["build-and-push"]["steps"]
        if step.get("uses", "").startswith("docker/build-push-action@")
    ]
    assert len(builds) == 1
    assert builds[0]["with"]["pull"] is True
    assert "runtime" in builds[0]["with"]["no-cache-filters"].split(",")


def test_vulnerability_scan_fails_workflow_and_always_uploads_findings():
    workflow = yaml.safe_load(
        (Path(__file__).parents[2] / ".github/workflows/docker-image.yml").read_text()
    )
    steps = workflow["jobs"]["security-scan"]["steps"]
    scan = next(
        step
        for step in steps
        if step.get("uses", "").startswith("aquasecurity/trivy-action@")
    )
    assert str(scan["with"]["exit-code"]) == "1"
    assert set(scan["with"]["severity"].split(",")) == {
        "UNKNOWN",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
    assert str(scan["with"]["ignore-unfixed"]).lower() == "false"
    assert not scan.get("continue-on-error", False)
    upload = next(
        step
        for step in steps
        if step.get("uses", "").startswith("github/codeql-action/upload-sarif@")
    )
    assert "always()" in upload["if"]
