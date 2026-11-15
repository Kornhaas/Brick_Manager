# Lagerverwaltung

Die Lagerverwaltung ist unter `/warehouse` erreichbar und in der Navigation verlinkt. Sie verwaltet feste Orte, bewegliche Einheiten und gezählte Bricks je Fundort getrennt von den setbezogenen Besitzmengen. Die bisherige manuelle Ortszuordnung bleibt für eindeutige unstrukturierte Altzuordnungen nutzbar.

## Start und vorhandene Zuordnungen

1. „Standardtypen anlegen“ erstellt die im Lagerplan genannten Behältertypen ohne vorhandene Typen zu überschreiben. Die übernommenen Produktmaße sind noch keine bestätigten Vor-Ort-Messungen.
2. Zone (Aktiv oder Archiv), Regal und Fach mit den vorhandenen Beschriftungen anlegen. Das reale Pilotfach ist frei wählbar; Regal 1/Fach 5 ist nur ein Beispiel.
3. Boxen/Becher oder Magazine mit ihren echten Etiketten erfassen. Etiketten sind nicht eindeutig; interne IDs unterscheiden gleich beschriftete Einheiten. Nummernlücken bleiben erhalten.
4. Bestehende Zuordnungen erscheinen als ungeklärt, bis sie nach physischer Prüfung einer Einheit zugeordnet werden. Vorhandene Rohtexte bleiben erhalten. Keine Menge wird aus Setbeständen geschätzt.
5. „Bestand zählen“ protokolliert eine Mengenfeststellung mit Begründung. Ein ungeprüfter Inhalt ist nicht leer. „Inhalt vollständig erfasst“ erst nach Sichtprüfung setzen.

Neue physische Zugänge über den Auftragstyp „Bricks aufnehmen“ buchen. Erst planen, anschließend die tatsächliche Einlagerung bestätigen. Die Zählkorrektur dient dem Bestandsabgleich und ist keine Umlagerung. Beide verändern keine `have_quantity`-Werte eigener Sets.

## Regalfront, Stapel und Schubladen

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

Unbekannte Maße, Nachbarpositionen, Stapelhöhenzunahmen oder Entnahme-/Lastgrenzen verhindern eine sichere Passzusage. Bekannte Kollisionen lassen sich nicht durch eine Bestätigung übergehen. Nutzbare Auflage und Belastbarkeit sind keine aus Volumen abgeleiteten Werte.

Historische Archivprüfung verwendet die exakte Teilenummer/Farbe und zählt unterschiedliche echte Sets. Startwerte: höchstens zwei bekannte Sets, letztes bekanntes Set mindestens zehn Jahre alt, validierter Katalog höchstens 90 Tage alt. Diese Regeln sind unter Einstellungen veränderbar. Verwandte Varianten werden nicht automatisch gleichgesetzt.

Bei unbekanntem Eigenbedarf erscheinen historisch geeignete Varianten mit **„Eigenbedarf unbekannt · bitte prüfen“**. Der Nutzer entscheidet beim Aufräumen. Bekannter Bedarf und „griffbereit halten“ schützen Inhalte. Eine ganze Box wird nur bei vollständig erfasstem geeignetem Inhalt geprüft; bei gemischtem Inhalt werden Teilumbuchungen angeboten. Konkretes Archivziel und Kapazität bleiben zu prüfen.

Bei der Teileaufnahme bleibt bei unbekanntem Eigenbedarf das konfigurierte Kategorieregal Standard, auch bei passendem Archivbestand. Neue Varianten bleiben griffbereit. Fehlende Farbe, Jahre, Inventarzuordnung, Bedarf oder Kategoriezuordnung werden erklärt. Ein Regalstandard ist noch keine freie Box. Vorschläge können manuell übersteuert werden; Bestands- und Stapelinvarianten bleiben verbindlich.

Eigene geplante Sets werden separat von besessenen Sets gepflegt. Eine leere Planliste bedeutet erst nach ausdrücklicher Prüfung „kein bekannter geplanter Bedarf“. Neue Pläne oder Katalogimporte machen die vorherige Bedarfsprüfung ungültig. Katalogimporte protokollieren ihren Gesamtstatus dauerhaft; fehlgeschlagene oder überlappende Läufe ermöglichen keine belastbare historische Freigabe.

## Etiketten und Schutz

Einzelne Einheiten über ihre ID auswählen und das Etikett herunterladen. Gleiche sichtbare Nummern erzeugen unterschiedliche technische Ausgabedateien. Den Druckstatus erst nach erfolgreichem Druck bestätigen. Bestehende Etikettennummern werden nicht neu durchnummeriert.

Schreibende Lageranfragen benötigen das CSRF-Token der aktuellen Sitzung. Die bestehende Desktop-Bearer-Authentifizierung bleibt gültig. Alte Schreibwege dürfen strukturierte oder mehrdeutige Fundorte nicht überschreiben oder löschen und verweisen stattdessen auf die Lagerverwaltung. Das Web-UI ist weiterhin für den bestehenden abgesicherten Betriebsrahmen vorgesehen; eine öffentliche Bereitstellung ist keine Folge dieser Funktion.
