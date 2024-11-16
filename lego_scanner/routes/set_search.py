"""
This module handles the set search functionality for the LEGO Scanner Flask application.

It fetches parts information for a given set number from the Rebrickable API and 
renders the results on a web page. Additionally, it allows saving the set and its parts
to the database, as well as updating a checklist for the parts owned.
"""

from flask import Blueprint, render_template, request, flash, current_app, redirect, url_for
import requests
from services.lookup_service import load_master_lookup
from services.rebrickable_service import get_category_name_from_db
from config import Config
from models import db, Set, Part  # Ensure you have these models defined in your application

# Define the blueprint
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
        current_app.logger.info(f"Set number entered: {set_number}")

        if not set_number:
            flash("Please enter a set number.", category="danger")
        else:
            parts_info = fetch_set_parts_info(set_number)
            if not parts_info:
                flash(f"Failed to fetch parts for set {set_number}.", category="danger")

    return render_template('set_search.html', parts_info=parts_info, set_number=set_number)


@set_search_bp.route('/add_set', methods=['POST'])
def add_set():
    """
    Adds a new instance of the set to the database with all parts marked as missing by default.
    """
    set_number = request.form.get('set_number')

    try:
        parts_info = fetch_set_parts_info(set_number)
        if not parts_info:
            flash(f"Failed to fetch parts for set {set_number}.", category="danger")
            return redirect(url_for('set_search.set_search'))

        # Add the set to the database
        lego_set = Set(set_number=set_number)
        db.session.add(lego_set)
        db.session.flush()

        # Add parts with default "missing" status
        for part in parts_info:
            db_part = Part(
                part_num=part['part_num'],
                name=part['name'],
                category=part['category'],
                color=part['color'],
                color_rgb=part['color_rgb'],
                quantity=part['quantity'],
                have_quantity=0,  # Default to missing
                location=part['location'],
                set_id=lego_set.id
            )
            db.session.add(db_part)

        db.session.commit()
        flash(f"Set {set_number} added to the database with all parts marked as missing.", category="success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding set {set_number}: {e}")
        flash("An error occurred while adding the set.", category="danger")

    return redirect(url_for('set_search.set_search'))


@set_search_bp.route('/set_checklist', methods=['POST'])
def set_checklist():
    """
    Updates the checklist information for the parts of a set.
    """
    set_number = request.form.get('set_number')
    parts_data = request.form.to_dict(flat=False)

    try:
        lego_set = Set.query.filter_by(set_number=set_number).first()
        if not lego_set:
            flash(f"Set {set_number} not found in the database.", category="danger")
            return redirect(url_for('set_search.set_search'))

        # Update part quantities based on user input
        for part_id, have_quantity in zip(parts_data.get('part_id', []), parts_data.get('have_quantity', [])):
            part = Part.query.get(int(part_id))
            if part:
                # Handle empty or invalid input for have_quantity
                try:
                    part.have_quantity = int(have_quantity) if have_quantity.strip() else 0
                except ValueError:
                    part.have_quantity = 0
                db.session.add(part)

        db.session.commit()
        flash(f"Checklist for set {set_number} updated successfully.", category="success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating checklist: {e}")
        flash("An error occurred while updating the checklist.", category="danger")

    return redirect(url_for('set_search.set_search'))


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
            'location': full_location,
            'have_quantity': 0  # Default to missing
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
