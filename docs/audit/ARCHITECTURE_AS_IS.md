# Architektur: Ist-Zustand

## Komponenten

```mermaid
flowchart LR
  Browser --> Routes[Flask Blueprints / routes]
  Desktop[Desktop Client] --> API[/api/v1 client_api]
  Routes --> Services
  Routes --> Models[SQLAlchemy-Modelle]
  Services --> Models
  Models --> SQLite[(SQLite)]
  Services --> Rebrickable[Rebrickable]
  Services --> Brickognize[Brickognize]
  Routes --> Templates[Jinja / JavaScript / CSS]
  App[app.py] --> Routes
  App --> Scheduler[APScheduler]
  Scheduler --> Services
```

`brick_manager/app.py` ist der Kompositionspunkt: Es lädt `Config`, initialisiert
Flask-SQLAlchemy und Flask-Migrate, richtet Logging ein, registriert alle
Blueprints und legt Scheduler-Jobs für Backup und Synchronisierung an.

`models.py` definiert die Sammlung (`User_Set`, Teile, Minifiguren und
Lagerorte), Rebrickable-Stammdaten und Einstellungen. Der HTTP-Layer liegt in
`routes/`; wiederverwendbare fachliche und Integrationslogik liegt überwiegend
in `services/`. Templates und statische Assets bleiben serverseitig mit den
jeweiligen Routen gekoppelt.

## Daten- und Kontrollfluss

1. HTTP- oder Desktop-API-Anfragen treffen einen Blueprint.
2. Routen lesen/validieren Eingaben, nutzen Modelle oder Services und rendern
   HTML bzw. geben JSON zurück.
3. Services greifen bei Bedarf auf SQLite, Dateien, PDF-/Bildausgabe oder
   externe APIs zu.
4. Wiederkehrende Jobs rufen dieselben Synchronisierungs- bzw. Backup-Pfade auf.

## Architekturgrenzen

Die Einteilung in Routen, Services, Modelle und Templates ist sinnvoll und
soll beibehalten werden. Sie ist jedoch nicht überall scharf: große
Route-/Service-Dateien kombinieren teilweise Parsing, Orchestrierung,
Fehlerbehandlung und Datenzugriff. Ein vollständiger Architekturwechsel wäre
unverhältnismäßig und derzeit nicht empfohlen.
