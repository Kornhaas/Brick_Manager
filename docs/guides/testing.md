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

Letzter vollständiger Lauf: 30. Oktober 2026, 397 bestanden, 0 fehlgeschlagen,
0 übersprungen, 62,92 % Gesamt-Coverage. Ein `ResourceWarning` aus einer
SQLite-Verbindung wurde ausgegeben, hat den Lauf aber nicht fehlschlagen lassen.

## Erwartete Nachweise

- Routen: Status, stabiler HTML-/JSON-Vertrag, ungültige Eingaben, fehlende Ressource und resultierender Datenbankzustand.
- Services: fachliches Ergebnis und exakter externer Request, inklusive Timeout- und Fehlerverhalten.
- Modelle und Migrationen: Constraints, Beziehungen, Kaskaden sowie wiederholbare Upgrade-Pfade.
- Datei-/Label-/Cache-Logik: temporäre, deterministische Ausgaben und Bereinigung bei Fehlern.

Die Box-Label-Regressionstests prüfen PDF-Ausgaben auch bei fehlenden
Katalogeinträgen und unveränderte Lagerkennungen mit Leerzeichen beim Download
und bei der Druckbestätigung. Fehlende Katalogdaten werden auf dem Label
ausgewiesen und protokolliert; nur eine tatsächlich fehlende Box liefert 404.
Für das Avery-Raster (70 × 37 mm, 3 Spalten, 8 Reihen) prüfen die Layouttests
mindestens 5 mm Abstand von Text, Bildern und Boxnummernkreis zu den
Schnittkanten sowie kollisionsfreie Text-/Bildbereiche bei langen Namen,
schmalen und breiten Bildern und bis zu sechs sichtbaren Teilen pro Label.
Beim Drucken A4 und 100 % / tatsächliche Größe ohne Seitenanpassung wählen.
Die X-/Y-Korrektur verschiebt nur den gesamten Bogen; sie korrigiert keine
Skalierung oder abweichende Etikettenabstände.

```powershell
poetry run pytest --no-cov -q brick_manager/tests/test_storage_route_contracts.py brick_manager/tests/test_label_service_contracts.py
```

Tests dürfen keine realen Rebrickable- oder Brickognize-Endpunkte aufrufen. Die Anzahl gesammelter Tests ersetzt keine fachliche Assertion oder Coverage-Bewertung.

Der Regressionstest `test_manual_entry_contracts.py` prüft beim manuellen
Speichern den Erhalt bestehender Lagerplätze, Cache-Invalidierung und
wiederholtes Absenden ohne Duplikate. Mit 40 vorhandenen Lagerplätzen
erlaubt er höchstens vier SQL-Anweisungen für einen neuen Eintrag und
schließt Inventartabellen-Abfragen sowie Updates vorhandener Plätze aus.
Das ist eine Prüfung des Abfrageaufwands, keine Browser-Laufzeitmessung.

## Lagerabnahme vom 15. November 2026

Letzter vollständiger Lauf nach den Lagerkorrekturen: **518 bestanden,
0 fehlgeschlagen, 0 übersprungen, 71,34 % Gesamt-Coverage**. Alle konfigurierten
Tests einschließlich Branch-Coverage wurden mit `poetry run pytest -q` ausgeführt.
Die fokussierten Lagerdateien enthalten Alt-/Neuschema-, Mengen-, Reservierungs-,
Stapel-/Flächen-, History-/Bedarfs- und HTTP-Vertragsprüfungen. Die vollständige
Kriterienzuordnung steht in der [Lagerabnahme](../plans/storage-acceptance.md).

```bash
poetry run pytest --no-cov -q brick_manager/tests/test_storage_migration.py brick_manager/tests/test_storage_moves.py brick_manager/tests/test_storage_structure.py brick_manager/tests/test_warehouse_contracts.py brick_manager/tests/test_storage_legacy_compatibility.py brick_manager/tests/test_part_history.py brick_manager/tests/test_storage_suggestions.py
node --check brick_manager/static/js/warehouse.js
node --test tests/js/quantity_navigation.cjs
```

Der Node-Harness registriert mehrere Eventlistener wie ein echter Browser;
8 Tests prüfen Tab-Navigation und den unabhängigen Enter-Speicherpfad.

Optionaler echter Browserlauf (Playwright und Chromium einschließlich ihrer
Systembibliotheken in einer Entwicklungsumgebung bereitstellen):

```bash
poetry run python tests/browser/warehouse_smoke.py
```

Für die ausgeführte Abnahme lagen die Werkzeuge außerhalb der Projektumgebung:

```bash
PYTHONPATH=/tmp/brick-browser PLAYWRIGHT_BROWSERS_PATH=/tmp/brick-browser-cache poetry run python tests/browser/warehouse_smoke.py
```

Dieser Lauf bestand 8 repräsentative Abläufe mit 0 JavaScript-Fehlern. Er startet
nur die isolierte Test-App mit temporärem/in-memory SQLite, verwendet aktiven
CSRF-Schutz und fängt externe Requests ab. Er prüft reale Formulare einschließlich
Stapel, loser Auflage, Magazinunterteilung, Zählung, bestätigter Teilumbuchung,
Archivhinweis, Kategoriestandard, schmalem Viewport und Tastaturfokus. Er verwendet
keine echten Lagerdaten und ersetzt keine Vor-Ort-Prüfung von Maßen/Lasten.

### Startup-Regression: verschachtelte SQLite-Pfade

Der anschließende vollständige Lauf vom 15. November 2026 nach der
Startup-Korrektur bestand **521 Tests**, ohne Fehler oder übersprungene Tests,
mit **71,34 % Gesamt-Coverage**. Zusätzliche Fälle prüfen fehlende
Unterverzeichnisse für relative/absolute Pfade, den Erhalt gespeicherter Daten
bei Wiederholung sowie den regulären Flask-CLI-Loader in einem isolierten
Prozess mit temporärer SQLite-Datei. Scheduler-Ausführung und `.env`-Laden sind
in diesem Startup-Test deaktiviert; die vorhandene Bestandsdatenbank wird nicht
geöffnet.
