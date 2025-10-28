"""
This module provides services for interacting with the Rebrickable API.

It includes functions to:
- Fetch part details from the Rebrickable API.
- Fetch category names based on part category IDs.
- Fetch parts by category from the Rebrickable API.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import requests
from config import Config
from models import (
    RebrickableInventoryParts,
    RebrickablePartCategories,
    RebrickableParts,
)

#pylint: disable=W0107,C0301

class RebrickableAPIException(Exception):
    """Custom exception for errors interacting with the Rebrickable API."""
    pass


class RebrickableService:
    """Service class for interacting with the Rebrickable API."""

    BASE_URL = 'https://rebrickable.com/api/v3/lego/'
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 30

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Return common headers for Rebrickable API requests."""
        return {
            'Accept': 'application/json',
            'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
        }

    @staticmethod
    def _make_request(endpoint: str, params: Optional[Dict] = None, retries: int = MAX_RETRIES) -> Union[Dict, None]:
        """
        Make a request to the Rebrickable API with retry logic.

        Args:
            endpoint (str): API endpoint.
            params (dict): Query parameters.
            retries (int): Number of retry attempts.

        Returns:
            dict: API response JSON.
            None: If no data is available.

        Raises:
            RebrickableAPIException: If the request fails after retries.
        """
        url = f"{RebrickableService.BASE_URL}{endpoint}"
        headers = RebrickableService._get_headers()
        retry_delay = RebrickableService.INITIAL_RETRY_DELAY

        for attempt in range(retries):
            try:
                logging.info("Attempt %d: Fetching %s with params %s",
                             attempt + 1, url, params)
                response = requests.get(
                    url, headers=headers, params=params, timeout=RebrickableService.DEFAULT_TIMEOUT
                )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 404 and response.json().get("detail") == "Invalid page.":
                    logging.warning("No more data available at %s", url)
                    return None

                if response.status_code == 429:  # Rate limiting
                    retry_after = int(response.headers.get(
                        "Retry-After", retry_delay))
                    logging.warning(
                        "Rate limit hit. Retrying in %d seconds...", retry_after)
                    time.sleep(retry_after)
                    retry_delay *= 2

            except requests.exceptions.ReadTimeout:
                logging.error("Read timeout on attempt %d. Retrying in %d seconds...",
                              attempt + 1, retry_delay)
                time.sleep(retry_delay)
                retry_delay *= 2

            except requests.exceptions.RequestException as error:
                logging.error("Request failed: %s", error)
                raise RebrickableAPIException("Request failed") from error

        raise RebrickableAPIException(f"Failed to fetch data from {
                                      url} after {retries} retries.")

    @staticmethod
    def get_all_category_ids() -> List[Tuple[int, str]]:
        """
        Fetch all category IDs and names from the local database table rebrickable_part_categories.

        Returns:
            list: A list of tuples containing category IDs and names.
        """
        categories = RebrickablePartCategories.query.all()
        return [(cat.id, cat.name) for cat in categories]

    @staticmethod
    def get_part_details(part_num: str) -> Dict:
        """
        Fetch part details from the Rebrickable API.

        Args:
            part_num (str): The part number to fetch details for.

        Returns:
            dict: The JSON response containing part details.
        """
        logging.info("Fetching part details for part number: %s", part_num)
        endpoint = f'parts/{part_num}/'
        return RebrickableService._make_request(endpoint)

    @staticmethod
    def get_part_image_url(part_num: str) -> Optional[str]:
        """
        Lookup the first img_url for a part_num in rebrickable_inventory_parts.
        Returns None if not found.
        """
        part_img = RebrickableInventoryParts.query.filter_by(part_num=part_num).first()
        if part_img and part_img.img_url:
            return part_img.img_url
        return None

    @staticmethod
    def get_part_images_bulk(part_nums: List[str]) -> Dict[str, Optional[str]]:
        """
        Bulk lookup img_url for a list of part_nums in rebrickable_inventory_parts.
        Returns a dict mapping part_num to the first found img_url (or None).
        """
        if not part_nums:
            return {}
        # Query all matching rows at once
        rows = RebrickableInventoryParts.query.filter(
            RebrickableInventoryParts.part_num.in_(part_nums)
        ).all()
        # Map part_num to first img_url found
        img_map = {}
        for row in rows:
            if row.part_num not in img_map and row.img_url:
                img_map[row.part_num] = row.img_url
        # Fill missing part_nums with None
        for pn in part_nums:
            img_map.setdefault(pn, None)
        return img_map

    @staticmethod
    def get_parts_by_category(part_cat_id: Union[int, str], page_size: int = 1000, page: int = 1) -> Optional[Dict]:
        """
        Fetch parts for a given category from the local database table rebrickable_parts.

        Args:
            part_cat_id (Union[int, str]): The category ID (can be string or integer).
            page_size (int): Number of parts to fetch per page.
            page (int): The page number to fetch.

        Returns:
            dict: A dictionary with parts data and pagination info.
        """
        try:
            part_cat_id = int(part_cat_id)
        except ValueError as exc:
            logging.error(
                "Invalid category ID: %s. Unable to convert to integer.", part_cat_id
            )
            raise ValueError("Category ID must be an integer.") from exc

        query = RebrickableParts.query.filter_by(part_cat_id=part_cat_id)
        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()
        part_nums = [part.part_num for part in results]
        img_map = RebrickableService.get_part_images_bulk(part_nums)
        parts_list = [
            {
                'part_num': part.part_num,
                'name': part.name,
                'part_cat_id': part.part_cat_id,
                'part_material': part.part_material,
                'part_image_url': img_map.get(part.part_num)
            }
            for part in results
        ]
        return {
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': parts_list
        }

    @staticmethod
    def get_parts(filters: Optional[Dict] = None, page: int = 1, page_size: int = 1000, inc_part_details: bool = False) -> Dict:
        """
        Fetch a list of parts from the Rebrickable API.

        Args:
            filters (dict): Filters such as part_num, part_cat_id, etc.
            page (int): Page number to fetch.
            page_size (int): Number of results per page.
            inc_part_details (bool): Include additional part details.

        Returns:
            dict: A dictionary with parts data and pagination info.
        """
        logging.info(
            "Fetching parts, Page: %d, Page Size: %d, Filters: %s", page, page_size, filters)
        endpoint = 'parts/'
        params = filters or {}
        params.update({'page': page, 'page_size': page_size,
                      'inc_part_details': int(inc_part_details)})
        return RebrickableService._make_request(endpoint, params=params)

    @staticmethod
    def get_colors(page: int = 1, page_size: int = 100) -> Dict:
        """
        Fetch a list of colors from the Rebrickable API.

        Args:
            page (int): Page number to fetch.
            page_size (int): Number of results per page.

        Returns:
            dict: A dictionary with color data and pagination info.
        """
        logging.info("Fetching colors, Page: %d, Page Size: %d",
                     page, page_size)
        endpoint = 'colors/'
        params = {'page': page, 'page_size': page_size}
        return RebrickableService._make_request(endpoint, params=params)

    @staticmethod
    def get_themes(page: int = 1, page_size: int = 100) -> Dict:
        """
        Fetch a list of themes from the Rebrickable API.

        Args:
            page (int): Page number to fetch.
            page_size (int): Number of results per page.

        Returns:
            dict: A dictionary with theme data and pagination info.
        """
        logging.info("Fetching themes, Page: %d, Page Size: %d",
                     page, page_size)
        endpoint = 'themes/'
        params = {'page': page, 'page_size': page_size}
        return RebrickableService._make_request(endpoint, params=params)


# Add aliases for backward compatibility with tests
make_request = RebrickableService._make_request
get_user_sets = RebrickableService.get_parts  # Placeholder - needs actual implementation
get_set_parts = RebrickableService.get_parts  # Placeholder - needs actual implementation
get_missing_parts = RebrickableService.get_parts  # Placeholder - needs actual implementation
get_part_image_url = RebrickableService.get_part_image_url
