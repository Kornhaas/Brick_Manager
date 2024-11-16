from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


class Set(db.Model):
    __tablename__ = 'sets'
    id = db.Column(db.Integer, primary_key=True)  # Internal unique identifier
    set_number = db.Column(db.String(50), nullable=False)  # LEGO set number
    parts = db.relationship('Part', backref='set', lazy=True)

    def __repr__(self):
        return f'<Set {self.set_number} (ID: {self.id})>'


class Part(db.Model):
    __tablename__ = 'parts'
    id = db.Column(db.Integer, primary_key=True)
    part_num = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    color = db.Column(db.String(50))
    color_rgb = db.Column(db.String(6))
    quantity = db.Column(db.Integer, nullable=False)  # Required quantity
    have_quantity = db.Column(db.Integer, default=0)  # Quantity owned
    location = db.Column(db.String(100))
    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), nullable=False)

    def __repr__(self):
        return f'<Part {self.part_num} - {self.name}>'