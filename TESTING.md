# Testing Brick Manager

The suite uses pytest, a temporary SQLite database, Flask test clients, and mocked external HTTP boundaries. Run commands from the repository root through Poetry.

## Local environment and VS Code

Install the project, including its test dependencies, with:

```bash
poetry install
```

Poetry creates the environment in `.venv`. The checked-in VS Code settings use
`.venv/bin/python`, so test discovery and terminal test runs use the same Python.
After changing an already open workspace, run **Python: Select Interpreter**, choose
`.venv/bin/python`, and refresh the Test Explorer once. A rebuilt development
container installs the dependencies automatically.

## Commands

```bash
# Full configured suite with terminal, HTML, and XML coverage
poetry run pytest

# One focused test module without applying the repository-wide coverage gate
poetry run pytest --no-cov -q brick_manager/tests/test_client_api.py

# Tests that are not marked slow
poetry run pytest -m "not slow"

# Formatting and import checks
poetry run black --check brick_manager scripts
poetry run isort --check-only brick_manager scripts

# Repository quality checks without automatic fixes
poetry run python scripts/pre_commit_analysis.py --no-fix
```

The full pytest configuration is in `pytest.ini`; coverage exclusions are in `.coveragerc`. The configured global coverage floor is currently 16%. This is a minimum release gate, not a claim that every critical path has enough tests.

## Current suite state

Historical generated tests for APIs and models that no longer exist were removed instead of being hidden behind collection-time skips. The suite must not introduce broad skip lists to make the release gate green. Always report passed, failed, and skipped counts separately.

Verified full-suite baseline from 19 October 2026:

- 169 tests collected.
- 169 passed.
- 0 skipped.
- 30.05% total statement coverage.
- Known weak areas: Rebrickable synchronization, label generation, token management, and several write-heavy HTML routes.

Do not use the number of test files or collected tests as a substitute for executed behavioral coverage.

## Fixtures

The shared fixtures in `brick_manager/tests/conftest.py` provide:

- `app`: a Flask application configured with a temporary SQLite database.
- `client`: Flask HTTP test client.
- `runner`: Flask CLI runner.
- automatic table setup and teardown around tests.

The test app registers the real blueprints but avoids importing the production `app.py`, whose module-level startup also initializes logging, tables, lookup data, and scheduler jobs.

## What a regression test must prove

- Routes: status code, stable response fields or rendered contract, validation, authentication where applicable, and resulting database state.
- Services: business result plus the exact external request boundary, including method, URL, payload, timeout, and relevant failure behavior.
- Models and migrations: constraints, relationships, cascade behavior, upgrade from the previous schema, and repeat-run safety.
- File, image, cache, and label operations: deterministic temporary files, output properties, safe paths, and cleanup after failures.
- JavaScript-backed forms: both the rendered HTML/JavaScript contract and the server-side protection that remains when JavaScript is bypassed.

Avoid tests that catch every exception, contain `pass`, accept several unrelated status codes, or only call a function to increase coverage. Do not add broad collection-time skips merely to make the suite green.

## External systems

Automated tests must not call live Rebrickable or Brickognize endpoints. Mock `requests` where it is looked up by the module and include relevant timeout, authentication, malformed-response, pagination, rate-limit, and partial-batch scenarios.

## Coverage interpretation

For a focused test file, use `--no-cov` when the repository-wide threshold would make an otherwise successful narrow run fail. Before release, run the complete configured suite so the global threshold and integration behavior are still checked.

When reporting results, include:

```text
passed: <count>
failed: <count>
skipped: <count>
coverage: <percent, only when measured by a full representative run>
```
