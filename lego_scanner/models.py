"""
This module defines the database models for the LEGO Scanner Flask application.

It includes the Category model, which represents a category of LEGO parts.
"""

from datetime import datetime
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
