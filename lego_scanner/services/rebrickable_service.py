"""
This module provides services for interacting with the Rebrickable API and the Brickognize API.

It includes functions to:
- Fetch part details from the Rebrickable API.
- Fetch category names based on part category IDs.
- Get part predictions from the Brickognize API based on an uploaded image.
"""

import requests
from config import Config


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

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        return response.json().get('name', 'Unknown Category')

    print(f"Failed to fetch category name for {
          part_cat_id}: {response.status_code}")
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
