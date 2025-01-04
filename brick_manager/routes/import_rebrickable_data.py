"""
This module handles the loading and updating of Brick data (categories, parts, colors, and themes)
from the Rebrickable API into the local database.
"""
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError
from services.rebrickable_service import RebrickableService
from models import db, Category, PartInfo, Color, Theme

import_rebrickable_data_bp = Blueprint('import_rebrickable_data', __name__)

@import_rebrickable_data_bp.route('/import_data', methods=['GET', 'POST'])
def import_data():
    """
    Load and update Brick data (categories, parts, colors, and themes) from the Rebrickable API into the local database.

    Handles POST requests to fetch and store categories, parts, colors, and themes in the database.
    """
    if request.method == 'POST':
        try:
            _load_categories()
            _load_parts()
            _load_colors()
            _load_themes()
            return jsonify({'status': 'success', 'message': 'Data imported successfully!'}), 200
        except RequestException as req_err:
            print(f"HTTP request error: {str(req_err)}")
            return jsonify({'status': 'error', 'message': 'Failed to fetch data from Rebrickable API.'}), 500
        except SQLAlchemyError as db_err:
            print(f"Database error: {str(db_err)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Database error occurred. Changes rolled back.'}), 500
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'An unexpected error occurred. Changes rolled back.'}), 500

    return render_template('import_data.html')

def _load_categories():
    """
    Fetch and load Brick part categories into the local database.
    """
    categories = RebrickableService.get_all_category_ids()
    for cat_id, category_name in categories:
        existing_category = Category.query.filter_by(id=cat_id).first()
        if existing_category:
            existing_category.name = category_name
            existing_category.last_updated = datetime.utcnow()
        else:
            db.session.add(Category(id=cat_id, name=category_name))
    db.session.commit()

def _load_parts():
    """
    Fetch and load Brick parts into the local database.
    """
    print("Loading parts...")
    page = 1
    while True:
        parts_data = RebrickableService.get_parts(page=page, page_size=1000)
        if not parts_data:  # Stop if no data is returned (Invalid page)
            break

        parts = parts_data.get('results', [])
        for part in parts:
            existing_part = PartInfo.query.filter_by(part_num=part['part_num']).first()
            if not existing_part:
                db.session.add(PartInfo(
                    part_num=part['part_num'],
                    name=part['name'],
                    category_id=part['part_cat_id'],
                    part_img_url=part.get('part_img_url'),
                    part_url=part.get('part_url')
                ))
        db.session.commit()
        print(f"Imported {len(parts)} parts from page {page}.")
        page += 1


def _load_colors():
    print("Loading colors...")
    page = 1
    while True:
        colors_data = RebrickableService.get_colors(page=page, page_size=100)
        if not colors_data:
            break

        colors = colors_data.get('results', [])
        for color in colors:
            existing_color = Color.query.filter_by(id=color['id']).first()
            if not existing_color:
                db.session.add(Color(
                    id=color['id'],
                    name=color['name'],
                    rgb=color['rgb'],
                    is_trans=color['is_trans']
                ))
        db.session.commit()
        print(f"Imported {len(colors)} colors from page {page}.")
        page += 1


def _load_themes():
    print("Loading themes...")
    page = 1
    while True:
        themes_data = RebrickableService.get_themes(page=page, page_size=100)
        if not themes_data:
            break

        themes = themes_data.get('results', [])
        for theme in themes:
            existing_theme = Theme.query.filter_by(id=theme['id']).first()
            if not existing_theme:
                db.session.add(Theme(
                    id=theme['id'],
                    name=theme['name'],
                    parent_id=theme.get('parent_id')
                ))
        db.session.commit()
        print(f"Imported {len(themes)} themes from page {page}.")
        page += 1
