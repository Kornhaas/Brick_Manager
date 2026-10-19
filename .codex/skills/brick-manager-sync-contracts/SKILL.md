---
name: brick-manager-sync-contracts
description: Implement, debug, or review Brick Manager Rebrickable, Brickognize, image-download, token, scheduled-sync, or authenticated desktop API behavior. Use when remote calls, rate limits, credentials, retries, or JSON contracts are involved.
---

# Brick Manager Sync Contracts

Preserve local data, remote state, authentication, and client compatibility across integration changes.

1. Identify the contract boundary and direction: remote read, remote write, local import, scheduled sync, image download, or `/api/v1` client request. List stable identifiers and which system is authoritative before editing.
2. Keep secrets in configuration or encrypted storage. Never log tokens, API keys, authorization headers, full credential payloads, or decrypted values. Preserve constant-time bearer-key comparison and fail-closed behavior for the desktop API.
3. Use finite timeouts. Handle connection failures, non-success status codes, invalid JSON, pagination, rate limiting, and partial batch success explicitly. Bound retries and backoff; do not retry permanent validation/authentication failures as transient failures.
4. Make writes idempotent where possible. Fetch or compare current state before destructive reconciliation. Never interpret a failed or truncated remote read as an authoritative empty collection.
5. Keep database mutation transactional at a useful boundary. Return structured results that distinguish complete success, partial success, skipped work, rate limiting, and failure.
6. Treat `/api/v1` field names, status codes, authentication errors, ordering, clamping rules, and null handling as a versioned client contract. Additive changes are preferred; coordinate breaking changes with the client and API documentation.
7. Mock network calls in automated tests and assert exact request method, endpoint, relevant headers without secret values, parameters/body, timeout, and database effects. Include timeout, 401/403, 404, 429, malformed response, and partial-batch cases as relevant.

Read [references/integration-contracts.md](references/integration-contracts.md) for the current integration map and required invariants.

Do not call live remote write endpoints, generate tokens, or run a full synchronization unless the user explicitly authorizes that external mutation.
