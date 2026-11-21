"""Browser entrypoints for physical storage and confirmed movements."""

from __future__ import annotations

import hmac
import secrets
from pathlib import Path

from config import Config
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
)
from models import db
from services import (
    label_queue_service,
    storage_move_service,
    storage_service,
    storage_suggestion_service,
)
from services.label_service import (
    LABEL_FORMATS,
    create_avery_3474_pdf,
    create_box_label_jpg,
    create_label_sheet_pdf,
)
from services.part_history_service import part_history
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, HTTPException, NotFound

warehouse_bp = Blueprint("warehouse", __name__, url_prefix="/warehouse")


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("Ein JSON-Objekt wird benötigt.")
    return data


def _color():
    value = request.args.get("color_id")
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as error:
        raise BadRequest("Die Farbe muss eine ganze Zahl sein.") from error


@warehouse_bp.before_request
def protect_storage_writes():
    """Require a session-bound token for browser mutations, including JSON."""
    if not current_app.config.get("WAREHOUSE_ENABLED", True):
        raise NotFound("Lageransicht ist deaktiviert.")
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    if not current_app.config.get("WTF_CSRF_ENABLED", True):
        return None
    expected = session.get("warehouse_csrf")
    supplied = request.headers.get("X-CSRF-Token", "")
    if not expected or not hmac.compare_digest(expected, supplied):
        return jsonify({"error": "Sitzung abgelaufen. Seite neu laden."}), 403
    return None


@warehouse_bp.errorhandler(HTTPException)
def warehouse_http_error(error):
    db.session.rollback()
    return jsonify({"error": error.description}), error.code


@warehouse_bp.errorhandler(SQLAlchemyError)
def warehouse_database_error(error):
    db.session.rollback()
    current_app.logger.error(
        "Warehouse database operation failed: %s", type(error).__name__
    )
    return jsonify({"error": "Lageränderung konnte nicht gespeichert werden."}), 409


@warehouse_bp.get("")
@warehouse_bp.get("/")
@warehouse_bp.get("/intake", defaults={"page": "intake"})
@warehouse_bp.get("/reorganize", defaults={"page": "reorganize"})
@warehouse_bp.get("/box-types", defaults={"page": "box-types"})
@warehouse_bp.get("/locations", defaults={"page": "locations"})
@warehouse_bp.get("/capture", defaults={"page": "capture"})
@warehouse_bp.get("/settings-page", defaults={"page": "settings"})
def warehouse_page(page="overview"):
    token = session.get("warehouse_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["warehouse_csrf"] = token
    static_folder = current_app.static_folder
    version = (
        max(
            (Path(static_folder) / "js" / "warehouse.js").stat().st_mtime_ns,
            (Path(static_folder) / "css" / "warehouse.css").stat().st_mtime_ns,
        )
        if static_folder
        else 0
    )
    return render_template(
        "warehouse.html",
        warehouse_csrf=token,
        warehouse_asset_version=version,
        warehouse_page=page,
    )


@warehouse_bp.get("/data")
def warehouse_data():
    focused = request.args.get("view") == "focused"
    shelf_id = request.args.get("shelf_id", type=int)
    return jsonify(
        storage_service.overview(
            focused=focused,
            shelf_id=shelf_id,
            all_shelves=request.args.get("all") == "1",
        )
    )


@warehouse_bp.post("/setup")
def setup_types():
    return jsonify(storage_service.seed_container_types()), 201


@warehouse_bp.post("/locations")
def create_location():
    return jsonify(storage_service.create_location(_payload())), 201


@warehouse_bp.patch("/locations/<int:location_id>")
def update_location(location_id):
    return jsonify(storage_service.update_location(location_id, _payload()))


@warehouse_bp.get("/locations/<int:location_id>")
def location_space(location_id):
    return jsonify(storage_service.space_report(location_id))


@warehouse_bp.post("/types")
def create_type():
    return jsonify(storage_service.create_type(_payload())), 201


@warehouse_bp.patch("/types/<int:type_id>")
def update_type(type_id):
    return jsonify(storage_service.update_type(type_id, _payload()))


@warehouse_bp.post("/units")
def create_unit():
    return jsonify(storage_service.create_unit(_payload())), 201


@warehouse_bp.get("/units/<int:unit_id>")
def unit_details(unit_id):
    return jsonify(storage_service.unit_details(unit_id))


@warehouse_bp.patch("/units/<int:unit_id>")
def update_unit(unit_id):
    return jsonify(storage_service.update_unit(unit_id, _payload()))


@warehouse_bp.post("/units/<int:unit_id>/placement")
def capture_placement(unit_id):
    return jsonify(
        storage_service.place_unit(unit_id, _payload(), initial_only=True)
    ), 201


@warehouse_bp.post("/units/<int:unit_id>/preview")
def preview_placement(unit_id):
    return jsonify(storage_service.preview_placement(unit_id, _payload()))


@warehouse_bp.post("/units/<int:unit_id>/partitions")
def partition_drawer(unit_id):
    return jsonify(storage_service.partition_drawer(unit_id, _payload()))


@warehouse_bp.post("/contents")
def create_content():
    return jsonify(storage_service.save_content(_payload())), 201


@warehouse_bp.patch("/contents/<int:storage_id>")
def update_content(storage_id):
    return jsonify(storage_service.update_content(storage_id, _payload()))


@warehouse_bp.post("/stack-rules")
def save_stack_rule():
    return jsonify(storage_service.save_stack_rule(_payload())), 201


@warehouse_bp.get("/parts/<part_num>/locations")
def part_locations(part_num):
    return jsonify({"items": storage_service.list_part_locations(part_num, _color())})


@warehouse_bp.get("/parts/<part_num>/history")
def history(part_num):
    return jsonify(part_history(part_num, _color()))


@warehouse_bp.get("/parts/<part_num>/suggestion")
def intake_suggestion(part_num):
    return jsonify(storage_suggestion_service.intake_suggestion(part_num, _color()))


@warehouse_bp.get("/locations/<int:location_id>/suggestions")
def archive_suggestions(location_id):
    return jsonify(storage_suggestion_service.archive_suggestions(location_id))


@warehouse_bp.get("/settings")
def settings():
    return jsonify(storage_suggestion_service.get_settings())


@warehouse_bp.post("/settings")
def save_settings():
    return jsonify(storage_suggestion_service.save_settings(_payload()))


@warehouse_bp.post("/category-rules")
def save_category_rule():
    return jsonify(storage_suggestion_service.save_category_rule(_payload())), 201


@warehouse_bp.post("/preferences")
def save_preference():
    return jsonify(storage_suggestion_service.save_preference(_payload())), 201


@warehouse_bp.post("/planned-sets")
def save_planned_set():
    return jsonify(storage_suggestion_service.save_planned_set(_payload())), 201


@warehouse_bp.patch("/planned-sets/<int:plan_id>")
def update_planned_set(plan_id):
    return jsonify(storage_suggestion_service.update_planned_set(plan_id, _payload()))


@warehouse_bp.get("/moves")
def moves():
    return jsonify({"items": storage_move_service.list_moves()})


@warehouse_bp.post("/moves")
def create_move():
    return jsonify(storage_move_service.create_move(_payload())), 201


@warehouse_bp.post("/moves/<int:move_id>/plan")
def plan_move(move_id):
    return jsonify(storage_move_service.plan_move(move_id))


@warehouse_bp.post("/moves/<int:move_id>/confirm")
def confirm_move(move_id):
    return jsonify(storage_move_service.confirm_move(move_id, _payload()))


@warehouse_bp.post("/moves/<int:move_id>/cancel")
def cancel_move(move_id):
    return jsonify(storage_move_service.cancel_move(move_id))


@warehouse_bp.get("/units/<int:unit_id>/label")
def unit_label(unit_id):
    info = storage_service.unit_label_info(unit_id)
    try:
        generated = Path(create_box_label_jpg(info))
        return send_from_directory(
            Config.UPLOAD_FOLDER,
            generated.name,
            as_attachment=True,
            download_name=f"brick_unit_{unit_id}_label.jpg",
            mimetype="image/jpeg",
        )
    except OSError:
        current_app.logger.exception("Physical unit label generation failed")
        return jsonify({"error": "Etikett konnte nicht erzeugt werden."}), 500


@warehouse_bp.post("/units/<int:unit_id>/printed")
def unit_label_printed(unit_id):
    return jsonify(
        storage_service.update_unit(unit_id, {**_payload(), "label_printed": True})
    )


@warehouse_bp.get("/label-marks")
def label_marks():
    return jsonify({"marks": label_queue_service.marks()})


@warehouse_bp.post("/label-marks")
def set_label_mark():
    return jsonify(label_queue_service.set_mark(_payload()))


@warehouse_bp.post("/label-marks/sheet")
def marked_label_sheet():
    data = _payload()
    label_format = data.get("label_format", "avery_3474")
    if label_format not in LABEL_FORMATS:
        raise BadRequest("Unbekanntes Etikettenformat.")
    start = storage_service.integer(data.get("start_position", 1), "start_position")
    capacity = (
        LABEL_FORMATS[label_format]["columns"] * LABEL_FORMATS[label_format]["rows"]
    )
    if start is None or start > capacity:
        raise BadRequest(f"Startposition höchstens {capacity}.")
    offsets = []
    for name in ("horizontal_offset_mm", "vertical_offset_mm"):
        value = data.get(name, 0)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not -10 <= value <= 10
        ):
            raise BadRequest("Druckversatz zwischen -10 und 10 mm erforderlich.")
        offsets.append(value)
    infos = label_queue_service.label_infos(data)
    return send_file(
        (
            create_avery_3474_pdf(infos, start, *offsets)
            if label_format == "avery_3474"
            else create_label_sheet_pdf(infos, label_format, start, *offsets)
        ),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="marked_brick_labels.pdf",
    )


@warehouse_bp.post("/label-marks/printed")
def marked_labels_printed():
    return jsonify(label_queue_service.confirm(_payload()))


@warehouse_bp.post("/label-marks/remove")
def remove_label_mark():
    return jsonify(label_queue_service.remove(_payload()))


@warehouse_bp.get("/contents")
def content_options():
    return jsonify({"items": storage_service.content_options()})


@warehouse_bp.get("/contents/<int:storage_id>/group")
def legacy_group_contents(storage_id):
    return jsonify(storage_service.legacy_group_contents(storage_id))
