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
