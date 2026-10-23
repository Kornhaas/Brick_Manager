# Konfiguration

Die Konfiguration liegt in `brick_manager/config.py`. In Docker werden
Laufzeitdaten unter `/app/data` erwartet; lokal nutzt die Anwendung Verzeichnisse
unterhalb von `brick_manager/` sowie `data/instructions`.

| Variable | Zweck | Verhalten ohne Wert |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | SQLite-/SQLAlchemy-Verbindung | lokaler bzw. Docker-Standardpfad |
| `SECRET_KEY` | Flask-Sitzungssignierung | Entwicklungswert; in Produktion zwingend setzen |
| `REBRICKABLE_TOKEN` | Rebrickable-API-Zugang | Entwicklungswert; für echte Syncs sicher setzen |
| `BRICK_MANAGER_CLIENT_API_KEY` | Bearer-Key für `/api/v1` | leer; API antwortet dann mit 503 |

Beispiel für eine lokale Entwicklungsumgebung:

```bash
export SECRET_KEY='lokaler-entwicklungswert'
export REBRICKABLE_TOKEN='kein-echter-token-in-dokumentation'
export BRICK_MANAGER_CLIENT_API_KEY='lokaler-client-schluessel'
```

Zugangsdaten gehören nicht in Git, Logs, Tests oder Tickets. Die Verzeichnisse
für Uploads, Ausgaben, Cache, Datenbank, Logs und Anleitungen werden von der
Konfiguration angelegt. Upload-Dateinamen akzeptieren PNG, JPG/JPEG, GIF sowie
aus Kompatibilitätsgründen `.gi`; die maximale Anforderungsgröße beträgt 16 MiB.
