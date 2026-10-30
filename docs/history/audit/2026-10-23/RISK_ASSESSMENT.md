# Risikobewertung

| Risiko | Einstufung | Begründung | Schutzmaßnahme |
|---|---|---|---|
| Persistente Sammlungsdaten | hoch | SQLAlchemy-Modelle und SQLite sind zentrale Datenquelle. | Keine Migration, kein Reset und keine Datenformatänderung ohne explizite Freigabe und Backup-/Rollback-Plan. |
| Externe Synchronisierung | hoch | Rebrickable-/Brickognize-Aufrufe können Datenzustände verändern und benötigen Credentials. | Nur gemockt testen; keine Live-Aufrufe oder Remote-Schreibvorgänge im Modernisierungsprozess. |
| Start- und Scheduler-Verhalten | hoch | Modulimport hat Seiteneffekte und registriert zeitgesteuerte Aufgaben. | Isolierte Tests verwenden; Umstrukturierung erst nach Start-Charakterisierung. |
| Öffentliche Desktop-API | hoch | `/api/v1` ist ein externer Vertrag. | Keine Feld-, Status- oder Authentifizierungsänderung ohne Sync-Contract-Prüfung und Freigabe. |
| Dateiuploads und Label-Ausgabe | mittel | Unvertrauenswürdige Dateinamen/Inhalte und Dateisystemzugriffe. | Eingabe-/Pfadtests beibehalten und bei Änderungen gezielt erweitern. |
| Entwicklungs-Defaults in Config | mittel | Standardschlüssel können bei falscher Betriebsumgebung genutzt werden. | Operative Härtung nur nach Klärung der gewünschten Kompatibilität. |

Dieses Dokument beschreibt Risiken, nicht bestätigte Sicherheitslücken. Eine
autorisierte Sicherheitsprüfung war nicht Teil dieses Auftrags.
