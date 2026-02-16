# API Implementation Notes (2026-02-03)

This document captures the implementation details for the Phase 1 editor + daily endpoints added in early February 2026.

## Summary
- Implemented editor validation + save endpoints with schema v0.1 validation.
- Added daily open/append endpoints and ensured token auth parity across servers.
- Wired new endpoints through FastAPI, the legacy HTTP server, Tauri commands, and the Python bridge shim.
- Standardized JSON error responses in the FastAPI server.

## Endpoints

### POST `/api/validate`
Payload:
```json
{ "frontmatter": { ... }, "body": "..." }
```
Behavior:
- Validates frontmatter against schema v0.1.
- Returns `valid`, `errors`, and `warnings`.

Response:
```json
{ "valid": true, "errors": [], "warnings": [] }
```

### POST `/api/item/update`
Payload:
```json
{
  "path": "/abs/path/or/vault-relative",
  "frontmatter": { ... },
  "body": "...",
  "validate_only": false
}
```
Behavior:
- Merges provided frontmatter into the existing item.
- Updates `updated` timestamp.
- Enforces status transition rules.
- If `validate_only` is true, skips writing.

Response:
```json
{
  "path": "...",
  "frontmatter": { ... },
  "body": "...",
  "warnings": [],
  "saved": true
}
```

### GET `/api/daily/open?date=YYYY-MM-DD`
Behavior:
- Opens or creates the daily note for the date.

Response:
```json
{ "path": "...", "item": { ...item_view... } }
```

### POST `/api/daily/append`
Payload:
```json
{ "date": "YYYY-MM-DD", "text": "..." }
```
Behavior:
- Appends text to the daily note, creating it if needed.

Response:
```json
{ "path": "...", "item": { ...item_view... } }
```

## Error Handling
- All API errors use the JSON envelope `{ "error": "message" }`.
- FastAPI server now maps `ApiError`, validation errors, and 404s to the same envelope.

## Auth
- Token auth is enforced on all endpoints.
- Header: `X-Substrate-Token: <token>`
- Optional query param `?token=<token>` for GET requests.

## UI / Tauri Integration
- Tauri commands: `validate`, `item_update`, `daily_open`, `daily_append`.
- Python bridge supports the same command names for local UI testing.
- Legacy compatibility: `POST /api/daily/open` is supported for the UI bridge but is not part of the canonical contract.

## Files Touched
- `substrate/api.py`
- `tools/api_fastapi.py`
- `tools/api_server.py`
- `ui/tauri/src-tauri/src/commands.rs`
- `ui/tauri/src-tauri/src/main.rs`
- `tools/tauri_bridge.py`
- `docs/API_CONTRACT.md`

## Next Steps
- None. All planned tasks for this update are complete.
