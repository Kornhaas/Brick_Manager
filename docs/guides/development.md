# Entwicklung

## Voraussetzungen

Python 3.12 oder neuer, Poetry und SQLite werden benötigt. Abhängigkeiten aus
dem Repository-Root installieren:

```bash
poetry install
```

Die Anwendung lokal starten:

```bash
poetry run flask --app brick_manager/app.py run
```

## Tests und Qualität

```bash
poetry run pytest -q
poetry run pytest -q brick_manager/tests/test_client_api.py
make ruff
make typecheck
make audit
```

Tests verwenden die gemeinsame Flask-Testanwendung aus
`brick_manager/tests/conftest.py` und eine In-Memory-SQLite-Datenbank. Externe
HTTP-Aufrufe müssen gemockt werden. Eine Änderung an Route, Template oder
JSON-Nutzlast benötigt Tests für Erfolg, ungültige Eingaben und fehlende Daten.

## Arbeitsregeln

- Poetry-Befehle aus dem Repository-Root ausführen.
- Keine reale Synchronisierung, Token-Erzeugung, Datenbank-Reset, Restore oder
  Deployment im Testworkflow ausführen.
- Datenmodelländerungen brauchen eine vorwärtsgerichtete, wiederholbar sichere
  Migration sowie Datenintegritätstests.
- Öffentliche `/api/v1`-Felder, Statuscodes und Authentifizierungsverhalten als
  Vertrag behandeln.

Das Importieren von `app.py` startet gegenwärtig Initialisierung und Scheduler.
Für Routen- und Modelltests deshalb die Fixtures statt eines erneuten
Produktivimports verwenden.
