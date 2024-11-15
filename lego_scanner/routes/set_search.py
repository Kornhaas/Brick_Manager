"""
This module handles the set search functionality for the LEGO Scanner Flask application.

It fetches parts information for a given set number from the Rebrickable API and 
renders the results on a web page. Additionally, it allows saving the set and its parts
to the database.
"""

from flask import Blueprint, render_template, request, flash, current_app
import requests
from services.lookup_service import load_master_lookup
from services.rebrickable_service import get_category_name_from_db
from config import Config
from models import db, Set, Part  # Ensure you have these models defined in your application

set_search_bp = Blueprint('set_search', __name__)


@set_search_bp.route('/set_search', methods=['GET', 'POST'])
def set_search():
    """
    Handles the set search functionality. Fetches parts information for a given set number
    from the Rebrickable API and displays the results. Allows saving the set to the database.

    Returns:
        Renders the set_search.html template with the parts information.
    """
    parts_info = []
    set_number = None

    if request.method == 'POST':
        current_app.logger.info("Processing set search form submission")
        set_number = request.form.get('set_number')
        save_to_db = request.form.get('save_to_db') == 'on'
        current_app.logger.info(f"Set number entered: {set_number}")

        if not set_number:
            flash("Please enter a set number.", category="danger")
        else:
            parts_info = fetch_set_parts_info(set_number)
            if not parts_info:
                flash(f"Failed to fetch parts for set {set_number}.", category="danger")
            elif save_to_db:
                add_set_to_db(set_number, parts_info)
                flash(f"Set {set_number} and its parts have been saved to the database.", category="success")

    return render_template('set_search.html', parts_info=parts_info, set_number=set_number)


def fetch_set_parts_info(set_number):
    """
    Fetches the parts information for a given set number from the Rebrickable API.

    Args:
        set_number (str): The LEGO set number to fetch parts for.

    Returns:
        list: A list of dictionaries containing parts information.
    """
    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{set_number}/parts/',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        current_app.logger.info(f"Rebrickable API response: {response.status_code}")

        if response.status_code == 200:
            return parse_parts_info(response.json())

        current_app.logger.error(f"Failed to fetch parts for set {set_number}: {response.status_code}")
        return None

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching parts for set {set_number}: {str(e)}")
        return None


def parse_parts_info(data):
    """
    Parses the parts information from the Rebrickable API response.

    Args:
        data (dict): The JSON response from the Rebrickable API.

    Returns:
        list: A list of dictionaries containing parsed parts information.
    """
    parts_info = []
    master_lookup = load_master_lookup()

    for item in data.get('results', []):
        part_num, name, category, color, color_rgb, quantity, full_location = extract_part_info(
            item, master_lookup)
        parts_info.append({
            'part_num': part_num,
            'name': name,
            'category': category,
            'color': color,
            'color_rgb': color_rgb,
            'quantity': quantity,
            'location': full_location
        })

    return parts_info


def extract_part_info(item, master_lookup):
    """
    Extracts part information from the Rebrickable API response item.

    Args:
        item (dict): A single part data item from the Rebrickable API response.
        master_lookup (dict): A lookup dictionary for part location information.

    Returns:
        tuple: A tuple containing part_num, name, category, color, 
        color_rgb, quantity, and full_location.
    """
    part = item['part']
    part_num = part['part_num']
    name = part['name']
    category = get_category_name_from_db(part['part_cat_id'])
    current_app.logger.info(f"Category for part {part_num}: {category}")
    color = item['color']['name']
    color_rgb = item['color']['rgb']
    quantity = item['quantity']

    # Fetch location, level, and box from master_lookup
    part_info = master_lookup.get(part_num, {})
    location = part_info.get('location', 'Unknown')
    level = part_info.get('level', 'Unknown')
    box = part_info.get('box', 'Unknown')

    # Merge location, level, and box into a single string
    full_location = f"{location}/{level}/{box}"

    return part_num, name, category, color, color_rgb, quantity, full_location


def add_set_to_db(set_number, parts_info):
    """
    Saves the set and its parts to the database.

    Args:
        set_number (str): The LEGO set number.
        parts_info (list): List of dictionaries containing parts information.
    """
    try:
        # Add the set to the database
        lego_set = Set(set_number=set_number)
        db.session.add(lego_set)
        db.session.flush()  # Get the ID for the set

        # Add each part to the database
        for part in parts_info:
            db_part = Part(
                part_num=part['part_num'],
                name=part['name'],
                category=part['category'],
                color=part['color'],
                color_rgb=part['color_rgb'],
                quantity=part['quantity'],
                location=part['location'],
                set_id=lego_set.id
            )
            db.session.add(db_part)

        db.session.commit()
        current_app.logger.info(f"Set {set_number} and its parts have been saved to the database.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving set {set_number} to the database: {str(e)}")
        flash("An error occurred while saving the set to the database.", category="danger")
