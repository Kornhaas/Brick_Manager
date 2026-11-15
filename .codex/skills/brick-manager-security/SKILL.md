---
name: brick-manager-security
description: Review Brick Manager security boundaries in routes, uploads, tokens, remote requests, filesystem access, and dependencies. Use for scoped defensive security reviews and remediation planning.
---

# Brick Manager Security Review

Establish the requested scope and inspect `docs/reference/configuration.md`, the affected routes/services, configuration, and tests. Use repository security policy when present. A source review does not authorize probing deployed services or live remote writes.

- Trace untrusted input to SQL, templates, file paths, uploads, downloads, redirects, logging, and outgoing requests. Verify validation at the boundary and actual sink behavior.
- Check `/api/v1` authentication independently from web UI access. Do not assume desktop bearer authentication protects UI routes. Examine state-changing browser actions and CSRF according to the actual deployment and session model.
- Inspect token storage, redaction, authorization checks, request timeouts, URL restrictions, archive/path traversal, upload limits, and SQLite parameterization where relevant to the scope.
- Do not print secrets or read real credential values to demonstrate a finding. Use synthetic values and isolated temporary files/databases for reproduction.
- Report findings with file/line evidence, entry-to-sink path, prerequisites, impact, and a focused remediation. Separate confirmed findings from unverified suspicions and deployment assumptions. Report scope and verification limits even when no findings are identified.
- Run `make audit` when dependency review is requested; distinguish a vulnerable dependency from demonstrated application exploitability. Do not silently upgrade packages during a review.
- For requested fixes load the development skill plus data/sync/test skills as applicable; preserve collection data and public contracts. Reproduce locally with synthetic inputs and verify the corrected behavior.

If specialized Codex Security workflows are available, select the matching repository scan, diff scan, or finding-validation workflow for those requests. This local skill remains usable without external plugins.
