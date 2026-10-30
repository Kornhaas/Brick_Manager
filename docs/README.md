# Dokumentation

Dies ist der zentrale Dokumentationsindex für Brick Manager. Die Referenzdokumente beschreiben den überprüften aktuellen Code. Historische Berichte bleiben aus Nachvollziehbarkeitsgründen erhalten, sind aber keine Vorgabe für neue Änderungen.

## Referenz

- [Referenzarchitektur](architecture/reference-architecture.md): Komponenten, Verantwortlichkeiten, Daten- und Kontrollflüsse sowie Erweiterungsregeln.
- [Architekturentscheidungen](architecture/decisions.md): dauerhaft geltende technische Entscheidungen und ihr Kontext.
- [Datenbankschema](reference/database-schema.md): Modelle, Tabellen, Ownership und Regeln für Änderungen an persistierten Daten.
- [Modell-Kurzreferenz](reference/model-reference.md): Einstieg in die SQLAlchemy-Modelle ohne ein zweites Feldinventar zu pflegen.
- [Konfiguration](reference/configuration.md): Umgebungsvariablen, Pfade und Sicherheitsvorgaben.
- [Qualitätswerkzeuge](reference/quality-tooling.md): Hooks und lokale Checks.

## Anleitungen

- [Entwicklung](guides/development.md)
- [Tests](guides/testing.md)
- [Docker-Betrieb](guides/docker.md)
- [Anwendungsfunktionen](guides/user-guide.md)

## Historie

`history/` enthält zeitgebundene Feature-, Audit- und Modernisierungsberichte. Diese Dokumente können überholte Endpunkte, Messwerte oder Pläne enthalten und dürfen nicht als Architekturvertrag zitiert werden.

## Pflegevertrag

| Änderung | Gleichzeitig aktualisieren |
| --- | --- |
| Datenmodell, Migration oder Import | `reference/database-schema.md` und passende Tests |
| Öffentliche `/api/v1`-Schnittstelle | Referenzarchitektur, Konfiguration und Vertragstests |
| Konfiguration, Pfade oder Zugangsdaten | `reference/configuration.md` |
| Lokaler Ablauf, Tools oder Tests | passende Anleitung bzw. Qualitätsreferenz |
| Architekturentscheidung | `architecture/decisions.md` |

Die verbindliche Reihenfolge bei Widersprüchen ist: ausführbarer Code und Tests, versionierte Migrationen, Referenzdokumentation, historische Berichte.
