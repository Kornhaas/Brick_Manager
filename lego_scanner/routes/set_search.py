from flask import Blueprint, render_template, request, flash, current_app, redirect, url_for
import requests
from models import db, Set, UserSet, PartInSet, Minifigure, UserMinifigurePart, Category, PartInfo
from config import Config
from services.part_lookup_service import load_part_lookup

set_search_bp = Blueprint('set_search', __name__)

def get_or_create(session, model, defaults=None, **kwargs):
    """
    Utility function to fetch or create a database entry.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {**kwargs, **(defaults or {})}
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True

@set_search_bp.route('/set_search', methods=['GET', 'POST'])
def set_search():
    """
    Search for LEGO sets by their number and display the results, including minifigure parts.
    """
    set_info = {}
    parts_info = []
    minifigs_info = []

    if request.method == 'POST':
        set_number = request.form.get('set_number')
        current_app.logger.debug(f"Set search initiated for: {set_number}")

        if not set_number:
            flash("Please enter a set number.", category="danger")
        else:
            # Append -1 if not present
            if not set_number.endswith('-1'):
                set_number += '-1'
                current_app.logger.debug(f"Set number corrected to: {set_number}")
                
            set_info = fetch_set_info(set_number)
            if set_info:
                current_app.logger.debug(f"Set info fetched: {set_info}")
            else:
                current_app.logger.warning(f"No data found for set number: {set_number}")

            parts_info = fetch_set_parts_info(set_number)
            current_app.logger.debug(f"Parts info fetched: {len(parts_info)} parts found.")

            minifigs_info = fetch_minifigs_info(set_number)
            current_app.logger.debug(f"Minifigs info fetched: {len(minifigs_info)} minifigs found.")

            # Fetch parts for each minifigure
            for minifig in minifigs_info:
                fig_num = minifig.get('fig_num')
                if fig_num:
                    minifig_parts = fetch_minifigure_parts(fig_num)
                    minifig['parts'] = minifig_parts
                    current_app.logger.debug(f"Fetched {len(minifig_parts)} parts for minifigure {fig_num}.")
                else:
                    current_app.logger.warning(f"Minifigure {minifig} has no fig_num; skipping parts fetch.")

    return render_template(
        'set_search.html',
        set_info=set_info,
        parts_info=parts_info,
        minifigs_info=minifigs_info
    )


@set_search_bp.route('/add_set', methods=['POST'])
def add_set():
    """
    Add a LEGO set instance (UserSet) to the database, including its parts, minifigures, and minifigure parts.
    """
    set_number = request.form.get('set_number')
    status = request.form.get('status', 'unknown')  # Default to 'unknown'
    current_app.logger.debug(f"Adding set {set_number} to the database with status {status}.")

    try:
        # Append -1 if not present
        if not set_number.endswith('-1'):
            set_number += '-1'
            current_app.logger.debug(f"Set number corrected to: {set_number}")
                
        # Fetch or get the template set
        set_info = fetch_set_info(set_number)
        if not set_info:
            flash(f"Set {set_number} not found.", category="danger")
            return redirect(url_for('set_search.set_search'))

        template_set, created = get_or_create(db.session, Set, set_number=set_number, defaults={
            'name': set_info['name'],
            'set_img_url': set_info['set_img_url']
        })

        # Prevent duplicate UserSets
        #if UserSet.query.filter_by(set_id=template_set.id).first():
        #    flash(f"Set {template_set.name} already exists.", category="info")
        #    return redirect(url_for('set_search.set_search'))

        # Create UserSet with the provided status
        user_set = UserSet(template_set=template_set, status=status)
        db.session.add(user_set)
        db.session.flush()

        # Add parts
        parts_info = fetch_set_parts_info(set_number)
        for part in parts_info:
                    # Ensure the part exists in `part_info`
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

        # Add minifigures and parts
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

            # Add minifigure parts
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
        flash(f"Set {template_set.name} added successfully as {status}!", category="success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding set {set_number}: {e}")
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
        current_app.logger.error(f"Failed to fetch set info for {set_number}: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching set info for {set_number}: {e}")
        return None


def fetch_set_parts_info(set_number):
    """
    Fetches the parts information for a given set number from the Rebrickable API.
    """
    master_lookup = load_part_lookup()

    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{set_number}/parts/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            parts_info = []
            for item in data.get('results', []):
                part_num = item['part']['part_num']
                location_data = master_lookup.get(part_num, {})
                location = f"Location: {location_data.get('location', 'Unknown')}, " \
                           f"Level: {location_data.get('level', 'Unknown')}, " \
                           f"Box: {location_data.get('box', 'Unknown')}" if location_data else "Not Specified"

                part = {
                    'part_num': part_num,
                    'name': item['part'].get('name', 'Unknown'),
                    'category': item['part'].get('part_cat_id', None),
                    'color': item['color'].get('name', 'Unknown'),
                    'color_rgb': item['color'].get('rgb', 'FFFFFF'),
                    'quantity': item['quantity'],
                    'is_spare': item['is_spare'],
                    'part_img_url': item['part'].get('part_img_url', ''),
                    'location': location,
                }
                parts_info.append(part)
            return parts_info
        current_app.logger.error(f"Failed to fetch parts for set {set_number}: {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching parts for set {set_number}: {e}")
        return []

def fetch_minifigs_info(set_number):
    """
    Fetches the minifigures information for a given set number from the Rebrickable API.
    """
    master_lookup = load_part_lookup()

    try:
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/sets/{set_number}/minifigs/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            minifigs_info = []
            for item in data.get('results', []):
                fig_num = item['set_num']
                location_data = master_lookup.get(fig_num, {})
                location = f"Location: {location_data.get('location', 'Unknown')}, " \
                           f"Level: {location_data.get('level', 'Unknown')}, " \
                           f"Box: {location_data.get('box', 'Unknown')}" if location_data else "Not Specified"
                status = "Available" if location_data else "Not Available"

                minifigs_info.append({
                    'fig_num': fig_num,
                    'name': item.get('set_name', 'Unknown'),
                    'quantity': item['quantity'],
                    'img_url': item.get('set_img_url', ''),
                    'location': location,
                    'status': status,
                    'have_quantity': 0  # Default to 0 if not provided
                })
            return minifigs_info
        current_app.logger.error(f"Failed to fetch minifigs for set {set_number}: {response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching minifigs for set {set_number}: {e}")
        return []

def fetch_minifigure_parts(fig_num):
    """
    Fetches parts information for a specific minifigure from the Rebrickable API.
    """
    master_lookup = load_part_lookup()

    try:
        current_app.logger.debug(f"Fetching parts for minifigure: {fig_num}")
        response = requests.get(
            f'https://rebrickable.com/api/v3/lego/minifigs/{fig_num}/parts/?page_size=1000',
            headers={
                'Accept': 'application/json',
                'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            parts = data.get('results', [])
            if parts:
                current_app.logger.debug(f"Minifigure parts fetched for {fig_num}: {len(parts)} parts found.")
            else:
                current_app.logger.warning(f"No parts found for minifigure {fig_num}.")

            # Process and return the part details with location and status
            return [
                {
                    'part_num': item['part']['part_num'],
                    'name': item['part']['name'],
                    'color': item['color']['name'],
                    'color_rgb': item['color']['rgb'],
                    'quantity': item['quantity'],
                    'part_img_url': item['part']['part_img_url'],
                    'part_url': item['part']['part_url'],
                    'location': f"Location: {master_lookup.get(item['part']['part_num'], {}).get('location', 'Unknown')}, " \
                                f"Level: {master_lookup.get(item['part']['part_num'], {}).get('level', 'Unknown')}, " \
                                f"Box: {master_lookup.get(item['part']['part_num'], {}).get('box', 'Unknown')}" if master_lookup.get(item['part']['part_num']) else "Not Specified",
                    'status': "Available" if master_lookup.get(item['part']['part_num']) else "Not Available"
                }
                for item in parts
            ]
        else:
            current_app.logger.error(f"Failed to fetch parts for minifigure {fig_num}. Response code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching parts for minifigure {fig_num}: {e}")
        return []
