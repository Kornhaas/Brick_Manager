import os
import requests
from flask import current_app

def cache_image(image_url, cache_dir='static/cache/images'):
    """
    Download and cache an image locally if not already cached.

    Args:
        image_url (str): URL of the image to cache.
        cache_dir (str): Directory to store cached images.

    Returns:
        str: Path to the cached image or fallback image if the download fails.
    """
    fallback_image = "/static/default_image.png"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    filename = os.path.join(cache_dir, os.path.basename(image_url))
    if not os.path.exists(filename):
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                current_app.logger.error(f"Failed to download image: {image_url}")
                return fallback_image
        except Exception as e:
            current_app.logger.error(f"Error downloading image {image_url}: {e}")
            return fallback_image

    return f"/{filename}"
