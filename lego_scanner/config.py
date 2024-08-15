"""
This module defines the configuration settings for the LEGO Scanner application.

It includes paths for file uploads, allowed file types, and tokens for external APIs.
"""

import os


class Config:  # pylint: disable=R0903
    """
    Configuration settings for the LEGO Scanner application.

    Attributes:
        UPLOAD_FOLDER (str): The directory where uploaded files are stored.
        ALLOWED_EXTENSIONS (set): A set of allowed file extensions for uploads.
        REBRICKABLE_TOKEN (str): The API token for accessing the Rebrickable service.
        MASTER_LOOKUP_PATH (str): The path to the master lookup JSON file.
    """

    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    REBRICKABLE_TOKEN = os.getenv('REBRICKABLE_TOKEN')
    MASTER_LOOKUP_PATH = os.path.join(
        os.getcwd(), 'lookup/master_lookup.json')  # Ensure this path is correct
    SQLALCHEMY_DATABASE_URI = 'sqlite:///lego_scanner.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
