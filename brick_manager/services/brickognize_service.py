"""

This module provides services for interacting with the Brickognize API.


It includes functions to:

- Get part predictions from the Brickognize API based on an uploaded image.
- Enrich the predictions with additional category information from the SQLite database.
"""
import logging

import requests
from services.sqlite_service import get_category_name_from_part_num

# pylint: disable=W0718


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
    logging.info(
        "Starting Brickognize prediction for file: %s (path: %s)", filename, file_path
    )

    api_url = "https://api.brickognize.com/predict/"
    headers = {"accept": "application/json"}

    logging.debug("API URL: %s", api_url)
    logging.debug("Request headers: %s", headers)

    try:
        # Use 'with' statement to ensure the file is properly closed after use
        logging.debug("Opening file for upload: %s", file_path)
        with open(file_path, "rb") as file:
            files = {"query_image": (filename, file, "image/jpeg")}
            logging.info("Sending POST request to Brickognize API...")
            response = requests.post(api_url, headers=headers, files=files, timeout=10)

        logging.info(
            "Received response from Brickognize API - Status Code: %s",
            response.status_code,
        )
        logging.debug("Response headers: %s", dict(response.headers))

        response.raise_for_status()  # Raise an HTTPError for bad HTTP status codes
        logging.debug("HTTP status check passed")

        predictions = response.json()
        logging.info("Successfully parsed JSON response from Brickognize API")
        logging.debug("Raw predictions data: %s", predictions)

    except requests.exceptions.RequestException as req_err:
        logging.error(
            "Request to Brickognize API failed for file %s: %s", filename, req_err
        )
        logging.error("Request details - URL: %s, Timeout: 10s", api_url)
        return None
    except ValueError as json_err:
        logging.error(
            "Error decoding JSON response from the Brickognize API for file %s: %s",
            filename,
            json_err,
        )
        logging.error(
            "Response content (first 500 chars): %s",
            response.text[:500] if "response" in locals() else "No response available",
        )
        return None
    except FileNotFoundError as file_err:
        logging.error("File not found: %s - %s", file_path, file_err)
        return None
    except Exception as e:
        logging.error(
            "Unexpected error during Brickognize API call for file %s: %s", filename, e
        )
        return None

    # Enrich predictions with category names
    if predictions and "items" in predictions:
        items_count = len(predictions["items"])
        logging.info("Enriching %d prediction items with category names", items_count)

        successful_enrichments = 0
        failed_enrichments = 0

        for idx, item in enumerate(predictions["items"]):
            part_num = item.get("id")  # Assuming 'id' corresponds to part_num
            logging.debug(
                "Processing item %d/%d: part_num=%s", idx + 1, items_count, part_num
            )

            if part_num:
                try:
                    category_name = get_category_name_from_part_num(part_num)
                    item["category_name"] = category_name
                    logging.debug(
                        "Successfully enriched part_num %s with category: %s",
                        part_num,
                        category_name,
                    )
                    successful_enrichments += 1
                except Exception as db_err:
                    logging.warning(
                        "Failed to retrieve category name for part_num %s: %s",
                        part_num,
                        db_err,
                    )
                    item["category_name"] = "Unknown Category"
                    failed_enrichments += 1
            else:
                logging.warning("Item %d has no part_num (id field)", idx + 1)
                item["category_name"] = "Unknown Category"
                failed_enrichments += 1

        logging.info(
            "Category enrichment complete - Success: %d, Failed: %d",
            successful_enrichments,
            failed_enrichments,
        )
    else:
        logging.warning("No items found in predictions or predictions is empty")
        logging.debug("Predictions structure: %s", predictions)

    logging.info("Brickognize prediction process completed for file: %s", filename)
    return predictions


def predict_part(image_path):
    """

    Predict part from image using Brickognize API.


    Args:
        image_path (str): Path to the image file

    Returns:
        dict: Prediction results
    """
    import os

    filename = os.path.basename(image_path)
    return get_predictions(image_path, filename)


def identify_lego_part(image_path):
    """

    Identify LEGO part from image (alias for predict_part).


    Args:
        image_path (str): Path to the image file

    Returns:
        dict: Identification results
    """
    return predict_part(image_path)


def get_part_details(part_id):
    """

    Get detailed information about a part.


    Args:
        part_id (str): Part identifier

    Returns:
        dict: Part details
    """
    # This would typically fetch from database or API

    return {"part_id": part_id, "name": f"Part {part_id}", "category": "Unknown"}
