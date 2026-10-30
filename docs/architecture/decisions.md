# Architekturentscheidungen

Diese Entscheidungen gelten, bis sie durch einen neuen, datierten Eintrag ersetzt werden.

| Datum | Entscheidung | Begründung und Folgen |
| --- | --- | --- |
| 2026-10-30 | Flask-Blueprint-/Service-/Modellstruktur beibehalten. | Sie entspricht der vorhandenen Anwendung. Neue Funktionen folgen den bestehenden Grenzen statt eine parallele Schicht einzuführen. |
| 2026-10-30 | `app.py` ohne explizites Refactoring nicht zur App-Factory umbauen. | Der Import erzeugt Tabellen, lädt Lookups und startet den Scheduler. Eine Änderung beeinflusst Start, CLI und Tests und braucht Charakterisierungstests. |
| 2026-10-30 | Referenzdokumentation von historischen Berichten trennen. | Nur Dokumente außerhalb von `docs/history/` sind für neue Arbeit normativ; Historie bleibt nachvollziehbar erhalten. |
| 2026-10-30 | Ausführbarer Code, Migrationen und Tests stehen über Textdokumentation. | Dokumentation wird in jedem betroffenen Change angepasst und durch Repository-Tests gegen Schema-Drift geschützt. |
