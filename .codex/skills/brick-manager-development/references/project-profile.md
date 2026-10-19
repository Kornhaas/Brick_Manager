# Project Profile

## Runtime and layout

- Python `^3.11`; Poetry manages dependencies. The current environment may select Python 3.12.
- Flask app: `brick_manager/app.py`. It constructs a module-level app, registers blueprints, creates tables, starts APScheduler jobs, and loads lookup data during import.
- Data model: `brick_manager/models.py`, Flask-SQLAlchemy, SQLite, Flask-Migrate dependency present.
- HTTP layer: `brick_manager/routes/`; reusable logic and external clients: `brick_manager/services/`.
- UI: Jinja templates plus vanilla JavaScript and CSS under `brick_manager/templates/` and `brick_manager/static/`.
- Runtime files may live under `/app/data` in Docker or project-local directories during development.

Importing `app.py` has side effects. Prefer the isolated test app in `brick_manager/tests/conftest.py` for route tests unless the behavior under test specifically concerns application startup or scheduling.

## Verification

Focused test:

```bash
poetry run pytest -q brick_manager/tests/test_client_api.py
```

Full suite:

```bash
poetry run pytest -q
```

Non-mutating quality checks:

```bash
poetry run python scripts/pre_commit_analysis.py --no-fix
```

Ruff is the formatter and fast lint baseline for changed files. BasedPyright uses the top-level `brick_manager/` import layout and checks production code in basic mode. Use the Make targets below when their concern is relevant:

```bash
make ruff       # Ruff lint and formatting checks
make typecheck  # BasedPyright
make audit      # known vulnerable dependencies
make dead-code  # Vulture candidates; review Flask routes before removal
```

Formatting intentionally changes files; use it only when authorized by the implementation task:

```bash
poetry run black brick_manager scripts
poetry run isort brick_manager scripts
```

The verified 19 October 2026 baseline collected 169 tests: 169 passed and 0 were skipped, with 30.05% total statement coverage. Re-run before citing these numbers in a later report.

## Change mapping

- Model or persisted-field change: inspect all queries, serializers, imports, templates, and migration needs; use `$brick-manager-data-change`.
- Rebrickable, Brickognize, token, cache-download, or desktop API change: use `$brick-manager-sync-contracts`.
- Label change: verify image generation, PDF output, filesystem isolation, and failure cleanup.
- Route/UI change: verify success, malformed input, missing record, and template/JavaScript field compatibility.
- Scheduler/startup change: verify repeated imports, application context, duplicate jobs, and shutdown behavior.

## Known documentation drift

`database_schema.md` and `TESTING.md` were reconciled on 19 October 2026. Keep them current, while continuing to confirm schema and coverage claims against models, migrations, fixtures, and actual test runs.
