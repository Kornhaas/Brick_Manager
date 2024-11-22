import os
import requests
from flask import Blueprint, jsonify, render_template, current_app
from models import UserSet, Part, Minifigure, UserMinifigurePart
from services.lookup_service import load_master_lookup
from sqlalchemy.orm import selectinload

dashboard_bp = Blueprint('dashboard', __name__)

def cache_image(image_url, cache_dir='static/cache/images'):
    """
    Download and cache an image locally if not already cached.
    Returns the path to the cached image.
    """
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Generate a filename based on the URL
    filename = os.path.join(cache_dir, os.path.basename(image_url))

    if not os.path.exists(filename):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                current_app.logger.error(f"Failed to download image: {image_url}")
        except Exception as e:
            current_app.logger.error(f"Error downloading image {image_url}: {e}")

    # Return the path relative to the static folder
    return f"/{filename}"

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Dashboard route to display an overview of total and missing parts/minifigures.
    """
    # Query parts, minifigures, and user minifigure parts, excluding assembled sets
    parts = Part.query.join(UserSet).filter(UserSet.status != 'assembled').all()
    minifigures = Minifigure.query.join(UserSet).filter(UserSet.status != 'assembled').all()

    # Calculate totals and missing counts
    total_parts = sum(part.have_quantity for part in parts)
    missing_parts = sum(part.quantity - part.have_quantity for part in parts if part.quantity > part.have_quantity)
    missing_spare_parts = sum(part.quantity - part.have_quantity for part in parts if part.is_spare and part.quantity > part.have_quantity)
    missing_minifigures = sum(minifig.quantity - minifig.have_quantity for minifig in minifigures if minifig.quantity > minifig.have_quantity)

    # Render the dashboard template with counts
    return render_template(
        'dashboard.html',
        total_parts=total_parts,
        missing_parts=missing_parts,
        missing_spare_parts=missing_spare_parts,
        missing_minifigures=missing_minifigures,
    )

@dashboard_bp.route('/api/missing_parts', methods=['GET'])
def api_missing_parts():
    """
    API endpoint to retrieve missing parts with enriched data, excluding parts from assembled sets.
    """
    master_lookup = load_master_lookup()

    # Query missing parts and their associated user sets and categories
    missing_parts = (
        Part.query.options(
            selectinload(Part.user_set),
            selectinload(Part.category)
        )
        .filter(Part.quantity > Part.have_quantity)
        .join(UserSet, UserSet.id == Part.user_set_id)
        .filter(UserSet.status != "assembled")
        .all()
    )

    # Helper function for enriching part data
    def enrich_item(item):
        part_data = master_lookup.get(item.part_num, {})
        img_url = cache_image(item.part_img_url or "/static/default_image.png")
        return {
            'set_id': item.user_set.template_set.set_number,
            'internal_id': item.user_set.id,
            'item_id': item.part_num,
            'name': item.name,
            'color': item.color or "Unknown",
            'missing_quantity': item.quantity - item.have_quantity,
            'category': item.category.name if item.category else "No Category",
            'location': f"Location: {part_data.get('location', 'Unknown')}, "
                        f"Level: {part_data.get('level', 'Unknown')}, "
                        f"Box: {part_data.get('box', 'Unknown')}" if part_data else "Not Specified",
            'img_url': img_url,
        }

    # Enrich and return missing parts data
    missing_parts_data = [enrich_item(part) for part in missing_parts]
    return jsonify(missing_parts_data)
