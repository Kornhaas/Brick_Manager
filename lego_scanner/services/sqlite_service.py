"""
This module provides services for interacting with the SQLite database.

"""
from models import Category



def get_category_name_from_db(part_cat_id):
    """
    Fetch the category name from the local database based on the category ID.

    Args:
        part_cat_id (int): The category ID.

    Returns:
        str: The category name if found in the database, 'Unknown Category' otherwise.
    """
    category = Category.query.filter_by(id=part_cat_id).first()
    return category.name if category else 'Unknown Category'
