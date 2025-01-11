"""
This module defines the SQLAlchemy models for the Brick Manager application.

Models include:
- Category
- Set
- UserSet
- PartInfo
- Color
- Theme
- PartInSet
- Minifigure
- MinifigurePart
- UserMinifigurePart
- PartStorage
"""
#pylint: disable=C0301,R0903

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean

db = SQLAlchemy()


class Category(db.Model):
    """
    Represents a category for parts.
    """
    __tablename__ = 'categories'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    last_updated = db.Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        """Convert the Category object to a dictionary."""
        return {'id': self.id, 'name': self.name, 'last_updated': self.last_updated}


class Set(db.Model):
    """
    Represents a set of parts or models.
    """
    __tablename__ = 'sets'
    id = db.Column(Integer, primary_key=True)
    set_number = db.Column(String, nullable=False)
    name = db.Column(String, nullable=True)
    set_img_url = db.Column(String, nullable=True)

    # Relationships
    user_sets = db.relationship(
        "UserSet", back_populates="template_set", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f'<Set {self.set_number} - {self.name} (ID: {self.id})>'

    def to_dict(self):
        """Convert the Set object to a dictionary."""
        return {'id': self.id, 'set_number': self.set_number, 'name': self.name, 'set_img_url': self.set_img_url}


class UserSet(db.Model):
    """
    Represents a user's collection of sets.
    """
    __tablename__ = 'user_sets'

    id = db.Column(Integer, primary_key=True)
    set_id = db.Column(Integer, ForeignKey('sets.id'), nullable=False)
    status = db.Column(String, default='unknown', nullable=False)

    # Relationships
    template_set = db.relationship('Set', back_populates='user_sets')
    parts_in_set = db.relationship(
        'PartInSet', back_populates='user_set', cascade="all, delete-orphan", lazy=True)
    minifigures = db.relationship(
        'Minifigure', back_populates='user_set', cascade="all, delete-orphan", lazy=True)
    user_minifigure_parts = db.relationship(
        'UserMinifigurePart', back_populates='user_set', cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f'<UserSet {self.id} - {self.template_set.set_number}>'

    def to_dict(self):
        """Convert the UserSet object to a dictionary."""
        return {'id': self.id, 'set_id': self.set_id, 'status': self.status}


class PartInfo(db.Model):
    """
    Represents information about individual parts.
    """
    __tablename__ = 'part_info'

    part_num = db.Column(String, primary_key=True)
    name = db.Column(String, nullable=False)
    category_id = db.Column(Integer, ForeignKey(
        'categories.id'), nullable=True)
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)

    # Relationships
    category = db.relationship('Category', lazy='joined')
    parts_in_sets = db.relationship(
        'PartInSet', back_populates='part_info', lazy='dynamic')

    def __repr__(self):
        return f'<PartInfo {self.part_num} - {self.name}>'

    def to_dict(self):
        """Convert the PartInfo object to a dictionary."""
        return {
            'part_num': self.part_num,
            'name': self.name,
            'category_id': self.category_id,
            'part_img_url': self.part_img_url,
            'part_url': self.part_url,
        }


class Color(db.Model):
    """
    Represents a color used in parts.
    """
    __tablename__ = 'colors'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, nullable=False)
    rgb = db.Column(String, nullable=False)
    is_trans = db.Column(Boolean, nullable=False)

    def __repr__(self):
        return f"<Color {self.name} (ID: {self.id})>"

    def to_dict(self):
        """Convert the Color object to a dictionary."""
        return {'id': self.id, 'name': self.name, 'rgb': self.rgb, 'is_trans': self.is_trans}


class Theme(db.Model):
    """
    Represents a theme for sets or parts.
    """
    __tablename__ = 'themes'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, nullable=False)
    parent_id = db.Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Theme {self.name} (ID: {self.id}, Parent: {self.parent_id})>"

    def to_dict(self):
        """Convert the Theme object to a dictionary."""
        return {'id': self.id, 'name': self.name, 'parent_id': self.parent_id}


class PartInSet(db.Model):
    """
    Represents the relationship between parts and sets.
    """
    __tablename__ = 'parts_in_set'

    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, ForeignKey(
        'part_info.part_num'), nullable=False)
    color = db.Column(String, nullable=False)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship('UserSet', back_populates='parts_in_set')
    part_info = db.relationship('PartInfo', back_populates='parts_in_sets')

    def __repr__(self):
        return f'<PartInSet {self.part_num} - Quantity: {self.quantity}>'


class Minifigure(db.Model):
    """
    Represents a minifigure in a set.
    """
    __tablename__ = 'minifigures'
    id = db.Column(Integer, primary_key=True)
    fig_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    img_url = db.Column(String, nullable=True)
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)

    # Relationships
    user_set = db.relationship("UserSet", back_populates="minifigures")
    parts = db.relationship(
        "MinifigurePart", back_populates="minifigure", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f'<Minifigure {self.fig_num} - {self.name}>'


class MinifigurePart(db.Model):
    """
    Represents individual parts of a minifigure.
    """
    __tablename__ = 'minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    color = db.Column(String, nullable=True)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)
    minifigure_id = db.Column(Integer, ForeignKey(
        'minifigures.id'), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    minifigure = db.relationship("Minifigure", back_populates="parts")

    def __repr__(self):
        return f'<MinifigurePart {self.part_num} - {self.name}>'


class UserMinifigurePart(db.Model):
    """
    Represents a user's specific collection of minifigure parts.
    """
    __tablename__ = 'user_minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    color = db.Column(String, nullable=True)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)  # Track ownership
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)
    user_set_id = db.Column(Integer, ForeignKey(
        'user_sets.id'), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship(
        "UserSet", back_populates="user_minifigure_parts")

    def __repr__(self):
        return f'<UserMinifigurePart {self.part_num} - {self.name}>'


class PartStorage(db.Model):
    """
    Represents the storage information for parts.
    """
    __tablename__ = 'part_storage'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, ForeignKey(
        'part_info.part_num'), nullable=False)
    location = db.Column(String)
    level = db.Column(String)
    box = db.Column(String)

    # Relationships
    part_info = db.relationship(
        'PartInfo', backref='part_storage', lazy='joined')

    def __repr__(self):
        return f'<PartStorage {self.part_num} - Location: {self.location}, Level: {self.level}, Box: {self.box}>'
