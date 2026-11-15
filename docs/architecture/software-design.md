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

Der Ablauf verbindet HTTP-Eingaben, externe Daten, lokale Dateien und Darstellung. Änderungen an Lagerfeldern müssen deshalb neben Modellen auch die auf `PartStorage` basierenden Lookup-Funktionen, Formular-/JSON-Verbraucher und Cache-/Label-Verwendung prüfen. Das vollständige Schema bleibt ausschließlich in der [Datenbankreferenz](../reference/database-schema.md).

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

## Implementierte Lagerverwaltung

- `services/storage_service.py`: feste Orte, Behälter, Unterteilungen, initiale
  Ist-Aufstellung, Adressauflösung, explizite Bestandszählung und dreistufige
  Passprüfung (`fits`, `unknown`, `no_fit`). Einfache Alt-Schreibwege passieren eine
  gemeinsame Schutzprüfung; strukturierte bzw. mehrdeutige Zuordnungen erfordern
  die Lagerverwaltung.
- `services/storage_move_service.py`: idempotente Entwürfe, reservierte Pläne,
  Versions-/Geometriesnapshots und atomare Bestätigung. SQLite-Schreiblock vor
  Reservierungs-/Versionsprüfung verhindert konkurrierende Doppelbuchungen.
  Konservativ werden ganze beteiligte Einheiten und Zielaufstellungen reserviert.
  Quelle und Ziel addieren/subtrahieren nur physische Mengen; Setbesitz bleibt gleich.
- `services/part_history_service.py`: eindeutige echte Setvorkommen je Teil/Farbe
  über Inventarversionen, Ersatzteile, Figuren und Untersets; explizite unbekannte
  Jahre/Verknüpfungen und generationsgebundene Katalogabdeckung.
- `services/storage_suggestion_service.py`: Kategorieziele, eigene Planliste,
  Bedarfsstatus, Präferenzen und erklärte Archiv-/Aufnahmevorschläge. Historisch
  belastbare Daten bei unbekanntem Bedarf erlauben manuelle Prüfung, keine
  unbedingte Archivfreigabe.
- `routes/warehouse.py`, `templates/warehouse.html`, `static/js/warehouse.js`:
  CSRF-geschützte Browseroperationen, beschriftete DOM-Regalfront mit Listen- und
  Tastaturalternative, getrennte Planungs-/Bestätigungsaktionen und ID-basierte Labels.

Die Übersicht projiziert unstrukturierte `PartStorage`-Zeilen rein lesend in
Beschriftungsgruppen nach unverändertem Regal-/Fach-/Boxtext. Nur eine eindeutige
Regal-/Fachübereinstimmung erlaubt die Anzeige unter einem festen Fach; fehlende
oder mehrdeutige Adressen bleiben separat. Die Projektion erzeugt weder
`StorageUnit`-Identitäten noch Mengen oder Aufstellungen. Einzelne Inhaltszeilen
werden weiterhin ausschließlich über die bestehende bestätigte Zuordnung aufgelöst.
Unaufgelöste Altbelegung sperrt positive Stellflächen-/Passzusagen, auch bei
bekanntem Regal und unbekanntem Fach. Die Oberfläche begrenzt sichtbare Gruppen
und Inhaltszeilen und rendert Katalog-/Nutzerdaten als Text. Katalogbild-URLs
werden additiv mitgegeben; die Oberfläche akzeptiert ausschließlich HTTP(S),
lädt Bilder verzögert ohne Referrer und zeigt bei Ladefehlern ein Ersatzsymbol.
Die schematische Beschriftungsfront platziert aufsteigende Einträge spaltenweise
von unten nach oben; die wählbare Zeilenzahl ist reine Anzeige, kein Stapelnachweis.
Die DOM-/Tastaturreihenfolge bleibt numerisch aufsteigend. Die gemeinsame
`partIcon`-Darstellung wird auch in den Inhaltstabellen bestehender und bestätigter
Behälter verwendet; dadurch gelten Bildvalidierung und Ersatzsymbol dort ebenfalls.

Zählkorrekturen erhalten Begründung und Vorher-/Nachherwerte im Bewegungsjournal.
Unbekannte Altfarben können ausdrücklich identifiziert werden; bereits bekannte
Farbidentitäten werden nicht still überschrieben. Das Auflösen einer ursprünglichen
Zuordnung bestätigt deren Migrationsmapping und bewahrt die Rohbeschriftung.

Auflagenpositionen sind relativ zur jeweiligen Unterlage. Fachpositionen sind
relativ zum Fachboden. Die gemessene Freihöhe gilt konservativ über die volle
Tiefe. Stapelumschichtungen werden in physisch bestätigte Einzelschritte zerlegt;
das System verspricht keinen simultanen Flächentausch über noch belegte Ziele.
Eine leere Hülle bleibt eine belegte Basis, bis sie entfernt oder verlagert wird.

Importe veröffentlichen ihre Abdeckung erst nach geprüftem Gesamtabschluss. Ein
fehlerhafter/überlappender Lauf hinterlässt keine scheinbar gültige alte Abdeckung
für gemischte aktuelle Tabellen. Die eigene Planungsprüfung ist an Katalog und
Planliste gebunden und wird bei Änderungen ungültig.

Aktuelle Adressen kommen aus dem Aufstellungsmodell. Die Desktop-Lesefelder
bleiben erhalten und werden additiv um IDs/Mengen/Adressinformationen ergänzt.
Ein alter PUT auf strukturierte oder mehrdeutige Fundorte antwortet nach gültiger
Authentifizierung mit 409. Der Legacy-Lookup liefert alle Orte und nur bei genau
einem Treffer einen primären Ort. Druckdateien unterscheiden gleich beschriftete
Einheiten über ihre ID; Druckstatus erfordert eine gesonderte Bestätigung.

Schema und Upgrade: [Datenbankreferenz](../reference/database-schema.md).
Kriterien und Tests: [Lagerabnahme](../plans/storage-acceptance.md).

### Explizite Etikettenvormerkungen

`services/label_queue_service.py` speichert jede explizite Vormerkung separat als
nicht geheime JSON-Präferenz in `ConfigSettings` unter
`warehouse_label_request:<sha256>`. Der Schlüssel hasht das kanonische Ziel:
physische `unit_id` oder unveränderte Altfundorttexte. Einzelne Schlüssel vermeiden
verlorene Änderungen an einer gemeinsam gespeicherten Gesamtliste. Diese additive
Nutzung der vorhandenen Präferenztabelle benötigt keine Schemamigration und lässt
bestehende Druckstatuswerte unangetastet.

Die CSRF-geschützten `/warehouse/label-marks`-Operationen markieren, entfernen,
rendern und bestätigen. PDF und Bestätigung verwenden Generation und Fingerabdruck
der tatsächlichen Etiketteninformationen; Altgruppen enthalten zusätzlich ihre
Inhaltszeilen-IDs. Die Bestätigung prüft unter SQLite-Schreiblock alle Ziele vor
atomarem Statuswechsel und Entfernen der Vormerkungen. Veraltete Bestätigungen
liefern 409. Wiederholtes Bestätigen erzeugt keine weiteren Änderungen.

`static/js/label_marks.js` bindet den eigenständigen Vormerkungsbereich auf der
bestehenden Box-/Etikettenseite an. Alte manuelle Druckauswahlen behalten ihren
bisherigen Vertrag. Bilder werden in einer gebündelten Inventarabfrage je Übersicht
aufgelöst, damit fehlende Teile-Stammbilder nicht zu einzelnen Abfragen je Lagerzeile
führen. Exakte Farbe wird bevorzugt; bei unbekannter Farbe bleibt die Ersatzvorschau
als solche fachlich ungeprüft.

Die Lagerübersicht merkt sich das zuletzt ausgewählte einzelne Fach unter
`brick-manager.warehouse.last-shelf` im lokalen Browserspeicher. Beim initialen
Aufbau wird nur dieses oder das erste numerisch sortierte Fach gerendert. Gelöschte
IDs und gesperrter Browserspeicher fallen auf das erste Fach zurück; manuelles
„Alle Fächer“ gilt bis zum nächsten Seitenaufruf. Die Browser-Startabfrage verwendet zusätzlich den fachweisen Datenvertrag:
`/warehouse/data?view=focused&shelf_id=<id>` lädt katalogangereicherte Altinhalte
nur für das gewählte Fach. Ohne gültige ID wird das erste natürlich sortierte
Fach gewählt; `all=1` fordert die Gesamtansicht ausdrücklich an. Globale
Zähler stammen aus einer schlanken skalaren Projektion. Ungeklärte Gruppen
werden zunächst ohne Inhaltslisten übertragen und über
`/warehouse/contents/<id>/group` beim Öffnen geladen. Die globale Inhaltsauswahl
für Bearbeitungsformulare lädt `/warehouse/contents` erst bei Bedarf. Bestätigte
Einheiten und ihre Inhalte bleiben für Navigation und Umbuchung verfügbar.
Der bisherige vollständige `/warehouse/data`-Vertrag bleibt kompatibel.
Schnell folgende Fachwechsel verwenden eine Antwortgeneration; veraltete
Antworten überschreiben die aktuelle Auswahl nicht. Archivaktionen warten auf
den abgeschlossenen Fachwechsel.

Der additive Index `ix_inventory_part_color_image` auf
`rebrickable_inventory_parts(part_num, color_id, img_url)` deckt die gebündelte
Bildsuche ab und vermeidet den Scan der gesamten Inventartabelle. Die neue
Migration `20261115_warehouse_image_lookup.sql` erzeugt ausschließlich diesen
Index; angewendete frühere Migrationsartefakte bleiben unverändert.
