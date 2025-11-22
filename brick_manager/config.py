"""

This module defines the configuration settings for the Brick Manager application.


It includes paths for file uploads, allowed file types, and tokens for external APIs.
Supports both local development and Docker environments.
"""

import os


class Config:  # pylint: disable=R0903
    """

    Configuration settings for the Brick Manager application.


    Attributes:
        UPLOAD_FOLDER (str): The directory where uploaded files are stored.
        ALLOWED_EXTENSIONS (set): A set of allowed file extensions for uploads.
        REBRICKABLE_TOKEN (str): The API token for accessing the Rebrickable service.
    """

    # Dynamic paths - use environment variables for Docker, fallback for local dev

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Check if running in Docker (data volumes are mounted)
    if os.path.exists("/app/data"):
        # Docker environment - use mounted volumes
        UPLOAD_FOLDER = "/app/data/uploads"
        OUTPUT_FOLDER = "/app/data/output"
        CACHE_FOLDER = "/app/data/cache"
        INSTANCE_FOLDER = "/app/data/instance"
        LOG_FOLDER = "/app/data/logs"
        INSTRUCTIONS_FOLDER = "/app/data/instructions"
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "SQLALCHEMY_DATABASE_URI", "sqlite:////app/data/instance/brick_manager.db"
        )
    else:
        # Local development environment
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
        OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
        CACHE_FOLDER = os.path.join(BASE_DIR, "static", "cache")
        INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")
        LOG_FOLDER = os.path.join(BASE_DIR, "logs")
        INSTRUCTIONS_FOLDER = os.path.join(os.path.dirname(BASE_DIR), "data", "instructions")
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "SQLALCHEMY_DATABASE_URI", f"sqlite:///{INSTANCE_FOLDER}/brick_manager.db"
        )

    # Application settings
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gi"}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REBRICKABLE_TOKEN = os.getenv("REBRICKABLE_TOKEN", "test-token")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # Flask settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    TEMPLATES_AUTO_RELOAD = True

    # Ensure all directories exist
    for folder in [
        UPLOAD_FOLDER,
        OUTPUT_FOLDER,
        CACHE_FOLDER,
        INSTANCE_FOLDER,
        LOG_FOLDER,
        INSTRUCTIONS_FOLDER,
    ]:
        os.makedirs(folder, exist_ok=True)
