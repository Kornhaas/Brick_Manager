"""
This module handles caching of images locally to optimize retrieval and reduce repeated downloads.
"""

import os
from urllib.parse import urlparse

import requests
from flask import current_app, url_for
from werkzeug.utils import secure_filename

# pylint: disable=W0718


def get_cache_directory():
    """
    Get the configured cache directory from Flask config.

    Returns:
        str: Path to the cache directory
    """
    if hasattr(current_app, "config") and "CACHE_FOLDER" in current_app.config:
        cache_dir = current_app.config["CACHE_FOLDER"]
        # Ensure images subdirectory exists
        images_cache_dir = os.path.join(cache_dir, "images")
        os.makedirs(images_cache_dir, exist_ok=True)
        return images_cache_dir
    else:
        # Fallback to static directory for local development
        fallback_dir = "static/cache/images"
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir


def is_valid_url(url):
    """
    Validate that a given URL is well-formed and has a scheme and netloc.
    Args:
        url (str): The URL to validate.
    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def cache_image(image_url, cache_dir=None):
    """
    Download and cache an image locally if not already cached.

    Args:
        image_url (str): URL of the image to cache.
        cache_dir (str, optional): Directory to store cached images.
                                 If None, uses configured CACHE_FOLDER.

    Returns:
        str: Path to the cached image or fallback image if the download fails.
    """
    # Define the fallback image using Flask's url_for
    fallback_image = url_for("static", filename="default_image.png", _external=True)

    # Validate the image URL
    if not image_url or not isinstance(image_url, str) or not is_valid_url(image_url):
        current_app.logger.warning(
            "Invalid or missing image URL. Using fallback image."
        )
        return fallback_image

    # Use configured cache directory if not specified
    if cache_dir is None:
        cache_dir = get_cache_directory()

    try:
        # Normalize the cache directory path
        abs_cache_dir = os.path.abspath(cache_dir)
        os.makedirs(abs_cache_dir, exist_ok=True)

        # Extract and secure the filename from the URL
        raw_filename = os.path.basename(urlparse(image_url).path)
        filename = secure_filename(raw_filename)  # Sanitize the filename

        if not filename:
            current_app.logger.warning(
                f"Invalid filename from URL: {image_url}. Using fallback image."
            )
            return fallback_image

        # Generate the full local file path for caching
        cached_path = os.path.normpath(os.path.join(abs_cache_dir, filename))

        # Validate the cached path
        abs_cached_path = os.path.abspath(cached_path)

        # Cross-platform validation to ensure cached path resides within cache_dir
        if not abs_cached_path.startswith(abs_cache_dir):
            current_app.logger.error(
                f"Potential path traversal detected: {abs_cached_path}"
            )
            return fallback_image

        # Check for drive mismatch on Windows
        if os.name == "nt":  # Windows-specific drive validation
            cache_drive, _ = os.path.splitdrive(abs_cache_dir)
            cached_drive, _ = os.path.splitdrive(abs_cached_path)
            if cache_drive != cached_drive:
                current_app.logger.error(
                    f"Paths are on different drives: {abs_cached_path} vs {abs_cache_dir}"
                )
                return fallback_image

        # Check if the image is already cached
        if not os.path.exists(abs_cached_path):
            current_app.logger.info(f"Downloading image: {image_url}")
            try:
                response = requests.get(image_url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(abs_cached_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            f.write(chunk)
                    current_app.logger.info(
                        f"Image successfully cached: {abs_cached_path}"
                    )
                else:
                    current_app.logger.error(
                        f"Failed to download image {image_url}. Status Code: {response.status_code}"
                    )
                    return fallback_image
            except requests.exceptions.RequestException as req_err:
                current_app.logger.error(
                    f"Request error while downloading image {image_url}: {req_err}"
                )
                return fallback_image
        else:
            current_app.logger.debug(f"Using cached image: {abs_cached_path}")

        # Return the URL for the cached image
        # Use the cache serving route for Docker environment
        if hasattr(current_app, "config") and "CACHE_FOLDER" in current_app.config:
            # Docker environment - use cache serving route
            return url_for("main.serve_cached_image", filename=filename, _external=True)
        else:
            # Local development - use static file serving
            rel_cached_path = os.path.relpath(
                abs_cached_path, os.path.abspath("static")
            )
            return url_for(
                "static", filename=rel_cached_path.replace(os.sep, "/"), _external=True
            )

    except requests.exceptions.RequestException as req_err:
        current_app.logger.error(
            f"Request error while downloading image {image_url}: {req_err}"
        )
    except Exception as e:
        current_app.logger.error(
            f"Unexpected error while caching image {image_url}: {e}"
        )

    # Return fallback image in case of errors
    return fallback_image


def get_cached_image_path(image_url, cache_dir=None):
    """
    Get the path to a cached image without downloading it.

    Args:
        image_url (str): The URL of the image
        cache_dir (str, optional): Directory where cached images are stored.
                                  If None, uses configured CACHE_FOLDER.

    Returns:
        str: Path to the cached image if it exists, None otherwise
    """
    if not is_valid_url(image_url):
        return None

    filename = image_url.split("/")[-1]
    if not filename or "." not in filename:
        return None

    # Use configured cache directory if not specified
    if cache_dir is None:
        cache_dir = get_cache_directory()

    cache_path = os.path.join(cache_dir, filename)
    if os.path.exists(cache_path):
        return cache_path
    return None
