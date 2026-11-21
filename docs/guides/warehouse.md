# Lagerverwaltung

Die Lagerverwaltung ist unter `/warehouse` erreichbar und in der Navigation verlinkt. Sie verwaltet feste Orte, bewegliche Einheiten und gezählte Bricks je Fundort getrennt von den setbezogenen Besitzmengen. Die bisherige manuelle Ortszuordnung bleibt für eindeutige unstrukturierte Altzuordnungen nutzbar.

## Start und vorhandene Zuordnungen

### Die passende Arbeitsseite wählen

Die Lagerverwaltung trennt tägliche Arbeit und Einrichtung. Alle Bereiche haben
eigene URLs und eine gemeinsame Navigation; ein Seitenwechsel setzt keine
Lageränderung in Gang.

| Arbeitsseite | Aufgabe |
| --- | --- |
| **Übersicht** (`/warehouse`) | Fach auswählen, Boxen und deren Inhalte öffnen, Boxetiketten vormerken und den Sammeldruck aufrufen |
| **Einlagern** (`/warehouse/intake`) | Teil und Farbe suchen, Zielbox und Menge festlegen, neue Zugänge planen und anschließend physisch bestätigen |
| **Aufräumen** (`/warehouse/reorganize`) | Fach auf Archivkandidaten prüfen, Teilmengen oder ganze Boxen verschieben und Aufträge bestätigen |
| **Boxgrößen** (`/warehouse/box-types`) | Behältertypen und ihre Maße anlegen oder ändern; zusätzliche Stapelregeln bei Bedarf öffnen |
| **Regale & Fächer** (`/warehouse/locations`) | Zonen, Regale und Fächer pflegen, Fachmaße ändern und Fachbeschriftung drucken |
| **Bestand erfassen** (`/warehouse/capture`) | Vorhandene Boxen, Aufstellungen und Inhalte erstmalig erfassen beziehungsweise zählen |
| **Regeln** (`/warehouse/settings-page`) | Kategorieziele, geplante Sets und Archivkriterien verwalten |

Die Übersicht enthält keine Einrichtungs- oder Bewegungsformulare.
Mess- und Stellflächenhinweise lassen sich bei Bedarf unter „Platz und
Messstatus prüfen“ öffnen. Bestätigte Boxkarten zeigen bis zu drei
Inhaltsvarianten als Vorschau; die vollständige Liste steht in den Boxdetails.
Die Bewegungsseiten zeigen nur die zur gewählten Aufgabe passenden Felder. Einlagern
verwendet direkt den Zugangsvorgang; Quelle und Stapelposition sind dafür nicht nötig.
„Behälter zuordnen“ an einer bisherigen Beschriftungsgruppe öffnet die
Bestandserfassung mit der ausgewählten Inhaltszeile.

Für den ersten Aufbau: zunächst **Boxgrößen**, dann **Fächer**, danach
**Bestand erfassen** verwenden. Neue physische Zugänge anschließend über
**Einlagern** buchen. Vorhandenen Bestand nicht als neuen Zugang doppelt erfassen.
Die Standardtypen werden erst durch den ausdrücklichen Einrichtungsbutton angelegt.

Unter **Regeln → Kategorieziele** die Kategorie nach ihrem Katalognamen auswählen.
Die Auswahl ist alphabetisch sortiert und beginnt mit „Kategorie wählen“.
Auch gespeicherte Kategoriezuordnungen zeigen den Namen. Kategorie-IDs müssen
nicht nachgeschlagen oder eingegeben werden. Ohne importierte Kategorien bleibt
das Speichern deaktiviert und ein Hinweis nennt den leeren Teilekatalog.
Liefert der laufende Server die Kategorienliste noch nicht, erscheint stattdessen
ein Ladefehler mit Hinweis auf die Aktualisierung der Anwendung. Ein Neuimport
ist dafür nicht erforderlich. Nach Laden des aktuellen Servercodes die Seite
neu laden; die vorhandenen Namen werden wieder angeboten.

Fachlabels enthalten die lesbare Lageradresse. In **Fächer** die gewünschten
Fächer auswählen und die Druckansicht öffnen. Sie ist für normales Papier und
anschließendes Zuschneiden gedacht; die Avery-Bögen für Boxetiketten bleiben
auf der bestehenden Etikettendruckseite verfügbar.

1. Unter **Boxgrößen → Mit Standardgrößen starten → Standardtypen ergänzen** die im Lagerplan genannten Behältertypen anlegen, ohne vorhandene Typen zu überschreiben. Die übernommenen Produktmaße sind noch keine bestätigten Vor-Ort-Messungen.
2. Zone (Aktiv oder Archiv), Regal und Fach mit den vorhandenen Beschriftungen anlegen. Das reale Pilotfach ist frei wählbar; Regal 1/Fach 5 ist nur ein Beispiel.
3. Boxen/Becher oder Magazine mit ihren echten Etiketten erfassen. Etiketten sind nicht eindeutig; interne IDs unterscheiden gleich beschriftete Einheiten. Nummernlücken bleiben erhalten.
4. Bestehende Zuordnungen erscheinen im passenden Fach als gestrichelte Beschriftungsgruppen mit ihren bisherigen Boxetiketten. Gleiche Rohbeschriftungen werden gemeinsam angezeigt; dies bestätigt noch keinen einzelnen physischen Behälter. Fehlende oder mehrdeutige Fundorte stehen separat unter „Fundort noch zuordnen“. Vorhandene Rohtexte und Nummernlücken bleiben erhalten. Keine Menge wird aus Setbeständen geschätzt.
5. „Bestand zählen“ protokolliert eine Mengenfeststellung mit Begründung. Ein ungeprüfter Inhalt ist nicht leer. „Inhalt vollständig erfasst“ erst nach Sichtprüfung setzen.

Eine Beschriftungsgruppe öffnet ihre Teile, Farben, Notizen und Mengen; unbekannte Mengen heißen „ungezählt“. Über „Behälter zuordnen“ wird die bestehende Inhaltszeile im Erfassungsformular ausgewählt. Erst nach physischer Prüfung einen erfassten Behälter wählen und speichern. Listen zeigen zunächst 24 Gruppen bzw. 50 Inhaltszeilen; weitere Einträge lassen sich einblenden, größere Gruppenlisten nach Beschriftung durchsuchen. Regal-, Fach- und Boxnummern werden numerisch sortiert, ohne die Originaletiketten umzuschreiben. Auch die vollständigen Lagerort-Auswahllisten (etwa für Kategorieziele) folgen dieser Reihenfolge: Bereich, Regalnummer, darunter die zugehörigen Fächer; 2 steht vor 10.

Neue physische Zugänge über den Auftragstyp „Bricks aufnehmen“ buchen. Erst planen, anschließend die tatsächliche Einlagerung bestätigen. Die Zählkorrektur dient dem Bestandsabgleich und ist keine Umlagerung. Beide verändern keine `have_quantity`-Werte eigener Sets.

## Regalfront, Stapel und Schubladen

Bis zum Abschluss der Startabfrage zeigt die deaktivierte Fachauswahl „Fach wird geladen …“. „Alle Fächer“ ist kein anfänglicher HTML-Standardwert. Eine Dateiversion in der Script-URL verhindert, dass ältere JavaScript-Fassungen im Browsercache die neue Auswahlsteuerung überlagern.

Beim Öffnen wird das zuletzt gewählte einzelne Fach in diesem Browser wiederhergestellt. Beim ersten Besuch oder wenn das gespeicherte Fach nicht mehr existiert, startet die Übersicht mit dem ersten numerisch sortierten Fach. „Alle Fächer“ bleibt manuell auswählbar, wird aber nicht zum Startstandard. Dadurch werden beim Einstieg nur die Karten und katalogangereicherten Altinhalte eines Fachs geladen. Ungeklärte Gruppen bleiben sichtbar; ihre Inhaltslisten werden erst beim Öffnen nachgeladen. Die vollständige Inhaltsauswahl für Erfassungs- und Umbuchungsformulare wird bei Bedarf geladen. Ohne verfügbaren Browserspeicher funktioniert die Auswahl weiterhin; beim nächsten Besuch startet dann wieder das erste Fach.

Bestehende Boxkarten zeigen bis zu drei unterschiedliche Teil-/Farbvarianten mit Katalogbild, Name und Teilenummer; weitere Varianten sind angegeben und in den Details einsehbar. Fehlende oder nicht ladbare Bilder erhalten ein Ersatzsymbol. Die Bildauswahl verwendet zuerst eine passende Inventarfarbe, dann das Teile-Stammbild und schließlich ein anderes vorhandenes Inventarbild. Eine Ersatzfarbe ist keine Bestätigung der tatsächlichen Boxfarbe. Katalogbilder können von ihrem gespeicherten externen Bildanbieter geladen werden.

Die Beschriftungsgruppen der Regalfront zählen **unten links nach oben, dann in der nächsten Spalte weiter**. „Boxen je Spalte“ wählt zwei bis sechs Zeilen, zunächst drei. Diese Anzeigeoption bestätigt keine tatsächliche Stapelung. Die Listenansicht liest sich weiterhin aufsteigend von oben nach unten. Bei vielen Spalten lässt sich die schematische Front seitlich scrollen; Etikettennummern bleiben unverändert.

Regalfront und Listenansicht zeigen Fächer und Einheiten mit Füllzustand. Die schematische Ansicht macht ohne Messwerte keine Passzusage. Eine Teileabfrage führt zu allen bestätigten Fundorten und stabilen Einheitenlinks.

Bestehende Stapel unten beginnend erfassen, dann jeweils die nächste Einheit mit der vorherigen als Unterlage. Eine Aufstellung kann als ungeprüfte Beobachtung erfasst werden; diese ist keine verifizierte Stapelvorlage. Eine bereits aufgestellte Einheit wird ausschließlich über einen Bewegungsauftrag verschoben.

Sichtlagerboxen nur innerhalb derselben Größe stapeln. Eine gerichtete Stapelregel wird ausdrücklich mit ihrer Quelle, Höhenzunahme und gegebenenfalls Anzahl-/Höhengrenze bestätigt. Lose Auflage ist eine eigene Beziehung, insbesondere bei CYEER. Feinkost-Kombinationen und sichere Stapelhöhen vor Ort prüfen. Offene Front kann Inhaltszugriff ermöglichen; die Entnahme der ganzen unteren Box kann trotzdem das Abnehmen der oberen erfordern.

Die zwei Standardmagazine erzeugen 30 bzw. 9 Schubladen. Jede Schublade kann ganz oder mit zwei/drei adressierbaren Unterteilungen verwendet werden. Eine belegte Struktur lässt sich erst nach bestätigter Umbuchung des Inhalts ändern; erneutes Bestätigen derselben Unterteilung erhält die IDs. Oberhalb eines Magazins stehende Boxen sind eigene Auflagen.

## Bewegen, Umbuchen und Überlauf

Ein Entwurf zeigt Quelle und Ziel, verändert aber den Istfundort nicht. „Planen“ reserviert die beteiligten Einheiten. Reservierungen sind bewusst konservativ: gleichzeitig abhängige Arbeiten werden nacheinander durchgeführt. Bei mehreren Veränderungen eines Fachs pro tatsächlich ausgeführter Bewegung bestätigen; ein Abbruch macht bereits bestätigte Schritte nicht rückgängig.

- Ganze Einheit: Etikett und Inhalt folgen ihrer ID. Aufliegende Einheiten zuerst abnehmen bzw. in eigenen Schritten bewegen.
- Teilmenge: Quelle und Ziel benötigen eindeutige Teil-/Farbidentitäten und bekannte Mengen. Zielbestand wird addiert, nicht überschrieben. Ungeklärten Zielbestand zuerst abgleichen.
- Größerer Behälter: Zielbox platzieren, Inhalte umbuchen, danach die leere alte Hülle ausdrücklich entfernen oder anderswo aufstellen.
- Zweiter Ort: Nur die gewählte Menge umbuchen; Restmenge und ursprünglicher Ort bleiben sichtbar.

„Physisch bestätigen“ erst nach tatsächlicher Ausführung verwenden. Unbekannte Passung und Zielkapazität müssen dabei vor Ort geprüft sein. Erneute Bestätigung bucht nicht doppelt; veraltete Revisionen und konkurrierende Pläne werden abgewiesen. Eine Rückbewegung ist ein neuer Auftrag.

Die Platzwirkung unterscheidet leeren Inhalt, niedrigeren Stapel und entfernte Basis. Eine leere Hülle belegt weiter Stellfläche; eine entfernte obere Box gibt keine Grundfläche frei. Getrennte Lücken werden nicht zu einer breiten Lücke addiert.

## Messwerte und Vorschläge

Fachbreite, Tiefe, Höhenprofil und linke Positionen in Millimetern pflegen. Das Höhenprofil gilt als konservative Freihöhe über die gesamte nutzbare Tiefe. Wenn eine Schräge tiefenabhängig ist, die minimale Freihöhe messen oder den Messstatus unbekannt lassen. Auflagenpositionen beziehen sich auf die jeweilige Auflagefläche; Positionen auf Fachböden auf die linke Fachkante. Unter Dachschrägen wird die gesamte Breite einschließlich dazwischenliegender Messpunkte geprüft.

Noch nicht physisch zugeordnete Bestandszeilen im Fach verhindern eine sichere Aussage über freie Stellfläche und Passung. Bekannte Regalzuordnungen mit unbekanntem Fach gelten konservativ für alle Fächer dieses Regals.

Unbekannte Maße, Nachbarpositionen, Stapelhöhenzunahmen oder Entnahme-/Lastgrenzen verhindern eine sichere Passzusage. Bekannte Kollisionen lassen sich nicht durch eine Bestätigung übergehen. Nutzbare Auflage und Belastbarkeit sind keine aus Volumen abgeleiteten Werte.

Historische Archivprüfung verwendet die exakte Teilenummer/Farbe und zählt unterschiedliche echte Sets. Startwerte: höchstens zwei bekannte Sets, letztes bekanntes Set mindestens zehn Jahre alt, validierter Katalog höchstens 90 Tage alt. Diese Regeln sind unter Einstellungen veränderbar. Verwandte Varianten werden nicht automatisch gleichgesetzt.

Bei unbekanntem Eigenbedarf erscheinen historisch geeignete Varianten mit **„Eigenbedarf unbekannt · bitte prüfen“**. Der Nutzer entscheidet beim Aufräumen. Bekannter Bedarf und „griffbereit halten“ schützen Inhalte. Eine ganze Box wird nur bei vollständig erfasstem geeignetem Inhalt geprüft; bei gemischtem Inhalt werden Teilumbuchungen angeboten. Konkretes Archivziel und Kapazität bleiben zu prüfen.

Bei der Teileaufnahme bleibt bei unbekanntem Eigenbedarf das konfigurierte Kategorieregal Standard, auch bei passendem Archivbestand. Neue Varianten bleiben griffbereit. Fehlende Farbe, Jahre, Inventarzuordnung, Bedarf oder Kategoriezuordnung werden erklärt. Ein Regalstandard ist noch keine freie Box. Vorschläge können manuell übersteuert werden; Bestands- und Stapelinvarianten bleiben verbindlich.

Eigene geplante Sets werden separat von besessenen Sets gepflegt. Eine leere Planliste bedeutet erst nach ausdrücklicher Prüfung „kein bekannter geplanter Bedarf“. Neue Pläne oder Katalogimporte machen die vorherige Bedarfsprüfung ungültig. Katalogimporte protokollieren ihren Gesamtstatus dauerhaft; fehlgeschlagene oder überlappende Läufe ermöglichen keine belastbare historische Freigabe.

## Etiketten und Schutz

Einzelne Einheiten über ihre ID auswählen und das Etikett herunterladen. Gleiche sichtbare Nummern erzeugen unterschiedliche technische Ausgabedateien. Den Druckstatus erst nach erfolgreichem Druck bestätigen. Bestehende Etikettennummern werden nicht neu durchnummeriert.

Schreibende Lageranfragen benötigen das CSRF-Token der aktuellen Sitzung. Die bestehende Desktop-Bearer-Authentifizierung bleibt gültig. Alte Schreibwege dürfen strukturierte oder mehrdeutige Fundorte nicht überschreiben oder löschen und verweisen stattdessen auf die Lagerverwaltung. Das Web-UI ist weiterhin für den bestehenden abgesicherten Betriebsrahmen vorgesehen; eine öffentliche Bereitstellung ist keine Folge dieser Funktion.

Die Inhaltstabellen in den Behälterdetails zeigen ebenfalls eine Bildspalte mit Teilevorschau oder Ersatzsymbol, sowohl für bestehende Beschriftungsgruppen als auch für bestätigte Behälter. Lange Teilenamen dürfen umbrechen; kurze Angaben wie Farbe und Menge bleiben zusammenhängend. Auf schmalen Bildschirmen sind die Details horizontal scrollbar.

## Etiketten zum Neudruck vormerken

Jede Boxkarte hat eine separate Checkbox **„Etikett neu drucken“**. Die Vormerkung
bleibt über Seitenwechsel, Browserneustart und Serverneustart erhalten. Sie ändert
weder Fundort noch Menge und ist vom bisherigen Druckstatus getrennt. Unvollständige
Altfundorte benötigen zuerst eine Schrank-/Fach-/Boxzuordnung. Gleich beschriftete
bestätigte Behälter werden anhand ihrer internen IDs unterschieden.

Der Link **„Vorgemerkte Etiketten gesammelt drucken“** führt zur bestehenden
Etikettendruckseite. Dort erstellt **„Alle vorgemerkten drucken · PDF“** einen
mehrseitigen Avery-3474-Bogen (bis zu 1000 Vormerkungen je Download). Startposition
und Druckversatz werden aus den vorhandenen Bogendruck-Einstellungen übernommen.
Ein Download entfernt keine Vormerkung und gilt noch nicht als erfolgreicher Druck.
Erst **„Erfolgreichen Druck bestätigen“** setzt den Druckstatus der ausgewählten
Boxen und entfernt genau deren Vormerkungen. Nach Neuladen der Druckseite ist für
die Bestätigung ein erneuter Download erforderlich.

Bei verändertem Boxinhalt oder erneuter Vormerkung seit dem Download lehnt die
Anwendung eine veraltete Bestätigung ab: Liste neu laden und ein aktuelles PDF
herunterladen. Fehlgeschlagene Downloads erhalten alle Häkchen. Einzelne
Vormerkungen können ohne Druckbestätigung entfernt werden, auch wenn ihr
ursprünglicher Fundort inzwischen nicht mehr existiert. Die bisherigen manuellen
Druckauswahlen bleiben nutzbar und bestätigen keine separate Vormerkung.
