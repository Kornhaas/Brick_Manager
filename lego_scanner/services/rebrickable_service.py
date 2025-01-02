"""
This module provides services for interacting with the Rebrickable API.

It includes functions to:
- Fetch part details from the Rebrickable API.
- Fetch category names based on part category IDs.
- Fetch parts by category from the Rebrickable API.
"""

import time
import requests
from config import Config


class RebrickableAPIException(Exception):
    """Custom exception for errors interacting with the Rebrickable API."""
    pass


class RebrickableService:
    """Service class for interacting with the Rebrickable API."""

    BASE_URL = 'https://rebrickable.com/api/v3/lego/'

    @staticmethod
    def _get_headers():
        """Return common headers for Rebrickable API requests."""
        return {
            'Accept': 'application/json',
            'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
        }

    @staticmethod
    def _make_request(endpoint, params=None, retries=3):
        url = f"{RebrickableService.BASE_URL}{endpoint}"
        headers = RebrickableService._get_headers()
        retry_delay = 30  # Start with 2 seconds

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}: Fetching {url} with params {params}...")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    if response.json().get("detail") == "Invalid page.":
                        print(f"No more data available at {url}.")
                        return None
                elif response.status_code == 429:  # Rate limiting
                    retry_after = int(response.headers.get("Retry-After", retry_delay))
                    print(f"Rate limit hit. Retrying in {retry_after} seconds...")
                    time.sleep(retry_after)
                    retry_delay *= 2
            except requests.exceptions.ReadTimeout:
                print(f"Read timeout on attempt {attempt + 1}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                raise

        raise RebrickableAPIException(f"Failed to fetch data from {url} after {retries} retries.")


    @staticmethod
    def get_all_category_ids():
        """
        Fetches all category IDs and names from the Rebrickable API.

        Returns:
            list: A list of tuples containing category IDs and names.

        Raises:
            RebrickableAPIException: If the API request fails.
        """
        print("Fetching all category IDs...")
        endpoint = 'part_categories/'
        data = RebrickableService._make_request(endpoint)
        return [(category['id'], category['name']) for category in data.get('results', [])]

    @staticmethod
    def get_part_details(part_num):
        """
        Fetch part details from the Rebrickable API based on the part number.

        Args:
            part_num (str): The part number to fetch details for.

        Returns:
            dict: The JSON response containing part details if successful.

        Raises:
            RebrickableAPIException: If the API request fails.
        """
        print(f"Fetching part details for part number: {part_num}...")
        endpoint = f'parts/{part_num}/'
        return RebrickableService._make_request(endpoint)

    @staticmethod
    def get_category_name(part_cat_id):
        """
        Fetch the name of a category from the Rebrickable API based on the part category ID.

        Args:
            part_cat_id (int): The ID of the part category.

        Returns:
            str: The name of the category if successful, 'Unknown Category' otherwise.
        """
        print(f"Fetching category name for category ID: {part_cat_id}...")
        try:
            endpoint = f'part_categories/{part_cat_id}/'
            data = RebrickableService._make_request(endpoint)
            return data.get('name', 'Unknown Category')
        except RebrickableAPIException:
            return 'Unknown Category'

    @staticmethod
    def get_parts_by_category(part_cat_id, page_size=1000, page=1):
        """
        Fetch parts from the Rebrickable API for a given category.

        Args:
            part_cat_id (int): The category ID.
            page_size (int): The number of parts to fetch per page.
            page (int): The page number to fetch.

        Returns:
            dict: A dictionary with parts data and pagination info.

        Raises:
            RebrickableAPIException: If the API request fails.
        """
        print(f"Fetching parts for category ID: {part_cat_id}, Page: {page}...")
        endpoint = 'parts/'
        params = {
            'part_cat_id': part_cat_id,
            'page_size': page_size,
            'page': page
        }
        return RebrickableService._make_request(endpoint, params=params)

    @staticmethod
    def get_parts(filters=None, page=1, page_size=1000, inc_part_details=False):
        """
        Fetch a list of parts from the Rebrickable API.

        Args:
            filters (dict): Filters such as part_num, part_cat_id, etc.
            page (int): Page number to fetch.
            page_size (int): Number of results per page.
            inc_part_details (bool): Whether to include additional part details.

        Returns:
            dict: A dictionary with parts data and pagination info.
        """
        print(f"Fetching parts, Page: {page}, Page Size: {page_size}, Filters: {filters}...")
        endpoint = 'parts/'
        params = filters or {}
        params.update({
            'page': page,
            'page_size': page_size,
            'inc_part_details': int(inc_part_details)
        })
        return RebrickableService._make_request(endpoint, params=params)

    @staticmethod
    def get_colors(page=1, page_size=100):
        """
        Fetch a list of colors from the Rebrickable API.

        Args:
            page (int): Page number to fetch.
            page_size (int): Number of results per page.

        Returns:
            dict: A dictionary with color data and pagination info.
        """
        print(f"Fetching colors, Page: {page}, Page Size: {page_size}...")
        endpoint = 'colors/'
        params = {
            'page': page,
            'page_size': page_size
        }
        return RebrickableService._make_request(endpoint, params=params)

    @staticmethod
    def get_themes(page=1, page_size=100):
        """
        Fetch a list of themes from the Rebrickable API.

        Args:
            page (int): Page number to fetch.
            page_size (int): Number of results per page.

        Returns:
            dict: A dictionary with theme data and pagination info.
        """
        print(f"Fetching themes, Page: {page}, Page Size: {page_size}...")
        endpoint = 'themes/'
        params = {
            'page': page,
            'page_size': page_size
        }
        return RebrickableService._make_request(endpoint, params=params)