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
