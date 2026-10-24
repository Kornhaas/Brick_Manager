# Architekturentscheidungen

| Datum | Entscheidung | Begründung |
|---|---|---|
| 2026-10-23 | Bestehende Flask-Blueprint-/Service-/Model-Struktur beibehalten. | Sie passt zur Anwendung; ein vollständiger Architekturwechsel hätte hohe Kompatibilitäts- und Datenrisiken. |
| 2026-10-23 | Keine App-Factory-Migration ohne Charakterisierung und Freigabe. | `app.py` hat Importseiteneffekte; eine Änderung beeinflusst Start, CLI, Tests und Scheduler. |
| 2026-10-23 | Coverage wird als Messgröße, nicht als Selbstzweck behandelt. | Die aktuelle Messung von 63,58 % Lines und 51,18 % Branches zeigt substanzielle Lücken; neue Tests müssen Verhalten und Risiken absichern. |
