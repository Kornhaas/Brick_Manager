"""
This module provides services for interacting with the Rebrickable API.

It includes functions to:
- Fetch part details from the Rebrickable API.
- Fetch category names based on part category IDs.
- Fetch parts by category from the Rebrickable API.
"""

import logging
import time
from typing import List, Optional, Dict, Tuple, Union
import requests
from config import Config
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
        Fetch all category IDs and names from the Rebrickable API.

        Returns:
            list: A list of tuples containing category IDs and names.
        """
        logging.info("Fetching all category IDs...")
        endpoint = 'part_categories/'
        data = RebrickableService._make_request(endpoint)
        return [(category['id'], category['name']) for category in data.get('results', [])]

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
    def get_category_name(part_cat_id: int) -> str:
        """
        Fetch the name of a category from the Rebrickable API.

        Args:
            part_cat_id (int): The ID of the part category.

        Returns:
            str: The name of the category or 'Unknown Category' if not found.
        """
        logging.info("Fetching category name for category ID: %d", part_cat_id)
        try:
            endpoint = f'part_categories/{part_cat_id}/'
            data = RebrickableService._make_request(endpoint)
            return data.get('name', 'Unknown Category')
        except RebrickableAPIException:
            return 'Unknown Category'

    @staticmethod
    def get_parts_by_category(part_cat_id: int, page_size: int = 1000, page: int = 1) -> Optional[Dict]:
        """
        Fetch parts for a given category from the Rebrickable API.

        Args:
            part_cat_id (int): The category ID.
            page_size (int): Number of parts to fetch per page.
            page (int): The page number to fetch.

        Returns:
            dict: A dictionary with parts data and pagination info.
        """
        logging.info(
            "Fetching parts for category ID: %d, Page: %d", part_cat_id, page)
        endpoint = 'parts/'
        params = {'part_cat_id': part_cat_id,
                  'page_size': page_size, 'page': page}
        return RebrickableService._make_request(endpoint, params=params)

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
