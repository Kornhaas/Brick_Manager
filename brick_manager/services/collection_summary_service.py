"""Page-scoped scalar collection summaries without materializing inventories."""

from models import User_Parts, UserMinifigurePart, db
from sqlalchemy import func


def set_quantity_totals(set_ids):
    """Keep physical copies separate; include regular, spare and figure rows."""
    identifiers = list(set_ids)
    if not identifiers:
        return {}
    totals = {identifier: {"required": 0, "owned": 0} for identifier in identifiers}
    for model in (User_Parts, UserMinifigurePart):
        rows = (
            db.session.query(
                model.user_set_id,
                func.coalesce(func.sum(model.quantity), 0),
                func.coalesce(func.sum(model.have_quantity), 0),
            )
            .filter(model.user_set_id.in_(identifiers))
            .group_by(model.user_set_id)
            .all()
        )
        for identifier, required, owned in rows:
            totals[identifier]["required"] += int(required)
            totals[identifier]["owned"] += int(owned)
    return totals
