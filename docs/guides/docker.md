# Docker-Betrieb

`docker-compose.yml` startet den Container `bricks-manager` mit persistenten Host-Verzeichnissen unter `data/`. Der Dienst veröffentlicht Port `5000` und verwendet einen Healthcheck auf `/health`.

## Start

```powershell
Copy-Item .env.example .env
# .env mit sicheren Werten ergänzen
docker compose up -d
docker compose ps
```

Alternativ richtet `make setup` die lokale `.env`-Vorlage und Datenordner ein und startet anschließend den Stack.

## Persistente Daten

| Host-Pfad | Container-Pfad | Inhalt |
| --- | --- | --- |
| `data/instance` | `/app/data/instance` | SQLite-Datenbank |
| `data/uploads` | `/app/data/uploads` | Uploads |
| `data/output` | `/app/data/output` | Labels und Exporte |
| `data/cache` | `/app/data/cache` | Cache |
| `data/logs` | `/app/data/logs` | Logs |
| `data/instructions` | `/app/data/instructions` | Bauanleitungen |

Diese Verzeichnisse vor Update, Umzug oder Wiederherstellung sichern. Ein Container-Neustart ersetzt keine geprüfte Datenbanksicherung.

## Build und Veröffentlichung auf GitHub

Ein Push auf `main` startet `.github/workflows/docker-image.yml`. Zuerst läuft
die Python-Testsuite, danach entstehen die Images für `linux/amd64` und
`linux/arm64`. Der Workflow veröffentlicht `docker.io/kornhaas/bricks_manager`
mit den Tags `main` und `latest`, startet einen wegwerfbaren Testcontainer ohne
Produktivvolume, prüft `/health` und führt den Security-Scan aus.

Ein erfolgreicher Release-Nachweis umfasst den vollständig abgeschlossenen
Workflow für den tatsächlich gepushten Commit, nicht nur einen gestarteten Build.
Mit angemeldeter GitHub-CLI lässt sich der Lauf beobachten:

```powershell
gh run list --repo Kornhaas/Brick_Manager --workflow docker-image.yml --branch main
gh run watch <run-id> --repo Kornhaas/Brick_Manager --exit-status
```

Der Job „Deploy“ erzeugt derzeit ausschließlich eine Bereitstellungsmitteilung.
Er aktualisiert keinen laufenden Produktionsserver. Ein echtes Serverupdate
bleibt ein gesonderter Auftrag; der App-Start kann Migrationen und Jobs auslösen.

## Sicherheitsupdates des Images

Beide Docker-Stufen aktualisieren geerbte Alpine-Pakete mit `apk upgrade`.
CI zieht das Basisimage neu (`pull: true`) und verwendet für die benannte
`runtime`-Stufe keinen Layer-Cache. Dadurch bleiben verfügbare Paketkorrekturen
nicht in einem alten Installationslayer hängen. Für denselben lokalen Ablauf:

```powershell
docker build --pull --no-cache-filter runtime -t brick-manager:review .
```

Trivy behandelt alle Schweregrade einschließlich noch nicht behebbarer Befunde
als Workflowfehler. Der SARIF-Bericht wird auch im Fehlerfall hochgeladen.
Der Scan findet derzeit **nach** dem Registry-Push statt: Er verhindert eine
erfolgreiche Pipeline/Bereitstellungsmitteilung, aber nicht die vorangehende
Image-Veröffentlichung. Ein Scan vor der Veröffentlichung ist ein weiterer
Planungspunkt. Für den Befundstand vom 22. November 2026 wurden krb5-libs,
libcrypto3, libssl3 und zlib aktualisiert; neue Advisories erfordern neue Builds.

## Weitere Betriebshinweise

- Der optionale Nginx-Dienst läuft nur mit dem Profil `production`; seine referenzierte Nginx-Konfiguration muss vor Aktivierung bereitgestellt werden.
- Die Compose-Defaults für Tokens und `SECRET_KEY` sind nur Platzhalter. In Produktion zwingend durch eigene Werte ersetzen.
- Live-Synchronisierung und Wiederherstellung sind zustandsverändernde Vorgänge und werden nicht als Routine-Healthcheck ausgeführt.
