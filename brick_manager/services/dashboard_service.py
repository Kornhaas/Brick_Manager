"""Fast collection aggregates and durable dashboard trend snapshots."""

# SQLAlchemy exposes SQL functions dynamically through ``func``.
# pylint: disable=not-callable

from datetime import date

from models import (
    NON_LOOSE_PART_STATUSES,
    CollectionSnapshot,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from sqlalchemy import case, func, or_

STATUS_LABELS = {
    "unknown": "Unknown",
    "konvolut": "Konvolut",
    "assembled": "Assembled",
    "sealed": "Sealed",
    "missingparts": "Missing parts",
    "complete": "Complete",
    "completenospareparts": "Complete, no spares",
}


def _quantity_totals(model, *, exclude_non_loose=False):
    query = db.session.query(
        func.coalesce(func.sum(model.have_quantity), 0),
        func.coalesce(func.sum(model.quantity), 0),
        func.coalesce(
            func.sum(
                case(
                    (
                        model.quantity > model.have_quantity,
                        model.quantity - model.have_quantity,
                    ),
                    else_=0,
                )
            ),
            0,
        ),
    ).join(User_Set, model.user_set_id == User_Set.id)
    if exclude_non_loose:
        query = query.filter(~User_Set.status.in_(NON_LOOSE_PART_STATUSES))
    owned, required, missing = query.one()
    return int(owned), int(required), int(missing)


def build_dashboard_data():
    """Return chart-ready collection metrics without loading inventory rows."""
    regular_owned, regular_required, regular_missing = _quantity_totals(User_Parts)
    minifig_owned, minifig_required, minifig_missing = _quantity_totals(
        UserMinifigurePart
    )
    loose_owned, _loose_required, loose_missing = _quantity_totals(
        User_Parts, exclude_non_loose=True
    )
    _minifig_loose_owned, _minifig_loose_required, loose_minifig_missing = (
        _quantity_totals(UserMinifigurePart, exclude_non_loose=True)
    )

    missing_set_condition = or_(
        User_Set.parts_in_set.any(User_Parts.have_quantity < User_Parts.quantity),
        User_Set.user_minifigure_parts.any(
            UserMinifigurePart.have_quantity < UserMinifigurePart.quantity
        ),
    )
    total_sets = User_Set.query.count()
    incomplete_sets = User_Set.query.filter(missing_set_condition).count()
    complete_sets = max(total_sets - incomplete_sets, 0)

    missing_spares = int(
        db.session.query(
            func.coalesce(func.sum(User_Parts.quantity - User_Parts.have_quantity), 0)
        )
        .join(User_Set)
        .filter(
            User_Parts.is_spare.is_(True),
            User_Parts.quantity > User_Parts.have_quantity,
            ~User_Set.status.in_(NON_LOOSE_PART_STATUSES),
        )
        .scalar()
    )
    konvolut_owned, _konvolut_required, konvolut_missing = _quantity_totals_for_status(
        User_Parts, "konvolut"
    )
    _konvolut_minifig_owned, _required, konvolut_minifig_missing = (
        _quantity_totals_for_status(UserMinifigurePart, "konvolut")
    )

    status_rows = (
        db.session.query(User_Set.status, func.count(User_Set.id))
        .group_by(User_Set.status)
        .order_by(func.count(User_Set.id).desc())
        .all()
    )
    theme_rows = (
        db.session.query(RebrickableThemes.name, func.count(User_Set.id))
        .join(RebrickableSets, RebrickableSets.theme_id == RebrickableThemes.id)
        .join(User_Set, User_Set.set_num == RebrickableSets.set_num)
        .group_by(RebrickableThemes.id, RebrickableThemes.name)
        .order_by(func.count(User_Set.id).desc())
        .limit(8)
        .all()
    )
    largest_sets = (
        db.session.query(User_Set.id, RebrickableSets)
        .join(RebrickableSets, User_Set.set_num == RebrickableSets.set_num)
        .order_by(RebrickableSets.num_parts.desc())
        .limit(5)
        .all()
    )

    return {
        "total_sets": total_sets,
        "complete_sets": complete_sets,
        "incomplete_sets": incomplete_sets,
        "owned_parts": regular_owned + minifig_owned,
        "required_parts": regular_required + minifig_required,
        "missing_parts": regular_missing + minifig_missing,
        "loose_owned_parts": loose_owned,
        "loose_missing_parts": loose_missing,
        "missing_minifigure_parts": loose_minifig_missing,
        "missing_spare_parts": missing_spares,
        "konvolut_parts": konvolut_owned,
        "missing_konvolut_parts": konvolut_missing,
        "missing_konvolut_minifigure_parts": konvolut_minifig_missing,
        "status_distribution": [
            {"label": STATUS_LABELS.get(status, status.title()), "value": count}
            for status, count in status_rows
        ],
        "theme_distribution": [
            {"label": name, "value": count} for name, count in theme_rows
        ],
        "largest_sets": [
            {
                "box_id": box_id,
                "set_num": catalog_set.set_num,
                "name": catalog_set.name,
                "parts": catalog_set.num_parts,
                "image": catalog_set.img_url,
            }
            for box_id, catalog_set in largest_sets
        ],
    }


def _quantity_totals_for_status(model, status):
    owned, required, missing = (
        db.session.query(
            func.coalesce(func.sum(model.have_quantity), 0),
            func.coalesce(func.sum(model.quantity), 0),
            func.coalesce(
                func.sum(
                    case(
                        (
                            model.quantity > model.have_quantity,
                            model.quantity - model.have_quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(User_Set, model.user_set_id == User_Set.id)
        .filter(User_Set.status == status)
        .one()
    )
    return int(owned), int(required), int(missing)


def record_daily_snapshot(metrics, captured_on=None):
    """Create or refresh today's aggregate; repeated calls are idempotent."""
    snapshot_date = captured_on or date.today()
    snapshot = CollectionSnapshot.query.filter_by(captured_on=snapshot_date).first()
    if snapshot is None:
        snapshot = CollectionSnapshot()
        snapshot.captured_on = snapshot_date
        db.session.add(snapshot)

    for field in (
        "total_sets",
        "owned_parts",
        "required_parts",
        "missing_parts",
        "complete_sets",
        "incomplete_sets",
    ):
        setattr(snapshot, field, metrics[field])
    db.session.commit()
    return snapshot


def load_snapshot_history(limit=90):
    """Return oldest-to-newest snapshots for the trend chart."""
    snapshots = (
        CollectionSnapshot.query.order_by(CollectionSnapshot.captured_on.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date": snapshot.captured_on.isoformat(),
            "sets": snapshot.total_sets,
            "owned": snapshot.owned_parts,
            "missing": snapshot.missing_parts,
        }
        for snapshot in reversed(snapshots)
    ]
