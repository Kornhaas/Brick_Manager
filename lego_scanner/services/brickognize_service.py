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

    with open(file_path, 'rb') as file:
        files = {'query_image': (filename, file, 'image/jpeg')}
        response = requests.post(api_url, headers=headers, files=files, timeout=10)

    try:
        return response.json()
    except ValueError:
        print("Error decoding JSON response from the API")
        return None
