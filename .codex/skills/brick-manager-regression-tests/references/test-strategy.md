# Test Strategy

## Current harness

- Pytest configuration: `pytest.ini`; tests live in `brick_manager/tests/`.
- `conftest.py` creates a temporary SQLite database, registers blueprints, exposes `app`, `client`, and `runner`, and recreates tables around tests.
- `BRICK_MANAGER_CLIENT_API_KEY` is set to `test-client-api-key` in the test app.
- Many historical generated classes are marked skipped through `LEGACY_TEST_CLASSES` because they target removed APIs. They are not evidence of current coverage.
- The configured global coverage floor is 16%, which is a release floor, not an adequacy target for changed behavior.

## Useful commands

```bash
# One test or test file
poetry run pytest -q brick_manager/tests/test_client_api.py -k quantity

# Current tests without the slow marker
poetry run pytest -q -m "not slow"

# Full configured suite and coverage
poetry run pytest -q
```

Prefer selecting by file/node or meaningful marker. Do not use `--disable-warnings` to conceal warnings relevant to the changed code.

## Patterns by layer

Route/API tests:

- Authenticate where required.
- Assert status, exact stable fields, content type, and database state.
- Exercise invalid JSON/types, bounds, missing entities, and authorization.

Service tests:

- Mock `requests` at the module where it is looked up.
- Model pagination and partial batches faithfully.
- Assert commits or rollbacks and structured error results.

Model/data tests:

- Assert constraints and relationship/cascade behavior through SQLAlchemy.
- For migrations, start from the previous schema rather than `db.create_all()` on the new models.

File/label/cache tests:

- Use a temporary directory and small deterministic images.
- Assert file signature, dimensions or PDF properties, sanitized paths, and cleanup after failure.

Frontend changes:

- When no browser harness exists, test server-rendered contract plus any pure JavaScript logic that can be isolated. Do not claim end-to-end UI coverage from a route-only test.

## Baseline interpretation

The October 2026 diagnostic run collected 414 items, with 156 passed, 258 skipped, and 27.35% statement coverage. Sync and many write-heavy route modules were near 10–25%. Re-run before citing numbers; prioritize risk and changed behavior over gaming aggregate coverage.
