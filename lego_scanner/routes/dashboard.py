import os
import requests
from flask import Blueprint, jsonify, render_template, current_app, request
from models import db, UserSet, Part, Minifigure, UserMinifigurePart
from sqlalchemy.orm import selectinload

dashboard_bp = Blueprint('dashboard', __name__)

def cache_image(image_url, cache_dir='static/cache/images'):
    """Download and cache an image locally if not already cached."""
    fallback_image = "/static/default_image.png"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

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
                return fallback_image
        except Exception as e:
            current_app.logger.error(f"Error downloading image {image_url}: {e}")
            return fallback_image
    return f"/{filename}"

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Dashboard route to display an overview of total and missing parts/minifigure parts.
    """
    # Query parts and user minifigure parts, excluding specific set statuses
    parts = Part.query.join(UserSet).filter(~UserSet.status.in_(['assembled', 'konvolut'])).all()
    minifigure_parts = (
        UserMinifigurePart.query.options(
            selectinload(UserMinifigurePart.user_set)
        )
        .filter(UserMinifigurePart.quantity > UserMinifigurePart.have_quantity)
        .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
        .all()
    )

    # Calculate totals and missing counts
    total_parts = sum(part.have_quantity for part in parts)
    missing_parts = len(Part.query.options(
            selectinload(Part.user_set),
            selectinload(Part.category)
        )
        .filter(Part.quantity > Part.have_quantity)
        .join(UserSet, UserSet.id == Part.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
        .all())
    missing_spare_parts = sum(part.quantity - part.have_quantity for part in parts if part.is_spare and part.quantity > part.have_quantity)
    missing_minifigure_parts = sum(
        minifigure_part.quantity - minifigure_part.have_quantity
        for minifigure_part in minifigure_parts
        if minifigure_part.quantity > minifigure_part.have_quantity
    )

    # Calculate konvolut-specific data
    konvolut_parts = len(Part.query.options(
            selectinload(Part.user_set),
            selectinload(Part.category)
        )
        .filter(Part.quantity > Part.have_quantity)
        .join(UserSet, UserSet.id == Part.user_set_id)
        .filter(UserSet.status == 'konvolut')
        .all())
    konvolut_minifigure_parts = len(UserMinifigurePart.query.options(
            selectinload(UserMinifigurePart.user_set)
        )
        .filter(UserMinifigurePart.quantity > UserMinifigurePart.have_quantity)
        .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
        .filter(UserSet.status == 'konvolut')
        .all())

    # Render the dashboard template with counts
    return render_template(
        'dashboard.html',
        total_parts=total_parts,
        missing_parts=missing_parts,
        missing_spare_parts=missing_spare_parts,
        missing_minifigure_parts=missing_minifigure_parts,
        konvolut_parts=konvolut_parts,
        konvolut_minifigure_parts=konvolut_minifigure_parts,
    )

@dashboard_bp.route('/update_quantity', methods=['POST'])
def update_quantity():
    """Batch update have_quantity for parts or minifigure parts."""
    data = request.get_json()
    changes = data.get('changes', [])

    if not changes:
        return jsonify({'error': 'No changes provided'}), 400

    try:
        for change in changes:
            part_id = change.get('part_id')
            new_quantity = change.get('new_quantity')

            if not part_id or new_quantity is None:
                continue  # Skip invalid entries

            part = Part.query.filter_by(id=part_id).first()
            if part:
                part.have_quantity = new_quantity
            else:
                minifigure_part = UserMinifigurePart.query.filter_by(id=part_id).first()
                if minifigure_part:
                    minifigure_part.have_quantity = new_quantity

        db.session.commit()
        return jsonify({'message': 'Changes saved successfully!'}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating quantities: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to save changes'}), 500


@dashboard_bp.route('/details/<category>', methods=['GET'])
def details(category):
    """Page to show detailed data for parts or minifigure parts."""
    category = category.lower()

    # Define category-specific queries
    if category == 'missing_parts':
        data = (
            Part.query.options(
                selectinload(Part.user_set),
                selectinload(Part.category)
            )
            .filter(Part.quantity > Part.have_quantity)
            .join(UserSet, UserSet.id == Part.user_set_id)
            .filter(~UserSet.status.in_(['assembled', 'konvolut']))
            .all()
        )
        title = "Missing Parts"
        include_category = True
    elif category == 'missing_minifigure_parts':
        data = (
            UserMinifigurePart.query.options(
                selectinload(UserMinifigurePart.user_set)
            )
            .filter(UserMinifigurePart.quantity > UserMinifigurePart.have_quantity)
            .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
            .filter(~UserSet.status.in_(['assembled', 'konvolut']))
            .all()
        )
        title = "Missing Minifigure Parts"
        include_category = False
    elif category == 'konvolut_parts':
        data = (
            Part.query.options(
                selectinload(Part.user_set),
                selectinload(Part.category)
            )
            .join(UserSet, UserSet.id == Part.user_set_id)
            .filter(UserSet.status == 'konvolut')
            .all()
        )
        title = "Konvolut Parts"
        include_category = True
    elif category == 'konvolut_minifigure_parts':
        data = (
            UserMinifigurePart.query.options(
                selectinload(UserMinifigurePart.user_set)
            )
            .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
            .filter(UserSet.status == 'konvolut')
            .all()
        )
        title = "Konvolut Minifigure Parts"
        include_category = False
    else:
        return "Invalid category", 400

    # Enrich the data for rendering
    enriched_data = [
        {
            "part_id": item.id,
            "set_id": item.user_set.template_set.set_number if hasattr(item, "user_set") else None,
            "internal_id": item.user_set.id if hasattr(item, "user_set") else None,
            "part_num": getattr(item, "part_num", None),
            "name": item.name,
            "color": getattr(item, "color", "Unknown"),
            "category": item.category.name if include_category and item.category else None,
            "have_quantity": item.have_quantity,
            "total_quantity": item.quantity,
            "image_url": item.part_img_url or "/static/default_image.png",
        }
        for item in data
    ]

    # Get unique categories for dropdown if applicable
    categories = []
    if include_category:
        categories = sorted({item.category.name for item in data if item.category})

    return render_template(
        'details.html',
        title=title,
        data=enriched_data,
        category=category,
        categories=categories,
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
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
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
            'total_quantity': item.quantity,
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

@dashboard_bp.route('/api/missing_minifigure_parts', methods=['GET'])
def api_missing_minifigure_parts():
    """
    API endpoint to retrieve missing minifigure parts with enriched data, excluding specific set statuses.
    """
    master_lookup = load_master_lookup()

    # Query missing minifigure parts and their associated user sets
    missing_minifigure_parts = (
        UserMinifigurePart.query.options(
            selectinload(UserMinifigurePart.user_set)  # Load associated user sets
        )
        .filter(UserMinifigurePart.quantity > UserMinifigurePart.have_quantity)  # Missing parts
        .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))  # Exclude specific statuses
        .all()
    )

    # Helper function for enriching minifigure part data
    def enrich_minifigure_part(item):
        part_data = master_lookup.get(item.part_num, {})
        img_url = cache_image(item.part_img_url or "/static/default_image.png")
        return {
            'set_id': item.user_set.template_set.set_number,
            'internal_id': item.user_set.id,
            'part_num': item.part_num,
            'name': item.name,
            'color': item.color or "Unknown",  # Include color
            'total_quantity': item.quantity,
            'missing_quantity': item.quantity - item.have_quantity,
            'location': f"Location: {part_data.get('location', 'Unknown')}, "
                        f"Level: {part_data.get('level', 'Unknown')}, "
                        f"Box: {part_data.get('box', 'Unknown')}" if part_data else "Not Specified",
            'img_url': img_url,
        }

    # Enrich and return missing minifigure parts data
    missing_minifigure_parts_data = [enrich_minifigure_part(part) for part in missing_minifigure_parts]
    return jsonify(missing_minifigure_parts_data)

