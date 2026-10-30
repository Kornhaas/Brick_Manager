# Brick Manager

Brick Manager ist eine Flask-Anwendung zur Verwaltung einer Klemmbaustein-Sammlung: Sets, Teile, Minifiguren, Fehlteile, Lagerorte und Etiketten werden lokal in SQLite verwaltet. Rebrickable und Brickognize sind optionale externe Integrationen.

Die vollständige, gepflegte Dokumentation beginnt unter [docs/README.md](docs/README.md). Diese Datei bleibt bewusst im Repository-Root, weil Poetry sie als Paketbeschreibung verwendet.

## Schnellstart

Voraussetzungen: Python 3.12, Poetry und SQLite.

```powershell
poetry install
Copy-Item .env.example .env
poetry run flask --app brick_manager/app.py run
```

Die Anwendung ist danach unter `http://127.0.0.1:5000` erreichbar. Vor einem echten Rebrickable-Abgleich und vor dem Einsatz der Desktop-API müssen die Zugangsdaten in `.env` gesetzt werden.

## Einstiegspunkte

- [Referenzarchitektur](docs/architecture/reference-architecture.md)
- [Konfiguration und Sicherheit](docs/reference/configuration.md)
- [Entwicklung](docs/guides/development.md)
- [Tests](docs/guides/testing.md)
- [Docker-Betrieb](docs/guides/docker.md)
- [Datenmodell und Migrationen](docs/reference/database-schema.md)

## Dokumentationsregeln

`brick_manager/models.py`, versionierte Migrationen und ausführbare Tests sind die maßgeblichen Quellen für Persistenz und Verhalten. Änderungen an Routen, externen Verträgen, Konfiguration oder Datenmodell müssen die jeweils verlinkte Referenzdokumentation im selben Change aktualisieren.
