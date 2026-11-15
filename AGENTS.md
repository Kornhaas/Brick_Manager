# Brick Manager Agent Guide

Repository-specific skills live under `.codex/skills/`. Load the smallest matching set before acting:

- `brick-manager-development`: ordinary Flask feature, bugfix, refactor, or review work.
- `brick-manager-data-change`: models, SQLite schema, migrations, imports, backups, or persisted-data transformations.
- `brick-manager-sync-contracts`: Rebrickable, Brickognize, downloads, tokens, scheduled sync, or `/api/v1` contracts.
- `brick-manager-regression-tests`: test-focused work and regression-test design.

- `brick-manager-architecture`: component boundaries, cross-cutting refactors, and architectural decisions.
- `brick-manager-ux`: task-based usability/accessibility reviews and UX design.
- `brick-manager-security`: scoped defensive security reviews and remediation planning.

## Specialist agents

Project agents are defined in `.codex/agents/*.toml`:

| Agent | Responsibility | Primary skill |
| --- | --- | --- |
| `architect` | Architecture, tradeoffs, component contracts | `brick-manager-architecture` |
| `senior_developer` | End-to-end implementation and debugging | `brick-manager-development` |
| `tester` | Reproduction, behavioral tests, verification | `brick-manager-regression-tests` |
| `usability_expert` | Current task flows, accessibility, interaction friction | `brick-manager-ux` |
| `security_expert` | Trust boundaries and evidence-based security review | `brick-manager-security` |
| `database_architect` | Schema, migrations, ownership, data integrity | `brick-manager-data-change` |
| `ux_designer` | Intended flows, interface states, layout and content | `brick-manager-ux` |

Choose only roles relevant to the task; small changes do not require the whole team. When delegation is supported and permitted by the session, assign bounded tasks with explicit file ownership and expected evidence. Parallelize independent reviews; serialize dependent implementation and shared-file edits. The parent integrates findings and verifies the final result. Review roles default to analysis; implementation requires an assignment. Without custom-agent support, read the role file and apply its instructions in the main session, stating that no independent agent ran.

See [AI collaboration](docs/guides/ai-collaboration.md) for usage and verification limits.

Use multiple skills when the task genuinely crosses boundaries; for example, a new persisted API field needs development, data-change, sync-contract, and regression-test guidance.

Treat `brick_manager/models.py`, versioned migrations, and executable tests as the primary source of truth. Keep `docs/reference/database-schema.md` and `docs/guides/testing.md` synchronized with verified behavior and measurements. Preserve user collection data, never expose credentials, and do not perform live remote writes, database resets, restores, or deployments without explicit user authorization.

Use Poetry commands from the repository root. Preserve unrelated working-tree changes.

## Documentation is part of completion

Keep all maintained project documentation in `docs/`, indexed by `docs/README.md`. Root entrypoints such as README.md and AGENTS.md and tool-discoverable `.codex/` instructions remain in their required locations and link to the central documentation; do not create competing design documents there.

For every completed work item, update the affected documentation in the same change and append a dated entry to `docs/logbook.md` describing the result, rationale, actual verification, and remaining limitations. Do not invent historical entries, test results, or implemented behavior. If no reference/design update is needed, state why in the logbook entry. The parent agent owns the integrated entry; specialists report documentation impacts to it to avoid duplicate entries and concurrent edits.

Use `docs/architecture/high-level-design.md` for system context and major flows, `docs/architecture/reference-architecture.md` for component boundaries and runtime architecture, `docs/architecture/software-design.md` for implementation contracts and extension points, and `docs/architecture/decisions.md` for lasting technical decisions. Keep detailed schema, configuration, testing, operation, and user guidance in the existing reference/guide files and link rather than duplicate them. Mark proposals separately from current behavior. Historical reports stay under `docs/history/`.

Before handoff, check documentation against the changed code and tests, validate local links in touched Markdown files, and report documentation updates with verification limits. Read `docs/README.md` for the change-to-document mapping.

## Commit messages

Whenever generating or suggesting a commit message, including editor-generated
messages, use Conventional Commits as required by `scripts/install_hooks.sh`:

```text
<type>[optional scope]: <description>
```

- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`.
- Use a lowercase type, an optional scope in parentheses, and a colon followed by one space.
- Write a concrete English description in the imperative, with at most 50 characters in the description.
- Describe the actual staged changes; avoid generic messages such as "Implement code changes".
- Do not add `!` before the colon: the current commit hook does not accept that syntax.
- When asked only for a commit message, return the message without Markdown fences or explanatory text.

Examples: `fix(ui): support quantity navigation on iPad`,
`chore(devcontainer): provide UTF-8 locales`.
