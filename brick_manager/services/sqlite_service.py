"""
This module provides services for interacting with the SQLite database.

"""
import logging
from models import RebrickableParts, RebrickablePartCategories


def get_category_name_from_db(part_cat_id):
    """
    Fetch the category name from the local database based on the category ID.

    Args:
        part_cat_id (int): The category ID.

    Returns:
        str: The category name if found in the database, 'Unknown Category' otherwise.
    """
    logging.debug("Fetching category name for part_cat_id: %s", part_cat_id)
    
    try:
        category = RebrickablePartCategories.query.filter_by(id=part_cat_id).first()
        
        if category:
            logging.debug("Successfully found category: %s for part_cat_id: %s", category.name, part_cat_id)
            return category.name
        else:
            logging.warning("No category found for part_cat_id: %s", part_cat_id)
            return 'Unknown Category'
            
    except Exception as e:
        logging.error("Database error while fetching category for part_cat_id %s: %s", part_cat_id, e)
        return 'Unknown Category'


def get_category_name_from_part_num(part_num):
    """
    Fetch the category name based on the part number.

    Args:
        part_num (str): The part number.

    Returns:
        str: The category name if found, 'Unknown Category' otherwise.
    """
    logging.debug("Fetching category name for part_num: %s", part_num)
    
    try:
        # Query RebrickableParts for the part_num
        logging.debug("Querying RebrickableParts table for part_num: %s", part_num)
        part_info = RebrickableParts.query.filter_by(part_num=part_num).first()
        
        if not part_info:
            logging.warning("No part found in RebrickableParts for part_num: %s", part_num)
            return 'Unknown Category'
            
        if not part_info.part_cat_id:
            logging.warning("No part_cat_id found for part_num: %s", part_num)
            return 'Unknown Category'
        
        logging.debug("Found part_cat_id: %s for part_num: %s", part_info.part_cat_id, part_num)
        
        # Query RebrickablePartCategories for the part_cat_id
        logging.debug("Querying RebrickablePartCategories table for part_cat_id: %s", part_info.part_cat_id)
        category = RebrickablePartCategories.query.filter_by(id=part_info.part_cat_id).first()
        
        if category:
            logging.debug("Found category: %s for part_num: %s (part_cat_id: %s)", 
                         category.name, part_num, part_info.part_cat_id)
            return category.name
        else:
            logging.warning("No category found for part_cat_id: %s (part_num: %s)", 
                           part_info.part_cat_id, part_num)
            return 'Unknown Category'
            
    except Exception as e:
        logging.error("Database error while fetching category for part_num %s: %s", part_num, e)
        return 'Unknown Category'
