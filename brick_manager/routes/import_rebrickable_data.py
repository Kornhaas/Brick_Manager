"""

This module handles the loading and updating of Brick data (categories, parts, colors, and themes)

from Rebrickable CSV files into the local SQLite database.
"""

import gzip
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from uuid import uuid4

import pandas as pd
import requests
from flask import Blueprint, current_app, jsonify, render_template, request
from models import db

# pylint: disable=C0301
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

# Lazy import to avoid circular dependency issues
MODEL_MAP = None

_IMPORT_EXECUTOR = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="catalog-import"
)
_IMPORT_JOBS = {}
_IMPORT_JOBS_LOCK = Lock()
_ACTIVE_IMPORT_JOB_ID = None


def _display_name(file_name):
    """Return a concise label for one Rebrickable archive."""
    return file_name.removesuffix(".csv.gz").replace("_", " ").title()


def _new_import_job(job_id):
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Import queued",
        "completed": 0,
        "total": len(FILES),
        "percent": 0,
        "files": [
            {
                "name": file_name,
                "label": _display_name(file_name),
                "status": "pending",
                "records": None,
            }
            for file_name in FILES
        ],
    }


def _update_import_job(job_id, **changes):
    with _IMPORT_JOBS_LOCK:
        _IMPORT_JOBS[job_id].update(changes)


def _update_import_file(job_id, file_name, **changes):
    with _IMPORT_JOBS_LOCK:
        for file_status in _IMPORT_JOBS[job_id]["files"]:
            if file_status["name"] == file_name:
                file_status.update(changes)
                break


def _run_import_job(application, job_id):
    """Execute one catalog refresh while publishing UI-safe progress state."""
    global _ACTIVE_IMPORT_JOB_ID  # pylint: disable=global-statement

    with application.app_context():
        try:
            _update_import_job(
                job_id, status="running", message="Checking database tables"
            )
            ensure_table_structure()
            model_map = _get_model_map()

            for index, file_name in enumerate(FILES, start=1):
                _update_import_file(job_id, file_name, status="downloading")
                _update_import_job(
                    job_id,
                    message=f"Downloading and extracting {_display_name(file_name)}",
                )
                csv_path = download_and_extract_csv(file_name)

                _update_import_file(job_id, file_name, status="importing")
                _update_import_job(
                    job_id, message=f"Importing {_display_name(file_name)}"
                )
                record_count = import_csv_to_sqlite(csv_path, model_map[file_name])

                _update_import_file(
                    job_id,
                    file_name,
                    status="completed",
                    records=record_count,
                )
                _update_import_job(
                    job_id,
                    completed=index,
                    percent=round(index / len(FILES) * 100),
                )

            _update_import_job(
                job_id,
                status="completed",
                message="All catalog files imported successfully",
                percent=100,
            )
        except Exception:
            db.session.rollback()
            logging.exception("Background catalog import failed")
            with _IMPORT_JOBS_LOCK:
                job = _IMPORT_JOBS[job_id]
                for file_status in job["files"]:
                    if file_status["status"] in {"downloading", "importing"}:
                        file_status["status"] = "error"
                job.update(
                    status="error",
                    message="Import failed. Existing data for the current file was preserved.",
                )
        finally:
            with _IMPORT_JOBS_LOCK:
                if job_id == _ACTIVE_IMPORT_JOB_ID:
                    _ACTIVE_IMPORT_JOB_ID = None


def _get_model_map():
    """Get MODEL_MAP with lazy import to avoid circular dependencies."""
    global MODEL_MAP  # pylint: disable=global-statement
    if MODEL_MAP is None:
        from models import (  # pylint: disable=import-outside-toplevel
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
    return MODEL_MAP


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
    partial_gz_path = f"{gz_path}.part"
    partial_csv_path = f"{csv_path}.part"
    url = f"{BASE_URL}/{file_name}"
    logging.info(f"Downloading {url} ...")
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(partial_gz_path, "wb") as output:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        output.write(chunk)
        os.replace(partial_gz_path, gz_path)

        logging.info(f"Extracting {gz_path} ...")
        with (
            gzip.open(gz_path, "rb") as compressed,
            open(partial_csv_path, "wb") as extracted,
        ):
            shutil.copyfileobj(compressed, extracted)
        os.replace(partial_csv_path, csv_path)
    except Exception:
        for partial_path in (partial_gz_path, partial_csv_path):
            if os.path.exists(partial_path):
                os.remove(partial_path)
        raise
    finally:
        if os.path.exists(gz_path):
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

    # Replace one catalog table in a single transaction. If the append fails,
    # the previous reference data remains intact.
    with db.engine.begin() as connection:
        connection.execute(model_class.__table__.delete())
        df.to_sql(
            model_class.__tablename__, connection, if_exists="append", index=False
        )
    db.session.expire_all()

    # Clean up the CSV file
    os.remove(csv_path)

    logging.info(
        f"Successfully imported {len(df)} records into {model_class.__tablename__}"
    )
    return len(df)


@import_rebrickable_data_bp.post("/import_data/start")
def start_import():
    """Start one background catalog import or reconnect to the active job."""
    global _ACTIVE_IMPORT_JOB_ID  # pylint: disable=global-statement

    with _IMPORT_JOBS_LOCK:
        if _ACTIVE_IMPORT_JOB_ID:
            return (
                jsonify(
                    {
                        "status": "running",
                        "job_id": _ACTIVE_IMPORT_JOB_ID,
                        "already_running": True,
                    }
                ),
                202,
            )

        job_id = uuid4().hex
        _IMPORT_JOBS.clear()
        _IMPORT_JOBS[job_id] = _new_import_job(job_id)
        _ACTIVE_IMPORT_JOB_ID = job_id

    application = current_app.app_context().app
    _IMPORT_EXECUTOR.submit(_run_import_job, application, job_id)
    return jsonify({"status": "queued", "job_id": job_id}), 202


@import_rebrickable_data_bp.get("/import_data/status/<job_id>")
def import_status(job_id):
    """Return a snapshot of background import progress."""
    with _IMPORT_JOBS_LOCK:
        job = _IMPORT_JOBS.get(job_id)
        if job is None:
            return jsonify(
                {"status": "not_found", "message": "Import job not found"}
            ), 404
        return jsonify(deepcopy(job))


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

            model_map = _get_model_map()
            for file in FILES:
                csv_path = download_and_extract_csv(file)
                import_csv_to_sqlite(csv_path, model_map[file])
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

    model_map = _get_model_map()
    for file in FILES:
        csv_path = download_and_extract_csv(file)
        import_csv_to_sqlite(csv_path, model_map[file])
    logging.info("All CSV files imported successfully.")


if __name__ == "__main__":
    main()
