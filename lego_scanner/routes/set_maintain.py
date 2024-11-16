from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from models import db, UserSet, Part, Minifigure, UserMinifigurePart
from services.lookup_service import load_master_lookup
from sqlalchemy.orm import joinedload

set_maintain_bp = Blueprint('set_maintain', __name__)

@set_maintain_bp.route('/set_maintain', methods=['GET'])
def set_maintain():
    """
    Displays the list of user sets.
    """
    user_sets = UserSet.query.options(
        joinedload(UserSet.template_set),
        joinedload(UserSet.parts),
        joinedload(UserSet.minifigures)
    ).all()
    return render_template('set_maintain.html', user_sets=user_sets)

@set_maintain_bp.route('/set_maintain/<int:user_set_id>', methods=['GET'])
def get_user_set_details(user_set_id):
    """
    Returns the details of a specific UserSet, including its parts, minifigures, and user minifigure parts.
    """
    master_lookup = load_master_lookup()
    user_set = UserSet.query.options(
        joinedload(UserSet.parts),
        joinedload(UserSet.minifigures)
    ).get_or_404(user_set_id)

    # Helper function for location and status
    def enrich_item(item, master_lookup):
        part_data = master_lookup.get(item.part_num, {})
        return {
            'id': item.id,
            'part_num': item.part_num,
            'name': item.name,
            'quantity': item.quantity,
            'have_quantity': item.have_quantity,
            'part_img_url': item.part_img_url,
            'location': f"Location: {part_data.get('location', 'Unknown')}, "
                        f"Level: {part_data.get('level', 'Unknown')}, "
                        f"Box: {part_data.get('box', 'Unknown')}" if part_data else "Not Specified",
            'status': "Available" if part_data else "Not Available"
        }

    # Add parts details
    parts = [enrich_item(part, master_lookup) for part in user_set.parts]

    # Add minifigure details
    minifigs = [
        {
            'id': minifig.id,
            'fig_num': minifig.fig_num,
            'name': minifig.name,
            'quantity': minifig.quantity,
            'have_quantity': minifig.have_quantity,
            'img_url': minifig.img_url,
            'location': f"Location: {master_lookup.get(minifig.fig_num, {}).get('location', 'Unknown')}, "
                        f"Level: {master_lookup.get(minifig.fig_num, {}).get('level', 'Unknown')}, "
                        f"Box: {master_lookup.get(minifig.fig_num, {}).get('box', 'Unknown')}" if master_lookup.get(minifig.fig_num) else "Not Specified",
            'status': "Available" if master_lookup.get(minifig.fig_num) else "Not Available"
        }
        for minifig in user_set.minifigures
    ]

    # Add user minifigure parts details
    user_minifigure_parts = UserMinifigurePart.query.filter_by(user_set_id=user_set_id).all()
    minifigure_parts = [enrich_item(part, master_lookup) for part in user_minifigure_parts]

    return jsonify({
        'set_img_url': user_set.template_set.set_img_url,
        'parts': parts,
        'minifigs': minifigs,
        'minifigure_parts': minifigure_parts,
        'status': user_set.status
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
        # Update parts
        for part in user_set.parts:
            have_quantity = request.form.get(f'part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        # Update minifigures
        for minifig in user_set.minifigures:
            have_quantity = request.form.get(f'minifig_id_{minifig.id}')
            if have_quantity is not None:
                minifig.have_quantity = max(0, min(minifig.quantity, int(have_quantity)))
                db.session.add(minifig)

        # Update user minifigure parts
        user_minifigure_parts = UserMinifigurePart.query.filter_by(user_set_id=user_set_id).all()
        for part in user_minifigure_parts:
            have_quantity = request.form.get(f'minifig_part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        # Update status
        if status:
            user_set.status = status
            db.session.add(user_set)

        db.session.commit()
        flash(f"User Set for {user_set.template_set.set_number} updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating UserSet: {e}")
        flash("Failed to update UserSet.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))

@set_maintain_bp.route('/set_maintain/delete/<int:user_set_id>', methods=['POST'])
def delete_user_set(user_set_id):
    """
    Deletes a specific UserSet from the database.
    """
    user_set = UserSet.query.get_or_404(user_set_id)

    try:
        db.session.delete(user_set)
        db.session.commit()
        flash(f"User Set for {user_set.template_set.set_number} deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting UserSet: {e}")
        flash("Failed to delete User Set.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))