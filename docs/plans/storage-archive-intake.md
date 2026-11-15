# Implementierungsplan: Lageransicht, Archivierung und Einlagerung

Stand: 2026-11-15. Geprüfter Checkout: `845921b` einschließlich der vorhandenen lokalen Agenten-/Dokumentationsänderungen.

**Status: Umsetzung vorhanden; automatisierte Abnahme und Paketliste siehe [Abnahmeprotokoll](storage-acceptance.md).** Die Abschnitte zur Ist-Analyse dokumentieren den Ausgangsstand vor der Implementierung; Modell-/Ablaufabschnitte bleiben deren Arbeitsgrundlage. Die ursprüngliche Planungsphase endete ohne Codeänderung. Der anschließende Implementierungsauftrag autorisiert alle Pakete einschließlich automatisierter Verifikation an repräsentativen Testfächern. Ein echtes Pilotfach ist dafür keine Voraussetzung. Vor-Ort-Maße und physische Produktaussagen sind weiterhin gesondert zu prüfen. Aktuelle Referenzen beschreiben den implementierten Stand.

## 1. Ergebnis und Umfang

Die bestehende Anwendung kann Teile mehreren beschrifteten Fundorten zuordnen. Für das gewünschte Lager fehlen jedoch physische Behälteridentitäten, Aufstellungen/Stapel, Mengen je Lagerort, ein bestätigbarer Umlagerungsauftrag und verlässliche Daten über geplanten Bedarf und Katalogabdeckung.

Empfehlung: die vorhandenen Katalog- und Sammlungsmodelle weiterverwenden, `PartStorage` behutsam zu einer Inhalts-/Fundortzuordnung erweitern und feste Orte, bewegliche Einheiten sowie deren Aufstellung ergänzen. Eine Umlagerung verändert den aktuellen Fundort erst nach physischer Bestätigung. Vorschläge sind nachvollziehbare Regeln mit Unsicherheitsangaben; ein KI-Modell oder ein neuer externer Dienst ist dafür nicht erforderlich.

**Bestätigt am 2026-11-15:** Erstes Umsetzungspaket ist die Lagerstruktur mit Behältern, Stapeln und Mengen je Fundort einschließlich ihrer sicheren Migration und gemeinsamen Schreibgrenze (P0–P2). Darauf bauen Regalansicht, bestätigte Umbuchungen und Archivvorschläge auf. Die spätere Implementierung ist mit dem vollständigen Umsetzungsauftrag autorisiert.

**Regal 1, Fach 5 ist ausschließlich ein Dummy-Beispiel**, ebenso die illustrierten Boxnummern und Aufstellungen. Das tatsächliche Pilotfach legt der Nutzer später fest. Zunächst funktioniert die Ansicht schematisch mit unbekannten Maßen und manuell bestätigten Beziehungen. Bereits in Version 1 werden alte, seltene Teile bei belastbarer Set-Anzahl und belastbarem letztem Set-Jahr trotz unbekanntem Eigenbedarf zur **manuellen Archivprüfung** angezeigt: **„Eigenbedarf unbekannt · bitte prüfen“**. Der Nutzer entscheidet beim Aufräumen über Archivierung; daraus entsteht keine automatische Archivfreigabe. Bei der Teileaufnahme bleibt bei unbekanntem Eigenbedarf das Kategorieregal der Standard. Physisches Umräumen erfolgt immer durch den Nutzer.

## 2. Ist-Analyse mit Einstiegspunkten

Zeilennummern beziehen sich auf den untersuchten Stand; Symbole bleiben die maßgeblichen Einstiegspunkte.

| Bereich | Konkreter Befund und Quelle | Konsequenz für die Planung |
| --- | --- | --- |
| Teile, Farben, Kategorien | `brick_manager/models.py`: `RebrickableParts` ab Zeile 280, `RebrickableColors` ab 232, `RebrickablePartCategories` ab 208. Kategorie über `part_cat_id`, Variante/Farbe über exakte `part_num` und `color_id`. | Identitäten wiederverwenden; Farbe nicht aus einem beliebigen Teilebild ableiten. |
| Bestände in eigenen Sets | `User_Set` ab 58; `User_Parts` ab 120: erforderliche `quantity`, vorhandene `have_quantity`, Setbezug und `is_spare`. `UserMinifigurePart` ab 142 ebenfalls setgebunden. | Kein allgemeiner, mengenmäßig erfasster loser Bestand je Behälter. Setmengen sind keine Verteilung auf physische Orte. |
| Statussemantik | `USER_SET_STATUSES` ab 25 enthält keinen Planungsstatus. `routes/set_search.py:add_set` initialisiert Besitz abhängig vom Status; `services/dashboard_service.py:_quantity_totals` summiert Setzeilen, teilweise unter Ausschluss bestimmter Status. | Vorhandene Sets nicht in „geplante Sets“ umdeuten; aus Setzählern keine neue Lagergesamtmenge erzeugen. |
| Vorhandene Fundorte | `PartStorage` ab 173: stabile Zeilen-ID, Teilenummer, optionale Farbe, Textfelder `location`, `level`, `box`, Notizen und Druckstatus. `idx_part_location` ist kein eindeutiger Behälterschlüssel. | Mehrfachfundorte sind möglich, aber keine Stückzahlen, physischen Boxen, Maße, Stapel, Füllstände oder Archivzonen modelliert. |
| Manuelle Zuordnung | `routes/manual_entry.py:manual_entry` ab 30 erhält andere Orte; exakte Wiederholung wird anhand Teil/Ort/Farbe/Notiz erkannt. Regal/Fach/Box müssen dort numerisch sein. `validate_part` ab 162 liefert `storage_list`. | Mehrfachfundortliste wiederverwenden; beschriftete Orte künftig über IDs auswählen statt überall numerisch zu erzwingen. |
| Bestehende Boxansicht | `routes/box_maintenance.py:box_maintenance_page` rendert `templates/box_maintenance_new.html`; `static/js/box_maintenance_new.js` lädt Filter, Inhalte, Regal- und Fachübersichten. Gruppierung über Ort/Fach/Box, keine Geometrie. | Bestehende Navigation und Druckfunktionen weiterführen, grafische Aufstellung ergänzen. Inhaltszeilenzahl ist kein Stückbestand und kein Füllgrad. |
| Suche verliert Mehrfachfundorte | `routes/part_lookup.py:lookup_part`, Zeile 75, nimmt `.first()` pro Teilenummer. `services/part_lookup_service.py:load_part_lookup`, Zeilen 50–58, überschreibt Fundorte im Dictionary-Schlüssel `part_num`; Farbe und mehrere Orte gehen in dieser Projektion verloren. | Neue Suche benötigt alle bestätigten, farbbezogenen Zuordnungen mit stabilen Ziel-IDs. Legacy-Projektion nur als ausdrücklich eingeschränkte Kompatibilitätsschicht. |
| Alte Schreibwege | `routes/storage.py:add_to_storage`, `routes/part_location.py:save_locations`, `services/part_lookup_service.py:save_part_lookup`; außerdem `routes/set_maintain.py:update_part_location` und `routes/upload.py:save_storage_location` schreiben häufig den ersten Treffer pro Teil um. | Vor Pilotbetrieb alle Schreibwege koordinieren; kein Parallelbetrieb zweier widersprüchlicher Wahrheiten. |
| Desktop-Vertrag | `routes/client_api.py:get_part_storage` ab 97 liefert alle Orte, optional exakt farbgefiltert; `update_part_storage` ab 150 aktualisiert den ersten Ort für Teil/Farbe. | Lesefelder und Sortierung erhalten. Alter PUT ist keine mengen- oder behälterbezogene Umlagerung. Neue Operationen separat anbieten. |
| Etiketten | `routes/box_maintenance.py:get_label_queue`, `_box_label_info`, `confirm_label_sheet_printed`; Referenz ist bisher das Texttripel Ort/Fach/Box. Druckstatus sitzt auf Inhaltszeilen. | ID-basierte Auswahl ergänzen; bei doppelten Textetiketten keine gemeinsame Box erfinden. Vorhandene Beschriftung und Druckinformation erhalten. |
| Katalogvorkommen | `RebrickableSets` ab 394 enthält Setjahr; `RebrickableInventories` ab 463 Inventarversion und `set_num` als Text ohne FK; `RebrickableInventoryParts` ab 480 hat Schlüssel Inventar/Teil/Farbe/Ersatzteilflag. | Joins und distinct Setzählung sind möglich, aber fehlende Verknüpfungen müssen sichtbar bleiben. |
| Varianten und Unterinventare | `RebrickablePartRelationships` ab 326; `RebrickableInventorySets` ab 506 und `RebrickableInventoryMinifigs` ab 527. `routes/set_search.py:fetch_minifigure_parts` sucht Figureninventare über `fig_num` im Inventar-Setnummernfeld. | Varianten nicht still zusammenlegen. Figureninventar nicht als reguläres Set mitzählen; Unterinventare kontrolliert zu echten Elternsets auflösen. |
| Katalogimport | `routes/import_rebrickable_data.py:FILES`, `_run_import_job` und `import_csv_to_sqlite`: zwölf Dateien, Austausch transaktional je Tabelle; Fortschritt nur im Prozessspeicher. | Ein erfolgreicher Einzelimport belegt keinen konsistenten, vollständigen Gesamtsnapshot. Persistente Abdeckungs-/Generationsinformation fehlt. |
| Migration | `services/migration_service.py:apply_sqlite_migrations` führt SQL-Dateien bei jedem Lauf aus; `docker-entrypoint.sh`, Zeilen 55–57, ruft es vor dem Server auf. `migrations/20261023_add_collection_snapshots.sql` ist versioniert. | Keine Alembic-Infrastruktur voraussetzen. Wiederholung, atomarer Backfill und einmalige Schemaänderungen explizit unterstützen. |
| Vorhandene Tests | `test_storage_route_contracts.py`, `test_manual_entry_contracts.py`, `test_part_location_contracts.py`, `test_client_api.py`, `test_import_contracts.py`, `test_migration_service.py`, `test_dashboard_migration.py`. JS-Prüfung: `tests/js/quantity_navigation.cjs`. | Existierende Kontrakte als Ausgangspunkt lesen. Mockbasierter Lösch-/Lookup-Test beweist keine reale Mehrfachfundortkorrektheit. Neue Integrations- und UI-Fälle notwendig. |

### Belegte Lücken und Grenzen der Untersuchung

- Keine Modelle für Regale/Fächer als eigene Objekte, bewegliche Boxen, Magazin/Schubladen/Unterteilungen, Stapelbeziehungen, freie Stellfläche oder Dachschrägen.
- Keine Bestandsmenge pro `PartStorage`, keine Mengenreservierung, kein bestätigbarer Umräumauftrag und kein historisches Umlagerungsjournal.
- Keine explizite Kategorie-Standardzuordnung, kein strukturierter „Nachschub unwahrscheinlich“-Hinweis und keine eigene Liste geplanter Sets.
- Keine persistente Aussage, welche Kataloggeneration vollständig importiert oder für Archiventscheidungen geeignet ist. Globale Farbstatistiken `num_sets`, `y1`, `y2` beschreiben nicht eine bestimmte Teil/Farb-Kombination.
- Das Modell verlangt ein Setjahr, dennoch können fehlende Setzuordnungen, Legacy-Daten und unplausible Jahre die Ableitung unvollständig machen. Ein erfolgreicher Join darf solche Lücken nicht verschweigen.
- Keine echte Datenbank geöffnet: tatsächliche Bestandsgrößen, Duplikate, Fremdschlüssellücken, Katalogfrische und Regal-1/Fach-5-Inhalte sind noch nicht erhoben. Die Lücken 3/4/7/9 und die volle Box 6 sind das gewünschte Planungsszenario, kein gemessener Ist-Befund.

## 3. Fachliche Begriffe und unverzichtbare Regeln

1. **Fester Ort:** Lagerzone → Regal → Fach. Beschriftungen bleiben frei gewählte Texte. Archiv ist eine Zone, kein Löschen von Bestand.
2. **Bewegliche Einheit:** Box, Becher oder Magazin mit stabiler ID und nicht eindeutiger sichtbarer Etikettnummer. Eine Schublade gehört zu einem Magazin; eine Unterteilung gehört zu genau einer Schublade.
3. **Aufstellung:** Einheit steht auf einem Fachboden oder auf einer anderen Einheit. Darin liegen Reihenfolge, Auflageart und gegebenenfalls gemessene Position. Die Etikettnummer ist keine Stapelposition.
4. **Inhalt:** Teil/Farbe am konkreten adressierbaren Lagerbehälter, an einer ganzen Schublade oder an einer Unterteilung; Menge bekannt oder explizit unbekannt. Unterschiedliche Teilarten und Farben dürfen einen Behälter teilen.
5. **Plan versus Ist:** Vorschlag und geplanter Zielort ändern den bestätigten Fundort nicht. Erst „Physisch umgeräumt – bestätigen“ bucht eine Bewegung. Auch das bloße Annehmen eines Vorschlags ist keine Bestätigung.
6. **Unbekannt ist kein Nullwert:** Unbekannte Farbe, Menge, Geometrie, Historie oder Bedarf werden nicht zu „leer“, „passt“, „kein Bedarf“ oder „selten“ umgedeutet.
7. **Getrennte Mengenbegriffe:** Setbezogenes `have_quantity` und physische Lagermenge werden getrennt angezeigt. Umlagern ändert keinen Setbesitz. Ein neuer physischer Lagerzählwert wird nicht zusätzlich zu Setmengen als Gesamtbesitz summiert.

## 4. Kleinstes konsistentes Zielmodell

Alle Namen und Felder in diesem Abschnitt sind **Vorschläge**. Bestehende Rebrickable- und Settabellen bleiben die fachliche Basis. Kein paralleler Teilekatalog, kein zusätzliches Stack-Objekt mit eigener Nummerierung, kein allgemeines CAD-/Warenwirtschaftssystem.

### 4.1 Feste Orte, Einheiten und Aufstellung

| Modell | Wesentliche Felder und Bedeutung |
| --- | --- |
| `StorageLocation` | `id`, `parent_id`, `kind` (`zone`, `rack`, `shelf`, `unresolved`), `label`, `sort_order`, `revision`; optionale nutzbare Breite/Tiefe und stückweise lineares Höhenprofil `[(x_mm, h_mm)]`, Messstatus/-datum. Archiv/Aktiv über Zone. |
| `ContainerType` | `id`, Name, Art, äußere Breite/Tiefe/Höhe jeweils nullable, Maßequelle/-status, Zugriffsart (`front_open`, `remove_above`, `drawer`, `unknown`), ggf. obere Auflagefläche und bestätigte Last-/Höhengrenzen. Behältervolumen ist keine Stückkapazität. |
| `StorageUnit` | `id`, `type_id`, `kind` (`container`, `cabinet`, `drawer`, `compartment`), unverändertes `label`, optional `host_unit_id` für Schublade/Unterteilung, `ordinal`, `partition_count` nur für Schubladen, `fill_state` (`space`, `nearly_full`, `full`, `unknown`), `contents_complete`, `revision`. Einzelne Maße/Zugriffseigenschaften bei Bedarf am Exemplar überschreibbar. |
| `StoragePlacement` | `unit_id` als eindeutiger Schlüssel, entweder `shelf_id` oder `support_unit_id`, `relation_kind` (`on_shelf`, `stacked`, `loose_on`), `order_left`, optional gemessene `x_mm`, `depth_offset_mm`, `orientation`, `revision`, ggf. verwendete Regel-ID. Aufstellungsort wird entlang der Auflagekette aufgelöst. |
| `StackRule` | Gerichtetes Paar unterer/oberer Typ, Beziehung `stacked` oder `loose_on`, Verifikationsstatus/-quelle/-datum und nullable bestätigte Stapelhöhenzunahme, Maximalzahl/-höhe, Auflage-/Lastgrenzen. Unbestätigte Regeln erzeugen keine automatische Passzusage. |

Schubladen und Unterteilungen hängen über `host_unit_id` am Magazin bzw. an der Schublade und erhalten keine eigene externe Aufstellung. Nur äußere Einheiten stehen auf einer Fläche. Ganze Schublade **oder** zwei/drei aktive Unterteilungen: keine gleichzeitige doppelte Inhaltsführung. Änderungen der Unterteilung erfordern eine bestätigte Inhaltsverteilung; belegte Unterteilungen nicht löschen. Stabile IDs bleiben für Historie erhalten, nicht mehr verwendete Unterteilungen werden stillgelegt.

Jede äußere Einheit hat höchstens eine aktuelle Aufstellung. Ein Fach darf viele Einheiten nebeneinander tragen, ein Magazin mehrere separat positionierte Auflagen. Ein Stapel ist die abgeleitete Auflagekette; als UI-Referenz dient die ID seiner Basiseinheit. Seiten-an-Seite-Auflagen auf einem Magazin sind nicht automatisch ein einziger Stapel. Container/Support-Schleifen und Host-Schleifen werden verhindert; Löschungen belegter/unterstützender Einheiten sind gesperrt (`RESTRICT`). Eine Kette endet an einem Fach oder als ausdrücklich ungeklärter Standort. Kein automatisches Umnummerieren nach Entfernen einer Box.

### 4.2 Inhalt und vorhandene Fundorte

`PartStorage` bleibt die Inhalts-/Fundortzuordnung mit unveränderten IDs, `part_num`, optionaler `color_id`, Notizen und ursprünglichem Druckstatus. Additiv:

- `storage_unit_id` nullable: konkrete Box, ganze Schublade oder Unterteilung;
- `quantity` nullable, bei bekanntem Wert nicht negativ; `NULL` bedeutet „nicht gezählt“, nicht „0“;
- `revision` für konkurrierende Änderungen sowie Herkunft/Abgleichstatus für die Migration.

Die alten Texte `location`, `level`, `box` bleiben zunächst unverändert als Legacy-Referenz. Für neu bestätigte physische Einheiten entsteht die aktuelle Adresse aus dem Orts-/Aufstellungsmodell. Ein zentraler Adapter liefert alten Lesern weiterhin die bisherigen Feldnamen; keine unabhängigen Live-Schreibkopien der Adresse in allen Inhaltszeilen. Der originale Druckstatus wird nicht verworfen; neue, ID-basierte Druckbestätigungen werden nach Etikettenart an der Einheit geführt. Alte Textreferenzen bleiben nur eindeutig auflösbar verwendbar.

Mehrere bestehende Zeilen werden beim Backfill nicht verschmolzen, auch nicht bei gleichen Texten. Im neuen Mengenworkflow passende bekannte Inhaltszeilen am Ziel kontrolliert addieren. Bei unbekannter Farbe oder Menge keine automatische Zusammenfassung oder Teilumbuchung; zuerst zählen/identifizieren. Eine bekannte Nullmenge kann als leere Zuordnung erhalten bleiben, zählt aber nicht als vorhandener Inhalt. `contents_complete` bestätigt zusätzlich, dass keine unerfassten Inhalte im Behälter liegen.

### 4.3 Planung, Bedarf und Nachvollziehbarkeit

| Modell bzw. vorhandener Mechanismus | Kleinste benötigte Ergänzung |
| --- | --- |
| `StorageMove` | ID, Status (`draft`, `planned`, `confirmed`, `cancelled`), Art (`unit`, `quantity`, `intake`), eindeutiger Idempotenzschlüssel, Begründung, Zeitstempel, Quell-/Zielrevisionen und unveränderlicher Bestätigungssnapshot. |
| `StorageMoveItem` | Move-ID, konkrete Einheit oder Inhaltszeile, Menge bei Teilbewegung, Quelladresse/Quellrevision und Ziel-Einheit/-Aufstellung. Mehrere Schritte für Behälterwechsel/Umräumen; Reihenfolge und Abhängigkeiten festhalten. |
| `CategoryStorageRule` | Kategorie-ID → fester Standardort, vorzugsweise Regal-ID; optional Priorität und Archivziel. Ein Regal-Standard verspricht noch keine freie Box. |
| `PartStoragePreference` | Exaktes Paar Teil/Farbe und nullable manuelle Markierung `replenishment_unlikely`, optional „griffbereit halten“. Keine automatische Ersetzung der Kataloghistorie. |
| `PlannedSet` | Eigene ID, Katalog-`set_num`, gewünschte Anzahl, aktiv/inaktiv, Revision. Unabhängig von `User_Set` und dessen Besitzstatus. |
| `CatalogGeneration` | Import-ID, begonnener/beendeter Lauf, Gesamtstatus, je erforderlicher Datei Abschluss/Zeilenzahl/Quellnachweis, Validierungsfehler, abgeleitete Auswertungsrevision. Alte Bestände werden nicht allein durch vorhandene Zeilen als vollständig markiert. |
| `ConfigSettings` | Versionierte, validierte Regelwerte: maximal bekannte Sets (Start 2), Mindestalter (Start 10 Jahre), Frischegrenze des Katalogs, Planungsabdeckung (`unknown`/`reviewed`) mit Datum/Revision. Kategoriezuordnungen bleiben relational. Keine Tokens in Regelantworten ausgeben. |

Für Einstellungen mit nullable Farbe getrennte eindeutige Indizes für „Farbe bekannt“ und „Farbe unbekannt“ einsetzen; SQLite-NULL-Semantik nicht versehentlich als Eindeutigkeit behandeln. Teil/Farbe-Statistiken zunächst berechnen bzw. generationsgebunden cachen, keine dauerhaft unabhängig editierbare zweite Wahrheit anlegen. Eine Zwischenrelation für eindeutige Vorkommen kann später als neu aufbaubare Performanceoptimierung materialisiert werden.

Das sind die kleinsten Verantwortlichkeiten für alle angefragten Abläufe. Der Pilot muss nicht alle Oberflächen gleichzeitig erhalten: Orts-/Einheiten-/Inhaltsmodell und sichere Bewegungen zuerst, regelbasierte Vorschläge danach. `PlannedSet` bzw. eine explizit geprüfte Bedarfsabdeckung ist Voraussetzung für eine bedarfsgeprüfte Archivqualifikation. Die V1-Liste zur manuellen Archivprüfung bei unbekanntem Eigenbedarf benötigt belastbare Katalogdaten, aber keine fertig implementierte Planliste; ebenso wenig die schematische Regalansicht.

## 5. Migration und Kompatibilität

### 5.1 Vorbereitung und additive Einführung

1. Im späteren Implementierungsauftrag einen read-only Vorabbericht für eine ausdrücklich gewählte Datenbank vorsehen: bestehende Schemaversion, Anzahl `PartStorage`, Null-/Leerwerte, Farbkonflikte, exakte Texttripel, Duplikate und Fremdschlüsselverletzungen. Hier wurde dieser Bericht noch nicht ausgeführt.
2. Vor der tatsächlichen Migration SQLite-sichere Sicherung erstellen und Wiederherstellung an einer isolierten Kopie prüfen. Keine automatische Live-Wiederherstellung. Alt-/Neuschema-Fixtures für Tests vorbereiten.
3. Versionierte, additive Migrationen unter `brick_manager/migrations/` ergänzen. Neue Tabellen mit Checks/Indizes, bestehende Tabellen nur um nullable Felder bzw. sichere Defaults erweitern. Keine Katalog-/Setdaten löschen, neu zuweisen oder mengenmäßig normalisieren.
4. Der heutige Runner wiederholt SQL-Dateien und hat kein Versionsjournal. Vor `ALTER TABLE` ein kleines Migrationsjournal mit Version/Prüfsumme und atomarer Ausführung je Migration ergänzen. Bestehende idempotente Snapshot-Migration bleibt unterstützt. Keine Behauptung eines gemeinsamen Rollbacks über mehrere `executescript`-Aufrufe; Transaktionsgrenzen für Schema plus Backfill ausdrücklich testen. Bei neuer FK-Verletzung abbrechen; bekannte Legacy-Verletzungen vor/nachher differenzieren und erhalten.
5. Datenabhängigen Backfill als versionierten Schritt in derselben kontrollierten Migrationstransaktion ausführen; keine Import-Nebenwirkung von `app.py`. SQL-only und Python-Schritte über denselben Migrationsstatus koordinieren. Erfolg erst nach Invariantenprüfung journalisieren; unterbrochene Schritte müssen zurückrollen oder eindeutig fortsetzbar sein. Anwendung darf nicht auf ein halb migriertes Schema starten. CLI-/lokalen Startpfad zusätzlich zum Docker-Entrypoint dokumentieren.

### 5.2 Bestehende Beschriftungen und unbekannte Orte

- `PartStorage.id`, Rohtexte einschließlich Leerzeichen/führender Nullen, Farben, Notizen und Druckstatus erhalten. `quantity=NULL`, kein Ableiten aus `User_Parts.have_quantity`. Vorher-/Nachhervergleich zeigt unveränderte Set- und Bestandszeilen.
- Aus vollständigen Texten Kandidaten für Regal und Fach erzeugen, aber keine numerische Normalisierung (`01` ist nicht automatisch `1`). Interne IDs sind unabhängig von Texten. Mehrdeutige Beschriftungen werden als Klärungsfall dargestellt.
- Aus einem Texttripel kann lediglich ein **vorläufiger Behälterkandidat** entstehen. Zeilen desselben Tripels bleiben einzeln erhalten; ein gemeinsamer Kandidat gilt erst nach physischer Zuordnung als eine Box. Wiederholte Etiketten im selben Fach können mehrere Einheiten bezeichnen. Für solche Fälle bietet der Backfill eine aufzuteilende Kandidatengruppe statt stiller physischer Gleichsetzung.
- Für unvollständige/mehrdeutige Fundorte die ursprüngliche Zuordnung ohne `storage_unit_id` erhalten, als „Fundort ungeklärt“ anbieten und vorhandene Teiladresse anzeigen. Kein erfundenes „Regal 0“ und keine künstliche Stückzahl.
- Aufteilungs-/Zusammenführungsentscheidungen werden pro Legacy-Zeilen-ID protokolliert. Eine ergänzende Backfill-Mappingtabelle oder ein Migrationsmanifest macht Wiederholung und Rückverfolgung eindeutig; die Zeilen-ID selbst wird nicht ersetzt.
- Physische Erfassung im Pilot verifiziert Behälter, Inhalte, Farben, Mengen und Aufstellung. Nur gezählte/zugeordnete Daten werden für Mengenumbuchung freigeschaltet. Etiketten 3/4/7/9 nach Auslagerung nicht schließen oder neu vergeben.

### 5.3 Alle Schreibwege vor dem Pilot absichern

Ein gemeinsamer `storage_service` wird einzige fachliche Schreibgrenze. Bestehende Endpunkte bleiben soweit eindeutig kompatibel; sie rufen den Service auf. Legacy-Anfragen ohne konkrete Zuordnungs-/Einheiten-ID dürfen nur eindeutig unstrukturierte Altzuordnungen aktualisieren. Bei mehreren Kandidaten oder bereits strukturierter Aufstellung: `409` mit Auswahlhinweis bzw. Übergang zum neuen Bestätigungsdialog, kein beliebiges `.first()`.

Das betrifft insbesondere `manual_entry`, `storage`, `part_location`, `set_maintain`, `upload`, `box_maintenance`, `client_api` und `save_part_lookup`. Die bisherige „ersten Treffer aktualisieren“-Semantik des Desktop-PUT ist daher im mehrdeutigen Fall eine notwendige, ausdrücklich zu dokumentierende Verhaltensänderung. Lesepayloads bleiben erhalten, neue ID-/Unsicherheitsfelder werden additiv eingeführt. Mit dem Desktop-Client abstimmen und Kontrakttests aktualisieren; keine unbemerkte Versionsänderung.

`load_part_lookup` bleibt höchstens ein Legacy-Adapter; neue Verbraucher verwenden eine Liste nach Teil/Farbe und Zuordnungs-ID. Alle Mutationen invalidieren betroffene Lookup-/Ansichts-Caches nach Commit. Die heutigen Löschwege nicht als Implementierung einer Mengenbewegung verwenden. Alte Löschanfragen an belegte oder strukturierte Daten sperren bzw. in einen expliziten Korrekturablauf führen. Kein Kaskadenlöschen von Sammlungseinträgen über Behälter.

### 5.4 Abnahme und Rückweg

Auf isolierter Altbestandskopie: Migration zweimal ausführen, Unterbrechung simulieren, Rohdaten/IDs vergleichen, neue Constraints und SQLAlchemy-Lese-/Schreibzugriffe prüfen. Bekannte FK-Lücken dürfen nicht als neue Migrationsschäden ausgegeben oder „reparierend“ gelöscht werden. Vor dem ersten Schreibbetrieb kann die UI per Feature-Schalter auf Altansichten zurückfallen. Nach neuen Aufstellungs-/Mengenbuchungen ist ein altes Programm keine sichere Schreibalternative: neue Schreibwege sperren, additive Daten erhalten und vorwärts korrigieren. Eine Sicherung zurückspielen würde jüngere physische Buchungen verlieren und erfordert getrennte Freigabe sowie Abgleich.

## 6. Physische Regeln und Passprüfung

### 6.1 Anfangskatalog aus dem Auftrag

| Typ | Übernommene Vorgabe | Im System zu bestätigende Grenze |
| --- | --- | --- |
| HMH XS | 90 × 102 × 50 mm; nur gleiche Größe stapeln | Außenmaßreihenfolge/Orientierung, nutzbare Auflage, effektive Stapelhöhe und Maximalhöhe/-last |
| HMH S | 161 × 105 × 75 mm; nur gleiche Größe stapeln | Wie XS; keine Freigabe XS auf S bzw. umgekehrt |
| HMH Größe 3 | 248 × 145 × 127 mm; nur gleiche Größe stapeln | Wie XS; offene Front kann bei Stapelung erreichbar bleiben |
| Feinkostbecher 125/250/500 ml | Stapelbar | Typgleiche Grundbeziehung aus Auftrag erfassen; tatsächliche Deckel-/Becherform, gemischte Kombinationen, Höhenzunahme und zulässige Gesamthöhe vor Ort bestätigen |
| CYEER 750 ml | Andere Einheit kann lose darauf stehen | `loose_on`, kein eingerasteter Stapel; konkrete Paarung, sichere Auflage, Last und Stabilität prüfen |
| Transparenter Deckelbehälter | Zugriff kann das Abnehmen oberer Einheiten erfordern | Zugriff je Typ/Exemplar bestätigen; „transparent“ beweist weder freie Zugänglichkeit noch Stapelkompatibilität |
| STANLEY 1-93-980 | Magazin mit 30 kleinen Schubladen | Anzahl aus Auftrag; Zeilen/Spalten, Außen-/Schubladenmaße und obere Tragfläche vor Ort bestätigen |
| STANLEY 1-93-978 | Magazin mit 9 großen Schubladen | Wie oben; ganze Schublade oder zwei/drei adressierbare Unterteilungen |

Quellenstatus unterscheiden: `auftrag`, `produktangabe`, `gemessen`, `vor_ort_bestaetigt`. Eine bekannte Maßeangabe bestätigt nicht automatisch eine Kombination oder die zulässige Belastung. HMH-Typgleichheit ist eine notwendige Bedingung, aber keine pauschale Freigabe beliebig hoher Stapel. Unbestätigte bestehende Aufstellungen dürfen als Beobachtung erfasst werden, werden jedoch als ungeprüft gekennzeichnet und nicht als sichere Vorlage für automatische Vorschläge verwendet.

### 6.2 Layout, Schräge und Zugriff

- Zuerst eine **schematische Frontansicht** mit Fachgrenzen, links-nach-rechts-Reihenfolge und unteren/oberen Einheiten. Sichtbar „schematisch – Passung ungeprüft“. Unbekannte Breiten nicht durch Pixelabstände in angebliche Millimeter verwandeln.
- Gemessener Modus: nutzbare Fachbreite/-tiefe, linksbezogene Position und Orientierung der Basis, Typ-/Exemplarmaße und obere Freihöhe erfassen. Unter Dachschrägen das Höhenprofil über der gesamten Standbreite prüfen; die Höhe nur am Mittelpunkt reicht nicht. Bei Tiefenabhängigkeit der Schräge ist ein zusätzliches Tiefenprofil bzw. eine konservative gemessene Mindesthöhe erforderlich, sonst Ergebnis unbekannt.
- Einrasten/Überlappung über bestätigte Höhenzunahme pro Kombination berechnen; nicht einfach alle Außenhöhen addieren. Fehlt diese, nur konservative Schranke kennzeichnen oder Passung offenlassen. Bedien-/Entnahmefreiraum zusätzlich zur reinen Außenmaßpassung berücksichtigen.
- Frontoffene HMH-Box: Inhalt kann bei oberer Box erreichbar sein; physisches Entfernen der unteren Box kann dennoch ein Abnehmen der oberen erfordern. Deckelbehälter: Zugriffspfad zeigt die abzunehmenden Einheiten in Reihenfolge oben nach unten.
- Schublade: Zugriff nach vorne; Auszug und mögliche Blockierung zeigen. Auflagen auf einem Magazin haben eigene Beziehungen; keine automatische „rastet ein“-Annahme.
- Tiefe Ketten vollständig und zyklensicher laden; UI darf einklappen, aber keine oberen Einheiten ausblenden, die Zugriff oder Bewegung blockieren. Hintereinander stehende Behälter im Pilot nur mit ausdrücklich erfasster Tiefe; bei unbekannter Tiefe keine bestätigte freie Fläche.

### 6.3 Was ein Aufräumvorschlag tatsächlich freimacht

Für jede Variante die Änderungen getrennt ausweisen:

1. **Inhalt wird weniger / Behälter leer:** Eine reine Teileumbuchung entfernt die leere Hülle noch nicht aus dem Fach.
2. **Stapel wird niedriger:** Entfernen einer oberen Einheit kann Höhe freigeben, seine Grundfläche bleibt belegt.
3. **Grundfläche frei:** Erst Entfernen aller Einheiten auf einer Basis bzw. ihrer bestätigten Umstellung gibt deren Stellfläche frei. Eine untere Box mit verbleibender Auflage kann nicht einfach verschwinden.
4. **Zusammenhängende freie Fläche:** Gemessene freie Intervalle nur bei kompatibler Tiefe und lokalem Höhenprofil vereinigen. Getrennte Lücken sind keine zusammenhängende breite Stellfläche. Ein weiteres Umstellen zum Zusammenziehen der Lücken ist eine eigene geplante Bewegung.

Beispiel 3/4/7/9 → Archiv und größere Box für volle 6: zunächst Inhalte jeder Box prüfen, dann konkrete Archivziele, Auflageabhängigkeiten und belegte Basispositionen. Nur wenn die frei werdenden Positionen nach allen geplanten Schritten zusammenpassen, lautet das Ergebnis „größerer Behälter passt“. Sonst „Boxen vorgeschlagen; zusammenhängende Stellfläche/Passung noch zu prüfen“. Das Szenario darf mit anderer tatsächlicher Belegung zu einem anderen Ergebnis führen.

## 7. Bestandsbewahrende Bewegungen

### 7.1 Planung und Bestätigung

`draft → planned → confirmed`, daneben `draft/planned → cancelled`. Vorschau zeigt Ist- und Zielpfad, Inhalte/Mengen, Blocker, benötigte Zwischenablage und Auswirkungen auf freie Fläche. Der aktuelle Suchfundort bleibt bis zur Bestätigung unverändert; eine gesonderte Markierung nennt den geplanten Zielort.

Planung reserviert Quellmenge und eindeutig vergebene Aufstellungsposition logisch gegenüber anderen aktiven Plänen. Reservierungen werden serverseitig innerhalb derselben Transaktion geprüft; bloßes Prüfen im Browser reicht nicht. Keine datenbankweite Sperre über die Zeit des physischen Umräumens halten. Entwürfe reservieren noch nichts. Abbruch gibt Reservierungen frei; bestätigte Bewegungen werden nicht gelöscht.

Bei Bestätigung: kurze Schreibtransaktion (für SQLite frühzeitiger Schreiblock oder äquivalenter atomarer Versionsvergleich), aktuellen Planstatus, Quell-/Zielrevisionen, Mengen, Auflagen und konkurrierende Reservierungen erneut prüfen, dann alle abhängigen Zeilen und Journal atomar ändern. Auch zwei unterschiedliche Pläne gegen dieselbe Menge dürfen nicht beide bestätigen. Idempotenzschlüssel eindeutig: wiederholte Bestätigung liefert dasselbe Ergebnis ohne zweite Buchung; gleicher Schlüssel mit anderem Inhalt wird abgewiesen. Nach erfolgreichem Commit Lookup/Ansicht neu laden. Veralteter Plan → `409` und erneute Prüfung, keine stille Neuinterpretation.

### 7.2 Bewegungsarten und Invarianten

| Aktion | Bestands- und Platzregel |
| --- | --- |
| Ganze Box samt Inhalt | `StorageUnit.id` und Inhaltszeilen bleiben gleich; nur Aufstellung ändert sich. Alle Inhalte folgen der Einheit. Aufliegende Einheiten müssen ausdrücklich mitbewegt oder vorher abgenommen und neu platziert werden. |
| Magazin verschieben | Schubladen/Unterteilungen folgen als feste Kinder; auf dem Magazin stehende Behälter folgen nicht ungefragt. Ihre sicheren Zwischenschritte/Bewegungen müssen Bestandteil des Plans sein. |
| Teilmenge q umbuchen | Konkrete Quelle mit bekannter Farbe/Menge; `0 < q ≤ verfügbar`. Quelle minus q, Ziel plus q in einer Transaktion. Ziel muss aufnahmefähig sein. Summe aller bekannten physischen Mengen für Teil/Farbe vorher = nachher; Setmengen unverändert. |
| Bereits passender Zielbestand | Bekannte gleiche Teil/Farb-Zuordnung am Ziel addieren; gemischte Typen/Farben als getrennte Inhaltszeilen behalten. Unbekannte vorhandene Menge erst abgleichen. Nicht überschreiben. |
| Größerer Behälter | Leere Zielbox erfassen und auf freie/geplant frei werdende Position stellen, Inhalte vollständig/teilweise umbuchen. Alte Box als leer markieren; ihre Entfernung ist ein eigener Schritt. Zielbehälter kann erst nach dem Freiräumen des Platzes stehen. |
| Zweiter Lagerort | Neue/weitere konkrete Zielzuordnung anlegen. Ursprung mit Restmenge erhalten, Suche zeigt beide. Kein „Hauptort“ darf den zweiten unsichtbar machen. |
| Teileaufnahme | Neue physische Menge erst nach Identifikation und Bestätigung als Zugang buchen, nicht als wertneutrale Umlagerung. Wiederholte Aufnahmebestätigung mit gleichem Schlüssel erzeugt keinen doppelten Zugang. |

Füllzustände sind manuell beobachtete Kategorien, keine berechnete Volumen-/Stückgarantie. `full` sperrt reguläre weitere Aufnahme; `nearly_full` bzw. `unknown` erfordern eine bestätigte Kapazitätsprüfung. Eine Nutzerübersteuerung darf fachliche Rangfolge ändern, aber keine negativen Mengen, Doppelbelegung, verbotenen Stapel oder erfundene Geometrie erzwingen. Wenn ein Vorschlag physisch ungeprüft ist, lautet die Bestätigung „vor Ort geprüft“, nicht „systemseitig passend“.

Mehrschrittige Fachumräumung nicht pauschal nach dem ersten Schritt bestätigen. Pro physisch ausgeführter atomarer Bewegung bestätigen, den restlichen Plan auf neuen Revisionen fortschreiben. Unterbrechung zeigt die bereits tatsächlichen Bewegungen und verbleibenden Schritte. Umkehrung einer bestätigten Bewegung ist ein neuer Gegenauftrag; niemals rückwirkend historischen Ist-Zustand editieren. Eine Zählkorrektur benötigt ebenfalls einen eigenen begründeten Vorgang.

## 8. Kataloghistorie, Bedarf und Vorschlagslogik

### 8.1 Historische Vorkommen pro Teil und Farbe

Die Auswertung verwendet exakte `(part_num, color_id)`; ein farbloser Altbestand bekommt keine ausgedachte Farbstatistik. Ablauf:

1. Positive `RebrickableInventoryParts`-Zeilen an ihr Inventar binden. Direkte Setzuordnung über `RebrickableInventories.set_num → RebrickableSets.set_num`; nicht die Mengen oder Inventar-IDs zählen.
2. Vorkommensrelation `(part_num, color_id, echtes_set_num)` bilden. **Alle Inventarversionen vereinigen**: ein Teil, das in irgendeiner bekannten Version vorkommt, ist historisch bekannt. `DISTINCT` auf dieser Relation verhindert Doppelzählung durch Versionsstände, Menge und Ersatzteilflag.
3. Normale und Ersatzteilvorkommen berücksichtigen, zusätzlich `regular`/`spare_only` kennzeichnen. Ein Set mit beiden zählt einmal. So wird ein Teil nicht nur wegen weggefilterter Ersatzteile künstlich selten. Die Filterentscheidung bleibt im Ergebnis sichtbar.
4. Figureninventare über `RebrickableInventoryMinifigs` zu echten Elternsets auflösen; Figuren-ID selbst zählt nicht als Set. Verschachtelte Sets über `RebrickableInventorySets` mit Zyklenerkennung/Memoisierung auflösen. Direkt und indirekt gefundene Elternsets erneut deduplizieren. Vorkommen in Unterset und eigenständigem Set sind unterschiedliche echte Setnummern; beide zählen einmal, Mengenmultiplikation erhöht die Zahl nicht.
5. Verwaiste Inventare, fehlende Figuren-/Untersetinventare oder unauflösbare Eltern markieren. Im ersten Inkrement darf die Statistik nur direkte Vorkommen zeigen, dann aber als **unvollständig** und ohne automatische Archivqualifikation. Keine scheinbar vollständige niedrige Zahl aus einem inneren Join.
6. Für die eindeutigen echten Sets `COUNT(DISTINCT set_num)` sowie `MIN(year)`/`MAX(year)` über gültige bekannte Jahre bilden. Fehlende/unplausible Jahre separat zählen. Ohne gültiges Jahr `NULL`. Bei Teilabdeckung beobachtete Jahresgrenzen ausdrücklich als „frühestes/letztes bekanntes Jahr im geladenen Katalog“ ausweisen; diese sind kein Beweis vollständiger Historie.
7. `RebrickablePartRelationships` als Hinweis auf verwandte Formen/Varianten anzeigen, aber keine Zahlen verschiedener Teilenummern oder Farben zusammenführen und keine Austauschbarkeit für geplante Sets behaupten. Eine eventuelle Äquivalenzregel ist später gesondert fachlich zu verifizieren.

Ausgabe je Paar: bekannte Setzahl, beobachtetes erstes/letztes Jahr, normale/ersatzteilbezogene Kennzeichnung, ungelöste Verknüpfungen, Kataloggeneration, Berechnungsdatum, Abdeckungsstatus und konkrete fehlende Angaben. `0 bekannte Verknüpfungen` bedeutet nicht `0 reale Sets`; fehlende Jahre bleiben unbekannt.

Die Abdeckung bezieht sich auf einen definierten, vollständig geladenen Quellsnapshot, nicht auf die gesamte denkbare Brick-Historie. Erforderliche Dateien/Joins einschließlich Teilebeziehungen und Unterinventaren validieren. Importlauf vor Tabellenersatz persistent als „laufend“ markieren, nach validiertem Gesamtabschluss als geeignete Generation veröffentlichen; bei Teilfehler bleibt die nun gemischte aktuelle Datenbasis ungeeignet, auch wenn eine frühere Generation erfolgreich war. Zwischen laufendem Import und Vorschlagsbestätigung darf es keine Auswertung einer wechselnden Generation geben: Revision vergleichen und nach Abschluss neu berechnen. Dauerhaftes Staging ist erst nötig, wenn Vorschläge während des Imports verfügbar bleiben sollen.

### 8.2 Eigene geplante Sets und unbekannter Bedarf

Heute fehlt eine Planungsmodellierung. **Bestätigte Entscheidung D1:** Bis zur expliziten Erfassung/Bestätigung gilt Eigenbedarf als unbekannt. Eine leere neue `PlannedSet`-Tabelle bedeutet nicht „kein Bedarf“. Bereits Version 1 zeigt alte, seltene Teile bei belastbaren Katalogdaten zur manuellen Archivprüfung mit dem genauen Hinweis **„Eigenbedarf unbekannt · bitte prüfen“**. Das ist eine verpflichtende V1-Funktion, keine nur optionale spätere Anzeige. Der Nutzer entscheidet beim Aufräumen selbst; Vorschlag und Bestätigung der physischen Bewegung bleiben getrennt.

Die Datenqualitäts- und Alters-/Seltenheitsregeln gelten auch für die manuelle Prüfliste. Unbekannter Bedarf allein sperrt ihre Anzeige nicht. Bekannter positiver Bedarf und „griffbereit halten“ schließen den betreffenden Inhalt weiterhin aus. Bei fehlender historischer Belastbarkeit bleibt es bei einem Datenlückenhinweis ohne positive Einstufung als alter, seltener Prüfkandidat. Bei der Teileaufnahme bleibt das Kategorieregal Standard, solange der Eigenbedarf unbekannt ist; auch ein vorhandener Archivbestand ändert diesen Standard nicht.

`PlannedSet` hält gewünschte Anzahl und aktive Projekte. Für Bedarfsauflösung eine deterministisch gewählte gültige Inventarversion verwenden; vorgeschlagen ist die höchste vollständig auflösbare Version pro Set, mit sichtbarer Versionsangabe. Im Unterschied zur historischen Häufigkeit werden nicht alle Versionen addiert. Ersatzteile in Bedarf standardmäßig ausschließen, Option explizit anzeigen. Minifiguren und Untersets berücksichtigen, multiplikative Mengen korrekt auflösen; keine doppelte Addition bereits enthaltenen Inhalts. Nicht sicher auflösbare Inventarsemantik führt zu unbekanntem Bedarf, nicht zu Null. Vor Umsetzung anhand konkreter Katalogfixtures prüfen, welche Beziehungen zusätzliche Bestandteile liefern.

Für bekannte Planungssets jeden darin benötigten Teil/Farb-Typ zunächst griffbereit halten, unabhängig davon, ob bereits genügend physischer Bestand vorhanden ist. Das ist bewusst konservativ; keine automatische Archivierung von „Überschuss“ ohne zusätzliche Reservierungsregel. Bestehende offene Fehlmengen aus `User_Parts` und `UserMinifigurePart` zusätzlich als bekannten Bedarf berücksichtigen, ohne sie zu eigenen Planungssets umzudeuten. Der Vorschlag darf keinen bestehenden Fehlteileworkflow schlechter stellen.

Die Planungsabdeckung wird explizit als geprüft bzw. ungeklärt geführt; Nutzer kann „aktuelle Planliste vollständig, auch wenn leer“ bestätigen. Änderungen an Plänen, Inventaren oder Bedarfsdaten invalidieren betroffene Vorschläge. Keine neue reale Menge aus Bedarf erzeugen und vorhandenen Bestand nicht doppelt für mehrere geplante Sets reservieren. Eine umfassende setübergreifende Mengenallokation ist spätere Erweiterung; die konservative Typ-Sperre reicht für die erste sichere Archivregel.

### 8.3 Einstellbare Archivregel und Erklärung

Startwerte: höchstens **2 unterschiedliche bekannte Sets**, letztes bekanntes Set mindestens **10 Kalenderjahre** alt. Bewertungsdatum als Parameter injizieren; bei Jahr 2026 ist das bekannte letzte Setjahr spätestens 2016. Die Regel beschreibt historische Vorkommen, keine Garantie ausbleibender Produktion oder Nachfrage.

Die UI unterscheidet zwei Ergebnisse derselben historischen Regeln:

- **Manuelle Archivprüfung (V1):** belastbare historische Bedingungen erfüllt, Eigenbedarf unbekannt; immer **„Eigenbedarf unbekannt · bitte prüfen“**. Keine Aussage „bedarfsgerecht archivieren“. Ein Nutzerentscheid kann anschließend einen normalen Umräumplan erzeugen.
- **Bedarfsgeprüfter Vorschlagskandidat:** zusätzlich geprüfte Bedarfsabdeckung ohne bekannten Bedarf. Auch dies löst niemals eine automatische Buchung aus.

Für einen **bedarfsgeprüften Vorschlagskandidaten** müssen alle Bedingungen erfüllt sein:

- Exakte Teil/Farb-Identität und hinreichend vollständige, valide, hinreichend frische Kataloggeneration.
- Mindestens ein belegtes Setvorkommen; `known_set_count ≤ konfigurierter Grenzwert`.
- Gültiges letztes Jahr, Altersgrenze erreicht, keine die Einstufung unsicher machenden Verknüpfungs-/Jahreslücken.
- Planungsabdeckung geprüft und kein bekannter geplanter bzw. offener Setbedarf; kein „griffbereit halten“-Override.
- Inhalt für den betrachteten Vorschlag verifiziert. Unbekannte Historie/Identität/Inhalte erlauben keine positive Einstufung; ausschließlich unbekannter Eigenbedarf erlaubt die gesonderte manuelle Prüfliste.

**Annahme A2:** Katalogfrische zunächst maximal 90 Tage seit validiertem Snapshot, einstellbar und im Pilot abstimmbar. Ein einzelner vollständiger alter Import gilt nicht unbegrenzt als Abdeckung aktueller Varianten. Die Schwellen 2/10 und die Datenqualitätsgrenzen müssen im Vorschlag sichtbar sein.

Neue Varianten mit wenigen Vorkommen bleiben griffbereit, wenn ihr bekanntes letztes Setjahr die Altersgrenze noch nicht erreicht; neue/aktuelle Bekanntheit oder eigener Bedarf schlägt die Seltenheit. Unbekannte Historie bleibt vorsichtshalber aktiv. „Nachschub unwahrscheinlich“ ist ein manueller, rücknehmbarer Hinweis, kein Ersatz für Jahre, Abdeckung oder Bedarfsprüfung und keine harte Archivfreigabe.

Beispielerklärung: „2 bekannte Sets, letztes bekanntes Jahr 2014; Kataloggeneration X vollständig geprüft; Planliste geprüft, kein bekannter Bedarf; Archivziel Y noch auf Kapazität prüfen.“ Gegenbeispiel: „1 bekanntes Set von 2025: aktuell, griffbereit.“ Fehlende Daten einzeln nennen, etwa „Farbe unbestimmt“, „Inventarverknüpfung fehlt“, „Planungsbedarf ungeklärt“.

### 8.4 Behälterweise und bei Teileaufnahme

**Ganze Box:** Nur wenn `contents_complete`, alle enthaltenen Paare historisch qualifizieren und keine Auflage-/Zugriffs-/Zielblockade besteht. Unbekannter Eigenbedarf allein erlaubt die Anzeige der ganzen Box zur manuellen Prüfung, mit dem Hinweis „Eigenbedarf unbekannt · bitte prüfen“; der Nutzer muss diese Unsicherheit vor dem Umräumplan ausdrücklich beurteilen. Ein einziger Inhalt mit bekanntem Bedarf, aktueller Historie oder ungeklärter historischer Eignung verhindert die Ganzboxeinstufung. Gemischter Inhalt → geeignete Teilmengen in andere passende Archivbehälter vorschlagen; verbleibenden Inhalt und leere Hülle korrekt ausweisen. „Archivkandidat“ und „konkreter ausführbarer Umräumplan“ sind getrennte Stufen; unbekannte Zielkapazität verhindert die zweite Stufe bis zur Vor-Ort-Prüfung.

**Teileaufnahme, in dieser Reihenfolge:**

1. Teil und Farbe bestätigen, Menge bzw. „noch nicht gezählt“ erfassen. Bildidentifikation allein bestimmt keine sichere Farbe.
2. Bei unbekanntem Eigenbedarf zuerst das Kategorieregal als Standard anbieten und geeignete vorhandene Zuordnungen dort bevorzugen; Archivorte nur als ausdrücklich manuell gewählte Alternative. Bei geklärtem Bedarf vorhandene passende bestätigte Zuordnungen bevorzugen, wenn Zone, Zugriff, Kapazität und aktiver Bedarf passen. Nicht stumpf die niedrigste `PartStorage.id` wählen; bei aktuellem Bedarf keinen einzigen Archivort als beste Lösung anbieten.
3. Neue/aktuelle Varianten und Varianten mit geplantem Bedarf in griffbereite Plätze des Kategorie-Standardregals lenken.
4. Bei geklärtem Eigenbedarf alte seltene Varianten nur bei vollständigen Bedingungen als Archivvorschlag anbieten, vorzugsweise mit passendem vorhandenen Archivbestand. Die manuelle Archivprüfliste für das Aufräumen ändert den Intake-Standard bei unbekanntem Eigenbedarf nicht.
5. Sonst Kategorie-Standardort anbieten, z. B. Kategorie A → Regal 5, und fehlende Angaben nennen. Wenn dort kein konkreter Platz bekannt ist: „Regal 5 – Fach/Behälter wählen“, keine erfundene freie Box. Fehlt die Kategoriezuordnung, manuelle Ortsauswahl anbieten.
6. Nutzer kann alternative sichere Orte wählen und einen Grund/Hinweis hinterlegen. Vorschau und physische Bestätigung bleiben auch bei Übersteuerung erhalten.

## 9. UI-Entwurf und Arbeitsabläufe

Bestehende Jinja-/Bootstrap-/Vanilla-JavaScript-Struktur beibehalten. Frontansicht als DOM/SVG mit beschrifteten fokussierbaren Einheiten und gleichwertiger Listenansicht; keine reine Canvas-Fläche. Vorschlag und bestätigter Ort unterscheiden sich durch Text und Muster/Umrandung, nicht nur Farbe. Ansicht bleibt bei unbekannten Maßen nutzbar.

### 9.1 Lagerübersicht und Fundortnavigation

```text
Lager > Aktiv > Regal 1                 [Liste | Frontansicht]
Ansicht: schematisch – Abmessungen unvollständig
+ Fach 5 ---------------------------------------------------+
| links: Stapel A       Mitte: Einzelbox      rechts: Becher |
| [Etikett 4, oben]     [Etikett 6, voll]     [Deckelbox]     |
| [Etikett 3, unten]                         [Etikett 9]      |
+-----------------------------------------------------------+
Auswahl: Box 3 · interne Referenz #… · HMH S
Aktuell: Regal 1 / Fach 5 / Stapel A / Position 1 von unten
Inhalt zugänglich: ja · Box entnehmen: obere Box zuerst abnehmen
[Inhalt] [Verschieben planen] [Füllstand] [Fach aufräumen]
```

Die Skizze ist eine illustrative mögliche Anordnung, keine Behauptung über die reale Stellung der Etiketten 3/4/6/9. Volle Nummern, Typ und Kurz-ID machen gleiche Etiketten unterscheidbar. Regal/Fach werden beschriftet angezeigt; zusätzlich geordnete Platzposition. Tiefe Stapel vollständig aufklappbar.

Details navigieren Regal → Fach → Stapel/Einheit → Inhalt; beim Magazin zusätzlich Schublade → Unterteilung. Beispielpfad: „Regal 1 / Fach 5 / Magazin 2 / Schublade 7 / Unterteilung B“. Magazinraster erst mit bestätigter Anordnung zeichnen, davor nummerierte Schubladenliste. Leere Boxen bleiben sichtbar.

Teilesuche zeigt alle bestätigten Orte der gewählten Farbe mit Menge oder „ungezählt“, Archivkennzeichnung, Zugriff und eventuellem geplanten Ziel. Ein Klick springt zum Fach, scrollt die Einheit ins Bild und fokussiert sie; URL mit stabilen IDs statt Etiketten als Primärschlüssel. Wiederholte Etiketten erzeugen keine Mehrdeutigkeit. Unbekannter Fundort bleibt als Klärungsaktion sichtbar.

### 9.2 Schnellerfassung bestehender Stapel von unten nach oben

1. Regal/Fach auswählen, neue Spalte/Standposition bestimmen; Typ und Etikett der untersten Einheit erfassen oder eine vorhandene Einheit auswählen.
2. „Nächste Box darüber“ übernimmt nur bei bestätigter Paarung passende Typvorschläge; Etikett frei eingeben, keine laufende Nummer erzwingen. Auflageart getrennt auswählen.
3. Laufende Vorschau zeigt Reihenfolge, unbekannte Maße, mögliche Zugriffshindernisse und ungeprüfte Beziehungen. Falsche letzte Eingabe lokal zurücknehmen, ohne eine bereits physisch bestätigte Bewegung zu löschen.
4. Stapelaufnahme zusammen prüfen und als beobachteten Ist-Zustand bestätigen. Dies ist eine einmalige Erfassung vorhandener Aufstellung, keine erfundene Umlagerung. Inhalte separat abgleichen; „Aufstellung erfasst“ setzt nicht `contents_complete`.

Tastaturablauf mit sichtbarem Fokus, Enter für weitere Einheit und klarer Abschlussaktion; auf Touch große Bedienelemente. Reihenfolge zusätzlich als Liste „1 unten, 2 darüber …“ bearbeiten; Drag-and-drop ist optional und hat eine Buttonalternative. Ganze Einheiten müssen beim Wiederverwenden auf bestehende Platzierung geprüft werden, sonst doppelte Erfassung verhindern.

### 9.3 Fach aufräumen und Box 6 vergrößern

Fach auswählen → „Aufräumvorschläge“ → begründete Kandidatenliste. Bereits V1 zeigt historisch belastbare alte/seltene Inhalte bei unbekanntem Bedarf mit „Eigenbedarf unbekannt · bitte prüfen“. Pro Box: alle Inhalte geprüft?, Katalog/Bedarf bekannt?, Ganzbox oder Teilumbuchung?, Ziel?, Auswirkungen auf Höhe/Grundfläche? Neben der Liste Vorschau vor/nachher. Manuelle Prüfkandidaten als solche kennzeichnen; der Nutzer entscheidet über die Archivierung, bevor er einen konkreten Umräumplan übernimmt.

Für 3/4/7/9 werden getrennte Entscheidungen angeboten. Wenn z. B. Box 4 einen aktuellen Inhalt enthält, ist sie kein Ganzboxkandidat; Teilumbuchung zeigt ihre Restbelegung. Freie Fläche wird erst nach geplanter Entfernung leerer Hüllen oder ganzer Einheiten angezeigt. Die größere Zielbox für 6 wird einschließlich ihres Typs und der benötigten Fläche gewählt, nicht allein über ein „größer“-Flag.

„Plan übernehmen“ erstellt reservierte, geordnete Arbeitsschritte: ggf. obere Einheiten auf definierte Zwischenablage, geeignete Inhalte/Boxen ins Archiv, Stellfläche zusammenführen, größere Box platzieren, Inhalt von 6 übertragen, leere alte Box entfernen. Kein Schritt behauptet, ein nicht vorhandener Zwischenplatz sei frei. Jeder abhängige Schritt wird erst nach vorheriger Bestätigung ausführbar. Bei unbekannten Maßen bleibt der Plan bis zur physischen Passprüfung entsprechend markiert.

### 9.4 Teileaufnahme und Überlauf

Formularfolge: Teilenummer → Farbe → Menge → vorhandene passende Orte → erklärter Standard-/Archivvorschlag. `quantity=NULL` ist als „Fundort ohne Zählung erfassen“ möglich, aber nicht als quantitativ sichere Buchung. Der Vorschlag nennt seine Gründe und fehlenden Angaben unmittelbar beim Ziel.

Bei „voll“: „größerer Behälter“ und „zweiter Ort“ anbieten. Vorschau nennt alte und neue Mengen sowie beide Adressen. Bei Restmenge bleibt der ursprüngliche Ort erhalten. „Geplant“ und „physisch eingelagert“ sind zwei getrennte Aktionen. Bei Konflikt die gewählten Werte erhalten und den geänderten Bestand anzeigen; keine doppelte Buchung durch erneutes Absenden.

Alle Flows benötigen Lade-/Leer-/Fehlerzustand, verständliche Validierung direkt am Feld, zugängliche Statusmeldungen und erneute Datenprüfung nach Rückkehr zur Seite. IDs/Notizen sicher rendern; Fach-/Boxnamen nie ungeprüft über `innerHTML` einfügen. Zustandsändernde Browserrouten in die vorhandene Zugriffsstrategie einordnen und CSRF-Schutz für die neuen Flows vorsehen. Desktop-Bearer-Authentifizierung unverändert erhalten. Die Planung autorisiert keine öffentliche Bereitstellung.

## 10. Technischer Zuschnitt und Umsetzungspakete

Vorgeschlagene neue Dateien unter `brick_manager/`:

- `services/storage_service.py`: Orte, Einheiten, Inhalt, Adressauflösung und gemeinsame Validierung;
- `services/storage_move_service.py`: Plan, Reservierungen, Revisionen, Bestätigung und Journal;
- `services/part_history_service.py`: generationsgebundene Vorkommen, Jahre und Abdeckung;
- `services/storage_suggestion_service.py`: Kategorie-/Archiv-/Einlagerungsregeln und erklärbare Ergebnisse;
- `routes/warehouse.py`, `templates/warehouse.html`, `static/js/warehouse.js`: Lageransicht und Aktionen. Bestehende `box_maintenance`-Oberfläche verlinkt den neuen Einstieg und behält Druckfunktionen.

Diese Aufteilung kann bei der Implementierung zusammengelegt werden, solange Verantwortlichkeiten überschaubar bleiben. Kein Umbau zur App-Factory als Nebenaufgabe. Neue Modelle zunächst in `models.py` entsprechend vorhandener Struktur; Tests in `brick_manager/tests/`.

Vorgeschlagene Browser-Endpunkte: `GET /warehouse`, `GET /warehouse/locations/<id>`, `GET /warehouse/units/<id>`, `POST /warehouse/moves` (Entwurf), `POST /warehouse/moves/<id>/plan`, `POST /warehouse/moves/<id>/confirm`, `POST /warehouse/moves/<id>/cancel`, `GET /warehouse/suggestions?...`. Bestätigung benötigt Plan-ID, erwartete Revision und Idempotenzschlüssel. `400` für ungültige Eingaben, `404` für fehlende Objekte, `409` für veraltete Planung/Reservierung/Belegung, konsistente sichere Fehlermeldungen. Neue Desktop-Funktionen bei Bedarf additiv unter `/api/v1` mit demselben Service, nicht über ungeschützte Browserrouten.

### Reihenfolge, Abhängigkeiten und Abnahme

**Bestätigte Priorität:** P0–P2 bilden das erste Umsetzungspaket „Behälter, Stapel und Mengen je Fundort“. Vorbereitung, additive Migration und einheitliche Schreibgrenze gehören zu diesem Paket; Regaloberfläche und bestätigte Bewegungen folgen darauf. Historische V1-Prüflisten dürfen ohne fertige eigene Setplanung ausgeliefert werden.

| Paket | Abhängigkeit | Bereiche und konkrete Arbeit | Überprüfbare Akzeptanz |
| --- | --- | --- | --- |
| P0 – Bestandsaufnahme und Pilotprotokoll | Planungsphase abgeschlossen; gesonderter Implementierungsauftrag | Read-only Datenbericht, Mess-/Erfassungsbogen für ein später vom Nutzer gewähltes Pilotfach (Dummy: Regal 1/Fach 5), offene Beschriftungsgruppen, Testfixtures, Ausgangs-Kontrakttests. Noch kein reales Umräumen. | Jede bekannte Zeile im Pilotscope erscheint im Mapping oder als Klärungsfall. Keine Schätzung als Messung. Alle heute vorhandenen Schreibwege sind inventarisiert. |
| P1 – Lagerstruktur und Migrationsgrundlage | P0 | Behälter, Stapelbeziehungen und Mengen je Fundort; `models.py`, `migration_service.py`, neue versionierte Migrationen, lokaler/Docker-Startvertrag, Backfill und Feature-Schalter. | Alt-IDs/Rohtexte/Setmengen erhalten; Migration zweimal sicher; Abbruch/Neustart getestet; keine zusätzlichen FK-Schäden. Neue Datenfelder für Altmenge/Geometrie bleiben unbekannt. |
| P2 – Einheitliche Schreibgrenze | P1 | Storage-Service, Adapter aller in Abschnitt 5.3 genannten Routen/Lookup-Funktionen; Etiketten-ID-Auflösung und Cacheinvalidierung. | Keine Änderung eines zufälligen ersten Fundorts bei Mehrdeutigkeit; keine widersprüchlichen Legacy-Schreibzugriffe; eindeutige Altverträge weiter erfüllt bzw. Änderungen explizit abgestimmt. |
| P3 – Schematische Lageransicht und Erfassung | P2 | Neuer Warehouse-Blueprint, Jinja/JS, Navigation, Stapelerfassung, Magazin/Schubladen/Unterteilungen, Such-Deeplinks. | Synthetisches Beispiel enthält gemischte Typen, nebeneinander unterschiedliche Stapel und wiederholte Etiketten; vollständige Tastatur-/Listenalternative. Keine Maßpassung ohne Daten. |
| P4 – Sichere Bewegung und Zugang | P2; Oberfläche aus P3 | Move-Service, Journal, Reservierungen, Bestätigungsdialoge, Mengenaufnahme/-transfer, Ganzbehälter, Überlauf, Zwischenablagen. | 10 → Quelle 6/Ziel +4 erhält Gesamtmenge; zweiter Confirm wirkungslos; konkurrierender Plan wird abgewiesen. Geplantes Ziel verändert Istfundort nicht. Leere Hülle belegt weiter Platz. |
| P5 – Verifizierte Physik und Flächenvorschau | P3/P4 | Typ-/StackRule-Pflege, Maße/Höhenprofile, Zugriff, freie Intervalle und Umräumschritte. | Gleichgroße bestätigte HMH-Paarung möglich, gemischte HMH-Größe ausgeschlossen; lose Auflage getrennt. Schräge über voller Breite geprüft; getrennte Lücken nicht addiert. Fehlende Messung → unbekannt. |
| P6a – Historie und V1-Bedarfsstatus | P1; P2 für Schreibkoordination | History-Service, persistente Kataloggeneration im Import, Vorkommensauflösung, Kategorieziele, Präferenzen und expliziter unbekannter Eigenbedarf; bekannte Fehlmengen berücksichtigen. | Zähler bleibt bei mehreren Versionen/Ersatzteilzeilen stabil; Figureninventar zählt nicht selbst als Set. Fehlende Verknüpfungen/Jahre verhindern historische Prüfkandidaten; ausschließlich unbekannter Eigenbedarf nicht. Kein Import mit Live-Netz in Tests. |
| P6b – Eigene Planliste und Bedarfsauflösung | P6a; keine Voraussetzung für manuelle V1-Prüfliste | `PlannedSet`-Pflege und geprüfte Bedarfsabdeckung nach Abschnitt 8.2. | Ungeprüfte Leerliste bleibt unbekannt; bekannter positiver Bedarf schützt Inhalte; eine bedarfsgeprüfte Qualifikation erfordert geprüfte Abdeckung. |
| P7 – Archivprüfung und Einlagerungsvorschläge V1 | P4/P5/P6a; bedarfsgeprüfte Qualifikation zusätzlich P6b | Suggestion-Service, Fach-Aufräumdialog, Intake-Integration in `manual_entry`/Upload/Suche, konfigurierbare Schwellen, Vorschlagsrevisionen. | Ganze Box nur bei vollständig geeigneten Inhalten und bestätigbarer Zielaufnahme; gemischte Box bietet Teilumbuchung. 3/4/7/9 und Box 6 als Fixture vollständig erklärbar. Neue Varianten bleiben aktiv. Unbekannter Bedarf zeigt „Eigenbedarf unbekannt · bitte prüfen“ beim Aufräumen und belässt bei Aufnahme das Kategorieregal als Standard. |
| P8 – Pilotabnahme und breitere Freigabe | P7 | Manuelle Vor-Ort-Prüfung im später vom Nutzer gewählten Pilotfach, Dokumentation, lokale und Integrationsprüfungen, begrenzte Freigabe per Schalter. | Reale IDs/Beschriftungen und bestätigte Bestände mit Fach abgeglichen; keine offene Mengenabweichung; Passzusage nur bei Messnachweis. Ausstehende Messungen/Datenlücken sind sichtbar, Erweiterung auf weitere Regale erst nach Pilotabnahme. |

### Erfassung für das später gewählte Pilotfach

Vor der Pilotabnahme pro tatsächlich vorhandener Einheit Etikett, interne ID, Typ, links-nach-rechts-Position, Unterlage/Auflageart, untere/obere Nachbarn, Zugriffsart, Füllzustand und vollständig erfassten Inhalt dokumentieren. Vorhandene Etiketten nicht anhand des Beispiels ergänzen oder entfernen. Gleiche Etiketten durch Foto/Position und später interne IDs unterscheiden.

Den nutzbaren Fachboden, Tiefe, Höhenprofil unter der Schräge und notwendige Zwischenablage messen. Je verwendetem Behältertyp Außenmaße mit Orientierung, wirkliche Stapelhöhenzunahme und Entnahmefreiraum prüfen. Bei gemischten Bechern und losen Auflagen jede konkret verwendete Paarung bestätigen. Beim Magazin Schubladenanordnung, Unterteilungen und obere Auflagen aufnehmen. Ein nicht gemessener Wert bleibt leer. Diese Erhebung ist spätere Pilotarbeit; sie wurde für den Plan nicht durchgeführt.

P3/P4 ermöglichen bereits eine nutzbare Lageransicht mit Bewegungen. P5 und P6a können nach stabilen Schnittstellen unabhängig bearbeitet werden. P7 ergänzt die manuelle V1-Archivprüfung und wartet auf diese Grundlagen, aber nicht auf P6b. Ein Pilot zum Erproben der Archivprüfung benötigt P7; das tatsächliche Fach bleibt frei wählbar. Keine feste Aufwandsschätzung vor P0; die Komplexität hängt besonders an Legacy-Zuordnungen, vorhandenen Kataloglücken und tatsächlichen Stapel-/Magazinmaßen.

Jedes Paket aktualisiert betroffene Design-/Referenz-/Anleitungsdokumente und das Logbuch. `reference/database-schema.md` erst zusammen mit tatsächlich implementierten Modellen/Migrationen auf den neuen Iststand heben; diesen Plan nicht vorzeitig zum gültigen Schema erklären.

## 11. Test- und Abnahmematrix

Die folgenden Fälle sind **geplante Tests**, hier nicht ausgeführt. Für Migrationen Alt-Schema-Fixtures und temporäre SQLite-Dateien, für Routen die isolierte App aus `tests/conftest.py`; externe Dienste mocken. Neue Tests müssen Verhalten und Dateninvarianten prüfen, nicht nur Status 200 oder nachgebaute Implementierungsdetails.

| Fall | Erwarteter Nachweis |
| --- | --- |
| Gemischtes Fach | HMH, Becher, Deckelbox und Magazin im selben Fach; unterschiedliche Basisbreiten und Stapelhöhen nebeneinander; keine falsche Gruppierung nach Typ oder Etikett. |
| Tiefer Stapel | Mindestens 20 Ebenen als technische Fixture, keine Aussage zur real zulässigen Höhe. Vollständige Adressauflösung, Abnahmefolge, Fokus-/Listennavigation; Zyklus wird abgewiesen, keine Rekursionsschleife. |
| HMH-Regeln | Gleiche Größe nur mit bestätigter Regel vorgeschlagen; XS/S/3 gemischt verboten. Frontzugriff kann möglich sein, Entfernen der unteren Box zeigt trotzdem Blocker. |
| Becher und lose Auflage | Unbestätigte 125/250-/500-ml-Kombination nicht automatisch gewählt. CYEER-Auflage bleibt `loose_on`; unbekannte Belastbarkeit keine sichere Passzusage. |
| Magazin | Exakt 30 bzw. 9 adressierbare Schubladen, bei bestätigtem Layout passende Darstellung. Schublade ganz oder 2/3 Unterteilungen. Belegte Unterteilung nicht löschen, Wechsel erhält Inhalt und Historie. Auflagen folgen Magazinbewegung nur als explizite Schritte. |
| Labels und Lücken | Boxetiketten 1,2,5,6,8 bleiben nach Entfernen 3/4/7/9 unverändert. Zwei Boxen mit Etikett 6 haben unterschiedliche IDs und Deeplinks. Text `01` und führende/abschließende Leerzeichen über Migration erhalten. |
| Mehrfachfundorte/Farben | Gleiches Teil in Rot und Blau sowie zwei Orte derselben Farbe. Suche zeigt alle passenden Orte, unbekannte Farbe separat. Legacy-Update ohne eindeutige Identität verändert nichts und meldet Konflikt. |
| Unbekannte Herkunft | Null-/Leerfelder und fehlender Katalogbezug bleiben sichtbar; kein stiller Verlust durch inneren Join. Mengenmigration erzeugt NULL statt 0 oder kopierter Setmenge. |
| Migration und Neustart | Zweiter Lauf ohne zusätzliche Einheiten/Zuordnungen; unterbrochener Backfill erhält Altzustand oder setzt kontrolliert fort. IDs, Notizen, Druckstatus, Setmengen unverändert; bekannte/neue FK-Verletzungen unterschieden. |
| Mengenverschiebung | Quelle 10, Ziel 2, Transfer 4 → Quelle 6, Ziel 6, Summe 12. 0/negativ/zu viel/Bools ablehnen. Unbekannte Quelle oder Zielmenge verlangt Zählung; Fehler rollt alle Mengen und Journalstatus zurück. |
| Wiederholung und Konkurrenz | Doppelbestätigung gleicher ID bucht einmal. Zwei Pläne auf dieselben verfügbaren 10 Stück mit je 7 dürfen nicht beide planen/bestätigen. Veraltete Zielposition/Füllstand/Quellrevision → Konflikt, kein Teilcommit. |
| Ganze Box / größerer Behälter | Ganze Box wechselt Ort ohne Änderung der Inhalte; Teiltransfer lässt Restort bestehen. Beim Wechsel bleibt Altbox leer und stellflächenwirksam, bis sie entfernt wird; Ziel mit vorhandenem Inhalt wird nicht überschrieben. |
| Unterbrechung eines Fachplans | Nach zwei von fünf bestätigten Schritten entspricht Istansicht genau diesen zwei. Abbruch löscht keine bestätigte Bewegung; Restreservierungen werden freigegeben. |
| Stellfläche | Entfernen oberer Box senkt Höhe ohne Grundflächengewinn. Entleeren ohne Entfernen gibt keine Fläche frei. Zwei getrennte 100-mm-Lücken ergeben keinen 180-mm-Platz. Umstellen zum Zusammenführen braucht eigene Schritte. |
| Schräge und Messlücken | Rechteck passt am Mittelpunkt, kollidiert aber am Rand unter Schräge → ungeeignet. Unbekannte Tiefe/Höhenzunahme/Freiraum → Passung unbekannt; schematische Anzeige bleibt möglich. |
| Setzählung | Gleiches Teil/Farbe in zwei Inventarversionen, mit Menge 5 und als Ersatzteil im selben Set → genau 1 Set. Zweite Farbe getrennt; zwei echte Setnummern → 2. |
| Unterinventare/Varianten | Teil direkt und über Figur im selben Set → 1. Figuren-ID ohne echtes Elternset wird nicht als Set gezählt. Untersetpfade deduplizieren, Zyklen/fehlende Links sperren Vollständigkeit; verwandte Teilenummern bleiben getrennt. |
| Alte/neue Variante | Bewertungsjahr 2026: 2 Sets, zuletzt 2016, vollständige Daten und kein Bedarf → Kandidat; zuletzt 2017 oder neu 2025 → griffbereit. 3 Sets → außerhalb Startregel. Grenzwerte und Jahrwechsel deterministisch testen. |
| Unvollständiger Katalog | Keine Links, fehlende Jahre, unvollständige Unterinventare, abgelaufene Generation oder fehlgeschlagener Import → keine automatische Archivqualifikation. Beobachtete Werte und fehlende Daten werden korrekt angezeigt. |
| Bedarf | Leere ungeprüfte Planliste → unbekannt: bei belastbar alten/seltenen Inhalten in V1 manuelle Prüfliste mit exakt „Eigenbedarf unbekannt · bitte prüfen“, aber kein bedarfsgeprüfter Kandidat. Bei unvollständiger Historie kein positiver Prüfkandidat. Geprüft leere Liste erlaubt bedarfsgeprüfte Regelprüfung. Ein aktives geplantes Set bzw. vorhandene offene Setfehlmenge hält Teil/Farbe griffbereit; unauflösbares Planinventar sperrt. |
| Gemischter Inhalt | Drei archivgeeignete Paare plus ein aktuelles/ungeklärtes Paar → kein Ganzboxvorschlag. Teilumbuchung nennt Restmenge und tatsächlichen Platzgewinn. Unvollständig aufgenommene Box niemals pauschal als vollständig geeignet werten. |
| Teileaufnahme | Bei unbekanntem Eigenbedarf bleibt das Kategorieregal Standard, auch bei historischer Prüfeignung und vorhandenem Archivbestand; manuelle Zielwahl bleibt möglich. Vorhandenen passenden zugänglichen Bestand bevorzugen; volle Zielbox überspringen, zweite/größere Box anbieten. Fehlende Katalog-/Bedarfsdaten → Kategorie A/Regal 5 mit Gründen. Fehlende Kategorie → manuelle Auswahl; Override und wiederholte Bestätigung korrekt. |
| Sicherheit und UI | Ungültige IDs/Hostbeziehungen/ungültige JSON-Typen, CSRF- und API-Authentifizierungsfehler; Etikett mit HTML-Zeichen bleibt Text. Keine Token/Interna in Fehlern. Tastatur/Touch, schmaler Bildschirm, Fehler-/Leerzustände und Fokus nach Deeplink manuell bzw. mit Browserharness prüfen. |

Beispielhafte spätere Testdateien: `test_storage_migration.py`, `test_warehouse_contracts.py`, `test_storage_moves.py`, `test_part_history.py`, `test_storage_suggestions.py` sowie isolierte JS-Tests für Frontlayout und Interaktionen. Bestehende Storage-/API-/Importtests gezielt erweitern. DB-Mutationsfälle echte Transaktionen prüfen lassen, nicht die Schreiblogik selbst wegmocken.

Spätere Verifikation: zuerst betroffene Dateien mit `poetry run pytest -q --no-cov <testdateien>` für isolierte Funktionsprüfungen, danach `poetry run pytest -q` einschließlich der konfigurierten Coverage-Anforderungen. Im untersuchten `pytest.ini` steht aktuell `--cov-fail-under=60`; ältere Skill-Referenzen nennen abweichende historische Werte und sind kein aktueller Nachweis. Geänderte Python-Dateien mit `poetry run ruff check` und `poetry run ruff format --check`, Modell-/Interfaceänderungen mit `poetry run basedpyright` prüfen. Browser-/Vor-Ort-Prüfung getrennt berichten; aus Routenprüfungen keine vollständige UI-Abdeckung ableiten.

## 12. Bestätigte Entscheidungen und verbleibende Annahmen

| Punkt | Entscheidung bzw. vorgeschlagene Annahme | Status / Auswirkung |
| --- | --- | --- |
| D1: Unbekannter Eigenbedarf – bestätigt | V1 zeigt historisch belastbare alte/seltene Inhalte mit „Eigenbedarf unbekannt · bitte prüfen“ zur manuellen Archivprüfung. Bei Teileaufnahme Kategorieregal als Standard. | Nutzer entscheidet beim Aufräumen; keine automatische Archivfreigabe. Planliste P6b ist keine Voraussetzung für die manuelle V1-Prüfliste. |
| A2: Katalogfrische | Einstellbarer Start 90 Tage seit geprüftem Snapshot | Zu alte Daten führen zum Kategorie-Fallback. In P6 mit realem Importablauf abstimmen. |
| A3: Geometrieumfang | Pilot zunächst schematisch, eine Reihe in der Tiefe; gemessene Tiefe bei Bedarf explizit ergänzen | Schneller nutzbar; keine automatische Millimeterpassung für unbekannte/hintereinander liegende Anordnung. In P0 aufnehmen. |
| A4: Maße und Sicherheit | Außenmaßreihenfolge, Stapelhöhenzunahme, Deckel-/Entnahmefreiraum, Auflage/Last und Schräge vor Ort prüfen | Die genannten Produktmaße reichen nicht für alle Passprüfungen. Vor positiver Passzusage in P5/P8 messen. Keine Lastenwerte erfinden. |
| A5: Kategorieziele | Genau ein primäres Regal/Fach je Kategorie, optional gesondertes Archivziel | Einfacher Fallback, Nutzer darf abweichen. Priorisierte Mehrfachstandards bei Bedarf später ergänzen. |
| A6: Füllzustand | Manuell, mit zusätzlichem `unknown`; keine Prozent- oder Stückberechnung aus Volumen | Verhindert Scheingenauigkeit. Eignung konkreter Aufnahme vor Ort bestätigen. |
| A7: Bestandsbegriff | Physische Lagerzählung separat von setbezogenem Besitz, keine Summierung beider | Bestehende Set-/Dashboardlogik bleibt fachlich erhalten. Eine spätere gemeinsame Bestands-/Reservierungsrechnung braucht eigenes Konzept; keine Doppelzählung in neuen Anzeigen. |
| A8: Planung von Sets | Separate einfache Planliste; vollständig auflösbare aktuelle Inventarversion für Mengen, alle Versionen für historische Vorkommen | Besitzstatus bleibt unverändert. Versionsauswahl und Unterinventarsemantik vor P6 anhand Fixtures bestätigen. |
| A9: Ersatzteile und Varianten | Historie inkl. Ersatzteilen; Planbedarf standardmäßig ohne Ersatzteile; keine automatische Variantenäquivalenz | Konservativere Archivregel; Spezialpräferenzen explizit ergänzbar. |
| A10: Doppelbeschriftungen | Vorläufige Legacy-Gruppen, erst nach physischer Prüfung konkrete Behälter | Zusätzlicher Pilotabgleich notwendig, aber keine irreversible falsche Zusammenlegung. |
| A11: Stapel/Unterteilung | Auflageketten abgeleitet; Schubladen 1/2/3 Inhaltsbereiche | Reicht für Auftrag. Andere Unterteilungsformen erst bei realem Bedarf planen; bestehende IDs bei Umgestaltung erhalten. |
| A12: Alte Clients | Lesen additiv; mehrdeutige oder strukturierte Legacy-Schreibanfragen mit Konflikt statt willkürlichem Überschreiben beantworten | Abstimmung mit Desktop-Verbrauchern vor P2; mögliche Übergangsphase dokumentieren. |

Die Priorität des ersten Umsetzungspakets, die manuelle V1-Archivprüfung und der Intake-Standard sind bestätigt; die reale Pilotwahl steht noch aus. Die übrigen Annahmen sind weiterhin reversibel und nicht durch diese Bestätigung pauschal beschlossen. Keiner dieser Punkte blockiert die Fertigstellung dieses Plans. Sie sind Abnahme-/Messpunkte für die spätere Umsetzung. Ein Schritt, der sichere Geometrie, verifizierte Stapelung, gezählte Mengen oder bekannte Bedarfsabdeckung benötigt, bleibt bis dahin entsprechend eingeschränkt.

## 13. Historischer Abschluss der Planungsphase

Erstellt wurden ausschließlich Plan und Dokumentationsverweise sowie ein Logbucheintrag. Quellcode-/Test-/Migrationsdateien wurden gelesen, aber nicht geändert. Keine Anwendungstests oder Migrationen ausgeführt und keine Produktivdatenbank geöffnet. Die hier beschriebenen Tests, Modelle und Endpunkte sind zukünftige Arbeit; sie sind keine bereits vorhandenen Fähigkeiten.

Zugehörige aktuelle Referenzen: [Architektur](../architecture/reference-architecture.md), [High-Level-Design](../architecture/high-level-design.md), [Softwaredesign](../architecture/software-design.md), [Schema](../reference/database-schema.md), [Tests](../guides/testing.md). Der Plan ersetzt diese Ist-Dokumente erst mit tatsächlich implementierten und geprüften Änderungen.

## 14. Konkretisierungen aus der Umsetzung

- Sichere Standardfreigabe: `WAREHOUSE_ENABLED` schaltet die neue Oberfläche;
  Legacy-Schutz gilt unabhängig davon. Kein echtes Pilotfach als technische
  Freigabevoraussetzung; die Tests verwenden ausdrücklich synthetische Fächer.
- Reservierung bewusst pro beteiligter Einheit statt einer komplexen parallelen
  Teilmengenallokation. Abhängige Auflagenumstellungen werden nacheinander
  physisch bestätigt; überlappende zukünftige Ziele werden abgewiesen.
- Eine gemessene Fachhöhenkurve beschreibt die konservative Mindestfreihöhe
  über der gesamten nutzbaren Tiefe. Ohne diesen Nachweis bleibt die Passung offen.
- Zählkorrekturen und das Auflösen unbekannter Farben sind ausdrücklich
  protokollierte Erfassungen. Neue Zugänge und Bewegungen bleiben separate
  bestätigbare Aufträge. Eine bekannte Teil-/Farbidentität wird nicht still geändert.
- Historische Importläufe ohne persistente Abdeckung gelten nicht nachträglich
  als vollständig. Teilfehler und überlappende Läufe bleiben ungeeignet, bis
  ein neuer konsistenter vollständiger Lauf vorliegt.
- ID-basierte Einzel-Etiketten nutzen den bestehenden Renderer; der sichtbare
  Text bleibt unverändert, der technische Dateiname enthält zusätzlich die ID.

Paketstatus, Kriterienabgleich, tatsächlich ausgeführte Prüfungen und Vor-Ort-Grenzen
stehen zentral im [Abnahmeprotokoll](storage-acceptance.md).
