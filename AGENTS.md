# Brick Manager Agent Guide

Repository-specific skills live under `.codex/skills/`. Load the smallest matching set before acting:

- `brick-manager-development`: ordinary Flask feature, bugfix, refactor, or review work.
- `brick-manager-data-change`: models, SQLite schema, migrations, imports, backups, or persisted-data transformations.
- `brick-manager-sync-contracts`: Rebrickable, Brickognize, downloads, tokens, scheduled sync, or `/api/v1` contracts.
- `brick-manager-regression-tests`: test-focused work and regression-test design.

Use multiple skills when the task genuinely crosses boundaries; for example, a new persisted API field needs development, data-change, sync-contract, and regression-test guidance.

Treat `brick_manager/models.py`, versioned migrations, and executable tests as the primary source of truth. Keep `database_schema.md` and `TESTING.md` synchronized with verified behavior and measurements. Preserve user collection data, never expose credentials, and do not perform live remote writes, database resets, restores, or deployments without explicit user authorization.

Use Poetry commands from the repository root. Preserve unrelated working-tree changes.
