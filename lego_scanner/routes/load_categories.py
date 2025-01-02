# Import Statements
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError
from services.rebrickable_service import get_all_category_ids_from_api
from models import db, PartCategory

# Blueprint for loading categories
load_categories_bp = Blueprint('load_categories', __name__)
populate_data_bp = Blueprint('populate_data', __name__)

@load_categories_bp.route('/load_categories', methods=['GET', 'POST'])
def load_categories():
    """
    Load and update LEGO part categories from the Rebrickable API into the local database.

    If the method is POST, fetch the categories, update or add them to the database,
    and commit the changes. Handle errors gracefully.
    """
    if request.method == 'POST':
        try:
            # Fetch categories from the Rebrickable API
            categories = get_all_category_ids_from_api()

            for cat_id, category_name in categories:
                existing_category = PartCategory.query.filter_by(id=cat_id).first()
                if existing_category:
                    existing_category.name = category_name
                    existing_category.last_updated = datetime.utcnow()
                else:
                    new_category = PartCategory(id=cat_id, name=category_name)
                    db.session.add(new_category)

            db.session.commit()
            flash("Categories loaded/updated successfully!", category="success")
        except RequestException as req_err:
            db.session.rollback()
            flash(f"HTTP request error: {str(req_err)}", category="danger")
        except SQLAlchemyError as db_err:
            db.session.rollback()
            flash(f"Database error: {str(db_err)}", category="danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Unexpected error: {str(e)}", category="danger")
        finally:
            db.session.close()
        return redirect(url_for('main.index'))

    return render_template('load_categories.html')


# Routes for populating data from Rebrickable
@populate_data_bp.route('/populate/categories', methods=['POST'])
def populate_categories():
    """
    Populate LEGO categories into the database.
    """
    try:
        load_categories()
        return jsonify({'message': 'Categories populated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@populate_data_bp.route('/populate/parts', methods=['POST'])
def populate_parts():
    """
    Populate LEGO parts into the database.
    """
    try:
        populate_parts_function()  # Replace with actual implementation
        return jsonify({'message': 'Parts populated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@populate_data_bp.route('/populate/colors', methods=['POST'])
def populate_colors():
    """
    Populate LEGO colors into the database.
    """
    try:
        populate_colors_function()  # Replace with actual implementation
        return jsonify({'message': 'Colors populated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@populate_data_bp.route('/populate/themes', methods=['POST'])
def populate_themes():
    """
    Populate LEGO themes into the database.
    """
    try:
        populate_themes_function()  # Replace with actual implementation
        return jsonify({'message': 'Themes populated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@populate_data_bp.route('/populate/sets', methods=['POST'])
def populate_sets():
    """
    Populate LEGO sets into the database.
    """
    try:
        populate_sets_function()  # Replace with actual implementation
        return jsonify({'message': 'Sets populated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
