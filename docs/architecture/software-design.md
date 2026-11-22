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

## Aufgabenbezogene Lageroberfläche

`routes/warehouse.py` rendert die Lagerseiten mit gemeinsamem Sitzungstoken,
Seitenschlüssel und Navigation. `/warehouse` enthält Übersicht und ausgewählte
Boxdetails. `/warehouse/intake`, `/warehouse/reorganize`, `/warehouse/box-types`,
`/warehouse/locations`, `/warehouse/capture` und `/warehouse/settings-page` rendern
nur ihre jeweiligen Arbeitsformulare. `static/js/warehouse.js` bleibt der gemeinsame
Controller für Optionen, sichere Textdarstellung, Fehler und API-Aufrufe; Bindungen
und zusätzliche Abfragen richten sich nach vorhandenen Seitenelementen.

Die Bestandserfassung ist von neuen Zugängen und bestätigten Bewegungen getrennt.
Ein Legacy-Inhalt wird über `/warehouse/capture?storage_id=<id>` zur Zuordnung
übergeben; stabile Einheitenlinks bleiben `/warehouse?unit_id=<id>`.
Bewegungsformulare zeigen nur die Felder ihrer Vorgangsart. Ausgeblendete Eingaben
sind deaktiviert und werden nicht als versteckte Altwerte übertragen.
Fachbeschriftung verwendet die bestehende Ortshierarchie und eine separate
Druckansicht im Browser; Boxetiketten verwenden weiterhin die bestehende
Etikettenerzeugung und Vormerkung. Es werden keine neuen Persistenzformate benötigt.

Die Regelansicht verwendet für Kategorien eine Namensauswahl. `GET /warehouse/settings`
liefert dafür additiv `categories` mit `id` und `name`; `category_rules` enthält
zusätzlich `category_name`. Auswahl und Übersicht zeigen Katalognamen, während
der bestehende Schreibvertrag weiterhin die numerische `category_id` verwendet.
Leere Kataloge sperren die Kategorieauswahl und das Speichern mit einem erklärenden
Hinweis. Fehlt die Kategorienliste in einer älteren Serverantwort, zeigt die
Oberfläche dagegen einen Lade-/Aktualisierungsfehler statt eines leeren Katalogs
oder einer Aufforderung zum Neuimport. Eine vollständige Antwort nach erneutem
Laden gibt die Auswahl wieder frei. Namen werden im Browser als Text behandelt;
fehlende Namensinformationen gelten nicht als Nachweis gelöschter Kategorien.

## Sammlungsstabilität und skalare Übersichten

### Setliste und eigener Arbeitsbereich

`/set_maintain` stellt die gefilterte und paginierte Sammlung dar. Echte Links
führen auf `/set_maintain/<user_set_id>/details`; die technische Identität bleibt
die physische Kopie, nicht die Katalognummer. Diese HTML-Route ergänzt den
bisherigen JSON-Endpunkt `/set_maintain/<user_set_id>`, dessen Antwortvertrag
erhalten bleibt. `set_maintenance_service.py:inventory_details` liefert das
gemeinsame Lesemodell mit gebündelten Katalogbild-/Lagerabfragen. Nur der
HTML-Arbeitsbereich ergänzt `unassigned_minifig_parts`: zur Kopie gehörende
Teile ohne passende Figur bleiben bearbeitbar, ohne die Figurenzuordnung zu
verändern oder den alten JSON-Vertrag zu erweitern.

Die neue Detailseite verwendet ein einheitliches explizites Speichern. Mengen,
Status und Sammelentwürfe werden gemeinsam an dieselbe kopienbezogene Route
gesendet. Die Felder `part_id_<id>` und `minifig_part_id_<id>` bleiben getrennt.
`apply_set_edits` löst alle Ziele innerhalb der Kopie auf und prüft vor einer
Zuweisung Ganzzahlen, Grenzen und Status. Leere Änderungen, unbekannte oder
mehrfach genannte Felder und fremde Inhalte werden abgewiesen. Die Route besitzt
Commit/Rollback. Die neuen strikten Bereichsfehler ersetzen nicht die weiter
kompatible Begrenzung in den alten Schreibverträgen.

Bei JavaScript-Saves bestätigt JSON die tatsächlich angenommenen Werte und den
Fortschritt. Der Controller aktualisiert den bestätigten Vergleichsstand,
überschreibt keine während der Anfrage neu bearbeiteten Werte und meldet nur
bei vollständig bestätigtem aktuellem Entwurf Erfolg. Nach verlorener Antwort
gelten betroffene Werte als ungewiss und werden bei Retry erneut explizit
gesendet. Ohne JavaScript führt ein erfolgreicher Formularsave mit 303 wieder
auf dieselbe Detailseite; Fehler rendern korrigierbare Eingaben an dieser Stelle.
Die einzelnen Speichervorgänge sind transaktional; konkurrierende unabhängige
Browser besitzen weiterhin keinen Versions-/Konfliktschutz.

`set_navigation_service.py` rekonstruiert den `return_to`-Kontext ausschließlich
für die lokale Setliste aus erlaubten, typisierten Parametern. Suchtext, Box,
Thema, Status, Inventar, Label, Gruppierung, Seitengröße, Seite und serverseitige
Sortierung bleiben erhalten. Sortierausdrücke sind fest vorgegeben; Teilmengen
werden über skalare Summen sortiert. Ungültige Rückziele werden nicht übernommen.
`returned_box` und ein stabiler Zeilenanker erlauben Fokus-/Positionswiederherstellung.
Die Liste erklärt nicht mehr vorhandene Treffer und korrigiert ungültig gewordene
Ergebnisseiten. Beim Browser-Zurück wird ein veralteter Listenstand neu abgefragt.
Browserlokale Scrollwerte und geöffnete Übersicht sind eine Ergänzung; ohne
Sitzungsspeicher bleibt die Rückkehr über Link und Zeilenanker nutzbar.

`set_detail.html`, `set_detail.js` und `set_detail.css` enthalten ausschließlich
den Arbeitsbereich der Kopie. Sammelaktionen und Mengenfilter verwenden die
fachliche Sollmenge des jeweiligen Eingabefelds statt Tabellenspaltennummern.
Das gilt auch für den kompatiblen alten Renderer. Ausgeblendete Mengen bleiben
Teil einer ausdrücklich bestätigten Sammelaktion. HTML-Tabellen scrollen auf
schmalen Bildschirmen innerhalb ihres Bereichs; beschriftete Mengenfelder,
Fehlertexte und normale Tab-Navigation erhalten den Tastaturzugriff.

### PDF-Setetiketten

`POST /set_maintain/generate_label` akzeptiert eine positive ganzzahlige `set_id`
(auch als Zeichenkette) und eines der unterstützten Formate als `box_size`.
Ungültige Eingaben liefern 400, fehlende Kopien 404, Erzeugungsfehler 500.
Erlaubte Formate sind `MB-1`, `MB-4` und `BIG-BOX`. Erfolg liefert ausschließlich
`application/pdf` als `<box_id>_<box_size>.pdf`.
Auf ausdrücklichen Nutzerwunsch ersetzt dieser Vertrag die frühere XML-Ausgabe;
deren Vorlagen und Ersetzungscode sind entfernt. Kein Konverter oder zusätzlicher
Exportprozess bleibt bestehen. `set_label_service.py` rendert mit ReportLab:
MB-1 als A4-Kreuz auf einer Seite, MB-4 mit Deckelmotiv und vier Seitenstreifen
auf zwei, Big Box auf drei A4-Querseiten. `BOX_DIMENSIONS_MM` enthält die vom
Nutzer genannten physischen Maße 160/110/50, 320/225/50 und 305/229/102 mm.
Etiketten berücksichtigen mindestens 5 mm Abstand pro Kante und das druckbare
A4-Limit 277 × 190 mm. Lange/kurze Seiten bleiben unterschieden; je nach Höhe
passen vier oder zwei Streifen auf eine Seite. Schnittmaße stehen in der
[Benutzeranleitung](../guides/user-guide.md#setetiketten-herunterladen).

Die Seitenbögen verwenden gemeinsame horizontale Schnittkanten ohne Stege:
Zeilenhöhe entspricht exakt der Etikettenhöhe, alle linken Kanten liegen bei
10 mm einschließlich kürzerer Streifen. Der gesamte Block ist vertikal zentriert.
Dadurch können Reihen und gleich breite Paare mit dem Papierschneider getrennt
werden, ohne zusätzliche Zwischenstreifen auszuschneiden. MB-1 behält sein bereits
anliegendes Kreuz; Etikettenmaße und PDF-Seitenzahlen ändern sich nicht.

Eingebettete Vera-Schriften stammen aus ReportLab, nicht dem Betriebssystem.
Namen werden als Text mit begrenztem Umbruch/Verkleinerung und nötigenfalls
Auslassungszeichen gezeichnet; Bilder behalten ihr Seitenverhältnis.
`PrintScaling=None` und ein Hinweis auf jeder Seite unterstützen 100-%-Druck.
Bildabrufe erlauben nur HTTPS zu `cdn.rebrickable.com`/`rebrickable.com`, ohne
Zugangsdaten, Sonderports oder Weiterleitungen. Connect-/Read-Timeout 3/10 Sekunden,
15-Sekunden-Streamprüfung, höchstens 8 MiB und 25 Millionen dekodierte Pixel;
PNG/JPEG/WebP werden auf maximal 2600 × 2600 Pixel reduziert und auf Weiß gelegt.
Ein URL-Hash adressiert den Cache unter `CACHE_FOLDER/set_labels/`; fehlerhafte
Einträge können neu geladen werden, Schreibfehler im optionalen Cache verhindern
den Druck nicht. Ohne Bild entsteht ein beschrifteter Platzhalter, angekündigt
über `X-Label-Warning` und sichtbare Browserrückmeldung.

Eine temporäre Datei in `OUTPUT_FOLDER` ersetzt das PDF-Ziel atomar;
fehlgeschlagene Ersetzungen erhalten die vorige Datei und entfernen temporäre Reste.

Die Route bereitet den Download vor und bestätigt erst dann den bestehenden
automatischen `label_printed`-Status. Fehler rollen die Datenbanktransaktion zurück;
eine bereits erzeugte Datei kann bei einem anschließenden Commitfehler bestehen
bleiben. Der Status ist kein Nachweis physischen Drucks. Der Browser zeigt
Fortschritt, Fehler und erneuten Versuch an der Zeile, hält den Listenkontext und
aktualisiert nach Erfolg Kontrollkästchen und Statusanzeige ohne Neuladen.

### Mengenidentität und Speicherung

`collection_quantity_service.py` behandelt die Identität einer Mengenzeile als
`(part_type, part_id)`: `regular` und `minifig` haben unabhängige ID-Räume.
Dashboard-Batches werden vollständig validiert und aufgelöst, bevor eine Menge
zugewiesen wird. Fehlende Ziele liefern 404, mehrdeutige untypisierte Altaufrufe
409 und doppelte/ungültige Ziele 400; der gesamte Batch bleibt dabei unverändert.
Die Route besitzt Commit/Rollback. Erfolgsantworten enthalten additiv `updates`
mit Typ, ID und tatsächlich gespeicherter (begrenzter) Menge. Eindeutige alte
Payloads ohne Typ bleiben gültig. Die Setpflege akzeptiert weiterhin ganzzahlige
Ziffernstrings, aber keine Booleans, Dezimalwerte oder unbekannten Typen.

`static/js/detail_quantities.js` ersetzt den alten jQuery-Inline-Autosave in den
Dashboarddetails. Delegierte Eingaben und eine Batch-Warteschlange erhalten die
neueste Eingabe, bestätigen konkrete Serverwerte und behalten Fehler bis zum
sichtbaren Retry. Der kompatible ältere Set-Renderer serialisiert analog pro
logischer Teilidentität; sein Formularabschluss wartet auf laufende Mengenänderungen und darf
nach einem Setwechsel kein anderes Formular absenden. Diese Warteschlangen lösen
keine gleichzeitigen Änderungen durch unabhängige Browser/Sitzungen; eine solche
Versionsprüfung bleibt ein eigenes Schema-/Vertragsthema.

`collection_summary_service.py:set_quantity_totals` berechnet pro paginierter
Setliste nur skalare Summen regulärer, Ersatz- und Minifigurenteilzeilen für die
sichtbaren Set-IDs. Es werden dafür keine Inventarobjekte geladen. Physische
Setkopien bleiben nach `user_set_id` getrennt, leere Sets ergeben null. Suchfilter
und dargestellte Zeilenthemen verwenden getrennte Variablen.

`backup_service.py` verwendet die vorhandene SQLite-Backup-API und den tatsächlichen
Engine-Pfad. Der geplante App-Wrapper beschafft diesen im App-Kontext und isoliert
Fehler weiterhin vom Scheduler. Gleichzeitige Sicherungen haben kollisionsfreie
Namen; Rotation erfolgt erst nach erfolgreicher Sicherung und ausschließlich für
eigene, ältere reguläre Backup-Dateien. Fremde/manuelle Dateien und Symlinks
werden nicht entfernt. In-memory- und Nicht-SQLite-Engines werden übersprungen.
App-Initialisierung und Schedulerkonfiguration wurden dabei nicht umgebaut.

Weitere bestätigte Altlasten und ihre noch nicht umgesetzten Prüfungen stehen im
[Verbesserungsplan](../plans/architecture-usability-improvements.md).
