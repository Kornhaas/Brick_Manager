---
name: brick-manager-regression-tests
description: Add, repair, or review Brick Manager pytest coverage for bugs, routes, services, models, integrations, and data changes. Use for test-focused work or whenever a regression must be reproduced and prevented with meaningful assertions.
---

# Brick Manager Regression Tests

Create tests that fail for the unwanted behavior and prove the intended observable contract.

1. Read the implementation, its callers, and nearby current tests. Check `LEGACY_TEST_CLASSES` in `brick_manager/tests/conftest.py`; do not copy obsolete generated tests or silently add new skips.
2. For a bugfix, reproduce the bug with a focused failing test before or alongside the fix. Assert response payloads, persisted state, generated artifact properties, or outbound request contracts rather than only status codes or lack of exceptions.
3. Use the shared Flask app, client, and database fixtures when suitable. Keep database rows minimal and satisfy real foreign keys. Isolate filesystem output with temporary paths.
4. Mock at the network/process boundary, not the business logic being tested. Configure realistic response objects and assert method, URL, payload, timeout, and meaningful side effects.
5. Cover the main success path and the most material boundary/failure paths: malformed input, missing records, authentication, rollback, timeout/rate limit, or repeat execution as applicable.
6. Avoid broad `try/except`, conditional assertions, `pass`, tests that merely call functions, and coverage-only loops. A test must fail when the promised behavior is removed.
7. Run the focused test file, then relevant neighboring tests. Use the full suite for cross-cutting changes. Report passed, failed, and skipped counts separately and mention material low coverage.

Read [references/test-strategy.md](references/test-strategy.md) for fixtures, commands, and test patterns specific to this repository.
