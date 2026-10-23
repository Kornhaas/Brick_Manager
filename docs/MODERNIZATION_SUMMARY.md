# Modernisierungszusammenfassung

Stand: 23. Oktober 2026

Die testgetriebene Modernisierung hat nun auch Produktionscode erreicht. Neue
Vertrags-, System- und UI-Tests sichern Mengenänderungen, Lagerorte, Uploads,
Bauanleitungen, Dashboard-Kennzahlen, Detailansichten, Health-/Cache-Routen und
die Desktop-API. Die getesteten Endpunkte validieren JSON-Typen strenger,
rollen fehlgeschlagene Transaktionen zurück und geben keine internen
Datenbankfehler mehr an Clients weiter.

Der vollständige Lauf umfasst 355 bestandene Tests ohne Fehler oder Skips. Die
Messung beträgt 62,93 % Line Coverage, 50,56 % Branch Coverage und 60,21 %
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
