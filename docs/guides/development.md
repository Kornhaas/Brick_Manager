# Entwicklung

## Einrichten und Starten

```powershell
poetry install
Copy-Item .env.example .env
poetry run flask --app brick_manager/app.py run
```

Alle Poetry-Befehle werden im Repository-Root ausgeführt. Für gewöhnliche Route-, Service- und UI-Arbeit wird die bestehende Blueprint-/Service-/Modellgrenze beibehalten.

## Arbeitsablauf

1. Betroffene Route, Service, Modell, Template/JavaScript und Tests zuerst lesen.
2. Eingaben an der HTTP-Grenze validieren; wiederverwendbare Logik in Services halten.
3. Verhalten mit fokussierten Tests absichern und relevante Referenzdokumentation im selben Change aktualisieren.
4. Zuerst gezielte, danach breitere Qualitätschecks ausführen.

`app.py` hat Startseiteneffekte. Route- und Modelltests verwenden deshalb die Test-App aus `brick_manager/tests/conftest.py`, nicht einen erneuten Import der Produktiv-App.

## Qualitätschecks

```powershell
poetry run pytest -q brick_manager/tests/test_client_api.py
poetry run pytest -q
make ruff
make typecheck
make audit
poetry run python scripts/pre_commit_analysis.py --no-fix
```

`make hooks` installiert die Git-Hooks. Commit-Nachrichten folgen Conventional Commits, etwa `docs: reorganize reference documentation`.

## Grenzen

Keine produktive Synchronisierung, Token-Erzeugung, Datenbank-Reset, Wiederherstellung oder Deployment als Teil des normalen Entwicklungsablaufs ausführen. Änderungen an Persistenz, `/api/v1` oder externen Diensten brauchen zusätzlich eine Kompatibilitäts- und Datenfolgenprüfung.

## Lagerdatenbank migrieren

Die Lagerverwaltung verwendet versionierte SQLite-SQL-/Python-Migrationen mit
Prüfsummenjournal. Vor Änderungen an echten Entwicklungsbeständen eine konsistente
Sicherung anlegen und zunächst eine Kopie migrieren. Die folgenden Pfade sind
Beispiele für ausdrücklich ausgewählte Entwicklungsdateien, keine Produktivpfade:

```bash
PYTHONPATH=brick_manager poetry run python -m services.migration_service /tmp/brick-dev.db --inspect
PYTHONPATH=brick_manager poetry run python -m services.migration_service /tmp/brick-dev.db --backup /tmp/brick-dev-before-storage.db
PYTHONPATH=brick_manager poetry run python -m services.migration_service /tmp/brick-dev-copy.db brick_manager/migrations
```

`--inspect` öffnet nur eine vorhandene Datenbank im Read-only-Modus. Eine Sicherung
überschreibt keine bestehende Datei. Upgrade und Journal sind je Artefakt atomar;
Wiederholung verifiziert die unveränderte Prüfsumme. Angewendete Dateien nicht
nachträglich ändern, sondern eine weitere Migration hinzufügen. Docker und lokaler
App-Start verwenden denselben Runner vor ORM-Lesezugriffen. Nicht unterstützte
Datenbanken erhalten keine SQLite-Migration. Ein altes Programm darf nach neuen
Lagerbuchungen nicht schreibend auf die erweiterte Datenbank zurückgesetzt werden.
Eine Wiederherstellung bleibt ein eigener Auftrag mit anschließendem physischem
Abgleich.

### SQLite-Pfade beim lokalen Start

Relative SQLite-Adressen wie `sqlite:///data/instance/brick_manager.db` werden
von Flask-SQLAlchemy unter dem Flask-Instance-Verzeichnis aufgelöst. Dieses
Verzeichnis ist nicht automatisch identisch mit `Config.INSTANCE_FOLDER`. Der
Migrationsrunner verwendet den vom Engine-URL gelieferten Dateipfad und legt
fehlende Elternverzeichnisse vor dem Öffnen an. Er wechselt bei einem Fehler
nicht auf eine andere Datenbank und verändert keine vorhandenen Zählwerte.

Flask lädt beim CLI-Start die `.env` auch dann, wenn zuvor eine gleichnamige
Shell-Variable mit `env -u` entfernt wurde. Einen Datenbank-Override deshalb
bewusst in `.env` korrigieren oder einen gewünschten absoluten SQLite-Pfad
explizit in der Umgebung setzen. `FLASK_SKIP_DOTENV=1` überspringt die gesamte
`.env`, einschließlich anderer dort gespeicherter Einstellungen.
