# Anwendungsfunktionen

Diese Übersicht beschreibt die dauerhaft vorhandenen Bereiche der Webanwendung. Detailverhalten wird durch die jeweiligen Routen, Templates und Tests definiert; historische Funktionsnotizen befinden sich unter `docs/history/features/`.

| Bereich | Einstieg | Zweck |
| --- | --- | --- |
| Start und Gesundheit | `/`, `/health` | Übersicht und Betriebsstatus |
| Set-Suche und -Pflege | `/set_search`, `/set_maintain` | Katalogsets hinzufügen, physische Kopien und Mengen verwalten |
| Fehlteile | `/missing_parts` | Fehlende reguläre, Ersatz- und Minifigurenteile ermitteln und Mengen erfassen |
| Physisches Lager | `/warehouse` | Behälter, Stapel, Mengen, bestätigte Bewegungen und manuelle Archivprüfung; [Anleitung](warehouse.md) |
| Teile und Lagerorte | `/lookup_part`, `/part_location`, `/box_maintenance` | Teile finden, Lagerplätze pflegen und Boxen verwalten |
| Etiketten | Set- und Boxpflege | Set- und Boxetiketten direkt als PDF erzeugen, Druckstatus führen |
| Datenimport und Synchronisierung | `/import_data`, `/admin/sync` | Rebrickable-Katalog importieren und bewusst angestoßene Abgleiche ausführen |
| Konfiguration | `/token_management` | API-Tokens verwalten |
| Bauanleitungen | `/building_instructions` | Lokale Anleitungsdateien bereitstellen |

## Desktop-API

Der Desktop-Client verwendet die versionierte API unter `/api/v1`. Sie stellt Teile, Setzuordnungen und Lagerorte bereit und erlaubt das Aktualisieren eigener Mengen und Lagerorte. Jeder Request verlangt einen konfigurierten Bearer-Key. Vertragsdetails und Sicherheitsvorgaben stehen in der [Referenzarchitektur](../architecture/reference-architecture.md) und in der [Konfiguration](../reference/configuration.md).

## Bedienungsgrundsätze

Navigation und Arbeitsseiten nutzen ein gemeinsames Indigo-/Türkis-Farbschema,
lokale Bricks-Symbole und gut erkennbare Hauptaktionen. Das Dashboard bleibt der
visuelle Ausgangspunkt. Aktive Bereiche sind hervorgehoben, Tastaturfokus bleibt
sichtbar; die Einstellung „Bewegung reduzieren“ des Systems wird berücksichtigt.

- Mehrere `user_sets` mit derselben Setnummer sind zulässig und repräsentieren physische Kopien.
- Ersatzteile bleiben bei Mengen- und Fehlteilberechnungen von regulären Teilen getrennt.
- Ein Teil kann mehrere Lagerorte haben; Änderungen müssen den betroffenen Ort eindeutig adressieren.
- Externe Abgleiche und Katalogimporte können Daten verändern. Sie werden bewusst angestoßen und ersetzen keine Sicherungsstrategie.

## Boxetiketten drucken

Die Lagerverwaltung besitzt getrennte Arbeitsseiten: **Übersicht** für Boxen und
Inhalte pro Fach, **Einlagern** für neue Zugänge, **Umräumen** für Bewegungen und
Archivprüfung, **Boxgrößen** für Behältermaße und **Fächer** für Lagerstruktur,
Fachmaße und Fachbeschriftung. **Bestand erfassen** dient der erstmaligen Aufnahme
vorhandener Behälter und Inhalte; **Regeln** bündelt Kategorieziele und Archivregeln.
Die [Lageranleitung](warehouse.md) beschreibt den passenden Einstieg je Aufgabe.

Die Boxpflege bietet zwei A4-Formate: Avery 3474 mit 24 Etiketten zu 70 × 37 mm
und Avery Zweckform 3657 mit 40 Etiketten zu 48,5 × 25,4 mm. Das Format vor
dem Herunterladen auswählen; Startposition, freie Plätze, Sammelauswahl und die
Kalibrierlinien passen sich daran an. Die kompakte Variante zeigt ein Bild des
ersten Inhalts, dessen Teilenummer, eine Inhaltszusammenfassung und die Boxnummer.
Bei mehreren Inhalten weist `(+n)` auf weitere Positionen hin. Immer in 100 % /
tatsächlicher Größe und ohne automatische Seitenskalierung drucken.

Die Boxpflege bündelt den Etikettendruck und vorgemerkte Neudrucke in gleich
breiten Karten. Die Tabelle bleibt innerhalb der zentrierten Arbeitsfläche
horizontal scrollbar, statt auf sehr breiten Bildschirmen die gesamte Seite zu
strecken.

## Setetiketten herunterladen

In der Setliste laden **MB-1 PDF**, **MB-4 PDF** und **Big Box PDF** die
Etiketten für die gewählte physische Box direkt als PDF herunter. PDF öffnen
und mit **100 % / tatsächlicher Größe** drucken, ohne „An Seite anpassen“.
Es ist kein zusätzlicher Editor oder Export nötig. Bilder sind im PDF eingebettet.

| Format | Angegebene Schachtelmaße | Druckbogen und Schnittmaße |
| --- | --- | --- |
| MB-1 | 160 × 110 × 50 mm | Eine A4-Seite quer: Deckel 150 × 100 mm, zwei Seiten 150 × 40 mm und zwei Seiten 100 × 40 mm, als Kreuz angeordnet. |
| MB-4 | 320 × 225 × 50 mm | Zwei A4-Seiten quer: Deckelmotiv 277 × 190 mm auf Seite 1; zweimal 277 × 40 mm und zweimal 215 × 40 mm auf Seite 2. |
| Big Box | 305 × 229 × 102 mm | Drei A4-Seiten quer: Deckelmotiv 277 × 190 mm, zwei lange Seiten mit je 277 × 92 mm und zwei kurze Seiten mit je 219 × 92 mm, jeweils eine Seite pro Paar. |

Dünne Umrandungen dienen als Schnittlinien. Grundlage sind die vom Nutzer
angegebenen Schachtelmaße. Mindestens 5 mm Abstand pro Kante und maximal
277 × 190 mm je Etikett lassen alle Bögen auf A4 mit 10 mm Papierabstand drucken.
Die großen Motive und langen Seitenetiketten bedecken deshalb nicht die gesamte
Schachtelfläche. Vor einer Serie einen Ausdruck an der tatsächlichen Schachtel
prüfen.

Die Seitenstreifen von MB-4 und Big Box sind für den Papierschneider ohne
Zwischenraum untereinander angeordnet und teilen ihre horizontalen Schnittkanten.
Alle beginnen bündig 10 mm vom linken Papierrand, auch die kürzeren Streifen.
Zuerst die gemeinsame linke Außenkante und die waagerechten Reihen schneiden,
danach die rechten Kanten auf die jeweilige Breite kürzen. Gleich breite Paare
lassen sich gemeinsam ausrichten. MB-4 hat dadurch drei Zwischenstreifen weniger,
Big Box einen weniger je Seitenbogen; Maße und Seitenzahlen bleiben gleich.
MB-1 liegt bereits ohne Zwischenräume im Kreuz und behält diese Anordnung.

Lange Namen werden
umgebrochen und bei Bedarf verkleinert oder mit Auslassungszeichen gekürzt.
Fehlt das Setbild oder schlägt sein Download fehl, bleibt das PDF druckbar und
enthält einen beschrifteten Platzhalter; die Zeile zeigt zusätzlich eine Warnung.

Liste und Filter bleiben geöffnet. Während der Erzeugung sind beide PDF-Knöpfe
dieser Zeile gesperrt; Fehler stehen direkt daneben und erlauben einen erneuten
Versuch. Nach erfolgreicher Erzeugung zeigt die Zeile weiterhin den automatischen
Druckstatus „Printed“. Das bestätigt die Dateierzeugung, keinen physischen Druck;
das Kontrollkästchen erlaubt die manuelle Korrektur.

## Mengen speichern und Setlisten verwenden

„View“ in der Setliste öffnet eine eigene Detailseite für genau diese physische
Setkopie. Setname, Katalognummer und Box-ID stehen über dem Teilebestand. Derselbe
Katalogeintrag kann mehrfach vorhanden sein; die Box-ID unterscheidet die Kopien.
Die Detailadresse kann direkt geöffnet oder als Lesezeichen gespeichert werden.

Reguläre Teile, Ersatzteile und die Teile jeder Minifigur sind nach Farbnamen
gruppiert. Neben dem Namen steht ein Farbmuster; transparente Farben sind
zusätzlich gekennzeichnet. Die Farbüberschrift klappt ihre Zeilen einzeln auf
und zu. „Farben einklappen/ausklappen“ bedient alle Gruppen. So lässt sich Schwarz
abschließen und Rot gezielt öffnen. Jede Gruppe zeigt, wie viele Positionen ihre
Sollmenge erreicht haben. Die Zähler zählen Teilezeilen, nicht einzelne Bricks.

Zeilen mit gleicher Soll-/Istmenge sind grün mit „Vollständig“ markiert;
abweichende Mengen rot mit Fehlmenge. Ungültige Werte zeigen „Eingabe prüfen“.
Diese Anzeigen folgen sofort dem aktuellen Entwurf; erst der Speicherstatus
bestätigt die dauerhafte Übernahme. Suche und Mengenfilter blenden leere
Farbgruppen aus und öffnen passende Treffer. Eine fehlerhafte Eingabe wird auch
in zuvor zugeklappten Gruppen wieder zugänglich. Speichern erhält die gewählte
Gruppenansicht; ein vollständiges Neuladen öffnet die Farbgruppen wieder.

Auf dieser neuen Arbeitsseite werden Mengen, Sammeländerungen und Setstatus
**erst mit „Speichern“ übernommen**. Der Speicherstatus zeigt offene Änderungen,
den laufenden Vorgang, die Bestätigung oder einen bleibenden Fehler mit
„Erneut speichern“. Der Knopf hält die Detailseite offen: Teilefilter,
geöffnete Abschnitte und Arbeitsposition bleiben erhalten. Neue Eingaben während
einer laufenden Anfrage werden nicht durch deren ältere Antwort überschrieben.
Ganze Mengen von null bis zur Sollmenge sind zulässig; Dezimalwerte und Werte
außerhalb dieses Bereichs werden als Fehler angezeigt. Der gesamte Entwurf einer
Bestätigung gehört zu einer Box und wird zusammen validiert und gespeichert.

Enter in einem Mengenfeld speichert den aktuellen Entwurf und geht nach
erfolgreicher Bestätigung zum nächsten sichtbaren Mengenfeld, Umschalt+Enter zum
vorherigen. Tab wechselt innerhalb des Bestands direkt zum nächsten sichtbaren,
bearbeitbaren Mengenfeld, Umschalt+Tab zum vorherigen. Bilder, zugeklappte
Farbgruppen und ausgeblendete Zeilen werden dabei übersprungen. Tab speichert
keine Mengen. Am Anfang/Ende bleibt der normale Fokuswechsel zu anderen
Bedienelementen möglich; Bildvorschauen bleiben per Tastatur erreichbar.
Enter in der Teilesuche filtert nur und speichert keine anderen
Entwürfe. „Nur abweichende Mengen“ arbeitet auch bei Minifigurenteilen korrekt;
die gerade bearbeitete Zeile bleibt nach einer Bestätigung gegebenenfalls bis
zum Feldwechsel sichtbar.

„Zur Trefferliste“ erhält Suchtext, Filter, Gruppierung, Sortierung, Ergebnisseite
und Seitengröße. Die Liste zeigt aktuelle Werte und führt den Fokus zur
ursprünglichen Box zurück. Ist diese nicht mehr im Ergebnis oder auf derselben
Seite, wird das erklärt, ohne die Filter zu löschen. Beim internen Zurückgehen
mit offenen Eingaben kann man speichern, verwerfen oder auf der Seite bleiben.
Beim Schließen/Neuladen mit offenen Änderungen schützt zusätzlich der übliche
Browserhinweis; eine Wiederherstellung ungespeicherter Entwürfe nach einem
Browserabsturz ist nicht zugesagt.

„Weitere Aktionen“ bietet „Alle als vorhanden markieren“ und „Alle auf 0 setzen“.
Vorher zeigt ein Dialog die Anzahl regulärer, Ersatz- und Minifigurenteilezeilen
sowie ausgeblendeter Zeilen. „Entwurf übernehmen“ verändert noch keine
gespeicherten Mengen; danach ausdrücklich speichern oder den Entwurf verwerfen.
Der Setstatus bleibt eine eigene Angabe und wird nicht aus dem Prozentwert des
Teilebestands abgeleitet. Vorhandene Minifigurenteile ohne passende Figur dieser
Box werden separat angezeigt; ihre Mengen lassen sich bearbeiten, ohne ihre
Zuordnung oder Katalogdaten umzuschreiben.

Lagerorte werden in der Detailseite angezeigt. Zur Pflege der physischen
Zuordnungen dient die Lagerverwaltung; der bisherige Lagerort-Textdialog wird
auf der neuen Seite nicht verwendet.

Die Dashboard-Detailansichten verwenden ebenfalls eine Speicherwarteschlange,
zeigen Fehler mit „Retry save“ und übernehmen die tatsächlich vom Server
bestätigte Menge. Reguläre Teile und Minifigurenteile werden eindeutig
unterschieden, auch bei gleicher interner Nummer. Bei einer mehrdeutigen Anfrage
eines alten Clients wird keine Menge verändert.

Die Setliste berechnet ihre Summen ohne vollständige Teilelisten zu laden.
Die Spaltenlinks sortieren die gesamte Treffermenge; Sortierung und Filter
bleiben auch über Seitengrenzen erhalten. Ein leerer Themenfilter bleibt leer.
Noch nicht angewandte Filteränderungen werden angezeigt; „Apply filters“ wendet
sie an. Die einklappbaren Übersichtskarten zeigen weiterhin die gesamte Sammlung.
