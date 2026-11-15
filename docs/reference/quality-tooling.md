# Qualitätswerkzeuge

Die Befehle werden im Repository-Root mit Poetry ausgeführt.

| Zweck | Befehl |
| --- | --- |
| Git-Hooks installieren | `make hooks` |
| Ruff linten und Formatierung prüfen | `make ruff` |
| Typen prüfen | `make typecheck` |
| Abhängigkeiten prüfen | `make audit` |
| Kandidaten für ungenutzten Code melden | `make dead-code` |
| umfassende Prüfung ohne Änderungen | `poetry run python scripts/pre_commit_analysis.py --no-fix` |

`scripts/pre_commit_analysis.py` kann ohne `--no-fix` Dateien formatieren bzw. reparieren. Änderungen vor dem Commit prüfen und stagen. Vulture-Ausgaben sind Kandidaten, keine Löschfreigabe.

Der Commit-Message-Hook verlangt Conventional Commits im Format `<type>[scope]: <beschreibung>`, zum Beispiel `fix(api): validate storage payload`.

## Unveränderliche Migrationen

Bereits angewendete Dateien unter `brick_manager/migrations/` bleiben bytegenau
unverändert. Auch eine reine Umformatierung verändert ihre SHA-256-Prüfsumme.
Die mutierenden Pre-commit-Hooks schließen dieses Verzeichnis ausdrücklich aus;
Ruffs `force-exclude = true` erhält den Ausschluss auch bei explizit übergebenen
Dateinamen und automatischer Formatierung. Normale Anwendungsdateien bleiben
weiterhin in den Prüfungen. Read-only-Hooks wie die Konfliktprüfung bleiben aktiv.

Bei `Applied migration changed` die Originalfassung aus einem nachweislich
passenden Commit oder Build wiederherstellen und ihre Prüfsumme mit dem Journal
abgleichen. Die Datei muss auch im Git-Index unverändert sein. Gespeicherte
Prüfsummen nicht einfach ersetzen und keine bereits angewendete Migration
nochmals ausführen. Fachliche Änderungen benötigen eine neue Migration.

Die Regression `test_migration_formatter_contract.py` wendet eine Migration an,
führt die echten Ruff-Kommandos mit explizitem Dateinamen aus und prüft danach
Byteidentität, erneuten sicheren Runner-Aufruf und unveränderten Inhalt. Weitere
Fälle prüfen die tatsächliche Dateiauswahl aller vier mutierenden Hooks.
