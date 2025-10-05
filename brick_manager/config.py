"""
This module defines the configuration settings for the Brick Manager application.

It includes paths for file uploads, allowed file types, and tokens for external APIs.
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

    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    SQLALCHEMY_DATABASE_URI = 'sqlite:///brick_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
