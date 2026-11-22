# Referenzarchitektur

## Zweck und Leitprinzipien

Brick Manager ist ein einzelner Flask-Prozess mit servergerendertem Web-UI, einer kleinen JSON-API für vertrauenswürdige Desktop-Clients und einer lokalen SQLite-Datenbank. Die Architektur bewahrt die Grenzen des gewachsenen Systems, statt eine zusätzliche abstrakte Schicht einzuführen.

1. Routen sind die HTTP-Grenze; sie validieren Eingaben, bestimmen Statuscodes und rendern HTML oder JSON.
2. Services kapseln wiederverwendbare Fach-, Integrations-, Datei-, Cache- und Renderinglogik.
3. Modelle definieren Persistenz, Beziehungen und einfache Serialisierung.
4. `app.py` ist der derzeitige Kompositionspunkt und hat bewusst dokumentierte Startseiteneffekte.
5. Rebrickable-Katalogdaten und sammlungseigene Daten bleiben getrennt.

## Systemübersicht

```mermaid
flowchart LR
  Browser[Browser: Jinja + JavaScript] --> Routes[Flask Blueprints]
  Desktop[Desktop-Client] --> Api[Authentifiziertes /api/v1]
  Api --> Routes
  Routes --> Services[Services]
  Routes --> Models[SQLAlchemy-Modelle]
  Services --> Models
  Models --> Sqlite[(SQLite)]
  Services --> Files[Dateien: Uploads, Labels, Cache]
  Services --> Remote[Rebrickable / Brickognize]
  App[app.py] --> Routes
  App --> Scheduler[APScheduler]
  Scheduler --> Services
```

## Komponenten und Verantwortlichkeiten

| Bereich | Ort | Verantwortung |
| --- | --- | --- |
| App-Komposition | `brick_manager/app.py` | Flask-Erweiterungen, Logging, Blueprints, Startlogik und Scheduler |
| Konfiguration | `brick_manager/config.py` | Pfade, Umgebungsvariablen und Größenlimits |
| HTTP/UI | `brick_manager/routes/` | Blueprints, Eingabegrenzen, HTTP/JSON/Template-Verträge |
| Domäne/Integration | `brick_manager/services/` | Rebrickable, Brickognize, Labels, Caches, Imports und Backups |
| Persistenz | `brick_manager/models.py` | Tabellen, Beziehungen, Constraints und Serialisierung |
| Präsentation | `brick_manager/templates/`, `brick_manager/static/` | Jinja-Templates, CSS und Vanilla JavaScript |
| Tests | `brick_manager/tests/`, `tests/js/` | Flask-/SQLite-Verträge und isolierte JavaScript-Checks |

`app.py` registriert 18 Blueprints. Der Desktop-Client ist auf `/api/v1` beschränkt und verlangt einen Bearer-Key. Die UI-Routen sind nicht automatisch durch diesen Key geschützt; ein öffentliches Deployment braucht eine passende Netzwerk- und Zugriffsabsicherung.

## Persistenz und Ownership

Die vollständige Tabellenreferenz steht in [Datenbankschema](../reference/database-schema.md).

- Rebrickable-Tabellen sind ersetzbare Referenzkataloge.
- `user_sets`, `user_parts`, `user_minifigures`, `user_minifigure_parts`, `part_storage`, `collection_snapshots` und `config_settings` sind sammlungseigener Zustand.
- Ein Katalogimport darf Status, Mengen, Notizen, Lagerorte und Label-Status der Sammlung nicht löschen oder überschreiben.
- Schemaänderungen an bestehenden Datenbanken benötigen eine vorwärtsgerichtete und wiederholbar sichere Migration; `db.create_all()` genügt dafür nicht.

## Start- und Hintergrundverhalten

Beim Import von `app.py` werden vor ORM-Zugriffen die versionierten Migrationen der ausgewählten SQLite-Datenbank ausgeführt und Tabellen für neue Installationen angelegt, Lookup-Daten geladen, Blueprints registriert und ein Scheduler gestartet. Der Scheduler legt einen Backup-Job im Sechs-Stunden-Intervall sowie Jobs für fehlende Teile und Benutzer-Sets in Intervallen von sechs Stunden und 30 beziehungsweise 35 Minuten an. Deshalb importieren Routen- und Modelltests nicht die Produktiv-App, sondern verwenden `brick_manager/tests/conftest.py`.

Das ist Ist-Verhalten, keine Empfehlung für einen ungetesteten App-Factory-Umbau. Eine Änderung daran benötigt Charakterisierungstests und eine explizite Architekturentscheidung.

## Erweiterungsregeln

| Änderung | Platzierung und Nachweis |
| --- | --- |
| Neue HTML- oder JSON-Funktion | passender Blueprint; Erfolg, Eingabefehler und fehlende Ressource testen |
| Wiederverwendbare Fachlogik | Service; externe Aufrufe am `requests`-Rand mocken |
| Neues Persistenzfeld | Modell, vorwärtsgerichtete Migration, Schema-Referenz und Migrationstest |
| Externer Vertrag | Service plus Kontrakt- und Fehlerpfadtests; keine Live-Aufrufe im Test |
| Neue Konfiguration | `Config`, `.env.example` und Konfigurationsreferenz |

Öffentliche Routen, JSON-Felder, Statuscodes, Tabellen und Persistenzformate sind Verträge. Sie werden nur mit Kompatibilitätsanalyse, Tests und aktualisierter Dokumentation geändert.

## Lagerverwaltung und Kompatibilität

Der Warehouse-Blueprint besitzt aufgabenbezogene HTML-Einstiege für Übersicht,
Einlagern, Umräumen, Boxgrößen, Fächer, Bestandserfassung und Regeln. Gemeinsame
Navigation und aufgeteilte Jinja-Inhalte bilden die Präsentationsgrenze;
der Browsercontroller initialisiert nur die auf der jeweiligen Seite vorhandenen
Formulare. Die fachlichen JSON-Endpunkte und Services bleiben gemeinsam.
Seitenwechsel übertragen Kontext über IDs statt über duplizierte Fachlogik.

Der Warehouse-Blueprint stellt physische Lagerstruktur, gezählte Inhalte und
explizit bestätigte Bewegungen bereit. Storage-, Move-, History- und
Suggestion-Services trennen physische Änderungen von historischen Empfehlungen
und setbezogenem Besitz. Details stehen im [Softwaredesign](software-design.md).

Die Browser-Schreiboperationen erfordern ein Sitzungstoken. Der dedizierte
Desktop-Bearer-Key schützt weiterhin `/api/v1`; die Authentifizierung wird vor
der Prüfung einer mehrdeutigen Lageränderung ausgeführt. Bestehende eindeutige
unstrukturierte Legacy-Zuordnungen bleiben nutzbar; strukturierte oder mehrdeutige
Schreib-/Löschversuche werden mit 409 abgefangen. Das gilt auch bei deaktivierter
neuer Oberfläche, damit keine unsichere Schreibalternative entsteht.

Die [Lagerabnahme](../plans/storage-acceptance.md) dokumentiert automatisierte
Nachweise und die getrennten offenen Vor-Ort-Messungen.

## Schrittweise Altlastenbereinigung

Die Setpflege trennt Sammlungsliste und den eigenen Arbeitsbereich jeder
physischen Kopie. Der Set-Maintain-Blueprint stellt HTML-Navigation und
Transaktionsgrenzen bereit; `set_maintenance_service.py` kapselt das gemeinsame
Inventarlesemodell sowie die vollständige Validierung vor Mengenänderungen.
`set_navigation_service.py` begrenzt Herkunftsparameter und serverseitige
Sortierung. `set_label_service.py` kapselt native PDF-Layouts, begrenzte und
geprüfte Katalogbildabrufe mit Cache sowie atomare Dateiausgabe; HTTP und Druckstatus bleiben im
Blueprint. Die bisherigen JSON-/Einzelmengenverträge bleiben erhalten; die
neue Detailseite bestätigt Mengen und Status bewusst in einer Transaktion.
Rückkehrkontext und Client-Speicherzustände stehen im
[Softwaredesign](software-design.md#setliste-und-eigener-arbeitsbereich).

Die erste Architektur-/Usability-Welle ergänzt spezialisierte Services für
Sammlungsmengenidentität, seitenspezifische Mengenübersichten und konsistente
SQLite-Sicherungen. Routen bleiben HTTP-/Transaktionsgrenze; vorhandene
Blueprints und externe API-Verträge bleiben erhalten. Browseränderungen nutzen
weiter Vanilla JavaScript und gekapselte Speicherwarteschlangen. Details und
Grenzen stehen im [Softwaredesign](software-design.md#sammlungsstabilität-und-skalare-übersichten),
weitere priorisierte Schritte im [Verbesserungsplan](../plans/architecture-usability-improvements.md).
