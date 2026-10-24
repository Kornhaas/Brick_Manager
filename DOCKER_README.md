# Docker Operations

`docker-compose.yml` is the production-oriented configuration. It pulls the CI-built
Docker Hub image and mounts only persistent data directories. Source or template
changes therefore require a new CI image, not a server-side build.

## Initial setup

```bash
cp .env.example .env
# Set at least SECRET_KEY, REBRICKABLE_TOKEN as needed, and
# BRICK_MANAGER_CLIENT_API_KEY when the desktop API is used.

docker compose pull
docker compose up -d --no-build
docker compose ps
curl http://localhost:5000/health
```

Application: `http://localhost:5000`

By default the server pulls the `main` image tag. For a repeatable production
deployment, set `BRICK_MANAGER_IMAGE_TAG` in `.env` to a released version (for
example `1.2.3`) before running `docker compose pull`.

## Updating application code

```bash
docker compose pull
docker compose up -d --no-build
docker compose logs -f bricks-manager
```

`docker compose restart` only restarts the existing image. Use `docker compose pull`
followed by `docker compose up -d --no-build` to deploy a CI-built update.

## Development mode

The development override mounts `./brick_manager` read-only into the container and enables Flask reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Do not expose the development server to an untrusted network.

## Persistent data

| Host path | Container path | Purpose |
| --- | --- | --- |
| `./data/instance` | `/app/data/instance` | SQLite database and scheduled backups |
| `./data/uploads` | `/app/data/uploads` | Uploaded files |
| `./data/output` | `/app/data/output` | Generated labels and exports |
| `./data/cache` | `/app/data/cache` | Cached images and lookup data |
| `./data/logs` | `/app/data/logs` | Application logs |
| `./data/instructions` | `/app/data/instructions` | Building instructions |

Back up `data/` before upgrades that can affect persisted state:

```bash
make backup
```

## Database initialization and migrations

`docker-entrypoint.sh` follows this policy:

1. Create all declared tables only when the SQLite database does not yet exist.
2. Apply every restart-safe `*.sql` migration in `brick_manager/migrations/` in name order.
3. Validate foreign-key integrity after migration and fail startup if validation fails.

The repository's migration directory contains versioned SQLite scripts, not an
Alembic repository; `flask db upgrade` must therefore not be used at startup.

`db.create_all()` is not a migration mechanism and cannot add or transform columns in an existing table. Schema changes must include committed migration artifacts.

## Useful commands

```bash
docker compose logs -f bricks-manager
docker compose exec bricks-manager sh
docker compose exec bricks-manager python -m pytest
docker compose down
docker compose build --no-cache
docker compose up -d
```

`make db-shell` opens Python's SQLite shell inside the container; no separate Alpine SQLite client is required.

## Production notes

- Set a strong `SECRET_KEY`; do not keep the Compose placeholder.
- Set a strong `BRICK_MANAGER_CLIENT_API_KEY` before enabling trusted desktop clients.
- Keep port 5000 behind a firewall or reverse proxy; use HTTPS outside localhost or a trusted private LAN.
- The Flask development server is the current container command. For public or multi-user deployment, replace it with a reviewed production WSGI setup and ensure scheduled jobs run exactly once.
- Container health is checked through `/health`.
