# API Editor + Daily Endpoint Tests

This document summarizes the integration test coverage added for Phase 1 editor
and daily API endpoints.

## Location
- `texttests/integration/test_api_server.py`

## Coverage
- `POST /api/validate`
  - Valid frontmatter/body returns `valid: true` and empty errors.
  - Invalid frontmatter returns `valid: false` with errors populated.
- `POST /api/item/update`
  - `validate_only: true` returns `saved: false` and does not write.
  - Invalid updates return `400` and do not write.
  - Valid updates persist frontmatter/body changes.
- `GET /api/daily/open`
  - Opens or creates the daily note for the requested date.
- `POST /api/daily/append`
  - Appends text and returns the updated item payload.
- Token enforcement
  - Missing token returns `401` for new endpoints.
  - `X-Substrate-Token` header is accepted when required.

## Determinism
- Uses pytest `vault_root` fixture (temp vault).
- Uses fixed date `2026-02-03` to avoid time drift.

## Running
```bash
python3 -m pytest texttests/integration/test_api_server.py
```

## Last Run
- Date: 2026-02-03
- Result: 4 skipped
- Reason: Socket binding not permitted in this environment (server tests skipped).
