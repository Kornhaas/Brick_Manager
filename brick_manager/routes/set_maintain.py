# pyright: reportArgumentType=false, reportCallIssue=false
"""

This module manages the maintenance of user sets, including adding, updating, deleting,

and generating labels for sets and their parts.
"""

# pylint: disable=C0301,W0718

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from models import (
    USER_SET_STATUSES,
    PartStorage,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from services.collection_quantity_service import parse_integer
from services.collection_summary_service import set_quantity_totals
from services.set_label_service import SET_LABEL_SIZES, create_set_label_pdf
from services.set_maintenance_service import (
    InvalidSetField,
    apply_set_edits,
    completeness_percentage,
    inventory_details,
)
from services.set_navigation_service import (
    DEFAULT_FILTERS,
    LIST_ENDPOINT,
    details_navigation,
    list_parameters,
    order_sets,
    positive_number,
)
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

set_maintain_bp = Blueprint("set_maintain", __name__)


@set_maintain_bp.route("/update_part_location", methods=["POST"])
def update_part_location():
    """
    Updates or creates the location for a specific part.
    Expects JSON: {part_num, location, level, box}
    """
    try:
        data = request.get_json()
        part_num = data.get("part_num")
        location = data.get("location", "").strip()
        level = data.get("level", "").strip()
        box = data.get("box", "").strip()

        if not part_num:
            return jsonify({"success": False, "error": "Part number is required"}), 400

        # Find or create part storage entry
        part_storage = PartStorage.query.filter_by(part_num=part_num).first()

        if part_storage:
            # Update existing entry
            part_storage.location = location if location else None
            part_storage.level = level if level else None
            part_storage.box = box if box else None
        else:
            # Create new entry
            part_storage = PartStorage(
                part_num=part_num,
                location=location if location else None,
                level=level if level else None,
                box=box if box else None,
            )
            db.session.add(part_storage)

        db.session.commit()

        # Format the location string for display
        location_str = (
            f"Location: {location or 'Unknown'}, "
            f"Level: {level or 'Unknown'}, "
            f"Box: {box or 'Unknown'}"
        )

        return jsonify(
            {
                "success": True,
                "location": location_str,
                "message": "Location updated successfully",
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating part location: {e}")
        return (
            jsonify({"success": False, "error": "Unable to update part location."}),
            500,
        )


@set_maintain_bp.route("/set_maintain", methods=["GET"])
def set_maintain():
    """

    Displays the list of user sets with enhanced information including theme data.
    """
    context = list_parameters(request.args)
    filters = {**DEFAULT_FILTERS, **context}
    search, box_id, status = filters["q"], filters["box_id"], filters["status"]
    theme_name, label, completion = (
        filters["theme"],
        filters["label"],
        filters["completion"],
    )
    page, per_page = filters["page"], filters["per_page"]

    query = User_Set.query.join(User_Set.template_set).options(
        joinedload(User_Set.template_set)
    )

    if search:
        search_pattern = f"%{search}%"
        search_conditions = [
            RebrickableSets.set_num.ilike(search_pattern),
            RebrickableSets.name.ilike(search_pattern),
            RebrickableSets.theme.has(RebrickableThemes.name.ilike(search_pattern)),
        ]
        search_id = positive_number(search) if search.isdecimal() else None
        if search_id is not None:
            search_conditions.append(User_Set.id == search_id)
        query = query.filter(or_(*search_conditions))
    if box_id is not None:
        query = query.filter(User_Set.id == box_id)
    if status in USER_SET_STATUSES:
        query = query.filter(User_Set.status == status)
    if theme_name:
        query = query.filter(
            RebrickableSets.theme.has(RebrickableThemes.name == theme_name)
        )
    if label == "printed":
        query = query.filter(User_Set.label_printed.is_(True))
    elif label == "not-printed":
        query = query.filter(User_Set.label_printed.is_(False))

    missing_parts = or_(
        User_Set.parts_in_set.any(User_Parts.have_quantity < User_Parts.quantity),
        User_Set.user_minifigure_parts.any(
            UserMinifigurePart.have_quantity < UserMinifigurePart.quantity
        ),
    )
    has_parts = or_(User_Set.parts_in_set.any(), User_Set.user_minifigure_parts.any())
    has_owned_parts = or_(
        User_Set.parts_in_set.any(User_Parts.have_quantity > 0),
        User_Set.user_minifigure_parts.any(UserMinifigurePart.have_quantity > 0),
    )
    if completion == "incomplete":
        query = query.filter(missing_parts)
    elif completion == "complete":
        query = query.filter(has_parts, ~missing_parts)
    elif completion == "no-parts":
        query = query.filter(~has_owned_parts)

    ordered = order_sets(query, filters["sort"], filters["direction"], filters["group"])
    pagination = ordered.paginate(page=page, per_page=per_page, error_out=False)
    last_page = max(1, pagination.pages)
    return_box = positive_number(request.args.get("returned_box"))
    if page > last_page:
        context["page"] = last_page
        if return_box:
            context.update(returned_box=return_box, _anchor=f"set-box-{return_box}")
        return redirect(url_for(LIST_ENDPOINT, **context))
    user_sets = pagination.items
    return_notice = None
    if return_box and all(user_set.id != return_box for user_set in user_sets):
        if query.filter(User_Set.id == return_box).first() is None:
            return_notice = f"Box {return_box} no longer matches these results."
        else:
            return_notice = f"Box {return_box} is now on another results page."

    theme_summary = (
        db.session.query(
            RebrickableThemes.name,
            db.func.count(User_Set.id).label("set_count"),
        )
        .join(RebrickableSets, RebrickableSets.theme_id == RebrickableThemes.id)
        .join(User_Set, User_Set.set_num == RebrickableSets.set_num)
        .group_by(RebrickableThemes.name)
        .order_by(db.func.count(User_Set.id).desc(), RebrickableThemes.name.asc())
        .limit(12)
        .all()
    )
    status_summary = dict(
        db.session.query(User_Set.status, db.func.count(User_Set.id))
        .group_by(User_Set.status)
        .all()
    )

    totals = set_quantity_totals(user_set.id for user_set in user_sets)
    sets_with_completeness = []
    for user_set in user_sets:
        total_quantity = totals[user_set.id]["required"]
        total_have_quantity = totals[user_set.id]["owned"]

        # Get theme information
        row_theme_name = "Unknown"
        if user_set.template_set and user_set.template_set.theme:
            row_theme_name = user_set.template_set.theme.name

        # Get set name
        set_name = "Unknown Set"
        if user_set.template_set:
            set_name = user_set.template_set.name

        sets_with_completeness.append(
            {
                "user_set": user_set,
                "completeness_percentage": completeness_percentage(
                    total_have_quantity, total_quantity
                ),
                "theme_name": row_theme_name,
                "set_name": set_name,
                "set_num": (
                    user_set.template_set.set_num
                    if user_set.template_set
                    else "Unknown"
                ),
                "total_parts": total_quantity,
                "parts_owned": total_have_quantity,
            }
        )

    return render_template(
        "set_maintain.html",
        sets_with_completeness=sets_with_completeness,
        pagination=pagination,
        total_sets=User_Set.query.count(),
        missing_sets=User_Set.query.filter(missing_parts).count(),
        theme_summary=theme_summary,
        status_summary=status_summary,
        themes=[
            name
            for (name,) in db.session.query(RebrickableThemes.name)
            .distinct()
            .order_by(RebrickableThemes.name)
            .all()
        ],
        filters=filters,
        list_context_url=url_for(LIST_ENDPOINT, **context),
        return_notice=return_notice,
        return_box_id=return_box,
    )


@set_maintain_bp.get("/set_maintain/<int:user_set_id>")
def get_user_set_details(user_set_id):
    """Keep the existing JSON representation available to inventory consumers."""
    return jsonify(inventory_details(User_Set.query.get_or_404(user_set_id)))


def _unique_fields(pairs):
    fields = {}
    for field, value in pairs:
        if field in fields:
            raise InvalidSetField(field, "Jedes Feld darf nur einmal vorkommen.")
        fields[field] = value
    return fields


def _json_edits():
    try:
        fields = current_app.json.loads(
            request.get_data(), object_pairs_hook=_unique_fields
        )
    except InvalidSetField:
        raise
    except (ValueError, RecursionError) as error:
        raise InvalidSetField(
            None, "Setänderungen müssen ein JSON-Objekt sein."
        ) from error
    if not isinstance(fields, dict):
        raise InvalidSetField(None, "Setänderungen müssen ein JSON-Objekt sein.")
    return fields


@set_maintain_bp.route(
    "/set_maintain/<int:user_set_id>/details", methods=["GET", "POST"]
)
def set_details(user_set_id):
    """Display or explicitly save a single physical copy and retain the list origin."""
    if positive_number(user_set_id) is None:
        abort(404)
    user_set = User_Set.query.get_or_404(user_set_id)
    list_url, detail_url = details_navigation(
        user_set_id, request.args.get("return_to")
    )
    drafts, errors, message, code = {}, {}, None, 200
    if request.method == "POST":
        try:
            if request.is_json:
                drafts = _json_edits()
            else:
                drafts = request.form.to_dict()
                for field, values in request.form.lists():
                    if len(values) != 1:
                        raise InvalidSetField(
                            field, "Jedes Feld darf nur einmal vorkommen."
                        )
            confirmed = apply_set_edits(user_set, drafts)
            if request.is_json:
                totals = set_quantity_totals([user_set_id])[user_set_id]
                progress = completeness_percentage(totals["owned"], totals["required"])
            db.session.commit()
        except InvalidSetField as error:
            db.session.rollback()
            message, code = str(error), 400
            if error.field:
                errors[error.field] = message
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.error(
                "Could not save Set Maintenance copy %s", user_set_id
            )
            message, code = "Speichern fehlgeschlagen. Bitte erneut versuchen.", 409
        else:
            if request.is_json:
                return jsonify(
                    success=True,
                    values=confirmed,
                    status=confirmed["status"],
                    completeness_percentage=progress,
                )
            flash("Änderungen gespeichert.", "success")
            return redirect(detail_url, code=303)
        if request.is_json:
            return jsonify(success=False, error=message, field_errors=errors), code

    return render_template(
        "set_detail.html",
        user_set=user_set,
        detail_data={
            **inventory_details(
                user_set, include_unassigned=True, include_visuals=True
            ),
            "user_set_id": user_set.id,
            "set_num": user_set.set_num,
        },
        list_url=list_url,
        detail_url=detail_url,
        draft_values=drafts,
        save_error=message,
        field_errors=errors,
    ), code


@set_maintain_bp.route("/set_maintain/update_part_quantity", methods=["POST"])
def update_part_quantity():
    """Update the have_quantity for a specific part in real-time"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "message": "Invalid input value"}), 400
        if isinstance(data.get("part_id"), bool) or isinstance(
            data.get("have_quantity"), bool
        ):
            return jsonify({"success": False, "message": "Invalid input value"}), 400
        part_id = parse_integer(data.get("part_id"), positive_id=True)
        part_type = data.get("part_type", "regular")  # 'regular' or 'minifig'
        if not isinstance(part_type, str) or part_type not in {"regular", "minifig"}:
            return jsonify({"success": False, "message": "Invalid input value"}), 400
        new_quantity = parse_integer(data.get("have_quantity"))

        current_app.logger.info(
            f"Auto-updating {part_type} quantity: part_id={part_id}, quantity={new_quantity}"
        )

        if part_type == "minifig":
            # Update minifigure part
            part = UserMinifigurePart.query.get(part_id)
            if not part:
                current_app.logger.error(f"Minifigure part not found: id={part_id}")
                return (
                    jsonify({"success": False, "message": "Minifigure part not found"}),
                    404,
                )
        else:
            # Update regular part
            part = User_Parts.query.get(part_id)
            if not part:
                current_app.logger.error(f"Regular part not found: id={part_id}")
                return jsonify({"success": False, "message": "Part not found"}), 404

        # Clamp the value between 0 and the required quantity
        part.have_quantity = max(0, min(part.quantity, new_quantity))
        db.session.commit()

        current_app.logger.info(
            f"Successfully updated {part_type} quantity for part_id={part_id}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Quantity updated successfully",
                "have_quantity": part.have_quantity,
                "total_quantity": part.quantity,
            }
        )

    except (TypeError, ValueError) as e:
        current_app.logger.error(f"Invalid value in request: {e}")
        return jsonify({"success": False, "message": "Invalid input value"}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating part quantity: {e}")
        return jsonify({"success": False, "message": "Unable to update quantity."}), 500


@set_maintain_bp.route("/set_maintain/update", methods=["POST"])
def update_user_set():
    """

    Updates the parts, minifigures, and user minifigure parts owned for a specific User_Set.
    """
    user_set_id = request.form.get("user_set_id")

    user_set = User_Set.query.get_or_404(user_set_id)

    try:
        apply_set_edits(user_set, request.form, legacy=True)

        db.session.commit()
        flash(
            f"User Set for {user_set.template_set.set_num} updated successfully.",
            "success",
        )
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error updating User_Set: %s", error)
        flash("Failed to update User_Set.", "danger")

    return redirect(url_for("set_maintain.set_maintain"))


@set_maintain_bp.route("/set_maintain/update_label_status", methods=["POST"])
def update_set_label_status():
    """Updates the label_printed status for a user set."""
    try:
        current_app.logger.info("update_set_label_status endpoint called")
        data = request.get_json(silent=True)
        current_app.logger.info(f"Received data: {data}")

        if not data:
            current_app.logger.error("No data received")
            return jsonify({"error": "Invalid input data format."}), 400

        user_set_id = data.get("user_set_id")
        label_printed = data.get("label_printed")
        current_app.logger.info(
            f"user_set_id: {user_set_id}, label_printed: {label_printed}"
        )

        if user_set_id is None or not isinstance(label_printed, bool):
            current_app.logger.error("Missing required fields")
            return (
                jsonify(
                    {"error": "user_set_id and boolean label_printed are required."}
                ),
                400,
            )

        user_set = User_Set.query.get(user_set_id)
        if not user_set:
            current_app.logger.error(f"User set {user_set_id} not found")
            return jsonify({"error": "User set not found."}), 404

        current_app.logger.info(
            f"Before update: user_set.label_printed = {user_set.label_printed}"
        )
        user_set.label_printed = bool(label_printed)
        current_app.logger.info(
            f"After update: user_set.label_printed = {user_set.label_printed}"
        )
        db.session.commit()
        current_app.logger.info("Database committed successfully")

        return jsonify({"message": "Label status updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating set label status: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@set_maintain_bp.route("/set_maintain/delete/<int:user_set_id>", methods=["POST"])
def delete_user_set(user_set_id):
    """Deletes a specific User_Set from the database."""
    try:
        user_set = User_Set.query.options(joinedload(User_Set.template_set)).get_or_404(
            user_set_id
        )
        template_set_number = user_set.template_set.set_num
        db.session.delete(user_set)
        db.session.commit()
        flash(f"User Set for {template_set_number} deleted successfully.", "success")
    except Exception as error:
        db.session.rollback()
        current_app.logger.error("Error deleting User_Set: %s", error)
        flash("Failed to delete User Set.", "danger")

    return redirect(url_for("set_maintain.set_maintain"))


@set_maintain_bp.route("/set_maintain/generate_label", methods=["POST"])
def generate_label():
    """

    Generate a print-ready PDF for a set's physical box.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Ein JSON-Objekt mit Set und Boxgröße wird benötigt."), 400
    try:
        set_id = parse_integer(data.get("set_id"), positive_id=True)
    except ValueError:
        return jsonify(error="Eine gültige Box-ID wird benötigt."), 400
    box_size = data.get("box_size")
    if not isinstance(box_size, str) or box_size not in SET_LABEL_SIZES:
        return jsonify(
            error="Unbekannte Boxgröße. Bitte MB-1, MB-4 oder BIG-BOX wählen."
        ), 400
    current_app.logger.info(
        "Generating label for set %s with box size %s", set_id, box_size
    )
    response = None
    try:
        user_set = (
            User_Set.query.join(User_Set.template_set)
            .filter(User_Set.id == set_id)
            .first()
        )
        if not user_set:
            return jsonify({"error": "Set not found in the database"}), 404

        document = create_set_label_pdf(
            box_id=set_id,
            set_number=str(user_set.template_set.set_num),
            set_name=str(user_set.template_set.name or user_set.template_set.set_num),
            image_url=str(user_set.template_set.img_url or ""),
            box_size=box_size,
            output_folder=current_app.config["OUTPUT_FOLDER"],
            cache_folder=current_app.config.get("CACHE_FOLDER"),
        )
        response = send_file(
            document.path, as_attachment=True, mimetype="application/pdf"
        )
        if document.warning:
            response.headers["X-Label-Warning"] = document.warning

        # Automatically mark the label as printed
        user_set.label_printed = True
        db.session.commit()
        current_app.logger.info(
            f"Label automatically marked as printed for set {set_id}"
        )

        return response
    except Exception as error:
        if response is not None:
            response.close()
        db.session.rollback()
        current_app.logger.error(
            "Error generating set label (%s)", type(error).__name__
        )
        return jsonify(
            error="Etikett konnte nicht erstellt werden. Bitte erneut versuchen."
        ), 500
