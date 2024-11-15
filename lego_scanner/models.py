"""
This module defines the database models for the LEGO Scanner Flask application.

It includes the Category model, which represents a category of LEGO parts.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):  # pylint: disable=too-few-public-methods
    """
    Represents a category of LEGO parts.

    Attributes:
        id (int): The unique identifier for the category.
        name (str): The name of the category.
        last_updated (datetime): The timestamp when the category was last updated.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Category {self.name}>'


class Set(db.Model):
    __tablename__ = 'sets'  # Use plural for table names to avoid conflicts with SQL reserved words.
    id = db.Column(db.Integer, primary_key=True)
    set_number = db.Column(db.String(50), unique=True, nullable=False)

    parts = db.relationship('Part', backref='set', lazy=True)


class Part(db.Model):
    __tablename__ = 'parts'
    id = db.Column(db.Integer, primary_key=True)
    part_num = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    color = db.Column(db.String(50))
    color_rgb = db.Column(db.String(6))
    quantity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))
    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), nullable=False)