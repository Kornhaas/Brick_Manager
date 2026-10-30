# Tests

Die Suite nutzt pytest, eine temporäre SQLite-Datenbank, Flask-Testclients und gemockte externe HTTP-Grenzen. Die Konfiguration steht in `pytest.ini`, gemeinsame Fixtures in `brick_manager/tests/conftest.py`.

## Befehle

```powershell
# Ein fokussierter Test ohne die globale Coverage-Schwelle
poetry run pytest --no-cov -q brick_manager/tests/test_client_api.py

# Vollständige konfigurierte Suite einschließlich Coverage-Gate
poetry run pytest -q

# Nur nicht langsame Tests
poetry run pytest -q -m "not slow"

# JavaScript-Unit-Tests (Node.js 18+)
node --test tests/js/quantity_navigation.cjs
```

Die globale Coverage-Schwelle beträgt derzeit 60 Prozent. Sie ist ein Release-Gate, nicht der Nachweis ausreichender Testtiefe für jede risikoreiche Funktion. Messwerte werden nur nach einem erfolgreichen vollständigen Lauf dokumentiert; historische Messungen stehen unter `docs/history/`.

## Erwartete Nachweise

- Routen: Status, stabiler HTML-/JSON-Vertrag, ungültige Eingaben, fehlende Ressource und resultierender Datenbankzustand.
- Services: fachliches Ergebnis und exakter externer Request, inklusive Timeout- und Fehlerverhalten.
- Modelle und Migrationen: Constraints, Beziehungen, Kaskaden sowie wiederholbare Upgrade-Pfade.
- Datei-/Label-/Cache-Logik: temporäre, deterministische Ausgaben und Bereinigung bei Fehlern.

Tests dürfen keine realen Rebrickable- oder Brickognize-Endpunkte aufrufen. Die Anzahl gesammelter Tests ersetzt keine fachliche Assertion oder Coverage-Bewertung.
