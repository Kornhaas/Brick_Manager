import os
import requests
from flask import current_app, url_for

def cache_image(image_url, cache_dir='static/cache/images'):
    """
    Download and cache an image locally if not already cached.

    Args:
        image_url (str): URL of the image to cache.
        cache_dir (str): Directory to store cached images.

    Returns:
        str: Path to the cached image or fallback image if the download fails.
    """
    # Use Flask's url_for to get a fallback image path
    fallback_image = url_for('static', filename='default_image.png', _external=True)

    # Handle invalid or missing image_url
    if not image_url or not isinstance(image_url, str):
        current_app.logger.warning("Invalid or missing image URL. Using fallback image.")
        return fallback_image

    # Ensure the cache directory exists
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Generate the local file path for caching
    filename = os.path.basename(image_url)
    cached_path = os.path.join(cache_dir, filename)

    # Check if the image is already cached
    if not os.path.exists(cached_path):
        try:
            # Attempt to download the image
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(cached_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                current_app.logger.error(f"Failed to download image: {image_url} (Status: {response.status_code})")
                return fallback_image
        except Exception as e:
            current_app.logger.error(f"Error downloading image {image_url}: {e}")
            return fallback_image

    # Generate a URL for the cached image
    return url_for('static', filename=f'cache/images/{filename}', _external=True)
