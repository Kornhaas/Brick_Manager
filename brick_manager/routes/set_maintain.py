"""
This module manages the maintenance of user sets, including adding, updating, deleting,
and generating labels for sets and their parts.
"""
# pylint: disable=C0301,W0718

import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from models import db, User_Set, UserMinifigurePart, RebrickableParts, PartStorage, RebrickablePartCategories, RebrickableThemes

set_maintain_bp = Blueprint('set_maintain', __name__)


@set_maintain_bp.route('/set_maintain', methods=['GET'])
def set_maintain():
    """
    Displays the list of user sets with enhanced information including theme data.
    """
    user_sets = User_Set.query.options(
        joinedload(User_Set.template_set),
        joinedload(User_Set.parts_in_set),
        joinedload(User_Set.minifigures_in_set)
    ).order_by(User_Set.id.desc()).all()

    sets_with_completeness = []
    for user_set in user_sets:
        total_quantity = sum(part.quantity for part in user_set.parts_in_set)
        total_have_quantity = sum(
            part.have_quantity for part in user_set.parts_in_set)

        user_minifigure_parts = UserMinifigurePart.query.filter_by(
            user_set_id=user_set.id).all()
        total_quantity += sum(part.quantity for part in user_minifigure_parts)
        total_have_quantity += sum(
            part.have_quantity for part in user_minifigure_parts)

        completeness_percentage = (
            (total_have_quantity / total_quantity) *
            100 if total_quantity > 0 else 0
        )

        # Get theme information
        theme_name = "Unknown"
        if user_set.template_set and user_set.template_set.theme:
            theme_name = user_set.template_set.theme.name

        # Get set name
        set_name = "Unknown Set"
        if user_set.template_set:
            set_name = user_set.template_set.name

        sets_with_completeness.append({
            'user_set': user_set,
            'completeness_percentage': round(completeness_percentage, 2),
            'theme_name': theme_name,
            'set_name': set_name,
            'set_num': user_set.template_set.set_num if user_set.template_set else "Unknown",
            'total_parts': total_quantity,
            'parts_owned': total_have_quantity
        })

    return render_template('set_maintain.html', sets_with_completeness=sets_with_completeness)


@set_maintain_bp.route('/set_maintain/<int:user_set_id>', methods=['GET'])
def get_user_set_details(user_set_id):
    """
    Returns the details of a specific User_Set, including its parts, minifigures, and user minifigure parts.
    """
    from models import RebrickableColors, RebrickableInventoryParts, RebrickableInventories

    user_set = User_Set.query.options(
        joinedload(User_Set.template_set),
        joinedload(User_Set.parts_in_set),
        joinedload(User_Set.minifigures_in_set)
    ).get_or_404(user_set_id)

    user_minifigure_parts = UserMinifigurePart.query.options(
        joinedload(UserMinifigurePart.rebrickable_part),
        joinedload(UserMinifigurePart.rebrickable_color)
    ).filter_by(user_set_id=user_set_id).all()

    total_quantity = sum(part.quantity for part in user_set.parts_in_set)
    total_have_quantity = sum(
        part.have_quantity for part in user_set.parts_in_set)
    total_quantity += sum(part.quantity for part in user_minifigure_parts)
    total_have_quantity += sum(part.have_quantity for part in user_minifigure_parts)

    completeness_percentage = (
        (total_have_quantity / total_quantity) *
        100 if total_quantity > 0 else 0
    )

    def enrich_item(part):
        storage_data = db.session.query(PartStorage).filter_by(
            part_num=part.part_num).first()

        # Get part info with proper joins to get color and image information
        part_query = db.session.query(
            RebrickableParts,
            RebrickableColors
        ).join(
            RebrickableColors, RebrickableColors.id == part.color_id
        ).filter(
            RebrickableParts.part_num == part.part_num
        ).first()

        part_info = part_query[0] if part_query else None
        color_info = part_query[1] if part_query else None

        # Get category information using part_cat_id
        category_name = "Unknown Category"
        if part_info and part_info.part_cat_id:
            category = db.session.query(RebrickablePartCategories).filter_by(
                id=part_info.part_cat_id
            ).first()
            if category:
                category_name = category.name

        # Try to get inventory-specific image URL for regular parts
        inventory_img_url = None
        if user_set.template_set:
            inventory = RebrickableInventories.query.filter_by(
                set_num=user_set.template_set.set_num).first()
            if inventory:
                inv_part = RebrickableInventoryParts.query.filter_by(
                    inventory_id=inventory.id,
                    part_num=part.part_num,
                    color_id=part.color_id
                ).first()
                if inv_part and inv_part.img_url:
                    inventory_img_url = inv_part.img_url

        return {
            'id': part.id,
            'part_num': part.part_num,
            'name': part_info.name if part_info else "Unknown",
            'category': category_name,
            'quantity': part.quantity,
            'have_quantity': part.have_quantity,
            'color': color_info.name if color_info else "Unknown",
            'color_rgb': color_info.rgb if color_info else "FFFFFF",
            'part_img_url': inventory_img_url or (part_info.part_img_url if part_info else ''),
            'location': f"Location: {storage_data.location if storage_data else 'Unknown'}, "
            f"Level: {storage_data.level if storage_data else 'Unknown'}, "
            f"Box: {storage_data.box if storage_data else 'Unknown'}",
            'status': "Available" if storage_data else "Not Available",
            'is_spare': getattr(part, 'is_spare', False)
        }

    def enrich_minifigure_part(part):
        storage_data = db.session.query(PartStorage).filter_by(
            part_num=part.part_num).first()

        # Use the relationships that should be already loaded
        part_info = part.rebrickable_part
        color_info = part.rebrickable_color

        # Get category information using part_cat_id
        category_name = "Unknown Category"
        if part_info and part_info.part_cat_id:
            category = db.session.query(RebrickablePartCategories).filter_by(
                id=part_info.part_cat_id
            ).first()
            if category:
                category_name = category.name

        # For minifigure parts, first try the simple part image, then look for inventory-specific
        part_img_url = part_info.part_img_url if part_info else ''

        # Try to find a better image from minifigure inventories
        if not part_img_url:
            minifigures_in_set = user_set.minifigures_in_set
            for minifig in minifigures_in_set:
                inventory = RebrickableInventories.query.filter_by(
                    set_num=minifig.fig_num).first()
                if inventory:
                    inv_part = RebrickableInventoryParts.query.filter_by(
                        inventory_id=inventory.id,
                        part_num=part.part_num,
                        color_id=part.color_id
                    ).first()
                    if inv_part and inv_part.img_url:
                        part_img_url = inv_part.img_url
                        break  # Found the image, stop looking

        result = {
            'id': part.id,
            'part_num': part.part_num,
            'name': part_info.name if part_info else "Unknown",
            'category': category_name,
            'quantity': part.quantity,
            'have_quantity': part.have_quantity,
            'color': color_info.name if color_info else "Unknown",
            'color_rgb': color_info.rgb if color_info else "FFFFFF",
            'part_img_url': part_img_url,
            'location': f"Location: {storage_data.location if storage_data else 'Unknown'}, "
            f"Level: {storage_data.level if storage_data else 'Unknown'}, "
            f"Box: {storage_data.box if storage_data else 'Unknown'}",
            'status': "Available" if storage_data else "Not Available",
            'is_spare': getattr(part, 'is_spare', False)
        }

        # Debug logging for minifigure parts
        current_app.logger.debug(
            f"Minifigure part enriched: {part.part_num}, name: {result['name']}, img_url: {result['part_img_url']}")
        return result

    parts = [enrich_item(part) for part in user_set.parts_in_set]

    # Sort parts by color, then category, then name
    parts.sort(key=lambda x: (x['color'], x['category'], x['name']))

    # Group minifigure parts by minifigure using the new minifigure_id field
    minifigures_with_parts = []
    for minifig in user_set.minifigures_in_set:
        # Get parts for this specific minifigure using the minifigure_id
        minifig_parts = [
            part for part in user_minifigure_parts if part.minifigure_id == minifig.id]

        # Enrich and sort the parts for this minifigure
        enriched_parts = [enrich_minifigure_part(
            part) for part in minifig_parts]
        enriched_parts.sort(key=lambda x: (
            x['color'], x['category'], x['name']))

        minifig_data = {
            'id': minifig.id,
            'fig_num': minifig.fig_num,
            'name': minifig.rebrickable_minifig.name if minifig.rebrickable_minifig else "Unknown",
            'quantity': minifig.quantity,
            'img_url': minifig.rebrickable_minifig.img_url if minifig.rebrickable_minifig else '',
            'location': "Not Specified",
            'status': "Not Available",
            'parts': enriched_parts
        }
        minifigures_with_parts.append(minifig_data)

    return jsonify({
        'set_img_url': user_set.template_set.img_url if user_set.template_set and user_set.template_set.img_url else '/static/default_image.png',
        'parts': parts,
        # Now includes parts grouped with each minifig
        'minifigs': minifigures_with_parts,
        'status': user_set.status,
        'completeness_percentage': round(completeness_percentage, 2)
    })


@set_maintain_bp.route('/set_maintain/update', methods=['POST'])
def update_user_set():
    """
    Updates the parts, minifigures, and user minifigure parts owned for a specific User_Set.
    """
    user_set_id = request.form.get('user_set_id')
    status = request.form.get('status')
    user_set = User_Set.query.get_or_404(user_set_id)

    try:
        for part in user_set.parts_in_set:
            have_quantity = request.form.get(f'part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(
                    0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        user_minifigure_parts = UserMinifigurePart.query.filter_by(
            user_set_id=user_set_id).all()
        for part in user_minifigure_parts:
            have_quantity = request.form.get(f'minifig_part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(
                    0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        if status:
            user_set.status = status
            db.session.add(user_set)

        db.session.commit()
        flash(f"User Set for {
              user_set.template_set.set_num} updated successfully.", "success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error updating User_Set: %s", error)
        flash("Failed to update User_Set.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))


@set_maintain_bp.route('/set_maintain/update_label_status', methods=['POST'])
def update_set_label_status():
    """
    Updates the label_printed status for a user set.
    """
    try:
        current_app.logger.info("update_set_label_status endpoint called")
        data = request.get_json()
        current_app.logger.info(f"Received data: {data}")

        if not data:
            current_app.logger.error("No data received")
            return jsonify({"error": "Invalid input data format."}), 400

        user_set_id = data.get("user_set_id")
        label_printed = data.get("label_printed")
        current_app.logger.info(
            f"user_set_id: {user_set_id}, label_printed: {label_printed}")

        if user_set_id is None or label_printed is None:
            current_app.logger.error("Missing required fields")
            return jsonify({"error": "user_set_id and label_printed are required."}), 400

        user_set = User_Set.query.get(user_set_id)
        if not user_set:
            current_app.logger.error(f"User set {user_set_id} not found")
            return jsonify({"error": "User set not found."}), 404

        current_app.logger.info(
            f"Before update: user_set.label_printed = {user_set.label_printed}")
        user_set.label_printed = bool(label_printed)
        current_app.logger.info(
            f"After update: user_set.label_printed = {user_set.label_printed}")
        db.session.commit()
        current_app.logger.info("Database committed successfully")

        return jsonify({"message": "Label status updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating set label status: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@set_maintain_bp.route('/set_maintain/delete/<int:user_set_id>', methods=['POST'])
def delete_user_set(user_set_id):
    """
    Deletes a specific User_Set from the database.
    """
    try:
        user_set = User_Set.query.options(joinedload(
            User_Set.template_set)).get_or_404(user_set_id)
        template_set_number = user_set.template_set.set_num
        db.session.delete(user_set)
        db.session.commit()
        flash(f"User Set for {
              template_set_number} deleted successfully.", "success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error deleting User_Set: %s", error)
        flash("Failed to delete User Set.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))


@set_maintain_bp.route('/set_maintain/generate_label', methods=['POST'])
def generate_label():
    """
    Generate a DrawIO file for a Brick set label and provide it for download.
    """
    set_id = request.json.get('set_id')
    box_size = request.json.get('box_size')
    current_app.logger.info(
        "Generating label for set %s with box size %s", set_id, box_size)
    try:
        user_set = User_Set.query.join(User_Set.template_set).filter(
            User_Set.id == set_id).first()
        if not user_set:
            return jsonify({'error': 'Set not found in the database'}), 404

        label_data = {
            "BOX_LONG_TITLE": f"Brick SET - {user_set.template_set.set_num} - {user_set.template_set.name.replace('&', 'and')}",
            "BOX_SHORT_TITLE": user_set.template_set.set_num,
            "IMAGE_CONTEXT": user_set.template_set.img_url,
            "BOX_ID": str(user_set.id)
        }

        safe_box_size = secure_filename(box_size)
        drawio_template = os.path.join("templates", f"{safe_box_size}.drawio")
        if not os.path.exists(drawio_template):
            return jsonify({'error': f'DrawIO template {box_size} not found'}), 400

        with open(drawio_template, 'r', encoding='utf-8') as template_file:
            content = template_file.read()
            for key, value in label_data.items():
                content = content.replace(key, value)

        output_file = f"output/{set_id}_{box_size}.drawio"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(content)

        # Automatically mark the label as printed
        user_set.label_printed = True
        db.session.commit()
        current_app.logger.info(f"Label automatically marked as printed for set {set_id}")

        return send_file(output_file, as_attachment=True)
    except Exception as error:
        current_app.logger.error("Error generating label: %s", error)
        return jsonify({'error': 'Failed to generate label'}), 500
