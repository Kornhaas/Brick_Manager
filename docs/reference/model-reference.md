# Model Reference

The authoritative SQLAlchemy declarations live in [`models.py`](models.py). See [`../database_schema.md`](../database_schema.md) for the current table inventory, relationships, status semantics, and migration rules.

This file intentionally does not duplicate every model field. Keeping a second handwritten schema here previously caused the documentation to diverge from the executable model.

## Model groups

- Collection state: `User_Set`, `User_Parts`, `User_Minifigures`, `UserMinifigurePart`, and `PartStorage`.
- Rebrickable catalog: categories, colors, parts, relationships, elements, themes, sets, minifigures, and inventory tables.
- Configuration: `ConfigSettings`, including encrypted token values.

When changing a model:

1. Update `models.py` and its behavioral tests.
2. Add a forward migration for existing databases when the schema changes.
3. Update `database_schema.md` when a table, field, relationship, or invariant changes.
4. Verify catalog imports preserve collection-owned data.
