# Verhaltensbasis

## Als beabsichtigt und durch Struktur/Tests belegt

- Die Anwendung verwaltet Sets, Teile, Minifiguren und Lagerorte über
  SQLAlchemy und SQLite.
- Die Desktop-Schnittstelle ist versioniert unter `/api/v1`.
- Beim Anwendungsstart werden die Blueprints `client_api` und
  `building_instructions` neben den übrigen Benutzeroberflächen registriert.
- Uploads akzeptieren PNG, JPG/JPEG und GIF-Dateinamen. Die historische
  Erweiterung `.gi` bleibt aus Kompatibilitätsgründen ebenfalls akzeptiert.
- Rebrickable- und Brickognize-Integrationen sind Services, nicht Voraussetzungen
  jeder Anfrage.
- Statuswerte für Sets werden in `models.py` als Mengen definiert; Teile eines
  Sets und Minifiguren werden kaskadierend zugeordnet.
- Regelmäßige Backups sowie fehlende-Teile- und Set-Synchronisierung werden vom
  Scheduler eingerichtet.

## Historisch gewachsen / zu bestätigen

- `app.py` führt beim Import Tabellenanlage, Lookup-Laden und Scheduler-Setup
  aus. Das ist gegenwärtiges Verhalten, aber noch nicht als gewünschter
  öffentlicher Vertrag bewertet.
- Lokale Entwicklungswerte für Token und Secret sind vorhanden. Sie werden
  nicht als sichere Produktionsvorgabe interpretiert.

## Fehlerhaft oder unbestimmt

In diesem Audit wurde kein neues Verhalten als nachweislich fehlerhaft
klassifiziert. Live-Synchronisierung, Backup-Wiederherstellung, reale
Browserabläufe und Datenmigrationen wurden nicht ausgeführt und bleiben
unbestimmt.

## Charakterisierungsschwerpunkte

Vor Änderungen an den genannten Bereichen sind Tests für Import-/Scheduler-
Grenzen, ungültige API- und Upload-Eingaben, fehlende Datensätze sowie externe
Servicefehler zu ergänzen.
