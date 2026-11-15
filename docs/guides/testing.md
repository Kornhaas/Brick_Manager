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

### Unveränderliche Migrationen und Formatter

Nach der Wiederherstellung der Originalmigration und Absicherung der mutierenden
Hooks bestand der vollständige Lauf vom 15. November 2026 **529 Tests**, ohne
Fehler oder übersprungene Tests, mit **71,34 % Gesamt-Coverage**. Sechs zusätzliche
Regressionen prüfen echte explizite Ruff-Aufrufe auf einer angewendeten Migration
und die Dateiauswahl der vier mutierenden Pre-commit-Hooks. Die gespeicherte
Prüfsumme wird bei diesem Verfahren nicht verändert; semantische Änderungen an
einer angewendeten Datei bleiben durch die bestehenden Migrationsprüfungen gesperrt.

### Bestehende Lagerzuordnungen in der Übersicht

Der vollständige Lauf vom 15. November 2026 nach der Sichtbarkeitskorrektur
bestand **534 Tests**, ohne Fehler oder übersprungene Tests, mit **71,58 %
Gesamt-Coverage**. Fünf Regressionen in `test_warehouse_legacy_overview.py`
prüfen lesende Gruppenprojektion ohne erfundene Behälter, mehrdeutige Fachlabels,
die Zuordnung genau einer bestehenden Zeile und konservative Stellflächen-/
Passaussagen bei Altbelegung. Alle fünf schlugen vor der Korrektur fehl.

Zusätzlich liefen `tests/browser/warehouse_smoke.py` und
`tests/browser/warehouse_legacy_smoke.py` erfolgreich auf isolierten Testdaten.
Der neue Browserlauf prüft vorhandene Inhalte trotz null physischer Einheiten,
Nummernsortierung, unbekannte Mengen, Notizen, fehlende Fundorte, Textsicherheit,
die tatsächliche Zuordnung über das Formular und Darstellung bei 1365/390 Pixeln.
Aufruf mit derselben oben dokumentierten Playwright-Umgebung; keine echten
Sammlungsdaten werden durch diese Browsertests verändert.

### Teilevorschau und Spaltenrichtung

Nach Ergänzung der Teilevorschau und der Spaltenrichtung bestand der vollständige
Lauf am 15. November 2026 **534 Tests**, keine Fehler/Skips, **71,59 % Coverage**.
Der erweiterte `warehouse_legacy_smoke.py` prüft Vorschautexte und die echten
Kartenkoordinaten: unten nach oben, danach nächste Spalte, Änderung der Zeilenzahl
und die alternative aufsteigende Listenansicht. Beide Browser-Smokes bestanden.
Externe Bildrequests werden dabei abgefangen; die Erreichbarkeit des Bildanbieters
ist damit nicht geprüft. Der Backend-Vertrag prüft die übertragene Katalogbild-URL.

### Inventarbilder und expliziter Etiketten-Neudruck

Abschließender Gesamtlauf am 15. November 2026: **549 bestanden**, keine Fehler
oder Skips, **72,06 % Coverage**. Die 15 Fälle in
`test_label_reprint_queue.py` prüfen getrennte Vormerkung/Druckstatus,
Gruppierung, stabile Behälter-IDs, wiederholte/veraltete Bestätigung,
gezieltes Entfernen veralteter Vormerkungen, ungültige Eingaben, CSRF und
Inventarbilder bei fehlendem Teile-Stammbild. Der fokussierte Lauf verwendet
`--no-cov`; der Gesamtlauf erfüllt die bestehende Coverage-Schwelle.

Alle drei Browserläufe bestanden:
`warehouse_smoke.py`, `warehouse_legacy_smoke.py` und
`warehouse_labels_smoke.py`. Der neue Lauf lädt ein echtes Bild aus einer
lokal abgefangenen Inventarbild-URL, markiert über die echte Checkbox,
wechselt zur Druckseite, simuliert einen fehlgeschlagenen PDF-Download,
erzeugt danach ein echtes PDF und bestätigt den Druck über das Formular.
Neuladen vor der Bestätigung erhält die Vormerkung. Nur externe Bildzugriffe
der serverseitigen PDF-Erzeugung werden mit einem lokalen Bild ersetzt;
Bootstrap wird bei abgefangenen externen CDN-Requests ausdrücklich gestubbt.
Der Test nutzt ausschließlich eine wegwerfbare Testdatenbank mit aktivem CSRF.

### Fachweise Datenabfrage und Inventarbildindex

Abschließender Lauf am 15. November 2026: **553 bestanden**, keine Fehler oder
Skips, **72,24 % Coverage**. Drei zusätzliche Übersichtstests prüfen die fachweise
Antwort, weiterhin globale Zähler, zurückgestellte ungeklärte Inhalte,
Nachladen dieser Inhalte, leeres Fach ohne Bildabfrage und explizite Gesamtansicht.
Ein zusätzlicher Migrationstest erhält Inventar- und Lagerzeilen, wiederholt den
Indexschritt und prüft `EXPLAIN QUERY PLAN` auf die Nutzung als Covering Index.
Die vorhandenen Startup-/Frischdatenbanktests berücksichtigen jetzt drei
journalisierte Migrationsartefakte.

Alle drei Playwright-Abläufe bestanden mit dem fachweisen Vertrag. Der volle
Ablauf wurde nach Absicherung des laufenden Fachwechsels erneut erfolgreich
geprüft: Archivaktionen sind bis zum Abschluss des Fachwechsels deaktiviert.
Der Legacy-Lauf prüft weiterhin die zuletzt gewählte Fachauswahl und lädt
ungeklärte Inhalte erst beim Öffnen. Externe Zugriffe bleiben in diesen
isolierten Tests abgefangen.

Messung auf einer konsistenten Kopie der Entwicklungsdatenbank: ursprüngliche
vollständige Aufbereitung **14,078 s**, davon **13,532 s** Inventarbild-SQL.
Mit neuem Index: fachweise Aufbereitung inklusive JSON **0,064 s / 243.129 Byte**,
187 sichtbare Inhaltszeilen bei insgesamt 2.935; vollständige Ansicht
**0,292 s / 3.239.918 Byte**. Das sind lokale Messungen derselben Sammlung,
keine garantierten Antwortzeiten auf anderen Systemen. Gemessen wurde rein
lesend ohne Bilddownloads; die Kopie erhielt vorher ausschließlich den Index.

Am anschließend neu gestarteten Entwicklungsserver wurden HTTP 200 und
**222.120 Byte** für die fachweise Antwort gemessen: erster Aufruf **0,635 s**,
Folgeaufrufe **0,349 s / 0,379 s**. Der globale Zähler blieb bei 2.935. Diese
Messung schließt HTTP-Übertragung über localhost ein; die kompakte
Flask-Serialisierung erklärt den Unterschied zur Bytezahl des obigen
Standalone-JSON-Vergleichs.

Die explizite vollständige HTTP-Antwort benötigte auf dem eingebundenen
Dateisystem weiterhin **17,361 s / 2.981.187 Byte**. Sie wird beim Start nicht
mehr angefordert. Die lokale Kopie allein ist deshalb kein Nachweis für die
Geschwindigkeit der Gesamtansicht auf diesem Dateisystem.

### Prüfung vor lokalem Commit und main-Übernahme

Der vollständige Lauf vom 15. November 2026 einschließlich der Regression für
Startplatzhalter und versionierte Script-URL bestand **554 Tests**, keine Fehler
oder Skips, **72,24 % Coverage**. Die Fixture-Konfiguration bindet importierte
Anwendungsmodule an eine temporäre SQLite-Datei; die vorhandenen Live-Daten
werden nicht als Testdatenbank verwendet. Alle anwendbaren Pre-commit-Hooks,
projektweites BasedPyright und JavaScript-Syntaxprüfungen bestanden ebenfalls.
Browser- und Build-Nachweise der vorherigen Arbeit wurden dabei nicht wiederholt.
