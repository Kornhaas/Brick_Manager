# Integration Contracts

## Rebrickable

- Catalog API logic: `services/rebrickable_service.py`.
- Missing-parts/list reconciliation: `services/rebrickable_sync_service.py`.
- Owned-set list reconciliation: `services/rebrickable_sets_sync_service.py`.
- Token retrieval and decryption: `services/token_service.py`; token-management HTTP routes live in `routes/token_management.py`.
- Bulk imports download catalog archives from Rebrickable CDN through `routes/import_rebrickable_data.py`.

Use Rebrickable part numbers, color IDs, set numbers, list IDs, and inventory IDs consistently. For pagination, keep fetching until the API explicitly indicates completion. For 429 responses, honor server guidance when available and place a strict bound on attempts and total wait.

## Brickognize and image downloads

- Brick recognition uploads images through `services/brickognize_service.py`.
- Image cache and label code download remote images through `services/cache_service.py` and `services/label_service.py`.

Validate local upload paths and size/type limits. For remote image URLs, retain URL validation, response-size controls where practical, content validation, and safe local filenames. Do not weaken SSRF protections when adding supported hosts or redirects.

## Desktop API `/api/v1`

All routes require `Authorization: Bearer <BRICK_MANAGER_CLIENT_API_KEY>`. An unset server key returns 503; missing or invalid credentials return 401.

Current resources:

- `GET /parts/{part_num}` returns catalog details or 404.
- `GET /parts/{part_num}/sets` optionally filters integer `color_id` and returns `{ "items": [...] }`.
- `GET /parts/{part_num}/storage` optionally filters `color_id` and returns ordered storage rows.
- `PUT /user-parts/{id}/quantity` accepts a non-negative integer `have_quantity`, clamps it to required quantity, and returns derived `missing`.
- `PUT /parts/{part_num}/storage` validates optional integer `color_id` plus bounded string fields and upserts the first matching part/color row.

Before changing a field, search the repository and the consuming desktop client if it is in scope. Preserve deterministic ordering and distinguish empty collections from missing resources.

## Scheduled work

`brick_manager/app.py` starts backup and sync jobs at import time. Scheduler changes must consider multiple worker processes, repeated imports, application context, overlapping runs, and shutdown. Never assume an in-process scheduler provides distributed mutual exclusion.
