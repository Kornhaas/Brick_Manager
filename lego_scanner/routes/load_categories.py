"""
This module handles the loading and updating of LEGO part categories
from the Rebrickable API into the local database.
"""
# Standard Library import
from datetime import datetime

# Third-Party Library import
from flask import Blueprint, render_template, flash, redirect, url_for, request
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError

# First-Party import
from services.rebrickable_service import get_all_category_ids_from_api
from models import db, Category


load_categories_bp = Blueprint('load_categories', __name__)


@load_categories_bp.route('/load_categories', methods=['GET', 'POST'])
def load_categories():
    """
    Load and update LEGO part categories from the Rebrickable API into the local database.

    If the method is POST, fetch the categories, update or add them to the database,
    and commit the changes. If an error occurs, rollback the transaction.
    """
    if request.method == 'POST':
        try:
            categories = get_all_category_ids_from_api()
            print(f"Fetched categories: {categories}")  # Debugging print
            for cat_id, category_name in categories:
                print(f"Processing category {cat_id}: {category_name}")  # Debugging print
                existing_category = Category.query.filter_by(id=cat_id).first()
                if existing_category:
                    print(f"Updating category {cat_id}: {category_name}")  # Debugging print
                    existing_category.name = category_name
                    existing_category.last_updated = datetime.utcnow()
                else:
                    print(f"Adding new category {cat_id}: {category_name}")  # Debugging print
                    new_category = Category(id=cat_id, name=category_name)
                    db.session.add(new_category)
            print("Committing changes to the database...")  # Debugging print
            db.session.commit()
            print("Commit successful.")  # Debugging print
            flash("Categories loaded/updated successfully!")
        except RequestException as req_err:
            print(f"HTTP request error: {str(req_err)}")  # Debugging print
        except SQLAlchemyError as db_err:
            print(f"Database error: {str(db_err)}")  # Debugging print
            db.session.rollback()
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Unexpected error: {str(e)}")  # Debugging print
            db.session.rollback()
        return redirect(url_for('main.index'))

    return render_template('load_categories.html')
