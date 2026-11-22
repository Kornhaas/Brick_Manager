# Projektlogbuch

Das Logbuch dokumentiert abgeschlossene Arbeitsaufträge ab seiner Einführung. Frühere Berichte bleiben unter [Historie](history/README.md); historische Ergebnisse werden nicht nachträglich erfunden. Neuere Einträge stehen oben. Datum, Ergebnis, Grund, betroffene Dokumente, ausgeführte Prüfungen und offene Grenzen festhalten. Bei reinen Detailänderungen ohne Designauswirkung dies kurz begründen.

## 2026-11-22 – PDF-Schachteletiketten für MB-1, MB-4 und Big Box umgesetzt

**Ergebnis:** Die Setliste lädt native ReportLab-PDFs für alle drei Formate.
Die vom Nutzer genannten Schachtelmaße 160 × 110 × 50, 320 × 225 × 50 und
305 × 229 × 102 mm bestimmen die Etiketten mit mindestens 5 mm Kantenabstand
und maximal 277 × 190 mm auf A4 quer. MB-1 benötigt eine Kreuzseite, MB-4 zwei
Seiten, Big Box drei. Lange und kurze Seiten erhalten unterschiedliche Breiten;
das höhere neue Format erhält 92 mm hohe Seitenetiketten. Schnittlinien,
eingebettete Schriften/Bilder und ein 100-%-Druckhinweis unterstützen den Ausdruck.
Lange Namen werden eingepasst; fehlende Bilder durch Platzhalter und Warnung erklärt.
Filter, sichtbare Fehler mit Retry und der bestehende automatische Druckstatus
nach erfolgreicher Dateierzeugung bleiben erhalten.

**Bereinigung und Architektur:** Auf ausdrücklichen Auftrag sind beide
DrawIO-Vorlagen und die XML-/Platzhalter-Ersetzung vollständig entfernt.
Der bisherige Endpunkt liefert jetzt ausschließlich `application/pdf`; Route,
Browser und Artefakttests verwenden den neuen Vertrag. Es gibt keinen
Konvertierungsprozess oder Kompatibilitätsexport. Der Setetikettendienst bleibt
HTTP-/ORM-unabhängig; Bilder werden über HTTPS zu begrenzten Kataloghosts ohne
Weiterleitungen geladen, mit Zeit-/Byte-/Pixellimits validiert und optional per
URL-Hash gecacht. PDFs werden atomar geschrieben; Schreib-/Commitfehler erhalten
den bisherigen Druckstatus durch Rollback. `pypdf` wurde nur für Entwicklungstests
gelockt; vorhandene fremde Lockfile-Aktualisierungen blieben erhalten. Generierte
Beispiel-PDFs und Renderdateien sind von Git ausgeschlossen.

**Verifikation:** Zwei PDF-Vertragstests scheiterten vor der Umstellung an
`application/xml` statt PDF und bestanden anschließend. Aktuell 56 gezielte
PDF-/HTTP-/Bild-/Dateiregressionen bestanden auf Windows und Linux. Vollständige
Linux-Suite: 698 bestanden, 0 fehlgeschlagen, 0 übersprungen, 75,45 % Coverage;
Setetikettendienst 99 % einschließlich Branches. Alle 25 Node-Tests bestanden.
Edge prüfte drei echte PDF-Downloads, Seitenzahlen 1/2/3, Bildwarnung, Fehler/Retry,
Filter und Druckstatus; die vier vorhandenen Detail-/Minifigurenabläufe bestanden
erneut. Die sechs Beispielseiten für Box 187 mit echtem Katalogbild sowie ein
Platzhalter-/Langtitelbeispiel wurden mit Poppler gerendert und visuell geprüft.
Ruff, Formatprüfung, JavaScript-Syntax und BasedPyright für die Backenddateien
bestanden. Dokumentationslinks und `git diff --check` mit CRLF-Berücksichtigung
geprüft; keine Vorlagendatei oder DrawIO-Erzeugungslogik im Laufzeitpfad verblieben.

**Dokumentation und Grenzen:** Bedienung und Maße in der
[Benutzeranleitung](guides/user-guide.md#setetiketten-herunterladen), Vertrag und
Bildgrenzen im [Softwaredesign](architecture/software-design.md#pdf-setetiketten),
außerdem Architektur, Entscheidung, Konfiguration, Testanleitung und
[Umsetzungsplan](plans/architecture-usability-improvements.md#vorschlag-schachteletiketten-direkt-als-pdf-22-november-2026)
aktualisiert. Schachtelmaße stammen aus den Nutzerangaben, nicht aus einer
physischen Messung; ein realer Probeausdruck bei 100 % steht aus. Ein PDF-Download
bestätigt keinen physischen Druck. Tests verwendeten ausschließlich isolierte
Datenbanken und temporäre Ausgaben; Beispiele wurden ohne Datenbank erzeugt.
Keine Produktionsdaten verändert, kein App-Neustart und kein Deployment.

## 2026-11-22 – Direkte PDF-Ausgabe für Schachteletiketten empfohlen

**Analyseergebnis:** Die bereitgestellte MB-4-DrawIO-Datei und die vorhandene
Etikettenerzeugung wurden lesend verglichen. Automatischer DrawIO-PDF-Export ist
per offizieller CLI möglich; für dieses Projekt wird direkte PDF-Erzeugung mit
dem bereits eingesetzten ReportLab empfohlen. Das erfordert einmaliges
Nachbilden der beiden Schachtellayouts, vermeidet danach einen zusätzlichen
Exportprozess und erlaubt explizite Druckmaße und gezielte Artefakttests.
Ein großes Deckelmotiv und vier Seitenstreifen wurden in der MB-4-XML erkannt;
reale Maße und Seitenaufteilung müssen bei Umsetzung abgeglichen werden.

**Dokumentation und Nachweise:** Abwägung, vorgeschlagener Bedienablauf,
Komponentengrenzen, additive Einführung und Prüfplan im
[Vorschlag für PDF-Schachteletiketten](plans/architecture-usability-improvements.md#vorschlag-schachteletiketten-direkt-als-pdf-22-november-2026)
festgehalten. Geprüft wurden XML, `pyproject.toml`, vorhandene ReportLab-Ausgabe,
Setetikettenroute/-dienst und die offiziellen DrawIO-/ReportLab-Dokumentationen.
Lokale Dokumentationslinks und Whitespace geprüft. Keine neuen Laufzeittests:
keine Implementierung geändert. Kein PDF erzeugt, kein visueller/physischer
Drucknachweis und kein DrawIO-Headless-Export getestet. Keine Produktionsoperation.
Vorschlag noch nicht angenommen; aktuelle Bedien-/Architekturverträge bleiben
unverändert, deshalb keine Aktualisierung ihrer Ist-Beschreibungen.

## 2026-11-22 – Erneute Etikettenfehlermeldung auf alten Laufzeitstand eingegrenzt

**Nachprüfung:** Im zugänglichen Container begann der laufende Flask-Prozess um
12:40 UTC; Route und Template der Etikettenkorrektur wurden erst um 13:03 UTC
geändert. Der Prozess verwendet daher noch den vorher importierten Python-Code.
Die gemeldete Skriptadresse `set-detail-1` gehört ebenfalls zum älteren Stand;
das aktuelle Template verwendet `set-label-2`. HTTP 304 bedeutet Browsercache,
nicht erfolgreiche Übernahme einer Backendänderung. Alle 22 isolierten
Etikettenregressionen bestanden erneut unter Linux (0 fehlgeschlagen/übersprungen).

**Betriebsgrenze:** Kein Neustart, keine Produktionsschreibprüfung und kein
Deployment vorgenommen. Der erforderliche Neustart mit der aktuellen
Produktivkonfiguration benötigt gemäß AGENTS.md einen separaten ausdrücklichen
Produktionsauftrag, weil der Start Migrationen und Jobs auslösen kann; siehe
[Produktivdatenbank](reference/configuration.md#produktivdatenbank). Keine weitere
Design-/Referenzänderung erforderlich: Diagnose des Laufzeitstands, keine neue
Implementierungsänderung. Die bereits dokumentierte und getestete Korrektur
bleibt unverändert; ihre Aktivierung im laufenden Prozess steht aus.

## 2026-11-22 – HTTP-400-Fehler bei Setetiketten behoben und abgesichert

**Ursache und Ergebnis:** Der gemeldete MB-4-Download für Box 187 suchte die
DrawIO-Vorlage relativ zum Prozessarbeitsverzeichnis statt wie Flask relativ
zum Anwendungsverzeichnis. Zwei neue Regressionen reproduzierten HTTP 400 vor
dem Fix für MB-1 und MB-4. Der neue `set_label_service.py` löst Vorlagen korrekt
auf, erzeugt gültiges XML auch bei Katalogsonderzeichen und schreibt atomar.
Die Route validiert Anfragen und rollt bei Erzeugungs-/Commitfehlern zurück.
Der bestehende automatische Druckstatus nach erfolgreicher Erzeugung bleibt
erhalten; fehlgeschlagene Ersetzungen beschädigen keine vorherige Datei.
Der Browser meldet Fortschritt, Erfolg und Fehler an der Box, erlaubt Retry
ohne Filterverlust und aktualisiert den Druckstatus ohne Neuladen.

**Verifikation:** 22 neue Regressionstests bestanden auf Windows und Linux;
vollständiger Linux-Lauf: 664 bestanden, 0 fehlgeschlagen, 0 übersprungen,
74,87 % Gesamt-Coverage. Alle 25 Node-Tests bestanden. Der neue isolierte
Edge-Browserlauf prüfte echte Downloads beider Formate, Sonderzeichen,
sichtbaren Fehler mit anschließend erfolgreichem Retry, Filter und Druckstatus.
Die vier vorhandenen Setdetail-Browserabläufe bestanden erneut einschließlich
beobachteter BFCache-Rückkehr und Minifigurenregression. Ruff, Formatprüfung,
JavaScript-Syntax und BasedPyright für Route/Etikettendienst bestanden.
Lokale Links der geänderten Dokumentation geprüft; `git diff --check` für
`brick_manager`, `tests` und `docs` ohne Fehler. Die bereits fremd geänderte
`poetry.lock` wurde nicht bearbeitet; ihr Gesamt-Diff meldet CRLF-Whitespace.

**Dokumentation und Grenzen:** [Benutzeranleitung](guides/user-guide.md),
[Softwaredesign](architecture/software-design.md#pdf-setetiketten),
[Referenzarchitektur](architecture/reference-architecture.md) und
[Testanleitung](guides/testing.md#pdf-setetiketten) aktualisiert. Ausschließlich
isolierte Testdatenbanken und temporäre Ausgaben; keine Produktivoperation und
kein Deployment. XML und Downloads wurden geprüft, kein physischer Druck oder
Öffnen in DrawIO. Nach einer erfolgreichen Dateierzeugung mit anschließendem
Commitfehler kann die Datei bestehen bleiben, der Druckstatus wird zurückgerollt.

## 2026-11-22 – Eigene Setdetailseite mit verlässlichem Speichern umgesetzt

**Ergebnis:** „View“ öffnet einen eigenen Arbeitsbereich für die physische
Setkopie mit Namen, Katalognummer und Box-ID. „Speichern“ bestätigt Mengen und
Status gemeinsam, erhält die Seite und Arbeitsposition und zeigt offene,
laufende, bestätigte oder fehlgeschlagene Änderungen. Beim Verlassen stehen
Speichern, Verwerfen und Weiterarbeiten zur Wahl. Neue Eingaben und Entwürfe
überstehen Speicherfehler; eine ältere Antwort überschreibt keine neueren Werte.

**Kontext und Minifiguren:** Die Rückkehr erhält Filter, Gruppierung, globale
Sortierung, Ergebnisseite, Seitengröße sowie Browserposition und Zeilenfokus.
Browser-Zurück lädt veraltete Ergebnisse neu; entfallene Treffer und Seiten
werden erklärt beziehungsweise korrigiert. Minifiguren-Mengenfilter und
Sammelaktionen verwenden Sollmengen statt falscher Spaltennummern. Verdeckte
Zeilen werden in der Sammelbestätigung genannt, kopieneigene nicht zugeordnete
Minifigurenteile bleiben bearbeitbar. Die neue Seite verwendet einheitlich
explizites Speichern; vorhandene JSON-, Einzelmengen- und Legacy-Schreibverträge
bleiben erhalten. Keine Schema- oder Figurenzuordnungsänderung.

**Architektur und Dokumentation:** Der Blueprint bleibt HTTP-/Transaktionsgrenze;
Inventarlesemodell und Validierung liegen in `set_maintenance_service.py`, erlaubter
Listenkontext und SQL-Sortierung in `set_navigation_service.py`. Der neue Browser-
Controller hält den Entwurf bis zur bestätigten Transaktion. Aktuelle Bedienung,
Komponenten und Grenzen sind in [Benutzeranleitung](guides/user-guide.md),
[Softwaredesign](architecture/software-design.md),
[Referenzarchitektur](architecture/reference-architecture.md),
[High-Level-Design](architecture/high-level-design.md),
[Architekturentscheidungen](architecture/decisions.md) und dem
[Analyse-/Umsetzungsplan](plans/architecture-usability-improvements.md) gepflegt.

**Verifikation:** Zwei neue Routenregressionen scheiterten zunächst auf dem
archivierten Ausgangsstand (GET/POST 404) und bestanden nach der Umsetzung.
31 neue Detailprüfungen; vollständige Linux-Suite 642 bestanden, 0 fehlgeschlagen,
0 übersprungen, 74,46 % Coverage. Alle 25 Node-Prüfungen bestanden. Vier
umfangreiche Edge-Abläufe bestanden einschließlich echter beobachteter BFCache-
Rückkehr, Filter-/Seite-2-Kontext, wiederholtem Save, falschen Eingaben,
Netzwerkfehler mit Tastatur-Retry, Suche-Enter ohne Speichern, Sammelvorschau und
Entwurfsentscheidungen. Zusätzlicher Check verlorener Bestätigungsantworten
bestanden. Der Ladecheck für 3 versus 203 Inventarzeilen verwendete jeweils
6 SELECTs. Ruff/Format und BasedPyright für die Backenddateien bestanden.
Desktop-/390-Pixel-Ansicht geprüft; kein Dokumentüberlauf bei 390 Pixeln auch mit
der tatsächlichen Bootstrap-CSS.

**Grenzen:** Keine Produktivdaten für Schreibprüfungen verwendet, keine
Produktiv-App gestartet und kein Rollout. Keine echte Safari-/iPad- oder
Screenreader-Abnahme. Paralleländerungen unabhängiger Browser bleiben beim
bisherigen Last-Writer-Verhalten. Der alte Lagerort-Textdialog wird auf der
neuen Seite nicht angeboten; die Lagerverwaltung ist dafür der Einstieg.

## 2026-11-22 – Usability- und UX-Analyse der Setpflege

**Ergebnis:** Die Analyse bestätigt den gemeldeten Verlust von Filter- und
Arbeitskontext nach „Save Changes“. Zwei unabhängige Rollenreviews und ein
isolierter Edge-Ablauf verglichen Inline-Ansicht, eigene Detailseite,
Master-Detail und Modal. Empfohlen ist eine eigene Arbeitsseite pro physischer
Setkopie mit getrennten Aktionen für Speichern und Rückkehr, sichtbarer
Boxidentität und einer gemeinsamen verlässlichen Speicheranzeige.
Weitere Befunde betreffen Minifiguren-Sammelaktionen/Fehlteilefilter,
Fehler-/Entwurfserhalt, veraltete Listenwerte, globale Sortierung,
Lagerortvorbelegung, Tastatur und schmale Bildschirme. Prioritäten,
Kontraktgrenzen und Abnahmeszenarien stehen im
[Setpflege-Vorschlag](plans/architecture-usability-improvements.md#vorschlag-setpflege-als-eigener-arbeitsbereich-22-november-2026),
der im Dokumentationsindex verlinkt ist.

**Nachweis:** 24 bestehende Node-Prüfungen bestanden. Der temporäre Browserlauf
nutzte die gemeinsame Test-App, In-memory-SQLite und 26 synthetische Kopien.
Er reproduzierte den nackten Listenredirect bei Erfolg und Validierungsfehler,
bestätigte gespeicherte Mengen/Status, den unterschiedlichen internen Rückweg,
die fehlende Detailadresse und Minifigurenprobleme. Bei 390 Pixel Bildschirmbreite
wurden 650 Pixel Dokumentbreite gemessen. Der erfolgreiche Lauf hatte keine
JavaScript-Fehler. Keine Produktivdaten verändert oder Produktiv-App gestartet.

**Grenzen:** Vorschlag, keine Implementierung und kein Deployment. Keine echten
Nutzertests, Screenreader-/iPad-Abnahme oder Live-Leistungsmessung. Aktuelle
Benutzeranleitung, Softwaredesign und Architekturentscheidungen bleiben beim
umgesetzten Iststand; ein angenommener Entwurf wird erst mit dessen Umsetzung
in diese Referenzen übernommen.

## 2026-11-21 – Filter der Setpflege auf dem laufenden Server überprüft

**Ergebnis:** Ein unabhängiger Testagent reproduzierte das Verhalten des
GET-Filterformulars in einem isolierten Edge-Lauf und auf dem vom Nutzer
genannten laufenden Server. Dreamzzz ergab 38 Treffer; Auswahl von „Sealed“
allein änderte weder URL noch Tabelle. Nach „Apply filters“ blieben 8 versiegelte
Sets, mit einer passenden Box-ID und erneutem Absenden genau 1. Nicht vorhandene
Boxen lieferten 0 Treffer. Status und Boxnummer werden mit dem Thema kombiniert.
Die Übersichtskarten bleiben bewusst sammlungsweit und sind kein Filterzähler.

**Ursache und Nachweis:** `set_maintenance.js` überspringt beim aktuellen
Filterformular die alte Sofortfilterung; Änderungen werden erst mit dem
GET-Formular abgeschickt. 24 isolierte Browsernavigationen prüften Suchtext,
Boxnummer, Thema, alle sieben Statuswerte, Inventar, Etiketten und Gruppierung.
Zusätzlich bestanden 9 fokussierte UI-Vertragstests, 18 wurden abgewählt.
Die Live-Browserprüfung verwendete ausschließlich lesende GET-Anfragen.
Keine Filterlogik verändert, da dieser Auftrag eine genaue Überprüfung verlangt.
Keine weitere Referenzänderung: Das bestehende Absendeverhalten bleibt erhalten.

## 2026-11-21 – Integrationsstand für main und Docker freigegeben

**Umfang:** Der Nutzer beauftragt die Übernahme aller vorhandenen Änderungen
nach `main` und die Überwachung des dadurch ausgelösten Docker-Workflows.
Der Integrationsstand enthält die Sammlungsstabilisierung, getrennte
Lagerarbeitsseiten, Kategorienamen und Fehlerzustände, zusätzliche Boxetiketten,
Browserregressionen sowie die vorhandenen SQLite-Editor-Empfehlungen und den
aktualisierten Dependency-Lock. Die jeweiligen Fachänderungen sind in den
vorherigen Einträgen und der [Lageranleitung](guides/warehouse.md) beschrieben.

**Lokale Freigabeprüfung:** Vollständiger Windows-Lauf mit UTF-8: 611 Tests,
609 bestanden, 2 fehlgeschlagen, 0 übersprungen; Gesamt-Coverage 73,25 %.
Die beiden Fehler betreffen fehlende Windows-Symlinkrechte und den unter
Windows unzugänglichen Linux-Interpreter der vorhandenen `.venv`.
Poetry-Lock-Prüfung und sämtliche anwendbaren Pre-Commit-Prüfungen bestanden.
Für Python wurde der bereits dokumentierte externe Prüfinterpreter verwendet.
Eine leere temporäre Git-Konfigurationsvariable musste nur im Prüfprozess
neutralisiert werden; die Repository-Konfiguration blieb unverändert.

**Linux-Nachweis:** Anschließend dieselbe vollständige Suite mit Python 3.12.16
und den exakt gelockten Abhängigkeiten in einer separaten virtuellen Umgebung
im Linux-Container ausgeführt: 611 bestanden, 0 fehlgeschlagen, 0 übersprungen,
73,22 % Gesamt-Coverage. Die beiden Windowsfehler sind dort nicht vorhanden.
Die Testdatenbanken bleiben durch die gemeinsamen Fixtures temporär isoliert.

**Veröffentlichungsgrenze:** Der Workflow baut nach bestandenen Linux-Tests
`kornhaas/bricks_manager` für AMD64 und ARM64, veröffentlicht die Branch-/Latest-Tags
und prüft den Containerstart samt Health-Endpunkt. Der Job „Deploy“ erzeugt nur
einen Hinweis; ein automatischer Neustart des Produktivservers ist nicht
konfiguriert. Der neue Workflowlauf ist bei Erstellung dieses Eintrags noch
nicht abgeschlossen; sein Ergebnis wird im zugehörigen Chat nachverfolgt.
Keine Produktivmigration oder Produktivdatenänderung ist Teil dieses Auftrags.

## 2026-11-21 – Alte Serverantwort nicht mehr als leeren Katalog anzeigen

**Ergebnis:** Die Kategorieauswahl unterscheidet eine ausdrücklich leere
Kategorienliste von einem fehlenden Antwortfeld. Bei älterem Servercode zeigt
sie einen Lade-/Aktualisierungshinweis, sperrt das Speichern und fordert keinen
Neuimport. Nach vollständiger Antwort ist die Auswahl wieder nutzbar. Bei
fehlender Namensinformation behauptet auch die Regelübersicht nicht mehr,
die Kategorie sei aus dem Katalog entfernt worden.

**Verifikation:** Der isolierte Edge-Browserlauf bestand elf Abläufe ohne
JavaScript-Fehler. Neu geprüft wurden fehlende und leere Kategorienantworten,
die jeweils passende Meldung, gesperrtes Speichern und Wiederherstellung nach
erneutem Laden der vollständigen Antwort. Ruff und JavaScript-Syntax geprüft;
die Änderungen an [Lageranleitung](guides/warehouse.md) und
[Softwaredesign](architecture/software-design.md) beschreiben diese Unterscheidung.
Kein Import, kein Serverneustart und kein Zugriff mit Schreibrechten auf die
Produktivsammlung. Die laufende Anwendung muss für die Namensauswahl weiterhin
den bereits implementierten aktuellen Python-Code laden.

## 2026-11-21 – Fehlende Kategorieauswahl im laufenden Server eingegrenzt

**Diagnose:** Die verfügbare Produktivdatenbank enthält 76 Kategorien mit Namen
(`rebrickable_part_categories`). Die laufende, über den lokalen Port 5000
erreichbare Anwendung liefert bei `GET /warehouse/settings` dagegen noch kein
`categories`-Feld. Der aktuelle Quellcode liefert dieses Feld bereits. Damit
verwendet die neue Oberfläche eine ältere Serverantwort und deutet das fehlende
Feld irreführend als leeren Katalog. Ein erneuter Katalogimport ist nicht nötig;
der laufende Server muss den aktualisierten Python-Code laden.

**Nachweis und Grenzen:** SQLite ausschließlich mit `mode=ro` und
`PRAGMA query_only=ON` gelesen; Anzahl und Namensbeispiele mit einer lesenden
HTTP-Antwort sowie dem vorhandenen Quellcode verglichen. Kein Import, kein
Anwendungsneustart und keine Datenänderung ausgeführt. Keine neuen Tests oder
Referenzänderungen, da dieser Auftrag die Laufzeitabweichung diagnostiziert
und kein neues Verhalten implementiert.

## 2026-11-21 – Kategorienamen in Lagerregeln statt ID-Eingabe

**Ergebnis und Grund:** Kategorieziele verwenden eine alphabetische Auswahl
der importierten Kategorienamen statt eines Zahlenfelds. Auch gespeicherte
Zuordnungen zeigen den Namen, damit keine internen IDs bekannt sein müssen.
Ohne Kategorien erklärt ein Hinweis den fehlenden Teilekatalog und sperrt
das Speichern. Der vorhandene numerische Schreibvertrag und gespeicherte
Zuordnungen bleiben unverändert; die Einstellungen liefern lediglich zusätzliche
Katalog- und Namensfelder. Details in [Lageranleitung](guides/warehouse.md)
und [Softwaredesign](architecture/software-design.md).

**Verifikation:** 32 fokussierte Pythonprüfungen bestanden, darunter zwei neue
Regressionen für Kategorienamen, leeren Katalog, numerisches Speichern und
unbekannte Kategorien. Der isolierte Edge-Browserlauf bestand zehn Abläufe,
einschließlich Auswahl nach sichtbarem Namen, Speichern und Anzeige der Regel.
Ruff-Lint, Python-Format und JavaScript-Syntax geprüft. Keine Produktivdaten
verwendet. Kein vollständiger Suite-Lauf für diese begrenzte UI-/Antwortergänzung;
die zuvor dokumentierten Umgebungsgrenzen gelten weiterhin.

## 2026-11-21 – Lagerverwaltung nach Aufgaben aufgeteilt

**Ergebnis:** Die bisherige Sammelseite wurde in Übersicht, Einlagern,
Aufräumen, Boxgrößen, Regale/Fächer, Bestandserfassung und Regeln aufgeteilt.
Die Übersicht konzentriert sich auf Fach, Boxen, Inhalte und Etiketten.
Bestätigte Boxkarten zeigen bis zu drei Inhaltsvarianten direkt als Vorschau.
Eigene Konfigurationsseiten zeigen vorhandene Größen und Lagerorte mit
Bearbeitungsaktionen. Fachlabels lassen sich gezielt auswählen und als
zuschneidbare Papierkarten drucken. Gleichmäßige Fachhöhen erhalten ein einfaches
Eingabefeld; abweichende Messprofile bleiben als erweiterte Option verfügbar.
Bewegungen zeigen nur passende Pflichtfelder. Alte Zuordnungen öffnen die
Bestandserfassung mit Inhalts-ID; Details und Fachkontext bleiben erreichbar.

**Grund und Architektur:** Ein unabhängiger UX-Rollenreview bestätigte die
Überladung durch gleichzeitig angebotene Aufgaben. Die Umsetzung erhält den
Warehouse-Blueprint, Services und JSON-Verträge und rendert je URL nur die
zugehörigen Formulare. Formularbindung und zusätzliche Datenabfragen richten
sich nach der aktuellen Seite. Ein separater Testagent prüfte die Integration.
Kein Datenmodell, keine Migration und keine Produktivdaten wurden verändert.
Dokumentiert in [Lageranleitung](guides/warehouse.md),
[Benutzeranleitung](guides/user-guide.md), [Softwaredesign](architecture/software-design.md),
[Referenzarchitektur](architecture/reference-architecture.md),
[High-Level-Design](architecture/high-level-design.md) und
[Architekturentscheidungen](architecture/decisions.md).

**Verifikation:** 105 fokussierte Seiten-, Routen-, Altzuordnungs- und
Etikettenprüfungen sowie 52 Struktur-/Bewegungs-/Vorschlagsprüfungen bestanden.
16 neue Seitenprüfungen sichern Aufgabentrennung, Navigation, eindeutige IDs,
Sitzungstoken und deaktivierte Einstiege. Alle 25 bestehenden Node-Tests
bestanden. Python-Lint und Formatprüfung der geänderten Routen-/Testdateien
sowie JavaScript-Syntax sind erfolgreich.
Der volle Lauf sammelte 609 Tests: 606 bestanden, 3 fehlgeschlagen,
0 übersprungen; Coverage 73,22 %. Die Fehler betreffen fehlende Windows-Rechte
für Symlinks, das Lesen einer UTF-8-Workflowdatei als cp1252 und einen unter
Windows unzugänglichen Linux-Interpreter in der vorhandenen `.venv`.
Der Workflowtest bestand im separaten Nachlauf mit `PYTHONUTF8=1`.
Poetry lief mit deaktivierter lokaler Venv-Auswahl im vorhandenen Python 3.13;
die beschädigte lokale `.venv` wurde nicht repariert. BasedPyright ist in
diesem Prüfinterpreter nicht verfügbar.

**Grenzen:** Automatisierte Browserprüfungen verwenden ausschließlich die
isolierte Testanwendung und temporäre Daten. Quelltextreview und Browserprüfung
ersetzen keinen Nutzertest mit der realen Sammlung und keinen Papier-Probedruck.
Der neue Edge-Browserlauf bestand neun Abläufe, einschließlich echter
Einlagerung von sieben Test-Bricks über Entwurf, Reservierung und physische
Bestätigung, Formularrücksetzung, gezieltem Fachlabeldruck und fachübergreifenden
Boxlinks. Die drei bisherigen Lager-Browserläufe bestanden ebenfalls
(acht Lagerabläufe, Altzuordnungen und Etiketten einschließlich Fehlerpfaden).
Desktop und 390-Pixel-Ansicht wurden zusätzlich visuell geprüft.
Lokale Dateilinks der geänderten Markdown-Dokumente sind geprüft.

## 2026-11-20 – Kompaktes Boxetikettenformat ergänzt

**Ergebnis:** Die Etikettenauswahl unterstützt zusätzlich Avery Zweckform 3657
mit 40 Etiketten pro A4-Bogen (4 × 10, 48,5 × 25,4 mm). Bogenraster,
Startposition, freie-Platz-Anzeige, Kalibrierlinien, Dateinamen sowie der Druck
vorgemerkter Etiketten verwenden das ausgewählte Format. Das kompakte Layout
zeigt Boxnummer, ein Bild des ersten Inhalts, dessen Teilenummer und eine
Zusammenfassung weiterer Inhalte. Avery 3474 bleibt unverändert vorausgewählt.

**Grund und Nachweis:** Kleine Behälter benötigen ein zweites, kleineres
Etikettenformat. Die Herstellerseite für [Avery Zweckform 3657](https://www.avery-zweckform.com/produkt/universal-etiketten-3657)
bestätigt Maße und 40 Etiketten pro Bogen. Ergänzte Service- und Routentests
prüfen PDF-Erzeugung, das 4-×-10-Raster, Position 40 und das Bild des ersten
Inhalts. 76 fokussierte Service-, Routen- und Vormerkungstests bestanden mit dem vorhandenen
Systeminterpreter; Python-/JavaScript-Syntax, Ruff und Diff-Whitespace sind
ebenfalls geprüft. Poetry konnte die vorhandene, gesperrte `.venv` nicht
reparieren. Kein Datenmodell, keine Migration und keine Produktivdaten sind
betroffen.

**Oberfläche:** Der Bereich für vorgemerkte Neudrucke und der Etikettendruck
teilen jetzt eine zentrierte Arbeitsfläche und gleichartige Karten. Sichtbare
Beschriftungen und Rückmeldungen des Etikettendrucks sind auf Deutsch
vereinheitlicht; die Tabelle bleibt bei Bedarf scrollbar.

## 2026-11-15 – Erste testgetriebene Architektur-/Usability-Welle

**Auftrag und Review:** Projektweite Sichtung anhand des sauberen Stands `ac40f74` aus Architektur-, Nutzer- und Usability-Perspektive. Zwei unabhängige Rollenreviews lieferten Quellcodebefunde und gezielte Nachweise; der koordinierende Agent integrierte Umsetzung und Dokumentation. Priorisierung und noch offene Altlasten stehen im [Verbesserungsplan](plans/architecture-usability-improvements.md). Die Sichtung ist kein vollständiger Sicherheits-/Nutzertest und keine Behauptung, sämtliche Altlasten beseitigt zu haben.

**Umgesetzt:** (1) Geplante Backups nutzen konsistente SQLite-Snapshots statt Dateikopie, die tatsächliche Engine-Quelle, kollisionsfreie Namen und gezielte Rotation. (2) Dashboard-Mengen verwenden Typ und ID, lösen Batches vor Mutation vollständig auf und bestätigen tatsächliche Werte. Eindeutige Altpayloads bleiben gültig; mehrdeutige, fehlende oder doppelte Ziele verändern keine Teilbestände. Einzeländerungen runden keine Dezimalwerte still ab und weisen unbekannte Typen zurück. (3) Setpflege und Dashboard speichern serialisiert, erhalten neueste Eingaben und zeigen bleibende Fehler/Retry. Formularabschluss wartet auf ausstehende Änderungen und kann nach Setwechsel kein anderes Formular absenden. Der alte Dashboard-Inline-Autosave wurde entfernt. (4) Setlisten berechnen skalare Seitensummen statt sämtliche Inventarobjekte zu laden; Themenfilter und Zeilenthema sind getrennt. (5) Minifiguren-/Teiltexte werden als Text escaped und RGB-Werte validiert. (6) Der auskommentierte Pytest-Aufruf im Docker-Vorjob ist wieder aktiv und sperrt Veröffentlichung bei Testfehlern.

**TDD-Nachweise:** 13 Parent-Regressionen zuerst rot; sechs zusätzliche Fehler bei Einzelwerten reproduziert. Das Backup-Review belegte WAL-Verlust, falsche relative Quelldatei und Löschung fremder Sicherungen vor der Korrektur; anschließend 13 Backupfälle grün. Die neuen JavaScript-Tests reproduzierten Mengenrennen und Markup-Interpretation vor deren Korrektur. Der CI-Vertragstest scheiterte vor Aktivierung des Testschritts. Integriert 70 fokussierte Pythonprüfungen vor dem abschließenden Gate-Test bestanden.

**Abschlussprüfung:** Nach allen Änderungen **589 Python-Tests bestanden, keine Fehler/Skips, 73,06 % Coverage**. 25 Node-Prüfungen bestanden, darunter vorhandene Tastaturnavigation, 13 Set-Speicherfälle, drei Renderingfälle und der Dashboard-Harness. Gezielter echter Dashboard-Browserlauf mit temporärer Datenbank bestätigt kollidierende IDs, verzögerte Writes, Fehler/Retry, Dezimalprüfung, Clamping und unveränderten anderen Bestand. Zwei unabhängige isolierte Chromiumprüfungen bestätigten Setmengen-/Bulkabschluss und wörtliche Katalogdarstellung. Externe Requests bzw. unveränderte DataTables-Initialisierung wurden ausdrücklich gestubbt. Ruff projektweit, Formatprüfung (108 Dateien), BasedPyright ohne Fehler/Warnungen, JS-Syntax, lokale Dokumentverweise und Diff-Whitespace erfolgreich. Wheel und Quellpaket erfolgreich aus isoliertem Quellbaum gebaut und ohne Datenbank-/`.env`-Dateien geprüft.

**Messung und Dokumentation:** Synthetischer isolierter Setlistenfall mit 30 Sets/6.000 Teilezeilen: 6.000 auf 0 geladene Teileobjekte, 10 auf 9 Queries, ein Vergleichslauf 0,1891 auf 0,0979 Sekunden. Keine Live-Messung und keine garantierte Zeitgrenze. Architektur, Entscheidungen, High-Level-Design, Softwaredesign, Benutzer-/Testanleitung und Backup-Konfiguration aktualisiert. Kein Datenmodell oder Migrationsartefakt geändert; eine neue Schemamigration ist nicht erforderlich.

**Grenzen und Arbeitsstand:** Erste Welle lokal auf `refactor/collection-stability` zur Prüfung zusammengefasst; nicht nach `main` übernommen oder veröffentlicht. Keine Live-Datenbank geöffnet, kein bestehender Server gestartet/neu gestartet, keine Synchronisation und keine Remote-Pipeline ausgelöst. Unabhängige gleichzeitige Browseränderungen sind weiterhin ohne datenbankgestützte Versionsprüfung; weitere asynchrone Navigationsrennen, langsame Detail-/Lagerpfade, Queue-Isolation und explizitere Initialisierung bleiben priorisiert im Plan. Reale Nutzerbeobachtung, Produktions-Rollout und aktueller Remote-Containerbuild benötigen einen eigenen Schritt.

## 2026-11-15 – Push freigegeben und GitHub-Builds erfolgreich geprüft

**Freigabe und Ergebnis:** Der Nutzer hat Push und anschließende Buildprüfung einschließlich Docker-Image-Veröffentlichung ausdrücklich bestätigt. `main` mit Commit `c6b4b0e` wurde ohne Force-Push übertragen. Der reguläre Pre-push-Hook bestand erneut **554 Tests**, ohne Fehler/Skips, mit **72,24 % Coverage**. Keine Hook-Umgehung.

**GitHub-Nachweise:** [Python-Tests](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852911), [Pylint-Workflow](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852642), [Codacy](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852831) und [Docker-Workflow](https://github.com/Kornhaas/Brick_Manager/actions/runs/43744852562) erfolgreich abgeschlossen. Docker-Jobs für Build/Push, anschließenden Containerstart mit Healthcheck und Trivy-Scan sind erfolgreich. Der Job namens „Deploy“ gibt ausschließlich eine Bereitstellungsinformation aus; der Workflow enthält keinen aktiven Server-Deployment-Schritt. Auch die automatisch gestarteten Dependabot-Läufe waren erfolgreich.

**Veröffentlichtes Artefakt:** Multiarch-Image für `linux/amd64` und `linux/arm64` unter `kornhaas/bricks_manager:main` und `:latest`, Manifest-Digest `sha256:2551531470ef5087dc7a84090d6dd16bf9c25e32e53271180565a228f41bd8e4`. Nachgewiesen durch erfolgreiche Buildjobs und deren Publikationslogs, nicht durch einen lokalen Dockerbuild. Der Healthcheck läuft im frischen GitHub-Testcontainer; es wurden keine Live-Daten eingebunden. Lokale Live-Daten und lokaler bzw. entfernter Anwendungsserver wurden nicht verändert.

**Einordnung:** Pylint ist im bestehenden Workflow nicht blockierend; ein grüner Lauf bedeutet nicht, dass sämtliche Pylint-Hinweise behoben wurden. Ein erfolgreicher Scan ist kein vollständiger Sicherheitsaudit. Keine Änderung an Anwendungscode oder Workflow für diese Prüfung erforderlich. Testanleitung und Logbuch enthalten die Nachweise.

## 2026-11-15 – Lokale Builds des zusammengeführten Commits geprüft

**Ergebnis:** `poetry check --lock` für `4c8bcea` erfolgreich. Wheel und Quellpaket aus einem sauberen Git-Archiv gebaut; 99 Pythondateien im Wheel kompilieren. Original-Lagermigration und neuer Bildindex sind bytegleich enthalten. README und neue Migration sind im Quellpaket vorhanden; beide Archive enthalten keine Datenbank oder `.env`. Der langsame erste Workspace-Build wurde beendet und durch den erfolgreichen isolierten Build ersetzt. Testanleitung ergänzt und lokale Dokumentverweise geprüft.

**Grenzen und nächster Schritt:** Kein lokales Docker-/Podman-/BuildKit-Werkzeug vorhanden. GitHub bestätigt null Workflow-Läufe für den neuen Commit; der entfernte `main` steht weiterhin auf `845921b`, dessen vorhandene Läufe erfolgreich sind. Das bestätigt noch nicht den neuen Stand. Ein Push würde auch das Docker-Image veröffentlichen und ist für diese Prüfung noch nicht freigegeben. Keine Live-Datenbank geöffnet, keine Anwendung gestartet und kein Server verändert. Die vorherigen 554 erfolgreichen Tests wurden für die reine Paketprüfung nicht wiederholt.

## 2026-11-15 – Lagerverbesserungen für lokale Übernahme nach main zusammengefasst

**Auftrag und Stand:** Alle offenen Projektänderungen auf `feat/warehouse-overview-reprints` zusammengefasst: vorhandene Lagerinhalte, Teilevorschauen in Karten/Details, Spaltennummerierung, dauerhafte Etikettenvormerkungen mit Sammeldruck, fachweise Datenabfrage und Bildindex sowie Startauswahl/Cachekorrektur. Zugehörige Regressionen, Betriebsgrenzen für Live-Daten und zentrale Dokumentation gehören zum selben Commit. Ziel ist die vom Nutzer beauftragte lokale Fast-forward-Übernahme nach `main`; kein Push oder Deployment.

**Abschlussprüfung:** Vollständige Suite erneut auf isolierten temporären Datenbanken ausgeführt: **554 bestanden, 0 fehlgeschlagen, 0 übersprungen, 72,24 % Coverage**. Projektweites BasedPyright ohne Fehler/Warnungen, JavaScript-Syntax beider betroffener Dateien und alle anwendbaren Pre-commit-Hooks erfolgreich. Geprüfte Dateiliste enthält keine Datenbank oder `.env`; die bereits angewendete Originalmigration ist unverändert. Lokale Dokumentverweise und Diff-Whitespace geprüft. Keine Live-Datenbank geöffnet, keine Migration ausgeführt und keinen lokalen oder entfernten Server gestartet/neu gestartet. Die vorher dokumentierten Browser-/Build-Nachweise bleiben gültig und wurden für den Git-Vorgang nicht erneut ausgeführt.

## 2026-11-15 – Serverstandort und Live-Daten getrennt

**Präzisierung durch den Nutzer:** Der eigentliche Server läuft anderswo. Hier sind die Live-Daten verfügbar; die hier gestarteten lokalen Flask-Prozesse sind nicht mit diesem Server gleichzusetzen. Die vorherige Dokumentation zur Produktionszuordnung ist in diesem Sinn zu lesen. Repository-Anweisungen und Konfigurationsreferenz entsprechend präzisiert. Der Schutz der Daten gilt unabhängig vom Standort des ausführenden Prozesses.

**Prüfung:** Nur Dokumentation geändert, Diff-Whitespace geprüft. Keine Datenbank geöffnet und keinen lokalen oder entfernten Server verändert. Kein Anwendungstest für diese textliche Präzisierung erforderlich.

## 2026-11-15 – Produktionszuordnung der echten Sammlung klargestellt

**Korrektur:** Der Nutzer bestätigt ausdrücklich, dass `data/instance/brick_manager.db` (Alias `/app/data/instance/brick_manager.db`) die Produktivdatenbank ist. Die bisherigen Einträge und Meldungen, die diese Datei als Entwicklungsdatenbank bezeichneten, enthalten eine falsche Umgebungszuordnung. Sie bleiben als historische Aufzeichnung erhalten und sind keine Freigabe für weitere Produktionsoperationen.

**Bereits erfolgt:** Die physische Lagermigration und später die Inventarbild-Indexmigration wurden bereits auf dieser Datei ausgeführt; außerdem wurde die Anwendung mehrfach dagegen neu gestartet. Beim letzten Indexschritt wurden Sicherung und Testkopie erstellt und nach Anwendung unveränderte Tabellenzeilenzahlen und Fingerabdrücke der sammlungseigenen Daten sowie erhaltene ursprüngliche Journalzeilen und Fremdschlüssellücken bestätigt. Das ändert die falsche Einstufung nicht.

**Verbindliche Grenze:** Produktionspfad und gesonderte Auftragsanforderung für Migrationen, Schreiben und Anwendungsstarts/-neustarts in `AGENTS.md` und Konfigurationsreferenz festgehalten. Weitere Tests ausschließlich mit temporären Datenbanken oder wegwerfbaren Kopien. Nur Dokumentation geändert; keine Datenbank geöffnet, kein Server verändert und keine Migration ausgeführt. Lokalen Dokumentverweis und Diff-Whitespace geprüft; keine Anwendungstests für diese Dokumentationskorrektur erforderlich.

## 2026-11-15 – Startwert der Fachauswahl und Scriptcache korrigiert

**Ursache und Ergebnis:** Das anfängliche HTML enthielt weiterhin „Alle Fächer“, bevor die asynchrone Fachauswahl gesetzt wurde. Es zeigt jetzt zunächst die deaktivierte Auswahl „Fach wird geladen …“, danach das letzte bzw. erste vorhandene Fach. Ohne Fächer erscheint „Noch kein Fach erfasst“. Die Script-URL enthält die tatsächliche Dateiänderungszeit als Versionskennung, damit ältere gecachte Fassungen nicht weiterverwendet werden. Lageranleitung aktualisiert; kein Schema-/Datenwechsel.

**Prüfung:** 27 Warehouse-Vertragstests bestanden, darunter ein neuer Test des anfänglichen HTML und der versionierten Script-URL. Der erweiterte isolierte Browserlauf hält die Startdatenantwort bewusst zurück und bestätigt den Ladeplatzhalter ohne „Alle Fächer“; danach bestehende Tests für Einzelfachstart, gespeicherte Auswahl, ungültige ID, manuelle Gesamtansicht und Zuordnung bestanden. Ruff, Formatprüfung, JavaScript-Syntax, statische Analyse, Dokumentverweise und Diff-Whitespace geprüft. Keine erneute vollständige Python-Suite für diese begrenzte HTML-/Cachekorrektur ausgeführt; letzter Gesamtlauf bleibt 553 bestanden. Entwicklungsserver mit derselben Sammlungsdatei neu gestartet. Lesende Live-Prüfung bestätigt den HTML-Ladeplatzhalter, die versionierte Script-URL und nach Laden konkret „Aktiv / Regal 1 / Fach 1“ statt Gesamtansicht.

## 2026-11-15 – Datenabfrage und Bildsuche der Lagerübersicht beschleunigt

**Messbare Ursache:** Die vollständige Datenantwort benötigte im Nutzerbrowser etwa 18 Sekunden und 3 MB. Lesendes Profiling derselben Entwicklungsdatenbank ergab 14,078 Sekunden, davon 13,532 Sekunden in der Inventarbild-SQL-Abfrage. Ein passender Lookup-Index fehlte; die bisherige Fachauswahl begrenzte lediglich den DOM-Aufbau.

**Umsetzung:** Additiver Covering Index `ix_inventory_part_color_image` über Teil/Farbe/Bild-URL, in Modell und neuer unveränderlicher SQL-Migration. Der Browser verwendet einen fachweisen Startvertrag; Altinhalte anderer Fächer werden nicht katalogangereichert oder übertragen. Globale Zähler und ungeklärte Gruppen bleiben sichtbar, deren Inhalte werden erst beim Öffnen geladen. Die globale Inhaltsauswahl für Bearbeitung wird erst bei Bedarf geladen. Bestätigte Einheiten bleiben für Navigation/Bewegung verfügbar. Gesamtansicht und bisheriger vollständiger Datenvertrag sind weiterhin explizit nutzbar. Antwortgenerationen verhindern überholte Fachwechselantworten; Archivaktionen warten auf den abgeschlossenen Fachwechsel.

**Sicherung und vorhandene Daten:** Vorher konsistente Sicherung `data/instance/backups/brick_manager-before-image-index-1794759517681739236.db`. Migration samt Wiederholung auf einer lokalen Kopie geprüft: sämtliche Tabellenzeilenzahlen, Fingerabdrücke der sammlungseigenen Tabellen, ursprüngliche Journalzeilen und bestehende 127 Fremdschlüssellücken unverändert. Danach ausschließlich den Index in die freigegebene Entwicklungsdatenbank übernommen und dieselben Vergleiche gegen deren unmittelbaren Vorzustand erfolgreich wiederholt. Die Original-Lagermigration behält ihre SHA-256-Prüfsumme; das Journal enthält jetzt drei Artefakte. Keine Bestandsbereinigung, kein Reset und keine Produktionsänderung. Der Covering Index belegt zusätzlichen Speicher und wird bei Inventaränderungen mitgepflegt.

**Prüfung:** 19 gezielte Migrations-/Übersichtstests bestanden. Abschließender Gesamtlauf nach Anpassung der beiden erwarteten Migrationszahlen: **553 bestanden, 0 fehlgeschlagen, 0 übersprungen, 72,24 % Coverage**. Alle drei isolierten Browserabläufe erfolgreich; voller Warehouse-Lauf nach Absicherung des Fachwechsels und Legacy-Lauf nach abschließender Oberflächenkorrektur erneut bestanden. Projektweites Ruff, Formatprüfung von Anwendung/Tests (101 Dateien), BasedPyright ohne Fehler/Warnungen, JavaScript-Syntax und Diff-Whitespace erfolgreich. Wheel gebaut und neue Migration im Artefakt nachgewiesen. Softwaredesign, Schemareferenz, Lageranleitung, Testanleitung und Abnahmenachweis aktualisiert; lokale Dateiverweise geprüft.

**Messung und Grenzen:** Auf der lokalen Datenbankkopie benötigt die fachweise Aufbereitung einschließlich JSON 0,064 Sekunden und 243.129 Byte statt 3.239.918 Byte der Gesamtansicht. Nach Neustart des echten Entwicklungsservers lieferte die fachweise HTTP-Antwort 222.120 Byte: erster Aufruf 0,635 Sekunden, zwei Folgeaufrufe 0,349 bzw. 0,379 Sekunden, bei weiterhin 2.935 globalen Inhaltszeilen. Die niedrigere Bytezahl ist die kompakte Flask-HTTP-Serialisierung. Die ausdrücklich angeforderte Gesamtantwort blieb auf dem eingebundenen Dateisystem mit 17,361 Sekunden und 2.981.187 Byte langsam; sie ist kein Startpfad mehr. Der rein lesende echte Browserlauf bestätigt fachweisen Start, keine vorgezogene Gesamt-Inhaltsabfrage, Fachwechsel, Wiederherstellung der Auswahl und keine JavaScript-Fehler. Dateisystem, Cache und Netzwerk beeinflussen die Werte; die Vor-Ort-Prüfungen bleiben unverändert.

## 2026-11-15 – Mit zuletzt gewähltem Fach starten

**Ergebnis:** Die Lageransicht startet mit dem zuletzt im Browser gewählten einzelnen Fach, sonst mit dem ersten numerisch sortierten Fach. Gelöschte IDs fallen auf das erste Fach zurück; gesperrter Browserspeicher verhindert die Nutzung nicht. „Alle Fächer“ bleibt manuell verfügbar und wird beim nächsten Besuch nicht automatisch wieder geöffnet. Nur Karten des Startfachs werden aufgebaut; die bestehende vollständige Datenabfrage bleibt bestehen. Keine Änderung an Sammlungsdaten oder Serverkonfiguration. Lageranleitung und Softwaredesign aktualisiert.

**Prüfung:** Erweiterter isolierter Legacy-Browserlauf bestätigt Einzelfach als Standard, Wiederherstellung nach Neuladen, ungültige gespeicherte ID und weiterhin nutzbare Gesamtansicht. Bestehender vollständiger Warehouse-Browserlauf ebenfalls bestanden, ohne JavaScript-Fehler. JavaScript-Syntax, Ruff/Formatprüfung des Browsertests, Dokumentverweise und Diff-Whitespace geprüft. Keine erneute vollständige Python-Suite für die reine Browserdarstellung ausgeführt. Zusätzlich rein lesend am laufenden Server bestätigt: ein Startfach mit zunächst 24 Karten, Auswahl eines anderen Fachs nach Neuladen wiederhergestellt. Die anfängliche Datenabfrage und das Laden externer Bilder können weiterhin Zeit benötigen.

## 2026-11-15 – Teilebilder in Behälterdetails

**Ergebnis:** Auch die Inhaltstabellen bestehender Beschriftungsgruppen und bestätigter Behälter zeigen jetzt eine eigene Bildspalte. Gemeinsame Bilddarstellung mit der Boxkarte erhält HTTP(S)-Prüfung, verzögertes Laden und Ersatzsymbol. Teilenamen bleiben sichtbar; Farbe, Menge und Überschriften werden nicht mitten im Wort getrennt. Schmale Ansichten scrollen innerhalb der Details. Lageranleitung und Softwaredesign ergänzt; keine Daten-/Schemaänderung.

**Prüfung:** Erweiterter isolierter Playwright-Lauf bestätigt ein tatsächlich geladenes Teilebild mit Name/Nummer in der geöffneten Detailtabelle und den weiterhin funktionierenden Etikettenablauf. Der bestehende Legacy-Browserlauf einschließlich Zuordnung sowie Desktop-/Mobilgrenzen bestand ebenfalls. JavaScript-Syntax, Ruff/Formatprüfung des geänderten Browsertests, lokale Dokumentverweise und Diff-Whitespace erfolgreich. Keine erneute vollständige Python-Suite für diese reine Darstellungsänderung ausgeführt; letzter Gesamtlauf bleibt 549 bestanden. Keine echten Bestandsdaten verändert.

## 2026-11-15 – Inventarbilder und dauerhafte Etikettenvormerkung

**Ursache und Ergebnis:** Fehlende Teile-Stammbilder führten zu Ersatzsymbolen, obwohl Inventardaten Bilder enthielten. Die gebündelte Inventarbildauswahl bevorzugt jetzt eine passende Farbe, dann Stammbild bzw. anderes verfügbares Inventarbild. Lesender Abgleich der freigegebenen Sammlung: 2.866 von 2.935 Lagerzeilen haben damit eine Bild-URL. Echte externe Bilder wurden in der laufenden Regalansicht erfolgreich geladen und visuell geprüft; fehlende Katalogbilder behalten ein Ersatzsymbol.

**Druckablauf:** Separate Checkbox „Etikett neu drucken“ auf bestehenden Boxgruppen und bestätigten Einheiten. Vormerkungen werden pro kanonischem Ziel in der vorhandenen Präferenztabelle gespeichert und bleiben über Neuladen/Seitenwechsel erhalten. Die bestehende Etikettenseite enthält eine gemeinsame PDF-Aktion und eine gesonderte Bestätigung des tatsächlichen Drucks. Ein Download oder Druckfehler entfernt keine Vormerkung. Generations- und Inhaltsprüfungen sowie eine atomare Bestätigung verhindern, dass ein älterer Download neuere Vormerkungen oder veränderte Boxen abhakt. Unvollständige Adressen sind erklärt gesperrt; veraltete Vormerkungen lassen sich separat entfernen. Bestehende manuelle Druckauswahlen bleiben erhalten.

**Daten und Dokumentation:** Kein Schemawechsel, keine Migration, kein Backfill und keine vorab gesetzten Häkchen in der echten Sammlung. Vorhandene Mengen, Rohbeschriftungen, Sammlungsdaten und Druckstatus bleiben erhalten. Softwaredesign, Schemareferenz (Präferenzschlüssel), Lageranleitung, Testanleitung und Abnahmenachweis aktualisiert. Die journalisierte Migration bleibt bytegleich.

**Verifikation:** 15 fokussierte Regressionen bestanden. Abschließender vollständiger Lauf **549 bestanden, 0 fehlgeschlagen, 0 übersprungen, 72,06 % Coverage**. Alle drei echten isolierten Browserläufe bestanden, einschließlich neuem vollständigem Vormerken-/PDF-/Bestätigungsablauf mit aktivem CSRF, echter PDF-Erzeugung und simulierter Downloadstörung. Externe PDF-Bildzugriffe wurden durch ein lokales Testbild ersetzt. Projektweites Ruff, Formatprüfung von Anwendung und Tests (101 Dateien), BasedPyright ohne Fehler/Warnungen, JavaScript-Syntax und Diff-Whitespace erfolgreich; lokale Dokumentverweise geprüft.

**Laufende Entwicklungsansicht und Grenzen:** Server mit der freigegebenen Sammlungsdatei neu gestartet. Reale Übersicht rein lesend auf Bilder, Checkboxen und unveränderte 2.935 Lagerzeilen geprüft. Die Druckseite zeigt die leere echte Vormerkliste und korrekt deaktivierte Aktionen. Beim absichtlichen Blockieren externer CDNs meldete die bestehende Druckseite zunächst fehlendes Bootstrap; mit explizitem Bootstrap-Teststub lief dieselbe lesende Seitenprüfung ohne JavaScript-Fehler. Keine echte Box markiert, kein Live-PDF erzeugt und kein physischer Druck ausgeführt. Externe Bildverfügbarkeit bleibt anbieterspezifisch; tatsächliche Etikettenausrichtung und Druckqualität sind vor Ort zu prüfen.

## 2026-11-15 – Teilevorschau und Nummerierung von unten nach oben

**Ergebnis:** Bestehende Boxkarten zeigen bis zu drei Teil-/Farbvarianten mit Bild oder Ersatzsymbol, Katalogname und Teilenummer; weitere Varianten bleiben über die Details zugänglich. Bild-URLs werden ausschließlich als HTTP(S) akzeptiert, verzögert und ohne Referrer geladen. In der Regalfront beginnt die Anzeige unten links, zählt nach oben und setzt in der nächsten Spalte fort. Die Anzeigeoption „Boxen je Spalte“ erlaubt zwei bis sechs Zeilen, zunächst drei. Dieser reversible Startwert behauptet keine tatsächliche Stapelhöhe; die Listenansicht bleibt aufsteigend von oben nach unten. Keine Umnummerierung, Datenmigration oder Änderung gespeicherter Aufstellungen.

**Dokumentation:** Lageranleitung, Softwaredesign und Testanleitung aktualisiert. Das Schema bleibt unverändert; die Datenantwort ergänzt lediglich die vorhandene Katalogbild-URL.

**Verifikation:** Vollständige Suite **534 bestanden, 0 fehlgeschlagen, 0 übersprungen; 71,59 % Coverage**. Beide isolierten Playwright-Läufe bestanden, keine JavaScript-Fehler. Erweiterte Regression prüft Teilevorschau, tatsächliche Kartenkoordinaten von unten nach oben, nächsten Spaltenbeginn, wählbare Zeilenzahl und alternative Listenreihenfolge. Ruff, Formatprüfung der drei betroffenen Pythondateien, projektweites BasedPyright (0 Fehler/Warnungen), JavaScript-Syntax und Diff-Whitespace erfolgreich. Lokale Dokumentverweise geprüft. Entwicklungsserver neu gestartet; rein lesender Browserlauf mit der freigegebenen Sammlung bestätigt 18 Karten in Regal 11/Fach 1, Teilevorschauen, Spaltenrichtung und Mobilbreite. Externe Requests wurden in Browserprüfungen abgefangen; tatsächliche Verfügbarkeit externer Katalogbilder bleibt anbieterspezifisch und wird durch das Ersatzsymbol abgefangen.

## 2026-11-15 – Lagerort-Auswahllisten numerisch sortiert

**Ergebnis:** Alle vollständigen Lagerort-Auswahllisten verwenden jetzt dieselbe natürliche Sortierung wie die Fachauswahl: Bereich, Regalnummer und zugehörige Fachnummer. Damit sind insbesondere Kategorieziele und Strukturformulare nicht länger nach Anlagereihenfolge gemischt. Beschriftungen und gespeicherte IDs bleiben unverändert. Lageranleitung ergänzt; keine Schema- oder Architekturänderung.

**Prüfung:** JavaScript-Syntaxprüfung erfolgreich. Im laufenden Entwicklungsserver per Playwright alle vier vollständigen Auswahllisten mit jeweils 61 Orten geprüft: durchgehend numerisch sortiert, beispielsweise Regal 1 mit Fach 1 bis 6 vor Regal 2. Nur lesende Browseraktionen. Diff-Whitespace und lokale Dokumentverweise geprüft. Keine erneute vollständige Python-Testsuite für diese reine Sortierung der Anzeige ausgeführt.

## 2026-11-15 – Bestehende Lagerinhalte in der Regalübersicht sichtbar

**Ursache und Korrektur:** Die Übersicht zeigte ausschließlich bestätigte physische Einheiten. Obwohl alle bisherigen Lagerzeilen erhalten waren, wirkten die Fächer deshalb leer. Bestehende Boxbeschriftungen erscheinen jetzt als gestrichelte Beschriftungsgruppen mit anklickbaren Teilen, Farben, Notizen und ungeklärten Mengen. Fehlende oder mehrdeutige Adressen bleiben separat auffindbar. Numerische Sortierung, Suche und begrenzte Listen erhalten Originaletiketten und Nummernlücken. Eine bestehende Inhaltszeile kann über das reguläre Formular gezielt einem geprüften Behälter zugeordnet werden.

**Datenschutz und Platzplanung:** Rein lesende Projektion ohne neue Behälter, erfundene Mengen oder Schemaänderung. Unbestätigte Altbelegung verhindert positive Aussagen über freie Stellfläche und Passung. Die unveränderte Originalmigration behält ihre journalisierte Prüfsumme. Softwaredesign, Lageranleitung, Testanleitung und Abnahmenachweis aktualisiert; eine Änderung der Schemareferenz ist mangels Schemaänderung nicht erforderlich.

**Verifikation:** Fünf neue Regressionen zunächst fehlgeschlagen, danach bestanden. Abschließende vollständige Suite: **534 bestanden, 0 fehlgeschlagen, 0 übersprungen, 71,58 % Coverage**. Bestehender und neuer Playwright-Browserlauf auf isolierter Datenbank erfolgreich, einschließlich tatsächlicher Einzelzuordnung, Textsicherheit und Desktop-/Mobilansicht. Projektweites Ruff erfolgreich; Formatprüfung aller Pythondateien unter Anwendung/Tests erfolgreich (98 Dateien), BasedPyright ohne Fehler/Warnungen, JavaScript-Syntax und Diff-Whitespace geprüft. Der zusätzlich versuchte repositoryweite Formatter-Check meldet ausschließlich zwei unveränderte historische Markdown-Berichte mit alten Codebeispielen; diese wurden nicht umformatiert.

**Reale Entwicklungsansicht:** Server mit der freigegebenen gefüllten Sammlungsdatei neu gestartet. HTTP 200 für Health, Lagerseite und Datenantwort. Rein lesender Browserlauf zeigt bestehende Gruppen und deren Inhalte, ohne JavaScript-Fehler oder horizontales Überlaufen bei 390 Pixeln. Die 2.935 bestehenden Zeilen ergeben 1.269 Beschriftungsgruppen: 1.624 Zeilen eindeutig unter Fächern, 1.311 mit noch ungeklärtem Fundort. Keine physische Einheit automatisch erzeugt. Ursprüngliche Sammlungszeilenzahlen und Inhaltsfingerabdrücke anschließend erneut mit der Baseline verglichen und unverändert bestätigt. Ausnahme: Die bestehende Dashboard-Funktion hat einen zusätzlichen Tages-Snapshot für den 15. November mit 425 Sets angelegt; die beiden ursprünglichen Snapshots sind unverändert. Das Migrationsjournal blieb unverändert.

**Vor Ort offen:** Tatsächliche Behälteridentität, Aufstellung, Stapel, Mengen und Maße bleiben physisch zu bestätigen; vorhandene Beschriftungen allein belegen diese Eigenschaften nicht.

## 2026-11-15 – Gefüllte Sammlungsdatei nach Bestätigung aktiviert

**Auftrag und Ergebnis:** Nach ausdrücklicher Auswahl durch den Nutzer auf `data/instance/brick_manager.db` umgestellt, dieselbe Datei wie `/app/data/instance/brick_manager.db`. Lokalen `.env`-Override auf den absoluten Pfad gesetzt und den Entwicklungsserver auf `127.0.0.1:5000` neu gestartet. Der geöffnete Dateideskriptor des laufenden Prozesses bestätigt genau diese Datei.

**Sicherung und Migration:** Vorher konsistente SQLite-Sicherung `data/instance/backups/brick_manager-before-warehouse-20261115T124120657968Z.db` erstellt. Migration und Wiederholung auf isolierter Kopie sowie ORM-Lesezugriffe geprüft. Danach die freigegebene Datei migriert und erneut mit der Sicherung verglichen: ursprüngliche Datentabellen mit unveränderten Zeilenzahlen, sämtliche ursprünglichen Spalten der sammlungseigenen Tabellen mit identischen SHA-256-Fingerabdrücken. Der ursprüngliche Journaleintrag blieb unverändert; die neue Migration wurde zusätzlich journalisiert. Keine Wiederherstellung und kein Reset.

**Bestand und Laufzeit:** 425 eigene Sets, 53.820 Set-Teilzeilen und 2.935 Lagerzuordnungen erhalten. Alle 2.935 Altzuordnungen besitzen ein nachvollziehbares Migrationsmapping; neue physische Mengen bleiben unbekannt statt aus Setbeständen geschätzt zu werden. `/health`, `/warehouse` und `/warehouse/data` liefern HTTP 200. Die Datenantwort enthält alle 2.935 Lagerzuordnungen und 61 aus den vorhandenen Ortsbeschriftungen abgeleitete, noch ungeprüfte feste Orte.

**Vorhandene Datenlücken:** Die 127 bereits vor der Migration bestehenden Fremdschlüssel-Verweislücken blieben unverändert: 21 Minifigurenteil- und 18 Set-Teil-Verweise sowie 9 Lagerzuordnungen ohne passenden Katalogteil; außerdem 75 Inventarteil- und 4 Inventarfiguren-Verweise ohne zugeordnetes Inventar. Keine dieser Bestandszeilen wurde bereinigt oder gelöscht. Die vorherige kleinere Datenbankdatei bleibt unangetastet erhalten.

## 2026-11-15 – Gefüllte Sammlungsdatei und irrtümliche Dateizuordnung identifiziert

**Korrektur der Zuordnung:** Die Sammlung liegt in `data/instance/brick_manager.db`, identisch mit der unter `/app/data/instance/brick_manager.db` eingebundenen Datei. Read-only-Prüfung: 425 eigene Sets, 53.820 Set-Teilzeilen und 2.935 Lagerzuordnungen; außerdem 64.998 Katalogteile und 28.605 Katalogsets. Diese Datei ist etwa 196 MB groß und besitzt noch keine physische Lagermigration.

Die zuvor ausdrücklich benannte Datei `brick_manager/instance/brick_manager.db` ist eine andere Datei mit leeren Sammlungs-/Katalogtabellen. Auch deren vor dem Serverstart angelegte Sicherung und die benachbarte Kopie enthalten dort keine Bestandszeilen. Die frühere Leer-Aussage beschreibt diese andere Datei und nicht die gefüllte Sammlung; die Zuordnung hätte vor dem Umstellen umfassender geprüft werden müssen.

**Vorgehen:** Ausschließlich lesende Datenbankverbindungen mit `mode=ro` und `query_only`; weder Datenbankinhalte noch Konfiguration geändert. Den richtigen Zielpfad zur Klärung vorgelegt, bevor die gefüllte Sammlung migriert oder der Server umgestellt wird.

## 2026-11-15 – Originalmigration nach automatischer Umformatierung wiederhergestellt

**Ursache:** Die angewendete `20261115_physical_storage.py` hatte nach einer reinen Umformatierung eine neue Dateiprüfsumme. Der Python-AST war identisch; der Migrationsrunner lehnte die Datei korrekt ab. Der bisherige Ruff-Ausschluss galt bei expliziten Dateilisten der Pre-commit-Hooks nicht zuverlässig.

**Korrektur:** Die bytegenaue Originalfassung aus dem geprüften Wheel wiederhergestellt. Deren SHA-256 `4cfeaa1b620088e3e31bb1809f068f12fbde798dfa64b14f6da58d39e4d17d87` stimmt mit dem vorhandenen Datenbankjournal überein. Die formatierte Fassung für die Nachvollziehbarkeit unter `/tmp/brick-migration-formatted-before-recovery.py` aufbewahrt. Die bereits vorgemerkte Migration im Git-Index ebenfalls auf die Originalbytes synchronisiert. `force-exclude = true` und explizite Ausschlüsse der vier mutierenden Hooks verhindern erneutes Umschreiben; die beiden zugehörigen Konfigurationskorrekturen sind ebenfalls vorgemerkt. Andere vorgemerkte Änderungen bleiben erhalten.

**Prüfung und Grenzen:** Der Formatierungsfehler wurde mit dem echten Ruff-Aufruf reproduziert. Danach 18 gezielte Formatter-/Migrationsprüfungen bestanden; Hook-Konfiguration gültig. Die echte Datenbank nur lesend mit der wiederhergestellten Datei verglichen, das Journal nicht geändert und keinen Backfill erneut ausgeführt. Der bestehende Server liefert `/health` und `/warehouse` mit HTTP 200. Abschließender Gesamtlauf: **529 bestanden, 0 fehlgeschlagen, 0 übersprungen, 71,34 % Coverage**. Projektweites Ruff, Formatprüfung (99 Dateien), BasedPyright (0 Fehler/Warnungen), gültige Hook-Konfiguration sowie explizite Ruff-Aufrufe auf der wiederhergestellten Migration erfolgreich. Qualitätsreferenz aktualisiert; keine fachliche Schemaänderung erforderlich.

## 2026-11-15 – Lagerverwaltung auch ohne Umgebungsvariable aktiv

**Ergebnis:** Bestätigt, dass `Config.WAREHOUSE_ENABLED` bereits mit dem Fallback `true` arbeitet und die Route bei fehlendem Konfigurationsschlüssel ebenfalls aktiviert bleibt. Dokumentation und `.env.example` präzisieren den Standard ausdrücklich auch für eine fehlende Umgebungsvariable. Keine Laufzeitänderung nötig.

**Regression:** Die reale Konfiguration wird mit fehlender Variable und explizitem `true` geladen und jeweils über den regulären `/warehouse`-Einstieg geprüft. Verzeichniserzeugung dabei isoliert; vorhandene deaktivierte Konfiguration wird weiterhin vom bestehenden Test geprüft. Keine Bestandsdaten oder laufenden Servereinstellungen verändert. Verifikation: 26 Warehouse-Vertragstests bestanden; Ruff, Formatierung und Diff-Prüfung erfolgreich.

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
