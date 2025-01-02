"""
This module handles the loading and updating of LEGO parts
from the Rebrickable API into the local database.
"""
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError
from services.rebrickable_service import get_all_parts, RebrickableAPIException
from models import db, Part, PartCategory

load_parts_bp = Blueprint('load_parts', __name__)

@load_parts_bp.route('/load_parts', methods=['GET', 'POST'])
def load_parts():
    """
    Load and update LEGO parts from the Rebrickable API into the local database.

    If the method is POST, fetch parts page by page, update or add them to the database,
    and commit the changes. Handle errors gracefully with rollback where necessary.
    """
    if request.method == 'POST':
        page = 1
        total_parts = 0

        try:
            while True:
                print(f"Fetching parts from page {page}...")  # Debugging print

                try:
                    parts_data = get_all_parts(page=page, page_size=1000)
                except RebrickableAPIException as api_error:
                    print(f"API Exception: {api_error}")  # Debugging print
                    flash("API error occurred while fetching parts.")
                    break

                if not parts_data or not parts_data['results']:
                    print("No more parts to fetch.")  # Debugging print
                    break

                for part in parts_data['results']:
                    part_num = part.get('part_num')
                    if not part_num:
                        print(f"Skipping invalid part entry: {part}")  # Debugging print
                        continue

                    # Ensure the category exists or create it
                    category_id = part.get('part_cat_id')
                    if category_id:
                        category = PartCategory.query.filter_by(id=category_id).first()
                        if not category:
                            category = PartCategory(
                                id=category_id,
                                name='Unknown'  # Default name if the category name isn't fetched
                            )
                            db.session.add(category)
                            db.session.flush()

                    # Check for existing part
                    existing_part = Part.query.filter_by(part_num=part_num).first()

                    if existing_part:
                        print(f"Updating part {part_num}: {part.get('name', 'Unknown')}")  # Debugging print
                        existing_part.name = part.get('name', 'Unknown')
                        existing_part.part_cat_id = category_id
                    else:
                        print(f"Adding new part {part_num}: {part.get('name', 'Unknown')}")  # Debugging print
                        new_part = Part(
                            part_num=part_num,
                            name=part.get('name', 'Unknown'),
                            part_cat_id=category_id,
                        )
                        db.session.add(new_part)

                db.session.commit()
                total_parts += len(parts_data['results'])
                print(f"Page {page} committed successfully.")  # Debugging print

                # Increment the page for the next iteration
                page += 1

        except RequestException as req_err:
            print(f"HTTP request error: {str(req_err)}")  # Debugging print
            flash("Failed to fetch parts from the Rebrickable API.")
        except SQLAlchemyError as db_err:
            print(f"Database error: {str(db_err)}")  # Debugging print
            db.session.rollback()
            flash("Database error occurred while loading parts.")
        except KeyError as key_err:
            print(f"Key error in response data: {key_err}")  # Debugging print
            db.session.rollback()
            flash("Unexpected data format received from the API.")
        except Exception as e:  # Catch-all for unexpected errors
            print(f"Unexpected error: {str(e)}")  # Debugging print
            db.session.rollback()
            flash("An unexpected error occurred while loading parts.")

        flash(f"Successfully loaded/updated {total_parts} parts!")
        return redirect(url_for('main.index'))

    return render_template('load_parts.html')
