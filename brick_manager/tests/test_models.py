"""

Unit tests for the models module.


This test suite validates the functionality of all database models
in the Bricks Manager application.
"""

from models import RebrickableSets, db


class TestRebrickableSets:
    """Test cases for RebrickableSets model."""

    def test_create_rebrickable_set(self, app):
        """Test creating a RebrickableSets instance."""
        with app.app_context():
            rebrickable_set = RebrickableSets(
                set_num="10001-1",
                name="Test Set",
                year=2023,
                theme_id=1,
                num_parts=100,
                img_url="http://example.com/image.jpg",
            )
            db.session.add(rebrickable_set)
            db.session.commit()

            assert rebrickable_set.set_num is not None
            assert rebrickable_set.set_num == "10001-1"
            assert rebrickable_set.name == "Test Set"
            assert rebrickable_set.year == 2023
            assert rebrickable_set.num_parts == 100

    def test_rebrickable_set_repr(self, app):
        """Test the string representation of RebrickableSets."""
        with app.app_context():
            rebrickable_set = RebrickableSets(
                set_num="10001-1", name="Test Set", year=2023, theme_id=1
            )
            expected = "<RebrickableSet 10001-1 - Test Set>"
            assert repr(rebrickable_set) == expected
