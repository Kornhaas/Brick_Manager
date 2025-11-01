"""

This module defines the main route for the Brick Manager application.


It includes:
- A route to render the index (home) page.
- Health check endpoint for Docker monitoring.
- Cached image serving endpoint.
"""

import os

from flask import Blueprint, abort, current_app, jsonify, render_template, send_file
from models import db
from sqlalchemy import text

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """

    Render the index (home) page.


    Returns:
        Response: Renders the index.html template.
    """
    return render_template("index.html")


@main_bp.route("/health")
def health_check():
    """

    Health check endpoint for Docker monitoring.


    Returns:
        JSON response indicating application health status.
    """
    try:
        # Test database connection
        db.session.execute(text("SELECT 1"))
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "healthy",
                    "message": "Application is running properly",
                    "database": "connected",
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "message": f"Health check failed: {str(e)}",
                    "database": "disconnected",
                }
            ),
            500,
        )


@main_bp.route("/cache/images/<filename>")
def serve_cached_image(filename):
    """

    Serve cached images from the cache directory.


    Args:
        filename (str): Name of the cached image file

    Returns:
        Response: The cached image file or 404 if not found
    """
    try:
        # Get the configured cache directory
        if hasattr(current_app, "config") and "CACHE_FOLDER" in current_app.config:
            cache_dir = os.path.join(current_app.config["CACHE_FOLDER"], "images")
        else:
            # Fallback for local development
            cache_dir = "static/cache/images"

        # Validate filename for security
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            abort(404)

        # Construct full file path
        file_path = os.path.join(cache_dir, filename)

        # Check if file exists and serve it
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        else:
            abort(404)

    except Exception as e:
        current_app.logger.error(f"Error serving cached image {filename}: {e}")
        abort(404)


@main_bp.route("/debug/cache")
def debug_cache():
    """

    Debug endpoint to test cache functionality.


    Returns:
        JSON: Cache status and test results
    """
    try:
        from services.cache_service import cache_image, get_cache_directory

        # Get cache directory info
        cache_dir = get_cache_directory()
        cache_exists = os.path.exists(cache_dir)
        cache_writable = os.access(cache_dir, os.W_OK) if cache_exists else False

        # List existing cached files
        cached_files = []
        if cache_exists:
            cached_files = [
                f
                for f in os.listdir(cache_dir)
                if os.path.isfile(os.path.join(cache_dir, f))
            ]

        # Test cache with a real external image URL
        test_result = "Not tested"
        try:
            # Use a simple external image that should work
            test_url = "https://httpbin.org/image/png"
            current_app.logger.info(f"Testing cache with URL: {test_url}")
            cached_url = cache_image(test_url)
            test_result = f"Success: {cached_url}"
        except Exception as e:
            test_result = f"Failed: {str(e)}"

        # Re-check cached files after test
        cached_files_after_test = []
        if cache_exists:
            cached_files_after_test = [
                f
                for f in os.listdir(cache_dir)
                if os.path.isfile(os.path.join(cache_dir, f))
            ]

        return jsonify(
            {
                "cache_directory": cache_dir,
                "cache_exists": cache_exists,
                "cache_writable": cache_writable,
                "cached_files_count_before": len(cached_files),
                "cached_files_count_after": len(cached_files_after_test),
                "cached_files_before": cached_files[:10],  # First 10 files before test
                "cached_files_after": cached_files_after_test[
                    :10
                ],  # First 10 files after test
                "config_cache_folder": current_app.config.get(
                    "CACHE_FOLDER", "Not configured"
                ),
                "test_result": test_result,
                "docker_environment": os.path.exists("/app/data"),
            }
        )

    except Exception as e:
        return (
            jsonify({"error": str(e), "cache_directory": "Error getting directory"}),
            500,
        )
