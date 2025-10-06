"""
This module handles the search, retrieval, and addition of Brick sets, parts, and minifigures.
"""

from flask import Blueprint, render_template, request, flash, current_app, redirect, url_for
import requests
from models import db, User_Set, User_Parts, User_Minifigures, UserMinifigurePart, RebrickableParts, RebrickableSets, RebrickableInventoryParts, RebrickableColors, RebrickableInventories, RebrickableInventoryMinifigs, RebrickableMinifigs
from config import Config
from services.part_lookup_service import load_part_lookup
#pylint: disable=C0301,W0718
set_search_bp = Blueprint('set_search', __name__)


def get_or_create(session, model, defaults=None, **kwargs):
    """
    Utility function to fetch or create a database entry.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


@set_search_bp.route('/set_search', methods=['GET', 'POST'])
def set_search():
    """
    Search for Brick sets by their number and display the results, including minifigure parts.
    """
    set_info = {}
    parts_info = []
    minifigs_info = []

    if request.method == 'POST':
        set_number = request.form.get('set_number')
        current_app.logger.debug("Set search initiated for: %s", set_number)

        if not set_number:
            flash("Please enter a set number.", category="danger")
        else:
            if not set_number.endswith('-1'):
                set_number += '-1'
                current_app.logger.debug(
                    "Set number corrected to: %s", set_number)

            set_info = fetch_set_info(set_number)
            if set_info:
                current_app.logger.debug("Set info fetched: %s", set_info)
            else:
                current_app.logger.warning(
                    "No data found for set number: %s", set_number)

            parts_info = fetch_set_parts_info(set_number)
            current_app.logger.debug(
                "Parts info fetched: %d parts found.", len(parts_info))

            minifigs_info = fetch_minifigs_info(set_number)
            current_app.logger.debug(
                "Minifigs info fetched: %d minifigs found.", len(minifigs_info))

            for minifig in minifigs_info:
                fig_num = minifig.get('fig_num')
                if fig_num:
                    minifig_parts = fetch_minifigure_parts(fig_num)
                    minifig['parts'] = minifig_parts
                    current_app.logger.debug(
                        "Fetched %d parts for minifigure %s.", len(minifig_parts), fig_num)

    return render_template(
        'set_search.html',
        set_info=set_info,
        parts_info=parts_info,
        minifigs_info=minifigs_info
    )


@set_search_bp.route('/add_set', methods=['POST'])
def add_set():
    """
    Add a Brick set instance (User_Set) to the database, including its parts, minifigures, and minifigure parts.
    """
    set_number = request.form.get('set_number')
    status = request.form.get('status', 'unknown')
    current_app.logger.debug(
        "Adding set %s to the database with status %s.", set_number, status)

    try:
        if not set_number:
            flash("Set number is required.", category="danger")
            return redirect(url_for('set_search.set_search'))
            
        if not set_number.endswith('-1'):
            set_number += '-1'
            current_app.logger.debug("Set number corrected to: %s", set_number)

        set_info = fetch_set_info(set_number)
        if not set_info:
            flash(f"Set {set_number} not found.", category="danger")
            return redirect(url_for('set_search.set_search'))

        # Check if RebrickableSet already exists, if not create it
        template_set, _ = get_or_create(db.session, RebrickableSets, set_num=set_number, defaults={
            'name': set_info['name'],
            'year': set_info.get('year', 2023),
            'theme_id': set_info.get('theme_id', 1),
            'num_parts': set_info.get('num_parts', 0),
            'img_url': set_info['set_img_url']
        })

        user_set = User_Set()
        user_set.set_num = template_set.set_num
        user_set.status = status
        db.session.add(user_set)
        db.session.flush()

        parts_info = fetch_set_parts_info(set_number)
        for part in parts_info:
            part_info, _ = get_or_create(db.session, RebrickableParts, part_num=part['part_num'], defaults={
                'name': part['name'],
                'part_cat_id': part['category'],
                'part_img_url': part['part_img_url'],
                'part_url': part.get('part_url', ''),
            })

            # Get or create color
            color_info, _ = get_or_create(db.session, RebrickableColors, name=part['color'], defaults={
                'rgb': part['color_rgb'],
                'is_trans': False
            })

            user_part = User_Parts()
            user_part.part_num = part_info.part_num
            user_part.color_id = color_info.id
            user_part.quantity = part['quantity']
            user_part.is_spare = part['is_spare']
            user_part.user_set_id = user_set.id
            db.session.add(user_part)

        minifigs_info = fetch_minifigs_info(set_number)
        for minifig in minifigs_info:
            # Get or create rebrickable minifig
            rebrickable_minifig, _ = get_or_create(db.session, RebrickableMinifigs, fig_num=minifig['fig_num'], defaults={
                'name': minifig['name'],
                'num_parts': minifig.get('num_parts', 0),
                'img_url': minifig['img_url']
            })
            
            db_minifig = User_Minifigures()
            db_minifig.fig_num = minifig['fig_num']
            db_minifig.quantity = minifig['quantity']
            db_minifig.user_set_id = user_set.id
            db.session.add(db_minifig)
            db.session.flush()

            minifig_parts = fetch_minifigure_parts(minifig['fig_num'])
            for part in minifig_parts:
                part_info, _ = get_or_create(db.session, RebrickableParts, part_num=part['part_num'], defaults={
                    'name': part['name'],
                    'part_cat_id': part.get('category_id'),
                    'part_img_url': part['part_img_url'],
                    'part_url': part.get('part_url', ''),
                })

                # Get or create color
                color_info, _ = get_or_create(db.session, RebrickableColors, name=part['color'], defaults={
                    'rgb': part['color_rgb'],
                    'is_trans': False
                })

                minifig_part = UserMinifigurePart()
                minifig_part.part_num = part_info.part_num
                minifig_part.color_id = color_info.id
                minifig_part.quantity = part['quantity']
                minifig_part.user_set_id = user_set.id
                db.session.add(minifig_part)
        db.session.commit()
        flash(f"Set {template_set.name} added successfully as {
              status}!", category="success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error adding set %s: %s", set_number, error)
        flash("An error occurred while adding the set.", category="danger")

    return redirect(url_for('set_search.set_search'))


def fetch_set_info(set_number):
    """
    Fetches basic set information from the internal database (rebrickable_sets table).
    """
    try:
        # Query the RebrickableSets table for set information
        rebrickable_set = RebrickableSets.query.filter_by(set_num=set_number).first()
        
        if rebrickable_set:
            # Return data in the same format as the API response
            return {
                'set_num': rebrickable_set.set_num,
                'name': rebrickable_set.name,
                'year': rebrickable_set.year,
                'theme_id': rebrickable_set.theme_id,
                'num_parts': rebrickable_set.num_parts,
                'set_img_url': rebrickable_set.img_url
            }
        else:
            current_app.logger.warning(
                "Set %s not found in local database", set_number)
            return None
    except Exception as error:
        current_app.logger.error(
            "Error fetching set info from database for %s: %s", set_number, error)
        return None


def fetch_set_parts_info(set_number):
    """
    Fetches the parts information for a given set number from the internal database.
    Uses RebrickableInventories, RebrickableInventoryParts, RebrickableParts, and RebrickableColors tables.
    """
    master_lookup = load_part_lookup()

    try:
        # First, find the inventory for this set
        inventory = RebrickableInventories.query.filter_by(set_num=set_number).first()
        
        if not inventory:
            current_app.logger.warning(
                "No inventory found for set %s in local database", set_number)
            return []
        
        # Query inventory parts with joins to get part and color information
        inventory_parts = db.session.query(
            RebrickableInventoryParts,
            RebrickableParts,
            RebrickableColors
        ).join(
            RebrickableParts, RebrickableInventoryParts.part_num == RebrickableParts.part_num
        ).join(
            RebrickableColors, RebrickableInventoryParts.color_id == RebrickableColors.id
        ).filter(
            RebrickableInventoryParts.inventory_id == inventory.id
        ).all()
        
        parts_info = []
        for inv_part, part, color in inventory_parts:
            part_info = {
                'part_num': part.part_num,
                'name': part.name or 'Unknown',
                'category': part.part_cat_id,
                'color': color.name or 'Unknown',
                'color_rgb': color.rgb or 'FFFFFF',
                'quantity': inv_part.quantity,
                'is_spare': inv_part.is_spare,
                'part_img_url': inv_part.img_url or part.part_img_url,
                'location': format_location(master_lookup.get(part.part_num))
            }
            parts_info.append(part_info)
        
        current_app.logger.debug(
            "Fetched %d parts for set %s from local database", len(parts_info), set_number)
        return parts_info
        
    except Exception as error:
        current_app.logger.error(
            "Error fetching parts for set %s from database: %s", set_number, error)
        return []


def fetch_minifigs_info(set_number):
    """
    Fetches the minifigures information for a given set number from the internal database.
    Uses RebrickableInventories, RebrickableInventoryMinifigs, and RebrickableMinifigs tables.
    """
    try:
        # First, find the inventory for this set
        inventory = RebrickableInventories.query.filter_by(set_num=set_number).first()
        
        if not inventory:
            current_app.logger.warning(
                "No inventory found for set %s in local database", set_number)
            return []
        
        # Query inventory minifigs with joins to get minifigure information
        inventory_minifigs = db.session.query(
            RebrickableInventoryMinifigs,
            RebrickableMinifigs
        ).join(
            RebrickableMinifigs, RebrickableInventoryMinifigs.fig_num == RebrickableMinifigs.fig_num
        ).filter(
            RebrickableInventoryMinifigs.inventory_id == inventory.id
        ).all()
        
        minifigs_info = []
        for inv_minifig, minifig in inventory_minifigs:
            minifig_info = {
                'fig_num': minifig.fig_num,
                'name': minifig.name or 'Unknown',
                'quantity': inv_minifig.quantity,
                'img_url': minifig.img_url,
                'location': format_location(load_part_lookup().get(minifig.fig_num))
            }
            minifigs_info.append(minifig_info)
        
        current_app.logger.debug(
            "Fetched %d minifigs for set %s from local database", len(minifigs_info), set_number)
        return minifigs_info
        
    except Exception as error:
        current_app.logger.error(
            "Error fetching minifigs for set %s from database: %s", set_number, error)
        return []


def fetch_minifigure_parts(fig_num):
    """
    Fetches parts information for a specific minifigure from the internal database.
    Uses fig_num to find inventory in rebrickable_inventories (where set_num = fig_num),
    then gets parts from rebrickable_inventory_parts using the inventory_id.
    """
    master_lookup = load_part_lookup()

    try:
        # First, find the inventory for this minifigure (fig_num is used as set_num)
        inventory = RebrickableInventories.query.filter_by(set_num=fig_num).first()
        
        if not inventory:
            current_app.logger.warning(
                "No inventory found for minifigure %s in local database", fig_num)
            return []
        
        # Query inventory parts with joins to get part and color information
        inventory_parts = db.session.query(
            RebrickableInventoryParts,
            RebrickableParts,
            RebrickableColors
        ).join(
            RebrickableParts, RebrickableInventoryParts.part_num == RebrickableParts.part_num
        ).join(
            RebrickableColors, RebrickableInventoryParts.color_id == RebrickableColors.id
        ).filter(
            RebrickableInventoryParts.inventory_id == inventory.id
        ).all()
        
        parts_info = []
        for inv_part, part, color in inventory_parts:
            part_info = {
                'part_num': part.part_num,
                'name': part.name or 'Unknown',
                'color': color.name or 'Unknown',
                'color_rgb': color.rgb or 'FFFFFF',
                'quantity': inv_part.quantity,
                'part_img_url': inv_part.img_url or part.part_img_url,
                'location': format_location(master_lookup.get(part.part_num))
            }
            parts_info.append(part_info)
        
        current_app.logger.debug(
            "Fetched %d parts for minifigure %s from local database", len(parts_info), fig_num)
        return parts_info
        
    except Exception as error:
        current_app.logger.error(
            "Error fetching parts for minifigure %s from database: %s", fig_num, error)
        return []


def format_location(location_data):
    """
    Formats the location data for display.
    """
    if not location_data:
        return "Not Specified"
    return f"Location: {location_data.get('location', 'Unknown')}, Level: {location_data.get('level', 'Unknown')}, Box: {location_data.get('box', 'Unknown')}"
