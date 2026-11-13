"""Manual entry should write only the requested storage location."""

from models import PartStorage, RebrickablePartCategories, RebrickableParts, db
from services import part_lookup_service
from sqlalchemy import event


def test_manual_entry_preserves_locations_and_avoids_bulk_save(app, client):
    with app.app_context():
        db.session.add(RebrickablePartCategories(id=1, name="Bricks"))
        db.session.add(
            RebrickableParts(part_num="3002", name="Brick 2 x 3", part_cat_id=1)
        )
        db.session.add_all(
            PartStorage(part_num="3002", location=str(i), level="1", box="1")
            for i in range(40)
        )
        db.session.commit()
        part_lookup_service.invalidate_part_lookup_cache()
        part_lookup_service.load_part_lookup()
        statements = []

        def record_sql(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(db.engine, "before_cursor_execute", record_sql)
        try:
            response = client.post(
                "/manual_entry",
                data={"part_num": "3002", "schrank": "999", "fach": "1", "box": "1"},
            )
        finally:
            event.remove(db.engine, "before_cursor_execute", record_sql)
        assert response.status_code == 200
        assert b"1 part(s) added" in response.data
        assert len(statements) <= 4
        assert not any("rebrickable_inventory_parts" in sql for sql in statements)
        assert not any(sql.startswith("UPDATE") for sql in statements)
        assert PartStorage.query.count() == 41
        assert PartStorage.query.filter_by(location="0").count() == 1
        assert PartStorage.query.filter_by(location="999").count() == 1
        assert part_lookup_service._part_lookup_cache is None
        lookup = part_lookup_service.load_part_lookup()
        assert "3002" in lookup
        response = client.post(
            "/manual_entry",
            data={"part_num": "3002", "schrank": "999", "fach": "1", "box": "1"},
        )
        assert b"1 part(s) updated" in response.data
        assert PartStorage.query.count() == 41
        part_lookup_service.invalidate_part_lookup_cache()
