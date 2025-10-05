"""
This module handles the loading and updating of Brick data (categories, parts, colors, and themes)
from Rebrickable CSV files into the local SQLite database.
"""

import logging
from flask import Blueprint, render_template, request, jsonify
from models import db
import os
import requests
import gzip
import shutil
import pandas as pd

# pylint: disable=C0301,W0718
import_rebrickable_data_bp = Blueprint('import_rebrickable_data', __name__)

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
    os.makedirs(IMPORT_DIR, exist_ok=True)
    gz_path = os.path.join(IMPORT_DIR, file_name)
    csv_path = os.path.join(IMPORT_DIR, file_name.replace('.gz', ''))
    url = f"{BASE_URL}/{file_name}"
    logging.info(f"Downloading {url} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(gz_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    logging.info(f"Extracting {gz_path} ...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(gz_path)
    return csv_path

def import_csv_to_sqlite(csv_path, model_class):
    logging.info(f"Importing {csv_path} into {model_class.__tablename__} ...")
    df = pd.read_csv(csv_path)
    df.to_sql(model_class.__tablename__, db.engine, if_exists='replace', index=False)
    os.remove(csv_path)

@import_rebrickable_data_bp.route('/import_data', methods=['GET', 'POST'])
def import_data():
    """
    Load and update Brick data (categories, parts, colors, and themes) 
    from the Rebrickable API into the local database.

    Handles POST requests to fetch and store categories, parts, colors, and themes in the database.
    """
    if request.method == 'POST':
        try:
            from models import (
                RebrickablePartCategories, RebrickableColors, RebrickableParts,
                RebrickablePartRelationships, RebrickableElements, RebrickableThemes,
                RebrickableSets, RebrickableMinifigs, RebrickableInventories,
                RebrickableInventoryParts, RebrickableInventorySets, RebrickableInventoryMinifigs
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
            return jsonify({'status': 'success', 'message': 'CSV data imported into SQLite!'}), 200
        except Exception as e:
            logging.error("Unexpected error: %s", str(e))
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'An unexpected error occurred. Changes rolled back.'}), 500
    return render_template('import_data.html')

def main():
    logging.basicConfig(level=logging.INFO)

    for file in FILES:
        csv_path = download_and_extract_csv(file)
        import_csv_to_sqlite(csv_path, MODEL_MAP[file])
    logging.info("All CSV files imported successfully.")

if __name__ == "__main__":
    main()
