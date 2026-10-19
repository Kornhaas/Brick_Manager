---
name: brick-manager-development
description: Implement, debug, refactor, or review ordinary Brick Manager Flask features across routes, services, templates, static assets, and models. Use for repository work that is not primarily a schema migration, external sync contract, or test-only task.
---

# Brick Manager Development

Work from the repository root and preserve the existing Flask blueprint, service, SQLAlchemy, Jinja, and vanilla JavaScript architecture.

1. Read the affected route, service, model, template, JavaScript, and focused tests before editing. Treat executable code and current tests as stronger evidence than feature-summary documents.
2. Keep request parsing and HTTP responses in `brick_manager/routes/`. Put reusable domain, integration, file, and rendering logic in `brick_manager/services/`. Avoid adding more unrelated responsibilities to large route modules.
3. Preserve established imports: application modules are currently imported as top-level modules with `brick_manager/` placed on `sys.path`. Do not casually convert only part of the project to package-relative imports.
4. Validate untrusted form, JSON, URL, filename, and path input at the boundary. Do not expose tokens, authorization headers, filesystem paths, or exception details in responses or logs.
5. Keep templates and their JavaScript/API payloads in sync. When changing JSON or form fields, search for every producer and consumer.
6. Add or update focused behavioral tests. Use `$brick-manager-regression-tests` when the main task is test design or a bug regression. Use `$brick-manager-data-change` for persistent-data changes and `$brick-manager-sync-contracts` for external integrations or `/api/v1` contracts.
7. Run the narrowest relevant tests first, then broaden verification in proportion to the change. Do not describe skipped legacy tests as passing coverage.

## Quality baseline

Use Poetry-managed quality tools. For changed Python files, run `poetry run ruff check` and `poetry run ruff format --check`; use `poetry run basedpyright` when interfaces or model attributes change. `make audit` checks dependency vulnerabilities and `make dead-code` reports candidates that require human review before removal. Do not suppress Ruff or BasedPyright findings solely to pass a check; add scoped exclusions only for verified framework or dynamic-ORM false positives.

Read [references/project-profile.md](references/project-profile.md) when locating components, choosing commands, or deciding the appropriate verification scope.

Do not perform deployment, database reset, live synchronization, token generation, or destructive cleanup unless the user explicitly requests that operation.
