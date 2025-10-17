"""
Unit tests for the models module.

This test suite validates the functionality of all database models
in the Lego Manager application.
"""

import pytest
from datetime import datetime
from models import (
    db, RebrickableSets, RebrickableParts, RebrickableColors, 
    RebrickablePartCategories, RebrickableInventories, RebrickableInventoryParts,
    RebrickableMinifigs, RebrickableThemes, User_Set, User_Parts,
    UserMinifigurePart, PartStorage, User_Minifigures
)


class TestRebrickableSets:
    """Test cases for RebrickableSets model."""
    
    def test_create_rebrickable_set(self, app):
        """Test creating a RebrickableSets instance."""
        with app.app_context():
            rebrickable_set = RebrickableSets(
                set_num='10001-1',
                name='Test Set',
                year=2023,
                theme_id=1,
                num_parts=100,
                img_url='http://example.com/image.jpg'
            )
            db.session.add(rebrickable_set)
            db.session.commit()
            
            assert rebrickable_set.set_num is not None
            assert rebrickable_set.set_num == '10001-1'
            assert rebrickable_set.name == 'Test Set'
            assert rebrickable_set.year == 2023
            assert rebrickable_set.num_parts == 100

    def test_rebrickable_set_repr(self, app):
        """Test the string representation of RebrickableSets."""
        with app.app_context():
            rebrickable_set = RebrickableSets(set_num='10001-1', name='Test Set', year=2023, theme_id=1)
            expected = "<RebrickableSet 10001-1 - Test Set>"
            assert repr(rebrickable_set) == expected


class TestRebrickablePartCategories:
    """Test cases for RebrickablePartCategories model."""
    
    def test_create_part_category(self, app):
        """Test creating a RebrickablePartCategories instance."""
        with app.app_context():
            category = RebrickablePartCategories(
                id=1,
                name='Brick'
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.id == 1
            assert category.name == 'Brick'

    def test_part_category_repr(self, app):
        """Test the string representation of RebrickablePartCategories."""
        with app.app_context():
            category = RebrickablePartCategories(id=1, name='Brick')
            expected = "<RebrickablePartCategories(1, 'Brick')>"
            assert repr(category) == expected


class TestRebrickableColors:
    """Test cases for RebrickableColors model."""
    
    def test_create_color(self, app):
        """Test creating a RebrickableColors instance."""
        with app.app_context():
            color = RebrickableColors(
                id=1,
                name='Red',
                rgb='FF0000',
                is_trans=False
            )
            db.session.add(color)
            db.session.commit()
            
            assert color.id == 1
            assert color.name == 'Red'
            assert color.rgb == 'FF0000'
            assert color.is_trans is False

    def test_color_repr(self, app):
        """Test the string representation of RebrickableColors."""
        with app.app_context():
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            expected = "<RebrickableColors(1, 'Red', 'FF0000')>"
            assert repr(color) == expected


class TestRebrickableParts:
    """Test cases for RebrickableParts model."""
    
    def test_create_part(self, app):
        """Test creating a RebrickableParts instance."""
        with app.app_context():
            # First create a category
            category = RebrickablePartCategories(id=1, name='Brick')
            db.session.add(category)
            db.session.commit()
            
            part = RebrickableParts(
                part_num='3001',
                name='Brick 2 x 4',
                part_cat_id=1,
                part_url='http://example.com/part',
                part_img_url='http://example.com/part.jpg'
            )
            db.session.add(part)
            db.session.commit()
            
            assert part.part_num == '3001'
            assert part.name == 'Brick 2 x 4'
            assert part.part_cat_id == 1
            assert part.category.name == 'Brick'

    def test_part_repr(self, app):
        """Test the string representation of RebrickableParts."""
        with app.app_context():
            part = RebrickableParts(part_num='3001', name='Brick 2 x 4')
            expected = "<RebrickableParts('3001', 'Brick 2 x 4')>"
            assert repr(part) == expected


class TestRebrickableInventories:
    """Test cases for RebrickableInventories model."""
    
    def test_create_inventory(self, app):
        """Test creating a RebrickableInventories instance."""
        with app.app_context():
            inventory = RebrickableInventories(
                id=1,
                version=1,
                set_num='10001-1'
            )
            db.session.add(inventory)
            db.session.commit()
            
            assert inventory.id == 1
            assert inventory.version == 1
            assert inventory.set_num == '10001-1'

    def test_inventory_repr(self, app):
        """Test the string representation of RebrickableInventories."""
        with app.app_context():
            inventory = RebrickableInventories(id=1, version=1, set_num='10001-1')
            expected = "<RebrickableInventories(1, 1, '10001-1')>"
            assert repr(inventory) == expected


class TestRebrickableInventoryParts:
    """Test cases for RebrickableInventoryParts model."""
    
    def test_create_inventory_part(self, app):
        """Test creating a RebrickableInventoryParts instance."""
        with app.app_context():
            # Create required dependencies
            inventory = RebrickableInventories(id=1, version=1, set_num='10001-1')
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            db.session.add_all([inventory, color])
            db.session.commit()
            
            inv_part = RebrickableInventoryParts(
                inventory_id=1,
                part_num='3001',
                color_id=1,
                quantity=4,
                is_spare=False,
                img_url='http://example.com/part.jpg'
            )
            db.session.add(inv_part)
            db.session.commit()
            
            assert inv_part.inventory_id == 1
            assert inv_part.part_num == '3001'
            assert inv_part.color_id == 1
            assert inv_part.quantity == 4
            assert inv_part.is_spare is False

    def test_inventory_part_repr(self, app):
        """Test the string representation of RebrickableInventoryParts."""
        with app.app_context():
            inv_part = RebrickableInventoryParts(
                inventory_id=1, part_num='3001', color_id=1, quantity=4
            )
            expected = "<RebrickableInventoryParts(1, '3001', 1, 4)>"
            assert repr(inv_part) == expected


class TestUserSet:
    """Test cases for User_Set model."""
    
    def test_create_user_set(self, app):
        """Test creating a User_Set instance."""
        with app.app_context():
            # Create template set first
            template_set = RebrickableSets(
                set_num='10001-1',
                name='Test Set',
                year=2023,
                theme_id=1,
                num_parts=100
            )
            db.session.add(template_set)
            db.session.commit()
            
            user_set = User_Set(
                set_num=template_set.set_num,
                status='complete'
            )
            db.session.add(user_set)
            db.session.commit()
            
            assert user_set.id is not None
            assert user_set.set_num == template_set.set_num
            assert user_set.status == 'complete'
            assert user_set.template_set.name == 'Test Set'

    def test_user_set_repr(self, app):
        """Test the string representation of User_Set."""
        with app.app_context():
            user_set = User_Set(id=1, set_num='10001-1', status='complete')
            expected = "<User_Set(1, 1, 'complete')>"
            assert repr(user_set) == expected


class TestUserParts:
    """Test cases for User_Parts model."""
    
    def test_create_user_part(self, app):
        """Test creating a User_Parts instance."""
        with app.app_context():
            # Create required dependencies
            theme = RebrickableThemes(id=1, name='Test Theme')
            template_set = RebrickableSets(set_num='10001-1', name='Test Set', year=2023, theme_id=1)
            user_set = User_Set(set_num='10001-1', status='complete')
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            
            db.session.add_all([theme, template_set, color])
            db.session.commit()
            db.session.add(user_set)
            db.session.commit()
            
            user_part = User_Parts(
                user_set_id=user_set.id,
                part_num='3001',
                color_id=1,
                quantity=4,
                have_quantity=2,
                is_spare=False
            )
            db.session.add(user_part)
            db.session.commit()
            
            assert user_part.user_set_id == user_set.id
            assert user_part.part_num == '3001'
            assert user_part.quantity == 4
            assert user_part.have_quantity == 2
            assert user_part.is_spare is False

    def test_user_part_repr(self, app):
        """Test the string representation of User_Parts."""
        with app.app_context():
            user_part = User_Parts(
                user_set_id=1, part_num='3001', color_id=1, quantity=4
            )
            expected = "<User_Parts(1, '3001', 1, 4)>"
            assert repr(user_part) == expected


class TestUserMinifigurePart:
    """Test cases for UserMinifigurePart model."""
    
    def test_create_user_minifigure_part(self, app):
        """Test creating a UserMinifigurePart instance."""
        with app.app_context():
            # Create required dependencies
            template_set = RebrickableSets(set_num='10001-1', name='Test Set')
            user_set = User_Set(set_num='10001-1', status='complete')
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            
            db.session.add_all([template_set, color])
            db.session.commit()
            db.session.add(user_set)
            db.session.commit()
            
            # Create a minifigure first
            minifigure = User_Minifigures(
                fig_num='fig-001',
                quantity=1,
                user_set_id=user_set.id
            )
            db.session.add(minifigure)
            db.session.commit()
            
            minifig_part = UserMinifigurePart(
                user_set_id=user_set.id,
                minifigure_id=minifigure.id,
                part_num='3626',
                color_id=1,
                quantity=1,
                have_quantity=0,
                is_spare=False
            )
            db.session.add(minifig_part)
            db.session.commit()
            
            assert minifig_part.user_set_id == user_set.id
            assert minifig_part.minifigure_id == minifigure.id
            assert minifig_part.part_num == '3626'
            assert minifig_part.quantity == 1
            assert minifig_part.have_quantity == 0

    def test_user_minifigure_part_repr(self, app):
        """Test the string representation of UserMinifigurePart."""
        with app.app_context():
            minifig_part = UserMinifigurePart(
                user_set_id=1, minifigure_id=1, part_num='3626', color_id=1, quantity=1
            )
            expected = "<UserMinifigurePart 3626 - Quantity: 1>"
            assert repr(minifig_part) == expected


class TestPartStorage:
    """Test cases for PartStorage model."""
    
    def test_create_part_storage(self, app):
        """Test creating a PartStorage instance."""
        with app.app_context():
            storage = PartStorage(
                part_num='3001',
                location='Shelf A',
                level='2',
                box='B1'
            )
            db.session.add(storage)
            db.session.commit()
            
            assert storage.id is not None
            assert storage.part_num == '3001'
            assert storage.location == 'Shelf A'
            assert storage.level == '2'
            assert storage.box == 'B1'

    def test_part_storage_repr(self, app):
        """Test the string representation of PartStorage."""
        with app.app_context():
            storage = PartStorage(
                part_num='3001', location='Shelf A', level='2', box='B1'
            )
            expected = "<PartStorage('3001', 'Shelf A', '2', 'B1')>"
            assert repr(storage) == expected


class TestModelRelationships:
    """Test cases for model relationships."""
    
    def test_user_set_parts_relationship(self, app):
        """Test the relationship between User_Set and User_Parts."""
        with app.app_context():
            # Create dependencies
            template_set = RebrickableSets(set_num='10001-1', name='Test Set')
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            db.session.add_all([template_set, color])
            db.session.commit()
            
            user_set = User_Set(set_num=template_set.set_num, status='complete')
            db.session.add(user_set)
            db.session.commit()
            
            # Add parts to the set
            part1 = User_Parts(
                user_set_id=user_set.id, part_num='3001', color_id=1, quantity=4
            )
            part2 = User_Parts(
                user_set_id=user_set.id, part_num='3002', color_id=1, quantity=2
            )
            db.session.add_all([part1, part2])
            db.session.commit()
            
            # Test relationship
            assert len(user_set.parts_in_set) == 2
            assert part1 in user_set.parts_in_set
            assert part2 in user_set.parts_in_set

    def test_part_category_relationship(self, app):
        """Test the relationship between RebrickableParts and RebrickablePartCategories."""
        with app.app_context():
            category = RebrickablePartCategories(id=1, name='Brick')
            db.session.add(category)
            db.session.commit()
            
            part = RebrickableParts(
                part_num='3001', name='Brick 2 x 4', part_cat_id=1
            )
            db.session.add(part)
            db.session.commit()
            
            # Test relationship
            assert part.category == category
            assert part.category.name == 'Brick'

    def test_inventory_parts_relationship(self, app):
        """Test the relationship between RebrickableInventories and RebrickableInventoryParts."""
        with app.app_context():
            inventory = RebrickableInventories(id=1, version=1, set_num='10001-1')
            color = RebrickableColors(id=1, name='Red', rgb='FF0000')
            db.session.add_all([inventory, color])
            db.session.commit()
            
            inv_part1 = RebrickableInventoryParts(
                inventory_id=1, part_num='3001', color_id=1, quantity=4
            )
            inv_part2 = RebrickableInventoryParts(
                inventory_id=1, part_num='3002', color_id=1, quantity=2
            )
            db.session.add_all([inv_part1, inv_part2])
            db.session.commit()
            
            # Test relationship
            assert len(inventory.parts) == 2
            assert inv_part1 in inventory.parts
            assert inv_part2 in inventory.parts