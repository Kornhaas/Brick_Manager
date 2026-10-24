CREATE TABLE IF NOT EXISTS collection_snapshots (
    id INTEGER NOT NULL PRIMARY KEY,
    captured_on DATE NOT NULL UNIQUE,
    total_sets INTEGER NOT NULL DEFAULT 0,
    owned_parts INTEGER NOT NULL DEFAULT 0,
    required_parts INTEGER NOT NULL DEFAULT 0,
    missing_parts INTEGER NOT NULL DEFAULT 0,
    complete_sets INTEGER NOT NULL DEFAULT 0,
    incomplete_sets INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_collection_snapshots_captured_on
    ON collection_snapshots (captured_on);
