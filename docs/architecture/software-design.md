# Softwaredesign

## Einordnung

Dieses Dokument beschreibt Implementierungsgrenzen und Änderungsverträge des bestehenden Systems. Für Systemkontext siehe [High-Level-Design](high-level-design.md), für Komponenten und Startverhalten die [Referenzarchitektur](reference-architecture.md). Verbindliche technische Entscheidungen stehen in [Architekturentscheidungen](decisions.md).

## Verantwortlichkeiten und Verträge

| Bereich | Implementierung und Änderungsvertrag |
| --- | --- |
| HTTP-Eingang | `brick_manager/routes/`: Form-/JSON-Eingaben prüfen, Statuscodes und Antworten festlegen; betroffene Templates und API-Verbraucher gemeinsam ändern |
| Wiederverwendbare Logik | `brick_manager/services/`: Fachlogik, externe Clients und Dateiverarbeitung; Fehler- und Seiteneffekte für Aufrufer nachvollziehbar halten |
| Persistenz | `brick_manager/models.py` und versionierte Migrationen: bestehende Daten erhalten, Transaktionen und Wiederholbarkeit beachten |
| Präsentation | `brick_manager/templates/` und `static/`: Jinja, CSS und Vanilla JavaScript; Formularnamen, JSON-Felder und DOM-Verbraucher synchron halten |
| Komposition | `brick_manager/app.py`: Erweiterungen, Blueprints und Hintergrundaufgaben; Import-Seiteneffekte bei Änderungen und Prüfungen berücksichtigen |

Die Trennung beschreibt die bestehenden Verantwortlichkeiten und die Richtung für Erweiterungen. Sie behauptet nicht, dass bestehende Routen ausschließlich Services verwenden: direkte Modellzugriffe und umfangreichere Routenlogik sind vorhanden.

## Beispiel: Teile und Lagerorte

`brick_manager/routes/part_location.py` lädt Kategorien über `RebrickableService` und lokale Zuordnungen über `load_part_lookup`. Bei einer Kategorieauswahl werden Teileinformationen mit Lookup-Feldern und gecachten Bildern ergänzt und an `part_location.html` übergeben. Fehler beim Laden führen in diesem Ablauf zu einer Fehlerseite mit Status 500.

Der Ablauf verbindet HTTP-Eingaben, externe Daten, lokale Dateien und Darstellung. Änderungen an Lagerfeldern müssen deshalb neben Modellen auch Lookup-Funktionen, Formular-/JSON-Verbraucher und Cache-/Label-Verwendung prüfen. Das vollständige Schema bleibt ausschließlich in der [Datenbankreferenz](../reference/database-schema.md).

## Querschnittsregeln

- Produktionsmodule verwenden überwiegend Top-Level-Imports wie `models` und `services`; keine isolierte Teilumstellung auf relative Imports.
- Bestehende SQLite-Dateien benötigen bei Schemaänderungen Migrationen; `create_all()` aktualisiert bestehende Tabellen nicht ausreichend.
- Externe Antworten, Zeitüberschreitungen und Wiederholungen werden am jeweiligen Integrationsvertrag geprüft. Der lokale Skill `.codex/skills/brick-manager-sync-contracts/SKILL.md` enthält den Arbeitsablauf.
- Eingaben, Dateipfade und URLs an der jeweiligen Grenze prüfen. Geheimnisse und interne Fehlerdetails gehören nicht in öffentliche Antworten.
- UI-Änderungen berücksichtigen Tastatur, Touch, Fokus und verständliche Lade-, Leer-, Fehler- und Erfolgszustände. Dies sind Änderungsanforderungen, keine Behauptung vollständiger vorhandener Barrierefreiheit.

Konfigurationsnamen und Pfade werden in der [Konfigurationsreferenz](../reference/configuration.md) gepflegt; dieses Dokument dupliziert deren Inventar nicht.

## Verifikation und Erweiterung

Route- und Modelltests nutzen möglichst die isolierte Flask-App in `brick_manager/tests/conftest.py`. Die Fixture-Datei isoliert zusätzlich Datenbankpfade für Legacy-Tests, die die Produktiv-App importieren. Das macht deren übrige Start-Seiteneffekte nicht automatisch unbedenklich. Netzwerk- und Dateigrenzen in Tests isolieren; beobachtbare Antworten, gespeicherte Zustände und erzeugte Artefakte prüfen.

Konkrete Befehle und Messwerte stehen in der [Testanleitung](../guides/testing.md) und der [Qualitätsreferenz](../reference/quality-tooling.md). Dieses Dokument enthält keine ungeprüften aktuellen Testzahlen.

Bei einer Erweiterung die betroffenen Produzenten und Verbraucher ermitteln, das Verhalten samt Fehlerpfaden implementieren und prüfen sowie passende Referenzen und das [Logbuch](../logbook.md) aktualisieren. Neue dauerhafte Entwurfsentscheidungen zusätzlich mit Grund und Folgen dokumentieren.

## Geplante Erweiterung

Der [Implementierungsplan für Lageransicht, Archivierung und Einlagerung](../plans/storage-archive-intake.md) beschreibt die vorgeschlagene Trennung von festen Orten, beweglichen Behältern und Aufstellungen sowie sichere Bewegungen und regelbasierte Vorschläge. Dieser Plan ist noch nicht umgesetzt; die hier beschriebene bestehende Architektur bleibt davon unberührt.
