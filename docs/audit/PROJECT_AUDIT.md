# Projekt-Audit: Brick Manager

Stand: 23. Oktober 2026 (Messung im lokalen Arbeitsbaum)

## Umfang und Methode

Dieses Audit bewertet den eingecheckten Python-/Flask-Code, die bestehende
Testsuite, Konfiguration und Projekt-Dokumentation. Es nimmt keine produktive
Datenbank, keine Rebrickable-Verbindung und keinen Deployment-Endpunkt in
Anspruch. Aussagen zu Laufzeitdaten, realen Zugangsdaten, Datenvolumen und
externer API-Verfügbarkeit sind daher bewusst als unbekannt behandelt.

## Befund

Brick Manager ist eine Flask-Anwendung zur Verwaltung einer LEGO-Sammlung. Die
fachlichen Kerndaten liegen in SQLite und werden über SQLAlchemy-Modelle
verwaltet. Jinja-Templates und Vanilla-JavaScript bilden die Oberfläche;
Blue­prints organisieren die HTTP-Routen. Rebrickable und Brickognize sind
optionale externe Integrationen. ReportLab/Pillow erzeugen Labels und Bilder.

Die Anwendung besitzt 17 registrierte Blueprints. Die größten fachlichen
Komponenten sind `services/rebrickable_sync_service.py` (1.894 Zeilen),
`routes/missing_parts.py` (1.015), `services/rebrickable_sets_sync_service.py`
(688), `routes/set_maintain.py` (623) und `routes/box_maintenance.py` (600).
Sie sind die wichtigsten Kandidaten für behutsame, testgestützte Entkopplung.

## Verifizierte Testbasis

Der vollständige konfigurierte Lauf sammelte 355 Tests; alle bestanden ohne
Skips. Die erzeugte Cobertura-Datei enthält 2.781 abgedeckte von 4.419
ausführbaren Produktivzeilen: **62,93 % Line Coverage**. Zusätzlich sind 631
von 1.248 Branches abgedeckt (**50,56 %**); pytest-cov weist kombiniert
**60,21 %** aus. Das Repository erzwingt nun 60 % Coverage (`pytest.ini`).

## Stärken

- Poetry, pytest, pytest-cov, Ruff, BasedPyright und Sicherheitswerkzeuge sind
  als Abhängigkeiten bzw. Make-Ziele vorhanden.
- Die Testsuite deckt Modelle, Routen, Services, API-Verträge und mehrere
  Regressionen ab.
- Persistente Modelle verwenden Beziehungen und Löschkaskaden explizit.
- Konfiguration erlaubt lokale Entwicklung und Docker-Datenvolumes.

## Grenzen und unbekannte Aspekte

- Ein Import von `app.py` erstellt Tabellen, lädt Lookup-Daten und startet
  Scheduler-Jobs; die Testisolierung muss deshalb weiterhin `tests/conftest.py`
  bevorzugen.
- Das Audit hat keine Live-Synchronisierung, Token- oder Backup-Wiederherstellung
  durchgeführt. Deren operatives Verhalten bleibt unbestätigt.
- Migrationshistorie und reale Bestandsdaten wurden nicht verändert oder geprüft.

Weiterführende Befunde: [Architektur](ARCHITECTURE_AS_IS.md),
[Schulden](TECHNICAL_DEBT.md), [Risiken](RISK_ASSESSMENT.md) und
[Plan](MODERNIZATION_PLAN.md).
