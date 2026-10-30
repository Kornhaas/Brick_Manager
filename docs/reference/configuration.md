# Konfiguration und Sicherheit

Die zur Laufzeit verwendete Konfiguration liegt in `brick_manager/config.py`; `.env.example` ist die kopierbare Vorlage. Zugangsdaten gehören ausschließlich in die lokale `.env` oder in die Deployment-Umgebung, nie in Git, Logs, Tests oder Tickets.

## Umgebungsvariablen

| Variable | Zweck | Verhalten ohne Wert |
| --- | --- | --- |
| `SECRET_KEY` | Signiert Flask-Sitzungen | Entwicklungswert aus `Config`; in Produktion zwingend ersetzen |
| `REBRICKABLE_TOKEN` | Rebrickable-API-Zugang | Entwicklungswert; für echte Synchronisierung einen echten Token setzen |
| `BRICK_MANAGER_CLIENT_API_KEY` | Bearer-Key für `/api/v1` | leer; die Desktop-API antwortet dann mit `503` |
| `SQLALCHEMY_DATABASE_URI` | SQLite-/SQLAlchemy-Verbindung | lokaler bzw. Docker-Standardpfad |
| `FLASK_ENV`, `FLASK_DEBUG` | Flask-Umgebung | insbesondere im Docker-Compose gesetzt |
| `LOG_LEVEL` | derzeit für Betriebsumgebungen reserviert | wird von `Config` nicht ausgewertet |

Die Desktop-API akzeptiert ausschließlich `Authorization: Bearer <key>`. Sie ist für einen vertrauenswürdigen Client im privaten Netz gedacht. Für nicht-lokale Bereitstellung sind HTTPS, Firewall- und Zugriffsschutz erforderlich.

## Laufzeitpfade

| Umgebung | Datenbank | Weitere Laufzeitdaten |
| --- | --- | --- |
| Lokal | `brick_manager/instance/brick_manager.db` | Uploads, Ausgabe, Logs und Cache unter `brick_manager/`; Bauanleitungen unter `data/instructions/` |
| Docker | `/app/data/instance/brick_manager.db` | `/app/data/{uploads,output,cache,logs,instructions}` |

`Config` legt diese Verzeichnisse beim Import an. Uploads dürfen maximal 16 MiB groß sein; erlaubte Endungen sind `png`, `jpg`, `jpeg`, `gif` sowie das historische Kompatibilitätsformat `gi`.

## Sichere Inbetriebnahme

1. `.env.example` nach `.env` kopieren und `SECRET_KEY` sowie bei Bedarf die API-Keys durch zufällige Werte ersetzen.
2. Den SQLite-Pfad auf persistente Speicherung prüfen, bevor produktive Daten eingegeben werden.
3. Für externe Synchronisierung Tokens erst nach dem lokalen Start setzen und nie in Screenshots übernehmen.
4. Vor Backup, Restore, Datenimport oder Live-Synchronisierung die jeweiligen Betriebsfolgen prüfen.
