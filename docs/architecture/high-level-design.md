# High-Level-Design

## Zweck und Umfang

Brick Manager verwaltet eine Brick-Sammlung mit Sets, Teilen und Lagerorten. Katalogdaten von Rebrickable unterstützen Suche und Zuordnung; Brickognize unterstützt die bildbasierte Teileerkennung. Das Web-UI umfasst unter anderem Bestandsbearbeitung, Lagerverwaltung, fehlende Teile und Etiketten. Eine JSON-Schnittstelle unterstützt Desktop-Clients.

Dieses Dokument beschreibt den bestehenden Systemzuschnitt. Komponenten und Laufzeitdetails stehen in der [Referenzarchitektur](reference-architecture.md), Implementierungsregeln im [Softwaredesign](software-design.md).

## Systemkontext

| Beteiligter bzw. System | Interaktion |
| --- | --- |
| Sammlungsnutzer im Browser | Jinja-Seiten und JavaScript für Suche, Bestand, Lagerorte und Verwaltung |
| Desktop-Client | Authentifizierte `/api/v1`-Anfragen |
| Rebrickable | Externe Katalog- und Sammlungsintegration |
| Brickognize | Externe Bilderkennung |
| Lokale Ablage | SQLite sowie Dateien für Uploads, Caches, Lookup-Daten und erzeugte Ausgaben |

Der Anwendungsprozess nutzt Flask und APScheduler. Die bestehende Systemgrafik und Komponentenübersicht werden zentral in der [Referenzarchitektur](reference-architecture.md#systemübersicht) gepflegt.

## Hauptabläufe

1. **Sammlung bearbeiten:** Browseranfragen erreichen einen Blueprint; Routen und Services lesen oder verändern Modelle und liefern HTML bzw. JSON. JavaScript aktualisiert betroffene UI-Zustände.
2. **Teile suchen und zuordnen:** Routen kombinieren Kataloginformationen, lokale Lookup-/Lagerdaten und bei Bedarf externe Dienste. Der konkrete Persistenzweg hängt vom Workflow ab; nicht alle Lagerinformationen liegen ausschließlich in SQLite.
3. **Kataloge und Sammlungsdaten synchronisieren:** Import- und Sync-Routen bzw. Hintergrundjobs verwenden Integrationsservices. Austauschbare Katalogdaten und sammlungseigener Zustand müssen getrennt erhalten bleiben.
4. **Ausgaben erzeugen:** Services erstellen unter anderem Etiketten; Bild- und Dateicaches unterstützen die Darstellung. Dateipfade und Fehlerbereinigung gehören zum jeweiligen Vertrag.
5. **Desktop-Zugriff:** Der API-Blueprint prüft Bearer-Zugangsdaten und liefert die vereinbarten JSON-Verträge. Diese Authentifizierung schützt nicht automatisch die Web-UI.

## Qualitätsziele und Grenzen

Sammlungsdaten erhalten, externe Fehler kontrolliert behandeln und die vorhandene Flask-/Jinja-Struktur verständlich erweitern. Änderungen müssen öffentliche Verträge und Bedienabläufe berücksichtigen. Die bestehende Startlogik hat Datenbank- und Scheduler-Seiteneffekte; Details und Testfolgen stehen in der Referenzarchitektur.

Sicherheits- und Betriebsannahmen stehen in der [Konfigurationsreferenz](../reference/configuration.md) und der [Docker-Anleitung](../guides/docker.md). Dieses Dokument erklärt keine öffentliche Bereitstellung für automatisch abgesichert.

## Nachweis und Pflege

Quellen sind `brick_manager/app.py`, `routes/`, `services/`, `models.py`, `templates/` und `static/` sowie die verlinkte Referenzarchitektur. Änderungen an Systemgrenzen, Hauptabläufen oder externen Beteiligten aktualisieren dieses Dokument im selben Arbeitsauftrag. Neue Zielbilder sind als Vorschläge zu kennzeichnen und nach Annahme in den [Architekturentscheidungen](decisions.md) festzuhalten.

## Lagerverwaltung

Die Oberfläche trennt tägliche Aufgaben von Einrichtung: Die Hauptseite zeigt
Boxen und Inhalte pro Fach; Einlagern und Umräumen haben eigene Arbeitsseiten.
Boxgrößen und Fächer mit Beschriftung werden separat konfiguriert. Die Erfassung
des vorhandenen Istbestands und Vorschlagsregeln sind ergänzende Bereiche.
Diese Navigation bildet Aufgaben ab, während die gemeinsame Lagerdomäne erhalten bleibt.

`/warehouse` ergänzt die Sammlung um feste Lagerorte, identifizierbare Behälter,
Magazin-/Schubladenstrukturen, Auflagebeziehungen und gezählte Mengen je Fundort.
Die Regalfront ist ohne Messwerte schematisch. Physische Bestandsmengen bleiben
vom setbezogenen Besitz getrennt. Entwurf und reservierter Plan ändern den
aktuellen Fundort erst nach ausdrücklicher Bestätigung der Bewegung.

Lokale Regeln nutzen historische Katalogvorkommen, bekannte Bedarfe und
Kategorieziele. Historisch geeignete Varianten mit unbekanntem Eigenbedarf werden
zur manuellen Archivprüfung angezeigt; bei Teileaufnahme bleibt das
Kategorieregal Standard. Externe Modelle oder zusätzliche KI-Dienste sind dafür
nicht erforderlich. Details: [Softwaredesign](software-design.md),
[Lageranleitung](../guides/warehouse.md), [Umsetzungsabnahme](../plans/storage-acceptance.md).

## Zuverlässige Sammlungsbearbeitung

Die Setliste dient zum Finden, Filtern und Sortieren; die eigene Detailseite
einer physischen Setkopie zum Bearbeiten. Speichern bestätigt Mengen und Status
gemeinsam und hält den Arbeitsbereich offen. Erst eine ausdrückliche Rückkehr
zeigt die aktualisierte Liste mit dem bisherigen Filter-/Positionskontext.
Offene Entwürfe und fehlgeschlagene Bestätigungen bleiben sichtbar und
korrigierbar. Verschiedene eigene Kopien derselben Katalognummer bleiben getrennt.

Die Schachteletiketten für MB-1, MB-4 und Big Box werden direkt als druckfertige PDFs
erzeugt. Setbilder, Titel und Boxnummern sind enthalten; ein externer Editor
oder manueller Export ist nicht mehr nötig. Feste Schnittmaße und getrennte
Deckel-/Seitenlayouts halten die Ausgabe maßhaltig. Fehlende Bilder werden
erklärt, Erzeugungsfehler können ohne Verlust des Listenkontexts erneut versucht
werden. Druck bei 100 % und ein Probeausdruck bleiben für die physische Passung nötig.

Sammlungszeilen werden nach Datensatztyp und interner ID unterschieden, damit
reguläre und Minifigurenteile mit gleicher Nummer nicht verwechselt werden.
Mengenänderungen bestätigen die tatsächlich gespeicherten Werte; fehlende oder
mehrdeutige Batchziele führen ohne Teiländerung zu einem erklärten Fehler.
Browserwarteschlangen erhalten die neueste Eingabe und machen Speicherfehler
sichtbar. Parallele unabhängige Sitzungen benötigen weiterhin eine eigene
Versions-/Konfliktstrategie.

Übersichten berechnen Summen direkt in der Datenbank für die sichtbare Seite,
statt vollständige Inventare für reine Zähler zu laden. Geplante Sicherungen
verwenden konsistente SQLite-Snapshots einschließlich bestätigter WAL-Daten.
Die Umsetzung folgt weiterhin Blueprint, Service, Modell und Vanilla JavaScript;
Details und stufenweiser Folgeplan stehen im
[Softwaredesign](software-design.md#sammlungsstabilität-und-skalare-übersichten)
und [Verbesserungsplan](../plans/architecture-usability-improvements.md).
