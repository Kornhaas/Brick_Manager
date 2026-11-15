"""Add physical storage without inferring stock quantities or box identity.

The SQL below is a frozen schema snapshot; do not regenerate deployed migrations.
"""

import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_generations (
	id INTEGER NOT NULL,
	import_id TEXT NOT NULL,
	status TEXT DEFAULT 'running' NOT NULL,
	started_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
	completed_at DATETIME,
	files JSON DEFAULT '{}' NOT NULL,
	errors JSON DEFAULT '[]' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_catalog_status CHECK (status IN ('running', 'completed', 'failed')),
	UNIQUE (import_id)
);

CREATE TABLE IF NOT EXISTS collection_snapshots (
	id INTEGER NOT NULL,
	captured_on DATE NOT NULL,
	total_sets INTEGER NOT NULL,
	owned_parts INTEGER NOT NULL,
	required_parts INTEGER NOT NULL,
	missing_parts INTEGER NOT NULL,
	complete_sets INTEGER NOT NULL,
	incomplete_sets INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS config_settings (
	id INTEGER NOT NULL,
	"key" TEXT NOT NULL,
	value TEXT,
	encrypted BOOLEAN NOT NULL,
	description TEXT,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE ("key")
);

CREATE TABLE IF NOT EXISTS container_types (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	kind TEXT DEFAULT 'container' NOT NULL,
	width_mm FLOAT,
	depth_mm FLOAT,
	height_mm FLOAT,
	dimensions_status TEXT DEFAULT 'unknown' NOT NULL,
	access_mode TEXT DEFAULT 'unknown' NOT NULL,
	drawer_count INTEGER,
	properties JSON DEFAULT '{}' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_type_width_mm CHECK (width_mm IS NULL OR width_mm > 0),
	CONSTRAINT ck_type_depth_mm CHECK (depth_mm IS NULL OR depth_mm > 0),
	CONSTRAINT ck_type_height_mm CHECK (height_mm IS NULL OR height_mm > 0),
	CONSTRAINT ck_type_drawer_count CHECK (drawer_count IS NULL OR drawer_count > 0),
	UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS rebrickable_colors (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	rgb TEXT NOT NULL,
	is_trans BOOLEAN NOT NULL,
	num_parts INTEGER,
	num_sets INTEGER,
	y1 FLOAT,
	y2 FLOAT,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_inventories (
	id INTEGER NOT NULL,
	version INTEGER NOT NULL,
	set_num TEXT NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_minifigs (
	fig_num TEXT NOT NULL,
	name TEXT NOT NULL,
	num_parts INTEGER NOT NULL,
	img_url TEXT,
	PRIMARY KEY (fig_num)
);

CREATE TABLE IF NOT EXISTS rebrickable_part_categories (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_themes (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	parent_id INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(parent_id) REFERENCES rebrickable_themes (id)
);

CREATE TABLE IF NOT EXISTS storage_locations (
	id INTEGER NOT NULL,
	parent_id INTEGER,
	kind TEXT NOT NULL,
	label TEXT NOT NULL,
	sort_order INTEGER DEFAULT '0' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	width_mm FLOAT,
	depth_mm FLOAT,
	height_profile JSON,
	measurement_status TEXT DEFAULT 'unknown' NOT NULL,
	measured_at DATETIME,
	zone_kind TEXT DEFAULT 'active' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_location_kind CHECK (kind IN ('zone', 'rack', 'shelf', 'unresolved')),
	CONSTRAINT ck_location_parent CHECK (parent_id IS NULL OR parent_id != id),
	CONSTRAINT ck_location_width CHECK (width_mm IS NULL OR width_mm > 0),
	CONSTRAINT ck_location_depth CHECK (depth_mm IS NULL OR depth_mm > 0),
	FOREIGN KEY(parent_id) REFERENCES storage_locations (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS storage_moves (
	id INTEGER NOT NULL,
	status TEXT DEFAULT 'draft' NOT NULL,
	kind TEXT NOT NULL,
	idempotency_key TEXT NOT NULL,
	reason TEXT,
	payload JSON DEFAULT '{}' NOT NULL,
	snapshot JSON DEFAULT '{}' NOT NULL,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
	confirmed_at DATETIME,
	revision INTEGER DEFAULT '1' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_move_status CHECK (status IN ('draft', 'planned', 'confirmed', 'cancelled')),
	CONSTRAINT ck_move_kind CHECK (kind IN ('unit', 'quantity', 'intake', 'count')),
	UNIQUE (idempotency_key)
);

CREATE TABLE IF NOT EXISTS category_storage_rules (
	id INTEGER NOT NULL,
	category_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	archive_location_id INTEGER,
	revision INTEGER DEFAULT '1' NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (category_id),
	FOREIGN KEY(category_id) REFERENCES rebrickable_part_categories (id),
	FOREIGN KEY(location_id) REFERENCES storage_locations (id) ON DELETE RESTRICT,
	FOREIGN KEY(archive_location_id) REFERENCES storage_locations (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS rebrickable_inventory_minifigs (
	inventory_id INTEGER NOT NULL,
	fig_num TEXT NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (inventory_id, fig_num),
	FOREIGN KEY(inventory_id) REFERENCES rebrickable_inventories (id),
	FOREIGN KEY(fig_num) REFERENCES rebrickable_minifigs (fig_num)
);

CREATE TABLE IF NOT EXISTS rebrickable_parts (
	part_num TEXT NOT NULL,
	name TEXT NOT NULL,
	part_cat_id INTEGER NOT NULL,
	part_material TEXT,
	part_img_url TEXT,
	part_url TEXT,
	PRIMARY KEY (part_num),
	FOREIGN KEY(part_cat_id) REFERENCES rebrickable_part_categories (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_sets (
	set_num TEXT NOT NULL,
	name TEXT NOT NULL,
	year INTEGER NOT NULL,
	theme_id INTEGER NOT NULL,
	num_parts INTEGER NOT NULL,
	img_url TEXT,
	PRIMARY KEY (set_num),
	FOREIGN KEY(theme_id) REFERENCES rebrickable_themes (id)
);

CREATE TABLE IF NOT EXISTS stack_rules (
	id INTEGER NOT NULL,
	lower_type_id INTEGER NOT NULL,
	upper_type_id INTEGER NOT NULL,
	relation_kind TEXT NOT NULL,
	verified BOOLEAN DEFAULT '0' NOT NULL,
	source TEXT,
	verified_at DATETIME,
	height_increment_mm FLOAT,
	max_count INTEGER,
	max_height_mm FLOAT,
	properties JSON DEFAULT '{}' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_stack_pair UNIQUE (lower_type_id, upper_type_id, relation_kind),
	CONSTRAINT ck_stack_relation CHECK (relation_kind IN ('stacked', 'loose_on')),
	CONSTRAINT ck_stack_increment CHECK (height_increment_mm IS NULL OR height_increment_mm > 0),
	CONSTRAINT ck_stack_count CHECK (max_count IS NULL OR max_count > 0),
	CONSTRAINT ck_stack_height CHECK (max_height_mm IS NULL OR max_height_mm > 0),
	FOREIGN KEY(lower_type_id) REFERENCES container_types (id) ON DELETE RESTRICT,
	FOREIGN KEY(upper_type_id) REFERENCES container_types (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS storage_units (
	id INTEGER NOT NULL,
	type_id INTEGER,
	kind TEXT DEFAULT 'container' NOT NULL,
	label TEXT NOT NULL,
	host_unit_id INTEGER,
	ordinal INTEGER,
	partition_count INTEGER DEFAULT '1' NOT NULL,
	fill_state TEXT DEFAULT 'unknown' NOT NULL,
	contents_complete BOOLEAN DEFAULT '0' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	active BOOLEAN DEFAULT '1' NOT NULL,
	label_printed BOOLEAN DEFAULT '0' NOT NULL,
	properties JSON DEFAULT '{}' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_unit_kind CHECK (kind IN ('container', 'cabinet', 'drawer', 'compartment')),
	CONSTRAINT ck_unit_host CHECK (host_unit_id IS NULL OR host_unit_id != id),
	CONSTRAINT ck_unit_partitions CHECK (partition_count IN (1, 2, 3)),
	CONSTRAINT ck_unit_fill CHECK (fill_state IN ('unknown', 'space', 'nearly_full', 'full')),
	CONSTRAINT ck_unit_revision CHECK (revision >= 1),
	FOREIGN KEY(type_id) REFERENCES container_types (id) ON DELETE RESTRICT,
	FOREIGN KEY(host_unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS part_storage (
	id INTEGER NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER,
	location TEXT,
	level TEXT,
	box TEXT,
	notes TEXT,
	label_printed BOOLEAN NOT NULL,
	storage_unit_id INTEGER,
	quantity INTEGER,
	revision INTEGER DEFAULT '1' NOT NULL,
	migration_status TEXT DEFAULT 'unresolved' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_storage_quantity CHECK (quantity IS NULL OR quantity >= 0),
	CONSTRAINT ck_storage_revision CHECK (revision >= 1),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id),
	FOREIGN KEY(storage_unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS part_storage_preferences (
	id INTEGER NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER,
	replenishment_unlikely BOOLEAN,
	keep_accessible BOOLEAN DEFAULT '0' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id)
);

CREATE TABLE IF NOT EXISTS planned_sets (
	id INTEGER NOT NULL,
	set_num TEXT NOT NULL,
	quantity INTEGER DEFAULT '1' NOT NULL,
	active BOOLEAN DEFAULT '1' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_planned_set_quantity CHECK (quantity > 0),
	FOREIGN KEY(set_num) REFERENCES rebrickable_sets (set_num)
);

CREATE TABLE IF NOT EXISTS rebrickable_elements (
	element_id TEXT NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER NOT NULL,
	design_id TEXT,
	PRIMARY KEY (element_id),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_inventory_parts (
	inventory_id INTEGER NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	is_spare BOOLEAN NOT NULL,
	img_url TEXT,
	PRIMARY KEY (inventory_id, part_num, color_id, is_spare),
	FOREIGN KEY(inventory_id) REFERENCES rebrickable_inventories (id),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id)
);

CREATE TABLE IF NOT EXISTS rebrickable_inventory_sets (
	inventory_id INTEGER NOT NULL,
	set_num TEXT NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (inventory_id, set_num),
	FOREIGN KEY(inventory_id) REFERENCES rebrickable_inventories (id),
	FOREIGN KEY(set_num) REFERENCES rebrickable_sets (set_num)
);

CREATE TABLE IF NOT EXISTS rebrickable_part_relationships (
	rel_type TEXT NOT NULL,
	child_part_num TEXT NOT NULL,
	parent_part_num TEXT NOT NULL,
	PRIMARY KEY (rel_type, child_part_num, parent_part_num),
	FOREIGN KEY(child_part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(parent_part_num) REFERENCES rebrickable_parts (part_num)
);

CREATE TABLE IF NOT EXISTS storage_placements (
	unit_id INTEGER NOT NULL,
	shelf_id INTEGER,
	support_unit_id INTEGER,
	relation_kind TEXT DEFAULT 'on_shelf' NOT NULL,
	order_left INTEGER DEFAULT '0' NOT NULL,
	x_mm FLOAT,
	depth_offset_mm FLOAT,
	orientation TEXT DEFAULT 'normal' NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	rule_id INTEGER,
	PRIMARY KEY (unit_id),
	CONSTRAINT ck_placement_support CHECK ((shelf_id IS NOT NULL AND support_unit_id IS NULL) OR (shelf_id IS NULL AND support_unit_id IS NOT NULL)),
	CONSTRAINT ck_placement_cycle CHECK (support_unit_id IS NULL OR support_unit_id != unit_id),
	CONSTRAINT ck_placement_relation CHECK (relation_kind IN ('on_shelf', 'stacked', 'loose_on')),
	CONSTRAINT ck_placement_x CHECK (x_mm IS NULL OR x_mm >= 0),
	CONSTRAINT ck_placement_depth CHECK (depth_offset_mm IS NULL OR depth_offset_mm >= 0),
	FOREIGN KEY(unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT,
	FOREIGN KEY(shelf_id) REFERENCES storage_locations (id) ON DELETE RESTRICT,
	FOREIGN KEY(support_unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT,
	FOREIGN KEY(rule_id) REFERENCES stack_rules (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS user_sets (
	id INTEGER NOT NULL,
	set_num TEXT NOT NULL,
	status TEXT NOT NULL,
	label_printed BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(set_num) REFERENCES rebrickable_sets (set_num)
);

CREATE TABLE IF NOT EXISTS legacy_storage_mappings (
	storage_id INTEGER NOT NULL,
	candidate_key TEXT NOT NULL,
	storage_unit_id INTEGER,
	confirmed BOOLEAN DEFAULT '0' NOT NULL,
	PRIMARY KEY (storage_id),
	FOREIGN KEY(storage_id) REFERENCES part_storage (id) ON DELETE RESTRICT,
	FOREIGN KEY(storage_unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS storage_move_items (
	id INTEGER NOT NULL,
	move_id INTEGER NOT NULL,
	unit_id INTEGER,
	storage_id INTEGER,
	quantity INTEGER,
	target_unit_id INTEGER,
	target_placement JSON,
	source_revision INTEGER,
	source_snapshot JSON DEFAULT '{}' NOT NULL,
	ordinal INTEGER DEFAULT '0' NOT NULL,
	depends_on_id INTEGER,
	status TEXT DEFAULT 'planned' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_move_item_quantity CHECK (quantity IS NULL OR quantity > 0),
	FOREIGN KEY(move_id) REFERENCES storage_moves (id) ON DELETE RESTRICT,
	FOREIGN KEY(unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT,
	FOREIGN KEY(storage_id) REFERENCES part_storage (id) ON DELETE RESTRICT,
	FOREIGN KEY(target_unit_id) REFERENCES storage_units (id) ON DELETE RESTRICT,
	FOREIGN KEY(depends_on_id) REFERENCES storage_move_items (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS user_minifigures (
	id INTEGER NOT NULL,
	fig_num TEXT NOT NULL,
	quantity INTEGER NOT NULL,
	user_set_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(fig_num) REFERENCES rebrickable_minifigs (fig_num),
	FOREIGN KEY(user_set_id) REFERENCES user_sets (id)
);

CREATE TABLE IF NOT EXISTS user_parts (
	id INTEGER NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	have_quantity INTEGER,
	user_set_id INTEGER NOT NULL,
	is_spare BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id),
	FOREIGN KEY(user_set_id) REFERENCES user_sets (id)
);

CREATE TABLE IF NOT EXISTS user_minifigure_parts (
	id INTEGER NOT NULL,
	part_num TEXT NOT NULL,
	color_id INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	have_quantity INTEGER,
	user_set_id INTEGER NOT NULL,
	minifigure_id INTEGER NOT NULL,
	is_spare BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(part_num) REFERENCES rebrickable_parts (part_num),
	FOREIGN KEY(color_id) REFERENCES rebrickable_colors (id),
	FOREIGN KEY(user_set_id) REFERENCES user_sets (id),
	FOREIGN KEY(minifigure_id) REFERENCES user_minifigures (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_collection_snapshots_captured_on ON collection_snapshots (captured_on);

CREATE INDEX IF NOT EXISTS ix_storage_locations_parent_id ON storage_locations (parent_id);

CREATE INDEX IF NOT EXISTS ix_storage_moves_status ON storage_moves (status);

CREATE INDEX IF NOT EXISTS ix_storage_units_host_unit_id ON storage_units (host_unit_id);

CREATE INDEX IF NOT EXISTS ix_storage_units_type_id ON storage_units (type_id);

CREATE INDEX IF NOT EXISTS idx_part_location ON part_storage (part_num, location, level, box);

CREATE UNIQUE INDEX IF NOT EXISTS uq_preference_colour ON part_storage_preferences (part_num, color_id) WHERE color_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_preference_unknown_colour ON part_storage_preferences (part_num) WHERE color_id IS NULL;

CREATE INDEX IF NOT EXISTS ix_storage_placements_shelf_id ON storage_placements (shelf_id);

CREATE INDEX IF NOT EXISTS ix_storage_placements_support_unit_id ON storage_placements (support_unit_id);

CREATE INDEX IF NOT EXISTS ix_legacy_storage_mappings_candidate_key ON legacy_storage_mappings (candidate_key);

CREATE INDEX IF NOT EXISTS ix_storage_move_items_move_id ON storage_move_items (move_id);
"""


def _execute_statements(connection, script):
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise ValueError("Incomplete migration SQL")


def upgrade(connection):
    """Run inside the migration runner's transaction."""
    _execute_statements(connection, SCHEMA)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(part_storage)")}
    additions = {
        "storage_unit_id": "INTEGER REFERENCES storage_units(id) ON DELETE RESTRICT",
        "quantity": "INTEGER CHECK (quantity IS NULL OR quantity >= 0)",
        "revision": "INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1)",
        "migration_status": "TEXT NOT NULL DEFAULT 'unresolved'",
    }
    for name, declaration in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE part_storage ADD COLUMN {name} {declaration}")
    connection.execute("CREATE INDEX IF NOT EXISTS ix_part_storage_storage_unit_id ON part_storage(storage_unit_id)")
    rows = connection.execute("SELECT id, location, level, box FROM part_storage ORDER BY id").fetchall()
    complete_rows = [row for row in rows if all(isinstance(value, str) and value.strip() for value in row[1:])]
    shelves = {}
    if complete_rows:
        zone = connection.execute("INSERT INTO storage_locations (kind, label, measurement_status) VALUES ('zone', 'Aktiv', 'legacy_unverified')").lastrowid
        racks = {}
        for storage_id, location, level, box in complete_rows:
            if location not in racks:
                racks[location] = connection.execute("INSERT INTO storage_locations (parent_id, kind, label, measurement_status) VALUES (?, 'rack', ?, 'legacy_unverified')", (zone, location)).lastrowid
            key = (location, level)
            if key not in shelves:
                shelves[key] = connection.execute("INSERT INTO storage_locations (parent_id, kind, label, measurement_status) VALUES (?, 'shelf', ?, 'legacy_unverified')", (racks[location], level)).lastrowid
    for storage_id, location, level, box in rows:
        key = json.dumps([location, level, box], ensure_ascii=False, separators=(",", ":"))
        complete = all(isinstance(value, str) and value.strip() for value in (location, level, box))
        connection.execute("INSERT OR IGNORE INTO legacy_storage_mappings (storage_id, candidate_key) VALUES (?, ?)", (storage_id, key))
        connection.execute("UPDATE part_storage SET migration_status = ? WHERE id = ? AND storage_unit_id IS NULL", ("candidate" if complete else "unresolved", storage_id))
