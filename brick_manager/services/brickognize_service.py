"""
This module provides services for interacting with the Brickognize API.

It includes functions to:

- Get part predictions from the Brickognize API based on an uploaded image.
- Enrich the predictions with additional category information from the SQLite database.
"""
import logging
import requests
from services.sqlite_service import get_category_name_from_part_num
#pylint: disable=W0718

def get_predictions(file_path, filename):
    """
    Get part predictions from the Brickognize API based on an uploaded image.

    Args:
        file_path (str): The file path to the image.
        filename (str): The name of the file.

    Returns:
        dict: The JSON response containing predictions if successful,
              enriched with category names.
        None: If the request fails.
    """
    api_url = "https://api.brickognize.com/predict/"
    headers = {'accept': 'application/json'}

    try:
        # Use 'with' statement to ensure the file is properly closed after use
        with open(file_path, 'rb') as file:
            files = {'query_image': (filename, file, 'image/jpeg')}
            response = requests.post(
                api_url, headers=headers, files=files, timeout=10)

        response.raise_for_status()  # Raise an HTTPError for bad HTTP status codes
        predictions = response.json()

    except requests.exceptions.RequestException as req_err:
        logging.error("Request to Brickognize API failed: %s", req_err)
        return None
    except ValueError:
        logging.error("Error decoding JSON response from the Brickognize API.")
        return None

    # Enrich predictions with category names
    if predictions and 'items' in predictions:
        for item in predictions['items']:
            part_num = item.get('id')  # Assuming 'id' corresponds to part_num
            if part_num:
                try:
                    item['category_name'] = get_category_name_from_part_num(
                        part_num)
                except Exception as db_err:
                    logging.warning(
                        "Failed to retrieve category name for part_num %s: %s", part_num, db_err)
                    item['category_name'] = 'Unknown Category'
            else:
                item['category_name'] = 'Unknown Category'

    return predictions
