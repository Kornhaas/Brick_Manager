# GitHub-Qualität und visueller Auftritt

Stand: 22. November 2026. Die Bestandsaufnahme stammt aus Repositorydateien und
authentifizierten GitHub-API-Abfragen. Empfehlungen sind ausdrücklich noch keine
umgestellten Repositoryeinstellungen.

## Bereits umgesetzt

- Gemeinsame Gestaltung aus dem Dashboard abgeleitet: Indigo/Navy, Violett,
  Türkis, helle Karten und klare Aktionsflächen. Neue lokale SVG-Grafiken,
  Navigation und Signet; kein zusätzlicher Icon-/Grafikdienst.
- README mit eigenem Projektbanner, tatsächlich dynamischen Workflow-Badges
  und direkten Einstiegen in die Dokumentation.
- Aktualisierte Containerpakete und fehlschlagender Trivy-Job bei Befunden;
  [Details und Grenzen](../guides/docker.md#sicherheitsupdates-des-images).

## Priorität 1: vorhandene Schutzmaßnahmen wirksam machen

| Beobachteter Stand | Empfehlung | Nutzen / Grenze |
| --- | --- | --- |
| Secret Scanning und Push Protection laut API deaktiviert | Beide aktivieren | Unterstützte Zugangsdaten vor Veröffentlichung erkennen/blockieren; kein Ersatz für Tokenrotation bei bereits veröffentlichten Schlüsseln |
| Drei erforderliche Checks; Adminausnahme aktiv | Python-/Ruff-/Typenprüfung und aussagekräftige Sicherheitsergebnisse als verpflichtende PR-Checks gestalten | Prüfungen sollen Fehler tatsächlich blockieren; bestehender Pylint-Lauf meldet auch ältere Hinweise |
| Eine Freigabe plus Freigabe des letzten Pushs verlangt | Reviewregel an tatsächliche Maintainerzahl anpassen | Ein alleiniger Maintainer kann sich nicht selbst unabhängig freigeben; Adminsperre erst mit funktionierendem Freigabeweg aktivieren |
| Trivy scannt nach Registry-Push | Image zunächst bauen/scannen, erst nach Erfolg Tags veröffentlichen | Verhindert künftig auch die Veröffentlichung fehlerhafter Kandidaten |
| Dependabot prüft wöchentlich Python | GitHub Actions und Docker ergänzen; Patch-/Minor-Updates sinnvoll gruppieren | Auch Buildwerkzeuge/Basisimages aktuell halten; Major-Updates gezielt prüfen |
| Actions-Token standardmäßig read-only | Beibehalten, Drittanbieter-Actions auf geprüfte Commit-SHAs pinnen | Weniger Schreibrechte und veränderliche Buildabhängigkeiten |

## Priorität 2: Bedienbarkeit automatisch absichern

Vorhandene isolierte Browserprüfungen in CI aufnehmen: Set filtern, Detail öffnen,
Menge ändern, speichern, auf Detail bleiben, zur ursprünglichen Listenposition
zurückkehren; PDF-Download mit Fehler und Retry; Einlagern und Bestätigung.
Mindestens Desktop und 390-Pixel-Viewport sowie Tastaturbedienung prüfen.
Der neue `visual_identity_smoke.py` ergänzt sechs Seiten in beiden Größen,
mobile Navigation, Fokus und lokale Assetantworten. Ein axe-basierter
Barrierefreiheitscheck wäre die nächste Ergänzung; ein automatischer Scan
ersetzt keine Bedienprüfung.

Für neue Abhängigkeiten ist ein PR-Dependency-Review sinnvoll. CodeQL für
Python/JavaScript kann Codacy ergänzen, falls die konkrete Abdeckung zusätzliche
Risiken findet. SonarQube erst ergänzen, wenn ein gepflegtes Quality Gate für
neuen Code gewünscht ist; mehrere gleichartige Warnlisten ohne Verantwortlichkeit
verbessern das Projekt kaum. Bestehende niedrige Abdeckung besonders in
Fehlteile-/Sync-Routen gezielt durch reale Fehlerfälle verbessern, keine pauschale
100-%-Quote einführen.

## Priorität 3: einladender Projekteinstieg

Die Beschreibung, Homepage und Themen waren leer; ein eigenes Social-Preview-Bild
war bereits gesetzt. Empfohlene Beschreibung:

> Manage your Bricks collection: sets, missing parts, storage and printable labels.

Passende Themen: `bricks`, `inventory-management`, `flask`, `python`, `sqlite`,
`self-hosted`. Homepage erst setzen, wenn eine passende öffentliche Einstiegsseite
vorhanden ist. Keine interne Serveradresse veröffentlichen.

Das neue Signet erscheint in App, Favicon und Banner. Für die Social Preview
liegen ein 1280×640-SVG als Quelle und `static/brand/project-social.png` als Export
vor; der Browser-Smoke erzeugt die PNG aus derselben Quelle.
GitHub akzeptiert dafür PNG/JPG/GIF unter 1 MB. Das Bild kann im bestehenden
Social-Preview-Feld ersetzt werden; das Kontobild ist eine eigene Einstellung.
Es wurde kein Kontobild oder bestehendes Social-Preview-Bild verändert.

Als nächstes: zwei anonymisierte Screenshots, eine kurze Funktionsrunde,
Bug-/Featurevorlagen mit Version und Reproduktionsschritten sowie eine knappe
Beitragsanleitung. `SECURITY.md` mit wirklich betreutem Meldeweg ergänzen;
keine erfundene Kontaktadresse. Automatisches Löschen gemergter Branches ist
praktisch, Automerge nur für klar begrenzte Änderungen mit bestandenen Checks.

## Betrieb bleibt ein eigener Qualitätsbereich

SQLite-Backups einschließlich WAL-Zustand und eine echte Wiederherstellungsprobe
in einer isolierten Umgebung sind wichtiger als ein weiterer Scanner.
Produktivdaten, Tokens und private Katalog-/Sammlungsinformationen gehören nicht
in GitHub-Artefakte oder Screenshots. Ein gesicherter Netzwerkzugang und
regelmäßige getestete Updates müssen zum tatsächlichen Serverbetrieb passen.

## Quellen

- [GitHub: Sicherheitsfunktionen konfigurieren](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository)
- [GitHub: Dependency Review für Pull Requests](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-dependency-changes-in-a-pull-request)
- [GitHub: Social Preview](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)
