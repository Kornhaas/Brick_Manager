"""
This module provides services for interacting with the Rebrickable API 
and the Brickognize API.

It includes functions to:
- Fetch part details from the Rebrickable API.
- Fetch category names based on part category IDs.
- Get part predictions from the Brickognize API based on an uploaded image.
"""
import time
import requests
from config import Config
from models import Category


class RebrickableAPIException(Exception):
    """Custom exception for errors interacting with the Rebrickable API."""


def get_all_category_ids_from_api():
    """
    Fetches all category IDs and names from the Rebrickable API.

    Returns:
        list: A list of tuples containing category IDs and names.

    Raises:
        RebrickableAPIException: If the API request fails.
    """
    url = 'https://rebrickable.com/api/v3/lego/part_categories/'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return [(category['id'], category['name']) for category in data['results']]

    raise RebrickableAPIException(
        f"Failed to fetch category IDs: {response.status_code}")


def get_part_details(part_num):
    """
    Fetch part details from the Rebrickable API based on the part number.

    Args:
        part_num (str): The part number to fetch details for.

    Returns:
        dict: The JSON response containing part details if successful.
        None: If the request fails.
    """
    print(f"Fetching part details for {part_num}")
    url = f'https://rebrickable.com/api/v3/lego/parts/{part_num}/'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        return response.json()

    print(f"Failed to fetch part details for {part_num}: {response.status_code}")
    return None


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


def get_category_name(part_cat_id):
    """
    Fetch the name of a category from the Rebrickable API based on the part category ID.

    Args:
        part_cat_id (str): The ID of the part category.

    Returns:
        str: The name of the category if successful, 'Unknown Category' otherwise.
    """
    url = f'https://rebrickable.com/api/v3/lego/part_categories/{part_cat_id}/'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }

    retries = 3

    for _ in range(retries):
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('name', 'Unknown Category')
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            print(f"Rate limit hit. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            print(f"Failed to fetch category name for {part_cat_id}: {response.status_code}")
            return 'Unknown Category'
    return 'Unknown Category'


def get_predictions(file_path, filename):
    """
    Get part predictions from the Brickognize API based on an uploaded image.

    Args:
        file_path (str): The file path to the image.
        filename (str): The name of the file.

    Returns:
        dict: The JSON response containing predictions if successful.
        None: If the request fails.
    """
    api_url = "https://api.brickognize.com/predict/"
    headers = {'accept': 'application/json'}

    # Use 'with' statement to ensure the file is properly closed after use
    with open(file_path, 'rb') as file:
        files = {'query_image': (filename, file, 'image/jpeg')}
        response = requests.post(
            api_url, headers=headers, files=files, timeout=10)

    try:
        return response.json()
    except ValueError:
        print("Error decoding JSON response from the API")
        return None
