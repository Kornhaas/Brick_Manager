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

## Vorschlag: Setpflege als eigener Arbeitsbereich (22. November 2026)

**Status: Am 22. November 2026 zur Umsetzung angenommen.** Der folgende Abschnitt
dokumentiert die Analyse des Ausgangsstands `935cca5` und den angenommenen
Vorschlag; der Implementierungs- und Prüfstand wird im zugehörigen Logbucheintrag
festgehalten. Auftrag der Analyse: den vollständigen
Ablauf vom Finden einer physischen Setkopie über die Teileerfassung bis zum
Speichern und Zurückkehren prüfen. Keine Änderung der Bedienungslogik, keine
Produktivzugriffe mit Schreibrechten und kein Rollout im Analyseauftrag.

### Nutzerziel und tatsächlicher Ablauf

Das zentrale Ziel ist eine unterbrechungsfreie Bestandsaufnahme: Eine Box aus
einer gefilterten Sammlung öffnen, Teile zählen, regelmäßig zur Sicherheit
speichern und anschließend an derselben Stelle weiterarbeiten. Die Rückkehr
zur Sammlung ist eine eigene Entscheidung und darf keine Nebenwirkung des
Speicherns sein.

Aktuell liest `/set_maintain` die Filter aus der URL. „View“ lädt JSON für eine
`User_Set.id`, versteckt die Liste und zeigt einen Detailbereich derselben Seite.
Weder Adresse noch Browserhistorie bilden die geöffnete Box ab. Das Detailformular
sendet Mengen und Status an `/set_maintain/update`; dessen Erfolgs- und Fehlerpfad
leiten beide auf `/set_maintain` ohne Suchparameter zurück.

Der vorhandene Knopf „Back to Sets“ ist ein anderer Fall: Er zeigt den bisherigen
Listen-DOM und erhält dadurch die Filter, lädt aber Fortschritt und
Filterzugehörigkeit nicht neu und stellt Zeilenfokus/Arbeitsposition nicht gezielt
wieder her. Diese beiden Wege dürfen in der Diagnose nicht gleichgesetzt werden.

### Priorisierte Befunde

| Priorität | Befund und Auswirkung | Nachweis |
| --- | --- | --- |
| Hoch | Erfolgreiches Speichern beendet die Bearbeitung und verliert Filter, Seite und ausgewählte Box. Selbst ein Formularfehler endet auf der nackten Liste statt bei korrigierbaren Eingaben. | `routes/set_maintain.py:update_user_set`; beides mit isolierten Anfragen reproduziert. |
| Hoch | Mengen werden beim Verlassen des Felds automatisch gespeichert; Status und Sammelaktionen sind dagegen zunächst Entwürfe. Es fehlt eine gemeinsame Aussage, ob wirklich alle Änderungen bestätigt sind. Nach einer Sammelaktion können ältere „Gespeichert“-Meldungen stehen bleiben. | `static/js/set_maintenance.js:attachAutoSaveListeners`, `quantitySaveFeedback`, Sammelaktionen; unterschiedliche Wege im Browser bestätigt. |
| Hoch | „Mark All Parts as Existing“ liest die Sollmenge über die sechste Tabellenspalte. Bei Minifigurenteilen liegt sie in Spalte fünf. Auch der Abweichungsfilter verwendet die falsche Spalte. Die Erfolgsmeldung passt nicht zum Ergebnis. | Im Browser: reguläres Teil wird auf 5 gesetzt, Minifigurenteil bleibt auf 1 bei Soll 5. Ein bestätigtes vollständiges Minifigurenteil bleibt unter „Show only mismatched parts“ sichtbar. |
| Hoch | Die Detailansicht nennt nur „Set Details“, ohne sichtbare Set-/Boxidentität. Öffnen verändert keine Browseradresse; Neuladen schließt die Details. Die Tastatur verliert den Fokus auf den versteckten View-Knopf. | Im Browser: unveränderte Listen-URL, generischer Titel, aktives Element `BODY`, Details nach Reload geschlossen. |
| Hoch | Langsame Detailantworten können nach einem neueren Setwechsel eintreffen und die aktuelle Ansicht überschreiben; Fehler werden nur in der Konsole protokolliert. | Quellcodebefund ohne gezielte Verzögerungsreproduktion: Detail-Fetch ohne Antwortgeneration oder sichtbaren Fehler-/Wiederholen-Zustand. |
| Hoch, separat absichern | Die Lagerortbearbeitung zerlegt einen formatierten Text mit Leerzeichen/Bindestrichen statt strukturierter Felder. Die Vorbelegung und der teilenummerweite Geltungsbereich sind für Nutzer nicht zuverlässig erkennbar. Handler werden nach fester 500-ms-Frist gebunden. | Quellcodebefund in `initLocationEditHandlers` und `/update_part_location`; keine schreibende Liveprüfung. |
| Mittel | Gesamtübersicht und Trefferliste vermitteln verschiedene Bezugsgrößen. Dropdown-Auswahl allein filtert nicht. Quick-Karten ersetzen Filter; „Open complete list“ springt nur zum aktuellen Formular. | Routen-/Templatebefund; die Filterfunktion wurde am 21. November separat geprüft. |
| Mittel | Sortierung verändert nur die gerenderte Seite und ist nicht Teil der URL. Bei Themengruppierung werden Datenzeilen umgehängt, während Gruppenüberschriften stehen bleiben. | `initTableSorting`; Quellcodebefund, keine globale Sortiergarantie. |
| Mittel | Auf Mobilgeräten beanspruchen breite, teilweise verschachtelte Tabellen mehr Platz als der Bildschirm. Mengenfelder haben keine zeilenspezifischen zugänglichen Namen. Detailwechsel und Rückkehr steuern Fokus nicht. | Edge mit 390 Pixeln: Dokumentbreite 650 Pixel. Zugänglichkeitsbefunde aus Markup/JavaScript, kein Screenreader-/Gerätenachweis. |
| Mittel | Sammelaktionen sind prominent, wirken auch auf ausgeblendete Zeilen und melden sofort Erfolg. Ausstehende Einzel-Saves und neue Sammelentwürfe sind technisch nicht sauber als verschiedene Zustände behandelt. | Quellcode und bestehender Queue-Test: Beim Formularabschluss kann ein neuer aktueller Wert einer zuvor ausstehenden Zeile vor dem Gesamtformular als Einzel-Save versendet werden. |

### Vergleich der Navigationsvarianten

| Variante | Vorteil | Grenze | Empfehlung |
| --- | --- | --- | --- |
| Inline-Ansicht erhalten und beim Speichern offen lassen | Kleinster Eingriff gegen den unmittelbaren Rücksprung | Eigene Adresse, Browser-Zurück, Neuladen, Antwortreihenfolge und veraltete Liste brauchen weiterhin zusätzliche Zustandslogik | Mögliche Zwischenlösung, wenn ausschließlich ein kleiner Sofortfix gewünscht ist |
| Eigene Detailseite pro physischer Setkopie | Klarer Arbeitsbereich, direkt verlinkbar, Browserhistorie nutzbar, Platz für lange Inventare und kleine Bildschirme | Rückweg und Speicherzustände müssen trotzdem ausdrücklich umgesetzt werden | Empfohlenes Ziel |
| Liste und Inventar nebeneinander | Schneller Wechsel zwischen vielen Boxen am Desktop | Wenig Breite für Teile/Figuren, deutlich komplexer auf Tablet und Mobilgerät | Optionaler späterer Komfort, keine notwendige erste Ausbaustufe |
| Vollständiges Inventar im Modal | Liste bleibt optisch im Hintergrund | Lange Tabellen, Tastatur, Scrollflächen und Fehlerbehandlung werden schwieriger | Nur kleine Dialoge für Status, Bestätigung und Bildansicht verwenden |

### Empfohlener Ablauf und Oberfläche

1. **Sammlung finden:** Eine übersichtliche Trefferliste mit Filtern, aktivem
   Filterhinweis, Trefferzahl, stabiler Sortierung und Pagination. Globale
   Sammlungskarten sind als solche beschriftet und bei Bedarf einklappbar.
   „Filter anwenden“ bleibt eindeutig; geänderte, noch nicht angewandte Werte
   erhalten einen sichtbaren Hinweis. Rücksetzungen sind ausdrücklich erkennbar.
2. **Physische Kopie öffnen:** Ein echter Link führt auf eine eigene Detailseite.
   Oben stehen Bild, Setname, Katalognummer und Box-ID. Die Box-ID identifiziert
   die eigene Kopie; gleiche Setnummern dürfen nicht zusammenfallen. Eine
   separate Anzeige trennt den manuell gesetzten Setstatus vom berechneten
   Teilefortschritt. Keine komplette Sammlungsübersicht über dem Arbeitsbereich.
3. **Teile bearbeiten:** Abschnitte für reguläre Teile, Ersatzteile und
   Minifiguren mit nachvollziehbaren Mengen. Suchtext, „nur fehlende Teile“,
   geöffnete Abschnitte, aktuelle Zeile und Scrollposition bleiben bei einem
   Zwischenspeichern erhalten. Eine vollständig gewordene Zeile darf den Fokus
   bei aktiver Fehlteileansicht nicht unvermittelt verlieren.
4. **Speichern und weiterarbeiten:** Ein dauerhaft erreichbarer Hauptknopf
   „Speichern“ bestätigt alle zu diesem Zeitpunkt erfassten Änderungen und lässt
   dieselbe Box mit derselben Arbeitsposition offen. Ein wiederholter Klick
   erzeugt keinen Navigationswechsel und keine doppelte Buchung.
5. **Zur Trefferliste zurückkehren:** Ein eigener sekundärer Link führt zur
   Herkunftsliste. Filter, Gruppierung, Sortierung, Seite und Seitengröße bleiben
   erhalten. Die Liste lädt aktuelle Fortschritte und fokussiert die verlassene
   Box. Ist diese nach einer Änderung nicht mehr auf dieser Seite, bleiben die
   Filter erhalten und ein sachlicher Hinweis erklärt die fehlende Zeile; der
   Fokus landet bei den Ergebnissen oder einem passenden Nachbartreffer.

Eine dauerhaft sichtbare Speicheranzeige unterscheidet mindestens:

- „Ungespeicherte Änderungen“ – auch ein noch fokussiertes geändertes Feld zählt.
- „Wird gespeichert …“ – Bestätigungen sind noch ausstehend.
- „Alle Änderungen gespeichert“ – nur wenn Mengen, Status und bestätigte
  Sammeländerungen den aktuellen angezeigten Werten entsprechen.
- „Speichern fehlgeschlagen – Eingaben bleiben erhalten“ mit erreichbarem Retry.

Bereits bestätigte automatische Mengenspeicherungen bleiben als solche erkennbar,
wenn ein späterer Status-/Gesamtspeichervorgang fehlschlägt. Ein Fehler darf nicht
behaupten, alle vorherigen Saves seien zurückgerollt. Bestehende bewährte
Einzelmengen-Saves bleiben nutzbar; es braucht keine zweite konkurrierende
Speicherwarteschlange. Beim bewussten Verlassen mit offenen Entwürfen stehen
„Speichern und zurück“, „Verwerfen und zurück“ und „Hier bleiben“ zur Wahl.

Sammelaktionen gehören in „Weitere Aktionen“. Vor Anwendung werden Umfang,
betroffene Teilarten und ausgeblendete Zeilen genannt. „Alle auf 0 setzen“ braucht
eine eindeutige Bestätigung. Eine Vorschau ist noch kein gespeichertes Ergebnis.
Vor dem Bestätigen muss der Entwurf abbrechbar sein; eine dauerhafte Undo-Historie
nach dem Speichern wäre eine gesonderte Persistenzfunktion und ist nicht zugesagt.

### Vorgeschlagene technische Grenzen

- Neue HTML-Route beispielsweise `/set_maintain/<user_set_id>/details` ergänzen.
  Das bestehende `/set_maintain/<user_set_id>` liefert weiterhin JSON und wird
  nicht still in HTML umgewandelt. Vorhandene Mengen-, Etiketten- und
  Lagerverträge erhalten.
- Flask/Jinja und Vanilla JavaScript beibehalten. Datenaufbereitung und
  Speichervalidierung wiederverwenden beziehungsweise fachlich aus dem großen
  Routenmodul herauslösen; kein zweiter unabhängiger Inventarschreiber.
- Bei erfolgreichem Formularsave auf dieselbe Detailseite zurückführen oder dort
  eine bestätigte Antwort verarbeiten. Validierungsfehler zeigen dieselben
  Entwürfe mit feldnahen Hinweisen. Ein bewusstes Verlassen ist ein anderer
  Navigationsvorgang. Ein einfaches Reload nach Save allein erhält noch keine
  Teilefilter, offenen Abschnitte oder Arbeitsposition.
- Herkunftskontext aus erlaubten, typisierten Filterwerten neu aufbauen. Keine
  ungeprüften absoluten `next`-/Referer-Ziele übernehmen. Direkte Detaillinks
  ohne Herkunft bekommen einen sinnvollen Link zur Sammlung.
- Globalen Sortierzustand über explizite URL-Parameter und serverseitige Ordnung
  abbilden. Bei Browser-Zurück nach Änderungen veraltete gecachte Ergebnisse
  aktualisieren; nicht blind `history.back()` für jeden Rückweg verwenden.
- Vorhandene ausstehende Einzel-Saves abwarten, ohne neue Sammelentwürfe dabei
  versehentlich als Einzeländerungen zu senden. Eine bestätigte Sammelaktion
  vollständig validieren und innerhalb der gewählten physischen Kopie speichern.
- Feldnamen für reguläre und Minifigurenteile weiterhin getrennt halten.
  Mengeneingaben bekommen zugängliche Namen aus Teil, Farbe und Sollmenge.
  Enter-Navigation erhalten; Retry, Aktionen und Zurück bleiben per Tastatur
  erreichbar. Kleine Bildschirme brauchen begrenzte Tabellen-Scrollbereiche
  oder eine geeignete mobile Darstellung statt Dokumentüberlauf.
- Für diese Navigationsänderung ist zunächst keine Schemaänderung erforderlich.
  Gleichzeitige Änderungen in unabhängigen Browsern bleiben ein eigenes
  Konfliktthema und werden nicht durch eine neue Seite automatisch gelöst.

### Umsetzung und Abnahme eines späteren Auftrags

**Erste Priorität:** Speichern und Verlassen trennen, Entwürfe bei Fehlern
erhalten, Boxidentität sichtbar machen und die bestätigten Minifigurenfehler
absichern. Rückkehrkontext gehört von Anfang an dazu, nicht erst in eine spätere
Komfortphase. Danach Tabellen, Tastatur-/Touch-Bedienung, Gruppierung und
globale Sortierung zusammenhängend verbessern. Lagerortbearbeitung vor weiterer
Verwendung strukturiert reproduzieren und separat nach ihren Datenregeln sichern.

Als verbindliche Abnahmeszenarien werden vorgeschlagen:

1. Von einer gefilterten Seite 2 eine von zwei gleichen Katalogsets öffnen,
   dreimal Mengen ändern und speichern; stets dieselbe Box/Teilezeile und
   Arbeitsposition behalten. Die andere physische Kopie bleibt unverändert.
2. Nach Reload oder direktem Detaillink dieselbe Box öffnen können. Nach Save
   und explizitem Zurück sowie Browser-Zurück aktuelle Treffer mit ursprünglichem
   Filter-/Sortier-/Seitenzustand sehen.
3. Nach Status- oder Mengenänderung aus dem aktiven Filter fallen: keine
   automatische Filterlöschung, nachvollziehbarer Hinweis, stabiler Fokus und
   gültige Pagination auch bei weniger Ergebnisseiten.
4. Netzwerk-/Validierungsfehler und ausstehende Saves: Entwürfe bleiben erhalten,
   keine falsche Gesamtbestätigung, Retry ohne falschen Setwechsel. Während einer
   laufenden Einzeländerung eine Sammelvorschau starten und wieder abbrechen;
   dabei keine unbestätigten Sammelwerte speichern.
5. Reguläre Teile, Ersatzteile, Minifigurenteile sowie ausgeblendete Zeilen
   korrekt zählen, vollständig markieren und filtern. Die Fehlteileansicht darf
   den aktuellen Eingabefokus nicht verlieren.
6. Tastatur und 390-Pixel-Ansicht prüfen; zusätzlich echter Tablet-/iPad-Test für
   Bildschirmtastatur und Safari, wenn das Zielgerät verfügbar ist. Einen großen
   repräsentativen Teilebestand mit begrenzten Abfragen und Ladezuständen prüfen.

### Tatsächlich ausgeführte Prüfung und Grenzen

Zwei unabhängige Rollenreviews für Usability und Navigationsarchitektur,
Quellcode-/Dokumentabgleich und 24 bestehende Node-Prüfungen (Navigation,
Speicherwarteschlange, Detaildarstellung) bestanden. Diese Unit-Tests bilden DOM
und Netzantworten vereinfacht nach und sichern die neu gefundenen Probleme nicht
vollständig ab.

Ein zusätzlicher temporärer Edge-Prüflauf verwendete die gemeinsame isolierte
Flask-Testanwendung mit In-memory-SQLite, 26 synthetischen Setkopien, einem
regulären Teil und einem Minifigurenteil. Er bestätigte Kontextverlust nach
erfolgreichem Save, denselben Redirect bei Validierungsfehler, erhaltene Filter
beim internen Zurück, Schließen der Details bei Reload, fehlende sichtbare
Boxidentität/Fokusführung, beide Minifigurenprobleme sowie 650 Pixel Dokumentbreite
bei 390 Pixel Viewport. Die gespeicherten Werte wurden in der temporären Datenbank
kontrolliert. Keine JavaScript-Laufzeitfehler im erfolgreichen Prüflauf.

Keine Tests mit realen Nutzern, Screenreadern, echtem iPad oder dem produktiven
Schreibablauf. Ladezeit-/Lastbefunde und die Lagerortproblematik sind
Quellcodebefunde, keine gemessenen Live-Benchmarks oder ausgeführten
Produktivänderungen. Zum Zeitpunkt dieses Analyseabschnitts war der Vorschlag
noch nicht implementiert.

### Umgesetzter Kern und Abschlussprüfung (22. November 2026)

Der anschließend beauftragte Kern ist umgesetzt: eigener HTML-Arbeitsbereich
pro physischer Box, Speichern ohne Navigation, validierter Rückweg mit
Filter-/Sortier-/Seitenkontext, Fokus- und Positionswiederherstellung sowie
korrekte Sammelaktionen und Mengenfilter für Minifigurenteile. Auch vorhandene
kopieneigene Minifigurenteile ohne passende Figur werden auf der HTML-Seite
bearbeitbar angezeigt. Der bisherige JSON-Vertrag und die Figurenzuordnungen
bleiben unverändert.

Die neue Seite verwendet bewusst ein einheitliches explizites Speichern für
Mengen, Setstatus und Sammelentwürfe statt der bisherigen Mischung aus
automatischen Einzel-Saves und offenen Formularfeldern. Alte Einzelmengen- und
Formularverträge bleiben kompatibel. Sichtbarer Entwurfsstatus, Retry und die
Auswahl beim Verlassen sichern diesen Ablauf. Die ursprüngliche Lagerort-
Textbearbeitung wird nicht in die neue Seite übernommen; die Lagerverwaltung
bleibt der Arbeitsbereich für physische Zuordnungen.

Vollständiger Linux-Testlauf: 642 bestanden, 0 fehlgeschlagen, 0 übersprungen,
74,46 % Coverage. 25 Node-Prüfungen und vier umfangreiche Edge-Abläufe bestanden,
darunter tatsächlich beobachtetes Browsercache-Zurück mit erneuter Abfrage,
Seite-2-Kontext, wiederholte Saves ohne Positionsverlust, Netzwerkfehler/Retry,
Entwurfsentscheidungen, Sammelaktionen und 390-Pixel-Bedienung. Ein zusätzlicher
Ladecheck ergab sechs SELECTs sowohl für drei als auch 203 Inventarzeilen.
Eine unabhängige Abschlussprüfung fand zusätzlich Enter-in-der-Suche,
Retry-Fokus und wiederhergestellte Verlassen-Zustände; alle drei Befunde wurden
korrigiert und in den Browsernachweis aufgenommen.

Weitergehende Altlasten des älteren Renderers, echter Geräte-/Screenreader-Test,
Konfliktschutz zwischen unabhängigen Browsern und eine dauerhafte Undo-Historie
sind damit nicht als erledigt erklärt. Aktuelle Bedienung und technische
Verträge stehen in [Benutzeranleitung](../guides/user-guide.md#mengen-speichern-und-setlisten-verwenden)
und [Softwaredesign](../architecture/software-design.md#setliste-und-eigener-arbeitsbereich).

## Vorschlag: Schachteletiketten direkt als PDF (22. November 2026)

**Status: beauftragt und umgesetzt.** Der Nutzer hat die direkte PDF-Erzeugung
für MB-1 und MB-4 und anschließend ausdrücklich die vollständige Entfernung der
alten Vorlagen und des Ersetzungscodes verlangt. Zusätzlich wurden konkrete
Schachtelmaße und die Big Box mit 305 × 229 × 102 mm ergänzt. Der Setetiketten-Endpunkt liefert
jetzt ausschließlich PDF. Das folgende Variantenbild dokumentiert die ursprüngliche
Abwägung; eine zusätzliche DrawIO-Ausgabe ist kein Teil der Umsetzung.

Die bereitgestellte `187_MB-4.drawio` wurde als XML gelesen: ein großes Motiv
mit Settitel und vier beschriftete Seitenstreifen mit Setbildern und Boxnummer.
Die Datei referenziert Bilder extern. Ihre Layoutkoordinaten reichen über die
angegebene Seitenhöhe hinaus; ein neuer Druckbogen muss deshalb Seitenaufteilung,
Bildverhältnis und reale Maße ausdrücklich festlegen, statt alles automatisch
auf eine Seite zu verkleinern. Die Datei wurde in dieser Analyse nicht gerendert
oder physisch gedruckt.

### Abwägung

| Weg | Vorteil | Aufwand und Grenze |
| --- | --- | --- |
| DrawIO automatisch nach PDF exportieren | Vorhandenes frei bearbeitbares Layout mit dem ursprünglichen Renderer weiterverwenden. | DrawIO Desktop unterstützt PDF-Export per CLI; dafür wäre ein zusätzlicher Exportprozess mit passender Installation, Fehlerbehandlung und Prüfung im Dockerbetrieb nötig. Ein funktionsfähiger Headless-Betrieb wurde hier nicht erprobt. |
| Setetiketten direkt mit ReportLab als PDF erzeugen | Gleicher PDF-Baustein wie bei den vorhandenen Lageretiketten; Seitenmaße und Text-/Bildlayout gezielt testen, keine DrawIO-Laufzeit nötig. | Die zwei Schachtellayouts einmal gezielt nachbauen und ihre Millimetermaße sowie einen Ausdruck abgleichen. Freies Bearbeiten einer DrawIO-Datei verändert dieses neue PDF-Layout anschließend nicht automatisch. |

**Angenommene Empfehlung für Brick Manager:** direkte PDF-Erzeugung. ReportLab ist bereits
in `pyproject.toml` enthalten; `services/label_service.py:create_label_sheet_pdf`
verwendet es für A4-Lageretiketten. Dessen Avery-Abmessungen sind allerdings
keine Schachtelmaße und dürfen nicht ungeprüft übernommen werden. Für MB-1 und
MB-4 sind fachlich getrennte Drucklayouts entstanden, kein allgemeiner
DrawIO-Interpreter und keine Erweiterung der bestehenden großen Lageretikettenlogik
um einen Konvertierungsprozess.

### Umgesetzter Ablauf und Nachweis

- Setliste: „MB-1 PDF“, „MB-4 PDF“ und „Big Box PDF“ laden direkt druckbare PDFs;
  Liste, Filter und Position bleiben erhalten. Fehlermeldung und Retry an der
  Zeile bleiben verfügbar, eine Bildwarnung erklärt druckbare Platzhalter.
- MB-1: 150 × 100 mm Deckel und vier 40 mm hohe Seiten im Kreuz auf einer
  A4-Querseite. MB-4: 277 × 190 mm Deckelmotiv, zwei 277 × 40 mm und zwei
  215 × 40 mm Streifen auf zwei A4-Querseiten. Big Box: 277 × 190 mm Deckelmotiv,
  zwei 277 × 92 mm und zwei 219 × 92 mm Seiten auf insgesamt drei Seiten.
  Grundlage sind die Nutzermaße mit mindestens 5 mm Kantenabstand und A4-Limit.
  Dünne Schnittlinien, eingebettete Schriften/Bilder,
  maßhaltige Bildverhältnisse, Umbruch und Verkleinerung langer Titel.
- Geprüfte HTTPS-Bildabrufe mit engen Hosts, Zeit-/Größenlimits und optionalem
  Hash-Cache; Fehler führen zu Platzhaltern und einer ausdrücklichen Warnung.
- Der Endpunkt liefert `application/pdf`; alte XML-Ausgabe, Vorlagen und
  Ersetzungslogik sind entfernt. Der bisherige automatische Druckstatus nach
  Erzeugung bleibt bestehen und ist kein Nachweis physischen Drucks.
- 56 isolierte Prüfungen verwenden echte PDF-Artefakte: Seiten/Abmessungen,
  Schnittmaße/Ränder, Texte/Bilder, Cache-/Netzwerkfehler, Validierung und
  Rollback. Ein Edge-Ablauf bestätigt alle drei Downloads, Bildwarnung, Retry,
  Filter und Druckstatus. Die sechs Beispielseiten mit dem Setbild 71486-1
  wurden mit Poppler gerendert und visuell kontrolliert.

Es gibt auf ausdrücklichen Wunsch keinen Kompatibilitätsexport. Ein Rückbau
würde eine Codeversion vor der Umstellung benötigen; es gibt keine Schemaänderung.
Eine dynamische Vorlagenverwaltung und ein allgemeiner Layouteditor sind nicht
eingeführt. Kein Produktionsneustart oder Schreiben auf die Sammlung für diese
Tests. Ein realer Probeausdruck bei 100 % an den Schachteln steht weiterhin aus.

Grundlagen: [DrawIO-CLI-Export](https://github.com/jgraph/drawio/wiki/FAQ),
[ReportLab-Seiten, Text und Grafik](https://docs.reportlab.com/reportlab/userguide/ch2_graphics/).
