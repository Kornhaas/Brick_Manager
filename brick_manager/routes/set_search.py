"""
This module handles the search, retrieval, and addition of Brick sets, parts, and minifigures.
"""

from flask import Blueprint, render_template, request, flash, current_app, redirect, url_for
import requests
from models import db, Set, UserSet, PartInSet, Minifigure, UserMinifigurePart, PartInfo
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
    Add a Brick set instance (UserSet) to the database, including its parts, minifigures, and minifigure parts.
    """
    set_number = request.form.get('set_number')
    status = request.form.get('status', 'unknown')
    current_app.logger.debug(
        "Adding set %s to the database with status %s.", set_number, status)

    try:
        if not set_number.endswith('-1'):
            set_number += '-1'
            current_app.logger.debug("Set number corrected to: %s", set_number)

        set_info = fetch_set_info(set_number)
        if not set_info:
            flash(f"Set {set_number} not found.", category="danger")
            return redirect(url_for('set_search.set_search'))

        template_set, _ = get_or_create(db.session, Set, set_number=set_number, defaults={
            'name': set_info['name'],
            'set_img_url': set_info['set_img_url']
        })

        user_set = UserSet(template_set=template_set, status=status)
        db.session.add(user_set)
        db.session.flush()

        parts_info = fetch_set_parts_info(set_number)
        for part in parts_info:
            part_info, _ = get_or_create(db.session, PartInfo, part_num=part['part_num'], defaults={
                'name': part['name'],
                'category_id': part['category'],
                'part_img_url': part['part_img_url'],
                'part_url': part.get('part_url', ''),
            })

            db.session.add(PartInSet(
                part_num=part_info.part_num,
                color=part['color'],
                color_rgb=part['color_rgb'],
                quantity=part['quantity'],
                is_spare=part['is_spare'],
                user_set_id=user_set.id
            ))

        minifigs_info = fetch_minifigs_info(set_number)
        for minifig in minifigs_info:
            db_minifig = Minifigure(
                fig_num=minifig['fig_num'],
                name=minifig['name'],
                quantity=minifig['quantity'],
                img_url=minifig['img_url'],
                user_set_id=user_set.id
            )
            db.session.add(db_minifig)
            db.session.flush()

            minifig_parts = fetch_minifigure_parts(minifig['fig_num'])
            for part in minifig_parts:
                part_info, _ = get_or_create(db.session, PartInfo, part_num=part['part_num'], defaults={
                    'name': part['name'],
                    'category_id': part.get('category_id'),
                    'part_img_url': part['part_img_url'],
                    'part_url': part.get('part_url', ''),
                })

                db.session.add(UserMinifigurePart(
                    part_num=part_info.part_num,
                    name=part_info.name,
                    color=part['color'],
                    color_rgb=part['color_rgb'],
                    quantity=part['quantity'],
                    part_img_url=part['part_img_url'],
                    user_set_id=user_set.id
                ))
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
    Fetches basic set information including image URL.
    """
    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{set_number}/',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        current_app.logger.error(
            "Failed to fetch set info for %s: %d", set_number, response.status_code)
        return None
    except requests.exceptions.RequestException as error:
        current_app.logger.error(
            "Error fetching set info for %s: %s", set_number, error)
        return None


def fetch_set_parts_info(set_number):
    """
    Fetches the parts information for a given set number from the Rebrickable API.
    """
    master_lookup = load_part_lookup()

    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{
                set_number}/parts/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'part_num': item['part']['part_num'],
                    'name': item['part'].get('name', 'Unknown'),
                    'category': item['part'].get('part_cat_id'),
                    'color': item['color'].get('name', 'Unknown'),
                    'color_rgb': item['color'].get('rgb', 'FFFFFF'),
                    'quantity': item['quantity'],
                    'is_spare': item['is_spare'],
                    'part_img_url': item['part'].get('part_img_url'),
                    'location': format_location(master_lookup.get(item['part']['part_num']))
                }
                for item in data.get('results', [])
            ]
        current_app.logger.error(
            "Failed to fetch parts for set %s: %d", set_number, response.status_code)
        return []
    except requests.exceptions.RequestException as error:
        current_app.logger.error(
            "Error fetching parts for set %s: %s", set_number, error)
        return []


def fetch_minifigs_info(set_number):
    """
    Fetches the minifigures information for a given set number from the Rebrickable API.
    """
    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{
                set_number}/minifigs/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            return [
                {
                    'fig_num': item['set_num'],
                    'name': item.get('set_name', 'Unknown'),
                    'quantity': item['quantity'],
                    'img_url': item.get('set_img_url'),
                    'location': format_location(load_part_lookup().get(item['set_num']))
                }
                for item in response.json().get('results', [])
            ]
        current_app.logger.error(
            "Failed to fetch minifigs for set %s: %d", set_number, response.status_code)
        return []
    except requests.exceptions.RequestException as error:
        current_app.logger.error(
            "Error fetching minifigs for set %s: %s", set_number, error)
        return []


def fetch_minifigure_parts(fig_num):
    """
    Fetches parts information for a specific minifigure from the Rebrickable API.
    """
    master_lookup = load_part_lookup()

    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/minifigs/{
                fig_num}/parts/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            return [
                {
                    'part_num': item['part']['part_num'],
                    'name': item['part']['name'],
                    'color': item['color']['name'],
                    'color_rgb': item['color']['rgb'],
                    'quantity': item['quantity'],
                    'part_img_url': item['part']['part_img_url'],
                    'location': format_location(master_lookup.get(item['part']['part_num']))
                }
                for item in response.json().get('results', [])
            ]
        current_app.logger.error(
            "Failed to fetch parts for minifigure %s: %d", fig_num, response.status_code)
        return []
    except requests.exceptions.RequestException as error:
        current_app.logger.error(
            "Error fetching parts for minifigure %s: %s", fig_num, error)
        return []


def format_location(location_data):
    """
    Formats the location data for display.
    """
    if not location_data:
        return "Not Specified"
    return f"Location: {location_data.get('location', 'Unknown')}, Level: {location_data.get('level', 'Unknown')}, Box: {location_data.get('box', 'Unknown')}"
