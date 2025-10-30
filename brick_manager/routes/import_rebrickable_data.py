"""
This module handles the loading and updating of Brick data (categories, parts, colors, and themes)
from Rebrickable CSV files into the local SQLite database.
"""

import gzip
import logging
import os
import shutil

import pandas as pd
import requests
from flask import Blueprint, jsonify, render_template, request
from models import db

# pylint: disable=C0301,W0718
import_rebrickable_data_bp = Blueprint("import_rebrickable_data", __name__)

BASE_URL = "https://cdn.rebrickable.com/media/downloads"
IMPORT_DIR = "import"

FILES = [
    "part_categories.csv.gz",
    "colors.csv.gz",
    "parts.csv.gz",
    "part_relationships.csv.gz",
    "elements.csv.gz",
    "themes.csv.gz",
    "sets.csv.gz",
    "minifigs.csv.gz",
    "inventories.csv.gz",
    "inventory_parts.csv.gz",
    "inventory_sets.csv.gz",
    "inventory_minifigs.csv.gz",
]


def download_and_extract_csv(file_name):
    """
    Download and extract a gzipped CSV file from Rebrickable.

    Args:
        file_name (str): Name of the gzipped file to download

    Returns:
        str: Path to the extracted CSV file
    """
    os.makedirs(IMPORT_DIR, exist_ok=True)
    gz_path = os.path.join(IMPORT_DIR, file_name)
    csv_path = os.path.join(IMPORT_DIR, file_name.replace(".gz", ""))
    url = f"{BASE_URL}/{file_name}"
    logging.info(f"Downloading {url} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(gz_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    logging.info(f"Extracting {gz_path} ...")
    with gzip.open(gz_path, "rb") as f_in:
        with open(csv_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(gz_path)
    return csv_path


def ensure_table_structure():
    """
    Ensures all tables are created with proper SQLAlchemy model definitions
    This preserves primary keys, foreign keys, and other constraints
    """
    logging.info("Ensuring database tables match model definitions...")
    db.create_all()
    logging.info("✅ All tables are properly structured")


def import_csv_to_sqlite(csv_path, model_class):
    """
    Import CSV data into SQLite database using SQLAlchemy model.

    Args:
        csv_path (str): Path to the CSV file to import
        model_class: SQLAlchemy model class to import data into
    """
    logging.info(f"Importing {csv_path} into {model_class.__tablename__} ...")

    # Read the CSV data
    df = pd.read_csv(csv_path)

    # First, ensure the table exists with proper SQLAlchemy constraints
    # This will create the table with correct primary keys, foreign keys, etc.
    db.create_all()

    # Clear existing data but preserve table structure using SQLAlchemy
    try:
        # Use SQLAlchemy's delete method to maintain proper constraints
        db.session.query(model_class).delete()
        db.session.commit()
        logging.info(f"Cleared existing data from {model_class.__tablename__}")
    except Exception as e:
        logging.warning(f"Could not clear table {model_class.__tablename__}: {e}")
        db.session.rollback()

    # Import data while preserving table structure
    # Use 'append' instead of 'replace' to keep the SQLAlchemy-created structure
    df.to_sql(model_class.__tablename__, db.engine, if_exists="append", index=False)

    # Clean up the CSV file
    os.remove(csv_path)

    logging.info(
        f"Successfully imported {len(df)} records into {model_class.__tablename__}"
    )


@import_rebrickable_data_bp.route("/import_data", methods=["GET", "POST"])
def import_data():
    """
    Load and update Brick data (categories, parts, colors, and themes)
    from the Rebrickable API into the local database.

    Handles POST requests to fetch and store categories, parts, colors, and themes in the database.
    """
    if request.method == "POST":
        try:
            # First ensure all tables have proper structure
            ensure_table_structure()

            from models import (
                RebrickableColors,
                RebrickableElements,
                RebrickableInventories,
                RebrickableInventoryMinifigs,
                RebrickableInventoryParts,
                RebrickableInventorySets,
                RebrickableMinifigs,
                RebrickablePartCategories,
                RebrickablePartRelationships,
                RebrickableParts,
                RebrickableSets,
                RebrickableThemes,
            )

            MODEL_MAP = {
                "part_categories.csv.gz": RebrickablePartCategories,
                "colors.csv.gz": RebrickableColors,
                "parts.csv.gz": RebrickableParts,
                "part_relationships.csv.gz": RebrickablePartRelationships,
                "elements.csv.gz": RebrickableElements,
                "themes.csv.gz": RebrickableThemes,
                "sets.csv.gz": RebrickableSets,
                "minifigs.csv.gz": RebrickableMinifigs,
                "inventories.csv.gz": RebrickableInventories,
                "inventory_parts.csv.gz": RebrickableInventoryParts,
                "inventory_sets.csv.gz": RebrickableInventorySets,
                "inventory_minifigs.csv.gz": RebrickableInventoryMinifigs,
            }
            for file in FILES:
                csv_path = download_and_extract_csv(file)
                import_csv_to_sqlite(csv_path, MODEL_MAP[file])
            return (
                jsonify(
                    {"status": "success", "message": "CSV data imported into SQLite!"}
                ),
                200,
            )
        except Exception as e:
            logging.error("Unexpected error: %s", str(e))
            db.session.rollback()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "An unexpected error occurred. Changes rolled back.",
                    }
                ),
                500,
            )
    return render_template("import_data.html")


def main():
    """
    Main function to import all Rebrickable CSV files.
    Downloads and imports all required data files from Rebrickable.
    """
    logging.basicConfig(level=logging.INFO)

    for file in FILES:
        csv_path = download_and_extract_csv(file)
        import_csv_to_sqlite(csv_path, MODEL_MAP[file])
    logging.info("All CSV files imported successfully.")


if __name__ == "__main__":
    main()
