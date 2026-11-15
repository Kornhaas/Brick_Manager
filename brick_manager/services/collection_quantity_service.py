"""Typed collection quantities; physical warehouse stock is a separate domain."""

import re

from models import User_Parts, UserMinifigurePart
from werkzeug.exceptions import BadRequest, Conflict, NotFound

PART_MODELS = {"regular": User_Parts, "minifig": UserMinifigurePart}


def parse_integer(value, *, positive_id=False):
    """Preserve legacy integer strings, reject booleans/floats and invalid IDs."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("An integer is required")
    if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value.strip()) is None:
        raise ValueError("An integer is required")
    result = int(value)
    if positive_id and not 1 <= result <= 2**63 - 1:
        raise ValueError("Invalid part identifier")
    return result


def apply_batch(changes):
    """Resolve the complete batch before assignment; caller owns commit/rollback."""
    identifiers = {part_id for part_id, _quantity, _kind in changes}
    available = {
        kind: {
            row.id: row for row in model.query.filter(model.id.in_(identifiers)).all()
        }
        for kind, model in PART_MODELS.items()
    }
    resolved = []
    seen = set()
    for identifier, quantity, kind in changes:
        if kind is None:
            matches = [
                candidate
                for candidate in PART_MODELS
                if identifier in available[candidate]
            ]
            if len(matches) > 1:
                raise Conflict(
                    "Part ID is ambiguous; specify part_type as regular or minifig."
                )
            kind = matches[0] if matches else "regular"
        row = available[kind].get(identifier)
        if row is None:
            raise NotFound("Part not found; no quantities were changed.")
        key = (kind, identifier)
        if key in seen:
            raise BadRequest("Duplicate quantity target; no quantities were changed.")
        seen.add(key)
        resolved.append((kind, row, max(0, min(row.quantity, quantity))))
    updates = []
    for kind, row, quantity in resolved:
        row.have_quantity = quantity
        updates.append(
            {"part_id": row.id, "part_type": kind, "have_quantity": quantity}
        )
    return updates
