# Zielarchitektur

Die bestehende Flask-Blueprint-/Service-/Model-Struktur bleibt erhalten.
Ziel ist keine neue Schichtenarchitektur, sondern klarere Grenzen innerhalb
dieser vorhandenen Struktur:

- Routen: Eingabeprüfung, HTTP-Status, Rendering und Aufruf von Services.
- Services: wiederverwendbare Fach-, Integrations-, Datei- und Renderlogik.
- Modelle: Persistenzstruktur und einfache Serialisierung.
- App-Komposition: Konfiguration, Erweiterungsinitialisierung, Blueprint- und
  Scheduler-Registrierung.

Große Module werden nur schrittweise entlang getesteter, stabiler Grenzen
zerlegt. Öffentliche Routen, Datenbanktabellen, Persistenzformate und
Integrationverträge bleiben dabei unverändert.
