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
from sqlalchemy import Integer, ForeignKey, Boolean, Text

db = SQLAlchemy()


class User_Set(db.Model):
    """
    Represents a user's collection of sets.
    """
    __tablename__ = 'user_sets'

    id = db.Column(Integer, primary_key=True)
    set_num = db.Column(Text, ForeignKey(
        'rebrickable_sets.set_num'), nullable=False)
    status = db.Column(Text, default='unknown', nullable=False)
    label_printed = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    template_set = db.relationship('RebrickableSets', lazy='joined')
    parts_in_set = db.relationship(
        'User_Parts', back_populates='user_set', cascade="all, delete-orphan", lazy=True)
    minifigures_in_set = db.relationship(
        'User_Minifigures', back_populates='user_set', cascade="all, delete-orphan", lazy=True)
    user_minifigure_parts = db.relationship(
        'UserMinifigurePart', back_populates='user_set', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<User_Set {self.id} - {self.set_num}>'

    def to_dict(self):
        """Convert the User_Set object to a dictionary."""
        return {'id': self.id, 'set_num': self.set_num, 'status': self.status, 'label_printed': self.label_printed}


class User_Minifigures(db.Model):
    """
    Represents a user's minifigures in a set.
    """
    __tablename__ = 'user_minifigures'

    id = db.Column(Integer, primary_key=True)
    fig_num = db.Column(Text, ForeignKey(
        'rebrickable_minifigs.fig_num'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)

    # Relationships
    user_set = db.relationship('User_Set', back_populates='minifigures_in_set')
    rebrickable_minifig = db.relationship('RebrickableMinifigs', lazy='joined')

    def __repr__(self):
        return f'<User_Minifigures {self.fig_num} - Quantity: {self.quantity}>'


class User_Parts(db.Model):
    """
    Represents the relationship between parts and sets.
    """
    __tablename__ = 'user_parts'

    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey(
        'rebrickable_parts.part_num'), nullable=False)
    color_id = db.Column(Integer, ForeignKey(
        'rebrickable_colors.id'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship('User_Set', back_populates='parts_in_set')
    rebrickable_part = db.relationship('RebrickableParts', lazy='joined')
    rebrickable_color = db.relationship('RebrickableColors', lazy='joined')

    def __repr__(self):
        return f'<User_Parts {self.part_num} - Quantity: {self.quantity}>'


class UserMinifigurePart(db.Model):
    """
    Represents a user's specific collection of minifigure parts.
    Uses RebrickableParts directly instead of MinifigurePart.
    """
    __tablename__ = 'user_minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey(
        'rebrickable_parts.part_num'), nullable=False)
    color_id = db.Column(Integer, ForeignKey(
        'rebrickable_colors.id'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)  # Track ownership
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)
    minifigure_id = db.Column(Integer, ForeignKey(
        'user_minifigures.id'), nullable=False)  # Link to specific minifigure
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship(
        "User_Set", back_populates="user_minifigure_parts")
    user_minifigure = db.relationship("User_Minifigures")
    rebrickable_part = db.relationship('RebrickableParts', lazy='joined')
    rebrickable_color = db.relationship('RebrickableColors', lazy='joined')

    def __repr__(self):
        return f'<UserMinifigurePart {self.part_num} - Quantity: {self.quantity}>'


class PartStorage(db.Model):
    """
    Represents the storage information for parts.
    """
    __tablename__ = 'part_storage'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(Text, ForeignKey(
        'rebrickable_parts.part_num'), nullable=False)
    location = db.Column(Text)
    level = db.Column(Text)
    box = db.Column(Text)
    label_printed = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    rebrickable_part = db.relationship(
        'RebrickableParts', backref='part_storage', lazy='joined')

    def __repr__(self):
        return f'<PartStorage {self.part_num} - Location: {self.location}, Level: {self.level}, Box: {self.box}>'


class RebrickablePartCategories(db.Model):
    """
    Represents categories for Rebrickable parts.
    
    This model stores the category information for LEGO parts as defined by Rebrickable,
    such as 'Brick', 'Plate', 'Technic', etc.
    """
    __tablename__ = 'rebrickable_part_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<RebrickablePartCategory {self.name}>'

    def to_dict(self):
        """Convert the RebrickablePartCategory object to a dictionary."""
        return {'id': self.id, 'name': self.name}


class RebrickableColors(db.Model):
    """
    Represents colors available for LEGO parts from Rebrickable.
    
    This model stores color information including RGB values, transparency status,
    and statistics about how many parts and sets use each color.
    """
    __tablename__ = 'rebrickable_colors'
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
            'id': self.id,
            'name': self.name,
            'rgb': self.rgb,
            'is_trans': self.is_trans,
            'num_parts': self.num_parts,
            'num_sets': self.num_sets,
            'y1': self.y1,
            'y2': self.y2
        }

    # Relationships
    user_parts = db.relationship(
        'User_Parts', back_populates='rebrickable_color', lazy='dynamic')
    user_minifigure_parts = db.relationship(
        'UserMinifigurePart', back_populates='rebrickable_color', lazy='dynamic')


class RebrickableParts(db.Model):
    """
    Represents individual LEGO parts from the Rebrickable database.
    
    This model stores part information including part numbers, names, categories,
    materials, and image URLs for individual LEGO pieces.
    """
    __tablename__ = 'rebrickable_parts'
    part_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    part_cat_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_part_categories.id'), nullable=False)
    part_material = db.Column(db.Text)
    part_img_url = db.Column(db.Text, nullable=True)
    part_url = db.Column(db.Text, nullable=True)

    # Relationships
    category = db.relationship('RebrickablePartCategories', lazy='joined')
    user_parts = db.relationship(
        'User_Parts', back_populates='rebrickable_part', lazy='dynamic')
    user_minifigure_parts = db.relationship(
        'UserMinifigurePart', back_populates='rebrickable_part', lazy='dynamic')

    def __repr__(self):
        return f'<RebrickablePart {self.part_num}>'

    def to_dict(self):
        """Convert the RebrickablePart object to a dictionary."""
        return {
            'part_num': self.part_num,
            'name': self.name,
            'part_cat_id': self.part_cat_id,
            'part_material': self.part_material,
            'part_img_url': self.part_img_url,
            'part_url': self.part_url
        }


class RebrickablePartRelationships(db.Model):
    __tablename__ = 'rebrickable_part_relationships'
    rel_type = db.Column(db.Text, primary_key=True)
    child_part_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_parts.part_num'), primary_key=True)
    parent_part_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_parts.part_num'), primary_key=True)


class RebrickableElements(db.Model):
    __tablename__ = 'rebrickable_elements'
    element_id = db.Column(db.Text, primary_key=True)
    part_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_parts.part_num'), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_colors.id'), nullable=False)
    design_id = db.Column(db.Text)


class RebrickableThemes(db.Model):
    __tablename__ = 'rebrickable_themes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('rebrickable_themes.id'))

    def __repr__(self):
        return f"<Theme {self.name} (ID: {self.id}, Parent: {self.parent_id})>"

    def to_dict(self):
        """Convert the Theme object to a dictionary."""
        return {'id': self.id, 'name': self.name, 'parent_id': self.parent_id}


class RebrickableSets(db.Model):
    __tablename__ = 'rebrickable_sets'
    set_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_themes.id'), nullable=False)
    num_parts = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.Text)

    # Relationships
    user_sets = db.relationship(
        'User_Set', back_populates='template_set', lazy='dynamic')
    theme = db.relationship('RebrickableThemes', lazy='joined')

    def __repr__(self):
        return f'<RebrickableSet {self.set_num} - {self.name}>'

    def to_dict(self):
        """Convert the RebrickableSet object to a dictionary."""
        return {
            'set_num': self.set_num,
            'name': self.name,
            'year': self.year,
            'theme_id': self.theme_id,
            'num_parts': self.num_parts,
            'img_url': self.img_url
        }


class RebrickableMinifigs(db.Model):
    __tablename__ = 'rebrickable_minifigs'
    fig_num = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    num_parts = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.Text)

    # Relationships
    user_minifigures = db.relationship(
        'User_Minifigures', back_populates='rebrickable_minifig', lazy='dynamic')

    def __repr__(self):
        return f'<RebrickableMinifig {self.fig_num} - {self.name}>'


class RebrickableInventories(db.Model):
    __tablename__ = 'rebrickable_inventories'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)
    set_num = db.Column(db.Text, nullable=False)


class RebrickableInventoryParts(db.Model):
    __tablename__ = 'rebrickable_inventory_parts'
    inventory_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_inventories.id'), primary_key=True)
    part_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_parts.part_num'), primary_key=True)
    color_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_colors.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    is_spare = db.Column(db.Boolean, nullable=False,
                         default=False, primary_key=True)
    img_url = db.Column(db.Text)


class RebrickableInventorySets(db.Model):
    __tablename__ = 'rebrickable_inventory_sets'
    inventory_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_inventories.id'), primary_key=True)
    set_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_sets.set_num'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)


class RebrickableInventoryMinifigs(db.Model):
    __tablename__ = 'rebrickable_inventory_minifigs'
    inventory_id = db.Column(db.Integer, db.ForeignKey(
        'rebrickable_inventories.id'), primary_key=True)
    fig_num = db.Column(db.Text, db.ForeignKey(
        'rebrickable_minifigs.fig_num'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
