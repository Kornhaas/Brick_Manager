"""

This module defines the SQLAlchemy models for the Brick Manager application.


Models include:
- User_Set (replaces UserSet)
- User_Parts (replaces PartInSet, uses color_id instead of color/color_rgb)
- User_Minifigures (replaces Minifigure)
- UserMinifigurePart
- PartStorage
- RebrickablePartCategories
- RebrickableColors
- RebrickableParts
- RebrickableSets (replaces Set)
"""

# pylint: disable=C0301,R0903,C0103

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text

db = SQLAlchemy()

USER_SET_STATUSES = frozenset(
    {
        "unknown",
        "konvolut",
        "assembled",
        "sealed",
        "missingparts",
        "complete",
        "completenospareparts",
    }
)
FULL_OWNERSHIP_STATUSES = frozenset({"complete", "assembled", "sealed"})
NON_LOOSE_PART_STATUSES = frozenset({"assembled", "konvolut", "sealed"})


class CollectionSnapshot(db.Model):
    """Daily aggregate used for collection trend charts."""

    __tablename__ = "collection_snapshots"

    id = db.Column(Integer, primary_key=True)
    captured_on = db.Column(Date, nullable=False, unique=True, index=True)
    total_sets = db.Column(Integer, nullable=False, default=0)
    owned_parts = db.Column(Integer, nullable=False, default=0)
    required_parts = db.Column(Integer, nullable=False, default=0)
    missing_parts = db.Column(Integer, nullable=False, default=0)
    complete_sets = db.Column(Integer, nullable=False, default=0)
    incomplete_sets = db.Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<CollectionSnapshot {self.captured_on}>"


class User_Set(db.Model):
    """Represents a user's collection of sets."""

    __tablename__ = "user_sets"

    id = db.Column(Integer, primary_key=True)
    set_num = db.Column(Text, ForeignKey("rebrickable_sets.set_num"), nullable=False)
    status = db.Column(Text, default="unknown", nullable=False)
    label_printed = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    template_set = db.relationship("RebrickableSets", lazy="joined")
    parts_in_set = db.relationship(
        "User_Parts", back_populates="user_set", cascade="all, delete-orphan", lazy=True
    )
    minifigures_in_set = db.relationship(
        "User_Minifigures",
        back_populates="user_set",
        cascade="all, delete-orphan",
        lazy=True,
    )
    user_minifigure_parts = db.relationship(
        "UserMinifigurePart",
        back_populates="user_set",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<User_Set {self.id} - {self.set_num}>"

    def to_dict(self):
        """Convert the User_Set object to a dictionary."""

        return {
            "id": self.id,
            "set_num": self.set_num,
            "status": self.status,
            "label_printed": self.label_printed,
        }


class User_Minifigures(db.Model):
    """Represents a user's minifigures in a set."""

    __tablename__ = "user_minifigures"

    id = db.Column(Integer, primary_key=True)
    fig_num = db.Column(
        Text, ForeignKey("rebrickable_minifigs.fig_num"), nullable=False
    )
    quantity = db.Column(Integer, nullable=False)
    user_set_id = db.Column(Integer, ForeignKey("user_sets.id"), nullable=False)

    # Relationships
    user_set = db.relationship("User_Set", back_populates="minifigures_in_set")
    rebrickable_minifig = db.relationship("RebrickableMinifigs", lazy="joined")

    def __repr__(self):
        return f"<User_Minifigures {self.fig_num} - Quantity: {self.quantity}>"


class User_Parts(db.Model):
    """Represents the relationship between parts and sets."""

    __tablename__ = "user_parts"

    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey("rebrickable_parts.part_num"), nullable=False)
    color_id = db.Column(Integer, ForeignKey("rebrickable_colors.id"), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    user_set_id = db.Column(Integer, ForeignKey("user_sets.id"), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship("User_Set", back_populates="parts_in_set")
    rebrickable_part = db.relationship("RebrickableParts", lazy="joined")
    rebrickable_color = db.relationship("RebrickableColors", lazy="joined")

    def __repr__(self):
        return f"<User_Parts {self.part_num} - Quantity: {self.quantity}>"


class UserMinifigurePart(db.Model):
    """

    Represents a user's specific collection of minifigure parts.

    Uses RebrickableParts directly instead of MinifigurePart.
    """

    __tablename__ = "user_minifigure_parts"

    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey("rebrickable_parts.part_num"), nullable=False)
    color_id = db.Column(Integer, ForeignKey("rebrickable_colors.id"), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)  # Track ownership
    user_set_id = db.Column(Integer, ForeignKey("user_sets.id"), nullable=False)
    minifigure_id = db.Column(
        Integer, ForeignKey("user_minifigures.id"), nullable=False
    )  # Link to specific minifigure
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship("User_Set", back_populates="user_minifigure_parts")
    user_minifigure = db.relationship("User_Minifigures")
    rebrickable_part = db.relationship("RebrickableParts", lazy="joined")
    rebrickable_color = db.relationship("RebrickableColors", lazy="joined")

    def __repr__(self):
        return f"<UserMinifigurePart {self.part_num} - Quantity: {self.quantity}>"


class PartStorage(db.Model):
    """Represents the storage information for parts with support for multiple locations per part."""

    __tablename__ = "part_storage"

    __table_args__ = (
        # Allow same part_num with different colors or notes in different locations
        db.Index("idx_part_location", "part_num", "location", "level", "box"),
        db.CheckConstraint(
            "quantity IS NULL OR quantity >= 0", name="ck_storage_quantity"
        ),
        db.CheckConstraint("revision >= 1", name="ck_storage_revision"),
    )

    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey("rebrickable_parts.part_num"), nullable=False)
    color_id = db.Column(
        Integer, ForeignKey("rebrickable_colors.id"), nullable=True
    )  # Optional: track color
    location = db.Column(Text)
    level = db.Column(Text)
    box = db.Column(Text)
    notes = db.Column(Text, nullable=True)  # e.g., "spare parts", "red version", etc.
    label_printed = db.Column(Boolean, default=False, nullable=False)

    storage_unit_id = db.Column(
        Integer,
        ForeignKey("storage_units.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    quantity = db.Column(Integer, nullable=True)
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")
    migration_status = db.Column(
        Text, nullable=False, default="unresolved", server_default="unresolved"
    )
    storage_unit = db.relationship("StorageUnit", foreign_keys=[storage_unit_id])

    # Relationships
    rebrickable_part = db.relationship(
        "RebrickableParts", backref="part_storage", lazy="joined"
    )
    rebrickable_color = db.relationship(
        "RebrickableColors", backref="part_storage_colors", lazy="joined"
    )

    def __repr__(self):
        color_info = f" Color: {self.color_id}," if self.color_id else ""
        notes_info = f" ({self.notes})" if self.notes else ""
        return f"<PartStorage {self.part_num} -{color_info} Location: {self.location}, Level: {self.level}, Box: {self.box}{notes_info}>"


class RebrickablePartCategories(db.Model):
    """

    Represents categories for Rebrickable parts.


    This model stores the category information for brick parts as defined by Rebrickable,
    such as 'Brick', 'Plate', 'Technic', etc.
    """

    __tablename__ = "rebrickable_part_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<RebrickablePartCategory {self.name}>"

    def to_dict(self):
        """Convert the RebrickablePartCategory object to a dictionary."""

        return {"id": self.id, "name": self.name}


class RebrickableColors(db.Model):
    """

    Represents colors available for brick parts from Rebrickable.


    This model stores color information including RGB values, transparency status,
    and statistics about how many parts and sets use each color.
    """

    __tablename__ = "rebrickable_colors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    rgb = db.Column(db.Text, nullable=False)
    is_trans = db.Column(db.Boolean, nullable=False, default=False)
    num_parts = db.Column(db.Integer, nullable=True)
    num_sets = db.Column(db.Integer, nullable=True)
    y1 = db.Column(db.Float, nullable=True)
    y2 = db.Column(db.Float, nullable=True)

    def __repr__(self):
        # return f'<RebrickableColor {self.name}>'
        return f"<Color {self.name} (ID: {self.id})>"

    def to_dict(self):
        """Convert the RebrickableColor object to a dictionary."""

        return {
            "id": self.id,
            "name": self.name,
            "rgb": self.rgb,
            "is_trans": self.is_trans,
            "num_parts": self.num_parts,
            "num_sets": self.num_sets,
            "y1": self.y1,
            "y2": self.y2,
        }

    # Relationships
    user_parts = db.relationship(
        "User_Parts", back_populates="rebrickable_color", lazy="dynamic"
    )
    user_minifigure_parts = db.relationship(
        "UserMinifigurePart", back_populates="rebrickable_color", lazy="dynamic"
    )


class RebrickableParts(db.Model):
    """

    Represents individual brick parts from the Rebrickable database.


    This model stores part information including part numbers, names, categories,
    materials, and image URLs for individual brick pieces.
    """

    __tablename__ = "rebrickable_parts"

    part_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    part_cat_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_part_categories.id"), nullable=False
    )
    part_material = db.Column(db.Text)
    part_img_url = db.Column(db.Text, nullable=True)
    part_url = db.Column(db.Text, nullable=True)

    # Relationships
    category = db.relationship("RebrickablePartCategories", lazy="joined")
    user_parts = db.relationship(
        "User_Parts", back_populates="rebrickable_part", lazy="dynamic"
    )
    user_minifigure_parts = db.relationship(
        "UserMinifigurePart", back_populates="rebrickable_part", lazy="dynamic"
    )

    def __repr__(self):
        return f"<RebrickablePart {self.part_num}>"

    def to_dict(self):
        """Convert the RebrickablePart object to a dictionary."""

        return {
            "part_num": self.part_num,
            "name": self.name,
            "part_cat_id": self.part_cat_id,
            "part_material": self.part_material,
            "part_img_url": self.part_img_url,
            "part_url": self.part_url,
        }


class RebrickablePartRelationships(db.Model):
    """

    Represents relationships between Brick parts from Rebrickable.


    This model stores parent-child relationships between parts, such as when
    one part is a variant or component of another part.
    """

    __tablename__ = "rebrickable_part_relationships"

    rel_type = db.Column(db.Text, primary_key=True)
    child_part_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_parts.part_num"), primary_key=True
    )
    parent_part_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_parts.part_num"), primary_key=True
    )


class RebrickableElements(db.Model):
    """

    Represents Brick elements from Rebrickable.


    An element is a specific combination of a part in a particular color.
    This model maps element IDs to their corresponding parts and colors.
    """

    __tablename__ = "rebrickable_elements"

    element_id = db.Column(db.Text, primary_key=True)
    part_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_parts.part_num"), nullable=False
    )
    color_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_colors.id"), nullable=False
    )
    design_id = db.Column(db.Text)


class RebrickableThemes(db.Model):
    """

    Represents Brick themes from Rebrickable.


    This model stores theme information such as 'Star Wars', 'City', 'Technic', etc.
    Themes can have parent-child relationships for sub-themes.
    """

    __tablename__ = "rebrickable_themes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("rebrickable_themes.id"))

    def __repr__(self):
        return f"<Theme {self.name} (ID: {self.id}, Parent: {self.parent_id})>"

    def to_dict(self):
        """Convert the Theme object to a dictionary."""

        return {"id": self.id, "name": self.name, "parent_id": self.parent_id}


class RebrickableSets(db.Model):
    """

    Represents Brick sets from the Rebrickable database.


    This model stores set information including set numbers, names, years,
    themes, part counts, and image URLs for complete Brick sets.
    """

    __tablename__ = "rebrickable_sets"

    set_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    theme_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_themes.id"), nullable=False
    )
    num_parts = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.Text)

    # Relationships
    user_sets = db.relationship(
        "User_Set", back_populates="template_set", lazy="dynamic"
    )
    theme = db.relationship("RebrickableThemes", lazy="joined")

    def __repr__(self):
        return f"<RebrickableSet {self.set_num} - {self.name}>"

    def to_dict(self):
        """Convert the RebrickableSet object to a dictionary."""

        return {
            "set_num": self.set_num,
            "name": self.name,
            "year": self.year,
            "theme_id": self.theme_id,
            "num_parts": self.num_parts,
            "img_url": self.img_url,
        }


class RebrickableMinifigs(db.Model):
    """

    Represents Brick minifigures from the Rebrickable database.


    This model stores minifigure information including figure numbers, names,
    part counts, and image URLs for complete minifigures.
    """

    __tablename__ = "rebrickable_minifigs"

    fig_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    num_parts = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.Text)

    # Relationships
    user_minifigures = db.relationship(
        "User_Minifigures", back_populates="rebrickable_minifig", lazy="dynamic"
    )

    def __repr__(self):
        return f"<RebrickableMinifig {self.fig_num} - {self.name}>"


class RebrickableInventories(db.Model):
    """

    Represents inventories from Rebrickable.


    This model stores inventory information which tracks different versions
    of set contents and their associated parts and minifigures.
    """

    __tablename__ = "rebrickable_inventories"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)
    set_num = db.Column(db.Text, nullable=False)


class RebrickableInventoryParts(db.Model):
    """

    Represents parts within specific inventories from Rebrickable.


    This model stores the relationship between inventories and the parts they contain,
    including quantities, colors, spare part status, and part-specific images.
    """

    __tablename__ = "rebrickable_inventory_parts"

    inventory_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_inventories.id"), primary_key=True
    )
    part_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_parts.part_num"), primary_key=True
    )
    color_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_colors.id"), primary_key=True
    )
    quantity = db.Column(db.Integer, nullable=False)
    is_spare = db.Column(db.Boolean, nullable=False, default=False, primary_key=True)
    img_url = db.Column(db.Text)


class RebrickableInventorySets(db.Model):
    """

    Represents sets within specific inventories from Rebrickable.


    This model stores the relationship between inventories and the sets they contain,
    including quantities of each set within the inventory.
    """

    __tablename__ = "rebrickable_inventory_sets"

    inventory_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_inventories.id"), primary_key=True
    )
    set_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_sets.set_num"), primary_key=True
    )
    quantity = db.Column(db.Integer, nullable=False)


class RebrickableInventoryMinifigs(db.Model):
    """

    Represents minifigures within specific inventories from Rebrickable.


    This model stores the relationship between inventories and the minifigures they contain,
    including quantities of each minifigure within the inventory.
    """

    __tablename__ = "rebrickable_inventory_minifigs"

    inventory_id = db.Column(
        db.Integer, db.ForeignKey("rebrickable_inventories.id"), primary_key=True
    )
    fig_num = db.Column(
        db.Text, db.ForeignKey("rebrickable_minifigs.fig_num"), primary_key=True
    )
    quantity = db.Column(db.Integer, nullable=False)


class ConfigSettings(db.Model):
    """

    Stores application configuration settings including API tokens and other preferences.


    This model provides a secure way to store configuration data including encrypted
    API tokens for external services like Rebrickable. Settings are stored as key-value
    pairs with optional encryption for sensitive data.
    """

    __tablename__ = "config_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False, unique=True)
    value = db.Column(db.Text, nullable=True)
    encrypted = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def __repr__(self):
        return f"<ConfigSettings {self.key}>"

    def to_dict(self):
        """Convert the ConfigSettings object to a dictionary."""

        return {
            "id": self.id,
            "key": self.key,
            "value": "***" if self.encrypted else self.value,
            "encrypted": self.encrypted,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Add aliases for backward compatibility with tests
Parts = User_Parts
MissingParts = UserMinifigurePart  # Closest match for missing parts functionality


class StorageLocation(db.Model):
    """Fixed labelled storage hierarchy; dimensions remain unknown until measured."""

    __tablename__ = "storage_locations"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('zone', 'rack', 'shelf', 'unresolved')", name="ck_location_kind"
        ),
        db.CheckConstraint(
            "parent_id IS NULL OR parent_id != id", name="ck_location_parent"
        ),
        db.CheckConstraint(
            "width_mm IS NULL OR width_mm > 0", name="ck_location_width"
        ),
        db.CheckConstraint(
            "depth_mm IS NULL OR depth_mm > 0", name="ck_location_depth"
        ),
    )
    id = db.Column(Integer, primary_key=True)
    parent_id = db.Column(
        Integer, ForeignKey("storage_locations.id", ondelete="RESTRICT"), index=True
    )
    kind = db.Column(Text, nullable=False)
    label = db.Column(Text, nullable=False)
    sort_order = db.Column(Integer, nullable=False, default=0, server_default="0")
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")
    width_mm = db.Column(db.Float)
    depth_mm = db.Column(db.Float)
    height_profile = db.Column(db.JSON, nullable=True)
    measurement_status = db.Column(
        Text, nullable=False, default="unknown", server_default="unknown"
    )
    measured_at = db.Column(db.DateTime)
    zone_kind = db.Column(
        Text, nullable=False, default="active", server_default="active"
    )


class ContainerType(db.Model):
    """Container dimensions and access properties independent of physical labels."""

    __tablename__ = "container_types"
    __table_args__ = tuple(
        db.CheckConstraint(f"{field} IS NULL OR {field} > 0", name=f"ck_type_{field}")
        for field in ("width_mm", "depth_mm", "height_mm", "drawer_count")
    )
    id = db.Column(Integer, primary_key=True)
    name = db.Column(Text, nullable=False, unique=True)
    kind = db.Column(
        Text, nullable=False, default="container", server_default="container"
    )
    width_mm = db.Column(db.Float)
    depth_mm = db.Column(db.Float)
    height_mm = db.Column(db.Float)
    dimensions_status = db.Column(
        Text, nullable=False, default="unknown", server_default="unknown"
    )
    access_mode = db.Column(
        Text, nullable=False, default="unknown", server_default="unknown"
    )
    drawer_count = db.Column(Integer)
    properties = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")


class StorageUnit(db.Model):
    """A physical container, magazine, drawer or individually addressable compartment."""

    __tablename__ = "storage_units"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('container', 'cabinet', 'drawer', 'compartment')",
            name="ck_unit_kind",
        ),
        db.CheckConstraint(
            "host_unit_id IS NULL OR host_unit_id != id", name="ck_unit_host"
        ),
        db.CheckConstraint("partition_count IN (1, 2, 3)", name="ck_unit_partitions"),
        db.CheckConstraint(
            "fill_state IN ('unknown', 'space', 'nearly_full', 'full')",
            name="ck_unit_fill",
        ),
        db.CheckConstraint("revision >= 1", name="ck_unit_revision"),
    )
    id = db.Column(Integer, primary_key=True)
    type_id = db.Column(
        Integer, ForeignKey("container_types.id", ondelete="RESTRICT"), index=True
    )
    kind = db.Column(
        Text, nullable=False, default="container", server_default="container"
    )
    label = db.Column(Text, nullable=False)
    host_unit_id = db.Column(
        Integer, ForeignKey("storage_units.id", ondelete="RESTRICT"), index=True
    )
    ordinal = db.Column(Integer)
    partition_count = db.Column(Integer, nullable=False, default=1, server_default="1")
    fill_state = db.Column(
        Text, nullable=False, default="unknown", server_default="unknown"
    )
    contents_complete = db.Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")
    active = db.Column(Boolean, nullable=False, default=True, server_default="1")
    label_printed = db.Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    properties = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")
    container_type = db.relationship("ContainerType", foreign_keys=[type_id])


class StackRule(db.Model):
    """Verified directed support compatibility, including distinct loose supports."""

    __tablename__ = "stack_rules"
    __table_args__ = (
        db.UniqueConstraint(
            "lower_type_id", "upper_type_id", "relation_kind", name="uq_stack_pair"
        ),
        db.CheckConstraint(
            "relation_kind IN ('stacked', 'loose_on')", name="ck_stack_relation"
        ),
        db.CheckConstraint(
            "height_increment_mm IS NULL OR height_increment_mm > 0",
            name="ck_stack_increment",
        ),
        db.CheckConstraint("max_count IS NULL OR max_count > 0", name="ck_stack_count"),
        db.CheckConstraint(
            "max_height_mm IS NULL OR max_height_mm > 0", name="ck_stack_height"
        ),
    )
    id = db.Column(Integer, primary_key=True)
    lower_type_id = db.Column(
        Integer, ForeignKey("container_types.id", ondelete="RESTRICT"), nullable=False
    )
    upper_type_id = db.Column(
        Integer, ForeignKey("container_types.id", ondelete="RESTRICT"), nullable=False
    )
    relation_kind = db.Column(Text, nullable=False)
    verified = db.Column(Boolean, nullable=False, default=False, server_default="0")
    source = db.Column(Text)
    verified_at = db.Column(db.DateTime)
    height_increment_mm = db.Column(db.Float)
    max_count = db.Column(Integer)
    max_height_mm = db.Column(db.Float)
    properties = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")


class StoragePlacement(db.Model):
    """Current physical support edge; a stack is derived from these edges."""

    __tablename__ = "storage_placements"
    __table_args__ = (
        db.CheckConstraint(
            "(shelf_id IS NOT NULL AND support_unit_id IS NULL) OR (shelf_id IS NULL AND support_unit_id IS NOT NULL)",
            name="ck_placement_support",
        ),
        db.CheckConstraint(
            "support_unit_id IS NULL OR support_unit_id != unit_id",
            name="ck_placement_cycle",
        ),
        db.CheckConstraint(
            "relation_kind IN ('on_shelf', 'stacked', 'loose_on')",
            name="ck_placement_relation",
        ),
        db.CheckConstraint("x_mm IS NULL OR x_mm >= 0", name="ck_placement_x"),
        db.CheckConstraint(
            "depth_offset_mm IS NULL OR depth_offset_mm >= 0", name="ck_placement_depth"
        ),
    )
    unit_id = db.Column(
        Integer, ForeignKey("storage_units.id", ondelete="RESTRICT"), primary_key=True
    )
    shelf_id = db.Column(
        Integer, ForeignKey("storage_locations.id", ondelete="RESTRICT"), index=True
    )
    support_unit_id = db.Column(
        Integer, ForeignKey("storage_units.id", ondelete="RESTRICT"), index=True
    )
    relation_kind = db.Column(
        Text, nullable=False, default="on_shelf", server_default="on_shelf"
    )
    order_left = db.Column(Integer, nullable=False, default=0, server_default="0")
    x_mm = db.Column(db.Float)
    depth_offset_mm = db.Column(db.Float)
    orientation = db.Column(
        Text, nullable=False, default="normal", server_default="normal"
    )
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")
    rule_id = db.Column(Integer, ForeignKey("stack_rules.id", ondelete="RESTRICT"))


class StorageMove(db.Model):
    """An auditable intent whose physical effects apply only on confirmation."""

    __tablename__ = "storage_moves"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('draft', 'planned', 'confirmed', 'cancelled')",
            name="ck_move_status",
        ),
        db.CheckConstraint(
            "kind IN ('unit', 'quantity', 'intake', 'count')", name="ck_move_kind"
        ),
    )
    id = db.Column(Integer, primary_key=True)
    status = db.Column(
        Text, nullable=False, default="draft", server_default="draft", index=True
    )
    kind = db.Column(Text, nullable=False)
    idempotency_key = db.Column(Text, nullable=False, unique=True)
    reason = db.Column(Text)
    payload = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")
    snapshot = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    confirmed_at = db.Column(db.DateTime)
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")


class StorageMoveItem(db.Model):
    """Ordered physical work item or quantity allocation within an intent."""

    __tablename__ = "storage_move_items"
    __table_args__ = (
        db.CheckConstraint(
            "quantity IS NULL OR quantity > 0", name="ck_move_item_quantity"
        ),
    )
    id = db.Column(Integer, primary_key=True)
    move_id = db.Column(
        Integer,
        ForeignKey("storage_moves.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    unit_id = db.Column(Integer, ForeignKey("storage_units.id", ondelete="RESTRICT"))
    storage_id = db.Column(Integer, ForeignKey("part_storage.id", ondelete="RESTRICT"))
    quantity = db.Column(Integer)
    target_unit_id = db.Column(
        Integer, ForeignKey("storage_units.id", ondelete="RESTRICT")
    )
    target_placement = db.Column(db.JSON, nullable=True)
    source_revision = db.Column(Integer)
    source_snapshot = db.Column(
        db.JSON, nullable=False, default=dict, server_default="{}"
    )
    ordinal = db.Column(Integer, nullable=False, default=0, server_default="0")
    depends_on_id = db.Column(
        Integer, ForeignKey("storage_move_items.id", ondelete="RESTRICT")
    )
    status = db.Column(
        Text, nullable=False, default="planned", server_default="planned"
    )


class CategoryStorageRule(db.Model):
    """Primary category location and optional archival destination."""

    __tablename__ = "category_storage_rules"
    id = db.Column(Integer, primary_key=True)
    category_id = db.Column(
        Integer,
        ForeignKey("rebrickable_part_categories.id"),
        nullable=False,
        unique=True,
    )
    location_id = db.Column(
        Integer, ForeignKey("storage_locations.id", ondelete="RESTRICT"), nullable=False
    )
    archive_location_id = db.Column(
        Integer, ForeignKey("storage_locations.id", ondelete="RESTRICT")
    )
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")


class PartStoragePreference(db.Model):
    """Optional reversible manual signals for an exact part and colour pair."""

    __tablename__ = "part_storage_preferences"
    __table_args__ = (
        db.Index(
            "uq_preference_colour",
            "part_num",
            "color_id",
            unique=True,
            sqlite_where=db.text("color_id IS NOT NULL"),
        ),
        db.Index(
            "uq_preference_unknown_colour",
            "part_num",
            unique=True,
            sqlite_where=db.text("color_id IS NULL"),
        ),
    )
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey("rebrickable_parts.part_num"), nullable=False)
    color_id = db.Column(Integer, ForeignKey("rebrickable_colors.id"))
    replenishment_unlikely = db.Column(Boolean)
    keep_accessible = db.Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")


class PlannedSet(db.Model):
    """Independent future set demand, never a fabricated owned set."""

    __tablename__ = "planned_sets"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_planned_set_quantity"),
    )
    id = db.Column(Integer, primary_key=True)
    set_num = db.Column(Text, ForeignKey("rebrickable_sets.set_num"), nullable=False)
    quantity = db.Column(Integer, nullable=False, default=1, server_default="1")
    active = db.Column(Boolean, nullable=False, default=True, server_default="1")
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")


class CatalogGeneration(db.Model):
    """Persistent provenance for a complete, failed or in-progress catalog import."""

    __tablename__ = "catalog_generations"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('running', 'completed', 'failed')", name="ck_catalog_status"
        ),
    )
    id = db.Column(Integer, primary_key=True)
    import_id = db.Column(Text, nullable=False, unique=True)
    status = db.Column(
        Text, nullable=False, default="running", server_default="running"
    )
    started_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    completed_at = db.Column(db.DateTime)
    files = db.Column(db.JSON, nullable=False, default=dict, server_default="{}")
    errors = db.Column(db.JSON, nullable=False, default=list, server_default="[]")
    revision = db.Column(Integer, nullable=False, default=1, server_default="1")


class LegacyStorageMapping(db.Model):
    """A reversible grouping candidate, not an assertion of physical box identity."""

    __tablename__ = "legacy_storage_mappings"
    storage_id = db.Column(
        Integer, ForeignKey("part_storage.id", ondelete="RESTRICT"), primary_key=True
    )
    candidate_key = db.Column(Text, nullable=False, index=True)
    storage_unit_id = db.Column(
        Integer, ForeignKey("storage_units.id", ondelete="RESTRICT")
    )
    confirmed = db.Column(Boolean, nullable=False, default=False, server_default="0")
