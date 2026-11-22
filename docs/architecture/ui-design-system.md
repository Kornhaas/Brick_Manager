# Einheitliches UI-Konzept

Stand: 22. November 2026. Dieses Dokument legt die gemeinsame Gestaltung für
alle erreichbaren HTML-Arbeitsbereiche fest. Alle 20 von Routen verwendeten
Seitenvorlagen nutzen die gemeinsame Basis. Die Referenz sind Dashboard,
Setpflege und Lagerverwaltung.

## Gestaltungsprinzip

Ein Arbeitsbereich hat dieselbe Navigation, dieselben Inhaltskanten, einen
klaren Seitenkopf und darunter die zur Aufgabe passenden Karten. Eine gemeinsame
Farbpalette allein genügt nicht. Seiten dürfen keine eigenen Navigationen,
globalen Schriftregeln, Markenverläufe oder konkurrierenden Kartensysteme anlegen.
Die Fachlichkeit bestimmt Inhalte und Anordnung, nicht eine neue Designsprache.

## Verbindliche Bausteine

| Baustein | Einheitlicher Vertrag |
| --- | --- |
| App-Rahmen | `base.html`: genau eine Navigation und ein `main` mit Sprunglink; gemeinsame Ressourcen einmal im Dokumentkopf, Bootstrap einmal vor Seitenscripts |
| Inhaltsfläche | Maximal 1440 px; 24 px Innenabstand am Desktop, 16 px mobil; alle Arbeitsbereiche haben dieselben Außenkanten |
| Seitenkopf | Indigo-/Navy-Verlauf, weiße linksbündige Hauptüberschrift, türkisfarbener Bereichshinweis, kurze Beschreibung; einheitliche Iconkachel und optionale Hauptaktion |
| Überblick | Dashboard/Home dürfen mehr Platz für Übersicht und Illustration nutzen; Farben, Typografie, Kanten und Karten bleiben gleich |
| Detailkopf | Setbild und Kopienidentität ersetzen die allgemeine Illustration; gleiche Kopfgestaltung, bestehende Fokus-/Zurück-Verträge bleiben erhalten |
| Karten | Weiße Flächen, dezenter Rand/Schatten, 16 px Radius, einheitliche Innenabstände und neutrale Abschnittsköpfe |
| Aktionen | Indigo für die Hauptaktion, Kontur/neutral für Nebenaktionen, Rot für Löschen, Grün für tatsächliche Bestätigung/Erfolg; keine beliebige Farbe je Funktion |
| Formulare | Beschriftung über dem Feld, Hilfe darunter, 44 px bedienbare Höhe, weißer Feldgrund, klarer Fokus; Checkboxen behalten ihre native Größe |
| Tabellen | Ruhiger Kopf, konsistente Zellenabstände, Bilder passend begrenzt, innerhalb ihres Bereichs horizontal scrollbar; mengenbezogene Zustandsfarben bleiben erhalten |
| Rückmeldungen | Text plus konsistente Zustandsfarbe; keine dunkle Schrift auf kräftigem blauen/grünen Kartenkopf; Lade-/Fehler-/Leerzustände gehören zum Arbeitsbereich |
| Mobil | Karten stapeln, Aktionsleisten umbrechen, keine horizontale Seitenausdehnung; breite Fachtabellen scrollen in einem beschrifteten Bereich |
| Tastatur | Sichtbarer Fokus, erreichbare Hauptbereiche und Dialoge, bestehende direkte Mengennavigation; reduzierte Bewegung respektieren |

## Technische Grenze

Jinja-Vererbung stellt Rahmen und Ressourcen bereit. `ui_macros.html` stellt
Seitenkopf und Leerzustand bereit; `design-system.css` definiert Tokens und
Komponenten. Seitenspezifisches CSS darf Fachansichten, Bilder und
Interaktionszustände ergänzen. Die vorhandenen Blueprints, Formularnamen,
Element-IDs, JSON-Verträge, Mengen-/Speicherlogik und Sicherheitsgrenzen bleiben
maßgeblich. Keine neue Frontend-Laufzeit, keine Datenmigration und kein Zugriff
auf echte Konten zum Prüfen der Oberfläche.

## Abnahme

Alle erreichbaren Seiten einschließlich Such-/Scanergebnis, Details,
Verwaltung, Fehlerseiten und sieben Lager-Arbeitsbereichen prüfen. Leere,
gefüllte und relevante Fehlerzustände müssen im selben System liegen.
`test_app_shell.py` prüft den Rahmen und eindeutige DOM-IDs für diese Wege.
Browsernachweise müssen Desktop und Mobil, reale Formulare, Tabellen,
Dialoge, Tastatur und Druckansicht umfassen. Vorhandene Mengen-/Label- und
Lagerprüfungen bleiben Bestandteil der Abnahme.

Der isolierte Browserlauf `tests/browser/app_shell_smoke.py` prüft 24 reale
Seitenwege und fünf synthetische gefüllte/Fehler-/Leeransichten jeweils mit
1440 und 390 Pixeln. Dazu kommen echte Suchformularübermittlungen, Sprunglink,
mobile Navigation, eindeutige DOM-IDs, sichtbare Hauptaktionen und Druckansicht.
Die Detail-/PDF-/Lager-Browserläufe sichern die bestehenden Arbeitsabläufe ab.
Diese Prüfungen ersetzen keine Nutzungsstudie und keinen physischen iPad-Test.

Nicht von Routen verwendete historische Vorlagen (`index.html`,
`index_backup.html`, `manual_entry_old.html`, `box_maintenance.html`,
`update_set.html`) sind keine aktiven Arbeitsseiten. Sie bleiben in diesem
Darstellungspaket unverändert; neue oder wieder aktivierte Seiten müssen den
gemeinsamen Rahmen verwenden. Eine vollständige Vereinheitlichung der bereits
gemischten deutschen/englischen Fachtexte ist eine gesonderte Sprachumstellung.

## Erweiterungsablauf

1. `base.html` erweitern, Seitentitel und vorhandene Sprache festlegen.
2. `page_header` mit Bereich, kurzer Aufgabe und passendem lokalem SVG verwenden.
3. Inhalte in gemeinsame Karten/Formulare/Tabellenregionen gliedern; fachliche
   IDs und Payloads beibehalten. Nebenaktionen erhalten neutrale Konturen.
4. Seitenspezifische Ressourcen über die beiden Ressourcenblöcke laden;
   keine zusätzliche Bootstrap-Datei und keine globalen Inline-Stile anlegen.
5. Route in Struktur- und Browserprüfung aufnehmen, gefüllte und leere Zustände
   mit isolierten Daten prüfen. Verträge in [Softwaredesign](software-design.md)
   und [Testanleitung](../guides/testing.md) beachten.
