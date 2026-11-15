# High-Level-Design

## Zweck und Umfang

Brick Manager verwaltet eine LEGO-Sammlung mit Sets, Teilen und Lagerorten. Katalogdaten von Rebrickable unterstützen Suche und Zuordnung; Brickognize unterstützt die bildbasierte Teileerkennung. Das Web-UI umfasst unter anderem Bestandsbearbeitung, Lagerverwaltung, fehlende Teile und Etiketten. Eine JSON-Schnittstelle unterstützt Desktop-Clients.

Dieses Dokument beschreibt den bestehenden Systemzuschnitt. Komponenten und Laufzeitdetails stehen in der [Referenzarchitektur](reference-architecture.md), Implementierungsregeln im [Softwaredesign](software-design.md).

## Systemkontext

| Beteiligter bzw. System | Interaktion |
| --- | --- |
| Sammlungsnutzer im Browser | Jinja-Seiten und JavaScript für Suche, Bestand, Lagerorte und Verwaltung |
| Desktop-Client | Authentifizierte `/api/v1`-Anfragen |
| Rebrickable | Externe Katalog- und Sammlungsintegration |
| Brickognize | Externe Bilderkennung |
| Lokale Ablage | SQLite sowie Dateien für Uploads, Caches, Lookup-Daten und erzeugte Ausgaben |

Der Anwendungsprozess nutzt Flask und APScheduler. Die bestehende Systemgrafik und Komponentenübersicht werden zentral in der [Referenzarchitektur](reference-architecture.md#systemübersicht) gepflegt.

## Hauptabläufe

1. **Sammlung bearbeiten:** Browseranfragen erreichen einen Blueprint; Routen und Services lesen oder verändern Modelle und liefern HTML bzw. JSON. JavaScript aktualisiert betroffene UI-Zustände.
2. **Teile suchen und zuordnen:** Routen kombinieren Kataloginformationen, lokale Lookup-/Lagerdaten und bei Bedarf externe Dienste. Der konkrete Persistenzweg hängt vom Workflow ab; nicht alle Lagerinformationen liegen ausschließlich in SQLite.
3. **Kataloge und Sammlungsdaten synchronisieren:** Import- und Sync-Routen bzw. Hintergrundjobs verwenden Integrationsservices. Austauschbare Katalogdaten und sammlungseigener Zustand müssen getrennt erhalten bleiben.
4. **Ausgaben erzeugen:** Services erstellen unter anderem Etiketten; Bild- und Dateicaches unterstützen die Darstellung. Dateipfade und Fehlerbereinigung gehören zum jeweiligen Vertrag.
5. **Desktop-Zugriff:** Der API-Blueprint prüft Bearer-Zugangsdaten und liefert die vereinbarten JSON-Verträge. Diese Authentifizierung schützt nicht automatisch die Web-UI.

## Qualitätsziele und Grenzen

Sammlungsdaten erhalten, externe Fehler kontrolliert behandeln und die vorhandene Flask-/Jinja-Struktur verständlich erweitern. Änderungen müssen öffentliche Verträge und Bedienabläufe berücksichtigen. Die bestehende Startlogik hat Datenbank- und Scheduler-Seiteneffekte; Details und Testfolgen stehen in der Referenzarchitektur.

Sicherheits- und Betriebsannahmen stehen in der [Konfigurationsreferenz](../reference/configuration.md) und der [Docker-Anleitung](../guides/docker.md). Dieses Dokument erklärt keine öffentliche Bereitstellung für automatisch abgesichert.

## Nachweis und Pflege

Quellen sind `brick_manager/app.py`, `routes/`, `services/`, `models.py`, `templates/` und `static/` sowie die verlinkte Referenzarchitektur. Änderungen an Systemgrenzen, Hauptabläufen oder externen Beteiligten aktualisieren dieses Dokument im selben Arbeitsauftrag. Neue Zielbilder sind als Vorschläge zu kennzeichnen und nach Annahme in den [Architekturentscheidungen](decisions.md) festzuhalten.

## Geplante Erweiterung

Der [Implementierungsplan für Lageransicht, Archivierung und Einlagerung](../plans/storage-archive-intake.md) beschreibt die vorgeschlagene Trennung von festen Orten, beweglichen Behältern und Aufstellungen sowie sichere Bewegungen und regelbasierte Vorschläge. Dieser Plan ist noch nicht umgesetzt; die hier beschriebene bestehende Architektur bleibt davon unberührt.
