import os
import requests
from flask import Blueprint, jsonify, render_template, current_app, request
from models import db, UserSet, PartSetMapping, UserMinifigurePart
from sqlalchemy.orm import selectinload
from services.cache_service import cache_image  # Import the central service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Dashboard route to display an overview of total and missing parts/minifigure parts.
    """
    # Query parts and user minifigure parts, excluding specific set statuses
    parts = PartSetMapping.query.join(UserSet).filter(~UserSet.status.in_(['assembled', 'konvolut'])).all()
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
    missing_parts = len(PartSetMapping.query.options(
            selectinload(PartSetMapping.user_set)
        )
        .filter(PartSetMapping.quantity > PartSetMapping.have_quantity)
        .join(UserSet, UserSet.id == PartSetMapping.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
        .all())

    missing_spare_parts = sum(part.quantity - part.have_quantity for part in parts if part.is_spare and part.quantity > part.have_quantity)

    missing_minifigure_parts = sum(
        minifigure_part.quantity - minifigure_part.have_quantity
        for minifigure_part in minifigure_parts
        if minifigure_part.quantity > minifigure_part.have_quantity
    )

    # Calculate konvolut-specific data
    missing_konvolut_parts = sum(
        part.quantity - part.have_quantity
        for part in PartSetMapping.query.options(selectinload(PartSetMapping.user_set))
        .join(UserSet, UserSet.id == PartSetMapping.user_set_id)
        .filter(UserSet.status == 'konvolut', PartSetMapping.quantity > PartSetMapping.have_quantity)
        .all()
    )

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
        konvolut_parts=missing_konvolut_parts,
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

            part = PartSetMapping.query.filter_by(id=part_id).first()
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
            PartSetMapping.query.options(
                selectinload(PartSetMapping.user_set),
            )
            .filter(PartSetMapping.quantity > PartSetMapping.have_quantity)
            .join(UserSet, UserSet.id == PartSetMapping.user_set_id)
            .filter(~UserSet.status.in_(['assembled', 'konvolut']))
            .all()
        )
        title = "Missing Parts"
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
    else:
        return "Invalid category", 400

    # Enrich the data for rendering
    enriched_data = [
        {
            "part_id": item.id,
            "set_id": item.user_set.set.set_num if hasattr(item, "user_set") else None,
            "part_num": item.part_num,
            "name": getattr(item, "name", None),
            "have_quantity": item.have_quantity,
            "total_quantity": item.quantity,
            "image_url": cache_image(item.part.part_img_url or "/static/default_image.png"),
        }
        for item in data
    ]

    return render_template(
        'details.html',
        title=title,
        data=enriched_data,
        category=category,
    )


@dashboard_bp.route('/api/missing_parts', methods=['GET'])
def api_missing_parts():
    """
    API endpoint to retrieve missing parts with enriched data, excluding parts from assembled sets.
    """
    master_lookup = load_part_lookup()

    missing_parts = (
        PartSetMapping.query.options(
            selectinload(PartSetMapping.user_set),
        )
        .filter(PartSetMapping.quantity > PartSetMapping.have_quantity)
        .join(UserSet, UserSet.id == PartSetMapping.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
        .all()
    )

    def enrich_item(item):
        part_data = master_lookup.get(item.part_num, {})
        img_url = cache_image(item.part.part_img_url or "/static/default_image.png")
        return {
            'set_id': item.user_set.set.set_num,
            'item_id': item.part_num,
            'name': getattr(item.part, "name", "Unknown"),
            'total_quantity': item.quantity,
            'missing_quantity': item.quantity - item.have_quantity,
            'img_url': img_url,
        }

    missing_parts_data = [enrich_item(part) for part in missing_parts]
    return jsonify(missing_parts_data)


@dashboard_bp.route('/api/missing_minifigure_parts', methods=['GET'])
def api_missing_minifigure_parts():
    """
    API endpoint to retrieve missing minifigure parts with enriched data, excluding specific set statuses.
    """
    master_lookup = load_part_lookup()

    missing_minifigure_parts = (
        UserMinifigurePart.query.options(
            selectinload(UserMinifigurePart.user_set)
        )
        .filter(UserMinifigurePart.quantity > UserMinifigurePart.have_quantity)
        .join(UserSet, UserSet.id == UserMinifigurePart.user_set_id)
        .filter(~UserSet.status.in_(['assembled', 'konvolut']))
        .all()
    )

    def enrich_minifigure_part(item):
        part_data = master_lookup.get(item.part_num, {})
        img_url = cache_image(item.part_img_url or "/static/default_image.png")
        return {
            'set_id': item.user_set.set.set_num,
            'item_id': item.part_num,
            'name': item.name,
            'total_quantity': item.quantity,
            'missing_quantity': item.quantity - item.have_quantity,
            'img_url': img_url,
        }

    missing_minifigure_parts_data = [enrich_minifigure_part(part) for part in missing_minifigure_parts]
    return jsonify(missing_minifigure_parts_data)
