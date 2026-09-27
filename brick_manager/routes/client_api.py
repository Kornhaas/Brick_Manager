"""Versioned, authenticated JSON API for desktop and trusted LAN clients."""

from __future__ import annotations

import hmac

from flask import Blueprint, current_app, jsonify, request
from models import PartStorage, RebrickableParts, User_Parts, User_Set, db
from sqlalchemy.orm import joinedload

client_api_bp = Blueprint("client_api", __name__, url_prefix="/api/v1")


@client_api_bp.before_request
def require_client_api_key():
    """Fail closed unless a dedicated client API key is configured."""
    expected = current_app.config.get("BRICK_MANAGER_CLIENT_API_KEY", "")
    if not expected:
        return jsonify({"error": "Client API is not configured"}), 503

    authorization = request.headers.get("Authorization", "")
    scheme, _, supplied = authorization.partition(" ")
    if scheme.lower() != "bearer" or not supplied:
        return jsonify({"error": "Authentication required"}), 401
    if not hmac.compare_digest(supplied, expected):
        return jsonify({"error": "Invalid credentials"}), 401
    return None


@client_api_bp.get("/parts/<part_num>")
def get_part(part_num: str):
    part = (
        RebrickableParts.query.options(joinedload(RebrickableParts.category))
        .filter_by(part_num=part_num)
        .first()
    )
    if part is None:
        return jsonify({"error": "Part not found"}), 404

    return jsonify(
        {
            "part_num": part.part_num,
            "name": part.name,
            "part_cat_id": part.part_cat_id,
            "category_name": part.category.name if part.category else None,
            "part_material": part.part_material,
            "part_img_url": part.part_img_url,
            "part_url": part.part_url,
        }
    )


@client_api_bp.get("/parts/<part_num>/sets")
def get_sets_for_part(part_num: str):
    color_id = _optional_int(request.args.get("color_id"))
    if request.args.get("color_id") and color_id is None:
        return jsonify({"error": "color_id must be an integer"}), 400

    query = User_Parts.query.options(
        joinedload(User_Parts.user_set).joinedload(User_Set.template_set),
        joinedload(User_Parts.rebrickable_color),
    ).filter_by(part_num=part_num)
    if color_id is not None:
        query = query.filter_by(color_id=color_id)

    items = []
    for user_part in query.order_by(User_Parts.user_set_id).all():
        user_set = user_part.user_set
        if user_set is None:
            continue
        set_record = user_set.template_set
        color = user_part.rebrickable_color
        have = user_part.have_quantity or 0
        items.append(
            {
                "part_id": user_part.id,
                "user_set_id": user_set.id,
                "box_id": user_set.id,
                "set_num": user_set.set_num,
                "set_name": set_record.name if set_record else user_set.set_num,
                "set_img_url": set_record.img_url if set_record else None,
                "needed": user_part.quantity,
                "have": have,
                "missing": max(user_part.quantity - have, 0),
                "color_id": user_part.color_id,
                "color_name": color.name if color else None,
                "color_hex": color.rgb if color else None,
            }
        )
    return jsonify({"items": items})


@client_api_bp.get("/parts/<part_num>/storage")
def get_part_storage(part_num: str):
    color_id = _optional_int(request.args.get("color_id"))
    if request.args.get("color_id") and color_id is None:
        return jsonify({"error": "color_id must be an integer"}), 400

    query = PartStorage.query.filter_by(part_num=part_num)
    if color_id is not None:
        query = query.filter_by(color_id=color_id)
    items = [
        {
            "id": item.id,
            "part_num": item.part_num,
            "color_id": item.color_id,
            "location": item.location,
            "level": item.level,
            "box": item.box,
            "notes": item.notes,
            "label_printed": item.label_printed,
        }
        for item in query.order_by(PartStorage.id).all()
    ]
    return jsonify({"items": items})


@client_api_bp.put("/user-parts/<int:user_part_id>/quantity")
def update_user_part_quantity(user_part_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required"}), 400
    quantity = payload.get("have_quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        return jsonify({"error": "have_quantity must be a non-negative integer"}), 400

    user_part = db.session.get(User_Parts, user_part_id)
    if user_part is None:
        return jsonify({"error": "User part not found"}), 404

    user_part.have_quantity = min(quantity, user_part.quantity)
    db.session.commit()
    return jsonify(
        {
            "part_id": user_part.id,
            "have_quantity": user_part.have_quantity,
            "quantity": user_part.quantity,
            "missing": max(user_part.quantity - user_part.have_quantity, 0),
        }
    )


@client_api_bp.put("/parts/<part_num>/storage")
def update_part_storage(part_num: str):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    part = db.session.get(RebrickableParts, part_num)
    if part is None:
        return jsonify({"error": "Part not found"}), 404

    color_id = payload.get("color_id")
    if color_id is not None and (
        isinstance(color_id, bool) or not isinstance(color_id, int)
    ):
        return jsonify({"error": "color_id must be an integer or null"}), 400

    fields = ("location", "level", "box", "notes")
    values: dict[str, str | None] = {}
    for field in fields:
        value = payload.get(field, "")
        if not isinstance(value, str) or len(value) > 200:
            return jsonify(
                {"error": f"{field} must be a string of at most 200 characters"}
            ), 400
        values[field] = value.strip() or None

    query = PartStorage.query.filter_by(part_num=part_num, color_id=color_id)
    storage = query.order_by(PartStorage.id).first()
    if storage is None:
        storage = PartStorage(part_num=part_num, color_id=color_id)
        db.session.add(storage)

    for field, value in values.items():
        setattr(storage, field, value)
    db.session.commit()

    return jsonify(
        {
            "id": storage.id,
            "part_num": storage.part_num,
            "color_id": storage.color_id,
            "location": storage.location,
            "level": storage.level,
            "box": storage.box,
            "notes": storage.notes,
        }
    )


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        return None
