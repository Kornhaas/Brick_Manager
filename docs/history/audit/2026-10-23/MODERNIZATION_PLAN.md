# Priorisierter Modernisierungsplan

## Abgeschlossen in diesem Arbeitspaket

1. Arbeitsbaum geprüft (keine vorbestehenden Änderungen).
2. Architektur, Risiken, technische Schulden und Messbasis dokumentiert.
3. Bestehende Teststruktur und Coverage-Konfiguration erfasst.

## Nächste risikoarme Arbeitspakete

1. **Testmessung stabilisieren:** Branch-Messung korrekt konfigurieren und die
   aktuelle Basis reproduzierbar dokumentieren. Erfolg: keine Änderung des
   Produktionscodes, nachvollziehbarer Line-/Branch-Bericht.
2. **Verhalten absichern:** Charakterisierungstests für Startpfad,
   Scheduler-Grenzen, Client-API-Fehlerantworten sowie Upload-/Dateigrenzen.
   Erfolg: beobachtetes Verhalten ist als Vertrag festgehalten.
3. **Kritische Lücken schließen:** Tests für nicht abgedeckte Fehler- und
   Randfälle der großen Sync- und Routenmodule, mit gemockten Integrationen.
   Erfolg: Coverage wächst durch fachliche Assertions, nicht durch triviale
   Ausführung.
4. **Kleine Refactorings:** Nur nach den zugehörigen Tests jeweils reine
   Parsing-/Formatierungshelfer oder wiederholte Fehlerbehandlung auslagern.
   Erfolg: öffentliche Routen, JSON-Felder, SQLite-Schema und Templates bleiben
   unverändert.

## Freigabepflichtig

Folgende Vorhaben werden nicht autonom ausgeführt: App-Factory-/Startup-Umbau,
Schema- oder Migrationsänderungen, API-Vertragsänderungen, Austausch zentraler
Abhängigkeiten, geänderte Nutzerabläufe und Live-Synchronisierung. Vor jedem
solchen Paket werden Nutzen, Kompatibilitätsfolgen und Rollback präsentiert.
