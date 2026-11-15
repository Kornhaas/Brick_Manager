# Lagerverwaltung: Umsetzung und Abnahme

Stand: 2026-11-15. Grundlage: [Implementierungsplan](storage-archive-intake.md).
Alle Pakete sind im Checkout umgesetzt. Der letzte vollständige Lauf nach allen Korrekturen bestand am 2026-11-15 in 61,47 Sekunden.
Die automatisierte Abnahme verwendet
repräsentative Testfächer; ein echtes Pilotfach und reale Messwerte sind keine
Voraussetzung für Implementierung und Tests. Die Auswahl und physische Vermessung
eines echten Fachs bleiben gesonderte Vor-Ort-Arbeit.

## Aufgabenliste nach Umsetzungspaketen

- [x] **P0:** Read-only-Vorabbericht, SQLite-Sicherung und repräsentative
  Alt-/Neubestandsfixtures; Bestandszuordnungen und unbekannte Werte erfasst.
- [x] **P1:** Behälter, Aufstellungen/Stapel und Mengen je Fundort;
  additive, atomare, versionierte Migration mit Prüfsummenjournal und Backfill.
- [x] **P2:** Gemeinsame Schreib-/Schutzgrenze, vollständige Lookup-Listen,
  Desktop-Kompatibilität und ID-basierte Einzel-Etiketten.
- [x] **P3:** Regalfront und Listenansicht, unten beginnende Stapelerfassung,
  Magazine, Schubladen, Unterteilungen und Such-Deeplinks.
- [x] **P4:** Entwurf, Reservierung, Bestätigung, Abbruch, Zugang,
  Teilumbuchung, Behälterbewegung und explizite Entfernung leerer Hüllen.
- [x] **P5:** Verifizierte Stapelpaarungen, lose Auflage, gemessene
  Positions-/Höhenprüfung und getrennte Stellflächenintervalle.
- [x] **P6a:** Historische Vorkommen, Generation/Abdeckung, Kategorieziele,
  Präferenzen und unbekannter Eigenbedarf.
- [x] **P6b:** Separate eigene Planliste, Inventarbedarfsauflösung und
  invalidierbare Bestätigung ihrer Vollständigkeit.
- [x] **P7:** Manuelle V1-Archivprüfung und Aufnahmevorschläge mit
  Datenlückenerklärung; kein Archivstandard bei unbekanntem Eigenbedarf.
- [x] **P8 automatisiert:** Kriterienabgleich, gesamte Python-Suite,
  JavaScript-Prüfungen, echter Chromium-Durchlauf, statische Prüfungen,
  Paketbuild und Dokumentationsabgleich.
- [ ] **P8 vor Ort:** Späteres reales Fach auswählen, Inhalte zählen,
  Maße/Stapel-/Last-/Zugriffsbedingungen prüfen und reale Bewegungen abgleichen.
  Dieser Punkt begrenzt reale Passzusagen, blockiert aber keine technische Abnahme.

## Kriterienabgleich

Dateinamen in dieser Tabelle beziehen sich auf `brick_manager/tests/`; der echte
Browserdurchlauf steht unter `tests/browser/warehouse_smoke.py`.

| Kriterium aus dem Plan | Implementierung / tatsächlich geprüfter Nachweis |
| --- | --- |
| Vollständige Erfassung vorhandener Zuordnungen | Read-only-Bericht und `LegacyStorageMapping`; `test_storage_migration.py` erhält jede Altzeile samt NULL, Texten und IDs. Keine Zuordnung zu einer erfundenen physischen Einheit. |
| Frische Datenbank und alter Bestand | `test_fresh_database_migrates_and_works_through_sqlalchemy` sowie `test_old_rows_labels_counts_and_unknowns_are_preserved`; alte Setmengen und bekannte Lagerzählwerte erhalten. |
| Wiederholung, Unterbrechung, FK-Lücken | Migration zweimal, Prüfsummenänderung, atomarer Schema-/Backfill-Rollback und Vergleich neuer/alter FK-Lücken in `test_storage_migration.py`; vorhandene Migrationstests zusätzlich ausgeführt. |
| Sicherung und Startpfade | SQLite-Backup inkl. Wiederöffnen; `test_backup_only_cli_does_not_migrate_selected_database`; Docker/lokaler Start nutzen denselben Runner. `bash -n docker-entrypoint.sh` erfolgreich. |
| Alte Schreibwege ohne beliebiges Überschreiben | `test_storage_legacy_compatibility.py`: UI-Schreib-/Löschwege werden für strukturierte Bestände mit 409 gesperrt; API prüft zuvor den Bearer-Key. Bestehende manuelle Einfügungen bleiben durch die alte Query-/Datenerhaltregression abgesichert. |
| Mehrfachorte, Farbe und Suchsprung | Vollständige Lookup-Listen ohne Last-row-wins; Test mit zwei Orten und stabiler ID-Verlinkung; Browser prüft Query-Deeplink. Unbekannte Altfarbe kann über den regulären PATCH-Endpunkt aufgelöst werden. Eine aktive Planung zeigt im Suchergebnis gesondert Ziel und Menge, während Istadresse und Istmenge bis zur Bestätigung unverändert bleiben. |
| Gemischtes Fach und doppelte Beschriftungen | `test_warehouse_contracts.py`, `test_storage_structure.py`: unterschiedliche Typen und gleiche sichtbare Etiketten behalten eigene IDs; Browser erfasst repräsentative Boxen und Magazine. |
| Etikettlücken und Inhalt beim Verschieben | `test_unit_move_preserves_labels_and_old_address_until_confirmed`, `test_whole_box_moves_with_contents_only_after_confirmation`; keine Neunummerierung. |
| Tiefer Stapel und Zyklen | `test_twenty_level_stack_resolves_every_level_and_rejects_cycle`: 20 technische Ebenen, vollständige Adressauflösung und Zyklusabwehr, ohne reale Höhenfreigabe. |
| HMH nur innerhalb derselben Größe | Struktur- und HTTP-Tests für gleiche/verschiedene Größen; verifizierte Regeln erforderlich. Browser legt eine Regel an und erfasst die obere Box über das echte Formular. |
| Lose Auflage und unbestätigte Paarungen | CYEER `loose_on` in Struktur-, HTTP- und Browsertests; ungültige Flächen/Offsets und überlappende Auflagen werden abgewiesen. Unbekannte Paarungen bleiben ungeprüfte Beobachtung. |
| Magazine und 1/2/3 Inhaltsbereiche | Beide Standardmagazine erzeugen 30/9 Schubladen. Struktur-/HTTP-Tests prüfen Unterteilungen, Wiederholung mit unveränderten IDs und Sperre belegter Umgestaltung; Browser erfasst drei Unterteilungen. |
| Plan versus Ist und physische Bestätigung | `test_quantity_move_is_ineffective_until_confirmation_and_idempotent`, regulärer HTTP-Move und Browser: Planung ändert weder Mengen noch Fundort. Native Bestätigungsabfrage vor der physischen Buchung. |
| Teilmenge und belegtes Ziel | Quelle 10/Ziel 2/Transfer 4 ergibt 6/6; vorhandener Zielbestand wird addiert. Ungültige Mengen, unbekannte Zählung und volle Ziele werden abgewiesen; Kapazitätsunsicherheit erfordert Bestätigung. |
| Wiederholung, Konkurrenz, Veraltung | Idempotenzschlüssel/Revision, überhöhte Sammelmenge, Zwei-Sitzungs-SQLite-Reservierungsrennen und veränderte Geometrie/Regeln geprüft. Mehrere zukünftige Ziele dürfen weder Fachboden noch Stapelposition doppelt belegen. |
| Größerer Behälter, zweiter Ort und Unterbrechung | Identische geprüfte Mengenbewegung zu einem anderen konkreten Behälter; Restbestand und Leerhülle bleiben erhalten. Einzelbewegungen, Abbruch und vorausgehender Auftrag sind in `test_storage_moves.py` geprüft. Bestätigte Schritte werden nicht rückgängig gelöscht. |
| Leer, niedriger oder Grundfläche frei | Tests für leere Hülle ohne Flächengewinn, obere entfernte Einheit ohne Basisgewinn, erst nach Bestätigung entfernte Basis, No-op ohne erfundenen Gewinn und Vorher-/Nachherbericht beider Fächer. |
| Zusammenhängender Platz und Schräge | Getrennte Intervalle bleiben getrennt; gesamte Breite inkl. Zwischenmesspunkten, oberer Stapelhöhe, Nachbarmaßen/-position und Auflageposition geprüft. Unbekannte Daten ergeben keine positive Passzusage. |
| Historische Setzahl und Jahre | `test_part_history.py`: Versionen, Mengen und Ersatzteile erhöhen den Setzähler nicht; Teil/Farbe getrennt; Figuren und Untersets werden auf echte Sets aufgelöst, Zyklen/fehlende Links/Jahre bleiben unbekannt. |
| Alte/neue Varianten und Schwellen | Historische Alters-/Setzahlgrenzen einschließlich Jahrwechsel und benutzerdefinierter Werte; neue Varianten bleiben griffbereit (`test_storage_suggestions.py`). |
| Katalogabdeckung und Teilimporte | Erfolgreicher, fehlgeschlagener, veralteter und überlappender Kataloglauf getestet; bestehende Importverträge weiter bestanden. Keine Live-Netzaufrufe in diesen Tests. |
| Unbekannter Eigenbedarf in V1 | Exakter Hinweis „Eigenbedarf unbekannt · bitte prüfen“ in Service-/HTTP-/Browsertests. Manuelle Prüfung benötigt keine fertig geprüfte Planliste. |
| Geplante Sets und bekannter Bedarf | Planlisten-/Einstellungseinstieg, neuester auflösbarer Inventarstand, Untersetmengen und Invalidierung der Bedarfsprüfung getestet; positiver geplanter/offener Bedarf schützt Varianten. |
| Ganze Box und gemischter Inhalt | Vollständiger geeigneter Inhalt erforderlich; gemischter Inhalt ergibt Teilumbuchung. Auflagen, Restinhalt, Kapazitätsprüfung und Platzwirkung werden explizit angezeigt. |
| Aufnahme-Standard und Nutzerwahl | Unbekannter Bedarf behält Kategorieregal selbst mit passendem Archivbestand; volle Zielorte, manuelles Griffbereit-Override und fehlende Daten werden getestet. Browser prüft die tatsächlichen Formularwerte und Erklärung. |
| Sichere Oberfläche und Fehlerzustände | CSRF mit echter Browser-Sitzung, ungültige JSON-/Farbtypen, fehlende IDs, geschützte API-Authentifizierung, `textContent`-Darstellung, Listen-/Tastaturalternative und Fokus bei 390px. Lager-Feature-Schalter sperrt neue Mutationen. |
| Etikettidentität und Druckbestätigung | ID-spezifische Label-Endpunkte, getrennte Ausgabedateien bei gleichem Text, keine automatische Druckbestätigung; reguläre Route mit temporärer Ausgabe geprüft. |

## Ausgeführte Gesamtprüfungen

- `poetry run pytest -q`: **518 bestanden, 0 fehlgeschlagen, 0 übersprungen**;
  Gesamt-Coverage **71,34 %**, konfiguriertes 60-%-Gate erfüllt.
- Fokussierte Migration-/Struktur-/Move-/Legacy-/HTTP-/History-/Vorschlagssuites
  wurden während der Umsetzung wiederholt ausgeführt. Regressionen wurden vor
  Korrektur reproduziert und anschließend erneut geprüft. Der Gesamtlauf oben
  wurde nach den Produktionscodekorrekturen erneut ausgeführt.
- `poetry run ruff check brick_manager scripts tests/browser`: erfolgreich.
- `poetry run ruff format --check brick_manager scripts tests/browser`: erfolgreich.
- `poetry run basedpyright`: **0 Fehler, 0 Warnungen**. Eine bereits vorhandene
  unpräzise Label-Offset-Signatur wurde passend zum vorhandenen Float-Verhalten
  annotiert; keine fachliche Änderung und keine globale Abschwächung der Analyse.
- `node --check brick_manager/static/js/warehouse.js`: erfolgreich.
- `node --test tests/js/quantity_navigation.cjs`: **8 bestanden**. Beim ersten
  Lauf fiel ein bereits im Ausgangsstand defekter EventTarget-Ersatz auf: Er
  behielt nur den letzten Keydown-Listener. Der Test-Harness bildet jetzt mehrere
  Listener korrekt ab und prüft getrennt Tab sowie Enter; Produktcode unverändert.
- Playwright mit echtem Chromium: **8 Ablaufprüfungen erfolgreich, 0 JavaScript-Fehler**;
  isolierte Test-App, CSRF aktiv, repräsentatives Fach, externe Requests abgefangen.
- Bandit auf den sechs neuen/geänderten Storage-/History-/Move-/Suggestion-/Migrations-/Warehouse-Modulen:
  erfolgreich ohne gemeldete Findings.
- `poetry build`: Source-Distribution und Wheel gebaut; Artefaktinhalt auf neue
  Migration und Warehouse-Dateien geprüft.
- Lokale Markdown-Datei-/Abschnittsverweise und Diff-Whitespace-Prüfung unter
  Beachtung der bestehenden CRLF-Dateien geprüft.

Playwright und Node wurden für diese Prüfung in temporären Werkzeugverzeichnissen
bereitgestellt; sie sind keine neuen Laufzeitabhängigkeiten der Anwendung. Der
reproduzierbare Browseraufruf ist in der [Testanleitung](../guides/testing.md)
beschrieben. Kein Push, Deployment, Live-Sync oder Zugriff auf eine Produktivdatenbank.

## Offene Vor-Ort-Prüfungen

Reales Fach und echte Behälter auswählen, Rohbeschriftungen/Identitäten zuordnen,
Inhalte/Farben/Mengen prüfen und anschließend bewusst als vollständig markieren.
Außenmaßreihenfolge, tatsächliche nutzbare Auflage, Stapelhöhenzunahme, zulässige
Höhe/Last, Entnahmefreiraum und Freihöhe unter einer Schräge messen bzw. bestätigen.
Gemischte Feinkost-Paarungen, CYEER-Auflagen und die tatsächliche Magazinaufstellung
vor Ort prüfen. Testfixtures sind keine Produkt- oder Sicherheitsfreigabe.

Die Software bleibt mit unbekannten Maßen nutzbar und zeigt die Grenzen an. Es
wurde weder ein reales Fach als korrekt eingeräumt abgenommen noch behauptet,
dass alle denkbaren Fehlerfälle bei 71,34 % Gesamt-Coverage ausgeschlossen sind.

## Nachprüfung des Startup-Pfads

Die später gemeldete Startup-Lücke bei fehlenden SQLite-Unterverzeichnissen ist
korrigiert und durch relative/absolute Pfadtests sowie den echten Flask-CLI-Loader
mit temporärer Datenbank abgesichert. Abschließender vollständiger Lauf:
**521 bestanden, 0 fehlgeschlagen, 0 übersprungen, 71,34 % Coverage**.
Details im [Logbuch](../logbook.md) und in der [Entwicklungsanleitung](../guides/development.md#sqlite-pfade-beim-lokalen-start).

## Nachprüfung: Sichtbarkeit vorhandener Lagerzuordnungen

Die Regalübersicht zeigt bestehende Rohzuordnungen jetzt als unbestätigte
Beschriftungsgruppen; zuvor waren trotz erhaltener Inhalte nur physische
Einheiten sichtbar. Fehlende/mehrdeutige Adressen bleiben auffindbar.
`test_warehouse_legacy_overview.py` und der zusätzliche echte Browserlauf
`tests/browser/warehouse_legacy_smoke.py` prüfen diesen regulären Einstieg samt
Einzelzuordnung und unbekannter Belegung. Abschließender Gesamtlauf:
534 bestanden, 0 fehlgeschlagen, 0 übersprungen; 71,58 % Coverage.
Keine zusätzliche Migration oder automatische Behältererzeugung erforderlich.
Die Vor-Ort-Grenzen der ursprünglichen Abnahme bleiben bestehen.

## Nachprüfung: Bilder und vorgemerkte Etiketten

Fehlende Stammbilder erhalten eine gebündelte Inventarbildalternative. Explizite
Neudruckvormerkungen sind dauerhaft und unabhängig vom Druckstatus; Druck und
Bestätigung nutzen unveränderte Ziel-/Inhaltssnapshots. Bestehende Rohzuordnungen
und physische Einheiten sind unterstützt, ohne Mengen oder Aufstellungen zu ändern.
15 zusätzliche Regressionen und `warehouse_labels_smoke.py` prüfen den gesamten
Ablauf einschließlich Downloadfehler und veralteter Bestätigung. Alle drei
Browserläufe und der abschließende Gesamtlauf bestanden: **549 Tests**, keine
Fehler/Skips, **72,06 % Coverage**. Keine Schemaänderung erforderlich. Tatsächlicher
Druck und Kalibrierung bleiben Vor-Ort-Prüfungen.

## Nachprüfung: Ladezeit der Lagerübersicht

Die Startansicht lädt Altinhalte des ausgewählten Fachs; ungeklärte Gruppen und
globale Auswahlformulare laden ihre Inhalte bei Bedarf. Die Gesamtansicht bleibt
explizit verfügbar und der vollständige bisherige Datenvertrag kompatibel.
Ein neuer journalisierter Covering Index beschleunigt die Inventarbildsuche.
Frische Datenbank, vorhandenes Schema, Wiederholung, erhaltener Bestand und
Indexnutzung sind geprüft. Abschließender Gesamtlauf: **553 bestanden**, keine
Fehler/Skips, **72,24 % Coverage**; alle drei Browserläufe bestanden.
Lokale Vergleichsmessungen und Grenzen stehen in der
[Testanleitung](../guides/testing.md#fachweise-datenabfrage-und-inventarbildindex).
