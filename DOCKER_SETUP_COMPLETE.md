# Docker Setup Status

Docker support is present and maintained through:

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-entrypoint.sh`
- Docker-related targets in `Makefile`

This file previously duplicated operational instructions and drifted from the actual container behavior. Use [`DOCKER_README.md`](DOCKER_README.md) as the canonical Docker guide and [`README.md`](README.md) for the project overview.

Important current facts:

- Production source code is baked into the image; rebuild after code changes.
- Persistent state is mounted from `./data/`.
- New databases can be initialized from SQLAlchemy models.
- Existing database schema changes require committed migrations.
- The application and health endpoint are exposed on port 5000 by default.
