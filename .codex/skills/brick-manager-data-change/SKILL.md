---
name: brick-manager-data-change
description: Plan, implement, or review Brick Manager model, SQLite schema, migration, bulk import, backup, or persistent-data changes. Use whenever existing collection data could be transformed, invalidated, duplicated, or lost.
---

# Brick Manager Data Change

Protect existing user collection data and make schema and import changes repeatable.

1. Establish the current truth from `brick_manager/models.py`, versioned migrations, the queries that use the affected fields, and a real database schema when available. Keep `database_schema.md` synchronized, but do not use documentation alone to infer the live schema.
2. Identify affected primary keys, foreign keys, nullability, defaults, indexes, relationships, cascade behavior, serializers, forms, and external identifiers before editing.
3. Separate reference catalog data (`rebrickable_*`) from user-owned state (`user_sets`, quantities, missing parts, storage, labels, and configuration). A catalog refresh must not silently erase user-owned state.
4. For an existing database, provide an explicit forward migration. Do not rely on `db.create_all()` to alter existing tables. Prefer Flask-Migrate/Alembic artifacts when the project begins tracking migrations; otherwise supply a narrowly scoped, restart-safe migration with validation and rollback guidance.
5. Make bulk imports transactional or checkpointed. Validate input shape before mutation, use stable Rebrickable identifiers, define duplicate behavior, and avoid deleting valid rows after a partial download.
6. Test from an old-schema fixture or database copy through migration to the new invariant. Test a second run for idempotency and test failure/rollback behavior.
7. Report backup assumptions and any irreversible transformation. Never run `make reset-db`, restore, delete live data, or mutate an unknown database without explicit user authorization.

Read [references/data-invariants.md](references/data-invariants.md) before changing a model, migration, import, or backup path.
