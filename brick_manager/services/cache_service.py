"""
This module handles caching of images locally to optimize retrieval and reduce repeated downloads.
"""

import os
import requests
from flask import current_app, url_for
#pylint: disable=W0718

def cache_image(image_url, cache_dir='static/cache/images'):
    """
    Download and cache an image locally if not already cached.

    Args:
        image_url (str): URL of the image to cache.
        cache_dir (str): Directory to store cached images.

    Returns:
        str: Path to the cached image or fallback image if the download fails.
    """
    # Define the fallback image using Flask's url_for
    fallback_image = url_for(
        'static', filename='default_image.png', _external=True)

    # Validate the image URL
    if not image_url or not isinstance(image_url, str):
        current_app.logger.warning(
            "Invalid or missing image URL. Using fallback image.")
        return fallback_image

    try:
        # Ensure the cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Generate the local file path for caching
        filename = os.path.basename(image_url)
        if not filename:
            current_app.logger.warning(f"Failed to extract filename from URL: {
                                       image_url}. Using fallback image.")
            return fallback_image

        cached_path = os.path.join(cache_dir, filename)

        # Check if the image is already cached
        if not os.path.exists(cached_path):
            current_app.logger.info(f"Downloading image: {image_url}")
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(cached_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                current_app.logger.info(
                    f"Image successfully cached: {cached_path}")
            else:
                current_app.logger.error(
                    f"Failed to download image {image_url}. Status Code: {response.status_code}")
                return fallback_image

        # Return the URL for the cached image
        return url_for('static', filename=f'cache/images/{filename}', _external=True)

    except requests.exceptions.RequestException as req_err:
        current_app.logger.error(f"Request error while downloading image {
                                 image_url}: {req_err}")
    except Exception as e:
        current_app.logger.error(
            f"Unexpected error while caching image {image_url}: {e}")

    # Return fallback image in case of errors
    return fallback_image
