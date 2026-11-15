# Schrittweise Architektur- und Usability-Verbesserung

Ausgangsstand: `ac40f74` (15. November 2026), sauberer Checkout. Auftrag:
projektweite Architektur- und Nutzerperspektive prüfen und konkrete Verbesserungen
testgetrieben umsetzen. Diese Liste trennt die laufende erste Welle von noch
nicht umgesetztem Backlog. Sie ist keine Behauptung vollständiger Fehlerfreiheit.

## Arbeitsgrenzen

- Keine Live-Datenbank öffnen oder verändern; keine Serverstarts/-neustarts,
  Migrationen, Synchronisationen, Pushes oder Veröffentlichungen in diesem Auftrag.
- Bestehende Flask-/Service-/Modellstruktur erhalten, keine neue Frameworkschicht.
- Fehler zunächst durch Regression reproduzieren, dann kleinste fachlich passende
  Korrektur; Datenidentität und bestehende zulässige Aufrufe erhalten.
- Temporäre Datenbanken, begrenzte synthetische Bestände und Netzwerkattrappen
  für automatisierte Prüfungen verwenden. Keine Messung als Live-Benchmark ausgeben.

## Erste Welle

- [x] **Sichere geplante SQLite-Sicherungen.** `app.py:backup_database` verwendet
  derzeit Dateikopie statt SQLite-Backup-API. WAL und relativer Instance-Pfad
  benötigen Regressionen. Sicherung in Service verlagern, vorhandenen SQLite-
  Backuphelfer wiederverwenden, Rotation erst nach Erfolg und nur eigene Dateien.
- [x] **Eindeutige Mengenidentität im Dashboard.** `/update_quantity` sucht eine ID
  zuerst in regulären Teilen, dann in Minifigurenteilen. Unabhängige Tabellen können
  dieselbe ID haben. Typisierte DTOs/Requests; mehrdeutige Altaufrufe mit 409 stoppen,
  gesamten Batch vor Änderung auflösen, tatsächliche gespeicherte Mengen bestätigen.
- [x] **Zuverlässiges Speichern in der Setpflege.** `saveQuantity` sendet parallel;
  alte Antworten können neuere Eingaben zurücksetzen. Pro Feld serialisieren,
  neueste Absicht erhalten, keine stille Dezimaltrunkierung, verständlicher Fehler
  und erneuter Speicherversuch. Tab-/Enter-Bedienung erhalten.
- [x] **Schlanke Setliste und korrekter Themenfilter.** Die paginierte Liste lädt
  alle Teile-/Figurenobjekte ihrer Sets für Summen. Skalare Summen nur für die
  aktuelle Seite berechnen. Den Suchfilter nicht mit dem Thema der letzten
  gerenderten Zeile überschreiben. Prozentwerte und physische Kopien erhalten.

- [x] **Dashboard-Speicherbestätigung und Katalogtexte.** Alter Inline-Autosave
  durch einen delegierten, serialisierten Controller ersetzt: typisierte Ziele,
  neuere Eingaben erhalten, gespeicherte Clamp-Werte übernehmen, sichtbare Fehler
  und Retry. Minifiguren-/Teiltexte in der Setpflege werden als Text dargestellt,
  dynamische RGB-Angaben auf sechs Hexzeichen begrenzt.

- [x] **Docker-Veröffentlichung durch echte Tests sperren.** Der vorhandene
  Testschritt war auskommentiert. Eine Konfigurationsregression weist das nach;
  der abhängige Build-/Push-Job benötigt künftig einen erfolgreichen Pytestlauf.
  In diesem Auftrag wird keine Pipeline/Veröffentlichung ausgelöst.

## Priorisiertes Backlog aus den unabhängigen Reviews

Die folgenden Punkte sind zunächst Quellcodebefunde; konkrete Umsetzung und
Breite brauchen jeweils ihre eigenen Regressionen und eine abgegrenzte Welle.

| Priorität | Befund / Einstieg | Nächster Nachweis und kleinster Schritt |
| --- | --- | --- |
| Hoch | Setdetails laden ohne Antwortgeneration (`set_maintenance.js`); feste 500-ms-Handlerfrist für Lagerortzeilen | Verzögertes A nach B bzw. Zurück darf Auswahl nicht überschreiben; Handler beim tatsächlichen Rendern oder delegiert anbinden. |
| Hoch | Warehouse-Detailantworten können neuere Auswahl überschreiben (`warehouse.js:selectUnit`) | Zwei verzögerte Antworten und Wechsel auf Altgruppe; gemeinsame Detailgeneration statt bloßer Auswahl-ID. |
| Hoch | Label-Bildrenderer lädt eigenen Cache wieder über HTTP (`label_service.py`) | Lokales Cachebild im Backend ohne Loopback-Request lesen; Single-Worker- und Standalone-Fall testen. |
| Hoch | Fehlerhafte gespeicherte Etikettenvormerkung blockiert alle Vormerkungen (`label_queue_service.py:marks`) | Ungültige JSON-Präferenz neben gültiger Zeile: erklärter Einzelfehler statt 500 und kein stilles Löschen. |
| Mittel | Einzelner Etikettendruck wertet gesamte Queue und ausgewählte Inhalte doppelt aus (`selected`, `label_infos`) | Query-/Aufrufbudget unabhängig von ungewählten Boxen; nur angefragte Schlüssel laden und Infos wiederverwenden. |
| Mittel | Fokussierte Lagerübersicht lädt alle bestätigten Einheiten samt Inhalt (`storage_service.py:overview`) | 1 vs. 100 fremde Boxen: begrenzte Antwortgröße/Queries; schlanke Referenzen und Details bei Bedarf. |
| Mittel | Setdetails haben lineare Zusatzabfragen und nehmen ersten Lagerort ohne Farbe (`get_user_set_details`, `enrich_item`) | 1 vs. 50 Teile, mehrere Farben/Fundorte; gebündelter DTO-Aufbau mit erklärter Mehrdeutigkeit. |
| Mittel | Dashboard-Tages-Snapshot benutzt SELECT-dann-INSERT bei eindeutigem Datum | Zwei Sessions am Tagesanfang, Konfliktbehandlung/Upsert ohne 500; Lesen und Snapshot-Schreiben später entkoppeln. |
| Mittel | Boxfilter und Etikettendownload haben ungesicherte asynchrone Zustände | Verzögerte Requests, Abbruch/Fehler und wechselnde Auswahl im isolierten Browser testen, explizite Ladezustände. |
| Mittel | Setlistensortierung gilt nur für aktuelle Seite und ist klickabhängig | Globale serverseitige Sortierung mit stabilem Queryvertrag; Keyboard und `aria-sort`, Seitengrenzen ausdrücklich testen. |
| Mittel | Fehlteile-ID-Filter expandiert unbeschränkt Bereiche und ignoriert ungültige Teile (`missing_parts.py`) | Große/ungültige Bereiche begrenzen und Fehler erklären; Filter in SQL anwenden, bevor Sammlungszeilen geladen werden. |
| Später | App-Import startet Initialisierung und Scheduler | Charakterisierung von CLI, mehrfachen Imports und isoliertem Modus; explizite Startkonfiguration vor möglichem App-Factory-Umbau. |

## Abnahme der ersten Welle

1. Gezielte Regressionen zunächst fehlgeschlagen, nach Korrektur bestanden.
2. Mengen: kollidierende IDs, typisierte Mischbatches, mehrdeutige Altpayloads,
   ungültige/fehlende Ziele, Clamping und unveränderte andere Bestände.
3. UI: schnelle Eingabefolge, ausstehende Saves, Netzwerkfehler, Dezimalwerte,
   erneuter Versuch und vorhandene Tastaturnavigation.
4. Sicherung: bestätigte WAL-Daten, korrekte aufgelöste Quelle, Nicht-SQLite/
   In-memory, Kollisionen, fehlgeschlagene Sicherung und sichere Rotation.
5. Setliste: unveränderte Summen einschließlich Figuren/Ersatzteilen, Themenfilter,
   Seitengrenzen und keine geladenen Inventarobjekte für reine Summen.
6. Gesamtsuite, relevante JavaScript-/Browserprüfungen, Ruff, BasedPyright und
   Paketbuild. Ergebnisse und Grenzen in Testanleitung und Logbuch festhalten.

Die zentralen Architektur-/Bedienungsdokumente werden mit den tatsächlich
umgesetzten Verträgen aktualisiert. Ein Live-Rollout benötigt einen eigenen Auftrag.

## Status der ersten Welle

Die oben markierten Pakete sind implementiert. 13 anfängliche Parent-Regressionen
schlugen vor der Korrektur fehl; weitere Scalar-Regressionen bestätigten sechs
Fehler vor der Korrektur. Der Backup-Review reproduzierte insbesondere WAL-Verlust,
falsche relative Quelldatei und unzulässige Rotation. Die JavaScript-Prüfungen
reproduzierten Mengenrennen und Markup-Interpretation vor deren Korrektur.
Die integrierte Abschlussprüfung ist in Testanleitung und Logbuch dokumentiert: 589 Python-Tests, 25 Node-Prüfungen, gezielte isolierte Browserläufe und beide Paketformate bestanden. Ruff und BasedPyright sind grün. Kein Live-Rollout und keine Remote-Veröffentlichung wurden ausgeführt.
Das priorisierte Backlog ist damit ausdrücklich noch nicht umgesetzt.
