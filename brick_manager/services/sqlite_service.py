"""
This module provides services for interacting with the SQLite database.

"""
from models import PartInfo, Category



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


def get_category_name_from_part_num(part_num):
    """
    Fetch the category name based on the part number.

    Args:
        part_num (str): The part number.

    Returns:
        str: The category name if found, 'Unknown Category' otherwise.
    """
    # Query PartInfo for the part_num
    part_info = PartInfo.query.filter_by(part_num=part_num).first()
    if not part_info or not part_info.category_id:
        print(f"No category_id found for part_num: {part_num}")  # Debug log
        return 'Unknown Category'

    # Query Category for the category_id
    category = Category.query.filter_by(id=part_info.category_id).first()
    if category:
        print(f"Found category: {category.name} for part_num: {part_num}")  # Debug log
        return category.name

    print(f"No category found for category_id: {part_info.category_id}")  # Debug log
    return 'Unknown Category'
