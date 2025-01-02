from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# Core Template Database Tables
class Theme(db.Model):
    __tablename__ = 'themes'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(40), nullable=False)
    parent_id = db.Column(Integer, db.ForeignKey('themes.id'), nullable=True)

    parent = db.relationship('Theme', remote_side=[id], backref='subthemes')

    def __repr__(self):
        return f'<Theme {self.name}>'


class PartCategory(db.Model):
    __tablename__ = 'part_categories'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)

    def __repr__(self):
        return f'<PartCategory {self.name}>'


class Part(db.Model):
    __tablename__ = 'parts'
    part_num = db.Column(String(20), primary_key=True)
    name = db.Column(String(250), nullable=False)
    part_cat_id = db.Column(Integer, ForeignKey('part_categories.id'), nullable=True)
    part_url = db.Column(String, nullable=True)  # URL for the part
    part_img_url = db.Column(String, nullable=True)  # Image URL for the part
    print_of = db.Column(String(20), nullable=True)  # Reference to another part (e.g., printed version)
    
    category = relationship('PartCategory', backref='parts')

    def __repr__(self):
        return f'<Part {self.part_num} - {self.name}>'


class Set(db.Model):
    __tablename__ = 'sets'
    set_num = db.Column(String(20), primary_key=True)
    name = db.Column(String(256), nullable=True)
    year = db.Column(Integer, nullable=True)
    theme_id = db.Column(Integer, db.ForeignKey('themes.id'), nullable=True)
    num_parts = db.Column(Integer, nullable=True)
    set_img_url = db.Column(String, nullable=True)
    set_url = db.Column(String, nullable=True)

    theme = db.relationship('Theme', backref='sets')

    def __repr__(self):
        return f'<Set {self.set_num} - {self.name}>'


class Inventory(db.Model):
    __tablename__ = 'inventories'
    id = db.Column(Integer, primary_key=True)
    version = db.Column(Integer, nullable=False)
    set_num = db.Column(String(20), ForeignKey('sets.set_num'), nullable=False)

    set = relationship('Set', backref='inventories')

    def __repr__(self):
        return f'<Inventory {self.id} - Set {self.set_num}>'


class InventoryPart(db.Model):
    __tablename__ = 'inventory_parts'
    id = db.Column(Integer, primary_key=True)
    inventory_id = db.Column(Integer, ForeignKey('inventories.id'), nullable=False)
    part_num = db.Column(String(20), ForeignKey('parts.part_num'), nullable=False)
    color_id = db.Column(Integer, ForeignKey('colors.id'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    is_spare = db.Column(Boolean, default=False)

    inventory = relationship('Inventory', backref='inventory_parts')
    part = relationship('Part', backref='inventory_parts')
    color = relationship('Color', backref='inventory_parts')

    def __repr__(self):
        return f'<InventoryPart {self.part_num} - {self.quantity}>'


class Color(db.Model):
    __tablename__ = 'colors'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    rgb = db.Column(String(6), nullable=True)
    is_trans = db.Column(Boolean, default=False)

    def __repr__(self):
        return f'<Color {self.name}>'


class Minifig(db.Model):
    __tablename__ = 'minifigs'
    fig_num = db.Column(String(20), primary_key=True)
    name = db.Column(String(256), nullable=False)
    num_parts = db.Column(Integer, nullable=True)

    def __repr__(self):
        return f'<Minifig {self.fig_num} - {self.name}>'


# User-Specific Tables
class UserSet(db.Model):
    __tablename__ = 'user_sets'
    id = db.Column(Integer, primary_key=True)
    set_num = db.Column(String(20), ForeignKey('sets.set_num'), nullable=False)
    status = db.Column(String, default='unknown', nullable=False)

    set = relationship('Set', backref='user_sets')
    parts = relationship("PartSetMapping", back_populates="user_set", cascade="all, delete-orphan", lazy=True)
    user_minifigures = relationship("UserMinifigure", back_populates="user_set", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<UserSet {self.id} - Set {self.set_num}>'


class PartSetMapping(db.Model):
    __tablename__ = 'part_set_mapping'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String(20), ForeignKey('parts.part_num'), nullable=False)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    user_set = relationship('UserSet', back_populates='parts')
    part = relationship('Part', backref='part_mappings')

    def __repr__(self):
        return f'<PartSetMapping Part: {self.part_num}, Set: {self.user_set_id}, Quantity: {self.quantity}>'


class PartStorage(db.Model):
    __tablename__ = 'part_storage'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String(20), ForeignKey('parts.part_num'), nullable=False)
    location = db.Column(String, nullable=False)
    level = db.Column(String, nullable=False)
    box = db.Column(String, nullable=False)

    part = relationship('Part', backref='storage')

    def __repr__(self):
        return f'<PartStorage {self.part_num} - Location: {self.location}, Level: {self.level}, Box: {self.box}>'


class UserMinifigure(db.Model):
    __tablename__ = 'user_minifigures'
    id = db.Column(Integer, primary_key=True)
    fig_num = db.Column(String(20), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)

    user_set = relationship('UserSet', back_populates='user_minifigures')

    def __repr__(self):
        return f'<UserMinifigure {self.fig_num}>'


class UserMinifigurePart(db.Model):
    __tablename__ = 'user_minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String(20), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)
    is_spare = db.Column(Boolean, default=False, nullable=False)

    user_set = relationship('UserSet', backref='user_minifigure_parts')

    def __repr__(self):
        return f'<UserMinifigurePart {self.part_num}>'
