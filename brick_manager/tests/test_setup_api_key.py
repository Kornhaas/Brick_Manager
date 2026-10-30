from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from brick_manager import setup_api_key


class FakeSettings:
    existing = None
    query = None

    def __init__(self, **values):
        self.__dict__.update(values)


class FakeQuery:
    def filter_by(self, **values):
        assert values == {"key": "rebrickable_api_key"}
        return self

    def first(self):
        return FakeSettings.existing


@pytest.fixture(autouse=True)
def reset_settings():
    FakeSettings.existing = None
    FakeSettings.query = FakeQuery()


@pytest.fixture
def dependencies():
    added = []
    session = SimpleNamespace(add=Mock(side_effect=added.append), commit=Mock())
    db = SimpleNamespace(
        session=session,
        func=SimpleNamespace(current_timestamp=lambda: "now"),
    )
    app = SimpleNamespace(app_context=nullcontext)
    return app, db, added


def test_initial_setup_reads_key_from_environment(monkeypatch, dependencies):
    app, db, added = dependencies
    monkeypatch.setenv("REBRICKABLE_TOKEN", "  secret-key  ")
    messages = []

    assert setup_api_key.configure_api_key(
        app, db, FakeSettings, output=messages.append
    )
    assert added[0].value == "secret-key"
    assert all("secret-key" not in message for message in messages)


def test_missing_environment_key_does_not_create_setting(monkeypatch, dependencies):
    app, db, added = dependencies
    monkeypatch.delenv("REBRICKABLE_TOKEN", raising=False)

    with pytest.raises(ValueError, match="REBRICKABLE_TOKEN"):
        setup_api_key.configure_api_key(app, db, FakeSettings, output=lambda _: None)

    assert added == []


def test_declining_update_does_not_require_or_disclose_key(monkeypatch, dependencies):
    app, db, added = dependencies
    FakeSettings.existing = SimpleNamespace(value="existing-secret")
    monkeypatch.delenv("REBRICKABLE_TOKEN", raising=False)
    messages = []

    assert not setup_api_key.configure_api_key(
        app, db, FakeSettings, ask=lambda _: "n", output=messages.append
    )
    assert FakeSettings.existing.value == "existing-secret"
    assert added == []
    assert all("existing-secret" not in message for message in messages)


def test_confirming_update_replaces_key_without_disclosing_it(
    monkeypatch, dependencies
):
    app, db, _ = dependencies
    FakeSettings.existing = SimpleNamespace(value="existing-secret")
    monkeypatch.setenv("REBRICKABLE_TOKEN", "replacement-secret")
    messages = []

    assert setup_api_key.configure_api_key(
        app, db, FakeSettings, ask=lambda _: "y", output=messages.append
    )
    assert FakeSettings.existing.value == "replacement-secret"
    assert FakeSettings.existing.updated_at == "now"
    assert all("secret" not in message for message in messages)


def test_confirmed_update_without_environment_key_keeps_existing_value(
    monkeypatch, dependencies
):
    app, db, added = dependencies
    FakeSettings.existing = SimpleNamespace(
        value="existing-secret", updated_at="original-time"
    )
    monkeypatch.delenv("REBRICKABLE_TOKEN", raising=False)
    messages = []

    with pytest.raises(ValueError, match="REBRICKABLE_TOKEN"):
        setup_api_key.configure_api_key(
            app, db, FakeSettings, ask=lambda _: "y", output=messages.append
        )

    assert FakeSettings.existing.value == "existing-secret"
    assert FakeSettings.existing.updated_at == "original-time"
    assert added == []
    db.session.commit.assert_not_called()
    assert all("existing-secret" not in message for message in messages)
