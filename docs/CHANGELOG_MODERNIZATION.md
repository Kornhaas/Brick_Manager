# Modernisierungs-Änderungsprotokoll

## 2026-10-23

- Architektur-, Risiko-, Schuld-, Verhaltens-, Test- und UX-Audit ergänzt.
- Reproduzierbare Ausgangswerte für Testanzahl und Line Coverage dokumentiert.
- Startvertrag um die erwartete Blueprint-Registrierung von `client_api` und
  `building_instructions` abgesichert.
- Uploads akzeptieren nun die beabsichtigte GIF-Endung; die historische `.gi`
  bleibt kompatibel.
- Desktop-API-Fehlerverträge für ungültige Mengen, unbekannte Ressourcen und
  zu lange Lagertexte zusätzlich abgesichert.
- Coverage-Konfiguration um Branch-Messung erweitert; der nächste vollständige
  Lauf belegt 63,58 % Line-, 51,18 % Branch- und 60,86 % kombinierte Coverage.
- Die erzwungene Coverage-Schwelle wurde von 16 % auf 60 % angehoben.
- System- und UI-Verträge für Dashboard, Details, Cachebilder,
  Bauanleitungen, Lagerorte, Upload- und Set-Mengenänderungen ergänzt.
- JSON-Schreibendpunkte validieren Nutzlasttypen und Mengen vor der Mutation;
  Datenbankfehler werden zurückgerollt und nicht mehr an Clients durchgereicht.
- Upload-Dateien erhalten kollisionsfreie generierte Namen; der Debug-Cache ist
  außerhalb von Test- und Debugbetrieb nicht erreichbar.
- Token-, Admin-Sync-, Setlisten- und Katalog-API-Verträge decken Authentisierung,
  Pagination, Timeouts, Rate-Limits, Teilfehler und neutrale Fehlermeldungen ab.
- Katalogtabellen werden je CSV transaktional ersetzt; ein fehlgeschlagener
  Append bewahrt vorhandene Referenzdaten und die Quelldatei.
- Das App-Logging verwendet den dynamischen Flask-CLI-/WSGI-Stream und erzeugt
  beim lokalen Start keinen Fehler durch einen veralteten Terminal-Handler.
- Der Web-Katalogimport bietet einen Hintergrundjob mit Fortschrittsbalken,
  Datei-Checkliste, Phasenstatus, Datensatzanzahlen und Wiederaufnahme nach Reload.

Kompatibilität: keine Schema-, Migrations-, Datenformat-, API-Feld- oder
Remote-Verhaltensänderung. Die GIF-Annahme ist additiv; `.gi` bleibt unterstützt.

Verifiziert: 361 Tests bestanden, 0 fehlgeschlagen, 0 übersprungen. Das
80-%-Ziel bleibt offen; die große Sync-, Token- und Missing-Parts-Logik benötigt
weitere fachliche Tests, bevor eine strukturelle Zerlegung vorgenommen wird.
