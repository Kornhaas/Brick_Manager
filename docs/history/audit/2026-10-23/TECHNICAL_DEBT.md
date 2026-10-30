# Technische Schulden

| Priorität | Befund | Auswirkung | Sichere nächste Maßnahme |
|---|---|---|---|
| Hoch | `app.py` führt beim Import Initialisierung, `create_all`, Lookup-Laden und Scheduler-Setup aus. | Tests/CLI-Importe haben Seiteneffekte; wiederholtes Starten ist schwer prüfbar. | Zunächst Charakterisierungstests für Startpfad und Job-Registrierung; erst danach eine kompatible App-Factory-Entscheidung. |
| Hoch | Große Integrations- und Routenmodule bündeln viele Verantwortlichkeiten. | Fehleranalyse und gezieltes Testen sind aufwendig. | Kleine, reine Hilfsfunktionen extrahieren, jeweils mit Regressionstest; keine Routen- oder JSON-Verträge ändern. |
| Hoch | Gemessene Coverage liegt bei 63,58 % Lines und 51,18 % Branches. | Das 80-%-Qualitätsziel ist noch nicht nachgewiesen. | Kritische Fehler-/Grenzpfade vor allem in Missing Parts, Box Maintenance und Set Maintenance testen. |
| Mittel | `pytest.ini` verlangt 60 % Coverage, das Ziel liegt bei mindestens 80 %. | Regressionen in den verbleibenden ungetesteten Bereichen werden nicht vollständig verhindert. | Schwelle nach reproduzierbaren höheren Messungen stufenweise anheben. |
| Mittel | Konfiguration enthält Entwicklungs-Standardwerte für Secret und Rebrickable-Token. | Fehlkonfiguration einer öffentlichen Instanz wäre riskant. | Vor einer produktiv wirksamen Änderung Deployment-Kontext klären; Tests für sichere Konfigurationsvalidierung ergänzen. |
| Mittel | Dokumentation ist auf mehrere Root-Dateien verteilt. | Verhalten und Bedienung sind schwer zentral auffindbar. | Die unter `docs/` angelegten Referenzdokumente schrittweise mit verifiziertem Verhalten füllen. |

Keine dieser Maßnahmen ist in diesem Audit automatisch als Code-Refactoring
ausgeführt worden.
