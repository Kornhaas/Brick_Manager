# Teststrategie

## Ziel und Ebenen

- **Unit-Tests:** Modelle, reine Service- und Formatierungslogik mit isolierter
  Datenbank bzw. Mocks.
- **Route-/Vertragstests:** Erfolg, ungültige Eingaben, fehlende Datensätze und
  JSON-/Formularverträge pro betroffenem Blueprint.
- **Integrationsgrenzen:** SQLite, Dateisystem und externe Clients nur über
  temporäre Verzeichnisse, Testdatenbank und Mocks/Fakes.
- **Regressionen:** Jeder behobene Fehler erhält eine aussagekräftige Assertion
  auf das Nutzer- oder API-Verhalten.

## Mess- und Qualitätsregeln

Tests werden mit Poetry vom Repository-Root ausgeführt:

```bash
poetry run pytest -q
poetry run pytest -q brick_manager/tests/test_client_api.py
make ruff
make typecheck
```

Die Coverage-Schwelle wird erst angehoben, wenn sie zuverlässig erreicht wird.
Die Messung erfasst Line- und Branch-Coverage; die Zahlen werden ausschließlich
aus einem frischen vollständigen Lauf übernommen.
Für das langfristige Ziel von mindestens 90 % Line Coverage und sinnvoller
Branch Coverage werden zuerst die hochriskanten, bisher ungetesteten Pfade
priorisiert. Excludes müssen fachlich begründet werden; Tests dürfen keine
Implementierungsdetails ohne beobachtbares Verhalten prüfen.
