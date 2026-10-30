# Brick Manager Agent Guide

Repository-specific skills live under `.codex/skills/`. Load the smallest matching set before acting:

- `brick-manager-development`: ordinary Flask feature, bugfix, refactor, or review work.
- `brick-manager-data-change`: models, SQLite schema, migrations, imports, backups, or persisted-data transformations.
- `brick-manager-sync-contracts`: Rebrickable, Brickognize, downloads, tokens, scheduled sync, or `/api/v1` contracts.
- `brick-manager-regression-tests`: test-focused work and regression-test design.

Use multiple skills when the task genuinely crosses boundaries; for example, a new persisted API field needs development, data-change, sync-contract, and regression-test guidance.

Treat `brick_manager/models.py`, versioned migrations, and executable tests as the primary source of truth. Keep `docs/reference/database-schema.md` and `docs/guides/testing.md` synchronized with verified behavior and measurements. Preserve user collection data, never expose credentials, and do not perform live remote writes, database resets, restores, or deployments without explicit user authorization.

Use Poetry commands from the repository root. Preserve unrelated working-tree changes.

## Commit messages

Whenever generating or suggesting a commit message, including editor-generated
messages, use Conventional Commits as required by `scripts/install_hooks.sh`:

```text
<type>[optional scope]: <description>
```

- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`.
- Use a lowercase type, an optional scope in parentheses, and a colon followed by one space.
- Write a concrete English description in the imperative, with at most 50 characters in the description.
- Describe the actual staged changes; avoid generic messages such as "Implement code changes".
- Do not add `!` before the colon: the current commit hook does not accept that syntax.
- When asked only for a commit message, return the message without Markdown fences or explanatory text.

Examples: `fix(ui): support quantity navigation on iPad`,
`chore(devcontainer): provide UTF-8 locales`.
