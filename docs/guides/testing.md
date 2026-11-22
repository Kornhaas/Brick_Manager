# Tests

Die Suite nutzt pytest, eine temporäre SQLite-Datenbank, Flask-Testclients und gemockte externe HTTP-Grenzen. Die Konfiguration steht in `pytest.ini`, gemeinsame Fixtures in `brick_manager/tests/conftest.py`.

## Farbgruppen und visuelle Identität

`test_set_detail_colors.py` prüft gruppierte Zugehörigkeit regulärer, Ersatz-
und Minifigurenteile, vollständige/abweichende Zeilen, transparente und ungültige
RGB-Werte sowie fehlerhafte Formularentwürfe ohne Mengenänderung. Die neuen
Verhaltensfälle wurden zunächst ohne Gruppen, Zustände und Farbmuster rot
nachgewiesen. Ein anfänglicher `NULL`-RGB-Test wurde an die tatsächliche
NOT-NULL-Spalte angepasst (leere Zeichenkette als ungültiger Katalogwert).

`tests/browser/visual_identity_smoke.py` prüft mit synthetischer Sammlung und
isolierter Test-App sechs Seiten bei 1440/390 Pixeln, mobile Navigation,
sichtbaren Tastaturfokus und lokale Assets. Ein zusätzlicher echter Browserablauf
kontrolliert Farbmuster, sofortige Zeilen-/Gruppenzustände, Einklappen, Suche,
Wiederöffnen fehlerhafter Eingaben sowie Speichern/Neuladen. PNG-Nachweise und
Banner-/Icon-Exporte liegen unter `BRICK_VISUAL_ARTIFACTS`. Optional liefert
`BRICK_VISUAL_CDN_CACHE` nach SHA-256 der URL benannte unveränderte CDN-Dateien,
damit wiederholte Viewportwechsel nicht an externen CSS-/Font-Timeouts hängen.
Ohne Cache werden diese Abhängigkeiten regulär abgerufen.

Das ist keine vollständige WCAG-Abnahme, kein Nutzertest mit Personen und kein
Test des Produktionsservers. Die bestehenden Setdetail-/PDF-Browserläufe
prüfen zusätzlich Filter-/Positionsrückkehr, Retry, Minifiguren und Downloads.

## Container-Sicherheitsregressionen

`test_release_gate.py` prüft drei Verträge: echte Pytest-Ausführung vor dem
Veröffentlichungsjob, Aktualisierung geerbter Laufzeitpakete ohne CI-Layer-Cache
und fehlschlagende Trivy-Prüfung mit weiter hochgeladenem SARIF-Bericht.
Die letzten beiden Fälle scheiterten vor der Korrektur an fehlender Runtime-Stufe
bzw. fehlendem Fehler-Exitcode. Diese Konfigurationstests ersetzen keinen
tatsächlichen Image-Scan. Am 22. November 2026 ergab derselbe lokale Trivy-Scanner
0.76.2 für das alte Image 32 Paketbefunde und für den frisch gebauten Kandidaten
0; die originalen JSON-Berichte wurden als Security-Nachweise aufbewahrt.

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

Letzter erfolgreicher vollständiger Lauf: 22. November 2026, lokal im Linux-Devcontainer/Python 3.12:
700 bestanden, 0 fehlgeschlagen,
0 übersprungen, 75,45 % Gesamt-Coverage. Die bekannten Windows-Grenzen aus dem
Lauf vom 21. November (Symlinkrechte und Linux-Interpreter im gemeinsamen
Workspace) bleiben Umgebungsfragen und wurden nicht durch Testskips verdeckt.

## Setdetails und kontexterhaltende Rückkehr

`test_set_detail.py` prüft die direkt adressierbare HTML-Seite, die unveränderte
Legacy-JSON-Antwort, getrennte physische Kopien und ID-Namensräume, strikt
validierte und atomare Änderungen, Rücksprungziele, globale Sortierung und
ungültig gewordene Ergebnisseiten. Auch kopieneigene Minifigurenteile ohne
passende Figur sowie deren Eigentumsgrenzen werden isoliert geprüft.

```powershell
poetry run pytest --no-cov -q brick_manager/tests/test_set_detail.py brick_manager/tests/test_ui_contracts.py
node --test tests/js/*.cjs
```

Der zusätzliche Browserlauf benötigt Playwright und einen installierten
Chromium-Browser. Er startet ausschließlich die gemeinsame Testanwendung mit
temporärer SQLite-Datenbank:

```powershell
$env:BRICK_BROWSER_CHANNEL = 'msedge' # Optional, sonst Playwright-Chromium
poetry run python tests/browser/set_detail_smoke.py
```

Vier umfangreiche Abläufe prüfen Rückkehr von Seite 2 mit Filtern/Sortierung,
mehrfaches Speichern ohne Seitenwechsel, echte beobachtete BFCache-Rückkehr mit
aktuellen Werten, Tastatur und 390 Pixel, Netzwerkfehler/Retry, Entwürfe beim
Verlassen und vollständige Sammeländerungen einschließlich ausgeblendeter
Minifigurenteile. Der automatisierte Lauf blockiert externe Ressourcen über
Chromium-Auflösung. Ein zusätzlicher visueller 390-Pixel-Check verwendete die
echte festgelegte Bootstrap-CSS; auch dort überlief keine Seite den Bildschirm.
Eine Prüfung auf echtem iPad, Safari oder mit Screenreader wurde nicht ausgeführt.

## PDF-Setetiketten

`test_set_label_contracts.py` und `test_set_label_pdf.py` prüfen 58 Fälle:
tatsächliche PDFs und Druckstatus, Unabhängigkeit von externen Vorlagen und
Arbeitsverzeichnis, A4-Seitenzahlen/-größen, Schnittmaße und Seitenränder,
Sonderzeichen, lange Titel/Boxnummern, eingebettete Bilder mit korrektem Verhältnis,
Cache, fehlende Bilder und Warnungen, begrenzte/fehlgeschlagene HTTP-Abrufe,
ungültige Anfragen, fehlende Kopien, Dateifehler und Transaktions-Rollback.
Die Schnittregressionen messen gemeinsame horizontale Kanten ohne Zwischenraum
und eine bündige linke Schnittkante bei 10 mm für alle MB-4-/Big-Box-Seitenbögen.
`pypdf` ist dafür ausschließlich als Entwicklungsabhängigkeit gelockt; die
Anwendung benötigt weiterhin nur das bereits vorhandene ReportLab/Pillow.
Alle automatisierten Abrufe sind gemockt, Ausgaben und Datenbanken isoliert.

```powershell
poetry run pytest --no-cov -q brick_manager/tests/test_set_label_contracts.py brick_manager/tests/test_set_label_pdf.py
poetry run python tests/browser/set_label_smoke.py
```

Der Browserlauf benötigt wie der Setdetailtest Playwright und Chromium/Edge.
Er prüft alle drei echten PDF-Downloads gegen die erzeugten Dateien, Seitenzahlen,
Bildwarnung, sichtbare Fehlermeldung mit Retry, Druckstatus und unveränderte
Filteradresse. Externe Ressourcen sind blockiert. Zusätzliche lokale PDFs aller
drei Formate mit dem Setbild 71486-1 wurden über Poppler gerendert und visuell geprüft. Ein
physischer Druck wurde nicht ausgeführt.

## Erwartete Nachweise

Die aufgabenbezogenen Lagerseiten werden durch
`brick_manager/tests/test_warehouse_pages.py` geprüft: getrennte Formularmengen,
aktive Navigation, eindeutige HTML-IDs, gleichbleibendes Sitzungstoken und
deaktivierte Einstiege. `tests/browser/warehouse_pages_smoke.py` prüft die
Seitenübergänge und sichtbaren Formularzustände gegen eine isolierte Testanwendung.
Ausführung mit Playwright und Chromium:

```powershell
poetry run python tests/browser/warehouse_pages_smoke.py
# Alternativ einen installierten Chromium-Browser verwenden:
$env:BRICK_BROWSER_CHANNEL = 'msedge'
poetry run python tests/browser/warehouse_pages_smoke.py
```

`BRICK_BROWSER_SCREENSHOT` kann einen dauerhaften Screenshotpfad vorgeben.
Ohne diesen Parameter liegen Screenshots im temporären Arbeitsverzeichnis.
Das ist kein Test der Produktivdatenbank; die Testanwendung startet keine
Produktivmigrationen und keinen Produktionsscheduler.

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

### Paketbuild für den zusammengeführten Stand

Commit `4c8bcea` wurde mit `poetry check --lock` geprüft: erfolgreich, lediglich
bestehende Poetry-Hinweise zur älteren Metadatenstruktur. Wheel und Quellpaket
wurden aus einem sauberen `git archive` dieses Commits unter `/tmp` gebaut.
Der zunächst im eingebundenen Workspace gestartete Paketbuild wurde wegen der
langsamen Dateisystemzugriffe beendet und durch diesen reproduzierbaren
Build ohne Laufzeitdateien ersetzt. Beide Artefakte sind erfolgreich:

- `brick_manager-0.0.1-py3-none-any.whl`: 99 enthaltene Pythondateien kompilierbar;
  beide geprüften Migrationsartefakte bytegleich zum Commit.
- `brick_manager-0.0.1.tar.gz`: README und neue Indexmigration enthalten.

Beide Archive enthalten weder Datenbankdateien noch `.env`. Keine Anwendung
wurde für diese Prüfung gestartet und keine Live-Datenbank geöffnet.
In der aktuellen Arbeitsumgebung ist weder Docker noch Podman/BuildKit
verfügbar; ein tatsächlicher Containerbuild ist lokal daher nicht nachgewiesen.
Für diesen Commit existierte zum Prüfzeitpunkt kein GitHub-Actions-Lauf, weil
der entfernte `main` noch auf `845921b` stand. Ein Push auf `main` startet laut
`.github/workflows/docker-image.yml` auch die Veröffentlichung des Docker-Images.
Diese Veröffentlichung braucht eine ausdrückliche Freigabe; lokale Paketbuilds
sind kein Nachweis für einen erfolgreichen GitHub-/Multiarch-Dockerbuild.

### GitHub-Prüfung nach freigegebenem Push

Für Commit `c6b4b0e` wurden nach ausdrücklicher Push-/Publikationsfreigabe alle
relevanten Workflows erfolgreich abgeschlossen:
[Python-Tests](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852911),
[Pylint](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852642),
[Codacy](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852831) und
[Docker](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852562).
Docker baute/veröffentlichte beide Zielarchitekturen, prüfte Start/Health im
isolierten CI-Container und schloss den Trivy-Job erfolgreich ab. Der bestehende
Pylint-Workflow behandelt Hinweise nicht als Buildfehler. Der „Deploy“-Job ist
lediglich eine Benachrichtigung mit manuellen Deployment-Anweisungen.
Der Pre-push-Hook bestand nochmals 554 Tests mit 72,24 % Coverage.
Keine Live-Daten oder bestehenden Anwendungsserver wurden dafür verändert.

### Erste Architektur-/Usability-Welle

Die neuen Python-Regressionen in `test_collection_hardening.py` reproduzierten
zunächst 13 Fehler bei Tabellen-ID-Kollisionen, Batches, Setlisten und Filtern;
weitere Skalartests reproduzierten sechs Fehler durch Trunkierung/Typverwechslung.
Die 13 Backup-Tests in `test_backup_service.py` führen echte SQLite-WAL-Fälle aus
und extrahieren ausschließlich die zwei Scheduler-Wrapper aus dem AST, ohne die
Produktiv-App zu importieren. Quelle, Rotation, Symlinks, Kollisionen und
Fehlerisolation werden mit temporären Dateien geprüft.

JavaScript-Prüfung ohne zusätzliche npm-Abhängigkeiten:

```bash
node --test tests/js/*.cjs
```

Der ausgeführte Lauf bestand **25 Prüfungen**, darunter vorhandene Navigation,
13 neue Speicherszenarien, drei Katalog-Renderingfälle und der Dashboard-Controller.
Letzterer prüft mehrere Zusicherungen in einem Harness: serialisierte Writes,
neueste Absicht, Typidentität, Dezimalfehler, Server-Clamping, Retry und Rücknahme
während eines laufenden Saves. Rote Fälle wurden vor der jeweiligen Korrektur
nachgewiesen.

Zusätzlicher isolierter Browserlauf:

```bash
PYTHONPATH=/tmp/brick-browser PLAYWRIGHT_BROWSERS_PATH=/tmp/brick-browser-cache poetry run python tests/browser/collection_hardening_smoke.py
```

Er bedient echte Dashboard-Eingaben mit kollidierenden Datensatz-IDs und
kontrolliert verzögerten Antworten, Netzfehler/Retry, Dezimalprüfung, tatsächliche
Datenbankänderung und den unveränderten anderen Bestand. Externe DataTables-
Initialisierung wird bewusst gestubbt; der neue native Mengencontroller läuft
real. Zwei weitere isolierte Chromium-Prüfungen der Setpflege bestätigten
Mengen/Bulkabschluss und wörtliche Katalogdarstellung mit abgefangenen Requests.
Das sind automatisierte DOM-Prüfungen, keine Nutzertests mit Personen.

Synthetischer Setlistenvergleich mit 30 Sets und 6.000 Teilezeilen: zuvor 6.000
Teileobjekte/10 Queries/0,1891 s, danach 0 Teileobjekte/9 Queries/0,0979 s.
Je ein isolierter Lauf, kein Live-Benchmark und keine garantierte Latenz.
Die dauerhaft zugesicherte Regression prüft unveränderte Summen ohne geladene
Inventarobjekte, nicht eine fragile Zeitgrenze.

`test_release_gate.py` scheiterte zunächst am auskommentierten Pytest-Schritt im
Docker-Testjob. Der Schritt wird jetzt vor dem abhängigen Veröffentlichungsjob
ausgeführt. Diese Welle löst keine Remote-Pipeline oder Image-Publikation aus;
deren tatsächliches Ergebnis ist damit noch nicht geprüft.

Abschließender Gesamtlauf dieser Welle am 15. November 2026 nach dem CI-Gate-Fix:
**589 bestanden, 0 fehlgeschlagen, 0 übersprungen, 73,06 % Coverage**.
Projektweites Ruff und BasedPyright sowie Formatprüfung (108 Pythondateien)
bestanden. Wheel und Quellpaket wurden aus einem isolierten Quellbaum
(Commitbasis plus Arbeitsdiff und neuen Quelldateien) gebaut; neue Services und
Controller sind enthalten, alle enthaltenen Pythondateien kompilieren und keine
Datenbank oder `.env` liegt im Paket. Der lokale Paketbuild prüft keinen
Multiarch-Container und löst keine CI-Veröffentlichung aus.
