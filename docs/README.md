# Dokumentation

Dies ist der zentrale Dokumentationsindex für Brick Manager. Die Referenzdokumente beschreiben den überprüften aktuellen Code. Historische Berichte bleiben aus Nachvollziehbarkeitsgründen erhalten, sind aber keine Vorgabe für neue Änderungen.

## Zentrale Ablage und Pflege

`docs/` ist die zentrale Ablage für Projektwissen. Dokumentation wird mit jeder betroffenen Änderung gepflegt und gehört zur Fertigstellung. README und Agenten-/Skill-Dateien bleiben als Einstieg bzw. Werkzeugkonfiguration an ihren vorgesehenen Orten und verweisen hierher.

- [High-Level-Design](architecture/high-level-design.md): Systemkontext, Hauptabläufe und Qualitätsziele.
- [Softwaredesign](architecture/software-design.md): Implementierungsgrenzen, Verträge und Erweiterungspunkte.
- [Logbuch](logbook.md): datierte Ergebnisse, Gründe, ausgeführte Prüfungen und offene Grenzen.

Ist-Verhalten und Vorschläge klar kennzeichnen. Inhalte an genau einer fachlich passenden Stelle pflegen und andernorts verlinken. Nachweise aus Code und Tests haben Vorrang. Alte Messwerte werden nur mit ihrem damaligen Datum zitiert.

## Referenz

- [Referenzarchitektur](architecture/reference-architecture.md): Komponenten, Verantwortlichkeiten, Daten- und Kontrollflüsse sowie Erweiterungsregeln.
- [Architekturentscheidungen](architecture/decisions.md): dauerhaft geltende technische Entscheidungen und ihr Kontext.
- [Einheitliches UI-Konzept](architecture/ui-design-system.md): gemeinsamer Seitenrahmen, Komponenten, Farben, mobile Ansichten und Erweiterungsregeln.
- [Datenbankschema](reference/database-schema.md): Modelle, Tabellen, Ownership und Regeln für Änderungen an persistierten Daten.
- [Modell-Kurzreferenz](reference/model-reference.md): Einstieg in die SQLAlchemy-Modelle ohne ein zweites Feldinventar zu pflegen.
- [Konfiguration](reference/configuration.md): Umgebungsvariablen, Pfade und Sicherheitsvorgaben.
- [Projektsprache](reference/terminology.md): Bricks als allgemeiner Produktbegriff und Umgang mit technischen Bezeichnungen.
- [Qualitätswerkzeuge](reference/quality-tooling.md): Hooks und lokale Checks.

## Anleitungen

- [Entwicklung](guides/development.md)
- [KI-Zusammenarbeit und Agenten](guides/ai-collaboration.md)
- [Tests](guides/testing.md)
- [Lagerverwaltung](guides/warehouse.md): Erfassung, Umlagerung, Archivprüfung und Teileaufnahme.
- [Docker-Betrieb](guides/docker.md)
- [Anwendungsfunktionen](guides/user-guide.md)

## Planungsvorschläge

- [GitHub-Qualität und visueller Auftritt](plans/github-quality-and-identity.md): überprüfte Einstellungen, priorisierte Schutzmaßnahmen, Browserprüfungen und Projektgestaltung; Empfehlungen klar vom umgesetzten Stand getrennt.

- [Architektur- und Usability-Verbesserungen](plans/architecture-usability-improvements.md): projektweiter Review, testgetriebene erste Welle, priorisiertes Altlasten-Backlog und [Analyse mit Umsetzung der Setpflege](plans/architecture-usability-improvements.md#vorschlag-setpflege-als-eigener-arbeitsbereich-22-november-2026).

- [Lageransicht, Archivierung und Einlagerung](plans/storage-archive-intake.md): Ist-Analyse, Zielmodell, Migration, UI-Abläufe, frei wählbares Pilotfach und Akzeptanztests. Umsetzung einschließlich V1-Archivprüfung vorhanden; [Abnahme und Nachweise](plans/storage-acceptance.md). Regal 1/Fach 5 ist nur ein Dummy-Beispiel.

Die verlinkten Pläne unterscheiden Vorschläge, laufende Pakete und bereits abgenommene Umsetzung. Maßgeblich sind die jeweils dokumentierten Nachweise.

## Historie

`history/` enthält zeitgebundene Feature-, Audit- und Modernisierungsberichte. Diese Dokumente können überholte Endpunkte, Messwerte oder Pläne enthalten und dürfen nicht als Architekturvertrag zitiert werden.

## Pflegevertrag

| Änderung | Gleichzeitig aktualisieren |
| --- | --- |
| Systemkontext oder Hauptablauf | High-Level-Design und betroffene Architektur-/Designabschnitte |
| Komponentenverantwortung oder Laufzeitverhalten | Referenzarchitektur und Softwaredesign |
| UI-Ablauf oder Bedienung | Softwaredesign und Benutzeranleitung |
| Datenmodell, Migration oder Import | `reference/database-schema.md` und passende Tests |
| Öffentliche `/api/v1`-Schnittstelle | Referenzarchitektur, Konfiguration und Vertragstests |
| Konfiguration, Pfade oder Zugangsdaten | `reference/configuration.md` |
| Lokaler Ablauf, Tools oder Tests | passende Anleitung bzw. Qualitätsreferenz |
| Architekturentscheidung | `architecture/decisions.md` |

Die verbindliche Reihenfolge bei Widersprüchen ist: ausführbarer Code und Tests, versionierte Migrationen, Referenzdokumentation, historische Berichte.

Jeder abgeschlossene Arbeitsauftrag erhält zusätzlich einen Eintrag im [Logbuch](logbook.md). Wenn keine weitere Dokumentation betroffen ist, wird dies dort kurz begründet. Ein Eintrag enthält Datum, Ergebnis, Grund, Links auf betroffene Artefakte, tatsächlich ausgeführte Prüfungen und offene Punkte. Der koordinierende Agent führt Teilergebnisse zusammen; reine Zwischenstände werden nicht als abgeschlossene Ergebnisse eingetragen.

Vor Übergabe betroffene Aussagen mit Code und Tests abgleichen und lokale Links in geänderten Markdown-Dateien prüfen. Historische Berichte werden durch neue Arbeit nicht nachträglich zu aktuellen Referenzen umgeschrieben.
