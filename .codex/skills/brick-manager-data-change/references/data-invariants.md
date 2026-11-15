# Data Invariants

## Live model groups

User-owned state:

- `User_Set` / `user_sets`: one owned set record, linked by `set_num` to catalog data.
- `User_Parts` / `user_parts`: required and owned quantities per set, part, color, and spare flag.
- `User_Minifigures` and `UserMinifigurePart`: owned minifigure composition and quantities.
- `PartStorage` / `part_storage`: zero or more physical storage records per part; color is optional and location fields may be null.
- `ConfigSettings` / `config_settings`: encrypted or operational configuration values.

Reference catalog:

- categories, colors, parts, relationships, elements, themes, sets, minifigures, inventories, inventory parts, inventory sets, and inventory minifigures under `rebrickable_*` tables.

Read the actual declarations in `brick_manager/models.py` for keys and constraints; this list is routing context, not a schema replacement.

## Required preservation checks

- `part_num`, `set_num`, `fig_num`, Rebrickable numeric IDs, and inventory composite keys retain their external meaning.
- `have_quantity` remains non-negative and must not accidentally exceed intended business constraints.
- `quantity`, `color_id`, `user_set_id`, and `is_spare` jointly determine missing-part calculations; do not collapse spare and non-spare rows.
- A part may have multiple storage locations. An upsert must declare whether it addresses one matching location or all locations.
- Catalog refreshes preserve user set status, owned quantities, storage, notes, and `label_printed` state.
- Deleting a user set may cascade through owned child rows; deleting catalog data needs separate impact analysis.

## Migration acceptance checks

1. Record pre-migration row counts and representative relationships without printing secrets.
2. Back up the database using SQLite-safe means and document the recovery target.
3. Apply the migration to a disposable copy.
4. Run `PRAGMA foreign_key_check` and relevant uniqueness/null checks.
5. Exercise reads and writes through SQLAlchemy, not only raw SQL.
6. Re-run the migration or importer and confirm it is safe or fails with a clear already-applied condition.
7. Confirm rollback or restoration before considering a destructive transformation ready.

Versioned SQL and Python migrations live in `brick_manager/migrations/`. The runner journals each artifact with its SHA-256 and commits schema/backfill atomically. Never edit an already-applied artifact; add a new forward migration. Inspect the runner and migration tests before changing this contract. Physical-storage backfill preserves raw labels and unknown quantities, creating only unconfirmed mapping candidates.

Physical storage also owns `storage_locations`, `container_types`, `storage_units`, `storage_placements`, `stack_rules`, `storage_moves`, `storage_move_items`, `category_storage_rules`, `part_storage_preferences`, `planned_sets`, `catalog_generations`, and `legacy_storage_mappings`. See `docs/reference/database-schema.md`; never derive physical stock quantities from set-owned quantities.
