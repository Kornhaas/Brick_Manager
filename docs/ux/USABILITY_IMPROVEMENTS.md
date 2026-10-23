# Usability-Verbesserungen

Für dieses Audit wurden keine UI-Abläufe verändert. Die priorisierte, sichere
Reihenfolge lautet:

1. Der Upload-Hinweis nennt nun die tatsächlich akzeptierte GIF-Erweiterung;
   die Annahme wird durch einen Regressionstest geschützt.
2. vorhandene Fehler- und Validierungsantworten je Formular/JSON-Endpunkt
   durch Tests absichern;
3. unklare Fehlermeldungen nur textlich präzisieren, sofern Tests und Templates
   keine externen Textverträge brechen;
4. nach Browserprüfung gezielte Verbesserungen an Rückmeldungen bei Import,
   Upload, Synchronisierung und Label-Erzeugung vorschlagen.
