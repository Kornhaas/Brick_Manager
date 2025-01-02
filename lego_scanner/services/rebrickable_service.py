"""
This module provides services for interacting with the Rebrickable API 
and populating the local database.
"""

import time
import requests
import logging
from config import Config
from models import db, PartCategory, Part, Color, Set

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RebrickableAPIException(Exception):
    """Custom exception for errors interacting with the Rebrickable API."""


def fetch_paginated_data(api_url, retries=3, **filters):
    """
    Fetch paginated data from the Rebrickable API.
    Handles rate limiting and retries.

    Args:
        api_url (str): The API endpoint URL.
        retries (int): Number of retries for rate-limiting.
        **filters: Additional query parameters.

    Yields:
        dict: Paginated results from the API.
    """
    page = 1
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }
    while True:
        params = {'page': page, **filters}
        try:
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                yield data.get('results', [])
                if not data.get('next'):  # Stop if no more pages
                    break
                page += 1
            elif response.status_code == 429:
                if retries > 0:
                    retry_after = int(response.headers.get("Retry-After", 2))
                    logger.warning(f"Rate limit hit. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    raise RebrickableAPIException("Rate limit retries exhausted.")
            else:
                raise RebrickableAPIException(
                    f"Failed to fetch data: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            raise RebrickableAPIException(f"Error fetching data from API: {e}")


def populate_colors():
    """
    Fetch all colors from the Rebrickable API and populate the colors table.
    """
    logger.info("Starting color population.")
    try:
        for results in fetch_paginated_data('https://rebrickable.com/api/v3/lego/colors/'):
            for color in results:
                color_id = color.get('id')
                if color_id is None:
                    continue

                existing_color = Color.query.filter_by(id=color_id).first()
                if existing_color:
                    existing_color.name = color.get('name', 'Unknown')
                    existing_color.rgb = color.get('rgb')
                    existing_color.is_trans = color.get('is_trans', False)
                else:
                    db.session.add(Color(
                        id=color_id,
                        name=color.get('name', 'Unknown'),
                        rgb=color.get('rgb'),
                        is_trans=color.get('is_trans', False)
                    ))
        db.session.commit()
        logger.info("Colors populated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating colors: {e}")


def populate_themes():
    """
    Fetch all themes from the Rebrickable API and populate the themes table.
    """
    logger.info("Starting theme population.")
    try:
        for results in fetch_paginated_data('https://rebrickable.com/api/v3/lego/themes/'):
            for theme in results:
                theme_id = theme.get('id')
                if theme_id is None:
                    continue

                existing_theme = PartCategory.query.filter_by(id=theme_id).first()
                if existing_theme:
                    existing_theme.name = theme.get('name', 'Unknown')
                    existing_theme.parent_id = theme.get('parent_id')
                else:
                    db.session.add(PartCategory(
                        id=theme_id,
                        name=theme.get('name', 'Unknown'),
                        parent_id=theme.get('parent_id')
                    ))
        db.session.commit()
        logger.info("Themes populated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating themes: {e}")


def populate_sets(theme_id=None):
    """
    Fetch all sets from the Rebrickable API and populate the sets table.

    Args:
        theme_id (int, optional): Filter sets by theme ID.
    """
    logger.info("Starting set population.")
    try:
        for results in fetch_paginated_data('https://rebrickable.com/api/v3/lego/sets/', theme_id=theme_id):
            for set_data in results:
                set_num = set_data.get('set_num')
                if not set_num:
                    continue

                existing_set = Set.query.filter_by(set_num=set_num).first()
                if existing_set:
                    existing_set.name = set_data.get('name', 'Unknown')
                    existing_set.year = set_data.get('year')
                    existing_set.theme_id = set_data.get('theme_id')
                    existing_set.num_parts = set_data.get('num_parts')
                    existing_set.set_img_url = set_data.get('set_img_url')
                    existing_set.set_url = set_data.get('set_url')
                else:
                    db.session.add(Set(
                        set_num=set_num,
                        name=set_data.get('name', 'Unknown'),
                        year=set_data.get('year'),
                        theme_id=set_data.get('theme_id'),
                        num_parts=set_data.get('num_parts'),
                        set_img_url=set_data.get('set_img_url'),
                        set_url=set_data.get('set_url')
                    ))
        db.session.commit()
        logger.info("Sets populated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating sets: {e}")


def populate_part_categories():
    """
    Fetch and populate part categories from the Rebrickable API.
    """
    logger.info("Starting part category population.")
    try:
        for results in fetch_paginated_data('https://rebrickable.com/api/v3/lego/part_categories/'):
            for category in results:
                category_id = category.get('id')
                if category_id is None:
                    continue

                existing_category = PartCategory.query.filter_by(id=category_id).first()
                if existing_category:
                    existing_category.name = category.get('name', 'Unknown')
                else:
                    db.session.add(PartCategory(
                        id=category_id,
                        name=category.get('name', 'Unknown')
                    ))
        db.session.commit()
        logger.info("Part categories populated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating part categories: {e}")

