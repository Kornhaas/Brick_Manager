"""
This module manages the maintenance of user sets, including adding, updating, deleting,
and generating labels for sets and their parts.
"""
# pylint: disable=C0301,W0718

import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from models import db, UserSet, UserMinifigurePart, PartInfo, PartStorage

set_maintain_bp = Blueprint('set_maintain', __name__)


@set_maintain_bp.route('/set_maintain', methods=['GET'])
def set_maintain():
    """
    Displays the list of user sets.
    """
    user_sets = UserSet.query.options(
        joinedload(UserSet.template_set),
        joinedload(UserSet.parts_in_set),
        joinedload(UserSet.minifigures)
    ).order_by(UserSet.id.desc()).all()

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

        sets_with_completeness.append({
            'user_set': user_set,
            'completeness_percentage': round(completeness_percentage, 2)
        })

    return render_template('set_maintain.html', sets_with_completeness=sets_with_completeness)


@set_maintain_bp.route('/set_maintain/<int:user_set_id>', methods=['GET'])
def get_user_set_details(user_set_id):
    """
    Returns the details of a specific UserSet, including its parts, minifigures, and user minifigure parts.
    """
    # master_lookup = load_part_lookup()
    user_set = UserSet.query.options(
        joinedload(UserSet.parts_in_set),
        joinedload(UserSet.minifigures)
    ).get_or_404(user_set_id)

    user_minifigure_parts = UserMinifigurePart.query.filter_by(
        user_set_id=user_set_id).all()

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
        part_info = PartInfo.query.filter_by(part_num=part.part_num).first()
        return {
            'id': part.id,
            'part_num': part.part_num,
            'name': part_info.name if part_info else "Unknown",
            'quantity': part.quantity,
            'have_quantity': part.have_quantity,
            'color': part.color,
            'color_rgb': part.color_rgb,
            'part_img_url': part_info.part_img_url if part_info else '',
            'location': f"Location: {storage_data.location if storage_data else 'Unknown'}, "
            f"Level: {storage_data.level if storage_data else 'Unknown'}, "
            f"Box: {storage_data.box if storage_data else 'Unknown'}",
            'status': "Available" if storage_data else "Not Available"
        }

    parts = [enrich_item(part) for part in user_set.parts_in_set]
    minifigure_parts = [enrich_item(part) for part in user_minifigure_parts]

    minifigs = [
        {
            'id': minifig.id,
            'fig_num': minifig.fig_num,
            'name': minifig.name,
            'quantity': minifig.quantity,
            'have_quantity': minifig.have_quantity,
            'img_url': minifig.img_url,
            'location': "Not Specified",
            'status': "Not Available"
        }
        for minifig in user_set.minifigures
    ]

    return jsonify({
        'set_img_url': user_set.template_set.set_img_url,
        'parts': parts,
        'minifigs': minifigs,
        'minifigure_parts': minifigure_parts,
        'status': user_set.status,
        'completeness_percentage': round(completeness_percentage, 2)
    })


@set_maintain_bp.route('/set_maintain/update', methods=['POST'])
def update_user_set():
    """
    Updates the parts, minifigures, and user minifigure parts owned for a specific UserSet.
    """
    user_set_id = request.form.get('user_set_id')
    status = request.form.get('status')
    user_set = UserSet.query.get_or_404(user_set_id)

    try:
        for part in user_set.parts_in_set:
            have_quantity = request.form.get(f'part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(
                    0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        for minifig in user_set.minifigures:
            have_quantity = request.form.get(f'minifig_id_{minifig.id}')
            if have_quantity is not None:
                minifig.have_quantity = max(
                    0, min(minifig.quantity, int(have_quantity)))
                db.session.add(minifig)

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
              user_set.template_set.set_number} updated successfully.", "success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error updating UserSet: %s", error)
        flash("Failed to update UserSet.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))


@set_maintain_bp.route('/set_maintain/delete/<int:user_set_id>', methods=['POST'])
def delete_user_set(user_set_id):
    """
    Deletes a specific UserSet from the database.
    """
    try:
        user_set = UserSet.query.options(joinedload(
            UserSet.template_set)).get_or_404(user_set_id)
        template_set_number = user_set.template_set.set_number
        db.session.delete(user_set)
        db.session.commit()
        flash(f"User Set for {
              template_set_number} deleted successfully.", "success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error deleting UserSet: %s", error)
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
        user_set = UserSet.query.join(UserSet.template_set).filter(
            UserSet.id == set_id).first()
        if not user_set:
            return jsonify({'error': 'Set not found in the database'}), 404

        label_data = {
            "BOX_LONG_TITLE": f"Brick SET - {user_set.template_set.set_number} - {user_set.template_set.name.replace('&', 'and')}",
            "BOX_SHORT_TITLE": user_set.template_set.set_number,
            "IMAGE_CONTEXT": user_set.template_set.set_img_url,
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

        return send_file(output_file, as_attachment=True)
    except Exception as error:
        current_app.logger.error("Error generating label: %s", error)
        return jsonify({'error': 'Failed to generate label'}), 500
