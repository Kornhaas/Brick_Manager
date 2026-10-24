# Modernisierungszusammenfassung

Stand: 23. Oktober 2026

Die testgetriebene Modernisierung hat nun auch Produktionscode erreicht. Neue
Vertrags-, System- und UI-Tests sichern Mengenänderungen, Lagerorte, Uploads,
Bauanleitungen, Dashboard-Kennzahlen, Detailansichten, Health-/Cache-Routen und
die Desktop-API. Die getesteten Endpunkte validieren JSON-Typen strenger,
rollen fehlgeschlagene Transaktionen zurück und geben keine internen
Datenbankfehler mehr an Clients weiter.

Der vollständige Lauf umfasst 361 bestandene Tests ohne Fehler oder Skips. Die
Messung beträgt 63,58 % Line Coverage, 51,18 % Branch Coverage und 60,86 %
kombinierte pytest-cov Coverage. Das geforderte Mindestziel von 80 % ist damit
noch nicht erreicht und wird nicht als abgeschlossen dargestellt.

Die größten Risiken betreffen Startseiteneffekte, persistente SQLite-Daten,
externe Synchronisierungen und den `/api/v1`-Vertrag. Die empfohlenen nächsten
Schritte sind Charakterisierungstests und eine reproduzierbare Branch-Messung.
App-Startup-Umbau, Migrationen, API- und Nutzerablaufänderungen bleiben nur
dann erforderlich, wenn die zugehörigen Charakterisierungstests ein konkretes
Problem zeigen. Diese Modernisierung hat keine solchen Änderungen eingeführt.

Weitere kleine Modernisierungen verhindern Dateinamenskollisionen bei Uploads,
zeigen Lagerorte in der Detailansicht und fehlende Ersatzteile im Dashboard,
blenden Debug-Endpunkte außerhalb von Test/Debug aus und respektieren einen
konfigurierten Bauanleitungsordner. Datenbankschema, Migrationen und bestehende
Sammlungsdaten wurden nicht verändert.

Die zweite TDD-Runde sichert zusätzlich Token-Verschlüsselung, authentifizierte
Rebrickable-Aufrufe, Rate-Limits, Pagination, Setlisten-Abgleich sowie atomare
Katalogimporte ab. Fehlgeschlagene Imports bewahren die vorherigen Katalogdaten
und temporäre Downloads werden bei Fehlern bereinigt.

Die Logging-Konfiguration bindet keinen importzeitlichen Root-Stream mehr.
Flasks dynamischer CLI-/WSGI-Handler bleibt erhalten, die Konfiguration ist
idempotent und der lokale Flask-Start wurde ohne Logging-Ausnahme verifiziert.

Der Katalogimport läuft für die Weboberfläche nun als einzelner Hintergrundjob.
Eine per Polling aktualisierte Checkliste zeigt Download, Import, Datensatzanzahl,
Gesamtfortschritt und Fehlerzustand je Archiv. Ein zweiter Start verbindet sich
mit dem laufenden Job; ein Neuladen der Seite setzt die Beobachtung über die
lokal gespeicherte Job-ID fort.
