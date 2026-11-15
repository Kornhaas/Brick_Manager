# Projektlogbuch

Das Logbuch dokumentiert abgeschlossene Arbeitsaufträge ab seiner Einführung. Frühere Berichte bleiben unter [Historie](history/README.md); historische Ergebnisse werden nicht nachträglich erfunden. Neuere Einträge stehen oben. Datum, Ergebnis, Grund, betroffene Dokumente, ausgeführte Prüfungen und offene Grenzen festhalten. Bei reinen Detailänderungen ohne Designauswirkung dies kurz begründen.

## 2026-11-15 – Entwicklungsserver auf ausdrücklich gewählte Datenbank umgestellt

**Auftrag und Ergebnis:** Auf Nutzerwunsch die vorhandene Datei `brick_manager/instance/brick_manager.db` verwendet. Der zuvor laufende Entwicklungsserver hatte aufgrund des relativen `.env`-Overrides die andere Datei `brick_manager/instance/data/instance/brick_manager.db` geöffnet. Den lokalen, nicht versionierten Override auf den absoluten gewünschten Pfad geändert, den bisherigen Projektserver regulär beendet und Flask auf `127.0.0.1:5000` mit genau dieser Datenbank neu gestartet.

**Sicherung und Prüfung:** Vorher konsistente SQLite-Sicherung unter `brick_manager/instance/backups/brick_manager-before-start-20261115T113301629290Z.db` angelegt. Migration an einer temporären Kopie geprüft, anschließend beim autorisierten Start angewendet. Die Zeilenzahlen aller 19 ursprünglichen Tabellen sind gegenüber der Sicherung unverändert; keine Fremdschlüsselverletzungen. Zwei Migrationsstände sind journalisiert. Die gewählte Datei enthält derzeit 0 eigene Sets und 0 Lagerzuordnungen.

**Laufzeitnachweis:** Offene Dateideskriptoren des neuen Flask-Prozesses zeigen die ausdrücklich gewählte Datei. `/health` und `/warehouse` antworten mit HTTP 200. Keine Anwendungscodeänderung, kein Deployment, Reset oder Restore; der Entwicklungsserver bleibt aktiv.

## 2026-11-15 – SQLite-Start mit verschachteltem Datenbankpfad korrigiert

**Fehler und Ursache:** Der reguläre Flask-Start brach beim Migrationsrunner mit `sqlite3.OperationalError: unable to open database file` ab, wenn der konfigurierte Datenbankpfad zusätzliche noch fehlende Unterverzeichnisse enthielt. Relative SQLite-Adressen werden von Flask-SQLAlchemy unter seinem Instance-Verzeichnis aufgelöst; das Anlegen des separat konfigurierten Instance-Ordners reicht dafür nicht.

**Korrektur:** Der Runner legt die Elternverzeichnisse genau der ausgewählten SQLite-Datei vor dem Öffnen an. Keine alternative Datenbank, kein Reset und keine Änderung bereits versionierter Migrationsartefakte. Read-only-Inspektion und Sicherungsquellen bleiben von der Verzeichniserzeugung getrennt. Die Entwicklungsanleitung erklärt Pfadauflösung und erneutes `.env`-Laden trotz `env -u`.

**Verifikation:** Fehler für relative/absolute verschachtelte Pfade und über den regulären Flask-CLI-Loader mit einer temporären Datenbank reproduziert. Nach Korrektur 13 fokussierte Migrations-/Starttests bestanden, einschließlich Wiederholung und Erhalt eines gespeicherten Eintrags. Ruff, Formatprüfung und BasedPyright für die Änderung erfolgreich. Abschließender Gesamtlauf: **521 bestanden, 0 fehlgeschlagen, 0 übersprungen, 71,34 % Coverage** (113,34 Sekunden). Kein Start gegen die vorhandene Bestandsdatenbank ausgeführt; vorhandene Projekt-/Abhängigkeitsänderungen beibehalten.

## 2026-11-15 – Lagerverwaltung vollständig implementiert und automatisiert abgenommen

**Ergebnis:** P0–P7 einschließlich eigener Planliste und P8-Automation umgesetzt: feste Orte, identifizierbare Behälter/Stapel, Mengen je Fundort, additive Migration, Altbestandsabgleich, Regalfront/Listenansicht, bestätigte Bewegungen, Stellflächen-/Höhenprüfung, Kataloghistorie sowie manuelle Archiv- und Aufnahmevorschläge. Der unbekannte Eigenbedarf trägt den abgestimmten Hinweis; bei Aufnahme bleibt das Kategorieregal Standard. Repräsentative Testfächer ersetzen die Voraussetzung eines echten Pilotfachs.

**Datenerhalt und Review:** Frische und alte Testdatenbanken, unveränderte Mengen/Beschriftungen, Migrationswiederholung und Rollback geprüft. Zusätzliche unabhängige Prüfungen führten zu Regressionstests für unbekannte Nachbarmaße, ganze Stapelhöhen, doppelte Zukunftsziele, lose Auflageflächen, unveränderte Stapelregeln, No-op-Platzwirkungen und belegte Magazinkinder. Unbekannte Altfarben können explizit aufgelöst werden. API-Authentifizierung bleibt der Legacy-Konfliktprüfung vorgelagert. Bestehende Änderungen an Sprachregel und Projektdateien beibehalten.

**Verifikation:** Abschließender vollständiger Python-Lauf **518 bestanden, 0 fehlgeschlagen, 0 übersprungen, 71,34 % Coverage**. Node-Navigation **8 bestanden** und Warehouse-Syntax geprüft; der bestehende Test-Harness wurde für mehrere unabhängige Eventlistener korrigiert. Echter Chromium-Durchlauf **8 Ablaufprüfungen, 0 JavaScript-Fehler** mit aktiver CSRF-Prüfung. Ruff, Formatprüfung, projektweites BasedPyright (0 Fehler/Warnungen), fokussiertes Bandit, Shell-Syntax, Source-/Wheel-Build sowie lokale Dokumentationsverweise und CRLF-bewusste Diff-Prüfung erfolgreich. Alle Prüfungen nutzten Entwicklungs-/Testumgebungen; keine Produktivdatenbank, Live-Synchronisation, Push oder Deployment.

**Dokumentation und Grenzen:** [Abnahmeprotokoll](plans/storage-acceptance.md) gleicht jedes Plankriterium ab; [Lageranleitung](guides/warehouse.md), Schema, Architektur, Softwaredesign, Konfiguration und Testanleitung beschreiben den Iststand. Reale Auswahl, Zählung und Vermessung eines Lagerfachs sowie Bestätigung von Auflage-, Last- und Zugriffseigenschaften bleiben Vor-Ort-Arbeit. Unbekannte Maße werden nicht als sichere Passung ausgegeben.

## 2026-11-15 – Bricks als verbindlicher Produktbegriff

**Ergebnis und Grund:** Nutzerwunsch zur Projektsprache in `AGENTS.md` und der [Terminologiereferenz](reference/terminology.md) festgehalten und im Index verlinkt. Eigene Texte verwenden Bricks; der Projektname bleibt Brick Manager. Bereits vorhandene Textänderungen in Anwendung, Projektkommentaren und Dokumentation beibehalten.

**Prüfung:** Repositoryweite Textsuche einschließlich versteckter Projektdateien durchgeführt. Verbliebene Treffer betreffen vorgeschriebene externe API-Pfade samt Tests, einen bestehenden technischen Dateiverweis und generierte Analyseauszüge. Diese werden nicht pauschal umbenannt. Lokale Links und `git diff --check` für die in diesem Auftrag geänderten Dokumentationsdateien geprüft. Keine Anwendungstests für die reine Dokumentationsänderung ausgeführt.

**Grenzen:** Keine fachliche Änderung oder Datenmigration; Original-Katalog- und Nutzerdaten bleiben erhalten. Technisch erforderliche Schreibweisen bleiben gültig. Die Sprachregel ist keine rechtliche Bewertung.

## 2026-11-15 – V1-Entscheidungen zur Archivprüfung bestätigt

**Ergebnis und Grund:** Nutzerentscheidung im [Lagerplan](plans/storage-archive-intake.md) und [Entscheidungsprotokoll](architecture/decisions.md) festgehalten: zuerst Behälter, Stapel und Mengen je Fundort einschließlich Migrations-/Schreibgrundlage. Bereits V1 zeigt alte, seltene Teile bei belastbarer Set-Anzahl und belastbarem letztem Set-Jahr trotz unbekanntem Eigenbedarf zur manuellen Archivprüfung mit „Eigenbedarf unbekannt · bitte prüfen“. Der Nutzer entscheidet über Archivierung; bei Aufnahme bleibt das Kategorieregal Standard, bis der Eigenbedarf geklärt ist. Eine eigene Planliste ist dafür keine Voraussetzung.

**Korrektur zum ursprünglichen Planeintrag:** Regal 1/Fach 5 war ausschließlich ein Dummy-Beispiel, kein festgelegtes reales Pilotfach. Der Nutzer bestimmt das Pilotfach später. Paketabhängigkeiten, UI-Regeln und Testmatrix wurden entsprechend präzisiert; der Index verweist auf den aktualisierten Plan. Die übrigen reversiblen Planungsannahmen bleiben offen.

**Prüfung und Grenzen:** Dokumentationsverweise und `git diff --check` geprüft. Nur Dokumentation geändert; keine Anwendungstests, Datenbankzugriffe oder Implementierung ausgeführt. Die Bestätigung dokumentiert Produktentscheidungen vor der Umsetzung.

## 2026-11-15 – Lager-, Archivierungs- und Einlagerungsplan

**Ergebnis und Grund:** Den [Implementierungsplan](plans/storage-archive-intake.md) für Lageransicht, Archivierung und Einlagerung anhand des Checkouts `845921b` erstellt. Er umfasst konkrete Code-Einstiegspunkte, Datenlücken, ein additives Zielmodell mit Migrations-/Kompatibilitätsstrategie, UI-Abläufe, regelbasierte historische Auswertung, sicheren Umgang mit unbekanntem Bedarf, Umsetzungspakete, Testmatrix und Pilot Regal 1/Fach 5. Annahmen und erst vor Ort mögliche Passprüfungen sind gekennzeichnet.

**Dokumentation:** Plan im Index sowie in High-Level- und Softwaredesign als unimplementierter Vorschlag verlinkt. Schema- und Ist-Referenzarchitektur bleiben inhaltlich unverändert, da kein neues Laufzeitverhalten implementiert wurde. Es wurden keine neuen Architekturentscheidungen als bereits angenommen eingetragen.

**Prüfung:** Modelle, betroffene Routen/Services, Import-/Migrationsablauf, UI-Einstiegspunkte und einschlägige Testdateien statisch gelesen. Lokale Markdown-Datei- und Abschnittsverweise der für diesen Auftrag geänderten Dokumente sowie `git diff --check` geprüft; der dokumentierte Git-Diff der Anwendungsdateien ist leer. Keine Anwendungstests, Serverstarts, Datenbankzugriffe, Migrationen oder externen Synchronisationen ausgeführt.

**Offene Grenzen:** Reale Datenqualität und Inhalt/Geometrie des Pilotfachs sind ungeprüft. Maße und Stapelaussagen aus dem Auftrag wurden nicht unabhängig verifiziert. Automatische Archivkandidaten erfordern künftig geprüfte Katalog-/Inhalts-/Bedarfsabdeckung. Die Phase endet mit dem Plan; Anwendungscode und Datenbank bleiben unverändert.

## 2026-11-15 – KI-Rollen und zentrale Dokumentationspflege

**Ergebnis und Grund:** Die vorhandenen vier Fach-Skills wurden durch Architektur-, UX- und Security-Skills sowie sieben projektbezogene Agenten ergänzt. Architektur, Entwicklung, Tests, Usability, Sicherheit, Datenbank und UX-Design haben eigene Zuständigkeiten. Die Einrichtung ist in der [KI-Anleitung](guides/ai-collaboration.md) beschrieben.

`docs/` ist als zentrale Projektablage verbindlich festgelegt. [High-Level-Design](architecture/high-level-design.md) und [Softwaredesign](architecture/software-design.md) ergänzen die vorhandene [Referenzarchitektur](architecture/reference-architecture.md). `AGENTS.md` und die Entwicklungs-/Architektur-Skills verlangen Dokumentationspflege im selben Change und einen integrierten Logbucheintrag. Der [Dokumentationsindex](README.md) ordnet Änderungen den passenden Dokumenten zu.

**Prüfung:** Alle sieben Skills wurden mit dem Skill-Validator erfolgreich geprüft. Die sieben Agentendateien wurden als TOML gelesen und ihre erforderlichen Felder und Skill-Verweise geprüft. Lokale Markdown-Verweise der betroffenen Dokumente und `git diff --check` wurden geprüft. Die neuen Designdokumente wurden anhand der Referenzarchitektur sowie der Teile-Lagerort-Route und Test-Fixtures abgeglichen. Es wurden keine Anwendungstests für diese Dokumentations-/Konfigurationsänderung ausgeführt.

**Offene Grenzen:** Die tatsächliche Agentenerkennung und Ausführung in einer neuen Codex-Client-Sitzung ist weiterhin ungeprüft. Diese Arbeit umfasst keinen vollständigen Architektur-, Usability- oder Sicherheitsaudit. Anwendungscode und persistierte Sammlungsdaten wurden nicht verändert.
