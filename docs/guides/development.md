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
