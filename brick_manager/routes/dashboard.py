from flask import Blueprint, jsonify, render_template, current_app, request
from models import db, UserSet, PartInSet, Minifigure, UserMinifigurePart, PartInfo, PartStorage
from sqlalchemy.orm import selectinload
from services.cache_service import cache_image
from services.part_lookup_service import load_part_lookup

dashboard_bp = Blueprint('dashboard', __name__)

from flask import url_for

def enrich_part(item, master_lookup):
    """
    Enrich part data with additional information.
    """
    part_info = PartInfo.query.filter_by(part_num=item.part_num).first()
    part_data = master_lookup.get(item.part_num, {})
    category = part_info.category.name if part_info and part_info.category else "No Category"

    # Fallback to default image if the part image URL is unavailable
    img_url = cache_image(part_info.part_img_url if part_info else "/static/default_image.png")

    return {
        'part_id': item.id,
        'set_id': item.user_set.template_set.set_number if item.user_set else None,
        'internal_id': item.user_set.id if item.user_set else None,
        'part_num': item.part_num,
        'name': part_info.name if part_info else "Unknown",
        'color': item.color or "Unknown",
        'total_quantity': item.quantity,
        'have_quantity': item.have_quantity,  # Ensure this is included
        'category': category,
        'location': f"Location: {part_data.get('location', 'Unknown')}, "
                    f"Level: {part_data.get('level', 'Unknown')}, "
                    f"Box: {part_data.get('box', 'Unknown')}" if part_data else "Not Specified",
        'image_url': img_url,
    }

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Dashboard route to display an overview of total and missing parts/minifigure parts.
    """
    parts_in_sets = PartInSet.query.join(UserSet).filter(
        ~UserSet.status.in_(['assembled', 'konvolut'])
    ).all()

    minifigure_parts = UserMinifigurePart.query.join(UserSet).filter(
        UserMinifigurePart.quantity > UserMinifigurePart.have_quantity,
        ~UserSet.status.in_(['assembled', 'konvolut'])
    ).all()

    total_parts = sum(part.have_quantity for part in parts_in_sets)

    missing_parts = sum(
        part.quantity - part.have_quantity for part in parts_in_sets if part.quantity > part.have_quantity
    )

    missing_spare_parts = sum(
        part.quantity - part.have_quantity for part in parts_in_sets if part.is_spare and part.quantity > part.have_quantity
    )

    missing_minifigure_parts = sum(
        part.quantity - part.have_quantity for part in minifigure_parts
    )

    konvolut_parts = PartInSet.query.join(UserSet).filter(UserSet.status == 'konvolut').all()

    missing_konvolut_parts = sum(
        part.quantity - part.have_quantity for part in konvolut_parts if part.quantity > part.have_quantity
    )
    konvolut_minifigure_parts = UserMinifigurePart.query.join(UserSet).filter(UserSet.status == 'konvolut').all()

    missing_konvolut_minifigure_parts = sum(
        part.quantity - part.have_quantity for part in konvolut_minifigure_parts if part.quantity > part.have_quantity
    )

#konvolut_minifigure_parts
    return render_template(
        'dashboard.html',
        total_parts=total_parts,
        missing_parts=missing_parts,
        missing_spare_parts=missing_spare_parts,
        missing_minifigure_parts=missing_minifigure_parts,
        konvolut_parts=len(konvolut_parts),
        missing_konvolut_parts=missing_konvolut_parts,
        missing_konvolut_minifigure_parts= missing_konvolut_minifigure_parts,
    )


@dashboard_bp.route('/update_quantity', methods=['POST'])
def update_quantity():
    """Batch update have_quantity for parts or minifigure parts."""
    data = request.get_json()
    changes = data.get('changes', [])

    if not changes:
        return jsonify({'error': 'No changes provided'}), 400

    try:
        updated_records = 0
        with db.session.no_autoflush:  # Avoid committing before all updates are made
            for change in changes:
                part_id = change.get('part_id')
                new_quantity = change.get('new_quantity')

                if not part_id or new_quantity is None:
                    current_app.logger.warning(f"Invalid entry in changes: {change}")
                    continue  # Skip invalid entries

                # Update `PartInSet` first
                part = PartInSet.query.filter_by(id=part_id).first()
                if part:
                    current_app.logger.debug(f"Updating PartInSet ID {part_id} to quantity {new_quantity}")
                    part.have_quantity = max(0, min(part.quantity, int(new_quantity)))
                    db.session.add(part)
                    updated_records += 1
                else:
                    # If not found in `PartInSet`, try `UserMinifigurePart`
                    minifigure_part = UserMinifigurePart.query.filter_by(id=part_id).first()
                    if minifigure_part:
                        current_app.logger.debug(f"Updating UserMinifigurePart ID {part_id} to quantity {new_quantity}")
                        minifigure_part.have_quantity = max(0, min(minifigure_part.quantity, int(new_quantity)))
                        db.session.add(minifigure_part)
                        updated_records += 1

        if updated_records > 0:
            db.session.commit()  # Commit all changes at once for efficiency
            current_app.logger.info(f"Successfully updated {updated_records} records.")
            return jsonify({'message': f"{updated_records} records updated successfully!"}), 200
        else:
            current_app.logger.warning("No records were updated.")
            return jsonify({'message': "No records found to update."}), 404

    except Exception as e:
        current_app.logger.error(f"Failed to update quantities: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update quantities.'}), 500



@dashboard_bp.route('/details/<category>', methods=['GET'])
def details(category):
    """
    Page to show detailed data for parts or minifigure parts.
    """
    category = category.lower()
    master_lookup = load_part_lookup()

    if category == 'missing_parts':
        data = PartInSet.query.join(UserSet).filter(
            PartInSet.quantity > PartInSet.have_quantity,
            ~UserSet.status.in_(['assembled', 'konvolut'])
        ).all()
        title = "Missing Parts"
    elif category == 'missing_minifigure_parts':
        data = UserMinifigurePart.query.join(UserSet).filter(
            UserMinifigurePart.quantity > UserMinifigurePart.have_quantity,
            ~UserSet.status.in_(['assembled', 'konvolut'])
        ).all()
        title = "Missing Minifigure Parts"
    elif category == 'konvolut_parts':
        data = PartInSet.query.join(UserSet).filter(UserSet.status == 'konvolut').all()
        title = "Konvolut Parts"
    elif category == 'konvolut_minifigure_parts':
        data = UserMinifigurePart.query.join(UserSet).filter(UserSet.status == 'konvolut').all()
        title = "Konvolut Minifigure Parts"
    else:
        current_app.logger.error(f"Invalid category requested: {category}")
        return "Invalid category", 400  # This line triggers the 400 error

    enriched_data = [
        enrich_part(item, master_lookup)
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
    missing_parts = PartInSet.query.join(UserSet).filter(
        PartInSet.quantity > PartInSet.have_quantity,
        ~UserSet.status.in_(['assembled', 'konvolut'])
    ).all()

    enriched_data = [enrich_part(item, master_lookup) for item in missing_parts]
    return jsonify(enriched_data)

@dashboard_bp.route('/api/missing_minifigure_parts', methods=['GET'])
def api_missing_minifigure_parts():
    """
    API endpoint to retrieve missing minifigure parts with enriched data, excluding specific set statuses.
    """
    master_lookup = load_part_lookup()
    missing_minifigure_parts = UserMinifigurePart.query.join(UserSet).filter(
        UserMinifigurePart.quantity > UserMinifigurePart.have_quantity,
        ~UserSet.status.in_(['assembled', 'konvolut'])
    ).all()

    enriched_data = [enrich_part(item, master_lookup) for item in missing_minifigure_parts]
    return jsonify(enriched_data)
