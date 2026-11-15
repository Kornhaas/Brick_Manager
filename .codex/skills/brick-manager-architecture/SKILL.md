---
name: brick-manager-architecture
description: Plan or review Brick Manager component boundaries, cross-cutting refactors, startup behavior, and architectural decisions. Use for architectural tradeoffs rather than ordinary feature implementation.
---

# Brick Manager Architecture

Read `docs/architecture/reference-architecture.md`, `docs/architecture/decisions.md`, and the relevant runtime paths before proposing changes. Verify documentation claims against code.

- Preserve Flask blueprints, services, SQLAlchemy, Jinja, and vanilla JavaScript unless the task explicitly calls for a different architecture.
- Trace a representative request through route, service, model, template, and external boundary. Identify contracts and consumers affected by the proposal.
- Account for top-level application imports and `app.py` startup side effects, including database initialization and scheduled jobs. Do not import the production app merely to inspect it.
- Compare the smallest viable change with alternatives using collection-data safety, complexity, compatibility, and operability. Avoid introducing frameworks or layers without a concrete need.
- Return a recommendation with affected files, contract changes, implementation order, verification, and rollback limits. Record accepted lasting decisions in the existing architecture decisions document; label unaccepted proposals clearly.
- Load `brick-manager-data-change` for persistence and `brick-manager-sync-contracts` for remote or desktop API boundaries. Hand implementation to `brick-manager-development`.

Keep `docs/architecture/high-level-design.md`, `reference-architecture.md`, and `software-design.md` consistent at their respective abstraction levels. Link to detailed references rather than copying schemas or configuration inventories. Follow the documentation completion rule in `AGENTS.md`; include documentation impacts in the parent handoff and record integrated work in `docs/logbook.md`.
